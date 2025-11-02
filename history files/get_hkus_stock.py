import yfinance as yf
import pandas as pd
from datetime import datetime
import os
from openpyxl import load_workbook

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

def update_or_append_to_excel(company_name, stock_no, price, timestamp, filename="hk_stock_prices_new.xlsx", sheet_name="Sheet1"):
    row = {"Company Name": company_name, "Stock Number": stock_no, "Price": price, "Timestamp": timestamp}
    
    if os.path.exists(filename):
        # Read existing data from specified sheet
        try:
            df = pd.read_excel(filename, sheet_name=sheet_name)
        except:
            # If sheet doesn't exist, create empty DataFrame
            df = pd.DataFrame()
            df['Company Name'] = []
            df['Stock Number'] = []
            df['Price'] = []
            df['Timestamp'] = []
        
        # Convert stock numbers to strings for comparison and handle different formats
        df['Stock Number'] = df['Stock Number'].astype(str).str.zfill(4)
        stock_no_padded = stock_no.zfill(4)
        
        # Check if stock number already exists
        existing_row = df[df['Stock Number'] == stock_no_padded]
        
        if not existing_row.empty:
            # Update existing row
            df.loc[df['Stock Number'] == stock_no_padded, 'Price'] = price
            df.loc[df['Stock Number'] == stock_no_padded, 'Timestamp'] = timestamp
            df.loc[df['Stock Number'] == stock_no_padded, 'Company Name'] = company_name
            print(f"Updated existing record for stock {stock_no}")
        else:
            # Append new row
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            print(f"Added new record for stock {stock_no}")
        
        # Write back to Excel preserving all sheets
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get the workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Auto-adjust column widths
            try:
                for column in worksheet.columns:
                    max_length = 0
                    try:
                        column_letter = column[0].column_letter
                    except:
                        continue
                    
                    for cell in column:
                        try:
                            if cell.value:
                                cell_length = len(str(cell.value))
                                if cell_length > max_length:
                                    max_length = cell_length
                        except:
                            pass
                    
                    adjusted_width = min(max(max_length + 2, 10), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            except:
                pass  # If formatting fails, just continue
        
    else:
        # Create new file with first row
        df = pd.DataFrame([row])
        df.to_excel(filename, sheet_name=sheet_name, index=False)
        print(f"Created new file and added record for stock {stock_no}")

def update_all_stock_prices(filename="hk_stock_prices_new.xlsx", sheet_name="Sheet1", market_type="HK"):
    """Update all existing stock prices in the Excel file"""
    if not os.path.exists(filename):
        print("No Excel file found. Please add some stocks first.")
        return
    
    try:
        df = pd.read_excel(filename, sheet_name=sheet_name)
        if df.empty:
            print("No stocks found in the Excel file.")
            return
        
        print(f"Updating prices for {len(df)} {market_type} stocks...")
        updated_count = 0
        
        for index, row in df.iterrows():
            stock_no = str(row['Stock Number']).zfill(4)
            if market_type == "HK":
                symbol = f"{stock_no}.HK"
                price, company_name = get_hk_stock_price_and_name(symbol)
            else:  # US market
                symbol = stock_no  # US symbols don't need suffix
                price, company_name = get_us_stock_price_and_name(symbol)
            
            try:
                if price is not None:
                    # Update the price and timestamp
                    df.loc[index, 'Price'] = price
                    df.loc[index, 'Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    df.loc[index, 'Company Name'] = company_name
                    updated_count += 1
                    print(f"✓ Updated {stock_no} ({company_name}): {price}")
                else:
                    print(f"✗ Failed to update {stock_no}")
            except Exception as e:
                print(f"✗ Error updating {stock_no}: {str(e)}")
        
        # Write back to Excel preserving all sheets
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get the workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Auto-adjust column widths
            try:
                for column in worksheet.columns:
                    max_length = 0
                    try:
                        column_letter = column[0].column_letter
                    except:
                        continue
                    
                    for cell in column:
                        try:
                            if cell.value:
                                cell_length = len(str(cell.value))
                                if cell_length > max_length:
                                    max_length = cell_length
                        except:
                            pass
                    
                    adjusted_width = min(max(max_length + 2, 10), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            except:
                pass  # If formatting fails, just continue
        
        print(f"\nUpdate complete! Successfully updated {updated_count} out of {len(df)} {market_type} stocks.")
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")

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
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_or_append_to_excel(company_name, stock_no_padded, price, timestamp, "hk_stock_prices_new.xlsx", "HK_Stocks")
        
        elif choice == "2":
            stock_symbol = input("Enter US stock symbol (e.g., AAPL, MSFT, GOOGL): ").strip().upper()
            if not stock_symbol:
                print("Invalid input. Please enter a valid stock symbol.")
                continue
            
            price, company_name = get_us_stock_price_and_name(stock_symbol)
            if price is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_or_append_to_excel(company_name, stock_symbol, price, timestamp, "hk_stock_prices_new.xlsx", "US_Stocks")
        
        elif choice == "3":
            update_all_stock_prices("hk_stock_prices_new.xlsx", "HK_Stocks", "HK")
        
        elif choice == "4":
            update_all_stock_prices("hk_stock_prices_new.xlsx", "US_Stocks", "US")
        
        else:
            print("Invalid choice. Please enter a number between 1 and 5.") 