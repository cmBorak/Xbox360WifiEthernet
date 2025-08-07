@echo off
REM Xbox 360 WiFi Module Emulator - Windows Batch Launcher
REM This launches the installer on WSL/Linux systems

echo ========================================
echo Xbox 360 WiFi Module Emulator Installer
echo ========================================
echo.

REM Check if we're in WSL or need to use WSL
if exist "\\wsl$" (
    echo Detected WSL environment
    echo Launching installer in WSL...
    echo.
    wsl bash -c "cd '/mnt/c/Users/Chris/Documents/GitHub/PI usb faker/Xbox360WifiEthernet' && ./launch_installer.sh"
) else if exist "C:\Windows\System32\wsl.exe" (
    echo Launching via WSL...
    echo.
    wsl bash -c "cd '/mnt/c/Users/Chris/Documents/GitHub/PI usb faker/Xbox360WifiEthernet' && ./launch_installer.sh"
) else (
    echo ERROR: This installer requires WSL or a Linux environment
    echo.
    echo Please install WSL or run this on a Raspberry Pi
    echo.
    pause
    exit /b 1
)

echo.
echo Installation complete or cancelled
pause