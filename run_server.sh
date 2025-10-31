#!/bin/bash
# Wrapper script to run the E*TRADE MCP server
# Loads environment variables from .env file

cd "$(dirname "$0")"

# Load .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Run the Python server
python3 run_server.py


