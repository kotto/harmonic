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
    """Compatibilité : appelle extract_triples_enhanced()."""
    return extract_triples_enhanced(text)


def extract_triples_enhanced(text: str) -> List[Tuple[str, str, str, str]]:
    """
    Extraction ENRICHIE de triplets — 25+ patterns regex.
    
    Groupes de patterns :
      1. Définitions (est un/une, signifie, is a/an, means)
      2. Découverte/création (a découvert, a inventé, discovered, created)
      3. Voix passive (a été V par, was V by)
      4. Composition (se compose de, contient, consists of)
      5. Relations numériques (a X habitants, mesure X m)
      6. Relations temporelles (a eu lieu en, a duré X ans)
      7. Relations causales (cause, entraîne, provoque)
      8. Relations de localisation (se trouve à, is located in)
      9. Relations d'appartenance (appartient à, fait partie de)
      10. Relations comparatives (est plus grand que)
    
    Returns:
        Liste de (sujet, relation, objet, secteur)
    """
    triples = []
    seen_keys = set()
    secteur = detect_sector(text)
    
    # ── Nettoyage ───────────────────────────────────────────────────────
    text_clean = re.sub(r',\s*n[eé]\s+le\s+[^,]+', '', text)
    text_clean = re.sub(r',\s*mort\s+le\s+[^,]+', '', text_clean)
    text_clean = re.sub(r'\([^)]*\)', '', text_clean)
    text_clean = re.sub(r',\s+(est\s+(?:un|une|le|la|les|l)\s)', r' \1', text_clean)
    
    # Découper en segments
    segments = re.split(r'[.;]', text_clean)
    segments = [s.strip() for s in segments if len(s.strip()) > 10]
    segments.append(text_clean)
    
    # Stopwords
    stop_subjects = {'il', 'elle', 'on', 'cela', 'ceci', 'cet', 'cette', 'ces',
                     'qui', 'que', 'quoi', 'dont', 'tout', 'tous', 'toute', 'toutes',
                     'rien', 'personne', 'plusieurs', 'certains', 'cela', 'ce', 'ils',
                     'elles', 'the', 'this', 'that', 'these', 'those', 'it', 'he', 'she'}
    
    def _add(sujet: str, relation: str, objet: str, sec: str = None):
        """Ajoute un triplet avec déduplication."""
        s_clean = sujet.strip().lower()
        r_clean = relation.strip().lower()
        o_clean = objet.strip().lower()
        if not s_clean or not r_clean or not o_clean:
            return
        if len(s_clean) < 2 or len(o_clean) < 3:
            return
        if s_clean == o_clean:
            return
        if s_clean in stop_subjects:
            return
        key = (s_clean, r_clean, o_clean)
        if key not in seen_keys:
            seen_keys.add(key)
            triples.append((s_clean, r_clean, o_clean, sec or secteur))
    
    for seg in segments:
        if len(seg) < 15:
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 1 — Définitions
        # ═══════════════════════════════════════════════════════════════
        
        # 1a: "X est un/une/le/la/les/l'/des Y"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'est\s+(?:un|une|le|la|les|l\'|des|du|de la)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "est", m.group(2).strip(' .,;'))
            continue
        
        # 1b: "X signifie/désigne/représente/définit Y"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'(?:signifie|désigne|designe|représente|represente|définit|definit)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "signifie", m.group(2).strip(' .,;'))
            continue
        
        # 1c: "X is a/an/the Y" (EN)
        m = re.match(
            r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,3})\s+'
            r'is\s+(?:a|an|the)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "is", m.group(2).strip(' .,;'))
            continue
        
        # 1d: "X means/designates/represents/defines Y" (EN)
        m = re.match(
            r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,3})\s+'
            r'(?:means|designates|represents|defines)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "means", m.group(2).strip(' .,;'))
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 2 — Découverte/création (FR + EN)
        # ═══════════════════════════════════════════════════════════════
        
        discovery_verbs_fr = (
            'découvert|decouvert|inventé|invente|cree|créé|fondé|fonde|developpe|développé|'
            'publié|publie|formulé|formule|introduit|mesuré|mesure|observé|observe|'
            'détecté|detecte|détecte|analysé|analyse|synthétisé|synthetise|calculé|calcule|'
            'démontré|demontre|prouvé|prouve|établi|etabli|proposé|propose|conçu|concu|'
            'réalisé|realise|écrit|ecrit|composé|compose|peint|construit|bâti|bati'
        )
        discovery_verbs_en = (
            'discovered|invented|created|founded|developed|published|formulated|'
            'introduced|measured|observed|detected|analyzed|synthesised|synthesized|'
            'calculated|demonstrated|proved|established|proposed|designed|built|wrote|composed'
        )
        
        # 2a: "X a VERBE Y" (FR)
        m = re.match(
            r'([A-Z][a-zà-ÿ]+(?:\s[A-Z][a-zà-ÿ]+){0,2})\s+'
            r'a\s+(' + discovery_verbs_fr + r')\s+'
            r'(?:le |la |les |l\'|un |une |des |de |du )?(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), f"a {m.group(2).lower()}", m.group(3).strip(' .,;'))
            continue
        
        # 2b: "X VERBED Y" (EN, past tense)
        m = re.match(
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\s+'
            r'(' + discovery_verbs_en + r')\s+'
            r'(?:the |a |an )?(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), m.group(2).lower(), m.group(3).strip(' .,;'))
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 3 — Voix passive
        # ═══════════════════════════════════════════════════════════════
        
        # 3a: "Y a été VERBE par X" (FR)
        m = re.search(
            r'(.+?)\s+a\s+été\s+(' + discovery_verbs_fr + r')\s+par\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            objet, verbe, sujet_raw = m.group(1).strip().lower(), m.group(2).lower(), m.group(3).strip()
            # Extraire le sujet (premier nom propre ou premier mot capitalisé)
            sujet_words = sujet_raw.split()
            sujet = sujet_words[0].lower() if sujet_words else 'inconnu'
            _add(sujet, f"a été {verbe} par", objet)
            continue
        
        # 3b: "Y was/were VERBED by X" (EN)
        m = re.search(
            r'(.+?)\s+(?:was|were)\s+(' + discovery_verbs_en + r')\s+by\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            objet, verbe, sujet_raw = m.group(1).strip().lower(), m.group(2).lower(), m.group(3).strip()
            sujet = sujet_raw.split()[0].lower() if sujet_raw.split() else 'inconnu'
            _add(sujet, f"was {verbe} by", objet)
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 4 — Composition
        # ═══════════════════════════════════════════════════════════════
        
        # 4a: "X se compose de / est composé de / comprend / contient / inclut / est constitué de Y"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'(?:se compose de|est composé de|est compose de|comprend|contient|'
            r'inclut|renferme|est constitué de|est constitue de)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "comprend", m.group(2).strip(' .,;'))
            continue
        
        # 4b: "X consists of / is composed of / contains / includes Y" (EN)
        m = re.match(
            r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,3})\s+'
            r'(?:consists of|is composed of|contains|includes|comprises)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "contains", m.group(2).strip(' .,;'))
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 5 — Relations numériques/quantitatives
        # ═══════════════════════════════════════════════════════════════
        
        # 5a: "X a Y habitants/employés/membres/..."
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'a\s+(\d[\d\s]*(?:millions?|milliards?)?\s*(?:habitants?|employés?|employes?|'
            r'membres?|salariés?|salaries?|élèves?|eleves?|étudiants?|etudiants?|'
            r'habitants?|résidents?|residents?|citoyens?))',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "a", m.group(2).strip(' .,;'))
            continue
        
        # 5b: "X mesure Y (mètres/km/...)"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'mesure\s+(\d[\d\s,.]*\s*(?:mètres?|metres?|m|km|kilomètres?|kg|g|'
            r'tonnes?|litres?|L|hectares?|km²|m²))',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "mesure", m.group(2).strip(' .,;'))
            continue
        
        # 5c: "X date de Y" (origine temporelle)
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'date\s+(?:de|d\')\s*(\d{3,4}.*)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "date de", m.group(2).strip(' .,;'))
            continue
        
        # 5d: "X pèse Y (kg/tonnes)"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'pèse\s+(\d[\d\s,.]*\s*(?:kg|g|tonnes?|mg))',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "pèse", m.group(2).strip(' .,;'))
            continue
        
        # 5e: "X has Y inhabitants/employees/..." (EN)
        m = re.match(
            r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,3})\s+'
            r'has\s+(\d[\d\s,]*(?:million|billion|thousand)?\s*(?:inhabitants?|'
            r'employees?|members?|residents?|citizens?))',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "has", m.group(2).strip(' .,;'))
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 6 — Relations temporelles
        # ═══════════════════════════════════════════════════════════════
        
        # 6a: "X a eu lieu en/à Y"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,5})\s+'
            r'a\s+(?:eu|pris)\s+lieu\s+(?:en|à|au|aux|le)\s+(.+)',
            seg, re.IGNORECASE)
        if m and len(m.group(2)) > 2:
            _add(m.group(1), "a eu lieu en", m.group(2).strip(' .,;'))
            continue
        
        # 6b: "X a commencé/débuté en Y"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'a\s+(?:commencé|commence|débuté|debute)\s+(?:en|à|au|aux|le)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "a commencé en", m.group(2).strip(' .,;'))
            continue
        
        # 6c: "X a duré Y (ans/mois/jours)"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'a\s+duré\s+(\d[\d\s]*(?:ans?|mois|jours?|heures?|minutes?|siècles?|siecles?))',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "a duré", m.group(2).strip(' .,;'))
            continue
        
        # 6d: "X took place in Y" / "X began in Y" / "X lasted Y" (EN)
        for en_verb, rel in [('took place in', 'took place in'), 
                              ('began in', 'began in'),
                              ('lasted', 'lasted')]:
            m = re.match(
                r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,5})\s+'
                + en_verb + r'\s+(.+)',
                seg, re.IGNORECASE)
            if m:
                _add(m.group(1), rel, m.group(2).strip(' .,;'))
                break
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 7 — Relations causales
        # ═══════════════════════════════════════════════════════════════
        
        # 7a: "X cause/entraîne/provoque/déclenche/engendre Y"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'(?:cause|entraîne|entraine|provoque|déclenche|declenche|engendre|génère|genere)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "cause", m.group(2).strip(' .,;'))
            continue
        
        # 7b: "X causes/leads to/triggers/results in Y" (EN)
        m = re.match(
            r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,3})\s+'
            r'(?:causes|leads to|triggers|results in|provokes)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "causes", m.group(2).strip(' .,;'))
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 8 — Relations de localisation
        # ═══════════════════════════════════════════════════════════════
        
        # 8a: "X se trouve à/en/au/aux/dans/sur Y"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'(?:se trouve|est situé|est situe|se situe)\s+(?:à|en|au|aux|dans|sur|'
            r'près de|pres de|au bord de)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "se trouve", m.group(2).strip(' .,;'))
            continue
        
        # 8b: "X is located in/at/on/near Y" (EN)
        m = re.match(
            r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,3})\s+'
            r'(?:is located|lies|is situated)\s+(?:in|at|on|near|by)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "is located in", m.group(2).strip(' .,;'))
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 9 — Relations d'appartenance
        # ═══════════════════════════════════════════════════════════════
        
        # 9a: "X appartient à Y" / "X fait partie de Y"
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'(?:appartient à|appartient a|fait partie de|fait partie du|'
            r'est membre de|est un élément de|est un element de)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "appartient à", m.group(2).strip(' .,;'))
            continue
        
        # 9b: "X belongs to / is part of Y" (EN)
        m = re.match(
            r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,3})\s+'
            r'(?:belongs to|is part of|is a member of)\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), "belongs to", m.group(2).strip(' .,;'))
            continue
        
        # ═══════════════════════════════════════════════════════════════
        # GROUPE 10 — Relations comparatives
        # ═══════════════════════════════════════════════════════════════
        
        adj_fr = 'grand|petit|rapide|lent|haut|bas|fort|faible|léger|leger|lourd|cher|bon|mauvais|jeune|vieux|ancien|récent|recent|long|court|large|étroit|etroit|chaud|froid'
        adj_en = 'big|small|fast|slow|high|low|strong|weak|light|heavy|expensive|cheap|good|bad|young|old|recent|long|short|wide|narrow|hot|cold'
        
        # 10a: "X est plus/moins ADJ que Y" (FR)
        m = re.match(
            r'([A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}(?:\s[A-ZÀ-Üa-zà-ÿ][a-zà-ÿ]{1,}){0,3})\s+'
            r'est\s+(?:plus|moins)\s+(' + adj_fr + r')\s+que\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), f"est plus {m.group(2)} que", m.group(3).strip(' .,;'))
            continue
        
        # 10b: "X is ADJ-er / more ADJ than Y" (EN)
        m = re.match(
            r'([A-Z][a-z]{1,}(?:\s[A-Z][a-z]{1,}){0,3})\s+'
            r'is\s+(?:more|less)\s+(' + adj_en + r')\s+than\s+(.+)',
            seg, re.IGNORECASE)
        if m:
            _add(m.group(1), f"is more {m.group(2)} than", m.group(3).strip(' .,;'))
            continue
    
    return triples


def extract_triples_llm(text: str) -> List[Tuple[str, str, str, str]]:
    """
    Extraction de triplets via LLM (si disponible).
    Le LLM recoit le texte et doit retourner des triplets structures.
    """
    if not _LLM_AVAILABLE:
        return extract_triples_enhanced(text)
    
    prompt = f"""Extrait TOUS les faits du texte ci-dessous sous forme de triplets.
Format EXACT : sujet | relation | objet
Un triplet par ligne. Sujet et objet en minuscules. Max 10 mots.

Texte : {text[:2000]}

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
        if triples:
            log.info(f"extract_triples_llm: {len(triples)} triplets via LLM")
            return triples
        else:
            return extract_triples_enhanced(text)
    except Exception:
        return extract_triples_enhanced(text)


def extract_triples_batch(texts: List[str], use_llm: bool = True,
                           max_per_text: int = 500) -> List[Tuple[str, str, str, str]]:
    """
    Extrait des triplets d'une liste de textes, avec déduplication.

    Args:
        texts: Liste de textes à analyser
        use_llm: Si True, utilise le LLM (DeepSeek) pour l'extraction riche
        max_per_text: Nombre max de triplets par texte

    Returns:
        Liste de tuples (sujet, relation, objet, secteur) dédupliqués.
    """
    all_triplets = []
    seen = set()
    extract_fn = extract_triples_llm if (use_llm and _LLM_AVAILABLE) else extract_triples_simple
    
    total = len(texts)
    for i, text in enumerate(texts):
        if not text or len(text.strip()) < 50:
            continue
        
        try:
            triples = extract_fn(text)
            for s, r, o, sec in triples:
                s_clean = s.strip().lower()
                r_clean = r.strip().lower()
                o_clean = o.strip().lower()
                
                if not s_clean or not r_clean or not o_clean:
                    continue
                if len(s_clean) < 2 or len(o_clean) < 2:
                    continue
                if s_clean == o_clean:
                    continue
                
                key = (s_clean, r_clean, o_clean)
                if key not in seen:
                    seen.add(key)
                    all_triplets.append((s_clean, r_clean, o_clean, sec))
                    
                    if len(all_triplets) % 1000 == 0:
                        log.info(f"  extract_triples_batch: {len(all_triplets)} "
                                 f"triplets ({i+1}/{total} textes)")
        except Exception as e:
            log.debug(f"  Erreur extraction texte {i+1}/{total}: {e}")
            continue
        
        # Limiter par texte
        if len(all_triplets) >= max_per_text * (i + 1):
            all_triplets = all_triplets[:max_per_text * (i + 1)]
    
    log.info(f"extract_triples_batch terminé: {len(all_triplets)} triplets "
             f"de {total} textes")
    return all_triplets


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
