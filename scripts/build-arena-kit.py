"""Build a portable, credential-free archive and twelve case-sized alternatives."""
import importlib.util
import json
import shutil
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'exports/hackalem-review-kit-2026-10-01'
KIT=DEST/'hackalem-review-kit'


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def decision_schema():
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object','additionalProperties':False,
        'required':['repoId','caseId','status','reasonCode','reason','evidence'],
        'properties':{'repoId':{'type':'string'},'caseId':{'type':'integer','minimum':1,'maximum':12},
            'status':{'enum':['blocked','disqualified']},'reasonCode':{'enum':['review_environment','timing_unresolved','insufficient_evidence','late_submission','no_commits']},
            'reason':{'type':'string','minLength':20},'evidence':{'type':'array','minItems':1,'items':{'type':'string','minLength':1}},
            'score':{'const':0},'model':{'type':'string','minLength':1},
            'firstSolutionCommit':{'type':'string','pattern':'^[a-f0-9]{40}$'},'firstSolutionCommitAt':{'type':'string'},
            'allBranchesChecked':{'const':True},'windowCommitCount':{'const':0}},
        'allOf':[
            {'if':{'properties':{'status':{'const':'disqualified'}}},'then':{'required':['score','allBranchesChecked'],'properties':{'reasonCode':{'enum':['late_submission','no_commits']}}},
             'else':{'not':{'required':['score']},'properties':{'reasonCode':{'enum':['review_environment','timing_unresolved','insufficient_evidence']}}}},
            {'if':{'properties':{'reasonCode':{'const':'late_submission'}}},'then':{'required':['firstSolutionCommit','firstSolutionCommitAt']}},
            {'if':{'properties':{'reasonCode':{'const':'no_commits'}}},'then':{'required':['windowCommitCount']}}
        ]}


def build():
    catalog=json.loads((ROOT/'web/data/catalog.json').read_text(encoding='utf-8'))
    inventory=[{k:p.get(k) for k in ('id','name','url','caseId','defaultBranch','product')} for p in catalog['projects']]
    inventory.sort(key=lambda p:(p['caseId'],p['id']))
    ids={p['id'] for p in inventory}
    KIT.mkdir(parents=True,exist_ok=True)
    for name in ('START_HERE.txt','PASTE_PROMPT.txt','FORMAT.txt'):
        shutil.copyfile(ROOT/'scripts/arena-kit'/name,KIT/name)
    for name in ('kit.py','check.py'):
        (KIT/'tools').mkdir(exist_ok=True)
        shutil.copyfile(ROOT/'scripts/arena-kit'/name,KIT/'tools'/name)
    for name in ('review_policy.py','judge_checkout.py'):
        shutil.copyfile(ROOT/'scripts'/name,KIT/'tools'/name)
    shutil.copyfile(ROOT/'criteries.md',KIT/'criteries.md')
    (KIT/'requirements.txt').write_text('jsonschema>=4.18,<5\n',encoding='utf-8')
    shutil.copytree(ROOT/'cases',KIT/'cases',dirs_exist_ok=True)
    shutil.copytree(ROOT/'case-briefs',KIT/'case-briefs',dirs_exist_ok=True)
    schema=json.loads((ROOT/'scripts/judge-report.schema.json').read_text(encoding='utf-8'))
    schema['properties']['model']={'type':'string','minLength':1,'maxLength':200,
        'description':'Actual external model identity; Model not disclosed if hidden. Do not impersonate another model.'}
    schema['properties']['snapshot']={'type':'string','pattern':'^[a-f0-9]{40}$'}
    write(KIT/'schemas/report.schema.json',schema)
    write(KIT/'schemas/decision.schema.json',decision_schema())
    write(KIT/'inventory/repos.json',inventory)
    write(KIT/'inventory/cases.json',[{k:c[k] for k in ('id','title','subtitle','owner','count')} for c in catalog['cases']])
    write(KIT/'inventory/case-order.json',json.loads((ROOT/'data/judging-order.json').read_text())['caseOrder'])
    snapshots={}
    for path in (ROOT/'data/judging').glob('*/source-manifest.json'):
        row=json.loads(path.read_text(encoding='utf-8'));rid=path.parent.name
        if rid in ids:
            snapshots[rid]={k:row[k] for k in ('defaultSnapshot','branches','deadlineUtc')}
    write(KIT/'inventory/snapshots.json',snapshots)
    write(KIT/'inventory/snapshot-overrides.json',json.loads((ROOT/'data/snapshot-overrides.json').read_text(encoding='utf-8')))
    decisions=json.loads((ROOT/'data/eligibility-exclusions.json').read_text(encoding='utf-8'))
    write(KIT/'inventory/known-decisions.json',{rid:{k:v for k,v in row.items() if k!='wave'} for rid,row in decisions.items() if rid in ids})
    spec=importlib.util.spec_from_file_location('publish_reviews',ROOT/'scripts/publish-reviews.py')
    publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)
    write(KIT/'inventory/rubrics.json',publisher.CASE_MAX)
    template=(ROOT/'scripts/judge-prompt.txt').read_text(encoding='utf-8')
    template=template.replace('--label build -- <команда>','--label build --check-id BUILD-1 -- <команда>')
    template=template.replace('label замени на start/test при необходимости','label и check-id меняй для каждой отдельной проверки; ID должен совпадать с runtime.checks.id')
    # Templates retain constraints and evidence standards, not local agent paths.
    (KIT/'instructions').mkdir(exist_ok=True)
    (KIT/'instructions/review-template.txt').write_text(template,encoding='utf-8')
    for case in catalog['cases']:
        selected=[p for p in inventory if p['caseId']==case['id']]
        write(KIT/f'repo-lists/case-{case["id"]:02}.json',selected)
        (KIT/f'repo-lists/case-{case["id"]:02}.txt').write_text('\n'.join([
            f'Кейс {case["id"]}: {case["title"]} — {case["subtitle"]}',f'Проектов: {len(selected)}','',
            *[f'{i:03}. {p["name"]}\n     {p["id"]}\n     {p["url"]}' for i,p in enumerate(selected,1)]])+'\n',encoding='utf-8')
    write(KIT/'package.json',{'format':'hackalem-review-kit-v1','createdAt':datetime.now(timezone.utc).isoformat(),
        'expectedProjects':len(inventory),'cases':len(catalog['cases']),'containsPriorScores':False,'containsRepositorySources':False})
    files=[p for p in KIT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'
        and p.relative_to(KIT).parts[0] not in ('results','work')]
    full=DEST/'hackalem-all-1053.zip'
    with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in files:archive.write(path,path.relative_to(KIT).as_posix())
    chunks=DEST/'by-case';chunks.mkdir(exist_ok=True)
    for case in catalog['cases']:
        case_id=case['id'];selected=[p for p in inventory if p['caseId']==case_id];selected_ids={p['id'] for p in selected}
        with zipfile.ZipFile(chunks/f'case-{case_id:02}.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for path in files:
                rel=path.relative_to(KIT)
                if rel.parts[0]=='cases' and rel.parts[1]!=str(case_id):continue
                if rel.parts[0]=='case-briefs' and rel.name!=f'{case_id:02}.md':continue
                if rel.parts[0]=='repo-lists' and not rel.name.startswith(f'case-{case_id:02}.'):continue
                if rel.as_posix()=='inventory/repos.json':value=selected
                elif rel.as_posix()=='inventory/snapshots.json':value={k:v for k,v in snapshots.items() if k in selected_ids}
                elif rel.as_posix()=='inventory/snapshot-overrides.json':value={k:v for k,v in json.loads(path.read_text()).items() if k in selected_ids}
                elif rel.as_posix()=='inventory/known-decisions.json':value={k:v for k,v in json.loads(path.read_text()).items() if k in selected_ids}
                elif rel.as_posix()=='inventory/case-order.json':value=[case_id]
                elif rel.as_posix()=='inventory/cases.json':value=[{k:case[k] for k in ('id','title','subtitle','owner','count')}]
                elif rel.name=='package.json':value={'format':'hackalem-review-kit-v1','expectedProjects':len(selected),'caseId':case_id}
                else:archive.write(path,rel.as_posix());continue
                archive.writestr(rel.as_posix(),json.dumps(value,ensure_ascii=False,indent=2))
    print(json.dumps({'archive':str(full),'MiB':round(full.stat().st_size/1024**2,2),'repositories':len(inventory),
        'materialFiles':len(list((ROOT/'cases').rglob('*'))),'pinnedSnapshots':len(snapshots),'caseArchives':12},ensure_ascii=False))


if __name__=='__main__':build()
