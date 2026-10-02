import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher', ROOT/'scripts/publish-reviews.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublicationDiscoveryTest(unittest.TestCase):
    def test_capture_only_unknown_directory_does_not_block_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)/'hack-mistyped-id'
            captures = folder/'session-luna56/captures'
            captures.mkdir(parents=True)
            (captures/'build.stdout.log').write_text('build log')
            self.assertIsNone(publisher.publish(folder))
            (folder/'luna56.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'not in catalog'):
                publisher.publish(folder)

    def test_deadline_decision_without_judge_report_is_still_published(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)/'hack-late-fixture'
            folder.mkdir()
            exclusion = {'reviewStatus': 'late_submission'}
            with patch.object(publisher, 'projects', {folder.name: {}}), \
                 patch.object(publisher, 'exclusions', {folder.name: exclusion}), \
                 patch.object(publisher, 'publish_late_submission', return_value={'score': 0}) as late:
                self.assertEqual(publisher.publish(folder), {'score': 0})
                late.assert_called_once_with(folder.name, exclusion)
