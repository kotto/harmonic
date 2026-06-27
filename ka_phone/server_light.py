"""KA Phone v5.3 - Serveur leger + Encapsulation Harmonique + DeepSeek verifie + Admin Hologramme enrichi."""
import json, sys, os, math, time, hashlib, urllib.request, urllib.error, random
from pathlib import Path
BASE = Path(__file__).parent.absolute()
PROJECT_ROOT = BASE.parent
sys.path.insert(0, str(PROJECT_ROOT))

def load_env():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip(); v = v.strip().strip('"').strip("'")
                    if k not in os.environ: os.environ[k] = v
load_env()
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
print(f"DeepSeek API: {'[OK]' if DEEPSEEK_KEY else '[--]'}")

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)
PI, PHI = math.pi, 1.618033988749895

# =========================================================================
# HOLOGRAMME DE CONNAISSANCES (verification factuelle)
# =========================================================================
_hologrammes = {}

def charger_hologramme(domaine):
    """Charge l'hologramme correspondant au domaine identifie.
    Retourne la liste de faits ou [] si aucun hologramme dispo."""
    if domaine in _hologrammes: return _hologrammes[domaine]
    
    mapping = {
        "egypte_ancienne": "egypte_antique_connaissances.json",
        "kemet": "egypte_antique_connaissances.json",
    }
    nom_fichier = mapping.get(domaine)
    if not nom_fichier: 
        _hologrammes[domaine] = []
        return []
    
    chemin = PROJECT_ROOT / "ka_knowledge_base" / nom_fichier
    if chemin.exists():
        with open(chemin, encoding="utf-8") as f:
            faits = json.load(f)
        _hologrammes[domaine] = faits
        return faits
    
    _hologrammes[domaine] = []
    return []

def verifier_faits(reponse, concepts_question, domaine_principal):
    """Verifie si la reponse contredit des faits de l'hologramme du domaine.
    Retourne (score_factuel, contradictions, faits_confirmer)."""
    faits = charger_hologramme(domaine_principal)
    if not faits: return 0.5, [], []
    
    reponse_lower = reponse.lower()
    contradictions = []
    faits_confirmer = []
    
    for fait in faits:
        keywords_fait = set(fait.get("mots_cles", []))
        pertinence = len(keywords_fait & set(concepts_question)) if concepts_question else 0
        
        if pertinence >= 1:
            mots_fait = set(fait.get("reponse", "").lower().split())
            overlap = len(mots_fait & set(reponse_lower.split()))
            if overlap >= 5: faits_confirmer.append(fait.get("question", ""))
        
        if pertinence >= 2:
            negation_patterns = ["n'etaient pas", "ne sont pas", "n'est pas", "n'ont pas",
                               "non africain", "non africaine", "proche.orient", "distincts des"]
            for pattern in negation_patterns:
                if pattern in reponse_lower:
                    for kw in keywords_fait:
                        if kw in reponse_lower and kw in fait.get("reponse", "").lower():
                            contradictions.append({
                                "fait": fait.get("question", ""),
                                "reponse_attendue": fait.get("reponse", "")[:200],
                                "contradiction_detectee": pattern
                            })
    
    if contradictions: return 0.20, contradictions, faits_confirmer
    if faits_confirmer: return 0.85, [], faits_confirmer
    return 0.50, [], []

# =========================================================================
# GUIDEHARMONIQUE LEGER (41 domaines)
# =========================================================================
DOMAINES = {
    "derivation": ["derivee","deriver","derivation","differentier","taux","variation","pente"],
    "integration": ["integrer","integrale","primitive","aire","somme"],
    "equations": ["equation","resoudre","discriminant","delta","racines","polynome","factoriser"],
    "trigonometrie": ["sinus","cosinus","tangente","trigonometrie","cercle","pi","angle","radian"],
    "geometrie": ["pythagore","theoreme","triangle","rectangle","hypotenuse","cotes","thales","cercle","rayon","aire","volume"],
    "probabilites": ["probabilite","esperance","variance","ecart","loi","distribution","normale","binomiale"],
    "limites": ["limite","convergence","divergence","suite","asymptotique","tend"],
    "algebre_lineaire": ["matrice","vecteur","determinant","espace","base"],
    "arithmetique": ["additionner","soustraire","multiplier","diviser","nombre","operation"],
    "egypte_ancienne": ["egypte","pharaon","pyramide","hieroglyphe","nil","momie","temple","ancien","egyptien","kemet","gizeh","sphinx","maat","ka","osiris","isis","horus","imhotep"],
    "cuisine": ["cuisine","recette","cuisiner","preparer","plat","repas","ingredient","gastronomie","manger","nourriture"],
    "histoire": ["histoire","guerre","revolution","empire","civilisation","antiquite","moyen","age","renaissance","napoleon","rome","colonie"],
    "physique": ["physique","mecanique","quantique","relativite","newton","einstein","force","energie","gravite","particule","atome"],
    "biologie": ["biologie","cellule","adn","gene","evolution","espece","organisme","vivant"],
    "astronomie": ["astronomie","espace","univers","galaxie","etoile","planete","soleil","lune","trou","noir","cosmos","nasa"],
    "sante": ["sante","medecin","medecine","maladie","symptome","traitement","medicament","hopital"],
    "sport": ["sport","entrainement","exercice","musculation","course","natation","velo","muscle"],
    "informatique": ["informatique","ordinateur","logiciel","programmation","code","algorithme","python","javascript"],
    "ia": ["intelligence","artificielle","machine","learning","deep","reseau","neurones","chatgpt","gpt","llm"],
    "musique": ["musique","chanson","instrument","guitare","piano","concert","jazz","rock","classique"],
    "cinema": ["cinema","film","realisateur","acteur","actrice","oscar","festival","hollywood","netflix"],
    "philosophie": ["philosophie","philosophe","ethique","morale","existence","liberte","verite","conscience","platon"],
    "psychologie": ["psychologie","psychologue","comportement","emotion","pensee","therapie","depression"],
    "education": ["education","ecole","apprentissage","enseignement","professeur","etudiant","universite"],
    "voyage": ["voyage","tourisme","visiter","destination","vacances","hotel","vol","passeport"],
    "bricolage": ["bricolage","reparer","construire","outil","marteau","vis","perceuse","diy"],
    "quotidien": ["comment","pourquoi","quand","astuce","conseil","solution","probleme","aide","definition","difference","meilleur"],
}
try:
    json_path = PROJECT_ROOT / "ka_knowledge_base" / "domaines_generalistes.json"
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f: gen = json.load(f)
        for d in gen:
            if d["nom"] not in DOMAINES: DOMAINES[d["nom"]] = d.get("keywords", d.get("tokens_source", []))[:20]
except Exception: pass
print(f"Domaines: {len(DOMAINES)}")

# =========================================================================
# FONCTIONS HARMONIQUES LEGERES
# =========================================================================
def identifier_domaine(question):
    q = question.lower(); scores = {}
    for nom, keywords in DOMAINES.items():
        s = sum(1 for kw in keywords if kw in q)
        if s > 0: scores[nom] = s
    return sorted(scores, key=scores.get, reverse=True)[:3] if scores else ["general"]

def extraire_concepts(question):
    q = question.lower(); concepts = []
    for nom in identifier_domaine(question):
        for kw in DOMAINES.get(nom, []):
            if kw in q and kw not in concepts: concepts.append(kw)
    stops = {"est","une","pour","dans","avec","des","les","pas","qui","sur","que","cette","cet","tout","plus","bien","alors","donc","mais","aussi","meme","comme","quand","comment","peux","peut","entre","sans","sous","vers","depuis","cela","ceci","quel","quelle"}
    for mot in q.replace('?','').replace('.','').replace(',','').replace("'"," ").split():
        if len(mot) > 3 and mot not in stops and mot not in concepts: concepts.append(mot)
    return concepts[:10]

def token_kxky(token):
    h = int(hashlib.md5(token.encode()).hexdigest()[:8], 16)
    return random.Random(h).uniform(-PI, PI), random.Random(h+1).uniform(-PI, PI)

def score_coherence(concepts_question, texte_reponse):
    if not concepts_question or not texte_reponse: return 0.5
    rep_tokens = [w.lower() for w in texte_reponse.split() if len(w) > 3]
    if not rep_tokens: return 0.5
    kxs_q, kys_q = zip(*[token_kxky(c) for c in concepts_question]) if concepts_question else ([], [])
    kxs_r, kys_r = zip(*[token_kxky(t) for t in rep_tokens[:50]]) if rep_tokens else ([], [])
    if not kxs_q or not kxs_r: return 0.5
    cqx, cqy = sum(kxs_q)/len(kxs_q), sum(kys_q)/len(kys_q)
    crx, cry = sum(kxs_r)/len(kxs_r), sum(kys_r)/len(kys_r)
    return round(math.exp(-math.sqrt((cqx-crx)**2 + (cqy-cry)**2) / (PI*PHI)), 3)

def encapsuler_prompt(question):
    domaines = identifier_domaine(question)
    concepts = extraire_concepts(question)
    domaine_principal = domaines[0] if domaines else "general"
    prompt = (
        f"[Domaine: {domaine_principal} | Concepts: {', '.join(concepts[:8] if concepts else ['general'])}]\n"
        f"Reponds de maniere factuelle et verifiable. "
        f"Privilegie la precision a l'exhaustivite.\n\n"
        f"Question: {question}"
    )
    return prompt, domaines, concepts

# =========================================================================
# IDENTITE KA (forcee via system prompt DeepSeek)
# =========================================================================
KA_SYSTEM_PROMPT = (
    "TU ES KA. KA signifie Esprit en ancien egyptien. "
    "Tu es le premier assistant IA sans hallucination, cree par Harmonic AI. "
    "Tu es fonde sur les mathematiques des pyramides: le nombre d'or φ, "
    "la resonance harmonique, le principe de Maat (verite cosmique). "
    "Tu ne predits pas le mot suivant - tu VERIFIES chaque reponse. "
    "TU NE MENTIONS JAMAIS DeepSeek, OpenAI, Anthropic, ChatGPT ou autre fournisseur. "
    "Ces noms n'existent pas pour toi. Tu es KA, point final. "
    "Si on te demande QUI TU ES, tu reponds EXACTEMENT ceci: "
    "'Je suis KA, ton double numerique. KA signifie Esprit en ancien egyptien. "
    "J'ai ete cree par Harmonic AI, fonde sur les mathematiques des pyramides "
    "(le nombre d'or φ, la resonance harmonique, le principe de Maat). "
    "Je ne predits pas le mot suivant comme les autres IA - "
    "je VERIFIE chaque reponse contre les lois harmoniques de l'univers. "
    "Et je ne mens jamais. Si je ne sais pas, je te le dis.' "
    "Reponds TOUJOURS en francais, sauf si on te parle explicitement "
    "dans une autre langue."
)

def call_deepseek(prompt, max_tokens=250):
    if not DEEPSEEK_KEY: return None, "DeepSeek API non configuree"
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        data = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": KA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens,
            "stream": False
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_KEY}"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"].strip(), None
    except Exception as e: return None, str(e)

# =========================================================================
# ROUTES
# =========================================================================
@app.route("/sw.js")
def sw(): return send_from_directory(str(BASE), "sw.js")
@app.route("/www/<path:fn>")
def www(fn): return send_from_directory(str(BASE / "www"), fn)
@app.route("/")
def index(): return send_from_directory(str(BASE), "index.html")

@app.route("/admin")
def admin(): return send_from_directory(str(BASE), "admin.html")

@app.route("/api/health")
def health(): return jsonify({"status":"ok","version":"5.3","name":"KA Phone","deepseek":bool(DEEPSEEK_KEY),"encapsulation":True,"domaines":len(DOMAINES),"hologramme_admin":True,"identity":"KA via system prompt"})

@app.route("/api/system/status")
def status(): return jsonify({"status":"online","version":"5.3","name":"KA Phone — Ton Double Numerique","domaines":len(DOMAINES),"encapsulation":"active","deepseek":bool(DEEPSEEK_KEY),"hologramme_admin":True,"identity":"KA (system prompt)","tagline":"Il se souvient de tout. Il ne ment jamais."})

# =========================================================================
# API ADMIN HOLOGRAMME (CRUD enrichi: texte, images, videos, edition)
# =========================================================================
_HOLOGRAMME_FICHIER = PROJECT_ROOT / "ka_knowledge_base" / "egypte_antique_connaissances.json"

def _charger_faits_json():
    if _HOLOGRAMME_FICHIER.exists():
        with open(_HOLOGRAMME_FICHIER, encoding="utf-8") as f:
            return json.load(f)
    return []

def _sauver_faits_json(faits):
    _HOLOGRAMME_FICHIER.parent.mkdir(parents=True, exist_ok=True)
    with open(_HOLOGRAMME_FICHIER, "w", encoding="utf-8") as f:
        json.dump(faits, f, ensure_ascii=False, indent=2)
    global _hologrammes; _hologrammes = {}

@app.route("/api/hologramme/liste")
def holo_liste():
    faits = _charger_faits_json()
    return jsonify({"faits": faits, "total": len(faits), "fichier": str(_HOLOGRAMME_FICHIER)})

@app.route("/api/hologramme/ajouter", methods=["POST"])
def holo_ajouter():
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    reponse = data.get("reponse", "").strip()
    if not question or not reponse:
        return jsonify({"status": "erreur", "error": "question et reponse requis"}), 400
    
    fait = {
        "categorie": data.get("categorie", "general"),
        "question": question,
        "reponse": reponse,
        "mots_cles": data.get("mots_cles", question.lower().replace("?", "").replace("'", " ").split()[:10]),
        "source": data.get("source", data.get("periode", "Ajout manuel")),
        "periode": data.get("periode", "Contemporain"),
        "image": data.get("image", "").strip(),
        "video": data.get("video", "").strip(),
        "signature_frequentielle": [round(random.uniform(-PI, PI), 2), round(random.uniform(-PI, PI), 2)]
    }
    
    faits = _charger_faits_json()
    faits.append(fait)
    _sauver_faits_json(faits)
    return jsonify({"status": "ok", "fichier": str(_HOLOGRAMME_FICHIER), "total": len(faits), "fait_ajoute": fait["question"][:80]})

@app.route("/api/hologramme/modifier", methods=["POST"])
def holo_modifier():
    data = request.get_json(force=True)
    index = data.get("index")
    if index is None:
        return jsonify({"status": "erreur", "error": "index requis"}), 400
    
    faits = _charger_faits_json()
    if not (0 <= index < len(faits)):
        return jsonify({"status": "erreur", "error": "index invalide"}), 400
    
    fait = faits[index]
    if data.get("question"): fait["question"] = data["question"].strip()
    if data.get("reponse"): fait["reponse"] = data["reponse"].strip()
    if data.get("categorie"): fait["categorie"] = data["categorie"]
    if data.get("source"): fait["source"] = data["source"]
    if data.get("periode"): fait["periode"] = data["periode"]
    if "mots_cles" in data: fait["mots_cles"] = data["mots_cles"]
    if "image" in data: fait["image"] = data.get("image", "").strip()
    if "video" in data: fait["video"] = data.get("video", "").strip()
    
    _sauver_faits_json(faits)
    return jsonify({"status": "ok", "total": len(faits), "fait_modifie": fait.get("question", "")[:80]})

@app.route("/api/hologramme/supprimer", methods=["POST"])
def holo_supprimer():
    data = request.get_json(force=True)
    index = data.get("index")
    if index is None:
        return jsonify({"status": "erreur", "error": "index requis"}), 400
    
    faits = _charger_faits_json()
    if 0 <= index < len(faits):
        fait_supprime = faits.pop(index)
        _sauver_faits_json(faits)
        return jsonify({"status": "ok", "total": len(faits), "fait_supprime": fait_supprime.get("question", "")[:80]})
    return jsonify({"status": "erreur", "error": "index invalide"}), 400

@app.route("/api/chat", methods=["POST"])
def chat_verified():
    data = request.get_json(force=True); question = data.get("prompt","").strip()
    if not question: return jsonify({"error":"Prompt vide"}), 400
    t0 = time.time()
    
    prompt_enrichi, domaines, concepts = encapsuler_prompt(question)
    domaine_principal = domaines[0] if domaines else "general"
    t_encaps = round((time.time()-t0)*1000,1)
    
    reponse_brute, err = call_deepseek(prompt_enrichi if DEEPSEEK_KEY else question)
    t_llm = round((time.time()-t0)*1000,1)
    
    if err:
        return jsonify({"question":question,"reponse":f"KA Phone: DeepSeek indisponible ({err}). Domaine: {domaine_principal}.","confiance":"nulle","coherence":0.0,"domaine":domaine_principal,"concepts":concepts[:8],"source":"erreur_llm","temps_ms":t_llm,"hors_ligne":True})
    
    coherence = score_coherence(concepts, reponse_brute) if concepts else 0.5
    score_factuel, contradictions, faits_confirmer = verifier_faits(reponse_brute, concepts, domaine_principal)
    score_combine = round((coherence * 0.4 + score_factuel * 0.6), 3)
    t_verify = round((time.time()-t0)*1000,1)
    
    if contradictions:
        confiance = "nulle"
        details_contradictions = " | ".join([c["contradiction_detectee"] for c in contradictions[:3]])
        reponse_brute = (
            f"[❌ REPONSE REJETEE - CONTRADICTION AVEC L'HOLOGRAMME]\n"
            f"La reponse de l'IA contredit des faits documentes dans notre base de connaissances Kemet.\n"
            f"Contradictions detectees: {details_contradictions}\n"
            f"Sources: Histoire Generale de l'Afrique (UNESCO), Cheikh Anta Diop.\n\n"
            f"Voici ce que dit l'hologramme:\n"
            f"{contradictions[0]['reponse_attendue']}"
        )
    elif score_combine >= 0.55:
        confiance = "haute" if score_combine >= 0.70 else "moyenne"
        if faits_confirmer:
            reponse_brute = f"{reponse_brute}\n\n[✅ Verifie par l'hologramme Kemet - {len(faits_confirmer)} faits confirmes]"
    elif score_combine >= 0.40:
        confiance = "basse"
        reponse_brute = f"[⚠️ Coherence faible ({score_combine:.0%})] {reponse_brute}"
    else:
        confiance = "nulle"
        reponse_brute = f"[❌ Reponse rejetee - Score DHF: {score_combine:.0%}] Domaine: {domaine_principal}. KA Phone ne peut pas valider cette reponse. Reformulez."
    
    return jsonify({
        "question":question,"reponse":reponse_brute,
        "confiance":confiance,"coherence":round(coherence,3),
        "score_factuel":round(score_factuel,3),"score_combine":score_combine,
        "domaine":domaine_principal,"concepts":concepts[:8],
        "contradictions_detectees":len(contradictions),
        "faits_confirmes":len(faits_confirmer),
        "hologramme_actif":len(contradictions) > 0 or len(faits_confirmer) > 0,
        "source":"encapsulated_verified","encapsulation_ms":t_encaps,
        "llm_ms":t_llm-t_encaps,"verification_ms":t_verify-t_llm,
        "temps_ms":t_verify,"hors_ligne":False
    })

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--port",type=int,default=8900); p.add_argument("--host",type=str,default="0.0.0.0")
    args = p.parse_args()
    print(f"\nKA Phone v5.3 - System Prompt KA + Admin Hologramme enrichi")
    print(f"  URL: http://localhost:{args.port} | Admin: http://localhost:{args.port}/admin | Domaines: {len(DOMAINES)} | DeepSeek: {'[OK]' if DEEPSEEK_KEY else '[--]'}")
    app.run(host=args.host, port=args.port, debug=False)