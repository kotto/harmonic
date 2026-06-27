"""
API REST pour le Résoluteur Universel Harmonique.
Point d'entrée unique pour résoudre TOUS les types de problèmes.

Endpoints:
    POST /api/v1/resolver/resoudre  - Résoudre un problème
    GET  /api/v1/resolver/problemes  - Lister les problèmes disponibles
    GET  /api/v1/resolver/categories - Lister les catégories
    GET  /api/v1/resolver/statistiques - Statistiques du résoluteur
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from app.services.resolver_service import resolver

router = APIRouter(prefix="/api/v1/resolver", tags=["resolver"])


# ============================================================================
# MODÈLES DE DONNÉES
# ============================================================================

class RequeteResolution(BaseModel):
    """Requête de résolution d'un problème harmonique"""
    probleme_id: str
    parametres: Optional[Dict[str, Any]] = None


class ProblemeInfo(BaseModel):
    """Informations sur un problème"""
    id: str
    categorie: str
    enonce: str
    type: str
    entrees: List[str]


class ReponseResolution(BaseModel):
    """Réponse de résolution d'un problème"""
    probleme_id: str
    categorie: str
    solution: Any
    confiance: float
    constante_guide: str
    valeur_guide: float
    purete: float
    energie: float
    temps_execution: float
    recommandations: List[str]
    interpretation: str
    action: str


class StatistiquesResoluteur(BaseModel):
    """Statistiques du résoluteur"""
    total_problemes: int
    total_categories: int
    categories: Dict[str, int]
    types_disponibles: List[str]
    historique_resolutions: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/resoudre", response_model=ReponseResolution)
async def resoudre_probleme(requete: RequeteResolution):
    """
    Résout n'importe quel problème harmonique.
    
    Le Résoluteur Universel Harmonique utilise le cadre de raisonnement
    en 7 étapes (H0) pour résoudre TOUS les types de problèmes :
    - Optimisation (portefeuille, ressources, logistique)
    - Classification (détection fraude, sécurité réseau)
    - Prédiction (physique quantique, compréhension langage)
    - Créativité (composition musicale, génération art, code)
    - Décision (priorisation, tarification)
    
    Args:
        requete: { probleme_id: str, parametres?: dict }
        
    Returns:
        Solution complète avec interprétation harmonique
        
    Exemple:
        POST /api/v1/resolver/resoudre
        {
            "probleme_id": "optimisation_portefeuille",
            "parametres": {"actifs": 100, "risque": 0.3}
        }
    """
    try:
        if requete.parametres:
            solution = resolver.resoudre(
                requete.probleme_id,
                **requete.parametres
            )
        else:
            solution = resolver.resoudre(requete.probleme_id)
        
        interpretation = solution.interpretation
        
        return ReponseResolution(
            probleme_id=solution.probleme_id,
            categorie=solution.categorie.value,
            solution=solution.solution_harmonique.solution,
            confiance=solution.confiance,
            constante_guide=interpretation.get("constante_guide", ""),
            valeur_guide=interpretation.get("valeur_guide", 0.0),
            purete=interpretation.get("purete", 0.0),
            energie=interpretation.get("energie_finale", 0.0),
            temps_execution=solution.temps_execution,
            recommandations=solution.recommandations,
            interpretation=interpretation.get("interpretation", ""),
            action=interpretation.get("action", "")
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Problème inconnu: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de résolution: {str(e)}"
        )


@router.get("/problemes")
async def lister_problemes(
    categorie: Optional[str] = Query(None, description="Filtrer par catégorie")
):
    """
    Liste tous les problèmes disponibles dans le catalogue.
    
    Args:
        categorie: Filtre optionnel par catégorie (ex: "finance", "ia", "musique")
        
    Returns:
        Liste des problèmes avec leurs métadonnées
    """
    try:
        problemes = resolver.lister_problemes(categorie)
        
        return {
            "total": len(problemes),
            "categorie": categorie or "toutes",
            "problemes": [
                ProblemeInfo(
                    id=p.id,
                    categorie=p.categorie.value,
                    enonce=p.enonce,
                    type=p.type_probleme.value,
                    entrees=list(p.entrees.keys())
                )
                for p in problemes.values()
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )


@router.get("/categories")
async def lister_categories():
    """
    Liste toutes les catégories de problèmes disponibles.
    
    Returns:
        Liste des catégories avec le nombre de problèmes par catégorie
    """
    try:
        categories = resolver.lister_categories()
        stats = resolver.obtenir_statistiques()
        
        return {
            "total_categories": len(categories),
            "categories": categories,
            "repartition": stats["categories"]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )


@router.get("/statistiques", response_model=StatistiquesResoluteur)
async def obtenir_statistiques():
    """
    Statistiques d'utilisation du Résoluteur Universel Harmonique.
    
    Returns:
        Métriques sur le résoluteur et son utilisation
    """
    try:
        stats = resolver.obtenir_statistiques()
        return StatistiquesResoluteur(**stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )


@router.get("/catalogue")
async def catalogue_complet():
    """
    Catalogue complet organisé par catégories.
    
    Returns:
        Tous les problèmes organisés par catégorie avec détails
    """
    try:
        problemes = resolver.lister_problemes()
        categories = {}
        
        for p in problemes.values():
            cat = p.categorie.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "id": p.id,
                "enonce": p.enonce,
                "type": p.type_probleme.value,
                "entrees": list(p.entrees.keys()),
                "priorite": p.priorite
            })
        
        return {
            "total_problemes": len(problemes),
            "total_categories": len(categories),
            "categories": categories
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )
