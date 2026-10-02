import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('judge_snapshot',Path(__file__).resolve().parents[1]/'scripts/judge_snapshot.py')
snapshot=importlib.util.module_from_spec(spec);spec.loader.exec_module(snapshot)

class SnapshotTest(unittest.TestCase):
    def test_only_verified_archived_predeadline_push_can_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir()
            row={'snapshot':'a'*40,'branch':'main','evidence':{'archived':True,
                'pushedAt':'2026-09-23T12:59:07Z','url':'https://api.github.com/repos/BAITC-Hacks/test'}}
            path=root/'data/snapshot-overrides.json'
            path.write_text(json.dumps({'test':row}))
            self.assertEqual(snapshot.override(root,'test'),row)
            self.assertIsNone(snapshot.override(root,'other'))
            result=snapshot.apply([{'name':'main','commit':'b'*40},{'name':'feature','commit':'c'*40}],row,root,lambda *a,**k:'a'*40)
            self.assertEqual(result,[{'name':'feature','commit':'c'*40},{'name':'main','commit':'a'*40}])
            self.assertIn('12:59:07Z',snapshot.prompt_note(row))
            for evidence in [row['evidence']|{'pushedAt':'2026-09-23T13:00:01Z'},row['evidence']|{'archived':False}]:
                path.write_text(json.dumps({'test':row|{'evidence':evidence}}))
                with self.assertRaises(ValueError):snapshot.override(root,'test')
