# Windows Users - Quick Fix Guide 🪟

## 🚨 **Path Issue Fix**

If you get `"No such file or directory"` error, here are **3 easy fixes**:

### **Fix 1: Use PowerShell (Recommended)**
```powershell
# Right-click in the folder and select "Open PowerShell window here"
.\xbox360.ps1
```

### **Fix 2: Use the correct WSL path**
```cmd
wsl bash -c "cd '/mnt/c/Users/Chris/Documents/GitHub/PI usb faker/Xbox360WifiEthernet' && python3 installer.py"
```

### **Fix 3: Copy to a simpler path**
1. Copy the `Xbox360WifiEthernet` folder to `C:\Xbox360\`
2. Run: `xbox360.bat` from the new location

## 🎯 **Root Cause**

The issue happens because:
- **Windows path**: `C:\Users\Chris\Documents\GitHub\PI usb faker\Xbox360WifiEthernet`
- **WSL path**: `/mnt/c/Users/Chris/Documents/GitHub/PI usb faker/Xbox360WifiEthernet`
- **Problem**: Spaces in "PI usb faker" confuse the batch file

## ✅ **Best Solutions by Windows Version**

### **Windows 11 (Latest)**
```powershell
# Use PowerShell (handles paths better)
.\xbox360.ps1
```

### **Windows 10 with WSL2**
```cmd
# Fixed batch file should work
xbox360.bat
```

### **Windows 10 without WSL**
```cmd
# Direct Python execution
python installer.py --cli
```

## 🔧 **Alternative: Direct Installation**

Skip the launchers entirely:

```bash
# Open WSL terminal and navigate manually
wsl
cd /mnt/c/Users/Chris/Documents/GitHub
cd "PI usb faker/Xbox360WifiEthernet"
python3 installer.py
```

## 📋 **Test Your Setup**

```bash
# Quick test (works on any system)
python test.py --quick
```

The **PowerShell script (`xbox360.ps1`)** is the most reliable option for Windows users! 🎮✨