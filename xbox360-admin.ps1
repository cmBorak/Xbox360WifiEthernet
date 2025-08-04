# Xbox 360 WiFi Module Emulator - PowerShell Launcher with Auto-Elevation
# This version automatically requests administrator privileges

param([string[]]$Arguments)

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Requesting administrator privileges..." -ForegroundColor Yellow
    
    # Get the current script path
    $scriptPath = $MyInvocation.MyCommand.Path
    
    # Re-launch as administrator
    try {
        Start-Process PowerShell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`" -Arguments `"$($Arguments -join ' ')`""
        exit
    }
    catch {
        Write-Host "Failed to elevate privileges. Please run PowerShell as Administrator manually." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Now running as administrator
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Xbox 360 WiFi Module Emulator (Admin)" -ForegroundColor Cyan  
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if installer.py exists
if (-not (Test-Path "installer.py")) {
    Write-Host "ERROR: installer.py not found" -ForegroundColor Red
    Write-Host "Make sure you're running this from the Xbox360WifiEthernet directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Python installation
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    Write-Host "Found Python" -ForegroundColor Green
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
    Write-Host "Found Python3" -ForegroundColor Green
} else {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3 from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Starting installer with administrator privileges..." -ForegroundColor Green
Write-Host ""

# Check for WSL first (preferred)
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    Write-Host "WSL detected, using Linux environment..." -ForegroundColor Yellow
    
    try {
        $wslPath = wsl wslpath $PWD.Path
        Write-Host "Converted path: $wslPath" -ForegroundColor Gray
        
        # Run in WSL with sudo
        wsl bash -c "cd '$wslPath' && sudo python3 installer.py $($Arguments -join ' ')"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "Installation completed successfully!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "Installation encountered issues (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "WSL execution failed, trying direct Windows execution..." -ForegroundColor Yellow
        
        # Fallback to direct execution (already running as admin)
        & $pythonCmd installer.py @Arguments
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "Installation completed successfully!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "Note: Some features may require Linux/WSL environment" -ForegroundColor Yellow
        }
    }
}
else {
    Write-Host "WSL not detected, running directly on Windows..." -ForegroundColor Yellow
    Write-Host "Note: For full functionality, install WSL with: wsl --install" -ForegroundColor Gray
    Write-Host ""
    
    # Run directly on Windows (already running as admin)
    & $pythonCmd installer.py @Arguments
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Installation completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Installation may have failed. For best results:" -ForegroundColor Yellow
        Write-Host "1. Install WSL: wsl --install" -ForegroundColor Gray
        Write-Host "2. Restart your computer" -ForegroundColor Gray
        Write-Host "3. Run this script again" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Installation process completed." -ForegroundColor Cyan
Read-Host "Press Enter to exit"