@echo off
REM Xbox 360 WiFi Module Emulator - Universal Windows Launcher
REM Fixed version with proper WSL path conversion

echo ==========================================
echo Xbox 360 WiFi Module Emulator
echo ==========================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Check if installer.py exists
if not exist "installer.py" (
    echo ERROR: installer.py not found
    echo Make sure you're running this from the Xbox360WifiEthernet directory
    echo.
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found
        echo.
        echo Please install Python 3 from:
        echo https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=python3
) else (
    set PYTHON_CMD=python
)

echo Found Python, starting installer...
echo.

REM Check if WSL is available and try to use it
if exist "C:\Windows\System32\wsl.exe" (
    echo Detected WSL, using Linux environment for best compatibility...
    
    REM Use wslpath to properly convert the path
    for /f "delims=" %%i in ('wsl wslpath "%CD%"') do set WSL_PATH=%%i
    
    REM Check if the conversion worked
    if defined WSL_PATH (
        echo Converted path: %WSL_PATH%
        echo Note: Installation requires sudo privileges in WSL
        wsl bash -c "cd '%WSL_PATH%' 2>/dev/null && sudo python3 installer.py %* || echo 'Installation failed, check permissions'"
    ) else (
        echo Path conversion failed, trying manual conversion...
        REM Manual conversion as fallback
        set "MANUAL_PATH=%CD%"
        
        REM Replace drive letter (works for any drive)
        set "MANUAL_PATH=%MANUAL_PATH:~0,1%"
        set "MANUAL_PATH=/mnt/%MANUAL_PATH%"
        
        REM Add the rest of the path
        set "REST_PATH=%CD:~2%"
        set "REST_PATH=%REST_PATH:\=/%"
        set "MANUAL_PATH=%MANUAL_PATH%%REST_PATH%"
        
        echo Trying manual path: %MANUAL_PATH%
        echo Note: Installation requires sudo privileges in WSL
        wsl bash -c "cd '%MANUAL_PATH%' && sudo python3 installer.py %*"
    )
) else (
    echo WSL not detected, running directly on Windows...
    echo Note: For full functionality, install WSL: wsl --install
    echo.
    
    REM Try to run directly on Windows
    %PYTHON_CMD% installer.py %*
    
    if errorlevel 1 (
        echo.
        echo Installation may have failed. For best results:
        echo 1. Install WSL: wsl --install
        echo 2. Restart your computer
        echo 3. Run this script again
        echo.
        echo Or try running directly in WSL:
        echo   wsl bash -c "cd '/mnt/c/Users/Chris/Documents/GitHub/PI usb faker/Xbox360WifiEthernet' && python3 installer.py"
    )
)

echo.
echo Installation process completed.
pause