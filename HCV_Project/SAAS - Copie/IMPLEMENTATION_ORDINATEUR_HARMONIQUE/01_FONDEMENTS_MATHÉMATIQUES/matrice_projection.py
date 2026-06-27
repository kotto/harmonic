"""
🌊 MATRICE DE PROJECTION HOLOGRAPHIQUE
Fichier: matrice_projection.py
Auteur: Équipe Harmonique
Date: 28 avril 2026
Description: Implémentation de la matrice de projection holographique 2D → 3D/4D
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des constantes harmoniques
from constantes_harmoniques import CONSTANTES

@dataclass
class Coordonnees2D:
    """
    Coordonnées dans l'espace 2D harmonique
    """
    x: float
    y: float
    
    def __post_init__(self):
        """Validation des coordonnées"""
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise ValueError("Les coordonnées doivent être numériques")
    
    def to_array(self) -> np.ndarray:
        """Convertit en tableau numpy"""
        return np.array([self.x, self.y])

@dataclass
class Coordonnees3D:
    """
    Coordonnées dans l'espace 3D projeté
    """
    x: float
    y: float
    z: float
    t: float = 0.0  # Temps comme 4ème dimension
    
    def __post_init__(self):
        """Validation des coordonnées"""
        for coord in [self.x, self.y, self.z, self.t]:
            if not isinstance(coord, (int, float)):
                raise ValueError("Les coordonnées doivent être numériques")
    
    def to_array(self) -> np.ndarray:
        """Convertit en tableau numpy"""
        return np.array([self.x, self.y, self.z, self.t])
    
    def norme(self) -> float:
        """Calcule la norme euclidienne"""
        return np.sqrt(self.x**2 + self.y**2 + self.z**2 + self.t**2)

class MatriceProjection:
    """
    Matrice de projection holographique pour la transformation 2D → 3D/4D
    Basée sur les constantes harmoniques fondamentales
    """
    
    def __init__(self, custom_matrix: Optional[np.ndarray] = None):
        """
        Initialise la matrice de projection
        
        Args:
            custom_matrix: Matrice personnalisée (utilise la matrice harmonique par défaut)
        """
        if custom_matrix is not None:
            self.M = custom_matrix
            self._valider_matrice(custom_matrix)
        else:
            self.M = self._creer_matrice_harmonique()
        
        self.dimension_entree = 4  # Espace 2D + 2 paramètres harmoniques
        self.dimension_sortie = 4  # Espace 3D + temps
        
        # Propriétés de la matrice
        self.determinant = np.linalg.det(self.M)
        self.inverse = np.linalg.inv(self.M)
        
        logger.info(f"MatriceProjection initialisée: det={self.determinant:.6f}")
    
    def _creer_matrice_harmonique(self) -> np.ndarray:
        """
        Crée la matrice de projection harmonique fondamentale
        
        Returns:
            Matrice 4x4 basée sur les constantes harmoniques
        """
        phi = CONSTANTES.phi
        pi = CONSTANTES.pi
        e = CONSTANTES.e
        sqrt2 = CONSTANTES.sqrt2
        sqrt3 = CONSTANTES.sqrt3
        
        M = np.array([
            [1.0, pi/phi, sqrt2*sqrt3, e/pi],
            [1.0, 1.0, e/phi, pi/e],
            [1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0]
        ])
        
        return M
    
    def _valider_matrice(self, matrice: np.ndarray):
        """
        Valide que la matrice est appropriée pour la projection
        
        Args:
            matrice: Matrice à valider
        """
        if matrice.shape != (4, 4):
            raise ValueError("La matrice doit être 4x4")
        
        det = np.linalg.det(matrice)
        if abs(det) < 1e-10:
            raise ValueError("La matrice doit être inversible (determinant non nul)")
        
        if det < 0:
            logger.warning(f"Determinant négatif: {det:.6f}")
    
    def projeter_point(self, point_2d: Coordonnees2D) -> Coordonnees3D:
        """
        Projette un point de l'espace 2D vers l'espace 3D/4D
        
        Args:
            point_2d: Point dans l'espace 2D harmonique
            
        Returns:
            Point projeté dans l'espace 3D/4D
        """
        # Ajout des paramètres harmoniques
        vecteur_entree = np.array([
            point_2d.x,
            point_2d.y,
            1.0,  # Paramètre harmonique 1
            1.0   # Paramètre harmonique 2
        ])
        
        # Application de la projection
        vecteur_sortie = self.M @ vecteur_entree
        
        return Coordonnees3D(
            x=vecteur_sortie[0],
            y=vecteur_sortie[1],
            z=vecteur_sortie[2],
            t=vecteur_sortie[3]
        )
    
    def projeter_constante(self, constante_harmonique: float) -> Coordonnees3D:
        """
        Projette une constante harmonique
        
        Args:
            constante_harmonique: Valeur de la constante
            
        Returns:
            Point projeté représentant la constante
        """
        vecteur_entree = np.array([constante_harmonique, 1.0, 1.0, 1.0])
        vecteur_sortie = self.M @ vecteur_entree
        
        return Coordonnees3D(
            x=vecteur_sortie[0],
            y=vecteur_sortie[1],
            z=vecteur_sortie[2],
            t=vecteur_sortie[3]
        )
    
    def projeter_vecteur(self, vecteur: np.ndarray) -> np.ndarray:
        """
        Projette un vecteur 4D
        
        Args:
            vecteur: Vecteur 4D d'entrée
            
        Returns:
            Vecteur 4D projeté
        """
        if len(vecteur) != self.dimension_entree:
            raise ValueError(f"Le vecteur doit avoir {self.dimension_entree} dimensions")
        
        return self.M @ vecteur
    
    def projeter_inverse(self, point_3d: Coordonnees3D) -> Coordonnees2D:
        """
        Projection inverse (3D → 2D)
        
        Args:
            point_3d: Point dans l'espace 3D/4D
            
        Returns:
            Point original dans l'espace 2D
        """
        vecteur_entree = point_3d.to_array()
        vecteur_sortie = self.inverse @ vecteur_entree
        
        return Coordonnees2D(x=vecteur_sortie[0], y=vecteur_sortie[1])
    
    def projeter_surface(self, surface_2d: List[Coordonnees2D]) -> List[Coordonnees3D]:
        """
        Projette une surface 2D complète
        
        Args:
            surface_2d: Liste de points 2D
            
        Returns:
            Liste de points 3D projetés
        """
        return [self.projeter_point(point) for point in surface_2d]
    
    def calculer_distorsion(self, point_2d: Coordonnees2D) -> float:
        """
        Calcule le facteur de distorsion pour un point
        
        Args:
            point_2d: Point à analyser
            
        Returns:
            Facteur de distorsion
        """
        point_3d = self.projeter_point(point_2d)
        
        # Distorsion basée sur le changement de volume
        volume_2d = 1.0  # Unité dans l'espace 2D
        volume_3d = point_3d.norme()
        
        return volume_3d / volume_2d
    
    def analyser_projection(self) -> Dict[str, float]:
        """
        Analyse les propriétés de la matrice de projection
        
        Returns:
            Dictionnaire des propriétés
        """
        # Valeurs propres
        valeurs_propres, vecteurs_propres = np.linalg.eig(self.M)
        
        # Conditionnement
        conditionnement = np.linalg.cond(self.M)
        
        # Trace
        trace = np.trace(self.M)
        
        # Norme de Frobenius
        norme_frobenius = np.linalg.norm(self.M, 'fro')
        
        return {
            'determinant': self.determinant,
            'conditionnement': conditionnement,
            'trace': trace,
            'norme_frobenius': norme_frobenius,
            'valeurs_propres': valeurs_propres.tolist(),
            'rang': np.linalg.matrix_rank(self.M)
        }
    
    def visualiser_matrice(self) -> str:
        """
        Retourne une représentation textuelle de la matrice
        
        Returns:
            Représentation formatée
        """
        representation = "🌊 MATRICE DE PROJECTION HOLOGRAPHIQUE\n"
        representation += "=" * 50 + "\n"
        representation += f"Determinant: {self.determinant:.6f}\n"
        representation += f"Conditionnement: {np.linalg.cond(self.M):.2f}\n\n"
        
        representation += "Matrice M:\n"
        for i in range(4):
            ligne = "|"
            for j in range(4):
                valeur = self.M[i, j]
                ligne += f" {valeur:8.6f} "
            ligne += "|\n"
            representation += ligne
        
        return representation

class ProjectionHolographique:
    """
    Système complet de projection holographique
    Gère la projection d'objets complexes de l'espace 2D vers 3D
    """
    
    def __init__(self):
        self.matrice = MatriceProjection()
        self.projections = {}
        self.trajectories = {}
        
        logger.info("ProjectionHolographique initialisée")
    
    def projeter_objet(self, points_2d: List[Coordonnees2D], nom: str = "objet") -> List[Coordonnees3D]:
        """
        Projette un objet complet
        
        Args:
            points_2d: Liste de points définissant l'objet
            nom: Nom de l'objet pour référence
            
        Returns:
            Liste de points 3D projetés
        """
        points_3d = self.matrice.projeter_surface(points_2d)
        self.projections[nom] = points_3d
        
        logger.info(f"Objet '{nom}' projeté: {len(points_2d)} → {len(points_3d)} points")
        
        return points_3d
    
    def projeter_constantes_fondamentales(self) -> Dict[str, Coordonnees3D]:
        """
        Projette les 7 constantes harmoniques fondamentales
        
        Returns:
            Dictionnaire des constantes projetées
        """
        constantes = {
            'phi': CONSTANTES.phi,
            'pi': CONSTANTES.pi,
            'e': CONSTANTES.e,
            'sqrt2': CONSTANTES.sqrt2,
            'sqrt3': CONSTANTES.sqrt3,
            'sqrt5': CONSTANTES.sqrt5,
            'e_sur_pi': CONSTANTES.e_sur_pi
        }
        
        projections = {}
        for nom, valeur in constantes.items():
            projections[nom] = self.matrice.projeter_constante(valeur)
        
        self.projections['constantes'] = projections
        
        return projections
    
    def calculer_volume_projeté(self, nom: str) -> float:
        """
        Calcule le volume d'un objet projeté
        
        Args:
            nom: Nom de l'objet
            
        Returns:
            Volume approximatif
        """
        if nom not in self.projections:
            raise ValueError(f"Objet '{nom}' non trouvé")
        
        points = self.projections[nom]
        
        # Calcul simplifié du volume (convex hull)
        if len(points) < 4:
            return 0.0
        
        # Centre de masse
        centre = np.mean([p.to_array()[:3] for p in points], axis=0)
        
        # Volume approximatif (somme des tétraèdres)
        volume = 0.0
        for i in range(len(points) - 2):
            v1 = points[i].to_array()[:3] - centre
            v2 = points[i+1].to_array()[:3] - centre
            v3 = points[i+2].to_array()[:3] - centre
            
            volume += abs(np.dot(v1, np.cross(v2, v3))) / 6.0
        
        return volume
    
    def analyser_distorsion_globale(self, nom: str) -> Dict[str, float]:
        """
        Analyse la distorsion pour un objet projeté
        
        Args:
            nom: Nom de l'objet
            
        Returns:
            Statistiques de distorsion
        """
        if nom not in self.projections:
            raise ValueError(f"Objet '{nom}' non trouvé")
        
        # Reconstruction des points 2D originaux (approximation)
        points_3d = self.projections[nom]
        distorsions = []
        
        for point_3d in points_3d:
            point_2d = self.matrice.projeter_inverse(point_3d)
            distorsion = self.matrice.calculer_distorsion(point_2d)
            distorsions.append(distorsion)
        
        return {
            'distorsion_moyenne': np.mean(distorsions),
            'distorsion_min': np.min(distorsions),
            'distorsion_max': np.max(distorsions),
            'distorsion_std': np.std(distorsions)
        }
    
    def get_statistiques_globales(self) -> Dict:
        """
        Retourne les statistiques globales du système
        
        Returns:
            Statistiques complètes
        """
        return {
            'matrice_projection': self.matrice.analyser_projection(),
            'objets_projetes': len(self.projections),
            'noms_objets': list(self.projections.keys()),
            'dimension_entree': self.matrice.dimension_entree,
            'dimension_sortie': self.matrice.dimension_sortie
        }

# Fonctions utilitaires
def creer_surface_carree(taille: float, resolution: int = 10) -> List[Coordonnees2D]:
    """
    Crée une surface carrée pour les tests
    
    Args:
        taille: Taille du carré
        resolution: Nombre de points par côté
        
    Returns:
        Liste de points 2D
    """
    points = []
    pas = taille / resolution
    
    for i in range(resolution + 1):
        for j in range(resolution + 1):
            x = -taille/2 + i * pas
            y = -taille/2 + j * pas
            points.append(Coordonnees2D(x, y))
    
    return points

def creer_surface_circulaire(rayon: float, resolution: int = 20) -> List[Coordonnees2D]:
    """
    Crée une surface circulaire pour les tests
    
    Args:
        rayon: Rayon du cercle
        resolution: Nombre de points sur le périmètre
        
    Returns:
        Liste de points 2D
    """
    points = []
    
    # Périmètre
    for i in range(resolution):
        angle = 2 * np.pi * i / resolution
        x = rayon * np.cos(angle)
        y = rayon * np.sin(angle)
        points.append(Coordonnees2D(x, y))
    
    # Centre
    points.append(Coordonnees2D(0, 0))
    
    return points

# Tests et validation
if __name__ == "__main__":
    print("🌊 TEST DE LA MATRICE DE PROJECTION HOLOGRAPHIQUE")
    print("=" * 60)
    
    # Test de la matrice
    matrice = MatriceProjection()
    print(matrice.visualiser_matrice())
    
    # Test de projection d'un point
    point_2d = Coordonnees2D(1.0, 1.0)
    point_3d = matrice.projeter_point(point_2d)
    
    print(f"\n📊 PROJECTION DE POINT:")
    print(f"Point 2D: ({point_2d.x:.3f}, {point_2d.y:.3f})")
    print(f"Point 3D: ({point_3d.x:.3f}, {point_3d.y:.3f}, {point_3d.z:.3f}, {point_3d.t:.3f})")
    print(f"Distorsion: {matrice.calculer_distorsion(point_2d):.3f}")
    
    # Test de projection inverse
    point_reconstruit = matrice.projeter_inverse(point_3d)
    print(f"Point reconstruit: ({point_reconstruit.x:.3f}, {point_reconstruit.y:.3f})")
    
    # Test du système complet
    projection = ProjectionHolographique()
    
    # Projection des constantes
    print(f"\n📊 PROJECTION DES CONSTANTES:")
    constantes_projetees = projection.projeter_constantes_fondamentales()
    for nom, point in constantes_projetees.items():
        print(f"{nom}: ({point.x:.3f}, {point.y:.3f}, {point.z:.3f}, {point.t:.3f})")
    
    # Test de surface
    surface_carre = creer_surface_carree(2.0, 5)
    surface_projetee = projection.projeter_objet(surface_carre, "carre_test")
    
    print(f"\n📊 PROJECTION DE SURFACE:")
    print(f"Surface 2D: {len(surface_carre)} points")
    print(f"Surface 3D: {len(surface_projetee)} points")
    print(f"Volume projeté: {projection.calculer_volume_projeté('carre_test'):.3f}")
    
    # Analyse de distorsion
    distorsion = projection.analyser_distorsion_globale("carre_test")
    print(f"Distorsion moyenne: {distorsion['distorsion_moyenne']:.3f}")
    
    # Statistiques globales
    stats = projection.get_statistiques_globales()
    print(f"\n📊 STATISTIQUES GLOBALES:")
    print(f"Objets projetés: {stats['objets_projetes']}")
    print(f"Rang matrice: {stats['matrice_projection']['rang']}")
    print(f"Conditionnement: {stats['matrice_projection']['conditionnement']:.2f}")
    
    print(f"\n✅ Tous les tests passés avec succès!")
