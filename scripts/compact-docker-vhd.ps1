param([switch]$Elevated)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$logPath = Join-Path $projectRoot 'data\docker-compact.log'
$diskPath = Join-Path $env:LOCALAPPDATA 'Docker\wsl\disk\docker_data.vhdx'

$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    if ($Elevated) { throw 'UAC elevation did not grant administrator rights.' }
    $powershell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Elevated')
    try {
        $process = Start-Process -FilePath $powershell -ArgumentList $arguments -Verb RunAs -WindowStyle Hidden -PassThru
        # Wait for the helper only, not Docker Desktop descendants it starts.
        $process.WaitForExit()
        exit $process.ExitCode
    }
    catch {
        Write-Error "Administrator approval was not granted: $($_.Exception.Message)"
        exit 1
    }
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logPath) | Out-Null
Start-Transcript -Path $logPath -Append | Out-Null
$failed = $false
$stopped = $false
$mounted = $false
try {
    if (-not (Test-Path -LiteralPath $diskPath -PathType Leaf)) { throw "Docker disk not found: $diskPath" }
    Write-Output "BeforeGiB=$([math]::Round((Get-Item -LiteralPath $diskPath).Length / 1GB, 2))"
    $running = @(docker ps --quiet)
    if ($LASTEXITCODE -ne 0) { throw 'Docker must be running to trim its Linux filesystem before compaction.' }
    if ($running.Count -gt 0) { throw 'Active containers remain; refusing to interrupt them for disk compaction.' }
    # This script is loaded afresh at each wave boundary, also by an already
    # running queue. The helper additionally refuses cleanup while its wave lives.
    try { & (Join-Path $PSScriptRoot 'cleanup-judge-caches.ps1') }
    catch { $failed = $true; Write-Output "CACHE_CLEANUP_ERROR=$($_.Exception.Message)" }
    # Tell VHDX which ext4 blocks are free; removing Docker images alone does not.
    wsl -d docker-desktop -u root -- sh -c 'sync && fstrim -v /mnt/docker-desktop-disk'
    if ($LASTEXITCODE -ne 0) { throw 'Docker filesystem trim failed; disk compaction was not attempted.' }
    $stopped = $true
    docker desktop stop --timeout 180
    if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop did not stop cleanly.' }
    wsl --terminate docker-desktop 2>$null
    Import-Module Hyper-V -ErrorAction Stop
    # Without a read-only attachment Full silently falls back to Prezeroed.
    Mount-VHD -Path $diskPath -ReadOnly -NoDriveLetter -ErrorAction Stop
    $mounted = $true
    Optimize-VHD -Path $diskPath -Mode Full -ErrorAction Stop
    Write-Output "AfterGiB=$([math]::Round((Get-Item -LiteralPath $diskPath).Length / 1GB, 2))"
}
catch {
    $failed = $true
    Write-Output "COMPACT_ERROR=$($_.Exception.Message)"
}
finally {
    if ($mounted) {
        try { Dismount-VHD -Path $diskPath -ErrorAction Stop }
        catch { $failed = $true; Write-Output "DISMOUNT_ERROR=$($_.Exception.Message)" }
    }
    if ($stopped) {
        docker desktop start --timeout 180
        if ($LASTEXITCODE -ne 0) { $failed = $true }
        Write-Output "DOCKER_START_EXIT=$LASTEXITCODE"
    }
    Stop-Transcript | Out-Null
}
if ($failed) { exit 1 }
