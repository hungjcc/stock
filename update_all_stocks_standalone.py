"""
Standalone script to update all stocks (option 5) without importing other modules.
It connects to the database, fetches all stocks (optionally filtered by market),
fetches latest prices from Yahoo Finance, inserts history rows into
`StockPriceHistory`, updates the main table, and prints a summary.

Usage:
    python update_all_stocks_standalone.py        # update all markets
    python update_all_stocks_standalone.py HK     # update HK only
    python update_all_stocks_standalone.py US     # update US only

"""
import sys
from datetime import datetime

import yfinance as yf
import pypyodbc
from credential import username, password, server, database

# Connection string using ODBC Driver 18
conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"


def get_latest_price_and_name(symbol, market_type):
    query_symbol = f"{symbol}.HK" if market_type == "HK" else symbol
    try:
        ticker = yf.Ticker(query_symbol)
        data = ticker.history(period="1d")
        info = ticker.info
        company_name = info.get('shortName', '')
        if not data.empty:
            price = round(data['Close'].iloc[-1], 2)
            return price, company_name
        else:
            return None, company_name
    except Exception as e:
        print(f"Error fetching from Yahoo Finance for {query_symbol}: {e}")
        return None, None


def update_all(market_type=None):
    """Update all stocks in the DB. market_type can be 'HK', 'US', or None for all."""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()

        if market_type:
            cursor.execute("""
                SELECT StockNumber, Symbol, CompanyName, MarketType
                FROM [dbo].[test-myproject-table]
                WHERE MarketType = ?
            """, (market_type,))
        else:
            cursor.execute("""
                SELECT StockNumber, Symbol, CompanyName, MarketType
                FROM [dbo].[test-myproject-table]
            """)

        rows = cursor.fetchall()
        total = len(rows)
        if total == 0:
            print("No stocks found to update.")
            return

        print(f"Updating {total} stocks (market={market_type or 'ALL'})...")
        updated = 0
        failed = 0

        for stock_id, symbol, existing_name, mkt in rows:
            # For HK, symbol may be stored as zero-padded; ensure correct query
            try:
                price, company_name = get_latest_price_and_name(symbol, mkt)
                if price is None:
                    print(f"✗ No data for {symbol} ({mkt})")
                    failed += 1
                    continue

                ts = datetime.now()

                # Insert into history table
                cursor.execute("""
                    INSERT INTO StockPriceHistory (StockNumber, Symbol, CompanyName, Price, Timestamp, MarketType)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (stock_id, symbol, company_name, price, ts, mkt))

                # Update main table with latest price and name
                cursor.execute("""
                    UPDATE [dbo].[test-myproject-table]
                    SET Price = ?, Timestamp = ?, CompanyName = ?
                    WHERE StockNumber = ?
                """, (price, ts, company_name, stock_id))

                conn.commit()
                updated += 1
                print(f"✓ Updated {symbol} ({mkt}): {price}")
            except Exception as e:
                print(f"✗ Error processing {symbol} ({mkt}): {e}")
                conn.rollback()
                failed += 1

        print(f"\nFinished. Updated: {updated}, Failed: {failed}, Total: {total}")

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


def main():
    market = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().upper()
        if arg in ("HK", "US"):
            market = arg
        else:
            print("Invalid argument. Use 'HK' or 'US' or none for all.")
            return

    print(f"Start update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (market={market or 'ALL'})")
    update_all(market)
    print(f"End update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
