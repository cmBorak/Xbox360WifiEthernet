#!/bin/bash
# Comprehensive testing script for Xbox 360 Emulation Project
# Provides different testing modes and comprehensive reporting

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"
COVERAGE_DIR="$PROJECT_ROOT/htmlcov"

# Ensure test results directory exists
mkdir -p "$TEST_RESULTS_DIR"

echo -e "${BLUE}=== Xbox 360 Emulation Project Test Suite ===${NC}\n"

# Function to setup test environment
setup_test_env() {
    echo -e "${YELLOW}Setting up test environment...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        python3 -m venv "$VENV_PATH"
        echo -e "${GREEN}Created virtual environment${NC}"
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Install test dependencies
    pip install -q -r requirements-test.txt
    echo -e "${GREEN}Test dependencies installed${NC}\n"
}

# Function to run unit tests
run_unit_tests() {
    echo -e "${BLUE}Running Unit Tests...${NC}"
    pytest tests/ -m "unit or not integration" \
        --html="$TEST_RESULTS_DIR/unit-test-report.html" \
        --self-contained-html \
        --json-report --json-report-file="$TEST_RESULTS_DIR/unit-test-results.json" \
        -v
    echo -e "${GREEN}Unit tests completed${NC}\n"
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${BLUE}Running Integration Tests...${NC}"
    pytest tests/ -m "integration" \
        --html="$TEST_RESULTS_DIR/integration-test-report.html" \
        --self-contained-html \
        --json-report --json-report-file="$TEST_RESULTS_DIR/integration-test-results.json" \
        -v
    echo -e "${GREEN}Integration tests completed${NC}\n"
}

# Function to run hardware tests (requires Pi 4)
run_hardware_tests() {
    echo -e "${BLUE}Running Hardware Tests...${NC}"
    echo -e "${YELLOW}Note: Hardware tests require Raspberry Pi 4${NC}"
    
    if [ -f "/proc/cpuinfo" ] && grep -q "Raspberry Pi 4" /proc/cpuinfo; then
        pytest tests/ -m "hardware" \
            --html="$TEST_RESULTS_DIR/hardware-test-report.html" \
            --self-contained-html \
            --json-report --json-report-file="$TEST_RESULTS_DIR/hardware-test-results.json" \
            -v
        echo -e "${GREEN}Hardware tests completed${NC}\n"
    else
        echo -e "${YELLOW}Skipping hardware tests (not on Raspberry Pi 4)${NC}\n"
    fi
}

# Function to run performance tests
run_performance_tests() {
    echo -e "${BLUE}Running Performance Tests...${NC}"
    pytest tests/ -m "slow" \
        --benchmark-only \
        --benchmark-html="$TEST_RESULTS_DIR/benchmark-report.html" \
        --benchmark-json="$TEST_RESULTS_DIR/benchmark-results.json" \
        -v
    echo -e "${GREEN}Performance tests completed${NC}\n"
}

# Function to generate coverage report
generate_coverage() {
    echo -e "${BLUE}Generating Coverage Report...${NC}"
    
    # Run tests with coverage
    pytest tests/ \
        --cov=src \
        --cov-report=html:"$COVERAGE_DIR" \
        --cov-report=term-missing \
        --cov-report=json:"$TEST_RESULTS_DIR/coverage.json" \
        --cov-fail-under=70 \
        --html="$TEST_RESULTS_DIR/full-test-report.html" \
        --self-contained-html \
        -q
    
    echo -e "${GREEN}Coverage report generated at $COVERAGE_DIR/index.html${NC}\n"
}

# Function to run code quality checks
run_quality_checks() {
    echo -e "${BLUE}Running Code Quality Checks...${NC}"
    
    # Format checking with black
    echo "Checking code formatting..."
    black --check src/ tests/ || true
    
    # Import sorting with isort
    echo "Checking import sorting..."
    isort --check-only src/ tests/ || true
    
    # Linting with flake8
    echo "Running linter..."
    flake8 src/ tests/ --output-file="$TEST_RESULTS_DIR/flake8-report.txt" || true
    
    # Type checking with mypy
    echo "Running type checker..."
    mypy src/ > "$TEST_RESULTS_DIR/mypy-report.txt" 2>&1 || true
    
    echo -e "${GREEN}Code quality checks completed${NC}\n"
}

# Function to run critical path tests only
run_critical_tests() {
    echo -e "${BLUE}Running Critical Path Tests...${NC}"
    pytest tests/ -m "critical" \
        --html="$TEST_RESULTS_DIR/critical-test-report.html" \
        --self-contained-html \
        --json-report --json-report-file="$TEST_RESULTS_DIR/critical-test-results.json" \
        -v --tb=short
    echo -e "${GREEN}Critical tests completed${NC}\n"
}

# Function to run smoke tests (quick validation)
run_smoke_tests() {
    echo -e "${BLUE}Running Smoke Tests...${NC}"
    pytest tests/ -k "test_initialization or test_basic" \
        --html="$TEST_RESULTS_DIR/smoke-test-report.html" \
        --self-contained-html \
        -v --tb=line
    echo -e "${GREEN}Smoke tests completed${NC}\n"
}

# Function to display results summary
show_results() {
    echo -e "${BLUE}=== Test Results Summary ===${NC}"
    
    if [ -f "$TEST_RESULTS_DIR/coverage.json" ]; then
        coverage=$(python3 -c "import json; data=json.load(open('$TEST_RESULTS_DIR/coverage.json')); print(f'{data[\"totals\"][\"percent_covered\"]:.1f}%')")
        echo -e "Code Coverage: ${GREEN}$coverage${NC}"
    fi
    
    echo -e "\nTest Reports Available:"
    echo -e "  • Full Report: ${BLUE}$TEST_RESULTS_DIR/full-test-report.html${NC}"
    echo -e "  • Coverage Report: ${BLUE}$COVERAGE_DIR/index.html${NC}"
    echo -e "  • Benchmark Report: ${BLUE}$TEST_RESULTS_DIR/benchmark-report.html${NC}"
    
    echo -e "\nQuality Reports:"
    echo -e "  • Flake8: ${BLUE}$TEST_RESULTS_DIR/flake8-report.txt${NC}"
    echo -e "  • MyPy: ${BLUE}$TEST_RESULTS_DIR/mypy-report.txt${NC}"
}

# Main execution logic
main() {
    setup_test_env
    
    case "${1:-all}" in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "hardware")
            run_hardware_tests
            ;;
        "performance")
            run_performance_tests
            ;;
        "coverage")
            generate_coverage
            ;;
        "quality")
            run_quality_checks
            ;;
        "critical")
            run_critical_tests
            ;;
        "smoke")
            run_smoke_tests
            ;;
        "all")
            run_unit_tests
            run_integration_tests
            run_hardware_tests
            run_performance_tests
            generate_coverage
            run_quality_checks
            ;;
        "quick")
            run_smoke_tests
            run_critical_tests
            ;;
        *)
            echo -e "${RED}Usage: $0 [unit|integration|hardware|performance|coverage|quality|critical|smoke|all|quick]${NC}"
            echo -e "\nTest Types:"
            echo -e "  unit        - Unit tests only"
            echo -e "  integration - Integration tests only"
            echo -e "  hardware    - Hardware-dependent tests (Pi 4 required)"
            echo -e "  performance - Performance and benchmark tests"
            echo -e "  coverage    - Generate coverage report"
            echo -e "  quality     - Code quality checks"
            echo -e "  critical    - Critical path tests only"
            echo -e "  smoke       - Quick smoke tests"
            echo -e "  all         - All tests (default)"
            echo -e "  quick       - Smoke + critical tests"
            exit 1
            ;;
    esac
    
    show_results
}

# Execute main function with all arguments
main "$@"