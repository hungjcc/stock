import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import os

def calculate_technical_indicators(df):
    """Calculate various technical indicators"""
    # Moving averages
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    
    # MACD
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df

def create_enhanced_candlestick_chart():
    """Create an enhanced candlestick chart with technical indicators"""
    
    print("=" * 60)
    print("Enhanced Candlestick Chart Generator")
    print("=" * 60)
    
    # Get user input
    file_name = input("Enter Excel file name (e.g., TSLA_stock_data.xlsx): ").strip()
    
    if not file_name:
        print("No file name provided. Exiting.")
        return
    
    # Check if file exists
    if not os.path.exists(file_name):
        print(f"Error: File '{file_name}' not found.")
        return
    
    try:
        # Read data from Excel
        df = pd.read_excel(file_name, sheet_name='Summary')
        
        # Try to get stock symbol from different possible column names
        symbol = None
        company_name = 'Unknown'
        
        # Debug: Show Summary sheet columns
        print(f"Summary sheet columns: {list(df.columns)}")
        
        # Check for different possible column names
        symbol_columns = ['Symbol', 'Stock Symbol', 'Ticker']
        company_columns = ['Company Name', 'Company', 'Name']
        
        for col in symbol_columns:
            if col in df.columns and not df.empty:
                symbol = df.iloc[0][col]
                print(f"Found symbol '{symbol}' in column '{col}'")
                break
        
        for col in company_columns:
            if col in df.columns and not df.empty:
                company_name = df.iloc[0][col]
                print(f"Found company name '{company_name}' in column '{col}'")
                break
        
        # If still no symbol found, try to extract from filename
        if symbol is None:
            # Extract symbol from filename (e.g., "0002_stock_data.xlsx" -> "0002")
            base_name = os.path.splitext(os.path.basename(file_name))[0]
            if '_stock_data' in base_name:
                symbol = base_name.replace('_stock_data', '')
                # Add .HK suffix if it looks like a HK stock number
                if symbol.isdigit() and len(symbol) <= 4:
                    symbol = f"{symbol.zfill(4)}.HK"
            else:
                symbol = base_name
            print(f"Extracted symbol '{symbol}' from filename")
        
        if symbol is None:
            print("Error: Could not determine stock symbol from Summary sheet or filename.")
            return
        
        print(f"Processing: {symbol} - {company_name}")
        
        # Debug: Show available sheets
        try:
            excel_file = pd.ExcelFile(file_name)
            print(f"Available sheets: {excel_file.sheet_names}")
        except Exception as e:
            print(f"Warning: Could not read sheet names: {e}")
        
        # Read detailed data from the longest period available
        periods = ['200 Days', '100 Days', '50 Days', '10 Days']
        detailed_data = None
        
        for period in periods:
            try:
                detailed_data = pd.read_excel(file_name, sheet_name=period)
                print(f"Using {period} data for chart generation")
                break
            except Exception as e:
                print(f"Could not read {period} sheet: {e}")
                continue
        
        if detailed_data is None:
            print("Error: No detailed data sheets found.")
            print("Trying to find any sheet with required columns...")
            
            # Try to find any sheet with the required columns
            try:
                excel_file = pd.ExcelFile(file_name)
                for sheet_name in excel_file.sheet_names:
                    if sheet_name != 'Summary':
                        try:
                            test_data = pd.read_excel(file_name, sheet_name=sheet_name)
                            required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                            if all(col in test_data.columns for col in required_columns):
                                detailed_data = test_data
                                print(f"Found data in sheet: {sheet_name}")
                                break
                        except:
                            continue
            except:
                pass
            
            if detailed_data is None:
                print("Error: No suitable data sheets found.")
                return
        
        # Check required columns
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in detailed_data.columns for col in required_columns):
            print("Error: The sheet must contain these columns:", required_columns)
            return
        
        # Convert Date column to datetime
        detailed_data['Date'] = pd.to_datetime(detailed_data['Date'])
        detailed_data = detailed_data.sort_values('Date')
        
        # Calculate technical indicators
        detailed_data = calculate_technical_indicators(detailed_data)
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('Price & Volume', 'MACD', 'RSI')
        )
        
        # Color scheme
        colors = ['red' if close < open else 'green' 
                 for open, close in zip(detailed_data['Open'], detailed_data['Close'])]
        
        # 1. Candlestick chart with moving averages
        fig.add_trace(go.Candlestick(
            x=detailed_data['Date'],
            open=detailed_data['Open'],
            high=detailed_data['High'],
            low=detailed_data['Low'],
            close=detailed_data['Close'],
            name='Price',
            increasing_line_color='#26A69A',
            decreasing_line_color='#EF5350'
        ), row=1, col=1)
        
        # Add moving averages
        for ma, color in [('MA5', 'blue'), ('MA10', 'orange'), ('MA20', 'purple'), ('MA50', 'brown')]:
            if ma in detailed_data.columns:
                fig.add_trace(go.Scatter(
                    x=detailed_data['Date'],
                    y=detailed_data[ma],
                    mode='lines',
                    name=ma,
                    line=dict(color=color, width=1),
                    opacity=0.7
                ), row=1, col=1)
        
        # Add Bollinger Bands
        if 'BB_Upper' in detailed_data.columns:
            fig.add_trace(go.Scatter(
                x=detailed_data['Date'],
                y=detailed_data['BB_Upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='rgba(0,0,255,0.3)', width=1),
                fill=None
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=detailed_data['Date'],
                y=detailed_data['BB_Lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='rgba(0,0,255,0.3)', width=1),
                fill='tonexty',
                fillcolor='rgba(0,0,255,0.1)'
            ), row=1, col=1)
        
        # Add volume bars
        fig.add_trace(go.Bar(
            x=detailed_data['Date'],
            y=detailed_data['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.6
        ), row=1, col=1)
        
        # 2. MACD
        if 'MACD' in detailed_data.columns:
            fig.add_trace(go.Scatter(
                x=detailed_data['Date'],
                y=detailed_data['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color='blue', width=2)
            ), row=2, col=1)
            
            fig.add_trace(go.Scatter(
                x=detailed_data['Date'],
                y=detailed_data['MACD_Signal'],
                mode='lines',
                name='MACD Signal',
                line=dict(color='red', width=2)
            ), row=2, col=1)
            
            # MACD Histogram
            colors_macd = ['green' if val >= 0 else 'red' for val in detailed_data['MACD_Histogram']]
            fig.add_trace(go.Bar(
                x=detailed_data['Date'],
                y=detailed_data['MACD_Histogram'],
                name='MACD Histogram',
                marker_color=colors_macd,
                opacity=0.6
            ), row=2, col=1)
        
        # 3. RSI
        if 'RSI' in detailed_data.columns:
            fig.add_trace(go.Scatter(
                x=detailed_data['Date'],
                y=detailed_data['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ), row=3, col=1)
            
            # Add RSI overbought/oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", row=3, col=1)
        
        # Calculate statistics
        price_change = detailed_data['Close'].iloc[-1] - detailed_data['Close'].iloc[0]
        price_change_pct = (price_change / detailed_data['Close'].iloc[0]) * 100
        total_volume = detailed_data['Volume'].sum()
        avg_volume = detailed_data['Volume'].mean()
        
        print(f"Data points: {len(detailed_data)}")
        print(f"Date range: {detailed_data['Date'].min()} to {detailed_data['Date'].max()}")
        print(f"Price range: ${detailed_data['Close'].min():.2f} to ${detailed_data['Close'].max():.2f}")
        print(f"Chart creation completed. Attempting to display...")
        
        # Customize layout
        fig.update_layout(
            title=dict(
                text=f"{symbol} - {company_name}<br>Enhanced Technical Analysis Chart",
                x=0.02,
                xanchor='left',
                font=dict(size=20, color='black')
            ),
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            height=1000,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Update axes
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        # Add annotations with statistics
        fig.add_annotation(
            x=0.02, y=0.98, xref='paper', yref='paper',
            text=f"Price Change: {price_change:.2f} ({price_change_pct:.2f}%)<br>"
                 f"Total Volume: {total_volume:,.0f}<br>"
                 f"Avg Volume: {avg_volume:,.0f}",
            showarrow=False,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=1,
            font=dict(size=10)
        )
        
        # Show the figure
        print("Displaying chart in browser...")
        fig.show(renderer="browser")
        
        # Save the chart
        chart_filename = f"{symbol.replace('.', '_')}_enhanced_chart.html"
        fig.write_html(chart_filename)
        print(f"✓ Chart saved as: {chart_filename}")
        
        print("✓ Enhanced chart generated successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_enhanced_candlestick_chart() 