#!/bin/bash
# Automated Testing System Installation Script for Raspberry Pi 4
# Sets up continuous testing, monitoring, and automated error recovery

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=== Xbox 360 Emulation Automated Testing Setup ===${NC}\n"

# Check if running on Raspberry Pi 4
check_hardware() {
    echo -e "${YELLOW}Checking hardware compatibility...${NC}"
    
    if [ ! -f "/proc/cpuinfo" ]; then
        echo -e "${RED}Error: /proc/cpuinfo not found${NC}"
        exit 1
    fi
    
    if ! grep -q "Raspberry Pi 4" /proc/cpuinfo; then
        echo -e "${RED}Error: This script requires Raspberry Pi 4${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Running on Raspberry Pi 4${NC}"
}

# Install system dependencies
install_system_dependencies() {
    echo -e "${YELLOW}Installing system dependencies...${NC}"
    
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        libusb-1.0-0-dev \
        libudev-dev \
        git \
        curl \
        systemd \
        cron \
        logrotate \
        htop \
        iotop \
        nethogs
    
    echo -e "${GREEN}✓ System dependencies installed${NC}"
}

# Setup Python virtual environment
setup_python_environment() {
    echo -e "${YELLOW}Setting up Python environment...${NC}"
    
    cd "$PROJECT_ROOT"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-test.txt
    pip install python-daemon schedule psutil
    
    echo -e "${GREEN}✓ Python environment ready${NC}"
}

# Create systemd service for automated testing daemon
create_systemd_service() {
    echo -e "${YELLOW}Creating systemd service...${NC}"
    
    sudo tee /etc/systemd/system/xbox360-testing-daemon.service > /dev/null <<EOF
[Unit]
Description=Xbox 360 Emulation Automated Testing Daemon
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PROJECT_ROOT/venv/bin/python $PROJECT_ROOT/automated_testing_daemon.py --config $PROJECT_ROOT/test_daemon_config.json
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xbox360-testing

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_ROOT

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable xbox360-testing-daemon.service
    
    echo -e "${GREEN}✓ Systemd service created and enabled${NC}"
}

# Setup log rotation
setup_log_rotation() {
    echo -e "${YELLOW}Setting up log rotation...${NC}"
    
    sudo tee /etc/logrotate.d/xbox360-testing > /dev/null <<EOF
$PROJECT_ROOT/test-results/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 pi pi
    postrotate
        systemctl reload xbox360-testing-daemon || true
    endscript
}

/var/log/xbox360-testing.log {
    daily  
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 pi pi
}
EOF
    
    echo -e "${GREEN}✓ Log rotation configured${NC}"
}

# Create monitoring cron jobs
setup_monitoring_cron() {
    echo -e "${YELLOW}Setting up monitoring cron jobs...${NC}"
    
    # Create monitoring script
    cat > "$PROJECT_ROOT/system_monitor.sh" <<'EOF'
#!/bin/bash
# System monitoring script for Xbox 360 emulation

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$PROJECT_ROOT/test-results/system_monitor.log"

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check system resources
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
TEMP=$(vcgencmd measure_temp | cut -d'=' -f2 | cut -d'\'' -f1)

log_with_timestamp "CPU: ${CPU_USAGE}%, Memory: ${MEM_USAGE}%, Disk: ${DISK_USAGE}%, Temp: ${TEMP}°C"

# Check service status
if systemctl is-active --quiet xbox360-testing-daemon; then
    log_with_timestamp "Testing daemon: RUNNING"
else
    log_with_timestamp "Testing daemon: STOPPED - Attempting restart"
    systemctl restart xbox360-testing-daemon
fi

# Check for high resource usage
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    log_with_timestamp "WARNING: High CPU usage: ${CPU_USAGE}%"
fi

if (( $(echo "$MEM_USAGE > 85" | bc -l) )); then
    log_with_timestamp "WARNING: High memory usage: ${MEM_USAGE}%"
fi

if [ "$DISK_USAGE" -gt 90 ]; then
    log_with_timestamp "WARNING: High disk usage: ${DISK_USAGE}%"
    # Cleanup old test results
    find "$PROJECT_ROOT/test-results" -name "*.log" -mtime +7 -delete
    find "$PROJECT_ROOT/test-results" -name "*.json" -mtime +14 -delete
    find "$PROJECT_ROOT/test-results" -name "*.html" -mtime +14 -delete
fi

if (( $(echo "$TEMP > 75" | bc -l) )); then
    log_with_timestamp "WARNING: High temperature: ${TEMP}°C"
fi
EOF

    chmod +x "$PROJECT_ROOT/system_monitor.sh"
    
    # Add cron jobs
    (crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_ROOT/system_monitor.sh") | crontab -
    (crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_ROOT/run_tests.sh comprehensive > /dev/null 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "*/30 * * * * $PROJECT_ROOT/run_tests.sh smoke > /dev/null 2>&1") | crontab -
    
    echo -e "${GREEN}✓ Monitoring cron jobs configured${NC}"
}

# Create configuration files
create_config_files() {
    echo -e "${YELLOW}Creating configuration files...${NC}"
    
    # Create test daemon config
    cat > "$PROJECT_ROOT/test_daemon_config.json" <<EOF
{
  "test_interval_minutes": 15,
  "full_test_interval_hours": 6,
  "health_check_interval_minutes": 5,
  "max_fix_attempts": 3,
  "results_directory": "./test-results",
  "log_level": "INFO",
  "enable_auto_recovery": true,
  "enable_hardware_tests": true,
  "enable_network_tests": true,
  "enable_usb_tests": true,
  "enable_notifications": false,
  "notification_webhook": null,
  "test_types": {
    "quick_smoke": ["system_health", "basic_functionality"],
    "comprehensive": ["unit_tests", "integration_tests", "hardware_tests"],
    "critical_path": ["usb_gadget_activation", "network_bridge", "xbox_protocol"]
  },
  "auto_recovery_enabled": true,
  "performance_monitoring": {
    "cpu_threshold": 80,
    "memory_threshold": 85,
    "disk_threshold": 90,
    "temperature_threshold": 75
  }
}
EOF
    
    # Create test directories
    mkdir -p "$PROJECT_ROOT/test-results"
    mkdir -p "$PROJECT_ROOT/logs"
    
    echo -e "${GREEN}✓ Configuration files created${NC}"
}

# Set proper permissions
set_permissions() {
    echo -e "${YELLOW}Setting permissions...${NC}"
    
    # Ensure pi user can access USB gadget configuration
    sudo usermod -a -G dialout pi
    
    # Set project permissions
    sudo chown -R pi:pi "$PROJECT_ROOT"
    chmod +x "$PROJECT_ROOT/automated_testing_daemon.py"
    chmod +x "$PROJECT_ROOT/run_tests.sh"
    chmod +x "$PROJECT_ROOT/system_monitor.sh"
    
    # Create sudoers rule for necessary commands
    sudo tee /etc/sudoers.d/xbox360-testing > /dev/null <<EOF
# Allow pi user to run necessary commands for Xbox 360 testing
pi ALL=(ALL) NOPASSWD: /sbin/modprobe
pi ALL=(ALL) NOPASSWD: /sbin/modprobe -r  
pi ALL=(ALL) NOPASSWD: /usr/sbin/ip
pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart networking
pi ALL=(ALL) NOPASSWD: /usr/sbin/dhclient
pi ALL=(ALL) NOPASSWD: /usr/sbin/sysctl
pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart xbox360-testing-daemon
EOF
    
    echo -e "${GREEN}✓ Permissions configured${NC}"
}

# Start services
start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    
    sudo systemctl start xbox360-testing-daemon
    
    # Wait a moment and check status
    sleep 5
    
    if systemctl is-active --quiet xbox360-testing-daemon; then
        echo -e "${GREEN}✓ Testing daemon started successfully${NC}"
    else
        echo -e "${RED}✗ Testing daemon failed to start${NC}"
        sudo systemctl status xbox360-testing-daemon
    fi
}

# Create web dashboard (optional)
setup_web_dashboard() {
    echo -e "${YELLOW}Setting up web dashboard (optional)...${NC}"
    
    read -p "Would you like to install a web dashboard for monitoring? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install flask flask-cors
        
        cat > "$PROJECT_ROOT/web_dashboard.py" <<'EOF'
#!/usr/bin/env python3
"""
Simple web dashboard for Xbox 360 emulation testing results
"""
from flask import Flask, render_template_string, jsonify
import json
import glob
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Xbox 360 Emulation Testing Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status-healthy { color: green; }
        .status-unhealthy { color: red; }
        .test-pass { background: #d4edda; }
        .test-fail { background: #f8d7da; }
        .test-error { background: #fff3cd; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Xbox 360 Emulation Testing Dashboard</h1>
    <div id="status"></div>
    <div id="results"></div>
    
    <script>
        function loadData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = 
                        '<h2>System Status: <span class="status-' + 
                        (data.healthy ? 'healthy">Healthy' : 'unhealthy">Unhealthy') + 
                        '</span></h2><p>Last Check: ' + data.last_check + '</p>';
                });
                
            fetch('/api/recent-tests')
                .then(response => response.json())
                .then(data => {
                    let html = '<h2>Recent Test Results</h2><table><tr><th>Test</th><th>Status</th><th>Duration</th><th>Time</th></tr>';
                    data.forEach(test => {
                        html += '<tr class="test-' + test.status + '"><td>' + test.name + 
                               '</td><td>' + test.status + '</td><td>' + test.duration + 
                               's</td><td>' + test.timestamp + '</td></tr>';
                    });
                    html += '</table>';
                    document.getElementById('results').innerHTML = html;
                });
        }
        
        loadData();
        setInterval(loadData, 30000);
    </script>
</body>
</html>
    ''')

@app.route('/api/status')
def api_status():
    try:
        status_files = glob.glob('test-results/health_check_*.json')
        if status_files:
            latest_file = max(status_files)
            with open(latest_file) as f:
                data = json.load(f)
            return jsonify({
                'healthy': data['status'] == 'healthy',
                'last_check': data['last_check']
            })
    except:
        pass
    return jsonify({'healthy': False, 'last_check': 'Unknown'})

@app.route('/api/recent-tests')
def api_recent_tests():
    tests = []
    try:
        test_files = glob.glob('test-results/*.json')
        test_files.sort(reverse=True)
        
        for file in test_files[:10]:  # Last 10 test files
            with open(file) as f:
                data = json.load(f)
                if 'results' in data:
                    for result in data['results']:
                        tests.append({
                            'name': result['test_name'],
                            'status': result['status'],
                            'duration': result['duration'],
                            'timestamp': result['timestamp']
                        })
    except:
        pass
    
    return jsonify(tests[:20])  # Return last 20 tests

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF
        
        chmod +x "$PROJECT_ROOT/web_dashboard.py"
        
        # Create systemd service for web dashboard
        sudo tee /etc/systemd/system/xbox360-dashboard.service > /dev/null <<EOF
[Unit]
Description=Xbox 360 Testing Dashboard
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PROJECT_ROOT/venv/bin/python $PROJECT_ROOT/web_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable xbox360-dashboard.service
        sudo systemctl start xbox360-dashboard.service
        
        echo -e "${GREEN}✓ Web dashboard installed and started on port 8080${NC}"
    fi
}

# Main installation flow
main() {
    echo -e "${BLUE}Starting automated testing system installation...${NC}\n"
    
    check_hardware
    install_system_dependencies
    setup_python_environment
    create_config_files
    set_permissions
    create_systemd_service
    setup_log_rotation
    setup_monitoring_cron
    start_services
    setup_web_dashboard
    
    echo -e "\n${GREEN}=== Installation Complete ===${NC}"
    echo -e "${GREEN}✓ Automated testing daemon is running${NC}"
    echo -e "${GREEN}✓ System monitoring is active${NC}"
    echo -e "${GREEN}✓ Automatic error recovery is enabled${NC}"
    echo -e "\n${BLUE}Service Management:${NC}"
    echo -e "  Start daemon: ${YELLOW}sudo systemctl start xbox360-testing-daemon${NC}"
    echo -e "  Stop daemon:  ${YELLOW}sudo systemctl stop xbox360-testing-daemon${NC}"
    echo -e "  View logs:    ${YELLOW}journalctl -u xbox360-testing-daemon -f${NC}"
    echo -e "  Manual tests: ${YELLOW}$PROJECT_ROOT/run_tests.sh [quick|comprehensive]${NC}"
    echo -e "\n${BLUE}Test Results Location: ${YELLOW}$PROJECT_ROOT/test-results/${NC}"
    
    if systemctl is-active --quiet xbox360-dashboard 2>/dev/null; then
        PI_IP=$(hostname -I | awk '{print $1}')
        echo -e "${BLUE}Web Dashboard: ${YELLOW}http://$PI_IP:8080${NC}"
    fi
}

# Run main function
main "$@"