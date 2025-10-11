#!/bin/bash
set -e
echo "Building Docker images..."
docker-compose build
echo "Running tests for Python 3.8, 3.10, and 3.12..."
docker-compose up
