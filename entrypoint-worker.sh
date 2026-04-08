#!/bin/bash
set -e

# Ensure storage directories exist (already owned by appuser in image)
echo "Setting up storage directories..."
mkdir -p /app/storage/downloads /app/storage/temp

echo "Starting worker..."
exec python -m worker.main
