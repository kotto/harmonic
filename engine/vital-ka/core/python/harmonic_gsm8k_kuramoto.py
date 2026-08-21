#!/usr/bin/env python3
"""
harmonic_gsm8k_kuramoto.py — Solveur GSM8K par réseau d'oscillateurs couplés (Kuramoto)
======================================================================================

Mapping problème GSM8K → réseau d'oscillateurs :
- Chaque ENTITÉ (personne, objet) = oscillateur
- Chaque QUANTITÉ = oscillateur ancré à phase = 2π × valeur / BASE
- ACTIONS = modifications de la topologie de couplage (ajout arêtes +κ/−κ)
- QUESTION = lecture de la phase d'un oscillateur cible

Exemple "J'ai 3 pommes, j'en donne 1 à mon frère, combien me reste-t-il ?" :
- Oscillateurs : moi_pommes, frere_pommes, action_donner
- Ancres initiales : moi_pommes → phase(3), frere_pommes → phase(0)
- Action "donner 1" : couple (moi_pommes, action_donner) -κ, (frere_pommes, action_donner) +κ
- Évolution → moi_pommes converge vers phase(2), frere_pommes vers phase(1)
"""

import sys
sys.path.insert(0, 'E:\\SAAS - Copie\\engine\\vital-ka\\core\\python')

import numpy as np
import re
from typing import Dict, List, Tuple, Optional
from kuramoto_reasoner import KuramotoReasoner


BASE = 10          # Base de codage des quantités (0-9 par défaut)
MAX_VAL = BASE - 1 # Valeur max codable
PHASE_PER_UNIT = 2 * np.pi / BASE  # Phase par unité


class HarmonicGSM8KSolver:
    """
    Solveur GSM8K par oscillateurs couplés style Kuramoto.
    """
    
    def __init__(self, kappa: float = 1.5, sigma: float = 0.01, dt: float = 0.02):
        self.kappa = kappa
        self.sigma = sigma
        self.dt = dt
        self.net = None
        self.entity_map = {}      # nom_entité -> index
        self.quantity_map = {}    # (entité, objet) -> index
        self.action_nodes = []    # indices des nœuds d'action
        
    def _val_to_phase(self, val: float) -> float:
        """Encode valeur numérique en phase [0, 2π)."""
        # Modulo BASE pour valeurs > 9 (utiliser plusieurs oscillateurs pour grandes valeurs)
        v = val % BASE
        return v * PHASE_PER_UNIT
    
    def _phase_to_val(self, phase: float) -> float:
        """Décode phase en valeur numérique [0, BASE)."""
        phase = phase % (2 * np.pi)
        v = phase / PHASE_PER_UNIT
        return round(v)
    
    def _get_or_create_entity(self, entity: str, obj: str) -> int:
        """Récupère ou crée un oscillateur pour (entité, objet)."""
        key = (entity, obj)
        if key not in self.quantity_map:
            idx = len(self.entity_map)
            self.entity_map[key] = idx
            self.quantity_map[key] = idx
        return self.quantity_map[key]
    
    def _add_action_node(self, action_name: str) -> int:
        """Crée un nœud pour une action (donner, acheter, manger...)."""
        idx = len(self.entity_map)
        self.entity_map[('action', action_name)] = idx
        self.action_nodes.append(idx)
        return idx
    
    def solve(self, question: str, steps: int = 3000) -> Tuple[Optional[float], List[str]]:
        """
        Résout un problème GSM8K.
        
        Returns:
            (réponse numérique, étapes de raisonnement)
        """
        # 1. Parser la question pour extraire entités, quantités, actions
        entities, quantities, actions, question_target, action_names = self._parse_gsm8k(question)
        
        if not entities:
            return None, ["Aucune entité détectée"]
        
        # 2. Collecter TOUS les noms pour créer le réseau une seule fois
        all_names = set()
        
        # Noms quantités : entity_obj
        for (entity, obj) in quantities.keys():
            all_names.add(f"{entity}_{obj}")
        
        # Noms actions
        for an in action_names:
            all_names.add(an)
        
        # Nom cible
        target_name = f"{question_target[0]}_{question_target[1]}"
        all_names.add(target_name)
        
        # 3. Créer le réseau avec TOUS les noms
        self.net = KuramotoReasoner(list(all_names), kappa=self.kappa, sigma=self.sigma, dt=self.dt)
        
        # 4. Ancrer les quantités initiales (par NOM)
        for (entity, obj), val in quantities.items():
            name = f"{entity}_{obj}"
            phase = self._val_to_phase(val)
            self.net.anchor(name, phase)
        
        # 5. Ajouter les couplages d'actions
        for action in actions:
            self._add_action_coupling(action)
        
        # 6. Faire évoluer le réseau
        theta_final, r_series = self.net.run(steps)
        
        # 7. Lire la réponse
        if target_name not in self.net.idx:
            # Fallback : chercher oscillateur correspondant à l'objet demandé
            obj_wanted = self._extract_object_from_question(question)
            candidates = [n for n in self.net.names if n.endswith(f"_{obj_wanted}")]
            if candidates:
                target_name = candidates[0]
        
        if target_name in self.net.idx:
            idx = self.net.idx[target_name]
            phase = theta_final[idx] % (2 * np.pi)
            answer = self._phase_to_val(phase)
            
            steps_log = [
                f"Entités: {entities}",
                f"Quantités initiales: {quantities}",
                f"Actions: {actions}",
                f"Cible question: {target_name}",
                f"Phase finale: {phase:.3f} rad",
                f"Réponse décodée: {answer}",
                f"Cohérence finale r: {r_series[-1]:.3f}"
            ]
            return answer, steps_log
        
        return None, ["Cible non trouvée"]
    
    def _parse_gsm8k(self, question: str) -> Tuple[List[str], Dict, List[Dict], Tuple, List[str]]:
        """
        Parse une question GSM8K simple.
        Retourne: (entités, quantités_initiales, actions, cible_question, tous_noms_actions)
        """
        q = question.lower()
        
        entities = set()
        quantities = {}  # (entity, obj) -> valeur
        actions = []     # liste de dicts {type, source, target, obj, amount}
        action_names = []  # noms des nœuds d'action
        
        # Pronoms -> résolution contextuelle simple
        pronouns = {'he', 'she', 'they', 'it', 'him', 'her', 'them'}
        last_entity = None
        
        def resolve_entity(word):
            nonlocal last_entity
            if word in pronouns and last_entity:
                return last_entity
            last_entity = word
            return word
        
        # Patterns simples (à étendre)
        # "X has N obj" / "X had N obj"
        for m in re.finditer(r'(\w+)\s+(?:has|had|have)\s+(\d+)\s+(\w+)', q):
            entity, val, obj = resolve_entity(m.group(1)), int(m.group(2)), m.group(3)
            entities.add(entity)
            quantities[(entity, obj)] = val
        
        # "There are N obj"
        for m in re.finditer(r'there (?:are|were)\s+(\d+)\s+(\w+)', q):
            val, obj = int(m.group(1)), m.group(2)
            quantities[('world', obj)] = val
        
        # "X buys N more obj" / "X gets N obj" / "X buys N obj"
        for m in re.finditer(r'(\w+)\s+(?:buys?|gets?|receives?)\s+(\d+)(?:\s+more)?\s*(\w+)?', q):
            entity, amount, obj = resolve_entity(m.group(1)), int(m.group(2)), m.group(3)
            if not obj:
                for (e, o), v in quantities.items():
                    if e == entity:
                        obj = o
                        break
            if obj:
                actions.append({'type': 'add', 'source': entity, 'target': entity, 'obj': obj, 'amount': amount})
                action_names.append(f"action_add_{obj}_{amount}")
                entities.add(entity)
        
        # "X gives N obj to Y" / "X gives Y N obj" / "X gives N to Y"
        for m in re.finditer(r'(\w+)\s+gives?\s+(\w+)\s+(\d+)\s+(\w+)', q):
            giver, receiver, amount, obj = resolve_entity(m.group(1)), resolve_entity(m.group(2)), int(m.group(3)), m.group(4)
            actions.append({'type': 'transfer', 'source': giver, 'target': receiver, 'obj': obj, 'amount': amount})
            action_names.append(f"action_transfer_{obj}_{amount}")
            entities.add(giver)
            entities.add(receiver)
        
        # "X gives N to Y" / "X gives N obj to Y"
        for m in re.finditer(r'(\w+)\s+gives?\s+(\d+)\s+(?:to\s+)?(\w+)', q):
            giver, amount, receiver = resolve_entity(m.group(1)), int(m.group(2)), resolve_entity(m.group(3))
            # Objet implicite
            obj = None
            for (e, o), v in quantities.items():
                if e == giver:
                    obj = o
                    break
            if obj:
                actions.append({'type': 'transfer', 'source': giver, 'target': receiver, 'obj': obj, 'amount': amount})
                action_names.append(f"action_transfer_{obj}_{amount}")
                entities.add(giver)
                entities.add(receiver)
        
        # "X gives N obj" (sans destinataire = perte)
        for m in re.finditer(r'(\w+)\s+gives?\s+(\d+)\s+(\w+)', q):
            giver, amount, obj = resolve_entity(m.group(1)), int(m.group(2)), m.group(3)
            actions.append({'type': 'sub', 'source': giver, 'target': giver, 'obj': obj, 'amount': amount})
            action_names.append(f"action_sub_{obj}_{amount}")
            entities.add(giver)
        
        # "X eats/ate N obj" / "X uses N obj"
        for m in re.finditer(r'(\w+)\s+(?:eats?|ate|uses?)\s+(\d+)\s+(\w+)', q):
            entity, amount, obj = resolve_entity(m.group(1)), int(m.group(2)), m.group(3)
            actions.append({'type': 'sub', 'source': entity, 'target': entity, 'obj': obj, 'amount': amount})
            action_names.append(f"action_sub_{obj}_{amount}")
            entities.add(entity)
        
        # "X sells N obj for $Y each" - juste quantité pour l'instant
        for m in re.finditer(r'(\w+)\s+sells?\s+(\d+)\s+(\w+)', q):
            entity, amount, obj = resolve_entity(m.group(1)), int(m.group(2)), m.group(3)
            actions.append({'type': 'sub', 'source': entity, 'target': entity, 'obj': obj, 'amount': amount})
            action_names.append(f"action_sub_{obj}_{amount}")
            entities.add(entity)
        
        # Question cible : "how many obj does X have" / "how many obj"
        target = ('world', 'obj')  # défaut
        for m in re.finditer(r'how many\s+(\w+)\s+does\s+(\w+)\s+have', q):
            obj, entity = m.group(1), resolve_entity(m.group(2))
            target = (entity, obj)
        for m in re.finditer(r'how many\s+(\w+)', q):
            obj = m.group(1)
            target = ('world', obj)
        
        return list(entities), quantities, actions, target, action_names
    
    def _add_action_coupling(self, action: Dict):
        """Ajoute les couplages Kuramoto pour une action."""
        src = action['source']
        tgt = action['target']
        obj = action['obj']
        amount = action['amount']
        act_type = action['type']
        
        src_name = f"{src}_{obj}"
        tgt_name = f"{tgt}_{obj}"
        act_name = f"action_{act_type}_{obj}_{amount}"
        
        # Phase de l'action = encode le montant
        act_phase = self._val_to_phase(amount)
        self.net.anchor(act_name, act_phase)
        
        if act_type == 'add' or act_type == 'transfer':
            # Source -> Action (repulsion: source perd amount)
            self.net.add_contradiction(src_name, act_name)
            # Target -> Action (attraction: target gagne amount)  
            self.net.add_implication(tgt_name, act_name)
        elif act_type == 'sub':
            # Source -> Action (repulsion)
            self.net.add_contradiction(src_name, act_name)
    
    def _extract_object_from_question(self, question: str) -> str:
        """Extrait l'objet principal de la question."""
        q = question.lower()
        m = re.search(r'how many\s+(\w+)', q)
        if m:
            return m.group(1)
        # Fallback: premier nom après nombre
        m = re.search(r'\d+\s+(\w+)', q)
        if m:
            return m.group(1)
        return 'obj'


def solve_gsm8k_kuramoto(question: str, steps: int = 3000) -> Tuple[Optional[float], List[str]]:
    """Point d'entrée simple."""
    solver = HarmonicGSM8KSolver()
    return solver.solve(question, steps)


if __name__ == "__main__":
    print("=" * 60)
    print("HARMONIC GSM8K - KURAMOTO OSCILLATOR SOLVER")
    print("=" * 60)
    
    test_cases = [
        ("John has 5 apples. He buys 3 more. How many apples does John have?", 8),
        ("Mary had 10 cookies. She ate 4. How many cookies does Mary have left?", 6),
        ("John has 5 apples. He gives 2 to Mary. How many apples does John have?", 3),
        ("There are 6 boxes. Each box has 5 pencils. How many pencils in total?", 30),
    ]
    
    for q, expected in test_cases:
        print(f"\nQ: {q}")
        answer, steps = solve_gsm8k_kuramoto(q)
        status = "OK" if answer == expected else "KO"
        print(f"  {status} Expected: {expected}, Got: {answer}")
        for s in steps:
            print(f"    {s}")