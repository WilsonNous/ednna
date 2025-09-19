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


def should_filter_message(message: str) -> str:
    """
    Verifica se a mensagem deve ser filtrada (perguntas idiotas, ofensivas, etc)
    Retorna uma resposta pré-definida se for o caso, ou None se for para buscar no banco.
    """
    message_lower = message.lower().strip()
    palavras = message_lower.split()

    # 1. Filtro de palavrões - VERIFICAÇÃO POR PALAVRA COMPLETA
    palavroes = [
        'porra', 'caralho', 'puta', 'merda', 'bosta', 'cu', 'foda', 'idiota',
        'burro', 'imbecil', 'retardado', 'estúpido', 'palhaço', 'babaca', 'otário',
        'vagabundo', 'canalha', 'desgraçado', 'filho', 'puta', 'fdp', 'vai', 'tomar',
        'arrombado', 'corn', 'chupa', 'piroca', 'rola', 'pau', 'buceta', 'xoxota'
    ]

    # Verifica se alguma palavra completa está na lista de palavrões
    for palavra in palavras:
        if palavra in palavroes:
            return "Vamos manter o respeito, por favor. Como posso te ajudar com nossos serviços?"

    # 2. Filtro de temas sensíveis - MELHOR DETECÇÃO
    temas_sensiveis = [
        'petista', 'bolsonaro', 'lula', 'pt', 'psdb', 'psol', 'direita', 'esquerda',
        'comunista', 'capitalista', 'socialista', 'fascista', 'ditadura', 'democracia',
        'deus', 'jesus', 'alá', 'allah', 'bud', 'kardec', 'espírita', 'umbanda', 'candomblé',
        'evangélico', 'católico', 'protestante', 'ateu', 'ateísmo', 'religião', 'fé', 'igreja',
        'templo', 'missa', 'culto', 'política', 'eleição', 'voto', 'urn', 'tse', 'supremo',
        'stf', 'congresso', 'senado', 'câmara', 'prefeito', 'governador', 'presidente'
    ]

    for tema in temas_sensiveis:
        # Verifica se o tema aparece como palavra completa ou como parte relevante
        if (f" {tema} " in f" {message_lower} " or
                message_lower.startswith(tema + " ") or
                message_lower.endswith(" " + tema) or
                message_lower == tema):
            return ("Sou uma assistente técnica — prefiro falar sobre conciliação, "
                    "EDI, BPO e nossos produtos. Posso te ajudar com algo nessa área?")

    # 3. Perguntas absurdas / fora de escopo - CATEGORIZADAS

    # Matemática e cálculos
    calculos = [
        '2+2', '1+1', '3+3', '4+4', '5+5', '6+6', '7+7', '8+8', '9+9', '10+10',
        '2x2', '3x3', '4x4', '5x5', '6x6', '7x7', '8x8', '9x9', '10x10',
        '50+1', '100-1', 'quanto é', 'qual o resultado de', 'resolve essa conta',
        'matemática', 'álgebra', 'geometria', 'trigonometria', 'cálculo', 'raiz quadrada',
        'pi', 'π', 'seno', 'cosseno', 'tangente', 'derivada', 'integral'
    ]

    # Geografia e história
    geografia_historia = [
        'capital do brasil', 'capital de minas', 'capital de são paulo', 'capital do rio',
        'quem descobriu o brasil', 'independência do brasil', 'proclamação da república',
        'segunda guerra', 'primeira guerra', 'guerra fria', 'revolução francesa',
        'mapa', 'globo', 'planeta', 'terra', 'países', 'continentes', 'oceanos',
        'amazonas', 'nilo', 'montanhas', 'cordilheira', 'deserto', 'floresta'
    ]

    # Ciência e tecnologia complexa
    ciencia_complexa = [
        'teoria da relatividade', 'einstein', 'newton', 'gravidade', 'buracos negros',
        'big bang', 'universo', 'cosmos', 'galáxias', 'estrelas', 'planetas', 'via láctea',
        'física quântica', 'mecânica quântica', 'átomo', 'próton', 'nêutron', 'elétron',
        'dna', 'rna', 'genética', 'clone', 'clonagem', 'biotecnologia', 'nanotecnologia',
        'inteligência artificial', 'machine learning', 'deep learning', 'blockchain',
        'metaverso', 'realidade virtual', 'realidade aumentada'
    ]

    # Cultura pop e entretenimento
    cultura_pop = [
        'netflix', 'disney+', 'amazon prime', 'hbo max', 'filme', 'série', 'novela',
        'cinema', 'hollywood', 'oscar', 'grammy', 'emmy', 'festival', 'rock', 'sertanejo',
        'funk', 'rap', 'hip hop', 'mpb', 'bossa nova', 'ator', 'atriz', 'cantor', 'cantora',
        'banda', 'show', 'turnê', 'festival', 'you tube', 'youtube', 'tiktok', 'instagram',
        'twitter', 'facebook', 'whatsapp', 'telegram', 'redes sociais'
    ]

    # Perguntas pessoais e existenciais
    pessoais = [
        'qual seu signo', 'você é homem ou mulher', 'você tem namorado', 'você namora',
        'você é casada', 'tem filhos', 'quantos anos você tem', 'onde você mora',
        'de onde você é', 'qual sua cor favorita', 'qual sua comida preferida',
        'você gosta de', 'o que você faz no tempo livre', 'você dorme', 'você come',
        'você respira', 'você sonha', 'você tem sentimentos', 'você é real',
        'você é uma ia', 'você é robô', 'você é humano'
    ]

    # Perguntas filosóficas e existenciais
    filosoficas = [
        'qual o sentido da vida', 'porque existimos', 'o que é a morte', 'o que é o amor',
        'o que é felicidade', 'o que é verdade', 'o que é justiça', 'o que é moral',
        'o que é ética', 'livre arbítrio', 'destino', 'universo consciente', 'deus existe',
        'vida após a morte', 'reencarnação', 'karma', 'nirvana', 'iluminação'
    ]

    # Culinária e gastronomia
    culinaria = [
        'arroz com feijão', 'feijoada', 'churrasco', 'pizza', 'hambúrguer', 'sushi',
        'macarrão', 'lasanha', 'strogonoff', 'salada', 'sobremesa', 'bolo', 'sorvete',
        'receita', 'como fazer', 'modo de preparo', 'tempero', 'chef', 'restaurante',
        'comida japonesa', 'comida italiana', 'comida mexicana', 'comida árabe'
    ]

    # Esportes
    esportes = [
        'futebol', 'brasileirão', 'libertadores', 'copa do mundo', 'flamengo', 'corinthians',
        'palmeiras', 'são paulo', 'santos', 'vasco', 'fluminense', 'botafogo', 'grêmio',
        'internacional', 'atlético mineiro', 'cruzeiro', 'bahia', 'sport', 'náutico',
        'basquete', 'vôlei', 'tênis', 'formula 1', 'f1', 'motogp', 'ufc', 'mma', 'boxe',
        'judô', 'judo', 'jiu-jitsu', 'capoeira', 'natação', 'atletismo', 'olimpíadas'
    ]

    # Perguntas absurdas clássicas
    absurdas_classicas = [
        'qual a cor do cavalo branco de napoleão', 'se eu jogar um lápis no chão ele cai',
        'o ovo veio antes da galinha', 'quantos anjos cabem na cabeça de um alfinete',
        'o que veio primeiro', 'para que time o padre torce', 'o que é que não é',
        'quem nasceu primeiro', 'o que é um ponto', 'defina a cor azul'
    ]

    # Jogos e passatempos
    jogos = [
        'minecraft', 'fortnite', 'free fire', 'league of legends', 'lol', 'dota',
        'counter strike', 'cs go', 'valorant', 'xbox', 'playstation', 'nintendo',
        'pokémon', 'super mario', 'zelda', 'god of war', 'fifa', 'pes', 'game',
        'videogame', 'jogo eletrônico', 'tabuleiro', 'xadrez', 'dama', 'dominó',
        'baralho', 'poker', 'sinuca', 'bilhar'
    ]

    # Saúde e medicina complexa
    saude_complexa = [
        'como tratar câncer', 'cura do câncer', 'hiv', 'aids', 'diabetes', 'hipertensão',
        'alzheimer', 'parkinson', 'depressão', 'ansiedade', 'bipolar', 'esquizofrenia',
        'autismo', 'tdah', 'transplante', 'cirurgia', 'quimioterapia', 'radioterapia',
        'diagnóstico', 'prognóstico', 'receita médica', 'remédio controlado'
    ]

    # 4. Verificação otimizada por categoria
    categorias = [
        calculos, geografia_historia, ciencia_complexa, cultura_pop,
        pessoais, filosoficas, culinaria, esportes, absurdas_classicas,
        jogos, saude_complexa
    ]

    for categoria in categorias:
        for termo in categoria:
            # Verificação mais precisa: termo como palavra completa ou frase
            if (f" {termo} " in f" {message_lower} " or
                    message_lower.startswith(termo + " ") or
                    message_lower.endswith(" " + termo) or
                    message_lower == termo or
                    termo in palavras):
                return ("Sou especialista em conciliação financeira, "
                        "EDI e BPO — mas não em cálculos, culinária ou curiosidades. "
                        "Posso te ajudar com algo do nosso escopo?")

    # 5. Perguntas muito curtas ou sem sentido (critério mais rigoroso)
    palavras_curtas_permitidas = {'oi', 'olá', 'ola', 'bom', 'dia', 'boa', 'tarde', 'noite',
                                  'ok', 'okay', 'tchau', 'obrigado', 'obrigada', 'hello', 'hi'}

    if len(palavras) == 1 and palavras[0] not in palavras_curtas_permitidas:
        return ("Desculpe, não entendi. Pode reformular sua pergunta? "
                "Estou aqui para ajudar com nossos produtos e serviços!")

    # 6. Perguntas genéricas (verificação exata)
    perguntas_genericas = {
        'como vai', 'tudo bem', 'e aí', 'e ai', 'fala', 'fala aí', 'fala ai',
        'me ajuda', 'ajuda', 'socorro', 'help', 'alô', 'alo', 'opa', 'eae'
    }

    if message_lower in perguntas_genericas:
        return "Olá! Estou aqui para ajudar com conciliação financeira, EDI e BPO. Em que posso te ajudar?"

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
        saudacoes = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hello', 'hi']
        primeira_palavra = mensagem_lower.split()[0] if mensagem_lower.split() else ""

        if primeira_palavra in saudacoes or any(s in mensagem_lower for s in ['eai', 'e aí', 'tudo bem']):
            query_saudacao = ("SELECT answer, category FROM knowledge_base "
                              "WHERE category = 'saudacao' ORDER BY id LIMIT 1")
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

        # Termos de produto (Teia Card, Teia Values) - CORREÇÃO SEGURA
        termos_produto = {
            'teiacard': 'teia card',
            'teiacards': 'teia card',
            'teia cards': 'teia card',
            'teiavalue': 'teia values',
            'teiavalues': 'teia values'
        }

        mensagem_normalizada = mensagem_lower
        for termo_errado, termo_correto in termos_produto.items():
            # Substitui apenas quando é uma palavra completa usando regex
            mensagem_normalizada = re.sub(r'\b' + re.escape(termo_errado) + r'\b', termo_correto, mensagem_normalizada)

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
    
