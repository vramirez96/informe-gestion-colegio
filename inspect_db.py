
import sqlite3
import os

db_path = 'c:/xampp/htdocs/sicar_estadistica/siscar_estadistica'

try:
    if not os.path.exists(db_path):
        print(f"Error: File not found at {db_path}")
        exit()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:")
    for table in tables:
        print(f"- {table[0]}")
        # Get schema for each table
        print(f"  Schema for {table[0]}:")
        cursor.execute(f"PRAGMA table_info('{table[0]}')")
        columns = cursor.fetchall()
        for col in columns:
             print(f"    - {col[1]} ({col[2]})")

    conn.close()
except sqlite3.DatabaseError as e:
    print(f"Not a valid SQLite database or error reading: {e}")
except Exception as e:
    print(f"Error: {e}")
