#!/bin/bash
# Xbox 360 WiFi Module Emulator - Pi Test Runner
# Run this script on your Raspberry Pi 4

echo "🎮 Xbox 360 WiFi Module Emulator - Pi Test Script"
echo "=================================================="
echo ""
echo "This will test all functionality and generate detailed logs."
echo "The test will take approximately 2-5 minutes to complete."
echo ""

# Check if running as root (required for USB operations)
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script requires root privileges for USB operations."
    echo "   Please run with: sudo ./run_pi_test.sh"
    echo ""
    echo "   OR run the Python script directly:"
    echo "   sudo python3 test_pi_functionality.py"
    exit 1
fi

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi."
    echo "   Some tests may fail on other hardware."
    echo ""
fi

# Make sure we're in the right directory
if [ ! -f "test_pi_functionality.py" ]; then
    echo "❌ Error: test_pi_functionality.py not found in current directory"
    echo "   Please run this script from the Xbox360WifiEthernet directory"
    exit 1
fi

# Make test script executable
chmod +x test_pi_functionality.py

echo "🚀 Starting comprehensive functionality test..."
echo "📝 Logs will be saved with timestamp"
echo ""

# Run the test
python3 test_pi_functionality.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Test completed successfully!"
    echo "📄 Check the generated log files for detailed results"
else
    echo ""
    echo "❌ Test completed with issues"
    echo "📄 Check the generated log files for error details"
fi

echo ""
echo "📁 Generated files:"
ls -la pi_test_results_*.log pi_test_results_*.json 2>/dev/null | head -10

echo ""
echo "📋 To view the latest log:"
echo "   cat \$(ls -t pi_test_results_*.log | head -1)"
echo ""
echo "📊 To view JSON results:"
echo "   cat \$(ls -t pi_test_results_*.json | head -1)"