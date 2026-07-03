"""
Bootstrapper — Sevrage progressif du LLM
==========================================
Phase 1 : Le LLM extrait des triplets de textes → alimente le HarmonicModel
Phase 2 : Boucle feedback → si le modele est incertain, le LLM l'aide
Phase 3 : Metrique d'autonomie → mesure de la dependance au LLM

Principe : le HarmonicModel accumule sans jamais oublier.
Le LLM est une bequille temporaire, pas une dependance permanente.

Usage :
  boot = HarmonicBootstrapper()
  boot.ingest_text("Marie Curie a decouvert le radium en 1898")
  boot.ingest_corpus("data/corpus/")
  reponse = boot.ask_with_fallback("Qui a decouvert le radium ?")
  print(f\"Autonomie : {boot.autonomie:.0%}\")
"""

import sys, os, re, math, time, json, logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

log = logging.getLogger(__name__)

# Imports locaux
_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))
from harmonic_model import HarmonicModel, build_waves

# LLM (optionnel)
_LLM = None
_LLM_AVAILABLE = False
try:
    from llm.router import HarmonicLLM
    _LLM = HarmonicLLM()
    _LLM_AVAILABLE = _LLM.available_keys
except Exception:
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1 : EXTRACTEUR DE TRIPLETS
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_KEYWORDS = {
    'PHYSIQUE_FOND': ['physique', 'onde', 'lumiere', 'force', 'energie', 'gravite', 'quantique', 'atome', 'particule', 'relativite'],
    'PHYSIQUE_APPLI': ['technologie', 'machine', 'appareil', 'circuit', 'batterie', 'moteur', 'laser', 'internet', 'ordinateur'],
    'MATHS_PURES': ['mathematique', 'nombre', 'geometrie', 'algebre', 'theoreme', 'equation', 'logique', 'calcul'],
    'MATHS_APPLI': ['statistique', 'probabilite', 'algorithme', 'donnee', 'cryptographie', 'intelligence artificielle'],
    'BIOLOGIE': ['biologie', 'cellule', 'adn', 'gene', 'proteine', 'organe', 'espece', 'evolution', 'organisme'],
    'ECOLOGIE': ['ecologie', 'ecosysteme', 'climat', 'environnement', 'pollution', 'biodiversite'],
    'CONSCIENCE': ['conscience', 'esprit', 'pensee', 'perception', 'meditation', 'reve', 'cerveau'],
    'INTELLIGENCE': ['intelligence', 'raison', 'logique', 'apprentissage', 'memoire', 'intuition'],
    'EMOTION_POS': ['amour', 'joie', 'bonheur', 'paix', 'compassion', 'empathie', 'espoir'],
    'EMOTION_NEG': ['peur', 'tristesse', 'colere', 'stress', 'angoisse', 'souffrance'],
    'ASTRONOMIE': ['etoile', 'planete', 'galaxie', 'soleil', 'lune', 'astre', 'ciel'],
    'COSMOLOGIE': ['univers', 'cosmos', 'big bang', 'trou noir', 'expansion', 'multivers'],
    'PASSE': ['histoire', 'passe', 'origine', 'ancetre', 'tradition', 'archeologie'],
    'FUTUR': ['futur', 'avenir', 'progres', 'innovation', 'technologie', 'utopie'],
    'CULTURE': ['culture', 'art', 'musique', 'litterature', 'cinema', 'theatre', 'poesie'],
    'POLITIQUE': ['politique', 'democratie', 'justice', 'liberte', 'loi', 'etat', 'gouvernement'],
    'METAPHYSIQUE': ['philosophie', 'etre', 'existence', 'realite', 'verite', 'essence', 'neant'],
    'SPIRITUALITE': ['dieu', 'ame', 'spirituel', 'religion', 'foi', 'transcendance', 'sacre'],
    # Nouveaux secteurs — alignés avec qualitative_knowledge.py
    'CREATION': ['creation', 'creer', 'oeuvre', 'artiste', 'sculpture', 'peinture', 'dessin', 'architecture'],
    'EXPRESSION': ['expression', 'langage', 'parole', 'communication', 'ecriture', 'langue', 'discours'],
    'NATURE_ANIM': ['animal', 'mammifere', 'oiseau', 'poisson', 'insecte', 'reptile', 'faune'],
    'NATURE_VEGET': ['plante', 'arbre', 'fleur', 'foret', 'vegetal', 'flore', 'jardin'],
    'CORPS_ORGANES': ['corps', 'coeur', 'sang', 'poumon', 'foie', 'rein', 'cerveau', 'muscle', 'os'],
    'CORPS_SENS': ['vue', 'ouie', 'odorat', 'toucher', 'gout', 'oeil', 'oreille', 'peau'],
    # Secteurs pratiques (manquants cruciaux)
    'GEOGRAPHIE': ['geographie', 'pays', 'capitale', 'continent', 'montagne', 'fleuve', 'ocean', 'mer', 'ville', 'region', 'frontiere'],
    'SANTE': ['sante', 'maladie', 'medecin', 'medicament', 'vaccin', 'virus', 'bacterie', 'hopital', 'chirurgie', 'symptome'],
    'ECONOMIE': ['economie', 'marche', 'commerce', 'monnaie', 'banque', 'inflation', 'pib', 'croissance', 'entreprise', 'finance'],
}

def detect_sector(text: str) -> str:
    """Detecte le secteur semantique d'un texte (v2 — word boundaries)."""
    text_lower = text.lower()
    scores = {}
    for sector, keywords in SECTOR_KEYWORDS.items():
        score = 0
        for kw in keywords:
            # Utiliser word boundaries (\b) pour éviter les sous-chaînes
            # Ex: "onde" ne matchera plus "monde"
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                score += 1
        if score > 0:
            scores[sector] = score
    if scores:
        # En cas d'égalité, prendre le secteur avec le moins de keywords
        # (plus spécifique) plutôt que le premier dans le dict
        max_score = max(scores.values())
        best = [(s, len(SECTOR_KEYWORDS[s])) for s, sc in scores.items() if sc == max_score]
        best.sort(key=lambda x: x[1])  # trier par nombre de keywords (moins = plus spécifique)
        return best[0][0]
    return "GENERAL"


def extract_triples_simple(text: str) -> List[Tuple[str, str, str, str]]:
    """
    Extraction ROBUSTE de triplets par DECOUPAGE puis PATTERNS.
    
    Deux passes :
      1. Decouper le texte en segments (par ponctuation)
      2. Appliquer des patterns simples sur chaque segment
    
    Gere les incidentes Wikipedia (ne le..., mort le...).
    """
    triples = []
    secteur = detect_sector(text)
    
    # Nettoyer les incidentes Wikipedia : "X, né le..., est Y" → "X est Y"
    text_clean = re.sub(r',\s*n[eé]\s+le\s+[^,]+', '', text)
    text_clean = re.sub(r',\s*mort\s+le\s+[^,]+', '', text_clean)
    text_clean = re.sub(r'\([^)]*\)', '', text_clean)  # parentheses
    # Virgule avant "est" : "X, est Y" → "X est Y"
    text_clean = re.sub(r',\s+(est\s+(?:un|une|le|la|les|l)\s)', r' \1', text_clean)
    
    # Decouper en segments
    segments = re.split(r'[.;]', text_clean)
    segments = [s.strip() for s in segments if len(s.strip()) > 10]
    segments.append(text_clean)  # aussi le texte complet nettoye
    
    # Stopwords a filtrer
    stop_subjects = {'il', 'elle', 'on', 'cela', 'ceci', 'cet', 'cette', 'ces',
                     'qui', 'que', 'quoi', 'dont', 'tout', 'tous', 'toute', 'toutes',
                     'rien', 'personne', 'plusieurs', 'certains'}
    
    for segment in segments:
        seg = segment.strip()
        if len(seg) < 15:
            continue
        
        # Pattern 1: "X est un/une Y" ou "X is a/an Y" (definition)
        m = re.match(r'([A-Za-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-Za-zà-ÿ][a-zà-ÿ]{1,})?)\s+(?:est|is)\s+(?:un|une|le|la|les|l|a|an|the)\s+(.+)', seg, re.IGNORECASE)
        if not m:
            # Pattern 1b: "X est d'origine/de/du Y"
            m = re.match(r'([A-Za-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-Za-zà-ÿ][a-zà-ÿ]{1,})?)\s+est\s+(d|de|du|des)\s+(.+)', seg, re.IGNORECASE)
        if m:
            sujet = m.group(1).strip().lower()
            objet = m.group(2).strip(' .,;').lower() if len(m.groups()) >= 3 else m.group(2).strip(' .,;').lower()
            if len(m.groups()) >= 3 and m.group(2) in ('d','de','du','des'):
                objet = m.group(3).strip(' .,;').lower()
            if sujet not in stop_subjects and len(sujet) >= 2 and len(objet) >= 5:
                triples.append((sujet, "est", objet, secteur))
                continue
        
        # Pattern 2: "X a decouvert/invente/cree Y" (decouverte)
        m = re.match(r'([A-Z][a-zà-ÿ]+(?:\s[A-Z][a-zà-ÿ]+)?)\s+a\s+(decouvert|invente|cree|fonde|developpe|publie|formule|introduit)\s+(.+)', seg, re.IGNORECASE)
        if m:
            sujet, verbe, objet = m.group(1).strip().lower(), m.group(2), m.group(3).strip(' .,;').lower()
            if len(sujet) >= 3 and len(objet) >= 5:
                triples.append((sujet, f"a {verbe}", objet, secteur))
                continue
        
        # Pattern 3: "X a ete V par Y" — plus flexible
        m = re.search(r'(.+?)\s+a\s+ete\s+(decouvert|invente|cree|fonde)\s+par\s+(.+)', seg, re.IGNORECASE)
        if m:
            objet, verbe, suite = m.group(1).strip(' .,;').lower(), m.group(2), m.group(3).strip(' .,;').lower()
            if len(objet) >= 5:
                # Extraire un sujet potentiel de la suite
                sujet_words = [w for w in suite.split() if w[0].isupper() and len(w) > 2]
                sujet = sujet_words[0].lower() if sujet_words else suite.split()[0].lower() if suite.split() else 'inconnu'
                triples.append((sujet, f"a ete {verbe} par", objet, secteur))
                continue
        
        # Pattern 4: "X se compose de / comprend Y"
        m = re.match(r'([A-Za-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-Za-zà-ÿ][a-zà-ÿ]{1,})?)\s+(?:se compose de|est compose de|comprend|contient)\s+(.+)', seg, re.IGNORECASE)
        if m:
            sujet, objet = m.group(1).strip().lower(), m.group(2).strip(' .,;').lower()
            if sujet not in stop_subjects and len(sujet) >= 2 and len(objet) >= 5:
                triples.append((sujet, "comprend", objet, secteur))
                continue
    
    return triples


def extract_triples_llm(text: str) -> List[Tuple[str, str, str, str]]:
    """
    Extraction de triplets via LLM (si disponible).
    Le LLM recoit le texte et doit retourner des triplets structures.
    """
    if not _LLM_AVAILABLE:
        return extract_triples_simple(text)
    
    prompt = f"""Extrait TOUS les faits du texte ci-dessous sous forme de triplets.
Format EXACT : sujet | relation | objet
Un triplet par ligne. Sujet et objet en minuscules. Max 10 mots.

Texte : {text[:500]}

Triplets :"""
    
    try:
        resp = _LLM.generate(prompt, category="factual")
        lines = resp.content.strip().split('\n')
        triples = []
        for line in lines:
            parts = line.split('|')
            if len(parts) >= 3:
                s = parts[0].strip().lower()
                r = parts[1].strip().lower()
                o = parts[2].strip().lower()
                if len(s) > 1 and len(o) > 2:
                    sec = detect_sector(f"{s} {r} {o}")
                    triples.append((s, r, o, sec))
        return triples if triples else extract_triples_simple(text)
    except Exception:
        return extract_triples_simple(text)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 : BOUCLE FEEDBACK
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicBootstrapper:
    """
    Orchestrateur du sevrage progressif.
    
    Le LLM est utilise comme EXTRACTEUR de connaissances, pas comme GENERATEUR.
    Le HarmonicModel est la BIBLIOTHEQUE qui accumule sans jamais oublier.
    
    Metriques :
      - autonomie : proportion de questions resolues sans le LLM
      - couverture : nombre de faits dans la base
      - confiance : score moyen de matching
    """
    
    def __init__(self, use_memory: bool = True, model=None):
        """
        Args:
            use_memory: activer la mémoire holographique
            model: modèle HarmonicModel existant (si None, en crée un nouveau)
        """
        if model is not None:
            self.model = model
        else:
            self.model = HarmonicModel(use_memory=use_memory)
        self._autonomie_history = []
        self._llm_calls = 0
        self._total_queries = 0
    
    def ingest_text(self, text: str, use_llm: bool = False):
        """
        Ingere un texte : extrait les triplets et les ajoute au modele.
        
        Args:
            text: texte a analyser
            use_llm: utiliser le LLM pour l'extraction (plus precis mais plus lent)
        """
        if use_llm:
            triples = extract_triples_llm(text)
        else:
            triples = extract_triples_simple(text)
        
        for s, r, o, sec in triples:
            self.model.learn(s, r, o, sec)
        
        return len(triples)
    
    def ingest_corpus(self, corpus_dir: str, max_files: int = 10):
        """Ingere tout un repertoire de textes."""
        corpus_path = Path(corpus_dir)
        total = 0
        for path in list(corpus_path.glob("*.txt"))[:max_files]:
            if path.stat().st_size < 100:
                continue
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if len(line) > 30:
                        n = self.ingest_text(line)
                        total += n
        return total
    
    def _llm_fallback(self, question: str) -> Optional[str]:
        """Appelle le LLM pour obtenir une réponse. Retourne None si indisponible."""
        if not _LLM_AVAILABLE:
            return None
        try:
            import threading
            result = [None]
            def _call():
                try:
                    self._llm_calls += 1
                    self._autonomie_history.append(False)
                    llm_resp = _LLM.generate(question, category="factual")
                    result[0] = llm_resp.content.strip() or None
                except Exception:
                    result[0] = None
            
            thread = threading.Thread(target=_call, daemon=True)
            thread.start()
            thread.join(timeout=15)  # Timeout de 15 secondes
            if thread.is_alive():
                log.warning(f"LLM fallback timeout après 15s pour: {question[:80]}")
                return None
            return result[0]
        except Exception:
            return None
    
    def ask_with_fallback(self, question: str) -> Tuple[str, bool]:
        """
        Pose une question. Si le modele ne trouve pas de reponse,
        utilise le LLM en fallback ET APPREND de sa reponse.
        
        Returns:
            (reponse, autonomie: True si le modele a trouve seul)
        """
        self._total_queries += 1
        
        # Essayer le modele harmonique d'abord
        response = self.model.ask(question)
        
        # Vérifier la confiance (overlap lexical + phrases faibles)
        low_confidence = any(phrase in response.lower() for phrase in [
            'je ne connais pas', 'je ne trouve pas', 'pas de resonance',
            'connais pas assez'
        ])
        
        # Vérification supplémentaire : chevauchement lexical des SUJETS
        if not low_confidence:
            # Mots-outils à ignorer (verbes communs, prépositions, etc.)
            _ignore_words = {'le', 'la', 'les', 'de', 'des', 'un', 'une', 'et', 'est', 'a',
                           'que', 'qui', 'quoi', 'dans', 'sur', 'pour', 'avec', 'par',
                           'the', 'a', 'an', 'is', 'are', 'of', 'in', 'on', 'at', 'to',
                           'what', 'who', 'how', 'why', 'when', 'where', 'which',
                           'invente', 'cree', 'decouvert', 'fonctionne', 'explique', 'trouve',
                           'fait', 'dit', 'donne', 'utilise', 'appelle', 'signifie',
                           'comment', 'pourquoi', 'quand', 'combien'}
            q_words = set(w.strip('.,!?;:()[]{}') for w in question.lower().split()
                         if len(w) > 2 and w not in _ignore_words)
            r_words = set(w.strip('.,!?;:()[]{}') for w in response.lower().split() if len(w) > 2)
            subject_overlap = q_words & r_words
            # Si moins de la moitié des mots-sujets apparaissent → faible
            # Pour les questions courtes (1-2 mots-sujets), exiger 100%
            min_required = max(1, len(q_words) * 0.6) if len(q_words) <= 2 else len(q_words) * 0.5
            if len(q_words) > 0 and len(subject_overlap) < min_required:
                low_confidence = True
        
        if not low_confidence:
            self._autonomie_history.append(True)
            return response, True
        
        # Fallback LLM
        if _LLM_AVAILABLE:
            self._llm_calls += 1
            try:
                llm_resp = _LLM.generate(question, category="factual")
                llm_text = llm_resp.content.strip()
                
                # APPRENDRE de la reponse du LLM
                triples = extract_triples_simple(llm_text)
                for s, r, o, sec in triples:
                    self.model.knowledge_base.append((s, r, o, sec))
                if triples:
                    # Reconstruire les ondes avec les nouveaux faits
                    if hasattr(self.model, 'rebuild_waves'):
                        self.model.rebuild_waves()
                    else:
                        self.model.kx, self.model.ky, self.model.w2i = build_waves(self.model.knowledge_base)
                
                self._autonomie_history.append(False)
                return llm_text, False
            except Exception:
                pass
        
        self._autonomie_history.append(False)
        return response, False
    
    @property
    def autonomie(self) -> float:
        """Proportion de questions resolues sans le LLM (moyenne glissante)."""
        if not self._autonomie_history:
            return 1.0
        # Moyenne des 50 dernieres requetes
        recent = self._autonomie_history[-50:]
        return sum(recent) / len(recent)
    
    @property
    def stats(self) -> dict:
        return {
            'faits': len(self.model.knowledge_base),
            'vocab': self.model.vocabulary_size,
            'experiences': self.model.experience_count,
            'autonomie': round(self.autonomie * 100, 1),
            'llm_calls': self._llm_calls,
            'total_queries': self._total_queries,
            'sevrage': round((1 - self._llm_calls / max(self._total_queries, 1)) * 100, 1),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demonstration du bootstrapper."""
    print("=" * 60)
    print("HARMONIC BOOTSTRAPPER — Sevrage progressif du LLM")
    print("=" * 60)
    
    boot = HarmonicBootstrapper(use_memory=True)
    
    # Phase 1 : Peuplement
    print("\n[Phase 1] Peuplement initial...")
    textes = [
        "Albert Einstein a decouvert la relativite en 1905.",
        "La relativite generale decrit la gravitation comme courbure de l espace temps.",
        "Max Planck a introduit le quantum d action en 1900.",
        "Marie Curie a decouvert le radium et le polonium.",
        "La lumiere est une onde electromagnetique se deplacant a 300000 km/s.",
        "L ocean couvre 70% de la surface de la Terre.",
        "Le coeur pompe le sang dans tout le corps humain.",
        "La musique est l art des sons et du silence.",
    ]
    for t in textes:
        n = boot.ingest_text(t)
        if n > 0:
            s, r, o, sec = extract_triples_simple(t)[0] if extract_triples_simple(t) else ('?','?','?','?')
            print(f"  + {n} triplet: {s} | {r} | {o}")
    
    print(f"\n  Base : {len(boot.model.knowledge_base)} faits")
    
    # Phase 2 : Questions avec fallback
    print("\n[Phase 2] Questions (autonomie + fallback)...")
    questions = [
        "Qui a decouvert la relativite ?",
        "Qu est ce que la lumiere ?",
        "Quelle est la capitale du Bresil ?",  # Pas dans la base → fallback LLM
        "Comment fonctionne le coeur ?",
        "Qui a decouvert le quantum d action ?",
    ]
    
    for q in questions:
        response, autonomous = boot.ask_with_fallback(q)
        status = "AUTONOME" if autonomous else "LLM FALLBACK"
        print(f"  [{status}] >> {q}")
        print(f"           << {response[:120]}")
    
    print(f"\n  Autonomie : {boot.autonomie:.0%}")
    print(f"  Stats : {boot.stats}")


if __name__ == '__main__':
    demo()
