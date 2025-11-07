"""
Test FMP Peers Endpoint
Find the correct endpoint and format for peer data
"""

import requests
from ingestion.fmp_client import FMPClient

client = FMPClient()
symbol = "AAPL"

# Test different endpoint variations
endpoints_to_try = [
    # Format: (url, description)
    (f"{client.base_url}/stock_peers?symbol={symbol}", "v3/stock_peers"),
    (f"{client.base_url}/v4/stock_peers_bulk?symbol={symbol}", "v3/v4/stock_peers_bulk"),
    (f"{client.base_url.replace('/v3', '/v4')}/stock_peers_bulk?symbol={symbol}", "v4/stock_peers_bulk"),
    (f"https://financialmodelingprep.com/api/v4/stock_peers_bulk?symbol={symbol}", "direct v4/stock_peers_bulk"),
    (f"https://financialmodelingprep.com/stable/peers-bulk?symbol={symbol}", "stable/peers-bulk"),
    (f"{client.base_url}/stock_peers", f"v3/stock_peers (no param, POST style)"),
]

print(f"\nTesting FMP Peers Endpoints for {symbol}")
print("=" * 80)

for url, description in endpoints_to_try:
    try:
        full_url = f"{url}&apikey={client.api_key}" if "?" in url else f"{url}?apikey={client.api_key}"
        print(f"\n{description}:")
        print(f"URL: {full_url[:100]}...")
        
        response = requests.get(full_url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            if isinstance(data, list):
                print(f"Length: {len(data)}")
                if len(data) > 0:
                    print(f"First Item: {str(data[0])[:200]}")
            elif isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                print(f"Content: {str(data)[:200]}")
            else:
                print(f"Content: {str(data)[:200]}")
                
            # If we got non-empty data, this is likely the right endpoint
            if data and (isinstance(data, list) and len(data) > 0 or isinstance(data, dict)):
                print(f"✓ SUCCESS - This endpoint returned data!")
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Exception: {str(e)[:100]}")

print("\n" + "=" * 80)
print("\nNote: If all endpoints return empty [], the FMP plan may not include")
print("peer data, or you may need to contact FM support for the correct endpoint.")
