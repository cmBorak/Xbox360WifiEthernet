#!/usr/bin/env python3
"""
Fix USB-Sniffify Build Issues
This script fixes the CMakeLists.txt and rebuilds the USB tools properly
"""

import os
import shutil
import subprocess
from pathlib import Path

def run_command(cmd, description=""):
    """Run command and return success status"""
    print(f"🔧 {description}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        success = result.returncode == 0
        
        if success:
            print("✅ Command succeeded")
            if result.stdout.strip():
                print(f"Output: {result.stdout}")
        else:
            print("❌ Command failed")
            if result.stderr.strip():
                print(f"Error: {result.stderr}")
        
        return success, result.stdout, result.stderr
    except Exception as e:
        print(f"💥 Command exception: {e}")
        return False, "", str(e)

def fix_cmake_file():
    """Fix the CMakeLists.txt file"""
    print("🛠️ Fixing CMakeLists.txt...")
    
    cmake_file = Path("usb_sniffing_tools/usb-sniffify/CMakeLists.txt")
    
    if not cmake_file.exists():
        print("❌ CMakeLists.txt not found")
        return False
    
    # Read current content
    with open(cmake_file, 'r') as f:
        content = f.read()
    
    # Fixed CMakeLists.txt content
    fixed_content = '''cmake_minimum_required(VERSION 3.10)

project(usb-sniffify)

# Set C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBUSB REQUIRED libusb-1.0)
find_package(Threads REQUIRED)

# Include directories
include_directories(include)
include_directories(${LIBUSB_INCLUDE_DIRS})

# Check if we can build raw-gadget tools
if(EXISTS "/dev/raw-gadget" OR EXISTS "/sys/kernel/config/usb_gadget")
    set(CAN_BUILD_RAW_GADGET TRUE)
else()
    set(CAN_BUILD_RAW_GADGET FALSE)
    message(WARNING "raw-gadget not available - some tools will not be built")
endif()

# Build C library for basic tools
add_library(sniffifyc STATIC
    src/raw-helper.c
    include/raw-helper.h
)

# Build C++ library for advanced tools (includes RawGadgetPassthrough implementation)
add_library(sniffify STATIC
    src/raw-helper.cpp
    src/raw-gadget.cpp
    src/raw-gadget-passthrough.cpp
    include/raw-gadget.hpp
    include/raw-helper.h
)

# Build basic passthrough tool (C version)
add_executable(passthrough-c src/passthrough.c)
target_link_libraries(passthrough-c sniffifyc ${LIBUSB_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT} m)

# Build advanced passthrough tool (C++ version) - links with sniffify library
add_executable(passthrough src/passthrough.cpp)
target_link_libraries(passthrough sniffify ${LIBUSB_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT} m)

# Build USB utilities
add_executable(libusbhax src/libusbhax.c)
target_link_libraries(libusbhax ${LIBUSB_LIBRARIES})

# Build HID tools
add_executable(hid src/hid.c)
target_link_libraries(hid sniffifyc ${LIBUSB_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT})

# Set compiler flags
target_compile_options(sniffifyc PRIVATE -Wall -Wextra)
target_compile_options(sniffify PRIVATE -Wall -Wextra)

# Link libraries
target_link_libraries(sniffifyc ${LIBUSB_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT})
target_link_libraries(sniffify ${LIBUSB_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT})

# Install targets (only build executables that have main functions)
install(TARGETS sniffifyc sniffify DESTINATION lib)
install(TARGETS passthrough-c passthrough libusbhax hid DESTINATION bin)

# Print build summary
message(STATUS "Build configuration:")
message(STATUS "  libusb-1.0: ${LIBUSB_FOUND}")
message(STATUS "  raw-gadget support: ${CAN_BUILD_RAW_GADGET}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Executables: passthrough-c, passthrough, libusbhax, hid")
'''
    
    # Write fixed content
    with open(cmake_file, 'w') as f:
        f.write(fixed_content)
    
    print("✅ Fixed CMakeLists.txt")
    return True

def rebuild_tools():
    """Rebuild the USB tools"""
    print("🏗️ Rebuilding USB-Sniffify tools...")
    
    build_dir = Path("usb_sniffing_tools/usb-sniffify/build")
    
    # Clean and recreate build directory
    if build_dir.exists():
        print("🧹 Cleaning old build...")
        shutil.rmtree(build_dir)
    
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Change to build directory
    original_dir = os.getcwd()
    os.chdir(build_dir)
    
    try:
        # Run CMake
        success, _, _ = run_command("cmake ..", "Running CMake configuration")
        if not success:
            return False
        
        # Run Make
        success, _, _ = run_command("make -j$(nproc)", "Building tools")
        if not success:
            return False
        
        # Check what was built
        print("\n📦 Built executables:")
        built_files = []
        for exe in ['passthrough', 'passthrough-c', 'libusbhax', 'hid']:
            if Path(exe).exists():
                built_files.append(exe)
                print(f"✅ {exe}")
            else:
                print(f"❌ {exe} - not built")
        
        print(f"\n🎯 Successfully built {len(built_files)} executables")
        return len(built_files) > 0
        
    finally:
        os.chdir(original_dir)

def main():
    """Main function"""
    print("🛠️ USB-Sniffify Build Fixer")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("usb_sniffing_tools/usb-sniffify").exists():
        print("❌ USB-Sniffify directory not found")
        print("   Please run this from the Xbox360WifiEthernet directory")
        return False
    
    # Fix CMakeLists.txt
    if not fix_cmake_file():
        return False
    
    # Rebuild tools
    if not rebuild_tools():
        print("❌ Build failed")
        return False
    
    print("\n🎉 USB-Sniffify tools fixed and rebuilt successfully!")
    print("\n📁 Built tools are in: usb_sniffing_tools/usb-sniffify/build/")
    print("\n🧪 You can now run the full test:")
    print("   sudo ./run_pi_test.sh")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        exit(130)
    except Exception as e:
        print(f"💥 Error: {e}")
        exit(1)