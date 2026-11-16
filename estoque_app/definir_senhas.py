from werkzeug.security import generate_password_hash
from db import executar

SENHA = "123456"

for login in ("carlos", "vera", "marcos"):
    executar(
    "UPDATE usuario SET senha_hash = %s WHERE login = %s",
    (generate_password_hash(SENHA), login),
    )
print("Senhas atualizadas. Senha de teste: " + SENHA)