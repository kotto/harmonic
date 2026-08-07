"""
📚 Domain Seed Injection — Faits interconnectés pour domaines faibles
======================================================================
Injecte des faits riches et BIDIRECTIONNELS pour les domaines
où le KB original est pauvre (histoire, économie, astronomie...).

Principe : chaque fait est créé avec SON INVERSE pour garantir
une cohérence native élevée.
"""

import sys, os, time
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))


# ════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE FAITS INTERCONNECTÉS
# ════════════════════════════════════════════════════════════════

def make_bidirectional(subject: str, relation: str, obj: str, 
                       sector: str, inverse_relation: str = None) -> List[Tuple]:
    """
    Crée un fait ET son inverse pour garantir la bidirectionnalité.
    
    Ex: ("Soleil", "est une", "étoile", "ASTRONOMIE")
      → ("Soleil", "est une", "étoile", "ASTRONOMIE")
      → ("étoile", "a pour exemple", "Soleil", "ASTRONOMIE")
    """
    facts = [(subject, relation, obj, sector)]
    if inverse_relation:
        facts.append((obj, inverse_relation, subject, sector))
    return facts


def make_hierarchy(entity: str, parent: str, sector: str) -> List[Tuple]:
    """Crée une relation hiérarchique bidirectionnelle."""
    return make_bidirectional(entity, "est un type de", parent, sector,
                              "a pour sous-type")


def make_composition(whole: str, part: str, sector: str) -> List[Tuple]:
    """Crée une relation de composition bidirectionnelle."""
    return make_bidirectional(whole, "contient", part, sector,
                              "fait partie de")


def make_causality(cause: str, effect: str, sector: str) -> List[Tuple]:
    """Crée une relation causale bidirectionnelle."""
    return make_bidirectional(cause, "a causé", effect, sector,
                              "a été causé par")


# ════════════════════════════════════════════════════════════════
# DOMAINES À ENRICHIR
# ════════════════════════════════════════════════════════════════

def generate_astronomy_facts() -> List[Tuple]:
    """Faits interconnectés sur l'astronomie."""
    facts = []
    
    # Hiérarchie des corps célestes
    facts += make_hierarchy("Soleil", "étoile", "ASTRONOMIE")
    facts += make_hierarchy("Terre", "planète tellurique", "ASTRONOMIE")
    facts += make_hierarchy("Jupiter", "planète gazeuse", "ASTRONOMIE")
    facts += make_hierarchy("Mars", "planète tellurique", "ASTRONOMIE")
    facts += make_hierarchy("Lune", "satellite naturel", "ASTRONOMIE")
    facts += make_hierarchy("Voie Lactée", "galaxie spirale", "ASTRONOMIE")
    facts += make_hierarchy("Andromède", "galaxie spirale", "ASTRONOMIE")
    facts += make_hierarchy("Sirius", "étoile", "ASTRONOMIE")
    facts += make_hierarchy("Betelgeuse", "supergéante rouge", "ASTRONOMIE")
    facts += make_hierarchy("Trou noir supermassif", "trou noir", "ASTRONOMIE")
    
    # Composition
    facts += make_composition("Système Solaire", "Soleil", "ASTRONOMIE")
    facts += make_composition("Système Solaire", "Terre", "ASTRONOMIE")
    facts += make_composition("Système Solaire", "Mars", "ASTRONOMIE")
    facts += make_composition("Système Solaire", "Jupiter", "ASTRONOMIE")
    facts += make_composition("Voie Lactée", "Système Solaire", "ASTRONOMIE")
    facts += make_composition("Univers", "Voie Lactée", "ASTRONOMIE")
    facts += make_composition("Univers", "Andromède", "ASTRONOMIE")
    facts += make_composition("Terre", "Lune", "ASTRONOMIE")
    
    # Découvertes
    facts += make_bidirectional("Galilée", "a observé", "les lunes de Jupiter", "ASTRONOMIE",
                                "a été observé par")
    facts += make_bidirectional("Hubble", "a découvert", "l'expansion de l'univers", "ASTRONOMIE",
                                "a été découverte par")
    facts += make_bidirectional("Copernic", "a proposé", "le modèle héliocentrique", "ASTRONOMIE",
                                "a été proposé par")
    
    return facts


def generate_economy_facts() -> List[Tuple]:
    """Faits interconnectés sur l'économie."""
    facts = []
    
    # Concepts fondamentaux
    facts += make_hierarchy("PIB", "indicateur économique", "ECONOMIE")
    facts += make_hierarchy("inflation", "phénomène économique", "ECONOMIE")
    facts += make_hierarchy("chômage", "indicateur économique", "ECONOMIE")
    facts += make_hierarchy("taux d'intérêt", "outil de politique monétaire", "ECONOMIE")
    facts += make_hierarchy("marché boursier", "marché financier", "ECONOMIE")
    facts += make_hierarchy("capitalisme", "système économique", "ECONOMIE")
    facts += make_hierarchy("socialisme", "système économique", "ECONOMIE")
    facts += make_hierarchy("libéralisme", "doctrine économique", "ECONOMIE")
    facts += make_hierarchy("keynésianisme", "théorie économique", "ECONOMIE")
    
    # Relations causales
    facts += make_causality("crise de 1929", "Grande Dépression", "ECONOMIE")
    facts += make_causality("choc pétrolier de 1973", "récession mondiale", "ECONOMIE")
    facts += make_causality("crise des subprimes", "crise financière de 2008", "ECONOMIE")
    
    # Acteurs
    facts += make_bidirectional("Adam Smith", "a écrit", "La Richesse des Nations", "ECONOMIE",
                                "a été écrit par")
    facts += make_bidirectional("Keynes", "a fondé", "la macroéconomie moderne", "ECONOMIE",
                                "a été fondée par")
    facts += make_bidirectional("banque centrale", "contrôle", "la masse monétaire", "ECONOMIE",
                                "est contrôlée par")
    
    # Mécanismes
    facts += make_bidirectional("offre et demande", "déterminent", "le prix d'équilibre", "ECONOMIE",
                                "sont déterminés par")
    facts += make_bidirectional("taux d'intérêt élevé", "réduit", "l'investissement", "ECONOMIE",
                                "est réduit par")
    
    return facts


def generate_history_france_facts() -> List[Tuple]:
    """Faits interconnectés sur l'Histoire de France."""
    facts = []
    
    # Périodes
    facts += make_hierarchy("Moyen Âge", "période historique", "HISTOIRE")
    facts += make_hierarchy("Renaissance", "période historique", "HISTOIRE")
    facts += make_hierarchy("Révolution française", "révolution", "HISTOIRE")
    facts += make_hierarchy("Première Guerre mondiale", "guerre mondiale", "HISTOIRE")
    facts += make_hierarchy("Seconde Guerre mondiale", "guerre mondiale", "HISTOIRE")
    facts += make_hierarchy("Révolution française", "événement fondateur", "HISTOIRE")
    facts += make_hierarchy("Empire napoléonien", "empire", "HISTOIRE")
    facts += make_hierarchy("Troisième République", "république", "HISTOIRE")
    
    # Composition chronologique
    facts += make_bidirectional("Révolution française", "a précédé", "Empire napoléonien", "HISTOIRE",
                                "a succédé à")
    facts += make_bidirectional("Moyen Âge", "a précédé", "Renaissance", "HISTOIRE",
                                "a succédé à")
    facts += make_bidirectional("Première Guerre mondiale", "a précédé", "Seconde Guerre mondiale", "HISTOIRE",
                                "a succédé à")
    facts += make_bidirectional("Prise de la Bastille", "a déclenché", "Révolution française", "HISTOIRE",
                                "a été déclenchée par")
    
    # Personnages
    facts += make_bidirectional("Louis XIV", "était", "roi de France", "HISTOIRE",
                                "a été gouvernée par")
    facts += make_bidirectional("Napoléon", "était", "empereur des Français", "HISTOIRE",
                                "a été gouverné par")
    facts += make_bidirectional("De Gaulle", "a fondé", "la Cinquième République", "HISTOIRE",
                                "a été fondée par")
    facts += make_bidirectional("Jeanne d'Arc", "a mené", "la résistance contre les Anglais", "HISTOIRE",
                                "a été menée par")
    
    # Événements
    facts += make_bidirectional("Traité de Versailles", "a mis fin à", "Première Guerre mondiale", "HISTOIRE",
                                "a été terminée par")
    facts += make_bidirectional("Débarquement de Normandie", "a contribué à", "libération de la France", "HISTOIRE",
                                "a été permis par")
    
    return facts


def generate_medicine_facts() -> List[Tuple]:
    """Faits interconnectés supplémentaires sur la médecine."""
    facts = []
    
    # Hiérarchie médicale
    facts += make_hierarchy("cardiologie", "spécialité médicale", "SANTE")
    facts += make_hierarchy("neurologie", "spécialité médicale", "SANTE")
    facts += make_hierarchy("pédiatrie", "spécialité médicale", "SANTE")
    facts += make_hierarchy("oncologie", "spécialité médicale", "SANTE")
    facts += make_hierarchy("antibiotique", "médicament", "SANTE")
    facts += make_hierarchy("vaccin", "traitement préventif", "SANTE")
    facts += make_hierarchy("chimiothérapie", "traitement anticancéreux", "SANTE")
    
    # Composition
    facts += make_composition("système cardiovasculaire", "cœur", "SANTE")
    facts += make_composition("système nerveux", "cerveau", "SANTE")
    facts += make_composition("système immunitaire", "globules blancs", "SANTE")
    facts += make_composition("squelette", "os", "SANTE")
    
    # Découvertes
    facts += make_bidirectional("Pasteur", "a développé", "le vaccin contre la rage", "SANTE",
                                "a été développé par")
    facts += make_bidirectional("Fleming", "a découvert", "la pénicilline", "SANTE",
                                "a été découverte par")
    facts += make_bidirectional("Jenner", "a inventé", "la vaccination", "SANTE",
                                "a été inventée par")
    
    # Relations
    facts += make_bidirectional("vaccin", "protège contre", "maladie infectieuse", "SANTE",
                                "est prévenue par")
    facts += make_bidirectional("antibiotique", "combat", "infection bactérienne", "SANTE",
                                "est combattue par")
    
    return facts


# ════════════════════════════════════════════════════════════════
# INJECTION DANS LE KB
# ════════════════════════════════════════════════════════════════

def inject_domain_seeds(output_path: str = None):
    """
    Injecte les faits interconnectés dans le KB enrichi.
    """
    print("=" * 60)
    print("  📚 DOMAIN SEED INJECTION")
    print("=" * 60)
    
    # Charger le KB enrichi existant
    enriched_path = _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'knowledge_base_enriched.npz'
    if not enriched_path.exists():
        print("KB enrichi introuvable. Lancez d'abord kb_enrichment.py")
        return
    
    data = np.load(str(enriched_path), allow_pickle=True)
    existing_facts = [(str(f[0]), str(f[1]), str(f[2]), 
                      str(f[3]) if len(f) > 3 else "GENERAL") 
                     for f in data['facts']]
    print(f"KB actuel : {len(existing_facts):,} faits")
    
    # Générer les nouveaux faits
    generators = [
        ("Astronomie", generate_astronomy_facts),
        ("Économie", generate_economy_facts),
        ("Histoire de France", generate_history_france_facts),
        ("Médecine", generate_medicine_facts),
    ]
    
    all_new = []
    for name, gen in generators:
        t0 = time.time()
        new_facts = gen()
        all_new.extend(new_facts)
        print(f"  {name:<20} : +{len(new_facts):>4} faits interconnectés ({time.time()-t0:.2f}s)")
    
    # Dédupliquer
    existing_keys = set()
    for f in existing_facts:
        existing_keys.add((f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip()))
    
    unique_new = []
    for f in all_new:
        key = (f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip())
        if key not in existing_keys:
            existing_keys.add(key)
            unique_new.append(f)
    
    print(f"\n  ✅ {len(unique_new)} faits uniques ajoutés (sur {len(all_new)} générés)")
    
    # Fusionner
    all_facts = existing_facts + unique_new
    print(f"  📦 KB final : {len(all_facts):,} faits")
    
    # Sauvegarder
    if output_path is None:
        output_path = enriched_path
    
    from kb_enrichment import KBEnrichmentPipeline
    pipeline = KBEnrichmentPipeline()
    pipeline._save(all_facts, str(output_path))
    
    print(f"\n✅ Injection terminée.")
    return len(unique_new)


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    inject_domain_seeds()
