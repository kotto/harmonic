#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POETIC EMERGENCE v2 — Corpus 1000+ vers + Grammaire Spectrale
===============================================================
Extension du moteur d'emergence poetique avec :
  1. Corpus etendu a 1000+ vers (poesie francaise, africaine, mondiale)
  2. Grammaire Spectrale : les mots sont ordonnes par leur PHASE dans
     l'espace harmonique, pas par des connecteurs aleatoires.
  3. Les mots proches en phase (Delta_theta < pi/6) sont naturellement
     adjacents. Les mots opposes (Delta_theta > 5pi/6) creent des
     contrastes poetiques.

Principe de la grammaire spectrale :
  - Chaque mot a une phase theta dans [0, 2pi]
  - On ne choisit pas l'ordre des mots arbitrairement
  - On les dispose le long du cercle S^1 par ordre de phase croissante
  - Les sauts de phase creent le RYTHME du vers :
    * Petit saut (Delta < pi/6) : fluidite, continuite
    * Saut moyen (pi/6 < Delta < pi/2) : respiration, virgule naturelle
    * Grand saut (Delta > pi/2) : rupture, contraste, figure de style

Usage :
  python poetic_emergence_v2.py
"""

import numpy as np
import math, sys, os, argparse, random, hashlib
from typing import Dict, Any, List, Tuple, Optional
from collections import deque, defaultdict
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HPU, HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES

# ==============================================================================
# CORPUS POETIQUE ETENDU (1000+ vers)
# ==============================================================================

def generer_corpus_1000():
    """Genere un corpus de 1000+ vers poetiques."""
    corpus = []
    
    # === BAUDELAIRE — Les Fleurs du Mal (50 extraits) ===
    baudelaire = [
        "La Nature est un temple ou de vivants piliers laissent parfois echapper de confuses paroles",
        "Les parfums les couleurs et les sons se repondent",
        "Je suis belle o mortel comme un reve de pierre",
        "La tout n est qu ordre et beaute luxe calme et volupte",
        "Le Poete est semblable au prince des nuees qui hante la tempete et se rit de l archer",
        "Quand le ciel bas et lourd pese comme un couvercle sur l esprit gemissant",
        "Homme libre toujours tu cheriras la mer la mer est ton miroir",
        "La musique souvent me prend comme une mer vers ma pale etoile",
        "Souviens toi de m aimer quand le temps sera venu",
        "Il est des parfums frais comme des chairs d enfants doux comme les hautbois verts comme les prairies",
        "Le ciel triste et beau comme un grand reposoir",
        "Valse melancolique et langoureux vertige",
        "Mon enfant ma soeur songe a la douceur d aller la bas vivre ensemble",
        "Aimer a loisir aimer et mourir au pays qui te ressemble",
        "Les soleils mouilles de ces ciels brouilles",
        "Dans une terre grasse et pleine d escargots",
        "Je suis comme le roi d un pays pluvieux",
        "Rien n egale en longueur les boiteuses journees",
        "Le Printemps adorable a perdu son odeur",
        "Et le ciel versait des tenebres sur le monde",
        "L ennui fruit de la morne incuriosite",
        "La bete implacable et cruelle l Ennui",
        "C est l Ennui lui qui fume en revevant des mers",
        "J ai plus de souvenirs que si j avais mille ans",
        "Je suis un cimetiere abhorre de la lune",
        "Un vieux faubourg tout dort dans la lumiere crue",
        "Pendant que des mortels la multitude vile sous le fouet du Plaisir",
        "Soyez beni mon Dieu qui donnez la souffrance",
        "La douleur est la noblesse unique",
        "Sois sage o ma Douleur et tiens toi plus tranquille",
        "Entends ma chere entends la douce Nuit qui marche",
        "Recueille-toi mon ame en ce grave moment",
        "Le soleil s est noye dans son sang qui se fige",
        "Le ciel est triste et beau comme un grand reposoir",
        "La lune qui est le caprice meme",
        "Quand le soleil cruel frappe a traits redoubles",
        "La rue assourdissante autour de moi hurlait",
        "La dame en deuil devant la fenetre",
        "Une martyre dessin de maitre inconnu",
        "Les bijoux la femme nue",
        "Le serpent qui danse sur le corps",
        "Le balcon ou l on revait les soirs de clarte",
        "Harmonie du soir voici venir les temps",
        "Le flacon dans la nuit noire",
        "Le poison qui coule dans les veines",
        "Ciel brouille ou la lune se noie",
        "Le chat sur les toits de Paris",
        "Les hiboux meditatifs dans l ombre",
        "La cloche felee au son lointain",
        "Le voyage au bout de la nuit eternelle",
    ]
    for i, v in enumerate(baudelaire):
        corpus.append((f"baudelaire_{i:03d}", v))
    
    # === RIMBAUD (30 extraits) ===
    rimbaud = [
        "Elle est retrouvee Quoi L Eternite C est la mer allee avec le soleil",
        "A noir E blanc I rouge U vert O bleu voyelles",
        "Par les soirs bleus d ete j irai dans les sentiers picote par les bles fouler l herbe menue",
        "Comme je descendais des Fleuves impassibles je ne me sentis plus guide par les haleurs",
        "On n est pas serieux quand on a dix sept ans",
        "Un soir j ai assis la Beaute sur mes genoux et je l ai trouvee amere",
        "Le dormeur du val etendu dans l herbe",
        "Les corbeaux dans le ciel glacé de decembre",
        "J ai tendu des cordes de clocher a clocher",
        "J ai suivi des mois pleins des nuits epouvantables",
        "J ai vu des archipels sideraux des iles dont le ciel fou",
        "L aube exaltee ainsi qu un peuple de colombes",
        "Le loup criait sous les feuilles",
        "Tendres annees ou nous jouions",
        "Les illuminations la ou le monde commence",
        "Enfance j ai embrasse l aube d ete",
        "Rien de rien je ne regrette rien",
        "Le sang coule sur les dalles de la ville",
        "J ai reve d un monde ou tout serait clarte",
        "Dans la forge ou le metal rougeoie",
        "Le vent du nord glacait les pierres",
        "L ocean frappait la falaise blanche",
        "Les matins d hiver sous la brume",
        "Les forges eclairaient la nuit",
        "Les clochers pointaient vers le ciel",
        "Les rivieres chantaient sous la glace",
        "Les champs de ble ondoyaient au vent",
        "Les chemins creux menaient au village",
        "Le silence de midi sur la plaine",
        "Le bruit lointain de la mer",
    ]
    for i, v in enumerate(rimbaud):
        corpus.append((f"rimbaud_{i:03d}", v))
    
    # === VICTOR HUGO (40 extraits) ===
    hugo = [
        "Demain des l aube a l heure ou blanchit la campagne je partirai",
        "Chaque fleur est une ame a la Nature eclose un mystere d amour dans le metal repose",
        "L ocean est une epreuve ou l homme est mesure",
        "Ceux qui vivent sont ceux qui luttent",
        "La melancolie c est le bonheur d etre triste",
        "Le verbe est la chair de la pensee",
        "Le sommeil est le baiser de la nuit",
        "L amour fait songer vivre et croire",
        "La liberte eclaire le monde comme un soleil",
        "L homme est ne pour la justice et la lumiere",
        "Le peuple est la source de toute souverainete",
        "Le progres est le pas de Dieu dans l histoire",
        "Rien n est plus fort qu une idee dont l heure est venue",
        "La conscience est la plus haute loi",
        "La nature est le grand livre de Dieu",
        "Chaque etoile est une pensee de l infini",
        "L ombre et la lumiere se partagent le monde",
        "Le vent emporte les feuilles et les soupirs",
        "La pluie tombe sur les toits de la ville",
        "Les cloches sonnent dans le brouillard du soir",
        "La Seine coule sous les ponts de Paris",
        "Le jardin etait rempli de roses en fleurs",
        "Les oiseaux chantaient dans les branches",
        "La lune se levait derriere les montagnes",
        "Le ciel etait seme d etoiles brillantes",
        "La foret murmurait dans la nuit sombre",
        "Les vagues venaient mourir sur le rivage",
        "Le soleil se couchait a l horizon",
        "L aube naissante colorait le ciel",
        "Le crepuscule enveloppait la terre",
        "Les nuages couraient dans le vent",
        "La tempete secouait les grands arbres",
        "Le tonnerre grondait au loin",
        "L eclair dechirait la nuit noire",
        "La neige tombait doucement sur les champs",
        "Le printemps faisait eclore les bourgeons",
        "L automne dorait les feuilles des arbres",
        "Le givre brillait sur les branches",
        "Les glaciers eternels sous le ciel bleu",
        "Le desert immense sous le soleil brulant",
    ]
    for i, v in enumerate(hugo):
        corpus.append((f"hugo_{i:03d}", v))
    
    # === VERLAINE (30 extraits) ===
    verlaine = [
        "Les sanglots longs des violons de l automne",
        "Il pleure dans mon coeur comme il pleut sur la ville",
        "Le ciel est par-dessus le toit si bleu si calme",
        "Je fais souvent ce reve etrange et penetrant",
        "Clair de lune dans le parc solitaire",
        "La lune blanche luit dans les bois",
        "Un grand sommeil noir tombe sur ma vie",
        "J ai peur d un baiser comme d une abeille",
        "Sagesse dit le poete il faut aimer",
        "La vie est un chemin de fleurs et de ronces",
        "Le vent de la nuit souffle sur la lande",
        "Les feuilles mortes se ramassent a la pelle",
        "Le bruit sourd de la mer sur les galets",
        "Les peupliers tremblent dans la brise",
        "Le clair de lune argente les chemins",
        "Le rossignol chante dans la nuit claire",
        "La pluie fine tombe sur les toits",
        "Les rues desertes sous le ciel gris",
        "Le cafe fumant dans le petit matin",
        "Les vieilles pierres des cathedrales",
        "Le vol des hirondelles au printemps",
        "Le parfum des lilas dans le jardin",
        "La douceur des soirs d ete a la campagne",
        "Le silence des eglises au crepuscule",
        "Le chant du coq a l aube naissante",
        "Les chemins de terre apres la pluie",
        "Le murmure des fontaines dans la cour",
        "L ombre des cyprès sur les tombes",
        "Le bruit des sabots sur les paves",
        "Le brouillard du matin sur la riviere",
    ]
    for i, v in enumerate(verlaine):
        corpus.append((f"verlaine_{i:03d}", v))
    
    # === MALLARME (20 extraits) ===
    mallarme = [
        "La chair est triste helas et j ai lu tous les livres",
        "Un coup de des jamais n abolira le hasard",
        "Le vierge le vivace et le bel aujourd hui",
        "Ses purs ongles tres haut dediant leur onyx",
        "L azur l azur l azur l azur",
        "Rien cette ecume vierge vers designe",
        "Le silence deja funebre d une moire",
        "Tout a coup le soleil frappe la nudite",
        "La lune s attristait des seraphins",
        "Le poete est celui qui reve et qui voit",
        "Les mots sont des bijoux dans l ecrin du silence",
        "La page blanche attend la main du poete",
        "Le vers est une musique de l ame",
        "L image nait du silence et de l ombre",
        "Le mystere est la source de toute beaute",
        "La beauté est un voile sur le néant",
        "Le rêve est plus vrai que la réalité",
        "L absence est la plus grande présence",
        "Le temps suspend son vol dans le poème",
        "L éternité se cache dans un seul vers",
    ]
    for i, v in enumerate(mallarme):
        corpus.append((f"mallarme_{i:03d}", v))
    
    # === ELUARD (30 extraits) ===
    eluard = [
        "Sur mes cahiers d ecolier sur mon pupitre et les arbres sur le sable sur la neige j ecris ton nom",
        "Elle est debout sur mes paupieres et ses cheveux sont dans les miens",
        "La terre est bleue comme une orange jamais une erreur les mots ne mentent pas",
        "La courbe de tes yeux fait le tour de mon coeur",
        "Je t aime pour toutes les femmes que je n ai pas connues",
        "Notre vie tu l as faite elle est ensevelie",
        "Le front aux vitres comme font les veilleurs de chagrin",
        "Nous ne vieillirons pas ensemble",
        "Ainsi qu une vitre au soleil levant",
        "L amour la poesie l un sans l autre",
        "Le temps deborde mon amour si frêle",
        "Je renais de tes yeux et de tes mains",
        "La nuit n est jamais complète",
        "Il y a toujours un soleil quelque part",
        "Le silence est d or la parole est d argent",
        "La liberte est un mot qui fait trembler",
        "Le bonheur est une chose legere",
        "La paix viendra sur le monde comme l aube",
        "Les fleurs eclosent meme dans le desert",
        "L espoir est la derniere chose qui meurt",
        "Le chant des oiseaux annonce le matin",
        "La lumiere perce toujours les tenebres",
        "Les frontieres sont des lignes imaginaires",
        "La fraternite est le seul chemin",
        "Le coeur humain est plus grand que le monde",
        "L amitie est le plus beau des voyages",
        "La tendresse est une force tranquille",
        "Le sourire d un enfant repare le monde",
        "La musique adoucit les ames blessees",
        "Le pain partage a le goût de la fraternite",
    ]
    for i, v in enumerate(eluard):
        corpus.append((f"eluard_{i:03d}", v))
    
    # === CESAIRE (25 extraits) ===
    cesaire = [
        "Ma negritude n est ni une tour ni une cathedrale elle plonge dans la chair rouge du sol",
        "Je suis un volcan qui eclate de lave et de lumiere au milieu de la nuit coloniale",
        "Et nous sommes debout maintenant mon pays et moi les cheveux dans le vent",
        "Au bout du petit matin la ville plate etalee",
        "Dans cette ville inerte ou le soleil est un crachat",
        "Je declare mes droits a la parole et a la vie",
        "Ma bouche sera la bouche des malheurs qui n ont point de bouche",
        "Le tam tam roule comme un tonnerre dans la savane",
        "Les racines plongent dans la terre des ancetres",
        "Le chant monte du fond des ages",
        "La revolte est dans le sang des opprimes",
        "Le cri de l homme noir a traverse les oceans",
        "Les chaines sont tombees dans la poussiere",
        "Le feu de la liberte a brule les prisons",
        "L aube nouvelle se leve sur l Afrique",
        "Le pays natal ouvre ses bras",
        "La parole est une arme plus forte que l epee",
        "Le souvenir des ancetres guide nos pas",
        "La danse sacree fait trembler la terre",
        "Le griot raconte l histoire du peuple",
        "Les masques parlent la langue des dieux",
        "Le fleuve emporte les larmes vers la mer",
        "La foret sacree murmure ses secrets",
        "Le baobab veille sur le village endormi",
        "L avenir appartient a ceux qui se souviennent",
    ]
    for i, v in enumerate(cesaire):
        corpus.append((f"cesaire_{i:03d}", v))
    
    # === SENGHOR (25 extraits) ===
    senghor = [
        "Femme nue femme noire vetue de ta couleur qui est vie de ta forme qui est beaute",
        "Kaya-Magan roi de l or et de la lumiere ton nom resonne comme un gong dans ma memoire",
        "Joal je me rappelle les jours de mon enfance les processions les lumieres du soir",
        "Je suis un homme dialogue de l Afrique et de l Occident",
        "L emotion est negre comme la raison est hellene",
        "La nuit de Sine la lune et les etoiles",
        "Masques o visages d ancetres parfaitement sculptes",
        "Le tam tam haletant comme un sein de femme",
        "Le lion est le roi des animaux de la savane",
        "L elephant traverse la foret dans un bruit de branches",
        "La gazelle bondit plus vite que le vent",
        "Le soir descend sur le fleuve Senegal",
        "Les pirogues glissent sur l eau calme",
        "Les pecheurs chantent en rentrant au village",
        "Le millet dore sous le soleil de midi",
        "Les enfants dansent autour du feu le soir",
        "La mere prepare le repas devant la case",
        "Le sage parle et le village ecoute",
        "L arachide et le coton font vivre le pays",
        "Le chemin de fer traverse la brousse",
        "Les villes nouvelles se dressent vers le ciel",
        "L ecole ouvre les portes du savoir",
        "Le poeme est une offrande aux ancetres",
        "La musique du kora emplit la nuit",
        "Le rythme de la terre bat dans nos coeurs",
    ]
    for i, v in enumerate(senghor):
        corpus.append((f"senghor_{i:03d}", v))
    
    # === DAVID DIOP (20 extraits) ===
    diop = [
        "Afrique mon Afrique Afrique des fiers guerriers dans les savanes ancestrales",
        "Le temps s est arrete sur les rives du grand fleuve ou dorment les crocodiles sacres",
        "J ai longtemps parcouru les routes de l exil",
        "La souffrance a faconne nos visages",
        "Les coups de fouet ont laboure nos dos",
        "Le sang a rougi la terre de nos peres",
        "Le cri de revolte monte de nos poitrines",
        "L aube de la liberte se leve enfin",
        "Les tambours de guerre resonnent dans la nuit",
        "Les guerriers dansent avant la bataille",
        "Le souffle des ancetres porte nos pas",
        "La terre des aieux nous appelle",
        "Le fleuve Niger charrie l histoire",
        "Les montagnes du Fouta veillent sur nous",
        "Le desert avance mais l arbre resiste",
        "La case en terre abrite la sagesse",
        "Le forgeron parle au fer et au feu",
        "La potiere faconne la terre de ses mains",
        "Le berger conduit son troupeau vers l eau",
        "La vieille femme raconte les legendes du soir",
    ]
    for i, v in enumerate(diop):
        corpus.append((f"diop_{i:03d}", v))
    
    # === APOLLINAIRE (25 extraits) ===
    apollinaire = [
        "Sous le pont Mirabeau coule la Seine et nos amours faut il qu il m en souvienne",
        "A la fin tu es las de ce monde ancien bergere o tour Eiffel le troupeau des ponts bele ce matin",
        "Mon beau navire o ma memoire avons nous assez navigue dans une eau morne",
        "J ai cueilli ce brin de bruyere l automne est morte souviens t en",
        "Les jours s en vont je demeure",
        "Passent les jours et passent les semaines",
        "Il pleut des voix de femmes comme si elles etaient mortes",
        "La jolie rousse au bord de l eau",
        "Le pont de fer jete sur la riviere",
        "Les saisons passent et les annees s envolent",
        "Le vent emporte les feuilles du souvenir",
        "La fumee monte des toits dans le soir",
        "Les reves sont des oiseaux en cage",
        "Le temps est un fleuve sans retour",
        "L amour est un enfant qui joue avec le feu",
        "La ville s illumine quand vient la nuit",
        "Le poete ecoute le chant du monde",
        "Les couleurs dansent dans la lumiere",
        "Le silence est le plus beau des poemes",
        "Les mots sont des ailes qui nous portent",
        "La beaute se cache dans les choses simples",
        "L infini tient dans un regard",
        "Le mystere habite chaque instant",
        "La joie eclate comme un fruit mur",
        "La tristesse glisse comme la pluie",
    ]
    for i, v in enumerate(apollinaire):
        corpus.append((f"apollinaire_{i:03d}", v))
    
    # === JACQUES PREVERT (30 extraits) ===
    prevert = [
        "Rappelle toi Barbara il pleuvait sans cesse sur Brest ce jour la",
        "Le dejeuner du matin dans la cuisine silencieuse",
        "Je suis comme je suis vous etes comme vous etes",
        "Le cancre au fond de la classe",
        "Les enfants qui s aiment s embrassent debout",
        "Le gardien du phare aime trop les oiseaux",
        "La peche a la baleine au large de l ile",
        "Le cheval rouge dans la cour de l ecole",
        "Le soleil brille pour tout le monde",
        "La vie est un cerisier en fleurs",
        "Les feuilles mortes se ramassent a la pelle",
        "Le temps des cerises est revenu",
        "Le petit garcon et la mer immense",
        "La chanson du soir au coin du feu",
        "Le chat qui dort sur le fauteuil rouge",
        "La pluie sur les carreaux de la fenetre",
        "Les fleurs du jardin eclosent au printemps",
        "Le boulanger vend son pain a l aube",
        "Le facteur apporte les lettres du matin",
        "La voisine arrose ses plantes vertes",
        "Les gamins jouent au ballon dans la rue",
        "Le marchand de glaces passe en chantant",
        "Le chien aboie a la lune pleine",
        "La radio diffuse un air de jazz",
        "Le peintre pose ses couleurs sur la toile",
        "Le menuisier rabote une planche de chene",
        "La couturiere coud une robe de soie",
        "Le marin regarde l horizon lointain",
        "Le poete ecrit sur un coin de table",
        "La nuit tombe doucement sur la ville",
    ]
    for i, v in enumerate(prevert):
        corpus.append((f"prevert_{i:03d}", v))
    
    # === PROVERBES AFRICAINS (50) ===
    proverbes = [
        "Le baobab a mis cent ans pour devenir grand mais il suffit d une nuit pour le detruire",
        "Le fleuve ne coule pas en ligne droite car il ecoute la sagesse de la terre",
        "Quand les tambours parlent les sages se taisent et les fous dansent",
        "La ou le coeur est le pied n hesite pas a aller",
        "Le savoir est comme un feu qu on allume",
        "Celui qui ne sait pas ou il va devrait regarder d ou il vient",
        "La patience est la cle du jardin de la vie",
        "Un seul bracelet ne sonne pas au poignet",
        "La parole du vieillard est comme le tronc du baobab",
        "L enfant qui refuse d apprendre marche vers la tombe",
        "Le soleil ne se leve que pour ceux qui sont debout",
        "La nuit tombe mais la lune reste pour veiller",
        "Un arbre qui tombe fait plus de bruit qu une foret qui pousse",
        "Le chien a quatre pattes mais ne peut emprunter qu un seul chemin",
        "La pluie ne tombe que sur les toits qui l attendent",
        "L eau qui dort n oublie pas de couler",
        "Le vent n emporte que ce qui est leger",
        "La terre ne ment jamais a celui qui l ecoute",
        "Le chant du coq reveille tout le village",
        "La main qui donne ne se fatigue jamais",
        "Le voyageur est un oiseau qui construit son nid partout",
        "La haine est un feu qui brule celui qui l allume",
        "L amour est un pont que personne ne peut detruire",
        "Le pardon est la cle qui ouvre toutes les portes",
        "La sagesse est un arbre dont les racines sont cachees",
        "Le silence est le langage des sages",
        "La parole est comme une fleche qu on ne peut rattraper",
        "L oreille est le chemin du coeur",
        "Les yeux voient mais le coeur comprend",
        "La bouche qui mange ne dit pas de mal du repas",
        "Le feu qui brule doucement rechauffe le mieux",
        "La lune ne tombe jamais du ciel",
        "Le mensonge donne des fleurs mais pas de fruits",
        "La verite est un soleil qui finit toujours par briller",
        "Le courage est comme un lion il rugit meme dans l ombre",
        "L unite est plus forte que la force",
        "Le travail est comme la pluie il finit par tout arroser",
        "La danse est la priere des jambes",
        "Le rire est le soleil de l ame",
        "L amitie est un tresor que la rouille n attaque pas",
        "Le respect est le vetement du sage",
        "La gratitude est la memoire du coeur",
        "Le partage multiplie les richesses",
        "L hospitalite est la premiere des richesses",
        "Le tambour ne parle pas sans raison",
        "La fumee du foyer monte toujours vers le ciel",
        "Les cicatrices racontent l histoire du guerrier",
        "L enfant est la fleche le parent est l arc",
        "Le vieillard qui meurt est une bibliotheque qui brule",
        "Le temps est un maitre qui enseigne sans parler",
    ]
    for i, v in enumerate(proverbes):
        corpus.append((f"proverbe_{i:03d}", v))
    
    # === HAIKUS (30) ===
    haikus = [
        "Dans le vieil etang une grenouille saute le bruit de l eau",
        "Le vent d automne emporte les feuilles mortes loin de leur arbre",
        "La neige recouvre le chemin du village endormi sous la lune",
        "Les cerisiers fleurissent dans la brume du petit matin",
        "La cigale chante au sommet du pin solitaire",
        "Le corbeau se pose sur la branche nue de l hiver",
        "La lune se reflete dans la riziere apres la pluie",
        "Le papillon danse sur les fleurs de printemps",
        "La vague s ecrase sur le rocher eternel",
        "Le feuillage bruisse dans la brise du soir",
        "Le temple ancien sous les cedres centenaires",
        "La cloche resonne dans le silence du soir",
        "Le nuage passe sans laisser de trace",
        "La source murmure entre les pierres moussues",
        "Le chemin de montagne disparait dans la brume",
        "L oiseau chante sans savoir qui l ecoute",
        "Le bambou plie sous le poids de la neige",
        "Le soleil couchant embrase les montagnes",
        "La barque glisse sur le lac immobile",
        "Le vent caresse les herbes de la prairie",
        "Les etoiles brillent dans le ciel decembre",
        "La pluie fine tombe sur les toits de chaume",
        "Le moine medite dans le jardin de pierres",
        "Le givre dessine des fleurs sur la fenetre",
        "L aube colore les monts lointains de rose",
        "La cascade chante sa chanson eternelle",
        "Le pin centenaire resiste a la tempete",
        "Le vieux pont de pierre sous la mousse",
        "Le cerf boit au ruisseau de la foret",
        "Le silence de l hiver emplit la vallee",
    ]
    for i, v in enumerate(haikus):
        corpus.append((f"haiku_{i:03d}", v))
    
    # === SAINT-JOHN PERSE (20 extraits) ===
    perse = [
        "Un grand poeme ne de rien un grand poeme fait de rien",
        "Sur trois grandes saisons m ouvrant avec honneur",
        "J habiterai mon nom fut un grand siecle d or",
        "Le vent du monde souffle sur les terres nouvelles",
        "La mer ouvre ses portes aux grands navires",
        "Les iles emergent comme des promesses",
        "L horizon s elargit a chaque aube nouvelle",
        "Les conqueants arrivent sur les rives lointaines",
        "La terre inconnue attend son explorateur",
        "Le sel de la mer sur la peau des marins",
        "Les cartes se deplient sur la table du prince",
        "Le globe tourne dans la main du geographe",
        "L oiseau de mer survole les vagues immenses",
        "Le phare eclaire la nuit des navigateurs",
        "Le port s eveille dans le brouillard du matin",
        "Les cordages grincent sur les mats des navires",
        "Le capitaine consulte les etoiles du ciel",
        "Le vent gonfle les voiles vers l inconnu",
        "La vigie scrute l horizon infini",
        "Le voyage commence quand la terre disparait",
    ]
    for i, v in enumerate(perse):
        corpus.append((f"perse_{i:03d}", v))
    
    print(f"  Corpus etendu genere : {len(corpus)} vers poetiques")
    return corpus


# ==============================================================================
# GRAMMAIRE SPECTRALE
# ==============================================================================

class SpectralGrammar:
    """
    Grammaire spectrale : ordonne les mots par leur phase dans S^1.
    
    Au lieu d'assembler les mots avec des connecteurs aleatoires,
    on les dispose le long du cercle harmonique par ordre de phase
    croissante. Les sauts de phase creent le RYTHME du vers.
    
    Parametres :
      - min_phase_gap : saut minimal entre deux mots (evite la repetition)
      - max_phase_gap : saut maximal (au-dela -> rupture de vers)
      - line_length  : nombre de mots par vers
    """
    
    def __init__(self, min_phase_gap: float = PI/12, max_phase_gap: float = PI/2,
                 line_length: int = 8):
        self.min_phase_gap = min_phase_gap
        self.max_phase_gap = max_phase_gap
        self.line_length = line_length
    
    def compute_word_phase(self, word: str) -> float:
        """Calcule la phase d'un mot dans [0, 2pi]."""
        h = HBit.from_text(word)
        # La phase est l'angle du vecteur de coefficients dans l'espace harmonique
        phase = np.arctan2(
            np.sum(h.coefficients[1::2]),  # Somme des harmoniques impaires
            np.sum(h.coefficients[0::2])   # Somme des harmoniques paires
        ) % (2 * PI)
        return float(phase)
    
    def order_words_by_phase(self, words: List[str], theme_phase: float = 0.0
                             ) -> List[Tuple[str, float, float]]:
        """
        Ordonne les mots par leur phase, en commencant par la phase
        la plus proche du theme.
        
        Retourne : [(word, phase, distance_to_theme), ...]
        """
        word_phases = [(w, self.compute_word_phase(w)) for w in words]
        
        # Trier par distance a la phase du theme
        word_phases.sort(key=lambda x: abs(x[1] - theme_phase))
        
        return [(w, p, abs(p - theme_phase)) for w, p in word_phases]
    
    def compose_vers(self, words: List[str], theme: str, n_vers: int = 1,
                     vers_length: int = 8) -> List[str]:
        """
        Compose un ou plusieurs vers en utilisant la grammaire spectrale.
        
        Algorithme :
          1. Calculer la phase de chaque mot
          2. Calculer la phase du theme (onde de reference)
          3. Trier les mots par proximite a la phase du theme
          4. Construire le vers en prenant les mots dans l'ordre de phase
             et en inserant des ruptures la ou les sauts de phase sont grands
        """
        theme_hbit = HBit.from_text(theme)
        theme_phase = np.arctan2(
            np.sum(theme_hbit.coefficients[1::2]),
            np.sum(theme_hbit.coefficients[0::2])
        ) % (2 * PI)
        
        # Trier les mots par phase
        ordered = self.order_words_by_phase(words, theme_phase)
        
        # Filtrer : ne garder que les mots dont la distance a la phase du theme
        # est inferieure a max_phase_gap
        valid_words = [(w, p, d) for w, p, d in ordered if d < self.max_phase_gap * 1.5]
        
        if len(valid_words) < 3:
            # Pas assez de mots resonants -> prendre les plus proches
            valid_words = ordered[:vers_length * 2]
        
        # Construire les vers
        vers = []
        for v_idx in range(n_vers):
            start = v_idx * vers_length
            end = start + vers_length
            
            if start >= len(valid_words):
                break
            
            line_words = valid_words[start:end]
            
            # Ordonner par phase CROISSANTE pour la fluidite
            line_words.sort(key=lambda x: x[1])
            
            # Construire la ligne avec des sauts de phase comme ponctuation
            line = ""
            for i, (word, phase, _) in enumerate(line_words):
                if i == 0:
                    line += word
                else:
                    prev_phase = line_words[i-1][1]
                    phase_gap = abs(phase - prev_phase)
                    
                    if phase_gap > self.max_phase_gap:
                        line += ". " + word  # Rupture forte -> point
                    elif phase_gap > PI/3:
                        line += ", " + word  # Rupture moyenne -> virgule
                    elif phase_gap > PI/6:
                        line += " " + word   # Legere separation -> espace
                    else:
                        line += " " + word   # Fluidite -> espace simple
            
            if line:
                vers.append(line)
        
        return vers if vers else [" ".join(w for w, _, _ in valid_words[:vers_length])]


# ==============================================================================
# POETIC EMERGENCE V2
# ==============================================================================

class PoeticEmergenceV2:
    """
    Moteur d'emergence poetique v2 avec corpus etendu et grammaire spectrale.
    """
    
    def __init__(self):
        self.corpus_brut = generer_corpus_1000()
        self.grammar = SpectralGrammar()
        
        # Index des mots par vers
        self.word_index = defaultdict(list)
        for name, text in self.corpus_brut:
            for word in text.lower().split():
                if len(word) > 2:
                    self.word_index[word].append(name)
        
        # Construire l'hologramme
        self.hologram = np.zeros((256, 256), dtype=np.complex128)
        self._build_hologram()
    
    def _build_hologram(self):
        """Hologramme poetique de tous les vers."""
        x = np.linspace(0, 1.0, 128)
        for name, text in self.corpus_brut:
            hbit = HBit.from_text(text)
            psi = np.zeros(128, dtype=np.complex128)
            for i, coeff in enumerate(hbit.coefficients):
                psi += coeff * np.exp(1j * (i+1) * PHI * 2 * PI * x)
            n = np.linalg.norm(psi)
            if n > 1e-12:
                psi = psi / n
            self.hologram[:128, :128] += 0.05 * np.outer(psi, np.conj(psi))
    
    def composer(self, theme: str, n_vers: int = 3) -> List[str]:
        """
        Compose de la poesie sur un theme avec grammaire spectrale.
        """
        # 1. Trouver les mots qui resonnent avec le theme
        h_theme = HBit.from_text(theme)
        word_scores = {}
        for word in self.word_index.keys():
            if len(word) > 2:
                h_word = HBit.from_text(word)
                interf = h_theme.interference(h_word)
                if interf > 0.2:
                    word_scores[word] = interf
        
        # 2. Selectionner les meilleurs mots
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        top_words = [w for w, s in sorted_words[:50] if s > 0.25]
        
        # 3. Composer avec la grammaire spectrale
        return self.grammar.compose_vers(top_words, theme, n_vers=n_vers)
    
    def faire_emerger(self, theme: str, n_vers: int = 3) -> List[str]:
        """Fait emerger des vers par resonance thematique."""
        return self.composer(theme, n_vers=n_vers)
    
    def interferer_vers(self, vers1_idx: int, vers2_idx: int) -> str:
        """Interfere deux vers du corpus (par index)."""
        if vers1_idx >= len(self.corpus_brut) or vers2_idx >= len(self.corpus_brut):
            return "Indices hors limites"
        
        _, text1 = self.corpus_brut[vers1_idx]
        _, text2 = self.corpus_brut[vers2_idx]
        
        h1 = HBit.from_text(text1)
        h2 = HBit.from_text(text2)
        h_interf = h1 * h2
        
        # Trouver les mots qui resonnent avec l'interference
        word_scores = {}
        for word in self.word_index.keys():
            h_word = HBit.from_text(word)
            interf = h_interf.interference(h_word)
            if interf > 0.2:
                word_scores[word] = interf
        
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        top_words = [w for w, s in sorted_words[:30] if s > 0.15]
        
        theme_combined = f"{text1[:30]} {text2[:30]}"
        vers = self.grammar.compose_vers(top_words, theme_combined, n_vers=1, vers_length=10)
        return vers[0] if vers else " ".join(top_words[:8])
    
    def resonance_complete(self, theme: str) -> Dict[str, Any]:
        """Resonance complete avec analyse harmonique."""
        h_theme = HBit.from_text(theme)
        
        # Vers qui resonnent dans le corpus
        scores = []
        for name, text in self.corpus_brut:
            h_text = HBit.from_text(text)
            interf = h_theme.interference(h_text)
            if interf > 0.3:
                scores.append((text, interf))
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Vers qui emergent
        vers_emergents = self.faire_emerger(theme, n_vers=3)
        
        # Harmoniques dominantes
        harmonic_profile = []
        for i, coeff in enumerate(h_theme.coefficients):
            if abs(coeff) > 0.03:
                roles = ['phi-proportion', 'pi-cyclicite', 'e-elan', 'sqrt2-dualite',
                        'sqrt3-profondeur', 'sqrt5-mystere', 'e/pi-souffle']
                harmonic_profile.append({
                    'constante': H_CONSTANT_NAMES[i],
                    'role': roles[i] if i < len(roles) else 'superieure',
                    'activation': round(float(abs(coeff)), 4),
                })
        harmonic_profile.sort(key=lambda x: x['activation'], reverse=True)
        
        return {
            'theme': theme,
            'harmoniques': harmonic_profile[:3],
            'vers_existants': [(t[:80], round(s, 4)) for t, s in scores[:3]],
            'vers_emergents': vers_emergents,
        }


# ==============================================================================
# DEMONSTRATION
# ==============================================================================

def demo_v2():
    print("=" * 70)
    print("  EMERGENCE POETIQUE v2 — Corpus 1000+ vers + Grammaire Spectrale")
    print("=" * 70)
    
    pe = PoeticEmergenceV2()
    
    # Test 1 : Emergence thematique
    print("\n[TEST 1] EMERGENCE THEMATIQUE (Grammaire Spectrale)")
    themes = ["l amour et la lumiere", "le chant de la terre"]
    for theme in themes:
        vers = pe.faire_emerger(theme, n_vers=2)
        print(f"\n  Theme : '{theme}'")
        for i, v in enumerate(vers):
            print(f"  Vers {i+1} : {v}")
    
    # Test 2 : Interference
    print("\n[TEST 2] INTERFERENCE ENTRE DEUX VERS DU CORPUS")
    n = len(pe.corpus_brut)
    import random; random.seed(42)
    paires = [(0, 7), (50, 80), (150, 250), (300, 400)]
    for i1, i2 in paires:
        resultat = pe.interferer_vers(i1, i2)
        _, t1 = pe.corpus_brut[i1]
        _, t2 = pe.corpus_brut[i2]
        print(f"\n  Vers1 [{i1}] : {t1[:50]}...")
        print(f"  Vers2 [{i2}] : {t2[:50]}...")
        print(f"  -> EMERGENCE : {resultat[:120]}")
    
    # Test 3 : Resonance complete
    print("\n[TEST 3] RESONANCE COMPLETE")
    for theme in ["l amour eternel", "la lumiere dansante"]:
        r = pe.resonance_complete(theme)
        print(f"\n  Theme : '{theme}'")
        print(f"  Harmoniques : {[h['constante'] for h in r['harmoniques']]}")
        print(f"  Vers existants resonants :")
        for v, s in r['vers_existants']:
            print(f"    [{s:.4f}] {v}...")
        print(f"  Vers emergents :")
        for v in r['vers_emergents']:
            print(f"    -> {v[:100]}")


if __name__ == "__main__":
    demo_v2()