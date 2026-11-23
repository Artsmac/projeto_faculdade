from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from config import SECRET_KEY
from db import consultar, executar

app = Flask(__name__)
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
        email_digitado = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        resultado = consultar(
            "SELECT id_usuario, nome, senha, perfil_acesso "
            "FROM tb_usuarios WHERE email = %s",
            (email_digitado,),
        )
        if resultado and check_password_hash(resultado[0]["senha"], senha):
            usuario = resultado[0]
            session.clear()
            session["id_usuario"] = usuario["id_usuario"]
            session["nome"] = usuario["nome"]
            session["perfil"] = usuario["perfil_acesso"]
            return redirect(url_for("produtos"))
        flash("E-mail ou senha inválidos.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -- produtos (RF01 e RF05)

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
    dados = {}
    if request.method == "POST":
        dados = request.form
        erros = []

        sku = dados.get("sku", "").strip()
        if not sku:
            erros.append("Informe o código SKU do produto.")
        else:
            existente = consultar(
                "SELECT id_produto FROM tb_produtos WHERE sku = %s",
                (sku,),
            )
            if existente:
                erros.append("Já existe um produto cadastrado com este SKU.")

        nome = dados.get("nome", "").strip()
        if not nome:
            erros.append("Informe o nome do produto.")

        categoria = dados.get("categoria", "").strip() or None
        localizacao = dados.get("localizacao", "").strip() or None
        unidade_medida = dados.get("unidade_medida", "un").strip() or "un"
        data_validade = dados.get("data_validade", "").strip() or None

        try:
            preco_custo = Decimal(dados.get("preco_custo", "").replace(",", "."))
            if preco_custo < 0:
                erros.append("O preço de custo não pode ser negativo.")
        except InvalidOperation:
            erros.append("Preço de custo inválido.")

        try:
            preco_venda = Decimal(dados.get("preco_venda", "").replace(",", "."))
            if preco_venda < 0:
                erros.append("O preço de venda não pode ser negativo.")
        except InvalidOperation:
            erros.append("Preço de venda inválido.")

        try:
            estoque_atual = int(dados.get("estoque_atual", "0"))
            if estoque_atual < 0:
                erros.append("O estoque inicial não pode ser negativo.")
        except ValueError:
            erros.append("Estoque inicial inválido.")

        try:
            estoque_minimo = int(dados.get("estoque_minimo", "0"))
            if estoque_minimo < 0:
                erros.append("O estoque mínimo não pode ser negativo.")
        except ValueError:
            erros.append("Estoque mínimo inválido.")

        if erros:
            for erro in erros:
                flash(erro)
        else:
            executar(
                """
                INSERT INTO tb_produtos
                (sku, nome, categoria, localizacao, unidade_medida,
                 preco_custo, preco_venda, estoque_atual, estoque_minimo, data_validade)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

    return render_template("produto_form.html", dados=dados)


# -- entradas e saídas (RF02, RF03 e RN01)

@app.route("/entradas", methods=["GET", "POST"])
@perfil_requerido("ESTOQUISTA", "GERENTE")
def entradas():
    if request.method == "POST":
        id_produto = request.form.get("id_produto", "").strip()
        numero_lote_nf = request.form.get("numero_lote_nf", "").strip() or None
        motivo = request.form.get("motivo", "").strip() or "Compra / Reposição"

        try:
            quantidade = int(request.form.get("quantidade", "0"))
        except ValueError:
            quantidade = 0

        if not id_produto or quantidade <= 0:
            flash("Selecione um produto e informe uma quantidade maior que zero.")
        else:
            executar(
                """
                INSERT INTO tb_entradas (id_produto, id_usuario, quantidade, numero_lote_nf, motivo)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (id_produto, session["id_usuario"], quantidade, numero_lote_nf, motivo),
            )
            executar(
                "UPDATE tb_produtos SET estoque_atual = estoque_atual + %s WHERE id_produto = %s",
                (quantidade, id_produto),
            )
            flash("Entrada registrada e saldo atualizado com sucesso.")
            return redirect(url_for("entradas"))

    produtos_lista = consultar(
        "SELECT id_produto, sku, nome, estoque_atual, unidade_medida FROM tb_produtos ORDER BY nome"
    )
    historico = consultar(
        """
        SELECT
            e.data_hora,
            p.sku,
            p.nome AS produto,
            p.unidade_medida,
            e.quantidade,
            e.numero_lote_nf,
            e.motivo,
            u.nome AS usuario
        FROM tb_entradas e
        JOIN tb_produtos p ON p.id_produto = e.id_produto
        JOIN tb_usuarios u ON u.id_usuario = e.id_usuario
        ORDER BY e.data_hora DESC
        LIMIT 20
        """
    )
    return render_template("entradas.html", produtos=produtos_lista, historico=historico)


@app.route("/saidas", methods=["GET", "POST"])
@perfil_requerido("ESTOQUISTA", "GERENTE")
def saidas():
    if request.method == "POST":
        id_produto = request.form.get("id_produto", "").strip()
        motivo = request.form.get("motivo", "").strip()

        try:
            quantidade = int(request.form.get("quantidade", "0"))
        except ValueError:
            quantidade = 0

        if not id_produto or quantidade <= 0:
            flash("Selecione um produto e informe uma quantidade maior que zero.")
        elif not motivo:
            flash("Informe o motivo da saída (ex: Venda balcão, consumo interno ou perda).")
        else:
            produto = consultar(
                "SELECT nome, estoque_atual, unidade_medida FROM tb_produtos WHERE id_produto = %s",
                (id_produto,),
            )
            if not produto:
                flash("Produto não encontrado.")
            elif quantidade > produto[0]["estoque_atual"]:
                flash(
                    f"Bloqueado (RN01): Saldo insuficiente para '{produto[0]['nome']}'. "
                    f"Disponível: {produto[0]['estoque_atual']} {produto[0]['unidade_medida']}."
                )
            else:
                executar(
                    """
                    INSERT INTO tb_saidas (id_produto, id_usuario, quantidade, motivo)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (id_produto, session["id_usuario"], quantidade, motivo),
                )
                executar(
                    "UPDATE tb_produtos SET estoque_atual = estoque_atual - %s WHERE id_produto = %s",
                    (quantidade, id_produto),
                )
                flash("Saída registrada e saldo atualizado com sucesso.")
                return redirect(url_for("saidas"))

    produtos_lista = consultar(
        "SELECT id_produto, sku, nome, estoque_atual, unidade_medida FROM tb_produtos ORDER BY nome"
    )
    historico = consultar(
        """
        SELECT
            s.data_hora,
            p.sku,
            p.nome AS produto,
            p.unidade_medida,
            s.quantidade,
            s.motivo,
            u.nome AS usuario
        FROM tb_saidas s
        JOIN tb_produtos p ON p.id_produto = s.id_produto
        JOIN tb_usuarios u ON u.id_usuario = s.id_usuario
        ORDER BY s.data_hora DESC
        LIMIT 20
        """
    )
    return render_template("saidas.html", produtos=produtos_lista, historico=historico)


# -- reposição e alertas (RF04 e RN02 - PEPS)

@app.route("/alertas")
@login_requerido
def alertas():
    estoque_baixo = consultar(
        """
        SELECT
            sku,
            nome,
            categoria,
            localizacao,
            unidade_medida,
            estoque_atual,
            estoque_minimo
        FROM tb_produtos
        WHERE estoque_atual <= estoque_minimo
        ORDER BY (estoque_atual - estoque_minimo) ASC, nome ASC
        """
    )
    validade_proxima = consultar(
        """
        SELECT
            sku,
            nome,
            categoria,
            localizacao,
            unidade_medida,
            estoque_atual,
            data_validade,
            DATEDIFF(data_validade, CURDATE()) AS dias_restantes
        FROM tb_produtos
        WHERE data_validade IS NOT NULL
          AND estoque_atual > 0
          AND data_validade <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        ORDER BY data_validade ASC
        """
    )
    return render_template(
        "alertas.html",
        estoque_baixo=estoque_baixo,
        validade_proxima=validade_proxima,
    )


# -- área gerencial e auditoria (RN03)

@app.route("/gerencial", methods=["GET", "POST"])
@perfil_requerido("GERENTE")
def gerencial():
    if request.method == "POST":
        id_produto = request.form.get("id_produto", "").strip()
        justificativa = request.form.get("justificativa", "").strip()
        senha_confirmacao = request.form.get("senha_confirmacao", "")

        try:
            quantidade_contada = int(request.form.get("quantidade_contada", "-1"))
        except ValueError:
            quantidade_contada = -1

        if not id_produto or quantidade_contada < 0:
            flash("Selecione um produto e informe uma quantidade física válida (0 ou maior).")
        elif not justificativa:
            flash("A justificativa é obrigatória para auditoria (RN03).")
        else:
            gerente = consultar(
                "SELECT senha FROM tb_usuarios WHERE id_usuario = %s",
                (session["id_usuario"],),
            )
            if not gerente or not check_password_hash(gerente[0]["senha"], senha_confirmacao):
                flash("Bloqueado (RN03): Senha do gerente incorreta.")
            else:
                executar(
                    """
                    INSERT INTO tb_ajustes_auditoria
                    (id_produto, id_gerente, quantidade_contada, justificativa)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (id_produto, session["id_usuario"], quantidade_contada, justificativa),
                )
                executar(
                    "UPDATE tb_produtos SET estoque_atual = %s WHERE id_produto = %s",
                    (quantidade_contada, id_produto),
                )
                flash("Ajuste gerencial gravado no log de auditoria e saldo atualizado.")
                return redirect(url_for("gerencial"))

    produtos_lista = consultar(
        "SELECT id_produto, sku, nome, estoque_atual, unidade_medida FROM tb_produtos ORDER BY nome"
    )
    historico = consultar(
        """
        SELECT
            a.data_hora,
            p.sku,
            p.nome AS produto,
            p.unidade_medida,
            a.quantidade_contada,
            a.justificativa,
            u.nome AS responsavel
        FROM tb_ajustes_auditoria a
        JOIN tb_produtos p ON p.id_produto = a.id_produto
        JOIN tb_usuarios u ON u.id_usuario = a.id_gerente
        ORDER BY a.data_hora DESC
        LIMIT 20
        """
    )
    return render_template("gerencial.html", produtos=produtos_lista, historico=historico)

# -- dashboard / painel geral (Encontro 6)

@app.route("/dashboard")
@login_requerido
def dashboard():
    hoje_mes = consultar("SELECT DATE_FORMAT(CURDATE(), '%Y-%m') AS mes")[0]["mes"]
    mes = request.args.get("mes", "").strip() or hoje_mes
    categoria = request.args.get("categoria", "").strip()

    categorias_rows = consultar(
        "SELECT DISTINCT categoria FROM tb_produtos "
        "WHERE categoria IS NOT NULL AND categoria <> '' ORDER BY categoria"
    )
    categorias = [r["categoria"] for r in categorias_rows]

    filtro_cat_sql = " AND p.categoria = %s" if categoria else ""
    params_mov = [mes, categoria] if categoria else [mes]

    entradas_mes = consultar(
        f"""
        SELECT COALESCE(SUM(e.quantidade), 0) AS total
        FROM tb_entradas e
        JOIN tb_produtos p ON p.id_produto = e.id_produto
        WHERE DATE_FORMAT(e.data_hora, '%Y-%m') = %s {filtro_cat_sql}
        """,
        tuple(params_mov),
    )[0]["total"]

    saidas_mes = consultar(
        f"""
        SELECT COALESCE(SUM(s.quantidade), 0) AS total
        FROM tb_saidas s
        JOIN tb_produtos p ON p.id_produto = s.id_produto
        WHERE DATE_FORMAT(s.data_hora, '%Y-%m') = %s {filtro_cat_sql}
        """,
        tuple(params_mov),
    )[0]["total"]

    filtro_prod_sql = " WHERE categoria = %s" if categoria else ""
    params_prod = (categoria,) if categoria else ()

    resumo_estoque = consultar(
        f"""
        SELECT
            COUNT(*) AS total_produtos,
            COALESCE(SUM(estoque_atual), 0) AS total_unidades,
            COALESCE(SUM(estoque_atual * preco_venda), 0) AS patrimonio_venda,
            COALESCE(SUM(estoque_atual * preco_custo), 0) AS patrimonio_custo,
            COALESCE(SUM(CASE WHEN estoque_atual <= estoque_minimo THEN 1 ELSE 0 END), 0) AS total_alertas
        FROM tb_produtos
        {filtro_prod_sql}
        """,
        params_prod,
    )[0]

    entradas_dia = consultar(
        f"""
        SELECT DATE_FORMAT(e.data_hora, '%d/%m') AS dia, DATE(e.data_hora) AS data_ord, SUM(e.quantidade) AS total
        FROM tb_entradas e
        JOIN tb_produtos p ON p.id_produto = e.id_produto
        WHERE DATE_FORMAT(e.data_hora, '%Y-%m') = %s {filtro_cat_sql}
        GROUP BY DATE(e.data_hora), DATE_FORMAT(e.data_hora, '%d/%m')
        ORDER BY data_ord ASC
        """,
        tuple(params_mov),
    )
    saidas_dia = consultar(
        f"""
        SELECT DATE_FORMAT(s.data_hora, '%d/%m') AS dia, DATE(s.data_hora) AS data_ord, SUM(s.quantidade) AS total
        FROM tb_saidas s
        JOIN tb_produtos p ON p.id_produto = s.id_produto
        WHERE DATE_FORMAT(s.data_hora, '%Y-%m') = %s {filtro_cat_sql}
        GROUP BY DATE(s.data_hora), DATE_FORMAT(s.data_hora, '%d/%m')
        ORDER BY data_ord ASC
        """,
        tuple(params_mov),
    )

    mapa_dias = {}
    for row in entradas_dia:
        mapa_dias[row["dia"]] = {"entrada": int(row["total"]), "saida": 0}
    for row in saidas_dia:
        if row["dia"] not in mapa_dias:
            mapa_dias[row["dia"]] = {"entrada": 0, "saida": int(row["total"])}
        else:
            mapa_dias[row["dia"]]["saida"] = int(row["total"])

    chart_dias = list(mapa_dias.keys())
    chart_entradas = [mapa_dias[d]["entrada"] for d in chart_dias]
    chart_saidas = [mapa_dias[d]["saida"] for d in chart_dias]

    dist_categorias = consultar(
        """
        SELECT
            COALESCE(NULLIF(categoria, ''), 'Sem categoria') AS categoria,
            COALESCE(SUM(estoque_atual), 0) AS total
        FROM tb_produtos
        GROUP BY COALESCE(NULLIF(categoria, ''), 'Sem categoria')
        ORDER BY total DESC
        """
    )
    cat_labels = [r["categoria"] for r in dist_categorias]
    cat_valores = [int(r["total"]) for r in dist_categorias]

    mais_movimentados = consultar(
        f"""
        SELECT
            p.sku,
            p.nome,
            p.categoria,
            p.unidade_medida,
            SUM(s.quantidade) AS total_saida,
            p.estoque_atual
        FROM tb_saidas s
        JOIN tb_produtos p ON p.id_produto = s.id_produto
        WHERE DATE_FORMAT(s.data_hora, '%Y-%m') = %s {filtro_cat_sql}
        GROUP BY p.id_produto, p.sku, p.nome, p.categoria, p.unidade_medida, p.estoque_atual
        ORDER BY total_saida DESC
        LIMIT 5
        """,
        tuple(params_mov),
    )

    indicadores = {
        "entradas_mes": int(entradas_mes),
        "saidas_mes": int(saidas_mes),
        "total_produtos": int(resumo_estoque["total_produtos"]),
        "total_unidades": int(resumo_estoque["total_unidades"]),
        "patrimonio_venda": float(resumo_estoque["patrimonio_venda"]),
        "patrimonio_custo": float(resumo_estoque["patrimonio_custo"]),
        "total_alertas": int(resumo_estoque["total_alertas"]),
    }

    return render_template(
        "dashboard.html",
        mes=mes,
        categoria=categoria,
        categorias=categorias,
        indicadores=indicadores,
        chart_dias=chart_dias,
        chart_entradas=chart_entradas,
        chart_saidas=chart_saidas,
        cat_labels=cat_labels,
        cat_valores=cat_valores,
        mais_movimentados=mais_movimentados,
    )

if __name__ == "__main__":
    app.run(debug=True)