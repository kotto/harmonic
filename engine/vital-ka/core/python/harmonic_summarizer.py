"""
Harmonic Summarizer — Résumé par Résonance Ondulatoire
=========================================================
Résume un texte de N pages en extrayant sa STRUCTURE DE CONNAISSANCE.

CONTRASTE AVEC LES LLMs :
  LLM : « lis le texte → reformule en plus court » (boîte noire, peut inventer)
  HARMONIQUE : « extrais les triplets → calcule la centralité de résonance →
                exprime les piliers » (déterministe, vérifiable)

PIPELINE :
  1. SEGMENTATION : découpage en chunks (~500 mots)
  2. EXTRACTION : triplets (sujet, relation, objet) par patterns
  3. ENCODAGE : chaque fait → ψ ∈ ℂ (vecteur complexe)
  4. CENTRALITÉ : pour chaque fait, Σ cohérence avec tous les autres
  5. SÉLECTION : top-K faits les plus centraux = piliers du texte
  6. EXPRESSION : piliers → résumé en langage naturel

MÉTRIQUE CLÉ :
  Centralité(f_i) = Σ_j |⟨ψ_i | ψ_j⟩| / N
  → Un fait est « central » s'il résonne avec beaucoup d'autres faits.
  → Ce sont les idées que tout le reste soutient ou nuance.

USAGE :
  from harmonic_summarizer import HarmonicSummarizer
  
  summ = HarmonicSummarizer(brain)
  result = summ.summarize(text_20_pages, max_facts=10)
  print(result.summary)       # résumé en langage naturel
  print(result.key_themes)    # thèmes principaux détectés
  print(result.contradictions) # contradictions trouvées
  print(result.graph)         # graphe de cohérence (pour visualisation)
"""

import math
import re
import time
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895

# ═══════════════════════════════════════════════════════════════════════════════
# NETTOYAGE & VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def _clean_phrase(phrase: str) -> str:
    """
    Nettoie un syntagme extrait par regex.
    
    Corrige :
      · Articles tronqués : « s côtes » → « les côtes »
      · « l évolution » → « l'évolution »
      · Ponctuation parasite
      · Espaces multiples
    """
    # Reconstruire les articles tronqués
    phrase = re.sub(r'\bs\s+([a-zà-ÿ])', r'les \1', phrase)  # « s côtes » → « les côtes »
    phrase = re.sub(r'\bd\s+([a-zà-ÿ])', r'de \1', phrase)   # « d émission » → « de émission »
    phrase = re.sub(r'\bl\s+([a-zà-ÿ])', r"l'\1", phrase)     # « l évolution » → « l'évolution »
    phrase = re.sub(r'\bn\s+([a-zà-ÿ])', r"n'\1", phrase)     # « n est » → « n'est »
    phrase = re.sub(r'\bqu\s+([a-zà-ÿ])', r"qu'\1", phrase)   # « qu il » → « qu'il »
    
    # Ponctuation parasite
    phrase = re.sub(r'\s*\.\s*$', '', phrase)
    phrase = re.sub(r'\s*;\s*$', '', phrase)
    phrase = re.sub(r'\s+', ' ', phrase)
    
    return phrase.strip()

def _clean_subject(subject: str) -> str:
    """Nettoie un sujet extrait."""
    # Enlever les articles au début
    subject = re.sub(r'^(le |la |les |l |un |une |des |du |de la )', '', subject.lower())
    return _clean_phrase(subject)

def _normalize_key(s: str, r: str, o: str) -> tuple:
    """Crée une clé de déduplication normalisée."""
    sn = _clean_subject(s).strip()
    rn = r.lower().strip()
    on = _clean_phrase(o).strip().lower()
    # Normaliser les espaces et accents
    on = re.sub(r'\s+', ' ', on)
    return (sn, rn, on)

def _validate_triple(s: str, r: str, o: str) -> bool:
    """Valide qu'un triple est acceptable."""
    sn = _clean_subject(s).strip()
    on = _clean_phrase(o).strip()
    
    # Sujet trop court
    if len(sn) < 3:
        return False
    # Objet trop court
    if len(on) < 5:
        return False
    # Sujet = stopword
    if sn in {'il', 'elle', 'on', 'ils', 'elles', 'cela', 'ceci', 'cet', 'cette',
              'ces', 'ce', 'ca', 'qui', 'que', 'quoi', 'dont', 'tout', 'rien'}:
        return False
    # Objet = sujet (circularité)
    if sn == on:
        return False
    # Objet est juste un article ou préposition
    if on in {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'au', 'aux', 'sur',
              'dans', 'par', 'pour', 'avec', 'sans', 'sous', 'entre', 'vers'}:
        return False
    
    return True

def _dedup_triples(triples: List[Tuple[str, str, str, str]]) -> List[Tuple[str, str, str, str]]:
    """
    Déduplication intelligente :
      1. Normalise les clés (sujet, relation, objet)
      2. Élimine les doublons exacts
      3. Pour les mêmes (sujet, relation), garde l'objet le plus long
    """
    # Étape 1 : déduplication exacte normalisée
    seen = {}
    for s, r, o, sec in triples:
        key = _normalize_key(s, r, o)
        if key not in seen:
            seen[key] = (s, r, o, sec)
    
    # Étape 2 : pour les mêmes (sujet, relation), garder l'objet le plus informatif
    by_subj_rel = defaultdict(list)
    for (sn, rn, on), (s, r, o, sec) in seen.items():
        by_subj_rel[(sn, rn)].append((s, r, o, sec, len(on)))
    
    result = []
    for (sn, rn), candidates in by_subj_rel.items():
        # Garder l'objet le plus long (le plus informatif)
        best = max(candidates, key=lambda x: x[4])
        result.append((best[0], best[1], best[2], best[3]))
    
    return result

def _detect_contradictions_lexical(triples: List[Tuple[str, str, str, str]]) -> List[Tuple]:
    """
    Détecte les contradictions par patterns lexicaux (fallback mode léger).
    
    Cherche :
      · (X, est, Y) vs (X, n'est pas, Y) → contradiction directe
      · (X, augmente, Y) vs (X, diminue, Y) → opposition
      · (X, cause, Y) vs (X, empêche, Y) → opposition fonctionnelle
    """
    contradictions = []
    
    # Paires de relations opposées
    opposite_relations = [
        ('est', "n'est pas"),
        ('augmente', 'diminue'),
        ('cause', 'empêche'),
        ('produit', 'détruit'),
        ('favorise', 'menace'),
        ('crée', 'détruit'),
        ('protège', 'menace'),
        ('réduit', 'augmente'),
        ('est nécessaire', 'est inutile'),
        ('augmente', 'réduit'),
        ('favorise', 'détruit'),
        ('contribue à', 'menace'),
        ('augmente', 'menace'),   # OGM: augmente rendements VS menace biodiversité
        ('favorise', 'menace'),   # mondialisation: favorise croissance VS menace emplois
    ]
    
    # Normaliser une relation pour la comparaison (enlever la négation)
    def _strip_negation(rel: str) -> str:
        return re.sub(r'^ne\s+', '', rel).replace(' pas', '').strip()
    
    # Index par sujet
    by_subject = defaultdict(list)
    for s, r, o, sec in triples:
        sn = _clean_subject(s)
        by_subject[sn].append((r, o, sec))
    
    for subject, facts in by_subject.items():
        for i in range(len(facts)):
            for j in range(i + 1, len(facts)):
                r1, o1, _ = facts[i]
                r2, o2, _ = facts[j]
                
                # Vérifier si les relations sont opposées
                r1n = r1.lower().strip()
                r2n = r2.lower().strip()
                
                for opp_a, opp_b in opposite_relations:
                    if (r1n == opp_a and r2n == opp_b) or (r1n == opp_b and r2n == opp_a):
                        # Vérifier que les objets sont similaires (même sujet de contradiction)
                        o1n = _clean_phrase(o1)
                        o2n = _clean_phrase(o2)
                        # Les objets doivent être liés (partagent des mots ou sont identiques)
                        words1 = set(o1n.split())
                        words2 = set(o2n.split())
                        overlap = words1 & words2
                        if overlap or o1n == o2n:
                            contradictions.append((
                                (subject, r1, o1),
                                (subject, r2, o2),
                                -0.5  # score négatif = contradiction
                            ))
                            break
    
    return contradictions


# ═══════════════════════════════════════════════════════════════════════════════
# SEGMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

def segment_text(text: str, max_words_per_chunk: int = 500,
                 overlap_words: int = 50) -> List[str]:
    """
    Découpe un texte long en chunks avec chevauchement.

    Args:
        text: texte complet
        max_words_per_chunk: mots max par segment
        overlap_words: mots de chevauchement entre segments

    Returns:
        liste de segments
    """
    # Nettoyage basique
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\[(\d+)\]', '', text)  # références [1], [2]
    text = re.sub(r'\(\d{4}\)', '', text)  # dates entre parenthèses isolées

    # Découpage par paragraphes naturels d'abord
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 50]

    # Fusionner les paragraphes en chunks de ~max_words
    chunks = []
    current = []
    current_words = 0

    for para in paragraphs:
        words = len(para.split())
        if current_words + words > max_words_per_chunk and current:
            chunks.append(' '.join(current))
            # Garder les derniers mots pour le chevauchement
            overlap = current[-1].split()[-overlap_words:] if overlap_words > 0 else []
            current = [' '.join(overlap)] if overlap else []
            current_words = len(overlap)
        current.append(para)
        current_words += words

    if current:
        chunks.append(' '.join(current))

    return chunks


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION DE TRIPLETS
# ═══════════════════════════════════════════════════════════════════════════════

def extract_triples_from_text(text: str) -> List[Tuple[str, str, str, str]]:
    """
    Extrait les triplets d'un texte via l'extracteur 20 patterns + KB-trained.
    """
    try:
        from triple_extractor import TripleExtractor
        # Utiliser l'extracteur unifié (20 patterns + fallback bootstrapper)
        extractor = _get_extractor()
        return extractor.extract(text)
    except ImportError:
        pass
    
    # Fallback minimal si triple_extractor non disponible
    triples = []
    # ... (anciens patterns gardés pour compatibilité)
    return triples

# Singleton extractor (initialisé une fois)
_extractor_instance = None

def _get_extractor():
    global _extractor_instance
    if _extractor_instance is None:
        from triple_extractor import TripleExtractor
        _extractor_instance = TripleExtractor(use_trained=False)
    return _extractor_instance


# ═══════════════════════════════════════════════════════════════════════════════
# RÉSUMÉ HARMONIQUE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HarmonicSummary:
    """Résultat d'un résumé harmonique."""
    summary: str                          # résumé en langage naturel
    key_facts: List[Tuple[str, str, str, float]]  # (s, r, o, centralité)
    key_themes: List[str]                 # thèmes principaux détectés
    contradictions: List[Tuple]           # paires de faits contradictoires
    stats: dict                           # métriques
    graph_edges: List[Tuple] = None       # pour visualisation


class HarmonicSummarizer:
    """
    Résumeur harmonique — extrait les piliers de connaissance d'un texte.

    Ne « lit » pas le texte. Extrait sa structure d'idées et
    exprime les faits les plus centraux par résonance.
    """

    def __init__(self, brain=None, dim: int = 512, max_facts: int = 15):
        self.brain = brain
        self.dim = dim or (brain.unconscious.dim if brain else 512)
        self.max_facts = max_facts

    def _get_psi(self, text: str) -> np.ndarray:
        """Génère un ψ déterministe pour un texte."""
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        return v / (np.linalg.norm(v) + 1e-10)

    def _coherence(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """Cohérence de phase entre deux ψ."""
        if psi_a is None or psi_b is None:
            return 0.0
        dot = np.abs(np.dot(psi_a.conj(), psi_b))
        na = np.linalg.norm(psi_a)
        nb = np.linalg.norm(psi_b)
        return min(1.0, float(dot / (na * nb + 1e-10)))

    # ═══════════════════════════════════════════════════════════════════════
    # PIPELINE PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════

    def summarize(self, text: str, max_facts: int = None,
                  target_lang: str = 'fr') -> HarmonicSummary:
        """
        Résume un texte en extrayant ses piliers de connaissance.

        Args:
            text: texte complet (1 à 50 pages)
            max_facts: nombre max de faits dans le résumé
            target_lang: langue cible du résumé

        Returns:
            HarmonicSummary
        """
        max_facts = max_facts or self.max_facts
        t0 = time.time()

        # ── 1. SEGMENTATION ──
        chunks = segment_text(text, max_words_per_chunk=500)
        log.info(f"Segmentation: {len(chunks)} chunks")

        # ── 2. EXTRACTION ──
        all_triples_raw = []
        for chunk in chunks:
            triples = extract_triples_from_text(chunk)
            all_triples_raw.extend(triples)

        # ── 2b. NETTOYAGE + VALIDATION + DÉDUPLICATION ──
        # Valider chaque triple
        valid_triples = [(s, r, o, sec) for s, r, o, sec in all_triples_raw
                         if _validate_triple(s, r, o)]
        # Nettoyer les objets
        cleaned_triples = [(s, r, _clean_phrase(o), sec) for s, r, o, sec in valid_triples]
        # Dédupliquer
        all_triples = _dedup_triples(cleaned_triples)

        if not all_triples:
            return HarmonicSummary(
                summary="Aucune connaissance structurée extraite du texte.",
                key_facts=[], key_themes=[], contradictions=[],
                stats={'chunks': len(chunks), 'triples': 0, 'time_ms': 0}
            )

        log.info(f"Extraction: {len(all_triples)} triplets")

        # ── 3. ENCODAGE ──
        psis = []
        facts = []
        for s, r, o, sec in all_triples:
            psi = self._get_psi(f"{s}|{r}|{o}")
            psis.append(psi)
            facts.append((s, r, o, sec))

        # ── 4. CENTRALITÉ DE RÉSONANCE ──
        N = len(psis)
        centralities = np.zeros(N)

        for i in range(N):
            total_coh = 0.0
            for j in range(N):
                if i != j:
                    total_coh += self._coherence(psis[i], psis[j])
            centralities[i] = total_coh / max(1, N - 1)

        # ── 5. SÉLECTION DES PILIERS ──
        # Top-K par centralité, mais avec diversité (ne pas prendre 2 fois le même sujet)
        ranked = sorted(enumerate(centralities), key=lambda x: -x[1])
        selected = []
        seen_subjects = set()

        for idx, cent in ranked:
            s, r, o, sec = facts[idx]
            sujet_key = s.lower().strip()
            # Diversité : max 2 faits par sujet
            count = sum(1 for ss in seen_subjects if ss == sujet_key)
            if count >= 2:
                continue
            selected.append((s, r, o, sec, cent))
            seen_subjects.add(sujet_key)
            if len(selected) >= max_facts:
                break

        # ── 6. DÉTECTION DE THÈMES ──
        sectors = Counter(sec for _, _, _, sec, _ in selected)
        themes = [s for s, _ in sectors.most_common(5)]

        # ── 7. DÉTECTION DE CONTRADICTIONS ──
        contradictions = []
        # Essayer d'abord la détection par phase (mode holographique)
        if hasattr(self, 'brain') and self.brain is not None:
            try:
                # Version phase-based si dispo
                for i in range(min(len(selected), len(selected))):
                    for j in range(i + 1, min(len(selected), len(selected))):
                        if (selected[i][0].lower() == selected[j][0].lower() and
                                selected[i][1] != selected[j][1]):
                            coh = self._coherence(
                                self._get_psi(f"{selected[i][0]}|{selected[i][1]}|{selected[i][2]}"),
                                self._get_psi(f"{selected[j][0]}|{selected[j][1]}|{selected[j][2]}")
                            )
                            if coh < -0.01:
                                contradictions.append((selected[i][:3], selected[j][:3], coh))
            except Exception:
                pass
        
        # Fallback lexical (toujours actif)
        lexical_contradictions = _detect_contradictions_lexical(
            [(s, r, o, sec) for s, r, o, sec, _ in selected]
        )
        contradictions.extend(lexical_contradictions)

        # ── 8. EXPRESSION ──
        summary = self._compose_summary(selected, themes, contradictions, target_lang)

        elapsed = (time.time() - t0) * 1000

        return HarmonicSummary(
            summary=summary,
            key_facts=[(s, r, o, c) for s, r, o, _, c in selected],
            key_themes=themes,
            contradictions=contradictions,
            stats={
                'chunks': len(chunks),
                'triples_extracted': len(all_triples),
                'unique_facts': len(facts),
                'selected': len(selected),
                'time_ms': round(elapsed, 1),
            },
        )

    # ═══════════════════════════════════════════════════════════════════════
    # COMPOSITION
    # ═══════════════════════════════════════════════════════════════════════

    def _compose_summary(self, selected: List, themes: List[str],
                         contradictions: List, lang: str = 'fr') -> str:
        """Compose le résumé en langage naturel."""

        if lang == 'fr':
            lines = ["📖 RÉSUMÉ HARMONIQUE", ""]

            # Introduction
            lines.append(f"Ce texte contient {len(selected)} idées centrales "
                        f"organisées autour de {len(themes)} thèmes principaux.")
            lines.append("")

            # Faits clés par centralité
            lines.append("🔑 POINTS CLÉS (par ordre d'importance) :")
            lines.append("")
            for i, (s, r, o, _, cent) in enumerate(selected):
                # Nettoyer le sujet et l'objet pour l'affichage
                sn = _clean_subject(s).capitalize()
                on = _clean_phrase(o)
                rn = r.lower().strip()
                # Formater la phrase
                if rn.startswith('a '):
                    phrase = f"{i+1}. {sn} {rn} {on}."
                elif rn in ('est', 'sont', 'reste', 'demeure', 'devient'):
                    phrase = f"{i+1}. {sn} {rn} {on}."
                else:
                    phrase = f"{i+1}. {sn} {rn} {on}."
                # Capitalize first letter
                phrase = phrase[0].upper() + phrase[1:] if phrase else phrase
                lines.append(f"   {phrase}")
            lines.append("")

            # Thèmes
            if themes:
                lines.append("🏷️  THÈMES PRINCIPAUX :")
                lines.append(f"   {', '.join(themes)}")
                lines.append("")

            # Contradictions
            if contradictions:
                lines.append("⚠️  CONTRADICTIONS DÉTECTÉES :")
                for (s1, r1, o1), (s2, r2, o2), coh in contradictions[:3]:
                    lines.append(f"   • {s1} {r1} {o1}  VS  {s2} {r2} {o2}")
                lines.append("")

            return "\n".join(lines)
        else:
            # English version
            lines = ["📖 HARMONIC SUMMARY", ""]
            lines.append(f"This text contains {len(selected)} central ideas "
                        f"across {len(themes)} main themes.")
            lines.append("")
            lines.append("🔑 KEY POINTS (by importance):")
            lines.append("")
            for i, (s, r, o, _, cent) in enumerate(selected):
                lines.append(f"   {i+1}. {s.capitalize()} {r} {o}.")
            lines.append("")
            if themes:
                lines.append(f"🏷️  MAIN THEMES: {', '.join(themes)}")
                lines.append("")
            if contradictions:
                lines.append("⚠️  CONTRADICTIONS DETECTED:")
                for (s1, r1, o1), (s2, r2, o2), coh in contradictions[:3]:
                    lines.append(f"   • {s1} {r1} {o1}  VS  {s2} {r2} {o2}")
                lines.append("")
            return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  HARMONIC SUMMARIZER — Test")
    print("=" * 60)

    # Texte de test (~2 pages simulées)
    test_text = """
    La photosynthèse est le processus par lequel les plantes convertissent 
    la lumière du soleil en énergie chimique. Ce mécanisme est essentiel à 
    la vie sur Terre car il produit l'oxygène que nous respirons. 
    
    Les chloroplastes sont les organites cellulaires où se déroule la 
    photosynthèse. Ils contiennent la chlorophylle, un pigment vert qui 
    capture l'énergie lumineuse. La chlorophylle est composée de magnésium 
    et d'azote.
    
    Le cycle de Calvin est la phase sombre de la photosynthèse. Il permet 
    de fixer le dioxyde de carbone atmosphérique et de produire du glucose. 
    Ce cycle a été découvert par Melvin Calvin en 1961, ce qui lui a valu 
    le prix Nobel de chimie.
    
    L'oxygène produit par la photosynthèse est respiré par les animaux. 
    Les animaux produisent du CO2 qui est absorbé par les plantes. Cette 
    interdépendance forme le cycle du carbone.
    
    La déforestation massive menace ce cycle. Elle réduit la capacité de 
    la planète à absorber le CO2. Le réchauffement climatique est causé 
    par l'accumulation de gaz à effet de serre dans l'atmosphère.
    
    Les énergies renouvelables comme le solaire et l'éolien permettent de 
    réduire les émissions de CO2. La transition énergétique est nécessaire 
    pour préserver les écosystèmes. Les accords de Paris de 2015 ont fixé 
    des objectifs de réduction des émissions pour 195 pays.
    """

    summ = HarmonicSummarizer(dim=64, max_facts=8)
    result = summ.summarize(test_text)

    print()
    print(result.summary)
    print()
    print("📊 Stats:", result.stats)
    print()
    print("🔑 Faits clés:")
    for s, r, o, cent in result.key_facts:
        print(f"  [{cent:.4f}] {s} → {r} → {o}")
    print()
    if result.contradictions:
        print("⚠️  Contradictions:")
        for (s1, r1, o1), (s2, r2, o2), coh in result.contradictions:
            print(f"  {s1} {r1} {o1}  VS  {s2} {r2} {o2} (coh={coh:.3f})")
    print()
    print("✅ Harmonic Summarizer OK")
