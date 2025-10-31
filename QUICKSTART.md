# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file**:
   ```bash
   cp env.example .env
   # Edit .env and add your E*TRADE credentials
   ```

3. **Get API credentials from E*TRADE**:
   - Visit: https://us.etrade.com/etx/ris/apikey
   - Request a Sandbox key (for testing)
   - Copy Consumer Key and Consumer Secret to `.env`

## First-Time Authentication

1. **Start the MCP server** (or use with your MCP client)

2. **Initialize OAuth**:
   - Call `initialize_oauth` tool
   - Copy the `authorization_url` from the response

3. **Authorize**:
   - Open the `authorization_url` in your browser
   - Log in to E*TRADE
   - Authorize the application
   - Copy the verification code shown

4. **Complete OAuth**:
   - Call `complete_oauth` tool with the verification code
   - Tokens will be saved for future use

## Example: Place a Trade

```json
// 1. Get your account ID
{
  "tool": "etrade_get",
  "arguments": {"endpoint": "/v1/accounts/list"}
}

// 2. Check a stock quote
{
  "tool": "etrade_get",
  "arguments": {
    "endpoint": "/v1/market/quote",
    "params": {"symbol": "AAPL", "detailFlag": "ALL"}
  }
}

// 3. Place a market order
{
  "tool": "etrade_post",
  "arguments": {
    "method": "POST",
    "endpoint": "/v1/accounts/YOUR_ACCOUNT_ID/orders",
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

// 4. Check order status
{
  "tool": "etrade_get",
  "arguments": {
    "endpoint": "/v1/accounts/YOUR_ACCOUNT_ID/orders",
    "params": {"status": "OPEN"}
  }
}
```

## Common Tasks

### View Account Balance
```json
{
  "tool": "etrade_get",
  "arguments": {"endpoint": "/v1/accounts/YOUR_ACCOUNT_ID/balance"}
}
```

### View Holdings
```json
{
  "tool": "etrade_get",
  "arguments": {"endpoint": "/v1/accounts/YOUR_ACCOUNT_ID/positions"}
}
```

### Place Limit Order
```json
{
  "tool": "etrade_post",
  "arguments": {
    "method": "POST",
    "endpoint": "/v1/accounts/YOUR_ACCOUNT_ID/orders",
    "data": {
      "orderType": "EQ",
      "Order": [{
        "priceType": "LIMIT",
        "limitPrice": 350.00,
        "orderTerm": "GOOD_FOR_DAY",
        "Instrument": [{
          "Product": {"securityType": "EQ", "symbol": "MSFT"},
          "orderAction": "BUY",
          "quantityType": "QUANTITY",
          "quantity": 5
        }]
      }]
    }
  }
}
```

### Cancel Order
```json
{
  "tool": "etrade_post",
  "arguments": {
    "method": "PUT",
    "endpoint": "/v1/accounts/YOUR_ACCOUNT_ID/orders/cancel",
    "data": {"orderId": "order_id_to_cancel"}
  }
}
```

See the Example Workflow section in README.md for more examples.

## Troubleshooting

**"Not authenticated" error**: Run `initialize_oauth` → `complete_oauth` first.

**"Failed to get request token"**: Check your Consumer Key and Secret in `.env`.

**Orders not executing**: Make sure you're using the correct account ID and have sufficient buying power.


