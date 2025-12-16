
import sqlite3
import pandas as pd
import os

DB_PATH = 'c:/xampp/htdocs/sicar_estadistica/siscar_estadistica'

def get_connection():
    """Establishes a connection to the SQLite database."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")
    return sqlite3.connect(DB_PATH)

def load_data_pagos():
    """Loads payment data joining Pago and Detalle_pago."""
    query = """
    SELECT 
        p.Num_pago,
        p.Cod_alumno,
        p.Fecha,
        d.Cod_rubro,
        d.Valor,
        r.Nom_rubro
    FROM Pago p
    JOIN Detalle_pago d ON p.Num_pago = d.Num_pago
    LEFT JOIN Rubros r ON d.Cod_rubro = r.Cod_rubro
    """
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convertir Fecha a datetime (Unix Timestamp en ms)
    df['Fecha'] = pd.to_datetime(df['Fecha'], unit='ms', errors='coerce')
    return df

def load_data_alumnos():
    """Loads student information including Course and Grade."""
    query = """
    SELECT 
        a.Cod_alumno,
        a.P_apellido_alu || ' ' || a.S_apellido_alu || ' ' || a.P_nombre_alu || ' ' || a.S_nombre_alu as Nombre_Completo,
        a.Curso as Cod_curso,
        a.Activo,
        c.Nom_curso,
        g.Nom_grado
    FROM Alumno a
    LEFT JOIN Curso c ON a.Curso = c.Cod_curso
    LEFT JOIN Grados g ON c.Grado = g.Cod_grado
    """
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def load_data_deudores():
    """Loads debt information from TBL_Alumnos_deudores."""
    # Usamos COALESCE (o IFNULL en Sqlite) para asegurar que la suma no sea NULL
    query = """
    SELECT 
        d.Cod_alumno,
        d.Nom_curso,
        d.Mes,
        COALESCE(d.Matricula, 0) + COALESCE(d.Deuda, 0) + COALESCE(d.Pension, 0) + 
        COALESCE(d.Transporte, 0) + COALESCE(d.Sistemas, 0) + COALESCE(d.Asociacion, 0) + 
        COALESCE(d.Otros, 0) + COALESCE(d.Ludicas, 0) + COALESCE(d.Mpruebas, 0) as Total_Deuda,
        COALESCE(d.Matricula, 0) as Matricula, 
        COALESCE(d.Pension, 0) as Pension, 
        COALESCE(d.Transporte, 0) as Transporte,
        COALESCE(d.Sistemas, 0) as Sistemas,
        COALESCE(d.Asociacion, 0) as Asociacion,
        COALESCE(d.Otros, 0) as Otros,
        COALESCE(d.Ludicas, 0) as Ludicas,
        COALESCE(d.Mpruebas, 0) as Mpruebas,
        COALESCE(d.Deuda, 0) as Deuda_Anterior
    FROM TBL_Alumnos_deudores d
    """
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
