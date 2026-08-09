#!/usr/bin/env python3
"""
compilateur_thu.py — Compilateur Humain → Langage Ondulatoire (13 primitives)
================================================================================

Pipeline THU complet, bidirectionnel, avec GATE V2 (noyau ABC, α=1/φ) :

  GATE V2  →  ANALYSE  →  ALGÈBRE  →  ARITHMÉTIQUE  →  GÉOMÉTRIE
  (filtre)    (texte)      (éq.)       (Phase/Log)       (ψ_state)
                                                              │
  RÉPONSE  ←  ALGÈBRE  ←  ARITHMÉTIQUE  ←────────────────────┘
  (nombre)    (vérif)     (extraction)

GATE V2 : le filtre dynamique (noyau ABC, α=1/φ) élimine les phrases
sans contenu mathématique AVANT la compilation. Seules les phrases
qui passent le GATE sont compilées en programme ondulatoire.

PRINCIPE THU V2 : 'Filtrer est la seule opération qui n'a pas besoin
d'intention.' Le GATE ne choisit pas — il applique la dynamique et
ce qui survit EST mathématique.
"""

import sys, os, re, json, time, math, pickle
import numpy as np
from typing import Dict, List, Tuple, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wave_lang import (
    encode, decode, bind, unbind, superpose, resonate,
    normalize, rotate, interfere, diffract,
    filter_wave as filter_psi, phase_shift, emerge,
    DEFAULT_DIM,
)
from encodage_phase import PhaseEncoder
from encodage_logarithmique import LogWaveEncoder


# ═══════════════════════════════════════════════════════════════════════════
# 1. MÉMOIRE HOLOGRAPHIQUE (superposition de faits bindés)
# ═══════════════════════════════════════════════════════════════════════════

class MemoireHolographique:
    """
    Mémoire holographique : ψ_state = superpose(bind(bind(ent,obj), val))

    Chaque fait est un lien bindé. La superposition de tous les faits
    forme l'état ondulatoire du problème. Le décodage se fait par
    unbind + résonance.
    """

    def __init__(self, dim=DEFAULT_DIM):
        self.dim = dim
        self._state = np.zeros(dim, dtype=np.complex128)
        self._facts: Dict[str, np.ndarray] = {}  # clé → ψ_fait
        self._values: Dict[str, float] = {}       # clé → valeur scalaire
        self._phase = PhaseEncoder(500000)
        self._log = LogWaveEncoder(grid_size=2048, SCALE=300)

    # ── Primitives ondulatoires ──────────────────────────────────────────

    def _key(self, entity: str, obj: str) -> str:
        return f"{entity}|{obj}"

    def apprendre(self, entity: str, obj: str, valeur: float):
        """
        ENCODE + BIND + SUPERPOSE : stocke un fait dans l'hologramme.

        ψ_fait = bind(bind(encode(entity), encode(obj)), encode(str(valeur)))
        ψ_state = superpose(ψ_state, ψ_fait)
        """
        psi_ent = encode(entity, dim=self.dim)
        psi_obj = encode(obj, dim=self.dim)
        psi_val = encode(str(valeur), dim=self.dim)
        psi_fait = bind(bind(psi_ent, psi_obj), psi_val)

        key = self._key(entity, obj)
        self._facts[key] = psi_fait
        self._values[key] = float(valeur)
        self._state = normalize(superpose(self._state, psi_fait))

    def interroger(self, entity: str, obj: str) -> Optional[float]:
        """
        UNBIND : extrait la valeur associée à (entité, objet).

        1. Chercher dans le registre scalaire (exact)
        2. Chercher par résonance dans l'état ondulatoire
        """
        key = self._key(entity, obj)
        if key in self._values:
            return self._values[key]

        # Chercher par résonance
        psi_query = bind(encode(entity, dim=self.dim), encode(obj, dim=self.dim))
        best_key, best_score = None, -1.0
        for k, psi_fait in self._facts.items():
            score = float(resonate(psi_query, psi_fait))
            if score > best_score:
                best_score = score
                best_key = k

        if best_key and best_score > 0.1:
            return self._values.get(best_key)

        return None

    def mettre_a_jour(self, entity: str, obj: str, operation: str, operand: float):
        """
        UNBIND + ARITHMÉTIQUE + BIND : modifie une valeur existante.

        Arithmétique ondulatoire : PhaseEncoder (+,−) + LogEncoder (×,÷)
        """
        old_val = self.interroger(entity, obj)

        if old_val is None:
            # Chercher si une autre entité a cet objet
            for k, v in self._values.items():
                parts = k.split('|', 1)
                if len(parts) == 2 and parts[1] == obj:
                    old_val = float(v)
                    break

        if old_val is None:
            self.apprendre(entity, obj, operand)
            return

        # ARITHMÉTIQUE ONDULATOIRE
        if operation == 'ADD':
            result = self._phase.add(old_val, operand)
            new_val = result[0] if isinstance(result, tuple) else result
        elif operation == 'SUB':
            result = self._phase.subtract(old_val, operand)
            new_val = result[0] if isinstance(result, tuple) else result
        elif operation == 'MULT':
            result = self._log.multiply(old_val, operand)
            new_val = result[0] if isinstance(result, tuple) else result
        elif operation == 'DIV':
            result = self._log.divide(old_val, operand) if operand != 0 else old_val
            new_val = result[0] if isinstance(result, tuple) else result
        else:
            new_val = old_val + operand

        self.apprendre(entity, obj, float(new_val))

    def resoudre(self, entity: str = None, obj: str = None) -> Optional[float]:
        """Résout la question posée. Priorité : entité+objet exacts > objet seul > dernière valeur."""
        # 1. Recherche exacte
        if entity and obj:
            val = self.interroger(entity, obj)
            if val is not None:
                return val

        # 2. Chercher TOUTES les entités ayant cet objet, prendre la dernière
        if obj:
            candidates = []
            for k, v in self._values.items():
                parts = k.split('|', 1)
                if len(parts) == 2 and parts[1] == obj:
                    candidates.append((k, float(v)))
            if candidates:
                # Préférer l'entité spécifiée, sinon la dernière ajoutée
                if entity:
                    for k, v in candidates:
                        if k.startswith(f"{entity}|"):
                            return v
                return candidates[-1][1]  # dernière valeur

        # 3. Dernière valeur du registre
        if self._values:
            return float(list(self._values.values())[-1])
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 2. GRAMMAIRE DE COMPILATION (texte → opérations ondulatoires)
# ═══════════════════════════════════════════════════════════════════════════

REGLES = [
    # ── "X earns $N per hour" → RATE ──
    (r'(?P<ent>[A-Z][a-z]+)\s+earns?\s+(?P<rate>\d+(?:\.\d+)?)\s+'
     r'dollars?\s+per\s+(?P<unit>hour|day|week|month)',
     'RATE', ['ent', 'rate']),

    # ── "X works N hours" → DURATION ──
    (r'(?:He|She|They|It|\b[A-Z][a-z]+\b)\s+works?\s+'
     r'(?P<dur>\d+(?:\.\d+)?)\s+(?P<unit2>hours?|days?|weeks?)',
     'DURATION', ['dur']),

    # ── "X has N times as many" → TIMES_AS_MANY ──
    (r'(?P<ent>[A-Z][a-z]+)\s+has\s+(?P<mult>\d+)\s+times\s+as\s+many',
     'TIMES_AS_MANY', ['ent', 'mult']),

    # ── "Each X has N Y" → CROSS_MULT ──
    (r'[Ee]ach\s+(?P<container>\w+)\s+has\s+(?P<per_unit>\d+)\s+(?P<product>\w+)',
     'CROSS_MULT', ['container', 'per_unit', 'product']),

    # ── "There are N X" → THERE_ARE ──
    (r'[Tt]here\s+are\s+(?P<count>\d+)\s+(?P<container>\w+)',
     'THERE_ARE', ['count', 'container']),

    # ── "split into N equal groups" → PARTITION ──
    (r'split\s+into\s+(?P<groups>\d+)\s+equal\s+groups',
     'PARTITION', ['groups']),

    # ── "X gives N to" → LOSE ──
    (r'(?P<ent>[A-Z][a-z]+|\bhe\b|\bshe\b|\bthey\b)\s+gives?\s+(?P<val>\d+)\s+to',
     'LOSE', ['ent', 'val']),

    # ── "X sells/eats/spends/loses N" → LOSE ──
    (r'(?P<ent>[A-Z][a-z]+|\bhe\b|\bshe\b|\bthey\b)\s+'
     r'(?P<verb>sells?|sold|eats?|ate|spends?|spent|loses?|lost|gives?\s+away)\s+'
     r'(?P<val>\d+)',
     'LOSE', ['ent', 'val']),

    # ── "X gave Y N Z" → GAVE_TO ──
    (r'(?P<giver>[A-Z][a-z]+)\s+gave\s+(?P<ent>[a-z]+)\s+'
     r'(?P<val>\d+)\s+(?P<obj>\w+)',
     'GAVE_TO', ['giver', 'ent', 'val', 'obj']),

    # ── "X buys/gains/gets N" → GAIN ──
    (r'(?P<ent>[A-Z][a-z]+|\bhe\b|\bshe\b|\bthey\b)\s+'
     r'(?P<verb>buys|buy|bought|gains?|gets?|receives?|finds?|collects?)\s+'
     r'(?P<val>\d+)',
     'GAIN', ['ent', 'val']),

    # ── "X has/had N Y" → HAS (initialisation) ──
    (r'(?P<ent>[A-Z][a-z]+|\bhe\b|\bshe\b|\bthey\b)\s+'
     r'(?:has|had|have|owns?|bought|collected|found)\s+'
     r'(?P<val>\d+(?:\.\d+)?)\s+(?P<obj>\w+)',
     'HAS', ['ent', 'val', 'obj']),

    # ── "A bakery/store X bakes/has N Y" → HAS ──
    (r'[Aa]\s+(?P<ent>\w+)\s+(?:bakes?|makes?|produces?|has|had|have)\s+'
     r'(?P<val>\d+(?:\.\d+)?)\s+(?P<obj>\w+)',
     'HAS', ['ent', 'val', 'obj']),

    # ── "N are sold" → ARE_SOLD ──
    (r'(?P<val>\d+)\s+are\s+sold',
     'ARE_SOLD', ['val']),

    # ── "is/are cut into N Y" → CUT_INTO ──
    (r'(?:is|are)\s+cut\s+into\s+(?P<val>\d+)\s+(?P<obj>\w+)',
     'CUT_INTO', ['val', 'obj']),

    # ── QUESTION ──
    (r'[Hh]ow\s+many\s+(?P<obj>\w+)\s+'
     r'(?:does\s+(?P<ent>\w+)\s+have|are\s+there|remain|per\s+group)',
     'QUESTION', ['obj', 'ent']),

    (r'[Hh]ow\s+much\s+(?:does\s+(?P<ent>\w+)\s+earn|money)',
     'QUESTION_MONEY', ['ent']),
]


# ═══════════════════════════════════════════════════════════════════════════
# 3. COMPILATEUR THU
# ═══════════════════════════════════════════════════════════════════════════

# Règles extraites (chargées paresseusement depuis le data mining)
_extracted_rules_cache = None

def _classify_minilm(sent: str):
    """MiniLM classifieur : phrase → (opération, confiance)."""
    global _minilm_classifier
    if _minilm_classifier is None:
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'minilm_operations.pkl')
            with open(path, 'rb') as f:
                data = pickle.load(f)
            _minilm_classifier = {
                'clf': data['classifier'],
                'scaler': data['scaler'],
                'model': _get_minilm_model(),
            }
        except Exception:
            _minilm_classifier = False
            return None, 0.0

    if _minilm_classifier is False:
        return None, 0.0

    try:
        emb = _minilm_classifier['model'].encode([sent])[0]
        emb_scaled = _minilm_classifier['scaler'].transform([emb])
        probs = _minilm_classifier['clf'].predict_proba(emb_scaled)[0]
        idx = np.argmax(probs)
        op = _minilm_classifier['clf'].classes_[idx]
        return op, float(probs[idx])
    except Exception:
        return None, 0.0


def _get_minilm_model():
    """Charge MiniLM paresseusement."""
    global _minilm_model
    if _minilm_model is None:
        from sentence_transformers import SentenceTransformer
        _minilm_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _minilm_model


_minilm_classifier = None
_minilm_model = None


def _get_extracted_rules():
    """Charge les règles extraites (721 motifs) paresseusement."""
    global _extracted_rules_cache
    if _extracted_rules_cache is not None:
        return _extracted_rules_cache

    import json as _json
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'grammaire_extraite.json')
    try:
        with open(path, encoding='utf-8') as f:
            raw = _json.load(f)

        rules = []
        seen = set()
        for op_type, regles in raw.items():
            for r in regles:
                pattern = r['pattern']
                if pattern in seen:
                    continue
                seen.add(pattern)

                # Convertir le motif normalisé en regex
                escaped = re.escape(pattern)
                escaped = escaped.replace(r'<\ N\ >', r'\\d+(?:\\.\\d+)?')
                escaped = escaped.replace(r'<\ ENT\ >', r'[A-Z][a-z]{2,}')
                escaped = escaped.replace(r'<\ OBJ\ >', r'\\w+')

                rules.append((escaped, op_type, ['val']))

        _extracted_rules_cache = rules
        return rules
    except Exception:
        _extracted_rules_cache = []
        return []


class CompilateurTHU:
    """
    Compilateur THU : texte humain → programme ondulatoire (13 primitives).

    Niveaux THU :
      GATE V2   : filtre dynamique (noyau ABC, α=1/φ) — élimine le bruit
      ANALYSE   : segmentation en phrases, reconnaissance de patterns
      ALGÈBRE   : construction d'équations avec dépendances
      ARITHMÉTIQUE : PhaseEncoder (+,−) + LogEncoder (×,÷)
      GÉOMÉTRIE : état ondulatoire ψ_state (la réponse y émerge)
    """

    # GATE V2 partagé (initialisé une seule fois pour toutes les instances)
    _gate_instance = None

    @classmethod
    def _get_gate(cls):
        """GATE V2 statique — chargé une seule fois."""
        if cls._gate_instance is None:
            from filtre_dynamique import DynamicHarmonicFilter
            cls._gate_instance = DynamicHarmonicFilter()
        return cls._gate_instance

    def __init__(self):
        self.memoire = MemoireHolographique()
        self._last_entity: Optional[str] = None
        self._last_object: Optional[str] = None

    def _passe_gate(self, sent: str) -> bool:
        """
        GATE V2 : une phrase passe le filtre si elle contient
        du contenu mathématique.

        Optimisation : les phrases contenant un nombre passent directement.
        """
        if re.search(r'\d', sent):
            return True
        gate = CompilateurTHU._get_gate()
        result = gate.filter_iteratively(sent)
        return any(w >= 0.5 for _, w in result['survivors'])

    # ── ANALYSE : reconnaissance de patterns ─────────────────────────────

    def _extraire_nombres(self, text: str) -> List[float]:
        return [float(m.group(1)) for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', text)]

    def _resoudre_entite(self, sent: str, matched_ent: str = None) -> Optional[str]:
        if matched_ent:
            ent = matched_ent.lower()
            if ent in ('he', 'she', 'they', 'it', 'him', 'her', 'them'):
                return self._last_entity
            return ent
        caps = re.findall(r'\b([A-Z][a-z]{2,})\b', sent)
        if caps:
            return caps[0].lower()
        return self._last_entity

    def _resoudre_objet(self, sent: str, matched_obj: str = None) -> Optional[str]:
        if matched_obj and matched_obj.lower() not in (
            'more', 'many', 'much', 'fewer', 'less', 'times'
        ):
            return matched_obj.lower()
        return self._last_object

    def compiler_phrase(self, sent: str) -> Optional[Dict]:
        """ANALYSE : reconnaît le pattern grammatical."""
        # 1. Règles manuelles (précises)
        for pattern, op, slots in REGLES:
            m = re.search(pattern, sent, re.IGNORECASE)
            if m:
                params = {}
                for slot in slots:
                    try:
                        params[slot] = m.group(slot)
                    except IndexError:
                        params[slot] = None
                return {"op": op, "params": params, "sent": sent}

        # 2. Règles extraites (couverture) — chargées paresseusement
        extracted = _get_extracted_rules()
        for pattern, op, slots in extracted:
            try:
                m = re.search(pattern, sent, re.IGNORECASE)
                if m:
                    params = {}
                    # Extraire les slots nommés ou le premier nombre
                    for slot in slots:
                        try:
                            val = m.group(slot)
                            if val is not None:
                                params[slot] = val
                        except (IndexError, AttributeError):
                            pass
                    # Si pas de valeur extraite, prendre le premier nombre du match
                    if 'val' in slots and 'val' not in params:
                        nums = re.findall(r'\d+(?:\.\d+)?', m.group(0))
                        if nums:
                            params['val'] = nums[0]
                    if params:
                        return {"op": op, "params": params, "sent": sent}
            except re.error:
                continue

        # Fallback : phrase avec nombres mais sans règle → RAW_NUMBERS
        nums = self._extraire_nombres(sent)
        if nums:
            return {"op": "RAW_NUMBERS", "params": {"numbers": nums}, "sent": sent}

        return None

    # ── ALGÈBRE + ARITHMÉTIQUE : construction et exécution ───────────────

    def executer(self, compiled: Dict):
        """ALGÈBRE : construit l'équation. ARITHMÉTIQUE : l'exécute."""
        op = compiled["op"]
        p = compiled["params"]
        sent = compiled["sent"]
        m = self.memoire

        # Safeguard : si val est absent, extraire le premier nombre de la phrase
        def _val(key='val', default=None):
            v = p.get(key)
            if v is not None:
                return float(v)
            nums = self._extraire_nombres(sent)
            return float(nums[0]) if nums else default

        if op == "HAS":
            ent = self._resoudre_entite(sent, p.get("ent"))
            obj = self._resoudre_objet(sent, p.get("obj"))
            val = _val()
            if ent and obj and val:
                m.apprendre(ent, obj, val)
                self._last_entity = ent
                self._last_object = obj

        elif op == "GAIN":
            ent = self._resoudre_entite(sent, p.get("ent"))
            val = _val()
            if ent and self._last_object and val:
                m.mettre_a_jour(ent, self._last_object, "ADD", val)

        elif op == "LOSE":
            ent = self._resoudre_entite(sent, p.get("ent"))
            val = _val()
            if ent and self._last_object and val:
                m.mettre_a_jour(ent, self._last_object, "SUB", val)

        elif op == "GAVE_TO":
            receiver_raw = p.get("ent", "")
            receiver = self._resoudre_entite(sent, receiver_raw)
            val = _val()
            obj = self._resoudre_objet(sent, p.get("obj"))
            if receiver and obj and val:
                m.mettre_a_jour(receiver, obj, "ADD", val)

        elif op == "TIMES_AS_MANY":
            ent = self._resoudre_entite(sent, p.get("ent"))
            mult = _val('mult')
            if ent and self._last_object:
                obj = self._last_object
                for k, v in list(m._values.items()):
                    parts = k.split('|', 1)
                    if len(parts) == 2 and parts[1] == obj and parts[0] != ent:
                        m.apprendre(ent, obj, float(v) * mult)
                        self._last_entity = ent
                        break

        elif op == "THERE_ARE":
            count = _val('count')
            container = p.get("container", "").lower()
            if container:
                m.apprendre("_", container, count)
                self._last_object = container  # pour PARTITION

        elif op == "CROSS_MULT":
            container = p.get("container", "").lower()
            per_unit = _val('per_unit')
            product = p.get("product", "").lower()
            count = m.interroger("_", container)
            if count is None:
                for suffix in ['', 's', 'es']:
                    if count is None:
                        count = m.interroger("_", container.rstrip('s') + suffix)
            if count is not None and product:
                m.apprendre("_", product, count * per_unit)

        elif op == "PARTITION":
            groups = _val('groups')
            # Utiliser _last_object (défini par THERE_ARE)
            obj = self._last_object
            if obj:
                # Chercher la valeur associée à cet objet
                m.mettre_a_jour("_", obj, "DIV", groups)

        elif op == "RATE":
            ent = self._resoudre_entite(sent, p.get("ent"))
            rate = _val('rate')
            if ent:
                m.apprendre(ent, "rate", rate)
                self._last_entity = ent

        elif op == "DURATION":
            dur = _val('dur')
            ent = self._last_entity
            if ent:
                rate = m.interroger(ent, "rate")
                if rate is not None:
                    m.apprendre(ent, "money", rate * dur)
                    self._last_object = "money"

        elif op == "ARE_SOLD":
            val = _val()
            if self._last_entity and self._last_object:
                m.mettre_a_jour(self._last_entity, self._last_object, "SUB", val)

        elif op == "CUT_INTO":
            val = _val()
            obj = self._resoudre_objet(sent, p.get("obj"))
            if obj:
                m.apprendre("_", obj, val)
                self._last_object = obj

        elif op in ("MULT", "COMPARE"):
            # Règles extraites : multiplication générique
            val = p.get("val")
            if val is None:
                val = p.get("val1", 0)
            if val is not None:
                val = float(val)
                if val > 0 and self._last_entity and self._last_object:
                    m.mettre_a_jour(self._last_entity, self._last_object, "MULT", val)

        elif op == "DIV":
            # Règles extraites : division générique
            val = p.get("val")
            if val is not None:
                val = float(val)
                if val > 0 and self._last_entity and self._last_object:
                    m.mettre_a_jour(self._last_entity, self._last_object, "DIV", val)

        elif op == "RAW_NUMBERS":
            # Fallback conservateur : initialiser seulement si registre vide
            nums = p.get("numbers", [])
            if nums and not m._values:
                ent = self._resoudre_entite(sent) or "x"
                obj = self._resoudre_objet(sent) or "y"
                m.apprendre(ent, obj, nums[0])
                self._last_entity = ent
                self._last_object = obj

    # ── GÉOMÉTRIE : résolution par l'état ondulatoire ────────────────────

    def compiler_et_executer(self, probleme: str) -> Optional[float]:
        """
        Pipeline THU complet :
          GATE V2 → ANALYSE → ALGÈBRE → ARITHMÉTIQUE → GÉOMÉTRIE → réponse

        Le GATE V2 (noyau ABC, α=1/φ) filtre les phrases avant compilation.
        """
        q = probleme.strip()
        q = re.sub(r'\s+', ' ', q)
        sentences = re.split(r'(?<=[.;!?])\s+', q)
        sentences = [s.strip() for s in sentences if s.strip()]

        question_info = None

        for sent in sentences:
            # ── GATE V2 : ne compiler que les phrases mathématiques ──
            if not self._passe_gate(sent):
                continue

            compiled = self.compiler_phrase(sent)
            if compiled is None:
                continue

            if compiled["op"] in ("QUESTION", "QUESTION_MONEY"):
                question_info = compiled
                continue

            self.executer(compiled)

        # GÉOMÉTRIE → ARITHMÉTIQUE → ALGÈBRE → ANALYSE (reverse path)
        if question_info:
            p = question_info["params"]
            obj = p.get("obj", "")
            ent = p.get("ent", "")
            if question_info["op"] == "QUESTION_MONEY":
                ent = ent or self._last_entity or ""
                return self.memoire.resoudre(ent, "money")
            else:
                ent = ent or self._last_entity or ""
                obj = obj or self._last_object or ""
                return self.memoire.resoudre(ent, obj)

        return self.memoire.resoudre()


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
    print("═══ TEST COMPILATEUR THU ═══")
    print("  (13 primitives du langage ondulatoire standard)")
    print()
    ok = 0
    for q, expected in _SAMPLES:
        co = CompilateurTHU()
        result = co.compiler_et_executer(q)
        good = result is not None and abs(result - expected) < 1e-6
        ok += good
        print(f"  {'✅' if good else '❌'} {q[:52]:<54} → {result} ({expected})")
    print(f"\n  SCORE : {ok}/{len(_SAMPLES)} ({100*ok/len(_SAMPLES):.1f}%)")
    return ok


def benchmark_gsm8k(n=200):
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'data', 'benchmarks', 'gsm8k_test.jsonl')
    with open(path, encoding='utf-8') as f:
        problems = [json.loads(l) for l in f]
    import random
    random.seed(42)
    sample = random.sample(problems, min(n, len(problems)))
    correct, no_sol, total = 0, 0, len(sample)
    times = []
    print(f"═══ BENCHMARK COMPILATEUR THU ({total} problèmes) ═══")
    for i, p in enumerate(sample):
        q = p['question']
        m = re.search(r'####\s*(-?\d+(?:\.\d+)?)', p['answer'])
        expected = float(m.group(1)) if m else None
        co = CompilateurTHU()
        t0 = time.time()
        result = co.compiler_et_executer(q)
        dt = (time.time()-t0)*1000
        times.append(dt)
        if result is None: no_sol += 1
        elif expected and abs(result-expected) < 1e-6: correct += 1
        if (i+1) % 50 == 0:
            print(f"  {i+1:>4d}/{total} — {correct}/{i+1} ({100*correct/(i+1):.1f}%)")
    acc = 100*correct/total if total > 0 else 0
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
