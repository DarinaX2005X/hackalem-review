"""Keep the local catalog available independently of the judging terminal."""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def task_name(port):
    workspace = hashlib.sha256(str(ROOT).lower().encode()).hexdigest()[:10]
    return f'HackAlem-Catalog-{workspace}-{port}'


def supervise(port):
    """Run under Task Scheduler, outside the judging process tree."""
    node = shutil.which('node')
    if not node:
        return False
    log = ROOT/'data/local-server.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('ab', buffering=0) as output:
        while True:
            if healthy(port):
                time.sleep(5)
                continue
            output.write(f'\n[{time.strftime("%Y-%m-%d %H:%M:%S")}] Starting catalog supervisor={os.getpid()}\n'.encode())
            process = subprocess.Popen(
                [node, str(ROOT/'scripts/server.mjs')], cwd=ROOT,
                stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                env={**os.environ, 'PORT': str(port)})
            code = process.wait()
            output.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Catalog exited code={code}; retry in 5 seconds\n'.encode())
            time.sleep(5)


def start_windows_task(port):
    result = subprocess.run([
        'powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', str(ROOT/'scripts/start-catalog-task.ps1'),
        '-PythonPath', sys.executable, '-RootPath', str(ROOT),
        '-Port', str(port), '-TaskName', task_name(port)],
        capture_output=True, text=True, errors='replace', timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        print('Independent catalog startup failed: ' + result.stderr[-1500:], file=sys.stderr)
        return False
    return True


def healthy(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=2) as response:
            return response.status == 200 and b'HackAlem |' in response.read(4096)
    except (OSError, urllib.error.URLError):
        return False


def ensure(port=4173):
    if healthy(port):
        print(f'Catalog ready: http://127.0.0.1:{port}/')
        return True
    node = shutil.which('node')
    if not node:
        print('Cannot start catalog: node not found.', file=sys.stderr)
        return False
    if os.name == 'nt':
        # DETACHED_PROCESS only detaches the console: taskkill /T and Windows
        # job objects can still kill descendants. Scheduler owns this process.
        if not start_windows_task(port):
            return False
        for _ in range(24):
            if healthy(port):
                print(f'Catalog ready: http://127.0.0.1:{port}/ (independent Windows task)')
                return True
            time.sleep(0.25)
        print('Catalog task started but HTTP is unavailable; inspect data/local-server.log.', file=sys.stderr)
        return False
    log = ROOT/'data/local-server.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('ab') as output:
        process = subprocess.Popen([node, str(ROOT/'scripts/server.mjs')], cwd=ROOT,
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                   start_new_session=True,
                                   env={**os.environ, 'PORT':str(port)})
    for _ in range(20):
        if healthy(port):
            print(f'Catalog ready: http://127.0.0.1:{port}/ (PID {process.pid})')
            return True
        if process.poll() is not None:
            break
        time.sleep(0.25)
    print(f'Catalog did not start; inspect {log}.', file=sys.stderr)
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4173)
    parser.add_argument('--serve', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    sys.exit(0 if (supervise(args.port) if args.serve else ensure(args.port)) else 1)
