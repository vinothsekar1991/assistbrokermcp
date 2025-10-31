# Running the E*TRADE MCP Server

## Prerequisites

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp env.example .env
   # Edit .env and add your E*TRADE credentials
   ```

## Method 1: Running Directly (Testing)

You can run the server directly for testing, but note that MCP servers communicate via stdio, so direct execution will wait for input:

```bash
python etrade_mcp_server.py
```

**Note**: The server communicates via stdio (standard input/output), so when run directly, it will wait for MCP protocol messages. This is mainly useful for debugging.

## Method 2: Running with MCP Client (Recommended)

### Claude Desktop

1. **Find Claude Desktop config file**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Edit the config file** and add your MCP servers:

```json
{
  "mcpServers": {
    "etrade": {
      "command": "python3",
      "args": [
        "/Users/Vinoth/assistbrokermcp/run_server.py"
      ]
    },
    "Playwright": {
      "command": "npx @playwright/mcp@latest",
      "env": {
        "PLAYWRIGHT_HEADLESS": "true"
      },
      "args": []
    }
  }
}
```

**Note**: The Playwright MCP server is configured to run in headless mode (no visible browser window). This is required for automated OAuth flow. The `PLAYWRIGHT_HEADLESS` environment variable ensures the browser runs without a GUI.

**Important**: Replace `/Users/Vinoth/assistbrokermcp/` with your actual project path.

3. **Restart Claude Desktop** for changes to take effect.

### Using with Python Virtual Environment

If you're using a virtual environment:

```json
{
  "mcpServers": {
    "etrade": {
      "command": "/path/to/venv/bin/python",
      "args": [
        "/Users/Vinoth/assistbroker/etrade_mcp_server.py"
      ],
      "env": {
        "ETRADE_CONSUMER_KEY": "your_consumer_key",
        "ETRADE_CONSUMER_SECRET": "your_consumer_secret",
        "ETRADE_SANDBOX": "true"
      }
    }
  }
}
```

### Alternative: Using Wrapper Scripts (Recommended)

The project includes wrapper scripts that automatically load `.env` file:

**Option 1: Python wrapper** (cross-platform):
```json
{
  "mcpServers": {
    "etrade": {
      "command": "python3",
      "args": [
        "/Users/Vinoth/assistbroker/run_server.py"
      ]
    }
  }
}
```

**Option 2: Shell wrapper** (Unix/macOS):
```json
{
  "mcpServers": {
    "etrade": {
      "command": "/Users/Vinoth/assistbroker/run_server.sh",
      "env": {}
    }
  }
}
```

**Replace `/Users/Vinoth/assistbroker/` with your actual project path.**

The wrapper scripts automatically:
- Load environment variables from `.env` file
- Change to the correct directory
- Provide better error messages

## Method 3: Using MCP Inspector (Development/Debugging)

For development and debugging, you can use the MCP Inspector:

1. **Install MCP Inspector**:
   ```bash
   npm install -g @modelcontextprotocol/inspector
   ```

2. **Run with inspector**:
   ```bash
   mcp-inspector python etrade_mcp_server.py
   ```

This provides a web interface to test your MCP server.

## Testing the Server

### 1. Check if it starts without errors:
```bash
python -c "from etrade_mcp_server import app; print('Server imports OK')"
```

### 2. Test OAuth initialization:
Once connected to an MCP client, test the `initialize_oauth` tool first.

### 3. Verify tools are available:
The MCP client should list all 10 tools when the server is connected.

## Troubleshooting

### "Module not found" errors
```bash
# Make sure dependencies are installed
pip install -r requirements.txt

# If using virtual environment, activate it first
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

### "ETRADE_CONSUMER_KEY not found" error
- Make sure `.env` file exists and has your credentials
- Or set environment variables in the MCP client config

### Server exits immediately
- This is normal when run directly - MCP servers wait for stdio input
- Connect it to an MCP client instead

### Permission denied (for shell scripts)
```bash
chmod +x run_server.sh
```

## Verifying Installation

**Quick verification**:
You can verify the installation by checking:
- Python version (should be 3.8+)
- Required packages are installed (`pip list`)
- Configuration files
- Module imports

**Manual verification**:

1. **Check Python version** (needs 3.8+):
   ```bash
   python --version
   ```

2. **Verify packages**:
   ```bash
   python -c "import mcp; import requests; import requests_oauthlib; import dotenv; print('All packages OK')"
   ```

3. **Test imports**:
   ```bash
   python -c "from etrade_client import ETradeClient; from etrade_mcp_server import app; print('Imports successful')"
   ```

## Next Steps

After the server is running:
1. Initialize OAuth: Use `initialize_oauth` tool
2. Complete OAuth: Visit the authorization URL and use `complete_oauth`
3. Start trading: Use other tools to manage your account

