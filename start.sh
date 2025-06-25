#!/bin/bash

# AI Content Aggregator Startup Script
# Usage: ./start.sh [-d] [--help]
# -d: Development mode (starts both backend and frontend)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to show help
show_help() {
    echo "AI Content Aggregator Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --dev     Start in development mode (both backend and frontend)"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -d         Start both backend and frontend in development mode"
    echo "  $0 --dev      Same as above"
    echo ""
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
    
    # Start backend server in background
    print_status "Starting FastAPI server on port 8000..."
    uv run python main.py &
    BACKEND_PID=$!
    
    cd ..
    print_success "Backend started (PID: $BACKEND_PID)"
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
    
    # Start frontend server in background
    print_status "Starting Vite dev server on port 3000..."
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
    print_success "Frontend started (PID: $FRONTEND_PID)"
}

# Function to handle cleanup
cleanup() {
    print_status "Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend server stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend server stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Parse command line arguments
DEV_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dev)
            DEV_MODE=true
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

# Main execution
print_status "AI Content Aggregator Startup Script"
print_status "====================================="

if [ "$DEV_MODE" = true ]; then
    print_status "Starting in development mode..."
    
    check_prerequisites
    
    # Start both backend and frontend
    start_backend
    sleep 2  # Give backend time to start
    start_frontend
    
    print_success "Both servers are starting up!"
    print_status "Backend: http://localhost:8000"
    print_status "Frontend: http://localhost:3000"
    print_status "API Docs: http://localhost:8000/docs"
    print_status ""
    print_warning "Press Ctrl+C to stop both servers"
    
    # Wait for processes
    wait
else
    print_warning "No mode specified. Use -d for development mode or --help for usage information."
    show_help
    exit 1
fi