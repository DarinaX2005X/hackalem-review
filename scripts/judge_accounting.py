"""Token totals from saved attempts, including failures; API equivalent, not a bill."""
import json
from pathlib import Path

PRICES = {
    'gpt-6-luna': (0.10, 0.01, 0.50),
    'gpt-5.6-luna': (0.20, 0.02, 1.20),
}
NOTE = ('API-эквивалент по Standard short-context: кеш уже входит во вход. '
        'Это не списание: используется квота ChatGPT. Запись кеша, надбавки и '
        'расход без usage неизвестны; reasoning не прибавляется повторно к выходу.')

def summarize(records, wave=None):
    totals = {model: dict(attempts=0, missingUsage=0, inputTokens=0,
                        cachedInputTokens=0, outputTokens=0) for model in PRICES}
    seen = set()
    for record in records:
        model = record.get('modelId')
        if model not in totals or (wave is not None and record.get('wave') != wave):
            continue
        identity = record.get('events') or (model, record.get('repoId'), record.get('attempt'))
        if identity in seen:
            continue
        seen.add(identity)
        row = totals[model]
        row['attempts'] += 1
        row['missingUsage'] += not bool(record.get('reportedTurns'))
        for key in ('inputTokens', 'cachedInputTokens', 'outputTokens'):
            row[key] += record.get(key, 0)
    for model, row in totals.items():
        inp, cached, output = PRICES[model]
        row['apiEquivalentUsd'] = ((row['inputTokens'] - row['cachedInputTokens']) * inp
                                  + row['cachedInputTokens'] * cached
                                  + row['outputTokens'] * output) / 1_000_000
    return {'wave': wave, 'models': totals, 'note': NOTE,
            'apiEquivalentUsd': sum(row['apiEquivalentUsd'] for row in totals.values())}

def load_records(root, providers):
    records, seen = [], set()
    for path in Path(root).glob('*/*-usage.jsonl'):
        for line in path.read_text(encoding='utf-8').splitlines():
            try: record = json.loads(line)
            except ValueError: continue
            records.append(record)
            seen.add(record.get('events'))
    # A killed process may leave events without the final ledger entry.
    for path in Path(root).glob('*/session-*/attempt-*.json'):
        metadata = json.loads(path.read_text(encoding='utf-8'))
        if metadata['events'] in seen:
            continue
        events = Path(metadata['events'])
        usage = providers.event_summary(events)[1] if events.exists() else {}
        records.append({**metadata, **usage})
    return records

def print_table(summary, title, emit=print):
    emit(title, flush=True)
    emit(f"{'Модель':<16} {'Сессий':>7} {'Вход':>13} {'Кеш (вход)':>13} {'Выход':>11} {'API ≈ USD':>11}", flush=True)
    for model, row in summary['models'].items():
        emit(f"{model:<16} {row['attempts']:>7} {row['inputTokens']:>13,} "
             f"{row['cachedInputTokens']:>13,} {row['outputTokens']:>11,} {row['apiEquivalentUsd']:>11.4f}", flush=True)
    emit(f"Итого API ≈ ${summary['apiEquivalentUsd']:.4f}; "
         f"сессий без usage: {sum(r['missingUsage'] for r in summary['models'].values())}.", flush=True)

def save_and_print(root, providers, wave):
    root = Path(root)
    records = load_records(root/'data/judging', providers)
    current, total = summarize(records, wave), summarize(records)
    target = root/'data/judging-waves'
    target.mkdir(parents=True, exist_ok=True)
    (target/f'{wave}-usage.json').write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')
    (root/'data/judging-usage.json').write_text(json.dumps(total, ensure_ascii=False, indent=2), encoding='utf-8')
    print_table(current, 'Токены этой пачки (включая неудачные попытки):')
    print_table(total, 'Накоплено (GPT-6 Luna — прошлые проверки, GPT-5.6 Luna — текущие):')
    print(NOTE, flush=True)

class Tee:
    """Keep the same concise console log on disk, with immediate flushing."""
    def __init__(self, stream, file):
        self.stream, self.file = stream, file
    def write(self, text):
        self.stream.write(text)
        self.file.write(text)
        self.file.flush()
    def flush(self):
        self.stream.flush()
        self.file.flush()

