#!/usr/bin/env python3
"""
Script Launcher GUI
Provides GUI access to all Python scripts with logging to debuglogs
"""

import os
import sys
import subprocess
import threading
import queue
from pathlib import Path
from datetime import datetime

# GUI imports with fallback
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("❌ GUI not available. Install with: sudo apt install python3-tk")
    sys.exit(1)

class ScriptLauncherGUI:
    def __init__(self):
        self.setup_logging()
        self.setup_gui()
        self.setup_scripts()
        
    def setup_logging(self):
        """Setup centralized logging to debuglogs directory"""
        # Handle both Desktop and desktop (lowercase) variants
        possible_paths = [
            Path.home() / "Desktop" / "debuglogs",
            Path.home() / "desktop" / "debuglogs",
            Path("/home/pi/Desktop/debuglogs"),
            Path("/home/pi/desktop/debuglogs"),
            Path.home() / "debuglogs"
        ]
        
        self.debug_log_dir = None
        for path in possible_paths:
            if path.parent.exists():
                self.debug_log_dir = path
                break
        
        if not self.debug_log_dir:
            self.debug_log_dir = Path.home() / "Desktop" / "debuglogs"
        
        # Create directory
        self.debug_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file for launcher
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.debug_log_dir / f"script_launcher_{timestamp}.log"
        
        # Initialize logging
        self.log_buffer = []
        self.current_log_session = None
        
        # Log launcher start
        self.log_to_file("🚀 Script Launcher GUI Started", "INFO")
        self.log_to_file(f"Debug Log Directory: {self.debug_log_dir}", "INFO")
        self.log_to_file("=" * 50, "INFO")
    
    def log_to_file(self, message, level="INFO"):
        """Log message to file"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}\n"
            self.log_buffer.append(log_entry)
            
            # Flush every few entries
            if len(self.log_buffer) >= 5:
                self.flush_log()
                
        except Exception as e:
            print(f"Logging error: {e}")
    
    def flush_log(self):
        """Flush log buffer to file"""
        if self.log_buffer:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.writelines(self.log_buffer)
                self.log_buffer = []
            except Exception as e:
                print(f"Log flush error: {e}")
    
    def setup_gui(self):
        """Setup the GUI interface"""
        self.root = tk.Tk()
        self.root.title("🎮 Xbox 360 WiFi Emulator - Script Launcher")
        self.root.geometry("900x700")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎮 Xbox 360 WiFi Emulator Script Launcher", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Scripts frame
        scripts_frame = ttk.LabelFrame(main_frame, text="Available Scripts", padding="5")
        scripts_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        scripts_frame.columnconfigure(0, weight=1)
        
        # Create scrollable frame for scripts
        canvas = tk.Canvas(scripts_frame)
        scrollbar = ttk.Scrollbar(scripts_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        scripts_frame.rowconfigure(0, weight=1)
        scripts_frame.columnconfigure(0, weight=1)
        
        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Script Output", padding="5")
        output_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                   width=50, height=20)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control buttons frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Clear output button
        self.clear_btn = ttk.Button(controls_frame, text="Clear Output", 
                                   command=self.clear_output)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Open debuglogs button
        self.logs_btn = ttk.Button(controls_frame, text="📂 Open Debug Logs", 
                                  command=self.open_debug_logs)
        self.logs_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(controls_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT)
        
        # Queue for thread communication
        self.queue = queue.Queue()
        
        # Start queue processing
        self.process_queue()
        
        # Initial output
        self.add_output("🎮 Xbox 360 WiFi Emulator Script Launcher", "title")
        self.add_output("=" * 50, "info")
        self.add_output(f"📂 Debug logs directory: {self.debug_log_dir}", "info")
        self.add_output("💡 Select a script from the left panel to run it", "info")
        self.add_output("📝 All script operations will be logged to debuglogs", "info")
        self.add_output("=" * 50, "info")
    
    def setup_scripts(self):
        """Setup available scripts"""
        self.scripts = [
            {
                "name": "🔧 Comprehensive Pi Fix",
                "file": "comprehensive_pi_fix.py",
                "description": "Master fix script - addresses ALL Pi issues:\n• Python environment\n• DWC2 module loading\n• USB networking\n• Passthrough functionality",
                "category": "🛠️ Primary Fixes"
            },
            {
                "name": "🖥️ Fix Desktop Paths",
                "file": "fix_desktop_paths_pi.py", 
                "description": "Fix desktop app wrong paths for Pi:\n• Creates Pi-specific desktop files\n• Removes Windows/WSL paths\n• Copies to desktop automatically",
                "category": "🛠️ Primary Fixes"
            },
            {
                "name": "🐍 Fix Python Environment",
                "file": "fix_pi_python_environment.py",
                "description": "Fix Python externally-managed-environment:\n• Install system packages\n• Create virtual environment\n• Bypass pip restrictions",
                "category": "🛠️ Primary Fixes"
            },
            {
                "name": "📁 Move Redundant Desktop Files",
                "file": "move_redundant_desktop_files.py",
                "description": "Move redundant desktop files to separate directory:\n• Xbox360-Emulator-Fixed.desktop\n• Xbox360-Emulator-Simple.desktop\n• Xbox360-Emulator-Terminal-Fixed.desktop",
                "category": "🧹 Cleanup Tools"
            },
            {
                "name": "🔍 Diagnose Empty Logs",
                "file": "diagnose_empty_logs.py",
                "description": "Diagnose why GUI operations fail immediately:\n• Test Python imports\n• Check GUI initialization\n• Test logging mechanism",
                "category": "🔍 Diagnostic Tools"
            },
            {
                "name": "🖥️ Debug Desktop App",
                "file": "debug_desktop_app.py",
                "description": "Comprehensive desktop integration analysis:\n• Desktop environment check\n• File permissions analysis\n• Path resolution testing",
                "category": "🔍 Diagnostic Tools"
            },
            {
                "name": "🛠️ Fix DWC2 Comprehensive",
                "file": "fix_dwc2_comprehensive.py",
                "description": "Comprehensive DWC2 module fix:\n• Boot configuration\n• Module loading\n• Initramfs update",
                "category": "🔧 Specialized Fixes"
            },
            {
                "name": "🔄 Update Initramfs DWC2",
                "file": "update_initramfs_dwc2.py",
                "description": "Update initramfs for DWC2 modules:\n• Standalone initramfs update\n• Early boot module loading",
                "category": "🔧 Specialized Fixes"
            },
            {
                "name": "🧪 Test Centralized Logging",
                "file": "test_centralized_logging.py",
                "description": "Test the centralized logging system:\n• Verify debuglogs directory\n• Test session logging\n• Component integration test",
                "category": "🧪 Testing Tools"
            },
            {
                "name": "🎮 Main Xbox Installer",
                "file": "installer.py", 
                "description": "Main Xbox 360 WiFi Emulator installer:\n• Full GUI interface\n• Installation management\n• System configuration",
                "category": "🎮 Main Application"
            }
        ]
        
        self.create_script_buttons()
    
    def create_script_buttons(self):
        """Create buttons for all scripts organized by category"""
        current_category = None
        row = 0
        
        for script in self.scripts:
            # Add category header if new category
            if script["category"] != current_category:
                current_category = script["category"]
                
                if row > 0:  # Add spacing between categories
                    spacer = ttk.Frame(self.scrollable_frame, height=10)
                    spacer.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
                    row += 1
                
                # Category label
                category_label = ttk.Label(self.scrollable_frame, text=current_category, 
                                         font=('Arial', 10, 'bold'))
                category_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(5, 2))
                row += 1
            
            # Script frame
            script_frame = ttk.Frame(self.scrollable_frame, relief="ridge", borderwidth=1)
            script_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2, padx=5)
            script_frame.columnconfigure(0, weight=1)
            
            # Script button
            script_btn = ttk.Button(script_frame, text=script["name"],
                                  command=lambda s=script: self.run_script(s))
            script_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=2)
            
            # Description label
            desc_label = ttk.Label(script_frame, text=script["description"], 
                                 font=('Arial', 8), foreground='gray50')
            desc_label.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=(0, 5))
            
            row += 1
        
        # Update canvas scroll region
        self.scrollable_frame.update_idletasks()
    
    def run_script(self, script):
        """Run a selected script"""
        script_path = Path.cwd() / script["file"]
        
        if not script_path.exists():
            self.add_output(f"❌ Script not found: {script['file']}", "error")
            self.log_to_file(f"Script not found: {script['file']}", "ERROR")
            return
        
        self.add_output(f"\n🚀 Running: {script['name']}", "title")
        self.add_output(f"📂 Script: {script['file']}", "info")
        self.add_output("=" * 50, "info")
        
        self.log_to_file(f"Running script: {script['name']} ({script['file']})", "INFO")
        
        # Update status
        self.status_label.config(text=f"Running {script['name']}...")
        
        # Run script in thread
        def run_thread():
            try:
                # Run the script
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    cwd=str(Path.cwd())
                )
                
                # Send results to queue
                self.queue.put(('script_output', result.stdout))
                if result.stderr:
                    self.queue.put(('script_error', result.stderr))
                
                if result.returncode == 0:
                    self.queue.put(('script_complete', f"✅ {script['name']} completed successfully"))
                    self.queue.put(('log_message', f"Script completed successfully: {script['name']}", "SUCCESS"))
                else:
                    self.queue.put(('script_complete', f"❌ {script['name']} failed (exit code: {result.returncode})"))
                    self.queue.put(('log_message', f"Script failed: {script['name']} (exit code: {result.returncode})", "ERROR"))
                
            except Exception as e:
                self.queue.put(('script_error', f"Script execution error: {e}"))
                self.queue.put(('script_complete', f"❌ {script['name']} execution failed"))
                self.queue.put(('log_message', f"Script execution error: {script['name']}: {e}", "ERROR"))
        
        # Start the thread
        thread = threading.Thread(target=run_thread, daemon=True)
        thread.start()
    
    def process_queue(self):
        """Process queue messages from threads"""
        try:
            while True:
                message_type, *data = self.queue.get_nowait()
                
                if message_type == 'script_output':
                    self.add_output(data[0], "output")
                elif message_type == 'script_error':
                    self.add_output(data[0], "error")
                elif message_type == 'script_complete':
                    self.add_output(data[0], "success")
                    self.add_output("=" * 50, "info")
                    self.status_label.config(text="Ready")
                elif message_type == 'log_message':
                    self.log_to_file(data[0], data[1])
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue)
    
    def add_output(self, text, msg_type="info"):
        """Add text to output area with color coding"""
        colors = {
            "title": "#0066cc",
            "info": "#333333", 
            "success": "#006600",
            "error": "#cc0000",
            "warning": "#ff6600",
            "output": "#000000"
        }
        
        # Configure tag if not exists
        color = colors.get(msg_type, "#000000")
        tag_name = f"tag_{msg_type}"
        self.output_text.tag_configure(tag_name, foreground=color)
        
        # Add text
        self.output_text.insert(tk.END, text + "\n", tag_name)
        self.output_text.see(tk.END)
        
        # Update display
        self.root.update_idletasks()
    
    def clear_output(self):
        """Clear the output text area"""
        self.output_text.delete(1.0, tk.END)
        self.add_output("🧹 Output cleared", "info")
        self.log_to_file("Output area cleared", "INFO")
    
    def open_debug_logs(self):
        """Open the debug logs directory"""
        try:
            if sys.platform.startswith('linux'):
                subprocess.run(['xdg-open', str(self.debug_log_dir)])
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(self.debug_log_dir)])
            elif sys.platform == 'win32':
                subprocess.run(['explorer', str(self.debug_log_dir)])
            else:
                self.add_output(f"📂 Debug logs directory: {self.debug_log_dir}", "info")
            
            self.log_to_file("Opened debug logs directory", "INFO")
            
        except Exception as e:
            self.add_output(f"❌ Could not open debug logs: {e}", "error")
            self.add_output(f"📂 Debug logs location: {self.debug_log_dir}", "info")
            self.log_to_file(f"Failed to open debug logs directory: {e}", "ERROR")
    
    def on_closing(self):
        """Handle window closing"""
        self.log_to_file("Script Launcher GUI closing", "INFO")
        self.flush_log()
        self.root.destroy()
    
    def run(self):
        """Run the GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main function"""
    if not GUI_AVAILABLE:
        print("❌ GUI not available")
        print("💡 Install with: sudo apt install python3-tk")
        return
    
    try:
        app = ScriptLauncherGUI()
        app.run()
    except Exception as e:
        print(f"❌ Script Launcher failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()