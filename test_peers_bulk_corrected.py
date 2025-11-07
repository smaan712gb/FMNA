"""
Test FMP Peers Bulk Endpoint - Corrected Version
The bulk endpoint returns ALL peers data, not for a single symbol
"""

import requests
import time
from ingestion.fmp_client import FMPClient

client = FMPClient()

print("\n" + "=" * 80)
print("Testing FMP Peers Bulk Endpoint (No Symbol Parameter)")
print("=" * 80)

# Test the v4 bulk endpoint without symbol parameter
endpoints_to_try = [
    ("https://financialmodelingprep.com/api/v4/stock_peers_bulk", "v4/stock_peers_bulk (ALL DATA)"),
    ("https://financialmodelingprep.com/stable/peers-bulk", "stable/peers-bulk (ALL DATA)"),
]

for base_url, description in endpoints_to_try:
    try:
        full_url = f"{base_url}?apikey={client.api_key}"
        print(f"\n{description}:")
        print(f"URL: {full_url[:80]}...")
        
        response = requests.get(full_url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            
            # Handle CSV response
            if 'csv' in content_type.lower() or 'text' in content_type.lower():
                lines = response.text.split('\n')
                print(f"Response Format: CSV")
                print(f"Total Lines: {len(lines)}")
                print(f"First 5 lines:")
                for i, line in enumerate(lines[:5]):
                    print(f"  {i+1}: {line}")
                    
                # Parse CSV manually
                if len(lines) > 1:
                    headers = lines[0].split(',')
                    print(f"\nHeaders: {headers}")
                    
                    # Look for AAPL in the data
                    print(f"\nSearching for AAPL peers...")
                    for line in lines[1:100]:  # Check first 100 records
                        if 'AAPL' in line:
                            print(f"Found: {line}")
                            break
                            
            # Handle JSON response
            else:
                try:
                    data = response.json()
                    print(f"Response Format: JSON")
                    print(f"Response Type: {type(data)}")
                    
                    if isinstance(data, list):
                        print(f"Total Records: {len(data)}")
                        if len(data) > 0:
                            print(f"First Record: {data[0]}")
                            
                            # Look for AAPL
                            aapl_peers = [item for item in data if item.get('symbol') == 'AAPL']
                            if aapl_peers:
                                print(f"\nAAPL Peers: {aapl_peers[0]}")
                    elif isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                        
                except Exception as e:
                    print(f"JSON Parsing Error: {e}")
                    print(f"Raw Response (first 500 chars): {response.text[:500]}")
                    
            print(f"✓ SUCCESS - Endpoint returned data!")
            
        elif response.status_code == 429:
            print(f"⚠ Rate Limited - This bulk endpoint has a 10-second refresh limit")
            print(f"Response: {response.text[:300]}")
            
        elif response.status_code == 402:
            print(f"✗ Payment Required - Endpoint requires subscription upgrade")
            print(f"Response: {response.text[:300]}")
            
        else:
            print(f"Error: {response.text[:300]}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        
    # Wait between requests to avoid rate limiting
    time.sleep(2)

print("\n" + "=" * 80)
print("\nSummary:")
print("- v4/stock_peers_bulk: Returns ALL peers (rate limited, 10-sec refresh)")
print("- stable/peers-bulk: Requires paid subscription (402 error)")
print("\nRecommendation:")
print("1. Use v4/stock_peers_bulk to fetch ALL peers data (cache it)")
print("2. OR use individual stock data endpoints that may include peer info")
print("3. OR upgrade FMP subscription to access stable/peers-bulk")
print("=" * 80)
