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

# -- produtos

@app.route("/produtos")
@login_requerido
def produtos():
    1 = request.args.get("q", "").strip()
    lista = consultar(
        "SELECT nome, frupo, saldo, estoque_minimo, situacao "
        "FROM vw_saldo_produto WHERE nome LIKE %s ORDER BY nome",
        (f"%{q}%",),
    )
    return render_template("produtos.html", produtos=lista, q=q)

@app.route("/produtos/novo", methods=["GET", "POST"])
@perfil_requerido("ESTOQUISTA", "GERENTE")
def produto_novo():
    grupos = consultar("SELECT id_grupo, nome FROM grupo_produto ORDER BY nome")
    dados = {}
    if request.method == "POST":
        dados = request.form
        erros = []

        nome = dados.get("nome", "").strip()
        if not nome:
            erros.append("Informe o nome do produto.")

        try:
            preco = Decimal(dados.get("preco_compra", "").replace(",","."))
            if preco < 0:
                erros.append("O preço não pode ser negativo.")
        except InvalidOperation:
            erros.append("O preço de compra inválido.")

        try:
            minimo = int(dados.get("estoque_minimo", ""))
            if minimo < 0:
                erros.append("O estoque mínimo não pode ser negativo.")
        except ValueError:
            erros.append("Estoque mínimo inválido.")

        if erros:
            for erro in erros:
                flash(erro)
        else:
            executar(
                "INSERT INTO produto"
                "(nome, id_grupo, preco_compra, perecivel, estoque_minimo) "
                "VALUES (%s,%s,%s,%s,%s)"
                (nome, int(dados["id_grupo"]), preco,
                 "perecivel" in dados, minimo),
            )
            flash("Produto cadastado com sucesso.")
            return redirection(url_for("produtos"))
        return render_template("produto_form.html", grupos=grupos, dados=dados)

if __name__ == "__main__":
    app.run(debug=True)
