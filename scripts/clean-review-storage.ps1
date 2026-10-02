param([switch]$Elevated)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    if ($Elevated) { throw 'Administrator rights were not granted.' }
    $arguments = @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"",'-Elevated')
    $child = Start-Process powershell.exe -ArgumentList $arguments -Verb RunAs -WindowStyle Hidden -PassThru
    $child.WaitForExit()
    exit $child.ExitCode
}

$diskPath = Join-Path $env:LOCALAPPDATA 'Docker\wsl\disk\docker_data.vhdx'
$resultPath = Join-Path $projectRoot 'data\storage-cleanup-result.json'
$result = [ordered]@{ startedAt=[DateTime]::UtcNow.ToString('o'); administrator=$true;
    cFreeBeforeBytes=(Get-PSDrive C).Free; dockerBeforeBytes=(Get-Item -LiteralPath $diskPath).Length;
    caches=@(); errors=@(); dockerClean=$false; compacted=$false }
Start-Transcript -Path (Join-Path $projectRoot 'data\storage-cleanup.log') -Append | Out-Null
try {
    $judges = @(Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -match '^python(?:w)?\.exe$' -and $_.CommandLine -match 'judge-(all|wave)\.py') -or
        ($_.Name -eq 'codex.exe' -and $_.CommandLine -like '*D:\hackalem-review-work*')
    })
    if ($judges.Count) { throw "Judges are still running: $($judges.ProcessId -join ',')" }
    $livePath = Join-Path $projectRoot 'data\judging-live.json'
    if (Test-Path -LiteralPath $livePath) {
        $live = Get-Content -LiteralPath $livePath -Raw | ConvertFrom-Json
        if ($live.pid -and (Get-Process -Id $live.pid -ErrorAction SilentlyContinue)) { throw 'Wave process is still running.' }
    }
    docker info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) { throw 'Docker unavailable.' }
    $containers = @(docker ps -aq)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate Docker containers.' }
    if ($containers.Count) {
        docker rm --force --volumes @containers
        if ($LASTEXITCODE -ne 0) { throw 'Cannot remove Docker containers.' }
    }
    docker system prune --all --force --volumes
    if ($LASTEXITCODE -ne 0) { throw 'Docker system cleanup failed.' }
    docker volume prune --all --force
    if ($LASTEXITCODE -ne 0) { throw 'Docker volume cleanup failed.' }
    docker builder prune --all --force
    if ($LASTEXITCODE -ne 0) { throw 'Docker build cache cleanup failed.' }
    $result.dockerClean=$true

    . (Join-Path $PSScriptRoot 'cleanup-judge-caches.ps1')
    $localRoot = [IO.Path]::GetFullPath($env:LOCALAPPDATA)
    $profileRoot = [IO.Path]::GetFullPath($env:USERPROFILE)
    $targets = @(
        @{ Path=(Join-Path $localRoot 'uv\cache'); Parent=$localRoot },
        @{ Path=(Join-Path $localRoot 'pip\cache'); Parent=$localRoot },
        @{ Path=(Join-Path $localRoot 'npm-cache'); Parent=$localRoot },
        @{ Path=(Join-Path $profileRoot '.bun\install\cache'); Parent=$profileRoot }
    )
    foreach ($target in $targets) {
        try {
            $bytes = Clear-JudgeCacheDirectory $target.Path $target.Parent
            $result.caches += @{ path=$target.Path; removedLogicalBytes=$bytes; status='cleared' }
            Write-Output "CACHE_CLEARED=$($target.Path); logicalGiB=$([math]::Round($bytes/1GB,3))"
        }
        catch { $result.errors += "Cache $($target.Path): $($_.Exception.Message)" }
    }
    powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'compact-docker-vhd.ps1') -Elevated
    if ($LASTEXITCODE -ne 0) { throw 'Docker compaction failed; inspect docker-compact.log.' }
    $result.compacted=$true
}
catch { $result.errors += $_.Exception.Message; Write-Output "CLEANUP_ERROR=$($_.Exception.Message)" }
finally {
    $result.cFreeAfterBytes=(Get-PSDrive C).Free
    $result.dockerAfterBytes=(Get-Item -LiteralPath $diskPath).Length
    $result.finishedAt=[DateTime]::UtcNow.ToString('o')
    $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Stop-Transcript | Out-Null
}
if ($result.errors.Count) { exit 1 }
