import pypyodbc
from credential import username, password, server, database

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def setup_historical_table():
    try:
        # Connect to database
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Create StockPriceHistory table if it doesn't exist
        print("Creating StockPriceHistory table...")
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'StockPriceHistory')
        BEGIN
            CREATE TABLE StockPriceHistory (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                StockNumber INT,
                Symbol NVARCHAR(20),
                CompanyName NVARCHAR(255),
                Price DECIMAL(18,2),
                Timestamp DATETIME,
                MarketType NVARCHAR(10),
                FOREIGN KEY (StockNumber) REFERENCES [test-myproject-table](StockNumber)
            )
        END
        """)
        
        # Create indexes for better query performance
        print("Creating indexes...")
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_StockPriceHistory_StockNumber')
        BEGIN
            CREATE INDEX IX_StockPriceHistory_StockNumber ON StockPriceHistory(StockNumber)
        END
        """)
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_StockPriceHistory_Symbol_MarketType')
        BEGIN
            CREATE INDEX IX_StockPriceHistory_Symbol_MarketType ON StockPriceHistory(Symbol, MarketType)
        END
        """)
        
        conn.commit()
        print("Historical table setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up historical table: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_historical_table()