"""Validate score provenance. Legacy reports stay readable and are not reassessed."""

import math

VERSION = 2


def require(condition, message):
    if not condition:
        raise ValueError('Review policy: ' + message)


def validate_report_policy(report, require_current=False, publication=False):
    version = report.get('reviewPolicyVersion')
    if version is None and not require_current:
        return
    require(version == VERSION, 'missing or unsupported reviewPolicyVersion')
    require(report.get('assessmentStatus') in ('ready', 'incomplete'), 'assessment status missing')
    if publication:
        require(report['assessmentStatus'] == 'ready', 'assessment incomplete; do not rank unknown results')
    findings = {}
    checks = {}
    for check in report['runtime']['checks']:
        require(check.get('id') and check['id'] not in checks, 'duplicate/missing runtime check ID')
        require(check.get('status') in ('pass', 'fail', 'blocked', 'not_run'), 'check status missing')
        require(check.get('cause') in ('none', 'project', 'review_environment', 'external_service', 'unknown'), 'check cause missing')
        require(check.get('expected') and check.get('result'), 'check needs expected and actual result')
        checks[check['id']] = check
    for finding in report['findings']:
        require(finding.get('id') and finding['id'] not in findings, 'duplicate/missing finding ID')
        require(finding.get('kind') in ('defect', 'strength', 'limitation'), 'finding kind missing')
        require(finding.get('verification') in ('observed', 'source', 'unverified'), 'verification missing')
        require(finding.get('responsibility') in ('project', 'review_environment', 'external_service', 'unknown'), 'responsibility missing')
        require(all(finding.get(key) for key in ('claim', 'expected', 'actual', 'evidence')), 'finding needs concrete evidence and expected/actual result')
        for check_id in finding.get('checkIds', []):
            require(check_id in checks, 'finding references unknown check')
        findings[finding['id']] = finding
    if report.get('methodVersion', 0) >= 4:
        refs = report.get('gapFindingIds', [])
        require(len(refs) == len(report.get('gaps', [])), 'every gap needs a finding')
        for ref in refs:
            finding = findings.get(ref, {})
            require(finding.get('kind') == 'defect' and finding.get('responsibility') == 'project'
                    and finding.get('verification') in ('observed', 'source'),
                    'gaps must be verified project defects, not review limitations')
    for scale_name in ('global', 'case'):
        scale = report.get(scale_name)
        if not scale:
            continue
        for item in scale['criteria']:
            require('deductionItems' in item, 'criterion has no itemized deductions')
            points = 0
            used = set()
            for deduction in item['deductionItems']:
                amount = deduction.get('points')
                require(isinstance(amount, (int, float)) and not isinstance(amount, bool)
                        and math.isfinite(amount) and amount > 0, 'invalid deducted points')
                finding_id = deduction.get('findingId')
                require(finding_id in findings and finding_id not in used, 'missing/duplicate deduction finding')
                used.add(finding_id)
                finding = findings[finding_id]
                require(finding['kind'] == 'defect' and finding['responsibility'] == 'project'
                        and finding['verification'] in ('observed', 'source'),
                        'cannot deduct for environment, external service, or unverified finding')
                for check_id in finding.get('checkIds', []):
                    check = checks[check_id]
                    require(check['status'] not in ('blocked', 'not_run')
                            and check['cause'] not in ('review_environment', 'external_service', 'unknown'),
                            'blocked/inconclusive check cannot justify deducted points')
                require(deduction.get('reason'), 'deduction needs criterion-specific impact')
                points += amount
            require(abs(item['max'] - item['score'] - points) < 0.001, 'deductions do not equal points lost')
    for advice in report['futureAdvice']:
        refs = advice.get('findingIds', [])
        require(refs and all(ref in findings for ref in refs), 'advice must reference this project findings')
        require(all(findings[ref]['verification'] != 'unverified' and findings[ref]['kind'] != 'limitation'
                    for ref in refs), 'advice cannot invent participant mistakes from review limitations')
        require(all(advice.get(key) for key in ('principle', 'why', 'how', 'successCheck')), 'advice must explain relevance, action, and success check')
        require(isinstance(advice.get('timeboxMinutes'), int) and 1 <= advice['timeboxMinutes'] <= 300,
                'advice needs a realistic five-hour timebox')
