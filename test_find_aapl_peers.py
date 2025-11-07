"""
Find AAPL peers in the bulk CSV data
"""

import requests
import csv
from io import StringIO
from ingestion.fmp_client import FMPClient

client = FMPClient()

print("\nFetching peers bulk data...")
url = f"https://financialmodelingprep.com/api/v4/stock_peers_bulk?apikey={client.api_key}"
response = requests.get(url, timeout=30)

if response.status_code == 200:
    print(f"✓ Got CSV data: {len(response.text)} bytes")
    
    # Parse CSV
    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)
    
    # Search for specific symbols
    symbols_to_find = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'PLTR']
    
    print("\nSearching for US tech stocks...")
    print("-" * 80)
    
    found_count = 0
    for row in reader:
        symbol = row.get('symbol', '').strip('"')
        peers = row.get('peers', '').strip('"')
        
        if symbol in symbols_to_find:
            print(f"\n{symbol}:")
            print(f"  Peers: {peers[:200]}")
            if len(peers) > 200:
                print(f"  ... (truncated, total length: {len(peers)})")
            
            # Count peers
            peer_list = [p.strip() for p in peers.split(',') if p.strip()]
            print(f"  Total Peers: {len(peer_list)}")
            found_count += 1
            
            if found_count >= len(symbols_to_find):
                break
    
    print("\n" + "-" * 80)
    print(f"\nFound {found_count} out of {len(symbols_to_find)} symbols")
    
else:
    print(f"Error: {response.status_code}")
    print(response.text[:500])
