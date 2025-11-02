import yfinance as yf
import pypyodbc
from datetime import datetime
from credential import username, password, server, database

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

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
        print("\nView Price History:")
        print("1. View All History")
        print("2. View Specific Stock History")
        print("3. Quit")
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "3":
            print("Exiting program.")
            break
        
        elif choice == "1":
            view_price_history()
        
        elif choice == "2":
            market_type = input("Enter market type (HK/US): ").strip().upper()
            if market_type not in ["HK", "US"]:
                print("Invalid market type.")
                continue
            symbol = input("Enter stock symbol: ").strip().upper()
            if market_type == "HK":
                symbol = symbol.zfill(4)
            view_price_history(symbol, market_type)
        
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")