"""
Testing script to view data downloaded from ANBIMA API.

Run this script to:
1. Test fetching data from ANBIMA API for specific dates
2. View the structure and content of the API response
3. Verify data is being downloaded correctly
"""

import sys
import os
from datetime import date, timedelta
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import AnbimaETTJFetcher, fetch_anbima_ettj_api


def test_api_call(ref_date: date = None):
    """
    Test a direct API call and display the raw response.
    
    Args:
        ref_date: Date to fetch (defaults to today)
    """
    if ref_date is None:
        ref_date = date.today()
    
    date_str = ref_date.strftime('%Y-%m-%d')
    
    print(f"\n{'='*60}")
    print(f"Testing ANBIMA API for date: {date_str}")
    print(f"{'='*60}\n")
    
    try:
        response = fetch_anbima_ettj_api(date_str)
        
        if response is None:
            print("❌ No data returned from API (response is None)")
            return
        
        print("✅ API call successful!")
        print(f"\nRaw response type: {type(response)}")
        print(f"\nRaw response (pretty printed):")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error calling API: {e}")


def test_fetcher_for_date(ref_date: date = None):
    """
    Test the fetcher class for a specific date.
    
    Args:
        ref_date: Date to fetch (defaults to today)
    """
    if ref_date is None:
        ref_date = date.today()
    
    date_str = ref_date.strftime('%Y-%m-%d')
    
    print(f"\n{'='*60}")
    print(f"Testing AnbimaETTJFetcher for date: {date_str}")
    print(f"{'='*60}\n")
    
    fetcher = AnbimaETTJFetcher()
    data = fetcher.fetch_ettj_for_date(ref_date)
    
    if not data:
        print("❌ No data returned from fetcher")
        return
    
    print(f"✅ Fetched {len(data)} vertices\n")
    
    # Display first few entries
    print("Sample data (first 5 vertices):")
    print("-" * 80)
    for i, vertex in enumerate(data[:5]):
        print(f"\nVertex {i+1}:")
        for key, value in vertex.items():
            print(f"  {key}: {value}")
    
    if len(data) > 5:
        print(f"\n... and {len(data) - 5} more vertices")
    
    # Summary statistics
    print("\n" + "="*60)
    print("Summary Statistics:")
    print("="*60)
    print(f"Total vertices: {len(data)}")
    
    # Count how many have each rate type
    nominal_count = sum(1 for v in data if v.get('nominal') is not None)
    real_count = sum(1 for v in data if v.get('real') is not None)
    breakeven_count = sum(1 for v in data if v.get('breakeven') is not None)
    
    print(f"Vertices with nominal rate: {nominal_count}")
    print(f"Vertices with real rate: {real_count}")
    print(f"Vertices with breakeven rate: {breakeven_count}")


def test_week_data():
    """Test fetching data for the previous week."""
    print(f"\n{'='*60}")
    print("Testing week data fetch (previous week)")
    print(f"{'='*60}\n")
    
    today = date.today()
    days_since_monday = today.weekday()
    current_week_monday = today - timedelta(days=days_since_monday)

    previous_week_start = current_week_monday - timedelta(days=7)
    previous_week_end = previous_week_start + timedelta(days=4)
    
    print(f"Date range: {previous_week_start} to {previous_week_end}")
    
    fetcher = AnbimaETTJFetcher()
    data = fetcher.fetch_week_data(previous_week_start, previous_week_end)
    
    if not data:
        print("\n❌ No data returned for the week")
        return
    
    print(f"\n✅ Fetched {len(data)} total data points for the week")
    
    # Group by date
    dates_found = {}
    for vertex in data:
        vertex_date = vertex['date']
        if vertex_date not in dates_found:
            dates_found[vertex_date] = 0
        dates_found[vertex_date] += 1
    
    print(f"\nData found for {len(dates_found)} dates:")
    for d in sorted(dates_found.keys()):
        print(f"  {d}: {dates_found[d]} vertices")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ANBIMA ETTJ API Testing Script")
    print("="*60)
    
    # Test 1: Direct API call for today
    print("\n\n1. Testing direct API call (today)")
    test_api_call()
    
    # Test 2: Direct API call for a recent business day
    recent_date = date.today() - timedelta(days=3)
    print(f"\n\n2. Testing direct API call ({recent_date})")
    test_api_call(recent_date)
    
    # Test 3: Fetcher for today
    print("\n\n3. Testing fetcher (today)")
    test_fetcher_for_date()
    
    # Test 4: Week data
    print("\n\n4. Testing week data fetch")
    test_week_data()
    
    print("\n\n" + "="*60)
    print("Testing complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
