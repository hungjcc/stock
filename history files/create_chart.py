import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_candlestick_chart():
    # Get user input
    file_name = input("Enter Excel file name (e.g., TSLA_stock_data.xlsx): ")
    sheet_name = input("Enter sheet name (e.g., '10 Days' or 'Summary'): ")
    
    try:
        # Read data from Excel
        df = pd.read_excel(file_name, sheet_name=sheet_name)
        
        # Check required columns
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            print("Error: The sheet must contain these columns:", required_columns)
            return
        
        # Create subplots with shared x-axis
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05,
                           row_heights=[0.7, 0.3])
        
        # Add candlestick chart with custom colors (up=green, down=red)
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='green',    # Up day color
            decreasing_line_color='red',  # Down day color
            increasing_fillcolor='green',     # Fill color for up day
            decreasing_fillcolor='red'    # Fill color for down day
        ), row=1, col=1)
        
        # Add volume bar chart (colored by price direction)
        colors = ['green' if close > open else 'red' 
                 for close, open in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.6
        ), row=2, col=1)
        
        # Customize layout
        fig.update_layout(
            title=f"{sheet_name} Candlestick Chart (green=Up, red=Down)",
            yaxis_title=f"{file_name}",
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            plot_bgcolor='white'
        )
        
        # Customize axes
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        
        # Show the figure
        fig.show()
        
        print("Chart generated successfully!")
        
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

# Run the function
create_candlestick_chart()