"""One-off reviews at a case boundary, loaded by fresh wave subprocesses."""
import json
import subprocess
import sys
from datetime import datetime, timezone


def due(request, projects, ids, wave_name):
    return (request.get('status')=='pending' and wave_name.startswith('all-case-')
            and bool(ids) and all(projects[i]['caseId']==request.get('beforeCase') for i in ids)
            and request.get('repoId') in projects and request['repoId'] not in ids)


def run(root,work,projects,ids,wave_name,queue):
    path=root/'data/judging-priority.json'
    document=queue.read(path,{})
    requests=document.get('requests',[document])
    for request in requests:
        if due(request,projects,ids,wave_name):
            if run_request(root,work,request,queue,lambda:queue.write(path,document)):
                return True
    return False


def run_request(root,work,request,queue,save):
    repo_id=request['repoId']
    if queue.done(repo_id):
        request.update(status='complete',note='Already published')
        save()
        return False
    name='priority-'+repo_id+'-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    request.update(status='running',wave=name,startedAt=datetime.now(timezone.utc).isoformat())
    save()
    print(f'Приоритетная проверка после кейса {request["afterCase"]}: {repo_id}. Следующий кейс начнётся после неё.',flush=True)
    directory=work/'waves'/name
    result=None
    errors=[]
    try:
        result=subprocess.run([sys.executable,'-X','utf8',str(root/'scripts/judge-wave.py'),
            '--ids',repo_id,'--parallel','1','--wave-name',name,'--skip-priority'],cwd=root)
        published=subprocess.run([sys.executable,'-X','utf8',str(root/'scripts/publish-reviews.py')],cwd=root)
        if published.returncode==0:
            bundled=subprocess.run([sys.executable,'-X','utf8',str(root/'scripts/prepare-pages.py')],cwd=root)
            if bundled.returncode: errors.append('Site bundle failed')
        else: errors.append('Publication failed')
    except OSError as error:
        errors.append(str(error))
    finally:
        errors.extend(queue.finish_wave_cleanup(directory,[repo_id]))
    results=queue.read(directory/'results.json',[])
    limited=any(row.get('status')=='rate_limited' for row in results)
    request.update(status='complete' if queue.done(repo_id) and not errors else 'failed',
        finishedAt=datetime.now(timezone.utc).isoformat(),exitCode=result.returncode if result else None,
        errors=errors,results=results)
    save()
    print(f'Приоритетная проверка {repo_id}: {request["status"]}.',flush=True)
    return limited
