"""Portable review kit. No model calls; no participant code is executed here."""
import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(Path(__file__).resolve().parent))
START=datetime.fromisoformat('2026-09-23T08:00:00+00:00')
END=datetime.fromisoformat('2026-09-23T13:00:00+00:00')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'),parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Non-finite JSON number: '+value)))


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)


def projects():
    return {p['id']:p for p in read(ROOT/'inventory/repos.json')}


def project(repo_id):
    if not re.fullmatch(r'hack-[A-Za-z0-9_-]+',repo_id):raise ValueError('Invalid repository ID')
    return projects()[repo_id]


def evidence(repo_id):return ROOT/'results/evidence'/repo_id


def git(*args,cwd=None,timeout=600,input=None):
    result=subprocess.run(['git',*args],cwd=cwd,input=input.encode() if input is not None else None,
        capture_output=True,timeout=timeout,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
    if result.returncode:raise RuntimeError(result.stderr.decode('utf-8',errors='replace')[-2000:])
    return result.stdout.decode('utf-8',errors='replace').strip()


def prepare(repo_id):
    p=project(repo_id);folder=evidence(repo_id);folder.mkdir(parents=True,exist_ok=True)
    url='https://github.com/BAITC-Hacks/'+repo_id
    if p['url']!=url:raise ValueError('Repository URL does not match inventory')
    clone=ROOT/'work/clones'/repo_id
    clone.parent.mkdir(parents=True,exist_ok=True)
    if not (clone/'.git').exists():
        git('clone','--filter=blob:none','--no-checkout','--no-single-branch',url+'.git',str(clone),timeout=1800)
    refs=git('for-each-ref','--format=%(refname:short)','refs/remotes/origin/',cwd=clone).splitlines()
    refs=[r for r in refs if r!='origin/HEAD']
    if not refs:raise ValueError('No branch refs fetched; preparation is incomplete, not a zero-score project')
    pinned=read(ROOT/'inventory/snapshots.json').get(repo_id)
    if pinned:
        branches=pinned['branches'];selected=pinned['defaultSnapshot']
    else:
        branches=[]
        for ref in refs:
            # Filter a complete history walk; do not terminate early on an
            # incorrectly ordered timestamp in an ancestor.
            for line in git('log','--format=%H%x1f%cI',ref,cwd=clone).splitlines():
                sha,instant=line.split('\x1f')
                if datetime.fromisoformat(instant.replace('Z','+00:00'))<=END:
                    branches.append({'name':ref.removeprefix('origin/'),'commit':sha});break
        preferred=next((b for b in branches if b['name']==p['defaultBranch']),None)
        if not preferred and branches:
            preferred=max(branches,key=lambda b:git('show','-s','--format=%cI',b['commit'],cwd=clone))
        selected=preferred['commit'] if preferred else None
    override=read(ROOT/'inventory/snapshot-overrides.json').get(repo_id)
    if override:
        stamp=datetime.fromisoformat(override['evidence']['pushedAt'].replace('Z','+00:00'))
        if stamp>END or not override['evidence']['archived']:raise ValueError('Invalid audited push evidence')
        selected=override['snapshot']
        branches=[b for b in branches if b['name']!=override['branch']]+[{'name':override['branch'],'commit':selected}]
    for branch in branches:
        sha=branch['commit']
        if not re.fullmatch(r'[a-f0-9]{40}',sha):raise ValueError('Invalid snapshot SHA')
        try:git('cat-file','-e',sha+'^{commit}',cwd=clone)
        except RuntimeError:git('fetch','--filter=blob:none','origin',sha,cwd=clone,timeout=1800)
    manifest={'repoId':repo_id,'caseId':p['caseId'],'repoUrl':url,'deadlineUtc':END.isoformat(),
        'defaultSnapshot':selected,'branches':branches,'preparedAt':datetime.now(timezone.utc).isoformat(),
        'snapshotTimeEvidence':override,'selectionBasis':'pinned' if pinned else 'git-history'}
    if not selected:
        write(folder/'snapshot.json',manifest)
        raise ValueError('No pre-deadline snapshot: investigate timing; do not invent a code assessment')
    history=git('log','--format=%H%x1f%cI%x1f%aN',*[b['commit'] for b in branches],cwd=clone)
    manifest['windowCommits']=[]
    for line in history.splitlines():
        sha,instant,author=line.split('\x1f',2)
        if START<=datetime.fromisoformat(instant.replace('Z','+00:00'))<=END:
            manifest['windowCommits'].append({'sha':sha,'time':instant,'author':author})
    names=git('ls-tree','-r','--name-only',selected,cwd=clone).splitlines()
    manifest['fileCount']=len(names)
    write(folder/'snapshot.json',manifest)
    (folder/'git-history.log').write_text(history,encoding='utf-8')
    (folder/'files.txt').write_text('\n'.join(names)+'\n',encoding='utf-8')
    from judge_checkout import hydrate_snapshot,create_checkout
    hydrate_snapshot(clone,selected,git)
    checkout=ROOT/'work/checkouts'/repo_id/'source'
    checkout.parent.mkdir(parents=True,exist_ok=True)
    if os.name=='nt':create_checkout(clone,checkout,selected,git)
    elif not checkout.exists():git('worktree','add','--detach',str(checkout),selected,cwd=clone,timeout=1800)
    elif git('rev-parse','HEAD',cwd=checkout)!=selected:raise ValueError('Existing checkout has a different snapshot')
    print(json.dumps({'repoId':repo_id,'snapshot':selected,'checkout':str(checkout),'files':len(names)},ensure_ascii=False))
    if not manifest['windowCommits'] and not override:
        print('TIME_REVIEW_REQUIRED: no commits in the hackathon window; check decision rules before scoring.')


def prompt(repo_id,model):
    p=project(repo_id);manifest=read(evidence(repo_id)/'snapshot.json')
    if not manifest.get('defaultSnapshot'):raise ValueError('No eligible snapshot prepared')
    source=(ROOT/'instructions/review-template.txt').read_text(encoding='utf-8')
    filelist=(evidence(repo_id)/'files.txt').read_text(encoding='utf-8').splitlines()
    source=source.format(model=model,repo_url=p['url'],repo_id=repo_id,
        checkout=f'work/checkouts/{repo_id}/source',snapshot=manifest['defaultSnapshot'],
        manifest=f'results/evidence/{repo_id}/snapshot.json',global_criteria='criteries.md',case_id=p['caseId'],
        task_file=f'cases/{p["caseId"]}/task.txt',case_dir=f'cases/{p["caseId"]}/case-data',
        case_brief=(ROOT/f'case-briefs/{p["caseId"]:02}.md').read_text(encoding='utf-8'),
        dossier='Инвентаризация Git; не оценка. Полный список: results/evidence/'+repo_id+'/files.txt\n'+'\n'.join(filelist[:160]),
        capture_tool='tools/check.py',capture_dir=f'results/evidence/{repo_id}',
        api_requirements='Ключи не предоставлены. Установи требования и альтернативы по исходникам; никаких штрафов за отсутствие наших ключей.',
        resource_prefix='review-'+repo_id[5:13])
    override=manifest.get('snapshotTimeEvidence')
    if override:
        source=('ПРОВЕРЕННАЯ ПОПРАВКА: GitHub последний push '+override['evidence']['pushedAt']+
            ', репозиторий архивирован; указанный полный SHA был загружен до дедлайна. '
            'Локальные часы Git с -07:00 некорректны. Не откатывай код к раннему README.\n\n')+source
    path_map=ROOT/'work/checkouts'/repo_id/'source-paths.json'
    if path_map.exists():
        source+='\nВ Windows часть имён экранирована: прочитай work/checkouts/'+repo_id+'/source-paths.json. '
        source+='Для runtime распакуй исходный tar из этой карты в Linux-контейнер; не штрафуй за ограничения имён Windows.\n'
    source+='\nСохрани JSON в results/reports/'+repo_id+'.json. Схема: schemas/report.schema.json. '
    source+='Реальное имя модели: '+model+'. Если платформа его не раскрывает, используй Model not disclosed; не угадывай.\n'
    source+='Проверь: python tools/kit.py validate --repo '+repo_id+'. Исправляй ошибки формата по фактам, не подгоняй оценки.\n'
    path=evidence(repo_id)/'judge-prompt.txt';path.write_text(source,encoding='utf-8');print(path)


def validate_report(path):
    import jsonschema
    from review_policy import validate_report_policy
    report=read(path);p=project(report['repoId'])
    jsonschema.validate(report,read(ROOT/'schemas/report.schema.json'))
    if path.name!=p['id']+'.json' or report['caseId']!=p['caseId']:raise ValueError('Report identity mismatch')
    manifest=read(evidence(p['id'])/'snapshot.json')
    permitted={b['commit'] for b in manifest['branches']}
    if report['snapshot'] not in permitted:raise ValueError('Snapshot not in audited branch manifest')
    validate_report_policy(report,require_current=True,publication=True)
    weights=read(ROOT/'inventory/rubrics.json')[str(p['caseId'])]
    for name,expected in [('global',[25,20,15,20,20]),('case',weights)]:
        scale=report[name]
        if expected is None:
            if scale is not None:raise ValueError('Case has no official scoring scale')
            continue
        if scale is None or [r['max'] for r in scale['criteria']]!=expected:raise ValueError(name+': invalid weights')
        if any(not 0<=r['score']<=r['max'] for r in scale['criteria']):raise ValueError(name+': out-of-range score')
        if abs(sum(r['score'] for r in scale['criteria'])-scale['total'])>0.01:raise ValueError(name+': incorrect total')
    total=(report['global']['total']+report['case']['total'])/2 if report['case'] else report['global']['total']
    if abs(total-report['judgeScore'])>0.01:raise ValueError('Incorrect judgeScore')
    ledger=evidence(p['id'])/'checks.jsonl'
    checks={r['id']:r for r in (json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines())} if ledger.exists() else {}
    for check in report['runtime']['checks']:
        if check['status'] in ('pass','fail'):
            if check['id'] not in checks:raise ValueError('No execution log for '+check['id']+'; use tools/check.py --check-id')
            record=checks[check['id']]
            if check['status']=='pass' and (record.get('timedOut') or record['exitCode']!=0):raise ValueError('Pass contradicts execution log: '+check['id'])
            for key in ('stdout','stderr'):
                log=(ROOT/'results'/record[key]).resolve()
                if not log.is_relative_to((ROOT/'results').resolve()) or not log.is_file():raise ValueError('Missing/unsafe log path')
    return report


def validate_decision(path):
    import jsonschema
    row=read(path);p=project(row['repoId'])
    jsonschema.validate(row,read(ROOT/'schemas/decision.schema.json'))
    if path.name!=p['id']+'.json' or row['caseId']!=p['caseId']:raise ValueError('Decision identity mismatch')
    if row['status']=='disqualified':
        if row['reasonCode']=='late_submission':
            if datetime.fromisoformat(row['firstSolutionCommitAt'].replace('Z','+00:00'))<=END:raise ValueError('Solution is not late')
        elif row['reasonCode']=='no_commits':
            if row.get('windowCommitCount')!=0 or row.get('allBranchesChecked') is not True:raise ValueError('No-commits decision lacks full branch check')
    return row


def finalize(destination,scope=None):
    inventory=projects();allowed={p['id'] for p in inventory.values() if scope is None or p['caseId']==scope}
    if not allowed:raise ValueError('Requested scope contains no projects')
    rows=[];errors=[]
    for repo_id in sorted(allowed):
        report=ROOT/'results/reports'/f'{repo_id}.json';decision=ROOT/'results/decisions'/f'{repo_id}.json'
        try:
            if report.exists() and decision.exists():raise ValueError('Conflicting report and decision')
            if report.exists():
                r=validate_report(report);rows.append({'repoId':repo_id,'caseId':r['caseId'],'status':'reviewed','model':r['model'],'score':r['judgeScore'],'file':f'reports/{repo_id}.json'})
            elif decision.exists():
                r=validate_decision(decision);rows.append({'repoId':repo_id,'caseId':r['caseId'],'status':r['status'],'file':f'decisions/{repo_id}.json'})
            else:rows.append({'repoId':repo_id,'caseId':inventory[repo_id]['caseId'],'status':'pending'})
        except Exception as error:
            errors.append(repo_id+': '+str(error));rows.append({'repoId':repo_id,'caseId':inventory[repo_id]['caseId'],'status':'invalid'})
    unexpected=[]
    for kind in ('reports','decisions'):
        for path in (ROOT/'results'/kind).glob('*.json'):
            if path.stem not in inventory:unexpected.append(str(path.relative_to(ROOT/'results')))
    errors.extend('Unknown repository file: '+name for name in unexpected)
    counts={status:sum(r['status']==status for r in rows) for status in ['reviewed','disqualified','blocked','pending','invalid']}
    complete=not errors and counts['reviewed']+counts['disqualified']==len(allowed)
    manifest={'format':'hackalem-external-reviews-v1','source':'external-agent','createdAt':datetime.now(timezone.utc).isoformat(),
        'scopeCaseId':scope,'expectedProjects':len(allowed),'complete':complete,'counts':counts,'projects':rows,'errors':errors}
    write(ROOT/'results/manifest.json',manifest)
    summary='\n'.join([f'Expected: {len(allowed)}',f'Complete: {complete}',*['%s: %s'%item for item in counts.items()],*errors])+'\n'
    (ROOT/'results/SUMMARY.txt').write_text(summary,encoding='utf-8')
    if destination.is_relative_to(ROOT/'results'):raise ValueError('ZIP must be outside results/')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for path in sorted((ROOT/'results').rglob('*')):
            if not path.is_file() or path.is_symlink() or path.suffix=='.tmp':continue
            rel=path.relative_to(ROOT/'results')
            if rel.parts[0] in ('reports','decisions') and path.stem not in allowed:continue
            if rel.parts[0]=='evidence' and len(rel.parts)>1 and rel.parts[1] not in allowed:continue
            out.write(path,rel.as_posix())
    print(summary+str(destination))
    return complete


def main():
    parser=argparse.ArgumentParser();commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('list').add_argument('--case',type=int)
    p=commands.add_parser('prepare');p.add_argument('--repo',required=True)
    p=commands.add_parser('prompt');p.add_argument('--repo',required=True);p.add_argument('--model',default='Model not disclosed')
    p=commands.add_parser('validate');p.add_argument('--repo',required=True)
    p=commands.add_parser('finalize');p.add_argument('--case',type=int);p.add_argument('--output',default='review-results.zip')
    args=parser.parse_args()
    if args.command=='list':
        for p in sorted(projects().values(),key=lambda p:(p['caseId'],p['id'])):
            if args.case is None or p['caseId']==args.case:print(p['caseId'],p['id'],p['name'],p['url'],sep='\t')
    elif args.command=='prepare':prepare(args.repo)
    elif args.command=='prompt':prompt(args.repo,args.model)
    elif args.command=='validate':
        project(args.repo);p=ROOT/'results/reports'/f'{args.repo}.json'
        if p.exists():validate_report(p)
        else:validate_decision(ROOT/'results/decisions'/f'{args.repo}.json')
        print('REPORT_VALID')
    elif args.command=='finalize':
        if not finalize(Path(args.output).resolve(),args.case):return 2
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as error:print('KIT_ERROR:',error,file=sys.stderr);sys.exit(1)
