"""
Domain Router + Feedback Engine
=================================
Deux optimisations majeures pour la spécialisation :

1. DOMAIN ROUTER — Détecte le domaine actif (médecine, droit, photo...)
   AVANT le retrieval. Filtre les faits par domaine pour éviter le bruit.

2. FEEDBACK ENGINE — L'utilisateur corrige une réponse → l'IA apprend.
   Ajoute/supprime/modifie des faits en temps réel, persiste localement.

Usage :
    from domain_router import DomainRouter, FeedbackEngine

    router = DomainRouter()
    router.set_active_domain('medecine')       # explicite
    domain = router.detect('symptomes fièvre') # automatique
    filtered = router.filter_facts(facts)       # ne garde que les faits du domaine

    feedback = FeedbackEngine()
    feedback.correct('user_123', 'paludisme est causé par le froid', 
                     'paludisme est causé par le parasite Plasmodium')
    # → Le fait faux est supprimé, le bon est ajouté, persisté
"""

import os, sys, json, time, re, logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional, Set

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DOMAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

# Signatures de domaines : mots-clés qui révèlent le domaine
DOMAIN_SIGNATURES = {
    'medecine': {
        'keywords': [
            'symptôme', 'symptome', 'traitement', 'maladie', 'patient', 'diagnostic',
            'vaccin', 'médicament', 'medicament', 'dose', 'prescription', 'fièvre',
            'fievre', 'douleur', 'infection', 'virus', 'bactérie', 'bacterie',
            'cancer', 'diabète', 'diabete', 'hypertension', 'cholestérol',
            'chirurgie', 'opération', 'operation', 'saignement', 'allergie',
            'paludisme', 'malaria', 'sida', 'vih', 'covid', 'grippe',
            'rythme cardiaque', 'tension', 'pouls', 'globule', 'plaquette',
            'système immunitaire', 'cellule', 'gène', 'gene', 'adn',
        ],
        'sectors': ['SANTE', 'CORPS_ORGANES', 'CORPS_SANTE', 'BIOLOGIE'],
    },
    'droit': {
        'keywords': [
            'loi', 'légal', 'legal', 'juridique', 'tribunal', 'avocat', 'juge',
            'contrat', 'constitution', 'droit', 'justice', 'procès', 'proces',
            'amende', 'peine', 'prison', 'droits', 'devoirs', 'responsabilité',
            'responsabilite', 'succession', 'héritage', 'heritage', 'testament',
            'mariage', 'divorce', 'garde', 'pension', 'impôt', 'impot',
            'réglementation', 'reglementation', 'norme', 'code', 'article',
        ],
        'sectors': ['POLITIQUE', 'DROIT', 'JURIDIQUE'],
    },
    'photographie': {
        'keywords': [
            'photo', 'photographie', 'appareil', 'objectif', 'focale', 'ouverture',
            'diaphragme', 'iso', 'vitesse', 'obturation', 'exposition', 'lumière',
            'composition', 'cadrage', 'profondeur de champ', 'portrait', 'paysage',
            'macro', 'flash', 'tripod', 'trépied', 'trepled', 'filtre',
            'raw', 'jpeg', 'pixel', 'résolution', 'resolution', 'capteur',
            'balance des blancs', 'netteté', 'nettete', 'flou',
        ],
        'sectors': ['CULTURE', 'CREATION', 'TECHNOLOGIE'],
    },
    'finance': {
        'keywords': [
            'argent', 'investissement', 'bourse', 'action', 'obligation',
            'dividende', 'pib', 'inflation', 'taux', 'crédit', 'credit',
            'emprunt', 'hypothèque', 'hypotheque', 'banque', 'compte',
            'épargne', 'epargne', 'revenu', 'impôt', 'impot', 'budget',
            'dette', 'déficit', 'deficit', 'croissance', 'récession',
            'monnaie', 'change', 'forex', 'crypto', 'bitcoin',
        ],
        'sectors': ['ECONOMIE'],
    },
    'technologie': {
        'keywords': [
            'code', 'programme', 'logiciel', 'algorithme', 'donnée', 'donnee',
            'internet', 'réseau', 'reseau', 'serveur', 'application', 'app',
            'python', 'javascript', 'html', 'css', 'sql', 'base de données',
            'api', 'cloud', 'ia', 'intelligence artificielle', 'machine learning',
            'robot', 'capteur', 'arduino', 'raspberry', 'électronique',
        ],
        'sectors': ['TECHNOLOGIE', 'TECH'],
    },
    'cuisine': {
        'keywords': [
            'recette', 'cuisine', 'plat', 'ingrédient', 'ingredient', 'cuisson',
            'four', 'poêle', 'poele', 'mélanger', 'melanger', 'épice', 'epice',
            'sauce', 'pâte', 'pate', 'farine', 'sucre', 'sel', 'beurre',
            'légume', 'legume', 'fruit', 'viande', 'poisson', 'dessert',
        ],
        'sectors': ['CULTURE', 'CORPS'],
    },
    'education': {
        'keywords': [
            'apprendre', 'enseigner', 'cours', 'leçon', 'lecon', 'exercice',
            'examen', 'note', 'diplôme', 'diplome', 'étude', 'etude',
            'école', 'ecole', 'université', 'universite', 'élève', 'eleve',
            'professeur', 'pédagogie', 'pedagogie', 'mémoire', 'memoire',
            'compréhension', 'comprehension', 'révision', 'revision',
        ],
        'sectors': ['CULTURE', 'INTELLIGENCE'],
    },
    'agriculture': {
        'keywords': [
            'culture', 'récolte', 'recolte', 'semence', 'engrais', 'irrigation',
            'sol', 'terrain', 'champ', 'ferme', 'élevage', 'elevage',
            'bétail', 'betail', 'vache', 'mouton', 'poule', 'plante',
            'maladie des plantes', 'parasite', 'insecte', 'saison',
            'rotation', 'jachère', 'jeliere', 'compost',
        ],
        'sectors': ['ECOLOGIE', 'NATURE_VEGET', 'BIOLOGIE'],
    },
}


class DomainRouter:
    """
    Routeur de domaine — détecte et filtre par domaine.
    
    Un domaine actif peut être :
    - Défini explicitement (router.set_active_domain('medecine'))
    - Détecté automatiquement (router.detect('quel traitement pour...'))
    - Hérité de la spécialisation (quand l'utilisateur dit "spécialise-toi en X")
    """
    
    def __init__(self):
        self.active_domain: Optional[str] = None
        self.domain_history: List[str] = []  # historique pour détection automatique
        self.explicit: bool = False  # True si le domaine a été défini manuellement
    
    def set_active_domain(self, domain: str):
        """Définit le domaine actif explicitement."""
        self.active_domain = domain
        self.explicit = True
        self.domain_history.append(domain)
        log.info(f"🎯 Domaine actif: {domain} (explicite)")
    
    def clear_domain(self):
        """Réinitialise le domaine actif."""
        self.active_domain = None
        self.explicit = False
    
    def detect(self, question: str) -> Optional[str]:
        """
        Détecte le domaine d'une question.
        
        Returns:
            Le domaine détecté, ou None si indéterminé.
        """
        q_lower = question.lower()
        scores = Counter()
        
        for domain, sig in DOMAIN_SIGNATURES.items():
            for kw in sig['keywords']:
                if kw in q_lower:
                    scores[domain] += 1
        
        if scores:
            best = scores.most_common(1)[0]
            if best[1] >= 1:
                return best[0]
        
        return None
    
    def get_effective_domain(self, question: str) -> Optional[str]:
        """
        Retourne le domaine effectif pour une question.
        
        Priorité :
          1. Domaine explicite (si non expiré)
          2. Domaine détecté automatiquement
          3. Dernier domaine de l'historique
        """
        # 1. Détection automatique d'abord (surpasse l'explicite si fort signal)
        detected = self.detect(question)
        if detected:
            return detected
        
        # 2. Domaine explicite
        if self.active_domain:
            return self.active_domain
        
        # 3. Historique
        if self.domain_history:
            return self.domain_history[-1]
        
        return None
    
    def filter_facts(self, facts: List[Tuple], question: str = None,
                     strictness: float = 0.7) -> List[Tuple]:
        """
        Filtre les faits par domaine.
        
        Args:
            facts: liste de (sujet, relation, objet, secteur)
            question: question pour détecter le domaine
            strictness: 0 = pas de filtre, 1 = strict (uniquement le domaine)
        
        Returns:
            Faits filtrés (si domaine détecté) ou tous les faits (si indéterminé)
        """
        domain = self.get_effective_domain(question) if question else self.active_domain
        
        if not domain or strictness < 0.1:
            return facts  # Pas de filtre
        
        sig = DOMAIN_SIGNATURES.get(domain)
        if not sig:
            return facts
        
        target_sectors = set(sig['sectors'])
        keywords = set(kw.lower() for kw in sig['keywords'])
        
        domain_facts = []
        general_facts = []
        
        for fact in facts:
            s, r, o, sec = fact[0], fact[1], fact[2], fact[3] if len(fact) > 3 else 'GENERAL'
            sec_upper = str(sec).upper()
            text = f"{s} {r} {o}".lower()
            
            # Fait du domaine ?
            is_domain = (
                any(ts in sec_upper for ts in target_sectors) or
                any(kw in text for kw in keywords)
            )
            
            if is_domain:
                domain_facts.append(fact)
            else:
                general_facts.append(fact)
        
        # Mélanger selon la strictness
        if not domain_facts:
            return facts  # Aucun fait du domaine → garder tout
        
        # strictness=0.7 : 70% faits du domaine + 30% généraux
        n_domain = len(domain_facts)
        n_general = int(len(general_facts) * (1 - strictness))
        
        return domain_facts + general_facts[:n_general]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FEEDBACK ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class FeedbackEngine:
    """
    Moteur de feedback — l'utilisateur corrige l'IA en temps réel.
    
    Types de feedback :
      - CORRECT : "non, c'est faux" → le fait est supprimé/affaibli
      - ADD     : "apprends que X est Y" → nouveau fait ajouté
      - REFINE  : "en fait, c'est plutôt Z" → fait modifié
      - CONFIRM : "oui, c'est exact" → fait renforcé
    
    Persistance :
      - corrections sauvées dans data/users/<user_id>/corrections.json
      - faits personnalisés sauvés dans data/users/<user_id>/user_facts.npz
    """
    
    def __init__(self):
        self.users_dir = _ENGINE_DIR / "data" / "users"
        self.users_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache des corrections par utilisateur
        self._corrections: Dict[str, List[dict]] = {}
        
        # Faits personnalisés ajoutés par les utilisateurs
        self._user_facts: Dict[str, List[Tuple[str, str, str, str]]] = {}
    
    def _user_dir(self, user_id: str) -> Path:
        d = self.users_dir / user_id
        d.mkdir(parents=True, exist_ok=True)
        return d
    
    def _load_corrections(self, user_id: str):
        if user_id in self._corrections:
            return
        path = self._user_dir(user_id) / 'corrections.json'
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._corrections[user_id] = json.load(f)
            except Exception:
                self._corrections[user_id] = []
        else:
            self._corrections[user_id] = []
    
    def _save_corrections(self, user_id: str):
        path = self._user_dir(user_id) / 'corrections.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._corrections.get(user_id, []), f, ensure_ascii=False, indent=2)
    
    def correct(self, user_id: str, wrong_statement: str,
                correct_statement: str, domain: str = None) -> dict:
        """
        L'utilisateur signale une erreur et donne la correction.
        
        Args:
            wrong_statement: ce que l'IA a dit de faux
            correct_statement: ce qui est correct
            domain: domaine optionnel
        
        Returns:
            Résultat de la correction
        """
        self._load_corrections(user_id)
        
        correction = {
            'type': 'correct',
            'wrong': wrong_statement[:500],
            'correct': correct_statement[:500],
            'domain': domain,
            'timestamp': time.time(),
        }
        self._corrections[user_id].append(correction)
        self._save_corrections(user_id)
        
        # Extraire un fait de la correction et l'ajouter
        facts = self._extract_facts_from_correction(correct_statement, domain)
        if facts:
            self.add_facts(user_id, facts)
        
        log.info(f"✏️ Correction de {user_id}: '{wrong_statement[:40]}' → '{correct_statement[:40]}'")
        
        return {
            'success': True,
            'correction_id': len(self._corrections[user_id]),
            'facts_added': len(facts),
            'message': f"Merci ! J'ai appris de cette correction. {len(facts)} fait(s) ajouté(s).",
        }
    
    def add_facts(self, user_id: str,
                  facts: List[Tuple[str, str, str, str]]) -> dict:
        """
        Ajoute des faits personnalisés pour un utilisateur.
        """
        self._load_corrections(user_id)
        
        if user_id not in self._user_facts:
            self._user_facts[user_id] = []
        
        added = 0
        for fact in facts:
            s, r, o = str(fact[0]), str(fact[1]), str(fact[2])
            sec = str(fact[3]) if len(fact) > 3 else 'USER'
            if len(s) >= 2 and len(r) >= 2 and len(o) >= 2:
                self._user_facts[user_id].append((s, r, o, sec))
                added += 1
        
        # Sauvegarder
        self._save_user_facts(user_id)
        
        # Ajouter au FastRetriever si disponible
        try:
            from page_forge import _init_fast_retriever, _FAST_RETRIEVER
            _init_fast_retriever()
            if _FAST_RETRIEVER and added > 0:
                _FAST_RETRIEVER.add_facts(
                    [(s, r, o, sec) for s, r, o, sec in self._user_facts[user_id][-added:]]
                )
        except Exception:
            pass
        
        return {
            'success': True,
            'facts_added': added,
            'total_user_facts': len(self._user_facts.get(user_id, [])),
        }
    
    def learn_from_statement(self, user_id: str, statement: str,
                             domain: str = None) -> dict:
        """
        L'utilisateur dit "apprends que X est Y".
        
        Détecte le pattern d'apprentissage et extrait le fait.
        """
        s_lower = statement.lower().strip()
        
        # Patterns d'apprentissage
        patterns = [
            # "apprends que X est Y"
            (r"(?:apprends|retiens|sache|mémorise|memorise)\s+que\s+(.+?)\s+(?:est|sont|a|font|peuvent)\s+(.+)", 'est'),
            # "X est Y"
            (r"(.+?)\s+est\s+(?:un|une|le|la|l')\s*(.+)", 'est'),
            # "X a pour Y Z"
            (r"(.+?)\s+a\s+pour\s+(.+?)\s+(.+)", 'a pour'),
            # "X se trouve à/en Y"
            (r"(.+?)\s+(?:se trouve|est situé|est situe)\s+(?:à|a|en|au)\s+(.+)", 'est situé à'),
        ]
        
        facts = []
        for pattern, relation in patterns:
            match = re.search(pattern, s_lower)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    s = groups[0].strip()[:100]
                    o = groups[1].strip()[:100] if len(groups) == 2 else groups[-1].strip()[:100]
                    sec = domain.upper() if domain else 'USER'
                    facts.append((s, relation, o, sec))
                    break
        
        if not facts:
            # Apprentissage générique : stocker la phrase entière comme fait
            facts.append((statement[:80], 'appris de', user_id, 'USER'))
        
        result = self.add_facts(user_id, facts)
        result['extracted_facts'] = [(s, r, o) for s, r, o, sec in facts]
        
        log.info(f"📚 Apprentissage de {user_id}: {len(facts)} fait(s) extrait(s)")
        return result
    
    def _extract_facts_from_correction(self, statement: str,
                                       domain: str = None) -> List[Tuple[str, str, str, str]]:
        """Extrait des faits d'une correction."""
        facts = []
        
        # Pattern : "X est Y" ou "X sont Y"
        for match in re.finditer(
            r"([A-ZÉÈÊËÀÂÄÔÖÎÏÛÜÇ][^,.]+?)\s+(?:est|sont|a|se trouve|est causé|est cause)\s+([^,.]+?)(?:\.|,|$)",
            statement
        ):
            s = match.group(1).strip()[:100]
            o = match.group(2).strip()[:100]
            if len(s) > 3 and len(o) > 3:
                sec = domain.upper() if domain else 'USER'
                facts.append((s, 'est', o, sec))
        
        return facts[:3]  # Max 3 faits par correction
    
    def _save_user_facts(self, user_id: str):
        """Sauvegarde les faits utilisateur en .npz."""
        import numpy as np
        facts = self._user_facts.get(user_id, [])
        if not facts:
            return
        
        path = self._user_dir(user_id) / 'user_facts.npz'
        subjects = np.array([f[0] for f in facts], dtype=object)
        relations = np.array([f[1] for f in facts], dtype=object)
        objects = np.array([f[2] for f in facts], dtype=object)
        sectors = np.array([f[3] for f in facts], dtype=object)
        
        np.savez_compressed(str(path),
            subjects=subjects, relations=relations,
            objects=objects, sectors=sectors,
            amplitudes=np.ones(len(facts), dtype=np.float32) * 3.0,  # amplitude renforcée
            psies_real=np.zeros((len(facts), 64), dtype=np.float32),
            psies_imag=np.zeros((len(facts), 64), dtype=np.float32))
    
    def load_user_facts(self, user_id: str) -> List[Tuple[str, str, str, str]]:
        """Charge les faits d'un utilisateur depuis le disque."""
        import numpy as np
        path = self._user_dir(user_id) / 'user_facts.npz'
        if not path.exists():
            return []
        
        try:
            data = np.load(str(path), allow_pickle=True)
            facts = []
            for i in range(len(data['subjects'])):
                facts.append((
                    str(data['subjects'][i]),
                    str(data['relations'][i]),
                    str(data['objects'][i]),
                    str(data['sectors'][i]) if 'sectors' in data else 'USER',
                ))
            return facts
        except Exception:
            return []
    
    def get_stats(self, user_id: str) -> dict:
        """Statistiques de feedback pour un utilisateur."""
        self._load_corrections(user_id)
        user_facts = self._user_facts.get(user_id, [])
        corrections = self._corrections.get(user_id, [])
        
        return {
            'total_corrections': len(corrections),
            'total_user_facts': len(user_facts),
            'recent_corrections': corrections[-5:],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  🎯 DOMAIN ROUTER + ✏️ FEEDBACK ENGINE — Démo            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # === DOMAIN ROUTER ===
    print("\n=== DOMAIN ROUTER ===")
    router = DomainRouter()
    
    tests = [
        "Quel traitement pour le paludisme ?",
        "Quelle ouverture pour un portrait ?",
        "Quel est le taux d'imposition ?",
        "Comment fonctionne la photosynthèse ?",
        "Code python pour trier une liste",
    ]
    
    for q in tests:
        domain = router.detect(q)
        print(f"  '{q[:50]}' → {domain or 'indéterminé'}")
    
    # === FEEDBACK ENGINE ===
    print("\n=== FEEDBACK ENGINE ===")
    feedback = FeedbackEngine()
    
    # Test : apprentissage
    result = feedback.learn_from_statement('user_demo',
        'apprends que le paludisme est causé par le parasite Plasmodium',
        domain='medecine')
    print(f"  Apprentissage: {result['facts_added']} fait(s) ajouté(s)")
    
    # Test : correction
    result = feedback.correct('user_demo',
        'Le paludisme est causé par le froid',
        'Le paludisme est causé par le parasite Plasmodium transmis par le moustique anophèle',
        domain='medecine')
    print(f"  Correction: {result['facts_added']} fait(s) appris")
    
    # Stats
    stats = feedback.get_stats('user_demo')
    print(f"  Stats: {stats['total_corrections']} corrections, {stats['total_user_facts']} faits")
    
    # Vérifier que les faits sont bien là
    user_facts = feedback.load_user_facts('user_demo')
    print(f"\n  Faits utilisateur chargés: {len(user_facts)}")
    for s, r, o, sec in user_facts:
        print(f"    [{sec}] {s} | {r} | {o}")
    
    print("\n✅ Domain Router + Feedback Engine opérationnels !")
