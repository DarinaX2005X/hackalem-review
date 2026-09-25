"""Fetch directory names and linked README files only for ambiguous projects."""
import concurrent.futures
import html
import json
import pathlib
import re
import urllib.parse
from classify import DATA, fetch_text, load, write

DEST=DATA/'discovery'
DEST.mkdir(exist_ok=True)

def page_info(repo, path=''):
    branch=repo['default_branch']
    url=f'https://github.com/{repo["full_name"]}'
    if path:url+='/tree/'+urllib.parse.quote(branch,safe='')+'/'+urllib.parse.quote(path)
    text,error=fetch_text(url)
    if text is None:return {'url':url,'error':error}
    items=[]
    for match in re.finditer(r'<script\b[^>]*type="application/json"[^>]*>(.*?)</script>',text,re.S):
        try:obj=json.loads(match.group(1))
        except Exception:continue
        def walk(value):
            if isinstance(value,dict):
                if isinstance(value.get('items'),list):
                    for item in value['items']:
                        if isinstance(item,dict) and 'path' in item and 'contentType' in item:
                            items.append({k:item.get(k) for k in ('name','path','contentType')})
                for v in value.values():walk(v)
            elif isinstance(value,list):
                for v in value:walk(v)
        walk(obj)
    unique={i['path']:i for i in items}
    return {'url':url,'items':list(unique.values())}

def enrich(repo):
    dest=DEST/(repo['name']+'.json')
    if dest.exists():return load(dest)
    root=page_info(repo)
    readme=load(DATA/'readmes'/(repo['name']+'.json'),{})
    links=re.findall(r'\]\(([^)\s]+\.md)(?:#[^)]*)?\)',readme.get('text',''),re.I)
    paths=set(p.lstrip('./') for p in links if '://' not in p and '..' not in p)
    items=root.get('items',[])
    for item in items:
        if re.search(r'readme',item['name'],re.I):paths.add(item['path'])
    if len(readme.get('text',''))<600:
        dirs=[i['path'] for i in items if i['contentType']=='directory' and not i['name'].startswith('.') and i['name'] not in ('node_modules','assets','public','static','images','data','venv')]
        for folder in dirs[:7]:paths.add(folder+'/README.md')
    docs=[]
    for path in sorted(paths)[:12]:
        url=f'https://raw.githubusercontent.com/{repo["full_name"]}/{urllib.parse.quote(repo["default_branch"],safe="")}/{urllib.parse.quote(path)}'
        text,error=fetch_text(url)
        if text is not None:docs.append({'path':path,'text':text,'url':url})
    result={'repo':repo['name'],'root':root,'docs':docs}
    write(dest,result)
    return result

if __name__=='__main__':
    unresolved={x['repo'] for x in load(DATA/'unresolved.json')}
    rows=[x for x in load(DATA/'participants.json') if x['name'] in unresolved]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for n,r in enumerate(pool.map(enrich,rows),1):
            if n%25==0 or n==len(rows):print(f'Discovery {n}/{len(rows)}',flush=True)
