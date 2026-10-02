"""Give the current judge validation feedback without reading other reports."""
import argparse
import importlib.util
import json
from pathlib import Path
import jsonschema
from review_policy import validate_report_policy

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    try:
        report=json.loads(args.report.read_text(encoding='utf-8-sig'))
        schema=json.loads(Path(__file__).with_name('judge-report.schema.json').read_text(encoding='utf-8'))
        jsonschema.validate(report,schema)
        validate_report_policy(report,require_current=True,publication=True)
        for name in ('global','case'):
            scale=report.get(name)
            if scale and abs(sum(c['score'] for c in scale['criteria'])-scale['total'])>0.01:
                raise ValueError(f'{name}: criterion sum differs from total')
        expected=(report['global']['total']+report['case']['total'])/2 if report.get('case') else report['global']['total']
        if abs(expected-report['judgeScore'])>0.01:raise ValueError('judgeScore differs from rubric totals')
        spec=importlib.util.spec_from_file_location('publish_reviews',Path(__file__).with_name('publish-reviews.py'))
        publisher=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(publisher)
        publisher.validate_judge(report,report['repoId'],report['model'])
        print('REPORT_VALID')
    except (OSError,ValueError,KeyError,jsonschema.ValidationError) as error:
        print('REPORT_INVALID:',str(error)[:1500])
        print('Correct the report using your own evidence. Do not invent findings or change scores merely to pass validation.')
        raise SystemExit(1)
