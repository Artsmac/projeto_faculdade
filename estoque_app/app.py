from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import FLask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from config import SECRET_KEY
from db import consultar, executar

app = Flask (__name__)
app.secret_key = SECRET_KEY
@app.route("/")
def inicio():
    return "Controle de Estoque funcionando!"
if __name__ == "__main__":
    app.run(debug=True)

# -- controle de acesso

def login_requerido(funcao):
    def decorador(funcao):
        @wraps(funcao)
        def interna(*args, **kwargs):
            if "id_usuario" not in session:
                return redirect(url_for("login"))
            if session["perfil"] not in perfis:
                flash("Seu perfil não tem permissão para esta tela.")
                return redirect(url_for("produtos"))
            return funcao(*args, **kwargs)
        return interna
    return decorador