import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('api_audit', SCRIPTS / 'audit-api-requirements.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class FakeClient:
    def snapshots(self, repo):
        return [{'name': 'main', 'snapshot': 'aaa'}, {'name': 'feature/demo', 'snapshot': 'bbb'}]

    def metadata(self, path):
        return {'tree': [{'path': '.env.example', 'type': 'blob', 'sha': 'one', 'size': 80},
                         {'path': '.env', 'type': 'blob', 'sha': 'two', 'size': 200}], 'truncated': False}

    def variables(self, repo, sha, entry):
        return audit.extract('OPENAI_API_KEY=do-not-save-this-secret', entry['path'])


class AuditTests(unittest.TestCase):
    def test_all_snapshots_and_evidence_are_preserved_without_values(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(audit, 'OUTPUT', Path(folder)):
            project = {'id': 'hack-test', 'caseId': 12}
            result = audit.audit(project, FakeClient())
            self.assertEqual(result['status'], 'complete')
            self.assertEqual({r['snapshot'] for r in result['variables']}, {'aaa', 'bbb'})
            self.assertEqual({r['path'] for r in result['files']}, {'.env.example'})
            self.assertNotIn('do-not-save', (Path(folder) / 'projects/hack-test.json').read_text())
            # A completed scan is resumed without another network request.
            self.assertEqual(audit.audit(project, object()), result)

    def test_missing_snapshot_is_not_claimed_complete(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(audit, 'OUTPUT', Path(folder)):
            client = FakeClient()
            client.snapshots = lambda repo: []
            result = audit.audit({'id': 'hack-test', 'caseId': 12}, client)
            self.assertEqual(result['status'], 'partial')
            self.assertTrue(result['errors'])


if __name__ == '__main__':
    unittest.main()
