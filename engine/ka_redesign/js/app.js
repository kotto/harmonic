/**
 * KA App — Router, State Management & Navigation
 * ================================================
 * PWA shell qui charge les 12 écrans et gère la navigation
 */

(function() {
  'use strict';

  // ═══ STATE ═══
  const state = {
    currentScreen: 'home',
    screens: [
      { id: 'home',     icon: '🏠', label: 'Accueil' },
      { id: 'chat',     icon: '💬', label: 'Chat' },
      { id: 'memory',   icon: '🧠', label: 'Mémoire' },
      { id: 'code',     icon: '💻', label: 'Code' },
      { id: 'store',    icon: '📦', label: 'Store' },
    ],
    moreScreens: [
      { id: 'jlens',      icon: '🔍', label: 'J-Lens' },
      { id: 'health',     icon: '❤️', label: 'Santé' },
      { id: 'profile',    icon: '⚙️', label: 'Profil' },
      { id: 'enterprise', icon: '🏢', label: 'Enterprise' },
      { id: 'storage',    icon: '🗜️', label: 'Stockage' },
      { id: 'creative',   icon: '🎨', label: 'Créatif' },
    ],
    personality: localStorage.getItem('ka_personality') || 'ka',
    theme: localStorage.getItem('ka_theme') || 'dark',
    language: localStorage.getItem('ka_language') || 'fr',
    creativeMode: 'image',
    storageQuality: 'standard',
    selectedInterests: [],
    isOnboarded: localStorage.getItem('ka_onboarded') === 'true',
    loadedScreens: {},
  };

  // ═══ API CLIENT ═══
  const api = new KAApiClient();
  window.KA = window.KA || {};

  // ═══ NAVIGATION ═══
  function navigate(screenId) {
    if (screenId === 'more') {
      toggleMorePanel();
      return;
    }

    state.currentScreen = screenId;

    // Masquer tous les écrans
    document.querySelectorAll('.ka-screen').forEach(s => s.style.display = 'none');
    document.getElementById('more-panel')?.classList.remove('open');

    // Afficher l'écran cible
    const target = document.getElementById(`screen-${screenId}`);
    if (target) {
      target.style.display = 'block';
      target.style.animation = 'fadeIn 0.25s ease-out';
      loadScreenContent(screenId);
    }

    // Mettre à jour la nav bar
    updateNavBar(screenId);
    updateHeader(screenId);
  }

  function updateNavBar(activeId) {
    document.querySelectorAll('.ka-nav__btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.screen === activeId);
    });
  }

  function updateHeader(screenId) {
    const screen = state.screens.find(s => s.id === screenId) || 
                   state.moreScreens.find(s => s.id === screenId);
    if (screen) {
      document.getElementById('ka-header-title').textContent = screen.label;
    }
  }

  function toggleMorePanel() {
    const panel = document.getElementById('more-panel');
    panel.classList.toggle('open');
  }

  // ═══ SCREEN LOADING ═══
  async function loadScreenContent(screenId) {
    if (state.loadedScreens[screenId]) return;
    
    try {
      const res = await fetch(`screens/${screenId}.html`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const html = await res.text();
      
      const target = document.getElementById(`screen-${screenId}`);
      if (target) {
        target.innerHTML = html;
        state.loadedScreens[screenId] = true;
        
        // Exécuter les scripts inline
        const scripts = target.querySelectorAll('script');
        scripts.forEach(s => {
          const newScript = document.createElement('script');
          newScript.textContent = s.textContent;
          document.body.appendChild(newScript);
        });
      }
    } catch (err) {
      console.warn(`Screen ${screenId} not loaded:`, err);
    }
  }

  // ═══ KA PUBLIC API ═══
  Object.assign(window.KA, {
    navigate,
    api,
    state,

    // Chat
    async sendMessage(text) {
      if (!text || !text.trim()) return;
      const input = document.getElementById('chat-input');
      if (input) input.value = '';
      
      // Add user message to chat
      const container = document.getElementById('chat-messages');
      if (container) {
        container.innerHTML += `<div class="chat__msg chat__msg--user">
          <div class="chat__msg-bubble"><p>${text}</p><span class="chat__msg-time">${getTime()}</span></div>
        </div>`;
        container.scrollTop = container.scrollHeight;
      }
      
      try {
        const data = await api.chat(text, { personality: state.personality });
        if (container && data.response) {
          container.innerHTML += `<div class="chat__msg chat__msg--ka">
            <div class="chat__msg-avatar">KA</div>
            <div class="chat__msg-bubble"><p>${data.response}</p><span class="chat__msg-time">${getTime()}</span></div>
          </div>`;
          container.scrollTop = container.scrollHeight;
        }
      } catch (err) {
        if (container) {
          container.innerHTML += `<div class="chat__msg chat__msg--ka">
            <div class="chat__msg-avatar">KA</div>
            <div class="chat__msg-bubble"><p>Désolé, le serveur KA n'est pas accessible. Vérifiez votre connexion.</p></div>
          </div>`;
        }
      }
    },

    // Code
    async generateCode() {
      const editor = document.getElementById('code-editor');
      const lang = document.getElementById('code-lang')?.value || 'python';
      if (!editor || !editor.value.trim()) return;
      
      const output = document.getElementById('code-output');
      const outputContent = document.getElementById('code-output-content');
      if (output) output.style.display = 'block';
      if (outputContent) outputContent.textContent = 'Génération en cours...';
      
      try {
        const data = await api.generateCode(editor.value, lang);
        if (outputContent && data.code) {
          outputContent.textContent = data.code;
        }
      } catch (err) {
        if (outputContent) outputContent.textContent = 'Erreur: ' + err.message;
      }
    },

    codeTemplate(template) {
      const editor = document.getElementById('code-editor');
      if (editor) { editor.value = template; editor.focus(); }
    },

    copyCode() {
      const content = document.getElementById('code-output-content')?.textContent;
      if (content) navigator.clipboard?.writeText(content);
    },

    // Enterprise
    async createTenant() {
      const name = document.getElementById('ent-name')?.value;
      if (!name) return;
      try {
        const data = await api.enterpriseCreateTenant(name);
        const keyDiv = document.getElementById('ent-api-key');
        if (keyDiv) { keyDiv.style.display = 'block'; keyDiv.textContent = `Clé API: ${data.api_key}`; }
      } catch (err) { alert('Erreur: ' + err.message); }
    },

    async diagnoseBug() {
      const symptom = document.getElementById('ent-symptom')?.value;
      if (!symptom) return;
      try {
        const data = await api.enterpriseDiagnose(symptom);
        const div = document.getElementById('ent-diagnosis');
        if (div) {
          div.style.display = 'block';
          div.innerHTML = `<div style="padding:16px;background:var(--color-bg-alt);border-radius:8px;">
            <strong>Diagnostic:</strong> ${data.diagnosis || '—'}<br>
            <strong>Confiance:</strong> ${data.confidence || '—'}<br>
            <strong>Action:</strong> ${data.action || '—'}
          </div>`;
        }
      } catch (err) { alert('Erreur: ' + err.message); }
    },

    handleEnterpriseDrop(e) {
      e.preventDefault();
      const zone = document.getElementById('ent-upload-zone');
      if (zone) zone.style.borderColor = 'var(--color-border)';
      const files = e.dataTransfer?.files;
      if (files?.length) api.enterpriseUpload(Array.from(files));
    },

    // Storage
    handleStorageDrop(e) {
      e.preventDefault();
      document.getElementById('storage-upload-zone').style.borderColor = 'var(--color-border)';
      const file = e.dataTransfer?.files?.[0];
      if (file) this.analyzeFile(file);
    },
    
    async handleStorageFile(input) {
      const file = input.files?.[0];
      if (file) await this.analyzeFile(file);
    },

    async analyzeFile(file) {
      try {
        const data = await api.storageAnalyze(file);
        document.getElementById('storage-saved-pct').textContent = `${data.savings_pct || 0}%`;
        document.getElementById('storage-gauge-fill').style.width = `${data.savings_pct || 0}%`;
        document.getElementById('storage-before').textContent = `Avant: ${formatBytes(file.size)}`;
        document.getElementById('storage-after').textContent = `Après: ${formatBytes(data.compressed_size || file.size)}`;
      } catch (err) { console.error(err); }
    },

    setStorageQuality(q) {
      state.storageQuality = q;
      document.querySelectorAll('.storage__quality .chip').forEach(c => c.classList.remove('chip--active'));
      event?.target?.classList.add('chip--active');
    },

    // Creative
    setCreativeMode(mode) {
      state.creativeMode = mode;
      document.querySelectorAll('.creative__prompt .chip').forEach(c => c.classList.remove('chip--active'));
      event?.target?.classList.add('chip--active');
    },

    async generateMedia() {
      const prompt = document.getElementById('creative-prompt')?.value;
      if (!prompt) return;
      try {
        await api.mediaGenerate(prompt, [state.creativeMode]);
      } catch (err) { console.error(err); }
    },

    // Health
    async runHealthDiagnostic(e) {
      e?.preventDefault();
      // Handled in screen's own script
    },

    // Profile
    setPersonality(p) { state.personality = p; localStorage.setItem('ka_personality', p); },
    setTheme(t) { state.theme = t; localStorage.setItem('ka_theme', t); document.body.dataset.theme = t; },
    setLanguage(l) { state.language = l; localStorage.setItem('ka_language', l); },
    resetProfile() {
      localStorage.clear();
      state.isOnboarded = false;
      navigate('onboarding');
    },

    // J-Lens
    newJensAnalysis() {
      const topic = prompt('Quel sujet analyser ?');
      if (topic) api.reason(topic);
    },

    // Onboarding
    toggleInterest(btn) { btn.classList.toggle('selected'); },
    completeOnboarding() {
      state.isOnboarded = true;
      localStorage.setItem('ka_onboarded', 'true');
      navigate('home');
    },

    // Memory
    searchMemory(query) {
      console.log('Searching memory:', query);
    },
  });

  // ═══ UTILS ═══
  function getTime() {
    return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }

  function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  // ═══ SERVICE WORKER REGISTRATION ═══
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }

  // ═══ INIT ═══
  document.addEventListener('DOMContentLoaded', () => {
    // Apply saved theme
    document.body.dataset.theme = state.theme;
    
    // Start on onboarding or home
    const startScreen = state.isOnboarded ? 'home' : 'onboarding';
    navigate(startScreen);
    
    // Preload all screens
    state.screens.concat(state.moreScreens).forEach(s => loadScreenContent(s.id));
    
    // Health check
    api.health().then(d => console.log('KA Backend:', d)).catch(() => {});
  });

})();
