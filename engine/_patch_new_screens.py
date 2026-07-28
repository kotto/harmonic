"""Add 4 missing Stitch screens to ka_care.html"""
with open('ka_care.html', 'r', encoding='utf-8') as f:
    old = f.read()

# ── 1. Add CSS for new screens ──
new_css = """
/* Cardiac */
.ecg-grid{position:relative;width:100%;height:200px;background:#111;border-radius:12px;overflow:hidden;border:1px solid #2a2a2a}
.ecg-grid svg{position:absolute;top:0;left:0;width:100%;height:100%}
.ecg-grid .grid-overlay{position:absolute;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,transparent,transparent 49px,rgba(212,168,83,0.05) 50px),repeating-linear-gradient(90deg,transparent,transparent 49px,rgba(212,168,83,0.05) 50px)}
.stat-card{background:#111;border-radius:10px;padding:14px;border:1px solid #2a2a2a;text-align:center}
.stat-card .val{font-size:1.3em;font-weight:700;color:#d4a853}
.stat-card .lbl{font-size:.7em;color:#9b8f7e;margin-top:2px}
/* Scanner */
.scanner-view{position:relative;width:260px;height:260px;margin:30px auto;border:2px solid rgba(212,168,83,0.3);border-radius:16px}
.scanner-view .corner{position:absolute;width:30px;height:30px;border-color:#d4a853;border-style:solid}
.scanner-view .corner.tl{top:-2px;left:-2px;border-width:3px 0 0 3px;border-radius:8px 0 0 0}
.scanner-view .corner.tr{top:-2px;right:-2px;border-width:3px 3px 0 0;border-radius:0 8px 0 0}
.scanner-view .corner.bl{bottom:-2px;left:-2px;border-width:0 0 3px 3px;border-radius:0 0 0 8px}
.scanner-view .corner.br{bottom:-2px;right:-2px;border-width:0 3px 3px 0;border-radius:0 0 8px 0}
.scanner-view .scan-line{position:absolute;left:10%;right:10%;height:2px;background:linear-gradient(90deg,transparent,#d4a853,transparent);animation:scanAnim 2s ease-in-out infinite}
@keyframes scanAnim{0%,100%{top:10%}50%{top:85%}}
/* Events timeline */
.event-row{display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-left:2px solid #2a2a2a;margin-left:8px;padding-left:16px}
.event-row .dot{width:8px;height:8px;border-radius:50%;background:#d4a853;margin-top:6px;margin-left:-21px;flex-shrink:0}
.event-row .evt-time{font-size:.7em;color:#9b8f7e;min-width:50px}
.event-row .evt-text{font-size:.85em;color:#eae1d7}
/* Harmonic link badge */
.harmonic-badge{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;background:rgba(39,174,96,0.1);border:1px solid rgba(39,174,96,0.3);color:#27ae60;font-size:.75em;font-weight:600}
.harmonic-badge .dot{width:7px;height:7px;border-radius:50%;background:#27ae60;animation:pulse 2s infinite}
/* Quick actions grid */
.action-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
.action-card{background:#111;border-radius:12px;padding:18px;border:1px solid #2a2a2a;text-align:center;cursor:pointer;transition:all .15s}
.action-card:hover{border-color:rgba(212,168,83,0.4);background:#1a1810}
.action-card .icon{font-size:2em;margin-bottom:6px}
.action-card .title{font-weight:600;font-size:.9em;color:#d4a853}
.action-card .sub{font-size:.7em;color:#9b8f7e;margin-top:2px}
"""
old = old.replace('</style>', new_css + '</style>')

# ── 2. Add hidden screen divs for the 4 new screens ──
body_end = old.rfind('</body>')

new_screens = """
<div class="screen" id="screen-cardiac">
<div style="padding:16px">
<header style="text-align:center;padding:24px 0 16px"><h2 style="color:#d4a853">ANALYSE CARDIAQUE</h2></header>
<div class="card"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px"><h3 style="margin:0">ECG — Derivation II</h3><span class="harmonic-badge" id="harmonicStatus"><span class="dot"></span> Link Actif 94%</span></div>
<div class="ecg-grid"><div class="grid-overlay"></div>
<svg viewBox="0 0 600 200"><path d="M0,100 L50,100 L55,100 L60,30 L65,170 L70,100 L120,100 L125,100 L130,20 L135,180 L140,100 L200,100 L250,100 L300,100 L350,100 L400,100 L450,100 L500,100 L505,100 L510,40 L515,160 L520,100 L570,100 L600,100" stroke="#d4a853" stroke-width="2" fill="none" opacity="0.8"/></svg></div>
<div style="margin-top:12px"><input type="range" min="0" max="100" value="50" style="width:100%;accent-color:#d4a853"></div></div>
<div class="vital-grid" style="margin-top:12px">
<div class="stat-card"><div class="val">72</div><div class="lbl">BPM MOYEN</div></div>
<div class="stat-card"><div class="val">45 ms</div><div class="lbl">VARIABILITE</div></div>
<div class="stat-card"><div class="val">0</div><div class="lbl">ANOMALIES 24h</div></div>
<div class="stat-card"><div class="val">98%</div><div class="lbl">FIABILITE</div></div>
</div>
<div class="card" style="margin-top:12px"><h3>Evenements recents</h3>
<div class="event-row"><span class="dot"></span><span class="evt-time">14:30</span><span class="evt-text">Pic d'activite — 94 BPM</span></div>
<div class="event-row"><span class="dot" style="background:#666"></span><span class="evt-time">12:15</span><span class="evt-text">Phase de repos — 58 BPM</span></div>
<div class="event-row"><span class="dot" style="background:#666"></span><span class="evt-time">08:45</span><span class="evt-text">Variabilite matinale — 52 ms</span></div>
</div>
</div>
</div>

<div class="screen" id="screen-scanner">
<div style="padding:16px">
<header style="text-align:center;padding:24px 0 16px"><h2 style="color:#d4a853">SCANNER QR CODE</h2></header>
<div class="card" style="text-align:center">
<div class="scanner-view"><div class="corner tl"></div><div class="corner tr"></div><div class="corner bl"></div><div class="corner br"></div><div class="scan-line"></div></div>
<p style="color:#9b8f7e;margin:16px 0">Recherche de signal...</p>
<button class="btn btn-secondary" style="width:auto;padding:10px 24px;margin:0 auto">📷 Activer la camera</button>
<p style="font-size:.7em;color:#8b7355;margin-top:8px">Ou saisir le code manuellement</p>
<input placeholder="Code patient..." style="width:200px;padding:8px 12px;background:#141414;color:#d4c8a0;border:1px solid #2a2a2a;border-radius:8px;font-size:14px;font-family:inherit;text-align:center;margin-top:8px">
</div>
</div>
</div>

<div class="screen" id="screen-dossier">
<div style="padding:16px">
<header style="text-align:center;padding:24px 0 16px"><h2 style="color:#d4a853">DOSSIER MEDICAL</h2></header>
<div class="card" style="text-align:center"><div style="width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,#d4a853,#7b5804);display:flex;align-items:center;justify-content:center;font-size:1.6em;font-weight:700;margin:0 auto 8px" id="dossierAvatar">?</div><h3 id="dossierName">Patient anonyme</h3><p style="color:#9b8f7e;font-size:.8em" id="dossierId"></p></div>
<div class="vital-grid" style="margin-top:12px">
<div class="stat-card"><div class="val">72</div><div class="lbl">BPM</div></div>
<div class="stat-card"><div class="val">12/8</div><div class="lbl">cmHg</div></div>
<div class="stat-card"><div class="val">98%</div><div class="lbl">SpO2</div></div>
<div class="stat-card"><div class="val">36.7°</div><div class="lbl">Temp</div></div>
</div>
<div class="action-grid" style="margin-top:12px">
<div class="action-card" onclick="showScreen('resonance')"><div class="icon">🔍</div><div class="title">Nouveau Diagnostic</div><div class="sub">Lancer une analyse</div></div>
<div class="action-card" onclick="showScreen('cardiac')"><div class="icon">🫀</div><div class="title">Analyse Cardiaque</div><div class="sub">ECG detaille</div></div>
<div class="action-card" onclick="showScreen('history')"><div class="icon">📋</div><div class="title">Historique</div><div class="sub">Diagnostics passes</div></div>
<div class="action-card" onclick="showScreen('scanner')"><div class="icon">📷</div><div class="title">Scanner QR</div><div class="sub">Ouvrir un dossier</div></div>
</div>
</div>
</div>
"""
old = old[:body_end] + new_screens + old[body_end:]

# ── 3. Update bottom nav to include new tabs ──
# Add Cardiac and Scanner tabs (keep 4 main, use Dossier as detail of Profile)
# Just ensure the existing nav items work — the new screens are accessible from Dossier

# ── 4. Update JS to populate dossier when patient is selected ──
update_js = """
function updateDossier(){if(!currentPatient){document.getElementById('dossierAvatar').textContent='?';document.getElementById('dossierName').textContent='Patient anonyme';document.getElementById('dossierId').textContent='';return}document.getElementById('dossierAvatar').textContent=(currentPatient.name||'?')[0].toUpperCase();document.getElementById('dossierName').textContent=currentPatient.name;document.getElementById('dossierId').textContent='ID: '+currentPatient.id;}
var origOnPatientSelect = onPatientSelect;
onPatientSelect = function(id){origOnPatientSelect(id);updateDossier();}
"""
script_end = old.rfind('</script>')
old = old[:script_end] + update_js + old[script_end:]

with open('ka_care.html', 'w', encoding='utf-8') as f:
    f.write(old)
print('4 screens added: ' + str(len(old)) + ' chars')
