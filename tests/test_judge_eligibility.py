import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('judge_eligibility',Path(__file__).resolve().parents[1]/'scripts/judge_eligibility.py')
eligibility=importlib.util.module_from_spec(spec)
spec.loader.exec_module(eligibility)

class EligibilityTest(unittest.TestCase):
    def test_only_confirmed_exclusions_are_marked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            projects=dict.fromkeys(['late','none','error','unchecked','empty','active'])
            for name,commits in [('empty',[]),('active',[{'sha':'abc'}])]:
                folder=root/'data/judging'/name
                folder.mkdir(parents=True)
                (folder/'source-manifest.json').write_text(json.dumps({'branches':[{'name':'main'}],'windowCommits':commits}))
            rows=eligibility.collect(root,projects,{
                'late':{'reviewStatus':'late_submission'},
                'none':{'reason':'No commit in hackathon window'},
                'error':{'reason':'clone timeout'},
            })
            self.assertEqual(set(rows),{'late','none','empty'})
            self.assertEqual(rows['late']['status'],'late_submission')
            self.assertEqual(rows['none']['status'],'no_commits')
