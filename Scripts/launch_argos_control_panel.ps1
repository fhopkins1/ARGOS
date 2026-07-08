param(
    [int]$Port = 8765,
    [int]$WindowWidth = 1600,
    [int]$WindowHeight = 1000
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$hostName = "127.0.0.1"
$dashboardUrl = "http://$hostName`:$Port/"
$pythonCandidates = @(
    "C:/Users/Fletc/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",
    "python",
    "py"
)

function Test-ArgosPort {
    param([string]$HostName, [int]$Port)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        $connected = $async.AsyncWaitHandle.WaitOne(300)
        if ($connected) {
            $client.EndConnect($async)
        }
        $client.Close()
        return $connected
    } catch {
        return $false
    }
}

function Get-ArgosPython {
    foreach ($candidate in $pythonCandidates) {
        if ($candidate -eq "python" -or $candidate -eq "py") {
            $command = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($null -ne $command) {
                return $candidate
            }
            continue
        }
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    throw "No Python runtime was found for ARGOS Control Panel."
}

function Open-ArgosDashboard {
    param([string]$Url, [int]$Width, [int]$Height)

    $browserCandidates = @(
        "$env:ProgramFiles/Microsoft/Edge/Application/msedge.exe",
        "${env:ProgramFiles(x86)}/Microsoft/Edge/Application/msedge.exe",
        "$env:ProgramFiles/Google/Chrome/Application/chrome.exe",
        "${env:ProgramFiles(x86)}/Google/Chrome/Application/chrome.exe"
    )

    foreach ($browser in $browserCandidates) {
        if (Test-Path -LiteralPath $browser) {
            Start-Process `
                -FilePath $browser `
                -ArgumentList @("--new-window", "--window-size=$Width,$Height", "--window-position=40,30", $Url)
            return
        }
    }

    Start-Process $Url
}

if (-not (Test-ArgosPort -HostName $hostName -Port $Port)) {
    $python = Get-ArgosPython
    $serverScript = Join-Path $repoRoot "Scripts/start_argos_control_panel.py"
    Start-Process `
        -FilePath $python `
        -ArgumentList @($serverScript, "--host", $hostName, "--port", "$Port") `
        -WorkingDirectory $repoRoot `
        -WindowStyle Hidden

    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 250
        if (Test-ArgosPort -HostName $hostName -Port $Port) {
            $ready = $true
            break
        }
    }
    if (-not $ready) {
        throw "ARGOS Control Panel did not start on $dashboardUrl"
    }
}

Open-ArgosDashboard -Url $dashboardUrl -Width $WindowWidth -Height $WindowHeight
