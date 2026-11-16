import mysql.connector

conexao = mysql.connector.connect(
    host="localhost",
    port=3307,
    user="root",
    password="",
    database="controle_estoque",
)
cursor = conexao.cursor()
cursor.execute("SELECT nome, saldo FROM vw_saldo_produto")
for nome, saldo in cursor.fetchall():
    print(nome, saldo)
conexao.close()