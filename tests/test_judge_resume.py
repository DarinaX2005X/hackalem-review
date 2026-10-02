"""Exercise the judge queue without calling Codex."""

import importlib.util
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/judge-wave.py'
SPEC = importlib.util.spec_from_file_location('judge_wave',SCRIPT)
judge_wave = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(judge_wave)
QUEUE_SCRIPT = Path(__file__).resolve().parents[1]/'scripts/judge-all.py'
QUEUE_SPEC = importlib.util.spec_from_file_location('judge_all',QUEUE_SCRIPT)
judge_all = importlib.util.module_from_spec(QUEUE_SPEC)
QUEUE_SPEC.loader.exec_module(judge_all)

class JudgeQueueTest(unittest.TestCase):
    def test_only_template_before_deadline_is_not_a_solution(self):
        def git(*args,**kwargs):
            if args[0]=='ls-tree':return 'README.md' if args[-1]=='template' else 'README.md\napp.py'
            if args[0]=='show':return '# hack-fixture\nHackathon team repository for Fixture'
            if args[0]=='log':return 'template\x1f2026-09-14T05:50:21Z\nsolution\x1f2026-09-23T18:11:16+05:00'
            raise AssertionError(args)
        with patch.object(judge_wave,'git',git):
            late=judge_wave.late_submission(Path('.'),['origin/main'],[{'commit':'template'}])
            self.assertEqual(late['firstSolutionCommit'],'solution')
            self.assertEqual(late['reviewStatus'],'late_submission')
            self.assertIsNone(judge_wave.late_submission(Path('.'),['origin/main'],[{'commit':'real-prior-code'}]))

    def test_late_zero_is_a_deadline_decision_without_invented_judges(self):
        publisher=judge_wave.PUBLISHER
        with tempfile.TemporaryDirectory() as directory, patch.object(publisher,'TARGET',Path(directory)), \
             patch.object(publisher,'projects',{'fixture':{'url':'https://github.com/BAITC-Hacks/fixture','caseId':11}}):
            exclusion={'firstSolutionCommit':'a'*40,'firstSolutionCommitAt':'2026-09-23T18:11:16+05:00',
                       'deadlineUtc':'2026-09-23T13:00:00Z'}
            index=publisher.publish_late_submission('fixture',exclusion)
            report=json.loads((Path(directory)/'fixture.json').read_text(encoding='utf-8'))
            self.assertEqual(index['score'],0)
            self.assertEqual(report['judges'],[])
            self.assertIn('Разбор кода не проводился',report['reason'])
            self.assertEqual(index['runStatuses'],['unverified'])
            exclusion['firstSolutionCommitAt']='2026-09-23T17:59:00+05:00'
            with self.assertRaises(ValueError):publisher.publish_late_submission('fixture',exclusion)

    def test_timestamp_429_is_not_provider_quota(self):
        diagnostic=('2026-09-30T12:12:23.429325Z ERROR codex_models_manager::manager: '
                    'failed to refresh available models: request timed out')
        self.assertIsNone(judge_wave.LIMIT_PATTERN.search(diagnostic))
        for diagnostic in ('HTTP 429','unexpected status code: 429','Too many requests',
                           'rate_limit_exceeded','usage limit reached'):
            self.assertIsNotNone(judge_wave.LIMIT_PATTERN.search(diagnostic),diagnostic)

    def test_finish_case_eight_then_largest_cases_first(self):
        catalog={'cases':[{'id':c,'count':n} for c,n in [(9,31),(4,47),(8,66),(7,160),(12,130)]],
                 'projects':[{'id':str(c),'caseId':c} for c in (9,4,8,7,12)]}
        ordered=judge_all.ordered_projects(catalog,[8,7,12,4,9])
        self.assertEqual([p['caseId'] for p in ordered],[8,7,12,4,9])
        with self.assertRaises(ValueError):judge_all.ordered_projects(catalog,[8,8])

    def test_unfinished_preparation_is_selected_again_on_next_launch(self):
        projects=[{'id':'done','caseId':8},{'id':'clone-timeout','caseId':8},
                  {'id':'bad-windows-path','caseId':4}]
        with patch.object(judge_all,'done',side_effect=lambda repo:repo=='done'):
            self.assertEqual([p['id'] for p in judge_all.select_targets(projects,None,2,{})],
                             ['clone-timeout','bad-windows-path'])

    def test_dependency_caches_stay_in_disposable_session(self):
        with tempfile.TemporaryDirectory() as directory:
            session=Path(directory)
            env=judge_wave.PROVIDERS.environment(judge_wave.JUDGES[0],session)
            for key in ('UV_CACHE_DIR','PIP_CACHE_DIR','npm_config_cache','HF_HOME',
                        'TORCH_HOME','XDG_CACHE_HOME','BUN_INSTALL_CACHE_DIR',
                        'NODE_COMPILE_CACHE','PYTHONPYCACHEPREFIX','HF_HUB_CACHE',
                        'HF_DATASETS_CACHE','TEMP','TMP'):
                self.assertTrue(Path(env[key]).is_relative_to(session))
                self.assertTrue(Path(env[key]).is_dir())

    def test_single_judge_report_publishes_immediately(self):
        row={'repoId':'hack-test','eligible':True}
        ready=[]
        def fake_judge(job,model,wave):
            return {'repoId':job['repoId'],'model':model,'status':'complete'}
        with patch.object(judge_wave,'run_judge',fake_judge):
            results=judge_wave.run_prepared([row],1,Path('.'),emit=lambda *a,**k:None,on_review_ready=ready.append)
        self.assertEqual(ready,['hack-test'])
        self.assertEqual(len(results),1)

    def test_old_roster_or_partial_report_is_not_done(self):
        models=judge_all.MODELS
        reports=[{'methodVersion':4,'judges':[]},
                 {'methodVersion':4,'judges':[{'model':models[0]},{'model':'LongCat 2.5 Preview'}]}]
        for report in reports:
            with patch.object(judge_all,'read',return_value=report):self.assertFalse(judge_all.done('fixture'))
        with patch.object(judge_all,'read',return_value={'methodVersion':4,'judges':[{'model':m} for m in models]}):
            self.assertTrue(judge_all.done('fixture'))

    def test_parallel_four_runs_four_judges_at_once(self):
        rows = [{'repoId':f'hack-test-{index:02}','eligible':True} for index in range(6)]
        lock = threading.Lock()
        active = 0
        peak = 0
        pairs = []
        checkpoints = []

        def fake_judge(row, model, wave):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak,active)
            time.sleep(0.04)
            with lock:
                active -= 1
            return {'repoId':row['repoId'],'model':model,'status':'complete'}

        with patch.object(judge_wave,'run_judge',fake_judge):
            results = judge_wave.run_prepared(rows,4,Path('.'),emit=lambda message,flush:None,
                checkpoint=lambda current:checkpoints.append(len(current)),
                on_pair_complete=pairs.append)
        self.assertEqual(peak,4)
        self.assertEqual(len(results),6)
        self.assertEqual(checkpoints[:6],list(range(1,7)))
        self.assertEqual(set(pairs),{row['repoId'] for row in rows})

    def test_parallel_eight_never_exceeds_eight_active_judges(self):
        rows = [{'repoId':f'hack-test-{index:02}','eligible':True} for index in range(10)]
        oc_active = oc_peak = 0
        lock = threading.Lock()
        started = active = peak = 0

        def fake_judge(row, model, wave):
            nonlocal started, active, peak, oc_active, oc_peak
            with lock:
                started += 1
                sequence = started
                active += 1
                peak = max(peak,active)
                if model != judge_wave.JUDGES[0]['name']:
                    oc_active += 1
                    oc_peak = max(oc_peak,oc_active)
            time.sleep(0.05)
            with lock:
                active -= 1
                if model != judge_wave.JUDGES[0]['name']: oc_active -= 1
            return {'repoId':row['repoId'],'model':model,'status':'complete'}

        with patch.object(judge_wave,'run_judge',fake_judge):
            results = judge_wave.run_prepared(rows,8,Path('.'),emit=lambda message,flush:None)
        self.assertLessEqual(peak,8)
        self.assertGreater(peak,1)
        self.assertEqual(oc_peak,0)
        self.assertEqual(peak,8)
        self.assertEqual(len(results),10)

    def test_rate_limit_stops_submitting_new_sessions(self):
        rows = [{'repoId':f'hack-test-{index:02}','eligible':True} for index in range(10)]
        started = []
        messages = []

        def fake_judge(row, model, wave):
            started.append((row['repoId'],model))
            if row['repoId']==rows[0]['repoId'] and model==judge_wave.JUDGES[0]['name']:
                return {'repoId':row['repoId'],'model':model,'status':'rate_limited'}
            time.sleep(0.04)
            return {'repoId':row['repoId'],'model':model,'status':'complete'}

        def collect(message, flush):
            messages.append(message)

        with patch.object(judge_wave,'run_judge',fake_judge):
            results = judge_wave.run_prepared(rows,4,Path('.'),emit=collect)
        self.assertEqual(len(started),4)
        self.assertEqual(len(results),10)
        self.assertEqual(sum(row['status']=='skipped_due_limit' for row in results),6)
        self.assertEqual(sum('ОШИБКА' in message for message in messages),1)
        self.assertFalse(any('Active ' in message or 'START ' in message for message in messages))

    def test_wave_groups_up_to_twenty_projects(self):
        projects = [{'id':f'hack-test-{i:02}','caseId':7} for i in range(9)]
        self.assertEqual(judge_all.select_batch(projects+[{'id':'other','caseId':8}],4),projects)

    def test_case_queue_runs_all_projects_across_multiple_waves(self):
        projects = [{'id':f'hack-test-{i:02}','caseId':12} for i in range(45)]
        projects += [{'id':'another-case','caseId':11}]
        with patch.object(judge_all,'done',return_value=False):
            remaining=judge_all.select_targets(projects,12,0,{})
        batches=[]
        while remaining:
            batch=judge_all.select_batch(remaining,8)
            batches.append(len(batch))
            remaining=remaining[len(batch):]
        self.assertEqual(batches,[20,20,5])

    def test_max_projects_counts_only_unfinished_projects(self):
        projects=[{'id':f'hack-test-{i:02}','caseId':12} for i in range(5)]
        with patch.object(judge_all,'done',side_effect=lambda repo_id:repo_id==projects[0]['id']):
            selected=judge_all.select_targets(projects,12,2,{projects[1]['id']:{'reason':'excluded'}})
        self.assertEqual(selected,projects[2:4])

    def test_publication_failure_does_not_hide_a_judge_failure(self):
        repo='hack-test-00'
        completed=[{'repoId':repo,'model':model,'status':'complete'}
                   for model in judge_all.MODELS]
        self.assertTrue(judge_all.publication_only_unresolved([repo],completed))
        completed[0]['status']='rate_limited'
        self.assertFalse(judge_all.publication_only_unresolved([repo],completed))

    def test_all_twelve_case_briefs_have_required_sections(self):
        briefs = SCRIPT.parents[1]/'case-briefs'
        self.assertEqual(len(list(briefs.glob('*.md'))),12)
        for case_id in range(1,13):
            content = (briefs/f'{case_id:02}.md').read_text(encoding='utf-8')
            self.assertIn('## Критерии кейса',content)
            self.assertIn('## Тестовые данные и проверка',content)
            self.assertIn(f'cases/{case_id}/task.txt',content)

    def test_commands_never_resume_or_use_auto_model(self):
        for judge in judge_wave.JUDGES:
            with tempfile.TemporaryDirectory() as directory, patch.object(judge_wave.PROVIDERS,'executable',return_value='fake-cli'):
                if judge.get('blocked_reason'):
                    with self.assertRaises(RuntimeError): judge_wave.PROVIDERS.command(judge,Path('prompt.txt'),Path('session'))
                    continue
                args=judge_wave.PROVIDERS.command(judge,Path('prompt.txt'),Path(directory))
            self.assertNotIn('--continue',args)
            self.assertNotIn('--resume',args)
            self.assertIn(judge['id'],args)
            self.assertIn('forced_login_method="chatgpt"',args)
            self.assertIn('--ignore-user-config',args)
            self.assertIn('service_tier="default"',args)
            if judge['provider']=='opencode':
                self.assertTrue(judge['id'].endswith('-free'))
                config=json.loads(judge_wave.PROVIDERS.environment(judge)['OPENCODE_CONFIG_CONTENT'])
                self.assertEqual(config['small_model'],judge['id'])

    def test_event_ledger_preserves_reported_usage_and_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'events.jsonl'
            path.write_text('\n'.join(json.dumps(e) for e in [
                {'type':'step_finish','sessionID':'session-1','part':{'tokens':{'input':100,'output':20,'reasoning':8,'cache':{'read':40}},'cost':0}},
                {'type':'error','error':'rate limit'},
            ]),encoding='utf-8')
            session,usage,errors,texts=judge_wave.PROVIDERS.event_summary(path)
            self.assertEqual(session,'session-1')
            self.assertEqual(usage['inputTokens'],100)
            self.assertEqual(usage['cachedInputTokens'],40)
            self.assertEqual(usage['reportedCost'],0)
            self.assertIn('rate limit',errors)

if __name__=='__main__':
    unittest.main()
