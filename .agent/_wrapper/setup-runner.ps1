# setup-runner.ps1 — configure + install a GitHub Actions self-hosted runner
# on this Windows PC so the claude-dispatch workflow can run here.
#
# Run from an ELEVATED PowerShell prompt:
#   cd C:\Users\DANNY\Desktop\spacetime-lab
#   .\.agent\_wrapper\setup-runner.ps1 -RegistrationToken <token-from-github>
#
# Getting the registration token (interactive, one-time):
#   1. Open https://github.com/christianescamilla15-cell/spacetime-lab/settings/actions/runners/new
#   2. Under "Configure" copy the value after the --token flag (the UUID-looking string).
#   3. Pass it as -RegistrationToken.
#   Token is valid for ~1 hour; if it expires regenerate on the same page.
#
# Idempotent-ish: re-running with -Force blows away the previous install.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RegistrationToken,

    [string]$RepoUrl = 'https://github.com/christianescamilla15-cell/spacetime-lab',
    [string]$RunnerName = ('runner-' + ($env:COMPUTERNAME.ToLower())),
    [string]$Labels = 'self-hosted,windows,claude-dispatch',
    [string]$WorkFolder = '_work',
    [string]$InstallDir = 'C:\actions-runner',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Assert-Elevated {
    $me = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $me.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'This script must be run from an elevated PowerShell prompt.'
    }
}

function Download-Runner {
    param([string]$Dest)
    # Pin a known-good runner release.  Bump this version manually when upgrading.
    $ver = '2.319.1'
    $pkg = "actions-runner-win-x64-$ver.zip"
    $url = "https://github.com/actions/runner/releases/download/v$ver/$pkg"
    $zip = Join-Path $Dest $pkg
    if (-not (Test-Path $zip)) {
        Write-Host "Downloading runner $ver ..."
        Invoke-WebRequest -Uri $url -OutFile $zip
    }
    Write-Host 'Extracting runner ...'
    Expand-Archive -LiteralPath $zip -DestinationPath $Dest -Force
}

Assert-Elevated

# Handle previous install.
if (Test-Path $InstallDir) {
    if (-not $Force) {
        throw "$InstallDir already exists.  Re-run with -Force to wipe and reinstall."
    }
    Write-Host "Removing existing $InstallDir (-Force) ..."
    # Stop + uninstall any existing service.
    if (Test-Path (Join-Path $InstallDir 'svc.ps1')) {
        Push-Location $InstallDir
        try {
            & .\svc.ps1 stop     | Out-Null
            & .\svc.ps1 uninstall | Out-Null
        } catch { }
        Pop-Location
    }
    Remove-Item -Recurse -Force $InstallDir
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Download-Runner -Dest $InstallDir

Push-Location $InstallDir
try {
    Write-Host "Configuring runner ($RunnerName, labels=$Labels) ..."
    & .\config.cmd `
        --unattended `
        --url $RepoUrl `
        --token $RegistrationToken `
        --name $RunnerName `
        --labels $Labels `
        --work $WorkFolder `
        --replace

    Write-Host 'Installing runner as a Windows service ...'
    & .\svc.ps1 install
    & .\svc.ps1 start

    Write-Host ''
    Write-Host '=== DONE ==='
    Write-Host "Runner installed at:  $InstallDir"
    Write-Host "Runner name:          $RunnerName"
    Write-Host "Labels:               $Labels"
    Write-Host "Service started (check Services.msc for 'actions.runner.*')"
    Write-Host ''
    Write-Host 'Verify on GitHub:'
    Write-Host "  $RepoUrl/settings/actions/runners"
    Write-Host '  Runner should appear with a green "Idle" badge.'
    Write-Host ''
    Write-Host 'First dispatch (from any authenticated terminal):'
    Write-Host '  gh workflow run claude-dispatch.yml -f workflow=check-deploys'
} finally {
    Pop-Location
}
