#!/usr/bin/env python3
"""
hwat_surface.py — HWAT comme décodeur de surface contraint par le gate
=======================================================================

La brique F du plan : le transformer harmonique (PhaseAttention) comme
MOTEUR de la forme, branché sur la génération de surface.

  Étape 1 — ENCODAGE : ψ_fait_i = ψ_s ⊛ ψ_r ⊛ ψ_o pour chaque fait vérifié
            du consensus ; ψ_ctx (historique) en tête de séquence.
  Étape 2 — ATTENTION : PhaseAttention.forward — chaque fait « attend »
            les autres par cohérence de phase (cos Δφ · √(AᵢAⱼ)/√D).
            Les faits liés (mots partagés, même domaine) se renforcent ;
            le contexte conversationnel module la représentation.
  Étape 3 — DÉCODAGE CONTRAINT : pour chaque fait, le syntagme sujet est
            choisi par softmax de cohérence de phase entre la
            représentation attentionnée et les candidats (le/la/ce/cette/
            un/une + sujet). Le vocabulaire des candidats est BORNE aux
            mots du fait + mots fonctionnels — le gate garantit qu'aucun
            mot hors des faits vérifiés ne peut sortir.
            La définitude contextuelle émerge : après « le diabète est une
            maladie », le fait suivant choisit « l'insuline » (défini)
            plutôt que « une insuline » (indéfini) — la représentation
            attentionnée a « vu » le diabète.

Contrat inchangé : le décodeur ne produit que des phrases dont les mots
viennent des faits vérifiés (sujet, prédicat, complément) et des mots
fonctionnels (articles, prépositions, auxiliaires).
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# DÉCODEUR DE SURFACE PAR ATTENTION DE PHASE
# ═══════════════════════════════════════════════════════════════════════════════

class PhaseSurfaceDecoder:
    """
    Décodeur de surface : faits vérifiés → phrases, par attention de phase.
    """

    def __init__(self, encoder=None, dim: int = 512, n_heads: int = 4):
        try:
            from harmonic_transformer import PhaseAttention
            from holographic_encoder import HolographicEncoder
        except Exception as e:
            raise ImportError(f'PhaseSurfaceDecoder indisponible: {e}')
        self.enc = encoder or HolographicEncoder(dim=dim)
        self.dim = dim
        self.attn = PhaseAttention(dim=dim, n_heads=n_heads, causal=False)

    # ── Encodage des faits ────────────────────────────────────────────────

    def _fact_psi(self, fact) -> np.ndarray:
        s, r, o = str(fact[0]).strip(), str(fact[1]).strip(), str(fact[2]).strip()
        try:
            return self.enc.encode_fact(s, r, o)
        except Exception:
            return self.enc.encode_query(f'{s} {r} {o}')

    # ── Décodage d'un fait ────────────────────────────────────────────────

    def _sujet_candidates(self, s: str) -> List[str]:
        """Variantes SN pour le sujet — vocabulaire borné au sujet + articles.
        Élision devant voyelle : « l'insuline », pas « la insuline »."""
        from french_corrector import GENDER
        gender = GENDER.get(s.lower().rstrip('sx'), GENDER.get(s.lower(), 'm'))
        if s[:1].isupper():            # nom propre (Plasmodium) → pas d'article
            return [s]
        starts_vowel = s[:1].lower() in 'aeiouyhàâäéèêëîïôöùûü'
        if gender == 'f':
            if starts_vowel:
                return [f"l'{s}", s.capitalize(), f'cette {s}', f'une {s}']
            return [f'la {s}', s.capitalize(), f'cette {s}', f'une {s}']
        if starts_vowel:
            return [f"l'{s}", s.capitalize(), f'ce {s}', f'un {s}']
        return [f'le {s}', s.capitalize(), f'ce {s}', f'un {s}']

    def _expansion_candidates(self, r: str) -> List[str]:
        """Expansions fonctionnelles du prédicat (mots fonctionnels)."""
        r_key = r.lower().strip()
        return {
            'est': ['', ' bien ', ' en réalité ', ' notamment '],
            'sont': ['', ' bien ', ' en réalité '],
            'permet': ['', ' notamment ', ' en particulier '],
            'permet de': ['', ' notamment ', ' en particulier '],
            'contient': ['', ' notamment ', ' également '],
            'regule': ['', ' notamment ', ' en particulier '],
            'produit': ['', ' notamment ', ' également '],
            'cause': ['', ' notamment ', ' en particulier '],
            'provoque': ['', ' notamment ', ' en particulier '],
            'transporte': ['', ' notamment ', ' également '],
            'synthetise': ['', ' notamment ', ' également '],
            'traite': ['', ' notamment ', ' en particulier '],
            'filtre': ['', ' notamment ', ' également '],
        }.get(r_key, [''])

    def _decode_fact(self, fact, attended_i: np.ndarray,
                     mem, variation: int) -> str:
        """
        Choix des syntagmes par cohérence de phase avec la représentation
        attentionnée — pondéré par le renforcement appris (SurfaceMemory).
        """
        s, r, o = str(fact[0]).strip(), str(fact[1]).strip(), str(fact[2]).strip()

        # Candidats SN
        sn_opts = self._sujet_candidates(s)
        scores = []
        for cand in sn_opts:
            psi_cand = self.enc.encode_query(cand)
            coh = float(np.real(np.dot(attended_i, np.conj(psi_cand))))
            coh = (coh + 1.0) / 2.0                       # → [0, 1]
            amp = mem.amplitude(f'surface|{cand}') if mem else 0.0
            scores.append(coh + amp)
        sn = sn_opts[int(np.argmax(scores))]
        if sn[:1].islower() and sn != s:
            sn = sn

        # Expansion du prédicat
        exp_opts = self._expansion_candidates(r)
        exp_scores = []
        for cand in exp_opts:
            psi_cand = self.enc.encode_query(f'{r}{cand}'.strip())
            coh = float(np.real(np.dot(attended_i, np.conj(psi_cand))))
            coh = (coh + 1.0) / 2.0
            amp = mem.amplitude(f'exp|{cand}') if mem else 0.0
            exp_scores.append(coh + amp)
        expansion = exp_opts[int(np.argmax(exp_scores))]

        co = o.rstrip('.')
        phrase = f'{sn} {r}{expansion} {co}'.strip() + '.'
        if phrase[:1].islower():
            phrase = phrase[0].upper() + phrase[1:]
        keys = [f'surface|{sn}', f'pred|{r}', f'exp|{expansion}',
                f'obj|{co[:30]}']
        if mem:
            mem.record(keys)
        return phrase

    # ── Pipeline complet ──────────────────────────────────────────────────

    def decode_facts(self, facts: List[Tuple],
                     ctx_psi: Optional[np.ndarray] = None,
                     mem=None, variation: int = 0) -> List[str]:
        """
        Faits vérifiés → phrases, par attention de phase inter-faits.

        Args:
            facts: [(s, r, o, sec, score), ...] — déjà filtrés par le gate
            ctx_psi: superposition du contexte conversationnel (ou None)
            mem: SurfaceMemory (renforcement de la forme)
            variation: salt pour la variété

        Returns:
            list[str] — une phrase par fait, vocabulaire borné aux faits
        """
        if not facts:
            return []
        mem = mem or (None if not hasattr(mem, 'amplitude') else mem)
        try:
            from surface_grammar import memory as _sm
            mem = mem or _sm()
        except Exception:
            pass

        # 1. Encodage : ψ_fait_i pour chaque fait
        seq = np.array([self._fact_psi(f) for f in facts],
                       dtype=np.complex128)                 # [L, D]
        # Normalisation par ligne
        norms = np.linalg.norm(seq, axis=1, keepdims=True)
        seq = seq / (norms + 1e-12)

        # 2. Attention : ψ_ctx en tête de séquence (le contexte attend les
        #    faits et les faits attendent le contexte)
        if ctx_psi is not None:
            ctx_psi = np.asarray(ctx_psi, dtype=np.complex128).reshape(1, -1)
            n = np.linalg.norm(ctx_psi)
            if n > 1e-12:
                ctx_psi = ctx_psi / n
            seq = np.vstack([ctx_psi, seq])
        attended = self.attn.forward(seq)                  # [L', D]

        off = 1 if ctx_psi is not None else 0
        return [self._decode_fact(f, attended[off + i], mem, variation)
                for i, f in enumerate(facts)]


# Instance paresseuse (l'import de harmonic_transformer peut être lourd)
_decoder = None


def get_decoder(encoder=None) -> Optional[PhaseSurfaceDecoder]:
    global _decoder
    if _decoder is None:
        try:
            _decoder = PhaseSurfaceDecoder(encoder=encoder)
        except Exception:
            _decoder = False
    return _decoder if _decoder else None


def decode_with_hwat(facts: List[Tuple],
                     ctx_psi: Optional[np.ndarray] = None,
                     encoder=None) -> List[str]:
    """Point d'entrée : retourne [] si HWAT indisponible (fallback appelant)."""
    dec = get_decoder(encoder)
    if dec is None:
        return []
    return dec.decode_facts(facts, ctx_psi=ctx_psi)


if __name__ == '__main__':
    # Test rapide : attention inter-faits (définitude contextuelle)
    facts = [
        ('diabete', 'est', 'une maladie chronique caracterisee par un exces de glucose dans le sang', 'SANTE', 2.9),
        ('diabete de type 1', 'est cause par', 'une deficience en insuline', 'SANTE', 2.9),
        ('insuline', 'est utilisee pour', 'traiter le diabete', 'SANTE', 2.9),
        ('diabete de type 2', 'est cause par', 'une resistance a l insuline', 'SANTE', 2.9),
    ]
    from surface_grammar import SurfaceMemory
    mem = SurfaceMemory(path=None)
    dec = get_decoder()
    if dec:
        phrases = dec.decode_facts(facts, mem=mem)
        for p in phrases:
            print('  •', p)
    else:
        print('HWAT indisponible — fallback')
