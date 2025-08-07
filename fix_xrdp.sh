#!/bin/bash
# Comprehensive xRDP Fix Script for Raspberry Pi 4
# Diagnoses and fixes common xRDP connection and performance issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Logging
LOG_FILE="/tmp/xrdp_fix_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

show_banner() {
    clear
    echo -e "${PURPLE}"
    cat << 'EOF'
 ██╗  ██╗██████╗ ██████╗ ██████╗     ███████╗██╗██╗  ██╗
 ╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗    ██╔════╝██║╚██╗██╔╝
  ╚███╔╝ ██████╔╝██║  ██║██████╔╝    █████╗  ██║ ╚███╔╝ 
  ██╔██╗ ██╔══██╗██║  ██║██╔═══╝     ██╔══╝  ██║ ██╔██╗ 
 ██╔╝ ██╗██║  ██║██████╔╝██║         ██║     ██║██╔╝ ██╗
 ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝         ╚═╝     ╚═╝╚═╝  ╚═╝
                                                         
    Raspberry Pi 4 xRDP Comprehensive Fix Tool
EOF
    echo -e "${NC}"
    log_info "Starting xRDP diagnosis and repair"
    log_info "Log file: $LOG_FILE"
    echo
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
    log_success "Running with appropriate privileges"
}

# Check if running on Raspberry Pi
check_pi() {
    if [ ! -f "/proc/cpuinfo" ] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        log_warning "Not running on Raspberry Pi - some fixes may not apply"
    else
        log_success "Raspberry Pi detected"
    fi
}

# Diagnose current xRDP status
diagnose_xrdp() {
    log_info "Diagnosing current xRDP status..."
    
    # Check if xRDP is installed
    if ! dpkg -l | grep -q xrdp; then
        log_warning "xRDP is not installed"
        return 1
    fi
    log_success "xRDP package is installed"
    
    # Check xRDP service status
    if systemctl is-active --quiet xrdp; then
        log_success "xRDP service is running"
    else
        log_warning "xRDP service is not running"
    fi
    
    # Check if xRDP is listening on port 3389
    if netstat -tlnp | grep -q ":3389"; then
        log_success "xRDP is listening on port 3389"
    else
        log_warning "xRDP is not listening on port 3389"
    fi
    
    # Check desktop environment
    if pgrep -x "lxsession" > /dev/null; then
        log_success "LXDE desktop environment detected"
    elif pgrep -x "gnome-session" > /dev/null; then
        log_success "GNOME desktop environment detected"
    elif pgrep -x "xfce4-session" > /dev/null; then
        log_success "XFCE desktop environment detected"
    else
        log_warning "No desktop environment detected or session not running"
    fi
    
    # Check VNC conflicts
    if pgrep -x "vncserver" > /dev/null; then
        log_warning "VNC server is running - may conflict with xRDP"
    fi
    
    # Check for common configuration files
    if [ -f "/etc/xrdp/xrdp.ini" ]; then
        log_success "xRDP configuration file exists"
    else
        log_error "xRDP configuration file missing"
    fi
    
    return 0
}

# Install and configure xRDP
install_xrdp() {
    log_info "Installing and configuring xRDP..."
    
    # Update package lists
    apt-get update -qq
    
    # Install xRDP and dependencies
    apt-get install -y xrdp xrdp-pulseaudio-installer
    
    # Install desktop environment if not present
    if ! pgrep -x "lxsession" > /dev/null && ! pgrep -x "gnome-session" > /dev/null; then
        log_info "Installing LXDE desktop environment..."
        apt-get install -y lxde-core lxde-icon-theme
    fi
    
    log_success "xRDP installed successfully"
}

# Fix xRDP configuration
fix_xrdp_config() {
    log_info "Configuring xRDP for optimal performance..."
    
    # Backup original configuration
    cp /etc/xrdp/xrdp.ini /etc/xrdp/xrdp.ini.backup.$(date +%Y%m%d_%H%M%S)
    
    # Configure xRDP for better performance
    cat > /etc/xrdp/xrdp.ini << 'EOF'
[Globals]
; xrdp.ini file version number
ini_version=1

; Fork a new process for each incoming connection
fork=true
; TCP port to listen on
port=3389
; Regulate if the listening socket use socket option tcp_nodelay
; no buffering will be performed in the TCP stack
tcp_nodelay=true
; Regulate if the listening socket use socket option tcp_keepalive
; Keep TCP connection alive
tcp_keepalive=true
; Set tcp send/recv buffer
tcp_send_buffer_bytes=32768
tcp_recv_buffer_bytes=32768

; Security layer (rdp, tls, negotiate, negotiate_security)
security_layer=negotiate
; Certificate and key file locations
certificate=/etc/xrdp/cert.pem
key_file=/etc/xrdp/key.pem
; SSL protocols and ciphers (TLSv1.2, TLSv1.3)
tls_ciphers=HIGH

; Set login mode (0=ask user, 1=auto login, 2=auto login with domain)
ls_title=Raspberry Pi Remote Desktop
ls_full_window_title=Raspberry Pi RDP
ls_logo_filename=
; Domain name
ls_domain=
; Username and password (leave empty for manual entry)
ls_username=ASK
ls_password=ASK
; Working directory
ls_work_directory=
; Session startup program
ls_connect_tool=console
; Allow empty passwords (not recommended)
allow_empty_passwords=false

; Channel settings
; Enable clipboard redirection
enable_rdpdr=true
; Enable printer redirection  
enable_rdpprinter=false
; Enable serial port redirection
enable_rdpcomm=false
; Enable smart card redirection
enable_rdpscard=false

[Xorg]
name=Xorg
lib=libxup.so
username=ask
password=ask
ip=127.0.0.1
port=-1
code=20

[vnc-any]
name=vnc-any
lib=libvnc.so
username=ask
password=ask
ip=ask
port=ask5900
#delay_ms=2000

[neutrinordp-any]
name=neutrinordp-any
lib=libxrdpneutrinordp.so
username=ask
password=ask
ip=ask
port=ask3389

[Xvnc]
name=Xvnc  
lib=libvnc.so
username=ask
password=ask
ip=127.0.0.1
port=-1
#delay_ms=2000
EOF

    log_success "xRDP configuration updated"
}

# Fix session configuration
fix_session_config() {
    log_info "Configuring xRDP session settings..."
    
    # Create/update startwm.sh for better compatibility
    cat > /etc/xrdp/startwm.sh << 'EOF'
#!/bin/sh
# xrdp X session start script (c) 2015, 2017, 2021 mirabilos
# published under The MirOS Licence

# Rely on /etc/pam.d/xrdp-sesman using pam_env to load both
# /etc/environment and /etc/default/locale to initialise the
# locale and the user environment properly.

if test -r /etc/profile; then
	. /etc/profile
fi

# Check for Raspberry Pi specific setup
if test -r /etc/X11/Xsession.d/45x11-common_env; then
    . /etc/X11/Xsession.d/45x11-common_env
fi

# Set up environment for GUI applications
export XDG_CURRENT_DESKTOP=LXDE
export XDG_SESSION_DESKTOP=LXDE
export XDG_SESSION_TYPE=x11

# Fix for PolicyKit authentication in remote sessions
if test -z "$XDG_RUNTIME_DIR"; then
    export XDG_RUNTIME_DIR=/run/user/$(id -u)
fi

# Start the appropriate desktop environment
if command -v startlxde >/dev/null 2>&1; then
    exec startlxde
elif command -v gnome-session >/dev/null 2>&1; then
    exec gnome-session
elif command -v startxfce4 >/dev/null 2>&1; then
    exec startxfce4
elif command -v openbox-session >/dev/null 2>&1; then
    exec openbox-session
else
    # Fallback to basic X session
    xterm &
    exec /usr/bin/x-window-manager
fi
EOF

    chmod +x /etc/xrdp/startwm.sh
    
    log_success "xRDP session configuration updated"
}

# Fix user permissions and groups
fix_permissions() {
    log_info "Fixing user permissions and groups..."
    
    # Add xrdp user to ssl-cert group for certificate access
    usermod -a -G ssl-cert xrdp
    
    # Add pi user to necessary groups for RDP access
    usermod -a -G video pi
    usermod -a -G audio pi
    usermod -a -G pulse pi
    usermod -a -G input pi
    
    # Fix xRDP certificate permissions
    chown root:ssl-cert /etc/xrdp/cert.pem /etc/xrdp/key.pem 2>/dev/null || true
    chmod 640 /etc/xrdp/cert.pem /etc/xrdp/key.pem 2>/dev/null || true
    
    log_success "Permissions and groups configured"
}

# Configure audio redirection
fix_audio() {
    log_info "Configuring audio redirection..."
    
    # Install pulseaudio xRDP module
    apt-get install -y pulseaudio-module-xrdp
    
    # Configure PulseAudio for xRDP
    if [ ! -f /etc/pulse/xrdp-pulse.conf ]; then
        cat > /etc/pulse/xrdp-pulse.conf << 'EOF'
# PulseAudio configuration for xRDP
# Load the xRDP module
.ifexists module-xrdp-sink.so
load-module module-xrdp-sink
.endif

.ifexists module-xrdp-source.so  
load-module module-xrdp-source
.endif
EOF
    fi
    
    # Update default PulseAudio configuration
    if ! grep -q "xrdp-pulse.conf" /etc/pulse/default.pa; then
        echo ".include /etc/pulse/xrdp-pulse.conf" >> /etc/pulse/default.pa
    fi
    
    log_success "Audio redirection configured"
}

# Stop conflicting services
stop_conflicts() {
    log_info "Stopping conflicting services..."
    
    # Stop VNC services if running
    for service in vncserver-x11-serviced realvnc-xvnc-DefaultUser tightvncserver; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log_info "Stopping conflicting service: $service"
            systemctl stop "$service"
            systemctl disable "$service" 2>/dev/null || true
        fi
    done
    
    # Kill any running VNC processes
    pkill -f vnc 2>/dev/null || true
    
    log_success "Conflicting services stopped"
}

# Configure firewall for xRDP
configure_firewall() {
    log_info "Configuring firewall for xRDP..."
    
    # Check if ufw is installed and active
    if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
        log_info "UFW firewall detected, opening port 3389"
        ufw allow 3389/tcp
    fi
    
    # Check if iptables rules exist that might block xRDP
    if iptables -L INPUT -n | grep -q "DROP.*tcp.*3389"; then
        log_warning "iptables rules may be blocking port 3389"
        log_info "Adding iptables rule to allow xRDP"
        iptables -I INPUT -p tcp --dport 3389 -j ACCEPT
        
        # Save iptables rules
        if command -v iptables-save >/dev/null 2>&1; then
            iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
    fi
    
    log_success "Firewall configured for xRDP"
}

# Enable and start xRDP service
start_xrdp() {
    log_info "Starting xRDP services..."
    
    # Enable xRDP services
    systemctl enable xrdp
    systemctl enable xrdp-sesman
    
    # Restart xRDP services
    systemctl restart xrdp-sesman
    systemctl restart xrdp
    
    # Wait a moment for services to start
    sleep 3
    
    # Check if services started successfully
    if systemctl is-active --quiet xrdp && systemctl is-active --quiet xrdp-sesman; then
        log_success "xRDP services started successfully"
    else
        log_error "Failed to start xRDP services"
        return 1
    fi
    
    return 0
}

# Test xRDP connection
test_connection() {
    log_info "Testing xRDP connection..."
    
    # Check if xRDP is listening
    if netstat -tlnp | grep -q ":3389"; then
        log_success "xRDP is listening on port 3389"
    else
        log_error "xRDP is not listening on port 3389"
        return 1
    fi
    
    # Get Pi IP address
    PI_IP=$(hostname -I | awk '{print $1}')
    log_success "Pi IP address: $PI_IP"
    
    # Test basic connection (without authentication)
    if timeout 5 bash -c "echo >/dev/tcp/$PI_IP/3389" 2>/dev/null; then
        log_success "Basic TCP connection to port 3389 successful"
    else
        log_warning "Could not establish TCP connection to port 3389"
    fi
    
    return 0
}

# Performance optimization
optimize_performance() {
    log_info "Applying performance optimizations..."
    
    # Configure xRDP for better performance
    cat >> /etc/xrdp/xrdp.ini << 'EOF'

; Performance optimizations
max_bpp=24
xserverbpp=24
channel.rdpdr=true
channel.rdpsnd=true
channel.drdynvc=true
channel.cliprdr=true

; Compression settings
crypt_level=low
compression=true
use_compression_ratio=6:1

; Connection settings  
max_idle_time=0
max_disc_time=0
kill_disconnected=false
EOF

    # Configure session limits
    if [ -f /etc/security/limits.conf ]; then
        if ! grep -q "xrdp" /etc/security/limits.conf; then
            cat >> /etc/security/limits.conf << 'EOF'

# xRDP optimizations
xrdp soft nofile 4096
xrdp hard nofile 8192
EOF
        fi
    fi
    
    log_success "Performance optimizations applied"
}

# Create connection troubleshooting script
create_troubleshoot_script() {
    log_info "Creating troubleshooting script..."
    
    cat > /usr/local/bin/xrdp-troubleshoot << 'EOF'
#!/bin/bash
# xRDP Troubleshooting Script

echo "=== xRDP Status Check ==="
echo "Date: $(date)"
echo

echo "--- Service Status ---"
systemctl status xrdp --no-pager -l
echo
systemctl status xrdp-sesman --no-pager -l
echo

echo "--- Network Status ---"
echo "Listening ports:"
netstat -tlnp | grep 3389
echo

echo "--- Process Status ---"
echo "xRDP processes:"
ps aux | grep xrdp | grep -v grep
echo

echo "--- Log Files ---"
echo "Recent xRDP logs:"
tail -n 20 /var/log/xrdp/xrdp.log 2>/dev/null || echo "No xRDP log found"
echo
echo "Recent xRDP session logs:"
tail -n 20 /var/log/xrdp/xrdp-sesman.log 2>/dev/null || echo "No session log found"
echo

echo "--- Configuration ---"
echo "xRDP configuration:"
grep -v "^;" /etc/xrdp/xrdp.ini | grep -v "^$" | head -20
echo

echo "--- System Info ---"
echo "Desktop processes:"
ps aux | grep -E "(lxsession|gnome|xfce)" | grep -v grep
echo

echo "--- Firewall Status ---"
if command -v ufw >/dev/null; then
    echo "UFW status:"
    ufw status
fi
echo

echo "=== End Status Check ==="
EOF

    chmod +x /usr/local/bin/xrdp-troubleshoot
    log_success "Troubleshooting script created: /usr/local/bin/xrdp-troubleshoot"
}

# Display connection information
show_connection_info() {
    local pi_ip=$(hostname -I | awk '{print $1}')
    
    echo
    echo -e "${GREEN}=== xRDP Configuration Complete ===${NC}"
    echo
    echo -e "${BLUE}Connection Information:${NC}"
    echo -e "  IP Address: ${YELLOW}$pi_ip${NC}"
    echo -e "  Port: ${YELLOW}3389${NC}"
    echo -e "  Protocol: ${YELLOW}RDP${NC}"
    echo
    echo -e "${BLUE}To connect from Windows:${NC}"
    echo -e "  1. Open 'Remote Desktop Connection'"
    echo -e "  2. Enter: ${YELLOW}$pi_ip:3389${NC}"
    echo -e "  3. Username: ${YELLOW}pi${NC} (or your username)"
    echo -e "  4. Password: ${YELLOW}[your password]${NC}"
    echo
    echo -e "${BLUE}To connect from other systems:${NC}"
    echo -e "  • Linux: rdesktop -u pi $pi_ip:3389"
    echo -e "  • macOS: Use Microsoft Remote Desktop from App Store"
    echo -e "  • Mobile: Use RD Client apps"
    echo
    echo -e "${BLUE}Troubleshooting:${NC}"
    echo -e "  • Check status: ${YELLOW}sudo systemctl status xrdp${NC}"
    echo -e "  • View logs: ${YELLOW}sudo tail -f /var/log/xrdp/xrdp.log${NC}"
    echo -e "  • Run diagnostics: ${YELLOW}sudo xrdp-troubleshoot${NC}"
    echo -e "  • Restart service: ${YELLOW}sudo systemctl restart xrdp${NC}"
    echo
    echo -e "${GREEN}Installation log saved to: $LOG_FILE${NC}"
}

# Main execution function
main() {
    show_banner
    check_root
    check_pi
    
    if ! diagnose_xrdp; then
        log_info "xRDP not properly installed, installing..."
        install_xrdp
    fi
    
    stop_conflicts
    fix_xrdp_config
    fix_session_config
    fix_permissions
    fix_audio
    configure_firewall
    optimize_performance
    
    if start_xrdp; then
        sleep 2
        test_connection
        create_troubleshoot_script
        show_connection_info
        log_success "xRDP fix completed successfully!"
    else
        log_error "xRDP service failed to start properly"
        log_info "Check the logs and try running: sudo xrdp-troubleshoot"
        exit 1
    fi
}

# Run main function
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi