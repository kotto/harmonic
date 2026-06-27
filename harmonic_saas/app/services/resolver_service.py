"""
Service de résolution universelle harmonique.
Remplace les 7 services individuels (HDC, HCC, HSS, QFO, HLM, HCG, HAV)
par un unique moteur de raisonnement harmonique en 7 étapes (H0).

Utilise le Résoluteur Universel Harmonique pour résoudre
TOUS les types de problèmes avec le même cadre.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Ajouter le chemin du résoluteur universel
RESOLUTEUR_PATH = Path(__file__).parent.parent.parent.parent / "FINAL" / "theorie_unifiee_harmonique"
if RESOLUTEUR_PATH.exists():
    sys.path.insert(0, str(RESOLUTEUR_PATH))
else:
    # Fallback : chemin relatif
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from resoluteur_universel_harmonique import (
    ResoluteurUniverselHarmonique, ProblemeUniversel,
    CategorieProbleme, TypeProbleme, SolutionUniverselle
)


class ResolverService:
    """
    Service unique de résolution harmonique.
    Point d'entrée unique pour TOUS les problèmes de l'IA harmonique.
    
    Utilisation:
        resolver = ResolverService()
        solution = resolver.resoudre("optimisation_portefeuille", actifs=100, risque=0.3)
    """
    
    _instance = None
    _resoluteur = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialiser()
        return cls._instance
    
    def _initialiser(self):
        """Initialisation unique du résoluteur"""
        try:
            self._resoluteur = ResoluteurUniverselHarmonique(seed=42)
            self._initialise = True
        except Exception as e:
            print(f"[ResolverService] Erreur d'initialisation: {e}")
            self._initialise = False
    
    @property
    def resoluteur(self) -> ResoluteurUniverselHarmonique:
        """Accès au résoluteur (initialisation paresseuse)"""
        if self._resoluteur is None:
            self._resoluteur = ResoluteurUniverselHarmonique(seed=42)
        return self._resoluteur
    
    def resoudre(self, probleme_id: str, **parametres) -> SolutionUniverselle:
        """
        Résout n'importe quel problème harmonique.
        
        Args:
            probleme_id: Identifiant du problème (ex: "optimisation_portefeuille")
            **parametres: Paramètres personnalisés pour le problème
            
        Returns:
            SolutionUniverselle avec interprétation et recommandations
            
        Exemple:
            solution = resolver.resoudre(
                "optimisation_portefeuille",
                actifs=100,
                risque=0.3,
                rendement=0.15
            )
            print(solution.interpretation['constante_guide'])  # "pi"
            print(solution.recommandations[0])  # Recommandation actionnable
        """
        return self.resoluteur.resoudre(
            probleme_id,
            entrees_personnalisees=parametres if parametres else None
        )
    
    def lister_problemes(self, categorie: Optional[str] = None) -> Dict[str, ProblemeUniversel]:
        """Liste les problèmes disponibles, filtrés par catégorie optionnelle"""
        catalogue = self.resoluteur.catalogue_problemes
        if categorie:
            return {
                k: v for k, v in catalogue.items()
                if v.categorie.value == categorie
            }
        return catalogue
    
    def lister_categories(self) -> List[str]:
        """Liste toutes les catégories de problèmes disponibles"""
        categories = set()
        for p in self.resoluteur.catalogue_problemes.values():
            categories.add(p.categorie.value)
        return sorted(categories)
    
    def ajouter_probleme(self, probleme: ProblemeUniversel) -> bool:
        """Ajoute un nouveau problème au catalogue"""
        if probleme.id in self.resoluteur.catalogue_problemes:
            return False
        self.resoluteur.catalogue_problemes[probleme.id] = probleme
        return True
    
    def resoudre_par_categorie(self, categorie: str) -> List[SolutionUniverselle]:
        """Résout tous les problèmes d'une catégorie"""
        cat_enum = None
        for c in CategorieProbleme:
            if c.value == categorie:
                cat_enum = c
                break
        
        if cat_enum is None:
            return []
        
        return self.resoluteur.resoudre_par_categorie(cat_enum)
    
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """Retourne les statistiques du résoluteur"""
        total = len(self.resoluteur.catalogue_problemes)
        categories = {}
        for p in self.resoluteur.catalogue_problemes.values():
            cat = p.categorie.value
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        return {
            "total_problemes": total,
            "total_categories": len(categories),
            "categories": categories,
            "types_disponibles": [t.value for t in TypeProbleme],
            "historique_resolutions": len(self.resoluteur.historique)
        }


# Instance globale pour utilisation facile
resolver = ResolverService()
