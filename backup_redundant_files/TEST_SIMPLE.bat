@echo off
REM Xbox 360 WiFi Module Emulator - Simple Docker Test (Windows)

echo ==========================================
echo Xbox 360 WiFi Module Emulator - Simple Test
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found
    echo.
    echo Please install Docker Desktop for Windows:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo Docker found!
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

echo Building simple test container...
docker build -f docker\Dockerfile.simple -t xbox360-test .

if errorlevel 1 (
    echo.
    echo Build failed! Common issues:
    echo 1. Docker daemon not running
    echo 2. Not enough disk space
    echo 3. Network issues
    echo.
    pause
    exit /b 1
)

echo.
echo ================================
echo Container built successfully!
echo ================================
echo.
echo Starting interactive test environment...
echo.
echo Available commands once inside:
echo   sudo python3 installer_ui.py          # GUI installer
echo   sudo ./install_fully_automated.sh     # Command-line installer  
echo   ./system_status.sh                    # Check system status
echo   lsusb                                  # See mock Xbox adapter
echo   exit                                  # Leave container
echo.

REM Run the container interactively
docker run -it --rm --name xbox360-test -v "%CD%:/opt/xbox360-emulator" -w /opt/xbox360-emulator xbox360-test bash

echo.
echo Container session ended.
pause