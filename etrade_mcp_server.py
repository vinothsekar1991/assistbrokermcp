"""
MCP Server for E*TRADE API Trading
Provides tools for account information, market data, and trade execution
"""

import asyncio
import json
import os
from typing import Any, Optional, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from etrade_client import ETradeClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Server("etrade-mcp")

# Initialize E*TRADE client
etrade_client: Optional[ETradeClient] = None


def get_client() -> ETradeClient:
    """Get or initialize the E*TRADE client"""
    global etrade_client
    if etrade_client is None:
        consumer_key = os.getenv("ETRADE_CONSUMER_KEY")
        consumer_secret = os.getenv("ETRADE_CONSUMER_SECRET")
        sandbox = os.getenv("ETRADE_SANDBOX", "true").lower() == "true"
        
        if not consumer_key or not consumer_secret:
            raise ValueError(
                "ETRADE_CONSUMER_KEY and ETRADE_CONSUMER_SECRET must be set in environment variables"
            )
        
        etrade_client = ETradeClient(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            sandbox=sandbox
        )
    
    return etrade_client


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools"""
    return [
        Tool(
            name="etrade_get",
            description="Make a GET request to any E*TRADE API endpoint. Supports all GET endpoints like accounts, quotes, orders, positions, etc. Refer to etrade_endpoints.json for complete list of available endpoints, parameters, and examples.",
            inputSchema={
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "API endpoint path (e.g., '/v1/accounts/list', '/v1/accounts/{accountId}/balance', '/v1/market/quote'). See etrade_endpoints.json for all available endpoints."
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters as key-value pairs (e.g., {'symbol': 'AAPL', 'detailFlag': 'ALL'}). Refer to etrade_endpoints.json for endpoint-specific parameters.",
                        "additionalProperties": True
                    }
                },
                "required": ["endpoint"]
            }
        ),
        Tool(
            name="etrade_post",
            description="Make a POST, PUT, or DELETE request to any E*TRADE API endpoint. Supports all POST/PUT/DELETE endpoints like placing orders, canceling orders, etc. Refer to etrade_endpoints.json for complete list of available endpoints, request body structures, and examples.",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method: 'POST', 'PUT', or 'DELETE' (default: 'POST')",
                        "enum": ["POST", "PUT", "DELETE"],
                        "default": "POST"
                    },
                    "endpoint": {
                        "type": "string",
                        "description": "API endpoint path (e.g., '/v1/accounts/{accountId}/orders', '/v1/accounts/{accountId}/orders/cancel'). See etrade_endpoints.json for all available endpoints."
                    },
                    "data": {
                        "type": "object",
                        "description": "Request body as JSON object (e.g., order data, cancel request, etc.). Refer to etrade_endpoints.json for endpoint-specific request body structures and examples.",
                        "additionalProperties": True
                    },
                    "params": {
                        "type": "object",
                        "description": "Optional query parameters as key-value pairs. Refer to etrade_endpoints.json for endpoint-specific parameters.",
                        "additionalProperties": True
                    }
                },
                "required": ["endpoint"]
            }
        ),
        Tool(
            name="initialize_oauth",
            description="Initialize OAuth flow and get authorization URL. Returns the authorization URL for use with automated OAuth flow.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_login_credentials",
            description="Get E*TRADE login credentials from environment variables. Use these credentials with Playwright MCP to automate the OAuth authorization flow.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="automate_oauth",
            description="Automated OAuth flow using Playwright MCP. This will navigate to the authorization URL, login with stored credentials, accept authorization, and extract the verification code. Requires Playwright MCP server to be available.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="complete_oauth",
            description="Complete OAuth flow by providing the verification code from the authorization URL. Call this after visiting the URL from initialize_oauth.",
            inputSchema={
                "type": "object",
                "properties": {
                    "verificationCode": {
                        "type": "string",
                        "description": "The verification code obtained after visiting the authorization URL"
                    }
                },
                "required": ["verificationCode"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        client = get_client()
        
        if name == "etrade_get":
            endpoint = arguments["endpoint"] or ""
            # Normalize endpoint to start with '/'
            endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
            params = arguments.get("params", {})
            result = await client.api_get(endpoint, params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "etrade_post":
            endpoint = arguments["endpoint"] or ""
            endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
            method = (arguments.get("method", "POST") or "POST").upper()
            if method not in ("POST", "PUT", "DELETE"):
                return [TextContent(type="text", text=json.dumps({"error": f"Invalid method '{method}'. Use POST, PUT, or DELETE."}))]
            data = arguments.get("data", {})
            params = arguments.get("params", {})
            result = await client.api_request(method, endpoint, params=params if params else None, data=data if data else None)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "initialize_oauth":
            result = await client.initialize_oauth()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_login_credentials":
            username = os.getenv("ETRADE_USERNAME")
            password = os.getenv("ETRADE_PASSWORD")
            if not username or not password:
                return [TextContent(type="text", text=json.dumps({
                    "error": "ETRADE_USERNAME and ETRADE_PASSWORD must be set in environment variables",
                    "status": "error"
                }, indent=2))]
            return [TextContent(type="text", text=json.dumps({
                "username": username,
                "password": password,
                "status": "success"
            }, indent=2))]
        
        elif name == "automate_oauth":
            # This tool provides instructions for the agent to use Playwright MCP
            # The agent should call initialize_oauth first, then use Playwright to automate
            result = await client.initialize_oauth()
            if result.get("status") != "success":
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            auth_url = result.get("authorization_url")
            username = os.getenv("ETRADE_USERNAME")
            password = os.getenv("ETRADE_PASSWORD")
            
            if not username or not password:
                return [TextContent(type="text", text=json.dumps({
                    "error": "ETRADE_USERNAME and ETRADE_PASSWORD must be set in environment variables",
                    "authorization_url": auth_url,
                    "status": "error"
                }, indent=2))]
            
            return [TextContent(type="text", text=json.dumps({
                "authorization_url": auth_url,
                "instructions": "Use Playwright MCP to: 1) Navigate to authorization_url, 2) Fill username and password, 3) Click login, 4) Click Accept, 5) Extract verification code from textbox, 6) Call complete_oauth with the code",
                "username": username,
                "password": password,
                "status": "ready"
            }, indent=2))]
        
        elif name == "complete_oauth":
            verification_code = arguments["verificationCode"]
            result = await client.complete_oauth(verification_code)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())


