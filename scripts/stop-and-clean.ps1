param([switch]$Elevated)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$resultPath = Join-Path $projectRoot 'data\stop-and-clean-result.json'
$logPath = Join-Path $projectRoot 'data\stop-and-clean.log'
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    if ($Elevated) { throw 'Administrator rights were not granted.' }
    $hostExecutable = (Get-Process -Id $PID).Path
    $arguments = @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"",'-Elevated')
    $child = Start-Process -FilePath $hostExecutable -ArgumentList $arguments -Verb RunAs -WindowStyle Hidden -PassThru
    # Wait only for the cleanup host, not Docker Desktop descendants it starts.
    $child.WaitForExit()
    exit $child.ExitCode
}

Start-Transcript -LiteralPath $logPath -Append | Out-Null
$result = [ordered]@{startedAt=(Get-Date -Format o); administrator=$true; queueStopped=$false; workDeleted=$false; siteReviewsDeleted=$false; dockerClean=$false; compacted=$false; dockerRunning=$false; errors=@()}
try {
    $workTarget = 'D:\hackalem-review-work'
    $reviewTargets = @((Join-Path $projectRoot 'web\data\reviews'),(Join-Path $projectRoot 'docs\data\reviews'))
    # Validate exact absolute targets before any recursive filesystem operation.
    if ([IO.Path]::GetFullPath($workTarget) -ne 'D:\hackalem-review-work') { throw 'Unexpected work directory.' }
    if (Test-Path -LiteralPath $workTarget) {
        $item=Get-Item -LiteralPath $workTarget -Force
        if ($item.FullName -ne $workTarget -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Work target is redirected.' }
    }
    foreach ($target in $reviewTargets) {
        $resolved=[IO.Path]::GetFullPath($target)
        if (-not $resolved.StartsWith($projectRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Review target outside project.' }
        if (Test-Path -LiteralPath $target) {
            if ((Get-Item -LiteralPath $target -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Review target is redirected.' }
        }
        Write-Output "Review deletion target: $resolved"
    }
    Write-Output "Work deletion target: $workTarget"

    $processes=Get-CimInstance Win32_Process
    $roots=@($processes | Where-Object { $_.Name -match '^python(?:w)?\.exe$' -and $_.CommandLine -like "*$projectRoot*" -and $_.CommandLine -match 'judge-(all|wave)\.py' })
    foreach ($process in $roots) {
        if (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue) {
            Write-Output "Stopping judging process tree PID=$($process.ProcessId)"
            & taskkill.exe /PID $process.ProcessId /T /F
        }
    }
    # A previous queue may have died while a provider child survived it.
    $orphans=@(Get-CimInstance Win32_Process | Where-Object {
        ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($workTarget+'\',[StringComparison]::OrdinalIgnoreCase)) -or
        ($_.Name -match '^(qodercli.*|opencode|python|cmd|node)\.exe$' -and
        ($_.CommandLine -like "*$workTarget*" -or $_.CommandLine -like "*$projectRoot\data\judging\*"))
    })
    foreach ($process in $orphans) {
        if (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue) { & taskkill.exe /PID $process.ProcessId /T /F }
    }
    # Old Vite servers may have only relative argv; identify them by the native
    # module actually loaded from the participant workspace, not by image name.
    foreach ($process in @(Get-Process -Name node -ErrorAction SilentlyContinue)) {
        $ownedModules=@($process.Modules | Where-Object {
            $_.FileName.StartsWith($workTarget+'\',[StringComparison]::OrdinalIgnoreCase)
        })
        if ($ownedModules.Count) {
            Write-Output "Stopping participant Node PID=$($process.Id), module=$($ownedModules[0].FileName)"
            & taskkill.exe /PID $process.Id /T /F
        }
    }
    . (Join-Path $PSScriptRoot 'process-workdir.ps1')
    foreach ($process in @(Get-CimInstance Win32_Process)) {
        if ($process.ProcessId -eq $PID) { continue }
        $workingDirectory=[HackAlemProcessDirectory]::Get([int]$process.ProcessId)
        if ($workingDirectory -and ($workingDirectory.TrimEnd('\') -eq $workTarget -or
            $workingDirectory.StartsWith($workTarget+'\',[StringComparison]::OrdinalIgnoreCase))) {
            Write-Output "Stopping participant process PID=$($process.ProcessId), cwd=$workingDirectory"
            & taskkill.exe /PID $process.ProcessId /T /F
        }
    }
    Start-Sleep -Seconds 2
    $remaining=@(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(qodercli.*|opencode|python|cmd|node)\.exe$' -and
        (($_.CommandLine -like "*$projectRoot*" -and $_.CommandLine -match 'judge-(all|wave)\.py') -or $_.CommandLine -like "*$workTarget*")
    })
    if ($remaining.Count) { throw "Judging processes still running: $($remaining.ProcessId -join ',')" }
    $result.queueStopped=$true

    foreach ($target in $reviewTargets) {
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        @{methodVersion=4;reviews=@();partialReviews=@()} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $target 'index.json') -Encoding utf8
    }
    $result.siteReviewsDeleted=$true
    @{active=@();waiting=0;finished=0;accepted=0;failures=0;stopped=$true;reason='Stopped and cleaned at user request';updatedAt=(Get-Date -Format o)} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $projectRoot 'data\judging-live.json') -Encoding utf8
    $progressPath=Join-Path $projectRoot 'data\judging-progress.json'
    if (Test-Path -LiteralPath $progressPath) {
        $progress=Get-Content -LiteralPath $progressPath -Raw | ConvertFrom-Json
        $progress.completed=0
        $progress.updatedAt=Get-Date -Format o
        $progress | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $progressPath -Encoding utf8
    }

    & docker info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) {
        & docker desktop start --timeout 180
        if ($LASTEXITCODE -ne 0) { throw 'Docker could not start for cleanup.' }
    }
    $containerIds=@(& docker ps -aq)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot list Docker containers.' }
    if ($containerIds.Count) {
        & docker rm --force --volumes @containerIds
        if ($LASTEXITCODE -ne 0) { throw 'Could not remove Docker containers.' }
    }
    & docker system prune --all --force --volumes
    if ($LASTEXITCODE -ne 0) { throw 'Docker system prune failed.' }
    & docker volume prune --all --force
    if ($LASTEXITCODE -ne 0) { throw 'Docker volume prune failed.' }
    & docker builder prune --all --force
    if ($LASTEXITCODE -ne 0) { throw 'Docker builder prune failed.' }
    $result.dockerClean=$true

    if (Test-Path -LiteralPath $workTarget) { Remove-Item -LiteralPath $workTarget -Recurse -Force }
    $result.workDeleted= -not (Test-Path -LiteralPath $workTarget)

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'compact-docker-vhd.ps1') -Elevated
    if ($LASTEXITCODE -ne 0) { throw 'Docker VHD compaction failed; inspect docker-compact.log.' }
    $result.compacted=$true
}
catch {
    $result.errors+= $_.Exception.Message
    Write-Output "CLEANUP_ERROR=$($_.Exception.Message)"
}
finally {
    & docker info --format '{{.ServerVersion}}'
    if ($LASTEXITCODE -ne 0) { & docker desktop start --timeout 180 }
    & docker info --format '{{.ServerVersion}}'
    $result.dockerRunning=($LASTEXITCODE -eq 0)
    $result.finishedAt=Get-Date -Format o
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8
    Stop-Transcript | Out-Null
}
if ($result.errors.Count -or -not $result.dockerRunning) { exit 1 }
