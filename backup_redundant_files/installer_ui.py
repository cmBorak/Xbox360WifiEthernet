#!/usr/bin/env python3
"""
Xbox 360 WiFi Module Emulator - GUI Installer
Interactive installation interface with progress tracking and status monitoring
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import queue
import os
import sys
import time
import re
from pathlib import Path

class Xbox360InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Xbox 360 WiFi Module Emulator - Installer")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Set up the UI theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2E86AB')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='#A23B72')
        style.configure('Success.TLabel', foreground='#0F7B0F')
        style.configure('Error.TLabel', foreground='#CC2936')
        style.configure('Warning.TLabel', foreground='#F18F01')
        
        # Script directory
        self.script_dir = Path(__file__).parent.absolute()
        
        # Process tracking
        self.current_process = None
        self.process_queue = queue.Queue()
        self.is_installing = False
        
        # Installation state
        self.installation_steps = [
            "Checking system requirements",
            "Updating system packages", 
            "Configuring USB gadget support",
            "Creating directories",
            "Installing Python dependencies",
            "Installing emulator source files",
            "Creating systemd service",
            "Installing USB sniffing tools",
            "Creating helper scripts",
            "Testing installation",
            "Creating documentation",
            "Finalizing installation"
        ]
        
        self.current_step = 0
        self.total_steps = len(self.installation_steps)
        
        self.setup_ui()
        self.check_initial_status()
        
        # Start the queue processor
        self.process_queue_updates()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎮 Xbox 360 WiFi Module Emulator", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        subtitle_label = ttk.Label(main_frame, text="Turn your Raspberry Pi 4 into an Xbox 360 wireless adapter", 
                                 font=('Arial', 10, 'italic'))
        subtitle_label.grid(row=1, column=0, pady=(0, 20), sticky=tk.W)
        
        # Control buttons frame
        control_frame = ttk.LabelFrame(main_frame, text="Installation Control", padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        # Install button
        self.install_btn = ttk.Button(button_frame, text="🚀 Install", 
                                    command=self.start_installation, style='Accent.TButton')
        self.install_btn.grid(row=0, column=0, padx=(0, 5), pady=5, sticky=(tk.W, tk.E))
        
        # Status button
        self.status_btn = ttk.Button(button_frame, text="📊 Check Status", 
                                   command=self.check_status)
        self.status_btn.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # USB Capture button
        self.capture_btn = ttk.Button(button_frame, text="🕵️ USB Capture", 
                                    command=self.start_usb_capture)
        self.capture_btn.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Reboot button
        self.reboot_btn = ttk.Button(button_frame, text="🔄 Reboot", 
                                   command=self.reboot_system)
        self.reboot_btn.grid(row=0, column=3, padx=(5, 0), pady=5, sticky=(tk.W, tk.E))
        
        # Progress frame
        progress_frame = ttk.LabelFrame(control_frame, text="Installation Progress", padding="10")
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        # Current step label
        self.step_label = ttk.Label(progress_frame, text="Ready to install", style='Header.TLabel')
        self.step_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Progress percentage
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=2, column=0, sticky=tk.W)
        
        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Installation Output", padding="10")
        output_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80, 
                                                   font=('Consolas', 10), bg='#1e1e1e', fg='#ffffff',
                                                   insertbackground='white')
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure text tags for colored output
        self.output_text.tag_configure("success", foreground="#00ff00")
        self.output_text.tag_configure("error", foreground="#ff4444")
        self.output_text.tag_configure("warning", foreground="#ffaa00")
        self.output_text.tag_configure("info", foreground="#44aaff")
        self.output_text.tag_configure("header", foreground="#ff44ff", font=('Consolas', 10, 'bold'))
        
        self.log_message("Xbox 360 WiFi Module Emulator Installer Ready", "header")
        self.log_message("Click 'Install' to begin the automated installation process.", "info")
    
    def log_message(self, message, tag="normal"):
        """Add a message to the output log with optional color tag"""
        def _log():
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n", tag)
            self.output_text.see(tk.END)
        
        if threading.current_thread() == threading.main_thread():
            _log()
        else:
            self.root.after(0, _log)
    
    def update_progress(self, step, total_steps, message):
        """Update the progress bar and step information"""
        def _update():
            self.current_step = step
            percentage = (step / total_steps) * 100
            self.progress_var.set(percentage)
            self.progress_label.config(text=f"{percentage:.1f}%")
            self.step_label.config(text=f"Step {step}/{total_steps}: {message}")
            self.status_bar.config(text=message)
        
        if threading.current_thread() == threading.main_thread():
            _update()
        else:
            self.root.after(0, _update)
    
    def update_button_states(self, installing=False):
        """Update button states based on installation status"""
        def _update():
            if installing:
                self.install_btn.config(state='disabled', text='Installing...')
                self.capture_btn.config(state='disabled')
            else:
                self.install_btn.config(state='normal', text='🚀 Install')
                self.capture_btn.config(state='normal')
        
        if threading.current_thread() == threading.main_thread():
            _update()
        else:
            self.root.after(0, _update)
    
    def check_initial_status(self):
        """Check if system is already installed"""
        if (self.script_dir / "install_fully_automated.sh").exists():
            self.log_message("✅ Installation script found", "success")
        else:
            self.log_message("❌ Installation script not found", "error")
            
        # Check if already installed
        if Path("/opt/xbox360-emulator/installation_complete.txt").exists():
            self.log_message("✅ Xbox 360 emulator appears to be already installed", "success")
            self.log_message("ℹ️  You can reinstall or check status", "info")
    
    def start_installation(self):
        """Start the installation process in a separate thread"""
        if self.is_installing:
            return
            
        self.is_installing = True
        self.update_button_states(installing=True)
        self.log_message("🚀 Starting Xbox 360 WiFi Module Emulator installation...", "header")
        
        # Check if running as root
        if os.geteuid() != 0:
            self.log_message("❌ Installation must be run as root (sudo)", "error")
            messagebox.showerror("Permission Error", 
                               "This installer must be run with root privileges.\n\n"
                               "Please run: sudo python3 installer_ui.py")
            self.is_installing = False
            self.update_button_states(installing=False)
            return
        
        # Start installation thread
        install_thread = threading.Thread(target=self.run_installation, daemon=True)
        install_thread.start()
    
    def run_installation(self):
        """Run the installation process"""
        try:
            install_script = self.script_dir / "install_fully_automated.sh"
            
            if not install_script.exists():
                self.log_message("❌ Installation script not found!", "error")
                self.is_installing = False
                self.update_button_states(installing=False)
                return
            
            # Make script executable
            os.chmod(install_script, 0o755)
            
            # Run installation with live output
            self.log_message("📋 Running automated installation script...", "info")
            
            process = subprocess.Popen(
                ['bash', str(install_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.current_process = process
            step_count = 0
            
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                # Parse progress from output
                if "[Step " in line and "]" in line:
                    try:
                        step_match = re.search(r'\[Step (\d+)/(\d+)\] (.*)', line)
                        if step_match:
                            step_num = int(step_match.group(1))
                            total_steps = int(step_match.group(2))
                            step_message = step_match.group(3)
                            self.update_progress(step_num, total_steps, step_message)
                            step_count = step_num
                    except:
                        pass
                
                # Colorize output based on content
                if "✅" in line or "SUCCESS" in line.upper():
                    tag = "success"
                elif "❌" in line or "ERROR" in line.upper():
                    tag = "error"
                elif "⚠️" in line or "WARNING" in line.upper():
                    tag = "warning"
                elif "ℹ️" in line or "INFO" in line.upper():
                    tag = "info"
                elif "========" in line:
                    tag = "header"
                else:
                    tag = "normal"
                
                self.log_message(line, tag)
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                self.log_message("✅ Installation completed successfully!", "success")
                self.update_progress(self.total_steps, self.total_steps, "Installation complete!")
                messagebox.showinfo("Installation Complete", 
                                  "Xbox 360 WiFi Module Emulator installed successfully!\n\n"
                                  "The system will reboot automatically to activate USB gadget mode.\n"
                                  "After reboot, use 'Check Status' to verify everything is working.")
            else:
                self.log_message(f"❌ Installation failed with return code {return_code}", "error")
                messagebox.showerror("Installation Failed", 
                                   f"Installation failed with return code {return_code}\n"
                                   "Check the output log for details.")
        
        except Exception as e:
            self.log_message(f"❌ Installation error: {str(e)}", "error")
            messagebox.showerror("Installation Error", f"An error occurred during installation:\n{str(e)}")
        
        finally:
            self.is_installing = False
            self.update_button_states(installing=False)
            self.current_process = None
    
    def check_status(self):
        """Check system status"""
        self.log_message("📊 Checking system status...", "info")
        
        status_thread = threading.Thread(target=self.run_status_check, daemon=True)
        status_thread.start()
    
    def run_status_check(self):
        """Run status check in separate thread"""
        try:
            status_script = self.script_dir / "system_status.sh"
            
            if not status_script.exists():
                self.log_message("❌ Status script not found", "error")
                return
            
            # Make script executable
            os.chmod(status_script, 0o755)
            
            # Run status check
            result = subprocess.run(['bash', str(status_script)], 
                                  capture_output=True, text=True, timeout=30)
            
            # Display output
            for line in result.stdout.splitlines():
                if "✅" in line:
                    tag = "success"
                elif "❌" in line:
                    tag = "error"
                elif "⚠️" in line:
                    tag = "warning"
                else:
                    tag = "normal"
                
                self.log_message(line, tag)
            
            if result.stderr:
                self.log_message("Errors from status check:", "error")
                for line in result.stderr.splitlines():
                    self.log_message(line, "error")
        
        except subprocess.TimeoutExpired:
            self.log_message("❌ Status check timed out", "error")
        except Exception as e:
            self.log_message(f"❌ Status check error: {str(e)}", "error")
    
    def start_usb_capture(self):
        """Start USB protocol capture"""
        self.log_message("🕵️ Starting USB protocol capture...", "info")
        
        capture_thread = threading.Thread(target=self.run_usb_capture, daemon=True)
        capture_thread.start()
    
    def run_usb_capture(self):
        """Run USB capture in separate thread"""
        try:
            capture_script = self.script_dir / "quick_capture.sh"
            
            if not capture_script.exists():
                self.log_message("❌ Capture script not found", "error")
                return
            
            # Check if running as root
            if os.geteuid() != 0:
                self.log_message("❌ USB capture requires root privileges", "error")
                return
            
            # Make script executable
            os.chmod(capture_script, 0o755)
            
            # Run capture
            self.log_message("📡 Running USB capture (this may take 30 seconds)...", "info")
            
            result = subprocess.run(['bash', str(capture_script)], 
                                  capture_output=True, text=True, timeout=60)
            
            # Display output
            for line in result.stdout.splitlines():
                if "✅" in line:
                    tag = "success"
                elif "❌" in line:
                    tag = "error"
                elif "📡" in line or "🔍" in line:
                    tag = "info"
                else:
                    tag = "normal"
                
                self.log_message(line, tag)
            
            if result.stderr:
                for line in result.stderr.splitlines():
                    self.log_message(line, "error")
        
        except subprocess.TimeoutExpired:
            self.log_message("❌ USB capture timed out", "error")
        except Exception as e:
            self.log_message(f"❌ USB capture error: {str(e)}", "error")
    
    def reboot_system(self):
        """Reboot the system"""
        if messagebox.askyesno("Reboot System", 
                              "Are you sure you want to reboot the system?\n\n"
                              "This is required after installation to activate USB gadget mode."):
            self.log_message("🔄 Rebooting system...", "info")
            try:
                subprocess.run(['sudo', 'reboot'], check=True)
            except Exception as e:
                self.log_message(f"❌ Reboot failed: {str(e)}", "error")
    
    def process_queue_updates(self):
        """Process any queued UI updates"""
        try:
            while True:
                item = self.process_queue.get_nowait()
                # Process queue items if needed
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue_updates)
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_installing and self.current_process:
            if messagebox.askyesno("Installation in Progress", 
                                  "Installation is currently running. Do you want to cancel it?"):
                try:
                    self.current_process.terminate()
                except:
                    pass
                self.root.destroy()
            else:
                return
        else:
            self.root.destroy()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = Xbox360InstallerGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()