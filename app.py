#!/usr/bin/env python3
"""
Ednna Chatbot - Netunna Software
Backend Flask com MySQL — Inteligência Contextual + Aprendizado Ativo
Deploy seguro no Render via GitHub
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging
import re
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'netunna_secret_key_2025')

# Configuração do banco de dados
DB_CONFIG = {
    "host": os.getenv('DB_HOST', 'localhost'),
    "user": os.getenv('DB_USER', 'seu_usuario'),
    "password": os.getenv('DB_PASSWORD', ''),
    "database": os.getenv('DB_NAME', 'seu_banco'),
    "port": int(os.getenv('DB_PORT', 3306)),
    "charset": 'utf8mb4',
    "collation": 'utf8mb4_unicode_ci'
}


def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Erro ao conectar ao MySQL: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    try:
        conn = get_db_connection()
        status = 'healthy' if conn and conn.is_connected() else 'degraded'
        if conn: conn.close()
        return jsonify({'status': status}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON inválido'}), 400
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400

        # Histórico de conversa
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        session['conversation_history'].append({
            'role': 'user',
            'text': user_message,
            'timestamp': str(datetime.now())
        })

        last_question = session['conversation_history'][-2]['text'] if len(session['conversation_history']) > 1 else None
        response = get_chat_response(user_message, user_id, last_question)

        session['conversation_history'].append({
            'role': 'bot',
            'text': response['response'],
            'timestamp': str(datetime.now())
        })

        return jsonify(response)
    except Exception as e:
        logger.error(f"Erro no /api/chat: {e}")
        return jsonify({'error': 'Erro interno'}), 500


# === ROTAS ADMINISTRATIVAS ===

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        correct_password = os.getenv('ADMIN_PASSWORD', 'netunna123')
        if password == correct_password:
            session['admin_logged_in'] = True
            return redirect(url_for('learn_dashboard'))
        return '<script>alert("Senha incorreta!"); window.location="/admin/login";</script>', 401
    return '''
        <html><body style="font-family:Arial;text-align:center;padding:50px;">
            <h3>🔐 Login Admin</h3>
            <form method="post" style="display:inline-block;text-align:left;">
                <input type="password" name="password" placeholder="Senha" required style="padding:10px;width:300px;"><br><br>
                <button type="submit" style="padding:10px 20px;background:#007bff;color:white;border:none;">Entrar</button>
            </form>
        </body></html>
    '''


@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    if not conn:
        return "Erro de conexão", 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM messages WHERE is_from_user = 1")
        total_respondidas = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM unknown_questions WHERE status = 'pending'")
        total_pendentes = cursor.fetchone()['total']

        cursor.execute("""
            SELECT question, COUNT(*) as count FROM unknown_questions 
            WHERE created_at > DATE_SUB(NOW(), INTERVAL 10 HOUR)
            GROUP BY question ORDER BY count DESC LIMIT 5
        """)
        frequentes = cursor.fetchall()

        return render_template('dashboard.html',
                               total_respondidas=total_respondidas,
                               total_pendentes=total_pendentes,
                               taxa_edi=92,
                               frequentes=frequentes)
    finally:
        cursor.close()
        conn.close()


@app.route('/admin/learn')
def learn_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    if not conn:
        return "Erro DB", 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, user_id, question, created_at FROM unknown_questions 
        WHERE status = 'pending' ORDER BY created_at DESC LIMIT 50
    """)
    questions = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_learn.html', questions=questions)


@app.route('/admin/teach', methods=['POST'])
def teach_ednna():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Acesso negado'}), 403

    data = request.get_json()
    q = data.get('question', '').strip()
    a = data.get('answer', '').strip()
    c = data.get('category', '').strip()

    if not all([q, a, c]):
        return jsonify({"error": "Campos obrigatórios"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB"}), 500

    cursor = conn.cursor()
    try:
        words = re.findall(r'\w{5,}', a.lower())
        keywords = ",".join(set(words[:10])) or "geral"

        cursor.execute("""
            INSERT INTO knowledge_base (question, answer, category, keywords, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE answer = VALUES(answer), updated_at = NOW()
        """, (q, a, c, keywords))

        cursor.execute("UPDATE unknown_questions SET status = 'answered' WHERE question = %s", (q,))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# === FUNÇÕES AUXILIARES ===

def get_or_create_user_profile(user_id, connection):
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        if not profile:
            cursor.execute("""
                INSERT INTO user_profiles (user_id, name, company, erp) VALUES (%s, NULL, NULL, NULL)
            """, (user_id,))
            connection.commit()
            return {'user_id': user_id, 'name': None, 'company': None, 'erp': None}
        return profile
    except Error as e:
        logger.error(f"Erro ao buscar perfil: {e}")
        return {'user_id': user_id}
    finally:
        if cursor: cursor.close()


def update_user_profile(user_id, updates, connection):
    cursor = None
    try:
        cursor = connection.cursor()
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        query = f"UPDATE user_profiles SET {set_clause}, updated_at = NOW() WHERE user_id = %s"
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        logger.error(f"Erro ao atualizar perfil: {e}")
    finally:
        if cursor: cursor.close()


def get_or_create_conversation(user_id, connection):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id FROM conversations WHERE user_id = %s AND status = 'active' 
            ORDER BY started_at DESC LIMIT 1
        """, (user_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        cursor.execute("INSERT INTO conversations (user_id, started_at, status) VALUES (%s, NOW(), 'active')", (user_id,))
        connection.commit()
        return cursor.lastrowid
    except Error as e:
        logger.error(f"Erro ao criar conversa: {e}")
        return 1
    finally:
        if cursor: cursor.close()


def log_message(conversation_id, message, is_from_user, connection):
    cursor = None
    try:
        cursor = connection.cursor()
        query = "INSERT INTO messages (conversation_id, message_text, is_from_user, sent_at) VALUES (%s, %s, %s, NOW())"
        cursor.execute(query, (conversation_id, message, is_from_user))
        connection.commit()
    except Error as e:
        logger.error(f"Erro ao registrar mensagem: {e}")
    finally:
        if cursor: cursor.close()


# === RESPOSTA INTELIGENTE COM CONTEXTO ===

def get_chat_response(message, user_id, last_user_question=None):
    conn = get_db_connection()
    if not conn:
        return {'response': 'Erro de conexão', 'intent': 'error'}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        msg_low = message.strip().lower()

        # Carrega perfil do usuário
        profile = get_or_create_user_profile(user_id, conn) or {}
        name = profile.get('name')
        company = profile.get('company')
        erp = profile.get('erp')

        # Normalização de termos
        terms = {'teiacard': 'teia card', 'teiavalue': 'teia values'}
        norm = msg_low
        for err, cor in terms.items():
            norm = norm.replace(err, cor)

        # 🔁 Mantém foco no tema (EDI, Teia Card, etc)
        intencao_atual = None
        if last_user_question:
            if 'edi' in last_user_question.lower():
                intencao_atual = 'edi'
            elif 'teia card' in last_user_question.lower():
                intencao_atual = 'teia_card'
            elif 'bpo' in last_user_question.lower():
                intencao_atual = 'bpo'

        # ✅ SAUDAÇÕES
        saudacoes = ['oi', 'olá', 'bom dia', 'boa tarde', 'tudo bem']
        if any(s in msg_low for s in saudacoes):
            resposta = f"Olá, {name}! Como posso te ajudar hoje?" if name else "Olá! Como posso te ajudar hoje?"
            cid = get_or_create_conversation(user_id, conn)
            log_message(cid, message, True, conn)
            log_message(cid, resposta, False, conn)
            return {'response': resposta, 'intent': 'saudacao'}

        # ✅ DESPEDIDAS
        despedidas = ['tchau', 'até logo', 'obrigado', 'valeu', 'falou']
        if any(d in msg_low for d in despedidas):
            resposta = f"Tchau, {name}! Fico à disposição." if name else "Tchau! Estou aqui quando precisar."
            cid = get_or_create_conversation(user_id, conn)
            log_message(cid, message, True, conn)
            log_message(cid, resposta, False, conn)
            return {'response': resposta, 'intent': 'despedida'}

        # 🔹 DETECÇÃO DE PERFIL
        if not name:
            match = re.search(r"\b(?:me chamo|meu nome é|sou|eu sou)\s+(\w+)", msg_low)
            if match:
                update_user_profile(user_id, {'name': match.group(1).title()}, conn)
        if not company:
            match = re.search(r"\b(?:trabalho na|sou da|empresa)\s+(\w+)", msg_low)
            if match:
                update_user_profile(user_id, {'company': match.group(1).title()}, conn)
        if not erp:
            erps = {'totvs': 'TOTVS', 'sap': 'SAP', 'oracle': 'ORACLE', 'sankhya': 'SANKHYA'}
            for key, value in erps.items():
                if key in msg_low:
                    update_user_profile(user_id, {'erp': value}, conn)
                    break

        # 🔍 BUSCA POR INTENÇÃO
        result = None
        if intencao_atual:
            try:
                cursor.execute("""
                    SELECT answer, category FROM knowledge_base 
                    WHERE category = %s AND (question LIKE %s OR keywords LIKE %s)
                    ORDER BY updated_at DESC LIMIT 1
                """, (intencao_atual, f'%{norm}%', f'%{norm}%'))
                result = cursor.fetchone()
            except Error as e:
                logger.error(f"Erro na busca por intenção: {e}")

        # 🔍 Busca geral
        if not result:
            try:
                cursor.execute("""
                    SELECT answer, category FROM knowledge_base 
                    WHERE question LIKE %s OR keywords LIKE %s 
                    ORDER BY updated_at DESC LIMIT 1
                """, (f'%{norm}%', f'%{norm}%'))
                result = cursor.fetchone()
            except Error as e:
                logger.error(f"Erro na busca geral: {e}")

        # 🔍 Full-text como fallback
        if not result and len(norm.split()) > 1:
            try:
                safe_norm = conn.converter.escape(norm)
                query_fulltext = f"""
                    SELECT answer, category,
                           MATCH(question, keywords, answer) AGAINST('{safe_norm}' IN NATURAL LANGUAGE MODE) as score
                    FROM knowledge_base
                    WHERE MATCH(question, keywords, answer) AGAINST('{safe_norm}' IN NATURAL LANGUAGE MODE) > 0.7
                    ORDER BY score DESC
                    LIMIT 1
                """
                cursor.execute(query_fulltext)
                result = cursor.fetchone()
            except Exception as e:
                logger.error(f"Erro na busca full-text: {e}")

        # ✅ RESPOSTA ENCONTRADA
        if result:
            cid = get_or_create_conversation(user_id, conn)
            resposta_final = result['answer']
            log_message(cid, message, True, conn)
            log_message(cid, resposta_final, False, conn)
            return {'response': resposta_final, 'intent': result['category'], 'confidence': 0.9}

        # 📚 APRENDIZADO ATIVO
        short_question = message[:255]
        cursor.execute("""
            SELECT id FROM unknown_questions 
            WHERE question = %s AND created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """, (short_question,))
        if not cursor.fetchone():
            cid = get_or_create_conversation(user_id, conn)
            cursor.execute("""
                INSERT INTO unknown_questions (user_id, question, conversation_id, status)
                VALUES (%s, %s, %s, 'pending')
            """, (user_id, short_question, cid))
            conn.commit()

        # 💡 SUGESTÃO INTELIGENTE
        if intencao_atual == 'edi':
            sugestao = "Posso explicar as 4 fases do processo de EDI?"
        elif intencao_atual == 'teia_card':
            sugestao = "Quer saber como funciona a conciliação automática?"
        else:
            sugestao = "Posso te ajudar a esclarecer melhor?"

        resposta = f"Desculpe, ainda não sei responder isso. {sugestao}"
        cid = get_or_create_conversation(user_id, conn)
        log_message(cid, resposta, False, conn)
        return {'response': resposta, 'intent': 'unknown', 'confidence': 0.1}

    except Error as e:
        logger.error(f"Erro no banco: {e}")
        return {'response': 'Erro ao processar', 'intent': 'error'}
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# Protege rotas admin
@app.before_request
def require_login():
    if '/admin/' in request.path and request.endpoint != 'admin_login':
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
