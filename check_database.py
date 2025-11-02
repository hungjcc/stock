import pypyodbc
from credential import username, password, server, database

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def check_database_tables():
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Check if StockPriceHistory table exists
        print("\nChecking database tables...")
        cursor.execute("""
        SELECT CASE 
            WHEN EXISTS (
                SELECT 1 
                FROM sys.tables 
                WHERE name = 'StockPriceHistory'
            ) THEN 'Yes'
            ELSE 'No'
        END as TableExists
        """)
        
        result = cursor.fetchone()
        if result[0] == 'No':
            print("ERROR: StockPriceHistory table does not exist!")
            return
        
        # Check table structure
        print("\nTable Structure:")
        cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'StockPriceHistory'
        ORDER BY ORDINAL_POSITION
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col[0]}, Type: {col[1]}", end='')
            if col[2]:
                print(f"({col[2]})")
            else:
                print()
        
        # Check record count
        print("\nRecord Counts:")
        cursor.execute("SELECT COUNT(*) FROM StockPriceHistory")
        total_history = cursor.fetchone()[0]
        print(f"Total historical records: {total_history}")
        
        cursor.execute("""
        SELECT MarketType, COUNT(*) as Count 
        FROM StockPriceHistory 
        GROUP BY MarketType
        """)
        
        market_counts = cursor.fetchall()
        for market, count in market_counts:
            print(f"{market} market records: {count}")
        
        # Show sample data if exists
        if total_history > 0:
            print("\nSample Records (Latest 5):")
            cursor.execute("""
            SELECT TOP 5 StockNumber, Symbol, MarketType, Price, Timestamp
            FROM StockPriceHistory
            ORDER BY Timestamp DESC
            """)
            
            samples = cursor.fetchall()
            for record in samples:
                print(f"Stock: {record[1]} ({record[2]}), Price: ${record[3]:.2f}, Time: {record[4]}")
                
    except Exception as e:
        print(f"Error checking database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_database_tables()