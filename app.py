#!/usr/bin/env python3
"""
Ednna Chatbot - Netunna Software
Backend Flask com MySQL — SEM OpenAI
"""

from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

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

def should_filter_message(message: str) -> str:
    """
    Verifica se a mensagem deve ser filtrada (perguntas idiotas, ofensivas, etc)
    Retorna uma resposta pré-definida se for o caso, ou None se for para buscar no banco.
    """
    message_lower = message.lower().strip()
    
    # Lista de palavrões (adicione mais se quiser)
    palavroes = ['porra', 'caralho', 'puta', 'merda', 'bosta', 'cu', 'foda', 'idiota', 'burro', 'imbecil']
    for palavrao in palavroes:
        if palavrao in message_lower:
            return "Vamos manter o respeito, por favor. Como posso te ajudar com nossos serviços?"
    
    # Perguntas políticas/religiosas
    if any(p in message_lower for p in ['petista', 'bolsonaro', 'lula', 'deus', 'jesus', 'alá', 'religião', 'política', 'eleição']):
        return "Sou uma assistente técnica — prefiro falar sobre conciliação, EDI, BPO e nossos produtos. Posso te ajudar com algo nessa área?"
    
    # Perguntas absurdas / fora de escopo
    absurdas = [
        'arroz com feijão é bom', 'qual a capital do brasil', '50+1 é quanto', 'quantos funcionários tem',
        'qual o nome do ceo', 'quem é o dono', 'qual seu signo', 'você é homem ou mulher', 'você tem namorado',
        'qual a cor do cavalo branco de napoleão', 'se eu jogar um lápis no chão, ele cai', '2+2', 'quanto é 1+1'
    ]
    for absurda in absurdas:
        if absurda in message_lower:
            return "Sou especialista em conciliação financeira, EDI e BPO — mas não em cálculos, culinária ou curiosidades. Posso te ajudar com algo do nosso escopo?"
    
    # Perguntas muito curtas ou sem sentido
    if len(message_lower.split()) < 2 and message_lower not in ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite']:
        return "Desculpe, não entendi. Pode reformular sua pergunta? Estou aqui para ajudar com nossos produtos e serviços!"
    
    # Se passou por todos os filtros, retorna None → vai buscar no banco
    return None

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
            return jsonify({
                'status': 'healthy',
                'database': 'connected'
            }), 200
        else:
            return jsonify({
                'status': 'degraded',
                'database': 'disconnected'
            }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

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
        
        # Buscar resposta no banco de dados
        response = get_chat_response(user_message, user_id)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Erro no endpoint /api/chat: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

def get_chat_response(message, user_id):
    """Processa a mensagem e retorna uma resposta — com filtro de perguntas idiotas"""
    connection = get_db_connection()
    if not connection:
        return {'response': 'Erro de conexão com o banco de dados', 'intent': 'error'}
    
    try:
        # 🔍 PRIMEIRO: Aplica o filtro de perguntas idiotas
        filtered_response = should_filter_message(message)
        if filtered_response:
            # Registrar a mensagem do usuário
            conversation_id = get_or_create_conversation(user_id, connection)
            log_message(conversation_id, message, True, connection)
            log_message(conversation_id, filtered_response, False, connection)
            return {
                'response': filtered_response,
                'intent': 'filtered',
                'confidence': 0.99
            }
        
        # 🧠 DEPOIS: Processa normalmente (saudações, LIKE, Full-Text Search)
        cursor = connection.cursor(dictionary=True)
        
        # Normalizar a mensagem
        mensagem_lower = message.strip().lower()
        
        # Lista de saudações
        saudacoes = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'eai', 'e aí', 'tudo bem', 'hello', 'hi']
        for saudacao in saudacoes:
            if saudacao in mensagem_lower.split() or mensagem_lower.startswith(saudacao):
                query_saudacao = "SELECT answer, category FROM knowledge_base WHERE category = 'saudacao' ORDER BY id LIMIT 1"
                cursor.execute(query_saudacao)
                result = cursor.fetchone()
                if result:
                    conversation_id = get_or_create_conversation(user_id, connection)
                    log_message(conversation_id, message, True, connection)
                    log_message(conversation_id, result['answer'], False, connection)
                    return {
                        'response': result['answer'],
                        'intent': result['category'],
                        'confidence': 0.95
                    }
        
        # Termos de produto (Teia Card, Teia Values)
        termos_produto = {
            'teiacard': 'teia card',
            'teiacards': 'teia card',
            'teia card': 'teia card',
            'teia cards': 'teia card',
            'teia value': 'teia values',
            'teiavalues': 'teia values',
            'teia values': 'teia values',
            'teia value': 'teia values'
        }
        mensagem_normalizada = mensagem_lower
        for termo_errado, termo_correto in termos_produto.items():
            if termo_errado in mensagem_normalizada:
                mensagem_normalizada = mensagem_normalizada.replace(termo_errado, termo_correto)
        
        # Busca exata
        query_exact = """
        SELECT answer, category 
        FROM knowledge_base 
        WHERE question LIKE %s OR keywords LIKE %s 
        ORDER BY updated_at DESC 
        LIMIT 1
        """
        search_term = f'%{mensagem_normalizada}%'
        cursor.execute(query_exact, (search_term, search_term))
        result = cursor.fetchone()
        
        # Full-Text Search
        if not result and len(mensagem_normalizada.split()) > 1:
            query_fulltext = """
            SELECT answer, category, 
                   MATCH(question, keywords, answer) AGAINST(%s IN NATURAL LANGUAGE MODE) as score
            FROM knowledge_base
            WHERE MATCH(question, keywords, answer) AGAINST(%s IN NATURAL LANGUAGE MODE)
            AND MATCH(question, keywords, answer) AGAINST(%s IN NATURAL LANGUAGE MODE) > 0.5
            ORDER BY score DESC
            LIMIT 1
            """
            cursor.execute(query_fulltext, (mensagem_normalizada, mensagem_normalizada, mensagem_normalizada))
            result = cursor.fetchone()
        
        # Registrar a mensagem do usuário
        conversation_id = get_or_create_conversation(user_id, connection)
        log_message(conversation_id, message, True, connection)
        
        if result:
            log_message(conversation_id, result['answer'], False, connection)
            return {
                'response': result['answer'],
                'intent': result['category'],
                'confidence': 0.9
            }
        else:
            default_response = "Desculpe, ainda não sei responder isso. Pergunte sobre nossos serviços ou produtos!"
            log_message(conversation_id, default_response, False, connection)
            return {
                'response': default_response,
                'intent': 'unknown',
                'confidence': 0.1
            }
            
    except Error as e:
        logger.error(f"Erro no banco de dados: {e}")
        return {'response': 'Erro ao processar sua mensagem', 'intent': 'error'}
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_or_create_conversation(user_id, connection):
    """Obtém ou cria uma nova conversa para o usuário"""
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

def log_message(conversation_id, message, is_from_user, connection):
    """Registra uma mensagem no banco de dados"""
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO messages (conversation_id, message_text, is_from_user, sent_at) 
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(query, (conversation_id, message, is_from_user))
        connection.commit()
    except Error as e:
        logger.error(f"Erro ao registrar mensagem: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
