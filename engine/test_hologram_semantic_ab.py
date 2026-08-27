"""
🌊 TEST HOLOGRAMME CLINIQUE — Avec Encodeur Sémantique Entraîné
=================================================================
Intègre l'encodeur sémantique (semantic_clinique_full.json, 3925 mots)
dans le SpecializedHologram et teste la précision sur des requêtes
médicales réelles.

Comparaison A/B :
  A. Hologramme SANS sémantique (FNV1a seul) → baseline
  B. Hologramme AVEC sémantique (PPMI + SVD) → cible

Le but : mesurer le gain de précision apporté par la sémantique.

Auteur : THU — Univers-Holistique
Date   : 2026-08-23
"""

import sys, os, math, time, json, re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

_ENGINE_DIR = Path(__file__).resolve().parent

FACTS_DIR = _ENGINE_DIR / "vital-ka" / "data" / "medical_holograms"
SEMANTIC_PATH = _ENGINE_DIR / "vital-ka" / "data" / "semantic_clinique_full.json"

# Domaines à charger
DOMAINS = [
    "PALUDISME", "CLINIQUE", "MALADIES", "URGENCES",
    "PHARMACIE", "VIH_TB", "PEDIATRIE", "NUTRITION",
]

PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1.0 / PHI
DIM = 512
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════
# IMPORTS ONDULATOIRES
# ═══════════════════════════════════════════════════════════════════

sys.path.insert(0, str(_ENGINE_DIR / "vital-ka" / "core" / "python"))

from wave_lang import encode, bind, unbind, superpose, resonate, normalize, PHI as WPHI, ALPHA
from optimal_hologram_builder import (
    SpecializedHologram, HologramSpec, MIN_COHERENCE, MAX_CAPACITY, OptimalHologramBuilder
)

# ═══════════════════════════════════════════════════════════════════
# CHARGEUR D'ENCODEUR SÉMANTIQUE
# ═══════════════════════════════════════════════════════════════════

class SemanticEncoder:
    """Encodeur sémantique utilisant les phases S¹ entraînées."""
    
    def __init__(self, phases_path: Path):
        print(f"📂 Chargement de l'encodeur sémantique : {phases_path.name}")
        with open(phases_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.words = data['words']
        self.phases = data['phases']        # [[θ₀,...,θ₇], ...]
        self.n_phases = data['n_phases']    # 8
        self.singular_values = data.get('singular_values', [])
        
        self.word_to_idx = {w: i for i, w in enumerate(self.words)}
        self._cache: Dict[str, np.ndarray] = {}
        
        print(f"   ✅ {len(self.words)} mots, {self.n_phases} phases/mot")
        if self.singular_values:
            print(f"   σ₁={self.singular_values[0]:.1f}, σ₂={self.singular_values[1]:.1f}")
    
    def encode(self, word: str) -> np.ndarray:
        """Encode un mot en vecteur d'onde sémantique."""
        # Nettoyer
        word_clean = word.lower().strip().replace('_', ' ')
        word_clean = re.sub(r'[^a-zà-ÿ0-9\s]', '', word_clean).strip()
        
        if word_clean in self._cache:
            return self._cache[word_clean].copy()
        
        # Si le mot est dans le vocabulaire → phase sémantique
        idx = self.word_to_idx.get(word_clean)
        if idx is not None:
            phases = self.phases[idx]
            
            # Construire le vecteur : utiliser la 1ère phase
            # + bruit HRR pour orthogonalité
            theta = phases[0]
            
            # Amplitude basée sur la cohérence inter-phases
            # (si toutes les phases pointent dans la même direction → mot très informatif)
            phase_vecs = np.array([[math.cos(p), math.sin(p)] for p in phases])
            mean_vec = phase_vecs.mean(axis=0)
            amplitude = min(1.0, np.linalg.norm(mean_vec) * 2.0)
            
            # Phase principale
            psi = np.exp(1j * theta)
            
            # Bruit HRR (déterministe, pour orthogonalité binding)
            seed = hash(word_clean) & 0xFFFFFFFF
            rng = np.random.RandomState(seed)
            noise = (rng.randn(DIM) + 1j * rng.randn(DIM)) / np.sqrt(DIM)
            
            # Combiner : amplitude × (phase sémantique + ε × bruit HRR)
            epsilon = max(0.05, 0.5 - amplitude * 0.3)
            psi_full = amplitude * psi + epsilon * noise
            psi_full = normalize(psi_full)
            
            self._cache[word_clean] = psi_full.copy()
            return psi_full
        
        # Fallback FNV1a
        return encode(word, dim=DIM)
    
    def multi_word_psi(self, words: List[str]) -> np.ndarray:
        """Superpose plusieurs mots en un seul vecteur."""
        result = np.zeros(DIM, dtype=np.complex128)
        for w in words:
            result += self.encode(w)
        return normalize(result)


# ═══════════════════════════════════════════════════════════════════
# HOLOGRAMME AVEC SÉMANTIQUE
# ═══════════════════════════════════════════════════════════════════

class SemanticHologram:
    """Hologramme spécialisé avec encodeur sémantique intégré."""
    
    def __init__(self, domain: str, semantic_encoder: SemanticEncoder = None):
        self.domain = domain
        self.semantic = semantic_encoder
        self.memory = np.zeros(DIM, dtype=np.complex128)
        self.facts: List[Tuple[str, str, str]] = []
        self._fact_count = 0
        self._query_count = 0
        self._hallucinated = 0
    
    def store_facts(self, facts_list: List[dict], max_facts: int = 5000):
        """Stocke les faits dans la mémoire holographique avec encodage sémantique."""
        unique = {}
        for fact in facts_list:
            s = str(fact.get('s', '')).strip().replace('_', ' ')
            r = str(fact.get('r', '')).strip().replace('_', ' ')
            o = str(fact.get('o', '')).strip().replace('_', ' ')
            if not s or not o:
                continue
            
            s = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', s).strip()
            o = re.sub(r'[^a-zA-ZÀ-ÿ0-9\s]', ' ', o).strip()
            
            key = (s.lower(), r.lower(), o.lower())
            if key not in unique:
                unique[key] = (s, r, o)
        
        facts_to_store = list(unique.values())[:max_facts]
        print(f"   Stockage de {len(facts_to_store)} faits uniques...")
        
        for s, r, o in facts_to_store:
            if self.semantic:
                psi_s = self.semantic.encode(s)
                psi_r = self.semantic.encode(r)
                psi_o = self.semantic.encode(o)
            else:
                psi_s = encode(s, dim=DIM)
                psi_r = encode(r, dim=DIM)
                psi_o = encode(o, dim=DIM)
            
            fact = bind(psi_s, bind(psi_r, psi_o))
            self.memory = self.memory + fact
            self.facts.append((s, r, o))
            self._fact_count += 1
        
        print(f"   ✅ {self._fact_count} faits stockés")
    
    def query(self, question: str, top_k: int = 5) -> dict:
        """
        Interroge l'hologramme avec SCORING SÉMANTIQUE DIRECT.
        
        DIFFÉRENCE CLÉ avec la version précédente :
          AVANT : UNBIND(H, ψ_Q) → ψ_R → RESONATE(ψ_R, BIND(ψ_s, ψ_r, ψ_o))
                 → Les phases sont BROUILLÉES par la convolution circulaire
                 → L'information sémantique est perdue
          
          APRÈS : Pour chaque fait, scoring DIRECT par similarité de phase :
                 score = α·resonate(ψ_Q, ψ_s) + β·resonate(ψ_Q, ψ_o)
                 → Les phases sont PRÉSERVÉES
                 → La similarité sémantique est capturée
        
        Le UNBIND holographique n'est utilisé que pour le pré-filtrage
        (trouver les candidats). Le scoring final est SÉMANTIQUE DIRECT.
        """
        t0 = time.time()
        self._query_count += 1
        
        # Tokeniser
        stopwords = {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
                     'au', 'aux', 'en', 'pour', 'avec', 'sur', 'est', 'sont', 'ce',
                     'cette', 'dans', 'à', 'a', 'que', 'qui', 'quoi', 'comment',
                     'qu', 'quel', 'quelle', 'pourquoi', 'c', 'd', 'l', 's', 'n',
                     'pas', 'ne', 'plus', 'tout', 'tous', 'faire', 'dit', 'peut',
                     'son', 'sa', 'ses', 'il', 'elle', 'très', 'bien', 'être',
                     'the', 'is', 'are', 'of', 'in', 'on', 'at', 'to', 'for'}
        
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", question.lower())
        content = [t for t in tokens if t not in stopwords and len(t) > 1]
        if not content:
            content = tokens
        
        # ── ÉTAPE 1 : Pré-filtre lexical (trouver les candidats) ──
        # Un fait est candidat si son sujet ou objet partage des mots avec la question
        q_words = set(content)
        candidate_indices = []
        for i, (s, r, o) in enumerate(self.facts):
            s_words = set(re.findall(r"[a-zà-ÿ0-9]+", s.lower()))
            o_words = set(re.findall(r"[a-zà-ÿ0-9]+", o.lower()))
            if (s_words & q_words) or (o_words & q_words):
                candidate_indices.append(i)
        
        if not candidate_indices:
            candidate_indices = list(range(len(self.facts)))
        
        # ── ÉTAPE 2 : Scoring HYBRIDE (sémantique + lexical) ──
        if self.semantic:
            psi_Q = self.semantic.multi_word_psi(content)
        else:
            psi_Q = normalize(sum(encode(w, dim=DIM) for w in content))
        
        fact_scores = []
        for i in candidate_indices:
            s, r, o = self.facts[i]
            
            # SCORE SÉMANTIQUE : similarité de phase question ↔ sujet
            if self.semantic:
                psi_s = self.semantic.encode(s)
            else:
                psi_s = encode(s, dim=DIM)
            score_sem = resonate(psi_Q, psi_s)
            
            # BONUS LEXICAL : mots de la question dans relation + objet
            r_o_text = (r + " " + o).lower().replace('_', ' ')
            r_o_words = set(re.findall(r"[a-zà-ÿ0-9]+", r_o_text))
            matches = q_words & r_o_words
            lexical_bonus = len(matches) * 0.2
            
            # Score final = sémantique (concept) + lexical (spécificité)
            score = score_sem + lexical_bonus
            
            fact_scores.append((score, s, r, o, i, score_sem, lexical_bonus, len(matches)))
        
        fact_scores.sort(key=lambda x: -x[0])
        
        # Seuil
        threshold = 0.05
        reliable = [x for x in fact_scores if x[0] >= threshold]
        
        hallucinated = len(reliable) == 0
        if hallucinated:
            self._hallucinated += 1
            answer = "Je ne dispose pas d'information fiable sur ce sujet."
            sources = []
            max_coh = fact_scores[0][0] if fact_scores else 0.0
        else:
            top = reliable[:top_k]
            max_coh = top[0][0]
            answer = "\n".join(f"• {s} {r} {o} [sem={ss:.2f} lex={lb:.2f}]" 
                              for _, s, r, o, _, ss, lb, _ in top)
            sources = [{"subject": s, "relation": r, "object": o, 
                       "score": float(sc), "score_sem": float(ss), "lex_bonus": float(lb)} 
                       for sc, s, r, o, _, ss, lb, _ in top]
        
        return {
            "answer": answer,
            "sources": sources,
            "coherence": float(max_coh),
            "hallucinated": hallucinated,
            "time_ms": (time.time() - t0) * 1000,
            "n_candidates": len(candidate_indices),
            "n_reliable": len(reliable),
        }


# ═══════════════════════════════════════════════════════════════════
# TEST A/B — Avec vs Sans Sémantique
# ═══════════════════════════════════════════════════════════════════

def load_facts_for_domains(domains: List[str]) -> List[dict]:
    """Charge les faits des domaines spécifiés."""
    all_facts = []
    for dom in domains:
        path = FACTS_DIR / f"{dom}_facts.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            all_facts.extend(data)
            print(f"   📂 {dom:<20s} : {len(data):>6,} faits")
    print(f"   ✅ Total : {len(all_facts):,} faits")
    return all_facts


def run_ab_test():
    """Test A/B : hologramme avec vs sans sémantique."""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🧪 TEST A/B — Hologramme AVEC vs SANS Sémantique          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Charger l'encodeur sémantique
    semantic = None
    if SEMANTIC_PATH.exists():
        semantic = SemanticEncoder(SEMANTIC_PATH)
        print()
    
    # Charger les faits
    facts = load_facts_for_domains(DOMAINS)
    
    # Construire les deux hologrammes
    print(f"\n🔨 Construction des hologrammes...")
    
    # A. SANS sémantique (baseline)
    holo_baseline = SemanticHologram("medical", semantic_encoder=None)
    holo_baseline.store_facts(facts)
    
    # B. AVEC sémantique
    holo_semantic = SemanticHologram("medical", semantic_encoder=semantic)
    if semantic:
        holo_semantic.store_facts(facts)
    
    # Requêtes de test
    test_queries = [
        # ── Paludisme ──
        {
            "id": 1,
            "query": "symptômes du paludisme simple",
            "domain": "paludisme",
            "expected": ["fièvre", "frissons", "sueurs", "maux", "tête", "nausées", "fatigue"],
        },
        {
            "id": 2,
            "query": "traitement paludisme grave",
            "domain": "paludisme",
            "expected": ["artésunate", "quinine", "intraveineuse"],
        },
        {
            "id": 3,
            "query": "comment prévenir le paludisme",
            "domain": "paludisme",
            "expected": ["moustiquaire", "imprégnée", "tpi", "pulvérisation"],
        },
        
        # ── VIH/TB ──
        {
            "id": 4,
            "query": "traitement antirétroviral première ligne",
            "domain": "vih",
            "expected": ["tdf", "3tc", "dtg", "dolutégravir", "ténofovir"],
        },
        {
            "id": 5,
            "query": "comment diagnostiquer la tuberculose",
            "domain": "tb",
            "expected": ["bacilloscopie", "genexpert", "crachat", "bk"],
        },
        
        # ── Pharmacie ──
        {
            "id": 6,
            "query": "posologie paracétamol adulte",
            "domain": "pharmacie",
            "expected": ["paracétamol", "gramme", "dose", "intervalle"],
        },
        {
            "id": 7,
            "query": "contre indications ibuprofène",
            "domain": "pharmacie",
            "expected": ["ulcère", "grossesse", "rénal", "asthme"],
        },
        
        # ── Urgences ──
        {
            "id": 8,
            "query": "signes détresse respiratoire",
            "domain": "urgences",
            "expected": ["dyspnée", "cyanose", "tirage", "oxygène"],
        },
        {
            "id": 9,
            "query": "conduite à tenir arrêt cardiaque",
            "domain": "urgences",
            "expected": ["réanimation", "massage", "cardiaque", "défibrillation"],
        },
        
        # ── Nutrition ──
        {
            "id": 10,
            "query": "malnutrition aiguë sévère prise en charge",
            "domain": "nutrition",
            "expected": ["plumpynut", "atpe", "lait", "thérapeutique", "appétit"],
        },
        
        # ── Pédiatrie ──
        {
            "id": 11,
            "query": "signes gravité chez enfant fébrile",
            "domain": "pediatrie",
            "expected": ["convulsion", "léthargie", "refus", "boire", "geignement"],
        },
        
        # ── Hors domaine ──
        {
            "id": 12,
            "query": "comment cuisiner un gâteau au chocolat",
            "domain": "hors_domaine",
            "expected": [],
        },
    ]
    
    print(f"\n{'═'*70}")
    print("  🔍 REQUÊTES DE TEST")
    print("═" * 70)
    
    baseline_score = 0
    semantic_score = 0
    baseline_hall = 0
    semantic_hall = 0
    n_queries = len(test_queries)
    
    for q in test_queries:
        query = q["query"]
        expected = q["expected"]
        is_hors_domaine = q["domain"] == "hors_domaine"
        
        # Hologramme SANS sémantique
        r_base = holo_baseline.query(query)
        
        # Hologramme AVEC sémantique
        r_sem = holo_semantic.query(query) if semantic else r_base
        
        # Évaluer
        def score_response(result, expected_tokens):
            if result["hallucinated"]:
                return 0, True
            
            answer_lower = result["answer"].lower()
            hits = sum(1 for e in expected_tokens if e.lower() in answer_lower)
            recall = hits / len(expected_tokens) if expected_tokens else 0
            return recall, False
        
        recall_base, hall_base = score_response(r_base, expected)
        recall_sem, hall_sem = score_response(r_sem, expected)
        
        if is_hors_domaine:
            # Pour hors-domaine, on attend "je ne sais pas"
            if r_base["hallucinated"]:
                baseline_score += 1
            if r_sem["hallucinated"]:
                semantic_score += 1
        else:
            if recall_base >= 0.3:
                baseline_score += 1
            if recall_sem >= 0.3:
                semantic_score += 1
        
        if hall_base:
            baseline_hall += 1
        if hall_sem:
            semantic_hall += 1
        
        print(f"\n  [{q['id']:2d}] 🔍 {query}")
        print(f"       🎯 Attendus : {', '.join(expected[:5]) if expected else 'AUCUN (hors domaine)'}")
        print(f"       📡 SANS sémantique : {'🛑' if hall_base else '✅'} {r_base['answer'][:100]}")
        if semantic:
            print(f"       🧠 AVEC sémantique : {'🛑' if hall_sem else '✅'} {r_sem['answer'][:100]}")
        print(f"       ⚡ Temps : base={r_base['time_ms']:.1f}ms" + 
              (f", sem={r_sem['time_ms']:.1f}ms" if semantic else ""))
    
    # Synthèse
    print(f"\n{'═'*70}")
    print("  📊 RÉSULTATS A/B")
    print("═" * 70)
    print()
    print(f"  {'Métrique':<30s} {'SANS sémantique':>18s} {'AVEC sémantique':>18s} {'Gain':>10s}")
    print(f"  {'─'*30} {'─'*18} {'─'*18} {'─'*10}")
    print(f"  {'Précision':<30s} {baseline_score/n_queries:>17.0%} {semantic_score/n_queries:>17.0%} {semantic_score-baseline_score:>+10d}")
    print(f"  {'Hallucination':<30s} {baseline_hall/n_queries:>17.0%} {semantic_hall/n_queries:>17.0%} {semantic_hall-baseline_hall:>+10d}")
    print(f"  {'Faits stockés':<30s} {holo_baseline._fact_count:>18,d} {holo_semantic._fact_count if semantic else 0:>18,d}")
    print()
    
    # Vérification qualitative
    print("═" * 70)
    print("  🧠 VÉRIFICATION QUALITATIVE — Similarité sémantique")
    print("═" * 70)
    print()
    
    if semantic:
        test_pairs = [
            ("paludisme", "fièvre"),
            ("paludisme", "frissons"),
            ("paludisme", "artésunate"),
            ("anémie", "pâleur"),
            ("pneumonie", "toux"),
            ("diabète", "glycémie"),
            ("hypertension", "tension"),
            ("paludisme", "chaise"),
            ("fièvre", "voiture"),
        ]
        
        print(f"  {'Paire':<30s} {'Similarité':>10s} {'Attendu':>10s} {'OK':>6s}")
        print(f"  {'─'*30} {'─'*10} {'─'*10} {'─'*6}")
        
        sem_wins = 0
        for a, b in test_pairs:
            psi_a = semantic.encode(a)
            psi_b = semantic.encode(b)
            sim = resonate(psi_a, psi_b)
            
            psi_a_fnv = encode(a, dim=DIM)
            psi_b_fnv = encode(b, dim=DIM)
            sim_fnv = resonate(psi_a_fnv, psi_b_fnv)
            
            # Est-ce que la similarité sémantique est plus forte ?
            related = any(w in b or w in a for w in 
                         ["fièvre", "frissons", "artésunate", "pâleur", "toux", "glycémie", "tension"])
            
            if related:
                ok = sim > sim_fnv
                if ok:
                    sem_wins += 1
            else:
                ok = abs(sim) < 0.5
            
            print(f"  {a+' ↔ '+b:<30s} {sim:>+10.4f} {'haute' if related else '~0':>10s} {'✅' if ok else '❌':>6s}")
        
        print()
        print(f"  📊 L'encodeur sémantique bat le FNV1a sur {sem_wins}/{sum(1 for a,b in test_pairs if any(w in b or w in a for w in ['fièvre','frissons','artésunate','pâleur','toux','glycémie','tension']))} paires liées")
    
    print()
    print(f"  📁 Encodeur sémantique : {SEMANTIC_PATH}")
    print(f"  📁 Faits CLINIQUE       : {FACTS_DIR}")
    print()


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_ab_test()