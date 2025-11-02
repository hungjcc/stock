import pypyodbc
import csv
import os
from datetime import datetime
from credential import username, password, server, database

# Connection string (ODBC Driver 18)
conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"


def export_history_to_csv(filename='stock_price_history.csv', market_type=None, symbol=None):
    """Export StockPriceHistory to CSV. Optionally filter by market_type (HK/US) or symbol.

    filename: output CSV file path
    market_type: 'HK' or 'US' or None
    symbol: stock symbol (e.g., 'AAPL' or '0005') or None
    """
    try:
        conn = pypyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Build query
        base_query = "SELECT ID, StockNumber, Symbol, CompanyName, Price, Timestamp, MarketType FROM StockPriceHistory"
        params = []
        where_clauses = []
        if market_type:
            where_clauses.append("MarketType = ?")
            params.append(market_type)
        if symbol:
            where_clauses.append("Symbol = ?")
            params.append(symbol)

        if where_clauses:
            query = base_query + " WHERE " + " AND ".join(where_clauses) + " ORDER BY Timestamp ASC"
        else:
            query = base_query + " ORDER BY Timestamp ASC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        if not rows:
            print("No records found for the given filters. Nothing to export.")
            return False

        # Use cursor.description to get column names
        col_names = [desc[0] for desc in cursor.description]

        # Ensure directory exists
        out_dir = os.path.dirname(os.path.abspath(filename))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # Write CSV (utf-8-sig so Excel recognizes utf-8)
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(col_names)

            for row in rows:
                # Convert each row item to a CSV-friendly representation
                row_out = []
                for val in row:
                    # Handle datetime
                    if isinstance(val, datetime):
                        row_out.append(val.strftime("%Y-%m-%d %H:%M:%S"))
                    # pypyodbc may return decimal.Decimal for Price
                    else:
                        row_out.append(val)
                writer.writerow(row_out)

        print(f"Exported {len(rows)} records to '{filename}'.")
        return True

    except Exception as e:
        print(f"Error exporting history to CSV: {e}")
        return False

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


if __name__ == '__main__':
    print("Export Stock Price History to CSV")
    print("Leave filters blank to export all records.")
    market = input("Enter market type to filter (HK/US) or press Enter for all: ").strip().upper()
    if market == '':
        market = None
    elif market not in ('HK', 'US'):
        print("Invalid market type. Use 'HK' or 'US'.")
        raise SystemExit(1)

    symbol = input("Enter symbol to filter (AAPL or 0005) or press Enter for all: ").strip().upper()
    if symbol == '':
        symbol = None
    else:
        # keep HK symbols as zero-padded 4 digits if user provided a number
        if market == 'HK' and symbol.isdigit():
            symbol = symbol.zfill(4)

    default_file = 'stock_price_history.csv'
    filename = input(f"Enter output CSV filename (default: {default_file}): ").strip()
    if filename == '':
        filename = default_file

    ok = export_history_to_csv(filename=filename, market_type=market, symbol=symbol)
    if ok:
        print("Done.")
    else:
        print("No file created.")
