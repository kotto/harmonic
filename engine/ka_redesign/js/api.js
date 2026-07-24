/**
 * KA API Client — Unified Backend Interface
 * ==========================================
 * Client unifié pour les 53+ endpoints de ka_server.py (port 8765)
 * Plus enterprise_server.py (port 8842) et ka_care.py (port 8700)
 * 
 * Usage: KA.api.get('/api/health') ou KA.api.post('/api/chat', {message: '...'})
 */

(function() {
  'use strict';

  const DEFAULT_HOST = window.location.hostname === 'localhost' 
    ? 'http://localhost:8765' 
    : window.location.origin;

  class KAApiClient {
    constructor(baseUrl = DEFAULT_HOST) {
      this.baseUrl = baseUrl;
      this.enterpriseUrl = baseUrl.replace(':8765', ':8842');
      this.careUrl = baseUrl.replace(':8765', ':8700');
      this.userId = localStorage.getItem('ka_user_id') || 'anonymous';
      this.enterpriseKey = localStorage.getItem('ka_enterprise_key') || null;
    }

    async _fetch(method, path, body = null, options = {}) {
      const url = (options.baseUrl || this.baseUrl) + path;
      const headers = { 'Content-Type': 'application/json', ...options.headers };
      
      if (options.useEnterpriseKey && this.enterpriseKey) {
        headers['X-API-Key'] = this.enterpriseKey;
      }

      const config = { method, headers };
      if (body) config.body = JSON.stringify(body);

      try {
        const res = await fetch(url, config);
        const data = await res.json().catch(() => ({ raw: true }));
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      } catch (err) {
        console.error(`KA API ${method} ${path}:`, err);
        throw err;
      }
    }

    get(path, opts = {}) { return this._fetch('GET', path, null, opts); }
    post(path, body, opts = {}) { return this._fetch('POST', path, body, opts); }

    // ═══ CORE AI ═══
    async chat(message, context = {}) {
      const path = context.voice ? '/api/chat/voice' : '/api/chat';
      return this.post(path, {
        message, user_id: this.userId,
        style: context.style || 'balanced',
        depth: context.depth || 3,
        personality: context.personality || 'ka',
        voice: context.voice || false,
        emotion: context.emotion || 'warm',
      });
    }
    
    // ═══ VOICE / TTS ═══
    async speak(text, emotion = 'warm') {
      const resp = await fetch(this.baseUrl + '/api/voice/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, emotion })
      });
      if (!resp.ok) throw new Error('Voice TTS failed');
      return resp.arrayBuffer();
    }
    
    async chatWithVoice(message, emotion = 'warm') {
      return this.post('/api/chat/voice', {
        message, user_id: this.userId,
        emotion, voice: true,
        personality: 'ka', depth: 'standard',
      });
    }
    
    async getVoices() { return this.get('/api/voice/voices'); }
    async setEmotion(emotion) { return this.post('/api/voice/emotion', { emotion }); }
    async getVoiceInfo() { return this.get('/api/voice/info'); }

    async reason(topic) { return this.post('/api/reason', { topic }); }
    async create(n = 3, conceptA = '', conceptB = '') { 
      return this.post('/api/create', { n, concept_a: conceptA, concept_b: conceptB }); 
    }
    async haiku() { return this.get('/api/haiku'); }
    async surreal(n = 2) { return this.get(`/api/surreal?n=${n}`); }
    async learn(fact) { return this.post('/api/learn', { fact }); }
    async summarize(text) { return this.post('/api/summarize', { text }); }
    async page(topic) { return this.post('/api/page', { topic }); }
    async debug(symptom, code = '') { return this.post('/api/debug', { symptom, code }); }

    // ═══ SPECIALIZATION ═══
    async specialize(domain, depth = 5) {
      return this.post('/api/specialize', { user_id: this.userId, domain, depth });
    }
    async getSpecializeStatus() {
      return this.get(`/api/specialize/status/${this.userId}`);
    }

    // ═══ CODE GENERATION ═══
    async generateCode(prompt, language = 'python') {
      return this.post('/api/code/generate', { prompt, language });
    }
    async waveExplain(question, domain = '') {
      return this.post('/api/wave/explain', { question, domain });
    }

    // ═══ HOLOGRAM STORE ═══
    async storeList(type = '') { return this.get(`/api/store/list?type=${type}`); }
    async storeDownload(holoId) { return this.post(`/api/store/download/${holoId}`, { user_id: this.userId }); }
    async storeLoad(holoId, facts) { return this.post('/api/store/load', { holo_id: holoId, facts }); }
    async storeStats() { return this.get('/api/store/stats'); }

    // ═══ STORAGE ═══
    async storageAnalyze(file) {
      const formData = new FormData(); formData.append('file', file);
      const res = await fetch(this.baseUrl + '/api/storage/analyze', { method: 'POST', body: formData });
      return res.json();
    }
    async storageOptimize(file, quality = 'standard') {
      const formData = new FormData(); formData.append('file', file); formData.append('quality', quality);
      const res = await fetch(this.baseUrl + '/api/storage/optimize', { method: 'POST', body: formData });
      return { blob: await res.blob(), ratio: res.headers.get('X-Ratio'), saved: res.headers.get('X-Saved') };
    }

    // ═══ HEALTH ═══
    async healthDiagnostic(symptoms, vitaux = {}, age = null, sexe = null) {
      return this.post('/api/health/diagnostic', { symptomes: symptoms, vitaux, age, sexe });
    }

    // ═══ ENTERPRISE ═══
    async enterpriseCreateTenant(name) {
      const data = await this._fetch('POST', '/api/v2/enterprise/tenant', 
        { name }, { baseUrl: this.enterpriseUrl });
      if (data.api_key) {
        this.enterpriseKey = data.api_key;
        localStorage.setItem('ka_enterprise_key', data.api_key);
      }
      return data;
    }
    async enterpriseDiagnose(symptom, language = 'fr') {
      return this._fetch('POST', '/api/v2/enterprise/debug',
        { symptom, language }, { baseUrl: this.enterpriseUrl, useEnterpriseKey: true });
    }
    async enterpriseLearn(symptom, diagnosis, category = '') {
      return this._fetch('POST', '/api/v2/enterprise/learn',
        { symptom, diagnosis, category }, { baseUrl: this.enterpriseUrl, useEnterpriseKey: true });
    }
    async enterpriseFeedback(symptom, predicted, correct) {
      return this._fetch('POST', '/api/v2/enterprise/feedback',
        { symptom, predicted, correct }, { baseUrl: this.enterpriseUrl, useEnterpriseKey: true });
    }
    async enterpriseStats() {
      return this._fetch('GET', '/api/v2/enterprise/stats', null,
        { baseUrl: this.enterpriseUrl, useEnterpriseKey: true });
    }
    async enterpriseUpload(files) {
      const formData = new FormData();
      for (const f of files) formData.append('files', f);
      const res = await fetch(this.enterpriseUrl + '/api/v2/enterprise/upload', {
        method: 'POST', headers: { 'X-API-Key': this.enterpriseKey }, body: formData
      });
      return res.json();
    }

    // ═══ MEDIA ═══
    async mediaGenerate(prompt, modalities = ['image'], width = 512, height = 512) {
      return this.post('/api/media/generate', { prompt, modalities, width, height });
    }

    // ═══ HEALTH CHECK ═══
    async health() { return this.get('/api/health'); }
    async stats() { return this.get('/api/stats'); }
    async metrics() { return this.get('/api/metrics'); }
    async profile() { return this.get(`/api/profile/${this.userId}`); }

    // ═══ WEB SEARCH ═══
    async searchWeb(query, maxResults = 5) {
      return this.post('/api/search_web', { query, max_results: maxResults, lang: 'fr' });
    }

    // ═══ POETRY ═══
    async poem(theme, form = 'libre', emotion = '') {
      return this.post('/api/poem', { theme, form, emotion, user_id: this.userId });
    }
  }

  // Expose globally
  window.KAApiClient = KAApiClient;
})();
