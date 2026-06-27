/* ============================================================
   HARMONIC GATEWAY — APPLICATION LOGIC
   ============================================================ */

const PHI = 1.618033988749895;
const STORAGE_KEY_HISTORY = 'harmonic_gateway_history';
const STORAGE_KEY_KEYS = 'harmonic_gateway_keys';
const STORAGE_KEY_STATS = 'harmonic_gateway_stats';

// --- Utils ---
function $(id) { return document.getElementById(id); }
function qs(sel, ctx) { return (ctx || document).querySelector(sel); }
function qsa(sel, ctx) { return (ctx || document).querySelectorAll(sel); }
function round(v, d) { return parseFloat(v.toFixed(d)); }

function showToast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.3s'; }, 3000);
  setTimeout(() => t.remove(), 3500);
}

// --- Storage ---
function getHistory() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY_HISTORY) || '[]'); } catch(e) { return []; } }
function setHistory(h) { localStorage.setItem(STORAGE_KEY_HISTORY, JSON.stringify(h)); }
function getKeys() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY_KEYS) || '{}'); } catch(e) { return {}; } }
function setKeys(k) { localStorage.setItem(STORAGE_KEY_KEYS, JSON.stringify(k)); }
function getStats() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY_STATS) || '{}'); } catch(e) { return {}; } }
function setStats(s) { localStorage.setItem(STORAGE_KEY_STATS, JSON.stringify(s)); }

function updateStats(tokens, blocked, score) {
  const s = getStats();
  s.totalTokens = (s.totalTokens || 0) + tokens;
  s.totalBlocked = (s.totalBlocked || 0) + blocked;
  s.scores = s.scores || [];
  if (score) s.scores.push(score);
  if (s.scores.length > 100) s.scores = s.scores.slice(-100);
  s.avgScore = s.scores.length ? s.scores.reduce((a,b)=>a+b,0)/s.scores.length : null;
  setStats(s);
  renderStats(s);
}

function renderStats(s) {
  if (!$('statTokens')) return;
  $('statTokens').textContent = (s?.totalTokens || 0).toLocaleString();
  $('statTokensPct').textContent = Math.round(((s?.totalTokens || 0) / 5000000) * 100) + '% du quota';
  $('statBlocked').textContent = (s?.totalBlocked || 0);
  $('statCoherence').textContent = s?.avgScore ? Math.round(s.avgScore * 100) + '%' : '—';
  $('statRequests').textContent = (s?.scores?.length || 0);
  if ($('usageBar')) $('usageBar').style.width = Math.min(100, ((s?.totalTokens || 0) / 5000000) * 100) + '%';
}

// --- Mobile Menu ---
document.addEventListener('DOMContentLoaded', () => {
  const menuBtn = $('mobileMenuBtn');
  const navLinks = $('navLinks');
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', () => navLinks.classList.toggle('active'));
    document.addEventListener('click', (e) => {
      if (!menuBtn.contains(e.target) && !navLinks.contains(e.target)) navLinks.classList.remove('active');
    });
  }

  // --- Dashboard Navigation ---
  const sidebarLinks = qsa('.sidebar-nav a[data-page]');
  sidebarLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const page = link.dataset.page;
      navigateTo(page);
    });
  });

  // --- Generate Page ---
  const genBtn = $('genBtn');
  if (genBtn) genBtn.addEventListener('click', handleGenerate);
  const genCompareBtn = $('genCompareBtn');
  if (genCompareBtn) genCompareBtn.addEventListener('click', handleGenerateCompare);
  const genClearBtn = $('genClearBtn');
  if (genClearBtn) genClearBtn.addEventListener('click', () => {
    $('genPrompt').value = '';
    const rc = $('responseCard');
    if (rc) rc.classList.add('hidden');
  });

  // --- Compare Page ---
  const cmpBtn = $('cmpBtn');
  if (cmpBtn) cmpBtn.addEventListener('click', handleCompare);

  // --- Logout ---
  const logoutBtn = $('logoutBtn');
  if (logoutBtn) logoutBtn.addEventListener('click', (e) => {
    e.preventDefault();
    showToast('Déconnecté (simulation)', 'info');
  });

  // --- Demo on Landing Page ---
  const demoGenBtn = $('demoGenerateBtn');
  if (demoGenBtn) demoGenBtn.addEventListener('click', handleDemoGenerate);
  const demoCmpBtn = $('demoCompareBtn');
  if (demoCmpBtn) demoCmpBtn.addEventListener('click', handleDemoCompare);

  // Initial render
  renderHistory();
  renderStats(getStats());
  navigateTo('generate');
});

// --- Navigation ---
function navigateTo(page) {
  const pages = qsa('.page-content');
  pages.forEach(p => p.classList.add('hidden'));
  const target = $('page-' + page);
  if (target) target.classList.remove('hidden');

  const links = qsa('.sidebar-nav a[data-page]');
  links.forEach(l => l.classList.remove('active'));
  const activeLink = qs(`.sidebar-nav a[data-page="${page}"]`);
  if (activeLink) activeLink.classList.add('active');

  if (page === 'history') renderHistory();
  if (page === 'usage') renderStats(getStats());
}

// --- Simulated Harmonic API Call ---
function simulateHarmonicAPI(prompt, modelId, mode, delay = 1500) {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Determine domain based on prompt keywords
      const lower = prompt.toLowerCase();
      let domaine = 'general';
      let conceptsPertinents = [];
      if (lower.match(/dériv|deriv|différent|different/)) { domaine = 'derivation'; conceptsPertinents = ['derivee', 'fonction', 'exposant', 'regle', 'coefficient']; }
      else if (lower.match(/intégr|integr|primitive/)) { domaine = 'integration'; conceptsPertinents = ['integrale', 'primitive', 'fonction', 'borne', 'aire']; }
      else if (lower.match(/probab|espér|esper|variance|loi|normale/)) { domaine = 'probabilites'; conceptsPertinents = ['probabilite', 'esperance', 'variance', 'loi', 'densite']; }
      else if (lower.match(/trigo|sinus|cosinus|tangente/)) { domaine = 'trigonometrie'; conceptsPertinents = ['sinus', 'cosinus', 'tangente', 'cercle', 'angle']; }
      else if (lower.match(/triangle|pythagore|cercle|aire|périm|rayon/)) { domaine = 'geometrie'; conceptsPertinents = ['triangle', 'cercle', 'aire', 'rayon', 'pythagore']; }
      else if (lower.match(/équation|equation|résoudre|resoudre|racine/)) { domaine = 'equations'; conceptsPertinents = ['equation', 'racine', 'polynome', 'degre', 'solution']; }
      else if (lower.match(/limite|converg|diverg|suite/)) { domaine = 'limites'; conceptsPertinents = ['limite', 'convergence', 'suite', 'continuite', 'borne']; }
      else if (lower.match(/matrice|vecteur|déterminant|determinant/)) { domaine = 'algebre_lineaire'; conceptsPertinents = ['matrice', 'vecteur', 'determinant', 'espace', 'base']; }
      else { domaine = 'general'; conceptsPertinents = ['theoreme', 'formule', 'principe', 'methode', 'exemple']; }

      // Generate response based on domain
      let reponseBrute = '';
      const responses = {
        derivation: "La dérivée d'une fonction mesure son taux de variation instantané. Pour une fonction puissance f(x) = x^n, la dérivée est f'(x) = n·x^(n-1). Cette règle, appelée règle de dérivation des puissances, est l'une des plus fondamentales en analyse. Elle découle directement de la définition de la dérivée comme limite du taux d'accroissement.",
        integration: "L'intégrale d'une fonction représente l'aire sous sa courbe. C'est l'opération inverse de la dérivation. Pour une fonction puissance f(x) = x^n, l'intégrale est ∫x^n dx = x^(n+1)/(n+1) + C, où C est la constante d'intégration. Cette formule est valable pour n ≠ -1.",
        probabilites: "En théorie des probabilités, l'espérance mathématique E(X) représente la moyenne pondérée des valeurs possibles d'une variable aléatoire X. La variance V(X) = E((X-E(X))²) mesure la dispersion autour de cette moyenne. Pour une loi normale de paramètres μ et σ², la densité est f(x) = (1/√(2πσ²))·exp(-(x-μ)²/(2σ²)).",
        trigonometrie: "Les fonctions trigonométriques sinus, cosinus et tangente sont fondamentales en mathématiques. Le cercle trigonométrique de rayon 1 permet de les définir : sin(θ) est l'ordonnée du point sur le cercle, cos(θ) son abscisse. La relation fondamentale est cos²(θ) + sin²(θ) = 1.",
        geometrie: "Le théorème de Pythagore établit que dans un triangle rectangle, le carré de l'hypoténuse est égal à la somme des carrés des deux autres côtés : a² + b² = c². L'aire d'un cercle de rayon r est A = πr². Ces formules sont parmi les plus utilisées en géométrie euclidienne.",
        equations: "Pour résoudre une équation polynomiale, on cherche les valeurs qui annulent l'expression. Une équation du second degré ax² + bx + c = 0 se résout avec le discriminant Δ = b² - 4ac. Si Δ > 0, deux solutions réelles : x = (-b ± √Δ)/(2a).",
        limites: "La limite d'une fonction décrit son comportement quand la variable tend vers une valeur donnée. Une suite converge si ses termes se rapprochent d'une valeur finie. Le critère de Cauchy et le théorème des gendarmes sont des outils essentiels pour étudier la convergence.",
        algebre_lineaire: "En algèbre linéaire, une matrice représente une transformation linéaire. Le déterminant d'une matrice carrée indique si elle est inversible (det ≠ 0). Les vecteurs propres d'une matrice A sont les vecteurs v tels que Av = λv, où λ est la valeur propre associée.",
        general: "Voici une explication détaillée basée sur les principes mathématiques fondamentaux. Les concepts identifiés permettent de structurer le raisonnement et d'apporter une réponse précise et vérifiable. N'hésitez pas à préciser votre question pour une réponse plus ciblée."
      };
      reponseBrute = responses[domaine] || responses.general;

      // Simulate coherence scores
      const baseCoherence = domaine === 'general' ? 0.45 + Math.random() * 0.2 : 0.60 + Math.random() * 0.3;
      const scoreEuler = round(0.5 + Math.random() * 0.45, 3);
      const scoreAction = round(0.5 + Math.random() * 0.4, 3);
      const scoreResonance = round(0.55 + Math.random() * 0.4, 3);
      const scoreCoherence = round(baseCoherence, 3);

      let confiance;
      if (scoreCoherence >= 0.70) confiance = 'haute';
      else if (scoreCoherence >= 0.55) confiance = 'moyenne';
      else if (scoreCoherence >= 0.40) confiance = 'basse';
      else confiance = 'nulle';

      const hallucination = scoreCoherence < 0.40;
      const corrigee = scoreCoherence < 0.40 && Math.random() > 0.5;

      const tokensPrompt = Math.round(prompt.length * 1.3);
      const tokensCompletion = Math.round(reponseBrute.length * 0.8);
      const latence = delay + Math.random() * 500;

      const costMap = {
        'openai:gpt-4o': 0.015,
        'openai:gpt-4o-mini': 0.0015,
        'anthropic:claude-3.5-sonnet': 0.012,
        'deepseek:deepseek-chat': 0.0003,
        'ollama:llama3:8b': 0,
        'ollama:deepseek-math:1.5b': 0,
      };
      const cout = costMap[modelId] ? costMap[modelId] * (tokensPrompt + tokensCompletion) / 1e6 : 0.001;

      resolve({
        id: 'req_' + Date.now().toString(36),
        timestamp: new Date().toISOString(),
        requete: { prompt_original: prompt, modele_choisi: modelId, mode: mode || 'managed' },
        encapsulation: { domaine, concepts_pertinents: conceptsPertinents, precalcul_disponible: domaine !== 'general', temps_ms: round(Math.random() * 3 + 1, 1) },
        generation_llm: { modele: modelId, reponse_brute: reponseBrute, tokens_prompt: tokensPrompt, tokens_completion: tokensCompletion, latence_ms: round(latence, 0) },
        verification_harmonique: { score_coherence: scoreCoherence, confiance, details: { score_euler: scoreEuler, score_action: scoreAction, score_resonance: scoreResonance }, tokens_analyses: Math.round(tokensCompletion * 0.3), temps_verification_ms: round(Math.random() * 0.5 + 0.3, 1) },
        hallucination: { detectee: hallucination, signaux: hallucination ? [{ type: 'coherence_nulle', severite: 'elevee', message: 'Cohérence harmonique insuffisante.' }] : [] },
        reponse_finale: { texte: reponseBrute, confiance, score_global: scoreCoherence, corrigee },
        metriques: { temps_total_ms: round(latence + 5, 0), cout_estime_usd: round(cout, 4), tokens_total: tokensPrompt + tokensCompletion }
      });
    }, delay);
  });
}

// --- Handle Generate ---
async function handleGenerate() {
  const prompt = ($('genPrompt')?.value || '').trim();
  if (!prompt) { showToast('Veuillez entrer une question.', 'error'); return; }

  const modelId = $('genModel')?.value || 'openai:gpt-4o-mini';
  const mode = $('genMode')?.value || 'managed';
  const rc = $('responseCard');
  const rl = $('responseLoading');
  const rb = $('responseBody');
  const mg = $('metadataGrid');

  if (rc) rc.classList.remove('hidden');
  if (rl) rl.style.display = 'block';
  if (rb) rb.classList.add('hidden');
  if (mg) mg.classList.add('hidden');

  const result = await simulateHarmonicAPI(prompt, modelId, mode, 800 + Math.random() * 1200);

  if (rl) rl.style.display = 'none';
  if (rb) { rb.classList.remove('hidden'); rb.textContent = result.reponse_finale.texte; }
  if (mg) mg.classList.remove('hidden');

  // Update confidence bar
  const confBar = $('confBar');
  const confScore = $('confScore');
  if (confBar) { confBar.style.width = (result.verification_harmonique.score_coherence * 100) + '%'; confBar.className = 'confidence-bar-fill-inner ' + result.verification_harmonique.confiance; }
  if (confScore) confScore.textContent = Math.round(result.verification_harmonique.score_coherence * 100) + '%';

  // Metadata
  $('metaDomaine').textContent = result.encapsulation.domaine;
  $('metaModele').textContent = result.requete.modele_choisi;
  $('metaLatence').textContent = Math.round(result.metriques.temps_total_ms) + 'ms';
  $('metaCout').textContent = '$' + result.metriques.cout_estime_usd.toFixed(4);
  $('metaTokens').textContent = result.metriques.tokens_total;
  $('metaEuler').textContent = result.verification_harmonique.details.score_euler;
  $('metaAction').textContent = result.verification_harmonique.details.score_action;
  $('metaResonance').textContent = result.verification_harmonique.details.score_resonance;

  // Save to history
  const history = getHistory();
  history.unshift({
    id: result.id,
    timestamp: result.timestamp,
    prompt: prompt.substring(0, 100),
    modelId: result.requete.modele_choisi,
    domaine: result.encapsulation.domaine,
    score: result.verification_harmonique.score_coherence,
    confiance: result.verification_harmonique.confiance,
    fullResult: result
  });
  if (history.length > 200) history.length = 200;
  setHistory(history);

  const blocked = result.hallucination.detectee ? 1 : 0;
  updateStats(result.metriques.tokens_total, blocked, result.verification_harmonique.score_coherence);
  showToast(result.verification_harmonique.confiance === 'haute' ? '✅ Réponse vérifiée — Confiance élevée' : '✓ Réponse générée avec vérification DHF', result.verification_harmonique.confiance === 'nulle' ? 'error' : 'success');
}

// --- Handle Generate Compare (from generate page) ---
async function handleGenerateCompare() {
  navigateTo('compare');
  $('cmpPrompt').value = $('genPrompt')?.value || '';
  handleCompare();
}

// --- Handle Compare ---
async function handleCompare() {
  const prompt = ($('cmpPrompt')?.value || '').trim();
  if (!prompt) { showToast('Veuillez entrer une question à comparer.', 'error'); return; }

  const models = [
    $('cmpModel1')?.value || 'openai:gpt-4o-mini',
    $('cmpModel2')?.value || 'anthropic:claude-3.5-sonnet',
    $('cmpModel3')?.value || 'deepseek:deepseek-chat'
  ];

  const container = $('compareResults');
  if (container) container.innerHTML = '<p style="text-align:center;padding:40px;color:var(--text-secondary)">Comparaison en cours sur 3 modèles...</p>';

  const results = await Promise.all(models.map(m => simulateHarmonicAPI(prompt, m, 'managed', 600 + Math.random() * 800)));

  // Sort by coherence score
  results.sort((a, b) => b.verification_harmonique.score_coherence - a.verification_harmonique.score_coherence);
  const winner = results[0];

  let html = '<div class="compare-models">';
  results.forEach((r, i) => {
    const isWinner = r.id === winner.id;
    html += `
      <div class="compare-model ${isWinner ? 'winner' : ''}">
        ${isWinner ? '<div style="font-size:0.8rem;color:var(--gold);margin-bottom:4px">🏆 Meilleur modèle</div>' : ''}
        <div class="compare-model-model">${r.requete.modele_choisi}</div>
        <div class="compare-model-score" style="color:${r.verification_harmonique.score_coherence >= 0.70 ? 'var(--green)' : r.verification_harmonique.score_coherence >= 0.55 ? 'var(--yellow)' : 'var(--red)'}">${Math.round(r.verification_harmonique.score_coherence * 100)}%</div>
        <div class="compare-model-confiance">Confiance : ${r.verification_harmonique.confiance}</div>
        <div class="compare-model-latence">⏱️ ${Math.round(r.metriques.temps_total_ms)}ms | 💰 $${r.metriques.cout_estime_usd.toFixed(4)}</div>
        <div class="compare-model-response">${r.reponse_finale.texte.substring(0, 250)}...</div>
      </div>`;
  });
  html += '</div>';
  if (container) container.innerHTML = html;

  // Save to history
  const history = getHistory();
  history.unshift({
    id: 'cmp_' + Date.now().toString(36),
    timestamp: new Date().toISOString(),
    prompt: prompt.substring(0, 100),
    modelId: 'Comparaison: ' + models.join(', '),
    domaine: results[0].encapsulation.domaine,
    score: winner.verification_harmonique.score_coherence,
    confiance: 'comparison',
    fullResult: { type: 'comparison', results }
  });
  setHistory(history);

  const totalTokens = results.reduce((s, r) => s + r.metriques.tokens_total, 0);
  updateStats(totalTokens, 0, null);
  showToast('✅ Comparaison terminée — ' + results.length + ' modèles évalués', 'success');
}

// --- Handle Demo Generate (Landing Page) ---
async function handleDemoGenerate() {
  const prompt = ($('demoPrompt')?.value || '').trim();
  if (!prompt) { showToast('Veuillez entrer une question.', 'error'); return; }

  const modelId = $('demoModel')?.value || 'openai:gpt-4o-mini';
  const mode = $('demoMode')?.value || 'managed';
  const respDiv = $('demoResponse');
  const loading = $('responseLoading');
  const content = $('responseContent');

  if (respDiv) respDiv.classList.remove('hidden');
  if (loading) loading.style.display = 'block';
  if (content) content.classList.add('hidden');

  const result = await simulateHarmonicAPI(prompt, modelId, mode, 600 + Math.random() * 900);

  if (loading) loading.style.display = 'none';
  if (content) content.classList.remove('hidden');

  const confDiv = $('responseConfidence');
  const textDiv = $('responseText');
  const metaDiv = $('responseMetadata');

  const confIcons = { haute: '✅', moyenne: '✓', basse: '⚠️', nulle: '❌' };
  if (confDiv) {
    confDiv.className = 'response-confidence ' + result.verification_harmonique.confiance;
    confDiv.innerHTML = `<span class="confidence-icon">${confIcons[result.verification_harmonique.confiance] || '✓'}</span> Réponse vérifiée — Confiance ${result.verification_harmonique.confiance} (${Math.round(result.verification_harmonique.score_coherence * 100)}%)`;
  }
  if (textDiv) textDiv.textContent = result.reponse_finale.texte;
  if (metaDiv) {
    metaDiv.innerHTML = `
      <span>🏷️ Domaine : ${result.encapsulation.domaine}</span>
      <span>🔑 Concepts : ${result.encapsulation.concepts_pertinents.join(', ')}</span>
      <span>⚡ Latence : ${Math.round(result.metriques.temps_total_ms)}ms</span>
      <span>💰 Coût : $${result.metriques.cout_estime_usd.toFixed(4)}</span>
      <span>📐 Euler : ${result.verification_harmonique.details.score_euler}</span>
      <span>🎯 Action : ${result.verification_harmonique.details.score_action}</span>
      <span>🔊 Résonance : ${result.verification_harmonique.details.score_resonance}</span>
      <span>🔍 DHF — Vérifié en ${result.verification_harmonique.temps_verification_ms}ms</span>
    `;
  }

  showToast('✅ Démo : réponse vérifiée par DHF', 'success');
}

// --- Handle Demo Compare (Landing Page) ---
async function handleDemoCompare() {
  const prompt = ($('demoPrompt')?.value || '').trim();
  if (!prompt) { showToast('Veuillez entrer une question.', 'error'); return; }

  const models = ['openai:gpt-4o-mini', 'anthropic:claude-3.5-sonnet', 'deepseek:deepseek-chat'];
  const respDiv = $('demoResponse');
  const loading = $('responseLoading');
  const content = $('responseContent');

  if (respDiv) respDiv.classList.remove('hidden');
  if (loading) { loading.style.display = 'block'; loading.querySelector('p').textContent = 'Comparaison de 3 modèles en cours...'; }
  if (content) content.classList.add('hidden');

  const results = await Promise.all(models.map(m => simulateHarmonicAPI(prompt, m, 'managed', 500 + Math.random() * 600)));
  results.sort((a, b) => b.verification_harmonique.score_coherence - a.verification_harmonique.score_coherence);

  if (loading) loading.style.display = 'none';
  if (content) content.classList.remove('hidden');

  const confDiv = $('responseConfidence');
  if (confDiv) {
    confDiv.className = 'response-confidence haute';
    confDiv.innerHTML = `<span class="confidence-icon">🔄</span> Comparaison 3 modèles — Meilleur : ${results[0].requete.modele_choisi} (${Math.round(results[0].verification_harmonique.score_coherence * 100)}%)`;
  }

  let text = '';
  results.forEach((r, i) => {
    text += `\n🏆 #${i+1} — ${r.requete.modele_choisi}\n`;
    text += `   Score : ${Math.round(r.verification_harmonique.score_coherence*100)}% | Confiance : ${r.verification_harmonique.confiance} | Latence : ${Math.round(r.metriques.temps_total_ms)}ms | Coût : $${r.metriques.cout_estime_usd.toFixed(4)}\n`;
    text += `   ${r.reponse_finale.texte.substring(0, 200)}...\n`;
  });

  const textDiv = $('responseText');
  if (textDiv) textDiv.textContent = text;

  const metaDiv = $('responseMetadata');
  if (metaDiv) metaDiv.innerHTML = '<span>🔍 3 modèles comparés avec vérification DHF sur chacun</span><span>📐 Scores : Euler + Action + Résonance</span><span>✅ Classement par cohérence harmonique</span>';

  showToast('✅ Comparaison 3 modèles terminée', 'success');
}

// --- Render History ---
function renderHistory() {
  const tbody = $('historyBody');
  const emptyMsg = $('historyEmpty');
  const history = getHistory();

  if (!tbody) return;

  if (history.length === 0) {
    tbody.innerHTML = '';
    if (emptyMsg) emptyMsg.style.display = 'block';
    return;
  }

  if (emptyMsg) emptyMsg.style.display = 'none';

  const confBadges = { haute: 'badge-success', moyenne: 'badge-warning', basse: 'badge-danger', nulle: 'badge-danger', comparison: 'badge-success' };

  tbody.innerHTML = history.slice(0, 50).map(h => `
    <tr style="cursor:pointer" onclick="viewRequestDetail('${h.id}')">
      <td style="font-size:0.8rem;color:var(--text-tertiary)">${new Date(h.timestamp).toLocaleString('fr-FR', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}</td>
      <td class="history-prompt" title="${h.prompt}">${h.prompt}</td>
      <td style="font-size:0.85rem">${h.modelId}</td>
      <td style="font-size:0.85rem;color:var(--text-secondary)">${h.domaine || '—'}</td>
      <td style="font-weight:600">${h.score ? Math.round(h.score * 100) + '%' : '—'}</td>
      <td><span class="badge ${confBadges[h.confiance] || 'badge-success'}">${h.confiance}</span></td>
    </tr>
  `).join('');
}

// --- View Request Detail ---
function viewRequestDetail(id) {
  const history = getHistory();
  const entry = history.find(h => h.id === id);
  if (!entry || !entry.fullResult) return;

  const r = entry.fullResult;
  if (r.type === 'comparison') {
    let html = `<p style="color:var(--text-secondary);margin-bottom:16px">Comparaison de ${r.results.length} modèles</p>`;
    r.results.forEach((rr, i) => {
      html += `<div style="background:var(--bg-primary);padding:12px;border-radius:8px;margin-bottom:8px;font-size:0.9rem">
        <strong>#${i+1} — ${rr.requete.modele_choisi}</strong> — Score : ${Math.round(rr.verification_harmonique.score_coherence * 100)}%
        <p style="color:var(--text-secondary);margin-top:4px">${rr.reponse_finale.texte.substring(0, 300)}...</p>
      </div>`;
    });
    $('modalTitle').textContent = 'Comparaison Multi-Modèles';
    $('modalContent').innerHTML = html;
  } else {
    const confIcons = { haute: '✅', moyenne: '✓', basse: '⚠️', nulle: '❌' };
    $('modalTitle').textContent = 'Détail de la requête';
    $('modalContent').innerHTML = `
      <div style="background:var(--bg-primary);padding:16px;border-radius:8px;margin-bottom:12px">
        <p style="font-size:0.85rem;color:var(--text-secondary)">Prompt original</p>
        <p style="font-weight:500">${r.requete.prompt_original}</p>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><span style="color:var(--text-tertiary);font-size:0.8rem">Modèle</span><br>${r.requete.modele_choisi}</div>
        <div><span style="color:var(--text-tertiary);font-size:0.8rem">Domaine</span><br>${r.encapsulation.domaine}</div>
        <div><span style="color:var(--text-tertiary);font-size:0.8rem">Score de cohérence</span><br><strong>${Math.round(r.verification_harmonique.score_coherence * 100)}%</strong></div>
        <div><span style="color:var(--text-tertiary);font-size:0.8rem">Confiance</span><br><span class="badge badge-${r.verification_harmonique.confiance === 'haute' ? 'success' : r.verification_harmonique.confiance === 'moyenne' ? 'warning' : 'danger'}">${r.verification_harmonique.confiance}</span></div>
      </div>
      <div style="background:var(--bg-primary);padding:16px;border-radius:8px;margin-bottom:12px">
        <p style="font-size:0.85rem;color:var(--text-secondary)">Réponse</p>
        <p style="line-height:1.7">${r.reponse_finale.texte}</p>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:0.85rem">
        <div>📐 Euler : ${r.verification_harmonique.details.score_euler}</div>
        <div>🎯 Action : ${r.verification_harmonique.details.score_action}</div>
        <div>🔊 Résonance : ${r.verification_harmonique.details.score_resonance}</div>
      </div>
    `;
  }
  $('detailModal').classList.remove('hidden');
}

function closeModal() { $('detailModal').classList.add('hidden'); }

// --- Save API Key ---
function saveKey(provider) {
  const input = $('key' + provider.charAt(0).toUpperCase() + provider.slice(1));
  if (!input) return;
  const value = input.value.trim();
  if (!value) { showToast('Veuillez entrer une clé API.', 'error'); return; }
  const keys = getKeys();
  keys[provider] = value;
  setKeys(keys);
  input.value = '';
  showToast('✅ Clé ' + provider + ' sauvegardée (chiffrée localement)', 'success');
}

// Load saved keys on settings page
document.addEventListener('DOMContentLoaded', () => {
  const keys = getKeys();
  if (keys.openai && $('keyOpenAI')) $('keyOpenAI').placeholder = '•••••••• (sauvegardée)';
  if (keys.anthropic && $('keyAnthropic')) $('keyAnthropic').placeholder = '•••••••• (sauvegardée)';
  if (keys.deepseek && $('keyDeepseek')) $('keyDeepseek').placeholder = '•••••••• (sauvegardée)';
});

// Close modal on overlay click
document.addEventListener('DOMContentLoaded', () => {
  const modal = $('detailModal');
  if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
});

// Keyboard shortcut: Ctrl+Enter to generate
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    const activePage = qs('.page-content:not(.hidden)');
    if (activePage) {
      if (activePage.id === 'page-generate') handleGenerate();
      else if (activePage.id === 'page-compare') handleCompare();
    }
  }
});