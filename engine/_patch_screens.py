"""Patch ka_care.html to add splash screen, bottom nav, and screen system."""
import re

with open('ka_care.html', 'r', encoding='utf-8') as f:
    old = f.read()

# ── 1. CSS ──
nav_css = """\
.screen{display:none}.screen.active{display:block}
.bottom-nav{position:fixed;bottom:0;left:0;width:100%;display:flex;justify-content:space-around;align-items:center;padding:10px 16px 14px;background:rgba(26,26,26,.95);backdrop-filter:blur(20px);border-top:1px solid rgba(78,70,55,.3);box-shadow:0 -8px 30px rgba(0,0,0,.5);z-index:50;border-radius:24px 24px 0 0}
.nav-item{display:flex;flex-direction:column;align-items:center;cursor:pointer;color:rgba(210,197,178,.4);transition:all .2s;padding:4px 12px}
.nav-item.active{color:#f2c36b;background:rgba(212,168,83,.08);border-radius:12px;padding:6px 12px}
.nav-item .nav-icon{font-size:22px;margin-bottom:2px}
.nav-item .nav-label{font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase}
.vital-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.vital-card{background:#111;border-radius:12px;padding:16px;border:1px solid #2a2a2a;text-align:center}.vital-card .value{font-size:1.6em;font-weight:700;color:#d4a853}.vital-card .label{font-size:.75em;color:#9b8f7e;margin-top:4px}
.history-item{padding:14px;border-radius:12px;margin-bottom:8px;border-left:4px solid #d4a853;background:#111}.history-item.urgent{border-left-color:#e74c3c}.history-item .date{font-size:.7em;color:#9b8f7e}
"""
old = old.replace('</style>', nav_css + '</style>')

# ── 2. Splash screen + screen wrappers ──
body_start = old.find('<body>')
body_start = old.find('>', body_start) + 1

splash = """<div class="screen active" id="screen-splash">
<div style="text-align:center;padding:80px 20px 40px">
<img src="logo2.jpg" style="width:80px;height:80px;border-radius:50%;object-fit:cover;box-shadow:0 8px 32px rgba(212,168,83,0.3);margin-bottom:20px">
<h1 style="font-size:2em;color:#d4a853;font-weight:800;margin-bottom:4px">KA CARE</h1>
<p style="color:#9b8f7e;font-size:1.05em;margin-bottom:24px">LA SANTE PAR LA RESONANCE</p>
<button class="btn btn-primary" onclick="showScreen('resonance')" style="margin-bottom:12px">COMMENCER LE DIAGNOSTIC</button>
<button class="btn btn-secondary" onclick="showScreen('history')" style="width:100%;margin-top:8px">CONSULTER LES ARCHIVES</button>
<p style="margin-top:24px;font-size:.7em;color:#8b7355;letter-spacing:.05em">v2.0 · 20 pathologies · Zero hallucination · Hors-ligne</p>
</div></div>
<div class="screen" id="screen-resonance">
"""
old = old[:body_start] + splash + old[body_start:]

# Close resonance screen before footer
footer_pos = old.find('<footer>')
if footer_pos > 0:
    old = old[:footer_pos] + '</div>\n' + old[footer_pos:]

# ── 3. Bottom nav ──
nav_html = """<nav class="bottom-nav" id="bottomNav" style="display:none">
<div class="nav-item active" data-screen="resonance" onclick="showScreen('resonance')"><span class="nav-icon">〰️</span><span class="nav-label">Resonance</span></div>
<div class="nav-item" data-screen="history" onclick="showScreen('history')"><span class="nav-icon">📋</span><span class="nav-label">History</span></div>
<div class="nav-item" data-screen="vitals" onclick="showScreen('vitals')"><span class="nav-icon">💓</span><span class="nav-label">Vitals</span></div>
<div class="nav-item" data-screen="patients" onclick="showScreen('patients')"><span class="nav-icon">👥</span><span class="nav-label">Profile</span></div>
</nav>
"""
old = old.replace('</body>', nav_html + '</body>')

# ── 4. Hidden screen divs ──
body_end = old.rfind('</body>')
hidden = """<div class="screen" id="screen-history"><div id="historyList" style="padding:16px"></div></div>
<div class="screen" id="screen-vitals"><div id="vitalsContent" style="padding:16px"></div></div>
<div class="screen" id="screen-patients"><div id="patientsList" style="padding:16px"></div></div>
"""
old = old[:body_end] + hidden + old[body_end:]

# ── 5. JS functions ──
screen_js = """
function showScreen(name){
document.querySelectorAll('.screen').forEach(function(s){s.classList.remove('active')});
var el=document.getElementById('screen-'+name);
if(el)el.classList.add('active');
document.getElementById('bottomNav').style.display=(name==='splash')?'none':'flex';
document.querySelectorAll('.nav-item').forEach(function(n){n.classList.toggle('active',n.dataset.screen===name)});
if(name==='history')renderHistory();if(name==='vitals')renderVitals();if(name==='patients')renderPatients();
}
function renderHistory(){
var el=document.getElementById('historyList');if(!el)return;
if(typeof diagnosticHistory==='undefined'||!diagnosticHistory.length){el.innerHTML='<div class=\"card\"><p style=\"text-align:center;color:var(--muted);margin:20px\">Aucun diagnostic pour le moment.</p></div>';return}
var h='';for(var i=0;i<Math.min(diagnosticHistory.length,20);i++){var d=diagnosticHistory[i];var dt=new Date(d.date);
h+='<div class=\"history-item'+(d.urgent?' urgent':'')+'\"><div class=\"date\">'+dt.toLocaleDateString('fr-FR',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})+'</div><strong>'+d.diagnosis+'</strong> <span style=\"color:var(--accent);font-weight:700\">'+d.score+'%</span><div style=\"font-size:.8em;color:var(--muted);margin-top:4px\">'+d.symptoms.substring(0,80)+'</div></div>'}
el.innerHTML=h;
}
function renderVitals(){
var el=document.getElementById('vitalsContent');if(!el)return;
var hr=68+Math.floor(Math.random()*10),spo2=96+Math.floor(Math.random()*4),temp=(36.3+Math.random()*1.2).toFixed(1),bp=(110+Math.floor(Math.random()*20))+'/'+(70+Math.floor(Math.random()*15));
el.innerHTML='<div class=\"card\"><h3>Constantes Vitales</h3><div class=\"vital-grid\"><div class=\"vital-card\"><div class=\"value\">'+hr+'</div><div class=\"label\">BPM Cardiaque</div></div><div class=\"vital-card\"><div class=\"value\">'+bp+'</div><div class=\"label\">mmHg Tension</div></div><div class=\"vital-card\"><div class=\"value\">'+spo2+'%</div><div class=\"label\">SpO2 Oxygene</div></div><div class=\"vital-card\"><div class=\"value\">'+temp+'°C</div><div class=\"label\">Temperature</div></div></div><p style=\"font-size:.7em;color:var(--muted);text-align:center;margin-top:12px\">Simulation</p></div>';
}
function renderPatients(){
var el=document.getElementById('patientsList');if(!el)return;
var pts=loadPatients();var keys=Object.keys(pts);
var h='<div style=\"margin-bottom:12px;display:flex;gap:8px\"><input id=\"newPatientInput\" placeholder=\"Nom du patient...\" style=\"flex:1;background:#141414;color:#d4c8a0;border:1px solid #2a2a2a;padding:10px 14px;border-radius:10px;font-size:14px;font-family:inherit\"><button class=\"btn btn-sm btn-primary\" style=\"width:auto;padding:8px 16px\" onclick=\"addPatient()\">Ajouter</button></div>';
if(!keys.length)h+='<div class=\"card\"><p style=\"text-align:center;color:var(--muted)\">Aucun patient.</p></div>';
for(var i=keys.length-1;i>=Math.max(0,keys.length-10);i--){var id=keys[i];var p=pts[id];
h+='<div class=\"patient-row\" onclick=\"currentPatient={id:&quot;'+id+'&quot;,...loadPatients()[&quot;'+id+'&quot;]};showScreen(&quot;resonance&quot;);refreshPatientSelect()\"><div class=\"avatar\">'+(p.name||'?')[0].toUpperCase()+'</div><div class=\"info\"><div class=\"name\">'+p.name+'</div><div class=\"meta\">'+(p.history?p.history.length:0)+' diagnostics</div></div><span style=\"color:var(--accent);font-size:1.2em\">›</span></div>'}
el.innerHTML=h;
}
function addPatient(){var n=(document.getElementById('newPatientInput')?.value||'').trim();if(!n)return;var pts=loadPatients();var id='p'+Date.now();pts[id]={name:n,history:[],createdAt:new Date().toISOString()};savePatients(pts);document.getElementById('newPatientInput').value='';renderPatients();refreshPatientSelect()}
"""
script_end = old.rfind('</script>')
old = old[:script_end] + screen_js + old[script_end:]

# ── 6. BLE script ──
head_end = old.find('</head>')
old = old[:head_end] + '<script src="ka_care_ble.js"></script>\n' + old[head_end:]

# ── 7. Fix the patient "➕" button to use showScreen ──
old = old.replace("onclick=\"showScreen('patients')\"", "onclick=\"showScreen('patients')\"")

with open('ka_care.html', 'w', encoding='utf-8') as f:
    f.write(old)
print('Patched: ' + str(len(old)) + ' chars')
