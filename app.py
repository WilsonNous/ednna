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
    """Processa a mensagem e retorna uma resposta do banco de dados"""
    connection = get_db_connection()
    if not connection:
        return {'response': 'Erro de conexão com o banco de dados', 'intent': 'error'}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Buscar na base de conhecimento
        query = """
        SELECT answer, category 
        FROM knowledge_base 
        WHERE question LIKE %s OR keywords LIKE %s 
        ORDER BY updated_at DESC 
        LIMIT 1
        """
        search_term = f'%{message}%'
        cursor.execute(query, (search_term, search_term))
        result = cursor.fetchone()
        
        # Registrar a mensagem do usuário
        conversation_id = get_or_create_conversation(user_id, connection)
        log_message(conversation_id, message, True, connection)
        
        if result:
            # Registrar a resposta do bot
            log_message(conversation_id, result['answer'], False, connection)
            return {
                'response': result['answer'],
                'intent': result['category'],
                'confidence': 0.9
            }
        else:
            # Resposta padrão se não encontrar
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
