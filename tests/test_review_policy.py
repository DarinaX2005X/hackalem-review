import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_policy import validate_report_policy


def fixture():
    return {'reviewPolicyVersion': 2, 'assessmentStatus': 'ready',
            'runtime': {'checks': [{'id': 'T1', 'status': 'fail', 'cause': 'project',
                                    'expected': 'Budget cannot be exceeded', 'result': 'Over-budget plan accepted'}]},
            'findings': [{'id': 'F1', 'kind': 'defect', 'verification': 'observed',
                          'responsibility': 'project', 'claim': 'Invalid budget accepted',
                          'expected': 'Reject plan', 'actual': 'Accepted plan',
                          'evidence': ['src/plan.py:12'], 'checkIds': ['T1']}],
            'global': {'criteria': [{'max': 25, 'score': 23, 'deductionItems': [
                {'points': 2, 'findingId': 'F1', 'reason': 'The main constraint can be bypassed'}]}]},
            'case': None,
            'futureAdvice': [{'findingIds': ['F1'], 'principle': 'Test domain boundaries early',
                              'why': 'The budget boundary was not enforced', 'how': 'Try valid and invalid input before UI work',
                              'successCheck': 'Invalid input is rejected', 'timeboxMinutes': 15}]}


class PolicyTests(unittest.TestCase):
    def test_confirmed_defect_can_cost_points(self):
        validate_report_policy(fixture(), require_current=True, publication=True)

    def test_environment_and_unknown_are_not_participant_defects(self):
        for cause in ('review_environment', 'external_service', 'unknown'):
            report = fixture()
            report['runtime']['checks'][0]['cause'] = cause
            with self.assertRaisesRegex(ValueError, 'blocked/inconclusive'):
                validate_report_policy(report)
        report = fixture()
        report['findings'][0]['verification'] = 'unverified'
        with self.assertRaisesRegex(ValueError, 'cannot deduct'):
            validate_report_policy(report)

    def test_deductions_must_reconcile_and_advice_must_be_grounded(self):
        report = fixture()
        report['global']['criteria'][0]['score'] = 20
        with self.assertRaisesRegex(ValueError, 'points lost'):
            validate_report_policy(report)
        report = fixture()
        report['futureAdvice'][0]['findingIds'] = ['F_OTHER']
        with self.assertRaisesRegex(ValueError, 'this project'):
            validate_report_policy(report)

    def test_review_limitation_cannot_be_listed_as_project_gap(self):
        report=fixture()
        report.update(methodVersion=4,gaps=['No API key'],gapFindingIds=['L1'])
        report['findings'].append({'id':'L1','kind':'limitation','verification':'unverified',
            'responsibility':'review_environment','claim':'No API key','expected':'Live API',
            'actual':'Key intentionally absent','evidence':['environment: API key absent'],'checkIds':[]})
        with self.assertRaisesRegex(ValueError,'gaps must'):
            validate_report_policy(report)
        report['gaps']=['Invalid budget accepted'];report['gapFindingIds']=['F1']
        validate_report_policy(report)

    def test_incomplete_report_is_saved_but_not_ranked(self):
        report = fixture()
        report['assessmentStatus'] = 'incomplete'
        validate_report_policy(report)
        with self.assertRaisesRegex(ValueError, 'do not rank'):
            validate_report_policy(report, publication=True)

    def test_legacy_is_readable_but_new_run_must_use_policy(self):
        validate_report_policy({'methodVersion': 3})
        with self.assertRaisesRegex(ValueError, 'reviewPolicyVersion'):
            validate_report_policy({'methodVersion': 3}, require_current=True)


if __name__ == '__main__':
    unittest.main()
