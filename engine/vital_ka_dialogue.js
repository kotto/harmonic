/**
 * Vital Ka DIALOGUE — Orchestrateur Vocal Bidirectionnel
 * ========================================================
 * Relie le STT (micro → texte) à l'IA (texte → réponse) et au TTS (réponse → voix).
 *
 * Deux modes :
 *   🩺 'conseiller' — Voix autoritaire, réponses techniques
 *                     (diagnostic, protocoles, médicaments, phyto)
 *   🤗 'compagnon'  — Voix chaleureuse, explications simples
 *                     (éducation patient, conseils pratiques, empathie)
 *
 * Usage :
 *   KA_DIALOGUE.start();     // maintenir bouton → écoute micro
 *   KA_DIALOGUE.stop();      // relâcher → traite + répond vocalement
 *   KA_DIALOGUE.toggleMode();// basculer conseiller ↔ compagnon
 *
 * Dépendances : KA_STT, KA_VOICE, kaAI (vital_ka_ai.js), aiAddMessage()
 */

const KA_DIALOGUE = (() => {
  'use strict';

  let _mode = 'conseiller';       // 'conseiller' | 'compagnon'
  let _state = 'idle';            // 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
  let _lastRecognizedText = '';

  // ── Callbacks ──
  let _onStateChange = null;      // function(state, mode)
  let _onText = null;             // function(text, isInterim)
  let _onResponse = null;         // function(responseText, mode)

  // ═══════════════════════════════════════════════════════════════
  // API PUBLIQUE
  // ═══════════════════════════════════════════════════════════════

  function getState() { return _state; }
  function getMode()  { return _mode; }

  /** Démarre l'écoute micro (appelé au mousedown/touchstart) */
  function start() {
    if (!KA_STT.isSupported()) {
      _setState('error');
      if (typeof aiAddMessage === 'function') {
        aiAddMessage('⚠️ Reconnaissance vocale non supportée sur ce navigateur. Utilisez Chrome ou Edge.', 'system');
      }
      return;
    }
    if (_state === 'listening') return;

    // Déverrouiller l'AudioContext dans le geste utilisateur (prérequis TTS)
    if (typeof KA_VOICE !== 'undefined' && KA_VOICE.server) {
      KA_VOICE.server.unlock();
    }

    _lastRecognizedText = '';
    _setState('listening');

    // Configurer le callback STT
    KA_STT.onResult = (text) => {
      _lastRecognizedText = text;
      if (_onText) _onText(text, false);
    };
    KA_STT.onInterim = (text) => {
      if (_onText) _onText(text, true);
    };
    KA_STT.onError = (err) => {
      _setState('error');
      if (typeof aiAddMessage === 'function') {
        aiAddMessage('⚠️ ' + err.message, 'system');
      }
    };

    KA_STT.start('fr-FR');
  }

  /** Arrête l'écoute et traite le texte (appelé au mouseup/touchend) */
  async function stop() {
    if (_state !== 'listening') return;

    const text = KA_STT.stop();
    _setState('processing');

    if (text && text.trim()) {
      await _process(text.trim());
    } else {
      _setState('idle');
    }
  }

  /** Bascule entre les modes conseiller ↔ compagnon */
  function toggleMode() {
    _mode = _mode === 'conseiller' ? 'compagnon' : 'conseiller';
    if (_onStateChange) _onStateChange(_state, _mode);

    if (typeof aiAddMessage === 'function') {
      const label = _mode === 'conseiller'
        ? '🩺 Mode **Conseiller** — Réponses techniques, diagnostic'
        : '🤗 Mode **Compagnon** — Explications simples, conseils';
      aiAddMessage(label, 'system');
    }

    // Mettre à jour le bouton
    _updateModeButton();
  }

  /** Définir le mode explicitement */
  function setMode(mode) {
    if (mode === _mode) return;
    _mode = mode === 'compagnon' ? 'compagnon' : 'conseiller';
    if (_onStateChange) _onStateChange(_state, _mode);
    _updateModeButton();
  }

  /** Annule l'opération en cours */
  function cancel() {
    KA_STT.abort();
    if (typeof KA_VOICE !== 'undefined' && KA_VOICE.stop) {
      KA_VOICE.stop();
    }
    _setState('idle');
  }

  // ═══════════════════════════════════════════════════════════════
  // TRAITEMENT
  // ═══════════════════════════════════════════════════════════════

  async function _process(text) {
    // Afficher le texte reconnu dans le chat
    if (typeof aiAddMessage === 'function') {
      aiAddMessage('🎤 ' + text, 'user');
    }

    let response;

    if (_mode === 'conseiller') {
      response = await _processConseiller(text);
    } else {
      response = await _processCompagnon(text);
    }

    if (response) {
      // Afficher la réponse
      if (typeof aiAddMessage === 'function') {
        const icon = _mode === 'conseiller' ? '🩺' : '🤗';
        aiAddMessage(icon + ' ' + response, 'ai');
      }

      // Callback
      if (_onResponse) _onResponse(response, _mode);

      // Synthèse vocale
      _setState('speaking');
      if (typeof KA_VOICE !== 'undefined' && KA_VOICE.speak) {
        try {
          await KA_VOICE.speak(response, _mode);
        } catch (e) {
          console.warn('[KA_DIALOGUE] Erreur TTS:', e.message);
        }
      }
    }

    _setState('idle');
  }

  /**
   * Mode Conseiller : routage vers les fonctions IA existantes
   */
  async function _processConseiller(text) {
    const q = text.toLowerCase();

    // Essayer d'abord le backend /api/chat si disponible
    try {
      const backendResponse = await _tryBackendChat(text);
      if (backendResponse) return backendResponse;
    } catch (e) { /* fallback local */ }

    // ── Routage local (déterministe) ──

    // 1. Question sur le diagnostic en cours
    if (q.includes('explique') || q.includes('diagnostic') || q.includes('pourquoi') || q.includes('resultat')) {
      return _explainCurrentDiagnosis();
    }

    // 2. Diagnostics différentiels
    if (q.includes('différentiel') || q.includes('autre possibilit') || q.includes('compar')) {
      return _explainDifferentials();
    }

    // 3. Médicaments
    if (q.includes('médicament') || q.includes('traitement') || q.includes('dose') || q.includes('prescri')) {
      return _searchDrug(text);
    }

    // 4. Protocoles mère-enfant
    if (q.includes('grossesse') || q.includes('enceinte') || q.includes('mère') || q.includes('enfant') || q.includes('accouchement')) {
      return _searchProtocol(text);
    }

    // 5. Plantes / phytothérapie
    if (q.includes('plante') || q.includes('phyto') || q.includes('traditionnel') || q.includes('remède naturel')) {
      return _explainPhyto();
    }

    // 6. Hologramme
    if (q.includes('hologramme') || q.includes('profil') || q.includes('antécédent')) {
      return _explainHologram();
    }

    // 7. Clarification (réponse à une question en attente)
    if (typeof pendingClarification !== 'undefined' && pendingClarification) {
      return _handleClarification(text);
    }

    // 8. Fallback : recherche médicale générale
    if (typeof kaAI !== 'undefined' && kaAI && kaAI.searchMedical) {
      try {
        return kaAI.searchMedical(text);
      } catch (e) { /* ignore */ }
    }

    // 9. Dernier recours : analyse des symptômes
    if (_looksLikeSymptoms(text)) {
      return _suggestDiagnosis(text);
    }

    return _genericConseillerResponse(text);
  }

  /**
   * Mode Compagnon : reformulation patient, empathie, conseils pratiques
   */
  async function _processCompagnon(text) {
    const q = text.toLowerCase();

    // 1. Si un diagnostic existe, l'expliquer en langage simple
    const diag = _getCurrentDiagnosis();
    if (diag && (q.includes('explique') || q.includes('comprendre') || q.includes('c\'est quoi') || q.includes('maladie'))) {
      return _buildCompanionExplanation(diag);
    }

    // 2. Conseils pratiques basés sur le diagnostic
    if (diag && (q.includes('conseil') || q.includes('faire') || q.includes('manger') || q.includes('boire') || q.includes('repos'))) {
      return _buildCompanionAdvice(diag);
    }

    // 3. Plantes en langage simple
    if (q.includes('plante') || q.includes('remède') || q.includes('naturel') || q.includes('tisane')) {
      return _buildCompanionPhyto(diag);
    }

    // 4. Nouveaux symptômes → orienter vers le diagnostic
    if (_looksLikeSymptoms(text)) {
      return _buildCompanionTriage(text);
    }

    // 5. Réponse empathique générique
    return _buildCompanionGeneric(text);
  }

  // ═══════════════════════════════════════════════════════════════
  // AIDES INTERNES
  // ═══════════════════════════════════════════════════════════════

  function _getCurrentDiagnosis() {
    if (typeof getLastDiagnosis === 'function') {
      return getLastDiagnosis();
    }
    return null;
  }

  function _explainCurrentDiagnosis() {
    const diag = _getCurrentDiagnosis();
    if (!diag) return "Aucun diagnostic en cours. Lancez d'abord une analyse depuis l'écran Résonance.";
    if (typeof kaAI !== 'undefined' && kaAI && kaAI.explain) {
      const holo = typeof buildCurrentHologram === 'function' ? buildCurrentHologram() : null;
      return kaAI.explain(diag.top, holo, diag.pVec);
    }
    return 'Diagnostic : ' + diag.top.name + ' (confiance ' + Math.round(diag.top.score * 100) + '%). ' + (diag.top.c || '');
  }

  function _explainDifferentials() {
    const diag = _getCurrentDiagnosis();
    if (!diag || !diag.scores || diag.scores.length < 2) return "Pas assez de diagnostics différentiels. Lancez un diagnostic d'abord.";
    if (typeof kaAI !== 'undefined' && kaAI && kaAI.reason) {
      const holo = typeof buildCurrentHologram === 'function' ? buildCurrentHologram() : null;
      return kaAI.reason(diag.scores, holo);
    }
    let text = '## Diagnostics différentiels\n\n';
    for (const r of diag.scores.slice(0, 5)) {
      text += `- **${r.name}** : ${Math.round(r.score * 100)}%\n`;
    }
    return text;
  }

  function _searchDrug(text) {
    if (typeof kaAI !== 'undefined' && kaAI && kaAI.searchMedical) {
      return kaAI.searchMedical(text);
    }
    return "Recherche de médicaments : fonctionnalité en cours d'initialisation.";
  }

  function _searchProtocol(text) {
    if (typeof kaAI !== 'undefined' && kaAI && kaAI.searchMedical) {
      return kaAI.searchMedical(text);
    }
    return "Protocoles mère-enfant : fonctionnalité en cours d'initialisation.";
  }

  function _explainPhyto() {
    const diag = _getCurrentDiagnosis();
    if (!diag) return "Aucun diagnostic en cours. Lancez une analyse pour voir les plantes associées.";
    if (typeof Knowledge === 'object' && Knowledge && Knowledge.getPhytoFor && diag.top && diag.top.name) {
      try {
        const plants = Knowledge.getPhytoFor([diag.top.name], diag.pVec || null);
        if (!plants || !plants.length) return 'Aucune plante documentée pour ' + diag.top.name + '.';
        let text = '## 🌿 Plantes pour ' + diag.top.name + '\n\n';
        const ab = plants.filter(p => p.grade_evidence === 'A' || p.grade_evidence === 'B');
        for (const p of ab.slice(0, 5)) {
          const local = (p.noms_locaux && p.noms_locaux.length) ? ' (' + p.noms_locaux[0] + ')' : '';
          text += `- **${p.nom_scientifique}**${local} — Grade ${p.grade_evidence}\n  ${p.partie_utilisee} · ${p.preparation}\n`;
        }
        const vig = plants.filter(p => p.niveau_recommandation === 'vigilance');
        if (vig.length) {
          text += '\n⚠️ Plantes à éviter :\n';
          for (const p of vig.slice(0, 3)) {
            text += `- ${p.nom_scientifique} — ${p.precautions || 'Toxique'}\n`;
          }
        }
        text += '\n*La phytothérapie ne remplace pas le traitement de référence.*';
        return text;
      } catch (e) { return 'Erreur lors de la recherche de plantes.'; }
    }
    return 'Base de connaissances phytothérapie non disponible.';
  }

  function _explainHologram() {
    if (typeof buildCurrentHologram === 'function') {
      const holo = buildCurrentHologram();
      if (holo && holo.features && holo.features.length) {
        return '🧬 Hologramme patient : ' + holo.features.length + ' caractéristiques encodées.';
      }
    }
    return "Aucun hologramme disponible. Remplissez les informations patient.";
  }

  function _handleClarification(text) {
    // Appeler la boucle de clarification existante
    if (typeof aiSend === 'function') {
      aiSend();  // le texte est déjà dans l'input ou traité
    }
    return 'Réponse intégrée. Le diagnostic a été affiné.';
  }

  function _suggestDiagnosis(text) {
    return "Ces symptômes méritent un diagnostic. Je vous invite à les saisir dans l'écran Résonance pour une analyse complète. En attendant, voici ce que je peux vous dire : " + (_genericConseillerResponse(text) || "Surveillez l'évolution et consultez si les symptômes persistent.");
  }

  function _genericConseillerResponse(text) {
    // Utiliser l'IA locale si disponible
    if (typeof kaAI !== 'undefined' && kaAI && kaAI.searchMedical) {
      try { return kaAI.searchMedical(text); } catch (e) { /* ignore */ }
    }
    return "Question notée. Pour une analyse détaillée, utilisez l'écran Résonance (diagnostic) ou l'écran IA (recherche médicale).";
  }

  function _looksLikeSymptoms(text) {
    const symptomWords = ['mal', 'douleur', 'fièvre', 'tousse', 'vomi', 'diarrhée', 'fatigue', 'maux', 'courbature', 'frisson', 'saigne'];
    const q = text.toLowerCase();
    return symptomWords.some(w => q.includes(w));
  }

  // ═══════════════════════════════════════════════════════════════
  // RÉPONSES MODE COMPAGNON
  // ═══════════════════════════════════════════════════════════════

  function _buildCompanionExplanation(diag) {
    if (!diag || !diag.top) return "Je n'ai pas encore de diagnostic à vous expliquer.";
    const t = diag.top;
    const pct = Math.round((t.score || 0) * 100);
    let text = 'D\'après les symptômes que vous avez décrits, ';
    text += 'il pourrait s\'agir de **' + t.name.replace(/_/g, ' ') + '**. ';
    text += 'J\'ai une confiance de ' + pct + '% dans cette hypothèse. ';
    if (t.c) {
      text += '\n\nVoici ce que je vous recommande : ' + t.c + ' ';
    }
    if (t.d) {
      text += 'Je vous suggère de consulter dans un délai ' + t.d.toLowerCase() + '. ';
    }
    text += '\n\nNe vous inquiétez pas, cette maladie est bien connue et se traite efficacement. ';
    text += 'Avez-vous des questions sur ce diagnostic ?';
    return text;
  }

  function _buildCompanionAdvice(diag) {
    if (!diag || !diag.top) return "Je n'ai pas assez d'informations pour vous donner des conseils personnalisés.";
    const t = diag.top;
    let text = 'Pour **' + t.name.replace(/_/g, ' ') + '**, voici quelques conseils pratiques :\n\n';
    text += '💧 **Hydratation** : Buvez beaucoup d\'eau potable (au moins 2 litres par jour).\n';
    text += '😴 **Repos** : Reposez-vous autant que possible pour aider votre corps à guérir.\n';
    text += '🍽️ **Alimentation** : Mangez léger, privilégiez les fruits et légumes frais.\n';
    if (t.c) {
      text += '\n▶ ' + t.c + '\n';
    }
    text += '\n⚠️ Consultez un médecin si les symptômes s\'aggravent ou persistent.';
    return text;
  }

  function _buildCompanionPhyto(diag) {
    if (!diag || !diag.top) return "Faites d'abord un diagnostic pour connaître les plantes adaptées à votre situation.";
    if (typeof Knowledge === 'object' && Knowledge && Knowledge.getPhytoFor) {
      try {
        const plants = Knowledge.getPhytoFor([diag.top.name], diag.pVec || null);
        if (!plants || !plants.length) return "Je n'ai pas trouvé de plantes traditionnelles documentées pour cette condition.";
        let text = '🌿 Voici quelques **plantes traditionnelles** qui peuvent vous aider :\n\n';
        const ab = plants.filter(p => p.grade_evidence === 'A' || p.grade_evidence === 'B');
        for (const p of ab.slice(0, 4)) {
          const local = (p.noms_locaux && p.noms_locaux.length) ? ' (aussi appelé ' + p.noms_locaux[0] + ')' : '';
          text += `- **${p.nom_scientifique}**${local}\n  Utilisez les ${p.partie_utilisee.toLowerCase()}. Préparation : ${p.preparation.toLowerCase()}.\n`;
        }
        const vig = plants.filter(p => p.niveau_recommandation === 'vigilance');
        if (vig.length) {
          text += '\n⚠️ **Attention**, ces plantes sont toxiques, ne les utilisez pas :\n';
          for (const p of vig.slice(0, 2)) {
            text += `- ${p.nom_scientifique}\n`;
          }
        }
        text += '\n🌿 Ces plantes sont un **complément**, elles ne remplacent pas votre traitement médical.';
        return text;
      } catch (e) { return "Je n'ai pas pu accéder aux informations sur les plantes."; }
    }
    return "La base de données des plantes n'est pas disponible pour le moment.";
  }

  function _buildCompanionTriage(text) {
    let response = 'Merci d\'avoir partagé ces informations. ';
    response += 'Pour vous aider au mieux, je vous invite à saisir ces symptômes dans l\'écran **Résonance** (🔍). ';
    response += 'Cela permettra d\'identifier la cause possible et de vous proposer des plantes adaptées. ';
    response += '\n\nEn attendant, reposez-vous et buvez beaucoup d\'eau. ';
    response += 'Si vous avez de la fièvre, de fortes douleurs ou des saignements, consultez rapidement un médecin.';
    return response;
  }

  function _buildCompanionGeneric(text) {
    const q = text.toLowerCase();
    if (q.includes('bonjour') || q.includes('salut')) {
      return 'Bonjour ! Je suis votre compagnon Vital Ka. Je peux vous expliquer votre état de santé, vous conseiller des plantes traditionnelles, ou répondre à vos questions. Comment puis-je vous aider ?';
    }
    if (q.includes('merci')) {
      return 'Avec plaisir ! N\'hésitez pas si vous avez d\'autres questions. Prenez soin de vous. 🌿';
    }
    if (q.includes('qui es') || q.includes('tu es')) {
      return 'Je suis votre **compagnon de santé** Vital Ka. Mon rôle est de vous accompagner avec des explications simples, des conseils pratiques et des informations sur les plantes médicinales traditionnelles. Je travaille avec votre soignant pour vous offrir les meilleurs conseils.';
    }
    return 'Je vous écoute. Décrivez-moi ce qui vous préoccupe, je ferai de mon mieux pour vous aider avec des conseils adaptés. 🌿';
  }

  // ═══════════════════════════════════════════════════════════════
  // BACKEND (optionnel)
  // ═══════════════════════════════════════════════════════════════

  async function _tryBackendChat(text) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      const resp = await fetch('http://localhost:8765/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          style: _mode === 'compagnon' ? 'chaleureux' : 'concise',
          depth: 'standard',
          personality: _mode === 'compagnon' ? 'vulgarisateur' : 'savant',
        }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (resp.ok) {
        const data = await resp.json();
        return data.response || null;
      }
    } catch (e) { /* serveur injoignable, fallback local */ }
    return null;
  }

  // ═══════════════════════════════════════════════════════════════
  // UI
  // ═══════════════════════════════════════════════════════════════

  function _setState(state) {
    _state = state;
    if (_onStateChange) _onStateChange(state, _mode);
    _updateMicButton();
    _updateStatusText();
  }

  function _updateMicButton() {
    if (typeof document === 'undefined') return;
    const btn = document.getElementById('micBtn');
    if (!btn) return;
    btn.className = 'mic-btn ' + _state;
    const labels = {
      idle: '🎤 Maintenir pour parler',
      listening: '🔴 Parlez...',
      processing: '⏳ Analyse...',
      speaking: '🔊 Réponse...',
      error: '⚠️ Réessayer',
    };
    btn.textContent = labels[_state] || labels.idle;
  }

  function _updateModeButton() {
    if (typeof document === 'undefined') return;
    const btn = document.getElementById('voiceModeBtn');
    if (!btn) return;
    btn.textContent = _mode === 'conseiller' ? '🩺 Conseiller' : '🤗 Compagnon';
    btn.className = 'mode-btn ' + _mode;
  }

  function _updateStatusText() {
    if (typeof document === 'undefined') return;
    const el = document.getElementById('voiceStatus');
    if (!el) return;
    const texts = {
      idle: 'Maintenez le micro pour parler',
      listening: 'Je vous écoute...',
      processing: 'Je réfléchis...',
      speaking: 'Je vous réponds...',
      error: 'Une erreur est survenue',
    };
    el.textContent = texts[_state] || texts.idle;
  }

  // ── Initialisation au chargement ──
  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        _updateModeButton();
        _updateMicButton();
        _updateStatusText();
      }, 800);
    });
  }

  return {
    start, stop, cancel, toggleMode, setMode,
    getState, getMode,
    get onStateChange() { return _onStateChange; },
    set onStateChange(fn) { _onStateChange = fn; },
    get onText() { return _onText; },
    set onText(fn) { _onText = fn; },
    get onResponse() { return _onResponse; },
    set onResponse(fn) { _onResponse = fn; },
  };
})();
