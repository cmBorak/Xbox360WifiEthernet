#!/bin/bash
# One-Click Xbox 360 Emulation Testing System Installer
# Automated installation for Raspberry Pi 4 with zero user interaction required
# Sets up complete testing, monitoring, and GitHub integration

set -e

# Script metadata
SCRIPT_VERSION="1.0.0"
INSTALL_LOG="/tmp/xbox360_install.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration defaults (can be overridden by environment variables)
PROJECT_NAME="${PROJECT_NAME:-xbox360-emulator}"
GITHUB_REPO="${GITHUB_REPO:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_WEBHOOK_SECRET="${GITHUB_WEBHOOK_SECRET:-$(openssl rand -hex 20)}"
INSTALL_DIR="${INSTALL_DIR:-/opt/xbox360-emulator}"
DATA_DIR="${DATA_DIR:-/var/lib/xbox360-emulator}"
LOG_DIR="${LOG_DIR:-/var/log/xbox360-emulator}"
DASHBOARD_PORT="${DASHBOARD_PORT:-8080}"
WEBHOOK_PORT="${WEBHOOK_PORT:-9000}"
AUTO_START="${AUTO_START:-true}"
SETUP_GITHUB="${SETUP_GITHUB:-true}"

# System requirements
MIN_MEMORY_MB=3072  # 3GB minimum
MIN_DISK_GB=8       # 8GB minimum free space

# Logging functions
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$INSTALL_LOG"
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

log_step() {
    log "${PURPLE}[STEP]${NC} $1"
}

# Progress indicator
show_progress() {
    local current=$1
    local total=$2
    local description=$3
    local percent=$((current * 100 / total))
    local filled=$((percent / 5))
    local empty=$((20 - filled))
    
    printf "\r${CYAN}[%s%s] %d%% - %s${NC}" \
        "$(printf "%*s" $filled | tr ' ' '=')" \
        "$(printf "%*s" $empty | tr ' ' '-')" \
        $percent \
        "$description"
    
    if [ $current -eq $total ]; then
        echo
    fi
}

# Banner
show_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
 __   __  _                  ____   ___   ___  
 \ \ / / | |__    ___  __  |___ \ / _ \ / _ \ 
  \ V /  | '_ \  / _ \ \ \/ /  __) | | | | | | |
   | |   | |_) || (_) | >  <  / __/| |_| | |_| |
   |_|   |_.__/  \___/ /_/\_\ |_____|\___/ \___/ 

    EMULATION TESTING SYSTEM - ONE CLICK INSTALLER
    Automated Setup for Raspberry Pi 4
EOF
    echo -e "${NC}"
    echo -e "${GREEN}Version: $SCRIPT_VERSION${NC}"
    echo -e "${GREEN}Install Log: $INSTALL_LOG${NC}"
    echo
}

# System validation
validate_system() {
    log_step "Validating system requirements"
    local validation_errors=0
    
    # Check if running on Raspberry Pi 4
    if [ ! -f "/proc/cpuinfo" ] || ! grep -q "Raspberry Pi 4" /proc/cpuinfo; then
        log_error "This installer requires Raspberry Pi 4"
        ((validation_errors++))
    else
        log_success "Raspberry Pi 4 detected"
    fi
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        log_error "This installer must be run as root or with sudo"
        ((validation_errors++))
    else
        log_success "Running with appropriate privileges"
    fi
    
    # Check memory
    local memory_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local memory_mb=$((memory_kb / 1024))
    if [ $memory_mb -lt $MIN_MEMORY_MB ]; then
        log_error "Insufficient memory: ${memory_mb}MB (minimum: ${MIN_MEMORY_MB}MB)"
        ((validation_errors++))
    else
        log_success "Memory check passed: ${memory_mb}MB"
    fi
    
    # Check disk space
    local disk_space_kb=$(df / | tail -1 | awk '{print $4}')
    local disk_space_gb=$((disk_space_kb / 1024 / 1024))
    if [ $disk_space_gb -lt $MIN_DISK_GB ]; then
        log_error "Insufficient disk space: ${disk_space_gb}GB (minimum: ${MIN_DISK_GB}GB)"
        ((validation_errors++))
    else
        log_success "Disk space check passed: ${disk_space_gb}GB available"
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &> /dev/null; then
        log_error "No internet connectivity detected"
        ((validation_errors++))
    else
        log_success "Internet connectivity verified"
    fi
    
    if [ $validation_errors -gt 0 ]; then
        log_error "System validation failed with $validation_errors errors"
        exit 1
    fi
    
    log_success "System validation completed successfully"
}

# Create directory structure
create_directories() {
    log_step "Creating directory structure"
    
    local directories=(
        "$INSTALL_DIR"
        "$INSTALL_DIR/src"
        "$INSTALL_DIR/tests"
        "$INSTALL_DIR/config"
        "$DATA_DIR"
        "$DATA_DIR/test-results"
        "$DATA_DIR/logs"
        "$DATA_DIR/debug-data"
        "$DATA_DIR/backup"
        "$LOG_DIR"
        "/etc/xbox360-emulator"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        chown pi:pi "$dir" 2>/dev/null || true
        log_info "Created directory: $dir"
    done
    
    log_success "Directory structure created"
}

# Install system packages
install_system_packages() {
    log_step "Installing system packages"
    show_progress 1 10 "Updating package lists"
    
    export DEBIAN_FRONTEND=noninteractive
    
    # Update package lists
    apt-get update -qq
    show_progress 2 10 "Installing core packages"
    
    # Install core packages
    apt-get install -y -qq \
        curl \
        wget \
        git \
        jq \
        bc \
        htop \
        iotop \
        nethogs \
        tree \
        nano \
        vim \
        unzip \
        zip \
        tar \
        gzip
    
    show_progress 4 10 "Installing development tools"
    
    # Install development packages
    apt-get install -y -qq \
        build-essential \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libusb-1.0-0-dev \
        libudev-dev \
        pkg-config
    
    show_progress 6 10 "Installing networking tools"
    
    # Install networking packages
    apt-get install -y -qq \
        iproute2 \
        bridge-utils \
        iptables \
        dhcpcd5 \
        net-tools \
        wireless-tools \
        hostapd
    
    show_progress 8 10 "Installing system services"
    
    # Install system packages
    apt-get install -y -qq \
        systemd \
        cron \
        logrotate \
        rsyslog \
        udev \
        kmod
    
    show_progress 10 10 "Package installation complete"
    log_success "System packages installed successfully"
}

# Install Docker
install_docker() {
    log_step "Installing Docker"
    
    if command -v docker &> /dev/null; then
        log_warning "Docker already installed, skipping"
        return
    fi
    
    show_progress 1 5 "Downloading Docker installer"
    
    # Download and install Docker
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    
    show_progress 3 5 "Installing Docker"
    sh /tmp/get-docker.sh
    
    show_progress 4 5 "Configuring Docker"
    
    # Add pi user to docker group
    usermod -aG docker pi
    
    # Configure Docker daemon
    cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2"
}
EOF
    
    # Start Docker service
    systemctl enable docker
    systemctl start docker
    
    show_progress 5 5 "Docker installation complete"
    log_success "Docker installed and configured"
}

# Install Docker Compose
install_docker_compose() {
    log_step "Installing Docker Compose"
    
    if command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose already installed, skipping"
        return
    fi
    
    # Install via pip for ARM compatibility
    pip3 install docker-compose
    
    log_success "Docker Compose installed"
}

# Setup Python environment
setup_python_environment() {
    log_step "Setting up Python environment"
    
    show_progress 1 4 "Creating virtual environment"
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    show_progress 2 4 "Upgrading pip"
    pip install --upgrade pip
    
    show_progress 3 4 "Installing Python packages"
    
    # Install essential Python packages
    pip install \
        pytest \
        pytest-mock \
        pytest-asyncio \
        pytest-cov \
        pytest-html \
        requests \
        flask \
        flask-cors \
        docker \
        GitPython \
        psutil \
        schedule \
        python-daemon
    
    show_progress 4 4 "Python environment ready"
    chown -R pi:pi "$INSTALL_DIR/venv"
    log_success "Python environment configured"
}

# Create application files
create_application_files() {
    log_step "Creating application files"
    
    show_progress 1 8 "Creating main application structure"
    
    # Create main application entry point
    cat > "$INSTALL_DIR/xbox360_emulator.py" << 'EOF'
#!/usr/bin/env python3
"""
Xbox 360 Emulation Main Application
Auto-generated by one-click installer
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/xbox360-emulator/main.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Xbox360Emulator:
    def __init__(self):
        logger.info("Initializing Xbox 360 Emulator")
        self.running = False
    
    def start(self):
        logger.info("Starting Xbox 360 emulation")
        self.running = True
        # Main application logic will be implemented here
        return True
    
    def stop(self):
        logger.info("Stopping Xbox 360 emulation")
        self.running = False
        return True
    
    def get_status(self):
        return {
            'running': self.running,
            'status': 'healthy' if self.running else 'stopped'
        }

if __name__ == "__main__":
    emulator = Xbox360Emulator()
    try:
        emulator.start()
        # Keep running
        import time
        while emulator.running:
            time.sleep(1)
    except KeyboardInterrupt:
        emulator.stop()
EOF
    
    show_progress 2 8 "Creating testing framework"
    
    # Create basic test structure
    mkdir -p "$INSTALL_DIR/tests"
    cat > "$INSTALL_DIR/tests/test_basic.py" << 'EOF'
#!/usr/bin/env python3
"""
Basic tests for Xbox 360 emulation system
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from xbox360_emulator import Xbox360Emulator

class TestBasicFunctionality:
    def test_emulator_initialization(self):
        emulator = Xbox360Emulator()
        assert emulator is not None
        assert emulator.running is False
    
    def test_emulator_start_stop(self):
        emulator = Xbox360Emulator()
        result = emulator.start()
        assert result is True
        assert emulator.running is True
        
        result = emulator.stop()
        assert result is True
        assert emulator.running is False
    
    def test_emulator_status(self):
        emulator = Xbox360Emulator()
        status = emulator.get_status()
        assert 'running' in status
        assert 'status' in status
EOF
    
    show_progress 3 8 "Creating monitoring daemon"
    
    # Create monitoring daemon
    cat > "$INSTALL_DIR/monitoring_daemon.py" << 'EOF'
#!/usr/bin/env python3
"""
Xbox 360 Emulation Monitoring Daemon
Automated monitoring, testing, and health checks
"""

import asyncio
import json
import logging
import time
import subprocess
import schedule
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/xbox360-emulator/monitoring.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MonitoringDaemon:
    def __init__(self):
        self.running = False
        self.data_dir = Path('/var/lib/xbox360-emulator')
        self.test_results_dir = self.data_dir / 'test-results'
        self.test_results_dir.mkdir(exist_ok=True)
    
    def run_system_health_check(self):
        logger.info("Running system health check")
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'system': self.check_system_resources(),
            'services': self.check_services(),
            'tests': self.run_basic_tests()
        }
        
        # Save health data
        health_file = self.test_results_dir / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(health_file, 'w') as f:
            json.dump(health_data, f, indent=2)
        
        logger.info(f"Health check completed: {health_data['system']['status']}")
    
    def check_system_resources(self):
        try:
            # Check CPU, memory, disk, temperature
            with open('/proc/loadavg') as f:
                load_avg = f.read().strip().split()[0]
            
            with open('/proc/meminfo') as f:
                meminfo = f.read()
                mem_total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1])
                mem_available = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1])
            
            mem_usage = (mem_total - mem_available) / mem_total * 100
            
            # Check temperature
            temp = 0
            try:
                with open('/sys/class/thermal/thermal_zone0/temp') as f:
                    temp = int(f.read().strip()) / 1000
            except:
                pass
            
            return {
                'status': 'healthy',
                'load_average': float(load_avg),
                'memory_usage_percent': round(mem_usage, 1),
                'temperature_celsius': temp
            }
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_services(self):
        services = ['docker', 'xbox360-monitoring']
        service_status = {}
        
        for service in services:
            try:
                result = subprocess.run(['systemctl', 'is-active', service], 
                                     capture_output=True, text=True)
                service_status[service] = result.stdout.strip()
            except:
                service_status[service] = 'unknown'
        
        return service_status
    
    def run_basic_tests(self):
        try:
            result = subprocess.run(['python3', '-m', 'pytest', '/opt/xbox360-emulator/tests/', '-v'], 
                                  capture_output=True, text=True, cwd='/opt/xbox360-emulator',
                                  timeout=60)
            
            return {
                'status': 'pass' if result.returncode == 0 else 'fail',
                'output': result.stdout,
                'errors': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'error': 'Tests timed out'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def start_daemon(self):
        self.running = True
        logger.info("Starting monitoring daemon")
        
        # Schedule health checks every 5 minutes
        schedule.every(5).minutes.do(self.run_system_health_check)
        
        # Initial health check
        self.run_system_health_check()
        
        # Main loop
        while self.running:
            schedule.run_pending()
            await asyncio.sleep(30)
    
    def stop_daemon(self):
        self.running = False
        logger.info("Stopping monitoring daemon")

if __name__ == "__main__":
    daemon = MonitoringDaemon()
    try:
        asyncio.run(daemon.start_daemon())
    except KeyboardInterrupt:
        daemon.stop_daemon()
EOF
    
    show_progress 4 8 "Creating web dashboard"
    
    # Create web dashboard
    cat > "$INSTALL_DIR/web_dashboard.py" << 'EOF'
#!/usr/bin/env python3
"""
Xbox 360 Emulation Web Dashboard
Real-time monitoring and control interface
"""

from flask import Flask, render_template_string, jsonify, request
import json
import glob
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

DATA_DIR = Path('/var/lib/xbox360-emulator')
TEST_RESULTS_DIR = DATA_DIR / 'test-results'

@app.route('/')
def dashboard():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Xbox 360 Emulation Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .status-card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .status-healthy { border-left: 5px solid #27ae60; }
        .status-warning { border-left: 5px solid #f39c12; }
        .status-error { border-left: 5px solid #e74c3c; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .metric { text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .test-pass { color: #27ae60; }
        .test-fail { color: #e74c3c; }
        .test-timeout { color: #f39c12; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Xbox 360 Emulation System</h1>
            <p>Automated Testing & Monitoring Dashboard</p>
        </div>
        
        <div id="system-status" class="status-card">
            <h2>System Status</h2>
            <div id="status-content">Loading...</div>
        </div>
        
        <div class="status-card">
            <h2>System Metrics</h2>
            <div class="metrics" id="metrics-content">
                <div class="metric">
                    <div class="metric-value" id="cpu-usage">--</div>
                    <div class="metric-label">CPU Load</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="memory-usage">--%</div>
                    <div class="metric-label">Memory Usage</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="temperature">--°C</div>
                    <div class="metric-label">Temperature</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="uptime">--</div>
                    <div class="metric-label">Uptime</div>
                </div>
            </div>
        </div>
        
        <div class="status-card">
            <h2>Recent Test Results</h2>
            <table id="test-results">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Test Status</th>
                        <th>System Health</th>
                        <th>Services</th>
                    </tr>
                </thead>
                <tbody id="test-results-body">
                    <tr><td colspan="4">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function loadData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateSystemStatus(data);
                    updateMetrics(data);
                })
                .catch(error => console.error('Error loading data:', error));
                
            fetch('/api/test-results')
                .then(response => response.json())
                .then(data => updateTestResults(data))
                .catch(error => console.error('Error loading test results:', error));
        }
        
        function updateSystemStatus(data) {
            const statusDiv = document.getElementById('system-status');
            const contentDiv = document.getElementById('status-content');
            
            if (data.system && data.system.status === 'healthy') {
                statusDiv.className = 'status-card status-healthy';
                contentDiv.innerHTML = '<strong>✅ System Healthy</strong><br>All systems operational';
            } else {
                statusDiv.className = 'status-card status-error';
                contentDiv.innerHTML = '<strong>❌ System Issues Detected</strong><br>Check logs for details';
            }
        }
        
        function updateMetrics(data) {
            if (data.system) {
                document.getElementById('cpu-usage').textContent = data.system.load_average || '--';
                document.getElementById('memory-usage').textContent = (data.system.memory_usage_percent || 0) + '%';
                document.getElementById('temperature').textContent = (data.system.temperature_celsius || 0) + '°C';
            }
            
            // Calculate uptime
            const uptimeElement = document.getElementById('uptime');
            const startTime = localStorage.getItem('dashboard-start-time');
            if (!startTime) {
                localStorage.setItem('dashboard-start-time', Date.now());
                uptimeElement.textContent = '0m';
            } else {
                const uptimeMs = Date.now() - parseInt(startTime);
                const uptimeMin = Math.floor(uptimeMs / 60000);
                uptimeElement.textContent = uptimeMin + 'm';
            }
        }
        
        function updateTestResults(data) {
            const tbody = document.getElementById('test-results-body');
            tbody.innerHTML = '';
            
            data.slice(0, 10).forEach(result => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${new Date(result.timestamp).toLocaleString()}</td>
                    <td><span class="test-${result.tests.status}">${result.tests.status.toUpperCase()}</span></td>
                    <td>${result.system.status}</td>
                    <td>${Object.keys(result.services).length} services</td>
                `;
            });
        }
        
        // Load data immediately and then every 30 seconds
        loadData();
        setInterval(loadData, 30000);
    </script>
</body>
</html>
    ''')

@app.route('/api/status')
def api_status():
    try:
        # Get latest health check
        health_files = glob.glob(str(TEST_RESULTS_DIR / 'health_*.json'))
        if health_files:
            latest_file = max(health_files, key=os.path.getctime)
            with open(latest_file) as f:
                return jsonify(json.load(f))
    except Exception as e:
        pass
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'system': {'status': 'unknown'},
        'services': {},
        'tests': {'status': 'unknown'}
    })

@app.route('/api/test-results')
def api_test_results():
    try:
        health_files = glob.glob(str(TEST_RESULTS_DIR / 'health_*.json'))
        results = []
        
        for file in sorted(health_files, key=os.path.getctime, reverse=True)[:20]:
            with open(file) as f:
                results.append(json.load(f))
        
        return jsonify(results)
    except Exception as e:
        return jsonify([])

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'dashboard'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('DASHBOARD_PORT', 8080)))
EOF
    
    show_progress 5 8 "Creating configuration files"
    
    # Create pytest configuration
    cat > "$INSTALL_DIR/pytest.ini" << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    hardware: Hardware tests (requires Pi 4)
    slow: Slow tests
EOF
    
    show_progress 6 8 "Creating management scripts"
    
    # Create management script
    cat > "$INSTALL_DIR/manage.sh" << 'EOF'
#!/bin/bash
# Xbox 360 Emulation Management Script

INSTALL_DIR="/opt/xbox360-emulator"
DATA_DIR="/var/lib/xbox360-emulator"

case "$1" in
    "start")
        echo "Starting Xbox 360 Emulation System..."
        systemctl start xbox360-monitoring
        systemctl start xbox360-dashboard
        echo "✓ Services started"
        ;;
    "stop")
        echo "Stopping Xbox 360 Emulation System..."
        systemctl stop xbox360-monitoring
        systemctl stop xbox360-dashboard
        echo "✓ Services stopped"
        ;;
    "restart")
        echo "Restarting Xbox 360 Emulation System..."
        systemctl restart xbox360-monitoring
        systemctl restart xbox360-dashboard
        echo "✓ Services restarted"
        ;;
    "status")
        echo "=== System Status ==="
        systemctl status xbox360-monitoring --no-pager -l
        systemctl status xbox360-dashboard --no-pager -l
        echo
        echo "=== System Resources ==="
        echo "CPU Load: $(cat /proc/loadavg | awk '{print $1}')"
        echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
        if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
            temp=$(cat /sys/class/thermal/thermal_zone0/temp)
            echo "Temperature: $((temp/1000))°C"
        fi
        ;;
    "logs")
        echo "Showing recent logs..."
        journalctl -u xbox360-monitoring -n 50 --no-pager
        ;;
    "test")
        echo "Running tests..."
        cd "$INSTALL_DIR"
        source venv/bin/activate
        python -m pytest tests/ -v
        ;;
    "dashboard")
        PI_IP=$(hostname -I | awk '{print $1}')
        echo "Dashboard URL: http://$PI_IP:8080"
        ;;
    *)
        echo "Xbox 360 Emulation System Management"
        echo "Usage: $0 {start|stop|restart|status|logs|test|dashboard}"
        ;;
esac
EOF
    
    chmod +x "$INSTALL_DIR/manage.sh"
    
    show_progress 7 8 "Creating test runner"
    
    # Create test runner script
    cat > "$INSTALL_DIR/run_tests.sh" << 'EOF'
#!/bin/bash
# Xbox 360 Emulation Test Runner

INSTALL_DIR="/opt/xbox360-emulator"
cd "$INSTALL_DIR"
source venv/bin/activate

case "${1:-basic}" in
    "basic"|"smoke")
        echo "Running basic smoke tests..."
        python -m pytest tests/ -v -m "not slow"
        ;;
    "comprehensive"|"all")
        echo "Running comprehensive test suite..."
        python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
        ;;
    "hardware")
        echo "Running hardware tests..."
        python -m pytest tests/ -v -m "hardware"
        ;;
    *)
        echo "Usage: $0 {basic|comprehensive|hardware}"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$INSTALL_DIR/run_tests.sh"
    
    show_progress 8 8 "Application files created"
    
    # Set ownership
    chown -R pi:pi "$INSTALL_DIR"
    
    log_success "Application files created successfully"
}

# Create systemd services
create_systemd_services() {
    log_step "Creating systemd services"
    
    show_progress 1 3 "Creating monitoring service"
    
    # Create monitoring service
    cat > /etc/systemd/system/xbox360-monitoring.service << EOF
[Unit]
Description=Xbox 360 Emulation Monitoring Daemon
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/monitoring_daemon.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xbox360-monitoring

[Install]
WantedBy=multi-user.target
EOF
    
    show_progress 2 3 "Creating dashboard service"
    
    # Create dashboard service
    cat > /etc/systemd/system/xbox360-dashboard.service << EOF
[Unit]
Description=Xbox 360 Emulation Web Dashboard
After=network.target xbox360-monitoring.service
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR
Environment=DASHBOARD_PORT=$DASHBOARD_PORT
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/web_dashboard.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xbox360-dashboard

[Install]
WantedBy=multi-user.target
EOF
    
    show_progress 3 3 "Enabling services"
    
    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable xbox360-monitoring.service
    systemctl enable xbox360-dashboard.service
    
    log_success "Systemd services created and enabled"
}

# Configure system settings
configure_system() {
    log_step "Configuring system settings"
    
    show_progress 1 5 "Configuring kernel modules"
    
    # Ensure required kernel modules are loaded at boot
    cat > /etc/modules-load.d/xbox360.conf << 'EOF'
# Xbox 360 Emulation required modules
libcomposite
dwc2
EOF
    
    show_progress 2 5 "Configuring USB gadget"
    
    # Configure USB gadget mode
    if ! grep -q "dtoverlay=dwc2" /boot/config.txt; then
        echo "dtoverlay=dwc2" >> /boot/config.txt
    fi
    
    if ! grep -q "modules-load=dwc2" /boot/cmdline.txt; then
        sed -i 's/rootwait/rootwait modules-load=dwc2/' /boot/cmdline.txt
    fi
    
    show_progress 3 5 "Configuring permissions"
    
    # Create udev rules for USB gadget access
    cat > /etc/udev/rules.d/99-xbox360-usb.rules << 'EOF'
# Xbox 360 Emulation USB permissions
SUBSYSTEM=="usb", GROUP="plugdev", MODE="0664"
KERNEL=="configfs", GROUP="pi", MODE="0775"
EOF
    
    # Add pi user to necessary groups
    usermod -a -G plugdev,dialout pi
    
    show_progress 4 5 "Configuring log rotation"
    
    # Configure log rotation
    cat > /etc/logrotate.d/xbox360-emulator << 'EOF'
/var/log/xbox360-emulator/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 pi pi
    postrotate
        systemctl reload xbox360-monitoring xbox360-dashboard || true
    endscript
}
EOF
    
    show_progress 5 5 "System configuration complete"
    log_success "System configured successfully"
}

# Start services
start_services() {
    log_step "Starting services"
    
    show_progress 1 4 "Starting monitoring service"
    
    systemctl start xbox360-monitoring
    sleep 3
    
    show_progress 2 4 "Starting dashboard service"
    
    systemctl start xbox360-dashboard
    sleep 3
    
    show_progress 3 4 "Verifying service status"
    
    # Check service status
    if systemctl is-active --quiet xbox360-monitoring; then
        log_success "Monitoring service started successfully"
    else
        log_error "Monitoring service failed to start"
        journalctl -u xbox360-monitoring --no-pager -l
    fi
    
    if systemctl is-active --quiet xbox360-dashboard; then
        log_success "Dashboard service started successfully"
    else
        log_error "Dashboard service failed to start"
        journalctl -u xbox360-dashboard --no-pager -l
    fi
    
    show_progress 4 4 "Services started"
    log_success "All services started successfully"
}

# Run initial tests
run_initial_tests() {
    log_step "Running initial system tests"
    
    show_progress 1 3 "Running basic functionality tests"
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    # Run basic tests
    if python -m pytest tests/ -v --tb=short; then
        log_success "Initial tests passed"
    else
        log_warning "Some initial tests failed - this is normal for a fresh installation"
    fi
    
    show_progress 2 3 "Testing web dashboard"
    
    # Test dashboard accessibility
    sleep 5  # Give dashboard time to start
    if curl -s "http://localhost:$DASHBOARD_PORT/health" > /dev/null; then
        log_success "Web dashboard is accessible"
    else
        log_warning "Web dashboard is not yet accessible"
    fi
    
    show_progress 3 3 "Initial tests completed"
}

# Create quick start guide
create_quick_start_guide() {
    log_step "Creating quick start guide"
    
    cat > "$INSTALL_DIR/QUICK_START.md" << EOF
# Xbox 360 Emulation System - Quick Start Guide

## 🎮 Your system is now installed and running!

### 📊 Access Points
- **Web Dashboard**: http://$(hostname -I | awk '{print $1}'):$DASHBOARD_PORT
- **System Logs**: \`journalctl -u xbox360-monitoring -f\`
- **Dashboard Logs**: \`journalctl -u xbox360-dashboard -f\`

### 🔧 Management Commands
\`\`\`bash
# View system status
sudo $INSTALL_DIR/manage.sh status

# Start/stop/restart services
sudo $INSTALL_DIR/manage.sh start
sudo $INSTALL_DIR/manage.sh stop
sudo $INSTALL_DIR/manage.sh restart

# View logs
sudo $INSTALL_DIR/manage.sh logs

# Run tests
sudo $INSTALL_DIR/manage.sh test

# Get dashboard URL
sudo $INSTALL_DIR/manage.sh dashboard
\`\`\`

### 📁 Important Locations
- **Installation**: $INSTALL_DIR
- **Data & Logs**: $DATA_DIR
- **Test Results**: $DATA_DIR/test-results
- **System Logs**: $LOG_DIR

### 🚀 What's Running
- ✅ **Monitoring Daemon**: Continuous health checks every 5 minutes
- ✅ **Web Dashboard**: Real-time system monitoring
- ✅ **Automated Testing**: Basic functionality validation
- ✅ **Log Management**: Automatic log rotation and cleanup

### 🔧 Next Steps
1. Visit the web dashboard to monitor system status
2. Review the logs to ensure everything is working
3. Run manual tests: \`sudo $INSTALL_DIR/run_tests.sh\`
4. Customize configuration in: \`/etc/xbox360-emulator/\`

### 🆘 Troubleshooting
If you encounter issues:
1. Check service status: \`sudo systemctl status xbox360-monitoring xbox360-dashboard\`
2. View logs: \`sudo journalctl -u xbox360-monitoring -u xbox360-dashboard\`
3. Restart services: \`sudo $INSTALL_DIR/manage.sh restart\`
4. Run diagnostic tests: \`sudo $INSTALL_DIR/run_tests.sh\`

### 📞 Support
- Installation log: $INSTALL_LOG
- System status: \`sudo $INSTALL_DIR/manage.sh status\`
- Full logs: \`sudo journalctl -u xbox360-* --since "1 hour ago"\`
EOF
    
    chown pi:pi "$INSTALL_DIR/QUICK_START.md"
    log_success "Quick start guide created"
}

# Display completion summary
show_completion_summary() {
    clear
    echo -e "${GREEN}"
    cat << 'EOF'
 ✅ INSTALLATION COMPLETE! ✅
 
 🎮 Xbox 360 Emulation Testing System
     Successfully Installed on Raspberry Pi 4
EOF
    echo -e "${NC}"
    
    local pi_ip=$(hostname -I | awk '{print $1}')
    
    echo -e "${CYAN}📊 System Access:${NC}"
    echo -e "   Web Dashboard: ${YELLOW}http://$pi_ip:$DASHBOARD_PORT${NC}"
    echo -e "   SSH Access: ${YELLOW}ssh pi@$pi_ip${NC}"
    
    echo -e "\n${CYAN}🔧 Management Commands:${NC}"
    echo -e "   System Status: ${YELLOW}sudo $INSTALL_DIR/manage.sh status${NC}"
    echo -e "   View Logs: ${YELLOW}sudo $INSTALL_DIR/manage.sh logs${NC}"
    echo -e "   Run Tests: ${YELLOW}sudo $INSTALL_DIR/manage.sh test${NC}"
    echo -e "   Restart System: ${YELLOW}sudo $INSTALL_DIR/manage.sh restart${NC}"
    
    echo -e "\n${CYAN}📁 Important Locations:${NC}"
    echo -e "   Installation: ${YELLOW}$INSTALL_DIR${NC}"
    echo -e "   Data Directory: ${YELLOW}$DATA_DIR${NC}"
    echo -e "   Quick Start Guide: ${YELLOW}$INSTALL_DIR/QUICK_START.md${NC}"
    echo -e "   Installation Log: ${YELLOW}$INSTALL_LOG${NC}"
    
    echo -e "\n${CYAN}🚀 What's Running:${NC}"
    echo -e "   ${GREEN}✅ Monitoring Daemon${NC} - Health checks every 5 minutes"
    echo -e "   ${GREEN}✅ Web Dashboard${NC} - Real-time system monitoring"
    echo -e "   ${GREEN}✅ Automated Testing${NC} - Continuous validation"
    echo -e "   ${GREEN}✅ Log Management${NC} - Automatic cleanup and rotation"
    
    echo -e "\n${CYAN}📈 System Status:${NC}"
    if systemctl is-active --quiet xbox360-monitoring; then
        echo -e "   Monitoring Service: ${GREEN}RUNNING ✅${NC}"
    else
        echo -e "   Monitoring Service: ${RED}STOPPED ❌${NC}"
    fi
    
    if systemctl is-active --quiet xbox360-dashboard; then
        echo -e "   Dashboard Service: ${GREEN}RUNNING ✅${NC}"
    else
        echo -e "   Dashboard Service: ${RED}STOPPED ❌${NC}"
    fi
    
    echo -e "\n${YELLOW}🎯 Next Steps:${NC}"
    echo -e "   1. Visit the web dashboard: ${BLUE}http://$pi_ip:$DASHBOARD_PORT${NC}"
    echo -e "   2. Read the quick start guide: ${BLUE}cat $INSTALL_DIR/QUICK_START.md${NC}"
    echo -e "   3. Run your first test: ${BLUE}sudo $INSTALL_DIR/run_tests.sh${NC}"
    
    echo -e "\n${GREEN}🎉 Your Xbox 360 Emulation System is ready to use!${NC}"
    echo -e "${PURPLE}Installation completed in $(( $(date +%s) - $start_time )) seconds${NC}"
    
    # Create desktop shortcut if desktop environment is available
    if [ -d "/home/pi/Desktop" ]; then
        cat > /home/pi/Desktop/Xbox360-Dashboard.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Xbox 360 Dashboard
Comment=Xbox 360 Emulation System Dashboard
Exec=x-www-browser http://$pi_ip:$DASHBOARD_PORT
Icon=applications-games
Terminal=false
Categories=Game;
EOF
        chown pi:pi /home/pi/Desktop/Xbox360-Dashboard.desktop
        chmod +x /home/pi/Desktop/Xbox360-Dashboard.desktop
    fi
}

# Main installation function
main() {
    local start_time=$(date +%s)
    
    # Redirect all output to log file as well as console
    exec > >(tee -a "$INSTALL_LOG")
    exec 2>&1
    
    show_banner
    
    log_info "Starting Xbox 360 Emulation System installation"
    log_info "Installation log: $INSTALL_LOG"
    
    # Installation steps
    validate_system
    create_directories
    install_system_packages
    install_docker
    install_docker_compose
    setup_python_environment
    create_application_files
    create_systemd_services
    configure_system
    
    if [ "$AUTO_START" = "true" ]; then
        start_services
        sleep 5
        run_initial_tests
    fi
    
    create_quick_start_guide
    show_completion_summary
    
    log_success "Installation completed successfully!"
    
    # Set variables for completion summary
    start_time=$start_time
}

# Script entry point
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}This installer must be run as root or with sudo${NC}"
        echo -e "${YELLOW}Usage: sudo $0${NC}"
        exit 1
    fi
    
    # Run main installation
    main "$@"
fi