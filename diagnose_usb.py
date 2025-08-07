#!/usr/bin/env python3
"""
Quick USB System Diagnostic Script
Run this to diagnose and fix USB gadget, raw-gadget, and usb0 issues
"""

import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🩺 Xbox 360 USB System Diagnostic")
    print("=" * 40)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    try:
        from usb_system_fixer import USBSystemFixer
        
        # Create and run fixer
        fixer = USBSystemFixer()
        summary = fixer.diagnose_and_fix()
        
        # Print detailed report
        fixer.print_report(summary)
        
        # Exit with appropriate code
        if summary['issues_found'] == 0:
            print("\n🎉 All USB systems are working correctly!")
            return 0
        else:
            print(f"\n⚠️ {summary['issues_found']} issues found. See recommendations above.")
            return 1
            
    except ImportError as e:
        print(f"❌ Could not import USB system fixer: {e}")
        print("Make sure you're running from the correct directory.")
        return 1
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())