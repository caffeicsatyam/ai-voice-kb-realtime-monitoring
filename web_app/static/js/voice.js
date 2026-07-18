/**
 * QuickFund Voice Agent — Browser Voice & Chat Controller
 */

class VoiceAgent {
    constructor(agentType = 'loan') {
        this.agentType = agentType;
        this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        this.isRecording = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.messageContainer = document.getElementById('chat-messages');
        this.inputField = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
        this.micBtn = document.getElementById('mic-btn');
        this.statusEl = document.getElementById('connection-status');
        
        this.setupEventListeners();
        this.setupSpeechRecognition();
        this.addSystemMessage('Connected to QuickFund AI Agent. Type a message or click the microphone to start a voice conversation.');
    }

    setupEventListeners() {
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        if (this.inputField) {
            this.inputField.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }
        if (this.micBtn) {
            this.micBtn.addEventListener('click', () => this.toggleRecording());
        }
    }

    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('Web Speech API not available');
            if (this.micBtn) this.micBtn.style.display = 'none';
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = this.getLanguage();
        
        this.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(r => r[0].transcript)
                .join('');
            
            if (this.inputField) {
                this.inputField.value = transcript;
            }
            
            if (event.results[0].isFinal) {
                this.sendMessage(transcript);
            }
        };
        
        this.recognition.onend = () => {
            this.isRecording = false;
            if (this.micBtn) this.micBtn.classList.remove('recording');
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isRecording = false;
            if (this.micBtn) this.micBtn.classList.remove('recording');
        };
    }

    getLanguage() {
        switch (this.agentType) {
            case 'philippines': return 'fil-PH';
            case 'indonesia': return 'id-ID';
            default: return 'en-US';
        }
    }

    toggleRecording() {
        if (!this.recognition) {
            this.addSystemMessage('Voice recognition not available in this browser. Please type your message.');
            return;
        }
        
        if (this.isRecording) {
            this.recognition.stop();
            this.isRecording = false;
            if (this.micBtn) this.micBtn.classList.remove('recording');
        } else {
            this.recognition.start();
            this.isRecording = true;
            if (this.micBtn) this.micBtn.classList.add('recording');
        }
    }

    async sendMessage(text = null) {
        const message = text || (this.inputField ? this.inputField.value.trim() : '');
        if (!message) return;
        
        // Show user message
        this.addMessage(message, 'user');
        if (this.inputField) this.inputField.value = '';
        
        // Show typing indicator
        const typingEl = this.showTyping();
        
        // Disable input
        this.setInputState(false);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    agent: this.agentType,
                    session_id: this.sessionId,
                }),
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            if (typingEl) typingEl.remove();
            
            if (data.error) {
                this.addMessage(`Error: ${data.error}`, 'agent');
            } else {
                this.addMessage(data.response, 'agent');
                
                // Speak the response using TTS
                this.speak(data.response);
            }
        } catch (error) {
            if (typingEl) typingEl.remove();
            this.addMessage(`Connection error: ${error.message}`, 'agent');
        }
        
        this.setInputState(true);
    }

    addMessage(text, role) {
        if (!this.messageContainer) return;
        
        const div = document.createElement('div');
        div.className = `message ${role}`;
        
        const content = document.createElement('div');
        content.textContent = text;
        div.appendChild(content);
        
        const meta = document.createElement('div');
        meta.className = 'meta';
        meta.textContent = new Date().toLocaleTimeString();
        div.appendChild(meta);
        
        this.messageContainer.appendChild(div);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    addSystemMessage(text) {
        if (!this.messageContainer) return;
        
        const div = document.createElement('div');
        div.className = 'message agent';
        div.style.opacity = '0.8';
        div.style.fontStyle = 'italic';
        div.textContent = text;
        this.messageContainer.appendChild(div);
    }

    showTyping() {
        if (!this.messageContainer) return null;
        
        const div = document.createElement('div');
        div.className = 'typing-indicator';
        div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        this.messageContainer.appendChild(div);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        return div;
    }

    setInputState(enabled) {
        if (this.inputField) this.inputField.disabled = !enabled;
        if (this.sendBtn) this.sendBtn.disabled = !enabled;
    }

    speak(text) {
        if (!this.synthesis) return;
        
        // Cancel any ongoing speech
        this.synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        
        // Set voice based on agent type
        const voices = this.synthesis.getVoices();
        switch (this.agentType) {
            case 'philippines':
                utterance.lang = 'en-PH';
                break;
            case 'indonesia':
                utterance.lang = 'id-ID';
                break;
            default:
                utterance.lang = 'en-US';
        }
        
        this.synthesis.speak(utterance);
    }
}


/**
 * Nudge Dashboard Controller
 */
class NudgeDashboard {
    constructor() {
        this.ws = null;
        this.nudgeFeed = document.getElementById('nudge-feed');
        this.nudgeCount = 0;
        this.latencyData = [];
        
        this.connectWebSocket();
    }

    connectWebSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${location.host}/ws/nudges`);
        
        this.ws.onopen = () => {
            console.log('Nudge dashboard WebSocket connected');
            this.updateStatus('Connected', 'green');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.addNudge(data);
            } catch (e) {
                console.error('Failed to parse nudge data:', e);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('Disconnected', 'red');
            // Reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    addNudge(data) {
        if (!this.nudgeFeed) return;
        
        this.nudgeCount++;
        
        const div = document.createElement('div');
        let priority = 'medium';
        let signalType = '';
        let nudgeText = data.analysis || '';
        
        // Parse the analysis for display
        if (data.analysis) {
            if (data.analysis.includes('high') || data.analysis.includes('frustration') || data.analysis.includes('disclosure')) {
                priority = 'high';
            } else if (data.analysis.includes('suppressed') || data.analysis.includes('No actionable')) {
                priority = 'suppressed';
            } else if (data.analysis.includes('low') || data.analysis.includes('callback')) {
                priority = 'low';
            }
        }
        
        div.className = `nudge-item ${priority}`;
        div.innerHTML = `
            <div class="nudge-signal">${data.timestamp || ''} — ${priority.toUpperCase()}</div>
            <div class="nudge-text">${nudgeText.substring(0, 200)}</div>
            <div class="nudge-meta">Chunk: "${(data.chunk || '').substring(0, 80)}..."</div>
        `;
        
        this.nudgeFeed.insertBefore(div, this.nudgeFeed.firstChild);
        
        // Update counter
        const counter = document.getElementById('nudge-count');
        if (counter) counter.textContent = this.nudgeCount;
    }

    updateStatus(status, color) {
        const el = document.getElementById('ws-status');
        if (el) {
            el.innerHTML = `<span class="status-dot ${color}"></span>${status}`;
        }
    }
}
