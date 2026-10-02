param([Parameter(Mandatory=$true)][string]$WavePath,
      [Parameter(Mandatory=$true)][string]$RepoId)
$ErrorActionPreference = 'Stop'
$workRoot = 'D:\hackalem-review-work'
$waveRoot = [IO.Path]::GetFullPath((Join-Path $workRoot 'waves'))
$wave = [IO.Path]::GetFullPath($WavePath)
if ([IO.Path]::GetDirectoryName($wave) -ne $waveRoot) { throw 'Wave must be directly inside the judge waves directory.' }
if ($RepoId -notmatch '^hack-[a-zA-Z0-9_-]+$') { throw 'Invalid repository ID.' }
$targets = @((Join-Path $wave $RepoId), (Join-Path "$workRoot\clones" $RepoId), (Join-Path "$workRoot\dossiers" $RepoId))
# These disposable participant checkouts are explicitly authorised for removal.
# Git may already have unregistered a partially deleted worktree; it is not a
# reason to retain its remaining files, nor to skip other cleanup phases.
foreach ($target in $targets) {
    $absolute = [IO.Path]::GetFullPath($target)
    if (-not $absolute.StartsWith($workRoot+'\', [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetFileName($absolute) -ne $RepoId) { throw 'Deletion target outside participant workspace.' }
    $ancestor = $absolute
    while ($ancestor.Length -ge $workRoot.Length) {
        if (Test-Path -LiteralPath $ancestor) {
            $item = Get-Item -LiteralPath $ancestor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Redirected deletion path: $ancestor" }
        }
        $ancestor = [IO.Path]::GetDirectoryName($ancestor)
    }
    if (Test-Path -LiteralPath $absolute) {
        Remove-Item -LiteralPath $absolute -Recurse -Force
    }
    if (Test-Path -LiteralPath $absolute) { throw "Participant files remain: $absolute" }
}
