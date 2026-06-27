"""
🧬 SIMULATION MÉDICALE HARMONIQUE
Fichier: simulation_medicale_harmonique.py
Auteur: Équipe Harmonique
Date: 28 avril 2026
Description: Application de simulation médicale révolutionnaire basée sur les Hbits
             avec modélisation moléculaire quantique et analyse harmonique
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import math
from collections import defaultdict

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des composants harmoniques
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '02_ARCHITECTURE_QUANTIQUE'))
from hbits_geometriques import HbitGeometrique, RegistreHarmonique, PatternGeometrique
from circuits_harmoniques import BibliothequeCircuits, CircuitHarmonique, TypeCircuit
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '01_FONDEMENTS_MATHÉMATIQUES'))
from constantes_harmoniques import CONSTANTES
from matrice_projection import MatriceProjection

# Types de molécules
class TypeMolecule(Enum):
    PROTEINE = "proteine"
    ADN = "adn"
    ARN = "arn"
    MEDICAMENT = "medicament"
    ENZYME = "enzyme"
    VIRUS = "virus"

# Types d'interactions moléculaires
class TypeInteraction(Enum):
    LIAISON_HYDROGENE = "liaison_hydrogene"
    LIAISON_COVALENTE = "liaison_covalente"
    INTERACTION_VAN_DER_WAALS = "van_der_waals"
    INTERACTION_ELECTROSTATIQUE = "electrostatique"
    INTERACTION_HARMONIQUE = "harmonique"

@dataclass
class Atome:
    """
    Atome avec propriétés quantiques harmoniques
    """
    numero_atomique: int
    symbole: str
    position: np.ndarray
    vitesse: np.ndarray
    masse: float
    charge: float
    energie: float = 0.0
    phase_quantique: float = 0.0
    
    def __post_init__(self):
        """Initialisation des propriétés quantiques"""
        self.phase_quantique = np.random.uniform(0, 2*np.pi)

@dataclass
class Molecule:
    """
    Molécule avec structure harmonique
    """
    nom: str
    type_molecule: TypeMolecule
    atomes: List[Atome]
    liaisons: List[Tuple[int, int]] = field(default_factory=list)
    energie_totale: float = 0.0
    frequence_vibration: float = 0.0
    pattern_harmonique: Optional[PatternGeometrique] = None
    
    def __post_init__(self):
        """Calcul des propriétés moléculaires"""
        self.calculer_proprietes()
    
    def calculer_proprietes(self):
        """Calcule les propriétés moléculaires"""
        try:
            # Calcul du centre de masse
            if self.atomes:
                masses = np.array([atome.masse for atome in self.atomes])
                positions = np.array([atome.position for atome in self.atomes])
                self.centre_masse = np.average(positions, weights=masses, axis=0)
            else:
                self.centre_masse = np.zeros(3)
            
            # Calcul de l'énergie totale (simplifié)
            self.energie_totale = sum(atome.energie for atome in self.atomes)
            
            # Calcul de la fréquence de vibration harmonique
            self.frequence_vibration = self._calculer_frequence_vibration()
            
            # Détermination du pattern harmonique
            self.pattern_harmonique = self._determiner_pattern_harmonique()
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des propriétés moléculaires: {e}")
    
    def _calculer_frequence_vibration(self) -> float:
        """
        Calcule la fréquence de vibration harmonique
        
        Returns:
            Fréquence en THz
        """
        try:
            # Simulation basée sur les constantes harmoniques
            phi = CONSTANTES['phi']
            pi = CONSTANTES['pi']
            
            # Fréquence basée sur le nombre d'atomes et l'énergie
            n_atomes = len(self.atomes)
            energie_normalisee = self.energie_totale / max(n_atomes, 1)
            
            # Formule harmonique pour la fréquence
            frequence = (phi * pi * np.sqrt(energie_normalisee)) / (n_atomes ** 0.5)
            
            return min(frequence, 100.0)  # Limitation à 100 THz
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de fréquence: {e}")
            return 10.0  # Valeur par défaut
    
    def _determiner_pattern_harmonique(self) -> PatternGeometrique:
        """
        Détermine le pattern harmonique de la molécule
        
        Returns:
            Pattern géométrique harmonique
        """
        try:
            # Analyse de la structure moléculaire
            n_atomes = len(self.atomes)
            
            # Calcul de la géométrie
            if n_atomes < 3:
                return PatternGeometrique.CERCLE
            elif n_atomes < 6:
                return PatternGeometrique.SPIRALE
            elif n_atomes < 10:
                return PatternGeometrique.HELICE
            elif len(self.liaisons) > n_atomes * 1.5:
                return PatternGeometrique.TRINITE
            else:
                return PatternGeometrique.MIROIR
                
        except Exception as e:
            logger.error(f"Erreur lors de la détermination du pattern: {e}")
            return PatternGeometrique.CERCLE

@dataclass
class InteractionMoleculaire:
    """
    Interaction entre molécules avec calcul harmonique
    """
    molecule1: Molecule
    molecule2: Molecule
    type_interaction: TypeInteraction
    energie_interaction: float
    distance: float
    angle: float = 0.0
    temps_interaction: float = 0.0
    
    def __post_init__(self):
        """Calcul des propriétés de l'interaction"""
        self.calculer_force_interaction()
    
    def calculer_force_interaction(self):
        """Calcule la force de l'interaction"""
        try:
            phi = CONSTANTES['phi']
            
            # Force basée sur le type d'interaction et la distance
            facteur_type = {
                TypeInteraction.LIAISON_COVALENTE: 10.0,
                TypeInteraction.LIAISON_HYDROGENE: 5.0,
                TypeInteraction.INTERACTION_ELECTROSTATIQUE: 2.0,
                TypeInteraction.INTERACTION_VAN_DER_WAALS: 1.0,
                TypeInteraction.INTERACTION_HARMONIQUE: phi
            }
            
            force_base = facteur_type.get(self.type_interaction, 1.0)
            
            # Décroissance avec la distance
            self.force = force_base * np.exp(-self.distance / phi)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de force: {e}")
            self.force = 0.0

class SimulateurMoleculaireHarmonique:
    """
    Simulateur moléculaire quantique avec harmoniques
    """
    
    def __init__(self, nombre_hbits: int = 16):
        self.nombre_hbits = nombre_hbits
        self.registre_quantique = RegistreHarmonique(nombre_hbits)
        self.matrice_projection = MatriceProjection()
        self.molecules = []
        self.interactions = []
        self.temps_simulation = 0.0
        self.dt = 0.001  # pas de temps en picosecondes
        
        # Paramètres harmoniques
        self.phi = CONSTANTES['phi']
        self.pi = CONSTANTES['pi']
        self.e = CONSTANTES['e']
        
        # État de la simulation
        self.simulation_active = False
        self.thread_simulation = None
        
        logger.info(f"SimulateurMoleculaireHarmonique initialisé avec {nombre_hbits} Hbits")
    
    def ajouter_molecule(self, molecule: Molecule):
        """
        Ajoute une molécule à la simulation
        
        Args:
            molecule: Molécule à ajouter
        """
        try:
            self.molecules.append(molecule)
            
            # Encodage quantique de la molécule
            self._encoder_molecule_quantique(molecule)
            
            logger.info(f"Molécule {molecule.nom} ajoutée à la simulation")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la molécule: {e}")
    
    def _encoder_molecule_quantique(self, molecule: Molecule):
        """
        Encode une molécule dans le registre quantique
        
        Args:
            molecule: Molécule à encoder
        """
        try:
            # Utilisation des Hbits pour encoder les propriétés moléculaires
            n_hbits_disponibles = len(self.registre_quantique.qubits)
            n_hbits_utilises = min(len(molecule.atomes), n_hbits_disponibles)
            
            for i in range(n_hbits_utilises):
                if i < len(molecule.atomes):
                    atome = molecule.atomes[i]
                    
                    # Encodage de la position et de l'énergie
                    hbit = self.registre_quantique.qubits[i]
                    
                    # Normalisation des coordonnées
                    pos_normalisee = atome.position / np.linalg.norm(atome.position + 1e-10)
                    
                    # Encodage dans l'état quantique
                    amplitude_0 = pos_normalisee[0] * np.cos(atome.phase_quantique)
                    amplitude_1 = pos_normalisee[1] * np.sin(atome.phase_quantique)
                    
                    # Normalisation
                    norm = np.sqrt(abs(amplitude_0)**2 + abs(amplitude_1)**2)
                    if norm > 0:
                        hbit.etat.amplitude_0 = amplitude_0 / norm
                        hbit.etat.amplitude_1 = amplitude_1 / norm
                    
                    # Assignment du pattern harmonique
                    if molecule.pattern_harmonique:
                        hbit.pattern = molecule.pattern_harmonique
            
            logger.info(f"Molécule {molecule.nom} encodée dans {n_hbits_utilises} Hbits")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'encodage quantique: {e}")
    
    def calculer_interactions(self):
        """Calcule toutes les interactions moléculaires"""
        try:
            self.interactions = []
            
            for i, mol1 in enumerate(self.molecules):
                for j, mol2 in enumerate(self.molecules[i+1:], i+1):
                    # Calcul de la distance entre centres de masse
                    distance = np.linalg.norm(mol1.centre_masse - mol2.centre_masse)
                    
                    # Seuil d'interaction
                    if distance < 10.0:  # 10 Angstroms
                        # Détermination du type d'interaction
                        type_interaction = self._determiner_type_interaction(mol1, mol2, distance)
                        
                        # Calcul de l'énergie d'interaction
                        energie = self._calculer_energie_interaction(mol1, mol2, distance, type_interaction)
                        
                        # Calcul de l'angle
                        vecteur = mol2.centre_masse - mol1.centre_masse
                        angle = np.arctan2(vecteur[1], vecteur[0])
                        
                        interaction = InteractionMoleculaire(
                            molecule1=mol1,
                            molecule2=mol2,
                            type_interaction=type_interaction,
                            energie_interaction=energie,
                            distance=distance,
                            angle=angle,
                            temps_interaction=self.temps_simulation
                        )
                        
                        self.interactions.append(interaction)
            
            logger.info(f"{len(self.interactions)} interactions calculées")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des interactions: {e}")
    
    def _determiner_type_interaction(self, mol1: Molecule, mol2: Molecule, distance: float) -> TypeInteraction:
        """
        Détermine le type d'interaction entre deux molécules
        
        Args:
            mol1: Première molécule
            mol2: Deuxième molécule
            distance: Distance entre les molécules
            
        Returns:
            Type d'interaction
        """
        try:
            # Règles heuristiques pour déterminer le type d'interaction
            if distance < 1.5:
                return TypeInteraction.LIAISON_COVALENTE
            elif distance < 2.5:
                return TypeInteraction.LIAISON_HYDROGENE
            elif distance < 5.0:
                if mol1.type_molecule == TypeMolecule.PROTEINE and mol2.type_molecule == TypeMolecule.MEDICAMENT:
                    return TypeInteraction.HARMONIQUE
                else:
                    return TypeInteraction.INTERACTION_ELECTROSTATIQUE
            else:
                return TypeInteraction.INTERACTION_VAN_DER_WAALS
                
        except Exception as e:
            logger.error(f"Erreur lors de la détermination du type d'interaction: {e}")
            return TypeInteraction.INTERACTION_VAN_DER_WAALS
    
    def _calculer_energie_interaction(self, mol1: Molecule, mol2: Molecule, 
                                     distance: float, type_interaction: TypeInteraction) -> float:
        """
        Calcule l'énergie d'interaction entre deux molécules
        
        Args:
            mol1: Première molécule
            mol2: Deuxième molécule
            distance: Distance entre les molécules
            type_interaction: Type d'interaction
            
        Returns:
            Énergie d'interaction en kcal/mol
        """
        try:
            # Paramètres pour différents types d'interaction
            parametres = {
                TypeInteraction.LIAISON_COVALENTE: {'profondeur': 100.0, 'longueur': 1.5},
                TypeInteraction.LIAISON_HYDROGENE: {'profondeur': 5.0, 'longueur': 2.0},
                TypeInteraction.INTERACTION_ELECTROSTATIQUE: {'profondeur': 10.0, 'longueur': 3.0},
                TypeInteraction.INTERACTION_VAN_DER_WAALS: {'profondeur': 1.0, 'longueur': 4.0},
                TypeInteraction.INTERACTION_HARMONIQUE: {'profondeur': self.phi * 10, 'longueur': 2.5}
            }
            
            params = parametres.get(type_interaction, {'profondeur': 1.0, 'longueur': 3.0})
            
            # Potentiel de Lennard-Jones modifié
            sigma = params['longueur']
            epsilon = params['profondeur']
            
            # Terme harmonique basé sur les fréquences de vibration
            facteur_harmonique = 1.0 + 0.1 * np.cos(mol1.frequence_vibration - mol2.frequence_vibration)
            
            # Calcul de l'énergie
            r_ratio = sigma / distance
            energie = epsilon * facteur_harmonique * (r_ratio**12 - 2 * r_ratio**6)
            
            return energie
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'énergie: {e}")
            return 0.0
    
    def dynamique_moleculaire(self, pas: int = 100):
        """
        Exécute la dynamique moléculaire
        
        Args:
            pas: Nombre de pas de simulation
        """
        try:
            logger.info(f"Début de la dynamique moléculaire ({pas} pas)")
            
            for step in range(pas):
                # Calcul des forces
                forces = self._calculer_forces()
                
                # Mise à jour des positions et vitesses
                self._mettre_a_jour_positions(forces)
                
                # Mise à jour du registre quantique
                self._mettre_a_jour_registre_quantique()
                
                # Avancement du temps
                self.temps_simulation += self.dt
                
                # Calcul des interactions périodiquement
                if step % 10 == 0:
                    self.calculer_interactions()
            
            logger.info(f"Dynamique moléculaire terminée - Temps: {self.temps_simulation:.3f} ps")
            
        except Exception as e:
            logger.error(f"Erreur lors de la dynamique moléculaire: {e}")
    
    def _calculer_forces(self) -> Dict[int, np.ndarray]:
        """
        Calcule les forces sur chaque atome
        
        Returns:
            Dictionnaire des forces par index d'atome
        """
        try:
            forces = defaultdict(lambda: np.zeros(3))
            
            # Forces des interactions moléculaires
            for interaction in self.interactions:
                force = interaction.force
                direction = (interaction.molecule2.centre_masse - interaction.molecule1.centre_masse)
                direction = direction / np.linalg.norm(direction + 1e-10)
                
                # Application de la force aux atomes des deux molécules
                for atome in interaction.molecule1.atomes:
                    forces[id(atome)] -= force * direction
                for atome in interaction.molecule2.atomes:
                    forces[id(atome)] += force * direction
            
            # Forces de liaison intramoléculaire
            for molecule in self.molecules:
                for i, j in molecule.liaisons:
                    if i < len(molecule.atomes) and j < len(molecule.atomes):
                        atome1 = molecule.atomes[i]
                        atome2 = molecule.atomes[j]
                        
                        # Force de ressort harmonique
                        vecteur = atome2.position - atome1.position
                        distance = np.linalg.norm(vecteur)
                        force_liaison = 100.0 * (distance - 1.5)  # k * (x - x0)
                        
                        direction = vecteur / (distance + 1e-10)
                        force = force_liaison * direction
                        
                        forces[id(atome1)] += force
                        forces[id(atome2)] -= force
            
            return dict(forces)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des forces: {e}")
            return {}
    
    def _mettre_a_jour_positions(self, forces: Dict[int, np.ndarray]):
        """
        Met à jour les positions et vitesses des atomes
        
        Args:
            forces: Forces appliquées aux atomes
        """
        try:
            for molecule in self.molecules:
                for atome in molecule.atomes:
                    force = forces.get(id(atome), np.zeros(3))
                    
                    # Intégration de Verlet
                    acceleration = force / atome.masse
                    atome.vitesse += acceleration * self.dt
                    atome.position += atome.vitesse * self.dt
                    
                    # Mise à jour de la phase quantique
                    atome.phase_quantique += atome.energie * self.dt / self.hbar if hasattr(self, 'hbar') else 0.0
                    atome.phase_quantique = atome.phase_quantique % (2 * np.pi)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des positions: {e}")
    
    def _mettre_a_jour_registre_quantique(self):
        """Met à jour le registre quantique avec les nouvelles positions"""
        try:
            for molecule in self.molecules:
                self._encoder_molecule_quantique(molecule)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du registre: {e}")
    
    def visualiser_simulation(self):
        """Visualise la simulation moléculaire en 3D"""
        try:
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            # Configuration du graphique
            ax.set_xlabel('X (Å)')
            ax.set_ylabel('Y (Å)')
            ax.set_zlabel('Z (Å)')
            ax.set_title(f'🧬 Simulation Moléculaire Harmonique (t={self.temps_simulation:.3f} ps)')
            
            # Couleurs pour différents types de molécules
            couleurs_molecules = {
                TypeMolecule.PROTEINE: 'red',
                TypeMolecule.ADN: 'blue',
                TypeMolecule.ARN: 'green',
                TypeMolecule.MEDICAMENT: 'purple',
                TypeMolecule.ENZYME: 'orange',
                TypeMolecule.VIRUS: 'black'
            }
            
            # Visualisation des molécules
            for molecule in self.molecules:
                couleur = couleurs_molecules.get(molecule.type_molecule, 'gray')
                
                # Positions des atomes
                positions = np.array([atome.position for atome in molecule.atomes])
                
                # Taille basée sur le numéro atomique
                tailles = [atome.numero_atomique * 20 for atome in molecule.atomes]
                
                # Affichage des atomes
                ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2],
                         c=couleur, s=tailles, alpha=0.7, label=molecule.nom)
                
                # Affichage des liaisons
                for i, j in molecule.liaisons:
                    if i < len(molecule.atomes) and j < len(molecule.atomes):
                        pos1 = molecule.atomes[i].position
                        pos2 = molecule.atomes[j].position
                        ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], [pos1[2], pos2[2]],
                                'k-', alpha=0.3, linewidth=1)
            
            # Visualisation des interactions
            for interaction in self.interactions:
                pos1 = interaction.molecule1.centre_masse
                pos2 = interaction.molecule2.centre_masse
                
                # Couleur basée sur le type d'interaction
                couleurs_interactions = {
                    TypeInteraction.LIAISON_COVALENTE: 'red',
                    TypeInteraction.LIAISON_HYDROGENE: 'blue',
                    TypeInteraction.INTERACTION_ELECTROSTATIQUE: 'green',
                    TypeInteraction.INTERACTION_VAN_DER_WAALS: 'gray',
                    TypeInteraction.INTERACTION_HARMONIQUE: 'purple'
                }
                
                couleur = couleurs_interactions.get(interaction.type_interaction, 'gray')
                alpha = min(abs(interaction.energie_interaction) / 50.0, 1.0)
                
                ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], [pos1[2], pos2[2]],
                        '--', c=couleur, alpha=alpha, linewidth=2)
            
            # Légende
            ax.legend(loc='upper right', fontsize=8)
            
            # Limites des axes
            if self.molecules:
                all_positions = np.concatenate([np.array([atome.position for atome in mol.atomes]) 
                                            for mol in self.molecules])
                margin = 5.0
                ax.set_xlim([all_positions[:, 0].min() - margin, all_positions[:, 0].max() + margin])
                ax.set_ylim([all_positions[:, 1].min() - margin, all_positions[:, 1].max() + margin])
                ax.set_zlim([all_positions[:, 2].min() - margin, all_positions[:, 2].max() + margin])
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Erreur lors de la visualisation: {e}")
    
    def analyser_energetique(self) -> Dict[str, float]:
        """
        Analyse énergétique du système
        
        Returns:
            Dictionnaire des énergies
        """
        try:
            energie_cinetique = 0.0
            energie_potentielle = 0.0
            
            # Énergie cinétique
            for molecule in self.molecules:
                for atome in molecule.atomes:
                    energie_cinetique += 0.5 * atome.masse * np.linalg.norm(atome.vitesse)**2
            
            # Énergie potentielle des interactions
            for interaction in self.interactions:
                energie_potentielle += interaction.energie_interaction
            
            # Énergie de liaison
            for molecule in self.molecules:
                for i, j in molecule.liaisons:
                    if i < len(molecule.atomes) and j < len(molecule.atomes):
                        atome1 = molecule.atomes[i]
                        atome2 = molecule.atomes[j]
                        distance = np.linalg.norm(atome2.position - atome1.position)
                        energie_potentielle += 50.0 * (distance - 1.5)**2  # Potentiel harmonique
            
            energie_totale = energie_cinetique + energie_potentielle
            
            return {
                'energie_cinetique': energie_cinetique,
                'energie_potentielle': energie_potentielle,
                'energie_totale': energie_totale,
                'temperature': 2 * energie_cinetique / (3 * len(self.molecules) * 8.314) if self.molecules else 0.0
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse énergétique: {e}")
            return {}
    
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de la simulation
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            total_atomes = sum(len(mol.atomes) for mol in self.molecules)
            total_liaisons = sum(len(mol.liaisons) for mol in self.molecules)
            
            # Analyse énergétique
            energies = self.analyser_energetique()
            
            # Distribution des types de molécules
            types_molecules = defaultdict(int)
            for mol in self.molecules:
                types_molecules[mol.type_molecule.value] += 1
            
            # Distribution des interactions
            types_interactions = defaultdict(int)
            for interaction in self.interactions:
                types_interactions[interaction.type_interaction.value] += 1
            
            return {
                'temps_simulation': self.temps_simulation,
                'nombre_molecules': len(self.molecules),
                'total_atomes': total_atomes,
                'total_liaisons': total_liaisons,
                'total_interactions': len(self.interactions),
                'types_molecules': dict(types_molecules),
                'types_interactions': dict(types_interactions),
                'energies': energies,
                'nombre_hbits': self.nombre_hbits
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention des statistiques: {e}")
            return {'erreur': str(e)}

# Fonctions utilitaires pour créer des molécules exemples
def creer_molecule_eau() -> Molecule:
    """Crée une molécule d'eau H2O"""
    h1 = Atome(1, "H", np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0]), 1.008, 0.0)
    h2 = Atome(1, "H", np.array([0.96, 0.0, 0.0]), np.array([0.0, 0.0, 0.0]), 1.008, 0.0)
    o = Atome(8, "O", np.array([0.48, 0.93, 0.0]), np.array([0.0, 0.0, 0.0]), 15.999, -2.0)
    
    return Molecule(
        nom="Eau",
        type_molecule=TypeMolecule.MEDICAMENT,
        atomes=[h1, h2, o],
        liaisons=[(0, 2), (1, 2)]
    )

def creer_molecule_medicament() -> Molecule:
    """Crée une molécule de médicament simplifiée"""
    # Création d'une molécule simple (benzène)
    atomes = []
    liaisons = []
    
    # 6 atomes de carbone en cycle
    for i in range(6):
        angle = i * np.pi / 3
        x = 1.4 * np.cos(angle)
        y = 1.4 * np.sin(angle)
        z = 0.0
        
        carbone = Atome(6, "C", np.array([x, y, z]), np.array([0.0, 0.0, 0.0]), 12.011, 0.0)
        atomes.append(carbone)
        
        # Liaisons cycliques
        liaisons.append((i, (i + 1) % 6))
    
    return Molecule(
        nom="Benzène",
        type_molecule=TypeMolecule.MEDICAMENT,
        atomes=atomes,
        liaisons=liaisons
    )

def creer_proteine_simplifiee() -> Molecule:
    """Crée une protéine simplifiée"""
    atomes = []
    liaisons = []
    
    # Chaîne polypeptidique simple
    for i in range(10):
        x = i * 1.5
        y = np.sin(i * 0.5) * 2.0
        z = np.cos(i * 0.5) * 2.0
        
        # Atome principal (carbone alpha)
        carbone = Atome(6, "C", np.array([x, y, z]), np.array([0.0, 0.0, 0.0]), 12.011, 0.0)
        atomes.append(carbone)
        
        # Liaison peptidique
        if i > 0:
            liaisons.append((i-1, i))
    
    return Molecule(
        nom="Protéine simplifiée",
        type_molecule=TypeMolecule.PROTEINE,
        atomes=atomes,
        liaisons=liaisons
    )

# Point d'entrée principal pour les tests
if __name__ == "__main__":
    try:
        logger.info("🧬 Démonstration de la simulation médicale harmonique")
        
        # Initialisation du simulateur
        simulateur = SimulateurMoleculaireHarmonique(nombre_hbits=16)
        
        # Création des molécules exemples
        logger.info("\n--- Création des molécules ---")
        
        eau = creer_molecule_eau()
        medicament = creer_molecule_medicament()
        proteine = creer_proteine_simplifiee()
        
        # Ajout des molécules à la simulation
        simulateur.ajouter_molecule(eau)
        simulateur.ajouter_molecule(medicament)
        simulateur.ajouter_molecule(proteine)
        
        # Positionnement des molécules
        medicament.atomes[0].position += np.array([5.0, 0.0, 0.0])
        for atome in medicament.atomes[1:]:
            atome.position += np.array([5.0, 0.0, 0.0])
        
        proteine.atomes[0].position += np.array([0.0, 5.0, 0.0])
        for atome in proteine.atomes[1:]:
            atome.position += np.array([0.0, 5.0, 0.0])
        
        # Calcul des interactions initiales
        logger.info("\n--- Calcul des interactions ---")
        simulateur.calculer_interactions()
        
        # Analyse énergétique initiale
        logger.info("\n--- Analyse énergétique initiale ---")
        energies_initiales = simulateur.analyser_energetique()
        for cle, valeur in energies_initiales.items():
            print(f"  {cle}: {valeur:.4f}")
        
        # Dynamique moléculaire
        logger.info("\n--- Dynamique moléculaire ---")
        simulateur.dynamique_moleculaire(pas=50)
        
        # Analyse énergétique finale
        logger.info("\n--- Analyse énergétique finale ---")
        energies_finales = simulateur.analyser_energetique()
        for cle, valeur in energies_finales.items():
            print(f"  {cle}: {valeur:.4f}")
        
        # Statistiques finales
        logger.info("\n--- Statistiques de simulation ---")
        stats = simulateur.obtenir_statistiques()
        for cle, valeur in stats.items():
            if cle != 'types_molecules' and cle != 'types_interactions':
                print(f"  {cle}: {valeur}")
        
        print(f"  Types de molécules: {stats.get('types_molecules', {})}")
        print(f"  Types d'interactions: {stats.get('types_interactions', {})}")
        
        # Visualisation
        logger.info("\n--- Visualisation de la simulation ---")
        simulateur.visualiser_simulation()
        
        logger.info("🧬 Simulation médicale harmonique terminée avec succès")
        
    except KeyboardInterrupt:
        logger.info("Arrêt de la simulation")
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
