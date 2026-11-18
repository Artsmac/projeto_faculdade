-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS STOCKFLOW_db;
USE STOCKFLOW_db;

--Tabela de usuarios
CREATE TABLE IF NOT EXISTS tb_usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY, (INT, Chave Primary,AUTO_INCREMENT),
Identificador único do usuario;
    nome VARCHAR(100) NOT NULL, NOME DO OPERADOR;
    email VARCHAR(100) NOT NULL UNIQUE, E-MAIL CORPORATIVO UTILIZADO PARA AUTENTICAÇÃO;
    perfil_acesso ENUM( 'Estoquista', 'Vendedor', 'Gerente') NOT NULL, 
(Nivel de autenticação);
) ENGINE=InnoDB;

--Tabela de produtos 
CREATE TABLE IF NOT EXISTS tb_produtos (
    id_produto INT AUTO_INCREMENT PRIMARY KEY, (Chave Primary, Auto ALTO_INCREMENT) 
    sku VARCHAR(50) NOT NULL UNIQUE, Código SKU ou código de barras de identificação rápida;
    nome VARCHAR(150) NOT NULL, Descrição comercial completa do produto;
    categoria VARCHAR(50), Agrupamento do produto (Mercearia, Bebidas, Limpeza);
    localizacao VARCHAR(50) Endereço fisico de estocagem (Corredor A Prateleira 2);
    unidade_medida VARCHAR(20) DEFAULT Unidade de estocagem 'un', 'Kg', 'L';
    perfil_custo DECIMAL(10,2) NOT NULL, Valor unitário de aquisição junto ao distribuidor;
    preco_venda DECIMAL(10,2) NOT NULL, Valor unitário praticado para comercialização;
    estoque_atual INT NOT NULL DEFAULT 0, (Quantidade física disponivel em tempo real);
    estoque_minino INT NOT NULL DEFAULT 0, (Limite de segurança para disparo de alerta de reposição);
    data_validade DATE, Data de vencimento do lote estocado(crucial para o controle PEPS);
    CONSTRAINT chk_estoque_nao_negativo CHECK (estoque_atual >=0)
) ENGINE=InnoDB;

--Tabela de entrada de estoque
CREATE TABLE IF NOT NULL EXISTS tb_entradas (
    id_entrada INT ALTO_INCREMENT PRIMARY KEY, (INT, Chave Primary, AUTO_INCREMENT),
    Código único lançado da Entrada;
    id_produto INT NOT NULL, (INT, Chave Estrangeira) REFERENCES Produto ALTO_INCREMENT,
(tb_produtos.id_produto);
    quantidade INT NOT NULL, Quantidade de unidades recebidas;
    numero_lote_nf VARCHAR(50), Identificador do lote ou da Nota Fiscal de aquisição;
    motivo VARCHAR(255), Descrição da origem(compra de distribuidora);
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP, (Carimbo de data e data_hora do registro);
    FOREIGN KEY (id_produto) REFERENCES tb_produtos(id_produto),
    FOREIGN KEY (id_usuario) REFERENCES td_usuarios(id_usuario)
) ENGINE=InnoDB;

--Tabela de saida de estoque
CREATE TABLE IF NOT NULL EXISTS tb_saidas (
    id_saida INT AUTO_INCRENENT PRIMARY KEY, (INT, Chave Primary, Auto ALTO_INCREMENT) Código
único do lançamento de saída;
    id_produto INT NOT NULL, (INT, Chave Estrangeira) REFERENCES ao produto baixado,
(tb_produtos.id_produto);
    id_usuario INT NOT NULL, (INT, Chave Estrangeira) REFERENCES ao operador expedidor,
(tb_usuarios.ib_usuario);
    quantidade INT NOT NULL, QUANTIDADE DE UNIDADES RETIRADAS;
    motivo VARCHAR(255) NOT NULL, Justificativa da saída (venda balcão, avaria, consumo interno);
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP, Carimbo de data_hora da expedição;
    FOREIGN KEY (id_produto) REFERENCES tb_produtos(id_produto),
    FOREIGN KEY (id_usuario) REFERENCES tb_usuarios(id_usuario)
) ENGINE=InnoDB;

--Tabela de ajuste
CREATE TABLE IF NOT NULL EXISTS id_ajustes_auditoria (
    id_ajustes INT AUTO_INCREMENT PRIMARY KEY, Código de ajuste de id_ajustes_auditoria;
    id_produto INT NOT NULL, (INT Chave Estrangeira) REFERENCES AO id_produto corrigido;
    id_gerente INT NOT NULL, (INT Chave Estrangeira) REFERENCES ao perfil gerente autorizador;
    quantidade_contada INT NOT NULL, Nova contagem fisica apurada na prateleira;
    justificativa TEXT NOT NULL, Texto explicativo obrigatório sobre a discrepância encontrada;
    data_hora DATETIME DEFAULT CURRENT_ TIMESTAMP, Carimbo de data_hora do ajuste.
    FOREIGN KEY (id_produto) REFERENCES id_produtos(id_produto),
    FOREIGN KEY (id_gerente) REFERENCES id_usuarios(id_usuario)
) ENGINE=InnoDB;
