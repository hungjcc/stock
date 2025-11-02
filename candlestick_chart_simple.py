import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import os

def calculate_simple_indicators(df):
    """Calculate basic technical indicators"""
    # Moving averages
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def create_simple_candlestick_chart():
    """Create a simple candlestick chart without subplots"""
    
    print("=" * 60)
    print("Simple Candlestick Chart Generator")
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
        # Try to read any sheet with data
        excel_file = pd.ExcelFile(file_name)
        print(f"Available sheets: {excel_file.sheet_names}")
        
        # Find a sheet with the required columns
        data_sheet = None
        for sheet_name in excel_file.sheet_names:
            try:
                test_data = pd.read_excel(file_name, sheet_name=sheet_name)
                required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                if all(col in test_data.columns for col in required_columns):
                    data_sheet = sheet_name
                    print(f"Found suitable data in sheet: {sheet_name}")
                    break
            except:
                continue
        
        if data_sheet is None:
            print("Error: No sheet found with required columns")
            return
        
        # Read the data
        df = pd.read_excel(file_name, sheet_name=data_sheet)
        print(f"Data shape: {df.shape}")
        
        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Calculate indicators
        df = calculate_simple_indicators(df)
        
        # Create figure
        fig = go.Figure()
        
        # Add candlestick
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#26A69A',
            decreasing_line_color='#EF5350'
        ))
        
        # Add moving averages
        if 'MA5' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['MA5'],
                mode='lines',
                name='MA5',
                line=dict(color='blue', width=1)
            ))
        
        if 'MA20' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['MA20'],
                mode='lines',
                name='MA20',
                line=dict(color='orange', width=1)
            ))
        
        # Add volume bars
        colors = ['red' if close < open else 'green' 
                 for open, close in zip(df['Open'], df['Close'])]
        
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.6,
            yaxis='y2'
        ))
        
        # Calculate statistics
        price_change = df['Close'].iloc[-1] - df['Close'].iloc[0]
        price_change_pct = (price_change / df['Close'].iloc[0]) * 100
        
        # Update layout
        fig.update_layout(
            title=f"Simple Candlestick Chart - {file_name}",
            xaxis_title='Date',
            yaxis_title='Price',
            yaxis2=dict(
                title='Volume',
                overlaying='y',
                side='right'
            ),
            height=600,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Add statistics annotation
        fig.add_annotation(
            x=0.02, y=0.98, xref='paper', yref='paper',
            text=f"Price Change: {price_change:.2f} ({price_change_pct:.2f}%)",
            showarrow=False,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=1
        )
        
        print(f"Data points: {len(df)}")
        print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"Price range: ${df['Close'].min():.2f} to ${df['Close'].max():.2f}")
        print("Displaying chart in browser...")
        
        # Show the figure
        fig.show(renderer="browser")
        
        # Save the chart
        chart_filename = f"simple_candlestick_{os.path.splitext(file_name)[0]}.html"
        fig.write_html(chart_filename)
        print(f"✓ Chart saved as: {chart_filename}")
        
        print("✓ Simple candlestick chart completed!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_simple_candlestick_chart() 