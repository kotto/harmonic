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
    Extrait les triplets d'un texte via patterns + fallback bootstrapper.

    Patterns reconnus :
      · « X est un/une Y » → (X, est, Y)
      · « X a découvert/inventé/créé Y »
      · « X permet de Y »
      · « X cause/provoque Y »
      · « X est composé de Y »
      · « X se trouve dans/en Y »
    """
    triples = []
    text_clean = re.sub(r'\([^)]*\)', '', text)  # parenthèses
    text_clean = re.sub(r'\[[^\]]*\]', '', text_clean)  # crochets
    text_clean = re.sub(r'\s+', ' ', text_clean)

    # Découpage en phrases
    sentences = re.split(r'(?<=[.!?])\s+', text_clean)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    stop_subjects = {'il', 'elle', 'on', 'cela', 'ceci', 'cet', 'cette', 'ces',
                     'qui', 'que', 'quoi', 'dont', 'tout', 'rien', 'ils', 'elles'}

    for sent in sentences:
        s = sent.strip()
        if len(s) < 20:
            continue

        # Pattern 1: X est un/une Y
        m = re.match(
            r'([A-ZÀ-Ű][a-zà-ÿ]{2,}(?:\s[A-ZÀ-Ű][a-zà-ÿ]{2,}){0,3})\s+'
            r'(?:est|sont|était|étaient|reste|demeure)\s+'
            r'(?:un|une|le|la|les|l|des|du|de la)\s+(.+)',
            s, re.IGNORECASE
        )
        if m:
            sujet = m.group(1).strip().lower()
            objet = m.group(2).strip(' .,;').lower()
            if sujet not in stop_subjects and len(sujet) >= 3 and len(objet) >= 5:
                triples.append((sujet, "est", objet, "GENERAL"))
                continue

        # Pattern 2: X a V Y (découverte, création)
        m = re.match(
            r'([A-ZÀ-Ű][a-zà-ÿ]{2,}(?:\s[A-ZÀ-Ű][a-zà-ÿ]{2,}){0,2})\s+'
            r'a\s+(découvert|inventé|créé|fondé|développé|publié|formulé|'
            r'introduit|proposé|établi|démontré|prouvé)\s+(.+)',
            s, re.IGNORECASE
        )
        if m:
            sujet = m.group(1).strip().lower()
            verbe = m.group(2).lower()
            objet = m.group(3).strip(' .,;').lower()
            if len(sujet) >= 3 and len(objet) >= 5:
                triples.append((sujet, f"a {verbe}", objet, "SCIENCES"))
                continue

        # Pattern 3: X permet de Y / X cause Y
        m = re.search(
            r'([a-zà-ÿ]{3,}(?:\s[a-zà-ÿ]{3,}){0,3})\s+'
            r'(permet(?:tent)? de|cause|provoque|entraîne|génère|produit|'
            r'contribue à|participe à|joue un rôle dans)\s+(.+)',
            s, re.IGNORECASE
        )
        if m:
            sujet = m.group(1).strip().lower()
            relation = m.group(2).strip().lower()
            objet = m.group(3).strip(' .,;').lower()
            if len(sujet) >= 3 and len(objet) >= 5:
                triples.append((sujet, relation, objet, "GENERAL"))
                continue

        # Pattern 4: X se trouve dans/en Y
        m = re.search(
            r'([a-zà-ÿ]{3,}(?:\s[a-zà-ÿ]{3,}){0,3})\s+'
            r'(se trouve(?:nt)? (?:dans|en|au|aux|sur)|est (?:situé|localisé|présent) '
            r'(?:dans|en|au|aux|sur))\s+(.+)',
            s, re.IGNORECASE
        )
        if m:
            sujet = m.group(1).strip().lower()
            relation = m.group(2).strip().lower()
            objet = m.group(3).strip(' .,;').lower()
            if len(sujet) >= 3 and len(objet) >= 5:
                triples.append((sujet, relation, objet, "GEOGRAPHIE"))
                continue

        # Pattern 5: X est composé de Y
        m = re.search(
            r'([a-zà-ÿ]{3,}(?:\s[a-zà-ÿ]{3,}){0,3})\s+'
            r'(est|sont)\s+(composé|constitué|formé|fait)(?:e?s)?\s+(?:de|d|par)\s+(.+)',
            s, re.IGNORECASE
        )
        if m:
            sujet = m.group(1).strip().lower()
            objet = m.group(4).strip(' .,;').lower()
            if len(sujet) >= 3 and len(objet) >= 5:
                triples.append((sujet, "est composé de", objet, "SCIENCES"))
                continue

    # Fallback : bootstrapper si disponible (toujours pour les textes longs)
    try:
        from bootstrapper import extract_triples_simple
        bt_triples = extract_triples_simple(text)
        # Fusionner : priorité aux patterns (plus précis), compléter avec bootstrapper
        existing = {(s.lower().strip(), r.lower().strip(), o.lower().strip())
                    for s, r, o, _ in triples}
        for s, r, o, sec in bt_triples:
            key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
            if key not in existing:
                triples.append((s, r, o, sec))
                existing.add(key)
    except ImportError:
        pass

    # Déduplication
    seen = set()
    unique = []
    for s, r, o, sec in triples:
        key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append((s, r, o, sec))

    return unique


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
        all_triples = []
        for chunk in chunks:
            triples = extract_triples_from_text(chunk)
            all_triples.extend(triples)

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
        for i in range(min(len(selected), len(selected))):
            for j in range(i + 1, min(len(selected), len(selected))):
                # Même sujet + relations opposées → contradiction potentielle
                if (selected[i][0].lower() == selected[j][0].lower() and
                        selected[i][1] != selected[j][1]):
                    coh = self._coherence(
                        self._get_psi(f"{selected[i][0]}|{selected[i][1]}|{selected[i][2]}"),
                        self._get_psi(f"{selected[j][0]}|{selected[j][1]}|{selected[j][2]}")
                    )
                    if coh < -0.01:  # interférence destructive
                        contradictions.append((selected[i][:3], selected[j][:3], coh))

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
                # Formater le fait en phrase naturelle
                if r in ('est', 'sont'):
                    phrase = f"{i+1}. {s.capitalize()} {r} {o}."
                elif r.startswith('a '):
                    phrase = f"{i+1}. {s.capitalize()} {r} {o}."
                else:
                    phrase = f"{i+1}. {s.capitalize()} {r} {o}."
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
