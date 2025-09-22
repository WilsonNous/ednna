#!/usr/bin/env python3
"""
Ednna Chatbot - Netunna Software
Backend Flask com MySQL — Nível 2+3: Contexto + Memória de Usuário + Aprendizado Ativo
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
app.secret_key = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui')

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


def is_absurd_context(message: str) -> bool:
    """Verifica se a mensagem é absurda ou sem contexto."""
    message_lower = message.lower().strip()
    palavras_soltas = ['pena', 'banho', 'macaco', 'galho', 'shoope', 'ahh', 'ate', 'mas', 'serio']
    if len(message_lower.split()) == 1 and message_lower in palavras_soltas:
        return True
    absurdas = [
        'xuxu com quiabo é bom', 'quando toma banho', 'e macaco no galho',
        'ahh que pena', 'choro do palmeiras', 'palmeiras não tem mundial'
    ]
    return any(absurda in message_lower for absurda in absurdas)


def is_offensive_or_absurd(message: str) -> bool:
    """Verifica ofensas, absurdos ou tentativas de extrair dados sensíveis."""
    message_lower = message.lower().strip()
    palavroes = ['caralho', 'porra', 'buceta', 'xoxota', 'fdp', 'vtnc', 'arrombado']
    if any(p in message_lower for p in palavroes):
        return True
    ofensas = ['seu burro', 'você é idiota', 'não sabe nada']
    if any(o in message_lower for o in ofensas):
        return True
    termos_clientes = ['lista de clientes', 'nomes dos clientes', 'clientes da netunna']
    return any(t in message_lower for t in termos_clientes)


def get_appropriate_response_for_offensive(message: str) -> str:
    """Resposta apropriada para mensagens inválidas."""
    msg_low = message.lower()
    if any(w in msg_low for w in ['burr', 'idiota', 'imbecil']):
        return "Prefiro manter a conversa profissional. Posso te ajudar com nossos serviços?"
    if any(w in msg_low for w in ['caralho', 'porra', 'buceta']):
        return "Vamos manter o respeito, por favor. Como posso te ajudar com nossos serviços?"
    if 'clientes' in msg_low:
        return ("Informações sobre nossos clientes são confidenciais. "
                "Para parcerias, entre em contato com contato@netunna.com.br.")
    return "Sou especialista em conciliação financeira, EDI e BPO. Posso te ajudar?"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    try:
        conn = get_db_connection()
        status = 'healthy' if conn and conn.is_connected() else 'degraded'
        if conn: conn.close()
        return jsonify({'status': status, 'database': 'connected' if status == 'healthy' else 'disconnected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not  data:  # ✅ Corrigido: agora tem condição
            return jsonify({'error': 'JSON inválido'}), 400
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', 1)
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


@app.route('/admin/learn')
def learn_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    if not conn: return "Erro DB", 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, user_id, question, created_at FROM unknown_questions 
        WHERE status = 'pending' ORDER BY created_at DESC LIMIT 50
    """)
    questions = cursor.fetchall()
    cursor.close(); conn.close()

    return render_template('admin_learn.html', questions=questions)


@app.route('/admin/teach', methods=['POST'])
def teach_ednna():
    if not session.get('admin_logged_in'): return jsonify({'error': 'Acesso negado'}), 403
    data = request.get_json()
    q, a, c = data.get('question'), data.get('answer'), data.get('category')
    if not all([q, a, c]): return jsonify({"error": "Campos obrigatórios"}), 400

    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB"}), 500

    cursor = conn.cursor()
    try:
        keywords = ",".join(set(re.findall(r'\w{5,}', a.lower()))[:10]) or "geral"
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
        cursor.close(); conn.close()


# === FUNÇÕES AUXILIARES ===

def get_or_create_user_profile(user_id, connection):
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        if not profile:
            cursor.execute("""
                INSERT INTO user_profiles (user_id, name, company, erp, adquirente, last_issue)
                VALUES (%s, NULL, NULL, NULL, NULL, NULL)
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
        query = "SELECT id FROM conversations WHERE user_id = %s AND status = 'active' ORDER BY started_at DESC LIMIT 1"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        if result: return result[0]
        cursor.execute("INSERT INTO conversations (user_id, started_at, status) VALUES (%s, NOW(), 'active')", (user_id,))
        connection.commit()
        return cursor.lastrowid
    except Error as e:
        logger.error(f"Erro ao obter/criar conversa: {e}")
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


# === RESPOSTA INTELIGENTE ===

def get_chat_response(message, user_id, last_user_question=None):
    conn = get_db_connection()
    if not conn: return {'response': 'Erro de conexão', 'intent': 'error'}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        msg_low = message.strip().lower()

        # Saudações
        saudacoes = ['oi', 'olá', 'bom dia', 'boa tarde', 'tudo bem']
        if any(s in msg_low for s in saudacoes):
            cursor.execute("SELECT answer FROM knowledge_base WHERE category='saudacao' LIMIT 1")
            result = cursor.fetchone()
            if result:
                cid = get_or_create_conversation(user_id, conn)
                log_message(cid, message, True, conn)
                log_message(cid, result['answer'], False, conn)
                return {'response': result['answer'], 'intent': 'saudacao', 'confidence': 0.95}

        # Despedidas
        despedidas = ['tchau', 'até logo', 'obrigado', 'valeu', 'falou', 'até mais', 'vou sair', 'encerrar', 'finalizar']
        if any(d in msg_low for d in despedidas):
            profile = get_or_create_user_profile(user_id, conn) or {}
            name = profile.get('name')
            resposta = f"Tchau, {name}! Foi um prazer te ajudar." if name else "Tchau! Fico à disposição para ajudar."
            cid = get_or_create_conversation(user_id, conn)
            log_message(cid, message, True, conn); log_message(cid, resposta, False, conn)
            return {'response': resposta, 'intent': 'despedida', 'confidence': 0.95}

        # Perfil do usuário
        profile = get_or_create_user_profile(user_id, conn) or {}
        name = profile.get('name'); company = profile.get('company'); erp = profile.get('erp')
        prefix = f"Olá, {name}! " if name else ""
        if company: prefix += f"Da {company}, certo? "

        # 🔹 DETECÇÃO INTELIGENTE DE PERFIL DO USUÁRIO
        profile_updates = {}

        # 1. Detecta nome com múltiplas variações
        if not name:
            patterns_nome = [
                r"\b(?:me\s+chamo|meu\s+nome\s+é|sou|eu\s+sou|aqu(i|í)\s+é)\s+([A-Za-z]+)",
                r"\b([A-Za-z]+)\s+(?:aqui|reportando)"
            ]
            for pattern in patterns_nome:
                match = re.search(pattern, msg_low)
                if match:
                    profile_updates['name'] = match.group(2).title()
                    break

        # 2. Detecta empresa com contexto
        if not company:
            patterns_empresa = [
                r"\b(?:trabalho\s+na|sou\s+da|faco\s+parte\s+da|empresa\s+)([A-Za-z]+)",
                r"\b([A-Za-z]+)\s+(?:grupo|holdings?|institui[çc]ão|hospital|editora|óticas|lojas?)\b"
            ]
            for pattern in patterns_empresa:
                match = re.search(pattern, msg_low)
                if match:
                    company_name = match.group(1).title()
                    company_map = {
                        'Damyller': 'Damyller',
                        'Felicio': 'Hospital Felício Rocho',
                        'Puc': 'PUC RS',
                        'Modernaa': 'Editora Moderna'
                    }
                    company_name = company_map.get(company_name, company_name)
                    profile_updates['company'] = company_name
                    break

        # 3. Detecta ERP com maior cobertura
        if not erp:
            erp_map = {
                'totvs': 'TOTVS', 'protheus': 'TOTVS', 'flex': 'TOTVS', 'rm': 'TOTVS', 'siga': 'TOTVS',
                'sap': 'SAP', 'business one': 'SAP', 'b1': 'SAP',
                'oracle': 'ORACLE', 'netsuite': 'ORACLE',
                'sankhya': 'SANKHYA', 'microsiga': 'SANKHYA'
            }
            msg_for_erp = msg_low.replace('-', ' ')
            for key, value in erp_map.items():
                if key in msg_for_erp:
                    profile_updates['erp'] = value
                    break

        # 4. Atualiza perfil em uma única operação
        if profile_updates:
            update_user_profile(user_id, profile_updates, conn)
            if 'name' in profile_updates: name = profile_updates['name']
            if 'company' in profile_updates: company = profile_updates['company']
            if 'erp' in profile_updates: erp = profile_updates['erp']

        # Lógica de contexto curto
        if len(message.split()) <= 2 and last_user_question:
            last_low = last_user_question.lower()
            if "teia" in last_low:
                if "card" in last_low: message = "o que é o teia card"
                elif "values" in last_low: message = "o que é o teia values"
            elif any(w in last_low for w in ["chargeback", "estorno"]):
                if any(w in msg_low for w in ["que pena", "poxa"]): message = "como reduzir chargebacks"

        # Filtros de conteúdo
        if is_absurd_context(message):
            resp = "Prefiro focar em conciliação, EDI, BPO. Posso te ajudar com algo nessa área?"
            cid = get_or_create_conversation(user_id, conn)
            log_message(cid, message, True, conn); log_message(cid, resp, False, conn)
            return {'response': resp, 'intent': 'filtered', 'confidence': 0.99}

        if is_offensive_or_absurd(message):
            resp = get_appropriate_response_for_offensive(message)
            cid = get_or_create_conversation(user_id, conn)
            log_message(cid, message, True, conn); log_message(cid, resp, False, conn)
            return {'response': resp, 'intent': 'filtered', 'confidence': 0.99}

        # Busca normalizada
        terms = {'teiacard': 'teia card', 'teiavalue': 'teia values'}
        norm = msg_low
        for err, cor in terms.items(): norm = norm.replace(err, cor)

        cursor.execute("""
            SELECT answer, category FROM knowledge_base 
            WHERE question LIKE %s OR keywords LIKE %s 
            ORDER BY updated_at DESC LIMIT 1
        """, (f'%{norm}%', f'%{norm}%'))
        result = cursor.fetchone()

        if not result and len(norm.split()) > 1:
            cursor.execute("""
                SELECT answer, category, MATCH(question,keywords,answer) AGAINST(%s) as score
                FROM knowledge_base WHERE MATCH(question,keywords,answer) AGAINST(%s) > 0.7
                ORDER BY score DESC LIMIT 1
            """, (norm, norm))
            result = cursor.fetchone()

        # Resposta encontrada
        if result:
            cid = get_or_create_conversation(user_id, conn)
            full_answer = prefix + result['answer'] if prefix else result['answer']
            log_message(cid, message, True, conn); log_message(cid, full_answer, False, conn)
            return {'response': full_answer, 'intent': result['category'], 'confidence': 0.9}

        # Aprendizado ativo
        cursor.execute("""
            SELECT id FROM unknown_questions 
            WHERE question = %s AND created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """, (message,))
        if not cursor.fetchone():
            cid = get_or_create_conversation(user_id, conn)
            cursor.execute("""
                INSERT INTO unknown_questions (user_id, question, conversation_id, status)
                VALUES (%s, %s, %s, 'pending')
            """, (user_id, message, cid))
            conn.commit()

        # Sugestão baseada no contexto
        if last_user_question and "teia card" in last_user_question.lower():
            sug = "Quer saber mais sobre o Teia Card?"
        elif "bpo" in last_user_question.lower():
            sug = "Posso explicar a diferença entre BPO Técnico e Premium?"
        else:
            sug = "Posso te ajudar a esclarecer melhor?"

        default = f"Desculpe, ainda não sei responder isso. {sug}"
        final = prefix + default if prefix else default
        cid = get_or_create_conversation(user_id, conn)
        log_message(cid, final, False, conn)
        return {'response': final, 'intent': 'unknown', 'confidence': 0.1}

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
    

