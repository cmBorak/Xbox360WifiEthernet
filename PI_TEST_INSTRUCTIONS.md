# Pi Test Instructions

## Quick Start

1. **Copy the entire project to your Raspberry Pi 4**
2. **Navigate to the project directory**
3. **Run the test script as root:**
   ```bash
   sudo ./run_pi_test.sh
   ```

## What the Test Does

The comprehensive test script will:

### ✅ Test 1: System Information
- Check Pi hardware and OS version
- Verify kernel and Python versions
- List USB devices and network interfaces
- Check for required kernel modules

### ✅ Test 2: USB System Diagnostic  
- Run the USB diagnostic tool we created
- Check kernel module loading
- Verify filesystem mounts
- Test USB Device Controller availability
- Check raw-gadget support

### ✅ Test 3: Xbox 360 Gadget Functionality
- Test Xbox 360 gadget creation
- Verify usb0 interface creation
- Check gadget activation/deactivation
- Get detailed gadget status

### ✅ Test 4: USB Passthrough Functionality
- Test USB passthrough manager
- Scan for Xbox devices
- Test capture session creation
- Verify passthrough configuration

### ✅ Test 5: USB Capture Functionality
- Test capture analyzer
- Check usbmon availability  
- Verify capture configuration
- Test protocol analysis setup

### ✅ Test 6: USB-Sniffify Build Test
- Test CMake configuration
- Build all USB tools
- Verify executable creation
- Check for build errors

### ✅ Test 7: GUI Functionality Test
- Test tkinter availability
- Verify GUI class imports
- Check installer GUI structure

## Expected Output

The script will generate:
- **Detailed log file**: `pi_test_results_YYYYMMDD_HHMMSS.log`
- **JSON results file**: `pi_test_results_YYYYMMDD_HHMMSS.json`

## Interpreting Results

### ✅ All Tests Pass
- System is fully functional
- All features working correctly
- Ready for production use

### ⚠️ Partial Success (70%+ pass)
- Core functionality working
- Minor issues that may need attention
- Likely still usable

### ❌ Major Issues (<70% pass)  
- Critical problems detected
- May need kernel configuration changes
- Hardware or driver issues possible

## Common Expected Issues (Normal)

These are normal on standard Pi OS and indicate what needs to be configured:

1. **Raw-gadget module missing** - Normal, requires kernel recompilation
2. **Some USB modules not loaded** - Normal, loaded on demand
3. **Build tools need installation** - Normal, installed during setup

## Send Me the Logs

After running the test, please send me:

1. **The complete log file** (pi_test_results_*.log)
2. **The JSON results** (pi_test_results_*.json)  
3. **Any error messages** you see during execution

### How to Get the Files

```bash
# View the latest log
cat $(ls -t pi_test_results_*.log | head -1)

# View JSON results  
cat $(ls -t pi_test_results_*.json | head -1)

# Or copy files to share
cp pi_test_results_*.log pi_test_results_*.json /path/to/share/
```

## Alternative Execution

If the shell script doesn't work, run directly:

```bash
sudo python3 test_pi_functionality.py
```

## Troubleshooting

### Permission Denied
- Make sure you're running as root: `sudo ./run_pi_test.sh`

### Script Not Found  
- Make sure you're in the Xbox360WifiEthernet directory
- Check file exists: `ls -la test_pi_functionality.py`

### Python Import Errors
- The test will detect and report missing dependencies
- This is normal and expected - it shows what needs to be installed

---

**The test is designed to be safe and non-destructive. It only reads system information and tests functionality without making permanent changes.**