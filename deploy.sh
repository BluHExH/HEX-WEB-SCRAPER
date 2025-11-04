#!/bin/bash

# Deployment script for HEX Web Scraper

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "This script should not be run as root"
    exit 1
fi

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        exit 1
    fi
    
    log_info "All dependencies are installed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    docker-compose build
    log_info "Docker images built successfully"
}

# Start services
start_services() {
    log_info "Starting services..."
    docker-compose up -d
    log_info "Services started successfully"
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    docker-compose down
    log_info "Services stopped successfully"
}

# Show service status
show_status() {
    log_info "Service status:"
    docker-compose ps
}

# Show logs
show_logs() {
    log_info "Showing logs..."
    docker-compose logs -f
}

# Main deployment function
deploy() {
    log_info "Starting deployment..."
    
    check_dependencies
    build_images
    start_services
    
    log_info "Deployment completed successfully!"
    show_status
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|status|logs}"
        exit 1
        ;;
esac