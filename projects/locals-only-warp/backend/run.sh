#!/bin/bash

# Google Places API Backend Run Script
# Simple script to start the FastAPI server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PORT=8000
HOST="0.0.0.0"
DEV_MODE=false
BG_MODE=false
USE_VENV=false
SKIP_DB_INIT=false

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help            Show this help message"
    echo "  -p, --port PORT       Server port (default: 8000)"
    echo "  --host HOST           Server host (default: 0.0.0.0)"
    echo "  --dev                 Run in development mode with auto-reload"
    echo "  --bg                  Run server in background"
    echo "  --venv                Use virtual environment"
    echo "  --no-db-init          Skip database initialization"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start server on default port 8000"
    echo "  $0 --port 8080        # Start server on port 8080"
    echo "  $0 --dev              # Start in development mode"
    echo "  $0 --bg               # Run in background"
    echo "  $0 --venv             # Use virtual environment"
}

# Function to kill existing processes on port
kill_port_processes() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        print_warn "Found existing processes on port $port. Killing them..."
        echo $pids | xargs kill -TERM 2>/dev/null
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            echo $remaining_pids | xargs kill -KILL 2>/dev/null
            print_info "Force killed processes on port $port"
        else
            print_info "Gracefully killed processes on port $port"
        fi
    fi
}

# Function to setup virtual environment
setup_venv() {
    if [ "$USE_VENV" = true ]; then
        print_info "Setting up virtual environment..."
        
        # Determine Python command
        PYTHON_CMD="python3"
        if ! command -v python3 &> /dev/null; then
            PYTHON_CMD="python"
        fi
        
        # Create venv if it doesn't exist
        if [ ! -d "venv" ]; then
            print_info "Creating virtual environment..."
            $PYTHON_CMD -m venv venv
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Install dependencies
        if [ -f "requirements.txt" ]; then
            print_info "Installing dependencies..."
            pip install -r requirements.txt
            if [ "$DEV_MODE" = true ] && [ -f "requirements-dev.txt" ]; then
                pip install -r requirements-dev.txt
            fi
        fi
    fi
}

# Function to check environment
check_env() {
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        print_warn ".env file not found. Creating from template..."
        cp .env.example .env
        print_warn "Please edit .env file with your Google Maps API key before running again!"
        exit 1
    fi
    
    if [ -f ".env" ]; then
        source .env
        if [ -z "$GOOGLE_MAPS_API_KEY" ] || [ "$GOOGLE_MAPS_API_KEY" = "your_google_maps_api_key_here" ]; then
            print_error "Google Maps API key not configured in .env file"
            exit 1
        fi
    fi
}

# Function to initialize database
init_db() {
    if [ "$SKIP_DB_INIT" = false ]; then
        print_info "Initializing database..."
        python utils/db.py --init
        if [ $? -ne 0 ]; then
            print_error "Database initialization failed"
            exit 1
        fi
    fi
}

# Function to start server
start_server() {
    print_info "Starting FastAPI server on $HOST:$PORT"
    
    # Build uvicorn command
    cmd="python -m uvicorn src.main:app --host $HOST --port $PORT"
    
    if [ "$DEV_MODE" = true ]; then
        cmd="$cmd --reload"
        print_info "Development mode enabled (auto-reload)"
    fi
    
    if [ "$BG_MODE" = true ]; then
        print_info "Starting server in background..."
        nohup $cmd > logs/server.log 2>&1 &
        echo $! > server.pid
        print_info "Server started in background (PID: $(cat server.pid))"
        print_info "View logs: tail -f logs/server.log"
        print_info "Stop server: kill \$(cat server.pid)"
    else
        print_info "Starting server in foreground (Ctrl+C to stop)"
        echo ""
        print_info "🚀 Server URLs:"
        echo "  • API Docs: http://$HOST:$PORT/docs"
        echo "  • Health:   http://$HOST:$PORT/api/v1/health"
        echo ""
        exec $cmd
    fi
}

# Main function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            --host)
                HOST="$2"
                shift 2
                ;;
            --dev)
                DEV_MODE=true
                shift
                ;;
            --bg)
                BG_MODE=true
                shift
                ;;
            --venv)
                USE_VENV=true
                shift
                ;;
            --no-db-init)
                SKIP_DB_INIT=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Create logs directory
    mkdir -p logs
    mkdir -p data
    
    # Check and kill existing processes on port
    kill_port_processes $PORT
    
    # Setup virtual environment if requested
    setup_venv
    
    # Check environment configuration
    check_env
    
    # Initialize database
    init_db
    
    # Start server
    start_server
}

# Handle script interruption
trap 'echo ""; print_info "Shutting down..."; exit 0' SIGINT SIGTERM

# Run main function
main "$@"
