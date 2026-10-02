"""Publish only confirmed time-window exclusions, never missing author guesses."""
import json


def collect(root,projects,exclusions):
    rows={}
    for repo_id in projects:
        exclusion=exclusions.get(repo_id,{})
        if exclusion.get('reviewStatus')=='late_submission':
            rows[repo_id]={'status':'late_submission','reason':'Первый коммит с решением появился после 18:00 по Астане.'}
        elif exclusion.get('reason') in ('No commit in hackathon window','No pre-deadline branch commit'):
            rows[repo_id]={'status':'no_commits','reason':'Нет коммитов в период хакатона: 23 сентября, 13:00–18:00 по Астане.'}
        else:
            path=root/'data/judging'/repo_id/'source-manifest.json'
            if path.exists():
                manifest=json.loads(path.read_text(encoding='utf-8'))
                if manifest.get('branches') and manifest.get('windowCommits')==[]:
                    rows[repo_id]={'status':'no_commits','reason':'Нет коммитов в период хакатона: 23 сентября, 13:00–18:00 по Астане.'}
    return rows
