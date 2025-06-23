import pandas as pd
import mysql.connector
from datetime import datetime

# Configurações do banco de dados
from config import DB_CONFIG


# Função para conectar ao banco de dados
def conectar_db():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )


# Função para inserir clientes
def inserir_cliente(cursor, cliente_nome, cnpj=None, contato=None):
    cursor.execute("""
        INSERT INTO Clientes (Nome_Cliente, CNPJ, Contato)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE Nome_Cliente=VALUES(Nome_Cliente)
    """, (cliente_nome, cnpj, contato))
    return cursor.lastrowid


# Função para inserir players
def inserir_player(cursor, player_nome, tipo_player, detalhes=None):
    cursor.execute("""
        INSERT INTO Players (Nome_Player, Tipo_Player, Detalhes)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE Nome_Player=VALUES(Nome_Player)
    """, (player_nome, tipo_player, detalhes))
    return cursor.lastrowid


# Função para inserir operações
def inserir_operacao(cursor, id_cliente, id_player, tipo_operacao, descricao, status, data_cadastro):
    cursor.execute("""
        INSERT INTO Operacoes (ID_Cliente, ID_Player, Tipo_Operacao, Descricao_Problema, Status, Data_Cadastro)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (id_cliente, id_player, tipo_operacao, descricao, status, data_cadastro))
    return cursor.lastrowid


# Função para inserir chamados
def inserir_chamado(cursor, id_chamado, id_operacao, tipo_problema, estado, prioridade, assunto, autor,
                    data_inicio, data_fim, data_alterado, data_criado, observacoes):
    cursor.execute("""
        INSERT INTO Chamados_Redmine (
            ID_Chamado, ID_Operacao, Tipo_Problema, Estado, Prioridade, Assunto, Autor,
            Data_Inicio, Data_Fim, Data_Alterado, Data_Criado, Observacoes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (id_chamado, id_operacao, tipo_problema, estado, prioridade, assunto, autor, data_inicio, data_fim,
          data_alterado, data_criado, observacoes))


# Função principal para importar os dados
def importar_csv():
    # Conectar ao banco de dados
    conn = conectar_db()
    cursor = conn.cursor()

    # Ler o CSV
    df = pd.read_csv("data/issues.csv", sep=";", encoding="utf-8")

    for _, row in df.iterrows():
        # Extrair informações do CSV
        id_chamado = int(row["#"])
        projeto = row["Projeto"]
        tipo_problema = row["Tipo"]
        estado = row["Estado"]
        prioridade = row["Prioridade"]
        assunto = row["Assunto"]
        autor = row["Autor"]
        data_fim = parse_date(row["Data de fim"])
        data_inicio = parse_date(row["Data de início"])
        data_alterado = parse_datetime(row["Alterado"])
        data_criado = parse_datetime(row["Criado"])

        # Identificar cliente e player
        cliente_nome = extrair_cliente(assunto)
        player_nome, tipo_player = extrair_player(assunto)

        # Inserir cliente
        id_cliente = inserir_cliente(cursor, cliente_nome)

        # Inserir player
        id_player = inserir_player(cursor, player_nome, tipo_player)

        # Inserir operação
        tipo_operacao = mapear_tipo_operacao(tipo_problema)
        descricao = assunto
        status = "Aberto" if estado == "Aberto" else "Em Processamento"
        data_cadastro = data_inicio
        id_operacao = inserir_operacao(cursor, id_cliente, id_player, tipo_operacao, descricao, status, data_cadastro)

        # Inserir chamado
        observacoes = ""
        inserir_chamado(cursor, id_chamado, id_operacao, tipo_problema, estado, prioridade, assunto, autor,
                        data_inicio, data_fim, data_alterado, data_criado, observacoes)

    # Commit e fechar conexão
    conn.commit()
    cursor.close()
    conn.close()


# Funções auxiliares
def parse_date(date_str):
    if pd.isna(date_str) or date_str == "":
        return None
    return datetime.strptime(date_str, "%d/%m/%Y").date()


def parse_datetime(datetime_str):
    if pd.isna(datetime_str) or datetime_str == "":
        return None
    return datetime.strptime(datetime_str, "%d/%m/%Y %H:%M")


def extrair_cliente(assunto):
    # Exemplo: Extrair o nome do cliente do assunto
    partes = assunto.split(" - ")
    return partes[0].strip()


def extrair_player(assunto):
    # Exemplo: Extrair o player do assunto
    partes = assunto.split(" - ")
    player_nome = partes[1].strip() if len(partes) > 1 else "Desconhecido"
    tipo_player = "Adquirente" if "TicketLog" in player_nome or "Cielo" in player_nome else "Banco"
    return player_nome, tipo_player


def mapear_tipo_operacao(tipo_problema):
    if "Falta de Arquivo" in tipo_problema:
        return "Manutenção"
    elif "Erro de Arquivo" in tipo_problema:
        return "Manutenção"
    elif "Cancelar tráfego" in tipo_problema:
        return "Cancelamento"
    elif "Abertura Relacionamento" in tipo_problema:
        return "Abertura"
    else:
        return "Manutenção"


# Executar a importação
if __name__ == "__main__":
    importar_csv()
