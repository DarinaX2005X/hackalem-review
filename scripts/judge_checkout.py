"""Prepare exact Git snapshots without requiring Windows-compatible source names."""
import json
import concurrent.futures
import re
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath


def hydrate_snapshot(clone, snapshot, git):
    """Fetch only this tree, in bounded packs so model-heavy repos can resume."""
    for attempt in range(2):
        objects = git('rev-list', '--objects', '--missing=print', '--no-walk', snapshot, cwd=clone)
        missing = [line[1:] for line in objects.splitlines() if line.startswith('?')]
        if not missing:
            return
        try:
            chunks=[missing[i:i+8] for i in range(0,len(missing),8)]
            def fetch(chunk):
                git('-c', 'fetch.negotiationAlgorithm=noop', '-c', 'gc.auto=0',
                    'fetch', '--no-tags', '--no-write-fetch-head', '--no-auto-maintenance',
                    '--recurse-submodules=no', '--stdin', 'origin',
                    input='\n'.join(chunk)+'\n', cwd=clone, timeout=1800)
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(fetch,chunks))
        except (RuntimeError, subprocess.TimeoutExpired):
            if attempt: raise
    objects = git('rev-list', '--objects', '--missing=print', '--no-walk', snapshot, cwd=clone)
    if any(line.startswith('?') for line in objects.splitlines()):
        raise RuntimeError('Snapshot still has missing Git objects after fetch')


def windows_path(name):
    parts = PurePosixPath(name).parts
    if not parts or name.startswith('/') or any(p in ('.', '..') for p in parts):
        raise ValueError('Unsafe archive path: '+name)
    def component(part):
        # Also encode %, so two distinct Git paths cannot share an escaped name.
        end = len(part.rstrip(' .'))
        result = ''.join(f'%{ord(c):02X}' if c in '%<>:"\\|?*' or ord(c)<32 or i>=end else c
                         for i,c in enumerate(part))
        if re.match(r'^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', result, re.I):
            result = '%'+f'{ord(result[0]):02X}'+result[1:]
        return result
    return '/'.join(component(p) for p in parts)


def source_archive(clone, snapshot, archive, git):
    """Archive raw blobs; Git archive can apply EOL/export-ignore transformations."""
    records=git('ls-tree','-r','-z',snapshot,cwd=clone).split('\0')
    with subprocess.Popen(['git','-c',f'safe.directory={Path(clone).resolve().as_posix()}',
                           'cat-file','--batch'],cwd=clone,stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE) as process:
        try:
            with tarfile.open(archive,'w') as output:
                for record in records:
                    if not record: continue
                    metadata,name=record.split('\t',1)
                    mode,kind,oid=metadata.split()
                    windows_path(name)  # Reject absolute/traversal paths before writing.
                    if kind!='blob': raise RuntimeError('Unsupported source object: '+name)
                    process.stdin.write((oid+'\n').encode('ascii'));process.stdin.flush()
                    header=process.stdout.readline().split()
                    if len(header)!=3 or header[1]!=b'blob': raise RuntimeError('Missing blob: '+name)
                    length=int(header[2])
                    entry=tarfile.TarInfo(name);entry.mode=int(mode,8)&0o777
                    if mode=='120000':
                        entry.type=tarfile.SYMTYPE
                        entry.linkname=process.stdout.read(length).decode('utf-8')
                        output.addfile(entry)
                    else:
                        entry.size=length
                        output.addfile(entry,process.stdout)
                    if process.stdout.read(1)!=b'\n': raise RuntimeError('Incomplete blob: '+name)
            process.stdin.close()
            if process.wait(timeout=30):raise RuntimeError('Git blob export failed')
        except BaseException:
            process.kill();process.wait()
            raise


def create_checkout(clone, checkout, snapshot, git):
    marker=checkout.parent/(checkout.name+'-checkout.json')
    if checkout.exists():
        if marker.exists() and json.loads(marker.read_text())=={'snapshot':snapshot,'complete':True}:
            return
        raise RuntimeError('Incomplete checkout from an earlier attempt: '+str(checkout))
    names = git('ls-tree', '-r', '-z', '--name-only', snapshot, cwd=clone).split('\0')
    names = [name for name in names if name]
    incompatible = any(windows_path(name)!=name for name in names)
    if not incompatible:
        git('worktree', 'add', '--detach', str(checkout), snapshot, cwd=clone, timeout=1800)
        marker.write_text(json.dumps({'snapshot':snapshot,'complete':True}),encoding='utf-8')
        return
    archive = checkout.parent / (checkout.name+'-source.tar')
    source_archive(clone,snapshot,archive,git)
    git('worktree', 'add', '--no-checkout', '--detach', str(checkout), snapshot, cwd=clone)
    git('-c', 'core.protectNTFS=false', 'read-tree', snapshot, cwd=checkout)
    mapping = []
    destinations = set()
    with tarfile.open(archive) as source:
        for entry in source:
            if entry.isdir(): continue
            relative = windows_path(entry.name)
            if relative.casefold() in destinations:
                raise RuntimeError('Case-insensitive path collision: '+entry.name)
            destinations.add(relative.casefold())
            target = checkout / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if entry.isfile():
                with source.extractfile(entry) as stream, target.open('wb') as out:
                    shutil.copyfileobj(stream, out)
            elif entry.issym():
                # Original symlinks remain intact in the Linux source archive.
                target.write_text(entry.linkname, encoding='utf-8')
            else:
                raise RuntimeError('Unsupported archive entry: '+entry.name)
            if relative!=entry.name or entry.issym():
                mapping.append({'original':entry.name,'windows':relative,'symlink':entry.issym()})
    (checkout.parent/(checkout.name+'-paths.json')).write_text(json.dumps({
        'snapshot':snapshot,'archive':str(archive),'paths':mapping,
        'note':'Host-only path escaping. For runtime use the exact source archive inside a Linux container. '
               'Do not deduct points for Windows checkout limitations.'},ensure_ascii=False,indent=2),encoding='utf-8')
    marker.write_text(json.dumps({'snapshot':snapshot,'complete':True}),encoding='utf-8')
