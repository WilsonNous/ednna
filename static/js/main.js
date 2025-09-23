let userName = null;

window.addEventListener('load', () => {
    const savedName = localStorage.getItem('savedUserName');
    if (savedName) {
        userName = savedName;
        updateHeader();
    }
});

document.getElementById('loginBtn').addEventListener('click', () => {
    document.getElementById('loginModal').style.display = 'flex';
});

function closeLogin() {
    document.getElementById('loginModal').style.display = 'none';
}

function saveLogin() {
    const name = document.getElementById('nameInput').value.trim();
    const remember = document.getElementById('rememberName').checked;

    if (!name) {
        alert("Por favor, digite seu nome.");
        return;
    }

    userName = name;
    if (remember) {
        localStorage.setItem('savedUserName', name);
    } else {
        localStorage.removeItem('savedUserName');
    }
    closeLogin();
    updateHeader();
    addMessage(`Olá, ${name}! Que bom te ver. Como posso te ajudar hoje?`, 'bot');
}

function updateHeader() {
    const btn = document.querySelector('.login-btn');
    if (userName && btn) {
        btn.innerHTML = `<span class="user-badge">${userName}</span>`;
        btn.removeEventListener('click', openLogin);
    }
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';

    const typingDiv = createTypingIndicator();
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                user_id: getUserID()
            })
        });

        typingDiv.remove();

        const data = await response.json();
        if (response.ok) {
            addMessage(data.response, 'bot');
        } else {
            addMessage('Desculpe, tive um problema interno.', 'bot');
        }
    } catch (error) {
        typingDiv.remove();
        addMessage('Erro de conexão. Verifique sua internet.', 'bot');
    }
}

function createTypingIndicator() {
    const div = document.createElement('div');
    div.classList.add('message', 'bot-message');
    div.innerHTML = '<em>Ednna está digitando...</em>';
    return div;
}

function addMessage(text, sender) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');

    if (sender === 'bot') {
        const container = document.createElement('div');
        container.style.display = 'flex';
        container.style.alignItems = 'flex-start';
        container.style.gap = '12px';

        const avatar = document.createElement('img');
        avatar.src = "/static/assets/ednna-avat2.png";
        avatar.alt = "Ednna";
        avatar.style.width = "32px";
        avatar.style.height = "32px";
        avatar.style.borderRadius = "50%";
        avatar.style.flexShrink = "0";

        const content = document.createElement('div');

        if (typeof marked !== 'undefined') {
            try {
                content.innerHTML = marked.parse(text);
            } catch (e) {
                content.textContent = text;
            }
        } else {
            content.textContent = text;
        }

        container.appendChild(avatar);
        container.appendChild(content);
        messageDiv.appendChild(container);
    } else {
        messageDiv.textContent = text;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ✅ VINCULA O EVENTO DE ENTER AO CAMPO DE ENTRADA
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault(); // Evita submit de formulário (caso esteja em form)
        sendMessage();
    }
});

function getUserID() {
    if (!sessionStorage.getItem('userSessionId')) {
        const id = Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('userSessionId', id);
    }
    return sessionStorage.getItem('userSessionId');
}
// ✅ CORREÇÃO: Adiciona evento de clique ao botão "Enviar"
document.getElementById('sendBtn').addEventListener('click', sendMessage);
