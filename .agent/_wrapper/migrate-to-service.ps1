# migrate-to-service.ps1 — promote the current Startup-folder runner
# install to a proper Windows Service.  Idempotent: re-running is safe.
#
# Context: the initial install used a user-level Startup-folder entry so it
# could be set up without elevation.  That works fine on a desktop you
# always log in to, but a Windows Service is more robust (survives fast
# user switching, runs before login, gets a proper SCM entry, can be
# restarted via "Services.msc" or "sc").
#
# This script does NOT re-register the runner with GitHub — it reuses the
# existing C:\actions-runner\.credentials and .runner files.  So no new
# registration token is needed.  It only:
#   1. Stops any currently-running Runner.Listener process
#   2. Removes the Startup-folder autostart entry
#   3. Installs the runner as a Windows Service via svc.ps1 install
#   4. Starts the service
#
# Run from an ELEVATED PowerShell prompt:
#   cd C:\Users\DANNY\Desktop\spacetime-lab
#   .\.agent\_wrapper\migrate-to-service.ps1
#
# Verify afterward with:  Get-Service actions.runner.*
#                         gh api repos/.../actions/runners

[CmdletBinding()]
param(
    [string]$RunnerDir = 'C:\actions-runner',
    [string]$StartupEntry = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\github-actions-runner.cmd"
)

$ErrorActionPreference = 'Stop'

function Assert-Elevated {
    $me = New-Object Security.Principal.WindowsPrincipal(
        [Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $me.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'This script must be run from an elevated PowerShell prompt.'
    }
}

Assert-Elevated

Write-Host ''
Write-Host '=== 1. Stop any currently-running Runner.Listener ==='
$running = Get-Process -Name 'Runner.Listener' -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "  Stopping PID(s): $($running.Id -join ', ')"
    $running | Stop-Process -Force
    Start-Sleep -Seconds 2
} else {
    Write-Host '  No Runner.Listener running.'
}

Write-Host ''
Write-Host '=== 2. Remove Startup-folder autostart entry ==='
if (Test-Path $StartupEntry) {
    Write-Host "  Removing $StartupEntry"
    Remove-Item -Force $StartupEntry
} else {
    Write-Host '  No Startup-folder entry found (already migrated?).'
}

Write-Host ''
Write-Host '=== 3. Install runner as Windows Service ==='
if (-not (Test-Path (Join-Path $RunnerDir 'svc.ps1'))) {
    throw "svc.ps1 not found in $RunnerDir — is the runner actually installed here?"
}

Push-Location $RunnerDir
try {
    # If a service is already installed, uninstall first so we can reinstall cleanly.
    $existing = Get-Service -Name 'actions.runner.*' -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  Existing service found ($($existing.Name)) — removing first."
        & .\svc.ps1 stop      | Out-Null
        & .\svc.ps1 uninstall | Out-Null
    }

    Write-Host '  Running svc.ps1 install ...'
    & .\svc.ps1 install

    Write-Host '  Running svc.ps1 start ...'
    & .\svc.ps1 start
} finally {
    Pop-Location
}

Write-Host ''
Write-Host '=== 4. Verify ==='
Start-Sleep -Seconds 2
$svc = Get-Service -Name 'actions.runner.*' -ErrorAction SilentlyContinue
if ($svc) {
    Write-Host "  Service: $($svc.Name)  Status: $($svc.Status)"
} else {
    Write-Warning 'No actions.runner.* service found — install may have failed. See output above.'
}

Write-Host ''
Write-Host '=== DONE ==='
Write-Host "Runner now runs as Windows Service.  Check Services.msc under 'actions.runner.*'."
Write-Host 'Verify on GitHub:'
Write-Host '  https://github.com/christianescamilla15-cell/spacetime-lab/settings/actions/runners'
Write-Host '  Runner should show online with a green Idle badge.'
