# -*- coding: utf-8 -*-
"""Applique proprement le design compress.html au ka_index.html servi.
Restaurer l'original AVANT d'exécuter ce script.
"""
import io
import re

PATH = 'E:/SAAS - Copie/ka-mobile-android/www/ka_index.html'

with io.open(PATH, 'r', encoding='utf-8') as f:
    c = f.read()

# ══════════════════════════════════════════════════════════════
# PATCH 1 : HTML s-demo (remplacer l'ancienne démo « LE CHOC »)
# ══════════════════════════════════════════════════════════════
demo_html_start = c.find('<!-- ═══ DÉMO « LE CHOC »')
onboard_start = c.find('<!-- ═══ ONBOARDING ═══')
assert demo_html_start != -1 and onboard_start != -1, 'Sections demo HTML introuvables'

new_demo_html = '''  <!-- ═══ PREMIER LANCEMENT — KA accueille (design compress.html) ═══ -->
  <div class="sc" id="s-demo">
    <div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:30px 20px;text-align:center">
      <img id="ka-disc" src="/brand/ka.svg" alt="KA"
           style="width:120px;height:120px;margin-bottom:24px;filter:drop-shadow(0 14px 50px rgba(180,190,205,.35));animation:discSpin 24s linear infinite,discFloat 5s ease-in-out infinite">
      <div style="font-size:clamp(30px,8vw,38px);font-weight:200;letter-spacing:.12em;color:var(--t2)">
        <span style="font-family:Georgia,serif;font-weight:700;background:linear-gradient(180deg,#eceff3,#9ea5af);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 20px rgba(180,190,205,.2))">KA</span>
      </div>
      <div style="font-size:12px;font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:var(--t3);margin-bottom:18px;border:1px solid var(--b1);border-radius:999px;padding:6px 18px;background:var(--g1);display:inline-block">Compression Harmonique</div>
      <p style="color:var(--t2);font-size:14.5px;line-height:1.7;max-width:400px;margin-bottom:22px">
        <b>Bonjour</b>, je suis votre compagnon de compression harmonique.<br>
        Déposez une photo ou laissez-moi gérer votre stockage.<br>
        <b style="color:var(--life)">Zéro cloud, zéro perte.</b>
      </p>
      <div id="demo-uz" style="border:1.5px dashed var(--b3);border-radius:16px;padding:22px 18px;text-align:center;cursor:pointer;transition:all .3s;max-width:320px;width:100%;background:linear-gradient(135deg,rgba(139,131,255,.03),transparent)"
           onclick="document.getElementById('demo-file').click()">
        <span style="font-size:28px;margin-bottom:6px;display:block;filter:drop-shadow(0 4px 14px rgba(139,131,255,.3))">📤</span>
        <div style="font-size:14px;font-weight:700">Déposer une photo</div>
        <div style="font-size:11px;color:var(--t3);margin-top:4px">JPEG, PNG, WebP — max 50 Mo</div>
        <input type="file" id="demo-file" accept="image/*" style="display:none">
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:14px">
        <button class="btn btn--life" onclick="demoExpress()" style="padding:10px 20px;font-size:13px;font-weight:600;cursor:pointer;background:linear-gradient(135deg,var(--life),#1fae7c);color:#04261a;border:none;border-radius:999px">🚀 Voir un exemple</button>
        <button class="btn btn--soul" onclick="demoStoragePropose()" style="padding:10px 20px;font-size:13px;font-weight:600;cursor:pointer;background:var(--soul-d);border:.5px solid var(--soul-g);color:var(--soul-l);border-radius:999px">📱 Libérer de l'espace</button>
      </div>
      <div id="demo-progress" style="display:none;width:100%;max-width:320px;margin-top:12px">
        <div style="height:4px;background:var(--g1);border-radius:2px;overflow:hidden">
          <div id="demo-progress-bar" style="height:100%;width:0%;background:linear-gradient(90deg,var(--soul),var(--life));border-radius:2px;transition:width .3s"></div>
        </div>
        <div id="demo-progress-text" style="font-size:11px;color:var(--t4);margin-top:6px">Compression en cours…</div>
      </div>
      <div id="demo-result-compress" style="display:none;margin-top:14px;font-size:13px;color:var(--life);text-align:center"></div>
      <button class="btn btn--ghost" onclick="demoDismiss()" id="demo-skip-btn" style="margin-top:16px;font-size:12px;color:var(--t4);background:none;border:none;cursor:pointer">Passer pour l'instant</button>
    </div>
  </div>

  <style>
    @keyframes discSpin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
    @keyframes discFloat{0%,100%{margin-bottom:24px}50%{margin-bottom:32px}}
  </style>

'''
c = c[:demo_html_start] + new_demo_html + c[onboard_start:]
print('OK PATCH 1 (HTML s-demo)')

# ══════════════════════════════════════════════════════════════
# PATCH 2 : fonctions demo JS (remplacer « LE CHOC » par le nouveau flux)
# ══════════════════════════════════════════════════════════════
js_start = c.find('// ═══ DÉMO « LE CHOC »')
assert js_start != -1, 'Section demo JS introuvable'

# Fin : la fin de la fonction demoDone() — on cherche sa ligne puis l'accolade fermante
dd = c.find('function demoDone()')
assert dd != -1, 'demoDone introuvable'
brace = c.find('}', c.find('\n', dd))
js_end = brace + 1
while js_end < len(c) and c[js_end] in ' \n':
    js_end += 1

new_js = r'''// ═══ PREMIER LANCEMENT — KA accueille, compression conversationnelle ═══
function demoDismiss() {
  try { localStorage.setItem('ka_demo_done', '1'); } catch(e) {}
  if (kaNeedsOnboard()) {
    go('s-onboard');
    onboardRender();
  } else {
    go('s-home');
  }
}

// ── Démo express : charger une photo et la compresser ──
function demoExpress() {
  var btn = document.getElementById('demo-skip-btn'); if (btn) btn.style.display = 'none';
  showDemoProgress('Chargement de la photo de démonstration…');
  fetch('/img/demo_landscape.jpg')
    .then(function(r) { return r.arrayBuffer(); })
    .then(function(b) {
      var u = new Uint8Array(b), s = '';
      for (var i = 0; i < u.length; i++) s += String.fromCharCode(u[i]);
      var b64 = btoa(s);
      showDemoProgress('Analyse harmonique en cours…');
      return compressDemoB64(b64, 'demo_landscape.jpg', b.byteLength);
    })
    .catch(function(e) { demoProgressText('❌ ' + e.message); });
}

// ── Upload : compression via le sélecteur de fichier ──
(function() {
  var df = document.getElementById('demo-file');
  if (df) df.addEventListener('change', function() {
    if (df.files.length) {
      var file = df.files[0];
      var r = new FileReader();
      r.onload = function(e) {
        demoDismiss();
        setTimeout(function() {
          var b64 = e.target.result.split(',')[1];
          showDemoProgress('Analyse harmonique en cours…');
          compressDemoB64(b64, file.name, file.size);
        }, 600);
      };
      r.readAsDataURL(file);
    }
  });
})();

// ── Compression réelle via l'API ──
function compressDemoB64(b64, name, size) {
  var f = new FormData();
  f.append('file', new Blob([Uint8Array.from(atob(b64), function(c) { return c.charCodeAt(0); })], {type: 'image/jpeg'}), name || 'image.jpg');
  f.append('mode', 'select');
  f.append('min_psnr', '25');
  return fetch('/api/compress/preview', {method: 'POST', body: f})
    .then(function(r) { return r.json().then(function(d) { if (!r.ok) throw new Error(d.error || 'Erreur'); return d; }); })
    .then(function(d) {
      var sv = d.saved_percent, vr = d.ratio;
      var h = '<div style="text-align:left;background:var(--g1);border:1px solid var(--b1);border-radius:14px;padding:12px 14px;margin-top:10px">';
      h += '<div style="font-size:13px;font-weight:700;color:var(--life)">✅ Compression terminée <span style="float:right;background:var(--life-d);border:1px solid var(--life-g);border-radius:999px;padding:2px 10px;font-size:11px">×' + vr + '</span></div>';
      h += '<div style="font-size:12px;color:var(--t3);margin-top:4px">' + fmtBytes(size) + ' → <b style="color:var(--soul-l)">' + fmtBytes(d.compressed_size) + '</b> · <b style="color:var(--life)">' + sv + '%</b> économisés</div>';
      h += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;font-size:11px;color:var(--t3)"><span>🎯 PSNR <b style="color:var(--t1)">' + (d.psnr >= 99 ? '∞' : d.psnr.toFixed(1)) + ' dB</b></span><span>📦 <b style="color:var(--t1)">' + d.format + '</b></span><span>📐 <b style="color:var(--t1)">' + d.width + '×' + d.height + '</b></span></div>';
      h += '<div style="position:relative;aspect-ratio:3/2;background:#05070d;border-radius:10px;overflow:hidden;margin-top:10px"><img src="data:image/jpeg;base64,' + d.reconstructed_base64 + '" style="width:100%;height:100%;object-fit:contain" alt="Ψ"></div>';
      h += '</div>';
      h += '<div style="display:flex;gap:8px;justify-content:center;margin-top:12px;flex-wrap:wrap">';
      h += '<button onclick="demoFinish()" style="padding:10px 22px;border:none;border-radius:999px;font-size:13px;font-weight:600;cursor:pointer;background:linear-gradient(135deg,var(--life),#1fae7c);color:#04261a">🚀 Continuer</button>';
      h += '<button onclick="demoStoragePropose()" style="padding:10px 22px;border:.5px solid var(--soul-g);border-radius:999px;font-size:13px;font-weight:600;cursor:pointer;background:var(--soul-d);color:var(--soul-l)">📱 Et mes fichiers ?</button>';
      h += '</div>';
      document.getElementById('demo-result-compress').style.display = 'block';
      document.getElementById('demo-result-compress').innerHTML = h;
      document.getElementById('demo-progress').style.display = 'none';
      return d;
    })
    .catch(function(e) { demoProgressText('❌ ' + e.message); });
}

function demoFinish() {
  try { localStorage.setItem('ka_demo_done', '1'); } catch(e) {}
  if (kaNeedsOnboard()) { go('s-onboard'); onboardRender(); }
  else { go('s-home'); }
}

// ── Proposer l'analyse du stockage ──
function demoStoragePropose() {
  demoDismiss();
  setTimeout(function() {
    if (window.proposeStorageScan) proposeStorageScan();
    else go('s-storage');
  }, 600);
}

// ── Helpers ──
function showDemoProgress(txt) {
  var p = document.getElementById('demo-progress'); if (p) p.style.display = 'block';
  var b = document.getElementById('demo-progress-bar'); if (b) b.style.width = '40%';
  demoProgressText(txt);
}
function demoProgressText(txt) {
  var t = document.getElementById('demo-progress-text'); if (t) t.textContent = txt;
}
function fmtBytes(n) {
  if (n < 1024) return n + ' o';
  if (n < 1048576) return (n / 1024).toFixed(1) + ' Ko';
  return (n / 1048576).toFixed(1) + ' Mo';
}

'''
c = c[:js_start] + new_js + c[js_end:]
print('OK PATCH 2 (fonctions demo JS)')

# ══════════════════════════════════════════════════════════════
# PATCH 3 : storage conversationnel — AVANT la fin du script principal
# ══════════════════════════════════════════════════════════════
main_script_end = c.find('</script>', c.find('<script>', c.find('use strict')))
assert main_script_end != -1, 'Fin du script principal introuvable'

storage_js = r'''
// ═══════════════════════════════════════════════════════════════════════
// STORAGE SAVER — Conversationnel (design compress.html)
// ═══════════════════════════════════════════════════════════════════════
function kaSay(html){
  var c=document.getElementById('msglist');
  var m=document.createElement('div');m.className='msg msg--ka';m.innerHTML=html;
  c.appendChild(m);c.scrollTop=c.scrollHeight;
  return m;
}
function kaAsk(html,btns){
  var m=kaSay(html);
  var d=document.createElement('div');
  d.style.cssText='display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:10px';
  d.innerHTML=btns;
  m.appendChild(d);
  return m;
}
function proposeStorageScan(){
  go('s-msg');
  setTimeout(function(){
    kaAsk('<b>📱 Analyser le stockage ?</b><div style="font-size:11.5px;color:var(--t3);margin-top:4px">Je peux scanner vos fichiers, les compresser et libérer de l\'espace.<br>Les originaux sont conservés <b style="color:var(--life)">7 jours</b>.</div>',
      '<button class="btn btn--life" style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:var(--life-d);color:var(--life);font-weight:600" onclick="startStorageScan()">✅ Oui, analyser</button>'
      +'<button style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:none;color:var(--t3)" onclick="skipStorage()">Non merci</button>');
  },500);
}
function startStorageScan(){
  var m=kaSay('<div style="display:flex;align-items:center;gap:8px"><span style="width:12px;height:12px;border:2px solid var(--b2);border-top-color:var(--soul-l);border-radius:50%;animation:spin .7s linear infinite"></span> Analyse du stockage...</div>');
  fetch('/api/compress/storage/scan')
    .then(function(r){return r.json().then(function(d){if(!r.ok)throw new Error(d.error||'Erreur');return d})})
    .then(function(d){
      m.remove();
      kaAsk('<b>📊 Analyse terminée</b><div style="font-size:11.5px;color:var(--t3);margin-top:4px">J\'ai trouvé <b>'+d.total_files+' fichiers</b> représentant <b>'+d.total_size_fmt+'</b>.<br>💾 Économie estimée : <b style="color:var(--life)">'+d.saved_estimate_fmt+'</b> · Ratio <b>×'+d.estimated_ratio+'</b></div>',
        '<button class="btn btn--life" style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:var(--life-d);color:var(--life);font-weight:600" onclick="activateStorage()">🚀 Lancer la compression</button>'
        +'<button style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:var(--g1);color:var(--t2)" onclick="viewStorageStatus()">📈 Statistiques</button>'
        +'<button style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:none;color:var(--t3)" onclick="skipStorage()">Plus tard</button>');
    })
    .catch(function(e){m.remove();kaSay('<span style="color:var(--rose)">❌ '+e.message+'</span>')});
}
function activateStorage(){
  var m=kaSay('<div style="display:flex;align-items:center;gap:8px"><span style="width:12px;height:12px;border:2px solid var(--b2);border-top-color:var(--soul-l);border-radius:50%;animation:spin .7s linear infinite"></span> Activation du compresseur de fond...</div>');
  fetch('/api/compress/storage/activate',{method:'POST'})
    .then(function(r){return r.json()})
    .then(function(d){
      m.remove();
      kaSay('<b>✅ Compression activée</b><div style="font-size:11.5px;color:var(--t3);margin-top:4px">Le <b>GhostCompressor</b> tourne en arrière-plan. Chaque fichier est compressé un par un.</div>');
      setTimeout(function(){viewStorageStatus()},800);
    })
    .catch(function(e){m.remove();kaSay('<span style="color:var(--rose)">❌ '+e.message+'</span>')});
}
function viewStorageStatus(){
  fetch('/api/compress/storage/status')
    .then(function(r){return r.json()})
    .then(function(d){
      if(!d.success)throw new Error(d.error||'Erreur');
      var pct=d.total_original_bytes?Math.round(100*d.total_saved_bytes/d.total_original_bytes):0;
      var h='<b>📈 GhostCompressor — état</b>'
        +'<div style="background:rgba(61,219,160,.06);border:1px solid rgba(61,219,160,.18);border-radius:12px;padding:10px 12px;margin-top:6px">'
        +'<div style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--t2);padding:3px 0"><span>📂 Fichiers compressés</span><b style="color:var(--t1)">'+d.files_count+'</b></div>'
        +'<div style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--t2);padding:3px 0"><span>💾 Avant</span><b style="color:var(--t1)">'+d.total_original_fmt+'</b></div>'
        +'<div style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--t2);padding:3px 0"><span>📦 Après</span><b style="color:var(--soul-l)">'+d.total_compressed_fmt+'</b></div>'
        +'<div style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--t2);padding:3px 0"><span>✅ Économisé</span><b style="color:var(--life)">'+d.total_saved_fmt+'</b></div>'
        +(d.free_space_gb?'<div style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--t2);padding:3px 0"><span>💽 Espace libre</span><b style="color:var(--t1)">'+d.free_space_gb+' Go</b></div>':'')
        +'<div style="height:4px;border-radius:2px;background:var(--g2);overflow:hidden;margin-top:8px"><i style="display:block;height:100%;border-radius:2px;background:linear-gradient(90deg,var(--life),var(--soul));width:'+Math.min(100,pct)+'%;transition:width .6s"></i></div>'
        +'</div>';
      if(d.projection&&d.projection.photos_can_fit>0)h+='<div style="font-size:11px;color:var(--t3);margin-top:5px">🔮 Vous pouvez encore stocker environ <b style="color:var(--life)">+'+d.projection.photos_can_fit+' photos</b>.</div>';
      kaAsk(h,
        '<button class="btn btn--life" style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:var(--life-d);color:var(--life);font-weight:600" onclick="activateStorage()">🚀 Activer</button>'
        +'<button style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:var(--g1);color:var(--t2)" onclick="viewStorageStatus()">🔄 Rafraîchir</button>'
        +'<button style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:var(--g1);color:var(--rose)" onclick="deactivateStorage()">⏹ Arrêter</button>'
        +'<button style="padding:8px 16px;font-size:12px;border-radius:999px;border:none;cursor:pointer;background:none;color:var(--t3)" onclick="skipStorage()">Fermer</button>');
    })
    .catch(function(e){kaSay('<span style="color:var(--rose)">❌ '+e.message+'</span>')});
}
function deactivateStorage(){
  var ms=document.querySelectorAll('.msg--ka');if(ms.length)ms[ms.length-1].remove();
  fetch('/api/compress/storage/deactivate',{method:'POST'}).catch(function(){});
  kaSay('⏹ GhostCompressor arrêté.');
}
function skipStorage(){
  var ms=document.querySelectorAll('.msg--ka');if(ms.length)ms[ms.length-1].remove();
  kaSay('👍 D\'accord. Je reste disponible.');
}
'''
c = c[:main_script_end] + storage_js + '\n' + c[main_script_end:]
print('OK PATCH 3 (storage conversationnel)')

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(c)

# Vérifications finales
import re
checks = {
    'script ouverts': len(re.findall(r'<script[ >]', c)),
    'script fermés': len(re.findall(r'</script>', c)),
    'body ouverts': len(re.findall(r'<body>', c)),
    'body fermés': len(re.findall(r'</body>', c)),
    'html ouverts': len(re.findall(r'<html[ >]', c)),
    'html fermés': len(re.findall(r'</html>', c)),
}
for k, v in checks.items():
    print(f'  {k}: {v}')
