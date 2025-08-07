#!/usr/bin/env python3
"""
Test script to verify GUI logging functionality
"""

import sys
from pathlib import Path

# Test if GUI components are available
try:
    from installer import XboxInstallerGUI, GUI_AVAILABLE
    
    if not GUI_AVAILABLE:
        print("❌ GUI components not available")
        print("   Install tkinter: sudo apt install python3-tk")
        sys.exit(1)
    
    print("✅ GUI components available")
    
    # Test debug log directory setup
    gui = XboxInstallerGUI()
    
    print(f"📂 Debug log directory: {gui.debug_log_dir}")
    
    if gui.debug_log_dir.exists():
        print("✅ Debug logs directory exists")
        
        # Check README file
        readme_file = gui.debug_log_dir / "README.txt"
        if readme_file.exists():
            print("✅ README.txt created")
        else:
            print("⚠️  README.txt missing")
        
        # List existing log files
        log_files = list(gui.debug_log_dir.glob("*.log"))
        if log_files:
            print(f"📄 Found {len(log_files)} existing log files:")
            for log_file in sorted(log_files)[-5:]:  # Show last 5
                print(f"   {log_file.name}")
        else:
            print("📄 No existing log files (this is normal for first run)")
    else:
        print("❌ Debug logs directory not found")
    
    print("\n🎯 GUI Test Complete!")
    print("💡 You can now run: python3 installer.py")
    print("   Use the debug and fix buttons to generate logs")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're in the correct directory")
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()