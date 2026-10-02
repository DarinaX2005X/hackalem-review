"""Portable packaging/validation tests. No network, model calls, Docker or participant execution."""
import copy
import importlib.util
import json
import pathlib
import shutil
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
KIT=ROOT/'exports/hackalem-review-kit-2026-10-01/hackalem-review-kit'
spec=importlib.util.spec_from_file_location('arena_kit',ROOT/'scripts/arena-kit/kit.py')
kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
sys.path.insert(0,str(ROOT/'scripts'))


class ArenaKitTest(unittest.TestCase):
    def test_offline_preparation_prompt_and_command_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);rid='hack-fixture-portable'
            for name in ('schemas','inventory','instructions','case-briefs','tools'):
                shutil.copytree(KIT/name,root/name)
            kit.write(root/'inventory/repos.json',[{'id':rid,'name':'Fixture','caseId':4,
                'defaultBranch':'main','url':'https://github.com/BAITC-Hacks/'+rid}])
            kit.write(root/'inventory/snapshots.json',{})
            kit.write(root/'inventory/snapshot-overrides.json',{})
            clone=root/'work/clones'/rid;clone.mkdir(parents=True)
            def git(*args,env=None):
                return subprocess.run(['git',*args],cwd=clone,check=True,capture_output=True,env=env)
            git('init','-b','main')
            (clone/'README.md').write_text('Offline fixture source.\n')
            git('add','README.md')
            git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Fixture',
                env={**os.environ,'GIT_AUTHOR_DATE':'2026-09-23T12:00:00Z','GIT_COMMITTER_DATE':'2026-09-23T12:00:00Z'})
            git('update-ref','refs/remotes/origin/main','HEAD')
            with patch.object(kit,'ROOT',root):
                kit.prepare(rid);kit.prompt(rid,'Model not disclosed')
            text=(root/'results/evidence'/rid/'judge-prompt.txt').read_text(encoding='utf-8')
            self.assertIn('--check-id BUILD-1',text)
            self.assertIn('model=Model not disclosed',text)
            self.assertNotIn('{repo_id}',text)
            result=subprocess.run([sys.executable,str(root/'tools/check.py'),'--output-dir',
                str(root/'results/evidence'/rid),'--check-id','fixture-check','--',
                sys.executable,'-c','print("fixture command, no participant code")'],cwd=root,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            ledger=[json.loads(line) for line in (root/'results/evidence'/rid/'checks.jsonl').read_text().splitlines()]
            self.assertEqual(ledger[0]['exitCode'],0)
            self.assertEqual(ledger[0]['id'],'fixture-check')
            self.assertTrue((root/'results'/ledger[0]['stdout']).is_file())

    def fixture(self,root):
        # Existing evidence is used only inside a disposable test fixture and is
        # never included in the handoff ZIP or presented as an external review.
        report=json.loads((ROOT/'data/judging/hack-63569893-ml-empire/luna56.json').read_text(encoding='utf-8'))
        report['model']='External test fixture'
        rid=report['repoId'];case=report['caseId']
        for name in ('schemas','inventory'):
            shutil.copytree(KIT/name,root/name)
        kit.write(root/'inventory/repos.json',[{'id':rid,'caseId':case,'url':'https://github.com/BAITC-Hacks/'+rid}])
        kit.write(root/'results/evidence'/rid/'snapshot.json',{'branches':[{'name':'main','commit':report['snapshot']}]})
        evidence=root/'results/evidence'/rid;captures=evidence/'captures';captures.mkdir()
        (captures/'fixture.log').write_text('Test fixture log, not a new run of the project.\n')
        log=f'evidence/{rid}/captures/fixture.log'
        rows=[{'id':c['id'],'exitCode':0 if c['status']=='pass' else 1,'timedOut':False,'stdout':log,'stderr':log}
              for c in report['runtime']['checks'] if c['status'] in ('pass','fail')]
        (evidence/'checks.jsonl').write_text('\n'.join(json.dumps(r) for r in rows),encoding='utf-8')
        path=root/'results/reports'/f'{rid}.json';kit.write(path,report)
        return path,report

    def test_real_report_structure_accepts_honest_external_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);path,report=self.fixture(root)
            with patch.object(kit,'ROOT',root):
                self.assertEqual(kit.validate_report(path)['model'],'External test fixture')
                report['judgeScore']-=1;kit.write(path,report)
                with self.assertRaisesRegex(ValueError,'judgeScore'):kit.validate_report(path)

    def test_missing_execution_evidence_cannot_be_passed_as_reviewed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);path,report=self.fixture(root)
            (root/'results/evidence'/report['repoId']/'checks.jsonl').unlink()
            with patch.object(kit,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'execution log'):kit.validate_report(path)

    def test_partial_zip_preserves_missing_projects_and_excludes_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);path,report=self.fixture(root)
            inventory=kit.read(root/'inventory/repos.json')
            inventory.append({'id':'hack-fixture-pending','caseId':report['caseId']})
            kit.write(root/'inventory/repos.json',inventory)
            (root/'work').mkdir();(root/'work/private').write_text('must not ship')
            with patch.object(kit,'ROOT',root):
                self.assertFalse(kit.finalize(root/'output.zip'))
                manifest=kit.read(root/'results/manifest.json')
                self.assertEqual(manifest['counts']['reviewed'],1)
                self.assertEqual(manifest['counts']['pending'],1)
                with zipfile.ZipFile(root/'output.zip') as archive:
                    self.assertIn('manifest.json',archive.namelist())
                    self.assertFalse(any(name.startswith('work/') for name in archive.namelist()))
                with self.assertRaises(ValueError):kit.finalize(root/'none.zip',99)

    def test_blocked_is_not_zero_or_complete_and_late_requires_late_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);path,report=self.fixture(root);path.unlink()
            rid=report['repoId'];decision=root/'results/decisions'/f'{rid}.json'
            row={'repoId':rid,'caseId':report['caseId'],'status':'blocked','reasonCode':'review_environment',
                'reason':'Isolated runtime is unavailable in the test fixture.','evidence':['evidence/fixture.log']}
            kit.write(decision,row)
            with patch.object(kit,'ROOT',root):
                kit.validate_decision(decision)
                self.assertFalse(kit.finalize(root/'blocked.zip'))
                self.assertEqual(kit.read(root/'results/manifest.json')['counts']['blocked'],1)
                row.update(status='disqualified',reasonCode='late_submission',score=0,allBranchesChecked=True,
                    firstSolutionCommit='a'*40,firstSolutionCommitAt='2026-09-23T12:00:00Z')
                kit.write(decision,row)
                with self.assertRaisesRegex(ValueError,'not late'):kit.validate_decision(decision)

    def test_full_archive_and_case_partitions_are_complete_without_old_reviews(self):
        destination=KIT.parent
        with zipfile.ZipFile(destination/'hackalem-all-1053.zip') as archive:
            self.assertIsNone(archive.testzip())
            inventory=json.loads(archive.read('inventory/repos.json'))
            self.assertEqual(len(inventory),1053)
            self.assertFalse(any(name.startswith(('results/','data/judging/','work/')) for name in archive.namelist()))
            self.assertNotIn('enum',json.loads(archive.read('schemas/report.schema.json'))['properties']['model'])
        all_ids=[]
        for case in range(1,13):
            with zipfile.ZipFile(destination/f'by-case/case-{case:02}.zip') as archive:
                rows=json.loads(archive.read('inventory/repos.json'))
                self.assertTrue(all(r['caseId']==case for r in rows))
                all_ids.extend(r['id'] for r in rows)
        self.assertEqual(len(all_ids),1053)
        self.assertEqual(len(set(all_ids)),1053)
