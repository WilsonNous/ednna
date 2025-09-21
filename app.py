#!/usr/bin/env python3
"""
Ednna Chatbot - Netunna Software
Backend Flask com MySQL — Nível 2+3: Contexto + Memória de Usuário + Aprendizado Ativo
"""

from flask import Flask, request, jsonify, render_template, session
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging
import re  # ✅ Importe único no topo
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui')  # Necessário para sessões

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


def is_absurd_context(message: str) -> bool:
    """Verifica se a mensagem é absurda ou sem contexto — mesmo que não seja ofensiva."""
    message_lower = message.lower().strip()

    # Palavras soltas sem contexto
    palavras_soltas = [
        'pena', 'banho', 'macaco', 'galho', 'shoope', 'ahh', 'ate', 'mas', 'serio',
        'select', 'multas', 'gols', 'choro', 'palmeiras', 'tio', 'tiozao', 'mãe', 'pai'
    ]
    if len(message_lower.split()) == 1 and message_lower in palavras_soltas:
        return True

    # Frases absurdas
    absurdas = [
        'xuxu com quiabo é bom', 'quando toma banho', 'banho eh uma boa palavra',
        'e macaco no galho', 'qual o animal voce gosta', 'serio e o que fax saide animal',
        'voce mora em sao paulo', 'ahh que pena', 'que pena é essa', 'ate pena', 'mas que pena',
        'choro do palmeiras', 'palmeiras não tem mundial', 'voce tem mae', 'então tem pai tambem',
        'e o tio como vai', 'quem é o tiozao da netunna'
    ]
    for absurda in absurdas:
        if absurda in message_lower:
            return True

    return False


def is_offensive_or_absurd(message: str) -> bool:
    """Verifica se a mensagem é ofensiva ou tenta extrair informações sensíveis."""
    message_lower = message.lower().strip()

    # Palavrões graves
    palavroes_graves = ['caralho', 'porra', 'buceta', 'xoxota', 'piroca', 'rola', 'pau', 'vtnc',
                        'fdp', 'arrombado', 'desgraçado']
    if any(palavrao in message_lower for palavrao in palavroes_graves):
        return True

    # Ofensas pessoais diretas
    ofensas_pessoais = ['seu burro', 'sua burra', 'seu idiota', 'sua idiota', 'seu imbecil', 'sua imbecil',
                        'seu retardado', 'sua retardada', 'seu estúpido', 'você é burro', 'você é idiota',
                        'você é imbecil']
    if any(ofensa in message_lower for ofensa in ofensas_pessoais):
        return True

    # Absurdos clássicos
    absurdas_extremas = ['qual a cor do cavalo branco de napoleão', 'quantos anjos cabem na cabeça de um alfinete',
                         'se eu jogar um lápis no chão ele cai', 'o ovo veio antes da galinha']
    if any(absurda in message_lower for absurda in absurdas_extremas):
        return True

    # Ataques óbvios
    if any(termo in message_lower for termo in ['você é muito burr', 'que assistente horrível', 'não sabe nada']):
        return True

    # Tentativas de extrair lista de clientes
    termos_suspeitos = [
        'lista de clientes', 'quem são os clientes', 'todos os clientes', 'clientes da netunna',
        'nomes dos clientes', 'relação de clientes', 'clientes atendidos', 'parceiros da netunna',
        'estão com jesus', 'clientes cristãos', 'clientes religiosos', 'clientes com deus',
        'quantos clientes', 'nome dos clientes', 'quais empresas', 'empresas atendidas'
    ]
    for termo in termos_suspeitos:
        if termo in message_lower:
            return True

    return False


def get_appropriate_response_for_offensive(message: str) -> str:
    """Retorna resposta apropriada para mensagens ofensivas, absurdas ou que tentam extrair dados sensíveis."""
    message_lower = message.lower()

    # Resposta para ofensas diretas
    if any(palavra in message_lower for palavra in ['burr', 'idiota', 'imbecil', 'retardad']):
        return "Prefiro manter a conversa profissional. Posso te ajudar com nossos serviços de conciliação, EDI ou BPO?"

    # Resposta para palavrões
    if any(palavra in message_lower for palavra in ['caralho', 'porra', 'buceta', 'xoxota', 'pqp']):
        return "Vamos manter o respeito, por favor. Como posso te ajudar com nossos serviços?"

    # Resposta para tentativas de extrair lista de clientes
    if any(termo in message_lower for termo in [
        'lista de clientes', 'quem são os clientes', 'todos os clientes', 'clientes da netunna',
        'nomes dos clientes', 'relação de clientes', 'clientes atendidos', 'parceiros da netunna',
        'estão com jesus', 'clientes cristãos', 'clientes religiosos', 'clientes com deus'
    ]):
        return ("Informações sobre nossos clientes são confidenciais. "
                "Para parcerias ou referências, entre em contato com nosso time comercial "
                "pelo e-mail contato@netunna.com.br.")

    # Resposta padrão para outros casos
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
    """Endpoint para processar mensagens do chat — com contexto de conversa"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON inválidos'}), 400

        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', 1)

        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400

        # ✅ Cria ou recupera sessão por usuário
        if 'conversation_history' not in session:
            session['conversation_history'] = []

        # Adiciona a mensagem do usuário à história
        session['conversation_history'].append({
            'role': 'user',
            'text': user_message,
            'timestamp': str(datetime.now())
        })

        # Pega a última pergunta (antes da atual)
        last_user_question = session['conversation_history'][-2]['text'] \
            if len(session['conversation_history']) > 1 else None

        # ✅ PASSA last_user_question PARA get_chat_response
        response = get_chat_response(user_message, user_id, last_user_question)

        # Adiciona resposta à história
        session['conversation_history'].append({
            'role': 'bot',
            'text': response['response'],
            'timestamp': str(datetime.now())
        })

        return jsonify(response)

    except Exception as e:
        logger.error(f"Erro no endpoint /api/chat: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# === ROTAS ADMINISTRATIVAS PARA APRENDIZADO ATIVO ===

@app.route('/admin/learn')
def learn_dashboard():
    """Painel: mostra perguntas não respondidas"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Acesso negado'}), 403

    connection = get_db_connection()
    if not connection:
        return "Erro de conexão", 500

    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, user_id, question, created_at 
        FROM unknown_questions 
        WHERE status = 'pending' 
        ORDER BY created_at DESC 
        LIMIT 50
    """)
    questions = cursor.fetchall()
    cursor.close()
    connection.close()

    # Renderiza o HTML diretamente com Jinja (mesmo sem templates/)
    html = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Ensinar Ednna | Netunna</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f7f9fc; color: #333; }
        h1 { color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .card { background: white; border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 15px 0; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
        input, textarea, select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
        textarea { resize: vertical; min-height: 80px; }
        button { background: #007bff; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button:hover { background: #0056b3; }
        .empty { text-align: center; color: #777; font-style: italic; padding: 20px; }
    </style>
</head>
<body>
    <h1>🔍 Ensinar Ednna</h1>
    {% if questions %}
        {% for q in questions %}
        <div class="card" data-id="{{ q.id }}">
            <p><strong>Usuário {{ q.user_id }}:</strong> "{{ q.question }}"</p>
            <form class="teach-form" style="display:flex;flex-direction:column;">
                <input type="text" value="{{ q.question }}" readonly style="background:#f0f0f0;">
                <textarea placeholder="Resposta correta..." rows="4" required></textarea>
                <select required>
                    <option value="">Categoria</option>
                    <option value="teia_card">Teia Card</option>
                    <option value="teia_values">Teia Values</option>
                    <option value="edi">EDI</option>
                    <option value="bpo">BPO</option>
                    <option value="empresa">Empresa</option>
                    <option value="suporte">Suporte</option>
                </select>
                <button type="submit">✅ Ensinar Ednna</button>
            </form>
        </div>
        {% endfor %}
    {% else %}
        <div class="empty"><p>Nenhuma pergunta pendente.</p></div>
    {% endif %}

    <script>
        document.querySelectorAll('.teach-form').forEach(form => {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const [question, answer, category] = [
                    form.querySelector('input').value,
                    form.querySelector('textarea').value,
                    form.querySelector('select').value
                ];

                const res = await fetch('/admin/teach', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question, answer, category })
                });

                if (res.ok) {
                    alert('✅ Aprendido!');
                    form.closest('.card')?.remove();
                } else {
                    alert('❌ Erro');
                }
            });
        });
    </script>
</body>
</html>
    '''.replace('{% if questions %}', '').replace('{% for q in questions %}', '\n'.join([
        f'<div class="card" data-id="{q["id"]}">'
        f'<p><strong>Usuário {q["user_id"]}:</strong> "{q["question"]}"</p>'
        '<form class="teach-form" style="display:flex;flex-direction:column;">'
        f'<input type="text" value="{q["question"]}" readonly style="background:#f0f0f0;">'
        '<textarea placeholder="Resposta correta..." rows="4" required></textarea>'
        '<select required>'
        '<option value="">Categoria</option>'
        '<option value="teia_card">Teia Card</option>'
        '<option value="teia_values">Teia Values</option>'
        '<option value="edi">EDI</option>'
        '<option value="bpo">BPO</option>'
        '<option value="empresa">Empresa</option>'
        '<option value="suporte">Suporte</option>'
        '</select>'
        '<button type="submit">✅ Ensinar Ednna</button>'
        '</form></div>' for q in questions
    ]) if questions else '<div class="empty"><p>Nenhuma pergunta pendente.</p></div>')

    return html


@app.route('/admin/teach', methods=['POST'])
def teach_ednna():
    """Adiciona nova pergunta/resposta ao conhecimento"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Acesso negado'}), 403

    data = request.get_json()
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    category = data.get('category', '').strip()

    if not all([question, answer, category]):
        return jsonify({"error": "Campos obrigatórios"}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "DB"}), 500

    cursor = connection.cursor()
    try:
        # Gerar keywords simples
        keywords = ",".join(set(
            w for w in re.findall(r'\w+', answer.lower()) if len(w) > 4
        )[:15]) or "geral"

        cursor.execute("""
            INSERT INTO knowledge_base (question, answer, category, keywords, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE answer = VALUES(answer), updated_at = NOW()
        """, (question, answer, category, keywords))

        cursor.execute("""
            UPDATE unknown_questions SET status = 'answered' WHERE question = %s
        """, (question,))

        connection.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()


# Rota de login simples
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == os.getenv('ADMIN_PASSWORD', 'netunna123'):
            session['admin_logged_in'] = True
            return redirect('/admin/learn')
        return 'Senha incorreta', 401
    return '''
        <h3>Login Admin</h3>
        <form method="post">
            <input type="password" name="password" placeholder="Senha" required>
            <button type="submit">Entrar</button>
        </form>
    '''


# Proteger as rotas
@app.before_request
def require_login():
    if '/admin/' in request.path and not request.endpoint == 'admin_login':
        if not session.get('admin_logged_in') and request.endpoint != 'static':
            return redirect('/admin/login')


def get_chat_response(message, user_id, last_user_question=None):
    """Processa a mensagem — consulta banco primeiro, filtra só se necessário, com contexto inteligente"""
    connection = get_db_connection()
    if not connection:
        return {'response': 'Erro de conexão com o banco de dados', 'intent': 'error'}

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        mensagem_lower = message.strip().lower()

        # 🔹 NÍVEL 2: Carrega perfil do usuário
        profile = get_or_create_user_profile(user_id, connection)

        # 🔹 Detecta e salva informações do perfil
        name_match = None
        company_match = None

        # ✅ Correção 1: Regex separadas para evitar erro de lookbehind
        nome_pattern = r"(?:me chamo|meu nome é)\s+(\w+)"
        empresa_pattern = r"(?:trabalho na|empresa)\s+(\w+)"

        nome_busca = re.search(nome_pattern, mensagem_lower)
        if nome_busca and not profile['name']:
            name = nome_busca.group(1).title()
            update_user_profile(user_id, {'name': name}, connection)
            profile['name'] = name

        empresa_busca = re.search(empresa_pattern, mensagem_lower)
        if empresa_busca and not profile['company']:
            company = empresa_busca.group(1).title()
            update_user_profile(user_id, {'company': company}, connection)
            profile['company'] = company

        # Detecta ERP
        for erp in ['totvs', 'sap', 'rm', 'protheus', 'oracle', 'sankhya']:
            if erp in mensagem_lower and not profile['erp']:
                update_user_profile(user_id, {'erp': erp.upper()}, connection)
                profile['erp'] = erp.upper()
                break

        # 🔹 Prefixo personalizado
        response_prefix = ""
        if profile['name']:
            response_prefix += f"Olá, {profile['name']}! "
        if profile['company']:
            response_prefix += f"Da {profile['company']}, certo? "

        # ✅ 1. LÓGICA DE CONTEXTO: Se pergunta é curta, use a anterior
        if len(message.split()) <= 2 and last_user_question:
            last_lower = last_user_question.lower()
            msg_lower = message.lower()

            if "teia" in last_lower:
                if "card" in last_lower:
                    message = "o que é o teia card"
                elif "values" in last_lower:
                    message = "o que é o teia values"
                elif "edi" in last_lower:
                    message = "o que é edi"
                elif "bpo" in last_lower:
                    message = "o que é bpo financeiro"
            elif any(word in last_lower for word in ["chargeback", "estorno"]):
                if any(word in msg_lower for word in ["que pena", "poxa", "é triste"]):
                    message = "como reduzir chargebacks"
            elif "erp" in last_lower and "não integra" in last_lower:
                if any(word in msg_lower for word in ["e", "e ai", "e o"]):
                    message = "quais erps a netunna integra"
            elif "bancos" in last_lower:
                if any(word in msg_lower for word in ["e", "e os"]):
                    message = "quais adquirentes a netunna integra"

        # ✅ 2. FILTRO DE CONTEXTOS ABSURDOS
        if is_absurd_context(message):
            filtered_response = (
                "Prefiro focar em ajudar com conciliação, EDI, BPO e nossos produtos. "
                "Posso te ajudar com algo nessa área?"
            )
            conversation_id = get_or_create_conversation(user_id, connection)
            log_message(conversation_id, message, True, connection)
            log_message(conversation_id, filtered_response, False, connection)
            return {
                'response': filtered_response,
                'intent': 'filtered',
                'confidence': 0.99
            }

        # ✅ 3. FILTRO DE OFENSAS E EXTRACÇÃO DE DADOS
        if is_offensive_or_absurd(message):
            filtered_response = get_appropriate_response_for_offensive(message)
            conversation_id = get_or_create_conversation(user_id, connection)
            log_message(conversation_id, message, True, connection)
            log_message(conversation_id, filtered_response, False, connection)
            return {
                'response': filtered_response,
                'intent': 'filtered',
                'confidence': 0.99
            }

        # ✅ 4. SAUDAÇÕES
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
                final_answer = response_prefix + result['answer'] if response_prefix else result['answer']
                return {
                    'response': final_answer,
                    'intent': result['category'],
                    'confidence': 0.95
                }

        # ✅ 5. NORMALIZAÇÃO DE TERMOS
        termos_produto = {
            'teiacard': 'teia card',
            'teiacards': 'teia card',
            'teia cards': 'teia card',
            'teiavalue': 'teia values',
            'teiavalues': 'teia values'
        }
        mensagem_normalizada = mensagem_lower
        for termo_errado, termo_correto in termos_produto.items():
            mensagem_normalizada = re.sub(r'\b' + re.escape(termo_errado) + r'\b', termo_correto, mensagem_normalizada)

        # ✅ 6. BUSCA EXATA NO BANCO
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

        # ✅ 7. BUSCA POR SIMILARIDADE (FULL-TEXT) — SCORE > 0.7
        if not result and len(mensagem_normalizada.split()) > 1:
            query_fulltext = """
            SELECT answer, category, 
                   MATCH(question, keywords, answer) AGAINST(%s IN NATURAL LANGUAGE MODE) as score
            FROM knowledge_base
            WHERE MATCH(question, keywords, answer) AGAINST(%s IN NATURAL LANGUAGE MODE)
            AND MATCH(question, keywords, answer) AGAINST(%s IN NATURAL LANGUAGE MODE) > 0.7
            ORDER BY score DESC
            LIMIT 1
            """
            cursor.execute(query_fulltext, (mensagem_normalizada, mensagem_normalizada, mensagem_normalizada))
            result = cursor.fetchone()

        # ✅ 8. REGISTRAR MENSAGEM DO USUÁRIO
        conversation_id = get_or_create_conversation(user_id, connection)
        log_message(conversation_id, message, True, connection)

        # ✅ 9. SE ENCONTROU RESPOSTA NO BANCO
        if result:
            log_message(conversation_id, result['answer'], False, connection)
            final_answer = response_prefix + result['answer'] if response_prefix else result['answer']
            return {
                'response': final_answer,
                'intent': result['category'],
                'confidence': 0.9
            }

        # ✅ 10. NÍVEL 3: APRENDIZADO ATIVO — Registra perguntas não respondidas
        unknown_question = message.strip()
        cursor.execute("""
            SELECT id FROM unknown_questions 
            WHERE question = %s AND created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """, (unknown_question,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO unknown_questions (user_id, question, conversation_id, status)
                VALUES (%s, %s, %s, 'pending')
            """, (user_id, unknown_question, conversation_id))
            connection.commit()

        # ✅ 11. RESPOSTA PADRÃO SEGURA — Com sugestão baseada no contexto
        if last_user_question and "teia card" in last_user_question.lower():
            suggestion = "Quer saber mais sobre o Teia Card?"
        elif "bpo" in last_user_question.lower():
            suggestion = "Posso te explicar a diferença entre BPO Técnico e Premium?"
        elif "edi" in last_user_question.lower():
            suggestion = "Precisa de ajuda com integração via SFTP ou VAN?"
        else:
            suggestion = "Posso te ajudar a esclarecer melhor?"

        default_response = f"Desculpe, ainda não sei responder isso. {suggestion}"
        final_response = response_prefix + default_response if response_prefix else default_response
        log_message(conversation_id, final_response, False, connection)

        return {
            'response': final_response,
            'intent': 'unknown',
            'confidence': 0.1
        }

    except Error as e:
        logger.error(f"Erro no banco de dados: {e}")
        return {'response': 'Erro ao processar sua mensagem', 'intent': 'error'}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_or_create_user_profile(user_id, connection):
    """Obtém ou cria perfil de usuário"""
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
            return {
                'user_id': user_id,
                'name': None,
                'company': None,
                'erp': None,
                'adquirente': None,
                'last_issue': None
            }
        return profile
    except Error as e:
        logger.error(f"Erro ao buscar perfil: {e}")
        return {'user_id': user_id}
    finally:
        if cursor:
            cursor.close()


def update_user_profile(user_id, updates, connection):
    """Atualiza perfil do usuário"""
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
        if cursor:
            cursor.close()


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
        if cursor:
            cursor.close()


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
        if cursor:
            cursor.close()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
