#!/usr/bin/env python3
"""
Wrapper script to run the E*TRADE MCP server
Loads environment variables from .env file
"""

import os
import sys
from pathlib import Path

# Change to script directory to ensure relative imports work
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Add current directory to Python path
sys.path.insert(0, str(script_dir))

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")
    print("Install with: pip install python-dotenv")

# Verify required environment variables
consumer_key = os.getenv("ETRADE_CONSUMER_KEY")
consumer_secret = os.getenv("ETRADE_CONSUMER_SECRET")

if not consumer_key or not consumer_secret:
    print("Error: ETRADE_CONSUMER_KEY and ETRADE_CONSUMER_SECRET must be set")
    print("Create a .env file with your credentials or set environment variables")
    print("See env.example for template")
    sys.exit(1)

# Import and run the server
if __name__ == "__main__":
    try:
        from etrade_mcp_server import main
        import asyncio
        print(f"Starting E*TRADE MCP Server from {script_dir}", file=sys.stderr)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


