// 🎓 EDU-KA — sync-assets (jumeau de ka-mobile-android/scripts/sync-assets.mjs)
// Copie l'app EDU-KA (www/) et génère l'écran de connexion.
import { copyFileSync, mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const WWW = join(ROOT, 'www');

mkdirSync(WWW, { recursive: true });

// 1. L'app elle-même (source unique : www/educal_index.html)
if (!existsSync(join(WWW, 'educal_index.html'))) {
  console.error('❌ www/educal_index.html absent — crée l\'app avant de synchroniser');
  process.exit(1);
}

// 2. Écran de connexion (index.html) — test /api/health puis localStorage ka_api_url
const indexHtml = `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>EDU-KA — Connexion</title>
<style>
body{margin:0;font-family:'Segoe UI',sans-serif;color:#e8e6f5;display:flex;align-items:center;justify-content:center;min-height:100vh;
background:linear-gradient(160deg,#0d0a1f,#1b1240 60%,#0d0a1f)}
.box{max-width:340px;width:90%;text-align:center}
input{width:100%;padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,.15);
background:rgba(0,0,0,.3);color:#e8e6f5;font-size:1em;box-sizing:border-box;margin:10px 0}
button{width:100%;padding:13px;border:none;border-radius:12px;background:linear-gradient(135deg,#8b5cf6,#6366f1);
color:#fff;font-size:1em;font-weight:600;cursor:pointer}
p{font-size:.85em;color:#a5a0c8;min-height:1.2em}
</style>
</head>
<body>
<div class="box">
  <div style="font-size:3em">🌊🎓</div>
  <h1>EDU-KA</h1>
  <p>Adresse du serveur KA (harmonique) :</p>
  <input id="url" placeholder="http://192.168.1.10:8765">
  <button id="go">🌐 Se connecter</button>
  <p id="msg"></p>
</div>
<script>
const saved = localStorage.getItem('ka_api_url');
if (saved) document.getElementById('url').value = saved;
document.getElementById('go').onclick = async () => {
  const u = document.getElementById('url').value.trim();
  const m = document.getElementById('msg');
  if (!u) return;
  m.textContent = 'Test de connexion…';
  try {
    const r = await fetch(u + '/api/health', { timeout: 4000 });
    if (!r.ok) throw new Error();
    localStorage.setItem('ka_api_url', u.replace(/\\/$/, ''));
    localStorage.setItem('ka_user_id', 'eleve_' + Math.random().toString(36).slice(2, 8));
    location.href = 'educal_index.html';
  } catch (e) { m.textContent = '❌ Serveur injoignable'; }
};
</script>
</body>
</html>`;
writeFileSync(join(WWW, 'index.html'), indexHtml, 'utf-8');

// 3. Manifest PWA
writeFileSync(join(WWW, 'manifest.json'), JSON.stringify({
  name: 'EDU-KA', short_name: 'EDU-KA', start_url: 'educal_index.html', display: 'standalone',
  background_color: '#0d0a1f', theme_color: '#1b1240',
  icons: [{ src: 'icons/icon.png', sizes: '192x192', type: 'image/png' }],
}, null, 2));

console.log('✅ EDU-KA www/ synchronisé : index.html (connexion) + educal_index.html (app)');
