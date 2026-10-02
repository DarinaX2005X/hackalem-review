"""No model requests, containers, or real cleanup in these tests."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

accounting, providers = module('judge_accounting'), module('judge_providers')
queue, wave = module('judge-all'), module('judge-wave')

class AccountingTest(unittest.TestCase):
    def test_cached_input_is_subset_and_retries_count_once(self):
        a = dict(modelId='gpt-6-luna', wave='a', events='one', reportedTurns=1,
                 inputTokens=1_000_000, cachedInputTokens=800_000, outputTokens=100_000)
        b = dict(a, modelId='gpt-5.6-luna', events='two')
        missing = dict(a, wave='b', events='three', reportedTurns=0,
                       inputTokens=0, cachedInputTokens=0, outputTokens=0)
        result = accounting.summarize([a,a,b,missing], 'a')
        self.assertAlmostEqual(result['models']['gpt-6-luna']['apiEquivalentUsd'], .078)
        self.assertAlmostEqual(result['apiEquivalentUsd'], .254)
        self.assertEqual(result['models']['gpt-6-luna']['attempts'], 1)
        self.assertEqual(accounting.summarize([missing])['models']['gpt-6-luna']['missingUsage'], 1)

    def test_codex_completed_and_failed_usage_survives_interruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)/'repo/session-luna6'
            folder.mkdir(parents=True)
            events = folder/'events-one.jsonl'
            events.write_text('\n'.join(json.dumps(e) for e in [
                {'type':'thread.started','thread_id':'fixture'},
                {'type':'turn.completed','usage':{'input_tokens':1000,'cached_input_tokens':800,'output_tokens':100}},
                {'type':'turn.failed','error':{'message':'Usage limit reached'},
                 'usage':{'input_tokens':50,'cached_input_tokens':0,'output_tokens':4}},
            ]),encoding='utf-8')
            (folder/'attempt-one.json').write_text(json.dumps(dict(
                events=str(events), modelId='gpt-6-luna', wave='a', repoId='repo', attempt='one')))
            rows = accounting.load_records(Path(temporary), providers)
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['inputTokens'],1050)
            self.assertEqual(rows[0]['outputTokens'],104)
            session, usage, errors, _ = providers.event_summary(events)
            self.assertEqual(session,'fixture')
            self.assertIn('Usage limit reached',errors)

    def test_api_login_is_rejected_before_any_judge_runs(self):
        for output in ('Logged in using an API key', 'Not logged in'):
            with patch.object(providers, 'executable', return_value='codex'), \
                 patch.object(providers.subprocess, 'run', return_value=subprocess.CompletedProcess([],0,'',output)):
                with self.assertRaises(RuntimeError): providers.require_subscription()
        with patch.dict(os.environ, {'OPENAI_API_KEY':'fixture', 'OPENAI_BASE_URL':'fixture'}):
            env = providers.environment(providers.JUDGES[0])
        self.assertNotIn('OPENAI_API_KEY',env)
        self.assertNotIn('OPENAI_BASE_URL',env)

    def test_one_console_completion_per_project_without_start_or_poll_noise(self):
        rows = [dict(repoId='fixture',eligible=True)]
        messages = []
        def fake(job, model, directory):
            return dict(repoId=job['repoId'],model=model,status='complete',score=70)
        with patch.object(wave,'run_judge',fake):
            wave.run_prepared(rows,2,Path('.'),emit=lambda message,**kwargs:messages.append(message))
        self.assertEqual(len(messages),1)
        self.assertIn('ГОТОВО 1/1',messages[0])

    def test_cleanup_failure_is_not_reported_as_success(self):
        with patch.object(queue.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','daemon down')):
            with self.assertRaises(RuntimeError): queue.cleanup_wave_docker(['hack-fixture'])

    def test_random_container_names_are_matched_by_original_image_only(self):
        removed=[]
        def docker(command,**kwargs):
            args=command[1:]
            output=''
            if args[:2]==['container','ls']:
                output='\n'.join(json.dumps(row) for row in [
                    {'ID':'owned','Names':'vigorous_easley'},
                    {'ID':'other','Names':'unrelated_server'},
                    {'ID':'gone','Names':'already_removed'},
                ])
            elif args[:2]==['container','inspect']:
                if args[2]=='gone':return subprocess.CompletedProcess(command,1,'','No such container')
                output='luna56-46e44fd3-review' if args[2]=='owned' else 'someone-else/app'
            elif args[:2]==['container','rm']:removed.append(args[-1])
            return subprocess.CompletedProcess(command,0,output,'')
        with patch.object(queue.subprocess,'run',docker):
            queue.cleanup_wave_docker(['hack-46e44fd3-melnik'],prune_global=False)
        self.assertEqual(removed,['owned'])

    def test_file_failure_does_not_skip_docker_compaction(self):
        calls=[]
        def files(*args):
            calls.append('files')
            raise RuntimeError('fixture file lock')
        with patch.object(queue,'cleanup_wave_docker',side_effect=lambda *args:calls.append('docker')), \
             patch.object(queue,'cleanup_wave_worktrees',side_effect=files), \
             patch.object(queue,'compact_docker_vhd_if_needed',side_effect=lambda **kwargs:calls.append('compact') or True):
            errors=queue.finish_wave_cleanup(Path('.'),['hack-fixture'])
        self.assertEqual(calls,['docker','files','compact'])
        self.assertEqual(len(errors),1)

    def test_current_reports_publish_without_changing_scores(self):
        publisher=module('publish-reviews')
        for name in ('hack-63569893-ml-empire','hack-6d253846-dir-echoes'):
            path=ROOT/'data/judging'/name/'luna56.json'
            if not path.exists():
                self.skipTest('Local reports unavailable')
            report=json.loads(path.read_text(encoding='utf-8'))
            publisher.validate_judge(report,name,'GPT-5.6 Luna')

    def test_publication_error_does_not_print_done(self):
        messages=[]
        def fake(row,model,directory):
            return dict(repoId=row['repoId'],model=model,status='complete',score=70)
        with patch.object(wave,'run_judge',fake):
            wave.run_prepared([dict(repoId='fixture',eligible=True)],1,Path('.'),
                emit=lambda message,**kwargs:messages.append(message),on_review_ready=lambda repo:False)
        self.assertFalse(any('ГОТОВО' in message for message in messages))
        self.assertTrue(any('не завершена' in message for message in messages))

if __name__ == '__main__':
    unittest.main()
