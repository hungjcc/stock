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
            SELECT StockNumber FROM [dbo].[test-myproject-table]
            WHERE Symbol = ? AND MarketType = ?
        """, (symbol, market_type))
        
        result = cursor.fetchone()
        if result:
            stock_number = result[0]
            # Insert only into history table
            cursor.execute("""
                INSERT INTO StockPriceHistory 
                (StockNumber, Symbol, CompanyName, Price, Timestamp, MarketType)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (stock_number, symbol, company_name, price, timestamp, market_type))
            
            # Update main table with latest price
            cursor.execute("""
                UPDATE [dbo].[test-myproject-table]
                SET Price = ?, Timestamp = ?, CompanyName = ?
                WHERE StockNumber = ?
            """, (price, timestamp, company_name, stock_number))
            
            print(f"Updated price history for {symbol} ({company_name})")
        else:
            # Insert into main table first
            cursor.execute("""
                INSERT INTO [dbo].[test-myproject-table]
                (Symbol, CompanyName, Price, Timestamp, MarketType)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, company_name, price, timestamp, market_type))
            
            # Get the newly created StockNumber
            cursor.execute("SELECT @@IDENTITY")
            stock_number = cursor.fetchone()[0]
            
            # Insert into history table
            cursor.execute("""
                INSERT INTO StockPriceHistory 
                (StockNumber, Symbol, CompanyName, Price, Timestamp, MarketType)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (stock_number, symbol, company_name, price, timestamp, market_type))
            
            print(f"Added new stock {symbol} ({company_name})")
        
        conn.commit()
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
                    timestamp = datetime.now()
                    
                    # Insert into history table
                    cursor.execute("""
                        INSERT INTO StockPriceHistory 
                        (StockNumber, Symbol, CompanyName, Price, Timestamp, MarketType)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (stock_id, symbol, new_company_name, price, timestamp, mkt_type))
                    
                    # Update main table
                    cursor.execute("""
                        UPDATE [dbo].[test-myproject-table]
                        SET Price = ?, Timestamp = ?, CompanyName = ?
                        WHERE StockNumber = ?
                    """, (price, timestamp, new_company_name, stock_id))
                    
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

def view_price_history(symbol=None, market_type=None, limit=10):
    """View price history for a specific stock or all stocks"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        if symbol and market_type:
            cursor.execute("""
                SELECT h.Symbol, h.CompanyName, h.Price, h.Timestamp, h.MarketType
                FROM StockPriceHistory h
                WHERE h.Symbol = ? AND h.MarketType = ?
                ORDER BY h.Timestamp DESC
            """, (symbol, market_type))
        else:
            cursor.execute("""
                SELECT h.Symbol, h.CompanyName, h.Price, h.Timestamp, h.MarketType
                FROM StockPriceHistory h
                ORDER BY h.Timestamp DESC
            """)
        
        records = cursor.fetchmany(limit) if limit else cursor.fetchall()
        
        if not records:
            print("No price history found.")
            return
        
        print("\nPrice History:")
        print("Symbol\tMarket\tCompany Name\tPrice\tTimestamp")
        print("-" * 80)
        for symbol, name, price, timestamp, mkt_type in records:
            print(f"{symbol}\t{mkt_type}\t{name[:30]}\t${price:.2f}\t{timestamp}")
            
    except Exception as e:
        print(f"Error retrieving price history: {str(e)}")
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
                SELECT Symbol, CompanyName, Price, Timestamp, MarketType,
                       (SELECT COUNT(*) FROM StockPriceHistory h 
                        WHERE h.Symbol = t.Symbol AND h.MarketType = t.MarketType) as HistoryCount
                FROM [dbo].[test-myproject-table] t
                WHERE MarketType = ?
                ORDER BY Symbol
            """, (market_type,))
        else:
            cursor.execute("""
                SELECT Symbol, CompanyName, Price, Timestamp, MarketType,
                       (SELECT COUNT(*) FROM StockPriceHistory h 
                        WHERE h.Symbol = t.Symbol AND h.MarketType = t.MarketType) as HistoryCount
                FROM [dbo].[test-myproject-table] t
                ORDER BY MarketType, Symbol
            """)
        
        stocks = cursor.fetchall()
        if not stocks:
            print("No stocks found in the database.")
            return
        
        print("\nCurrent Stock List:")
        print("Symbol\tMarket\tCompany Name\tPrice\tLast Updated\tHistory Records")
        print("-" * 100)
        for symbol, name, price, timestamp, mkt_type, history_count in stocks:
            print(f"{symbol}\t{mkt_type}\t{name[:30]}\t${price:.2f}\t{timestamp}\t{history_count}")
            
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
        print("9. View Price History")
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
            print("\nView Price History:")
            print("1. View All History")
            print("2. View Specific Stock History")
            sub_choice = input("Enter your choice (1-2): ").strip()
            
            if sub_choice == "1":
                view_price_history()
            elif sub_choice == "2":
                market_type = input("Enter market type (HK/US): ").strip().upper()
                if market_type not in ["HK", "US"]:
                    print("Invalid market type.")
                    continue
                symbol = input("Enter stock symbol: ").strip().upper()
                if market_type == "HK":
                    symbol = symbol.zfill(4)
                view_price_history(symbol, market_type)
            else:
                print("Invalid choice.")
        
        else:
            print("Invalid choice. Please enter a number between 1 and 10.")