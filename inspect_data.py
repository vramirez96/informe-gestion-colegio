
import sqlite3
import pandas as pd

DB_PATH = 'c:/xampp/htdocs/sicar_estadistica/siscar_estadistica'

conn = sqlite3.connect(DB_PATH)

def inspect_table(table_name, limit=5):
    print(f"\n--- {table_name} ---")
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
        print(df.to_string())
        print(df.dtypes)
    except Exception as e:
        print(f"Error reading {table_name}: {e}")

inspect_table('Pago')
inspect_table('Detalle_pago')
inspect_table('Cartera_alumnos')
inspect_table('Activa_pago')
inspect_table('Rubros')
inspect_table('TBL_Alumnos_deudores') # Checking if this is actually empty

# Check distinct years/dates in Pago
try:
    print("\n--- Fechas en Pago ---")
    df_dates = pd.read_sql_query("SELECT Fecha FROM Pago LIMIT 20", conn)
    print(df_dates)
except:
    pass

conn.close()
