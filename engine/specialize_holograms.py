#!/usr/bin/env python3
"""
specialize_holograms.py — Centres d'intérêt → Hologramme dédié (wave v2)
=========================================================================

Spécialisation à la demande, dans l'esprit M4 (sans oracle, multi-signaux) :

  1. SEED CIBLÉ — à partir des centres d'intérêt de l'utilisateur :
     - ancres = mots du sujet + équivalents bilingues (leçon vécue :
       le plongement appris ne relie pas diabete↔diabetes, sim = −0.02)
     - pool = faits de TOUS les hologrammes du store + KB qualitative
     - pré-filtre lexical par ancre (frontière de mot) → pool réduit
     - scoring par résonance token vectorisée (Q·W_encᵀ), comme recall()
     - garder : ancre lexicale OU résonance ≥ seuil — un fait qui ne
       résonne pas au centroid du sujet n'entre pas dans l'hologramme

  2. CONSTRUCTION v2 — ψ composants, mémoire holographique H, pureté
     (mean/std) — même format que purify_holograms (download polaire OK)

  3. BENCHMARK INTERNE sans oracle — les questions « Qu est-ce que X ? »
     passent dans le rappel M4 : précision@1 = le fait top contient une
     ancre ou résonne ≥ 0.55 → quality_score écrit dans le registre

  4. ENRICHISSEMENT — WebRetriever (Wikipedia) + TripleExtractor pré-
     entraîné sur le seed → nouveaux faits filtrés par les mêmes ancres
     (hook pour tâche background)

Usage (dans le serveur) :
    from specialize_holograms import HologramSpecializer
    spec = HologramSpecializer(store, kb=KNOWLEDGE_BASE)
    result = spec.build(["diabete", "nutrition"], language="fr")
"""

import re
import sys
import time
import logging
import threading
from pathlib import Path
from collections import Counter
from typing import List, Tuple, Optional, Dict

import numpy as np

# Setup
_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from hologram_store import HologramStore, HologramMeta, STORE_DIR, HOLOGRAM_FORMAT_VERSION
from holographic_encoder import HolographicEncoder, _circular_convolve, _STOPWORDS

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# ANCRES BILINGUES FR ↔ EN (concepts courants)
# Le plongement appris ne transpose pas les langues : « diabete » ne résonne
# pas avec « diabetes ». On ancre donc les sujets fréquents avec leurs
# équivalents — la requête « diabete » devient {diabete, diabetes, insuline}.
# ═══════════════════════════════════════════════════════════════════════════════

ANCHOR_MAP = {
    'diabete': ['diabete', 'diabetes', 'insuline', 'insulin', 'glycemie', 'glucose'],
    'diabète': ['diabete', 'diabetes', 'insuline', 'insulin', 'glycemie', 'glucose'],
    'cancer': ['cancer', 'tumeur', 'tumor', 'oncologie', 'metastase', 'metastasis'],
    'coeur': ['coeur', 'heart', 'cardiaque', 'cardiac', 'cardiovasculaire', 'cardiovascular'],
    'cœur': ['coeur', 'heart', 'cardiaque', 'cardiac', 'cardiovasculaire', 'cardiovascular'],
    'sang': ['sang', 'blood', 'globule', 'globules', 'hematologie', 'anemie'],
    'vaccin': ['vaccin', 'vaccine', 'vaccination', 'immunisation', 'pasteur', 'salk', 'jenner'],
    'vaccination': ['vaccin', 'vaccine', 'vaccination', 'immunisation'],
    'paludisme': ['paludisme', 'malaria', 'plasmodium', 'anopheles', 'moustique', 'mosquito'],
    'grippe': ['grippe', 'flu', 'influenza', 'virus respiratoire'],
    'hypertension': ['hypertension', 'pression arterielle', 'blood pressure', 'lisinopril'],
    'antibiotique': ['antibiotique', 'antibiotic', 'antibiotics', 'bacterie', 'bacteria', 'waksman'],
    'anemie': ['anemie', 'anemia', 'globules rouges', 'red blood cells', 'fer'],
    'nutrition': ['nutrition', 'alimentation', 'diet', 'nutrient', 'nutriments', 'vitamine', 'vitamin'],
    'alimentation': ['nutrition', 'alimentation', 'diet', 'aliment', 'food', 'nutriment'],
    'sport': ['sport', 'exercice', 'exercise', 'entrainement', 'training', 'muscle', 'endurance'],
    'psychologie': ['psychologie', 'psychology', 'cerveau', 'brain', 'comportement', 'behavior', 'emotion'],
    'cerveau': ['cerveau', 'brain', 'neurone', 'neuron', 'neuro', 'cognition'],
    'philosophie': ['philosophie', 'philosophy', 'pensee', 'thought', 'existence', 'ethique'],
    'histoire': ['histoire', 'history', 'passe', 'passe', 'antiquite', 'antiquity', 'medieval'],
    'geographie': ['geographie', 'geography', 'continent', 'pays', 'country', 'riviere', 'river'],
    'astronomie': ['astronomie', 'astronomy', 'etoile', 'star', 'planete', 'planet', 'galaxie'],
    'physique': ['physique', 'physics', 'mecanique', 'mecanique quantique', 'quantum', 'relativite'],
    'mathematiques': ['mathematique', 'mathematics', 'math', 'algebre', 'algebra', 'geometrie', 'calcul'],
    'informatique': ['informatique', 'computer science', 'programmation', 'programming', 'algorithme', 'algorithm', 'python'],
    'musique': ['musique', 'music', 'instrument', 'harmonie', 'rythme', 'rhythm', 'melodie'],
    'economie': ['economie', 'economics', 'marche', 'market', 'monnaie', 'currency', 'croissance'],
    'droit': ['droit', 'law', 'legal', 'justice', 'loi'],
    'biologie': ['biologie', 'biology', 'cellule', 'cell', 'gene', 'genetique', 'genetics'],
    'ecologie': ['ecologie', 'ecology', 'environnement', 'environment', 'climat', 'climate', 'biodiversite'],
    'technologie': ['technologie', 'technology', 'innovation', 'numerique', 'digital'],
    'nutrition sportive': ['nutrition', 'sport', 'proteine', 'protein', 'calorie', 'muscle'],
}

# Seuils
SEED_MIN_FACTS = 4           # en-dessous : inexploitable — un hologramme précis
                             # de 4-8 faits reste utile (le gate M4 protège)
THIN_SEED = 15               # en-dessous : enrichissement Wikipedia automatique
                             # (les sujets étroits — paludisme — ont peu de
                             # faits dans le corpus)
SEED_MAX_FACTS = 300         # plafond par hologramme dédié
SEMANTIC_THRESHOLD = 0.55    # résonance token minimale (hors ancre lexicale exacte)
BENCHMARK_SIM = 0.55         # précision@1 : fait top jugé pertinent


def _clean_word(w: str) -> str:
    """Minuscules, sans accents ni ponctuation."""
    _ACCENTS = str.maketrans({
        'à': 'a', 'â': 'a', 'ä': 'a', 'á': 'a', 'ã': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'î': 'i', 'ï': 'i', 'í': 'i',
        'ô': 'o', 'ö': 'o', 'ó': 'o', 'õ': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u', 'ú': 'u',
        'ç': 'c', 'œ': 'oe', 'æ': 'ae',
        'À': 'a', 'Â': 'a', 'Ä': 'a', 'É': 'e', 'È': 'e', 'Ê': 'e', 'Ë': 'e',
        'Î': 'i', 'Ï': 'i', 'Ô': 'o', 'Ö': 'o', 'Ù': 'u', 'Û': 'u', 'Ü': 'u',
        'Ç': 'c', 'Œ': 'oe', 'Æ': 'ae',
    })
    w = w.translate(_ACCENTS)
    return w.strip('.,!?;:()[]{}«»"\'¿¡-').lower()


def _slugify(t: str, max_len: int = 30) -> str:
    slug = re.sub(r'[^a-z0-9]+', '_', _clean_word(t)).strip('_')
    return slug[:max_len] or 'theme'


def _kw_in_text(kw: str, text: str) -> bool:
    """Mot-clé en frontière de mot (préfixe pour les mots longs)."""
    kw = _clean_word(kw)
    if not kw:
        return False
    if len(kw) < 4:
        return re.search(rf'\b{re.escape(kw)}\b', text) is not None
    return re.search(rf'\b{re.escape(kw)}\w*', text) is not None


class HologramSpecializer:
    """Construit un hologramme dédié à partir des centres d'intérêt."""

    def __init__(self, store: HologramStore, encoder: Optional[HolographicEncoder] = None,
                 kb: Optional[List[Tuple]] = None):
        self.store = store
        self.encoder = encoder or HolographicEncoder(dim=512)
        self.kb = kb or []
        self._vocab_cache = {}

    # ── 1. Pool de candidats (pré-filtre lexical par ancre) ───────────────

    def _candidate_pool(self, anchors: List[str]) -> List[Tuple]:
        """
        Faits contenant une ancre (frontière de mot) dans TOUS les hologrammes
        du store + KB. Pré-filtre lexical : le pool passe de ~300k à quelques
        milliers de faits — le scoring vectoriel n'a plus qu'à départager.
        """
        anchors = sorted({a for a in anchors if len(a) >= 3}, key=len, reverse=True)
        pool = []

        # Faits des hologrammes (y compris v1 — seul le texte compte ici)
        for h in self.store.list_holograms():
            try:
                facts, _ = self.store.download(h['id'])
            except Exception:
                continue
            for s, r, o, sec in facts:
                text = f"{s} {r} {o}".lower()
                if any(_kw_in_text(a, text) for a in anchors):
                    pool.append((str(s), str(r), str(o), str(sec)))

        # KB qualitative (harmonique)
        for s, r, o, sec in self.kb:
            text = f"{s} {r} {o}".lower()
            if any(_kw_in_text(a, text) for a in anchors):
                pool.append((str(s), str(r), str(o), str(sec)))

        # Dédoublonnage
        seen = set()
        uniq = []
        for s, r, o, sec in pool:
            key = (s.lower()[:60], r.lower()[:60], o.lower()[:80])
            if key not in seen:
                seen.add(key)
                uniq.append((s, r, o, sec))
        return uniq

    # ── 2. Scoring par résonance token (vectorisé) ────────────────────────

    def _token_scores(self, facts: List[Tuple], anchors: List[str]) -> np.ndarray:
        """Résonance max entre les ψ des ancres et chaque mot des faits."""
        # Vocabulaire des faits
        vocab = {}
        fact_token_idx = []
        for s, r, o, _ in facts:
            toks = [_clean_word(w) for w in re.findall(
                r"[a-zA-ZàâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇœ'-]+", f"{s} {r} {o}")]
            toks = [t for t in toks if len(t) >= 2 and t not in _STOPWORDS]
            idxs = [vocab.setdefault(t, len(vocab)) for t in toks]
            fact_token_idx.append(idxs)

        W_enc = np.array([self.encoder.encode_word(w) for w in vocab],
                         dtype=np.complex128)
        Q = np.array([self.encoder.encode_word(a) for a in anchors
                      if len(a) >= 2], dtype=np.complex128)
        if Q.size == 0:
            return np.zeros(len(facts))

        sims = np.real(Q @ W_enc.conj().T)          # (A, V)
        scores = np.zeros(len(facts))
        for i, idxs in enumerate(fact_token_idx):
            if idxs:
                scores[i] = float(np.max(sims[:, idxs]))
        return np.clip(scores, 0.0, None)

    # ── 3. Construction v2 + pureté ───────────────────────────────────────

    def _build_v2(self, holo_id: str, facts: List[Tuple], metadata: Dict) -> Dict:
        """ψ composants + H + pureté (même format que purify_holograms)."""
        # Pré-encoder les mots uniques
        word_set = set()
        for s, r, o, _ in facts:
            for w in s.split() + r.split() + o.split():
                w = w.strip('.,!?;:')
                if len(w) >= 2:
                    word_set.add(w)
        for w in word_set:
            self.encoder.encode_word(w)

        psi_subjects, psi_relations, psi_objects, psi_facts = [], [], [], []
        for s, r, o, _ in facts:
            ps = self.encoder.encode_word(s)
            pr = self.encoder.encode_word(r)
            po = self.encoder.encode_word(o)
            psi_subjects.append(ps)
            psi_relations.append(pr)
            psi_objects.append(po)
            psi_facts.append(_circular_convolve(_circular_convolve(ps, pr), po))

        H = np.sum(psi_facts, axis=0) / np.sqrt(len(psi_facts))

        # Pureté (signal/bruit) : cohérence moyenne / écart-type
        coh = np.array([float(np.real(np.dot(f, np.conj(H))))
                        for f in psi_facts])
        purity = float(np.mean(coh) / (np.std(coh) + 1e-8))

        holo_path = STORE_DIR / f'{holo_id}.npz'
        np.savez_compressed(
            str(holo_path),
            subjects=np.array([f[0] for f in facts], dtype=object),
            relations=np.array([f[1] for f in facts], dtype=object),
            objects=np.array([f[2] for f in facts], dtype=object),
            sectors=np.array([f[3] for f in facts], dtype=object),
            hologram_memory=H.astype(np.complex64),
            psi_subjects=np.array(psi_subjects, dtype=np.complex64),
            psi_relations=np.array(psi_relations, dtype=np.complex64),
            psi_objects=np.array(psi_objects, dtype=np.complex64),
            amplitudes=np.ones(len(facts), dtype=np.float32),
            version=HOLOGRAM_FORMAT_VERSION,
            kb_hash='specialized_seed',
            domain=metadata.get('domain', ''),
            created_at=time.time(),
        )
        log.info(f"💾 {holo_id}: {len(facts)} faits, pureté={purity:.2f}")

        meta = HologramMeta(
            id=holo_id,
            name=metadata['name'],
            domain=metadata['domain'],
            icon=metadata.get('icon', '🎯'),
            description=metadata['description'],
            sectors=metadata.get('sectors', []),
            top_concepts=metadata.get('top_concepts', []),
            facts_count=len(facts),
            quality_score=metadata.get('quality_score', 0.5),
            author='KA-Specializer',
            type='personal',
            created_at=time.time(),
            benchmark_questions=metadata.get('benchmark_count', 0),
            version=HOLOGRAM_FORMAT_VERSION,
            kb_hash='specialized_seed',
        )
        self.store._registry[holo_id] = meta
        self.store._save_registry()
        return {'purity': purity}

    # ── 4. Benchmark interne (sans oracle) ────────────────────────────────

    def _benchmark(self, holo_id: str, interests: List[str],
                   anchors_by_interest: Dict[str, List[str]]) -> Tuple[float, float]:
        """
        Précision@1 : chaque intérêt est interrogé (« Qu est-ce que X ? ») dans
        le rappel M4 ; le fait top doit contenir une ancre ou résonner ≥ seuil.
        """
        hits = 0
        for interest in interests:
            q = f"Qu est-ce que {interest} ?"
            try:
                recalled = self.store.recall(holo_id, q, top_k=1)
            except Exception:
                continue
            if not recalled:
                continue
            s, r, o, _, score = recalled[0]
            text = f"{s} {r} {o}".lower()
            anchors = anchors_by_interest.get(interest, [])
            if any(_kw_in_text(a, text) for a in anchors) or score >= BENCHMARK_SIM:
                hits += 1
        precision = hits / max(1, len(interests))
        return precision, precision

    # ── 5. Pipeline complet ───────────────────────────────────────────────

    def build(self, interests: List[str], language: str = 'fr',
              max_facts: int = SEED_MAX_FACTS,
              benchmark: bool = True) -> Dict:
        t0 = time.time()
        interests = [_clean_word(i) for i in interests if _clean_word(i)]
        interests = list(dict.fromkeys(interests))[:4]   # dédup, max 4
        if not interests:
            return {'error': 'Aucun centre d intérêt valide'}

        # Ancres : mots du sujet + équivalents bilingues
        anchors_by_interest = {}
        all_anchors = set()
        for interest in interests:
            anchors = [interest] + ANCHOR_MAP.get(interest, [])
            anchors = list(dict.fromkeys(_clean_word(a) for a in anchors if _clean_word(a)))
            anchors_by_interest[interest] = anchors
            all_anchors.update(anchors)

        # Pool lexical
        pool = self._candidate_pool(list(all_anchors))
        if not pool:
            return {'error': f'Aucun fait contenant {interests} dans le store',
                    'interests': interests}

        # Résonance token → rang
        scores = self._token_scores(pool, list(all_anchors))
        lex = np.array([any(_kw_in_text(a, f"{s} {r} {o}")
                            for a in all_anchors) for s, r, o, _ in pool])

        # Garder : ancre lexicale (or) OU résonance franche
        keep = lex | (scores >= SEMANTIC_THRESHOLD)
        ranked = sorted(((float(scores[i]), bool(lex[i]), pool[i])
                         for i in np.where(keep)[0]),
                        key=lambda x: (-x[1], -x[0]))
        chosen = [f for _, _, f in ranked[:max_facts]]
        if len(chosen) < SEED_MIN_FACTS:
            return {'error': f'Seed trop pauvre ({len(chosen)} faits < {SEED_MIN_FACTS}) '
                             f'pour {interests}', 'interests': interests,
                    'candidates_scored': int(len(pool))}

        # Construire
        holo_id = 'personal_' + _slugify(interests[0])
        if holo_id in self.store._registry:
            holo_id = f"{holo_id}_{int(time.time()) % 10000}"
        domain = interests[0].replace('_', ' ')
        build_info = self._build_v2(holo_id, chosen, {
            'name': f"🎯 {domain}",
            'domain': domain,
            'description': f"Hologramme dédié aux centres d'intérêt : {', '.join(interests)}",
            'top_concepts': [c for c in all_anchors][:10],
            'benchmark_count': len(interests),
        })

        # Benchmark interne → quality_score
        quality_score = 0.5
        precision = 0.0
        if benchmark:
            precision, _ = self._benchmark(holo_id, interests, anchors_by_interest)
            quality_score = round(0.6 * precision + 0.4 * min(1.0, build_info['purity'] / 3.0), 3)
            meta = self.store._registry[holo_id]
            meta.quality_score = quality_score
            self.store._save_registry()

        # 🌐 Seed mince (< THIN_SEED) → enrichissement Wikipedia automatique :
        # les sujets étroits n'ont pas assez de faits dans le corpus ; on les
        # complète depuis l'extrait Wikipedia filtré par les mêmes ancres.
        # Si le réseau échoue, le seed reste utilisable tel quel.
        enriched = 0
        if len(chosen) < THIN_SEED:
            try:
                enrich_result = self.enrich_from_wiki(holo_id, interests,
                                                      language, max_new=120)
                enriched = int(enrich_result.get('added', 0))
            except Exception as e:
                log.warning(f"⚠ Auto-enrichissement {holo_id} échoué: {e}")

        return {
            'holo_id': holo_id,
            'interests': interests,
            'anchors': sorted(all_anchors)[:12],
            'facts_count': len(chosen) + enriched,
            'candidates_scored': int(len(pool)),
            'purity': round(build_info['purity'], 3),
            'precision_at_1': round(precision, 3),
            'quality_score': quality_score,
            'enriched': enriched,
            'build_ms': int((time.time() - t0) * 1000),
            'source': 'hologram-specialize',
        }

    # ── 6. Enrichissement Wikipedia (hook background) ─────────────────────

    def enrich_from_wiki(self, holo_id: str, interests: List[str],
                         language: str = 'fr', max_new: int = 120) -> Dict:
        """
        Ajoute des faits extraits de Wikipedia (TripleExtractor pré-entraîné
        sur le seed) filtrés par les mêmes ancres. Aucune ancre = aucun fait.
        """
        t0 = time.time()
        try:
            from web_retriever import WebRetriever
            from triple_extractor import TripleExtractor
        except Exception as e:
            return {'error': f'Dépendances: {e}'}

        # Seed actuel (pré-entraînement de l'extracteur + ancres existantes)
        facts, _ = self.store.download(holo_id)
        anchors = set()
        for interest in interests:
            anchors.update(ANCHOR_MAP.get(interest, [interest]))
        anchors = {_clean_word(a) for a in anchors if len(_clean_word(a)) >= 3}

        extractor = TripleExtractor()
        try:
            extractor.pre_train(facts, max_patterns=30)
        except Exception:
            pass

        retriever = WebRetriever()
        new_facts = []
        # Sujets-fragments à rejeter : « trois autres qui provoquent... »,
        # « certains chercheurs affirment... » — le triple extractor coupe
        # parfois au milieu d'une phrase.
        _FRAGMENT_STARTS = {'un', 'une', 'le', 'la', 'les', 'des', 'du', 'de',
                            'ce', 'ces', 'cette', 'qui', 'que', 'dont', 'ou',
                            'ceux', 'celles', 'certain', 'certains', 'certaines',
                            'trois', 'deux', 'quatre', 'plus', 'tous', 'toutes',
                            'tout', 'toute', 'l', 'd', 'en', 'au', 'aux', 'par',
                            'avec', 'pour', 'il', 'elle', 'ils', 'elles', 'on'}
        for interest in interests:
            try:
                doc = retriever.search_wikipedia(interest, lang=language)
            except Exception:
                continue
            if not doc:
                continue
            text = doc.get('extract') or doc.get('summary') or ''
            if not text:
                continue
            try:
                triples = extractor.extract(text, max_triples=80)
            except Exception:
                continue
            for s, r, o, sec in triples:
                s_clean = _clean_word(s)
                if not s_clean or s_clean.split()[0] in _FRAGMENT_STARTS:
                    continue
                t = f"{s} {r} {o}".lower()
                if any(_kw_in_text(a, t) for a in anchors):
                    new_facts.append((str(s), str(r), str(o), str(sec)))

        # Dédoublonnage avec le seed
        seen = {(f[0].lower()[:60], f[1].lower()[:60], f[2].lower()[:80]) for f in facts}
        added = []
        for f in new_facts:
            key = (f[0].lower()[:60], f[1].lower()[:60], f[2].lower()[:80])
            if key not in seen and len(added) < max_new:
                seen.add(key)
                added.append(f)

        if not added:
            return {'holo_id': holo_id, 'added': 0, 'msg': 'Aucun fait nouveau',
                    'ms': int((time.time() - t0) * 1000)}

        # Rebuild du npz avec les nouveaux faits
        merged = list(facts) + added
        meta_dict = self.store._registry[holo_id]
        self._build_v2(holo_id, merged, {
            'name': meta_dict.name,
            'domain': meta_dict.domain,
            'description': meta_dict.description,
            'top_concepts': meta_dict.top_concepts,
            'benchmark_count': meta_dict.benchmark_questions,
            'quality_score': meta_dict.quality_score,
        })
        # Re-mesurer le benchmark
        interests_clean = [_clean_word(i) for i in interests]
        anchors_by = {i: [_clean_word(a) for a in ANCHOR_MAP.get(i, [i])]
                      for i in interests_clean}
        precision, _ = self._benchmark(holo_id, interests_clean, anchors_by)
        meta = self.store._registry[holo_id]
        meta.quality_score = round(0.6 * precision + 0.4 * meta.quality_score, 3)
        self.store._save_registry()

        return {'holo_id': holo_id, 'added': len(added),
                'facts_count': len(merged), 'precision_at_1': round(precision, 3),
                'quality_score': meta.quality_score,
                'ms': int((time.time() - t0) * 1000)}


def dispatch_enrichment(store: HologramStore, holo_id: str, interests: List[str],
                        language: str = 'fr') -> None:
    """Enrichissement en arrière-plan (thread daemon)."""
    def _run():
        try:
            spec = HologramSpecializer(store)
            result = spec.enrich_from_wiki(holo_id, interests, language)
            log.info(f"🌐 Enrichissement {holo_id}: {result.get('added', 0)} faits — {result}")
        except Exception as e:
            log.error(f"⚠ Enrichissement {holo_id} échoué: {e}")
    threading.Thread(target=_run, daemon=True).start()


if __name__ == '__main__':
    # Test rapide hors serveur
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    store = HologramStore()
    try:
        from harmonic_model import KNOWLEDGE_BASE
        kb = [(str(s), str(r), str(o), str(sec)) for s, r, o, sec in KNOWLEDGE_BASE]
    except Exception:
        kb = []
    spec = HologramSpecializer(store, kb=kb)
    result = spec.build(["diabete"], language="fr")
    print(result)
