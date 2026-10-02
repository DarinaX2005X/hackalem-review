"""Capture one actual command, its exit code and logs for a report check ID."""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--label',default='check')
    parser.add_argument('--check-id',required=True)
    parser.add_argument('--timeout',type=int,default=1800)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command[1:] if args.command[:1]==['--'] else args.command
    if not command:parser.error('Command required after --')
    root=Path(__file__).resolve().parent.parent/'results';folder=Path(args.output_dir).resolve()
    if not folder.is_relative_to((root/'evidence').resolve()):parser.error('Output must be inside results/evidence/<repoId>')
    label=re.sub('[^A-Za-z0-9_-]','-',args.label)[:50]
    started=datetime.now(timezone.utc);stamp=started.strftime('%Y%m%dT%H%M%S%f')
    captures=folder/'captures';captures.mkdir(parents=True,exist_ok=True)
    stdout=captures/f'{stamp}-{label}.stdout.log';stderr=captures/f'{stamp}-{label}.stderr.log'
    timeout=False;clock=time.monotonic()
    with stdout.open('wb') as out,stderr.open('wb') as err:
        try:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=os.name!='nt')
            try:code=process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timeout=True
                if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                else:os.killpg(process.pid,signal.SIGKILL)
                process.wait();code=124
        except OSError as error:err.write(str(error).encode());code=127
    record={'id':args.check_id,'command':command,'startedAt':started.isoformat(),'endedAt':datetime.now(timezone.utc).isoformat(),
        'exitCode':code,'timedOut':timeout,'seconds':round(time.monotonic()-clock,3),
        'stdout':stdout.relative_to(root).as_posix(),'stderr':stderr.relative_to(root).as_posix()}
    with (folder/'checks.jsonl').open('a',encoding='utf-8') as out:out.write(json.dumps(record,ensure_ascii=False)+'\n')
    print(json.dumps(record,ensure_ascii=False))
    for path in [stdout,stderr]:
        with path.open('rb') as stream:stream.seek(max(0,path.stat().st_size-16000));tail=stream.read().decode('utf-8',errors='replace')[-5000:]
        if tail:print(path.name+' (tail):\n'+tail)
    return code


if __name__=='__main__':sys.exit(main())
