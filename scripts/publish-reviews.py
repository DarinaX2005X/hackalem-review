"""Validate independent reports before exposing a completed review to the site."""

import json
import re
from pathlib import Path
import importlib.util
import jsonschema
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
_policy_spec = importlib.util.spec_from_file_location('review_policy', ROOT/'scripts/review_policy.py')
POLICY = importlib.util.module_from_spec(_policy_spec)
_policy_spec.loader.exec_module(POLICY)
_provider_spec = importlib.util.spec_from_file_location('judge_providers', ROOT/'scripts/judge_providers.py')
PROVIDERS = importlib.util.module_from_spec(_provider_spec)
_provider_spec.loader.exec_module(PROVIDERS)
_snapshot_spec=importlib.util.spec_from_file_location('judge_snapshot',ROOT/'scripts/judge_snapshot.py')
SNAPSHOT=importlib.util.module_from_spec(_snapshot_spec)
_snapshot_spec.loader.exec_module(SNAPSHOT)
SOURCE = ROOT / 'data/judging'
TARGET = ROOT / 'web/data/reviews'
catalog = json.loads((ROOT / 'web/data/catalog.json').read_text(encoding='utf-8'))
projects = {p['id']: p for p in catalog['projects']}
exclusion_path=ROOT/'data/eligibility-exclusions.json'
exclusions=json.loads(exclusion_path.read_text(encoding='utf-8')) if exclusion_path.exists() else {}
GLOBAL_MAX = [25, 20, 15, 20, 20]
def case_weights(case_id):
    for file in (ROOT/'cases'/str(case_id)/'case-data').rglob('*.md'):
        lines = file.read_text(encoding='utf-8',errors='replace').splitlines()
        for index, line in enumerate(lines):
            if not re.match(r'^\|\s*Критерий\s*\|',line,re.I):
                continue
            weights = []
            for row in lines[index+2:]:
                if not row.startswith('|'):
                    break
                cells = [part.strip() for part in row.strip().strip('|').split('|')]
                if cells[0].casefold().startswith('итого'):
                    break
                weights.extend(int(cell) for cell in cells if re.fullmatch(r'\d+',cell))
            if weights and sum(weights)==100:
                return weights
    return None

CASE_MAX = {case_id:case_weights(case_id) for case_id in range(1,13)}

def validate_scale(scale, weights, label):
    criteria = scale['criteria']
    if len(criteria) != len(weights):
        raise ValueError(f'{label}: wrong criterion count')
    for item, maximum in zip(criteria, weights):
        if not isinstance(item['score'], (int,float)) or item['max'] != maximum or not 0 <= item['score'] <= maximum:
            raise ValueError(f'{label}: invalid score or weight')
        deductions=item.get('deductions','').strip()
        awarded=item.get('awarded','').strip()
        concise_award=(awarded==f'{item["score"]:g}/{maximum}' and len(deductions)>=100)
        if (not item.get('name') or (len(awarded)<30 and not concise_award) or not deductions
                or (item['score']<maximum and len(deductions)<20 and not item.get('deductionItems'))
                or not item.get('evidence')):
            raise ValueError(f'{label}: missing explanation')
    if abs(sum(item['score'] for item in criteria) - scale['total']) > 0.01:
        raise ValueError(f'{label}: total mismatch')

def validate_judge(judge, repo_id, model):
    jsonschema.validate(judge,json.loads((ROOT/'scripts/judge-report.schema.json').read_text(encoding='utf-8')))
    POLICY.validate_report_policy(judge, publication=True)
    if judge.get('methodVersion') != PROVIDERS.METHOD_VERSION or judge['repoId'] != repo_id or judge['model'] != model or judge['caseId'] != projects[repo_id]['caseId']:
        raise ValueError(f'{repo_id}: wrong identity')
    corrected_snapshot=SNAPSHOT.override(ROOT,repo_id)
    if corrected_snapshot and judge.get('snapshot')!=corrected_snapshot['snapshot']:
        raise ValueError(f'{repo_id}: outdated snapshot; repeat review using verified pre-deadline push')
    if not judge.get('overallSummary') or not judge.get('fiveHourContext'):
        raise ValueError(f'{repo_id}: missing summary or five-hour context')
    if (judge.get('gaps') and not judge.get('futureAdvice')) or len(judge.get('caseRequirements',[])) < 3:
        raise ValueError(f'{repo_id}: insufficient case or future-hackathon analysis')
    if not judge.get('testData',{}).get('provided') or not judge['testData'].get('checks'):
        raise ValueError(f'{repo_id}: missing test-data analysis')
    if not judge.get('runtime',{}).get('checks'):
        raise ValueError(f'{repo_id}: missing runtime evidence')
    validate_scale(judge['global'], GLOBAL_MAX, f'{model} global')
    weights = CASE_MAX[projects[repo_id]['caseId']]
    if weights:
        validate_scale(judge['case'], weights, f'{model} case')
    elif judge.get('case') is not None:
        raise ValueError(f'{repo_id}: case has no official rubric')
    expected = (judge['global']['total'] + judge['case']['total']) / 2 if weights else judge['global']['total']
    if abs(expected - judge['judgeScore']) > 0.01:
        raise ValueError(f'{repo_id}: judge score mismatch')

def publish(folder):
    repo_id = folder.name
    available = [judge for judge in PROVIDERS.JUDGES if (folder / f"{judge['label']}.json").exists()]
    # Capture-only directories can be left by a judge's mistyped output path.
    # They are not reports; still reject unknown IDs that contain a report.
    if not available and exclusions.get(repo_id,{}).get('reviewStatus')!='late_submission':
        return None
    if repo_id not in projects:
        raise ValueError(f'{repo_id}: not in catalog')
    if exclusions.get(repo_id,{}).get('reviewStatus')=='late_submission':
        return publish_late_submission(repo_id,exclusions[repo_id])
    files = [folder / f"{judge['label']}.json" for judge in available]
    judges = [json.loads(file.read_text(encoding='utf-8')) for file in files]
    for judge, model in zip(judges, (j['name'] for j in available)):
        validate_judge(judge, repo_id, model)
    if len({judge['snapshot'] for judge in judges}) != 1:
        raise ValueError(f'{repo_id}: different snapshots')
    complete = len(judges) == len(PROVIDERS.JUDGES)
    total = round(sum(judge['judgeScore'] for judge in judges) / len(judges),2) if complete else None
    result = {'methodVersion':PROVIDERS.METHOD_VERSION,'repoId':repo_id,'repoUrl':projects[repo_id]['url'],'caseId':projects[repo_id]['caseId'],
              'snapshot':judges[0]['snapshot'],'judges':judges,'score':total,
              'status':'complete' if complete else 'partial','expectedJudges':len(PROVIDERS.JUDGES)}
    destination = TARGET if complete else TARGET/'partial'
    destination.mkdir(parents=True,exist_ok=True)
    temp = destination / f'{repo_id}.json.tmp'
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(destination / f'{repo_id}.json')
    return {'methodVersion':PROVIDERS.METHOD_VERSION,'repoId':repo_id,'caseId':result['caseId'],'score':result['score'],
            'status':result['status'],'expectedJudges':len(PROVIDERS.JUDGES),
            'judgeScores':[{'model':j['model'],'score':j['judgeScore']} for j in judges],
            'runStatuses':[j['runtime']['status'] for j in judges],
            'demoStatuses':[j['liveDemo']['status'] for j in judges],
            'liveDemos':[{'status':j['liveDemo']['status'],'url':j['liveDemo'].get('url')} for j in judges],
            'testChecks':[len(j['testData']['checks']) for j in judges]}

def publish_late_submission(repo_id, exclusion):
    project=projects[repo_id]
    deadline=datetime.fromisoformat(exclusion['deadlineUtc'].replace('Z','+00:00'))
    submitted=datetime.fromisoformat(exclusion['firstSolutionCommitAt'].replace('Z','+00:00'))
    if (deadline!=datetime(2026,9,23,13,tzinfo=timezone.utc) or submitted<=deadline
            or not re.fullmatch(r'[a-f0-9]{40}',exclusion['firstSolutionCommit'])):
        raise ValueError('Unconfirmed late submission: '+repo_id)
    local=timezone(timedelta(hours=5))
    submitted_text=submitted.astimezone(local).strftime('%d.%m.%Y в %H:%M:%S')
    reason=('Разбор кода не проводился: первый коммит с решением появился '+submitted_text+
            ' по времени Астаны, после дедлайна 23.09.2026 в 18:00. До дедлайна был только шаблон '
            'репозитория либо не было коммитов. Итог — 0 баллов по правилу времени сдачи; '
            'качество реализации не оценивалось.')
    result={'methodVersion':PROVIDERS.METHOD_VERSION,'repoId':repo_id,'repoUrl':project['url'],
            'caseId':project['caseId'],'status':'late_submission','score':0,'judges':[],
            'expectedJudges':0,'reason':reason,'deadlineUtc':exclusion['deadlineUtc'],
            'firstSolutionCommit':exclusion['firstSolutionCommit'],
            'firstSolutionCommitAt':exclusion['firstSolutionCommitAt'],
            'commitUrl':project['url']+'/commit/'+exclusion['firstSolutionCommit']}
    TARGET.mkdir(parents=True,exist_ok=True)
    temp=TARGET/f'{repo_id}.json.tmp'
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(TARGET/f'{repo_id}.json')
    return {key:result[key] for key in ('methodVersion','repoId','caseId','status','score','expectedJudges')} | {
        'judgeScores':[],'runStatuses':['unverified'],'demoStatuses':['unverified'],
        'liveDemos':[],'testChecks':[]}


if __name__ == '__main__':
    eligibility_spec=importlib.util.spec_from_file_location('judge_eligibility',ROOT/'scripts/judge_eligibility.py')
    eligibility=importlib.util.module_from_spec(eligibility_spec)
    eligibility_spec.loader.exec_module(eligibility)
    eligibility_rows=eligibility.collect(ROOT,projects,exclusions)
    rows = []
    partial_rows = []
    errors = []
    if SOURCE.exists():
        for folder in sorted(SOURCE.iterdir()):
            if folder.is_dir():
                try:
                    row = publish(folder)
                    if row:
                        (partial_rows if row['status']=='partial' else rows).append(row)
                except (KeyError,TypeError,ValueError,FileNotFoundError,jsonschema.ValidationError) as error:
                    errors.append(f'{folder.name}: {str(error)[:600]}')
    for repo_id, exclusion in exclusions.items():
        if exclusion.get('reviewStatus')=='late_submission' and not any(r['repoId']==repo_id for r in rows):
            try: rows.append(publish_late_submission(repo_id,exclusion))
            except (KeyError,TypeError,ValueError) as error: errors.append(f'{repo_id}: {error}')
    TARGET.mkdir(parents=True,exist_ok=True)
    temp = TARGET / 'index.json.tmp'
    temp.write_text(json.dumps({'methodVersion':PROVIDERS.METHOD_VERSION,'reviews':rows,'partialReviews':partial_rows,'eligibility':eligibility_rows},ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(TARGET / 'index.json')
    print(f"Published {sum(r['status']=='complete' for r in rows)} complete GPT-5.6 Luna reviews")
    print(f"Published {sum(r['status']=='late_submission' for r in rows)} deadline decisions (0 points, no code review)")
    print(f'Published {len(partial_rows)} partial reviews without ranking or average')
    for error in errors:
        print('Not published:',error)
    (ROOT/'data/publication-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
    if errors:
        raise SystemExit(1)
