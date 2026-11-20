import mysql.connector
from config import DB_CONFIG

def consultar(sql, params=()):
    """SELECT: Devolve uma lista de dicionarios, um por linha."""
    conexao = mysql.connector.connect(**DB_CONFIG)
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        conexao.close()

def executar(sql, params=()):
    """INSERT, UPDATE OU DELETE: grava no banco de dados e devolve o id gerado."""
    conexao = mysql.connector.connect(**DB_CONFIG)
    cursor = None
    try:
        cursor = conexao.cursor()
        cursor.execute(sql, params)
        conexao.commit()
        return cursor.lastrowid
    except Exception:
        conexao.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conexao.close()


        
    