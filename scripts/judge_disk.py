"""Record disk consumption at wave boundaries without deleting shared user data."""
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


def size(path):
    try: return path.stat().st_size
    except OSError: return None


def directory_size(path):
    total=0
    pending=[path]
    while pending:
        try:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    try:
                        stat=entry.stat(follow_symlinks=False)
                        if entry.is_symlink() or getattr(stat,'st_file_attributes',0)&0x400: continue
                        if entry.is_dir(follow_symlinks=False): pending.append(entry.path)
                        else: total+=stat.st_size
                    except OSError: pass
        except OSError: pass
    return total


def save_snapshot(root, work, wave, phase):
    local=Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))
    codex=Path(os.environ.get('CODEX_HOME',Path.home()/'.codex'))
    row={'at':datetime.now(timezone.utc).isoformat(),'wave':wave,'phase':phase,
         'cFreeBytes':shutil.disk_usage('C:/').free,'dFreeBytes':shutil.disk_usage(work).free,
         'dockerVhdBytes':size(local/'Docker/wsl/disk/docker_data.vhdx'),
         'pagefileBytes':size(Path('C:/pagefile.sys')),
         'codexSessionsBytes':directory_size(codex/'sessions'),
         'codexLogDbBytes':size(codex/'logs_2.sqlite'),
         'codexHistoryDbBytes':size(codex/'thread_history_1.sqlite'),
         'judgeEvidenceBytes':directory_size(root/'data/judging'),
         'uvCacheBytes':directory_size(local/'uv/cache'),
         'pipCacheBytes':directory_size(local/'pip/cache'),
         'npmCacheBytes':directory_size(local/'npm-cache'),
         'bunCacheBytes':directory_size(Path.home()/'.bun/install/cache'),
         'tempBytes':directory_size(local/'Temp'),
         'judgeWorkBytes':directory_size(work)}
    target=root/'data/disk-usage.jsonl'
    previous=None
    if target.exists():
        for line in target.read_text(encoding='utf-8').splitlines():
            try: candidate=json.loads(line)
            except ValueError: continue
            if candidate.get('wave')==wave and candidate.get('phase')=='before-wave':
                previous=candidate
    if previous:
        row['deltaFromWaveStart']={key:value-previous[key] for key,value in row.items()
            if key.endswith('Bytes') and isinstance(value,int) and isinstance(previous.get(key),int)}
    with target.open('a',encoding='utf-8') as out: out.write(json.dumps(row)+'\n')
    print(f'Disk {phase}: C free {row["cFreeBytes"]/1024**3:.2f} GiB; '
          f'D free {row["dFreeBytes"]/1024**3:.2f} GiB; details: data/disk-usage.jsonl',flush=True)
    return row
