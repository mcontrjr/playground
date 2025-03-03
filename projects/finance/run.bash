#!/bin/bash

# Initialize variables
COMPOSE_FILE="docker-compose.yml"
SHOW_HELP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            SHOW_HELP=true
            shift
            ;;
        --dev)
            COMPOSE_FILE="docker-compose.dev.yml"
            shift
            ;;
        --db)
            COMPOSE_FILE="docker-compose.db.yml"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Show help message if requested
if [ "$SHOW_HELP" = true ]; then
    cat << 'EOF'
Usage: $0 [OPTIONS]

Options:
  -h, --help    Show this help message
  --dev         Use docker-compose.dev.yml configuration
  --db          Use docker-compose.db.yml configuration

Description:
  This script manages the Finance application containers.
  It handles container cleanup, directory permissions,
  and PostgreSQL initialization.
EOF
    exit 0
fi

# Stop all running containers
echo "Stopping running containers..."
docker compose down

# Remove any existing pg_log directory
echo "Removing existing pg_log directory..."
sudo rm -rf ./logs/pg_log

# Create necessary directories
echo "Creating new pg_log directory..."
mkdir -p ./logs/pg_log

# Set correct permissions for postgres user (UID 999 is typically postgres in the container)
echo "Setting correct permissions..."
sudo chown -R $(whoami):$(whoami) ./logs/pg_log
sudo chmod -R 750 ./logs/pg_log

# Start the containers
echo "Starting containers with $COMPOSE_FILE..."
docker compose -f $COMPOSE_FILE up -d

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 10
