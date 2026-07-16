/**
 * KA Phone — Core Application
 * ============================
 * Initialisation, navigation, API.
 */

/* global API_URL, RP, CALL_SCREENS, NAV_MAP, go */

// ── Auto-détection API ──
const h = location.hostname;
const isLocal = h==='localhost'||h==='127.0.0.1'||h.startsWith('192.168.')||h.startsWith('10.')||h.startsWith('172.16.');
const API_URL = isLocal ? 'http://'+h+':8765' : 'https://ka-api.onrender.com';
let API_ONLINE = false;

const RP = ['Je suis KA, votre assistant personnel intelligent. Posez-moi une question !',
  'Que voulez-vous savoir ? Je suis là pour vous aider.',
  'Bonjour ! Je suis KA. Que puis-je faire pour vous ?'];

// ── Vérification connexion ──
(async function checkAPI() {
  try {
    const r = await fetch(API_URL + '/api/health', {signal: AbortSignal.timeout(5000)});
    if (r.ok) { API_ONLINE = true; console.log('✅ KA connecté'); }
  } catch(e) { 
    API_ONLINE = false;
    console.log('⚠️ Serveur inaccessible — mode dégradé');
    const sb = document.querySelector('.sb__t');
    if (sb) sb.textContent = 'KA · ⚠️';
  }
})();

// ── API Chat ──
async function askKA(message) {
  if (!API_ONLINE) return RP[Math.floor(Math.random() * RP.length)];
  try {
    let uid = localStorage.getItem('ka_user_id');
    if (!uid) { uid = 'user_' + Date.now().toString(36) + Math.random().toString(36).slice(2,6); localStorage.setItem('ka_user_id', uid); }
    const res = await fetch(API_URL + '/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: message, user_id: uid})
    });
    if (!res.ok) throw new Error('API error');
    const data = await res.json();
    if (data.specialization) {
      setTimeout(function() {
        const el = document.getElementById('spec-info');
        if (el && data.specialization.success) {
          el.innerHTML = '🎯 '+data.specialization.domain+' · '+data.specialization.triplets_count.toLocaleString()+' faits';
          el.style.display = 'block';
        }
      }, 500);
    }
    return data.response || RP[Math.floor(Math.random() * RP.length)];
  } catch(e) { API_ONLINE = false; return RP[Math.floor(Math.random() * RP.length)]; }
}

// ── Navigation ──
const CALL_SCREENS = new Set(['s-call']);
const NAV_MAP = {'s-home':'nb-h','s-msg':'nb-m','s-mem':'nb-mm'};
let cur = 's-home';

function go(id) {
  if (id === cur) return;
  document.querySelectorAll('.sc').forEach(function(s) { s.classList.remove('sc--on','sc--in'); });
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.add('sc--on','sc--in');
  cur = id;
  const nb = document.getElementById('nav-bar');
  nb.style.display = CALL_SCREENS.has(id) ? 'none' : 'flex';
  Object.entries(NAV_MAP).forEach(function(e) {
    const btn = document.getElementById(e[1]);
    if (btn) btn.classList.toggle('nb--on', e[0] === id);
  });
  if (!Object.values(NAV_MAP).includes('nb-'+id)) document.getElementById('nb-more')?.classList.remove('nb--on');
  if (id === 's-call') { if (typeof startCall === 'function') startCall(); }
  else { if (typeof stopCall === 'function') stopCall(); }
  if (id === 's-cap') { if (typeof buildCapWave === 'function') buildCapWave(); }
  if (typeof closeMore === 'function') closeMore();
  // Hook dynamique
  if (typeof SCREEN_HOOKS !== 'undefined' && SCREEN_HOOKS[id]) {
    setTimeout(SCREEN_HOOKS[id], 100);
  }
}

function showMore() {
  document.getElementById('more-panel').style.display = 'block';
  document.getElementById('nb-more').classList.add('nb--on');
}

function closeMore() {
  const p = document.getElementById('more-panel');
  if (p) p.style.display = 'none';
  document.getElementById('nb-more')?.classList.remove('nb--on');
}

function tick() {
  const n = new Date();
  document.getElementById('clk').textContent = String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0');
}
tick(); setInterval(tick, 10000);
