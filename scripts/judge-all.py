"""Judge a selected queue in bounded parallel waves with disk guards."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import threading
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=Path('D:/hackalem-review-work')
PROGRESS=ROOT/'data/judging-progress.json'
EXCLUDED=ROOT/'data/eligibility-exclusions.json'
ORDER=ROOT/'data/judging-order.json'
DOCKER_VHD=Path(os.environ.get('LOCALAPPDATA',''))/'Docker/wsl/disk/docker_data.vhdx'
GIB=1024**3
import importlib.util
_spec=importlib.util.spec_from_file_location('judge_providers',ROOT/'scripts/judge_providers.py')
PROVIDERS=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PROVIDERS)
_account_spec=importlib.util.spec_from_file_location('judge_accounting',ROOT/'scripts/judge_accounting.py')
ACCOUNTING=importlib.util.module_from_spec(_account_spec)
_account_spec.loader.exec_module(ACCOUNTING)
_disk_spec=importlib.util.spec_from_file_location('judge_disk',ROOT/'scripts/judge_disk.py')
DISK=importlib.util.module_from_spec(_disk_spec)
_disk_spec.loader.exec_module(DISK)
MODELS=tuple(j['name'] for j in PROVIDERS.JUDGES)
LABELS=tuple(j['label'] for j in PROVIDERS.JUDGES)
CLEANUP_LABELS=tuple(dict.fromkeys((*LABELS,'luna6','qwen','mimo','longcat','sol','luna')))


def ensure_catalog(quiet=True):
    try:
        result=subprocess.run([sys.executable,'-X','utf8',
                               str(ROOT/'scripts/ensure-local-server.py')],
                              cwd=ROOT,timeout=30,capture_output=quiet,text=quiet)
        if result.returncode:
            print('Local catalog could not be restored; judging state is intact.',
                  result.stderr[-300:] if quiet and result.stderr else '',flush=True)
        return result.returncode == 0
    except (OSError,subprocess.TimeoutExpired) as error:
        print('Local catalog startup failed:',error,flush=True)
        return False

def read(path,default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return default

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(temp,path)

def done(repo_id):
    report=read(ROOT/'web/data/reviews'/f'{repo_id}.json',{})
    return (report.get('methodVersion')==PROVIDERS.METHOD_VERSION
            and {j['model'] for j in report.get('judges',[])}==set(MODELS))

def disk_ok():
    return shutil.disk_usage('C:/').free>=25*GIB and shutil.disk_usage('D:/').free>=50*GIB

def select_batch(remaining,parallel):
    case_id=remaining[0]['caseId']
    return [project for project in remaining if project['caseId']==case_id][:20]

def select_targets(projects,case_id,max_projects,excluded):
    targets=[project for project in projects if case_id is None or project['caseId']==case_id]
    if max_projects:
        targets=[project for project in targets if not done(project['id']) and project['id'] not in excluded][:max_projects]
    return targets


def ordered_projects(catalog, case_order):
    counts={case['id']:case['count'] for case in catalog['cases']}
    if len(case_order)!=len(set(case_order)) or any(case not in counts for case in case_order):
        raise ValueError('Invalid case order: expected unique case IDs from 1 to 12')
    ranks={case:index for index,case in enumerate(case_order)}
    return sorted(catalog['projects'],key=lambda p:(ranks.get(p['caseId'],len(ranks)),
                  counts[p['caseId']],p['caseId'],p['id']))


def record_disk(wave, phase):
    try: DISK.save_snapshot(ROOT,WORK,wave,phase)
    except OSError as error: print('Disk accounting unavailable:',error,flush=True)

def publication_only_unresolved(unresolved,results):
    statuses={(row['repoId'],row['model']):row['status'] for row in results}
    return bool(unresolved) and all(
        statuses.get((repo_id,model)) in ('complete','cached')
        for repo_id in unresolved for model in MODELS)

def compact_docker_vhd_if_needed(force=False):
    """Reclaim physical C: space after Docker cleanup, when the VHD has grown."""
    if os.name!='nt' or not DOCKER_VHD.is_file():
        if force:
            print('Cannot complete mandatory Docker compaction: VHD path unavailable.',flush=True)
            return False
        return True
    free=shutil.disk_usage('C:/').free
    size=DOCKER_VHD.stat().st_size
    if not force and (free>=60*GIB or size<12*GIB):
        return True
    try:
        result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',
                               str(ROOT/'scripts/compact-docker-vhd.ps1')],cwd=ROOT,
                              stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=900)
    except (OSError,subprocess.TimeoutExpired) as error:
        print('Docker disk compaction failed:',error,flush=True)
        return False
    finally:
        # Restore Docker only if the helper's own recovery did not succeed.
        try:
            ready=subprocess.run(['docker','info','--format','{{.ServerVersion}}'],capture_output=True,timeout=15)
            if ready.returncode:
                subprocess.run(['docker','desktop','start','--timeout','180'],capture_output=True,timeout=200)
        except (OSError,subprocess.TimeoutExpired) as error:
            print('Docker recovery startup failed:',error,flush=True)
    if result.returncode:
        print('Docker disk compaction failed. See data/docker-compact.log.',
              result.stderr[-400:],flush=True)
        return False
    after=DOCKER_VHD.stat().st_size
    print(f'Docker VHDX: {size/GIB:.2f} -> {after/GIB:.2f} GiB; '
          f'C: free {shutil.disk_usage("C:/").free/GIB:.2f} GiB.',flush=True)
    for _ in range(18):
        try:
            ready=subprocess.run(['docker','info','--format','{{.ServerVersion}}'],
                                 capture_output=True,timeout=15)
            if ready.returncode==0:
                return True
        except (OSError,subprocess.TimeoutExpired):
            pass
        time.sleep(5)
    print('Docker did not become ready after disk compaction; queue stopped.',flush=True)
    return False

def cleanup_wave_docker(ids,prune_global=True):
    """Remove this wave's containers, images, networks, volumes, and build cache."""
    prefixes=tuple(f'{judge}-{repo_id[5:13]}' for repo_id in ids for judge in CLEANUP_LABELS)
    def docker(*args):
        return subprocess.run(['docker',*args],capture_output=True,text=True,
                              encoding='utf-8',errors='replace',timeout=900)
    def matching(kind,format_string):
        options=['--all'] if kind=='container' else []
        listing=docker(kind,'ls',*options,'--format',format_string)
        if listing.returncode:
            raise RuntimeError(f'Docker {kind} cleanup failed: '+listing.stderr[-200:])
        return [name for name in listing.stdout.splitlines() if name.startswith(prefixes)]
    listing=docker('container','ls','--all','--format','{{json .}}')
    if listing.returncode:
        raise RuntimeError('Docker container cleanup failed: '+listing.stderr[-200:])
    containers=[]
    for line in listing.stdout.splitlines():
        row=json.loads(line)
        if row['Names'].startswith(prefixes):
            containers.append(row['ID'])
            continue
        # docker run without --name produces a random name. Config.Image retains
        # the original judge tag even when that image has since been untagged.
        origin=docker('container','inspect',row['ID'],'--format','{{.Config.Image}}')
        if origin.returncode:
            if 'no such' in origin.stderr.lower(): continue  # Agent already removed it.
            raise RuntimeError('Cannot identify container owner: '+origin.stderr[-200:])
        if origin.stdout.strip().startswith(prefixes):
            containers.append(row['ID'])
    for name in containers:
        result=docker('container','rm','--force','--volumes',name)
        if result.returncode: raise RuntimeError('Judge container retained: '+name+' '+result.stderr[-160:])
    images=matching('image','{{.Repository}}:{{.Tag}}')
    for tag in images:
        result=docker('image','rm','--force',tag)
        if result.returncode: raise RuntimeError('Judge image retained: '+tag+' '+result.stderr[-160:])
    networks=matching('network','{{.Name}}')
    for name in networks:
        result=docker('network','rm',name)
        if result.returncode: raise RuntimeError('Judge network retained: '+name+' '+result.stderr[-160:])
    volumes=matching('volume','{{.Name}}')
    for name in volumes:
        result=docker('volume','rm',name)
        if result.returncode: raise RuntimeError('Judge volume retained: '+name+' '+result.stderr[-160:])
    anonymous=docker('volume','prune','--force') if prune_global else None
    cache=docker('builder','prune','--all','--force') if prune_global else None
    for result in (anonymous,cache):
        if result is not None and result.returncode:
            raise RuntimeError('Docker prune failed: '+result.stderr[-300:])
    if prune_global:
        for args in (('system','prune','--all','--force','--volumes'),('volume','prune','--all','--force')):
            result=docker(*args)
            if result.returncode:
                raise RuntimeError('Full Docker cleanup failed: '+result.stderr[-300:])
        for kind in ('container','image','volume'):
            result=docker(kind,'ls','--quiet',*(['--all'] if kind=='container' else []))
            if result.returncode or result.stdout.strip():
                raise RuntimeError(f'Docker cleanup incomplete: {kind} resources remain. See Docker before restarting the queue.')


def cleanup_wave_worktrees(directory,ids):
    """Delete authorised disposable clones, including unregistered leftovers."""
    base=(WORK/'waves').resolve()
    if directory.resolve().parent != base:
        raise RuntimeError('Wave outside the judge workspace')
    errors=[]
    for repo_id in ids:
        result=subprocess.run([shutil.which('pwsh') or 'powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/cleanup-wave-files.ps1'),
                               '-WavePath',str(directory.resolve()),'-RepoId',repo_id],
                              stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
        if result.returncode:
            errors.append(repo_id+': '+result.stderr[-500:])
    if errors:
        raise RuntimeError('; '.join(errors))


def finish_wave_cleanup(directory,ids):
    """Attempt every stage even if another fails; never claim partial success."""
    errors=[]
    for label,action in (
        ('Docker cleanup',lambda:cleanup_wave_docker(ids)),
        ('Participant files',lambda:cleanup_wave_worktrees(directory,ids)),
        ('Docker compaction/restart',lambda:compact_docker_vhd_if_needed(force=True))):
        try:
            if action() is False:
                errors.append(label+': failed')
        except (OSError,RuntimeError,subprocess.TimeoutExpired) as error:
            errors.append(label+': '+str(error))
    return errors


def main():
    # Hold an OS lock; another queue must not overlap cleanup of active judges.
    lock_path=ROOT/'data/judging-queue.lock'
    lock_path.parent.mkdir(parents=True,exist_ok=True)
    lock_handle=lock_path.open('a+b')
    if os.name=='nt':
        import msvcrt
        lock_handle.seek(0)
        if lock_handle.read(1)==b'': lock_handle.write(b'0'); lock_handle.flush()
        lock_handle.seek(0)
        try: msvcrt.locking(lock_handle.fileno(),msvcrt.LK_NBLCK,1)
        except OSError: raise SystemExit('Another judging queue is already running.')
    parser=argparse.ArgumentParser()
    parser.add_argument('--max-waves',type=int,default=0,help='0 means run until queue is empty')
    parser.add_argument('--parallel',type=int,default=8,help='maximum simultaneous GPT-5.6 Luna reviews')
    parser.add_argument('--reasoning',choices=('medium','high'),default='high',help='medium may be faster; high preserves the previous review effort')
    parser.add_argument('--case',type=int,choices=range(1,13),help='judge only this case, then stop')
    parser.add_argument('--max-projects',type=int,default=0,help='0 means all remaining projects in the selected scope')
    args=parser.parse_args()
    os.environ['HACKALEM_JUDGE_REASONING']=args.reasoning
    if args.parallel < 1:
        parser.error('--parallel must be positive')
    if args.max_projects<0:
        parser.error('--max-projects must be non-negative')
    if args.max_waves<0:
        parser.error('--max-waves must be non-negative')
    for judge in PROVIDERS.JUDGES:
        try: PROVIDERS.check_budget(judge)
        except RuntimeError as error: raise SystemExit(str(error))
    try: PROVIDERS.require_subscription()
    except RuntimeError as error: raise SystemExit(str(error))
    if os.name=='nt':
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            raise SystemExit('Run this command in PowerShell as Administrator: every wave compacts and restarts Docker.')
    ensure_catalog()
    docker_ready=subprocess.run(['docker','info','--format','{{.ServerVersion}}'],capture_output=True)
    if docker_ready.returncode:
        raise SystemExit('Start Docker Desktop before running the judge queue.')
    print(f'Codex / ChatGPT: GPT-5.6 Luna; {args.reasoning}, service tier={PROVIDERS.SERVICE_TIER}. Пачки до 20 проектов.',flush=True)
    catalog=read(ROOT/'web/data/catalog.json',{})
    case_order=read(ORDER,{}).get('caseOrder',[])
    all_order=ordered_projects(catalog,case_order)
    print('Порядок кейсов: '+' -> '.join(map(str,dict.fromkeys(p['caseId'] for p in all_order))),flush=True)
    attempts=read(PROGRESS,{}).get('attempts',{})
    excluded=read(EXCLUDED,{})
    order=select_targets(all_order,args.case,args.max_projects,excluded)
    deferred=set()
    print(f'Selected {sum(not done(p["id"]) and p["id"] not in excluded for p in order)} '
          f'unfinished projects{f" in case {args.case}" if args.case else ""}; '
          f'up to {args.parallel} judges simultaneously.',flush=True)
    wave=0
    while True:
        remaining=[p for p in order if not done(p['id']) and p['id'] not in excluded and p['id'] not in deferred]
        if not remaining or (args.max_waves and wave>=args.max_waves):
            break
        if not compact_docker_vhd_if_needed():
            break
        if not disk_ok():
            print('Stopped: disk guard reached (C <25 GiB or D <50 GiB free)',flush=True)
            break
        batch=select_batch(remaining,args.parallel)
        case_id=batch[0]['caseId']
        wave+=1
        name=f'all-case-{case_id}-wave-{datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")}-{wave}'
        record_disk(name,'before-wave')
        ids=[p['id'] for p in batch]
        print(f'Пачка {wave}: кейс {case_id}, {len(ids)} проектов, до {args.parallel} агентов одновременно.',flush=True)
        command=[sys.executable,'-X','utf8',str(ROOT/'scripts/judge-wave.py'),'--ids',*ids,'--parallel',str(args.parallel),'--wave-name',name]
        directory=WORK/'waves'/name
        cleaned=set()
        interrupted=False
        with subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,encoding='utf-8',errors='replace',bufsize=1) as process:
            def forward_log():
                for line in process.stdout:
                    print(line.rstrip('\n'),flush=True)
            reader=threading.Thread(target=forward_log,daemon=True)
            reader.start()
            deadline=time.monotonic()+max(10800,7200*len(ids)+1200)
            next_catalog_check=time.monotonic()+30
            while process.poll() is None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
                except KeyboardInterrupt:
                    subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                    process.wait()
                    print('Stopped wave and agent process tree. Completed reports remain saved.',flush=True)
                    interrupted=True
                    break
                if time.monotonic()>=next_catalog_check:
                    ensure_catalog(quiet=True)
                    next_catalog_check=time.monotonic()+30
                partial=read(directory/'results.json',[])
                for repo_id in ids:
                    if repo_id in cleaned:
                        continue
                    statuses={row['model']:row['status'] for row in partial if row['repoId']==repo_id}
                    if all(statuses.get(model) in ('complete','cached') for model in MODELS):
                        try:
                            cleanup_wave_docker([repo_id],prune_global=False)
                            cleanup_wave_worktrees(directory,[repo_id])
                        except (OSError,RuntimeError,subprocess.TimeoutExpired) as error:
                            print('Очистка проекта отложена до конца пачки:',repo_id,error,flush=True)
                        cleaned.add(repo_id)
                if time.monotonic()>=deadline and process.poll() is None:
                    subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                    print('Judge wave timed out.',flush=True)
            exit_code=process.returncode
            reader.join(timeout=10)
        prepared=read(directory/'prepared.json',[])
        results=read(directory/'results.json',[])
        limited_ids={row['repoId'] for row in results if row.get('status')=='rate_limited'}
        for row in prepared:
            if row.get('eligible') is False and not row.get('error'):
                excluded[row['repoId']]={'reason':row.get('reason','No commit in hackathon window'),'wave':name}
                for field in ('reviewStatus','firstSolutionCommit','firstSolutionCommitAt','deadlineUtc'):
                    if field in row: excluded[row['repoId']][field]=row[field]
        write(EXCLUDED,excluded)
        for repo_id in ids:
            if not done(repo_id) and repo_id not in excluded and not limited_ids:
                attempts[repo_id]=attempts.get(repo_id,0)+1
        publish=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/publish-reviews.py')],cwd=ROOT,
                               capture_output=True,text=True,encoding='utf-8',errors='replace')
        bundle_ok=False
        if publish.returncode==0:
            bundle=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/prepare-pages.py')],cwd=ROOT,
                                  capture_output=True,text=True,encoding='utf-8',errors='replace')
            bundle_ok=bundle.returncode==0
        unresolved=[repo_id for repo_id in ids if not done(repo_id) and repo_id not in excluded]
        state={'methodVersion':PROVIDERS.METHOD_VERSION,'total':len(all_order),'completed':sum(done(p['id']) for p in all_order),
               'excludedByCommitWindow':len(excluded),'attempts':attempts,
               'lastWave':name,'lastWaveExitCode':exit_code,
               'lastWaveUnpublished':unresolved,
               'rateLimited':bool(limited_ids),
               'updatedAt':datetime.now(timezone.utc).isoformat()}
        write(PROGRESS,state)
        cleanup_errors=finish_wave_cleanup(directory,ids)
        record_disk(name,'after-cleanup')
        cleanup_ok=not cleanup_errors
        for error in cleanup_errors: print('ОШИБКА очистки:',error,flush=True)
        site_ok=ensure_catalog()
        state.update(cleanupSucceeded=cleanup_ok,siteHealthy=site_ok,bundleReady=bundle_ok)
        write(PROGRESS,state)
        print(f'Пачка {wave} завершена: готово {sum(done(r) for r in ids)}/{len(ids)}; '
              f'в каталоге {state["completed"]}/{state["total"]}. '
              f'D: и Docker {"очищены, диск сжат, Docker снова запущен" if cleanup_ok else "ОЧИСТКА НЕ ЗАВЕРШЕНА"}. '
              f'Сайт {"доступен" if site_ok else "недоступен"}; копия docs {"обновлена" if bundle_ok else "не обновлена"}.',flush=True)
        ACCOUNTING.save_and_print(ROOT,PROVIDERS,name)
        if not cleanup_ok or interrupted:
            break
        if limited_ids:
            print('Provider limit reached. Queue stopped without consuming retry attempts; '
                  'rerun this command later to continue from the first unfinished project.',flush=True)
            break
        if unresolved:
            if publication_only_unresolved(unresolved,results):
                deferred.update(unresolved)
                print('Reports need publication repair:',', '.join(unresolved),
                      'Continuing with other projects in the selected queue.',flush=True)
                continue
            deferred.update(unresolved)
            print('Deferred unfinished projects:',', '.join(unresolved),
                  'Saved for the next launch. Continuing with the rest of the queue.',flush=True)
            continue
    print('Judge queue stopped. Remaining in selected scope:',
          sum(not done(p['id']) and p['id'] not in excluded for p in order),flush=True)
    ensure_catalog()

if __name__=='__main__':
    log_dir=ROOT/'data/queue-logs'
    log_dir.mkdir(parents=True,exist_ok=True)
    log_path=log_dir/f'{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")}.log'
    with log_path.open('a',encoding='utf-8') as log:
        original_out,original_err=sys.stdout,sys.stderr
        sys.stdout=ACCOUNTING.Tee(original_out,log)
        sys.stderr=ACCOUNTING.Tee(original_err,log)
        try:
            print('Журнал:',log_path,flush=True)
            main()
        finally:
            sys.stdout,sys.stderr=original_out,original_err
