let userName = null;

// Carrega nome salvo ao iniciar
window.addEventListener('load', () => {
    const savedName = localStorage.getItem('savedUserName');
    if (savedName) {
        userName = savedName;
        updateHeader();
    }
});

// Abre modal de login
document.getElementById('loginBtn').addEventListener('click', () => {
    document.getElementById('loginModal').style.display = 'flex';
});

// Fecha modal
function closeLogin() {
    document.getElementById('loginModal').style.display = 'none';
}

// Salva login
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

// Atualiza cabeçalho com nome
function updateHeader() {
    const btn = document.querySelector('.login-btn');
    if (userName && btn) {
        btn.innerHTML = `<span class="user-badge">${userName}</span>`;
        btn.removeEventListener('click', openLogin); // Evita múltiplos listeners
    }
}

// Envia mensagem
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
        const response = await fetch('/
