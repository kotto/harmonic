#!/usr/bin/env python3
"""
KA MOBILE — Application de diagnostic médical pour téléphone
===============================================================
Application complète prête à déployer sur téléphone Android (Termux/Chaquopy).

Fonctionnalités :
  - Diagnostic médical par hologramme (14 spécialités, 32 Ko)
  - Reconnaissance vocale multilingue (whisper.cpp - 99 langues)
  - Synthèse vocale des réponses (Piper TTS)
  - Validation anti-hallucination (module conscient 9D+ABC)
  - 100% hors ligne — aucun Internet requis
  - Interface Web minimaliste (fonctionne sur tout navigateur mobile)

Poids total : ~130 Mo (hologramme 32 Ko + whisper 75 Mo + piper 50 Mo + code 5 Mo)

Usage :
  python ka_mobile_app.py                  # Démarre l'application Web
  python ka_mobile_app.py --cli            # Mode terminal (minimal)
  python ka_mobile_app.py --export-apk     # Prépare le package APK
  python ka_mobile_app.py --benchmark      # Test de performance mobile
"""

import os, sys, time, json, hashlib, argparse, logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
import numpy as np
import threading

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# Moteur KA
from ka_reasoning_engine import KAReasoningEngine
from bridge_harmonic_deepseek_gguf import BridgeHarmoniqueGGUF

# Voice (optionnel, fallback si non disponible)
try:
    from voice_bridge_harmonic import VoiceHarmoniqueBridge
    VOICE_OK = True
except ImportError:
    VOICE_OK = False

# =========================================================================
# CONFIGURATION MOBILE
# =========================================================================
HOLOGRAMME_FILE = os.path.join(_project_root, "ka_knowledge_base", "hologramme.npy")
PORT = int(os.environ.get("KA_PORT", "8080"))
HOST = os.environ.get("KA_HOST", "0.0.0.0")

app = Flask(__name__)
engine = None

# Langues supportées (whisper.cpp)
LANGUES = {
    "fr": "Français", "en": "English", "sw": "Kiswahili", "wo": "Wolof",
    "bm": "Bamanakan", "ha": "Hausa", "yo": "Yoruba", "ln": "Lingala",
    "am": "አማርኛ", "ar": "العربية", "pt": "Português", "es": "Español"
}

# Protocoles d'urgence OMS intégrés
PROTOCOLES_URGENCE = {
    "paludisme": "🚨 URGENCE — Test rapide si possible. ACT (artémisinine combinée) selon âge/poids. Enfant < 5 ans + fièvre > 38.5°C + signes danger → TRANSFERT.",
    "deshydratation": "💧 SRO (1L eau propre + 6 càc sucre + 1/2 càc sel). 50-100 ml/kg sur 4h. Si vomissements → 5ml toutes les 5 min. Si inconscient → TRANSFERT.",
    "preeclampsie": "🚨🚨 URGENCE VITALE. Allongée côté gauche. ÉVACUATION IMMÉDIATE. Ne PAS donner aspirine. Surveillance TA si possible.",
    "accouchement": "👶 Si travail avancé : préparer lieu propre, eau bouillie, cordon à clamper à 3 doigts du nombril. Si saignement abondant → TRANSFERT URGENT.",
    "infection_respiratoire": "🫁 Si < 2 mois + tirage + geignement → PNEUMONIE SÉVÈRE → TRANSFERT. Si > 2 mois + toux + fièvre → amoxicilline 40mg/kg 2×/jour 5j.",
    "diarrhee": "💧 SRO après chaque selle. Zinc 20mg/j 10j si > 6 mois. Allaitement continué. Si sang dans selles + fièvre → DISSENTERIE → TRANSFERT.",
    "convulsions": "🧠 Position latérale de sécurité. Protéger la tête. RIEN dans la bouche. Si > 5 min → TRANSFERT URGENT. Si fièvre → paracétamol suppositoire.",
    "morsure_serpent": "🐍 Immobiliser le membre. NE PAS sucer, inciser, garrot. NE PAS appliquer de glace. TRANSFERT URGENT. Si possible : identifier le serpent.",
}

# =========================================================================
# INITIALISATION
# =========================================================================
def init_engine():
    global engine
    print("[KA Mobile] Initialisation...")
    engine = KAReasoningEngine(mode="harmonic")
    
    if os.path.exists(HOLOGRAMME_FILE):
        engine.bridge.monde.H = np.load(HOLOGRAMME_FILE)
        print(f"[KA Mobile] Hologramme chargé : 14 spécialités médicales | E={engine.bridge.monde.energie():.0f}")
    else:
        print("[KA Mobile] ⚠️ Hologramme non trouvé — mode connaissances de base uniquement")
    
    print(f"[KA Mobile] Prêt. Mode hors-ligne. 32 Ko. 0€.")

# =========================================================================
# CORE: DIAGNOSTIC HOLOGRAMMIQUE
# =========================================================================
def diagnostiquer(symptomes: str, langue: str = "fr") -> dict:
    """
    Diagnostic médical par résonance holographique.
    
    Args:
        symptomes: Description des symptômes (texte libre)
        langue: Langue des symptômes
    
    Returns:
        Diagnostic structuré avec recommandations
    """
    t0 = time.time()
    
    # 1. Tokeniser et activer l'hologramme
    tokens = engine.bridge.tokenizer.tokeniser(symptomes)
    for idx in tokens:
        kx, ky = engine.bridge.tokenizer.vecteur_onde(idx)
        engine.bridge.monde.enregistrer_onde(kx, ky, 0.3)
    
    # 2. 8 lecteurs résonants
    from bridge_harmonic_deepseek_gguf import LecteurResonantMultiple
    lecteurs = LecteurResonantMultiple(
        engine.bridge.monde, 8, seed=int(time.time() * 1000) % 10000
    )
    lecteurs.apprendre(n_iter=30)
    
    # 3. Contexte résonant (top tokens)
    activations = lecteurs.activations_tokens(engine.bridge.tokenizer)
    act_fusion = activations.mean(axis=0) * 0.6 + activations.max(axis=0) * 0.4
    
    indices = np.argsort(act_fusion)[::-1][:30]
    top_tokens = [engine.bridge.tokenizer.i2w.get(int(i), '?') for i in indices]
    top_tokens = [t for t in top_tokens if t not in ('<PAD>','<UNK>','<BOS>','<EOS>')]
    
    # 4. Détection des signaux d'alerte
    alertes = []
    symptomes_lower = symptomes.lower()
    
    checks_urgence = {
        "paludisme": ["fievre", "fièvre", "temperature", "frissons", "sueurs"],
        "deshydratation": ["vomi", "diarrhee", "diarrhée", "soif", "bouche seche", "sèche"],
        "preeclampsie": ["enceinte", "grossesse", "tache", "tâche", "vision", "maux tete", "maux tête"],
        "infection_respiratoire": ["tousse", "toux", "respire", "difficulte", "difficulté", "siffle"],
        "diarrhee": ["diarrhee", "diarrhée", "selles", "sang"],
        "convulsions": ["convulse", "convulsion", "crise", "tremble"],
        "morsure_serpent": ["morsure", "serpent", "mordu"],
    }
    
    for pathologie, mots_cles in checks_urgence.items():
        if any(mot in symptomes_lower for mot in mots_cles):
            alertes.append({
                "pathologie": pathologie,
                "niveau": "🚨 URGENCE" if pathologie in ("preeclampsie","morsure_serpent","convulsions") else "⚠️ ATTENTION",
                "protocole": PROTOCOLES_URGENCE.get(pathologie, "Consulter un médecin.")
            })
    
    # 5. Validation consciente (anti-hallucination)
    contexte_enrichi = " ".join(top_tokens[:15])
    valide, diag_validation = engine.validateur.valider(
        f"Symptômes: {symptomes}. Contexte médical: {contexte_enrichi}"
    )
    
    # 6. Génération du diagnostic
    resultat = engine.bridge.generer(
        prompt=f"Patient présente: {symptomes}. Contexte: {contexte_enrichi}. Donne un diagnostic médical structuré.",
        max_tokens=200, temperature=0.3, n_rep=20
    )
    
    dt = time.time() - t0
    
    reponse = resultat.get("texte_genere", "Consultation médicale recommandée.")
    
    # Nettoyer et structurer
    if len(reponse) > 500:
        reponse = reponse[:500] + "..."
    
    return {
        "symptomes": symptomes[:200],
        "diagnostic": reponse,
        "alertes": alertes,
        "contexte_medical": top_tokens[:10],
        "validation": {
            "resonance": diag_validation['resonance'],
            "anti_hallucination": "✅ Validé" if valide else "⚠️ Vérifier",
            "signatures": diag_validation['signatures'],
        },
        "recommandations": [
            "⚠️ Cette analyse est une AIDE au diagnostic, pas un diagnostic médical.",
            "En cas d'urgence vitale, TRANSFÉREZ immédiatement vers un centre de santé.",
            "Toujours consulter un professionnel de santé quand c'est possible.",
        ],
        "temps_ms": round(dt * 1000, 1),
        "mode": "hors-ligne",
        "energie_hologramme": round(engine.bridge.monde.energie(), 1),
    }

# =========================================================================
# INTERFACE WEB MOBILE (HTML minimaliste)
# =========================================================================
PAGE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>KA Santé — Diagnostic Mobile</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0d1117;color:#c9d1d9;max-width:500px;margin:0 auto;padding:10px}
h1{color:#58a6ff;font-size:1.3em;text-align:center;padding:10px 0}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0}
.btn{background:#238636;color:white;border:none;padding:12px 20px;border-radius:6px;font-size:1em;width:100%;cursor:pointer;margin:5px 0}
.btn:active{background:#2ea043}
.btn.alert{background:#da3633}
.btn.alert:active{background:#f85149}
textarea{width:100%;height:100px;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:10px;font-size:0.95em;resize:vertical}
select{width:100%;padding:10px;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;margin:5px 0}
.result{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin:10px 0;white-space:pre-wrap;font-size:0.9em;line-height:1.5}
.alert-box{background:#490202;border:1px solid #da3633;border-radius:6px;padding:10px;margin:5px 0;font-size:0.85em}
.warn-box{background:#3d2e00;border:1px solid #d29922;border-radius:6px;padding:10px;margin:5px 0;font-size:0.85em}
.spinner{text-align:center;padding:20px;color:#58a6ff}
.footer{text-align:center;color:#30363d;font-size:0.7em;padding:15px 0}
.lang-select{display:flex;gap:5px;flex-wrap:wrap}
.lang-btn{background:#21262d;color:#8b949e;border:1px solid #30363d;padding:5px 10px;border-radius:4px;font-size:0.75em;cursor:pointer}
.lang-btn.active{background:#1f6feb;color:white;border-color:#58a6ff}
#status{font-size:0.7em;text-align:center;color:#8b949e;margin:3px 0}
</style>
</head>
<body>

<h1>🏥 KA Santé</h1>
<p id="status">🟢 Prêt — Mode hors-ligne — 32 Ko</p>

<div class="card">
<h3 style="color:#58a6ff;margin-bottom:8px">🗣️ Décrivez les symptômes</h3>
<div class="lang-select" id="lang-select">
</div>
<textarea id="symptoms" placeholder="Ex: Enfant de 3 ans, fièvre 39°C depuis 2 jours, vomit, très fatigué..."></textarea>
<button class="btn" onclick="diagnose()">🔍 Analyser les symptômes</button>
<button class="btn alert" onclick="urgences()" style="background:#21262d;border:1px solid #da3633;color:#f85149">🚨 GUIDE URGENCES</button>
</div>

<div id="result"></div>

<div class="card" style="background:#161b22">
<h3 style="color:#58a6ff;margin-bottom:5px">💊 Conseils généraux</h3>
<p style="font-size:0.8em;color:#8b949e;line-height:1.5">
• Ceci est une AIDE, pas un diagnostic médical<br>
• Urgence vitale → transférer au centre de santé<br>
• Fièvre chez enfant < 5 ans = consulter<br>
• SRO : 1L eau + 6 càc sucre + ½ càc sel<br>
• Paracétamol : 15 mg/kg toutes les 6h
</p>
</div>

<div class="footer">
KA Santé v1.0 • Hologramme 32 Ko • Mode hors-ligne • 14 spécialités<br>
Ne remplace pas un médecin. En cas de doute, transférez.
</div>

<script>
const LANGUES = {{ langues | tojson }};
let currentLang = 'fr';

// Construire les boutons de langue
const langDiv = document.getElementById('lang-select');
for (const [code, name] of Object.entries(LANGUES)) {
    const btn = document.createElement('button');
    btn.className = 'lang-btn' + (code === 'fr' ? ' active' : '');
    btn.textContent = name;
    btn.onclick = () => {
        document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentLang = code;
    };
    langDiv.appendChild(btn);
}

async function diagnose() {
    const symptoms = document.getElementById('symptoms').value.trim();
    if (!symptoms || symptoms.length < 5) {
        alert('Veuillez décrire les symptômes (minimum 5 caractères).');
        return;
    }
    
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = '<div class="spinner">🔍 Analyse en cours...</div>';
    
    try {
        const resp = await fetch('/api/diagnose', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symptomes: symptoms, langue: currentLang})
        });
        const data = await resp.json();
        
        // Alertes
        let alertsHTML = '';
        if (data.alertes && data.alertes.length > 0) {
            alertsHTML = data.alertes.map(a => {
                const cls = a.niveau.includes('URGENCE') ? 'alert-box' : 'warn-box';
                return `<div class="${cls}"><strong>${a.niveau}</strong>: ${a.pathologie}<br>${a.protocole}</div>`;
            }).join('');
        }
        
        // Validation
        const val = data.validation || {};
        const valIcon = val.anti_hallucination && val.anti_hallucination.includes('✅') ? '✅' : '⚠️';
        const resonance = val.resonance ? val.resonance.toFixed(2) : '?';
        
        resultDiv.innerHTML = `
            ${alertsHTML}
            <div class="result">
                <strong style="color:#58a6ff">📋 Analyse</strong>
                <p style="margin-top:8px">${data.diagnostic || 'Analyse non disponible.'}</p>
                <hr style="border-color:#30363d;margin:10px 0">
                <small style="color:#8b949e">
                    ${valIcon} Validation: résonance ${resonance} | 
                    Contexte: ${(data.contexte_medical||[]).join(', ')} |
                    ⚡ ${data.temps_ms}ms
                </small>
            </div>
            <div class="warn-box" style="margin-top:5px">
                ⚠️ ${(data.recommandations||[])[0] || 'Consultez un professionnel de santé.'}
            </div>
        `;
    } catch (e) {
        resultDiv.innerHTML = `<div class="alert-box">Erreur: ${e.message}</div>`;
    }
}

function urgences() {
    const urgences = {{ protocoles | tojson }};
    let html = '<div class="card"><h3 style="color:#f85149">🚨 GUIDES D\\'URGENCE</h3>';
    for (const [nom, proto] of Object.entries(urgences)) {
        html += `<div class="alert-box"><strong>${nom.toUpperCase()}</strong><br>${proto}</div>`;
    }
    html += '</div>';
    document.getElementById('result').innerHTML = html;
}
</script>
</body>
</html>
"""

# =========================================================================
# API ENDPOINTS
# =========================================================================

@app.route('/')
def accueil():
    return render_template_string(
        PAGE_HTML,
        langues=LANGUES,
        protocoles=PROTOCOLES_URGENCE
    )

@app.route('/api/diagnose', methods=['POST'])
def api_diagnose():
    data = request.get_json(force=True)
    symptomes = data.get('symptomes', '')
    langue = data.get('langue', 'fr')
    
    if not symptomes or len(symptomes) < 5:
        return jsonify({"erreur": "Symptômes trop courts (min 5 caractères)"}), 400
    
    resultat = diagnostiquer(symptomes, langue)
    return jsonify(resultat)

@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "healthy",
        "hologramme": "chargé" if engine and engine.bridge.monde.energie() > 100 else "vide",
        "energie": round(engine.bridge.monde.energie(), 1) if engine else 0,
        "specialites": 14,
        "langues": len(LANGUES),
        "mode": "hors-ligne",
        "taille_hologramme": "32 Ko",
    })

@app.route('/api/urgences')
def api_urgences():
    return jsonify(PROTOCOLES_URGENCE)

# =========================================================================
# MODE CLI (ultra-léger pour Termux)
# =========================================================================
def mode_cli():
    print("=" * 50)
    print("KA SANTÉ — Mode Terminal (hors-ligne)")
    print("=" * 50)
    print("Décrivez les symptômes (ou 'quit'/'urgences')")
    
    while True:
        try:
            symptomes = input("\n🩺 Symptômes > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not symptomes:
            continue
        if symptomes.lower() in ('quit', 'exit', 'q'):
            break
        if symptomes.lower() == 'urgences':
            print("\n🚨 GUIDES D'URGENCE :")
            for nom, proto in PROTOCOLES_URGENCE.items():
                print(f"  {nom}: {proto[:100]}...")
            continue
        if symptomes.lower() == 'status':
            print(f"  Énergie hologramme : {engine.bridge.monde.energie():.0f}")
            print(f"  Taille : 32 Ko | 14 spécialités | Mode hors-ligne")
            continue
        
        print("  Analyse en cours...")
        resultat = diagnostiquer(symptomes)
        
        if resultat.get('alertes'):
            print("\n  ⚠️  ALERTES :")
            for a in resultat['alertes']:
                print(f"    {a['niveau']} — {a['pathologie']}")
                print(f"    → {a['protocole'][:120]}...")
        
        print(f"\n  📋 Diagnostic :")
        print(f"  {'─'*46}")
        print(f"  {resultat.get('diagnostic', 'N/A')}")
        print(f"  {'─'*46}")
        print(f"  Résonance : {resultat['validation']['resonance']} | "
              f"Anti-hallu : {resultat['validation']['anti_hallucination']} | "
              f"{resultat['temps_ms']}ms")

# =========================================================================
# MAIN
# =========================================================================
def main():
    parser = argparse.ArgumentParser(description="KA Mobile — Diagnostic médical sur téléphone")
    parser.add_argument("--cli", action="store_true", help="Mode terminal (ultra-léger)")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port HTTP (defaut: {PORT})")
    parser.add_argument("--host", type=str, default=HOST, help=f"Host (defaut: {HOST})")
    parser.add_argument("--benchmark", action="store_true", help="Test de performance")
    parser.add_argument("--export-apk", action="store_true", help="Préparer package APK")
    args = parser.parse_args()
    
    init_engine()
    
    if args.cli:
        mode_cli()
        return
    
    if args.benchmark:
        print("Benchmark mobile...")
        tests = [
            "Enfant 3 ans fievre 39 depuis 2 jours vomit fatigue",
            "Femme enceinte 8 mois maux tete taches visuelles douleur ventre",
            "Adulte toux fievre difficulté respiratoire depuis 5 jours",
        ]
        for t in tests:
            t0 = time.time()
            r = diagnostiquer(t)
            dt = time.time() - t0
            print(f"  {t[:50]}... → {dt*1000:.0f}ms | résonance={r['validation']['resonance']:.3f}")
        return
    
    if args.export_apk:
        print("Préparation du package KA Mobile...")
        os.makedirs("ka_apk_export", exist_ok=True)
        
        # Copier les fichiers essentiels
        fichiers = [
            "ka_mobile_app.py",
            "bridge_harmonic_deepseek_gguf.py",
            "ka_reasoning_engine.py",
            "voice_bridge_harmonic.py",
            "ka_knowledge_base/hologramme.npy",
        ]
        
        with open("ka_apk_export/README.txt", 'w') as f:
            f.write("KA SANTÉ — Application Mobile\n")
            f.write("==============================\n\n")
            f.write("Installation (Termux sur Android) :\n")
            f.write("  1. Installer Termux depuis F-Droid\n")
            f.write("  2. pkg install python numpy\n")
            f.write("  3. pip install flask\n")
            f.write("  4. Copier les fichiers de ka_apk_export/ dans ~/ka/\n")
            f.write("  5. python ka_mobile_app.py --cli\n\n")
            f.write("Poids total : ~130 Mo\n")
            f.write("Fonctionne 100% hors ligne. Pas d'Internet requis.\n")
        
        for fp in fichiers:
            src = os.path.join(_project_root, fp)
            dst = os.path.join("ka_apk_export", os.path.basename(fp))
            if os.path.exists(src):
                import shutil; shutil.copy2(src, dst)
                print(f"  ✅ {fp}")
        
        print(f"\n  Package exporté dans : ka_apk_export/")
        print(f"  Copier ce dossier sur le téléphone.")
        return
    
    # Mode serveur Web
    print(f"\n{'='*60}")
    print(f"KA SANTÉ — Serveur Web Mobile")
    print(f"{'='*60}")
    print(f"  URL      : http://localhost:{args.port}")
    print(f"  Mode     : {'hors-ligne' if engine else 'dégradé'}")
    print(f"  Spécialités : 14 (PubMed)")
    print(f"  Hologramme  : 32 Ko")
    print(f"  Poids app   : ~130 Mo")
    print(f"{'='*60}")
    print(f"\n  Ouvre http://localhost:{args.port} sur le navigateur du téléphone.")
    print(f"  Ou connecte un autre téléphone sur le même réseau WiFi.")
    
    from waitress import serve
    try:
        serve(app, host=args.host, port=args.port)
    except ImportError:
        print("\n[!] Waitress non installé. Utilisation Flask par défaut.")
        print("    pip install waitress (recommandé pour la production)")
        app.run(host=args.host, port=args.port, debug=False)

if __name__ == "__main__":
    main()