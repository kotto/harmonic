#!/usr/bin/env python3
"""
compilateur_ondulatoire.py — Compilateur Langage Humain → Langage Ondulatoire
================================================================================

Principe THU : l'univers ne comprend pas "John has 5 apples".
Il comprend bind(ψ_john, bind(ψ_apples, ψ_5)).

Ce module est un COMPILATEUR, pas un pipeline NLP.
Il traduit le langage humain en PROGRAMME ONDULATOIRE exécutable.

ARCHITECTURE :
  Texte humain → [Grammaire] → Opérations ondulatoires → Phase/Log → Résultat

GRAMMAIRE (règles de compilation) :
  "X has N Y"              → LEARN(X, Y, N)
  "X buys/gains N Y"       → UPDATE(X, Y, ADD, N)
  "X sells/loses N Y"      → UPDATE(X, Y, SUB, N)
  "N times as many Y"      → LEARN(X, Y, MULT(N, QUERY(ref, Y)))
  "Each X has N Y"         → MULT(total, COUNT(X), N)
  "X earns N per hour"     → RATE(X, N)
  "X works N hours"        → EARN(X, N × rate)
  "X split into N groups"  → UPDATE(X, Y, DIV, N)
  "How many Y?"            → RESOLVE(Y)

USAGE :
  from compilateur_ondulatoire import CompilateurOndulatoire
  co = CompilateurOndulatoire()
  result = co.compiler_et_executer("John has 5 apples. He buys 3 more.")
  # → 8.0
"""

import sys, os, re, json, time, math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import encode, superpose, resonate, normalize, DEFAULT_DIM
from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder


# ═══════════════════════════════════════════════════════════════════════════
# 1. GRAMMAIRE ONDULATOIRE (règles de compilation)
# ═══════════════════════════════════════════════════════════════════════════

# Chaque règle est : (pattern_regex, type_opération, extracteur_de_paramètres)
#
# Le compilateur parcourt les règles dans l'ordre. La première qui match
# est compilée en opération ondulatoire.

GRAMMAIRE = [
    # ── Comparaison multiplicative (1 phrase) ──
    {
        "pattern": r'(?P<ent>[A-Z][a-z]+)\s+has\s+(?P<mult>\d+)\s+times\s+as\s+many',
        "op": "TIMES_AS_MANY",
        "slots": ["ent", "mult"],
    },
    # ── Taux horaire ──
    {
        "pattern": r'(?P<ent>[A-Z][a-z]+)\s+earns?\s+(?P<rate>\d+(?:\.\d+)?)\s+'
                   r'dollars?\s+per\s+(?P<unit>hour|day|week|month)',
        "op": "RATE",
        "slots": ["ent", "rate", "unit"],
    },
    # ── Durée après taux ──
    {
        "pattern": r'(?:He|She|They|It|\b[A-Z][a-z]+\b)\s+works?\s+'
                   r'(?P<duration>\d+(?:\.\d+)?)\s+(?P<unit2>hours?|days?|weeks?)',
        "op": "DURATION",
        "slots": ["duration", "unit2"],
    },
    # ── Cross-product : "Each X has N Y" ──
    {
        "pattern": r'[Ee]ach\s+(?P<container>\w+)\s+has\s+(?P<per_unit>\d+)\s+(?P<product>\w+)',
        "op": "CROSS_MULT",
        "slots": ["container", "per_unit", "product"],
    },
    # ── "There are N X" (conteneur) ──
    {
        "pattern": r'[Tt]here\s+are\s+(?P<count>\d+)\s+(?P<container>\w+)',
        "op": "THERE_ARE",
        "slots": ["count", "container"],
    },
    # ── Partition : "split into N equal groups" ──
    {
        "pattern": r'split\s+into\s+(?P<groups>\d+)\s+equal\s+groups',
        "op": "PARTITION",
        "slots": ["groups"],
    },
    # ── "gives N to" (perte) ──
    {
        "pattern": r'(?P<ent>[A-Z][a-z]+|\bhe\b|\bshe\b|\bthey\b)\s+'
                   r'gives?\s+(?P<val>\d+)\s+to',
        "op": "LOSE",
        "slots": ["ent", "val"],
    },
    # ── Perte : "X sells/eats/spends/loses N" ──
    {
        "pattern": r'(?P<ent>[A-Z][a-z]+|\bhe\b|\bshe\b|\bthey\b)\s+'
                   r'(?P<verb>sells?|sold|eats?|ate|spends?|spent|loses?|lost|'
                   r'gives?\s+away)\s+(?P<val>\d+)',
        "op": "LOSE",
        "slots": ["ent", "verb", "val"],
    },
    # ── Gain : "X buys/gains/gets N Y" ──
    {
        "pattern": r'(?P<ent>[A-Z][a-z]+|\bhe\b|\bshe\b|\bthey\b)\s+'
                   r'(?P<verb>buys|buy|bought|gains?|gets?|receives?|finds?|collects?)\s+'
                   r'(?P<val>\d+)',
        "op": "GAIN",
        "slots": ["ent", "verb", "val"],
    },
    # ── "gave X N Y" → gain pour X ──
    {
        "pattern": r'(?P<giver>[A-Z][a-z]+)\s+gave\s+(?P<ent>[a-z]+)\s+'
                   r'(?P<val>\d+)\s+(?P<obj>\w+)',
        "op": "GAVE_TO",
        "slots": ["giver", "ent", "val", "obj"],
    },
    # ── "X has/had N Y" (initialisation) ──
    {
        "pattern": r'(?P<ent>[A-Z][a-z]+|\bhe\b|\bshe\b|\bthey\b)\s+'
                   r'(?:has|had|have|owns?|bought|collected|found)\s+'
                   r'(?P<val>\d+(?:\.\d+)?)\s+(?P<obj>\w+)',
        "op": "HAS",
        "slots": ["ent", "val", "obj"],
    },
    # ── "X started with N Y" ──
    {
        "pattern": r'(?P<ent>[A-Z][a-z]+)\s+started\s+with\s+'
                   r'(?P<val>\d+)\s+(?P<obj>\w+)',
        "op": "HAS",
        "slots": ["ent", "val", "obj"],
    },
    # ── "A bakery/store X bakes/has N Y" ──
    {
        "pattern": r'[Aa]\s+(?P<ent>\w+)\s+(?:bakes?|makes?|produces?|has|had|have)\s+'
                   r'(?P<val>\d+(?:\.\d+)?)\s+(?P<obj>\w+)',
        "op": "HAS",
        "slots": ["ent", "val", "obj"],
    },
    # ── "X are sold" (passif) ──
    {
        "pattern": r'(?P<val>\d+)\s+are\s+sold',
        "op": "ARE_SOLD",
        "slots": ["val"],
    },
    # ── "X is/are cut into N Y" ──
    {
        "pattern": r'(?:is|are)\s+cut\s+into\s+(?P<val>\d+)\s+(?P<obj>\w+)',
        "op": "CUT_INTO",
        "slots": ["val", "obj"],
    },
    # ── Question ──
    {
        "pattern": r'[Hh]ow\s+many\s+(?P<obj>\w+)\s+'
                   r'(?:does\s+(?P<ent>\w+)\s+have|are\s+there|remain)',
        "op": "QUESTION",
        "slots": ["obj", "ent"],
    },
    {
        "pattern": r'[Hh]ow\s+much\s+(?:does\s+(?P<ent>\w+)\s+earn|money)',
        "op": "QUESTION_MONEY",
        "slots": ["ent"],
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# 2. MACHINE ONDULATOIRE (exécuteur de programme)
# ═══════════════════════════════════════════════════════════════════════════

class MachineOndulatoire:
    """
    Machine d'exécution ondulatoire.

    Maintient un ÉTAT ψ_state qui est une superposition de liens
    bind(bind(entité, objet), valeur).

    Les opérations modifient cet état par superposition/binding.
    La réponse émerge par unbinding de l'état final.
    """

    def __init__(self, dim=DEFAULT_DIM):
        self.dim = dim
        self.phase = PhaseEncoder(500000)
        self.log = LogWaveEncoder(grid_size=2048, SCALE=300)

        # État ondulatoire : superposition de tous les faits
        self._state = np.zeros(dim, dtype=np.complex128)

        # Registre classique pour les valeurs numériques
        # (la machine utilise les ondes pour les RELATIONS
        #  et le registre pour les VALEURS exactes)
        self._registry: Dict[str, float] = {}

        # Dernière entité et objet mentionnés (pour la coréférence)
        self._last_entity: Optional[str] = None
        self._last_object: Optional[str] = None

    # ── Primitives ondulatoires ─────────────────────────────────────────

    def _psi(self, text: str) -> np.ndarray:
        """Encode un texte en onde."""
        return encode(text, dim=self.dim)

    def _bind(self, a: str, b: str, c: str = None) -> np.ndarray:
        """Crée un lien bind(bind(a, b), c) ou bind(a, b)."""
        psi_a = self._psi(a)
        psi_b = self._psi(b)
        psi_ab = np.fft.ifft(np.fft.fft(psi_a) * np.fft.fft(psi_b))
        if c:
            psi_c = self._psi(c)
            return np.fft.ifft(np.fft.fft(psi_ab) * np.fft.fft(psi_c))
        return psi_ab

    # ── Opérations de la machine ────────────────────────────────────────

    def learn(self, entity: str, obj: str, value: float):
        """
        LEARN(X, Y, N) : associe la valeur N à l'entité X pour l'objet Y.

        État : ψ_state += bind(bind(ψ_X, ψ_Y), ψ_N)
        Registre : (X, Y) → N
        """
        key = f"{entity}|{obj}"
        psi_fact = self._bind(entity, obj, str(value))
        self._state = normalize(self._state + psi_fact)
        self._registry[key] = float(value)
        self._last_entity = entity
        self._last_object = obj

    def query(self, entity: str, obj: str) -> Optional[float]:
        """QUERY(X, Y) : récupère la valeur associée à (X, Y)."""
        # Recherche EXACTE uniquement (pas de fallback par préfixe —
        # "john_apples" ≠ "john_buys")
        key = f"{entity}|{obj}"
        if key in self._registry:
            return self._registry[key]
        return None

    def update(self, entity: str, obj: str, operation: str, operand: float):
        """
        UPDATE(X, Y, OP, N) : modifie la valeur de (X, Y) par OP(N).

        Utilise l'arithmétique ondulatoire (PhaseEncoder/LogEncoder)
        pour effectuer le calcul.
        """
        key = f"{entity}|{obj}"
        old_val = self.query(entity, obj)

        if old_val is None:
            # Chercher si une autre entité a cet objet (ex: "_slices" pour "john")
            for k, v in list(self._registry.items()):
                parts = k.split('|', 1)
                if len(parts) == 2 and parts[1] == obj:
                    old_val = float(v)
                    key = k
                    break

        if old_val is None:
            self.learn(entity, obj, operand)
            return

        if operation == 'ADD':
            new_val = self.phase.add(old_val, operand)
            new_val = new_val[0] if isinstance(new_val, tuple) else new_val
        elif operation == 'SUB':
            new_val = self.phase.subtract(old_val, operand)
            new_val = new_val[0] if isinstance(new_val, tuple) else new_val
        elif operation == 'MULT':
            new_val = self.log.multiply(old_val, operand)
            new_val = new_val[0] if isinstance(new_val, tuple) else new_val
        elif operation == 'DIV':
            new_val = self.log.divide(old_val, operand) if operand != 0 else old_val
            new_val = new_val[0] if isinstance(new_val, tuple) else new_val
        else:
            new_val = old_val + operand

        # Mettre à jour l'état ondulatoire
        # On retire l'ancien fait et on ajoute le nouveau
        old_psi = self._bind(entity, obj, str(old_val))
        new_psi = self._bind(entity, obj, str(new_val))
        self._state = normalize(self._state - old_psi + new_psi)
        self._registry[key] = float(new_val)

    def resolve(self, entity_hint: str = None, obj_hint: str = None) -> Optional[float]:
        """
        RESOLVE : extrait la réponse de l'état ondulatoire.

        Stratégie : chercher dans le registre la valeur correspondant
        à la question posée.
        """
        # Chercher par entité + objet
        if entity_hint and obj_hint:
            key = f"{entity_hint}_{obj_hint}"
            if key in self._registry:
                return self._registry[key]
            # Chercher par préfixe
            for k, v in self._registry.items():
                if k.startswith(f"{entity_hint}_") and obj_hint in k:
                    return v

        # Dernière valeur modifiée
        if self._last_entity and self._last_object:
            key = f"{self._last_entity}_{self._last_object}"
            if key in self._registry:
                return self._registry[key]

        # Dernière valeur du registre
        if self._registry:
            return list(self._registry.values())[-1]

        return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. COMPILATEUR (texte humain → programme ondulatoire)
# ═══════════════════════════════════════════════════════════════════════════

class CompilateurOndulatoire:
    """
    Compilateur : traduit le langage humain en programme ondulatoire.

    Pour chaque phrase du problème, le compilateur :
    1. Cherche une règle de grammaire qui match
    2. Extrait les paramètres (entité, objet, valeur, opération)
    3. Génère l'opération ondulatoire correspondante
    4. L'exécute sur la machine
    """

    def __init__(self):
        self.machine = MachineOndulatoire()

    def _extraire_nombres(self, text: str) -> List[float]:
        return [float(m.group(1)) for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', text)]

    def _resoudre_entite(self, sent: str, matched_ent: str = None) -> Optional[str]:
        """Résout l'entité d'une phrase (coréférence)."""
        if matched_ent:
            ent = matched_ent.lower()
            if ent in ('he', 'she', 'they', 'it'):
                return self.machine._last_entity
            return ent

        # Chercher un nom propre
        caps = re.findall(r'\b([A-Z][a-z]{2,})\b', sent)
        if caps:
            return caps[0].lower()

        return self.machine._last_entity

    def _resoudre_objet(self, sent: str, matched_obj: str = None) -> Optional[str]:
        """Résout l'objet d'une phrase. Priorité : matched > last > phrase."""
        if matched_obj and matched_obj.lower() not in ('more', 'many', 'much', 'fewer', 'less'):
            return matched_obj.lower()

        # Pas d'objet dans la règle → utiliser le dernier connu
        if self.machine._last_object:
            return self.machine._last_object

        # Fallback : dernier nom commun de la phrase
        words = re.findall(r'[a-z]{3,}', sent.lower())
        stop = {'the','a','an','of','in','for','to','is','are','was','were',
                'and','or','with','at','by','on','from','his','her','their',
                'its','he','she','they','it','more','each','every','how','many',
                'much','what','does','do','did','has','had','have','than','as',
                'this','that','these','those','left','remain','remaining',
                'total','altogether','per','there','then','also','some','all',
                'into','hour','hours','day','days','week','weeks',
                'buys','buy','sells','sell','ate','eats','eat','gives','give',
                'spends','spend','loses','lose'}
        candidates = [w for w in words if w not in stop and not w.isdigit()]
        if candidates:
            return candidates[-1]

        return None

    def compiler_phrase(self, sent: str) -> Optional[Dict]:
        """
        Compile une phrase en opération ondulatoire.

        Retourne l'opération compilée ou None si aucune règle ne match.
        """
        # Essayer chaque règle de grammaire
        for rule in GRAMMAIRE:
            m = re.search(rule["pattern"], sent, re.IGNORECASE)
            if m:
                params = {}
                for slot in rule["slots"]:
                    try:
                        params[slot] = m.group(slot)
                    except IndexError:
                        params[slot] = None

                return {
                    "op": rule["op"],
                    "params": params,
                    "sent": sent,
                }

        # Aucune règle → fallback : extraire les nombres
        nums = self._extraire_nombres(sent)
        if nums:
            return {
                "op": "RAW_NUMBERS",
                "params": {"numbers": nums},
                "sent": sent,
            }

        return None

    def executer_operation(self, compiled: Dict):
        """Exécute une opération compilée sur la machine ondulatoire."""
        op = compiled["op"]
        p = compiled["params"]
        sent = compiled["sent"]
        m = self.machine

        if op == "HAS":
            ent = self._resoudre_entite(sent, p.get("ent"))
            obj = self._resoudre_objet(sent, p.get("obj"))
            val = float(p["val"])
            if ent and obj:
                m.learn(ent, obj, val)

        elif op == "GAIN":
            ent = self._resoudre_entite(sent, p.get("ent"))
            val = float(p["val"])
            if ent:
                # GAIN n'a pas d'objet dans la règle → utiliser last_object
                obj = self.machine._last_object
                if obj:
                    m.update(ent, obj, "ADD", val)

        elif op == "LOSE":
            ent = self._resoudre_entite(sent, p.get("ent"))
            val = float(p["val"])
            if ent:
                # LOSE n'a pas d'objet dans la règle → utiliser last_object
                obj = self.machine._last_object
                if obj:
                    m.update(ent, obj, "SUB", val)

        elif op == "GAVE_TO":
            # "X gave Y N Z" → Y gains N Z
            receiver_raw = p.get("ent", "")
            receiver = self._resoudre_entite(sent, receiver_raw)
            val = float(p["val"])
            obj = self._resoudre_objet(sent, p.get("obj"))
            if receiver and obj:
                m.update(receiver, obj, "ADD", val)

        elif op == "TIMES_AS_MANY":
            # "X has N times as many" → multiplier un fait existant
            ent = self._resoudre_entite(sent, p.get("ent"))
            mult = float(p["mult"])
            if ent:
                obj = m._last_object
                # Chercher une AUTRE entité qui a le même objet
                for k, v in list(m._registry.items()):
                    parts = k.split('|', 1)
                    if len(parts) == 2 and parts[1] == obj and parts[0] != ent:
                        m.learn(ent, obj, float(v) * mult)
                        break

        elif op == "THERE_ARE":
            count = float(p["count"])
            container = p.get("container", "").lower()
            if container:
                m.learn("_", container, count)

        elif op == "CROSS_MULT":
            container = p.get("container", "").lower()
            per_unit = float(p["per_unit"])
            product = p.get("product", "").lower()
            # Chercher le compte du conteneur (essayer singulier ET pluriel)
            count = m.query("_", container)
            if count is None:
                # Essayer sans 's' final (pluriel → singulier)
                if container.endswith('s'):
                    count = m.query("_", container[:-1])
                # Essayer avec 's' (singulier → pluriel)
                if count is None:
                    count = m.query("_", container + 's')
                # Essayer 'es' (box → boxes)
                if count is None and container.endswith('x'):
                    count = m.query("_", container + 'es')
            if count is not None and product:
                m.learn("_", product, count * per_unit)

        elif op == "PARTITION":
            groups = float(p["groups"])
            # Appliquer la division au dernier fait
            if m._last_entity and m._last_object:
                m.update(m._last_entity, m._last_object, "DIV", groups)

        elif op == "RATE":
            ent = self._resoudre_entite(sent, p.get("ent"))
            rate = float(p["rate"])
            if ent:
                m.learn(ent, "rate", rate)

        elif op == "DURATION":
            duration = float(p["duration"])
            # Multiplier le taux par la durée
            ent = m._last_entity
            if ent:
                rate = m.query(ent, "rate")
                if rate is not None:
                    m.learn(ent, "money", rate * duration)

        elif op == "ARE_SOLD":
            val = float(p["val"])
            if m._last_entity and m._last_object:
                m.update(m._last_entity, m._last_object, "SUB", val)

        elif op == "CUT_INTO":
            val = float(p["val"])
            obj = self._resoudre_objet(sent, p.get("obj"))
            if obj:
                m.learn("_", obj, val)

        elif op == "QUESTION" or op == "QUESTION_MONEY":
            # La question déclenche la résolution
            pass

        elif op == "RAW_NUMBERS":
            nums = p.get("numbers", [])
            if nums and not m._registry:
                # Premier nombre → initialisation
                ent = self._resoudre_entite(sent)
                obj = self._resoudre_objet(sent)
                if ent and obj:
                    m.learn(ent, obj, nums[0])

    def compiler_et_executer(self, probleme: str) -> Optional[float]:
        """
        Compile et exécute un problème complet.

        1. Découpe en phrases
        2. Pour chaque phrase : compile → exécute
        3. La dernière phrase (question) déclenche la résolution
        """
        # Nettoyer
        q = probleme.strip()
        q = re.sub(r'\s+', ' ', q)

        # Découper en phrases
        sentences = re.split(r'(?<=[.;!?])\s+', q)
        sentences = [s.strip() for s in sentences if s.strip()]

        question_info = None

        for sent in sentences:
            compiled = self.compiler_phrase(sent)

            if compiled is None:
                continue

            # Si c'est une question, sauvegarder pour la résolution
            if compiled["op"] in ("QUESTION", "QUESTION_MONEY"):
                question_info = compiled
                continue

            # Exécuter l'opération
            self.executer_operation(compiled)

        # Résoudre
        if question_info:
            p = question_info["params"]
            obj = p.get("obj", "")
            ent = p.get("ent", "")
            if question_info["op"] == "QUESTION_MONEY":
                ent = ent or self.machine._last_entity or ""
                return self.machine.resolve(ent, "money")
            else:
                ent = ent or self.machine._last_entity or ""
                obj = obj or self.machine._last_object or ""
                return self.machine.resolve(ent, obj)

        # Pas de question explicite → dernière valeur
        return self.machine.resolve()


# ═══════════════════════════════════════════════════════════════════════════
# 4. TESTS + BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════

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
    print("═══ TEST COMPILATEUR ONDULATOIRE ═══")
    ok = 0
    for q, expected in _SAMPLES:
        co = CompilateurOndulatoire()
        result = co.compiler_et_executer(q)
        good = result is not None and abs(result - expected) < 1e-6
        ok += good
        print(f"{'✅' if good else '❌'} {q[:55]:<57} → {result} (attendu {expected})")
    print(f"\nSCORE : {ok}/{len(_SAMPLES)} ({100*ok/len(_SAMPLES):.1f}%)")
    return ok


def benchmark_gsm8k(n=200):
    co = CompilateurOndulatoire()
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]
    import random
    random.seed(42)
    sample = random.sample(problems, min(n, len(problems)))
    correct, no_sol, total = 0, 0, len(sample)
    times = []
    print(f"═══ BENCHMARK COMPILATEUR ONDULATOIRE ({total} problèmes) ═══")
    for i, p in enumerate(sample):
        q = p['question']
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', p['answer'])
        expected = float(m.group(1)) if m else None
        t0 = time.time()
        result = co.compiler_et_executer(q)
        dt = (time.time()-t0)*1000
        times.append(dt)
        if result is None: no_sol += 1
        elif expected and abs(result-expected) < 1e-6: correct += 1
        if (i+1) % 50 == 0:
            print(f"  {i+1:>4d}/{total} — {correct}/{i+1} ({100*correct/(i+1):.1f}%)")
    acc = 100*correct/total
    print(f"\n═══ RÉSULTATS ═══")
    print(f"  Accuracy : {acc:.1f}% ({correct}/{total})")
    print(f"  Sans sol.: {no_sol}")
    print(f"  Temps    : {np.mean(times):.1f} ms")
    return acc


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--benchmark', type=int, default=0)
    args = p.parse_args()
    if args.test or not args.benchmark:
        run_tests()
    if args.benchmark:
        benchmark_gsm8k(args.benchmark)
