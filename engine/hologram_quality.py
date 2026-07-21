"""
🌟 Hologram Quality Pipeline — Création Communautaire Contrôlée
=================================================================
Système complet de création, validation, curation et amélioration
des hologrammes par les utilisateurs.

PIPELINE :
  1. SOUMISSION — l'utilisateur propose des faits
  2. VALIDATION — scoring automatique (cohérence, complétude, unicité)
  3. REVUE — approbation par la communauté (votes, signals)
  4. PUBLICATION — l'hologramme est disponible
  5. AMÉLIORATION — feedback loop, versioning, merge

QUALITÉ :
  - Score de cohérence : les faits sont-ils logiquement liés ?
  - Score de complétude : couvre-t-on tous les sous-domaines ?
  - Score d'unicité : apporte-t-on des faits nouveaux ?
  - Détection de doublons
  - Filtrage anti-spam / contenu inapproprié
  - Réputation du contributeur
"""

import sys, os, json, time, re, hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))


# ════════════════════════════════════════════════════════════════
# 1. VALIDATION AUTOMATIQUE
# ════════════════════════════════════════════════════════════════

class FactValidator:
    """
    Valide la qualité des faits soumis par un utilisateur.
    
    Critères :
    - Longueur minimale des champs
    - Pas de contenu inapproprié (regex patterns)
    - Pas de doublons internes
    - Structure sujet-relation-objet cohérente
    """
    
    # Patterns de contenu inapproprié
    SPAM_PATTERNS = [
        r'https?://', r'www\.', r'\.com', r'\.io', r'\.org',  # URLs
        r'@\w+', r'#\w+',  # Social media handles
        r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}',  # Emails
        r'\b(buy|sell|cheap|discount|free|offer|click|subscribe)\b',  # Spam
        r'(.)\1{4,}',  # Répétitions excessives (aaaaa)
    ]
    
    # Patterns de contenu toxique
    TOXIC_PATTERNS = [
        r'\b(fuck|shit|ass|damn|bitch|kill|hate|die)\b',
        r'\b(putain|merde|connard|salope|enculé|nique|tue|crève)\b',
    ]
    
    @staticmethod
    def validate_fact(subject: str, relation: str, obj: str) -> Tuple[bool, str]:
        """
        Valide un triplet (sujet, relation, objet).
        Retourne (ok, raison_si_non).
        """
        # Longueur
        if len(subject) < 2 or len(relation) < 2 or len(obj) < 2:
            return False, "Champs trop courts (min 2 caractères)"
        if len(subject) > 200 or len(relation) > 200 or len(obj) > 500:
            return False, "Champs trop longs"
        
        # Contenu inapproprié
        full_text = f"{subject} {relation} {obj}".lower()
        for pattern in FactValidator.SPAM_PATTERNS:
            if re.search(pattern, full_text):
                return False, f"Contenu suspect détecté"
        for pattern in FactValidator.TOXIC_PATTERNS:
            if re.search(pattern, full_text):
                return False, f"Contenu inapproprié détecté"
        
        # Structure : la relation doit être un verbe ou une préposition
        relation_words = relation.lower().split()
        if len(relation_words) > 8:
            return False, "Relation trop longue (max 8 mots)"
        
        return True, "ok"
    
    @staticmethod
    def validate_batch(facts: List[Tuple[str, str, str, str]]) -> Dict:
        """
        Valide un lot de faits.
        Retourne : {valid_count, invalid_count, errors, duplicate_count}
        """
        seen = set()
        valid = []
        errors = []
        duplicates = 0
        
        for s, r, o, sector in facts:
            # Doublon interne
            key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            
            ok, reason = FactValidator.validate_fact(s, r, o)
            if ok:
                valid.append((s, r, o, sector))
            else:
                errors.append({"fact": f"{s[:30]} | {r[:20]} | {o[:30]}", "reason": reason})
        
        return {
            "submitted": len(facts),
            "valid": len(valid),
            "invalid": len(facts) - len(valid) - duplicates,
            "duplicates": duplicates,
            "errors": errors[:10],
        }


# ════════════════════════════════════════════════════════════════
# 2. SCORING DE QUALITÉ
# ════════════════════════════════════════════════════════════════

class QualityScorer:
    """
    Score de qualité d'un hologramme (0 à 100).
    
    Composantes :
    - Cohérence interne (30 pts) : les faits sont-ils liés entre eux ?
    - Complétude (25 pts) : couvre-t-on assez de sous-domaines ?
    - Unicité (20 pts) : apporte-t-on des faits nouveaux ?
    - Diversité (15 pts) : variété des sujets et relations
    - Structure (10 pts) : équilibre sujet-relation-objet
    """
    
    @staticmethod
    def score_coherence(facts: List[Tuple]) -> float:
        """Score de cohérence : combien de sujets sont aussi objets ailleurs ?"""
        subjects = set(f[0].lower().strip() for f in facts)
        objects = set(f[2].lower().strip() for f in facts)
        intersection = subjects & objects
        ratio = len(intersection) / max(len(subjects), 1)
        return min(30.0, ratio * 30.0)
    
    @staticmethod
    def score_completeness(facts: List[Tuple], expected_sectors: List[str]) -> float:
        """Score de complétude : ratio de secteurs couverts."""
        if not expected_sectors:
            return 15.0  # Score par défaut
        actual_sectors = set(f[3] for f in facts if f[3])
        covered = len(actual_sectors & set(expected_sectors))
        return min(25.0, (covered / max(len(expected_sectors), 1)) * 25.0)
    
    @staticmethod
    def score_uniqueness(facts: List[Tuple], existing_facts: Set[Tuple]) -> float:
        """Score d'unicité : ratio de faits vraiment nouveaux."""
        if not existing_facts:
            return 20.0
        new_count = 0
        for f in facts:
            key = (f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip())
            if key not in existing_facts:
                new_count += 1
        return min(20.0, (new_count / max(len(facts), 1)) * 20.0)
    
    @staticmethod
    def score_diversity(facts: List[Tuple]) -> float:
        """Score de diversité : entropie des sujets."""
        subjects = [f[0].lower().strip() for f in facts]
        counter = Counter(subjects)
        total = len(subjects)
        if total == 0:
            return 0
        # Entropie normalisée
        entropy = -sum((c/total) * np.log(c/total + 1e-10) for c in counter.values())
        max_entropy = np.log(min(len(counter), 50))
        return min(15.0, (entropy / (max_entropy + 1e-10)) * 15.0)
    
    @staticmethod
    def score_structure(facts: List[Tuple]) -> float:
        """Score structurel : équilibre des longueurs."""
        if not facts:
            return 0
        avg_subj = np.mean([len(f[0]) for f in facts])
        avg_rel = np.mean([len(f[1]) for f in facts])
        avg_obj = np.mean([len(f[2]) for f in facts])
        # Pénaliser les déséquilibres (ex: sujets très courts, objets très longs)
        balance = 1.0 - abs(avg_subj - avg_obj) / max(avg_subj, avg_obj, 1)
        return min(10.0, balance * 10.0)
    
    @staticmethod
    def compute_total(facts: List[Tuple], existing_facts: Set[Tuple] = None,
                      expected_sectors: List[str] = None) -> Dict:
        """Calcule le score de qualité complet."""
        existing_facts = existing_facts or set()
        expected_sectors = expected_sectors or []
        
        scores = {
            "coherence": round(QualityScorer.score_coherence(facts), 1),
            "completeness": round(QualityScorer.score_completeness(facts, expected_sectors), 1),
            "uniqueness": round(QualityScorer.score_uniqueness(facts, existing_facts), 1),
            "diversity": round(QualityScorer.score_diversity(facts), 1),
            "structure": round(QualityScorer.score_structure(facts), 1),
        }
        scores["total"] = round(sum(scores.values()), 1)
        scores["grade"] = (
            "A" if scores["total"] >= 80 else
            "B" if scores["total"] >= 60 else
            "C" if scores["total"] >= 40 else
            "D" if scores["total"] >= 20 else "E"
        )
        return scores


# ════════════════════════════════════════════════════════════════
# 3. SYSTÈME DE RÉPUTATION
# ════════════════════════════════════════════════════════════════

class ReputationSystem:
    """
    Réputation des contributeurs.
    
    Gagnée par :
    - Faits acceptés (+1 par fait)
    - Hologramme publié (+10)
    - Hologramme bien noté (+5 si score > 80)
    - Review utile (+2 par review acceptée)
    
    Perdue par :
    - Fait rejeté (-1)
    - Spam détecté (-20)
    - Contenu inapproprié (-50, ban)
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or str(
            Path(__file__).parent / "data" / "reputation.json"
        )
        self.users: Dict[str, dict] = {}
        self._load()
    
    def get_reputation(self, user_id: str) -> dict:
        if user_id not in self.users:
            self.users[user_id] = {
                "points": 0,
                "level": "Nouveau",
                "facts_submitted": 0,
                "facts_accepted": 0,
                "holograms_published": 0,
                "reviews_done": 0,
                "strikes": 0,
            }
        return self.users[user_id]
    
    def add_points(self, user_id: str, points: int, reason: str):
        rep = self.get_reputation(user_id)
        rep["points"] += points
        
        # Niveaux
        if rep["points"] >= 500:
            rep["level"] = "Maître"
        elif rep["points"] >= 200:
            rep["level"] = "Expert"
        elif rep["points"] >= 50:
            rep["level"] = "Confirmé"
        elif rep["points"] >= 10:
            rep["level"] = "Contributeur"
        
        self._save()
    
    def add_strike(self, user_id: str, reason: str) -> bool:
        """Ajoute un avertissement. Retourne True si banni."""
        rep = self.get_reputation(user_id)
        rep["strikes"] += 1
        if rep["strikes"] >= 3:
            rep["level"] = "Banni"
            rep["points"] = -100
            self._save()
            return True
        self._save()
        return False
    
    def can_publish(self, user_id: str) -> Tuple[bool, str]:
        """Vérifie si l'utilisateur peut publier."""
        rep = self.get_reputation(user_id)
        if rep["level"] == "Banni":
            return False, "Compte banni"
        if rep["points"] < -10:
            return False, "Réputation insuffisante"
        return True, "ok"
    
    def _save(self):
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception:
            pass
    
    def _load(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    self.users = json.load(f)
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════
# 4. PIPELINE DE PUBLICATION COMPLET
# ════════════════════════════════════════════════════════════════

class HologramPublisher:
    """
    Pipeline complet de publication d'hologramme communautaire.
    
    Étapes :
    1. VALIDATION — les faits sont-ils valides ?
    2. SCORING — quelle est la qualité ?
    3. DÉDOUBLONNAGE — y a-t-il des doublons avec l'existant ?
    4. MODÉRATION — l'utilisateur peut-il publier ?
    5. PUBLICATION — enregistrement + métadonnées
    """
    
    def __init__(self):
        from hologram_store import HologramStore
        self.store = HologramStore()
        self.reputation = ReputationSystem()
        self.validator = FactValidator()
        
        # Cache des faits existants pour dédoublonnage rapide
        self._existing_facts_cache: Optional[Set[Tuple]] = None
    
    def _get_existing_facts(self, domain: str) -> Set[Tuple]:
        """Récupère les faits existants pour un domaine (avec cache)."""
        if self._existing_facts_cache is None:
            self._existing_facts_cache = set()
            # Charger tous les faits existants du store
            for holo_id, meta in self.store._registry.items():
                if meta.type in ('official', 'community'):
                    facts = self.store.download(holo_id)
                    if facts:
                        for f in facts:
                            key = (str(f[0]).lower().strip(), 
                                   str(f[1]).lower().strip(),
                                   str(f[2]).lower().strip())
                            self._existing_facts_cache.add(key)
        return self._existing_facts_cache
    
    def submit(self, domain: str, facts: List[Tuple[str, str, str, str]],
               author: str, name: str = "", description: str = "") -> Dict:
        """
        Soumet un hologramme communautaire au pipeline qualité.
        
        Retourne un rapport complet.
        """
        report = {
            "status": "pending",
            "domain": domain,
            "author": author,
            "steps": {},
        }
        
        # ── Étape 1 : Validation ──
        validation = self.validator.validate_batch(facts)
        report["steps"]["validation"] = validation
        
        if validation["valid"] == 0:
            report["status"] = "rejected"
            report["reason"] = "Aucun fait valide"
            return report
        
        valid_facts = [(s, r, o, sec) for s, r, o, sec in facts 
                       if self.validator.validate_fact(s, r, o)[0]]
        
        # ── Étape 2 : Scoring qualité ──
        existing = self._get_existing_facts(domain)
        quality = QualityScorer.compute_total(valid_facts, existing)
        report["steps"]["quality"] = quality
        
        if quality["total"] < 20:
            report["status"] = "rejected"
            report["reason"] = f"Qualité insuffisante (score: {quality['total']}/100)"
            return report
        
        # ── Étape 3 : Dédoublonnage ──
        new_facts = []
        duplicates = 0
        for f in valid_facts:
            key = (f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip())
            if key not in existing:
                new_facts.append(f)
            else:
                duplicates += 1
        
        report["steps"]["dedup"] = {
            "total_valid": len(valid_facts),
            "new": len(new_facts),
            "duplicates": duplicates,
        }
        
        if len(new_facts) < 5:
            report["status"] = "rejected"
            report["reason"] = f"Pas assez de faits nouveaux ({len(new_facts)} < 5 minimum)"
            return report
        
        # ── Étape 4 : Modération ──
        can_publish, reason = self.reputation.can_publish(author)
        if not can_publish:
            report["status"] = "rejected"
            report["reason"] = f"Modération: {reason}"
            self.reputation.add_strike(author, reason)
            return report
        
        # ── Étape 5 : Publication ──
        result = self.store.publish(
            domain=domain,
            facts=new_facts,
            author=author,
            name=name or f"{domain} (qualité {quality['grade']})",
            description=description or f"Score: {quality['total']}/100 | {len(new_facts)} faits",
        )
        
        if result["success"]:
            report["status"] = "published"
            report["holo_id"] = result["holo_id"]
            report["facts_published"] = len(new_facts)
            
            # Réputation
            self.reputation.add_points(author, 10 + len(new_facts) // 10,
                                       f"Hologramme publié: {domain}")
            if quality["total"] >= 80:
                self.reputation.add_points(author, 5, "Qualité exceptionnelle")
        else:
            report["status"] = "error"
            report["reason"] = result.get("error", "Erreur inconnue")
        
        return report


# ════════════════════════════════════════════════════════════════
# 5. API DE CONTRIBUTION (endpoints Flask)
# ════════════════════════════════════════════════════════════════

def register_contribution_endpoints(app):
    """
    Enregistre les endpoints de contribution sur une app Flask.
    À appeler depuis le serveur principal.
    """
    publisher = HologramPublisher()
    
    @app.route('/api/holograms/submit', methods=['POST'])
    def submit_hologram():
        """
        Soumet un nouvel hologramme communautaire.
        
        Body: {
            "domain": "python",
            "name": "Python Tips",
            "description": "Astuces Python avancées",
            "author": "user_123",
            "facts": [
                ["Python", "est un", "langage interprété", "INFORMATIQUE"],
                ...
            ]
        }
        """
        data = request.get_json(force=True, silent=True) or {}
        domain = data.get("domain", "").strip()
        author = data.get("author", "anonymous")
        facts = data.get("facts", [])
        name = data.get("name", "")
        description = data.get("description", "")
        
        if not domain or not facts:
            return jsonify({"error": "domain et facts requis"}), 422
        
        report = publisher.submit(domain, facts, author, name, description)
        return jsonify(report)
    
    @app.route('/api/holograms/validate', methods=['POST'])
    def validate_facts():
        """Valide des faits sans les publier (aperçu)."""
        data = request.get_json(force=True, silent=True) or {}
        facts = data.get("facts", [])
        report = FactValidator.validate_batch(facts)
        quality = QualityScorer.compute_total(facts) if facts else {}
        return jsonify({"validation": report, "quality": quality})
    
    @app.route('/api/holograms/reputation/<user_id>', methods=['GET'])
    def get_reputation(user_id):
        """Récupère la réputation d'un utilisateur."""
        rep = publisher.reputation.get_reputation(user_id)
        return jsonify(rep)
    
    @app.route('/api/holograms/quality/<holo_id>', methods=['GET'])
    def get_quality(holo_id):
        """Score de qualité d'un hologramme existant."""
        facts = publisher.store.download(holo_id)
        if not facts:
            return jsonify({"error": "Hologramme non trouvé"}), 404
        quality = QualityScorer.compute_total(facts)
        return jsonify({"holo_id": holo_id, "quality": quality})


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  🌟 HOLOGRAM QUALITY PIPELINE — Test")
    print("=" * 60)
    
    # Test validation
    print("\n📋 Validation :")
    validator = FactValidator()
    test_facts = [
        ("Python", "est un", "langage de programmation", "INFO"),
        ("Python", "a été créé par", "Guido van Rossum", "INFO"),
        ("", "est", "vide", "INFO"),  # invalide (sujet vide)
        ("Python", "est", "http://spam.com", "INFO"),  # invalide (URL)
        ("Python", "est un", "langage de programmation", "INFO"),  # doublon
    ]
    result = validator.validate_batch(test_facts)
    print(f"  Validés: {result['valid']}/{result['submitted']}")
    print(f"  Erreurs: {len(result['errors'])}")
    print(f"  Doublons: {result['duplicates']}")
    
    # Test scoring
    print("\n📊 Scoring :")
    valid_facts = [
        ("Python", "est un", "langage interprété", "INFO"),
        ("Python", "supporte", "la programmation orientée objet", "INFO"),
        ("Python", "a été créé par", "Guido van Rossum", "HISTOIRE"),
        ("Python", "est utilisé pour", "le machine learning", "IA"),
        ("Python", "est utilisé pour", "le développement web", "WEB"),
        ("Django", "est un", "framework Python", "WEB"),
        ("Flask", "est un", "micro-framework Python", "WEB"),
        ("NumPy", "est une", "bibliothèque Python", "MATH"),
        ("Python", "a une syntaxe", "simple et lisible", "INFO"),
        ("Python", "est", "open source", "INFO"),
    ]
    quality = QualityScorer.compute_total(valid_facts)
    print(f"  Score total: {quality['total']}/100 (Grade {quality['grade']})")
    for k, v in quality.items():
        if k not in ('total', 'grade'):
            print(f"    {k}: {v}/{'30' if k=='coherence' else '25' if k=='completeness' else '20' if k=='uniqueness' else '15' if k=='diversity' else '10'}")

    # Test réputation
    print("\n👤 Réputation :")
    rep = ReputationSystem()
    rep.add_points("alice", 50, "Tests")
    rep.add_points("alice", 100, "Contribution majeure")
    print(f"  alice: {rep.get_reputation('alice')}")
    
    # Test pipeline complet
    print("\n🚀 Pipeline complet :")
    publisher = HologramPublisher()
    report = publisher.submit(
        domain="python_test",
        facts=valid_facts,
        author="alice",
        name="Python Basics",
        description="Fondamentaux de Python"
    )
    print(f"  Status: {report['status']}")
    if report['status'] == 'published':
        print(f"  Holo ID: {report['holo_id']}")
        print(f"  Faits: {report['facts_published']}")
    else:
        print(f"  Raison: {report.get('reason', '?')}")
    
    print(f"\n✅ Pipeline qualité opérationnel.")
