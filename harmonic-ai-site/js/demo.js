/* ==========================================================================
   Harmonic AI - Démonstration Interactive
   Interface de test et validation des fonctionnalités
   ========================================================================== */

class InteractiveDemo {
    constructor() {
        this.demoContainer = document.querySelector('.demo-card');
        this.demoContent = document.querySelector('.demo-content');
        this.demoInput = null;
        this.demoOutput = null;
        this.demoControls = null;
        
        this.config = {
            apiEndpoint: 'https://api.harmonic.ai/v1/generate',
            demoMode: true,
            maxTokens: 200,
            temperature: 0.0,
            verifiedMode: true
        };
        
        this.responses = {
            fr: {
                defaultQuestion: "Qui es-tu?",
                defaultResponse: "Je suis Deterministic AI, une IA conçue par Harmonic AI Corporation.",
                explanation: "Cette réponse est garantie déterministe : même prompt ⇒ même sortie.",
                placeholder: "Posez votre question ici...",
                sendButton: "Envoyer",
                clearButton: "Effacer",
                loadingText: "Génération en cours...",
                errorText: "Erreur de génération. Veuillez réessayer.",
                modeLabel: "Mode :",
                deterministicMode: "Déterministe",
                verifiedMode: "Vérifié",
                cacheHit: "Cache : OUI",
                cacheMiss: "Cache : NON"
            },
            en: {
                defaultQuestion: "Who are you?",
                defaultResponse: "I am Deterministic AI, an AI designed by Harmonic AI Corporation.",
                explanation: "This response is deterministically guaranteed: same prompt ⇒ same output.",
                placeholder: "Ask your question here...",
                sendButton: "Send",
                clearButton: "Clear",
                loadingText: "Generating...",
                errorText: "Generation error. Please try again.",
                modeLabel: "Mode:",
                deterministicMode: "Deterministic",
                verifiedMode: "Verified",
                cacheHit: "Cache: YES",
                cacheMiss: "Cache: NO"
            }
        };
        
        this.currentLanguage = 'fr';
        this.isGenerating = false;
        this.responseHistory = [];
    }
    
    init() {
        if (!this.demoContainer || !this.demoContent) {
            console.error('Éléments de démonstration non trouvés');
            return;
        }
        
        console.log('Démonstration interactive initialisée');
        
        // Créer l'interface interactive
        this.createInteractiveInterface();
        
        // Configurer les événements
        this.setupEventListeners();
        
        // Initialiser avec la langue actuelle
        this.updateLanguage(this.currentLanguage);
    }
    
    createInteractiveInterface() {
        // Sauvegarder le contenu original
        const originalContent = this.demoContent.innerHTML;
        
        // Créer la nouvelle interface
        this.demoContent.innerHTML = `
            <div class="demo-interface">
                <div class="demo-controls">
                    <div class="mode-selector">
                        <label>${this.responses[this.currentLanguage].modeLabel}</label>
                        <div class="mode-buttons">
                            <button class="mode-btn active" data-mode="deterministic">
                                ${this.responses[this.currentLanguage].deterministicMode}
                            </button>
                            <button class="mode-btn" data-mode="verified">
                                ${this.responses[this.currentLanguage].verifiedMode}
                            </button>
                        </div>
                    </div>
                    
                    <div class="cache-indicator">
                        <span class="cache-status">${this.responses[this.currentLanguage].cacheMiss}</span>
                    </div>
                </div>
                
                <div class="demo-input-container">
                    <textarea 
                        class="demo-input" 
                        placeholder="${this.responses[this.currentLanguage].placeholder}"
                        rows="3"
                    >${this.responses[this.currentLanguage].defaultQuestion}</textarea>
                    
                    <div class="input-actions">
                        <button class="btn btn-primary send-btn">
                            ${this.responses[this.currentLanguage].sendButton}
                        </button>
                        <button class="btn btn-outline clear-btn">
                            ${this.responses[this.currentLanguage].clearButton}
                        </button>
                    </div>
                </div>
                
                <div class="demo-output-container">
                    <div class="output-header">
                        <span class="output-label">Réponse :</span>
                        <span class="response-id">ID: SHA256-...</span>
                    </div>
                    <div class="demo-output">
                        ${this.responses[this.currentLanguage].defaultResponse}
                    </div>
                    <div class="output-footer">
                        <span class="explanation">
                            ${this.responses[this.currentLanguage].explanation}
                        </span>
                    </div>
                </div>
                
                <div class="demo-history">
                    <div class="history-header">
                        <span>Historique des réponses</span>
                        <button class="btn btn-outline history-clear">Effacer l'historique</button>
                    </div>
                    <div class="history-content">
                        <!-- Les réponses historiques apparaîtront ici -->
                    </div>
                </div>
            </div>
        `;
        
        // Référencer les éléments
        this.demoInput = this.demoContent.querySelector('.demo-input');
        this.demoOutput = this.demoContent.querySelector('.demo-output');
        this.demoControls = this.demoContent.querySelector('.demo-controls');
        this.sendButton = this.demoContent.querySelector('.send-btn');
        this.clearButton = this.demoContent.querySelector('.clear-btn');
        this.modeButtons = this.demoContent.querySelectorAll('.mode-btn');
        this.cacheStatus = this.demoContent.querySelector('.cache-status');
        this.responseIdElement = this.demoContent.querySelector('.response-id');
        this.historyContent = this.demoContent.querySelector('.history-content');
        this.historyClearButton = this.demoContent.querySelector('.history-clear');
    }
    
    setupEventListeners() {
        if (!this.sendButton || !this.clearButton) return;
        
        // Bouton d'envoi
        this.sendButton.addEventListener('click', () => this.generateResponse());
        
        // Bouton d'effacement
        this.clearButton.addEventListener('click', () => this.clearInput());
        
        // Entrée dans le champ de texte
        this.demoInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.generateResponse();
            }
        });
        
        // Sélection du mode
        this.modeButtons.forEach(button => {
            button.addEventListener('click', () => this.switchMode(button.dataset.mode));
        });
        
        // Effacer l'historique
        if (this.historyClearButton) {
            this.historyClearButton.addEventListener('click', () => this.clearHistory());
        }
    }
    
    updateLanguage(lang) {
        if (!this.responses[lang]) return;
        
        this.currentLanguage = lang;
        const texts = this.responses[lang];
        
        // Mettre à jour les textes
        if (this.demoInput) {
            this.demoInput.placeholder = texts.placeholder;
            
            // Si le champ est vide ou contient la question par défaut dans l'autre langue
            const currentValue = this.demoInput.value;
            if (!currentValue || currentValue === this.responses[lang === 'fr' ? 'en' : 'fr'].defaultQuestion) {
                this.demoInput.value = texts.defaultQuestion;
            }
        }
        
        if (this.sendButton) {
            this.sendButton.textContent = texts.sendButton;
        }
        
        if (this.clearButton) {
            this.clearButton.textContent = texts.clearButton;
        }
        
        if (this.demoOutput && !this.isGenerating) {
            this.demoOutput.textContent = texts.defaultResponse;
        }
        
        // Mettre à jour les labels de mode
        const modeLabels = this.demoContent.querySelectorAll('.mode-selector label');
        if (modeLabels.length > 0) {
            modeLabels[0].textContent = texts.modeLabel;
        }
        
        const deterministicBtn = this.demoContent.querySelector('[data-mode="deterministic"]');
        const verifiedBtn = this.demoContent.querySelector('[data-mode="verified"]');
        
        if (deterministicBtn) {
            deterministicBtn.textContent = texts.deterministicMode;
        }
        
        if (verifiedBtn) {
            verifiedBtn.textContent = texts.verifiedMode;
        }
        
        // Mettre à jour l'explication
        const explanation = this.demoContent.querySelector('.explanation');
        if (explanation) {
            explanation.textContent = texts.explanation;
        }
        
        // Mettre à jour le cache
        this.updateCacheStatus(false);
    }
    
    switchMode(mode) {
        if (!this.modeButtons) return;
        
        // Mettre à jour les boutons
        this.modeButtons.forEach(button => {
            button.classList.toggle('active', button.dataset.mode === mode);
        });
        
        // Mettre à jour la configuration
        this.config.verifiedMode = mode === 'verified';
        
        console.log(`Mode changé: ${mode}`);
        
        // Régénérer la réponse si une question est présente
        if (this.demoInput && this.demoInput.value.trim()) {
            this.generateResponse();
        }
    }
    
    async generateResponse() {
        if (this.isGenerating) return;
        
        const prompt = this.demoInput ? this.demoInput.value.trim() : '';
        
        if (!prompt) {
            this.showError('Veuillez entrer une question');
            return;
        }
        
        this.isGenerating = true;
        this.setLoadingState(true);
        
        try {
            let response;
            
            if (this.config.demoMode) {
                // Mode démo - simulation
                response = await this.simulateResponse(prompt);
            } else {
                // Mode réel - appel API
                response = await this.callRealAPI(prompt);
            }
            
            // Afficher la réponse
            this.displayResponse(response);
            
            // Ajouter à l'historique
            this.addToHistory(prompt, response);
            
            // Mettre à jour le cache (simulation)
            this.updateCacheStatus(Math.random() > 0.5);
            
        } catch (error) {
            console.error('Erreur de génération:', error);
            this.showError(this.responses[this.currentLanguage].errorText);
        } finally {
            this.isGenerating = false;
            this.setLoadingState(false);
        }
    }
    
    async simulateResponse(prompt) {
        // Simulation d'une réponse déterministe
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const texts = this.responses[this.currentLanguage];
        
        // Réponses simulées selon le prompt
        const responses = {
            'fr': {
                'qui es-tu?': texts.defaultResponse,
                'que fais-tu?': "Je développe des solutions d'IA déterministes pour les secteurs critiques.",
                'comment ça marche?': "Notre technologie utilise un cache déterministe et une politique de réponse vérifiée.",
                'quels sont vos avantages?': "Garantie de déterminisme, réduction de 99% des hallucinations, auditabilité complète."
            },
            'en': {
                'who are you?': texts.defaultResponse,
                'what do you do?': "I develop deterministic AI solutions for critical sectors.",
                'how does it work?': "Our technology uses a deterministic cache and a verified response policy.",
                'what are your advantages?': "Determinism guarantee, 99% hallucination reduction, complete auditability."
            }
        };
        
        const promptLower = prompt.toLowerCase();
        let response = texts.defaultResponse;
        
        // Chercher une réponse correspondante
        for (const [key, value] of Object.entries(responses[this.currentLanguage])) {
            if (promptLower.includes(key)) {
                response = value;
                break;
            }
        }
        
        // Générer un ID de réponse déterministe
        const responseId = this.generateResponseId(prompt, response);
        
        return {
            text: response,
            responseId: responseId,
            timestamp: new Date().toISOString(),
            mode: this.config.verifiedMode ? 'verified' : 'deterministic'
        };
    }
    
    async callRealAPI(prompt) {
        // Pour une implémentation réelle avec votre API
        const payload = {
            prompt: prompt,
            max_tokens: this.config.maxTokens,
            temperature: this.config.temperature,
            verified_mode: this.config.verifiedMode
        };
        
        const response = await fetch(this.config.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    displayResponse(response) {
        if (!this.demoOutput || !this.responseIdElement) return;
        
        this.demoOutput.textContent = response.text;
        this.responseIdElement.textContent = `ID: ${response.responseId.substring(0, 16)}...`;
        
        // Animation d'apparition
        this.demoOutput.style.opacity = '0';
        this.demoOutput.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            this.demoOutput.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            this.demoOutput.style.opacity = '1';
            this.demoOutput.style.transform = 'translateY(0)';
        }, 10);
    }
    
    generateResponseId(prompt, response) {
        // Génération d'un ID déterministe SHA256
        const data = `${prompt}::${response}::${this.config.temperature}::${this.config.verifiedMode}`;
        
        // Simulation d'un hash SHA256
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        
        return `SHA256-${Math.abs(hash).toString(16).padStart(64, '0').substring(0, 64)}`;
    }
    
    addToHistory(prompt, response) {
        if (!this.historyContent) return;
        
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const date = new Date(response.timestamp);
        const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        historyItem.innerHTML = `
            <div class="history-question">
                <strong>Q:</strong> ${prompt.substring(0, 100)}${prompt.length > 100 ? '...' : ''}
            </div>
            <div class="history-answer">
                <strong>A:</strong> ${response.text.substring(0, 80)}${response.text.length > 80 ? '...' : ''}
            </div>
            <div class="history-meta">
                <span class="history-time">${timeString}</span>
                <span class="history-mode">${response.mode}</span>
                <span class="history-id">${response.responseId.substring(0, 8)}...</span>
            </div>
        `;
        
        // Ajouter au début de l'historique
        this.historyContent.insertBefore(historyItem, this.historyContent.firstChild);
        
        // Limiter l'historique à 10 éléments
        const items = this.historyContent.querySelectorAll('.history-item');
        if (items.length > 10) {
            items[items.length - 1].remove();
        }
        
        // Sauvegarder dans le tableau
        this.responseHistory.unshift({
            prompt: prompt,
            response: response,
            timestamp: response.timestamp
        });
    }
    
    clearHistory() {
        if (!this.historyContent) return;
        
        this.historyContent.innerHTML = '';
        this.responseHistory = [];
        
        // Notification
        this.showNotification('Historique effacé', 'info');
    }
    
    clearInput() {
        if (this.demoInput) {
            this.demoInput.value = '';
            this.demoInput.focus();
        }
    }
    
    updateCacheStatus(isHit) {
        if (!this.cacheStatus) return;
        
        const texts = this.responses[this.currentLanguage];
        
        this.cacheStatus.textContent = isHit ? texts.cacheHit : texts.cacheMiss;
        this.cacheStatus.className = `cache-status ${isHit ? 'hit' : 'miss'}`;
        
        // Style
        this.cacheStatus.style.padding = '2px 8px';
        this.cacheStatus.style.borderRadius = '4px';
        this.cacheStatus.style.fontSize = '0.875rem';
        this.cacheStatus.style.fontWeight = '500';
        
        if (isHit) {
            this.cacheStatus.style.backgroundColor = 'rgba(0, 200, 83, 0.1)';
            this.cacheStatus.style.color = 'var(--color-accent-green)';
        } else {
            this.cacheStatus.style.backgroundColor = 'rgba(255, 111, 0, 0.1)';
            this.cacheStatus.style.color = 'var(--color-secondary)';
        }
    }
    
    setLoadingState(isLoading) {
        if (!this.sendButton) return;
        
        const texts = this.responses[this.currentLanguage];
        
        if (isLoading) {
            this.sendButton.textContent = texts.loadingText;
            this.sendButton.disabled = true;
            
            // Ajouter une animation de chargement
            this.sendButton.classList.add('loading');
        } else {
            this.sendButton.textContent = texts.sendButton;
            this.sendButton.disabled = false;
            this.sendButton.classList.remove('loading');
        }
    }
    
    showError(message) {
        // Notification d'erreur
        this.showNotification(message, 'error');
        
        // Animation sur le champ d'entrée
        if (this.demoInput) {
            this.demoInput.style.borderColor = 'var(--color-secondary)';
            
            setTimeout(() => {
                this.demoInput.style.borderColor = '';
            }, 1000);
        }
    }
    
    showNotification(message, type = 'info') {
        // Créer une notification
        const notification = document.createElement('div');
        notification.className = `demo-notification notification-${type}`;
        notification.textContent = message;
        
        // Style
        notification.style.position = 'fixed';
        notification.style.bottom = '20px';
        notification.style.right = '20px';
        notification.style.padding = '12px 20px';
        notification.style.background = type === 'error' ? 'var(--color-secondary)' : 'var(--color-primary)';
        notification.style.color = 'var(--color-white)';
        notification.style.borderRadius = '8px';
        notification.style.boxShadow = 'var(--shadow-lg)';
        notification.style.zIndex = '1000';
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(20px)';
        notification.style.transition = 'all 0.3s ease';
        
        // Ajouter au document
        document.body.appendChild(notification);
        
        // Animation d'entrée
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);
        
        // Supprimer après 3 secondes
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    const demo = new InteractiveDemo();
    demo.init();
    
    // Exporter pour une utilisation globale
    window.HarmonicAIDemo = demo;
});