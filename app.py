from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração do banco de dados
DB_CONFIG = {
    "host": os.getenv('DB_HOST', 'localhost'),
    "user": os.getenv('DB_USER', 'noust785_edi_admin'),
    "password": os.getenv('DB_PASSWORD', 'N3tunn@21#'),
    "database": os.getenv('DB_NAME', 'noust785_edi_ops'),
    "port": os.getenv('DB_PORT', 3306)
}

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

@app.route('/')
def index():
    """Página principal do chatbot"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para processar mensagens do chat"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', 1)  # ID default para usuários não logados
        
        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        # Buscar resposta no banco de dados
        response = get_chat_response(user_message, user_id)
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

def get_chat_response(message, user_id):
    """Processa a mensagem e retorna uma resposta"""
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
            # Resposta padrão se não encontrar correspondência
            default_response = "Desculpe, não entendi. Pode reformular sua pergunta?"
            log_message(conversation_id, default_response, False, connection)
            
            return {
                'response': default_response,
                'intent': 'unknown',
                'confidence': 0.1
            }
            
    except Error as e:
        print(f"Erro no banco de dados: {e}")
        return {'response': 'Erro ao processar sua mensagem', 'intent': 'error'}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_or_create_conversation(user_id, connection):
    """Obtém ou cria uma nova conversa para o usuário"""
    try:
        cursor = connection.cursor()
        
        # Verificar se há conversa ativa
        query = "SELECT id FROM conversations WHERE user_id = %s AND status = 'active' ORDER BY started_at DESC LIMIT 1"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            # Criar nova conversa
            query = "INSERT INTO conversations (user_id, started_at, status) VALUES (%s, NOW(), 'active')"
            cursor.execute(query, (user_id,))
            connection.commit()
            return cursor.lastrowid
            
    except Error as e:
        print(f"Erro ao obter/criar conversa: {e}")
        return 1  # Fallback para conversa padrão

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
        print(f"Erro ao registrar mensagem: {e}")

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Endpoint para obter histórico de conversas"""
    try:
        user_id = request.args.get('user_id', 1)
        limit = request.args.get('limit', 10)
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
        
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT c.id, c.started_at, c.ended_at, c.status, 
               COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        WHERE c.user_id = %s
        GROUP BY c.id
        ORDER BY c.started_at DESC
        LIMIT %s
        """
        cursor.execute(query, (user_id, limit))
        conversations = cursor.fetchall()
        
        return jsonify({'conversations': conversations})
        
    except Error as e:
        return jsonify({'error': f'Erro no banco de dados: {str(e)}'}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/conversation/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Endpoint para obter mensagens de uma conversa específica"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
        
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT m.message_text, m.is_from_user, m.sent_at, m.intent
        FROM messages m
        WHERE m.conversation_id = %s
        ORDER BY m.sent_at ASC
        """
        cursor.execute(query, (conversation_id,))
        messages = cursor.fetchall()
        
        return jsonify({'messages': messages})
        
    except Error as e:
        return jsonify({'error': f'Erro no banco de dados: {str(e)}'}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
