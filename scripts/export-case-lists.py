import json,csv,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'web/data/catalog.json').read_text(encoding='utf-8'))
dest=ROOT/'data/by-case'
dest.mkdir(exist_ok=True)
for case in data['cases']:
    projects=[{'repository':p['id'],'team':p['name'],'url':p['url'],'caseId':p['caseId'],'readmeUrl':p['readmeUrl']} for p in data['projects'] if p['caseId']==case['id']]
    (dest/f'{case["id"]:02d}.json').write_text(json.dumps({'case':case['title'],'subtitle':case['subtitle'],'projects':projects},ensure_ascii=False,indent=2),encoding='utf-8')
print('12 case lists exported')
