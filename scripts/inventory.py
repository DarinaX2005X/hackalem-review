import concurrent.futures
import json
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
RAW.mkdir(parents=True, exist_ok=True)

def page(number):
    path = RAW / f'repos-page-{number}.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8-sig'))
    url = f'https://api.github.com/orgs/BAITC-Hacks/repos?per_page=100&page={number}&type=public'
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'hackalem-review', 'Accept': 'application/vnd.github+json'})
            with urllib.request.urlopen(req, timeout=60) as response:
                items = json.load(response)
            path.write_text(json.dumps(items, ensure_ascii=False), encoding='utf-8')
            return items
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pages = list(pool.map(page, range(1, 38)))
    rows = {r['id']: r for p in pages for r in p}
    fields = ['id', 'name', 'full_name', 'html_url', 'description', 'size', 'language', 'created_at', 'pushed_at', 'updated_at', 'default_branch', 'archived', 'fork', 'topics']
    inventory = [{k: r.get(k) for k in fields} for r in rows.values()]
    (ROOT / 'data' / 'inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'repositories': len(inventory), 'size_positive': sum(r['size'] > 0 for r in inventory), 'pushed_since_start': sum(r['pushed_at'] >= '2026-09-23T08:00:00Z' for r in inventory), 'nonempty_pushed_since_start': sum(r['size'] > 0 and r['pushed_at'] >= '2026-09-23T08:00:00Z' for r in inventory)}, ensure_ascii=False))
