#!/bin/bash

# AI Content Aggregator Startup Script
# Usage: ./start.sh [-d] [--help]
# -d: Development mode (starts both backend and frontend with live logs)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Log files
BACKEND_LOG_FILE="backend.log"
FRONTEND_LOG_FILE="frontend.log"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_backend() {
    echo -e "${CYAN}[BACKEND]${NC} $1"
}

print_frontend() {
    echo -e "${MAGENTA}[FRONTEND]${NC} $1"
}

# Function to show help
show_help() {
    echo "AI Content Aggregator Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --dev     Start in development mode with live logs"
    echo "  -c, --clean   Cleanup existing processes and exit (no restart)"
    echo "  -f, --force   Force cleanup and restart (kills all existing processes)"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -d         Start both backend and frontend in development mode"
    echo "  $0 --dev      Same as above"
    echo "  $0 -c         Just cleanup existing processes"
    echo ""
}

# Function to cleanup existing processes
cleanup_existing() {
    print_status "Cleaning up existing processes..."
    
    # Kill any existing start.sh processes first
    if pgrep -f 'start.sh' >/dev/null 2>&1; then
        print_status "Terminating existing start.sh processes..."
        pkill -TERM -f 'start.sh' 2>/dev/null || true
        sleep 2
        # Force kill if still running
        pkill -KILL -f 'start.sh' 2>/dev/null || true
    fi
    
    # Try graceful shutdown first, then force kill
    print_status "Stopping development servers..."
    
    # Kill Node.js development processes
    pkill -TERM -f "npm run dev" 2>/dev/null || true
    pkill -TERM -f "next dev" 2>/dev/null || true
    pkill -TERM -f "node.*next" 2>/dev/null || true
    
    # Kill Python/FastAPI processes
    pkill -TERM -f "uvicorn.*main:app" 2>/dev/null || true
    pkill -TERM -f "python.*main.py" 2>/dev/null || true
    
    # Wait for graceful shutdown
    sleep 3
    
    # Force kill processes on specific ports
    if lsof -ti:8000 >/dev/null 2>&1; then
        print_status "Force killing processes on port 8000 (backend)..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    fi
    
    if lsof -ti:3000 >/dev/null 2>&1; then
        print_status "Force killing processes on port 3000 (frontend)..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    fi
    
    # Final cleanup of any remaining processes
    pkill -KILL -f "npm run dev" 2>/dev/null || true
    pkill -KILL -f "next dev" 2>/dev/null || true
    pkill -KILL -f "uvicorn.*main:app" 2>/dev/null || true
    pkill -KILL -f "python.*main.py" 2>/dev/null || true
    
    # Wait a moment for cleanup to complete
    sleep 1
    
    print_success "Cleanup completed"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Please install uv first."
        print_status "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install Node.js and npm first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to start backend
start_backend() {
    print_status "Starting backend server..."
    cd backend
    
    # Install/sync dependencies if needed
    if [ ! -d ".venv" ]; then
        print_status "Setting up Python virtual environment..."
        uv sync
    fi
    
    # Clean previous log
    > "$BACKEND_LOG_FILE"
    
    # Start backend server and log output
    print_status "Starting FastAPI server on port 8000..."
    uv run python main.py > "$BACKEND_LOG_FILE" 2>&1 &
    BACKEND_PID=$!
    
    cd ..
    print_success "Backend started (PID: $BACKEND_PID)"
    
    # Wait a moment for backend to start
    sleep 2
    
    # Check if backend started successfully
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend failed to start! Check logs:"
        tail -20 "backend/$BACKEND_LOG_FILE" | while read line; do
            print_backend "$line"
        done
        exit 1
    fi
    
    print_success "Backend is running at http://localhost:8000"
}

# Function to start frontend
start_frontend() {
    print_status "Starting frontend server..."
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing npm dependencies..."
        npm install
    fi
    
    # Clean previous log
    > "$FRONTEND_LOG_FILE"
    
    # Start frontend server and log output
    print_status "Starting Next.js dev server on port 3000..."
    npm run dev > "$FRONTEND_LOG_FILE" 2>&1 &
    FRONTEND_PID=$!
    
    cd ..
    print_success "Frontend started (PID: $FRONTEND_PID)"
    
    # Wait a moment for frontend to start
    sleep 3
    
    # Check if frontend started successfully
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend failed to start! Check logs:"
        tail -20 "frontend/$FRONTEND_LOG_FILE" | while read line; do
            print_frontend "$line"
        done
        exit 1
    fi
    
    print_success "Frontend is running at http://localhost:3000"
}

# Function to monitor logs
monitor_logs() {
    print_status "Starting log monitoring..."
    print_status "Backend logs: ${CYAN}CYAN${NC}, Frontend logs: ${MAGENTA}MAGENTA${NC}"
    print_status "Press Ctrl+C to stop all servers"
    print_status "====================================="
    
    # Monitor both log files in parallel
    (
        tail -f "backend/$BACKEND_LOG_FILE" 2>/dev/null | while IFS= read -r line; do
            print_backend "$line"
        done
    ) &
    BACKEND_TAIL_PID=$!
    
    (
        tail -f "frontend/$FRONTEND_LOG_FILE" 2>/dev/null | while IFS= read -r line; do
            print_frontend "$line"
        done
    ) &
    FRONTEND_TAIL_PID=$!
    
    # Wait for any process to exit
    wait
}

# Function to handle cleanup
cleanup() {
    print_status ""
    print_status "Shutting down servers..."
    
    # Kill log monitoring processes
    if [ ! -z "$BACKEND_TAIL_PID" ]; then
        kill $BACKEND_TAIL_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_TAIL_PID" ]; then
        kill $FRONTEND_TAIL_PID 2>/dev/null || true
    fi
    
    # Kill server processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend server stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend server stopped"
    fi
    
    print_success "All processes stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Parse command line arguments
DEV_MODE=false
FORCE_CLEANUP=false
CLEAN_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dev)
            DEV_MODE=true
            shift
            ;;
        -c|--clean)
            CLEAN_ONLY=true
            shift
            ;;
        -f|--force)
            FORCE_CLEANUP=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Automatically cleanup existing processes
cleanup_existing

# Handle clean-only mode
if [ "$CLEAN_ONLY" = true ]; then
    print_success "Cleanup completed. Exiting."
    exit 0
fi

# Main execution
print_status "AI Content Aggregator Startup Script"
print_status "====================================="

if [ "$DEV_MODE" = true ]; then
    print_status "Starting in development mode with live logs..."
    
    check_prerequisites
    
    # Start both backend and frontend
    start_backend
    start_frontend
    
    print_success "Both servers are running!"
    print_status "🔗 Backend: http://localhost:8000"
    print_status "🔗 Frontend: http://localhost:3000"
    print_status "📚 API Docs: http://localhost:8000/docs"
    print_status "📋 Health Check: http://localhost:8000/health"
    print_status ""
    
    # Start log monitoring
    monitor_logs
else
    print_warning "No mode specified. Use -d for development mode or --help for usage information."
    show_help
    exit 1
fi