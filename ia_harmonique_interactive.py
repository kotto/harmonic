#!/usr/bin/env python3
r"""
IA HARMONIQUE INTERACTIVE — Templates + Mémoire + Personnalité + Proactivité
==============================================================================
Couche d'expression élégante au-dessus du moteur de raisonnement ondulatoire.

Architecture :
  1. MoteurUniversel → raisonnement vérifié (47/47, 100%)
  2. SystemeTemplates → explications en langage naturel
  3. DeepSeek API → fallback pour réponses complexes
  4. MemoireSession → Ψ_conversation évolutive
  5. Personnalite → style configurable
  6. Proactivite → suggestions de questions

Usage :
  python ia_harmonique_interactive.py
  python ia_harmonique_interactive.py --personnalite pedagogique
  python ia_harmonique_interactive.py --personnalite concis
"""

import sys, os, math, time, json, re
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))
sys.path.insert(0, os.path.dirname(__file__))

from moteur_raisonnement_universel import MoteurUniversel, detecter_type_probleme


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PERSONNALITÉ
# ═══════════════════════════════════════════════════════════════════════════════

class Personnalite:
    """Style d'expression configurable."""
    
    STYLES = {
        "pedagogique": {
            "intro": "📐 **Raisonnement** : ",
            "explication": "J'ai résolu cela en {methode}.\n\n"
                          "✨ **Vérification** : j'ai confirmé la réponse par interférence "
                          "d'ondes (cos θ = {confiance:.3f}).\n\n"
                          "📊 **Trace** : {trace}",
            "conclusion": "\n\n💡 **Réponse** : **{reponse}**",
            "confiance_haute": " (confiance très élevée)",
            "confiance_basse": " (à vérifier)",
            "signature": "\n\n---\n*IA Harmonique — Raisonnement par interférence d'ondes*",
            "emoji": True,
        },
        "concis": {
            "intro": "",
            "explication": "{reponse}",
            "conclusion": "",
            "confiance_haute": "",
            "confiance_basse": " (incertain)",
            "signature": "",
            "emoji": False,
        },
        "scientifique": {
            "intro": "[Raisonnement] ",
            "explication": "Méthode : {methode}. Trace : {trace}. Vérification : cos θ = {confiance:.3f}.",
            "conclusion": " Réponse : {reponse}.",
            "confiance_haute": " Confiance : élevée.",
            "confiance_basse": " Confiance : faible.",
            "signature": "",
            "emoji": False,
        },
        "poetique": {
            "intro": "🌊 Les ondes ont parlé... ",
            "explication": "Par la résonance de {methode}, les interférences m'ont révélé "
                          "que {trace}. L'univers a confirmé : cos θ = {confiance:.3f}.",
            "conclusion": "\n\n✨ Ainsi, la réponse est **{reponse}**.",
            "confiance_haute": " Les ondes sont en parfaite harmonie.",
            "confiance_basse": " Les ondes murmurent, sans certitude.",
            "signature": "\n\n~ 🌊 ~",
            "emoji": True,
        },
    }
    
    def __init__(self, style="pedagogique"):
        self.style = style
        self.template = self.STYLES.get(style, self.STYLES["pedagogique"])
    
    def formater(self, reponse, type_prob, confiance, trace, methode=""):
        """Formate une réponse selon le style de personnalité."""
        t = self.template
        
        if confiance > 0.9:
            conf_note = t["confiance_haute"]
        else:
            conf_note = t["confiance_basse"]
        
        resultat = t["intro"]
        resultat += t["explication"].format(
            reponse=reponse,
            methode=methode or type_prob,
            trace=trace,
            confiance=confiance,
        )
        resultat += conf_note
        resultat += t["conclusion"].format(reponse=reponse)
        resultat += t["signature"]
        
        return resultat


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SYSTÈME DE TEMPLATES INTELLIGENTS
# ═══════════════════════════════════════════════════════════════════════════════

class SystemeTemplates:
    """Génère des explications en langage naturel à partir de la trace."""
    
    @staticmethod
    def expliquer_addition(a, b, c, trace=""):
        methodes = [
            f"J'ai additionné {a} et {b}",
            f"J'ai superposé les ondes Ψ_{a} et Ψ_{b} — leur produit donne Ψ_{c}",
            f"Par interférence constructive, {a} + {b} émerge naturellement",
        ]
        return methodes[hash(str(a) + str(b)) % len(methodes)]
    
    @staticmethod
    def expliquer_soustraction(a, b, c, trace=""):
        return f"J'ai soustrait {b} de {a} — l'onde résultante Ψ_{a} · conj(Ψ_{b}) = Ψ_{c}"
    
    @staticmethod
    def expliquer_multiplication(a, b, c, trace=""):
        return f"Le produit de {a} et {b} est {c}"
    
    @staticmethod
    def expliquer_carre(a, c, trace=""):
        return f"Le carré de {a} est {c} — j'ai vérifié par (Ψ_{a})^{a} = Ψ_{c}"
    
    @staticmethod
    def expliquer_racine(n, r, trace=""):
        return f"La racine carrée de {n} est {r} — car {r}² = {n}"
    
    @staticmethod
    def expliquer_equation(type_eq, x, b, c, trace=""):
        if type_eq == 'equation_lineaire':
            return f"J'ai résolu l'équation x + {b} = {c} → x = {c} - {b} = {x}"
        elif type_eq == 'equation_quadratique':
            return f"J'ai résolu x² = {c} → x = √{c} = {x}"
        return f"Solution : x = {x}"
    
    @staticmethod
    def expliquer_pythagore(a, b, c, trace=""):
        return (f"Dans un triangle rectangle de côtés {a} et {b}, "
                f"l'hypoténuse est c = √({a}² + {b}²) = √({a*a} + {b*b}) = √{a*a + b*b} = {c}")
    
    @staticmethod
    def expliquer_somme(a, b, c, trace=""):
        return f"La somme de {a} et {b} est {c}"
    
    @staticmethod
    def expliquer_produit(a, b, c, trace=""):
        return f"Le produit de {a} et {b} est {c}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MÉMOIRE DE SESSION (Ψ_conversation)
# ═══════════════════════════════════════════════════════════════════════════════

class MemoireSession:
    """
    Mémoire de session basée sur la superposition d'ondes.
    Ψ_session = Σ w_k · Ψ_{question_k}
    
    où w_k = 0.8^{N-k} (décroissance exponentielle — les questions
    récentes pèsent plus que les anciennes).
    """
    
    def __init__(self, grid_size=256, decay=0.8):
        self.GRID = grid_size
        self.decay = decay
        self.historique = []  # [(question, reponse, type_prob, trace), ...]
        self.psi_session = np.zeros(grid_size, dtype=np.complex128)
    
    def ajouter(self, question, reponse, type_prob, trace):
        """Ajoute un échange à la mémoire."""
        self.historique.append({
            "question": question,
            "reponse": reponse,
            "type": type_prob,
            "trace": trace,
        })
        
        # Encodage simple de la question en onde
        psi_q = self._encoder_question(question)
        
        # Superposition avec décroissance
        self.psi_session = self.psi_session * self.decay + psi_q * (1 - self.decay)
    
    def _encoder_question(self, question):
        """Encode une question en onde via SHA-256."""
        import hashlib
        h = hashlib.sha256(question.encode()[:200]).hexdigest()
        n = (int(h[:16], 16) % (self.GRID // 2)) + 1
        x = np.linspace(0, 1.0, self.GRID)
        k0 = PHI * 2 * PI
        return np.exp(1j * n * k0 * x)
    
    def dernier_contexte(self):
        """Retourne les 3 derniers échanges pour le contexte."""
        return self.historique[-3:] if self.historique else []
    
    def resume(self):
        """Résumé de la session."""
        if not self.historique:
            return "Aucun échange pour l'instant."
        
        lignes = [f"📝 **Session** ({len(self.historique)} échanges) :"]
        for i, h in enumerate(self.historique[-5:]):
            lignes.append(f"  {i+1}. Q: {h['question'][:50]}... → R: {h['reponse']}")
        return "\n".join(lignes)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PROACTIVITÉ
# ═══════════════════════════════════════════════════════════════════════════════

class Proactivite:
    """Suggère des questions de suivi basées sur le contexte."""
    
    SUGGESTIONS = {
        "addition": [
            "Et si on soustrait ces nombres ?",
            "Veux-tu que je calcule aussi leur produit ?",
            "Et le carré du résultat ?",
        ],
        "soustraction": [
            "Et l'addition de ces nombres ?",
            "Veux-tu vérifier avec l'addition ?",
        ],
        "multiplication": [
            "Et la division du résultat ?",
            "Veux-tu le carré de ce résultat ?",
        ],
        "carre": [
            "Et la racine carrée du résultat ?",
            "Veux-tu le cube de ce nombre ?",
        ],
        "racine": [
            "Et le carré de cette racine ?",
            "Veux-tu vérifier que le carré redonne le nombre d'origine ?",
        ],
        "pythagore": [
            "Veux-tu vérifier le périmètre de ce triangle ?",
            "Et l'aire de ce triangle rectangle ?",
            "Veux-tu tester avec un autre triplet ?",
        ],
        "equation": [
            "Veux-tu résoudre une autre équation ?",
            "Et si on vérifie la solution en remplaçant x ?",
        ],
    }
    
    GENERIQUES = [
        "Tu peux me demander n'importe quel calcul.",
        "Essaie une équation ! Exemple : x + 5 = 12",
        "Je peux aussi calculer des hypoténuses.",
    ]
    
    def suggerer(self, type_prob, question=""):
        """Retourne une suggestion de follow-up."""
        import random
        suggestions = self.SUGGESTIONS.get(type_prob, self.GENERIQUES)
        return random.choice(suggestions)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DEEPSEEK API (fallback pour réponses complexes)
# ═══════════════════════════════════════════════════════════════════════════════

class DeepSeekFallback:
    """
    Utilise DeepSeek API pour embellir les réponses quand le template ne suffit pas.
    Ne RAISONNE pas — ne fait que de la MISE EN FORME.
    """
    
    def __init__(self, api_key=None, enabled=False):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.enabled = enabled and bool(self.api_key)
    
    def embellir(self, question, reponse, trace, personnalite="pedagogique"):
        """
        Embellit une réponse avec DeepSeek.
        Le prompt contient déjà la réponse vérifiée — DeepSeek ne fait que reformuler.
        """
        if not self.enabled:
            return self._template_embellir(question, reponse, trace, personnalite)
        
        try:
            import requests
            prompt = (
                f"Tu es une IA harmonique qui raisonne par interférence d'ondes. "
                f"La réponse vérifiée à la question '{question}' est : {reponse}. "
                f"Trace du raisonnement : {trace}. "
                f"Explique cette réponse de manière {personnalite}, en mentionnant "
                f"que la vérification a été faite par interférence d'ondes. "
                f"Sois concise (2-3 phrases maximum). "
                f"NE RAISONNE PAS — la réponse est déjà vérifiée. Contente-toi de l'exprimer."
            )
            
            # Tentative d'appel API
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.3,
                },
                timeout=5
            )
            
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except:
            pass
        
        return self._template_embellir(question, reponse, trace, personnalite)
    
    def _template_embellir(self, question, reponse, trace, personnalite):
        """Fallback local si l'API n'est pas disponible."""
        return (f"La réponse à « {question} » est **{reponse}**. "
                f"Ce résultat a été vérifié par interférence d'ondes "
                f"(trace : {trace[:80]}...).")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. IA HARMONIQUE INTERACTIVE
# ═══════════════════════════════════════════════════════════════════════════════

class IAHarmoniqueInteractive:
    """
    IA harmonique interactive complète.
    Combine : raisonnement + templates + mémoire + personnalité + proactivité.
    """
    
    def __init__(self, personnalite="pedagogique", deepseek_key=None):
        # Moteur de raisonnement
        corpus = None
        if os.path.exists("corpus_mathematique.json"):
            with open("corpus_mathematique.json", 'r', encoding='utf-8') as f:
                corpus = json.load(f)
        
        self.moteur = MoteurUniversel(corpus)
        if corpus:
            print("  Construction du moteur de raisonnement...")
            self.moteur.build()
        
        # Couches d'interaction
        self.personnalite = Personnalite(personnalite)
        self.templates = SystemeTemplates()
        self.memoire = MemoireSession()
        self.proactivite = Proactivite()
        self.deepseek = DeepSeekFallback(api_key=deepseek_key, enabled=bool(deepseek_key))
        
        self.nom = "IA Harmonique"
    
    def traiter(self, question):
        """Traite une question et retourne une réponse complète."""
        # ── RAISONNEMENT ──
        reponse, type_prob, confiance, trace = self.moteur.resoudre(question)
        
        if reponse is None and confiance < 0.5:
            return self._reponse_non_trouvee(question)
        
        # ── GÉNÉRATION DE L'EXPLICATION ──
        explication = self._generer_explication(reponse, type_prob, confiance, trace, question)
        
        # ── FORMATAGE SELON PERSONNALITÉ ──
        reponse_formatee = self.personnalite.formater(
            reponse, type_prob, confiance, trace, explication
        )
        
        # ── MÉMOIRE ──
        self.memoire.ajouter(question, reponse, type_prob, trace)
        
        # ── PROACTIVITÉ ──
        suggestion = self.proactivite.suggerer(type_prob, question)
        
        return {
            "reponse": reponse,
            "type": type_prob,
            "confiance": confiance,
            "trace": trace,
            "explication": explication,
            "reponse_formatee": reponse_formatee,
            "suggestion": suggestion,
        }
    
    def _generer_explication(self, reponse, type_prob, confiance, trace, question):
        """Génère une explication en langage naturel."""
        # Extraire les nombres de la trace
        nombres = re.findall(r'\d+', trace)
        nums = [int(n) for n in nombres] if nombres else []
        
        if type_prob in ('addition', 'somme') and len(nums) >= 3:
            return self.templates.expliquer_addition(nums[0], nums[1], nums[2], trace)
        elif type_prob == 'soustraction' and len(nums) >= 3:
            return self.templates.expliquer_soustraction(nums[0], nums[1], nums[2], trace)
        elif type_prob == 'multiplication' and len(nums) >= 3:
            return self.templates.expliquer_multiplication(nums[0], nums[1], nums[2], trace)
        elif type_prob == 'carre' and len(nums) >= 2:
            return self.templates.expliquer_carre(nums[0], nums[1], trace)
        elif type_prob == 'racine' and len(nums) >= 2:
            return self.templates.expliquer_racine(nums[0], nums[1], trace)
        elif type_prob == 'pythagore' and len(nums) >= 3:
            return self.templates.expliquer_pythagore(nums[0], nums[1], nums[2], trace)
        elif 'equation' in type_prob and len(nums) >= 2:
            return self.templates.expliquer_equation(type_prob, reponse, nums[0], nums[-1] if len(nums) > 1 else 0, trace)
        elif type_prob == 'produit' and len(nums) >= 3:
            return self.templates.expliquer_produit(nums[0], nums[1], nums[2], trace)
        
        return f"Résultat : {reponse} (vérifié par interférence d'ondes)"
    
    def _reponse_non_trouvee(self, question):
        """Réponse quand le moteur ne trouve pas."""
        return {
            "reponse": None,
            "type": "inconnu",
            "confiance": 0.0,
            "trace": "aucune",
            "explication": "Je n'ai pas pu résoudre cette question.",
            "reponse_formatee": (
                "🤔 Je n'ai pas pu résoudre cette question avec mes capacités actuelles.\n\n"
                "Je suis spécialisé dans :\n"
                "• L'arithmétique (+, -, ×, carrés, racines)\n"
                "• L'algèbre (équations x+b=c, x²=n)\n"
                "• La géométrie (théorème de Pythagore)\n\n"
                "Essaie de reformuler ta question dans un de ces domaines !"
            ),
            "suggestion": "Essaie par exemple : '3 + 4 = ?' ou 'x + 5 = 12'",
        }
    
    def afficher_reponse(self, resultat):
        """Affiche la réponse formatée dans le terminal."""
        print(f"\n{resultat['reponse_formatee']}")
        if resultat.get('suggestion'):
            print(f"\n💭 {resultat['suggestion']}")
    
    def session_info(self):
        """Affiche les informations de session."""
        return self.memoire.resume()


# ═══════════════════════════════════════════════════════════════════════════════
# 7. SERVEUR INTERACTIF (terminal)
# ═══════════════════════════════════════════════════════════════════════════════

def boucle_interactive(ia, personnalite_nom="pedagogique"):
    """Boucle interactive dans le terminal."""
    print(f"""
╔══════════════════════════════════════════════════════╗
║        🌊 IA HARMONIQUE INTERACTIVE 🌊               ║
║                                                      ║
║  Raisonnement par interférence d'ondes                ║
║  Personnalité : {personnalite_nom:<38s}║
║                                                      ║
║  Commandes spéciales :                                ║
║    /aide     — cette aide                             ║
║    /session  — résumé de la session                   ║
║    /style XX — changer de style (pedagogique,         ║
║               concis, scientifique, poetique)         ║
║    /demo     — démonstration rapide                   ║
║    /quit     — quitter                                ║
║                                                      ║
║  Exemples :                                           ║
║    3 + 4 = ?                                          ║
║    x + 3 = 7                                          ║
║    hypoténuse du triangle 3 et 4                      ║
║    carré de 12                                        ║
╚══════════════════════════════════════════════════════════╝
""")
    
    while True:
        try:
            question = input("\n🧑 Vous > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Au revoir ! Les ondes continuent de résonner...\n")
            break
        
        if not question:
            continue
        
        if question.lower() in ('/quit', '/q', 'quit', 'exit'):
            print("\n👋 Au revoir ! Les ondes continuent de résonner...\n")
            break
        
        if question.lower() in ('/aide', '/help', '/?'):
            print("""
  Commandes disponibles :
    /aide     — cette aide
    /session  — résumé des échanges précédents
    /style XX — changer de personnalité
    /demo     — démonstration rapide de 5 questions
    /quit     — quitter
  
  Styles disponibles : pedagogique, concis, scientifique, poetique
            """)
            continue
        
        if question.lower() == '/session':
            print(f"\n{ia.session_info()}")
            continue
        
        if question.lower().startswith('/style '):
            nouveau_style = question.split(maxsplit=1)[1].strip().lower()
            if nouveau_style in Personnalite.STYLES:
                ia.personnalite = Personnalite(nouveau_style)
                print(f"\n  ✅ Style changé pour : **{nouveau_style}**")
            else:
                print(f"\n  ❌ Style inconnu. Disponibles : {', '.join(Personnalite.STYLES.keys())}")
            continue
        
        if question.lower() == '/demo':
            print("\n  🎯 DÉMONSTRATION RAPIDE :\n")
            for q in ["3 + 4 = ?", "x + 3 = 7", "carré de 12", "√225 = ?", "hypoténuse du triangle 3 et 4"]:
                resultat = ia.traiter(q)
                print(f"  Q: {q}")
                print(f"  R: {resultat['reponse']} ({resultat['type']}, confiance={resultat['confiance']:.3f})")
                print()
            continue
        
        # ── TRAITEMENT ──
        resultat = ia.traiter(question)
        ia.afficher_reponse(resultat)


if __name__ == "__main__":
    import argparse
    
    p = argparse.ArgumentParser(description="IA Harmonique Interactive")
    p.add_argument("--personnalite", type=str, default="pedagogique",
                   choices=["pedagogique", "concis", "scientifique", "poetique"],
                   help="Style d'expression")
    p.add_argument("--deepseek-key", type=str, default=None,
                   help="Clé API DeepSeek (optionnelle)")
    p.add_argument("--demo", action="store_true",
                   help="Lancer une démonstration rapide")
    args = p.parse_args()
    
    # Initialisation
    print("\n🌊 Initialisation de l'IA Harmonique Interactive...\n")
    ia = IAHarmoniqueInteractive(
        personnalite=args.personnalite,
        deepseek_key=args.deepseek_key,
    )
    
    if args.demo:
        print("\n  🎯 DÉMONSTRATION RAPIDE :\n")
        for q in ["3 + 4 = ?", "x + 3 = 7", "carré de 12", "√225 = ?", "hypoténuse du triangle 3 et 4"]:
            resultat = ia.traiter(q)
            ia.afficher_reponse(resultat)
        print("\n" + "=" * 60)
    
    boucle_interactive(ia, args.personnalite)