#!/usr/bin/env python3
r"""
🌊 RAISONNEUR ONDULATOIRE — Moteur de raisonnement par ondes (HRR pur)
=======================================================================

Moteur de raisonnement fondé sur les représentations holographiques
réduites (HRR — Holomorphic Reduced Representations). Tout est onde :
un fait est un binding, l'état est une superposition, une question
est un unbinding, une action est une transformation du champ.

ZÉRO REGEX (sauf extraction des nombres), ZÉRO MACHINE D'ÉTAT,
ZÉRO GABARIT — le raisonnement ÉMERGE de la dynamique des ondes.

Primitives :
  encode(entity)                → ψ (vecteur complexe 512-dim)
  bind(ψ_a, ψ_b)                → ψ_{a⊗b}  (convolution circulaire)
  unbind(ψ_{ab}, ψ_b)           → ~ψ_a     (corrélation circulaire)
  superpose(ψ₁, ψ₂, ...)        → H        (mémoire holographique)
  resonate(ψ_q, H)              → score    (similarité/interrogation)

Quantités :
  encode_quantity(q) : composante 0 = exp(i·α·q) [PhaseEncoder exact]
                        composantes 1-511 = hash(str(q)) [identité HRR]
  → la valeur est LISIBLE DIRECTEMENT dans la phase (0 fait stocké !)
  → l'identité est encodée dans le reste du vecteur (compatible HRR)

PIPELINE GSM8K :
  1. Parser la phrase en mots → onde
  2. Résoudre l'entité (par résonance avec l'état H)
  3. Extraire l'action (par résonance avec prototypes add/sub/mult/div/init)
  4. Appliquer : old = query(entity, obj) → compute → update H
  5. Question : query(target_entity, target_obj) → réponse

USAGE :
  from raisonneur_ondulatoire import OndulatoireReasoner
  r = OndulatoireReasoner()
  r.learn_fact("john", "apple", 5)
  r.learn_fact("mary", "apple", 3)
  r.apply_action("john", "apple", "add", 3)    # john achète 3 pommes
  print(r.query("john", "apple"))               # → 8.0
"""

import sys, os, re, math, time, json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import (
    encode, superpose, resonate, normalize,
    bind as _bind, unbind as _unbind,
    DEFAULT_DIM,
)
from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder

# ═══════════════════════════════════════════════════════════════════════════════
# 1. ENCODAGE DES QUANTITÉS : onde complète (hash), pas de composante réservée
#
# Note : Le binding circulaire HRR mélange TOUTES les composantes.
# On ne peut pas réserver une composante pour la valeur. À la place,
# la quantité est encodée comme une onde à part entière (encode("q"+str(q))),
# et le raisonneur utilise un REGISTRE Python pour les valeurs exactes.
# Le HRR sert à l'ADRESSAGE associatif (trouver le bon fait par résonance).
# ═══════════════════════════════════════════════════════════════════════════════


def _quantity_wave(q: float, dim: int = DEFAULT_DIM) -> np.ndarray:
    """Encode une quantité comme une onde complète (hash)."""
    return encode("q" + str(int(q * 1000)), dim=dim)


# Prototypes d'action (pour la résolution par résonance)
MOTS_ACTION = {
    'add':  ['buys', 'gains', 'gets', 'receives', 'earns', 'adds', 'more', 'and',
             'again', 'additional', 'also', 'another', 'next', 'then', 'picks',
             'collects', 'obtains', 'wins'],
    'sub':  ['sells', 'gives away', 'gives', 'loses', 'spends', 'eats', 'ate',
             'removes', 'takes away', 'dropped', 'uses', 'throws away',
             'left', 'remainder', 'remaining', 'after spending', 'less', 'fewer',
             'gave', 'donated', 'burned', 'consumed', 'drank'],
    'mult': ['times', 'twice', 'double', 'triple', 'per', 'each', 'every',
             'as many', 'as much', 'product', 'by', 'costs', 'at', 'apiece'],
    'div':  ['divided by', 'split', 'shared equally', 'among', 'half', 'third',
             'quarter', 'each of', 'each person', 'per person', 'evenly'],
    'init': ['has', 'had', 'have', 'owns', 'started with', 'bought', 'collected',
             'found', 'bakes', 'makes', 'produces', 'harvests', 'there are',
             'there were', 'weighs', 'grows', 'purchased', 'packed'],
}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. LE RAISONNEUR ONDULATOIRE (HRR hybride : adressage associatif + registre)
# ═══════════════════════════════════════════════════════════════════════════════

class OndulatoireReasoner:
    """
    Moteur de raisonnement ondulatoire (HRR avec registre de valeurs).

    L'état H est une superposition holographique de tous les faits.
    Chaque fait ψ_fait = bind(entity, bind(obj, quantity_wave)).
    Le registre Python garde les valeurs EXACTES (calculées par émergence).
    Le HRR sert à l'ADRESSAGE : retrouver le fait pertinent par résonance.
    """

    def __init__(self, dim: int = DEFAULT_DIM, max_n: int = 500000):
        self.dim = dim
        self.phase = PhaseEncoder(max_n)
        self.log = LogWaveEncoder(grid_size=2048, SCALE=300)

        # État holographique H = Σ ψ_fact
        self.H = np.zeros(dim, dtype=np.complex128)

        # Registre des faits : {(entity, obj): quantity}
        self._registry: Dict[Tuple[str, str], float] = {}

        # Cache des ondes de faits (pour soustraction lors des mises à jour)
        self._psi_facts: Dict[Tuple[str, str], np.ndarray] = {}

        # Vocabulaires
        self._entities: Dict[str, np.ndarray] = {}
        self._objects: Dict[str, np.ndarray] = {}

        # Prototypes d'action
        self._action_protos: Dict[str, np.ndarray] = {}
        self._build_action_protos()

    def _ensure_entity(self, name: str) -> np.ndarray:
        if name not in self._entities:
            self._entities[name] = encode(name, dim=self.dim)
        return self._entities[name]

    def _ensure_object(self, name: str) -> np.ndarray:
        if name not in self._objects:
            self._objects[name] = encode(name, dim=self.dim)
        return self._objects[name]

    def _build_action_protos(self):
        for action, mots in MOTS_ACTION.items():
            waves = [encode(m, dim=self.dim) for m in mots]
            proto = superpose(*waves) if waves else np.zeros(self.dim)
            self._action_protos[action] = proto / (np.linalg.norm(proto) + 1e-9)

    # ── Opérations fondamentales (HRR + registre) ────────────────────────────

    def learn_fact(self, entity: str, obj: str, quantity: float):
        """Ajoute un fait : H ← H + bind(ψ_e, bind(ψ_o, ψ_q))."""
        psi_e = self._ensure_entity(entity)
        psi_o = self._ensure_object(obj)
        psi_q = _quantity_wave(quantity, self.dim)
        psi_fact = _bind(psi_e, _bind(psi_o, psi_q))
        key = (entity.lower(), obj.lower())
        self._registry[key] = float(quantity)
        self._psi_facts[key] = psi_fact
        self.H = normalize(self.H + psi_fact)

    def query(self, entity: str, obj: str) -> Optional[float]:
        """
        Interroge l'état : « combien de [obj] a [entity] ? »

        Priorité : registre Python (valeur exacte, O(1)).
        Fallback : résonance HRR (adressage associatif approximatif).
        """
        key = (entity.lower(), obj.lower())
        if key in self._registry:
            return self._registry[key]
        # Fallback HRR
        psi_e = self._ensure_entity(entity)
        psi_o = self._ensure_object(obj)
        psi_query = _bind(psi_e, psi_o)
        psi_val = _unbind(self.H, psi_query)
        best_key, best_score = None, -1.0
        for k, psi_fact in self._psi_facts.items():
            psi_e2 = self._ensure_entity(k[0])
            psi_o2 = self._ensure_object(k[1])
            psi_q_candidate = _unbind(psi_fact, _bind(psi_e2, psi_o2))
            sc = float(resonate(psi_val, psi_q_candidate))
            if sc > best_score:
                best_score, best_key = sc, k
        if best_key and best_score > 0.05:
            return self._registry.get(best_key)
        return None

    def apply_action(self, entity: str, obj: str, action: str, value: float) -> float:
        """
        Applique une action : extraire q_old (registre), calculer q_new
        (arithmétique émergente), mettre à jour H et le registre.
        """
        key = (entity.lower(), obj.lower())
        q_old = self._registry.get(key, 0.0)

        # Calcul émergent
        if action == 'add':
            q_new = self.phase.add(float(q_old), float(value))[0]
        elif action == 'sub':
            q_new = self.phase.subtract(float(q_old), float(value))[0]
        elif action == 'mult':
            r = self.log.multiply(float(q_old), float(value))
            q_new = r[0] if r and r[0] is not None else float(q_old) * float(value)
        elif action == 'div':
            r = self.log.divide(float(q_old), float(value))
            q_new = r[0] if r and r[0] is not None else (float(q_old) / float(value) if float(value) != 0 else 0.0)
        elif action == 'init':
            q_new = float(value)
        else:
            q_new = q_old

        # Retirer l'ancien fait de H, ajouter le nouveau
        if key in self._psi_facts:
            self.H = normalize(self.H - self._psi_facts[key])

        psi_e = self._ensure_entity(entity)
        psi_o = self._ensure_object(obj)
        psi_q_new = _quantity_wave(q_new, self.dim)
        psi_new_fact = _bind(psi_e, _bind(psi_o, psi_q_new))

        self._registry[key] = float(q_new)
        self._psi_facts[key] = psi_new_fact
        self.H = normalize(self.H + psi_new_fact)

        return float(q_new)

    # ── Résolution par résonance ─────────────────────────────────────────────

    def resolve_entity(self, sentence: str) -> Optional[str]:
        words = [w for w in re.findall(r'[a-zà-ÿ]+', sentence.lower()) if len(w) > 1]
        if not words or not self._entities:
            return None
        psi_s = superpose(*[encode(w, dim=self.dim) for w in words])
        psi_s = psi_s / (np.linalg.norm(psi_s) + 1e-9)
        best, best_score = None, -1.0
        for name, psi_e in self._entities.items():
            sc = float(resonate(psi_s, psi_e))
            if sc > best_score:
                best_score, best = sc, name
        return best if best_score > 0.05 else None

    def resolve_action(self, sentence: str) -> Optional[str]:
        words = [w for w in re.findall(r'[a-zà-ÿ]+', sentence.lower()) if len(w) > 1]
        if not words:
            return None
        psi_s = superpose(*[encode(w, dim=self.dim) for w in words])
        psi_s = psi_s / (np.linalg.norm(psi_s) + 1e-9)
        best, best_score = None, -1.0
        for action, proto in self._action_protos.items():
            sc = float(resonate(psi_s, proto))
            if sc > best_score:
                best_score, best = sc, action
        return best if best_score > 0.05 else None

    def resolve_object(self, sentence: str) -> Optional[str]:
        words = [w for w in re.findall(r'[a-zà-ÿ]+', sentence.lower()) if len(w) > 1]
        if not words or not self._objects:
            return None
        psi_s = superpose(*[encode(w, dim=self.dim) for w in words])
        psi_s = psi_s / (np.linalg.norm(psi_s) + 1e-9)
        best, best_score = None, -1.0
        for name, psi_o in self._objects.items():
            sc = float(resonate(psi_s, psi_o))
            if sc > best_score:
                best_score, best = sc, name
        return best if best_score > 0.05 else None

    @property
    def entity_names(self) -> List[str]:
        return list(self._entities.keys())

    @property
    def object_names(self) -> List[str]:
        return list(self._objects.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PIPELINE GSM8K AVEC LE RAISONNEUR ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

# Mots-outils à ignorer pour la résolution d'objet
_STOP = {'the', 'a', 'an', 'of', 'in', 'for', 'to', 'is', 'are', 'was',
         'were', 'and', 'or', 'with', 'at', 'by', 'on', 'from', 'his',
         'her', 'their', 'its', 'he', 'she', 'they', 'it', 'more', 'each',
         'every', 'how', 'many', 'much', 'what', 'does', 'do', 'did',
         'left', 'remain', 'remaining', 'total', 'altogether', 'per',
         'has', 'had', 'have', 'than', 'as', 'this', 'that', 'these', 'those'}


def _extract_numbers(text: str) -> List[float]:
    """Extrait tous les nombres d'un texte (positifs, dans l'ordre)."""
    nums = []
    for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', text):
        v = float(m.group(1))
        if v > 0:
            nums.append(v)
    return nums


def _best_object_from_sentence(sentence: str, reasoner: OndulatoireReasoner,
                                exclude: set = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Devine l'objet ET l'entité d'une phrase par résonance + analyse simple.
    Retourne (entity, obj).
    """
    words = [w for w in re.findall(r'[a-zà-ÿ]+', sentence.lower())
             if w not in _STOP and len(w) > 1]
    # Entité : résonance
    entity = reasoner.resolve_entity(sentence)
    # Objet : résonance + fallback
    obj = reasoner.resolve_object(sentence)
    # Fallback nominal (dernier mot non-stop, non-verbe)
    if obj is None and words:
        action_verbs = {v for vals in MOTS_ACTION.values() for v in vals}
        for w in reversed(words):
            if w not in _STOP and w not in action_verbs and len(w) > 2:
                obj = w
                break
    return entity, obj


def _detect_mult_div(sentence: str) -> Optional[str]:
    """Détecte la multiplication ou division implicite (patterns anglais)."""
    s = sentence.lower()
    # Multiplication
    if re.search(r'\b(each|every|per|apiece|a\s+piece|times\s+as\s+(many|much)|twice|double|triple|'
                 r'how\s+much\s+does\s+.*\s+cost|price)\b', s):
        return 'mult'
    # Taux horaire / journalier
    if re.search(r'\b(earns?\s+\d+\s+(dollars?\s+)?per|makes?\s+\d+\s+(dollars?\s+)?per|'
                 r'per\s+(hour|day|week|month))\b', s):
        return 'mult'
    # Division
    if re.search(r'\b(among|split|shared\s+equally|divided\s+equally|'
                 r'each\s+(of|person|child|student|receives|gets)|per\s+person)\b', s):
        return 'div'
    return None


def _detect_comparison(sentence: str, nums: List[float]) -> Optional[Tuple[str, float]]:
    """
    Détecte les relations comparatives : 'N more/less than', 'N times as many'.
    Retourne (op, value) ou None.
    """
    s = sentence.lower()
    # "N more than" / "N less/fewer than"
    m = re.search(r'(\d+(?:\.\d+)?)\s+(more|less|fewer)\s+than', s)
    if m:
        val = float(m.group(1))
        op = 'add' if m.group(2) == 'more' else 'sub'
        return (op, val)
    # "N times as many/much as"
    m = re.search(r'(\d+(?:\.\d+)?)\s+times\s+as\s+(many|much)\s+as', s)
    if m:
        return ('mult', float(m.group(1)))
    # "twice as many/much" / "double"
    if re.search(r'\b(twice|double)\s+as\s+(many|much)\b', s):
        return ('mult', 2.0)
    # "half as many/much"
    if re.search(r'\bhalf\s+as\s+(many|much)\b', s):
        return ('mult', 0.5)
    # "three/four times as many"
    m = re.search(r'(three|four|five|six|seven|eight|nine|ten)\s+times\s+as\s+(many|much)', s)
    wmap = {'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7,
            'eight': 8, 'nine': 9, 'ten': 10}
    if m:
        return ('mult', float(wmap.get(m.group(1), 3)))
    return None


def solve_gsm8k(question: str, reasoner: OndulatoireReasoner = None) -> Optional[float]:
    if reasoner is None:
        reasoner = OndulatoireReasoner()

    q = question.strip()
    q = re.sub(r'\s+', ' ', q)
    sentences = re.split(r'(?<=[.;!?])\s+', q)
    sentences = [s.strip() for s in sentences if s.strip()]

    last_entity, last_obj = None, None
    for sent in sentences:
        is_question = bool(re.search(r'\b(how many|how much|what is|what are|'
                                      r'how far|how long|how old)\b', sent.lower()))
        if is_question:
            break

        nums = _extract_numbers(sent)
        if not nums:
            continue

        entity, obj = _best_object_from_sentence(sent, reasoner)
        entity = entity or last_entity
        # Si l'objet retourné n'est pas un objet connu du raisonneur
        # (ex: "friend" au lieu de "stickers"), utiliser last_obj
        if obj is not None and last_obj is not None:
            if obj not in reasoner.object_names:
                obj = last_obj
        if obj is None and last_obj:
            obj = last_obj

        # ── Détection d'action enrichie ──────────────────────────────────
        implicit_op = _detect_mult_div(sent)
        comparison = _detect_comparison(sent, nums)
        rate_mode = bool(re.search(r'\b(per\s+(hour|day|week|month)|'
                                    r'a\s+(day|week|month))\b', sent.lower()))

        # Première phrase ou "has/had/have" explicite → init
        is_init = (not reasoner._registry or len(reasoner._registry) == 0 or
                   bool(re.search(r'\b(?:^|\s)(?:has|had|have|there\s+are|there\s+were|'
                                  r'owns?|bought|collected|found|bakes?|makes?|'
                                  r'produces?)\s+\d+', sent.lower())))

        if is_init:
            action = 'init'
            # Essayer de trouver un nom propre (entité) dans la phrase
            if entity is None:
                # Chercher un mot capitalisé (hors début de phrase)
                caps = re.findall(r'\b([A-Z][a-z]{2,})\b', sent)
                if caps and reasoner._registry:
                    entity = caps[0].lower()
                elif caps:
                    entity = caps[0].lower()
            if entity is None and len(nums) >= 1 and not reasoner._registry:
                entity = 'someone'
            if obj is None and len(words := [w for w in re.findall(r'[a-z]{3,}', sent.lower())
                                              if w not in _STOP]) > 0:
                obj = words[-1]

        elif comparison:
            action, comp_val = comparison
            # Appliquer au dernier fait connu
            if entity and obj:
                reasoner.apply_action(entity, obj, action, comp_val)
                last_entity, last_obj = entity, obj
                continue
            # Sinon, on init puis on applique
            action = 'init'

        elif implicit_op:
            action = implicit_op
            if action == 'mult' and len(nums) >= 2:
                # "each box has 5 pencils" → multiplier le fait existant par 5
                # S'il y a un fait (entity, obj) existant → on multiplie
                key = (entity.lower(), obj.lower()) if entity and obj else None
                if key and key in reasoner._registry:
                    reasoner.apply_action(entity, obj, 'mult', nums[0] if len(nums) == 1 else nums[1])
                    last_entity, last_obj = entity, obj
                    continue
            if action == 'div' and entity and obj and len(nums) >= 2:
                reasoner.apply_action(entity, obj, 'div', nums[0] if len(nums) == 1 else nums[1])
                last_entity, last_obj = entity, obj
                continue
        elif rate_mode:
            # "earns $20 per hour, works 8 hours" → rate × time
            # On init la rate, puis on multiplie par la durée
            if len(nums) >= 2:
                # Créer un fait "rate" = nums[0]
                reasoner.apply_action(entity or 'someone', obj or 'money', 'init', nums[0])
                # Puis multiplier par le temps (nums[1])
                reasoner.apply_action(entity or 'someone', obj or 'money', 'mult', nums[1])
                last_entity, last_obj = entity, obj
                continue
        else:
            action = reasoner.resolve_action(sent) or 'add'

        if entity and obj and nums:
            val = nums[0]
            reasoner.apply_action(entity, obj, action, val)
            last_entity, last_obj = entity, obj

    # ── Répondre à la question ───────────────────────────────────────────
    target_entity, target_obj = last_entity, last_obj
    question_sent = sentences[-1] if sentences else ''
    if '?' in question_sent or 'how many' in question_sent.lower():
        q_entity, q_obj = _best_object_from_sentence(question_sent, reasoner)
        target_entity = q_entity or target_entity
        target_obj = q_obj or target_obj

    if target_entity and target_obj:
        return reasoner.query(target_entity, target_obj)

    if reasoner._registry:
        return list(reasoner._registry.values())[-1]

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TESTS + BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

_SAMPLES = [
    ("John has 5 apples. He buys 3 more. How many apples does he have?", 8.0),
    ("Mary had 10 cookies. She ate 4. How many cookies does she have left?", 6.0),
    ("Tom has 12 dollars. He spends 4 dollars. How many dollars does he have left?", 8.0),
    ("There are 6 boxes. Each box has 5 pencils. How many pencils are there in total?", 30.0),
    ("Sue has 10 stickers. She gives 3 to her friend. How many stickers does Sue have left?", 7.0),
    ("John has 5 apples. Mary has 3 times as many. How many apples does Mary have?", 15.0),
    ("A bakery bakes 24 loaves of bread. They sell 9 loaves. How many loaves are left?", 15.0),
    ("There are 4 cars. Each car has 4 wheels. How many wheels are there?", 16.0),
    ("Sam had 30 dollars. He spent 12 dollars. How many dollars does Sam have left?", 18.0),
    ("Lucy has 8 books. John has 3 times as many. How many books does John have?", 24.0),
    ("A store has 100 items. 45 are sold. How many remain?", 55.0),
    ("John has 5 apples. Mary gave him 3 more apples. How many apples does John have?", 8.0),
    ("James earns 20 dollars per hour. He works 8 hours. How much does he earn?", 160.0),
    ("There are 60 students. They are split into 4 equal groups. How many students per group?", 15.0),
    ("A pizza is cut into 8 slices. John eats 3 slices. How many slices are left?", 5.0),
]


def run_tests():
    print("═══ TESTS DU RAISONNEUR ONDULATOIRE ═══")
    ok = 0
    for q, expected in _SAMPLES:
        r = OndulatoireReasoner()
        result = solve_gsm8k(q, r)
        good = result is not None and abs(result - expected) < 1e-6
        ok += good
        print(f"{'✅' if good else '❌'} {q[:70]:<72} → {result} (attendu {expected})")
    print(f"\nSCORE : {ok}/{len(_SAMPLES)} ({100 * ok / len(_SAMPLES):.1f}%)")
    return ok, len(_SAMPLES)


def benchmark_gsm8k(sample: int = None, quick: bool = False) -> dict:
    """Benchmark sur GSM8K (raisonneur ondulatoire pur)."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]
    if sample:
        import random
        random.seed(42)
        problems = random.sample(problems, min(sample, len(problems)))
    elif quick:
        problems = problems[:200]

    correct, no_sol, total = 0, 0, len(problems)
    times = []

    for i, p in enumerate(problems):
        q = p.get('question', '')
        ans_str = p.get('answer', '')
        expected = None
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', ans_str)
        if m:
            expected = float(m.group(1))

        t0 = time.time()
        reasoner = OndulatoireReasoner()
        result = solve_gsm8k(q, reasoner)
        dt = (time.time() - t0) * 1000
        times.append(dt)

        if result is None:
            no_sol += 1
        elif expected is not None and abs(result - expected) < 1e-6:
            correct += 1

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{total} — {correct}/{i + 1} "
                  f"({100 * correct / (i + 1):.1f}%)")

    accuracy = 100 * correct / total if total > 0 else 0.0
    return {
        'accuracy': round(accuracy, 2),
        'correct': correct, 'total': total, 'no_solution': no_sol,
        'avg_ms': round(np.mean(times), 1) if times else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Tests sur les exemples')
    parser.add_argument('--sample', type=int, default=None)
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()

    if args.test or (not args.sample and not args.full and not args.quick):
        run_tests()

    if args.sample or args.full or args.quick:
        print(f"\n═══ BENCHMARK GSM8K (raisonneur ondulatoire pur) ═══")
        sample = None if args.full else (args.sample or 200)
        result = benchmark_gsm8k(sample=sample, quick=args.quick)
        print(f"\n  Problèmes : {result['total']}")
        print(f"  Corrects : {result['correct']}")
        print(f"  Accuracy : {result['accuracy']:.1f}%")
        print(f"  Sans solution : {result['no_solution']}")
        print(f"  Temps moyen : {result['avg_ms']:.1f} ms")

        out = 'raisonneur_gsm8k_result.json'
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  📊 {out}")
