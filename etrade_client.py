"""
E*TRADE API Client
Handles OAuth 1.0a authentication and API requests
"""

import os
import json
import asyncio
import requests
from requests_oauthlib import OAuth1
from urllib.parse import parse_qs
from typing import Optional, Dict, Any
import time


class ETradeClient:
    """Client for interacting with E*TRADE API"""
    
    # Sandbox endpoints
    SANDBOX_BASE = "https://apisb.etrade.com"
    SANDBOX_REQUEST_TOKEN_URL = "https://apisb.etrade.com/oauth/request_token"
    SANDBOX_AUTHORIZE_URL = "https://us.etrade.com/e/t/etws/authorize"
    SANDBOX_ACCESS_TOKEN_URL = "https://apisb.etrade.com/oauth/access_token"
    
    # Production endpoints
    PROD_BASE = "https://api.etrade.com"
    PROD_REQUEST_TOKEN_URL = "https://api.etrade.com/oauth/request_token"
    PROD_AUTHORIZE_URL = "https://us.etrade.com/e/t/etws/authorize"
    PROD_ACCESS_TOKEN_URL = "https://api.etrade.com/oauth/access_token"
    
    def __init__(self, consumer_key: str, consumer_secret: str, sandbox: bool = True):
        """
        Initialize E*TRADE client
        
        Args:
            consumer_key: Consumer key from E*TRADE
            consumer_secret: Consumer secret from E*TRADE
            sandbox: Whether to use sandbox environment (default: True)
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.sandbox = sandbox
        
        self.base_url = self.SANDBOX_BASE if sandbox else self.PROD_BASE
        self.request_token_url = self.SANDBOX_REQUEST_TOKEN_URL if sandbox else self.PROD_REQUEST_TOKEN_URL
        self.authorize_url = self.SANDBOX_AUTHORIZE_URL if sandbox else self.PROD_AUTHORIZE_URL
        self.access_token_url = self.SANDBOX_ACCESS_TOKEN_URL if sandbox else self.PROD_ACCESS_TOKEN_URL
        
        # OAuth tokens
        self.request_token = None
        self.request_token_secret = None
        self.access_token = None
        self.access_token_secret = None
        
        # Token validation cache (to avoid validating on every API call)
        self._tokens_validated = False
        
        # Try to load saved tokens
        self._load_tokens()
    
    def _load_tokens(self):
        """Load OAuth tokens from environment or file"""
        token_file = os.getenv("ETRADE_TOKEN_FILE", ".etrade_tokens.json")
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get("access_token")
                    self.access_token_secret = tokens.get("access_token_secret")
            except (IOError, OSError, json.JSONDecodeError, ValueError) as e:
                # Silently fail if token file is corrupted or inaccessible
                # This allows the OAuth flow to proceed normally
                pass
    
    def _save_tokens(self):
        """Save OAuth tokens to file"""
        if self.access_token and self.access_token_secret:
            token_file = os.getenv("ETRADE_TOKEN_FILE", ".etrade_tokens.json")
            try:
                with open(token_file, 'w') as f:
                    json.dump({
                        "access_token": self.access_token,
                        "access_token_secret": self.access_token_secret
                    }, f)
            except (IOError, OSError) as e:
                # Log error but don't raise - allow authentication to proceed
                # even if token saving fails
                pass
    
    def _get_oauth(self, token: Optional[str] = None, token_secret: Optional[str] = None) -> OAuth1:
        """Create OAuth1 object for requests"""
        return OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=token or self.access_token,
            resource_owner_secret=token_secret or self.access_token_secret,
            signature_type='AUTH_HEADER'
        )
    
    async def initialize_oauth(self) -> Dict[str, Any]:
        """
        Step 1: Get request token and authorization URL
        
        Returns:
            Dictionary with authorization_url
        """
        try:
            # Get request token (run in thread pool to avoid blocking)
            # For request token, we need to include callback_uri in OAuth signature
            # E*TRADE requires oauth_callback parameter for OAuth 1.0a
            def _make_request():
                oauth = OAuth1(
                    self.consumer_key,
                    client_secret=self.consumer_secret,
                    callback_uri='oob',  # Out-of-band callback for manual verification
                    signature_type='AUTH_HEADER',
                    signature_method='HMAC-SHA1'
                )
                return requests.post(self.request_token_url, auth=oauth)
            
            # Use to_thread if available (Python 3.9+), otherwise use executor
            try:
                response = await asyncio.to_thread(_make_request)
            except AttributeError:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, _make_request)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get request token: {response.status_code} - {response.text}")
            
            # Parse response
            params = parse_qs(response.text)
            self.request_token = params.get('oauth_token', [None])[0]
            self.request_token_secret = params.get('oauth_token_secret', [None])[0]
            
            if not self.request_token:
                raise Exception("Failed to parse request token from response")
            
            # Generate authorization URL
            auth_url = f"{self.authorize_url}?key={self.consumer_key}&token={self.request_token}"
            
            return {
                "authorization_url": auth_url,
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def complete_oauth(self, verification_code: str) -> Dict[str, Any]:
        """
        Step 2: Exchange verification code for access token
        
        Args:
            verification_code: Verification code from authorization page
            
        Returns:
            Dictionary with access token status
        """
        try:
            if not self.request_token or not self.request_token_secret:
                raise Exception("Request token not found. Please run initialize_oauth first.")
            
            # Exchange for access token (run in thread pool to avoid blocking)
            # oauth_verifier must be included in OAuth signature
            # When verifier is passed to OAuth1 constructor, it's automatically included in signature
            def _make_request():
                # Create OAuth1 with verifier - it will be automatically included in signature
                oauth = OAuth1(
                    self.consumer_key,
                    client_secret=self.consumer_secret,
                    resource_owner_key=self.request_token,
                    resource_owner_secret=self.request_token_secret,
                    signature_type='AUTH_HEADER',
                    verifier=verification_code  # OAuth1 will include this in signature and request body
                )
                return requests.post(
                    self.access_token_url,
                    auth=oauth
                )
            
            # Use to_thread if available (Python 3.9+), otherwise use executor
            try:
                response = await asyncio.to_thread(_make_request)
            except AttributeError:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, _make_request)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")
            
            # Parse response
            params = parse_qs(response.text)
            self.access_token = params.get('oauth_token', [None])[0]
            self.access_token_secret = params.get('oauth_token_secret', [None])[0]
            
            if not self.access_token:
                raise Exception("Failed to parse access token from response")
            
            # Save tokens
            self._save_tokens()
            # Reset validation flag since we have new tokens
            self._tokens_validated = False
            
            return {
                "status": "success",
                "message": "OAuth authentication completed successfully. You can now use other API functions."
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def _validate_tokens(self) -> bool:
        """
        Validate existing tokens by making a test API call
        
        Returns:
            True if tokens are valid, False otherwise
        """
        if not self.access_token or not self.access_token_secret:
            return False
        
        try:
            # Make a lightweight API call to validate tokens
            # Using account list endpoint as it's simple and doesn't require account ID
            url = f"{self.base_url}/v1/accounts/list"
            headers = {'Accept': 'application/json'}
            
            def _make_request():
                return requests.get(
                    url,
                    auth=self._get_oauth(),
                    headers=headers
                )
            
            # Use to_thread if available (Python 3.9+), otherwise use executor
            try:
                response = await asyncio.to_thread(_make_request)
            except AttributeError:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, _make_request)
            
            # If we get a 401 or 403, tokens are invalid
            if response.status_code in [401, 403]:
                return False
            
            # If we get a successful response, tokens are valid
            return response.status_code == 200
        
        except Exception:
            # Any exception means tokens are likely invalid
            return False
    
    def _clear_tokens(self):
        """Clear stored tokens"""
        self.access_token = None
        self.access_token_secret = None
        self._tokens_validated = False
        # Also clear from file
        token_file = os.getenv("ETRADE_TOKEN_FILE", ".etrade_tokens.json")
        if os.path.exists(token_file):
            try:
                os.remove(token_file)
            except (IOError, OSError):
                pass
    
    async def _check_auth(self):
        """
        Check if client is authenticated and tokens are valid.
        If tokens exist but are invalid, clear them and raise exception.
        Validates tokens only once per session (cached) to avoid redundant API calls.
        """
        if not self.access_token or not self.access_token_secret:
            raise Exception("Not authenticated. Please run initialize_oauth and complete_oauth first.")
        
        # Validate tokens only if not already validated in this session
        if not self._tokens_validated:
            is_valid = await self._validate_tokens()
            if not is_valid:
                # Clear invalid tokens
                self._clear_tokens()
                raise Exception("Access tokens are invalid or expired. Please run initialize_oauth and complete_oauth to re-authenticate.")
            # Mark tokens as validated for this session
            self._tokens_validated = True
    
    async def api_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generic API request method for POST, PUT, DELETE
        
        Args:
            method: HTTP method (POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            
        Returns:
            JSON response as dictionary
        """
        return await self._make_request(method, endpoint, params=params, data=data)
    
    async def api_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generic GET request method
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        return await self._make_request("GET", endpoint, params=params, data=None)
    
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated API request
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            
        Returns:
            JSON response as dictionary
        """
        await self._check_auth()
        
        url = f"{self.base_url}{endpoint}"
        # Only set Content-Type for POST/PUT requests with body data
        headers = {'Accept': 'application/json'}
        if method in ['POST', 'PUT'] and data:
            headers['Content-Type'] = 'application/json'
        
        # Run synchronous request in thread pool to avoid blocking
        def _make_request():
            return requests.request(
                method=method,
                url=url,
                auth=self._get_oauth(),
                headers=headers,
                params=params,
                json=data if method in ['POST', 'PUT'] else None
            )
        
        # Use to_thread if available (Python 3.9+), otherwise use executor
        try:
            response = await asyncio.to_thread(_make_request)
        except AttributeError:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, _make_request)
        
        # Handle authentication errors - tokens may have expired mid-session
        if response.status_code in [401, 403]:
            # Clear tokens and validation flag if we get auth error
            self._clear_tokens()
            raise Exception(f"Authentication failed (status {response.status_code}). Access tokens may have expired. Please run initialize_oauth and complete_oauth to re-authenticate.")
        
        if response.status_code not in [200, 201]:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        try:
            return response.json()
        except (ValueError, json.JSONDecodeError):
            return {"response": response.text, "status_code": response.status_code}
    
    async def get_account_list(self) -> Dict[str, Any]:
        """Get list of all accounts"""
        return await self._make_request("GET", "/v1/accounts/list")
    
    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Get account balance
        
        Args:
            account_id: Account ID key from account list
        """
        return await self._make_request("GET", f"/v1/accounts/{account_id}/balance")
    
    async def get_account_positions(self, account_id: str) -> Dict[str, Any]:
        """
        Get account positions (holdings)
        
        Args:
            account_id: Account ID key from account list
        """
        return await self._make_request("GET", f"/v1/accounts/{account_id}/positions")
    
    async def get_quote(self, symbol: str, detail_flag: str = "ALL") -> Dict[str, Any]:
        """
        Get market quote for one or more symbols
        
        Args:
            symbol: Single symbol or comma-separated symbols string
            detail_flag: Level of detail (ALL, FUNDAMENTAL, INTRADAY, OPTIONS, WEEK_52, MF_DETAIL)
        """
        symbols_path = symbol
        endpoint = f"/v1/market/quote/{symbols_path}"
        params: Dict[str, Any] = {}
        if detail_flag and detail_flag != "ALL":
            params["detailFlag"] = detail_flag
        return await self._make_request("GET", endpoint, params=params or None)
    
    async def place_order(
        self,
        account_id: str,
        symbol: str,
        quantity: int,
        order_action: str,
        order_type: str = "EQ",
        price_type: str = "MARKET",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place an order
        
        Args:
            account_id: Account ID key
            symbol: Stock symbol
            quantity: Number of shares
            order_action: BUY, SELL, BUY_TO_COVER, SELL_SHORT
            order_type: EQ (equity), etc.
            price_type: MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP_CNST
            limit_price: Limit price for LIMIT orders
            stop_price: Stop price for STOP orders
            client_order_id: Optional client order ID
        """
        # Build order request
        order = {
            "orderType": order_type,
            "clientOrderId": client_order_id or f"ORDER_{int(time.time())}",
            "Order": [
                {
                    "allOrNone": False,
                    "priceType": price_type,
                    "orderTerm": "GOOD_FOR_DAY",
                    "marketSession": "REGULAR",
                    "stopPrice": stop_price,
                    "limitPrice": limit_price,
                    "Instrument": [
                        {
                            "Product": {
                                "securityType": "EQ",
                                "symbol": symbol
                            },
                            "orderAction": order_action,
                            "quantityType": "QUANTITY",
                            "quantity": quantity
                        }
                    ]
                }
            ]
        }
        
        # Remove None values
        order["Order"][0] = {k: v for k, v in order["Order"][0].items() if v is not None}
        order["Order"][0]["Instrument"][0] = {k: v for k, v in order["Order"][0]["Instrument"][0].items() if v is not None}
        
        return await self._make_request("POST", f"/v1/accounts/{account_id}/orders", data=order)
    
    async def get_orders(
        self,
        account_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get orders for an account
        
        Args:
            account_id: Account ID key
            from_date: Start date in MM/dd/yyyy format
            to_date: End date in MM/dd/yyyy format
            status: Order status filter
        """
        params = {}
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date
        if status:
            params["status"] = status
        
        return await self._make_request("GET", f"/v1/accounts/{account_id}/orders", params=params if params else None)
    
    async def cancel_order(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order
        
        Args:
            account_id: Account ID key
            order_id: Order ID to cancel
        """
        return await self._make_request("PUT", f"/v1/accounts/{account_id}/orders/cancel", data={"orderId": order_id})

