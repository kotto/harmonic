/**
 * IA Harmonique — Application Web
 * Interface utilisateur avec le moteur ABC + multimodal
 */
(function() {
    'use strict';
    
    // État de l'application
    const state = {
        generator: new HarmonicEngine.ResponseGenerator(),
        attachedFiles: [],
        messages: [],
        isProcessing: false
    };
    
    // DOM refs
    const elements = {
        messagesList: document.getElementById('messagesList'),
        welcomeMsg: document.getElementById('welcomeMsg'),
        promptInput: document.getElementById('promptInput'),
        sendBtn: document.getElementById('sendBtn'),
        loadingIndicator: document.getElementById('loadingIndicator'),
        statsPanel: document.getElementById('statsPanel'),
        statsBtn: document.getElementById('statsBtn'),
        clearBtn: document.getElementById('clearBtn'),
        statRequests: document.getElementById('statRequests'),
        statResonance: document.getElementById('statResonance'),
        statLatency: document.getElementById('statLatency'),
        statCache: document.getElementById('statCache'),
        attachBtn: document.getElementById('attachBtn'),
        fileInput: document.getElementById('fileInput'),
        attachmentsBar: document.getElementById('attachmentsBar')
    };
    
    // =========================================================================
    // FONCTIONS UI
    // =========================================================================
    
    function addMessage(text, isUser, meta = {}) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isUser ? 'user' : 'ai'}`;
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text;
        msgDiv.appendChild(textDiv);
        
        if (!isUser && meta.resonance !== undefined) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            const resonancePct = Math.round(meta.resonance * 100);
            const latency = meta.processingTimeMs < 1 ? '< 1ms' : `${meta.processingTimeMs.toFixed(1)}ms`;
            const cacheTag = meta.cacheHit ? ' · Cache' : '';
            const cat = meta.category ? ` · ${meta.category}` : '';
            const filesTag = meta.fileCount ? ` · ${meta.fileCount} fichier(s)` : '';
            metaDiv.textContent = `Résonance : ${resonancePct}% · ${latency}${cacheTag}${cat}${filesTag}`;
            msgDiv.appendChild(metaDiv);
        }
        
        elements.messagesList.appendChild(msgDiv);
        elements.messagesList.scrollTop = elements.messagesList.scrollHeight;
        state.messages.push({ text, isUser, ...meta });
    }
    
    function showLoading() {
        elements.loadingIndicator.classList.remove('hidden');
        elements.sendBtn.disabled = true;
    }
    
    function hideLoading() {
        elements.loadingIndicator.classList.add('hidden');
        elements.sendBtn.disabled = false;
    }
    
    function updateStats() {
        const stats = state.generator.getStats();
        elements.statRequests.textContent = stats.totalRequests;
        elements.statResonance.textContent = `${(stats.avgResonance * 100).toFixed(1)}%`;
        elements.statLatency.textContent = `${stats.avgLatency.toFixed(2)}ms`;
        elements.statCache.textContent = `${(stats.cacheHitRate * 100).toFixed(0)}%`;
    }
    
    function hideWelcome() {
        elements.welcomeMsg.style.display = 'none';
    }
    
    // =========================================================================
    // FICHIERS JOINTS
    // =========================================================================
    
    function addAttachment(file) {
        const attachedFile = new HarmonicMultimodal.AttachedFile(file);
        state.attachedFiles.push(attachedFile);
        renderAttachments();
        elements.sendBtn.disabled = false;
    }
    
    function removeAttachment(index) {
        state.attachedFiles.splice(index, 1);
        renderAttachments();
        if (state.attachedFiles.length === 0 && !elements.promptInput.value.trim()) {
            elements.sendBtn.disabled = true;
        }
    }
    
    function renderAttachments() {
        elements.attachmentsBar.innerHTML = '';
        
        for (let i = 0; i < state.attachedFiles.length; i++) {
            const file = state.attachedFiles[i];
            const chip = document.createElement('div');
            chip.className = `attachment-chip ${file.type}`;
            
            const icon = document.createElement('span');
            icon.className = 'attachment-icon';
            const icons = { image: '🖼', audio: '🎵', video: '🎬', document: '📄', unknown: '📁' };
            icon.textContent = icons[file.type] || icons.unknown;
            
            const name = document.createElement('span');
            name.className = 'attachment-name';
            name.textContent = file.name.length > 20 ? file.name.substring(0, 17) + '…' : file.name;
            
            const remove = document.createElement('span');
            remove.className = 'attachment-remove';
            remove.textContent = '×';
            remove.onclick = () => removeAttachment(i);
            
            chip.appendChild(icon);
            chip.appendChild(name);
            chip.appendChild(remove);
            elements.attachmentsBar.appendChild(chip);
        }
    }
    
    // =========================================================================
    // GÉNÉRATION DE RÉPONSE
    // =========================================================================
    
    async function processPrompt(prompt) {
        if (state.isProcessing || (!prompt.trim() && state.attachedFiles.length === 0)) return;
        
        state.isProcessing = true;
        hideWelcome();
        
        const fileCount = state.attachedFiles.length;
        let userText = prompt;
        if (fileCount > 0) {
            const names = state.attachedFiles.map(f => f.name).join(', ');
            userText += `\n[Fichiers : ${names}]`;
        }
        
        // Message utilisateur
        addMessage(userText, true, { fileCount });
        showLoading();
        
        // Générer la réponse
        setTimeout(async () => {
            try {
                // Analyser les fichiers si présents
                let mergedSignature = null;
                let fileSummaries = [];
                
                if (state.attachedFiles.length > 0) {
                    const signatures = [];
                    for (const file of state.attachedFiles) {
                        await file.analyze();
                        signatures.push(file.signature);
                        fileSummaries.push(file.summary());
                    }
                    
                    if (signatures.length > 0) {
                        mergedSignature = HarmonicMultimodal.fuseSignatures(signatures);
                    }
                }
                
                // Si on a une signature fusionnée, on l'utilise comme contexte
                let result;
                if (mergedSignature && prompt.trim()) {
                    // Prompt avec fichiers : combiner
                    const promptSig = state.generator.analyzer.analyze(prompt);
                    const combined = HarmonicMultimodal.fuseSignatures([promptSig.toVector(), mergedSignature]);
                    result = state.generator.generate(prompt);
                    result.resonance = Math.sqrt(combined.reduce((s, v) => s + v*v, 0)) * PHI / 2;
                } else if (mergedSignature) {
                    // Uniquement des fichiers
                    const contextText = `Analyse de ${state.attachedFiles.length} fichier(s) :\n${fileSummaries.join('\n')}`;
                    result = state.generator.generate(contextText);
                } else {
                    // Texte seul
                    result = state.generator.generate(prompt);
                }
                
                result.fileCount = fileCount;
                addMessage(result.response, false, result);
                
                // Vider la barre d'attachements
                state.attachedFiles = [];
                renderAttachments();
                
                setTimeout(updateStats, 100);
                
            } catch (e) {
                console.error('Erreur de génération :', e);
                addMessage(`Désolé, une erreur est survenue : ${e.message}`, false, {});
            } finally {
                state.isProcessing = false;
                hideLoading();
                elements.promptInput.focus();
            }
        }, 50);
    }
    
    // =========================================================================
    // ÉVÉNEMENTS
    // =========================================================================
    
    // Envoyer
    elements.sendBtn.addEventListener('click', () => {
        const text = elements.promptInput.value.trim();
        processPrompt(text);
        elements.promptInput.value = '';
        elements.promptInput.style.height = 'auto';
    });
    
    // Entrée
    elements.promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const text = elements.promptInput.value.trim();
            processPrompt(text);
            elements.promptInput.value = '';
            elements.promptInput.style.height = 'auto';
        }
    });
    
    // Input
    elements.promptInput.addEventListener('input', () => {
        const hasText = !!elements.promptInput.value.trim();
        elements.sendBtn.disabled = !hasText && state.attachedFiles.length === 0;
        elements.promptInput.style.height = 'auto';
        elements.promptInput.style.height = Math.min(elements.promptInput.scrollHeight, 120) + 'px';
    });
    
    // Stats
    elements.statsBtn.addEventListener('click', () => {
        elements.statsPanel.classList.toggle('hidden');
        updateStats();
    });
    
    // Clear
    elements.clearBtn.addEventListener('click', () => {
        elements.messagesList.innerHTML = '';
        elements.welcomeMsg.style.display = '';
        state.messages = [];
        state.attachedFiles = [];
        renderAttachments();
        updateStats();
    });
    
    // Bouton attacher
    elements.attachBtn.addEventListener('click', () => {
        elements.fileInput.click();
    });
    
    // File input
    elements.fileInput.addEventListener('change', () => {
        for (const file of elements.fileInput.files) {
            addAttachment(file);
        }
        elements.fileInput.value = '';
    });
    
    // Drag & drop sur la zone de chat
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        chatContainer.classList.add('drag-over');
    });
    
    chatContainer.addEventListener('dragleave', () => {
        chatContainer.classList.remove('drag-over');
    });
    
    chatContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        chatContainer.classList.remove('drag-over');
        for (const file of e.dataTransfer.files) {
            addAttachment(file);
        }
    });
    
    // Exemples
    document.querySelectorAll('.example-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const prompt = chip.dataset.prompt;
            if (prompt) {
                elements.promptInput.value = prompt;
                elements.sendBtn.disabled = false;
                elements.promptInput.dispatchEvent(new Event('input'));
                elements.promptInput.focus();
            }
        });
    });
    
    // Logo → about
    document.querySelector('.app-logo').addEventListener('click', () => {
        document.getElementById('aboutModal').classList.remove('hidden');
    });
    document.querySelector('.modal-close').addEventListener('click', () => {
        document.getElementById('aboutModal').classList.add('hidden');
    });
    document.getElementById('aboutModal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            document.getElementById('aboutModal').classList.add('hidden');
        }
    });
    
    // =========================================================================
    // RECHERCHE WEB
    // =========================================================================
    
    const searchUI = new HarmonicSearch.SearchUI({
        onResult: (result) => {
            // Quand un résultat arrive, l'ajouter au chat
            if (result.totalResults > 0 && result.synthesis && typeof result.synthesis === 'object') {
                const s = result.synthesis;
                const consensusPct = Math.round(s.consensus * 100);
                const resonancePct = Math.round(s.avgResonance * 100);
                
                let response = `🔍 **Recherche Web : "${result.query}"**\n\n`;
                response += `**Synthèse harmonique** — ${s.sourceCount} sources analysées\n`;
                response += `Consensus : ${consensusPct}% · Résonance : ${resonancePct}%\n`;
                response += `Catégorie dominante : ${s.mainCategory}\n\n`;
                response += `**Résultats classés par résonance :**\n\n`;
                
                for (const r of result.results.slice(0, 5)) {
                    const resPct = Math.round((r.resonance || 0) * 100);
                    const hostname = r.url ? new URL(r.url).hostname : '';
                    response += `◆ [${resPct}%] ${r.title || 'Sans titre'}\n`;
                    response += `   ${r.snippet ? r.snippet.substring(0, 150) + '...' : ''}\n`;
                    response += `   ${hostname} · ${r.dominantCategory || 'Général'}\n\n`;
                }
                
                response += `\n_Signature harmonique : [${result.querySignature.map(v => v.toFixed(2)).join(', ')}]_`;
                
                addMessage(response, false, {
                    resonance: s.avgResonance,
                    processingTimeMs: 0.5,
                    category: 'Recherche Web'
                });
            } else {
                addMessage(`🔍 Recherche "${result.query}" : ${result.synthesis || 'Aucun résultat'}`, false, {
                    resonance: 0,
                    processingTimeMs: 0.5,
                    category: 'Recherche Web'
                });
            }
        }
    });
    
    // Créer l'interface de recherche
    searchUI.create('searchContainer');
    
    // Bouton de recherche web dans le header
    document.getElementById('webSearchBtn').addEventListener('click', () => {
        searchUI.toggle();
        if (searchUI.isOpen) {
            // Focus sur l'input de recherche
            setTimeout(() => document.getElementById('searchQuery')?.focus(), 300);
        }
    });
    
    // =========================================================================
    // ACTUALITÉS EN DIRECT
    // =========================================================================
    
    const newsDashboard = new HarmonicNews.NewsDashboard('newsContainer', {
        sources: ['lemonde', 'lefigaro', 'franceinfo', 'bbc', 'guardian', 'techcrunch', 'theverge', 'nature', 'science_daily'],
        pollInterval: 120000
    });
    newsDashboard.create();
    
    document.getElementById('newsBtn').addEventListener('click', () => {
        newsDashboard.toggle();
    });
    
    // =========================================================================
    // ANALYSEUR D'URL
    // =========================================================================
    
    const urlAnalyzer = new HarmonicURL.URLHarmonicAnalyzer();
    
    /**
     * Détecte si un prompt contient une URL à analyser
     */
    async function processURLs(prompt) {
        const urls = HarmonicURL.URLDetector.findUrls(prompt);
        if (urls.length === 0) return null;
        
        // Prendre la première URL
        const url = urls[0];
        addMessage(`🔗 Analyse de l'URL : ${url}`, true);
        showLoading();
        
        const result = await urlAnalyzer.analyzeForChat(url);
        hideLoading();
        
        if (result) {
            addMessage(result.response, false, {
                resonance: result.resonance || 0,
                processingTimeMs: 0.5,
                category: result.category || 'URL Analysis'
            });
        }
        
        return result;
    }
    
    // =========================================================================
    // RECHERCHE WEB + URL + PROMPT NORMAL
    // =========================================================================
    
    const originalProcess = processPrompt;
    processPrompt = async function(prompt) {
        // 1. Vérifier si le prompt contient une URL
        const hasURL = HarmonicURL.URLDetector.hasUrls(prompt);
        if (hasURL && !state.isProcessing) {
            await processURLs(prompt);
            return;
        }
        
        // 2. Vérifier si c'est une recherche web
        const searchPrefixes = ['recherche ', 'cherche ', 'trouve ', 'actualité', 'news ', 'web: '];
        const shouldSearch = searchPrefixes.some(prefix => 
            prompt.toLowerCase().startsWith(prefix)
        );
        
        if (shouldSearch && !state.isProcessing) {
            // Extraire la requête
            let query = prompt;
            for (const prefix of searchPrefixes) {
                if (query.toLowerCase().startsWith(prefix)) {
                    query = query.substring(prefix.length).trim();
                    break;
                }
            }
            
            if (query) {
                // Message utilisateur
                addMessage(prompt, true);
                showLoading();
                
                // Lancer la recherche
                searchUI.open();
                document.getElementById('searchQuery').value = query;
                await searchUI.search(query);
                
                hideLoading();
                return;
            }
        }
        
        // 3. Sinon, comportement normal (moteur ABC)
        return originalProcess(prompt);
    };
    
    elements.promptInput.focus();
    
})();
