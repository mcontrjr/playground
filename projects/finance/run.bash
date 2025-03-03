#!/bin/bash

# Stop all running containers
echo "Stopping running containers..."
docker compose down -v

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
echo "Starting containers..."
docker compose up -d

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Check container logs
echo "Checking container logs..."
docker logs finance_postgres

# Set correct permissions for postgres user (UID 999 is typically postgres in the container)
# echo "Setting correct permissions..."
# sudo chown -R 999:999 ./logs/pg_log
# sudo chmod -R 750 ./logs/pg_log
# sudo chown -R $(whoami):$(whoami) ./logs/pg_log