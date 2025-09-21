# admin.py
from flask import Flask, request, jsonify, render_template
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, template_folder='templates')

# Configuração do banco de dados (reutilize do app.py)
DB_CONFIG = {
    "host": os.getenv('DB_HOST', 'localhost'),
    "user": os.getenv('DB_USER', 'seu_usuario'),
    "password": os.getenv('DB_PASSWORD', ''),
    "database": os.getenv('DB_NAME', 'seu_banco'),
    "charset": 'utf8mb4',
    "collation": 'utf8mb4_unicode_ci'
}


def get_db():
    """Conexão segura com o banco"""
    return mysql.connector.connect(**DB_CONFIG)


@app.route('/admin/learn')
def learn_dashboard():
    """Página principal do painel: mostra perguntas não respondidas"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, user_id, question, created_at 
            FROM unknown_questions 
            WHERE status = 'pending' 
            ORDER BY created_at DESC 
            LIMIT 50
        """)
        questions = cursor.fetchall()

        return render_template('admin_learn.html', questions=questions)

    except Exception as e:
        print(f"Erro ao carregar perguntas: {e}")
        return "<h3>Erro ao carregar dados</h3>", 500
    finally:
        cursor.close()
        conn.close()


@app.route('/admin/teach', methods=['POST'])
def teach_ednna():
    """Endpoint que adiciona nova pergunta/resposta ao knowledge_base"""
    data = request.get_json()
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    category = data.get('category', '').strip()

    if not all([question, answer, category]):
        return jsonify({"error": "Todos os campos são obrigatórios"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Gerar keywords simples a partir da resposta
        words = answer.lower().split()
        keywords = ",".join(set([w for w in words if len(w) > 4][:15])) or "geral"

        # Inserir no knowledge_base
        cursor.execute("""
            INSERT INTO knowledge_base (question, answer, category, keywords, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE answer = VALUES(answer), updated_at = NOW()
        """, (question, answer, category, keywords))

        # Marcar como respondida
        cursor.execute("""
            UPDATE unknown_questions 
            SET status = 'answered' 
            WHERE question = %s AND status = 'pending'
        """, (question,))

        conn.commit()
        return jsonify({"status": "success", "message": "Ednna aprendeu com sucesso!"})

    except Exception as e:
        conn.rollback()
        print(f"Erro ao ensinar Ednna: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(port=5001, debug=True)
