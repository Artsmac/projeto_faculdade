import mysql.connector
from config import DB_CONFIG

try:
    conexao = mysql.connector.connect(**DB_CONFIG)
    cursor = conexao.cursor()

    print(f"Conexão estabelecida com sucesso ao banco '{DB_CONFIG['database']}'!")

    cursor.executer("SHOW TABLES")
    tabelas = [linha[0] for linha in cursor.fetchall()]
    print("Tabelas encontradas:", ", ".join(tabelas))

    cursor.execute("SELECT sku, nome, estoque_atual FROM tb_produtos")
    produtos = cursor.fetchall()

    if produtos:
        for sku, nome, estoque_atual in produtos:
            print(f"- [{sku}] {nome}: {estoque_atual} un")
    else:
        print("Tabela 'tb_produtos' conectada (0 produtos cadastrados no momento).")
except mysql.connector.Error as erro:
    print("Erro ao conectar ao MySQL:", erro)

finally:
    if "cursor" in locals() and cursor:
        cursor.close()
    if "conexao" in locals() and conexao.is_connected():
        conexao.close()
