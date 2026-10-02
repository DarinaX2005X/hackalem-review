"""Exercise compaction/recovery control flow with every system command mocked."""
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SHELL=shutil.which('pwsh') or shutil.which('powershell.exe')


@unittest.skipUnless(SHELL,'PowerShell unavailable')
class CompactionTest(unittest.TestCase):
    def run_compaction(self,fail=False,active=False,cache_fail=False):
        source=(ROOT/'scripts/compact-docker-vhd.ps1').read_text(encoding='utf-8')
        # Elevation is outside the tested body. No Docker/WSL/Hyper-V command runs.
        body=source[source.index('New-Item -ItemType Directory'):]
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);(root/'disk').write_bytes(b'fixture')
            (root/'cleanup-judge-caches.ps1').write_text("Mark 'cache-cleanup'"+
                ("; throw 'fixture cache locked'" if cache_fail else ''),encoding='utf-8')
            setup=r'''
$ErrorActionPreference='Stop'
$logPath=Join-Path $PSScriptRoot 'transcript'
$diskPath=Join-Path $PSScriptRoot 'disk'
$trace=Join-Path $PSScriptRoot 'trace'
function Mark($value) { Add-Content -LiteralPath $trace -Value $value }
function Start-Transcript { param($Path,[switch]$Append) }
function Stop-Transcript {}
function Import-Module { param($Name,$ErrorAction) }
function docker {
 $global:LASTEXITCODE=0
 Mark ('docker '+($args -join ' '))
 if ($args[0] -eq 'ps' -and ACTIVE) { 'existing-container' }
}
function wsl { $global:LASTEXITCODE=0; Mark ('wsl '+($args -join ' ')) }
function Mount-VHD { param($Path,[switch]$ReadOnly,[switch]$NoDriveLetter,$ErrorAction)
 if (-not $ReadOnly -or -not $NoDriveLetter) { throw 'Unsafe mount' }; Mark 'mount-readonly' }
function Optimize-VHD { param($Path,$Mode,$ErrorAction)
 Mark ('optimize '+$Mode); if (FAILURE) { throw 'simulated optimization failure' } }
function Dismount-VHD { param($Path,$ErrorAction); Mark 'dismount' }
'''.replace('ACTIVE','$true' if active else '$false').replace('FAILURE','$true' if fail else '$false')
            script=root/'test.ps1';script.write_text(setup+body,encoding='utf-8-sig')
            result=subprocess.run([SHELL,'-NoProfile','-NonInteractive','-File',str(script)],
                                  capture_output=True,timeout=30)
            trace=(root/'trace').read_text(encoding='utf-8-sig').splitlines()
            return result.returncode,trace

    def test_trim_then_readonly_compact_then_detach_then_restart(self):
        code,trace=self.run_compaction()
        self.assertEqual(code,0)
        self.assertLess(trace.index('cache-cleanup'),next(i for i,v in enumerate(trace) if 'fstrim -v /mnt/docker-desktop-disk' in v))
        self.assertLess(trace.index('mount-readonly'),trace.index('optimize Full'))
        self.assertLess(trace.index('optimize Full'),trace.index('dismount'))
        self.assertLess(trace.index('dismount'),trace.index('docker desktop start --timeout 180'))

    def test_failed_compaction_still_detaches_and_restarts(self):
        code,trace=self.run_compaction(fail=True)
        self.assertEqual(code,1)
        self.assertEqual(trace[-2:],['dismount','docker desktop start --timeout 180'])

    def test_active_containers_are_not_interrupted(self):
        code,trace=self.run_compaction(active=True)
        self.assertEqual(code,1)
        self.assertEqual(trace,['docker ps --quiet'])

    def test_cache_failure_does_not_skip_compaction_and_restart(self):
        code,trace=self.run_compaction(cache_fail=True)
        self.assertEqual(code,1)
        self.assertIn('optimize Full',trace)
        self.assertEqual(trace[-2:],['dismount','docker desktop start --timeout 180'])
