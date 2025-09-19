#!/usr/bin/env python3
"""
Ednna Chatbot - Netunna Software
Backend Flask com MySQL — Estratégia Inteligente de Filtro
"""

from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

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
        logger.info("Conexão com MySQL estabelecida com sucesso")
        return connection
    except Error as e:
        logger.error(f"Erro ao conectar ao MySQL: {e}")
        return None

def is_offensive_or_absurd(message: str) -> bool:
    """Verifica se a mensagem é ofensiva ou absurdamente fora do contexto"""
    message_lower = message.lower().strip()
    
    # Palavrões graves
    palavroes_graves = ['caralho', 'porra', 'buceta', 'xoxota', 'piroca', 'rola', 'pau', 'vtnc', 'fdp', 'arrombado', 'desgraçado']
    if any(palavrao in message_lower for palavrao in palavroes_graves):
        return True

    # Ofensas pessoais diretas
    ofensas_pessoais = ['seu burro', 'sua burra', 'seu idiota', 'sua idiota', 'seu imbecil', 'sua imbecil', 'seu retardado', 'sua retardada', 'seu estúpido', 'você é burro', 'você é idiota', 'você é imbecil']
    if any(ofensa in message_lower for ofensa in ofensas_pessoais):
        return True

    # Absurdos clássicos
    absurdas_extremas = ['qual a cor do cavalo branco de napoleão', 'quantos anjos cabem na cabeça de um alfinete', 'se eu jogar um lápis no chão ele cai', 'o ovo veio antes da galinha']
    if any(absurda in message_lower for absurda in absurdas_extremas):
        return True

    # Ataques óbvios
    if any(termo in message_lower for termo in ['você é muito burr', 'que assistente horrível', 'não sabe nada']):
        return True

    return False

def get_appropriate_response_for_offensive(message: str) -> str:
    """Retorna uma resposta apropriada para mensagens ofensivas/absurdas"""
    message_lower = message.lower()
    
    if any(palavra in message_lower for palavra in ['burr', 'idiota', 'imbecil', 'retardad']):
        return "Prefiro manter a conversa profissional. Posso te ajudar com nossos serviços de conciliação, EDI ou BPO?"
    elif any(palavra in message_lower for palavra in ['caralho', 'porra', 'buceta', 'xoxota']):
        return "Vamos manter o respeito, por favor. Como posso te ajudar com nossos serviços?"
    else:
        return "Sou especialista em conciliação financeira, EDI e BPO. Posso te ajudar com algo do nosso escopo?"

@app.route('/')
def index():
    """Página principal do chatbot"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Endpoint para verificar saúde da aplicação"""
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            conn.close()
            return jsonify({'status': 'healthy', 'database': 'connected'}), 200
        else:
            return jsonify({'status': 'degraded', 'database': 'disconnected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para processar mensagens do chat"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON inválidos'}), 400

        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', 1)

        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400

        response = get_chat_response(user_message, user_id)
        return jsonify(response)

    except Exception as e:
        logger.error(f"Erro no endpoint /api/chat: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

def get_chat_response(message, user_id):
    """Processa a mensagem — consulta banco primeiro, filtra só se necessário"""
    connection = get_db_connection()
    if not connection:
        return {'response': 'Erro de conexão com o banco de dados', 'intent': 'error'}

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        mensagem_lower = message.strip().lower()

        # 1. Saudações
        saudacoes = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hello', 'hi']
        primeira_palavra = mensagem_lower.split()[0] if mensagem_lower.split() else ""
        if primeira_palavra in saudacoes or any(s in mensagem_lower for s in ['eai', 'e aí', 'tudo bem']):
            query_saudacao = "SELECT answer, category FROM knowledge_base WHERE category = 'saudacao' ORDER BY id LIMIT 1"
            cursor.execute(query_saudacao)
            result = cursor.fetchone()
            if result:
                conversation_id = get_or_create_conversation(user_id, connection)
                log_message(conversation_id, message, True, connection)
                log_message(conversation_id, result['answer'], False, connection)
                return {'response': result['answer'], 'intent': result['category'], 'confidence': 0.95}

        # 2. Normalização de termos
        termos_produto = {'teiacard': 'teia card', 'teiacards': 'teia card', 'teia cards': 'teia card', 'teiavalue': 'teia values', 'teiavalues': 'teia values'}
        mensagem_normalizada = mensagem_lower
        for termo_errado, termo_correto in termos_produto.items():
            mensagem_normalizada = re.sub(r'\b' + re.escape(termo_errado) + r'\b', termo_correto, mensagem_normalizada)

        # 3. Busca exata
        query_exact = "SELECT answer, category FROM knowledge_base WHERE question LIKE %s OR keywords LIKE %s ORDER BY updated_at DESC LIMIT 1"
        search_term = f'%{mensagem_normalizada}%'
        cursor.execute(query_exact, (search_term, search_term))
        result = cursor.fetchone()

        # 4. Full-Text Search
        if not result and len(mensagem_normalizada.split()) > 1:
            query_fulltext = """
            SELECT answer, category, MATCH(question, keywords, answer) AGAINST(%s IN NATURAL LANGUAGE MODE) as score
            FROM knowledge_base
            WHERE MATCH(question, keywords, answer) AGAINST(%s IN NATURAL LANGUAGE MODE)
            ORDER BY score DESC LIMIT 1
            """
            cursor.execute(query_fulltext, (mensagem_normalizada, mensagem_normalizada))
            result = cursor.fetchone()

        # 5. Registrar mensagem
        conversation_id = get_or_create_conversation(user_id, connection)
        log_message(conversation_id, message, True, connection)

        # 6. Se encontrou, retorna
        if result:
            log_message(conversation_id, result['answer'], False, connection)
            return {'response': result['answer'], 'intent': result['category'], 'confidence': 0.9}

        # 7. Se não encontrou, aplica filtro só para casos extremos
        if is_offensive_or_absurd(message):
            filtered_response = get_appropriate_response_for_offensive(message)
            log_message(conversation_id, filtered_response, False, connection)
            return {'response': filtered_response, 'intent': 'filtered', 'confidence': 0.99}

        # 8. Resposta padrão
        default_response = "Desculpe, ainda não sei responder isso. Pergunte sobre conciliação, EDI, BPO ou nossos produtos!"
        log_message(conversation_id, default_response, False, connection)
        return {'response': default_response, 'intent': 'unknown', 'confidence': 0.1}

    except Error as e:
        logger.error(f"Erro no banco de dados: {e}")
        return {'response': 'Erro ao processar sua mensagem', 'intent': 'error'}
    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()

def get_or_create_conversation(user_id, connection):
    """Obtém ou cria uma nova conversa para o usuário"""
    cursor = None
    try:
        cursor = connection.cursor()
        query = "SELECT id FROM conversations WHERE user_id = %s AND status = 'active' ORDER BY started_at DESC LIMIT 1"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            query = "INSERT INTO conversations (user_id, started_at, status) VALUES (%s, NOW(), 'active')"
            cursor.execute(query, (user_id,))
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        logger.error(f"Erro ao obter/criar conversa: {e}")
        return 1
    finally:
        if cursor: cursor.close()

def log_message(conversation_id, message, is_from_user, connection):
    """Registra uma mensagem no banco de dados"""
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
