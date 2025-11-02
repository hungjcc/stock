import yfinance as yf
import pypyodbc
from datetime import datetime
from credential import username, password, server, database

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def get_stock_price_and_name(symbol):
    """Get stock price and company name from Yahoo Finance"""
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    info = stock.info
    company_name = info.get('shortName', '')
    if not data.empty:
        # Convert float price to int (cents) since the table uses INT
        latest_price = int(round(data['Close'].iloc[-1] * 100))
        print(f"Latest price for {symbol} ({company_name}): {latest_price/100:.2f}")
        return latest_price, company_name[:10]  # Truncate company name to 10 chars
    else:
        print(f"No data found for {symbol}")
        return None, None

def insert_stock_to_db(company_name, price, timestamp):
    """Insert a new stock record into the database"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Insert new record (StockNumber is IDENTITY column, so we don't specify it)
        cursor.execute("""
            INSERT INTO [dbo].[test-myproject-table] (CompanyName, Price, Timestamp)
            VALUES (?, ?, ?)
        """, (company_name, price, timestamp))
        
        conn.commit()
        print(f"Added new record for {company_name}")
        
    except Exception as e:
        print(f"Error inserting into database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def update_all_stock_prices():
    """Update all existing stock prices in the database"""
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get all stocks
        cursor.execute("SELECT StockNumber, CompanyName FROM [dbo].[test-myproject-table]")
        stocks = cursor.fetchall()
        
        if not stocks:
            print("No stocks found in the database.")
            return
        
        print(f"Updating prices for {len(stocks)} stocks...")
        updated_count = 0
        
        for stock_id, company_name in stocks:
            # For now, we'll use the company name to get the stock symbol
            # You might want to store the actual stock symbol in the database later
            symbol = company_name.strip()  # Remove padding from CHAR(10)
            
            try:
                price, _ = get_stock_price_and_name(symbol)
                if price is not None:
                    # Update the price and timestamp
                    cursor.execute("""
                        UPDATE [dbo].[test-myproject-table]
                        SET Price = ?, Timestamp = ?
                        WHERE StockNumber = ?
                    """, (price, datetime.now(), stock_id))
                    conn.commit()
                    updated_count += 1
                    print(f"✓ Updated {company_name.strip()}: {price/100:.2f}")
                else:
                    print(f"✗ Failed to update {company_name.strip()}")
            except Exception as e:
                print(f"✗ Error updating {company_name.strip()}: {str(e)}")
        
        print(f"\nUpdate complete! Successfully updated {updated_count} out of {len(stocks)} stocks.")
        
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    while True:
        print("\n=== Stock Price Tracker ===")
        print("1. Add New Stock")
        print("2. Update All Stocks")
        print("3. Quit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "3":
            print("Exiting program.")
            break
        
        elif choice == "1":
            symbol = input("Enter stock symbol (e.g., AAPL, MSFT, GOOGL): ").strip().upper()
            if not symbol:
                print("Invalid input. Please enter a valid stock symbol.")
                continue
            
            price, company_name = get_stock_price_and_name(symbol)
            if price is not None:
                timestamp = datetime.now()
                insert_stock_to_db(company_name, price, timestamp)
        
        elif choice == "2":
            update_all_stock_prices()
        
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")