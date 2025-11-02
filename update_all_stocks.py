"""
Simple script to run the "Update All Stocks" action (option 5) non-interactively.
It imports the update_all_stock_prices function from
`get_stock_sql_with_market_new.py` and runs it for all markets.

Usage:
    python update_all_stocks.py

Optional: pass MARKET on the command line to update only one market:
    python update_all_stocks.py HK
    python update_all_stocks.py US

"""
import sys
from datetime import datetime

try:
    # Import the function from the improved module
    from get_stock_sql_with_market_new import update_all_stock_prices
except Exception as e:
    print(f"Error importing update function: {e}")
    raise


def main():
    market = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().upper()
        if arg in ("HK", "US"):
            market = arg
        else:
            print("Invalid market argument. Use 'HK' or 'US'.")
            return

    print(f"Starting full update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (market={market or 'ALL'})...")
    update_all_stock_prices(market)
    print(f"Update finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
