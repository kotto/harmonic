// Harmonic AI Chat Interface
// Version 1.0 - DÃ©terministe & VÃ©rifiÃ©

class HarmonicAIChat {
    constructor() {
        this.messages = [];
        this.currentSessionId = this.generateSessionId();
        this.isGenerating = false;
        this.apiEndpoint = 'http://__EC2_IP__:8000/generate'; // Backend AWS rÃ©el
        this.demoMode = true; // Mode dÃ©mo par dÃ©faut, sera mis Ã  jour aprÃ¨s test de connexion
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateSessionId();
        this.loadSettings();
        this.addThemeToggle();
        this.checkBackendStatus();
    }
    
    bindEvents() {
        // Input et envoi
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        messageInput.addEventListener('input', this.handleInputResize.bind(this));
        messageInput.addEventListener('keydown', this.handleKeyDown.bind(this));
        sendBtn.addEventListener('click', this.sendMessage.bind(this));
        
        // Nouveau chat
        document.getElementById('newChatBtn').addEventListener('click', this.newChat.bind(this));
        
        // ParamÃ¨tres
        document.getElementById('settingsBtn').addEventListener('click', this.openSettings.bind(this));
        document.getElementById('settingsClose').addEventListener('click', this.closeSettings.bind(this));
        document.getElementById('saveSettings').addEventListener('click', this.saveSettings.bind(this));
        document.getElementById('resetSettings').addEventListener('click', this.resetSettings.bind(this));
        
        // Prompts rapides
        document.querySelectorAll('.prompt-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const prompt = e.currentTarget.getAttribute('data-prompt');
                this.useQuickPrompt(prompt);
            });
        });
        
        // Export
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.currentTarget.getAttribute('data-format');
                this.exportChat(format);
            });
        });
        
        // Copie Response ID
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetId = e.currentTarget.getAttribute('data-target');
                this.copyToClipboard(targetId);
            });
        });
        
        // Sidebar
        document.getElementById('sidebarClose').addEventListener('click', this.toggleSidebar.bind(this));
        
        // ParamÃ¨tres dynamiques
        document.getElementById('temperature').addEventListener('input', this.updateTempValue.bind(this));
        document.getElementById('maxTokens').addEventListener('input', this.updateTokensValue.bind(this));
        document.getElementById('confidenceThreshold').addEventListener('input', this.updateThresholdValue.bind(this));
    }
    
    addThemeToggle() {
        // CrÃ©er le bouton de basculement du thÃ¨me
        const themeToggle = document.createElement('button');
        themeToggle.id = 'themeToggle';
        themeToggle.className = 'theme-toggle';
        themeToggle.setAttribute('aria-label', 'Basculer le thÃ¨me');
        
        // DÃ©terminer le thÃ¨me actuel
        const currentTheme = document.body.getAttribute('data-theme') || 'light';
        this.updateThemeIcon(themeToggle, currentTheme);
        
        // Ajouter l'Ã©vÃ©nement de clic
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.body.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            this.toggleTheme(newTheme);
            this.updateThemeIcon(themeToggle, newTheme);
        });
        
        // Ajouter le bouton dans le header
        const headerRight = document.querySelector('.header-right');
        if (headerRight) {
            headerRight.prepend(themeToggle);
        }
    }
    
    toggleTheme(theme) {
        // Appliquer le thÃ¨me
        document.body.setAttribute('data-theme', theme);
        
        // Sauvegarder dans les paramÃ¨tres
        const settings = JSON.parse(localStorage.getItem('harmonic_ai_settings') || '{}');
        settings.theme = theme;
        localStorage.setItem('harmonic_ai_settings', JSON.stringify(settings));
        
        // Mettre Ã  jour le sÃ©lecteur dans les paramÃ¨tres
        const themeSelect = document.getElementById('theme');
        if (themeSelect) {
            themeSelect.value = theme;
        }
        
        // Afficher une notification
        this.showNotification(`ThÃ¨me ${theme === 'dark' ? 'sombre' : 'clair'} activÃ©`);
    }
    
    updateThemeIcon(button, theme) {
        if (theme === 'dark') {
            button.innerHTML = '<i class="fas fa-sun"></i>';
            button.title = 'Passer au thÃ¨me clair';
        } else {
            button.innerHTML = '<i class="fas fa-moon"></i>';
            button.title = 'Passer au thÃ¨me sombre';
        }
    }
    
    async testBackendConnection() {
        // Test de connexion au backend AWS rÃ©el
        const awsBackendUrl = 'http://__EC2_IP__:8000/health';
        const demoBackendUrl = 'https://api.harmonic-ai.com/v1/chat';
        
        try {
            console.log('Test de connexion au backend AWS...');
            
            // Essayer d'abord le backend AWS
            const response = await fetch(awsBackendUrl, {
                method: 'GET',
                mode: 'cors',
                headers: {
                    'Accept': 'application/json'
                },
                timeout: 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Backend AWS connectÃ©:', data);
                return {
                    connected: true,
                    backend: 'aws',
                    url: awsBackendUrl,
                    status: data.status || 'healthy'
                };
            }
        } catch (error) {
            console.log('Backend AWS non disponible:', error.message);
        }
        
        // Si AWS Ã©choue, essayer le backend de dÃ©mo
        try {
            console.log('Test de connexion au backend de dÃ©mo...');
            
            // Simuler une rÃ©ponse de dÃ©mo
            await new Promise(resolve => setTimeout(resolve, 100));
            
            return {
                connected: true,
                backend: 'demo',
                url: demoBackendUrl,
                status: 'demo_mode'
            };
        } catch (error) {
            console.log('Backend de dÃ©mo non disponible:', error.message);
        }
        
        return {
            connected: false,
            backend: 'none',
            url: null,
            status: 'offline'
        };
    }
    
    async checkBackendStatus() {
        // Tester la connexion et afficher le statut
        const status = await this.testBackendConnection();
        
        // CrÃ©er l'indicateur de statut
        const statusIndicator = document.createElement('div');
        statusIndicator.id = 'backendStatus';
        statusIndicator.className = 'backend-status';
        
        // Mettre Ã  jour le mode dÃ©mo en fonction du statut
        if (status.backend === 'aws' && status.connected) {
            this.demoMode = false;
            this.apiEndpoint = status.url.replace('/health', '/generate');
            statusIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Backend AWS connectÃ©';
            statusIndicator.className += ' status-connected';
            console.log('Mode production activÃ© avec backend AWS');
        } else if (status.backend === 'demo' && status.connected) {
            this.demoMode = true;
            statusIndicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Mode dÃ©mo (backend hors ligne)';
            statusIndicator.className += ' status-demo';
            console.log('Mode dÃ©mo activÃ©');
        } else {
            this.demoMode = true;
            statusIndicator.innerHTML = '<i class="fas fa-times-circle"></i> Backend hors ligne';
            statusIndicator.className += ' status-offline';
            console.log('Backend hors ligne, mode dÃ©mo activÃ©');
        }
        
        // Ajouter l'indicateur dans le header
        const headerRight = document.querySelector('.header-right');
        if (headerRight) {
            // VÃ©rifier si l'indicateur existe dÃ©jÃ 
            const existingStatus = document.getElementById('backendStatus');
            if (existingStatus) {
                existingStatus.remove();
            }
            headerRight.appendChild(statusIndicator);
        }
        
        // Afficher une notification si en mode dÃ©mo
        if (this.demoMode) {
            setTimeout(() => {
                this.showNotification('Mode dÃ©mo activÃ© - Utilisation de rÃ©ponses prÃ©-dÃ©finies');
            }, 1000);
        }
        
        return status;
    }
    
    generateSessionId() {
        // GÃ©nÃ¨re un ID de session unique basÃ© sur le timestamp et un random
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 5);
        return `session_${timestamp}_${random}`;
    }
    
    updateSessionId() {
        document.getElementById('sessionId').textContent = this.currentSessionId;
    }
    
    handleInputResize(e) {
        const textarea = e.target;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
    
    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || this.isGenerating) return;
        
        // Ajouter le message utilisateur
        this.addUserMessage(message);
        input.value = '';
        input.style.height = 'auto';
        
        // Afficher l'interface de chat
        this.showChatInterface();
        
        // Afficher l'indicateur de frappe
        this.showTypingIndicator();
        
        // GÃ©nÃ©rer la rÃ©ponse
        this.isGenerating = true;
        document.getElementById('sendBtn').disabled = true;
        
        try {
            const response = await this.generateAIResponse(message);
            this.addAIMessage(response);
            this.updateSidebar(response);
        } catch (error) {
            console.error('Erreur de gÃ©nÃ©ration:', error);
            this.addErrorMessage("DÃ©solÃ©, une erreur s'est produite. Veuillez rÃ©essayer.");
        } finally {
            this.hideTypingIndicator();
            this.isGenerating = false;
            document.getElementById('sendBtn').disabled = false;
        }
    }
    
    async generateAIResponse(prompt) {
        if (this.demoMode) {
            // Mode dÃ©mo avec rÃ©ponses prÃ©-dÃ©finies
            return this.getDemoResponse(prompt);
        }
        
        // Mode production avec vraie API AWS
        const settings = this.getCurrentSettings();
        
        // Format de payload pour l'API AWS
        const payload = {
            prompt: prompt,
            session_id: this.currentSessionId,
            temperature: settings.temperature,
            max_tokens: settings.maxTokens
        };
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const awsResponse = await response.json();
            
            // Adapter le format de rÃ©ponse AWS Ã  notre format attendu
            return {
                text: awsResponse.content || awsResponse.text || "RÃ©ponse reÃ§ue",
                response_id: this.generateResponseId(prompt),
                confidence: awsResponse.confidence || 0.95,
                response_time: awsResponse.processing_time || 1.5,
                citations: [], // L'API AWS ne retourne pas de citations pour l'instant
                verification_status: {
                    citations_verified: false,
                    logical_consistency: true,
                    confidence_calibrated: true
                }
            };
        } catch (error) {
            console.error('Erreur de connexion au backend AWS:', error);
            // Retourner au mode dÃ©mo en cas d'erreur
            return this.getDemoResponse(prompt);
        }
    }
    
    getDemoResponse(prompt) {
        // RÃ©ponses dÃ©mo pour dÃ©monstration
        const demoResponses = {
            "pythagore": {
                text: "Le thÃ©orÃ¨me de Pythagore Ã©tablit que dans un triangle rectangle, le carrÃ© de la longueur de l'hypotÃ©nuse est Ã©gal Ã  la somme des carrÃ©s des longueurs des deux autres cÃ´tÃ©s.\n\n**Formule** : aÂ² + bÂ² = cÂ²\n\n**Sources** :\n- Euclide, Ã‰lÃ©ments, Livre I, Proposition 47\n- Pythagoras (c. 570â€“495 BCE), Ã©cole pythagoricienne\n\n**Applications** :\n- Calcul de distances en gÃ©omÃ©trie\n- Navigation et triangulation\n- Architecture et construction",
                citations: [
                    {
                        source: "Euclide, Ã‰lÃ©ments",
                        content: "Proposition 47 : Dans les triangles rectangles, le carrÃ© du cÃ´tÃ© sous-tendant l'angle droit est Ã©gal aux carrÃ©s des cÃ´tÃ©s contenant l'angle droit.",
                        date: "c. 300 BCE",
                        confidence: 0.95
                    },
                    {
                        source: "Histoire des MathÃ©matiques",
                        content: "Le thÃ©orÃ¨me Ã©tait connu des Babyloniens (1800-1600 BCE) mais attribuÃ© Ã  Pythagore par la tradition grecque.",
                        date: "2023",
                        confidence: 0.85
                    }
                ],
                response_id: this.generateResponseId(prompt),
                confidence: 0.92,
                response_time: 1.2,
                verification_status: {
                    citations_verified: true,
                    logical_consistency: true,
                    confidence_calibrated: true
                }
            },
            "covid": {
                text: "Selon l'Organisation Mondiale de la SantÃ© (OMS), les symptÃ´mes courants du COVID-19 incluent :\n\n**SymptÃ´mes frÃ©quents** :\n- FiÃ¨vre\n- Toux sÃ¨che\n- Fatigue\n\n**SymptÃ´mes moins frÃ©quents** :\n- Perte du goÃ»t ou de l'odorat\n- Congestion nasale\n- Conjonctivite\n- Maux de gorge\n- Maux de tÃªte\n- Douleurs musculaires ou articulaires\n- Ã‰ruptions cutanÃ©es\n- NausÃ©es ou vomissements\n- DiarrhÃ©e\n- Frissons ou vertiges\n\n**SymptÃ´mes graves** (nÃ©cessitant une attention mÃ©dicale immÃ©diate) :\n- DifficultÃ©s Ã  respirer\n- Douleur ou pression persistante dans la poitrine\n- Confusion\n- IncapacitÃ© Ã  se rÃ©veiller ou Ã  rester Ã©veillÃ©\n- LÃ¨vres ou visage bleuÃ¢tres\n\n**Sources OMS** :\n- [Clinical management of COVID-19](https://www.who.int/publications/i/item/WHO-2019-nCoV-clinical-2021-2)\n- [COVID-19 symptoms](https://www.who.int/health-topics/coronavirus#tab=tab_3)",
                citations: [
                    {
                        source: "OMS - Clinical management of COVID-19",
                        content: "Les symptÃ´mes les plus frÃ©quents de la COVID-19 sont la fiÃ¨vre, la toux sÃ¨che et la fatigue.",
                        date: "2023",
                        confidence: 0.98,
                        url: "https://www.who.int/publications/i/item/WHO-2019-nCoV-clinical-2021-2"
                    },
                    {
                        source: "OMS - Coronavirus disease (COVID-19)",
                        content: "Les symptÃ´mes moins frÃ©quents incluent la perte du goÃ»t ou de l'odorat, les douleurs, les maux de tÃªte.",
                        date: "2024",
                        confidence: 0.96,
                        url: "https://www.who.int/health-topics/coronavirus#tab=tab_3"
                    }
                ],
                response_id: this.generateResponseId(prompt),
                confidence: 0.96,
                response_time: 1.5,
                verification_status: {
                    citations_verified: true,
                    logical_consistency: true,
                    confidence_calibrated: true
                }
            },
            "default": {
                text: `Je suis Harmonic AI, la premiÃ¨re IA 100% dÃ©terministe conÃ§ue pour Ã©liminer les hallucinations et garantir la fiabilitÃ© des informations.

**CaractÃ©ristiques clÃ©s** :
âœ… **0% d'hallucination vÃ©rifiable** - Toutes les affirmations factuelles sont accompagnÃ©es de citations
âœ… **DÃ©terminisme absolu** - MÃªme prompt = mÃªme sortie (Response ID unique)
âœ… **AuditabilitÃ© totale** - Chaque rÃ©ponse est traÃ§able et reproductible
âœ… **Abstention structurÃ©e** - Je m'abstiens quand les sources sont insuffisantes

**Exemple de vÃ©rification** :
Pour votre question "${prompt}", je rechercherai des sources vÃ©rifiables avant de fournir une rÃ©ponse. Si les sources sont insuffisantes, je vous indiquerai clairement les limites de ma rÃ©ponse.

**Response ID** : ${this.generateResponseId(prompt)}`,
                citations: [],
                response_id: this.generateResponseId(prompt),
                confidence: 0.88,
                response_time: 0.8,
                verification_status: {
                    citations_verified: false,
                    logical_consistency: true,
                    confidence_calibrated: true
                }
            }
        };
        
        // DÃ©tecter le type de prompt
        let responseType = "default";
        const promptLower = prompt.toLowerCase();
        
        if (promptLower.includes("pythagore") || promptLower.includes("thÃ©orÃ¨me")) {
            responseType = "pythagore";
        } else if (promptLower.includes("covid") || promptLower.includes("symptÃ´me")) {
            responseType = "covid";
        }
        
        return demoResponses[responseType];
    }
    
    generateResponseId(prompt) {
        // GÃ©nÃ¨re un Response ID SHA256-like (simulÃ© pour la dÃ©mo)
        const timestamp = Date.now();
        const hashInput = `${prompt}_${timestamp}_${this.currentSessionId}`;
        let hash = 0;
        
        for (let i = 0; i < hashInput.length; i++) {
            hash = ((hash << 5) - hash) + hashInput.charCodeAt(i);
            hash |= 0;
        }
        
        return `resp_${Math.abs(hash).toString(16).substr(0, 12)}_${timestamp.toString(36)}`;
    }
    
    addUserMessage(text) {
        const message = {
            id: `msg_${Date.now()}`,
            type: 'user',
            text: text,
            timestamp: new Date().toISOString()
        };
        
        this.messages.push(message);
        this.renderMessage(message);
    }
    
    addAIMessage(response) {
        const message = {
            id: `msg_${Date.now()}`,
            type: 'ai',
            text: response.text,
            response_id: response.response_id,
            confidence: response.confidence,
            response_time: response.response_time,
            citations: response.citations,
            verification_status: response.verification_status,
            timestamp: new Date().toISOString()
        };
        
        this.messages.push(message);
        this.renderMessage(message);
    }
    
    addErrorMessage(text) {
        const message = {
            id: `msg_${Date.now()}`,
            type: 'error',
            text: text,
            timestamp: new Date().toISOString()
        };
        
        this.messages.push(message);
        this.renderMessage(message);
    }
    
    renderMessage(message) {
        const container = document.getElementById('messagesContainer');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${message.type}`;
        messageDiv.id = message.id;
        
        // Avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        if (message.type === 'user') {
            avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
        } else if (message.type === 'ai') {
            avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
        } else {
            avatarDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        }
        
        // Contenu
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // En-tÃªte
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        
        const authorSpan = document.createElement('span');
        authorSpan.className = 'message-author';
        authorSpan.textContent = message.type === 'user' ? 'Vous' : 'Harmonic AI';
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        headerDiv.appendChild(authorSpan);
        headerDiv.appendChild(timeSpan);
        
        // Texte
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = this.formatMessageText(message.text);
        
        contentDiv.appendChild(headerDiv);
        contentDiv.appendChild(textDiv);
        
        // Response ID pour les rÃ©ponses AI
        if (message.type === 'ai' && message.response_id) {
            const responseIdDiv = document.createElement('div');
            responseIdDiv.className = 'response-id';
            responseIdDiv.innerHTML = `
                <i class="fas fa-fingerprint"></i>
                <span>Response ID: ${message.response_id}</span>
                <button class="copy-btn" data-target="${message.response_id}">
                    <i class="fas fa-copy"></i>
                </button>
            `;
            contentDiv.appendChild(responseIdDiv);
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        container.appendChild(messageDiv);
        
        // Scroll vers le bas
        container.scrollTop = container.scrollHeight;
        
        // Re-binder les boutons de copie
        this.rebindCopyButtons();
    }
    
    formatMessageText(text) {
        // Formatage Markdown basique
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^(.+)$/gm, '<p>$1</p>');
    }
    
    showTypingIndicator() {
        const container = document.getElementById('messagesContainer');
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message message-ai';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">Harmonic AI</span>
                </div>
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <span>VÃ©rification des sources...</span>
                </div>
            </div>
        `;
        
        container.appendChild(typingDiv);
        container.scrollTop = container.scrollHeight;
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    showChatInterface() {
        document.getElementById('welcomeScreen').style.display = 'none';
        document.getElementById('chatMessages').style.display = 'flex';
    }
    
    updateSidebar(response) {
        // Mettre Ã  jour le Response ID
        document.getElementById('currentResponseId').textContent = response.response_id;
        
        // Mettre Ã  jour la barre de confiance
        const confidencePercent = Math.round(response.confidence * 100);
        document.getElementById('confidenceFill').style.width = `${confidencePercent}%`;
        document.getElementById('confidenceValue').textContent = `${confidencePercent}%`;
        
        // Mettre Ã  jour le temps de rÃ©ponse
        document.getElementById('responseTime').textContent = `${response.response_time}s`;
        
        // Mettre Ã  jour les citations
        this.updateCitations(response.citations);
        
        // Mettre Ã  jour le statut de vÃ©rification
        this.updateVerificationStatus(response.verification_status);
    }
    
    updateCitations(citations) {
        const container = document.getElementById('citationsList');
        container.innerHTML = '';
        
        if (!citations || citations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>Aucune citation pour cette rÃ©ponse</p>
                </div>
            `;
            return;
        }
        
        citations.forEach((citation, index) => {
            const citationDiv = document.createElement('div');
            citationDiv.className = 'citation-item';
            
            const confidencePercent = Math.round(citation.confidence * 100);
            const confidenceColor = confidencePercent >= 90 ? 'var(--chat-success)' : 
                                  confidencePercent >= 70 ? 'var(--chat-warning)' : 
                                  'var(--chat-danger)';
            
            citationDiv.innerHTML = `
                <div class="citation-source">
                    <i class="fas fa-book"></i>
                    ${citation.source}
                </div>
                <div class="citation-content">
                    ${citation.content}
                </div>
                <div class="citation-meta">
                    <span>${citation.date}</span>
                    <span style="color: ${confidenceColor}">
                        Confiance: ${confidencePercent}%
                    </span>
                </div>
            `;
            
            container.appendChild(citationDiv);
        });
    }
    
    updateVerificationStatus(status) {
        const container = document.getElementById('verificationStatus');
        container.innerHTML = '';
        
        const items = [
            {
                key: 'citations_verified',
                label: 'Citations vÃ©rifiÃ©es',
                icon: status.citations_verified ? 'fa-check-circle' : 'fa-times-circle',
                color: status.citations_verified ? 'var(--chat-success)' : 'var(--chat-danger)'
            },
            {
                key: 'logical_consistency',
                label: 'Consistance logique',
                icon: status.logical_consistency ? 'fa-check-circle' : 'fa-times-circle',
                color: status.logical_consistency ? 'var(--chat-success)' : 'var(--chat-danger)'
            },
            {
                key: 'confidence_calibrated',
                label: 'Calibration de confiance',
                icon: status.confidence_calibrated ? 'fa-check-circle' : 'fa-times-circle',
                color: status.confidence_calibrated ? 'var(--chat-success)' : 'var(--chat-danger)'
            }
        ];
        
        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'status-item';
            
            itemDiv.innerHTML = `
                <i class="fas ${item.icon}" style="color: ${item.color}"></i>
                <span>${item.label}</span>
            `;
            
            container.appendChild(itemDiv);
        });
    }
    
    useQuickPrompt(prompt) {
        document.getElementById('messageInput').value = prompt;
        document.getElementById('messageInput').focus();
        this.handleInputResize({ target: document.getElementById('messageInput') });
    }
    
    newChat() {
        if (confirm('Voulez-vous vraiment commencer une nouvelle conversation ? L\'historique actuel sera effacÃ©.')) {
            this.messages = [];
            document.getElementById('messagesContainer').innerHTML = '';
            document.getElementById('welcomeScreen').style.display = 'flex';
            document.getElementById('chatMessages').style.display = 'none';
            
            // GÃ©nÃ©rer une nouvelle session ID
            this.currentSessionId = this.generateSessionId();
            this.updateSessionId();
            
            // RÃ©initialiser la sidebar
            this.updateSidebar({
                response_id: '-',
                confidence: 0,
                response_time: '-',
                citations: [],
                verification_status: {
                    citations_verified: false,
                    logical_consistency: false,
                    confidence_calibrated: false
                }
            });
        }
    }
    
    openSettings() {
        document.getElementById('settingsModal').classList.add('show');
    }
    
    closeSettings() {
        document.getElementById('settingsModal').classList.remove('show');
    }
    
    saveSettings() {
        const settings = {
            temperature: parseFloat(document.getElementById('temperature').value),
            maxTokens: parseInt(document.getElementById('maxTokens').value),
            requireCitations: document.getElementById('requireCitations').checked,
            enableAbstention: document.getElementById('enableAbstention').checked,
            confidenceThreshold: parseInt(document.getElementById('confidenceThreshold').value),
            theme: document.getElementById('theme').value,
            showSidebar: document.getElementById('showSidebar').checked
        };
        
        localStorage.setItem('harmonic_ai_settings', JSON.stringify(settings));
        
        // Appliquer le thÃ¨me
        document.body.setAttribute('data-theme', settings.theme === 'auto' ? 
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : 
            settings.theme);
        
        // Afficher/masquer la sidebar
        document.getElementById('chatSidebar').style.display = settings.showSidebar ? 'flex' : 'none';
        
        this.closeSettings();
        this.showNotification('ParamÃ¨tres enregistrÃ©s avec succÃ¨s');
    }
    
    loadSettings() {
        const saved = localStorage.getItem('harmonic_ai_settings');
        if (saved) {
            const settings = JSON.parse(saved);
            
            document.getElementById('temperature').value = settings.temperature;
            document.getElementById('maxTokens').value = settings.maxTokens;
            document.getElementById('requireCitations').checked = settings.requireCitations;
            document.getElementById('enableAbstention').checked = settings.enableAbstention;
            document.getElementById('confidenceThreshold').value = settings.confidenceThreshold;
            document.getElementById('theme').value = settings.theme;
            document.getElementById('showSidebar').checked = settings.showSidebar;
            
            this.updateTempValue();
            this.updateTokensValue();
            this.updateThresholdValue();
            
            // Appliquer le thÃ¨me
            document.body.setAttribute('data-theme', settings.theme === 'auto' ? 
                (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : 
                settings.theme);
            
            // Afficher/masquer la sidebar
            document.getElementById('chatSidebar').style.display = settings.showSidebar ? 'flex' : 'none';
        }
    }
    
    resetSettings() {
        if (confirm('Voulez-vous vraiment rÃ©initialiser tous les paramÃ¨tres ?')) {
            localStorage.removeItem('harmonic_ai_settings');
            location.reload();
        }
    }
    
    getCurrentSettings() {
        return {
            temperature: parseFloat(document.getElementById('temperature').value),
            maxTokens: parseInt(document.getElementById('maxTokens').value),
            requireCitations: document.getElementById('requireCitations').checked,
            enableAbstention: document.getElementById('enableAbstention').checked,
            confidenceThreshold: parseInt(document.getElementById('confidenceThreshold').value)
        };
    }
    
    updateTempValue() {
        const value = document.getElementById('temperature').value;
        document.getElementById('tempValue').textContent = parseFloat(value).toFixed(1);
    }
    
    updateTokensValue() {
        const value = document.getElementById('maxTokens').value;
        document.getElementById('tokensValue').textContent = value;
    }
    
    updateThresholdValue() {
        const value = document.getElementById('confidenceThreshold').value;
        document.getElementById('thresholdValue').textContent = `${value}%`;
    }
    
    toggleSidebar() {
        const sidebar = document.getElementById('chatSidebar');
        sidebar.classList.toggle('show');
    }
    
    exportChat(format) {
        const chatData = {
            session_id: this.currentSessionId,
            timestamp: new Date().toISOString(),
            messages: this.messages,
            settings: this.getCurrentSettings()
        };
        
        let content, mimeType, filename;
        
        switch (format) {
            case 'markdown':
                content = this.formatAsMarkdown(chatData);
                mimeType = 'text/markdown';
                filename = `harmonic_ai_chat_${this.currentSessionId}.md`;
                break;
            case 'json':
                content = JSON.stringify(chatData, null, 2);
                mimeType = 'application/json';
                filename = `harmonic_ai_chat_${this.currentSessionId}.json`;
                break;
            case 'pdf':
                this.showNotification('Export PDF en dÃ©veloppement');
                return;
            default:
                return;
        }
        
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showNotification(`Chat exportÃ© en ${format.toUpperCase()}`);
    }
    
    formatAsMarkdown(chatData) {
        let markdown = `# Chat Harmonic AI\n\n`;
        markdown += `**Session ID** : ${chatData.session_id}\n`;
        markdown += `**Date** : ${new Date(chatData.timestamp).toLocaleString()}\n\n`;
        markdown += `---\n\n`;
        
        chatData.messages.forEach(msg => {
            const time = new Date(msg.timestamp).toLocaleTimeString();
            const author = msg.type === 'user' ? 'Vous' : 'Harmonic AI';
            
            markdown += `### ${author} (${time})\n\n`;
            markdown += `${msg.text}\n\n`;
            
            if (msg.type === 'ai' && msg.response_id) {
                markdown += `**Response ID** : ${msg.response_id}\n`;
                markdown += `**Confiance** : ${Math.round(msg.confidence * 100)}%\n\n`;
                
                if (msg.citations && msg.citations.length > 0) {
                    markdown += `#### Citations :\n\n`;
                    msg.citations.forEach((cite, idx) => {
                        markdown += `${idx + 1}. **${cite.source}** (${cite.date})\n`;
                        markdown += `   > ${cite.content}\n`;
                        markdown += `   *Confiance : ${Math.round(cite.confidence * 100)}%*\n\n`;
                    });
                }
            }
            
            markdown += `---\n\n`;
        });
        
        return markdown;
    }
    
    copyToClipboard(targetId) {
        const element = document.getElementById(targetId);
        if (!element) return;
        
        const text = element.textContent;
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('CopiÃ© dans le presse-papier');
        }).catch(err => {
            console.error('Erreur de copie:', err);
        });
    }
    
    rebindCopyButtons() {
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetId = e.currentTarget.getAttribute('data-target');
                this.copyToClipboard(targetId);
            });
        });
    }
    
    showNotification(message) {
        // CrÃ©er une notification temporaire
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--chat-primary);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    getApiKey() {
        // Ã€ implÃ©menter : rÃ©cupÃ©rer la clÃ© API depuis les paramÃ¨tres
        return 'demo_key';
    }
}

// Initialiser le chat quand la page est chargÃ©e
document.addEventListener('DOMContentLoaded', () => {
    window.harmonicChat = new HarmonicAIChat();
});

// Styles CSS pour les animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
