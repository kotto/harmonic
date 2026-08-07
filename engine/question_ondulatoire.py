#!/usr/bin/env python3
r"""
🌊 LA QUESTION ONDULATOIRE — Décomposition Structurale d'une Question en Onde
==============================================================================

PROBLÈME RÉSOLU :
  Le champ pur ne répond pas aux questions parce que nous encodons la
  question comme un SAC DE MOTS (superposition de paquets d'onde).
  
  Or une question n'est PAS un sac de mots. Elle a une STRUCTURE :
  
  "Quelle est la capitale de la France ?"
         └─── RELATION ───┘    └─ CIBLE ─┘
         (type de lien)    (entité connue, point de départ)
  
  X ──[capitale_de]──→ France
  └── TROU (GAP) : l'inconnu à trouver

PRINCIPE :
  Une question = un GAP dans un graphe de couplage ondulatoire.
  
  1. On EXCITE la position de l'entité CIBLE (France)
  2. On MODULE cette excitation par la RELATION (capitale_de)
  3. L'onde modulée se PROPAGE à travers les couplages du champ
  4. Elle ARRIVE à la position de l'entité RÉPONSE (Paris)
  5. On DÉTECTE le point d'arrivée → réponse
  
  C'est une PROPAGATION D'ONDE À TRAVERS UN GRAPHE,
  pas une superposition statique de tokens.

TROIS TYPES DE QUESTIONS :
  
  Type 1 — SUJET MANQUANT : "? est la capitale de la France"
    → On connaît la RELATION et l'OBJET, on cherche le SUJET.
    → Exciter France, moduler par capitale_de, détecter la source.
  
  Type 2 — OBJET MANQUANT : "Paris est la capitale de ?"
    → On connaît le SUJET et la RELATION, on cherche l'OBJET.
    → Exciter Paris, moduler par capitale_de, détecter la destination.
  
  Type 3 — RELATION MANQUANTE : "Paris ? France"
    → On connaît le SUJET et l'OBJET, on cherche la RELATION.
    → Exciter les deux, détecter le mode de couplage qui les relie.

OPÉRATIONS ONDULATOIRES :
  
  1. ψ_excitation(x) = gaussienne centrée sur la position de la CIBLE
     → "Regarde ici"
  
  2. ψ_modulée(x) = ψ_excitation(x) · exp(i · φ_rel(x))
     → φ_rel(x) est une phase spécifique à la relation "capitale_de"
     → Cette modulation AGIT comme un FILTRE : seuls les couplages
       qui matchent cette modulation laissent passer l'onde
  
  3. ∂ψ/∂t = D·∇²ψ + γ·(K_c * ψ)
     → L'onde DIFFUSE + se PROPAGE via le couplage non-local
     → Le couplage K_c(x,y) est FORT entre concepts reliés
  
  4. détection = argmax_x |ψ(x, t_final) - ψ_excitation(x)|
     → Le point où l'onde ARRIVE (hors point d'excitation)
     → C'est la RÉPONSE

USAGE :
  python question_ondulatoire.py
"""

import math
import time
import re
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from champ_continu_ondulatoire import ContinuousKnowledgeField, PHI, TAU, PI
from champ_avance_ondulatoire import NonLocalField


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GRAPHE DE COUPLAGE ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveCouplingGraph:
    """
    Graphe de couplage entre concepts dans le champ continu.
    
    Chaque ARÊTE est un COUPLAGE pondéré entre deux positions.
    Chaque arête a un TYPE (la relation : "capitale_de", "ville_de", etc.).
    
    Contrairement à un graphe discret, les couplages sont CONTINUS :
    - La force décroît avec la distance spatiale
    - Le TYPE de relation est encodé comme une MODULATION DE PHASE
    """
    
    def __init__(self, field: NonLocalField, L: float = 1.0):
        self.field = field
        self.L = L
        
        # Positions des CONCEPTS (entités, pas relations)
        self.concept_positions: Dict[str, float] = {}
        
        # Registre SÉPARÉ des types de relation
        self.relation_types: Dict[str, float] = {}  # type → phase de modulation
        
        # Relations : (sujet, relation, objet)
        self.relations: List[Tuple[str, str, str]] = []
        
        # Stopwords
        self.stopwords = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou',
            'est', 'sont', 'que', 'qui', 'quoi', 'quel', 'quelle', 'quels', 'quelles',
            'dans', 'sur', 'avec', 'pour', 'pas', 'ne', 'se', 'ce', 'il', 'elle',
            'en', 'au', 'aux', 'à', 'the', 'a', 'an', 'is', 'are', 'of', 'in', 'on', 'to',
        }
        
        # Interrogatifs (marqueurs de question)
        self.interrogatifs = {
            'qui', 'quoi', 'que', 'quel', 'quelle', 'quels', 'quelles',
            'comment', 'pourquoi', 'quand', 'combien', 'lequel', 'laquelle',
        }
    
    def _hash_position(self, word: str) -> float:
        """Hash déterministe mot → position."""
        h = 0
        for ch in word.lower().encode('utf-8'):
            h = ((h << 5) - h + ch) & 0xFFFFFFFF
            h ^= (h >> 13)
        h = int(h * PHI * 1000000) & 0x7FFFFFFF
        return (h / 0x7FFFFFFF) * self.L
    
    def add_concept(self, word: str, position: Optional[float] = None):
        """Ajoute un concept au graphe."""
        w = word.lower().strip()
        if w in self.stopwords or w in self.concept_positions:
            return
        if position is None:
            position = self._hash_position(w)
        self.concept_positions[w] = position
    
    def add_relation(self, sujet: str, relation: str, objet: str):
        """
        Ajoute une RELATION orientée entre deux concepts.
        
        CRUCIAL : le type de relation (ex: "capitale_de") est enregistré
        dans relation_types, PAS dans concept_positions.
        Seuls le sujet et l'objet sont des entités avec position.
        """
        s = sujet.lower().strip()
        o = objet.lower().strip()
        r = relation.lower().strip()
        
        # Ajouter les entités (sujet, objet) comme concepts
        for w in [s, o]:
            if w not in self.concept_positions and w not in self.stopwords:
                self.add_concept(w)
        
        # Enregistrer le type de relation SÉPARÉMENT
        if r not in self.relation_types:
            self.relation_types[r] = self._hash_relation_phase(r)
        
        phase_rel = self.relation_types[r]
        self.relations.append((s, r, o))
        
        # Renforcer le couplage spatial entre sujet et objet
        if s in self.concept_positions and o in self.concept_positions:
            pos_s = self.concept_positions[s]
            pos_o = self.concept_positions[o]
            self._imprint_relation_bridge(pos_s, pos_o, phase_rel)
    
    def _hash_relation_phase(self, relation: str) -> float:
        """Hash déterministe relation → phase de modulation ∈ [0, 2π]."""
        h = 0
        for ch in relation.encode('utf-8'):
            h = ((h << 5) - h + ch) & 0xFFFFFFFF
        return ((h * PHI) % 1.0) * TAU
    
    def _imprint_relation_bridge(self, pos_a: float, pos_b: float, phase_rel: float):
        """
        Crée un PONT ONDULATOIRE entre deux positions.
        
        L'amplitude du pont est NORMALISÉE par le nombre de relations
        connectées à chaque nœud. Cela évite que les HUBS (ex: France
        avec 3 relations) dominent la propagation.
        """
        # Compter le degré de chaque nœud
        degree_a = sum(1 for s, r, o in self.relations 
                       if self.concept_positions.get(s) == pos_a 
                       or self.concept_positions.get(o) == pos_a)
        degree_b = sum(1 for s, r, o in self.relations 
                       if self.concept_positions.get(s) == pos_b 
                       or self.concept_positions.get(o) == pos_b)
        
        # Normaliser par le degré (éviter la dominance des hubs)
        norm_a = 1.0 / max(degree_a, 1)
        norm_b = 1.0 / max(degree_b, 1)
        norm = math.sqrt(norm_a * norm_b)  # moyenne géométrique
        
        # Créer une onde localisée aux DEUX positions
        psi_a = self.field.concept_to_wavepacket(
            f"bridge_a_{pos_a:.4f}", position=pos_a, width=0.06
        )
        psi_b = self.field.concept_to_wavepacket(
            f"bridge_b_{pos_b:.4f}", position=pos_b, width=0.06
        )
        
        # L'onde de couplage = superposition avec modulation de phase
        psi_bridge = psi_a + psi_b * np.exp(1j * phase_rel)
        
        self.field.imprint(psi_bridge * 0.5 * norm)
    
    def stabilize(self, duration: float = 2.0):
        """Stabilise le champ après l'ajout de relations."""
        self.field.relax(duration=duration, temperature=0.01)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DÉCOMPOSITION ONDULATOIRE DE LA QUESTION
# ═══════════════════════════════════════════════════════════════════════════════

class QuestionDecomposer:
    """
    Décompose une question en langage naturel en ses COMPOSANTES ONDULATOIRES.
    
    Une question = CIBLE + RELATION + TROU
    
    Exemples :
    - "Quelle est la capitale de la France ?"
      → CIBLE = "France", RELATION = "capitale", TROU_POSITION = SUJET
    
    - "Paris est la capitale de quel pays ?"
      → CIBLE = "Paris", RELATION = "capitale", TROU_POSITION = OBJET
    
    - "Paris est la capitale de la France ?" (question oui/non)
      → CIBLE = "Paris", OBJET = "France", RELATION = "capitale", TROU = aucun
        → Question de VÉRIFICATION : est-ce que ce triplet existe ?
    """
    
    def __init__(self, graph: WaveCouplingGraph):
        self.graph = graph
    
    def decompose(self, question: str) -> dict:
        """
        Décompose une question en ses composantes.
        
        CRUCIAL : On distingue les ENTITÉS (dans concept_positions)
        des TYPES DE RELATION (dans relation_types).
        "capitale" est une RELATION, pas une entité.
        
        Returns:
            dict avec :
            - 'known_entities': entités connues (dans concept_positions)
            - 'relations_mentioned': types de relation mentionnés (dans relation_types)
            - 'gap_type': 'subject' | 'object' | 'verification'
        """
        tokens = re.findall(r'[a-zA-Zàâäéèêëîïôöùûüç]+', question.lower())
        
        known_entities = []
        relations_mentioned = []
        interrogative = None
        
        for token in tokens:
            if token in self.graph.interrogatifs:
                interrogative = token
                continue
            if token in self.graph.stopwords:
                continue
            
            # Est-ce une ENTITÉ connue (concept avec position) ?
            if token in self.graph.concept_positions:
                known_entities.append(token)
            
            # Est-ce un TYPE DE RELATION connu ?
            # Utilise un match FLOU : le token doit apparaître DANS le nom de la relation
            # (ex: "capitale" match "capitale_de", "ville" match "ville_de")
            for rel_type in self.graph.relation_types:
                if token in rel_type and rel_type not in relations_mentioned:
                    relations_mentioned.append(rel_type)
                    break
        
        # Déterminer le type de gap
        gap_type = self._determine_gap_type(question, known_entities, 
                                              relations_mentioned, interrogative)
        
        return {
            'tokens': tokens,
            'known_entities': known_entities,
            'relations_mentioned': relations_mentioned,
            'interrogative': interrogative,
            'gap_type': gap_type,
        }
    
    def _determine_gap_type(self, question: str, entities: List[str],
                             relations: List[str], interrogative: Optional[str]) -> str:
        """
        Détermine le TYPE de gap dans la question.
        
        Heuristique basée sur la structure de la phrase.
        """
        q = question.lower()
        
        # Détection question oui/non
        if q.startswith(('est-ce que', 'est ce que', 'est-il', 'est-elle')):
            return 'verification'
        
        # "Quelle est la capitale de X ?" → X est l'objet, capitale est la relation
        # → on cherche le SUJET (gap = subject)
        if any(pat in q for pat in ['capitale de', 'ville de', 'pays de']):
            return 'subject'
        
        # "X est la capitale de ?" → X est le sujet, capitale est la relation
        # → on cherche l'OBJET (gap = object)
        if any(pat in q for pat in ['de quel', 'de quelle', 'de quels']):
            return 'object'
        
        # "Quel animal est X ?" → X est le sujet, "est" est la relation
        # → on cherche l'OBJET (type d'animal)
        if any(pat in q for pat in ['quel animal', 'quelle espèce']):
            return 'object'
        
        # "Qui est X ?" / "Qu'est-ce que X ?"
        if interrogative in ('qui', 'que', 'quoi'):
            return 'object'
        
        # "Quel/Quelle X... ?" → X est probablement le gap
        if interrogative in ('quel', 'quelle', 'quels', 'quelles'):
            # Le mot juste après l'interrogatif est le type recherché
            return 'subject'
        
        return 'subject'  # défaut
    
    def create_excitation_wave(self, target_entity: str, width: float = 0.04) -> np.ndarray:
        """
        Crée l'ONDE D'EXCITATION centrée sur l'entité cible.
        
        C'est le "point de départ" de la propagation.
        """
        if target_entity not in self.graph.concept_positions:
            return np.zeros(self.graph.field.grid_size, dtype=np.complex128)
        
        pos = self.graph.concept_positions[target_entity]
        return self.graph.field.concept_to_wavepacket(
            target_entity, position=pos, width=width
        )
    
    def create_modulation_phase(self, relation_type: str) -> float:
        """
        Crée la PHASE DE MODULATION pour un type de relation.
        
        Cette phase FILTRE les couplages : seuls ceux qui matchent
        cette phase laissent passer l'onde.
        """
        return self.graph._hash_relation_phase(relation_type)
    
    def create_gap_modulation(self, gap_type: str) -> np.ndarray:
        """
        Crée une MODULATION DE GAP — le "trou" dans l'onde.
        
        Selon le type de gap :
        - 'subject' : modulation qui INVERSE la direction de propagation
        - 'object' : modulation qui SUIT la direction de propagation
        - 'verification' : modulation symétrique (aller-retour)
        """
        n = self.graph.field.grid_size
        
        if gap_type == 'subject':
            # Gap sujet : on cherche ce qui POINTE VERS la cible
            # → inversion de phase pour remonter les couplages
            return np.ones(n, dtype=np.complex128) * np.exp(1j * PI)
        
        elif gap_type == 'object':
            # Gap objet : on cherche ce vers quoi la cible POINTE
            # → phase nulle, suit la direction naturelle
            return np.ones(n, dtype=np.complex128)
        
        elif gap_type == 'verification':
            # Vérification : on teste si le couplage existe
            return np.ones(n, dtype=np.complex128) * np.exp(1j * PI / 2)
        
        else:
            return np.ones(n, dtype=np.complex128)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PROPAGATION D'ONDE À TRAVERS LE GRAPHE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveQuestionPropagator:
    """
    Pose une question au champ en PROPAGEANT une onde modulée
    à travers le graphe de couplage.
    
    ALGORITHME :
    1. EXCITATION : créer une onde localisée à la position de la CIBLE
    2. MODULATION : multiplier par exp(i·φ_rel) pour filtrer par type de relation
    3. GAP : appliquer la modulation de gap (inversion si sujet manquant)
    4. PROPAGATION : laisser l'onde évoluer dans le champ couplé
    5. DÉTECTION : mesurer où l'onde ARRIVE (hors point d'excitation)
    """
    
    def __init__(self, graph: WaveCouplingGraph):
        self.graph = graph
        self.decomposer = QuestionDecomposer(graph)
    
    def ask(self, question: str, candidates: List[str],
            propagation_time: float = 2.0,
            top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Pose une question en PROPAGEANT UNE ONDE MODULÉE.
        
        Args:
            question: question en langage naturel
            candidates: concepts candidats pour la réponse
            propagation_time: temps de propagation
            top_k: nombre de réponses
        
        Returns:
            liste de (candidat, intensité_locale) triée par intensité décroissante
        """
        # ═══ ÉTAPE 1 : DÉCOMPOSER LA QUESTION ═══
        decomp = self.decomposer.decompose(question)
        
        known_entities = decomp['known_entities']
        relations_mentioned = decomp['relations_mentioned']
        gap_type = decomp['gap_type']
        
        print(f"    [DÉCOMPOSITION] entités={known_entities}, "
              f"relations={relations_mentioned}, gap={gap_type}")
        
        if not known_entities:
            # Aucune entité connue → on ne peut pas ancrer la question
            return [(c, 0.0) for c in candidates[:top_k]]
        
        # ═══ ÉTAPE 2 : CRÉER L'ONDE D'EXCITATION ═══
        # On excite la première entité connue (la plus probablement la cible)
        target = known_entities[0]
        psi_excitation = self.decomposer.create_excitation_wave(target, width=0.05)
        
        if np.all(np.abs(psi_excitation) < 1e-30):
            return [(c, 0.0) for c in candidates[:top_k]]
        
        # ═══ ÉTAPE 3 : MODULER PAR LA RELATION ═══
        if relations_mentioned:
            # On a identifié une relation → modulation spécifique
            rel_type = relations_mentioned[0]
            phase_rel = self.decomposer.create_modulation_phase(rel_type)
        else:
            # Pas de relation identifiée → modulation neutre
            phase_rel = 0.0
        
        # Appliquer la modulation de relation à l'onde d'excitation
        psi_modulated = psi_excitation * np.exp(1j * phase_rel)
        
        # ═══ ÉTAPE 4 : APPLIQUER LA MODULATION DE GAP ═══
        gap_mod = self.decomposer.create_gap_modulation(gap_type)
        psi_probe = psi_modulated * gap_mod
        
        # ═══ ÉTAPE 5 : SAUVEGARDER L'ÉTAT DU CHAMP ═══
        psi_field_before = self.graph.field.psi.copy()
        
        # ═══ ÉTAPE 6 : INJECTER LA SONDE DANS LE CHAMP ═══
        self.graph.field.psi += psi_probe * 3.0  # Amplifier la sonde
        
        # ═══ ÉTAPE 7 : PROPAGATION ═══
        # Augmenter temporairement le couplage non-local pour favoriser
        # la propagation le long des "ponts" de relation
        saved_coupling = self.graph.field.coupling_strength
        self.graph.field.coupling_strength = 0.4  # Couplage plus fort
        
        self.graph.field.relax(duration=propagation_time, temperature=0.02)
        
        # Restaurer
        self.graph.field.coupling_strength = saved_coupling
        
        # ═══ ÉTAPE 8 : DÉTECTER L'ARRIVÉE ═══
        # Le champ a changé. Où l'énergie a-t-elle augmenté (hors point d'excitation) ?
        psi_field_after = self.graph.field.psi.copy()
        delta_psi = psi_field_after - psi_field_before
        
        # Restaurer le champ
        self.graph.field.psi = psi_field_before
        
        # ═══ ÉTAPE 9 : MESURER L'INTENSITÉ ARRIVÉE SUR CHAQUE CANDIDAT ═══
        # On mesure l'intensité du DELTA (changement) autour de chaque candidat
        # Exclure l'entité cible (elle a reçu l'excitation directe)
        
        exclude_positions = set()
        for ent in known_entities:
            if ent in self.graph.concept_positions:
                exclude_positions.add(self.graph.concept_positions[ent])
        
        results = []
        for cand in candidates:
            cand_lower = cand.lower().strip()
            if cand_lower not in self.graph.concept_positions:
                results.append((cand, 0.0))
                continue
            
            pos = self.graph.concept_positions[cand_lower]
            
            # Vérifier si c'est la position d'excitation
            is_excitation_target = any(
                abs(pos - excl_pos) < 0.05 or
                abs(pos - excl_pos) > 0.95  # wrap périodique
                for excl_pos in exclude_positions
            )
            
            if is_excitation_target and gap_type != 'verification':
                # On ne mesure pas le point d'excitation (sauf vérification)
                # → pénalité pour éviter de retourner la cible comme réponse
                results.append((cand, 0.0))
                continue
            
            # Mesurer l'intensité du DELTA autour de ce candidat
            halfwidth = int(0.05 * self.graph.field.grid_size)
            center_idx = int(pos / self.graph.L * self.graph.field.grid_size)
            start = max(0, center_idx - halfwidth)
            end = min(self.graph.field.grid_size, center_idx + halfwidth)
            
            local_delta_intensity = np.sum(np.abs(delta_psi[start:end])**2)
            
            results.append((cand, float(local_delta_intensity)))
        
        # Trier par intensité décroissante
        results.sort(key=lambda x: -x[1])
        
        # Normaliser les scores
        if results and results[0][1] > 0:
            max_score = results[0][1]
            results = [(c, s / max_score) for c, s in results]
        
        return results[:top_k]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_15_propagation_ondulatoire():
    """
    TEST 15 : PROPAGATION D'ONDE MODULÉE — La Question comme Onde
    
    Le test décisif : la question est décomposée en EXCITATION + MODULATION + GAP,
    et l'onde se PROPAGE à travers les couplages vers la réponse.
    """
    print("=" * 72)
    print("  TEST 15 : LA QUESTION COMME ONDE — Propagation Modulée")
    print("=" * 72)
    
    print("\n  PRINCIPE :")
    print("    Une question N'EST PAS un sac de mots.")
    print("    C'est : EXCITATION(cible) × MODULATION(relation) × GAP(direction)")
    print("    L'onde se PROPAGE à travers les couplages vers la réponse.")
    
    # Créer le champ et le graphe
    print("\n  Création du graphe de couplage ondulatoire...")
    field = NonLocalField(grid_size=128, L=1.0, 
                          coupling_sigma=0.08, coupling_strength=0.2)
    graph = WaveCouplingGraph(field)
    
    # Ajouter les concepts avec positions sémantiques
    # NOTE : "capitale", "ville", "pays" ne sont PAS des entités → pas ajoutés ici
    # Ils seront enregistrés comme types de relation via add_relation()
    clusters = {
        'geographie_france': (0.30, ["Paris", "Lyon", "Marseille", "France"]),
        'geographie_uk': (0.55, ["Londres", "Angleterre", "Manchester"]),
        'geographie_japon': (0.80, ["Tokyo", "Japon", "Osaka"]),
        'animaux': (0.15, ["chat", "chien", "félin", "mammifère", "animal"]),
    }
    
    for cluster_name, (center, words) in clusters.items():
        n = len(words)
        for i, word in enumerate(words):
            spread = 0.06
            offset = (i - (n - 1) / 2) * spread / max(n - 1, 1)
            pos = (center + offset) % 1.0
            graph.add_concept(word, pos)
    
    print(f"    {len(graph.concept_positions)} concepts positionnés")
    
    # Ajouter les relations (les faits)
    print("\n  Ajout des relations (faits)...")
    relations = [
        ("Paris", "capitale_de", "France"),
        ("Londres", "capitale_de", "Angleterre"),
        ("Tokyo", "capitale_de", "Japon"),
        ("Lyon", "ville_de", "France"),
        ("Marseille", "ville_de", "France"),
        ("Manchester", "ville_de", "Angleterre"),
        ("Osaka", "ville_de", "Japon"),
        ("chat", "est_un", "félin"),
        ("chat", "est_un", "animal"),
        ("chien", "est_un", "mammifère"),
        ("chien", "est_un", "animal"),
    ]
    
    for s, r, o in relations:
        graph.add_relation(s, r, o)
        print(f"    {s} --[{r}]--> {o}")
    
    # Stabiliser
    print("\n  Stabilisation du champ...")
    graph.stabilize(duration=2.0)
    print(f"    Champ : {field}")
    
    # Créer le propagateur
    propagator = WaveQuestionPropagator(graph)
    
    # Questions de test
    print("\n  ═══════════════════════════════════════════════════════")
    print("  QUESTIONS — Propagation d'Onde Modulée")
    print("  ═══════════════════════════════════════════════════════")
    
    questions_test = [
        # (question, réponse_attendue, candidats)
        ("Quelle est la capitale de la France ?", "Paris",
         ["Paris", "Londres", "Tokyo", "Lyon", "Marseille", "France"]),
        ("Quelle est la capitale de Angleterre ?", "Londres",
         ["Paris", "Londres", "Tokyo", "Lyon", "Marseille", "Angleterre"]),
        ("Quelle est la capitale du Japon ?", "Tokyo",
         ["Paris", "Londres", "Tokyo", "Lyon", "Marseille", "Japon"]),
        ("Quel animal est le chat ?", "félin",
         ["félin", "mammifère", "animal", "chien"]),
        ("Quel animal est le chien ?", "mammifère",
         ["félin", "mammifère", "animal", "chat"]),
        ("Paris est la capitale de quel pays ?", "France",
         ["France", "Angleterre", "Japon"]),
        ("Lyon est une ville de quel pays ?", "France",
         ["France", "Angleterre", "Japon"]),
        ("Quelle ville est en Angleterre ?", "Londres",
         ["Paris", "Londres", "Tokyo", "Lyon", "Marseille"]),
    ]
    
    correct = 0
    total = len(questions_test)
    
    for question, expected, candidates in questions_test:
        print(f"\n    Q: '{question}'")
        results = propagator.ask(question, candidates, 
                                 propagation_time=1.5, top_k=3)
        
        top_candidate = results[0][0] if results else "?"
        top_score = results[0][1] if results else 0.0
        
        is_correct = (top_candidate.lower() == expected.lower())
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        score_strs = [f"{c}={s:.3f}" for c, s in results]
        print(f"    Top 3 : {score_strs}")
        print(f"    Attendu: '{expected}' → Obtenu: '{top_candidate}' {status}")
    
    accuracy = correct / total * 100
    print(f"\n  ── Résultat ──")
    print(f"  Propagation d'onde modulée : {correct}/{total} ({accuracy:.0f}%)")
    
    if accuracy >= 75:
        print("  ✅ LA QUESTION COMME ONDE FONCTIONNE !")
        print("     La décomposition excitation×modulation×gap capte la structure.")
    elif accuracy >= 50:
        print("  ⚠️  Progrès significatif — la propagation est le bon mécanisme.")
    else:
        print("  ❌ La propagation seule ne suffit pas encore.")
    
    return accuracy


def test_16_comparaison_methodes():
    """
    TEST 16 : COMPARAISON — Toutes les méthodes de Question
    
    Compare :
    1. Champ pur (superposition de tokens)
    2. Hybride Champ × Kuramoto
    3. Propagation d'onde modulée (CE TEST)
    """
    print("\n" + "=" * 72)
    print("  TEST 16 : COMPARAISON — Évolution des Méthodes de Question")
    print("=" * 72)
    
    print("""
  ┌──────────────────────────────┬──────────┬─────────────────────────────────┐
  │ MÉTHODE                      │ PRÉCISION│ MÉCANISME                       │
  ├──────────────────────────────┼──────────┼─────────────────────────────────┤
  │ 1. Champ pur (sac de mots)   │   25%    │ Superposition de tokens         │
  │    Test 9                    │          │ Énergie diffuse partout         │
  ├──────────────────────────────┼──────────┼─────────────────────────────────┤
  │ 2. Hybride Champ × Kuramoto  │   57%    │ Synchronisation de phase        │
  │    Test 13                   │          │ Contraste 8-38x                 │
  ├──────────────────────────────┼──────────┼─────────────────────────────────┤
  │ 3. Propagation d'onde modulée│  (test)  │ Excitation × Modulation × Gap   │
  │    Test 15                   │          │ L'onde SUIT les couplages       │
  └──────────────────────────────┴──────────┴─────────────────────────────────┘
""")
    
    print("  DIFFÉRENCE FONDAMENTALE :")
    print("    Méthode 1 : Σ_i ψ_token_i        → sac de mots")
    print("    Méthode 2 : dθ_i/dt = Σ K_ij sin(θ_j-θ_i) → synchronisation")
    print("    Méthode 3 : ψ_excitation × exp(i·φ_rel) × gap → PROPAGATION")
    print()
    print("  La méthode 3 est la seule qui CAPTE LA STRUCTURE de la question :")
    print("    - QUI est la cible (point de départ)")
    print("    - QUEL type de relation (modulation)")
    print("    - QUELLE direction (gap sujet/objet/vérification)")
    
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EXÉCUTION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔" + "═" * 70 + "╗")
    print("║  🌊 LA QUESTION ONDULATOIRE — Décomposition Structurale                ║")
    print("║  Excitation × Modulation × Gap → Propagation → Réponse               ║")
    print("╚" + "═" * 70 + "╝")
    print()
    
    start_time = time.time()
    results = {}
    
    # Test 15 : Le test décisif — Propagation d'onde modulée
    try:
        acc = test_15_propagation_ondulatoire()
        results['propagation_onde'] = acc
    except Exception as e:
        print(f"\n  ❌ Test 15 ÉCHEC : {e}")
        import traceback
        traceback.print_exc()
        results['propagation_onde'] = 0.0
    
    # Test 16 : Comparaison
    try:
        test_16_comparaison_methodes()
    except Exception as e:
        print(f"\n  ❌ Test 16 ÉCHEC : {e}")
    
    # Résumé
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 72)
    print("  RÉSUMÉ — LA QUESTION ONDULATOIRE")
    print("=" * 72)
    
    for test_name, score in results.items():
        if isinstance(score, float):
            if score >= 75:
                status = "✅ RÉUSSI"
            elif score >= 50:
                status = "⚠️  PARTIEL"
            else:
                status = "❌ ÉCHEC"
            print(f"  Test 15 - {test_name}: {score:.0f}% {status}")
    
    print(f"\n  Temps total : {elapsed:.2f} secondes")
    
    if results.get('propagation_onde', 0) >= 60:
        print("\n  🌊 LA QUESTION ONDULATOIRE EST VALIDÉE.")
        print("  Décomposer la question en (excitation, modulation, gap)")
        print("  est la BONNE façon de dialoguer avec le champ.")
    else:
        print("\n  ⚠️  La propagation a besoin de raffinement.")
        print("  Le principe (excitation×modulation×gap) est correct,")
        print("  mais l'implémentation de la propagation peut être améliorée.")
    
    print("=" * 72)
