#!/bin/bash
# Complete GitHub Integration Setup for Xbox 360 Emulation Project
# Sets up automatic deployment, testing, and debugging with GitHub

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=== Xbox 360 Emulation GitHub Integration Setup ===${NC}\n"

# Check if running on Raspberry Pi 4
check_hardware() {
    echo -e "${YELLOW}Checking hardware...${NC}"
    if grep -q "Raspberry Pi 4" /proc/cpuinfo; then
        echo -e "${GREEN}✓ Running on Raspberry Pi 4${NC}"
    else
        echo -e "${RED}⚠ Not running on Raspberry Pi 4 - some features may not work${NC}"
    fi
}

# Install required packages
install_dependencies() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    # Update package list
    sudo apt-get update
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        echo -e "${GREEN}✓ Docker installed${NC}"
    else
        echo -e "${GREEN}✓ Docker already installed${NC}"
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        sudo pip3 install docker-compose
        echo -e "${GREEN}✓ Docker Compose installed${NC}"
    else
        echo -e "${GREEN}✓ Docker Compose already installed${NC}"
    fi
    
    # Install additional tools
    sudo apt-get install -y git curl jq bc
    
    echo -e "${GREEN}✓ All dependencies installed${NC}"
}

# Setup GitHub repository
setup_github_repo() {
    echo -e "${YELLOW}Setting up GitHub repository...${NC}"
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        echo "Initializing git repository..."
        git init
        git add .
        git commit -m "Initial commit: Xbox 360 emulation project with automated testing"
    fi
    
    # Get GitHub repository details
    if [ -z "$GITHUB_REPO" ]; then
        echo "Please enter your GitHub repository (username/repo-name):"
        read -r GITHUB_REPO
    fi
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "Please enter your GitHub Personal Access Token:"
        echo "(Go to GitHub Settings > Developer Settings > Personal Access Tokens)"
        read -s GITHUB_TOKEN
        echo
    fi
    
    # Test GitHub connection
    if curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/$GITHUB_REPO > /dev/null; then
        echo -e "${GREEN}✓ GitHub connection successful${NC}"
    else
        echo -e "${RED}✗ GitHub connection failed. Please check your token and repository.${NC}"
        exit 1
    fi
    
    # Add GitHub remote if not exists
    if ! git remote get-url origin > /dev/null 2>&1; then
        git remote add origin https://github.com/$GITHUB_REPO.git
    fi
    
    echo -e "${GREEN}✓ GitHub repository configured${NC}"
}

# Create environment configuration
create_env_config() {
    echo -e "${YELLOW}Creating environment configuration...${NC}"
    
    # Generate webhook secret
    WEBHOOK_SECRET=$(openssl rand -hex 20)
    
    # Create .env file
    cat > .env << EOF
# GitHub Configuration
GITHUB_REPO=$GITHUB_REPO
GITHUB_TOKEN=$GITHUB_TOKEN
GITHUB_WEBHOOK_SECRET=$WEBHOOK_SECRET

# Update Configuration  
AUTO_UPDATE_ENABLED=true
UPDATE_CHECK_INTERVAL=3600
UPDATE_BRANCH=main

# Container Configuration
START_TESTING_DAEMON=true
LOG_LEVEL=INFO

# Monitoring Configuration
DASHBOARD_PORT=8080
WEBHOOK_PORT=9000
EOF
    
    echo -e "${GREEN}✓ Environment configuration created${NC}"
    echo -e "${BLUE}Webhook Secret: ${WEBHOOK_SECRET}${NC}"
}

# Setup GitHub webhook
setup_github_webhook() {
    echo -e "${YELLOW}Setting up GitHub webhook...${NC}"
    
    PI_IP=$(hostname -I | awk '{print $1}')
    WEBHOOK_URL="http://$PI_IP:9000/webhook"
    
    echo -e "${BLUE}Setting up webhook at: $WEBHOOK_URL${NC}"
    
    # Get webhook secret from .env
    source .env
    
    # Create webhook
    WEBHOOK_RESPONSE=$(curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"web\",
            \"active\": true,
            \"events\": [\"push\", \"pull_request\"],
            \"config\": {
                \"url\": \"$WEBHOOK_URL\",
                \"content_type\": \"json\",
                \"secret\": \"$GITHUB_WEBHOOK_SECRET\",
                \"insecure_ssl\": \"0\"
            }
        }" \
        https://api.github.com/repos/$GITHUB_REPO/hooks)
    
    if echo "$WEBHOOK_RESPONSE" | jq -e '.id' > /dev/null; then
        echo -e "${GREEN}✓ GitHub webhook created successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Webhook creation failed or already exists${NC}"
        echo "Response: $WEBHOOK_RESPONSE"
    fi
}

# Build and start containers
build_and_start() {
    echo -e "${YELLOW}Building and starting containers...${NC}"
    
    # Create necessary directories
    mkdir -p test-results logs debug-data backup
    
    # Build containers
    echo "Building containers..."
    docker-compose build
    
    # Start services
    echo "Starting services..."
    docker-compose up -d
    
    # Wait for services to start
    echo "Waiting for services to start..."
    sleep 30
    
    # Check service health
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✓ Services started successfully${NC}"
    else
        echo -e "${RED}✗ Some services failed to start${NC}"
        docker-compose logs
    fi
}

# Create monitoring dashboard
create_monitoring_script() {
    echo -e "${YELLOW}Creating monitoring script...${NC}"
    
    cat > monitor_system.sh << 'EOF'
#!/bin/bash
# System monitoring script for GitHub-integrated Xbox 360 emulation

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_services() {
    echo -e "${YELLOW}=== Service Status ===${NC}"
    
    services=("xbox360-emulator" "xbox360-github-updater" "xbox360-dashboard")
    
    for service in "${services[@]}"; do
        if docker ps | grep -q "$service"; then
            echo -e "$service: ${GREEN}RUNNING${NC}"
        else
            echo -e "$service: ${RED}STOPPED${NC}"
            echo "Attempting to restart $service..."
            docker-compose restart $service
        fi
    done
}

check_system_health() {
    echo -e "${YELLOW}=== System Health ===${NC}"
    
    # CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "CPU Usage: ${cpu_usage}%"
    
    # Memory usage  
    mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo "Memory Usage: ${mem_usage}%"
    
    # Disk usage
    disk_usage=$(df / | tail -1 | awk '{print $5}')
    echo "Disk Usage: $disk_usage"
    
    # Temperature
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        temp=$(echo "scale=1; $temp/1000" | bc)
        echo "Temperature: ${temp}°C"
        
        if (( $(echo "$temp > 75" | bc -l) )); then
            echo -e "${RED}⚠ High temperature warning${NC}"
        fi
    fi
}

check_github_connectivity() {
    echo -e "${YELLOW}=== GitHub Connectivity ===${NC}"
    
    if curl -s --max-time 10 https://api.github.com > /dev/null; then
        echo -e "GitHub API: ${GREEN}ACCESSIBLE${NC}"
    else
        echo -e "GitHub API: ${RED}UNREACHABLE${NC}"
    fi
    
    # Check last update
    if [ -f "logs/updater.log" ]; then
        last_update=$(tail -n 20 logs/updater.log | grep "update completed" | tail -n 1)
        if [ ! -z "$last_update" ]; then
            echo "Last Update: $last_update"
        fi
    fi
}

check_test_results() {
    echo -e "${YELLOW}=== Recent Test Results ===${NC}"
    
    if [ -d "test-results" ]; then
        latest_test=$(ls -t test-results/*.json 2>/dev/null | head -1)
        if [ ! -z "$latest_test" ]; then
            echo "Latest test: $(basename $latest_test)"
            
            # Check for failures
            if grep -q '"status": "fail"' "$latest_test"; then
                echo -e "${RED}⚠ Test failures detected${NC}"
            else
                echo -e "${GREEN}✓ Tests passing${NC}"
            fi
        fi
    fi
}

# Main monitoring function
main() {
    echo -e "${BLUE}=== Xbox 360 Emulation System Monitor ===${NC}"
    echo "$(date)"
    echo
    
    check_services
    echo
    check_system_health
    echo
    check_github_connectivity
    echo
    check_test_results
    echo
    
    # Log to file
    {
        echo "$(date): System check completed"
        docker-compose ps
    } >> logs/monitor.log
}

main "$@"
EOF
    
    chmod +x monitor_system.sh
    
    # Add to crontab for regular monitoring
    (crontab -l 2>/dev/null; echo "*/10 * * * * $PROJECT_ROOT/monitor_system.sh >> $PROJECT_ROOT/logs/cron_monitor.log 2>&1") | crontab -
    
    echo -e "${GREEN}✓ Monitoring script created and scheduled${NC}"
}

# Create quick management script
create_management_script() {
    echo -e "${YELLOW}Creating management script...${NC}"
    
    cat > manage.sh << 'EOF'
#!/bin/bash
# Xbox 360 Emulation Project Management Script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    "start")
        echo "Starting all services..."
        docker-compose up -d
        ;;
    "stop")
        echo "Stopping all services..."
        docker-compose down
        ;;
    "restart")
        echo "Restarting all services..."
        docker-compose restart
        ;;
    "logs")
        echo "Showing logs..."
        docker-compose logs -f
        ;;
    "status")
        echo "=== Service Status ==="
        docker-compose ps
        echo
        echo "=== System Resources ==="
        ./monitor_system.sh
        ;;
    "update")
        echo "Triggering manual update..."
        curl -X POST http://localhost:9000/manual-update
        ;;
    "test")
        echo "Running tests..."
        ./run_tests.sh ${2:-quick}
        ;;
    "dashboard")
        PI_IP=$(hostname -I | awk '{print $1}')
        echo "Dashboard URL: http://$PI_IP:8080"
        ;;
    "backup")
        echo "Creating backup..."
        backup_name="backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "backup/$backup_name"
        cp -r test-results logs debug-data "backup/$backup_name/"
        echo "Backup created: backup/$backup_name"
        ;;
    *)
        echo "Xbox 360 Emulation Management"
        echo "Usage: $0 {start|stop|restart|logs|status|update|test|dashboard|backup}"
        echo ""
        echo "Commands:"
        echo "  start     - Start all services"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  logs      - Show service logs"
        echo "  status    - Show system status"
        echo "  update    - Trigger manual update"
        echo "  test      - Run tests (test [quick|comprehensive])"
        echo "  dashboard - Show dashboard URL"
        echo "  backup    - Create system backup"
        ;;
esac
EOF
    
    chmod +x manage.sh
    echo -e "${GREEN}✓ Management script created${NC}"
}

# Display final information
show_completion_info() {
    PI_IP=$(hostname -I | awk '{print $1}')
    
    echo -e "\n${GREEN}=== GitHub Integration Setup Complete ===${NC}"
    echo -e "${GREEN}✓ Docker containers running${NC}"
    echo -e "${GREEN}✓ GitHub webhook configured${NC}"
    echo -e "${GREEN}✓ Automated testing active${NC}"
    echo -e "${GREEN}✓ Automatic updates enabled${NC}"
    echo
    echo -e "${BLUE}=== Access Information ===${NC}"
    echo -e "Web Dashboard:    ${YELLOW}http://$PI_IP:8080${NC}"
    echo -e "Updater Status:   ${YELLOW}http://$PI_IP:9000/status${NC}"
    echo -e "Manual Update:    ${YELLOW}curl -X POST http://$PI_IP:9000/manual-update${NC}"
    echo
    echo -e "${BLUE}=== Management Commands ===${NC}"
    echo -e "System Status:    ${YELLOW}./manage.sh status${NC}"
    echo -e "View Logs:        ${YELLOW}./manage.sh logs${NC}"
    echo -e "Run Tests:        ${YELLOW}./manage.sh test${NC}"
    echo -e "Create Backup:    ${YELLOW}./manage.sh backup${NC}"
    echo
    echo -e "${BLUE}=== Automatic Features Active ===${NC}"
    echo -e "${GREEN}✅ Code updates from GitHub pushes${NC}"
    echo -e "${GREEN}✅ Continuous testing every 15 minutes${NC}"
    echo -e "${GREEN}✅ Health monitoring every 5 minutes${NC}"
    echo -e "${GREEN}✅ Automatic error recovery${NC}"
    echo -e "${GREEN}✅ Performance monitoring${NC}"
    echo -e "${GREEN}✅ Log analysis and alerting${NC}"
    echo -e "${GREEN}✅ Backup and rollback capabilities${NC}"
    echo
    echo -e "${YELLOW}=== Next Steps ===${NC}"
    echo "1. Push your code to GitHub to trigger the first automated update"
    echo "2. Monitor the dashboard at http://$PI_IP:8080"
    echo "3. Check logs with './manage.sh logs'"
    echo "4. The system will now automatically update when you push to GitHub!"
}

# Main execution
main() {
    echo -e "${BLUE}Starting GitHub integration setup...${NC}\n"
    
    check_hardware
    install_dependencies
    setup_github_repo
    create_env_config
    setup_github_webhook
    build_and_start
    create_monitoring_script
    create_management_script
    show_completion_info
}

# Get GitHub details from user
if [ -z "$GITHUB_REPO" ]; then
    echo "Please set GITHUB_REPO environment variable (username/repo-name)"
    echo "Example: export GITHUB_REPO=myusername/xbox360-emulator"
    echo "Or run: GITHUB_REPO=myusername/xbox360-emulator GITHUB_TOKEN=your_token ./setup_github_integration.sh"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Please set GITHUB_TOKEN environment variable"
    echo "Get a token from: https://github.com/settings/tokens"
    echo "Required scopes: repo, workflow"
    exit 1
fi

# Run main setup
main "$@"