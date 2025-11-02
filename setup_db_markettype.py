import pypyodbc
from credential import username, password, server, database

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def alter_table():
    try:
        # Connect to database
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Add MarketType column if it doesn't exist
        print("Adding MarketType column...")
        cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sys.columns 
            WHERE object_id = OBJECT_ID(N'[dbo].[test-myproject-table]')
            AND name = 'MarketType'
        )
        BEGIN
            ALTER TABLE [dbo].[test-myproject-table]
            ADD MarketType NVARCHAR(10)
        END
        """)
        
        # Add Symbol column if it doesn't exist
        print("Adding Symbol column...")
        cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sys.columns 
            WHERE object_id = OBJECT_ID(N'[dbo].[test-myproject-table]')
            AND name = 'Symbol'
        )
        BEGIN
            ALTER TABLE [dbo].[test-myproject-table]
            ADD Symbol NVARCHAR(20)
        END
        """)
        
        # Modify CompanyName to be longer
        print("Modifying CompanyName column...")
        cursor.execute("""
        ALTER TABLE [dbo].[test-myproject-table]
        ALTER COLUMN CompanyName NVARCHAR(255)
        """)
        
        # Modify Price to be decimal
        print("Modifying Price column...")
        cursor.execute("""
        ALTER TABLE [dbo].[test-myproject-table]
        ALTER COLUMN Price DECIMAL(18,2)
        """)
        
        conn.commit()
        print("Table structure updated successfully!")
        
    except Exception as e:
        print(f"Error modifying table: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    alter_table()