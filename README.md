# E*TRADE MCP Tool

A Model Context Protocol (MCP) server that provides tools for interacting with the E*TRADE API to manage accounts, get market data, and place trades.

## Features

- **Account Management**: Get account list, balances, and positions
- **Market Data**: Get real-time quotes for stocks
- **Trade Execution**: Place, view, and cancel orders
- **OAuth 1.0a Authentication**: Secure API authentication flow with automatic token validation
- **Sandbox Support**: Test in sandbox environment before going live
- **Automatic Token Management**: Validates saved tokens on first use, re-authenticates if expired
- **Session Token Caching**: Validates tokens once per session for optimal performance

## Prerequisites

1. Python 3.8 or higher
2. An E*TRADE account
3. API credentials (Consumer Key and Consumer Secret)

## Setup

### 1. Get E*TRADE API Credentials

1. Log in to your E*TRADE account
2. Visit the [API Key Request Page](https://us.etrade.com/etx/ris/apikey)
3. Request a Sandbox key for testing (recommended) or a Production key
4. Copy your Consumer Key and Consumer Secret

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The MCP package may need to be installed from a specific source depending on your MCP client. If you encounter import errors, check the [Model Context Protocol documentation](https://modelcontextprotocol.io) for the correct installation method.

### 3. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   ETRADE_CONSUMER_KEY=your_consumer_key_here
   ETRADE_CONSUMER_SECRET=your_consumer_secret_here
   ETRADE_SANDBOX=true
   ```

### 4. Initialize OAuth Authentication

Before using the API, you need to authenticate:

1. Run the MCP server
2. Use the `initialize_oauth` tool to get an authorization URL
3. Visit the authorization URL in your browser
4. Authorize the application and copy the verification code
5. Use the `complete_oauth` tool with the verification code

The access tokens will be saved to `.etrade_tokens.json` for future use.

**Note**: If tokens are already saved in `.etrade_tokens.json`, they will be automatically validated on first use. If tokens are invalid or expired, you'll be prompted to re-authenticate.

**For Automated OAuth** (optional): If you want to use the `automate_oauth` tool, you'll need to configure Playwright MCP server with headless browser mode. See [RUNNING.md](RUNNING.md) for Playwright MCP configuration details.

## Usage

### Starting the MCP Server

The MCP server communicates via stdio and must be configured with an MCP client. See [RUNNING.md](RUNNING.md) for detailed instructions.

**Quick start**:
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with your E*TRADE credentials
3. Add server to your MCP client configuration (e.g., Claude Desktop)
4. Restart your MCP client

**For testing/debugging**, you can also use:
- Direct execution: `python etrade_mcp_server.py` (waits for stdio input)
- MCP Inspector: `mcp-inspector python etrade_mcp_server.py`

### Available Tools

#### Authentication
- **initialize_oauth**: Get authorization URL to start OAuth flow
- **complete_oauth**: Complete OAuth flow with verification code
- **get_login_credentials**: Get E*TRADE login credentials from environment variables (for automated OAuth)
- **automate_oauth**: Automated OAuth flow using Playwright MCP (requires Playwright MCP server)

#### Generic API Functions
- **etrade_get**: Make GET requests to any E*TRADE API endpoint
  - Supports all GET endpoints (accounts, quotes, orders, positions, transactions, etc.)
  - Pass endpoint path and optional query parameters
- **etrade_post**: Make POST, PUT, or DELETE requests to any E*TRADE API endpoint
  - Supports all POST/PUT/DELETE endpoints (placing orders, canceling orders, etc.)
  - Pass endpoint path, HTTP method, and request body data

See the Example Workflow section below for usage examples of E*TRADE API endpoints.

## Example Workflow

1. **Initialize OAuth**:
   ```json
   {
     "tool": "initialize_oauth",
     "arguments": {}
   }
   ```
   Result: Returns authorization_url

2. **Authorize**:
   - Visit the authorization_url
   - Grant permissions
   - Copy the verification code

3. **Complete OAuth**:
   ```json
   {
     "tool": "complete_oauth",
     "arguments": {"verificationCode": "your_code"}
   }
   ```

4. **Get Account List**:
   ```json
   {
     "tool": "etrade_get",
     "arguments": {
       "endpoint": "/v1/accounts/list"
     }
   }
   ```

5. **Get Stock Quote**:
   ```json
   {
     "tool": "etrade_get",
     "arguments": {
       "endpoint": "/v1/market/quote",
       "params": {"symbol": "AAPL", "detailFlag": "ALL"}
     }
   }
   ```

6. **Place a Market Order**:
   ```json
   {
     "tool": "etrade_post",
     "arguments": {
       "method": "POST",
       "endpoint": "/v1/accounts/{accountId}/orders",
       "data": {
         "orderType": "EQ",
         "Order": [{
           "priceType": "MARKET",
           "orderTerm": "GOOD_FOR_DAY",
           "Instrument": [{
             "Product": {"securityType": "EQ", "symbol": "AAPL"},
             "orderAction": "BUY",
             "quantityType": "QUANTITY",
             "quantity": 10
           }]
         }]
       }
     }
   }
   ```

7. **Check Orders**:
   ```json
   {
     "tool": "etrade_get",
     "arguments": {
       "endpoint": "/v1/accounts/{accountId}/orders",
       "params": {"status": "OPEN"}
     }
   }
   ```

See the Example Workflow and API Endpoints sections below for more comprehensive examples.

## API Endpoints

This MCP server provides generic functions (`etrade_get` and `etrade_post`) that support **all E*TRADE API endpoints**. You can access:

- Account information and balances
- Positions and holdings
- Market data and quotes
- Option chains
- Order placement and management
- Transaction history
- Alerts
- And any other E*TRADE API endpoint

### Endpoints Reference File

A comprehensive reference file (`etrade_endpoints.json`) contains all supported E*TRADE API endpoints with:
- Complete endpoint paths and HTTP methods
- Required and optional parameters
- Request/response structures
- Usage examples
- Order types, actions, and price types reference

**Agents should refer to `etrade_endpoints.json` when making API requests** to ensure correct endpoint usage, parameters, and request formats. The JSON file can be read directly and contains all necessary information.

Refer to the Example Workflow section for detailed examples of:
- Order types (MARKET, LIMIT, STOP, STOP_LIMIT)
- Order actions (BUY, SELL, BUY_TO_COVER, SELL_SHORT)
- All supported endpoints
- Request/response formats

## Important Notes

⚠️ **Sandbox vs Production**
- Always test in sandbox (`ETRADE_SANDBOX=true`) first
- Sandbox allows testing without real money
- Switch to production only after thorough testing

⚠️ **Security**
- Never commit `.env` or `.etrade_tokens.json` to version control
- Keep your Consumer Secret secure
- Tokens are stored locally in `.etrade_tokens.json`

⚠️ **API Limits**
- Be aware of E*TRADE API rate limits
- Some endpoints may have usage restrictions

⚠️ **Legal and Compliance**
- Review E*TRADE's API Developer License Agreement
- Understand the terms of use before deploying to production
- The E*TRADE Customer Protection Guarantee does not apply to API orders

## Troubleshooting

### "Not authenticated" Error
- Make sure you've completed the OAuth flow (`initialize_oauth` → `complete_oauth`)
- Check that `.etrade_tokens.json` exists and contains valid tokens
- If tokens exist but are invalid, they will be automatically cleared and you'll need to re-authenticate

### "Access tokens are invalid or expired" Error
- Tokens from `.etrade_tokens.json` were validated but found to be invalid
- The tokens have been automatically cleared
- Run `initialize_oauth` → `complete_oauth` to get new tokens

### "Failed to get request token" Error
- Verify your Consumer Key and Consumer Secret are correct
- Check that you're using the correct environment (sandbox vs production)

### API Request Failures
- Ensure your account has API access enabled
- Check that you've signed the required API agreements
- Verify the account has sufficient permissions for the requested operation

## Resources

- [E*TRADE Developer Platform](https://developer.etrade.com)
- [E*TRADE Getting Started Guide](http://developer.etrade.com/getting-started/developer-guides)
- [API Key Request](https://us.etrade.com/etx/ris/apikey)
- [Developer Support](https://developer.etrade.com/support)

## Project Structure

This section explains what each file in the project does:

### Core Files

- **`etrade_client.py`** - Main E*TRADE API client library
  - Handles OAuth 1.0a authentication flow
  - Manages access token storage and validation
  - Provides async methods for all E*TRADE API endpoints
  - Automatically validates tokens on first use
  - Clears invalid tokens and prompts re-authentication when needed

- **`etrade_mcp_server.py`** - MCP server implementation
  - Implements the Model Context Protocol server interface
  - Exposes tools for authentication and API access
  - Handles tool calls and converts them to E*TRADE API requests
  - Manages the E*TRADE client instance lifecycle
  - References `etrade_endpoints.json` in tool descriptions for agent guidance

- **`etrade_endpoints.json`** - Comprehensive E*TRADE API endpoints reference
  - Contains all supported API endpoints organized by category
  - Includes endpoint paths, HTTP methods, parameters, and examples
  - Provides usage notes, common patterns, and order type references
  - Used by agents to determine correct endpoint usage and parameters
  - Can be read directly as JSON (no additional utilities required)

### Server Scripts

- **`run_server.py`** - Python wrapper script to start the MCP server
  - Loads environment variables from `.env` file
  - Validates required credentials are present
  - Sets up Python path and imports
  - Starts the MCP server with proper error handling

- **`run_server.sh`** - Bash wrapper script to start the MCP server
  - Loads environment variables from `.env` file
  - Calls `run_server.py` with proper directory context
  - Convenient for Unix/Linux/macOS systems

### Configuration Files

- **`env.example`** - Template for environment variables
  - Shows required environment variables
  - Contains placeholder values (never commit real credentials!)
  - Copy to `.env` and fill in your actual credentials

- **`.env`** - Your actual environment variables (not committed to git)
  - Contains your E*TRADE Consumer Key and Secret
  - Sandbox/production setting
  - Optional: E*TRADE username/password for automated OAuth
  - See `.gitignore` - this file is excluded from version control

- **`requirements.txt`** - Python dependencies
  - Lists all required Python packages
  - Install with: `pip install -r requirements.txt`

- **`.gitignore`** - Git ignore rules
  - Excludes `.env` and `.etrade_tokens.json` from version control
  - Excludes Python cache files and virtual environments

### Documentation Files

- **`README.md`** - This file! Main project documentation
- **`QUICKSTART.md`** - Quick start guide for new users
- **`RUNNING.md`** - Detailed instructions for running the server

### Generated Files (Do Not Edit)

- **`.etrade_tokens.json`** - OAuth access tokens storage (not committed to git)
  - Automatically created after OAuth authentication
  - Contains access_token and access_token_secret
  - Used for subsequent API calls
  - Automatically validated on first use
  - Cleared automatically if tokens become invalid

- **`__pycache__/`** - Python bytecode cache (not committed to git)

## Latest Updates

### Token Validation System (Latest)

The client now includes automatic token validation:

- **Automatic Token Loading**: Tokens are loaded from `.etrade_tokens.json` on initialization
- **Token Validation**: Tokens are validated on first API call by making a test request
- **Session Caching**: Validation result is cached for the session to avoid redundant API calls
- **Automatic Re-authentication**: If tokens are invalid, they're cleared and you're prompted to re-authenticate
- **Mid-Session Expiration**: If tokens expire during a session (401/403 errors), they're automatically cleared

### Error Handling Improvements

- Specific exception handling for file operations
- Better error messages for authentication failures
- Graceful handling of corrupted token files

### Security Enhancements

- `env.example` contains only placeholder values
- Proper `.gitignore` to prevent committing sensitive files
- Token validation prevents using expired credentials

## License

This tool is provided as-is for educational and development purposes. Ensure compliance with E*TRADE's terms of service and applicable regulations.

