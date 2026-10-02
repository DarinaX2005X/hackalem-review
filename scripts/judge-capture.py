"""Run a noisy check, keep full logs, and return only a bounded console excerpt."""

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def excerpt(path, max_chars=5500, max_lines=60):
    size = path.stat().st_size
    with path.open('rb') as source:
        source.seek(max(0, size - max_chars * 4))
        data = source.read()
    text = data.decode('utf-8', errors='replace')
    text = '\n'.join(text.splitlines()[-max_lines:])
    if len(text) > max_chars:
        text = '…\n' + text[-max_chars:]
    if size > len(data) or len(data) > len(text.encode('utf-8', errors='replace')):
        text = '[показан только конец полного лога]\n' + text
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--label', default='check')
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('command required after --')
    label = re.sub(r'[^a-zA-Z0-9_-]', '-', args.label)[:40] or 'check'
    folder = Path(args.output_dir).resolve()/'captures'
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    stdout_path = folder/f'{stamp}-{label}.stdout.log'
    stderr_path = folder/f'{stamp}-{label}.stderr.log'
    started = time.monotonic()
    timed_out = False
    with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
        try:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=args.timeout,
                                    stdin=subprocess.DEVNULL)
            code = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            code = 124
        except OSError as error:
            stderr.write(str(error).encode('utf-8', errors='replace'))
            code = 127
    print(f'exitCode={code}; timedOut={timed_out}; seconds={time.monotonic()-started:.1f}')
    for name, path in (('stdout', stdout_path), ('stderr', stderr_path)):
        print(f'{name}={path}; bytes={path.stat().st_size}')
        if path.stat().st_size:
            print(excerpt(path))
    return code


if __name__ == '__main__':
    sys.exit(main())
