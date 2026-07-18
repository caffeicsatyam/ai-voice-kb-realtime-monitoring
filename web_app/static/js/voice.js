/**
 * QuickFund Voice Agent — Browser Voice & Chat Controller
 */

class VoiceAgent {
    constructor(agentType = 'loan') {
        this.agentType = agentType;
        this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        this.isRecording = false;
        this.isMuted = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.messageContainer = document.getElementById('chat-messages');
        this.inputField = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
        this.micBtn = document.getElementById('mic-btn');
        this.stopVoiceBtn = document.getElementById('stop-voice-btn');
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
        if (this.stopVoiceBtn) {
            this.stopVoiceBtn.addEventListener('click', () => this.toggleVoice());
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
        if (!this.synthesis || this.isMuted) return;
        
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

    toggleVoice() {
        this.isMuted = !this.isMuted;
        if (this.isMuted) {
            if (this.synthesis) {
                this.synthesis.cancel();
            }
            if (this.stopVoiceBtn) {
                this.stopVoiceBtn.textContent = '🔇';
                this.stopVoiceBtn.title = 'Unmute Agent Voice';
                this.stopVoiceBtn.style.background = 'rgba(239, 68, 68, 0.2)';
                this.stopVoiceBtn.style.color = 'var(--accent-red)';
                this.stopVoiceBtn.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            }
        } else {
            if (this.stopVoiceBtn) {
                this.stopVoiceBtn.textContent = '🔊';
                this.stopVoiceBtn.title = 'Mute Agent Voice';
                this.stopVoiceBtn.style.background = 'rgba(16, 185, 129, 0.2)';
                this.stopVoiceBtn.style.color = 'var(--accent-green)';
                this.stopVoiceBtn.style.borderColor = 'rgba(16, 185, 129, 0.3)';
            }
        }
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
        this.suppressedCount = 0;
        this.signalCounts = {};
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

        this.ws.onerror = () => {
            this.updateStatus('Connection issue', 'orange');
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('Disconnected', 'red');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    addNudge(data) {
        if (!this.nudgeFeed) return;

        this.clearPlaceholder();

        const isTranscript = data.event_type === 'transcript';
        const isSuppressed = data.event_type === 'suppressed' || data.emitted === false;
        const isNudge = !isTranscript && !isSuppressed;

        if (isNudge) {
            this.nudgeCount++;
            this.updateText('nudge-count', this.nudgeCount);
            this.updateText('total-nudges', this.nudgeCount);
        } else if (isSuppressed) {
            this.suppressedCount++;
            this.updateText('suppressed-count', this.suppressedCount);
        }

        const signal = data.signal || data.signal_type || '';
        if (signal && !isTranscript) {
            this.signalCounts[signal] = (this.signalCounts[signal] || 0) + 1;
            this.updateSignalCount(signal);
        }

        const div = document.createElement('div');
        const priority = this.resolvePriority(data, isTranscript, isSuppressed);
        div.className = `nudge-item ${priority}`;

        const title = document.createElement('div');
        title.className = 'nudge-signal';
        title.textContent = this.eventTitle(data, priority, isTranscript, isSuppressed);

        const text = document.createElement('div');
        text.className = 'nudge-text';
        text.textContent = this.eventText(data, isTranscript, isSuppressed);

        const meta = document.createElement('div');
        meta.className = 'nudge-meta';
        meta.textContent = this.eventMeta(data, signal, isTranscript);

        div.appendChild(title);
        div.appendChild(text);
        div.appendChild(meta);
        this.nudgeFeed.insertBefore(div, this.nudgeFeed.firstChild);
    }

    clearPlaceholder() {
        const placeholder = this.nudgeFeed.querySelector('p');
        if (placeholder) placeholder.remove();
    }

    resolvePriority(data, isTranscript, isSuppressed) {
        if (isTranscript) return 'transcript';
        if (isSuppressed) return 'suppressed';
        if (data.priority) return data.priority;

        const analysis = (data.analysis || '').toLowerCase();
        if (analysis.includes('high') || analysis.includes('frustration') || analysis.includes('disclosure')) {
            return 'high';
        }
        if (analysis.includes('low') || analysis.includes('callback')) {
            return 'low';
        }
        return 'medium';
    }

    eventTitle(data, priority, isTranscript, isSuppressed) {
        const timestamp = data.timestamp || '';
        if (isTranscript) {
            return `${timestamp} - ${(data.speaker || 'speaker').toUpperCase()}`;
        }
        if (isSuppressed) {
            return `${timestamp} - SUPPRESSED`;
        }
        const signal = (data.signal || data.signal_type || 'nudge').replaceAll('_', ' ');
        return `${timestamp} - ${priority.toUpperCase()} - ${signal}`;
    }

    eventText(data, isTranscript, isSuppressed) {
        if (isTranscript) return data.chunk || '';
        if (data.nudge) return data.nudge;
        if (data.analysis) return data.analysis;
        if (isSuppressed && data.reason) return `Suppressed: ${data.reason}`;
        return 'No actionable signal detected.';
    }

    eventMeta(data, signal, isTranscript) {
        if (isTranscript) return 'Transcript chunk';

        const parts = [];
        if (signal) parts.push(`Signal: ${signal}`);
        if (data.confidence !== undefined && data.confidence !== null) parts.push(`Confidence: ${data.confidence}`);
        if (data.evidence) parts.push(`Evidence: ${String(data.evidence).substring(0, 80)}`);
        if (data.chunk) parts.push(`Chunk: ${String(data.chunk).substring(0, 80)}...`);
        return parts.join(' | ');
    }

    updateSignalCount(signal) {
        const ids = {
            missed_cross_sell: 'sig-cross',
            missing_disclosure: 'sig-disc',
            frustration: 'sig-frust',
            payment_difficulty: 'sig-pay',
            callback_need: 'sig-cb',
            noisy_segment: 'sig-noise',
        };
        const id = ids[signal];
        if (id) this.updateText(id, this.signalCounts[signal]);
    }

    updateText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    updateStatus(status, color) {
        const html = `<span class="status-dot ${color}"></span>${status}`;
        const header = document.getElementById('ws-status');
        const pipeline = document.getElementById('pipeline-ws');
        if (header) header.innerHTML = html;
        if (pipeline) pipeline.innerHTML = html;
    }
}