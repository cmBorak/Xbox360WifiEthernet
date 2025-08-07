@echo off
REM Xbox 360 WiFi Module Emulator - Docker Testing (Windows)
REM This launches the Docker testing environment on Windows

echo ==========================================
echo Xbox 360 WiFi Module Emulator - Docker Testing
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

echo Docker found, starting testing environment...
echo.

REM Check if we're in WSL or need to use WSL
if exist "\\wsl$" (
    echo Using WSL environment...
    wsl bash -c "cd '/mnt/c/Users/Chris/Documents/GitHub/PI usb faker/Xbox360WifiEthernet' && ./test_in_docker.sh"
) else if exist "C:\Windows\System32\wsl.exe" (
    echo Launching via WSL...
    wsl bash -c "cd '/mnt/c/Users/Chris/Documents/GitHub/PI usb faker/Xbox360WifiEthernet' && ./test_in_docker.sh"
) else (
    echo Running Docker directly on Windows...
    echo.
    echo Note: GUI features will require VNC access at http://localhost:6080
    echo.
    cd /d "%~dp0"
    docker-compose -f docker\docker-compose.yml build pi-emulator
    docker-compose -f docker\docker-compose.yml up -d pi-emulator
    docker-compose -f docker\docker-compose.yml --profile vnc up -d vnc-server
    
    echo.
    echo ================================
    echo Docker Testing Environment Ready!
    echo ================================
    echo.
    echo VNC GUI Access: http://localhost:6080 (password: xbox360)
    echo.
    echo Available commands:
    echo   docker exec -it xbox360-pi-emulator bash
    echo   docker exec -it xbox360-pi-emulator sudo python3 installer_ui.py
    echo   docker exec -it xbox360-pi-emulator sudo ./install_fully_automated.sh
    echo   docker exec -it xbox360-pi-emulator ./system_status.sh
    echo.
    echo Press any key to open VNC in browser...
    pause >nul
    start http://localhost:6080
)

echo.
echo Testing environment ready!
pause