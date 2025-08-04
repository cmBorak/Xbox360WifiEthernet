# Xbox 360 WiFi Module Emulator - PowerShell Launcher
# Alternative launcher for Windows systems

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Xbox 360 WiFi Module Emulator" -ForegroundColor Cyan  
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
Write-Host "Starting installer..." -ForegroundColor Green
Write-Host ""

# Check for WSL
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    Write-Host "WSL detected, using Linux environment for best compatibility..." -ForegroundColor Yellow
    
    # Convert Windows path to WSL path
    try {
        $wslPath = wsl wslpath $PWD.Path
        Write-Host "Converted path: $wslPath" -ForegroundColor Gray
        
        # Run in WSL with sudo
        $arguments = $args -join " "
        Write-Host "Note: Installation requires sudo privileges in WSL" -ForegroundColor Yellow
        wsl bash -c "cd '$wslPath' && sudo python3 installer.py $arguments"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installation completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "Installation encountered issues (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "WSL path conversion failed, trying direct Windows execution..." -ForegroundColor Yellow
        
        # Fallback to direct execution
        Write-Host "Note: Installation requires administrator privileges" -ForegroundColor Yellow
        $arguments = $args
        & $pythonCmd installer.py @arguments
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "Note: Some features require Linux/WSL environment" -ForegroundColor Yellow
        }
    }
}
else {
    Write-Host "WSL not detected, running directly on Windows..." -ForegroundColor Yellow
    Write-Host "Note: For full functionality, install WSL with: wsl --install" -ForegroundColor Gray
    Write-Host ""
    
    # Run directly on Windows
    Write-Host "Note: Installation requires administrator privileges" -ForegroundColor Yellow
    $arguments = $args
    & $pythonCmd installer.py @arguments
    
    if ($LASTEXITCODE -ne 0) {
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