import yfinance as yf
import pypyodbc
from datetime import datetime
from credential import username, password, server, database
from export_history_to_csv import export_history_to_csv

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
            # Insert into history table
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

def list_all_stocks(market_type=None):
    """List all stocks in the database"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get stocks, optionally filtered by market type
        if market_type:
            cursor.execute("""
                SELECT t.Symbol, t.CompanyName, t.Price, t.Timestamp, t.MarketType,
                       (SELECT COUNT(*) FROM StockPriceHistory h 
                        WHERE h.Symbol = t.Symbol AND h.MarketType = t.MarketType) as HistoryCount
                FROM [dbo].[test-myproject-table] t
                WHERE t.MarketType = ?
                ORDER BY t.Symbol
            """, (market_type,))
        else:
            cursor.execute("""
                SELECT t.Symbol, t.CompanyName, t.Price, t.Timestamp, t.MarketType,
                       (SELECT COUNT(*) FROM StockPriceHistory h 
                        WHERE h.Symbol = t.Symbol AND h.MarketType = t.MarketType) as HistoryCount
                FROM [dbo].[test-myproject-table] t
                ORDER BY t.MarketType, t.Symbol
            """)
        
        stocks = cursor.fetchall()
        if not stocks:
            print("No stocks found in the database.")
            return
        
        print("\nCurrent Stock List:")
        print("Symbol  Market  Company Name                      Price      Last Updated           History")
        print("-" * 90)
        for symbol, name, price, timestamp, mkt_type, history_count in stocks:
            symbol_fmt = f"{symbol:<6}"
            market_fmt = f"{mkt_type:<7}"
            name_fmt = f"{name[:30]:<30}"
            price_fmt = f"${price:>8.2f}"
            timestamp_fmt = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            history_fmt = f"{history_count:>3} records"
            
            print(f"{symbol_fmt} {market_fmt} {name_fmt} {price_fmt}  {timestamp_fmt}  {history_fmt}")
            
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def view_price_history(symbol=None, market_type=None, page_size=10, page_number=1):
    """View price history for a specific stock or all stocks with pagination"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get total count for pagination
        if symbol and market_type:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM StockPriceHistory 
                WHERE Symbol = ? AND MarketType = ?
            """, (symbol, market_type))
        else:
            cursor.execute("SELECT COUNT(*) FROM StockPriceHistory")
        
        total_records = cursor.fetchone()[0]
        total_pages = (total_records + page_size - 1) // page_size
        
        # Adjust page number if out of bounds
        page_number = min(max(1, page_number), total_pages)
        offset = (page_number - 1) * page_size
        
        # Get records with pagination
        if symbol and market_type:
            cursor.execute("""
                SELECT h.Symbol, h.CompanyName, h.Price, h.Timestamp, h.MarketType
                FROM StockPriceHistory h
                WHERE h.Symbol = ? AND h.MarketType = ?
                ORDER BY h.Timestamp DESC
                OFFSET ? ROWS
                FETCH NEXT ? ROWS ONLY
            """, (symbol, market_type, offset, page_size))
        else:
            cursor.execute("""
                SELECT h.Symbol, h.CompanyName, h.Price, h.Timestamp, h.MarketType
                FROM StockPriceHistory h
                ORDER BY h.Timestamp DESC
                OFFSET ? ROWS
                FETCH NEXT ? ROWS ONLY
            """, (offset, page_size))
        
        records = cursor.fetchall()
        
        if not records:
            print("No price history found.")
            return
        
        # Print pagination info
        print(f"\nPrice History (Page {page_number} of {total_pages}, Total Records: {total_records})")
        print("Symbol  Market  Company Name                      Price      Timestamp")
        print("-" * 75)
        
        for symbol, name, price, timestamp, mkt_type in records:
            # Format each column with fixed width
            symbol_fmt = f"{symbol:<6}"
            market_fmt = f"{mkt_type:<7}"
            name_fmt = f"{name[:30]:<30}"
            price_fmt = f"${price:>8.2f}"
            timestamp_fmt = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"{symbol_fmt} {market_fmt} {name_fmt} {price_fmt}  {timestamp_fmt}")
        
        # Print navigation options
        if total_pages > 1:
            print("\nNavigation:")
            if page_number > 1:
                print("P - Previous page")
            if page_number < total_pages:
                print("N - Next page")
            print("Q - Return to main menu")
            
            while True:
                nav = input("\nEnter navigation choice: ").strip().upper()
                if nav == 'P' and page_number > 1:
                    return view_price_history(symbol, market_type, page_size, page_number - 1)
                elif nav == 'N' and page_number < total_pages:
                    return view_price_history(symbol, market_type, page_size, page_number + 1)
                elif nav == 'Q':
                    break
                elif nav not in ['P', 'N', 'Q']:
                    print("Invalid choice. Please try again.")
            
    except Exception as e:
        print(f"Error retrieving price history: {str(e)}")
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
        print("11. Export history to CSV")
        
        choice = input("\nEnter your choice (1-11): ").strip()
        
        if choice == "10":
            print("Exiting program.")
            break

        elif choice == "11":
            print("\nExport Price History to CSV")
            market = input("Enter market type to filter (HK/US) or press Enter for all: ").strip().upper()
            if market == '':
                market = None
            elif market not in ('HK', 'US'):
                print("Invalid market type. Use 'HK' or 'US'.")
                continue

            symbol = input("Enter symbol to filter (AAPL or 0005) or press Enter for all: ").strip().upper()
            if symbol == '':
                symbol = None
            else:
                if market == 'HK' and symbol.isdigit():
                    symbol = symbol.zfill(4)

            default_file = 'stock_price_history.csv'
            filename = input(f"Enter output CSV filename (default: {default_file}): ").strip()
            if filename == '':
                filename = default_file

            ok = export_history_to_csv(filename=filename, market_type=market, symbol=symbol)
            if ok:
                print("Export completed.")
            else:
                print("Export failed or no records found.")
        
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
                view_price_history(page_number=1)
            elif sub_choice == "2":
                market_type = input("Enter market type (HK/US): ").strip().upper()
                if market_type not in ["HK", "US"]:
                    print("Invalid market type.")
                    continue
                symbol = input("Enter stock symbol: ").strip().upper()
                if market_type == "HK":
                    symbol = symbol.zfill(4)
                view_price_history(symbol, market_type, page_number=1)
            else:
                print("Invalid choice.")
        
        else:
            print("Invalid choice. Please enter a number between 1 and 11.")