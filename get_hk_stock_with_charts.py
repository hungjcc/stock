import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import mplfinance as mpf
import warnings
warnings.filterwarnings('ignore')

def get_stock_data_multi_period(symbol, periods=[10, 50, 100, 200]):
    """Get stock data for multiple periods"""
    stock = yf.Ticker(symbol)
    info = stock.info
    company_name = info.get('shortName', '')
    
    all_data = {}
    
    for period in periods:
        try:
            data = stock.history(period=f"{period}d")
            
            if not data.empty:
                latest_data = data.iloc[-1]
                first_data = data.iloc[0]
                
                period_data = {
                    'company_name': company_name,
                    'symbol': symbol,
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
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'raw_data': data
                }
                
                all_data[period] = period_data
                
                print(f"=== {period} Days Data ===")
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

def create_k_diagram(data, symbol, company_name, period):
    """Create K-diagram (candlestick chart)"""
    try:
        # Set up the chart style
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            gridstyle='',
            y_on_right=False,
            marketcolors=mpf.make_marketcolors(
                up='red',
                down='green',
                edge='inherit',
                wick='inherit',
                volume='in',
                ohlc='inherit'
            ),
            rc={'font.size': 10}
        )
        
        # Create the chart
        fig, axes = mpf.plot(
            data,
            type='candle',
            volume=True,
            style=style,
            title=f'{symbol} ({company_name}) - {period} Days K-Diagram',
            ylabel='Price (HKD)',
            ylabel_lower='Volume',
            figsize=(12, 8),
            panel_ratios=(3, 1),
            returnfig=True
        )
        
        # Save the chart
        chart_filename = f"{symbol.replace('.HK', '')}_{period}d_k_diagram.png"
        plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ K-diagram saved: {chart_filename}")
        return chart_filename
        
    except Exception as e:
        print(f"Error creating K-diagram: {e}")
        return None

def save_to_excel_with_charts(stock_no, all_data, company_name):
    """Save stock data to Excel and create K-diagrams"""
    if not all_data:
        print("No data to save")
        return
    
    filename = f"{stock_no.zfill(4)}_stock_data.xlsx"
    
    try:
        # Create Excel file
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Summary sheet
            summary_data = []
            for period, data in all_data.items():
                summary_data.append({
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
            
            # Detailed sheets for each period
            for period, data in all_data.items():
                daily_data = data['raw_data']
                if not daily_data.empty:
                    daily_df = daily_data.reset_index()
                    daily_df['Date'] = daily_df['Date'].dt.strftime('%Y-%m-%d')
                    daily_df = daily_df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                    daily_df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                    daily_df['Daily Change %'] = daily_df['Close'].pct_change() * 100
                    daily_df.to_excel(writer, sheet_name=f'{period} Days', index=False)
        
        print(f"✓ Excel data saved to {filename}")
        
        # Create K-diagrams
        print("\nCreating K-diagrams...")
        charts_created = []
        
        for period, data in all_data.items():
            if 'raw_data' in data and not data['raw_data'].empty:
                chart_filename = create_k_diagram(
                    data['raw_data'], 
                    data['symbol'], 
                    company_name, 
                    period
                )
                if chart_filename:
                    charts_created.append(chart_filename)
        
        if charts_created:
            print(f"✓ Created {len(charts_created)} K-diagram(s):")
            for chart in charts_created:
                print(f"  - {chart}")
        
        return filename
        
    except Exception as e:
        print(f"Error saving data: {e}")
        return None

def main():
    print("Hong Kong Stock Multi-Period Tracker with K-Diagrams")
    print("=" * 60)
    print("Gets stock data for 10, 50, 100, and 200 days periods")
    print("Creates Excel files and K-diagram charts")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Enter stock number (e.g., 5, 23, 123, 0005)")
        print("2. Type 'quit' to exit")
        
        user_input = input("\nEnter your choice: ").strip()
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        
        if not user_input.isdigit() or not (1 <= len(user_input) <= 4):
            print("Invalid input. Please enter 1-4 digits for stock number or 'quit' to exit.")
            continue
        
        stock_no_padded = user_input.zfill(4)
        symbol = f"{stock_no_padded}.HK"
        
        print(f"\nGetting multi-period data for {symbol}...")
        all_data, company_name = get_stock_data_multi_period(symbol)
        
        if all_data:
            save_to_excel_with_charts(stock_no_padded, all_data, company_name)
        else:
            print(f"No data available for {symbol}")

if __name__ == "__main__":
    main() 