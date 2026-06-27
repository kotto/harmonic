#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assistant Harmonique Vocal Complet
====================================
Architecture :
1. IA Harmonique → recherche factuelle via 12 hologrammes de connaissance
2. DeepSeek API → reformulation des faits en langage naturel fluide
3. TTS Server → synthèse vocale de la réponse

Pipeline complet :
Question → Hologrammes (TF-IDF + cosinus 7D) → Top-3 faits
       → DeepSeek ("Formule une réponse avec ces faits")
       → TTS local (Edge-TTS sur port 5050)

Hologrammes intégrés :
- mathématiques, science, général, philosophie
- histoire, géographie, culture, économie
- santé, nature, sports, technologie
(12 domaines, ~105K connaissances)

En mode dégradé (sans clé API DeepSeek) :
- Les faits bruts sont retournés directement
- Le TTS reste fonctionnel si le serveur est lancé

Configuration :
- export DEEPSEEK_API_KEY="sk-..." (optionnel, sinon mode dégradé)
- python tts_server.py (pour la voix, optionnel)

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, time, sys, os, json, glob
import numpy as np
from collections import Counter

# ==============================================================================
# CONSTANTES HARMONIQUES
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2); sqrt3 = math.sqrt(3); sqrt5 = math.sqrt(5)
e_sur_pi = e / pi

H = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_names = ['φ','π','e','√2','√3','√5','e/π']; H_sum = H.sum()

# ==============================================================================
# CONFIGURATION (via variables d'environnement)
# ==============================================================================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
TTS_SERVER_URL  = os.getenv("TTS_SERVER_URL", "http://localhost:5050")

# ==============================================================================
# HOLOGRAMME MINIMAL (recherche TF-IDF + cosinus 7D)
# ==============================================================================

class HologrammeMinimal:
    """Moteur de recherche holographique léger."""
    
    def __init__(self):
        self.connaissances = []  # [{'texte': str, 'domaine': str, 'mots': set}]
        self.idf = {}
    
    def charger(self, dossier="data/holograms", max_total=20000):
        """Charge les 12 hologrammes (JSON) avec priorité aux domaines scientifiques."""
        domaines_charges = {}
        total = 0
        
        for fichier_npy in sorted(glob.glob(os.path.join(dossier, "hologram64_*.npy"))):
            if total >= max_total:
                break
            
            base = os.path.basename(fichier_npy)
            domaine = base.replace("hologram64_", "").replace(".npy", "")
            fichier_json = fichier_npy.replace(".npy", "_data.json")
            
            textes = []
            if os.path.exists(fichier_json):
                with open(fichier_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'texts' in data:
                        textes = data['texts']
                    elif isinstance(data, list):
                        textes = data
                    elif isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], str):
                                textes = v; break
            
            # Limites par domaine (priorité aux domaines factuels)
            limites = {
                "general": 8000, "science": 5000, "history": 3000,
                "geography": 2000, "philosophy": 1000, "mathematics": 1000,
                "technology": 500, "health": 500, "culture": 300,
                "economics": 300, "nature": 200, "sports": 200,
            }
            max_domaine = limites.get(domaine, 300)
            textes = textes[:max_domaine]
            
            n_avant = len(self.connaissances)
            for texte in textes:
                if texte and len(texte.strip()) > 10:
                    self.connaissances.append({
                        'texte': texte.strip(),
                        'domaine': domaine,
                        'mots': set(texte.lower().split()),
                    })
                    total += 1
                    if total >= max_total:
                        break
            
            n_injecte = len(self.connaissances) - n_avant
            domaines_charges[domaine] = n_injecte
        
        # Calculer IDF
        doc_count = Counter()
        for conn in self.connaissances:
            for mot in conn['mots']:
                doc_count[mot] += 1
        N = len(self.connaissances)
        for mot, count in doc_count.items():
            self.idf[mot] = math.log((N + 1) / (count + 1)) + 1
        
        print(f"  {total} connaissances chargées depuis {len(domaines_charges)} domaines")
        for d, n in sorted(domaines_charges.items()):
            barre = "█" * (n // 500)
            print(f"    {d:<15s} {n:>5d} {barre}")
        
        return total
    
    def rechercher(self, question, top_k=3):
        """Recherche TF-IDF + cosinus 7D."""
        mots_q = set(question.lower().split())
        
        # Vecteur 7D de la question
        vq = np.zeros(7, dtype=np.float64)
        for mot in mots_q:
            for i, c in enumerate(mot):
                vq[(ord(c) + i) % 7] += H[(ord(c) + i) % 7] / H_sum
        nq = np.linalg.norm(vq)
        if nq > 0: vq /= nq
        
        scores = []
        for conn in self.connaissances:
            # Score TF-IDF
            tfidf = sum(self.idf.get(m, 1.0) for m in conn['mots'] if m in mots_q)
            
            # Score cosinus 7D
            vc = np.zeros(7, dtype=np.float64)
            for mot in conn['mots']:
                for i, c in enumerate(mot):
                    vc[(ord(c) + i) % 7] += H[(ord(c) + i) % 7] / H_sum
            nc = np.linalg.norm(vc)
            if nc > 0: vc /= nc
            cos_sim = max(0, float(np.dot(vq, vc)))
            
            score = tfidf * 5.0 + cos_sim * 2.0
            scores.append((conn['texte'], conn['domaine'], score))
        
        scores.sort(key=lambda x: x[2], reverse=True)
        return [(s[0], s[1]) for s in scores[:top_k]]


# ==============================================================================
# DEEPSEEK — Reformulation
# ==============================================================================

def reformuler_deepseek(question, faits, api_key=DEEPSEEK_API_KEY):
    """Envoie les faits à DeepSeek pour reformulation naturelle."""
    
    if not api_key:
        return None  # Mode dégradé
    
    faits_texte = "\n".join(f"Fait {i+1} : {f}" for i, f in enumerate(faits))
    
    prompt = f"""Tu es un assistant scientifique français, précis et pédagogue.

Voici des connaissances extraites de notre base :

{faits_texte}

Question : "{question}"

Consignes :
- Réponds en 3-5 phrases maximum, en français naturel
- Utilise UNIQUEMENT les faits ci-dessus
- Si aucun fait ne répond exactement, dis-le honnêtement
- Ajoute le contexte utile (date, scientifique, valeur)
- Ne mentionne PAS "les faits fournis" ou "la base de connaissances"
- Parle comme un expert qui connaît son sujet

Réponse :"""
    
    try:
        import urllib.request
        import urllib.error
        
        data = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Tu es un assistant scientifique français, précis et pédagogue."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 400,
        }).encode('utf-8')
        
        req = urllib.request.Request(DEEPSEEK_API_URL, data=data, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result["choices"][0]["message"]["content"].strip()
    
    except urllib.error.HTTPError as ex:
        return f"[API Error {ex.code}: {ex.reason}]"
    except Exception as ex:
        return f"[Erreur: {str(ex)[:100]}]"


# ==============================================================================
# TTS — Synthèse Vocale (via tts_server.py)
# ==============================================================================

def synthetiser_voix(texte, server_url=TTS_SERVER_URL):
    """Appelle le serveur TTS local pour vocaliser le texte."""
    if not server_url:
        return False
    
    try:
        import urllib.request
        import urllib.parse
        
        params = urllib.parse.urlencode({"text": texte, "voice": "fr-FR-DeniseNeural"})
        url = f"{server_url}/speak?{params}"
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            # Sauvegarder l'audio
            audio_data = resp.read()
            if audio_data and len(audio_data) > 100:
                # Sauvegarder dans un fichier temporaire
                import tempfile
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp.write(audio_data)
                tmp.close()
                print(f"  🔊 Audio sauvegardé : {tmp.name}")
                return True
        return False
    except Exception as ex:
        print(f"  ⚠️  TTS indisponible ({str(ex)[:50]})")
        return False


# ==============================================================================
# ASSISTANT HARMONIQUE VOCAL
# ==============================================================================

class AssistantHarmoniqueVocal:
    """
    Assistant complet : IA Harmonique → DeepSeek → TTS.
    
    Usage :
        assistant = AssistantHarmoniqueVocal()
        assistant.initialiser()
        reponse = assistant.repondre("quelle est la constante de Planck")
        print(reponse['reponse'])
    """
    
    def __init__(self):
        self.hologramme = HologrammeMinimal()
        self.initialise = False
        self.deepseek_dispo = bool(DEEPSEEK_API_KEY)
    
    def initialiser(self, max_connaissances=15000):
        """Charge les hologrammes et prépare l'assistant."""
        print("=" * 60)
        print("ASSISTANT HARMONIQUE VOCAL — Initialisation")
        print("=" * 60)
        print()
        print("Chargement des hologrammes...")
        n = self.hologramme.charger(max_total=max_connaissances)
        print()
        print(f"  Connaissances : {n}")
        print(f"  Vocabulaire IDF : {len(self.hologramme.idf)} mots")
        print(f"  DeepSeek : {'✅ Connecté' if self.deepseek_dispo else '⚠️  Mode dégradé (pas de clé API)'}")
        print(f"  TTS      : {'✅ localhost:5050' if TTS_SERVER_URL else '❌ Désactivé'}")
        print()
        self.initialise = True
        return n
    
    def repondre(self, question, vocal=False, debug=False):
        """
        Répond à une question via le pipeline complet.
        
        Args:
            question : str
            vocal    : si True, vocalise la réponse
            debug    : si True, affiche les détails intermédiaires
        
        Returns:
            dict avec 'reponse', 'faits', 'domaines', 'temps_ms'
        """
        if not self.initialise:
            return {"erreur": "Assistant non initialisé. Appeler initialiser() d'abord."}
        
        debut_total = time.time()
        
        # === ÉTAPE 1 : Recherche holographique ===
        t1 = time.time()
        resultats = self.hologramme.rechercher(question, top_k=3)
        faits = [r[0] for r in resultats]
        domaines = list(set(r[1] for r in resultats))
        temps_recherche = (time.time() - t1) * 1000
        
        if debug:
            print(f"  [DEBUG] Recherche : {temps_recherche:.0f}ms, {len(faits)} faits trouvés")
            for i, (f, d) in enumerate(resultats):
                print(f"    {i+1}. [{d}] {f[:100]}...")
        
        # === ÉTAPE 2 : Reformulation DeepSeek ===
        t2 = time.time()
        if self.deepseek_dispo and faits:
            reponse = reformuler_deepseek(question, faits)
            if reponse and not reponse.startswith("[") :
                pass  # Succès
            else:
                # Fallback : utiliser le meilleur fait
                reponse = faits[0] if faits else "[Aucune connaissance trouvée]"
        else:
            reponse = faits[0] if faits else "[Aucune connaissance trouvée]"
        temps_deepseek = (time.time() - t2) * 1000
        
        # === ÉTAPE 3 : Synthèse vocale ===
        if vocal:
            t3 = time.time()
            synthetiser_voix(reponse)
            temps_tts = (time.time() - t3) * 1000
        else:
            temps_tts = 0
        
        temps_total = (time.time() - debut_total) * 1000
        
        return {
            "question": question,
            "reponse": reponse,
            "faits": faits,
            "domaines": domaines,
            "temps_recherche_ms": temps_recherche,
            "temps_deepseek_ms": temps_deepseek,
            "temps_tts_ms": temps_tts,
            "temps_total_ms": temps_total,
        }


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo():
    print()
    assistant = AssistantHarmoniqueVocal()
    assistant.initialiser(max_connaissances=15000)
    
    questions = [
        "quelle est la constante de Planck",
        "qui a découvert la relativité",
        "comment fonctionne la photosynthèse",
        "quelle est la vitesse de la lumière",
        "qu'est-ce que le Big Bang",
    ]
    
    print("=" * 60)
    print("TEST DE L'ASSISTANT")
    print("=" * 60)
    print()
    
    for q in questions:
        print(f"❓ {q}")
        r = assistant.repondre(q, debug=True)
        print(f"💬 {r['reponse'][:250]}")
        print(f"   ⏱️  Recherche: {r['temps_recherche_ms']:.0f}ms | "
              f"DeepSeek: {r['temps_deepseek_ms']:.0f}ms | "
              f"Total: {r['temps_total_ms']:.0f}ms")
        print(f"   📚 Domaines: {', '.join(r['domaines'])}")
        print()
    
    print("=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    demo()