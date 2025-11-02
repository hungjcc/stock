import yfinance as yf
import pypyodbc
from datetime import datetime
from credential import username, password, server, database

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def get_stock_price_and_name(symbol, market_type="US"):
    """Get stock price and company name from Yahoo Finance"""
    # Add .HK suffix for Hong Kong stocks
    query_symbol = f"{symbol}.HK" if market_type == "HK" else symbol
    
    stock = yf.Ticker(query_symbol)
    data = stock.history(period="1d")
    info = stock.info
    company_name = info.get('shortName', '')
    if not data.empty:
        latest_price = round(data['Close'].iloc[-1], 2)
        print(f"Latest price for {query_symbol} ({company_name}): {latest_price}")
        return latest_price, company_name
    else:
        print(f"No data found for {query_symbol}")
        return None, None

def insert_stock_to_db(symbol, company_name, price, timestamp, market_type):
    """Insert a new stock record into the database"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Check if symbol already exists for the given market
        cursor.execute("""
            SELECT COUNT(*) FROM [dbo].[test-myproject-table]
            WHERE Symbol = ? AND MarketType = ?
        """, (symbol, market_type))
        
        if cursor.fetchone()[0] > 0:
            print(f"Stock {symbol} ({market_type}) already exists in database.")
            return False
        
        # Insert new record
        cursor.execute("""
            INSERT INTO [dbo].[test-myproject-table] 
            (Symbol, CompanyName, Price, Timestamp, MarketType)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, company_name, price, timestamp, market_type))
        
        conn.commit()
        print(f"Added new record for {symbol} ({company_name}) - {market_type}")
        return True
        
    except Exception as e:
        print(f"Error inserting into database: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_all_stock_prices(market_type=None):
    """Update all existing stock prices in the database"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get all stocks, optionally filtered by market type
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
        
        stocks = cursor.fetchall()
        
        if not stocks:
            print("No stocks found in the database.")
            return
        
        print(f"Updating prices for {len(stocks)} stocks...")
        updated_count = 0
        
        for stock_id, symbol, company_name, mkt_type in stocks:
            try:
                price, new_company_name = get_stock_price_and_name(symbol, mkt_type)
                if price is not None:
                    # Update the price, timestamp, and potentially the company name
                    cursor.execute("""
                        UPDATE [dbo].[test-myproject-table]
                        SET Price = ?, Timestamp = ?, CompanyName = ?
                        WHERE StockNumber = ?
                    """, (price, datetime.now(), new_company_name, stock_id))
                    conn.commit()
                    updated_count += 1
                    print(f"✓ Updated {symbol} ({new_company_name}) - {mkt_type}: {price}")
                else:
                    print(f"✗ Failed to update {symbol} - {mkt_type}")
            except Exception as e:
                print(f"✗ Error updating {symbol} - {mkt_type}: {str(e)}")
        
        print(f"\nUpdate complete! Successfully updated {updated_count} out of {len(stocks)} stocks.")
        
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def get_stock_count(market_type=None):
    """Get the count of stocks in the database"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        if market_type:
            cursor.execute("""
                SELECT MarketType, COUNT(*) as count 
                FROM [dbo].[test-myproject-table]
                WHERE MarketType = ?
                GROUP BY MarketType
            """, (market_type,))
        else:
            cursor.execute("""
                SELECT MarketType, COUNT(*) as count 
                FROM [dbo].[test-myproject-table]
                GROUP BY MarketType
                UNION ALL
                SELECT 'Total' as MarketType, COUNT(*) as count 
                FROM [dbo].[test-myproject-table]
            """)
        
        results = cursor.fetchall()
        print("\nStock Count Summary:")
        print("-" * 30)
        for market, count in results:
            print(f"{market or 'Unspecified'}: {count} stocks")
        print("-" * 30)
            
    except Exception as e:
        print(f"Error getting stock count: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def list_all_stocks(market_type=None):
    """List all stocks in the database"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get stocks, optionally filtered by market type
        if market_type:
            cursor.execute("""
                SELECT Symbol, CompanyName, Price, Timestamp, MarketType 
                FROM [dbo].[test-myproject-table]
                WHERE MarketType = ?
                ORDER BY Symbol
            """, (market_type,))
        else:
            cursor.execute("""
                SELECT Symbol, CompanyName, Price, Timestamp, MarketType 
                FROM [dbo].[test-myproject-table]
                ORDER BY MarketType, Symbol
            """)
        
        stocks = cursor.fetchall()
        if not stocks:
            print("No stocks found in the database.")
            return
        
        print("\nCurrent Stock List:")
        print("Symbol\tMarket\tCompany Name\tPrice\tLast Updated")
        print("-" * 80)
        for symbol, name, price, timestamp, mkt_type in stocks:
            print(f"{symbol}\t{mkt_type}\t{name[:30]}\t${price:.2f}\t{timestamp}")
            
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    while True:
        print("\n=== Stock Price Tracker ===")
        print("1. Add New HK Stock")
        print("2. Add New US Stock")
        print("3. Update All HK Stocks")
        print("4. Update All US Stocks")
        print("5. Update All Stocks")
        print("6. List All Stocks")
        print("7. List HK Stocks")
        print("8. List US Stocks")
        print("9. Show Stock Count")
        print("10. Quit")
        
        choice = input("\nEnter your choice (1-10): ").strip()
        
        if choice == "10":
            print("Exiting program.")
            break
        
        elif choice in ["1", "2"]:
            market_type = "HK" if choice == "1" else "US"
            if market_type == "HK":
                symbol = input("Enter HK stock number (1-4 digits, e.g., 5, 23, 123, 0005): ").strip()
                if not symbol.isdigit() or not (1 <= len(symbol) <= 4):
                    print("Invalid input. Please enter 1 to 4 digits for the stock number.")
                    continue
                symbol = symbol.zfill(4)
            else:
                symbol = input("Enter US stock symbol (e.g., AAPL, MSFT, GOOGL): ").strip().upper()
                if not symbol:
                    print("Invalid input. Please enter a valid stock symbol.")
                    continue
            
            price, company_name = get_stock_price_and_name(symbol, market_type)
            if price is not None:
                timestamp = datetime.now()
                insert_stock_to_db(symbol, company_name, price, timestamp, market_type)
        
        elif choice in ["3", "4", "5"]:
            market_type = None if choice == "5" else ("HK" if choice == "3" else "US")
            update_all_stock_prices(market_type)
        
        elif choice in ["6", "7", "8"]:
            market_type = None if choice == "6" else ("HK" if choice == "7" else "US")
            list_all_stocks(market_type)
            
        elif choice == "9":
            get_stock_count()
        
        else:
            print("Invalid choice. Please enter a number between 1 and 10.")