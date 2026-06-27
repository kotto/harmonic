#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moteur de Langage Harmonique — Reformulation par Règles
=========================================================
Post-processeur de texte qui transforme des faits bruts
en phrases naturelles et grammaticalement correctes.

Principes :
1. Élision des redondances ("X est X est Y" → "X est Y")
2. Ordre canonique : [Sujet] [Verbe] [Valeur] [Contexte]
3. Contractions ("de le" → "du", élision)
4. Nettoyage de ponctuation
5. Aucun template — transformation directe du texte

Usage :
    moteur = MoteurLangage()
    reponse = moteur.reformuler(faits)
    → "La constante de Planck vaut 6,626×10⁻³⁴ J·s. 
       Elle fut introduite par Max Planck en 1900."

Auteur : KOTTO Alain — 19 Juin 2026
"""

import re, random

# ================================
# RÈGLES DE TRANSFORMATION
# ================================

# Patterns de redondance sujet-verbe
# "X est X est Y" → "X est Y"
# "X vaut X vaut Y" → "X vaut Y"  
# "X a pour valeur X a pour valeur Y" → "X a pour valeur Y"
REDONDANCE_VERBE = [
    (r'\b(est)\s+\1\b', r'\1'),      # "est est" → "est"
    (r'\b(vaut)\s+\1\b', r'\1'),     # "vaut vaut" → "vaut"
]

# Patterns de répétition de sujet
# "La constante de Planck est La constante de Planck h = 6.626..." 
# → "La constante de Planck vaut h = 6.626..."
# On détecte que le sujet est répété après le verbe
REPETITION_SUJET = re.compile(
    r'^(.+?)\s+(est|vaut|a pour valeur|désigne|correspond à)\s+\1\s+(.+)',
    re.IGNORECASE
)

# Pattern pour détecter et nettoyer les artefacts Q/R
QR_ARTEFACT = re.compile(
    r'(?:question|q)\s*:\s*(.+?)\s*(?:reponse|r[eé]ponse|r)\s*:\s*(.+)',
    re.IGNORECASE
)

# Préfixes à supprimer au début d'une phrase
PREFIXES_A_SUPPRIMER = [
    r'^reponse\s*:\s*', r'^réponse\s*:\s*',
    r'^information\s+sur\s+', r'^information\s*:\s*',
    r'^info\s*:\s*', r'^question\s*:\s*',
]

# Verbes à normaliser
NORMALISATION_VERBE = {
    'est': 'est',
    'vaut': 'vaut', 
    'vaut exactement': 'vaut',
    'a pour valeur': 'a pour valeur',
    'est égal à': 'vaut',
    'est égale à': 'vaut',
    'désigne': 'désigne',
    'correspond à': 'correspond à',
    'consiste en': 'consiste en',
    'fonctionne de la manière suivante :': 'fonctionne ainsi :',
}

# Mots de liaison pour connecter deux faits
CONNECTEURS = [
    "Par ailleurs, {}", "De plus, {}", "En outre, {}",
    "{}",  # Parfois, pas de connecteur
]

# ================================
# MOTEUR DE LANGAGE
# ================================

class MoteurLangage:
    """
    Transforme des faits bruts en langage naturel.
    """
    
    def reformuler(self, faits):
        """
        Reformule une liste de faits en une réponse fluide.
        
        Args:
            faits: liste de strings (faits bruts du moteur TF-IDF)
        
        Returns:
            Une phrase ou un petit paragraphe en langage naturel
        """
        if not faits:
            return "Je ne dispose pas d'assez d'informations pour répondre à cette question."
        
        # Étape 1 : Nettoyer chaque fait
        faits_nets = []
        for f in faits:
            net = self._nettoyer_fait(f)
            if net and len(net) > 10 and net not in faits_nets:
                faits_nets.append(net)
        
        if not faits_nets:
            return "Aucune information exploitable trouvée."
        
        # Étape 2 : Reformuler le fait principal
        principal = self._reformuler_phrase(faits_nets[0])
        # Forcer un point final
        principal = principal.rstrip('.') + '.'
        
        # Étape 3 : Ajouter UN seul fait secondaire (max 2 faits au total)
        if len(faits_nets) > 1:
            for f in faits_nets[1:3]:
                reformule = self._reformuler_phrase(f)
                reformule = reformule.rstrip('.') + '.'
                # Éviter les doublons et les faits contradictoires
                if reformule and reformule[:40] not in principal[:len(principal)//2]:
                    # Filtrer les connaissances manifestement erronées
                    if not self._est_manifestement_faux(reformule):
                        connecteur = random.choice(CONNECTEURS)
                        if connecteur != "{}":
                            reformule = reformule[0].lower() + reformule[1:]
                        principal = principal + ' ' + connecteur.format(reformule)
                        break  # Un seul fait secondaire suffit
        
        # Étape 4 : Post-traitement grammatical
        principal = self._post_traitement(principal)
        
        return principal
    
    def _nettoyer_fait(self, texte):
        """Nettoie un fait brut."""
        texte = texte.strip()
        
        # 1. Supprimer les artefacts Q/R
        m = QR_ARTEFACT.search(texte)
        if m:
            reponse = m.group(2).strip()
            texte = reponse
        
        # 2. Supprimer les préfixes
        for pattern in PREFIXES_A_SUPPRIMER:
            texte = re.sub(pattern, '', texte, flags=re.IGNORECASE)
        
        # 3. Garder la première phrase (la plus informative)
        # Mais pas couper sur un point de notation scientifique (6.626)
        parts = re.split(r'(?<!\d)\.(?!\d)', texte)
        if parts and len(parts[0].strip()) > 10:
            texte = parts[0].strip()
        
        return texte.strip()
    
    def _reformuler_phrase(self, texte):
        """
        Reformule une phrase en supprimant les redondances
        et en appliquant l'ordre canonique.
        """
        texte = texte.strip()
        if not texte:
            return texte
        
        # 1. Détecter et corriger la répétition du sujet
        # "X est X Y" → "X est Y"
        m = REPETITION_SUJET.match(texte)
        if m:
            sujet = m.group(1).strip()
            verbe = m.group(2).strip().lower()
            complement = m.group(3).strip()
            
            # Normaliser le verbe
            verbe = NORMALISATION_VERBE.get(verbe, verbe)
            
            # Nettoyer le complément
            complement = self._nettoyer_complement(complement, sujet)
            
            return f"{sujet} {verbe} {complement}"
        
        # 2. Correction simple des doublons de verbe
        for pattern, remplacement in REDONDANCE_VERBE:
            texte = re.sub(pattern, remplacement, texte, flags=re.IGNORECASE)
        
        # 3. Capitaliser la première lettre
        if texte and texte[0].islower():
            texte = texte[0].upper() + texte[1:]
        
        return texte
    
    def _nettoyer_complement(self, complement, sujet):
        """
        Nettoie le complément après le verbe.
        - Supprime les redondances avec le sujet
        - Tronque si trop long
        - Ajoute un point final
        """
        # Supprimer la répétition du sujet dans le complément
        sujet_lower = sujet.lower()
        comp_lower = complement.lower()
        
        if comp_lower.startswith(sujet_lower):
            complement = complement[len(sujet):].strip()
            # Nettoyer les artefacts restants (deux-points, etc.)
            complement = re.sub(r'^[:\s]+', '', complement)
        
        # Tronquer à 200 caractères
        if len(complement) > 200:
            # Couper au dernier point ou espace avant 200
            coupe = complement[:200].rstrip()
            dernier_point = coupe.rfind('.')
            dernier_espace = coupe.rfind(' ')
            if dernier_point > 150:
                complement = coupe[:dernier_point+1]
            elif dernier_espace > 150:
                complement = coupe[:dernier_espace] + '...'
            else:
                complement = coupe + '...'
        
        # S'assurer que ça finit par un point
        complement = complement.strip()
        if complement and complement[-1] not in '.!?':
            complement += '.'
        
        return complement
    
    def _est_manifestement_faux(self, texte):
        """Filtre les connaissances manifestement erronées du corpus."""
        faux_patterns = [
            r'(einstein|newton|planck|darwin|curie|pasteur|tesla|marconi|bell|edison)\s+a\s+(découvert|inventé)\s+le\s+(vaccin contre la rage|courant alternatif|tableau périodique|rayonnement hawking|lois du mouvement|structure de l\'ADN|évolution par sélection naturelle|radioactivité|relativité|gravitation universelle)',
            r'(einstein|newton|darwin|tesla)\s+a\s+(découvert|inventé)\s+(le|la)\s+(vaccin|tableau|lois|évolution|radioactivité|relativité|gravitation)',
        ]
        for pattern in faux_patterns:
            if re.search(pattern, texte, re.IGNORECASE):
                # Vérifier que ce n'est pas la VRAIE découverte
                vraies_paires = [
                    ('pasteur', 'vaccin contre la rage'),
                    ('einstein', 'relativité'),
                    ('newton', 'gravitation'),
                    ('darwin', 'évolution'),
                    ('curie', 'radioactivité'),
                    ('mendeleïev', 'tableau périodique'),
                    ('tesla', 'courant alternatif'),
                    ('marconi', 'radio'),
                    ('bell', 'téléphone'),
                    ('edison', 'ampoule'),
                ]
                for personne, decouverte in vraies_paires:
                    if personne in texte.lower() and decouverte in texte.lower():
                        return False  # C'est la vraie découverte
                return True  # C'est une fausse attribution
        return False
    
    def _post_traitement(self, texte):
        """Applique les corrections grammaticales finales."""
        # Contractions
        texte = re.sub(r'\b(le|la)\s+([aeéèêhiouâîôûAEÉÈÊHIOUÂÎÔÛ])', r"l'\2", texte)
        texte = texte.replace('de le ', 'du ')
        texte = texte.replace('de les ', 'des ')
        texte = texte.replace('à le ', 'au ')
        texte = texte.replace('à les ', 'aux ')
        texte = texte.replace('ce est ', "c'est ")
        texte = texte.replace('que il ', "qu'il ")
        texte = texte.replace('que elle ', "qu'elle ")
        texte = texte.replace('si il ', "s'il ")
        texte = texte.replace('ne est ', "n'est ")
        texte = texte.replace('je ai ', "j'ai ")
        
        # Nettoyage des espaces
        texte = re.sub(r'\s{2,}', ' ', texte)
        texte = re.sub(r'\s+([.,;:!?])', r'\1', texte)
        texte = re.sub(r'([.,;:!?])([^\s\d])', r'\1 \2', texte)
        
        # Pas de double ponctuation
        texte = texte.replace('..', '.')
        texte = texte.replace('.,', '.')
        
        # Majuscule en début
        texte = texte.strip()
        if texte and texte[0].islower():
            texte = texte[0].upper() + texte[1:]
        
        # Point final
        if texte and texte[-1] not in '.!?':
            texte += '.'
        
        return texte


# ================================
# TEST
# ================================
def demo():
    print("=" * 70)
    print("MOTEUR DE LANGAGE — Reformulation par Règles")
    print("=" * 70)
    print()
    
    moteur = MoteurLangage()
    
    # Cas de test : faits bruts typiques de l'IA harmonique
    tests = [
        # Cas 1 : Redondance sujet
        (["La constante de Planck h = 6.626×10⁻³⁴ J·s.",
          "Max Planck a introduit le quantum d'action en 1900."],
         "constante de Planck"),
        
        # Cas 2 : Q/R artefact
        (["Question: Quelle est la vitesse de la lumiere en km/s ?  Reponse: 300000",
          "La vitesse de la lumière dans le vide est exactement c = 299 792 458 m/s."],
         "vitesse de la lumière"),
        
        # Cas 3 : Fait avec répétition interne
        (["Einstein a publié la relativité restreinte en 1905 (E=mc²) et la relativité générale en 1915.",
          "La relativité générale décrit la gravité comme courbure de l'espace-temps."],
         "relativité"),
        
        # Cas 4 : Big Bang
        (["Le Big Bang s'est produit il y a 13.8 milliards d'années.",
          "La théorie du Big Bang a été proposée par Georges Lemaître en 1927."],
         "Big Bang"),
        
        # Cas 5 : Photosynthèse
        (["La photosynthèse : 6 CO₂ + 6 H₂O + lumière → C₆H₁₂O₆ + 6 O₂.",
          "Les plantes convertissent l'énergie solaire en énergie chimique."],
         "photosynthèse"),
        
        # Cas 6 : Masse de l'électron
        (["La masse de l'electron est 9.109 * 10^-31 kg.",
          "L'électron a une charge électrique négative."],
         "électron"),
        
        # Cas 7 : Double répétition
        (["La constante de Planck h = 6.626×10⁻³⁴ J·s.",
          "La constante de Planck h = 6.626 * 10^-34 Joules seconde.",
          "Max Planck a introduit le quantum d'action h en 1900."],
         "constante de Planck"),
    ]
    
    for faits, sujet in tests:
        print(f"  [{sujet}]")
        print(f"    Faits bruts :")
        for f in faits:
            print(f"      • {f[:100]}...")
        reponse = moteur.reformuler(faits)
        print(f"    Reformulé  : {reponse[:200]}")
        print()
    
    print("=" * 70)
    print("✅ TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    demo()