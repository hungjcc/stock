import yfinance as yf
import pandas as pd
from datetime import datetime
import os
from openpyxl import load_workbook
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np

def detect_market(symbol):
    """
    Detect if the symbol is for Hong Kong or US market
    Returns: 'HK' or 'US'
    """
    if symbol.endswith('.HK'):
        return 'HK'
    elif symbol.endswith('.US') or symbol.endswith('.O') or '.' not in symbol:
        return 'US'
    else:
        # Default to US for unknown formats
        return 'US'

def get_stock_detailed_prices_multi_period(symbol, periods=[10, 50, 100, 200]):
    """
    Get detailed stock price information for multiple periods
    Supports both Hong Kong and US stocks
    Returns: Dictionary with data for each period
    """
    # Normalize symbol format
    market = detect_market(symbol)
    if market == 'HK' and not symbol.endswith('.HK'):
        symbol = f"{symbol.zfill(4)}.HK"
    elif market == 'US' and symbol.endswith('.HK'):
        symbol = symbol.replace('.HK', '')
    
    stock = yf.Ticker(symbol)
    info = stock.info
    company_name = info.get('shortName', '') or info.get('longName', '')
    
    all_data = {}
    
    for period in periods:
        try:
            # Get data for the specified period
            data = stock.history(period=f"{period}d")
            
            if not data.empty:
                # Calculate summary statistics
                latest_data = data.iloc[-1]
                first_data = data.iloc[0]
                
                period_data = {
                    'company_name': company_name,
                    'symbol': symbol,
                    'market': market,
                    'period_days': period,
                    'start_date': first_data.name.strftime('%Y-%m-%d'),
                    'end_date': latest_data.name.strftime('%Y-%m-%d'),
                    'open_price': first_data['Open'],
                    'close_price': latest_data['Close'],
                    'high_price': data['High'].max(),
                    'low_price': data['Low'].min(),
                    'volume': data['Volume'].sum(),
                    'avg_volume': data['Volume'].mean(),
                    'price_change': latest_data['Close'] - first_data['Open'],
                    'price_change_pct': ((latest_data['Close'] - first_data['Open']) / first_data['Open']) * 100,
                    'volatility': data['Close'].std(),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                all_data[period] = period_data
                
                print(f"=== {period} Days Data ===")
                print(f"Market: {market}")
                print(f"Period: {period_data['start_date']} to {period_data['end_date']}")
                print(f"开盘价 (Open): {period_data['open_price']:.2f}")
                print(f"收盘价 (Close): {period_data['close_price']:.2f}")
                print(f"最高价 (High): {period_data['high_price']:.2f}")
                print(f"最低价 (Low): {period_data['low_price']:.2f}")
                print(f"成交量 (Volume): {period_data['volume']:,.0f}")
                print(f"平均成交量 (Avg Volume): {period_data['avg_volume']:,.0f}")
                print(f"价格变化: {period_data['price_change']:.2f} ({period_data['price_change_pct']:.2f}%)")
                print(f"波动率 (Volatility): {period_data['volatility']:.2f}")
                print("-" * 40)
                
            else:
                print(f"No data found for {period} days period")
                
        except Exception as e:
            print(f"Error getting {period} days data: {e}")
    
    return all_data, company_name

def create_k_diagram(data, symbol, company_name, period_days, save_path):
    """
    Create K-diagram (candlestick chart) for the given stock data
    """
    try:
        # Set up the figure and axis
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
        fig.suptitle(f'{symbol} - {company_name}\n{period_days} Days K-Diagram', fontsize=14, fontweight='bold')
        
        # Prepare data for candlestick chart
        dates = data.index
        opens = data['Open'].values
        highs = data['High'].values
        lows = data['Low'].values
        closes = data['Close'].values
        volumes = data['Volume'].values
        
        # Color scheme for candlesticks
        colors = ['red' if close < open else 'green' for open, close in zip(opens, closes)]
        
        # Plot candlesticks
        for i, (date, open_price, high, low, close, color) in enumerate(zip(dates, opens, highs, lows, closes, colors)):
            # Body of the candle
            body_height = abs(close - open_price)
            body_bottom = min(open_price, close)
            
            # Draw the body
            rect = Rectangle((i - 0.3, body_bottom), 0.6, body_height, 
                           facecolor=color, edgecolor='black', linewidth=0.5)
            ax1.add_patch(rect)
            
            # Draw the wick
            ax1.plot([i, i], [low, high], color='black', linewidth=1)
            
            # Draw the open/close lines
            if close > open_price:  # Green candle (bullish)
                ax1.plot([i - 0.3, i + 0.3], [open_price, open_price], color='black', linewidth=1)
                ax1.plot([i - 0.3, i + 0.3], [close, close], color='black', linewidth=1)
            else:  # Red candle (bearish)
                ax1.plot([i - 0.3, i + 0.3], [open_price, open_price], color='black', linewidth=1)
                ax1.plot([i - 0.3, i + 0.3], [close, close], color='black', linewidth=1)
        
        # Set up the price chart
        ax1.set_ylabel('Price', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f'Price Chart ({period_days} Days)', fontweight='bold')
        
        # Format x-axis
        if len(dates) > 20:
            # Show every 5th date for better readability
            step = max(1, len(dates) // 10)
            ax1.set_xticks(range(0, len(dates), step))
            ax1.set_xticklabels([dates[i].strftime('%m/%d') for i in range(0, len(dates), step)], rotation=45)
        else:
            ax1.set_xticks(range(len(dates)))
            ax1.set_xticklabels([date.strftime('%m/%d') for date in dates], rotation=45)
        
        # Plot volume bars
        ax2.bar(range(len(volumes)), volumes, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
        ax2.set_ylabel('Volume', fontweight='bold')
        ax2.set_xlabel('Date', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Volume Chart', fontweight='bold')
        
        # Format volume x-axis
        if len(dates) > 20:
            ax2.set_xticks(range(0, len(dates), step))
            ax2.set_xticklabels([dates[i].strftime('%m/%d') for i in range(0, len(dates), step)], rotation=45)
        else:
            ax2.set_xticks(range(len(dates)))
            ax2.set_xticklabels([date.strftime('%m/%d') for date in dates], rotation=45)
        
        # Add statistics text box
        stats_text = f"""
Statistics:
Open: ${opens[0]:.2f}
Close: ${closes[-1]:.2f}
High: ${max(highs):.2f}
Low: ${min(lows):.2f}
Change: ${closes[-1] - opens[0]:.2f} ({((closes[-1] - opens[0]) / opens[0] * 100):.2f}%)
Volume: {sum(volumes):,.0f}
        """
        
        # Position the text box
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"Error creating K-diagram: {e}")
        plt.close()
        return False

def save_stock_to_excel(stock_symbol, all_data, company_name):
    """
    Save stock data to Excel file named by stock symbol
    """
    if not all_data:
        print("No data to save")
        return
    
    # Create filename based on market and symbol
    market = all_data[list(all_data.keys())[0]]['market']
    if market == 'HK':
        # For HK stocks, use the 4-digit number
        stock_no = stock_symbol.replace('.HK', '').zfill(4)
        filename = f"{stock_no}_stock_data.xlsx"
    else:
        # For US stocks, use the symbol directly
        clean_symbol = stock_symbol.replace('.', '_')
        filename = f"{clean_symbol}_stock_data.xlsx"
    
    try:
        # Create Excel writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Create summary sheet
            summary_data = []
            for period, data in all_data.items():
                summary_data.append({
                    'Market': data['market'],
                    'Symbol': data['symbol'],
                    'Company Name': data['company_name'],
                    'Period (Days)': period,
                    'Start Date': data['start_date'],
                    'End Date': data['end_date'],
                    'Open Price': data['open_price'],
                    'Close Price': data['close_price'],
                    'High Price': data['high_price'],
                    'Low Price': data['low_price'],
                    'Volume': data['volume'],
                    'Avg Volume': data['avg_volume'],
                    'Price Change': data['price_change'],
                    'Price Change %': data['price_change_pct'],
                    'Volatility': data['volatility'],
                    'Timestamp': data['timestamp']
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create detailed sheets for each period and generate K-diagrams
            for period, data in all_data.items():
                # Get detailed daily data for this period
                stock = yf.Ticker(data['symbol'])
                daily_data = stock.history(period=f"{period}d")
                
                if not daily_data.empty:
                    # Prepare daily data
                    daily_df = daily_data.reset_index()
                    daily_df['Date'] = daily_df['Date'].dt.strftime('%Y-%m-%d')
                    daily_df = daily_df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                    daily_df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                    
                    # Add percentage change column
                    daily_df['Daily Change %'] = daily_df['Close'].pct_change() * 100
                    
                    daily_df.to_excel(writer, sheet_name=f'{period} Days', index=False)
                    
                    # Create K-diagram for this period
                    chart_filename = f"{stock_symbol.replace('.', '_')}_{period}d_k_diagram.png"
                    if create_k_diagram(daily_data, data['symbol'], data['company_name'], period, chart_filename):
                        print(f"✓ Generated K-diagram: {chart_filename}")
                    else:
                        print(f"✗ Failed to generate K-diagram for {period} days")
            
            # Auto-adjust column widths
            workbook = writer.book
            for sheet_name in workbook.sheetnames:
                worksheet = workbook[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
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
        
        print(f"✓ Data saved to {filename}")
        print(f"  File location: {os.path.abspath(filename)}")
        
    except Exception as e:
        print(f"Error saving to Excel: {e}")

def update_all_stock_prices_multi_period(filename="stock_detailed_prices.xlsx"):
    """Update all existing stock prices in the Excel file with multi-period data"""
    if not os.path.exists(filename):
        print("No Excel file found. Please add some stocks first.")
        return
    
    try:
        df = pd.read_excel(filename, sheet_name='Sheet1')
        if df.empty:
            print("No stocks found in the Excel file.")
            return
        
        print(f"Updating multi-period prices for {len(df)} stocks...")
        updated_count = 0
        
        for index, row in df.iterrows():
            # Handle both HK and US stocks
            if 'Stock Number' in df.columns:
                # HK stock format
                stock_no = str(row['Stock Number']).zfill(4)
                symbol = f"{stock_no}.HK"
            elif 'Symbol' in df.columns:
                # US stock format
                symbol = str(row['Symbol'])
            else:
                print("Unknown column format in Excel file")
                continue
            
            try:
                all_data, company_name = get_stock_detailed_prices_multi_period(symbol)
                if all_data:
                    # Save individual stock file
                    save_stock_to_excel(symbol, all_data, company_name)
                    updated_count += 1
                    print(f"✓ Updated {symbol} ({company_name})")
                else:
                    print(f"✗ Failed to update {symbol}")
            except Exception as e:
                print(f"✗ Error updating {symbol}: {str(e)}")
        
        print(f"\nUpdate complete! Successfully updated {updated_count} out of {len(df)} stocks.")
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")

def display_stock_summary(filename="stock_detailed_prices.xlsx"):
    """Display a summary of all stocks in the Excel file"""
    if not os.path.exists(filename):
        print("No Excel file found.")
        return
    
    try:
        df = pd.read_excel(filename, sheet_name='Sheet1')
        if df.empty:
            print("No stocks found in the Excel file.")
            return
        
        print("\n" + "="*100)
        print("STOCK PRICE SUMMARY")
        print("="*100)
        print(f"{'Market':<6} {'Symbol':<10} {'Company':<25} {'Open':<8} {'Close':<8} {'High':<8} {'Low':<8} {'Change%':<8}")
        print("-"*100)
        
        for _, row in df.iterrows():
            # Handle both HK and US stocks
            if 'Stock Number' in df.columns:
                # HK stock format
                stock_no = str(row['Stock Number']).zfill(4)
                symbol = f"{stock_no}.HK"
                market = "HK"
            elif 'Symbol' in df.columns:
                # US stock format
                symbol = str(row['Symbol'])
                market = "US"
            else:
                continue
            
            company = str(row.get('Company Name', ''))[:23]  # Truncate long names
            open_price = f"{row.get('Open', 0):.2f}" if pd.notna(row.get('Open')) else "N/A"
            close_price = f"{row.get('Close', 0):.2f}" if pd.notna(row.get('Close')) else "N/A"
            high_price = f"{row.get('High', 0):.2f}" if pd.notna(row.get('High')) else "N/A"
            low_price = f"{row.get('Low', 0):.2f}" if pd.notna(row.get('Low')) else "N/A"
            change_pct = f"{row.get('Change %', 0):.2f}%" if pd.notna(row.get('Change %')) else "N/A"
            
            print(f"{market:<6} {symbol:<10} {company:<25} {open_price:<8} {close_price:<8} {high_price:<8} {low_price:<8} {change_pct:<8}")
        
        print("="*100)
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")

if __name__ == "__main__":
    print("Stock Multi-Period Detailed Price Tracker")
    print("=" * 60)
    print("Supports both Hong Kong and US stocks")
    print("Gets stock data for 10, 50, 100, and 200 days periods")
    print("Saves each stock to individual Excel files")
    print("=" * 60)
    print("\nStock Symbol Formats:")
    print("- Hong Kong: 5, 23, 123, 0005, 5.HK, 0005.HK")
    print("- US: AAPL, MSFT, GOOGL, TSLA, etc.")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Enter stock symbol (HK: 5, 0005, 5.HK | US: AAPL, MSFT, etc.)")
        print("2. Type 'all' to update all existing stocks")
        print("3. Type 'summary' to display current stock summary")
        print("4. Type 'quit' to exit")
        
        user_input = input("\nEnter your choice: ").strip()
        
        if user_input.lower() == 'quit':
            print("Exiting program.")
            break
        
        if user_input.lower() == 'all':
            update_all_stock_prices_multi_period()
            continue
        
        if user_input.lower() == 'summary':
            display_stock_summary()
            continue
        
        # Handle stock symbol input
        symbol = user_input.upper()
        
        # Validate input
        if not symbol:
            print("Invalid input. Please enter a valid stock symbol.")
            continue
        
        print(f"\nGetting multi-period data for {symbol}...")
        all_data, company_name = get_stock_detailed_prices_multi_period(symbol)
        
        if all_data:
            save_stock_to_excel(symbol, all_data, company_name)
        else:
            print(f"No data available for {symbol}") 