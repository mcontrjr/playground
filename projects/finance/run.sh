#!/bin/bash
mkdir -p ./logs/pg_log

sudo chown -R $(whoami):$(whoami) ./logs/pg_log
sudo chmod -R 755 ./logs/pg_log

docker compose -f docker-compose.yml up -d
