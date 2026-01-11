/**
 * Nova AI - Frontend Application
 * World-class AI Personal Assistant
 */

const API_BASE = 'http://localhost:8000';
let isProcessing = false;
let conversationHistory = [];
let currentTheme = 'dark';

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    addSidebarOverlay();
    initializeTheme();
});

async function initializeApp() {
    await checkApiHealth();
}

function setupEventListeners() {
    const input = document.getElementById('message-input');
    
    // Auto-resize textarea
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 150) + 'px';
    });
    
    // Handle Enter key
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Close sidebar on overlay click
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('sidebar-overlay')) {
            toggleSidebar();
        }
    });
    
    // Smooth scroll for landing page links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

function addSidebarOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);
}

// ============================================================================
// Theme Toggle Functions
// ============================================================================

function initializeTheme() {
    // Check for saved theme preference or default to dark
    const savedTheme = localStorage.getItem('nova-theme') || 'dark';
    setTheme(savedTheme);
}

function toggleTheme() {
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    currentTheme = theme;
    localStorage.setItem('nova-theme', theme);
    
    if (theme === 'light') {
        document.body.classList.add('light-theme');
    } else {
        document.body.classList.remove('light-theme');
    }
}

// ============================================================================
// Landing Page Navigation
// ============================================================================

function enterChatExperience() {
    document.body.classList.add('chat-mode');
    document.getElementById('landing-page').classList.add('hidden');
    document.getElementById('chat-app').classList.add('active');
    
    // Focus on input after transition
    setTimeout(() => {
        document.getElementById('message-input').focus();
    }, 300);
}

function backToLanding() {
    document.body.classList.remove('chat-mode');
    document.getElementById('landing-page').classList.remove('hidden');
    document.getElementById('chat-app').classList.remove('active');
    
    // Scroll to top of landing page
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToFeatures() {
    document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
}

// ============================================================================
// API Functions
// ============================================================================

async function checkApiHealth() {
    const statusBadge = document.getElementById('status-badge');
    const statusText = statusBadge.querySelector('.status-text');
    
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        if (response.ok) {
            statusBadge.classList.add('connected');
            statusBadge.classList.remove('error');
            statusText.textContent = 'Connected';
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        statusBadge.classList.add('error');
        statusBadge.classList.remove('connected');
        statusText.textContent = 'Offline';
        console.error('API health check failed:', error);
    }
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message || isProcessing) return;
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Show chat interface
    showChatInterface();
    
    // Add user message
    addMessage(message, 'user');
    conversationHistory.push({ role: 'user', content: message });
    
    // Show loading
    const loadingId = showTypingIndicator();
    isProcessing = true;
    updateSendButton();
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        removeTypingIndicator(loadingId);
        addMessage(data.response, 'assistant', data.timestamp);
        conversationHistory.push({ role: 'assistant', content: data.response });
        
    } catch (error) {
        removeTypingIndicator(loadingId);
        const errorMsg = `I'm having trouble connecting to the server. Please make sure the backend is running on port 8000.\n\nError: ${error.message}`;
        addMessage(errorMsg, 'assistant');
        console.error('Error:', error);
    } finally {
        isProcessing = false;
        updateSendButton();
    }
}

// ============================================================================
// UI Functions
// ============================================================================

function showChatInterface() {
    const heroWelcome = document.getElementById('hero-welcome');
    const chatMessages = document.getElementById('chat-messages');
    
    heroWelcome.classList.add('hidden');
    chatMessages.classList.add('active');
}

function showWelcomeScreen() {
    const heroWelcome = document.getElementById('hero-welcome');
    const chatMessages = document.getElementById('chat-messages');
    
    heroWelcome.classList.remove('hidden');
    chatMessages.classList.remove('active');
}

function addMessage(text, sender, timestamp = null) {
    const container = document.getElementById('chat-messages');
    const time = timestamp ? formatTime(timestamp) : formatTime(new Date().toISOString());
    const avatar = sender === 'user' ? '👤' : '✨';
    
    const messageEl = document.createElement('div');
    messageEl.className = `message ${sender}`;
    messageEl.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-bubble">
            <div class="message-text">${formatMessageText(text)}</div>
            <div class="message-time">
                <span>${time}</span>
            </div>
        </div>
    `;
    
    container.appendChild(messageEl);
    scrollToBottom();
}

function formatMessageText(text) {
    // Escape HTML
    let formatted = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Convert line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Bold text
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    return formatted;
}

function formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const id = 'typing-' + Date.now();
    
    const typingEl = document.createElement('div');
    typingEl.className = 'message assistant';
    typingEl.id = id;
    typingEl.innerHTML = `
        <div class="message-avatar">✨</div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    container.appendChild(typingEl);
    scrollToBottom();
    
    return id;
}

function removeTypingIndicator(id) {
    const typing = document.getElementById(id);
    if (typing) {
        typing.remove();
    }
}

function scrollToBottom() {
    const chatArea = document.querySelector('.chat-area');
    chatArea.scrollTop = chatArea.scrollHeight;
}

function updateSendButton() {
    const btn = document.getElementById('send-btn');
    btn.disabled = isProcessing;
}

// ============================================================================
// Clear Chat
// ============================================================================

function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    conversationHistory = [];
    showWelcomeScreen();
}

// ============================================================================
// Quick Actions
// ============================================================================

function sendQuickAction(message) {
    const input = document.getElementById('message-input');
    input.value = message;
    sendMessage();
    
    // Close sidebar on mobile
    const sidebar = document.getElementById('sidebar');
    if (sidebar.classList.contains('open')) {
        toggleSidebar();
    }
}

// ============================================================================
// Mobile Sidebar
// ============================================================================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
    
    // Prevent body scroll when sidebar is open
    document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
}
