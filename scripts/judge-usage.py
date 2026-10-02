"""Report recorded judge tokens and an API-price equivalent (not an API bill)."""

import argparse
import json
import re
from pathlib import Path

WORK = Path('D:/hackalem-review-work/waves')
PRICE = {'sol': {'input':2.0,'cached':0.2,'output':10.0},
         'luna': {'input':0.1,'cached':0.01,'output':0.5}}

def legacy_tokens(path):
    try:
        content = path.read_text(encoding='utf-8',errors='replace')
    except OSError:
        return None
    matches = re.findall(r'(?m)^tokens used\r?\n([0-9 \u00a0\u202f]+)\r?$',content,re.I)
    return int(re.sub(r'\D','',matches[-1])) if matches else None

def event_usage(path):
    usage = {'input':0,'cached':0,'output':0,'turns':0}
    with path.open(encoding='utf-8',errors='replace') as events:
        for line in events:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('type') not in ('turn.completed','turn.failed'):
                continue
            item = event.get('usage')
            if not isinstance(item,dict):
                continue
            usage['input'] += item.get('input_tokens',0)
            usage['cached'] += item.get('cached_input_tokens',item.get('input_tokens_details',{}).get('cached_tokens',0))
            usage['output'] += item.get('output_tokens',0)
            usage['turns'] += 1
    return usage

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wave',help='name of one wave directory; omit for all recorded sessions')
    parser.add_argument('--legacy',action='store_true',help='read old Sol/Luna logs on D: instead of current saved attempts')
    parser.add_argument('--json',action='store_true',help='print current usage as JSON')
    args = parser.parse_args()
    if not args.legacy:
        import judge_accounting as accounting
        import judge_providers as providers
        root=Path(__file__).resolve().parents[1]
        summary=accounting.summarize(accounting.load_records(root/'data/judging',providers),args.wave)
        if args.json:
            print(json.dumps(summary,ensure_ascii=False,indent=2))
        else:
            accounting.print_table(summary,'Измеренные токены Codex Luna:')
            print(accounting.NOTE)
        return
    if args.wave:
        selected = (WORK/args.wave).resolve()
        if selected.parent != WORK.resolve() or not selected.is_dir():
            parser.error('wave must name an existing directory directly under the waves folder')
        roots = [selected]
    else:
        roots = list(WORK.glob('*'))
    result = {model:{'legacySessions':0,'legacyTotal':0,'unmeasuredSessions':0,
                     'measuredTurns':0,'caseContextTurns':0,
                     'input':0,'cached':0,'output':0} for model in PRICE}
    for path in (path for root in roots for path in root.glob('*/session-*/stderr.log')):
        model = path.parent.name.removeprefix('session-')
        if model not in result:
            continue
        tokens = legacy_tokens(path)
        if tokens is None:
            result[model]['unmeasuredSessions'] += 1
        else:
            result[model]['legacySessions'] += 1
            result[model]['legacyTotal'] += tokens
    event_files = [(path,False) for root in roots for path in root.glob('*/session-*/events-*.jsonl')]
    if not args.wave:
        event_files.extend((path,True) for path in (WORK.parent/'case-briefs').glob('*/*/*/events-*.jsonl'))
    for path,is_context in event_files:
        model = (path.parent.parent.name if is_context else path.parent.name.removeprefix('session-'))
        if model not in result:
            continue
        usage = event_usage(path)
        if not usage['turns']:
            result[model]['unmeasuredSessions'] += 1
        result[model]['measuredTurns'] += usage['turns']
        if is_context:
            result[model]['caseContextTurns'] += usage['turns']
        for field in ('input','cached','output'):
            result[model][field] += usage[field]
    measured_cost = 0
    for model, row in result.items():
        price = PRICE[model]
        row['measuredApiEquivalentUsd'] = round(((row['input']-row['cached'])*price['input']
                                                  +row['cached']*price['cached']
                                                  +row['output']*price['output'])/1_000_000,2)
        measured_cost += row['measuredApiEquivalentUsd']
    estimates = {}
    for output_share in (0.1,0.2,0.3):
        total = measured_cost
        for model,row in result.items():
            price = PRICE[model]
            legacy = row['legacyTotal']
            total += legacy*((1-output_share)*price['input']+output_share*price['output'])/1_000_000
        estimates[f'{round(output_share*100)}% output, legacy uncached'] = round(total,2)
    missing=sum(row['unmeasuredSessions'] for row in result.values())
    note=('Usage отсутствует для некоторых завершившихся ошибкой сессий; 0 учтённых токенов '
          'не доказывает 0 фактически использованных или оплаченных токенов.' if missing else
          'Числа из event usage; это эквивалент стоимости API, а не выписка по счёту.')
    print(json.dumps({'wave':args.wave,'models':result,
                      'recordedTotalTokens':sum(r['legacyTotal']+r['input']+r['output'] for r in result.values()),
                      'apiEquivalentUsdScenarios':estimates,
                      'note':note+' Старые логи содержат только общее число токенов.'},
                     ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
