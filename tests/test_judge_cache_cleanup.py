"""Only delete generated fixtures; never touch real caches or running judges."""
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SHELL=shutil.which('pwsh') or shutil.which('powershell.exe')


@unittest.skipUnless(SHELL,'PowerShell unavailable')
class CacheCleanupTest(unittest.TestCase):
    def run_fixture(self, body):
        with tempfile.TemporaryDirectory() as directory:
            folder=pathlib.Path(directory)
            source=ROOT/'scripts/cleanup-judge-caches.ps1'
            script=folder/'fixture.ps1'
            script.write_text(". '"+str(source).replace("'","''")+"'\n"+body,encoding='utf-8-sig')
            result=subprocess.run([SHELL,'-NoProfile','-NonInteractive','-File',str(script)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_cleanup_boundary_rejects_active_mismatched_and_completed_waves(self):
        self.run_fixture('''
$progress=[pscustomobject]@{lastWave='wave'}
$live=[pscustomobject]@{wave='wave';pid=$PID}
if (Test-JudgeCacheBoundary $progress $live) { throw 'active process accepted' }
function Get-Process { param($Id,$ErrorAction) }
if (-not (Test-JudgeCacheBoundary $progress $live)) { throw 'inactive boundary rejected' }
$live.wave='other'
if (Test-JudgeCacheBoundary $progress $live) { throw 'mismatched wave accepted' }
$live.wave='wave'
$progress | Add-Member -NotePropertyName cleanupSucceeded -NotePropertyValue $false
if (Test-JudgeCacheBoundary $progress $live) { throw 'finished cleanup accepted' }
''')

    def test_only_validated_fixture_cache_is_removed(self):
        self.run_fixture('''
$cache=Join-Path $PSScriptRoot 'cache'
New-Item -ItemType Directory -Path $cache | Out-Null
[IO.File]::WriteAllBytes((Join-Path $cache 'entry'),[byte[]](1,2,3))
$bytes=Clear-JudgeCacheDirectory $cache $PSScriptRoot
if ($bytes -ne 3 -or (Test-Path -LiteralPath $cache)) { throw 'cache was not removed' }
$outside=Join-Path $PSScriptRoot 'outside'
New-Item -ItemType Directory -Path $outside | Out-Null
$rejected=$false
try { Clear-JudgeCacheDirectory $outside $cache } catch { $rejected=$true }
if (-not $rejected -or -not (Test-Path -LiteralPath $outside)) { throw 'outside path affected' }
''')

    def test_junction_inside_cache_is_unlinked_without_deleting_target(self):
        self.run_fixture('''
$cache=Join-Path $PSScriptRoot 'cache'
$outside=Join-Path $PSScriptRoot 'outside'
New-Item -ItemType Directory -Path $cache,$outside | Out-Null
[IO.File]::WriteAllText((Join-Path $outside 'keep'),'keep')
New-Item -ItemType Junction -Path (Join-Path $cache 'redirect') -Target $outside | Out-Null
Clear-JudgeCacheDirectory $cache $PSScriptRoot
if ((Test-Path -LiteralPath $cache) -or -not (Test-Path -LiteralPath (Join-Path $outside 'keep'))) { throw 'junction traversal' }
New-Item -ItemType Junction -Path $cache -Target $outside | Out-Null
$rejected=$false
try { Clear-JudgeCacheDirectory $cache $PSScriptRoot } catch { $rejected=$true }
if (-not $rejected -or -not (Test-Path -LiteralPath (Join-Path $outside 'keep'))) { throw 'redirected root accepted' }
''')
