param(
    [Parameter(Mandatory=$true)][string]$PythonPath,
    [Parameter(Mandatory=$true)][string]$RootPath,
    [Parameter(Mandatory=$true)][string]$TaskName,
    [int]$Port = 4173
)
$ErrorActionPreference = 'Stop'
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing -and $existing.State -eq 'Running') { exit 0 }
$pythonWindowless = Join-Path (Split-Path -Parent $PythonPath) 'pythonw.exe'
if (Test-Path -LiteralPath $pythonWindowless) { $PythonPath = $pythonWindowless }
$scriptPath = Join-Path $RootPath 'scripts\ensure-local-server.py'
$action = New-ScheduledTaskAction -Execute $PythonPath -Argument ('-X utf8 "{0}" --serve --port {1}' -f $scriptPath, $Port) -WorkingDirectory $RootPath
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
# On-demand only: no recurring trigger and no judging commands.
Register-ScheduledTask -TaskName $TaskName -Action $action -Principal $principal -Settings $settings -Description 'Independent local HackAlem catalog server; does not run judges.' -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
