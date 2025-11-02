import yfinance as yf
import pypyodbc
from datetime import datetime
from credential import username, password, server, database

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def get_hk_stock_price_and_name(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    info = stock.info
    company_name = info.get('shortName', '')
    if not data.empty:
        latest_price = round(data['Close'].iloc[-1], 2)
        print(f"Latest price for {symbol} ({company_name}): {latest_price}")
        return latest_price, company_name
    else:
        print(f"No data found for {symbol}")
        return None, company_name

def get_us_stock_price_and_name(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    info = stock.info
    company_name = info.get('shortName', '')
    if not data.empty:
        latest_price = round(data['Close'].iloc[-1], 2)
        print(f"Latest price for {symbol} ({company_name}): {latest_price}")
        return latest_price, company_name
    else:
        print(f"No data found for {symbol}")
        return None, company_name

def update_or_append_to_db(company_name, stock_no, price, timestamp, market_type):
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Check if stock exists
        cursor.execute(
            "SELECT COUNT(*) FROM StockPrices WHERE StockNumber = ? AND MarketType = ?",
            (stock_no, market_type)
        )
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            # Update existing record
            cursor.execute("""
                UPDATE StockPrices 
                SET Price = ?, Timestamp = ?, CompanyName = ?
                WHERE StockNumber = ? AND MarketType = ?
            """, (price, timestamp, company_name, stock_no, market_type))
            print(f"Updated existing record for stock {stock_no}")
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO StockPrices (CompanyName, StockNumber, Price, Timestamp, MarketType)
                VALUES (?, ?, ?, ?, ?)
            """, (company_name, stock_no, price, timestamp, market_type))
            print(f"Added new record for stock {stock_no}")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error updating database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def update_all_stock_prices(market_type="HK"):
    """Update all existing stock prices in the database"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get all stocks of specified market type
        cursor.execute("SELECT StockNumber FROM StockPrices WHERE MarketType = ?", (market_type,))
        stocks = cursor.fetchall()
        
        if not stocks:
            print(f"No {market_type} stocks found in the database.")
            return
        
        print(f"Updating prices for {len(stocks)} {market_type} stocks...")
        updated_count = 0
        
        for stock in stocks:
            stock_no = str(stock[0]).zfill(4) if market_type == "HK" else stock[0]
            
            if market_type == "HK":
                symbol = f"{stock_no}.HK"
                price, company_name = get_hk_stock_price_and_name(symbol)
            else:  # US market
                symbol = stock_no  # US symbols don't need suffix
                price, company_name = get_us_stock_price_and_name(symbol)
            
            try:
                if price is not None:
                    # Update the price and timestamp
                    cursor.execute("""
                        UPDATE StockPrices 
                        SET Price = ?, Timestamp = ?, CompanyName = ?
                        WHERE StockNumber = ? AND MarketType = ?
                    """, (price, datetime.now(), company_name, stock_no, market_type))
                    conn.commit()
                    updated_count += 1
                    print(f"✓ Updated {stock_no} ({company_name}): {price}")
                else:
                    print(f"✗ Failed to update {stock_no}")
            except Exception as e:
                print(f"✗ Error updating {stock_no}: {str(e)}")
        
        print(f"\nUpdate complete! Successfully updated {updated_count} out of {len(stocks)} {market_type} stocks.")
        
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    while True:
        print("\n=== Stock Price Tracker ===")
        print("1. Add/Update HK Stock")
        print("2. Add/Update US Stock")
        print("3. Update All HK Stocks")
        print("4. Update All US Stocks")
        print("5. Quit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "5":
            print("Exiting program.")
            break
        
        elif choice == "1":
            stock_no = input("Enter HK stock number (1-4 digits, e.g., 5, 23, 123, 0005): ").strip()
            if not stock_no.isdigit() or not (1 <= len(stock_no) <= 4):
                print("Invalid input. Please enter 1 to 4 digits for the stock number.")
                continue
            
            stock_no_padded = stock_no.zfill(4)
            symbol = f"{stock_no_padded}.HK"
            price, company_name = get_hk_stock_price_and_name(symbol)
            if price is not None:
                timestamp = datetime.now()
                update_or_append_to_db(company_name, stock_no_padded, price, timestamp, "HK")
        
        elif choice == "2":
            stock_symbol = input("Enter US stock symbol (e.g., AAPL, MSFT, GOOGL): ").strip().upper()
            if not stock_symbol:
                print("Invalid input. Please enter a valid stock symbol.")
                continue
            
            price, company_name = get_us_stock_price_and_name(stock_symbol)
            if price is not None:
                timestamp = datetime.now()
                update_or_append_to_db(company_name, stock_symbol, price, timestamp, "US")
        
        elif choice == "3":
            update_all_stock_prices("HK")
        
        elif choice == "4":
            update_all_stock_prices("US")
        
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")