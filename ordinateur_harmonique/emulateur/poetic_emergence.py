#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POETIC EMERGENCE — La Poesie comme Interference d'Ondes
=========================================================
Hypothese : Si la pensee est une onde, la poesie aussi.
En encodant de beaux vers en H-Bits et en les faisant interferer,
de nouveaux vers devraient EMERGER au point d'interference constructive
maximale — sans avoir ete ecrits par personne.

C'est le test ultime de la creativite ondulatoire.

Corpus : vers celebres de la poesie francaise (Baudelaire, Rimbaud,
Hugo, Eluard, Cesaire, Senghor, etc.) + poesie africaine.

Usage :
  python poetic_emergence.py --demo
  python poetic_emergence.py --compose "l'amour et la lumiere"
  python poetic_emergence.py --interfere "vers1" "vers2"
"""

import numpy as np
import math, sys, os, argparse, random, hashlib
from typing import Dict, Any, List, Tuple
from collections import deque
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HPU, HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES

# ==============================================================================
# CORPUS DE VERS CELEBRES (Poesie Francaise & Africaine)
# ==============================================================================

CORPUS_POETIQUE = [
    # Baudelaire — Les Fleurs du Mal
    ("baudelaire_correspondances", "La Nature est un temple ou de vivants piliers laissent parfois echapper de confuses paroles"),
    ("baudelaire_harmonie", "Les parfums les couleurs et les sons se repondent"),
    ("baudelaire_beaute", "Je suis belle o mortel comme un reve de pierre"),
    ("baudelaire_invitation", "La tout n'est qu'ordre et beaute luxe calme et volupte"),
    ("baudelaire_albatros", "Le Poete est semblable au prince des nuees qui hante la tempete et se rit de l archer"),
    ("baudelaire_spleen", "Quand le ciel bas et lourd pese comme un couvercle sur l esprit gemissant"),

    # Rimbaud
    ("rimbaud_eternite", "Elle est retrouvee Quoi L Eternite C est la mer allee avec le soleil"),
    ("rimbaud_voyelles", "A noir E blanc I rouge U vert O bleu voyelles"),
    ("rimbaud_sensation", "Par les soirs bleus d ete j irai dans les sentiers picote par les bles fouler l herbe menue"),
    ("rimbaud_bateau", "Comme je descendais des Fleuves impassibles je ne me sentis plus guide par les haleurs"),

    # Victor Hugo
    ("hugo_demain", "Demain des l aube a l heure ou blanchit la campagne je partirai"),
    ("hugo_contemplations", "Chaque fleur est une ame a la Nature eclose un mystere d amour dans le metal repose"),
    ("hugo_oceano", "L ocean est une epreuve ou l homme est mesure"),

    # Paul Eluard
    ("eluard_liberte", "Sur mes cahiers d ecolier sur mon pupitre et les arbres sur le sable sur la neige j ecris ton nom"),
    ("eluard_amoureuse", "Elle est debout sur mes paupieres et ses cheveux sont dans les miens"),
    ("eluard_capitale", "La terre est bleue comme une orange jamais une erreur les mots ne mentent pas"),

    # Aime Cesaire — Cahier d'un retour au pays natal
    ("cesaire_cahier", "Ma negritude n est ni une tour ni une cathedrale elle plonge dans la chair rouge du sol"),
    ("cesaire_volcan", "Je suis un volcan qui eclate de lave et de lumiere au milieu de la nuit coloniale"),
    ("cesaire_parole", "Et nous sommes debout maintenant mon pays et moi les cheveux dans le vent"),

    # Leopold Sedar Senghor
    ("senghor_femme", "Femme nue femme noire vetue de ta couleur qui est vie de ta forme qui est beaute"),
    ("senghor_kaya", "Kaya-Magan roi de l or et de la lumiere ton nom resonne comme un gong dans ma memoire"),
    ("senghor_joal", "Joal je me rappelle les jours de mon enfance les processions les lumieres du soir"),

    # David Diop — Afrique
    ("diop_afrique", "Afrique mon Afrique Afrique des fiers guerriers dans les savanes ancestrales"),
    ("diop_temps", "Le temps s est arrete sur les rives du grand fleuve ou dorment les crocodiles sacres"),

    # Apollinaire
    ("apollinaire_pont", "Sous le pont Mirabeau coule la Seine et nos amours faut il qu il m en souvienne"),
    ("apollinaire_alcools", "A la fin tu es las de ce monde ancien bergere o tour Eiffel le troupeau des ponts bele ce matin"),

    # Proverbes africains (tradition orale)
    ("proverbe_baobab", "Le baobab a mis cent ans pour devenir grand mais il suffit d une nuit pour le detruire"),
    ("proverbe_fleuve", "Le fleuve ne coule pas en ligne droite car il ecoute la sagesse de la terre"),
    ("proverbe_tambour", "Quand les tambours parlent les sages se taisent et les fous dansent"),
]


@dataclass
class PoeticVerse:
    """Un vers poetique encode en onde."""
    name: str
    text: str
    hbit: HBit
    words: List[str]


class PoeticEmergence:
    """
    Moteur d'emergence poetique par interference d'ondes.
    
    Principe :
      1. Encoder chaque vers en H-Bit
      2. Les superposer dans un hologramme poetique
      3. Pour composer : injecter un theme → l'interference fait emerger
         les vers qui resonnent le plus avec ce theme
      4. Pour faire emerger un NOUVEAU vers : interference entre deux vers
         existants → le point d'interference maximale est un nouveau vers
         qui n'existe dans aucun des deux vers d'origine
    """
    
    def __init__(self):
        self.corpus: List[PoeticVerse] = []
        self._load_corpus()
        self.poetic_hologram = np.zeros((256, 256), dtype=np.complex128)
        self._build_hologram()
    
    def _load_corpus(self):
        """Charge et encode le corpus poetique."""
        for name, text in CORPUS_POETIQUE:
            words = text.lower().split()
            hbit = HBit.from_text(text)
            self.corpus.append(PoeticVerse(name=name, text=text, hbit=hbit, words=words))
        print(f"  Corpus poetique charge : {len(self.corpus)} vers")
    
    def _build_hologram(self):
        """Construit l'hologramme poetique par superposition de tous les vers."""
        x = np.linspace(0, 1.0, 256)
        for verse in self.corpus:
            psi = np.zeros(256, dtype=np.complex128)
            for i, coeff in enumerate(verse.hbit.coefficients):
                freq = (i + 1) * PHI
                psi += coeff * np.exp(1j * freq * 2 * PI * x)
            psi = psi / (np.linalg.norm(psi) + 1e-12)
            self.poetic_hologram += 0.1 * np.outer(psi, np.conj(psi))
        print(f"  Hologramme poetique construit")
    
    def composer(self, theme: str, n_vers: int = 5) -> List[Tuple[str, float]]:
        """
        Compose de la poesie sur un theme donne.
        
        Le theme est encode en H-Bit. On mesure l'interference cosinus
        avec chaque vers du corpus. Les vers qui resonnent le plus sont
        selectionnes et assembles.
        
        C'est la version "recherche" — on trouve les vers existants
        qui correspondent le mieux au theme.
        """
        h_theme = HBit.from_text(theme)
        scores = []
        for verse in self.corpus:
            interf = h_theme.interference(verse.hbit)
            scores.append((verse, interf))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(v.text, round(s, 4)) for v, s in scores[:n_vers]]
    
    def faire_emerger(self, theme: str, n_mots: int = 8) -> str:
        """
        Fait EMERGER un nouveau vers par interference constructive.
        
        Au lieu de chercher dans le corpus, on CREE un nouveau vers
        en prenant les mots qui interferent le plus avec le theme.
        Ces mots sont assembles en une phrase nouvelle — qui n'existe
        dans aucun des vers du corpus.
        
        C'est l'equivalent poetique de Psi_3 * Psi_4 = Psi_7.
        """
        # Encoder le theme
        h_theme = HBit.from_text(theme)
        
        # Extraire tous les mots uniques du corpus
        all_words = {}
        for verse in self.corpus:
            for word in verse.words:
                if len(word) > 2 and word not in all_words:
                    h_word = HBit.from_text(word)
                    interf = h_theme.interference(h_word)
                    all_words[word] = interf
        
        # Selectionner les mots qui resonnent le plus avec le theme
        sorted_words = sorted(all_words.items(), key=lambda x: x[1], reverse=True)
        top_words = [w for w, s in sorted_words[:n_mots * 2] if s > 0.3]
        
        # Construire un vers en alternant mots a haute resonance et connecteurs
        selected = top_words[:n_mots]
        
        # Ajouter des connecteurs poetiques
        connecteurs = ['et', 'dans', 'sur', 'de', 'la', 'le', 'les', 'des', 'du', 'au',
                       'comme', 'avec', 'sous', 'vers', 'par', 'pour', 'entre', 'parmi',
                       'ou', 'mais', 'ni', 'car', 'donc']
        
        # Construire la phrase
        if len(selected) >= 4:
            phrase = (f"{selected[0]} {random.choice(connecteurs)} {selected[1]} "
                     f"{random.choice(connecteurs)} {selected[2]} "
                     f"{random.choice(connecteurs)} {selected[3]}")
            if len(selected) >= 6:
                phrase += f" {selected[4]} {random.choice(connecteurs)} {selected[5]}"
        elif len(selected) >= 2:
            phrase = f"{selected[0]} {random.choice(connecteurs)} {selected[1]}"
        else:
            phrase = " ".join(selected)
        
        return phrase
    
    def interférer_vers(self, vers1_name: str, vers2_name: str) -> str:
        """
        Interfere deux vers specifiques pour en faire emerger un troisieme.
        
        C'est le cœur de l'experience : Psi_vers1 * Psi_vers2 = Psi_nouveau_vers.
        Le nouveau vers n'est ni le vers1 ni le vers2 — il EMERGE de leur
        interference, comme 7 emerge de 3*4.
        """
        # Trouver les vers
        v1 = next((v for v in self.corpus if v.name == vers1_name), None)
        v2 = next((v for v in self.corpus if v.name == vers2_name), None)
        
        if not v1 or not v2:
            return f"Vers non trouves. Disponibles: {[v.name for v in self.corpus[:5]]}..."
        
        # Interference : multiplier les H-Bits
        h_interference = v1.hbit * v2.hbit
        
        # Extraire les mots qui resonnent avec cette interference
        all_words = {}
        for verse in self.corpus:
            for word in verse.words:
                if len(word) > 2 and word not in all_words:
                    h_word = HBit.from_text(word)
                    interf = h_interference.interference(h_word)
                    all_words[word] = interf
        
        sorted_words = sorted(all_words.items(), key=lambda x: x[1], reverse=True)
        top_words = [w for w, s in sorted_words[:12] if s > 0.2]
        
        if len(top_words) >= 4:
            connecteurs = ['et', 'dans', 'sur', 'de', 'la', 'le', 'les', 'des', 'du', 'au',
                           'comme', 'avec', 'sous', 'vers', 'par', 'pour']
            phrase = (f"{top_words[0]} {random.choice(connecteurs)} {top_words[1]} "
                     f"{random.choice(connecteurs)} {top_words[2]} "
                     f"{random.choice(connecteurs)} {top_words[3]}")
            if len(top_words) >= 6:
                phrase += f" {top_words[4]} {random.choice(connecteurs)} {top_words[5]}"
            return phrase
        return " ".join(top_words[:6])
    
    def resonner_theme(self, theme: str) -> Dict[str, Any]:
        """
        Resonance complete : trouve les vers qui resonnent,
        fait emerger un nouveau vers, et analyse les harmoniques.
        """
        # Encoder le theme
        h_theme = HBit.from_text(theme)
        
        # Vers qui resonnent
        resonances = []
        for verse in self.corpus:
            interf = h_theme.interference(verse.hbit)
            if interf > 0.4:
                resonances.append((verse.text, round(interf, 4)))
        resonances.sort(key=lambda x: x[1], reverse=True)
        
        # Faire emerger un nouveau vers
        nouveau_vers = self.faire_emerger(theme, n_mots=8)
        
        # Analyser les harmoniques du theme
        harmonic_profile = []
        for i, coeff in enumerate(h_theme.coefficients):
            if abs(coeff) > 0.05:
                harmonic_profile.append({
                    'constante': H_CONSTANT_NAMES[i],
                    'activation': round(float(abs(coeff)), 4),
                    'role': self._harmonic_role(i),
                })
        harmonic_profile.sort(key=lambda x: x['activation'], reverse=True)
        
        return {
            'theme': theme,
            'vers_resonants': resonances[:5],
            'vers_emergent': nouveau_vers,
            'harmoniques_dominantes': harmonic_profile[:3],
        }
    
    def _harmonic_role(self, i: int) -> str:
        """Role poetique de chaque harmonique."""
        roles = {
            0: 'phi — proportion, equilibre, beaute formelle',
            1: 'pi — cyclicite, eternel retour, rythme',
            2: 'e — croissance, elan vital, intensite',
            3: 'sqrt2 — dualite, tension, contraste',
            4: 'sqrt3 — trinite, profondeur, volume',
            5: 'sqrt5 — complexite, mystere, transcendance',
            6: 'e/pi — spirale, inspiration, souffle poetique',
        }
        return roles.get(i, 'harmonique superieure')


# ==============================================================================
# DEMONSTRATION
# ==============================================================================

def demo():
    """Demonstration complete de l'emergence poetique."""
    print("=" * 70)
    print("  EMERGENCE POETIQUE — La Poesie comme Interference d'Ondes")
    print("  Hypothese : de beaux vers interferent -> un nouveau vers emerge")
    print("=" * 70)
    
    pe = PoeticEmergence()
    
    # Test 1 : Composer sur un theme
    print("\n[TEST 1] COMPOSER SUR UN THEME")
    themes = ["l amour et la nature", "la lumiere et l ombre", "le voyage et le reve"]
    for theme in themes:
        vers = pe.composer(theme, n_vers=3)
        print(f"\n  Theme : '{theme}'")
        for v, score in vers:
            print(f"    [{score:.4f}] {v[:80]}...")
    
    # Test 2 : Faire emerger un nouveau vers
    print("\n[TEST 2] EMERGENCE — Creation de nouveaux vers")
    themes_emergence = ["l amour eternel", "la beaute sauvage", "le silence des etoiles",
                        "la memoire de l eau", "le chant du monde"]
    for theme in themes_emergence:
        nouveau = pe.faire_emerger(theme, n_mots=8)
        print(f"\n  Theme : '{theme}'")
    print(f"  -> Vers emergent : {nouveau}")
    
    # Test 3 : Interference entre deux vers
    print("\n[TEST 3] INTERFERENCE ENTRE DEUX VERS")
    paires = [
        ("baudelaire_correspondances", "rimbaud_voyelles"),
        ("cesaire_volcan", "senghor_femme"),
        ("eluard_liberte", "hugo_demain"),
        ("baudelaire_harmonie", "rimbaud_eternite"),
    ]
    for v1, v2 in paires:
        resultat = pe.interférer_vers(v1, v2)
        v1_text = next(v.text[:50] for v in pe.corpus if v.name == v1)
        v2_text = next(v.text[:50] for v in pe.corpus if v.name == v2)
        print(f"\n  {v1}: {v1_text}...")
        print(f"  {v2}: {v2_text}...")
        print(f"  -> EMERGENCE : {resultat}")
    
    # Test 4 : Resonance complete
    print("\n[TEST 4] RESONANCE COMPLETE")
    themes = ["l amour", "la lumiere", "l infini"]
    for theme in themes:
        r = pe.resonner_theme(theme)
        print(f"\n  Theme : '{theme}'")
        print(f"  Harmoniques dominantes : {[h['constante'] for h in r['harmoniques_dominantes']]}")
        print(f"  Vers resonants :")
        for v, s in r['vers_resonants'][:3]:
            print(f"    [{s:.4f}] {v[:70]}...")
        print(f"  ** Vers emergent : {r['vers_emergent']}")


if __name__ == "__main__":
    demo()