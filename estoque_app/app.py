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

# -- login

@app.route("/")
def index():
    return redirect(url_for("produtos"))
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_digitado = request.form.get("login", "").strip()
        senha = request.form.get("senha", "")
        resultado = consultar(
            "SELECT id_usuario, nome, senha_hash, perfil "
            "FROM usuario WHERE login = %s AND ativo = TRUE",
            (login_digitado,),
        )
        if resultado and check_password_hash(resultado[0]["senha_hash"], senha):
            usuario = resultado[0]
            session.clear()
            session["id_usuario"] = usuario["id_usuario"]
            session["nome"] = usuario["nome"]
            session["perfil"] = usuario["perfil"]
            return redirect(url_for("produtos"))
        flash("Login ou senha inválidos.")
    return render_template(login.html)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))