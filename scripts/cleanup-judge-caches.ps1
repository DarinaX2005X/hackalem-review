# Loaded at the existing end-of-wave compaction boundary, including by a queue
# started before this helper was added. Never run shared cleanup per participant.
$ErrorActionPreference = 'Stop'

function Test-JudgeCacheBoundary($Progress, $Live) {
    if (-not $Progress -or -not $Live -or -not $Progress.lastWave -or
        $Progress.lastWave -ne $Live.wave -or -not $Live.pid -or
        $Progress.PSObject.Properties.Name -contains 'cleanupSucceeded') { return $false }
    if (Get-Process -Id $Live.pid -ErrorAction SilentlyContinue) { return $false }
    return $true
}

function Clear-JudgeCacheDirectory([string]$Path, [string]$AllowedParent) {
    $absolute = [IO.Path]::GetFullPath($Path)
    $parent = [IO.Path]::GetFullPath($AllowedParent).TrimEnd('\')
    if (-not $absolute.StartsWith($parent+'\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Cache is outside its allowed parent: $absolute"
    }
    # Validate every existing ancestor and descendant before recursive deletion.
    # Do not follow junctions/symlinks into other directories.
    $ancestor = $absolute
    while ($ancestor) {
        if (Test-Path -LiteralPath $ancestor) {
            if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Redirected cache path: $ancestor"
            }
        }
        $ancestor = [IO.Path]::GetDirectoryName($ancestor)
    }
    if (-not (Test-Path -LiteralPath $absolute)) { return 0L }
    $pending = [Collections.Generic.Stack[string]]::new()
    $pending.Push($absolute)
    $links = [Collections.Generic.List[object]]::new()
    $bytes = 0L
    while ($pending.Count) {
        foreach ($item in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                $links.Add($item)
                continue
            }
            if ($item.PSIsContainer) { $pending.Push($item.FullName) }
            else { $bytes += $item.Length }
        }
    }
    # Bun caches contain junctions. Delete only each link, never its target.
    # Directory.Delete without recursion removes a junction itself on Windows.
    foreach ($link in $links) {
        if ($link.PSIsContainer) { [IO.Directory]::Delete($link.FullName) }
        else { Remove-Item -LiteralPath $link.FullName -Force }
    }
    Remove-Item -LiteralPath $absolute -Recurse -Force
    if (Test-Path -LiteralPath $absolute) { throw "Cache files remain: $absolute" }
    return $bytes
}

function Invoke-JudgeCacheCleanup {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $progressPath = Join-Path $projectRoot 'data\judging-progress.json'
    $livePath = Join-Path $projectRoot 'data\judging-live.json'
    if (-not (Test-Path -LiteralPath $progressPath) -or -not (Test-Path -LiteralPath $livePath)) { return }
    $progress = Get-Content -LiteralPath $progressPath -Raw | ConvertFrom-Json
    $live = Get-Content -LiteralPath $livePath -Raw | ConvertFrom-Json
    if (-not (Test-JudgeCacheBoundary $progress $live)) {
        Write-Output 'CACHE_CLEANUP_SKIPPED=not an inactive, unfinished wave cleanup boundary'
        return
    }
    $localRoot = [IO.Path]::GetFullPath($env:LOCALAPPDATA)
    $profileRoot = [IO.Path]::GetFullPath($env:USERPROFILE)
    # Explicit allowlist only. No Temp, installed packages, reports or Codex history.
    $targets = @(
        @{ Path=(Join-Path $localRoot 'uv\cache'); Parent=$localRoot },
        @{ Path=(Join-Path $localRoot 'pip\cache'); Parent=$localRoot },
        @{ Path=(Join-Path $localRoot 'npm-cache'); Parent=$localRoot },
        @{ Path=(Join-Path $profileRoot '.bun\install\cache'); Parent=$profileRoot }
    )
    $beforeFree = (Get-PSDrive -Name C).Free
    $rows = @()
    foreach ($target in $targets) {
        try {
            $bytes = Clear-JudgeCacheDirectory $target.Path $target.Parent
            $rows += @{ path=$target.Path; removedLogicalBytes=$bytes; status='cleared' }
            Write-Output "CACHE_CLEARED=$($target.Path); logicalGiB=$([math]::Round($bytes/1GB,3))"
        }
        catch {
            $rows += @{ path=$target.Path; status='failed'; error=$_.Exception.Message }
            Write-Output "CACHE_ERROR=$($target.Path); $($_.Exception.Message)"
        }
    }
    $afterFree = (Get-PSDrive -Name C).Free
    $record = @{ at=[DateTime]::UtcNow.ToString('o'); wave=$progress.lastWave;
        cFreeBeforeBytes=$beforeFree; cFreeAfterBytes=$afterFree;
        cFreeDeltaBytes=($afterFree-$beforeFree); caches=$rows }
    $record | ConvertTo-Json -Depth 5 -Compress | Add-Content -LiteralPath (Join-Path $projectRoot 'data\cache-cleanup.jsonl') -Encoding UTF8
    Write-Output "CACHE_C_FREE_DELTA_GIB=$([math]::Round(($afterFree-$beforeFree)/1GB,3))"
    if (@($rows | Where-Object { $_.status -eq 'failed' }).Count) { throw 'Some dependency caches could not be cleared; see data/cache-cleanup.jsonl.' }
}

if ($MyInvocation.InvocationName -ne '.') { Invoke-JudgeCacheCleanup }
