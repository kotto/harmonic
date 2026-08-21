#!/usr/bin/env node
/* ══════════════════════════════════════════════════════════════════════════
   KA MOBILE ANDROID — Synchronisation des assets web → www/
   ══════════════════════════════════════════════════════════════════════════
   Embarque l'app web KA Phone (engine/ka_index.html) dans www/ pour Capacitor.
   - ka_index.html est copié tel quel + 4 patchs ciblés (regex stables) :
     1. API_URL → priorité à localStorage['ka_api_url'] (serveur configuré
        depuis l'écran de connexion index.html)
     2. Service Worker → désactivé en WebView (window.Capacitor)
     3. Pont natif ka_native.js injecté après <body> (STT Android)
     4. Bouton discret « ⚙ » (ka_server_switch.js) pour reconfigurer le serveur
   - Génère index.html : écran de connexion au 1er lancement (adresse du
     serveur KA mémorisée en localStorage, test /api/health, redirect).

   Usage : node scripts/sync-assets.mjs
   ══════════════════════════════════════════════════════════════════════════ */
import { copyFileSync, mkdirSync, readFileSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');   // ka-mobile-android/
const SRC  = join(ROOT, '..');                                       // engine/
const WWW  = join(ROOT, 'www');

// ── Écran de connexion : adresse du serveur KA → localStorage → KA ────────
const CONNECT_HTML = `<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover">
<title>KA — Connexion</title>
<style>
:root{--bg:#0a0a1a;--panel:rgba(20,20,40,.85);--border:rgba(212,168,83,.25);--gold:#d4a853;--text:#eae1d7;--muted:#8a8395;--ok:#3ddba0;--err:#ff6b6b}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'SF Pro Display',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;align-items:center;justify-content:center}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse at 50% 0%,rgba(212,168,83,.07) 0%,transparent 60%);pointer-events:none}
.card{position:relative;width:min(92vw,420px);background:var(--panel);border:1px solid var(--border);border-radius:20px;padding:32px 26px;backdrop-filter:blur(16px)}
.logo{width:72px;height:72px;margin:0 auto 14px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:34px;border:2px solid var(--border);background:radial-gradient(circle at 30% 25%,#1b1b3a,#0d0d20)}
h1{text-align:center;font-size:1.45em;color:var(--gold);letter-spacing:.02em}
.sub{text-align:center;color:var(--muted);font-size:12.5px;margin:6px 0 22px;line-height:1.5}
label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
input{width:100%;margin-top:8px;background:#0d0d22;border:1px solid var(--border);color:var(--text);border-radius:12px;padding:13px 14px;font-size:15px;outline:none}
input:focus{border-color:var(--gold)}
.hint{font-size:11px;color:var(--muted);margin-top:7px;line-height:1.45}
button{width:100%;margin-top:16px;background:linear-gradient(135deg,#d4a853,#7b5804);color:#0d0d0d;border:none;border-radius:12px;padding:13px;font-size:15px;font-weight:700;cursor:pointer}
button:disabled{opacity:.55}
#msg{text-align:center;font-size:12.5px;margin-top:12px;min-height:18px}
#msg.ok{color:var(--ok)} #msg.err{color:var(--err)}
a.sk{display:block;text-align:center;margin-top:12px;color:var(--muted);font-size:11.5px;text-decoration:none}
.foot{text-align:center;margin-top:20px;font-size:10px;color:var(--muted)}
</style></head><body>
<div class="card">
  <div class="logo">⚛</div>
  <h1>KA Mobile</h1>
  <p class="sub">Compagnon harmonique · 100 % local<br>Connectez-vous au serveur KA</p>
  <label for="srv">Adresse du serveur KA</label>
  <input id="srv" type="text" inputmode="url" autocomplete="off" placeholder="ex. 192.168.1.42:8765">
  <p class="hint">💡 Sur l'émulateur : <b>10.0.2.2:8765</b> (le PC). Sur un téléphone : l'adresse IP du
  PC qui fait tourner <i>ka_server.py</i> — même réseau WiFi. Le port <b>:8765</b> est ajouté automatiquement.</p>
  <button id="go">Connecter</button>
  <div id="msg"></div>
  <a class="sk" href="#" id="sk">Connecter directement sans vérifier</a>
  <div class="foot">KA · Théorie Harmonique Universelle</div>
</div>
<script>
(function(){
  var KEY='ka_api_url';
  function normalize(raw){
    raw=(raw||'').trim().replace(/\\/+$/,'');
    if(!raw)return null;
    if(!/^https?:\\/\\//i.test(raw))raw='http://'+raw;
    var host=raw.replace(/^https?:\\/\\//i,'').split('/')[0];
    if(!/:\\d+$/.test(host))raw=raw+':8765';
    return raw;
  }
  var inp=document.getElementById('srv'),msg=document.getElementById('msg'),btn=document.getElementById('go');
  var saved=null;try{saved=localStorage.getItem(KEY)||null;}catch(e){}
  inp.value=saved||'10.0.2.2:8765';
  inp.focus(); if(saved)inp.select();
  function setMsg(t,cls){msg.textContent=t||'';msg.className=cls||'';}
  function connect(verify){
    var url=normalize(inp.value);
    if(!url){setMsg('Adresse invalide','err');return;}
    btn.disabled=true;setMsg('Test de connexion…','');
    var done=function(ok){
      try{localStorage.setItem(KEY,url);}catch(e){}
      if(ok){setMsg('✅ Connecté — lancement de KA…','ok');}
      location.href='ka_index.html';
    };
    if(!verify){done(true);return;}
    fetch(url+'/api/health',{signal:AbortSignal.timeout(4000)})
      .then(function(r){done(r.ok);})
      .catch(function(){done(true);});   // même en échec de test → KA gère son propre mode dégradé
  }
  btn.addEventListener('click',function(){connect(true);});
  document.getElementById('sk').addEventListener('click',function(e){e.preventDefault();connect(false);});
  inp.addEventListener('keydown',function(e){if(e.key==='Enter')connect(true);});
})();
</script>
</body></html>
`;

let copied = 0, missing = 0, bytes = 0;
function ensureDir(p) { mkdirSync(p, { recursive: true }); }
function track(s, d) { copied++; bytes += statSync(s).size; }

console.log('═══ KA Mobile — sync assets → www/ ═══');
ensureDir(WWW);

// ── 1. ka_index.html patché ────────────────────────────────────────────────
const SRC_HTML = join(SRC, 'ka_index.html');
const DST_HTML = join(WWW, 'ka_index.html');
if (!existsSync(SRC_HTML)) { console.warn('  ⚠ ABSENT : ka_index.html'); missing++; }
else {
  let html = readFileSync(SRC_HTML, 'utf8');
  const n0 = html.length;

  // (1) API_URL : override localStorage (défini par l'écran de connexion)
  const apiFrom = /var API_URL = isLocal \? `http:\/\/\$\{apiHost\}:8765` : 'https:\/\/ka-api\.onrender\.com';/;
  if (apiFrom.test(html)) {
    html = html.replace(apiFrom,
      'var API_URL = (function(){try{var u=localStorage.getItem(\'ka_api_url\');if(u)return u;}catch(e){}'
      + 'return isLocal?`http://${apiHost}:8765`:\'https://ka-api.onrender.com\';})(); // [ka-android] override localStorage');
  } else { console.warn('  ⚠ PATCH API_URL introuvable — ligne modifiée dans ka_index.html ?'); missing++; }

  // (2) Service Worker désactivé en WebView (sw.js absent du bundle)
  html = html.replace(/if \('serviceWorker' in navigator\) \{/,
    'if (\'serviceWorker\' in navigator && !window.Capacitor) { // [ka-android] SW off en WebView');

  // (3) Pont natif avant le premier script inline
  html = html.replace(/<body[^>]*>/,
    (m) => m + '\n<script src="ka_native.js"></script>');

  // (4) Bouton discret de reconfiguration du serveur
  html = html.replace(/<\/body>/,
    '<script src="ka_server_switch.js"></script>\n</body>');

  writeFileSync(DST_HTML, html, 'utf8');
  copied++; bytes += Buffer.byteLength(html);
  console.log('  ✓ ka_index.html patché (' + (html.length - n0) + ' octets de patchs)');
}

// ── 2. Scripts du wrapper ───────────────────────────────────────────────────
for (const f of ['ka_native.js', 'ka_server_switch.js']) {
  const s = join(ROOT, 'scripts', f), d = join(WWW, f);
  if (!existsSync(s)) { console.warn('  ⚠ ABSENT : scripts/' + f); missing++; continue; }
  copyFileSync(s, d); track(s, d);
  console.log('  ✓ ' + f);
}

// ── 3. Manifest PWA + icônes (référencés par ka_index.html) ────────────────
const MISC = ['manifest.json', 'icons/ka-192.svg', 'icons/ka-512.svg'];
for (const rel of MISC) {
  const s = join(SRC, rel), d = join(WWW, rel);
  if (!existsSync(s)) { console.warn('  ⚠ ABSENT : ' + rel); missing++; continue; }
  ensureDir(dirname(d));
  copyFileSync(s, d); track(s, d);
}

// ── 4. index.html — écran de connexion (point d'entrée Capacitor) ─────────
writeFileSync(join(WWW, 'index.html'), CONNECT_HTML, 'utf8');
copied++; bytes += Buffer.byteLength(CONNECT_HTML);
console.log('  ✓ index.html (écran de connexion)');

console.log(`═══ ${copied} fichiers copiés (${(bytes / 1024).toFixed(0)} Ko) — ${missing} manquant(s) ═══`);
process.exit(missing ? 1 : 0);
