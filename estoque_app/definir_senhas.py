from werkzeug.security import generate_password_hash
from db import executar

SENHA = "123456"

usuarios_teste = [
    ("Carlos Souza", "carlos.souza@empresa.com.br", "Gerente"),
    ("Vera Lima", "vera.lima@empresa.com.br", "Vendedor"),
    ("Marcos Silva", "marcos.silva@empresa.com.br", "Estoquista"),
]

senha_criptografada = generate_password_hash(SENHA)

for nome, email,perfil in usuarios_teste:
    executar(
        """
        INSERT INTO tb_usuarios(nome, email, senha, perfil_acesso)
        VALUES (%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            nome = VALUES(nome),
            senha = VALUES(senha),
            perfil_acesso = VALUES(perfil_acesso),
        """,
        (nome, email, senha_criptografada, perfil),
    )

print("Usuários e senhas configurados com sucesso")
print(f"Senha padrão para todos: {SENHA}")
for nome, emailm perfil in usuarios_teste:
    print(f"- {perfil}: {email}")
