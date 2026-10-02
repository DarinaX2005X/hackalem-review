"""Verify neutral, cached inputs without running participant code or judges."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('judge_dossier', ROOT/'scripts/judge_dossier.py')
dossier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dossier)


def git(repo, *args):
    result = subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True,
                            encoding='utf-8', check=True)
    return result.stdout.strip()


class DossierTest(unittest.TestCase):
    def test_capture_keeps_full_output_but_limits_visible_excerpt(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable, str(ROOT/'scripts/judge-capture.py'),
                                     '--output-dir',temporary,'--label','test','--',
                                     sys.executable,'-c','print("x" * 50000)'],
                                    capture_output=True,text=True,encoding='utf-8',errors='replace')
            self.assertEqual(result.returncode,0)
            self.assertLess(len(result.stdout),12000)
            self.assertIn('exitCode=0',result.stdout)
            logs = list((Path(temporary)/'captures').glob('*.stdout.log'))
            self.assertEqual(len(logs),1)
            self.assertGreater(logs[0].stat().st_size,50000)

    def test_inventory_and_case_schema_are_cached_by_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = root/'cases/1/case-data'
            case.mkdir(parents=True)
            (case/'sample.csv').write_text('id,value\n1,42\n',encoding='utf-8')
            repo = root/'repo'
            repo.mkdir()
            git(repo,'init','-q')
            git(repo,'config','user.email','tester@example.test')
            git(repo,'config','user.name','Tester')
            (repo/'README.md').write_text('Start here',encoding='utf-8')
            (repo/'package.json').write_text(json.dumps({'scripts':{'build':'vite build','test':'node --test'}}),encoding='utf-8')
            (repo/'src').mkdir()
            (repo/'src/main.js').write_text('console.log(1)',encoding='utf-8')
            git(repo,'add','.')
            git(repo,'commit','-qm','initial')
            snapshot = git(repo,'rev-parse','HEAD')
            git(repo,'checkout','-qb','other')
            (repo/'src/other.js').write_text('console.log(2)',encoding='utf-8')
            git(repo,'add','.')
            git(repo,'commit','-qm','other branch')
            branches = [{'name':'main','commit':snapshot},
                        {'name':'other','commit':git(repo,'rev-parse','HEAD')}]
            project = {'id':'hack-test-dossier','caseId':1}
            work = root/'work'
            output = dossier.build_dossier(project,repo,snapshot,branches,
                                           [{'author':'Tester'}],work,root)
            text = output.read_text(encoding='utf-8')
            self.assertIn('README.md',text)
            self.assertIn('src/main.js',text)
            self.assertIn('src/other.js',text)
            self.assertIn('sample.csv',text)
            self.assertIn('id, value',text)
            self.assertIn('build, test',text)
            inventory = json.loads((output.parent/f'{snapshot}-inventory.json').read_text(encoding='utf-8'))
            self.assertEqual(inventory['fileCount'],3)
            self.assertEqual(inventory['branchChanges'][0]['changedCount'],1)
            self.assertEqual(dossier.build_dossier(project,repo,snapshot,branches,
                                                   [{'author':'Tester'}],work,root),output)

    def test_branch_inventory_does_not_need_other_branch_blob_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root/'repo'
            repo.mkdir()
            git(repo,'init','-q')
            git(repo,'config','user.email','tester@example.test')
            git(repo,'config','user.name','Tester')
            git(repo,'config','diff.renames','true')
            (repo/'old.txt').write_text('original content\n' * 30)
            git(repo,'add','.')
            git(repo,'commit','-qm','base')
            snapshot = git(repo,'rev-parse','HEAD')
            (repo/'old.txt').unlink()
            (repo/'new.txt').write_text('original content\n' * 30 + 'branch-only change\n')
            git(repo,'add','-A')
            git(repo,'commit','-qm','rename and edit')
            other = git(repo,'rev-parse','HEAD')
            blob = git(repo,'rev-parse',f'{other}:new.txt')
            # Simulate an unhydrated branch in a partial clone, with no remote
            # available to fetch its contents. Tree metadata remains available.
            missing_blob = repo/'.git/objects'/blob[:2]/blob[2:]
            missing_blob.chmod(0o600)
            missing_blob.unlink()
            output = dossier.build_dossier({'id':'hack-partial','caseId':1},repo,snapshot,
                [{'name':'main','commit':snapshot},{'name':'other','commit':other}],[],root/'work',root)
            record = json.loads((output.parent/f'{snapshot}-inventory.json').read_text(encoding='utf-8'))
            self.assertEqual(record['branchChanges'][0]['changedCount'],2)
            self.assertEqual(set(record['branchChanges'][0]['sample']),{'old.txt','new.txt'})

    def test_check_journal_ignores_failures_and_other_snapshots(self):
        spec = importlib.util.spec_from_file_location('judge_checks', ROOT/'scripts/judge_checks.py')
        checks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checks)
        self.assertNotIn('example-secret',checks.redact('curl -u apiuser:example-secret /api/products'))
        self.assertNotIn('example-token',checks.redact('Authorization: Bearer example-token'))
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            events = base/'events.jsonl'
            events.write_text('\n'.join(json.dumps(row) for row in [
                {'type':'item.completed','item':{'type':'command_execution',
                 'command':'docker build -t example .','exit_code':0,'aggregated_output':'done'}},
                {'type':'item.completed','item':{'type':'command_execution',
                 'command':'pytest','exit_code':1,'aggregated_output':'failed'}},
                {'type':'item.completed','item':{'type':'command_execution',
                 'command':'Get-Content README.md','exit_code':0,'aggregated_output':'text'}},
            ])+'\n',encoding='utf-8')
            target = base/'checks.json'
            first = checks.save_successes(target,'abc',events)
            self.assertEqual([row['kind'] for row in first['checks']],['build'])
            self.assertIn('docker build',checks.resume_note(target,'abc'))
            self.assertIn('пока пуст',checks.resume_note(target,'different'))
            second = checks.save_successes(target,'abc',events)
            self.assertEqual(len(second['checks']),1)


if __name__ == '__main__':
    unittest.main()
