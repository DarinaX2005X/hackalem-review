"""Read the public GitHub contributors summary; never clone a repository."""
import concurrent.futures
import json
import pathlib
import time
import threading
import urllib.error
import urllib.request
from github_api import credential,request

ROOT=pathlib.Path(__file__).resolve().parents[1]
DEST=ROOT/'data'/'contributors'
DEST.mkdir(exist_ok=True)
STOP=threading.Event()
TOKEN=None

def get(repo):
    if STOP.is_set():return 'skipped'
    path=DEST/(repo['name']+'.json')
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old.get('status')=='complete':return 'cached'
    url=f'https://api.github.com/repos/{repo["full_name"]}/contributors?anon=true&per_page=100'
    try:
        if not TOKEN:return 'no_credentials'
        content=[]
        for page in range(1,30):
            items=request(f'repos/{repo["full_name"]}/contributors?anon=true&per_page=100&page={page}',token=TOKEN)
            if not isinstance(items,list):return 'unexpected'
            content.extend(items)
            if len(items)<100:break
        if not isinstance(content,list):return 'unexpected'
        result={'status':'complete','source':url,'contributors':[{'login':c.get('login'),'name':c.get('name'),'id':c.get('id'),'type':c.get('type'),'total':c.get('contributions')} for c in content]}
        path.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
        return 'complete'
    except urllib.error.HTTPError as e:
        if e.code in (403,429):STOP.set()
        return str(e.code)
    except Exception:
        return 'error'

if __name__=='__main__':
    TOKEN=credential()
    rows=json.loads((ROOT/'data'/'participants.json').read_text(encoding='utf-8'))
    for round in range(4):
        counts={}
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for result in pool.map(get,rows):counts[result]=counts.get(result,0)+1
        print(json.dumps({'round':round+1,**counts}),flush=True)
        if counts.get('pending',0)==0:break
        if counts.get('403',0)>10 or counts.get('429',0)>0:break
        time.sleep(20)
