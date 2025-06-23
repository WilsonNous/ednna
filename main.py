# main.py

import mysql.connector
from config import DB_CONFIG

def criar_tabelas():
    try:
        # Conectar ao banco de dados
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        cursor = conn.cursor()

        # Ler o script SQL
        with open("create_tables.sql", "r") as file:
            sql_script = file.read()

        # Executar o script SQL
        for statement in sql_script.split(";"):
            if statement.strip():
                cursor.execute(statement)

        print("Tabelas criadas com sucesso!")

    except mysql.connector.Error as err:
        print(f"Erro ao criar tabelas: {err}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    criar_tabelas()
