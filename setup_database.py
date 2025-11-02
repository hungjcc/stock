import pypyodbc
from credential import username, password, server, database

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def setup_database():
    try:
        # Connect to database
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Create StockPrices table if it doesn't exist
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'StockPrices')
        BEGIN
            CREATE TABLE StockPrices (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                CompanyName NVARCHAR(255),
                StockNumber NVARCHAR(20),
                Price DECIMAL(18,2),
                Timestamp DATETIME,
                MarketType NVARCHAR(10)
            )
        END
        """)
        
        # Create index on StockNumber and MarketType
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_StockPrices_StockNumber_MarketType')
        BEGIN
            CREATE INDEX IX_StockPrices_StockNumber_MarketType 
            ON StockPrices(StockNumber, MarketType)
        END
        """)
        
        conn.commit()
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_database()