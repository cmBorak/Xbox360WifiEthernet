# Multi-stage Dockerfile for Xbox 360 Emulation on Raspberry Pi 4
# Optimized for automated testing and debugging

# Build stage
FROM python:3.11-slim-bullseye as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libusb-1.0-0-dev \
    libudev-dev \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements-test.txt requirements.txt* ./
RUN pip install --upgrade pip && \
    pip install -r requirements-test.txt && \
    (pip install -r requirements.txt || true)

# Runtime stage
FROM python:3.11-slim-bullseye

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    udev \
    kmod \
    iproute2 \
    bridge-utils \
    iptables \
    dhcpcd5 \
    systemd \
    procps \
    net-tools \
    curl \
    git \
    sudo \
    cron \
    logrotate \
    bc \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    usermod -aG sudo appuser && \
    echo 'appuser ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Create necessary directories
RUN mkdir -p /app/test-results /app/logs /app/debug-data && \
    chown -R appuser:appuser /app

# Switch to app user
USER appuser
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Make scripts executable
RUN chmod +x *.sh *.py || true

# Create entrypoint script
RUN cat > entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /app/logs/container.log
}

log "Starting Xbox 360 Emulation Container"

# Check if running on Raspberry Pi 4 (if not in container)
if [ -f "/proc/cpuinfo" ]; then
    if grep -q "Raspberry Pi 4" /proc/cpuinfo; then
        log "✓ Detected Raspberry Pi 4 hardware"
    else
        log "⚠ Not running on Raspberry Pi 4 - some features may not work"
    fi
fi

# Load kernel modules if possible
log "Loading kernel modules..."
sudo modprobe libcomposite || log "Could not load libcomposite module"
sudo modprobe dwc2 || log "Could not load dwc2 module"

# Setup configfs if available
if [ -d "/sys/kernel/config" ]; then
    sudo chmod -R 755 /sys/kernel/config/ || true
    log "✓ Configfs permissions set"
else
    log "⚠ Configfs not available"
fi

# Start the automated testing daemon in background if requested
if [ "$START_TESTING_DAEMON" = "true" ]; then
    log "Starting automated testing daemon"
    python /app/automated_testing_daemon.py --config /app/test_daemon_config.json &
    DAEMON_PID=$!
    log "Testing daemon started with PID $DAEMON_PID"
fi

# Start the main application
log "Starting Xbox 360 emulation application"
exec "$@"
EOF

RUN chmod +x entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from xbox360_emulator import Xbox360Emulator; e = Xbox360Emulator(); print('healthy' if e else 'unhealthy')" || exit 1

# Environment variables
ENV START_TESTING_DAEMON=true
ENV PYTHONPATH=/app/src
ENV LOG_LEVEL=INFO

# Volumes for persistence
VOLUME ["/app/test-results", "/app/logs", "/app/debug-data"]

# Ports
EXPOSE 8080

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "/app/automated_testing_daemon.py"]