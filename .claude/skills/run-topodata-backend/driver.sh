#!/bin/bash
# Driver script for TopoData Backend API
# This script launches the FastAPI server and runs smoke tests against it

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER_HOST="127.0.0.1"
SERVER_PORT="8000"
BASE_URL="http://${SERVER_HOST}:${SERVER_PORT}"
LOG_FILE="/tmp/topodata_driver.log"
PID_FILE="/tmp/topodata_driver.pid"

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Stopping server..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    log_info "Server stopped"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Start the server
start_server() {
    log_info "Starting FastAPI server..."

    # Set PYTHONIOENCODING to avoid unicode issues on Windows
    export PYTHONIOENCODING=utf-8

    # Start server in background
    uv run uvicorn main:app --host "$SERVER_HOST" --port "$SERVER_PORT" > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$PID_FILE"

    # Wait for server to be ready
    log_info "Waiting for server to start..."
    MAX_WAIT=30
    WAIT_TIME=0

    while [ $WAIT_TIME -lt $MAX_WAIT ]; do
        if curl -s "$BASE_URL/" > /dev/null 2>&1; then
            log_info "Server is ready!"
            return 0
        fi
        sleep 1
        WAIT_TIME=$((WAIT_TIME + 1))
    done

    log_error "Server failed to start within ${MAX_WAIT}s"
    cat "$LOG_FILE"
    return 1
}

# Run smoke tests
run_tests() {
    log_info "Running smoke tests..."

    # Test 1: Root endpoint
    log_info "Test 1: Root endpoint"
    RESPONSE=$(curl -s "$BASE_URL/")
    if echo "$RESPONSE" | grep -q "Bienvenido"; then
        log_info "✓ Root endpoint works"
    else
        log_error "✗ Root endpoint failed"
        return 1
    fi

    # Test 2: Register user
    log_info "Test 2: User registration"
    REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"username": "driver_test_user", "email": "driver_test@example.com", "password": "testpass123"}')

    if echo "$REGISTER_RESPONSE" | grep -q "driver_test_user"; then
        log_info "✓ User registration works"
        USER_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    else
        log_warn "User already exists or registration failed"
    fi

    # Test 3: Login
    log_info "Test 3: User login"
    LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "driver_test_user", "email": "driver_test@example.com", "password": "testpass123"}')

    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        log_info "✓ Login works"
        TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d':' -f2 | tr -d '"')
    else
        log_error "✗ Login failed"
        return 1
    fi

    # Test 4: Access protected endpoint (get projects)
    log_info "Test 4: Protected endpoint - Get projects"
    PROJECTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/projects/" \
        -H "Authorization: Bearer $TOKEN")

    if echo "$PROJECTS_RESPONSE" | grep -q "name"; then
        log_info "✓ Protected endpoint works"
        PROJECT_COUNT=$(echo "$PROJECTS_RESPONSE" | grep -o '"name"' | wc -l)
        log_info "  Found $PROJECT_COUNT projects"
    else
        log_error "✗ Protected endpoint failed"
        return 1
    fi

    # Test 5: Create project
    log_info "Test 5: Create project"
    CREATE_PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/projects/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Driver Test Project",
            "coordinate_system": "EPSG:25830",
            "description": "Test project created by driver script",
            "locale_string": "es-ES",
            "zona_utm": "30N",
            "a_elip": 6378137.0,
            "b_elip": 6356752.314140356,
            "f_elip": 0.003352810681182319,
            "inv_f_elip": 298.257222101
        }')

    if echo "$CREATE_PROJECT_RESPONSE" | grep -q "Driver Test Project"; then
        log_info "✓ Project creation works"
        PROJECT_ID=$(echo "$CREATE_PROJECT_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    else
        log_warn "Project creation failed or already exists"
    fi

    # Test 6: Get user info
    log_info "Test 6: Get current user info"
    USER_INFO=$(curl -s -X GET "$BASE_URL/api/v1/auth/me" \
        -H "Authorization: Bearer $TOKEN")

    if echo "$USER_INFO" | grep -q "driver_test_user"; then
        log_info "✓ Get user info works"
    else
        log_error "✗ Get user info failed"
        return 1
    fi

    log_info "All tests passed! ✓"
    return 0
}

# Main execution
main() {
    echo "=========================================="
    echo "  TopoData Backend API Driver"
    echo "=========================================="
    echo ""

    start_server
    run_tests

    echo ""
    log_info "Driver completed successfully"
    echo ""
    echo "API is running at: $BASE_URL"
    echo "Swagger UI: $BASE_URL/docs"
    echo "Server logs: $LOG_FILE"
    echo ""
    echo "Press Ctrl+C to stop the server"

    # Keep server running until interrupted
    wait
}

# Run main function
main "$@"
