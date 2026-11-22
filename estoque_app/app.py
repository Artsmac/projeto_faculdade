from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from config import SECRET_KEY
from db import consultar, executar

app = Flask (__name__)
app.secret_key = SECRET_KEY

# -- controle de acesso

def login_requerido(funcao):
    @wraps(funcao)
    def interna(*args, **kwargs):
        if "id_usuario" not in session:
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)
    return interna

def perfil_requerido(*perfis):
    def decorador(funcao):
        @wraps(funcao)
        def interna(*args, **kwargs):
            if "id_usuario" not in session:
                return redirect(url_for("login"))
            perfis_permitidos = [p.upper() for p in perfis]
            if session.get("perfil", "").upper() not in perfis_permitidos:
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
    q = request.args.get("q", "").strip()
    lista = consultar(
        """
        SELECT
            sku,
            nome,
            categoria,
            localizacao,
            unidade_medida,
            estoque_atual,
            estoque_minimo,
            data_validade,
            CASE
                WHEN estoque_atual = 0 THEN 'Sem estoque'
                WHEN estoque_atual <= estoque_minimo THEN 'Estoque baixo'
                ELSE 'Normal'
            END AS situacao
        FROM tb_produtos
        WHERE nome LIKE %s OR sku LIKE %s
        ORDER BY nome
        """,
        (f"%{q}%", f"%{q}%"),
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

        sku = dados.get("sku", "").strip()
        if not sku:
            erros.append("Informe o codigo SKU do produto.")
        else:
            existente = consultar(
                "SELECT id_produto FORM tb_produtos WHERE sku = %s"
                (sku,),
            )
            if existente:
                erros.append("Já existe um produto cadastrado com este SKU.")

        nome = dados.get("nome", "").strip()
        if not nome:
            erros.append("Informe o nome do produto.")
        categoria = dados.get("categoria", "").strip() or None
        localizacao = dados.get("localizacao", "").strip() or None
        unidade_medida = dados.get("unidade_medida", "").strip() or "un"
        data_validade = dados.get("data_validade", "").strip() or None

        try:
            preco_custo = Decimal(dados.get("preco_custo", "").replace(",", "."))
            if preco_custo < 0:
                erros.append("O preço de custo nçao pode ser negativo.")
        except InvalidOperation:
            erros.append("Preço de custo inválido.")

        try:
            preco_venda = Decimal(dados.get("preco_venda", "").replace(",", "."))
            if preco_venda < 0:
                erros.append("O preço de venda não pode ser negativo.")
        except ValueError:
            erros.append("Preço de venda inválido.")

        try:
            estoque_atual = int(dados.get("estoque_atual", "0"))
            if estoque_atual < 0:
                erros.append("O estoque inicial não pode ser negativo")
        except ValueError:
            erros.append("Estoque inicial inválido.")

        try:
            estoque_minimo = int(dados.get("estoque_minimo", "0"))
            if estoque_minimo < 0:
                erros.append("O estoque míninmo não pode ser negativo.")
        except ValueError:
            erros.append("Estoque mínimo inválido.")

        if erros:
            for erro in erros:
                flash(erro)
        else:
            executar(
                """
                INSERT INTO tb_produtos
                (sku, nome, categoria, localizacao, unidade_medida, preco_custo, preco_venda, estoque_atual, estoque_minimo, data_validade)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    sku,
                    nome,
                    categoria,
                    localizacao,
                    unidade_medida,
                    preco_custo,
                    preco_venda,
                    estoque_atual,
                    estoque_minimo,
                    data_validade,
                ),
            )
            flash("Produto cadastrado com sucesso.")
            return redirect(url_for("produtos"))
    return render_template("produto_form.html", daods=dados)
if __name == "__main__":
        app.run(debug=True)

#
#        if not dados.get("id_grupo"):
#           erros.append("Selecione um grupo de produto.")
#
#        try:
#           preco=Decimal(dados.get("preco_compra", "").replace(",", "."))
#           if preco < 0:
#               erros.append("O preço não pode ser negativo")
#       except InvalidOperation:
#           erros.append("Preço de compra inválido")
#
#       try:
#            minimo = int(dados.get("estoque_minimo", ""))
#            if minimo <0:
#                erros.append("O estoque mínimo não pode ser negativo.")
#        except ValueError:
#            erros.append("Estoque mínimo inválido.")
#
#        if erros:
#            for erro in erros:
#               flash(erro)
#        else:
#            executar(
#                "INSERT INTO produto"
#                "(nome, id_grupo, preco_compra, perecivel, estoque_minimo) "
#                "VALUES (%s,%s,%s,%s,%s)",
#                (
#                    nome,
#                    int(dados["id_grupo"]),
#                    preco,
#                    "perecivel" in dados,
#                    minimo,
#                ),
#            )
#            flash("Produto cadastrado com sucesso.")
#            return redirect(url_for("produtos"))
#
#    return render_template("produto_form.html", grupos=grupos, dados=dados)
#if __name__ == "__main__":
#    app.run(debug=True)