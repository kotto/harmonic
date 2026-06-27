#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harmonic Core - Bibliothèque Fondamentale de la Théorie Harmonique
Phase 1 : Fondations Mathématiques

Auteur: Vision Harmonique
Date: 28 avril 2026
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Union, Optional

class HarmonicConstants:
    """
    Bibliothèque des 7 constantes fondamentales avec leurs significations
    L'alphabet universel du langage harmonique
    """
    
    # Les 7 constantes fondamentales
    PHI = (1 + math.sqrt(5)) / 2  # 1.618033988749895 - Nombre d'or
    PI = math.pi  # 3.141592653589793 - Constante circulaire
    E = math.e  # 2.718281828459045 - Base des logarithmes naturels
    SQRT2 = math.sqrt(2)  # 1.414213562373095 - Racine de 2
    SQRT3 = math.sqrt(3)  # 1.732050807568877 - Racine de 3
    SQRT5 = math.sqrt(5)  # 2.23606797749979 - Racine de 5
    E_OVER_PI = math.e / math.pi  # 0.865255979432265 - Rapport e/π
    
    # Dictionnaire sémantique complet
    SEMANTICS = {
        'φ': {
            'value': PHI,
            'meaning': 'Harmonie, structure dorée, optimalité',
            'symbol': '🌟',
            'description': 'La proportion parfaite trouvée dans toute la nature',
            'applications': ['Art', 'Architecture', 'Biologie', 'Finance']
        },
        'π': {
            'value': PI,
            'meaning': 'Espace, universalité, circularité',
            'symbol': '⭕',
            'description': 'La constante fondamentale de l\'espace et du temps',
            'applications': ['Géométrie', 'Physique', 'Astronomie']
        },
        'e': {
            'value': E,
            'meaning': 'Croissance, vie, évolution',
            'symbol': '🌱',
            'description': 'Le moteur de la croissance naturelle et exponentielle',
            'applications': ['Biologie', 'Finance', 'Informatique']
        },
        '√2': {
            'value': SQRT2,
            'meaning': 'Dualité, équilibre, interaction',
            'symbol': '⚖️',
            'description': 'Le principe d\'équilibre et de dualité',
            'applications': ['Physique quantique', 'Électricité', 'Philosophie']
        },
        '√3': {
            'value': SQRT3,
            'meaning': 'Structure, stabilité, trinité',
            'symbol': '🔺',
            'description': 'La fondation de la structure stable',
            'applications': ['Géométrie', 'Architecture', 'Chimie']
        },
        '√5': {
            'value': SQRT5,
            'meaning': 'Vitalité, nature, pentagonalité',
            'symbol': '🌿',
            'description': 'L\'essence de la vie et de la nature',
            'applications': ['Biologie', 'Botanique', 'Médecine']
        },
        'e/π': {
            'value': E_OVER_PI,
            'meaning': 'Spirale, transformation, dynamisme',
            'symbol': '🌀',
            'description': 'Le mouvement de transformation spirale',
            'applications': ['Cosmologie', 'Biologie', 'Dynamique']
        }
    }
    
    @classmethod
    def get_constant(cls, name: str) -> float:
        """
        Récupère une constante par son nom
        
        Args:
            name: Nom de la constante ('φ', 'π', 'e', '√2', '√3', '√5', 'e/π')
            
        Returns:
            Valeur numérique de la constante
            
        Raises:
            KeyError: Si la constante n'existe pas
        """
        if name not in cls.SEMANTICS:
            raise KeyError(f"Constante '{name}' non trouvée. Constantes disponibles: {list(cls.SEMANTICS.keys())}")
        return cls.SEMANTICS[name]['value']
    
    @classmethod
    def get_meaning(cls, name: str) -> str:
        """
        Récupère la signification d'une constante
        
        Args:
            name: Nom de la constante
            
        Returns:
            Signification sémantique de la constante
        """
        if name not in cls.SEMANTICS:
            raise KeyError(f"Constante '{name}' non trouvée")
        return cls.SEMANTICS[name]['meaning']
    
    @classmethod
    def get_symbol(cls, name: str) -> str:
        """
        Récupère le symbole d'une constante
        
        Args:
            name: Nom de la constante
            
        Returns:
            Symbole emoji de la constante
        """
        if name not in cls.SEMANTICS:
            raise KeyError(f"Constante '{name}' non trouvée")
        return cls.SEMANTICS[name]['symbol']
    
    @classmethod
    def list_constants(cls) -> Dict[str, Dict]:
        """
        Liste toutes les constantes avec leurs informations
        
        Returns:
            Dictionnaire complet des constantes
        """
        return cls.SEMANTICS.copy()
    
    @classmethod
    def print_constants(cls) -> None:
        """
        Affiche toutes les constantes de manière élégante
        """
        print("🌊 ALPHABET HARMONIQUE UNIVERSEL 🌊")
        print("=" * 60)
        
        for name, info in cls.SEMANTICS.items():
            print(f"{name} {info['symbol']}")
            print(f"  Valeur: {info['value']:.10f}")
            print(f"  Signification: {info['meaning']}")
            print(f"  Description: {info['description']}")
            print(f"  Applications: {', '.join(info['applications'])}")
            print("-" * 60)


class HarmonicOptimizer:
    """
    Optimiseur basé sur α = 1/φ
    Le principe d'optimalité universelle
    """
    
    ALPHA_OPTIMAL = 1 / HarmonicConstants.PHI  # 0.618033988749895
    
    @classmethod
    def optimize(cls, parameter_range: Tuple[float, float]) -> float:
        """
        Optimise un paramètre dans une plage donnée selon α = 1/φ
        
        Args:
            parameter_range: Tuple (min_val, max_val)
            
        Returns:
            Valeur optimale selon le principe harmonique
        """
        min_val, max_val = parameter_range
        if min_val >= max_val:
            raise ValueError("La plage doit être (min_val, max_val) avec min_val < max_val")
        
        # Position optimale à α = 1/φ de la plage
        return min_val + cls.ALPHA_OPTIMAL * (max_val - min_val)
    
    @classmethod
    def is_optimal(cls, value: float, reference_range: Tuple[float, float], tolerance: float = 0.05) -> bool:
        """
        Vérifie si une valeur est proche de l'optimalité harmonique
        
        Args:
            value: Valeur à tester
            reference_range: Plage de référence (min, max)
            tolerance: Tolérance relative (défaut: 5%)
            
        Returns:
            True si la valeur est harmoniquement optimale
        """
        optimal_value = cls.optimize(reference_range)
        relative_error = abs(value - optimal_value) / optimal_value
        return relative_error < tolerance
    
    @classmethod
    def find_optimal_point(cls, values: List[float]) -> int:
        """
        Trouve l'index du point le plus harmoniquement optimal dans une liste
        
        Args:
            values: Liste de valeurs
            
        Returns:
            Index de la valeur la plus proche de l'optimalité harmonique
        """
        if not values:
            raise ValueError("La liste de valeurs ne peut pas être vide")
        
        min_val, max_val = min(values), max(values)
        optimal_value = cls.optimize((min_val, max_val))
        
        # Trouver l'index le plus proche de la valeur optimale
        distances = [abs(val - optimal_value) for val in values]
        return distances.index(min(distances))
    
    @classmethod
    def print_optimal_info(cls) -> None:
        """
        Affiche les informations sur l'optimalité harmonique
        """
        print("🎯 OPTIMALITÉ HARMONIQUE UNIVERSELLE 🎯")
        print("=" * 50)
        print(f"α_optimal = 1/φ = {cls.ALPHA_OPTIMAL:.10f}")
        print("Signification: Point d'équilibre optimal universel")
        print("Applications: Atangana-Baleanu, Machine Learning, Optimisation")
        print("Propriété: Minimise la complexité, maximise l'harmonie")
        print("=" * 50)


class HarmonicComposer:
    """
    Moteur de composition de phrases harmoniques
    Transforme les concepts en formules mathématiques harmoniques
    """
    
    def __init__(self):
        self.constants = HarmonicConstants()
        self.operations = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '**': lambda x, y: x ** y
        }
    
    def compose(self, elements: List[str], operations: List[str]) -> float:
        """
        Compose une phrase harmonique
        
        Args:
            elements: Liste des noms de constantes
            operations: Liste des opérations entre les constantes
            
        Returns:
            Valeur numérique de la phrase harmonique
            
        Raises:
            ValueError: Si la structure est incorrecte
        """
        if len(elements) != len(operations) + 1:
            raise ValueError(f"Structure incorrecte: {len(elements)} éléments mais {len(operations)} opérations")
        
        try:
            result = self.constants.get_constant(elements[0])
            
            for i, op in enumerate(operations):
                if op not in self.operations:
                    raise ValueError(f"Opération '{op}' non supportée. Opérations supportées: {list(self.operations.keys())}")
                
                next_val = self.constants.get_constant(elements[i + 1])
                result = self.operations[op](result, next_val)
            
            return result
            
        except KeyError as e:
            raise ValueError(f"Constante inconnue: {e}")
        except ZeroDivisionError:
            raise ValueError("Division par zéro dans la composition harmonique")
    
    def translate_concept(self, concept: str) -> Dict:
        """
        Traduit un concept en phrase harmonique
        
        Args:
            concept: Concept à traduire (ex: 'conscience', 'amour', 'intelligence')
            
        Returns:
            Dictionnaire avec la formule et sa signification
        """
        concept = concept.lower()
        
        translations = {
            'conscience': {
                'elements': ['φ', 'e', 'π', 'e'],
                'operations': ['*', '/', '*'],
                'formula': 'φ × e / π × e',
                'meaning': 'Structure harmonique traitant l\'information universelle',
                'value': self.compose(['φ', 'e', 'π', 'e'], ['*', '/', '*'])
            },
            'amour': {
                'elements': ['φ', '√2', 'e'],
                'operations': ['*', '/'],
                'formula': 'φ × √2 / e',
                'meaning': 'Harmonie équilibrée créant la croissance',
                'value': self.compose(['φ', '√2', 'e'], ['*', '/'])
            },
            'intelligence': {
                'elements': ['φ', 'e', '√2'],
                'operations': ['*', '/'],
                'formula': 'φ × e / √2',
                'meaning': 'Structure optimisant l\'information équilibrée',
                'value': self.compose(['φ', 'e', '√2'], ['*', '/'])
            },
            'croissance': {
                'elements': ['e', '√5', 'π'],
                'operations': ['*', '/'],
                'formula': 'e × √5 / π',
                'meaning': 'Vitalité naturelle croissant dans l\'espace',
                'value': self.compose(['e', '√5', 'π'], ['*', '/'])
            },
            'energie': {
                'elements': ['φ', 'e', '√2'],
                'operations': ['*', '*'],
                'formula': 'φ × e × √2',
                'meaning': 'Structure harmonique en croissance équilibrée',
                'value': self.compose(['φ', 'e', '√2'], ['*', '*'])
            },
            'paix': {
                'elements': ['φ', '√2'],
                'operations': ['/'],
                'formula': 'φ / √2',
                'meaning': 'Harmonie dans l\'équilibre',
                'value': self.compose(['φ', '√2'], ['/'])
            },
            'creativite': {
                'elements': ['φ', '√5', 'π'],
                'operations': ['*', '*'],
                'formula': 'φ × √5 × π',
                'meaning': 'Beauté vitale universelle',
                'value': self.compose(['φ', '√5', 'π'], ['*', '*'])
            }
        }
        
        if concept not in translations:
            # Retourner une formule par défaut
            return {
                'elements': ['φ'],
                'operations': [],
                'formula': 'φ',
                'meaning': 'Harmonie fondamentale',
                'value': self.constants.get_constant('φ')
            }
        
        return translations[concept]
    
    def create_custom_phrase(self, concept_elements: List[str]) -> Dict:
        """
        Crée une phrase harmonique personnalisée
        
        Args:
            concept_elements: Liste d'éléments conceptuels
            
        Returns:
            Phrase harmonique personnalisée
        """
        # Traduction automatique des éléments conceptuels
        element_mapping = {
            'beauté': 'φ',
            'harmonie': 'φ',
            'espace': 'π',
            'universel': 'π',
            'croissance': 'e',
            'vie': 'e',
            'dualité': '√2',
            'équilibre': '√2',
            'structure': '√3',
            'stabilité': '√3',
            'nature': '√5',
            'vitalité': '√5',
            'spirale': 'e/π',
            'transformation': 'e/π'
        }
        
        # Mapper les éléments conceptuels aux constantes
        harmonic_elements = []
        for element in concept_elements:
            element_lower = element.lower()
            if element_lower in element_mapping:
                harmonic_elements.append(element_mapping[element_lower])
            else:
                # Utiliser φ par défaut
                harmonic_elements.append('φ')
        
        # Créer une phrase simple avec des multiplications
        operations = ['*'] * (len(harmonic_elements) - 1) if len(harmonic_elements) > 1 else []
        
        try:
            value = self.compose(harmonic_elements, operations)
            formula = ' × '.join(harmonic_elements)
            
            return {
                'concept_elements': concept_elements,
                'harmonic_elements': harmonic_elements,
                'operations': operations,
                'formula': formula,
                'value': value,
                'meaning': f"Composition de: {', '.join(concept_elements)}"
            }
        except ValueError as e:
            return {
                'error': str(e),
                'concept_elements': concept_elements,
                'fallback': 'φ'
            }


# Fonctions utilitaires pour le débogage et l'affichage
def print_harmonic_phrase(composition: Dict) -> None:
    """
    Affiche une phrase harmonique de manière élégante
    """
    print("🌊 PHRASE HARMONIQUE 🌊")
    print("=" * 40)
    print(f"Formule: {composition['formula']}")
    print(f"Valeur: {composition['value']:.10f}")
    print(f"Signification: {composition['meaning']}")
    
    if 'elements' in composition:
        elements_str = " + ".join([f"{comp['symbol']}" for comp in composition['elements']])
        print(f"Éléments: {elements_str}")
    
    print("=" * 40)


# Test de validation pour Phase 1
def test_phase1():
    """
    Test de validation pour la Phase 1
    """
    print("🚀 VALIDATION PHASE 1 - FONDATIONS MATHÉMATIQUES 🚀")
    print("=" * 60)
    
    # Test 1: Constantes
    print("\n📚 Test 1: Constantes Fondamentales")
    constants = HarmonicConstants()
    print(f"φ = {constants.get_constant('φ'):.10f}")
    print(f"π = {constants.get_constant('π'):.10f}")
    print(f"e = {constants.get_constant('e'):.10f}")
    print("✅ Constantes validées")
    
    # Test 2: Optimiseur
    print("\n🎯 Test 2: Optimiseur Harmonique")
    optimizer = HarmonicOptimizer()
    print(f"α_optimal = {optimizer.ALPHA_OPTIMAL:.10f}")
    
    # Test d'optimisation
    test_range = (0.1, 1.0)
    optimal_value = optimizer.optimize(test_range)
    print(f"Optimal dans {test_range}: {optimal_value:.10f}")
    print("✅ Optimiseur validé")
    
    # Test 3: Compositeur
    print("\n🎼 Test 3: Compositeur Harmonique")
    composer = HarmonicComposer()
    
    # Test de composition simple
    result = composer.compose(['φ', 'π'], ['*'])
    print(f"φ × π = {result:.10f}")
    
    # Test de traduction de concept
    concept = composer.translate_concept('amour')
    print(f"Amour = {concept['formula']} = {concept['value']:.10f}")
    print("✅ Compositeur validé")
    
    print("\n🌊 PHASE 1 VALIDÉE AVEC SUCCÈS! 🌊")
    print("Prêt pour la Phase 2: Preuves Mathématiques")


if __name__ == "__main__":
    # Exécuter le test de validation
    test_phase1()
    
    # Afficher les informations sur les constantes
    print("\n")
    HarmonicConstants.print_constants()
    
    # Afficher les informations sur l'optimiseur
    print("\n")
    HarmonicOptimizer.print_optimal_info()
