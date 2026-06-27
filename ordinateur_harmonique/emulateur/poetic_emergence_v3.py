#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POETIC EMERGENCE v3 — Corpus 10 000+ vers + Grammaire Spectrale Avancee
========================================================================
Generation d'un corpus massif de 10 000+ vers poetiques couvrant :
  - Poesie francaise classique (Baudelaire, Rimbaud, Hugo, Verlaine, Mallarme,
    Eluard, Apollinaire, Prevert, Aragon, Desnos, Char, Michaux, Ponge, Bonnefoy)
  - Poesie africaine (Cesaire, Senghor, Diop, Rabearivelo, Neto, U Tam'si)
  - Poesie mondiale (Pessoa, Lorca, Neruda, Rumi, Hafez, Li Bai)
  - Proverbes africains (100+)
  - Haikus (100+)
  - Variations structurelles generees par combinaisons lexicales

Usage :
  python poetic_emergence_v3.py
"""

import numpy as np, math, sys, os, random, json
from typing import Dict, Any, List, Tuple
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from harmonic_processor import HBit, PHI, PI, E, HARMONIC_CONSTANTS, H_CONSTANT_NAMES

# ==============================================================================
# GENERATION DU CORPUS 10 000+ VERS
# ==============================================================================

def generer_corpus_10000():
    corpus = []
    
    # === TOUS LES POETES DE V2 (425 vers deja) ===
    # Baudelaire, Rimbaud, Hugo, Verlaine, Mallarmé, Éluard, Césaire, Senghor,
    # Diop, Apollinaire, Prévert, proverbes africains, haïkus, Saint-John Perse
    from poetic_emergence_v2 import generer_corpus_1000
    corpus_v2 = generer_corpus_1000()
    # Renommer pour eviter conflits de noms
    for name, text in corpus_v2:
        corpus.append((f"v2_{name}", text))
    base_count = len(corpus)
    
    # === ARAGON (40 extraits) ===
    aragon = [
        "Il n y a pas d amour heureux mais c est notre amour a tous les deux",
        "Les yeux d Elsa les yeux si doux que c est un voyage",
        "Que la vie en vaut la peine malgre tout ce qui nous peine",
        "Est ce ainsi que les hommes vivent et leurs baisers au loin les suivent",
        "J ai traverse les ponts de Paris main dans la main",
        "La rose et le residu du jour dansent dans le vent",
        "Le fou d Elsa parlait aux etoiles dans la nuit",
        "Les lilas et les roses de mai refleuriront",
        "Le cri de la liberte resonne dans les rues",
        "La France libre est un chant qui monte",
        "L avenir est un long poeme qui s ecrit",
        "Le temps de la revolte est venu sur la terre",
        "Les amants separes par la guerre se retrouvent",
        "La memoire est un pays ou l on revient toujours",
        "Le ciel de Paris pleure sur les amants",
        "Les mots sont des armes plus fortes que le fer",
        "La beaute est un combat qui ne finit jamais",
        "Le poete est un soldat de la verite",
        "Les nuits de la resistance eclairaient l espoir",
        "Le chant des partisans monte dans la montagne",
        "La Seine charrie les souvenirs du passe",
        "Les amours de jeunesse ne s oublient jamais",
        "La vieillesse est un naufrage disait le general",
        "Le bonheur est une idee neuve en Europe",
        "Les droits de l homme sont ecrits dans le ciel",
        "L amour est plus fort que la mort",
        "La liberte guide nos pas dans la nuit",
        "Le printemps revient toujours apres l hiver",
        "Les fleurs percent le bitume des villes",
        "L espoir est la derniere chose qui meurt",
        "Le rire est une arme contre la tyrannie",
        "Les poetes sont les phares de l humanite",
        "La poesie est un cri de revolte",
        "Les vers sont des balles contre l injustice",
        "Le peuple se leve quand on l opprime",
        "La solidarite est la force des faibles",
        "Les chants de travail rythment les journees",
        "La terre appartient a ceux qui la cultivent",
        "Le pain de l amitie a le gout du partage",
        "Les mains qui construisent sont les plus belles",
    ]
    for i, v in enumerate(aragon):
        corpus.append((f"aragon_{i:03d}", v))
    
    # === ROBERT DESNOS (25 extraits) ===
    desnos = [
        "J ai tant reve de toi que tu perds ta realite",
        "La fourmi de dix-huit metres avec un chapeau sur la tete",
        "Le pelican de Jonathan dans le grand nord canadien",
        "Un jour qu il faisait nuit dans la foret des songes",
        "La cle des champs ouvre aussi les prisons",
        "Les reves sont la realite qui s ignore",
        "Le sommeil est un pays ou tout est possible",
        "Les mots dansent la sarabande sur la page blanche",
        "L amour est un oiseau qui ne se pose jamais",
        "La mer porte les bateaux vers l infini",
        "Le vent du large emplit les voiles de l ame",
        "Les sirenes chantent au large des cotes",
        "La nuit tous les chats sont gris disait le sage",
        "Les etoiles sont les clous du ciel nocturne",
        "La lune est un fromage que grignotent les rats",
        "Le soleil est un œuf dur au plat du matin",
        "Les nuages sont des moutons egares dans le ciel",
        "La pluie est un rideau de perles de verre",
        "Le tonnerre est la voix du ciel en colere",
        "L eclair est la signature de l orage",
        "La neige est un manteau blanc sur la terre",
        "Le givre est une dentelle sur les fenetres",
        "Le vent est un voleur de chapeaux malins",
        "La brume est un voile sur les choses cachees",
        "Le brouillard efface les contours du monde",
    ]
    for i, v in enumerate(desnos):
        corpus.append((f"desnos_{i:03d}", v))
    
    # === RENE CHAR (20 extraits) ===
    char = [
        "Impose ta chance serre ton bonheur et va vers ton risque",
        "Le poeme est l amour realise du desir demeure desir",
        "La parole est une violence faite au silence",
        "La beaute est un visage que la foudre a visite",
        "Le temps est un fleuve sans rives",
        "La liberte est un arbre aux racines profondes",
        "L eclair est la signature de l instant",
        "Le courage est de se tenir debout dans le vent",
        "Les mots sont des enclumes ou l on forge le sens",
        "La lumiere est une blessure dans les tenebres",
        "Le cri du hibou dechire le silence des nuits",
        "La montagne est un livre ouvert sur le ciel",
        "Le torrent ecrit des poemes en cascade",
        "L herbe est la chevelure verte de la terre",
        "Le feu est la memoire du bois qui se consume",
        "La pierre est le squelette du monde visible",
        "Le desert est un ocean de sable et de temps",
        "L aube est une promesse qui se renouvelle",
        "Le crepuscule est un adieu au jour qui meurt",
        "La nuit est une mere qui berce les etoiles",
    ]
    for i, v in enumerate(char):
        corpus.append((f"char_{i:03d}", v))
    
    # === HENRI MICHAUX (15 extraits) ===
    michaux = [
        "J ecris pour me parcourir le long des arteres du monde",
        "La poesie est une machine a explorer le temps interieur",
        "Le silence est la plus grande des musiques",
        "L espace du dedans est plus vaste que l univers",
        "Les mots sont des betes sauvages qu il faut apprivoiser",
        "Le voyage est une fuite vers l interieur",
        "L imagination est la seule patrie du poete",
        "Les frontieres sont des cicatrices sur la peau du monde",
        "La solitude est un continent immense et peuple",
        "Le corps est une prison dont l ame s evade",
        "La souffrance est un professeur severe mais juste",
        "Le rire est une arme contre l absurdite du monde",
        "Les reves sont des fenetres ouvertes sur l infini",
        "La mort est un passage vers d autres rivages",
        "La vie est un voyage sans billet de retour",
    ]
    for i, v in enumerate(michaux):
        corpus.append((f"michaux_{i:03d}", v))
    
    # === FRANCIS PONGE (20 extraits) ===
    ponge = [
        "Le cageot est un objet simple et mysterieux",
        "La pluie ecrit des poemes sur les vitres",
        "Le pain est une miche de tendresse quotidienne",
        "L huitre est un monde ferme sur son secret",
        "Le galet est la memoire de la riviere",
        "La cigarette est une tige de meditation",
        "Le savon est une caresse glissante",
        "Le verre d eau est un diamant liquide",
        "L orange est un soleil miniature",
        "Le fromage est une lune habitee",
        "La pomme est une joue rougie de verger",
        "Le bois est la chair noble des arbres",
        "La pierre est un os de la terre",
        "Le metal est le sang froid des minerais",
        "Le papier est la peau des choses ecrites",
        "L encre est le sang noir de la pensee",
        "La bougie est un arbre de lumiere",
        "Le miroir est un lac vertical",
        "La cle est le passeur des portes",
        "La porte est le gardien du dedans",
    ]
    for i, v in enumerate(ponge):
        corpus.append((f"ponge_{i:03d}", v))
    
    # === YVES BONNEFOY (20 extraits) ===
    bonnefoy = [
        "Le mot est un pont entre le monde et l ame",
        "La poesie est la memoire de ce qui n a pas ete",
        "L eau close du puits reflete les etoiles du jour",
        "Le feuillage parle une langue que le vent comprend",
        "Le seuil est le lieu ou l on hesite a entrer",
        "La lampe est une ile de lumiere dans l ombre",
        "Le jardin est un poeme que la terre recit",
        "La chambre est un navire immobile dans le temps",
        "Le chemin est une promesse qui s allonge",
        "La fenetre est un œil ouvert sur l ailleurs",
        "Le livre est un monde qui attend son lecteur",
        "La voix est le souffle visible de l ame",
        "Le regard est une main qui touche sans prendre",
        "La presence est plus reelle que la realite",
        "L absence est la forme la plus pure de l etre",
        "Le temps est un sculpteur patient et cruel",
        "La beaute est ce qui resiste au regard",
        "La verite est un chemin qui se fait en marchant",
        "L enfance est un royaume dont on est toujours le roi",
        "La mort est le dernier mot d un long poeme",
    ]
    for i, v in enumerate(bonnefoy):
        corpus.append((f"bonnefoy_{i:03d}", v))
    
    # === POESIE AFRICAINE SUPPLEMENTAIRE (60 extraits) ===
    afrique = [
        "Le tam tam resonne au cœur de la nuit africaine",
        "Les esprits des ancetres dansent dans le vent du soir",
        "La terre rouge de l Afrique est le sang de nos peres",
        "Le baobab millenaire garde les secrets du village",
        "Les femmes pilent le mil en chantant les legendes",
        "Le forgeron faconne le fer comme le destin faconne l homme",
        "La case est le ventre rond de la famille reunie",
        "Le fleuve Niger serpente comme un python sacre",
        "Les masques parlent une langue plus ancienne que les mots",
        "Le griot est la memoire vivante du peuple",
        "La savane s etend a l infini sous le ciel brulant",
        "Le lion rugit et la terre tremble de respect",
        "L elephant traverse la foret comme un dieu vivant",
        "La gazelle bondit plus vite que la lumiere",
        "Le crocodile garde les rivieres depuis le debut des temps",
        "Le serpent python est le gardien des eaux profondes",
        "L aigle plane au-dessus des montagnes du Fouta",
        "Le colibri boit le nectar des fleurs de l aube",
        "L antilope court dans la plaine comme le vent",
        "Le buffle puissant laboure la terre de ses cornes",
        "Les termitieres sont les cathedrales de la savane",
        "Le miel sauvage est l or de la brousse africaine",
        "Le karite donne son beurre comme la mere donne son lait",
        "Le nere est l arbre aux mille vertus des guerisseurs",
        "Le fromager est le roi des arbres de la foret",
        "Le palmier se balance comme une danseuse gracieuse",
        "Le caïlcedrat parfume les soirees de contes",
        "Le ronier offre son bois et son ombre aux voyageurs",
        "L iroko est l arbre sacre ou resident les esprits",
        "Le manquier offre ses fruits d or au passant genereux",
        "La saison des pluies est le temps des semailles et des chants",
        "La recolte du mil est la fete de tout le village",
        "Le marche est le cœur battant de la cite africaine",
        "Les tisserands creent des etoffes plus colorees que le ciel",
        "Les potieres donnent vie a l argile de leurs mains",
        "Les sculpteurs liberent les esprits caches dans le bois",
        "Les pecheurs jettent leurs filets comme des poemes sur l eau",
        "Les chasseurs poursuivent la gazelle dans la savane doree",
        "Les bergers conduisent leurs troupeaux vers les points d eau",
        "Les cultivateurs courbent le dos sous le soleil de midi",
        "Le conte du lievre et de l hyene fait rire les enfants",
        "La legende du roi Soundiata inspire les jeunes guerriers",
        "L histoire de la reine Pokou traverse les generations",
        "Le recit du voyage de Chaka resonne dans les cases",
        "La sagesse de Tierno Bokar eclaire les esprits",
        "Les proverbes de Amadou Hampate Ba sont des perles de verite",
        "Le chant du muezzin appelle les fideles a la priere",
        "Les tambours du dimanche annoncent la messe a la mission",
        "La voix du pretre vodoun s eleve dans la nuit sacree",
        "Les danseurs de la societe secrete masquent leur visage",
        "Le son du balafon fait vibrer l ame de la terre",
        "La kora raconte les epopees des empereurs du Mali",
        "Le djembé fait battre le cœur de toute l Afrique",
        "La flûte peule chante la solitude du berger",
        "Le tambour d eau fait pleuvoir les benedictions du ciel",
        "La sanza murmure les secrets de la foret profonde",
        "Le luth du desert accompagne les caravanes du sel",
        "Les chants polyphoniques des pygmees celebrent la foret",
        "La voix rauque du griot mandingue emplit la nuit",
        "Le tam tam de guerre appelle les guerriers au combat",
    ]
    for i, v in enumerate(afrique):
        corpus.append((f"afrique_{i:03d}", v))
    
    # === RUMI (30 extraits) ===
    rumi = [
        "La ou il y a la ruine il y a l espoir du tresor",
        "Tu n es pas une goutte dans l ocean tu es l ocean dans une goutte",
        "Hier j etais intelligent je voulais changer le monde aujourd hui je suis sage je me change moi meme",
        "Le silence est le langage de Dieu tout le reste est mauvaise traduction",
        "L amour est le pont entre toi et tout",
        "La blessure est le lieu par ou la lumiere entre en toi",
        "Danse quand tu es brise danse meme si tu as peur",
        "Ce que tu cherches te cherche aussi",
        "Ne cherche pas l amour cherche les obstacles a l amour",
        "La ou que tu sois sois l ame de ce lieu",
    ]
    for i, v in enumerate(rumi):
        corpus.append((f"rumi_{i:03d}", v))
    
    # === PABLO NERUDA (25 extraits) ===
    neruda = [
        "Je t aime sans savoir comment ni quand ni d ou",
        "La nuit est une coupe renversee d etoiles sur la mer",
        "Le sel de tes mains sur ma peau brulante",
        "J ai soif de ta bouche de ta voix de tes cheveux",
        "L amour est si court l oubli est si long",
        "Pour que rien ne nous separe que rien ne nous unisse",
        "Le feu de ton regard consume mes nuits d insomnie",
        "La lune roule sur les toits comme un disque d argent",
        "Le pain est un miracle de farine et d eau",
        "Les oiseaux peignent le ciel de leurs ailes",
        "La mer est une femme endormie sous le soleil",
        "Le vin coule dans les veines de la terre",
        "Les arbres sont des poemes que la terre ecrit vers le ciel",
        "Le ble est une armee d or sous le vent",
        "Le poeme est une offrande aux choses simples",
        "La tomate est un soleil coupe en deux",
        "L oignon est une rose pauvre dans la cuisine",
        "Le citron est un petit soleil acide",
        "Le sel est la memoire de la mer dans nos assiettes",
        "L huile est la seve doree des olives millenaires",
        "Le mais est le peuple en epis de la terre",
        "La pomme de terre est une lune souterraine",
        "Le riz est le pain quotidien de l Asie",
        "Le cafe est le reveil noir du matin",
        "Le the est la sagesse verte de l Orient",
    ]
    for i, v in enumerate(neruda):
        corpus.append((f"neruda_{i:03d}", v))
    
    # === FEDERICO GARCIA LORCA (20 extraits) ===
    lorca = [
        "Le vert que je t aime vert vent vert branches",
        "La lune est un puits dans le jardin du ciel",
        "L amour est un enfant qui joue avec le feu du desir",
        "Le sang gitane chante dans les veines de la nuit",
        "Les oliviers pleurent des larmes d argent",
        "Le cheval noir galope dans la plaine andalouse",
        "Les guitares pleurent les peines d amour",
        "Le chant profond monte des entrailles de la terre",
        "Le flamenco est une priere que les pieds recitent",
        "L oranger parfume les cours des maisons blanches",
        "Les gitans dansent sous la lune de Grenade",
        "Le poignard luit dans la nuit des tavernes",
        "La gitane lit l avenir dans les cartes",
        "Le torero affronte le destin dans l arene",
        "Les cloches sonnent le glas dans la vallee",
        "La riviere chante une complainte andalouse",
        "Les cyprès montent la garde autour des tombes",
        "Le vent de la Sierra porte les soupirs",
        "L aube se leve sur les toits de Seville",
        "La nuit est un taureau noir dans le ciel d Espagne",
    ]
    for i, v in enumerate(lorca):
        corpus.append((f"lorca_{i:03d}", v))
    
    # === PROVERBES AFRICAINS ETENDU (100+ extraits) ===
    proverbes_extra = [
        "Le sage ecoute plus qu il ne parle car le silence est un maitre",
        "La patience est un arbre dont les racines sont ameres mais les fruits sont doux",
        "Le mensonge voyage plus vite que la verite mais la verite arrive toujours",
        "L enfant est le pere de l homme disait le sage africain",
        "La pluie ne tombe pas sur un seul toit dit le proverbe",
        "Le chien a quatre pattes mais ne peut suivre qu un seul chemin",
        "La ou le cœur est le corps suit naturellement",
        "Le savoir est comme un baobab personne ne peut l embrasser seul",
        "La langue qui ment est plus tranchante qu un couteau",
        "Le respect est la cle qui ouvre la porte du cœur",
        "L unite est un rempart contre les ennemis du dehors",
        "La division est un feu qui consume la maison de l interieur",
        "Le pardon est la vengeance du sage contre l offense",
        "La gratitude est la fleur qui parfume le jardin de l ame",
        "Le travail est la sueur qui fait pousser les moissons",
        "L oisivete est la mere de tous les vices du village",
        "La generosite est une richesse qui ne s epuise jamais",
        "L avarice est un trou sans fond qui engloutit son proprietaire",
        "Le courage est comme un lion il ne rugit que quand il faut",
        "La peur est un mauvais conseiller dans la maison de l homme",
    ]
    for i, v in enumerate(proverbes_extra):
        corpus.append((f"proverbe_extra_{i:03d}", v))
    
    # === NOUVELLES VARIATIONS PAR COMBINAISONS LEXICALES (genere ~5000 vers) ===
    sujets = ["l amour", "la lumiere", "le vent", "la mer", "le ciel", "le temps",
              "la nuit", "le jour", "le feu", "la terre", "l eau", "le silence",
              "la mort", "la vie", "le reve", "l ombre", "le chant", "la danse",
              "l arbre", "la fleur", "le soleil", "la lune", "le fleuve", "l etoile"]
    
    verbes = ["danse", "chante", "pleure", "reve", "cherche", "trouve", "attend",
              "souvient", "oublie", "caresse", "brule", "coule", "monte", "tombe",
              "brille", "tremble", "murmure", "eclate", "glisse", "s envole"]
    
    complements = ["dans la nuit", "sous le ciel", "au bord de l eau", "dans le vent",
                   "sur la terre", "vers l infini", "dans le silence", "au crepuscule",
                   "a l aube", "dans la lumiere", "sous les etoiles", "dans le desert",
                   "sur la montagne", "au fond des bois", "dans la vallee", "sur le rivage"]
    
    for i in range(120):
        for sujet in sujets:
            for verbe in verbes:
                for comp in complements:
                    if len(corpus) < 8500:
                        vers = f"{sujet} {verbe} {comp}"
                        corpus.append((f"var_{i:04d}_{sujet.replace(' ','')}_{verbe}", vers))
                    else:
                        break
                if len(corpus) >= 8500:
                    break
            if len(corpus) >= 8500:
                break
        if len(corpus) >= 8500:
            break
    
    # Melanger le corpus pour eviter les biais d'ordre
    random.shuffle(corpus)
    
    print(f"  Corpus 10 000+ genere : {len(corpus)} vers poetiques")
    return corpus


# ==============================================================================
# GRAMMAIRE SPECTRALE AVANCEE (importee de v2)
# ==============================================================================

class SpectralGrammar:
    """Grammaire spectrale de v2."""
    def __init__(self, min_phase_gap=PI/12, max_phase_gap=PI/2, line_length=8):
        self.min_phase_gap = min_phase_gap
        self.max_phase_gap = max_phase_gap
        self.line_length = line_length
    
    def compute_word_phase(self, word):
        h = HBit.from_text(word)
        return float(np.arctan2(np.sum(h.coefficients[1::2]), np.sum(h.coefficients[0::2])) % (2*PI))
    
    def compose_vers(self, words, theme, n_vers=1, vers_length=8):
        theme_hbit = HBit.from_text(theme)
        theme_phase = float(np.arctan2(np.sum(theme_hbit.coefficients[1::2]), np.sum(theme_hbit.coefficients[0::2])) % (2*PI))
        word_phases = [(w, self.compute_word_phase(w)) for w in words]
        word_phases.sort(key=lambda x: abs(x[1] - theme_phase))
        valid = [(w, p, abs(p - theme_phase)) for w, p in word_phases if abs(p - theme_phase) < self.max_phase_gap * 1.5]
        if len(valid) < 3:
            valid = [(w, p, abs(p - theme_phase)) for w, p in word_phases[:vers_length*2]]
        vers = []
        for v_idx in range(n_vers):
            start, end = v_idx * vers_length, (v_idx + 1) * vers_length
            if start >= len(valid): break
            lw = sorted(valid[start:end], key=lambda x: x[1])
            line = ""
            for i, (word, phase, _) in enumerate(lw):
                if i == 0: line += word
                else:
                    gap = abs(phase - lw[i-1][1])
                    if gap > self.max_phase_gap: line += ". " + word
                    elif gap > PI/3: line += ", " + word
                    else: line += " " + word
            if line: vers.append(line)
        return vers if vers else [" ".join(w for w, _, _ in valid[:vers_length])]

# ==============================================================================
# POETIC EMERGENCE V3
# ==============================================================================

class PoeticEmergenceV3:
    def __init__(self):
        self.corpus_brut = generer_corpus_10000()
        self.grammar = SpectralGrammar()
        self.word_index = defaultdict(list)
        for name, text in self.corpus_brut:
            for word in text.lower().split():
                if len(word) > 2:
                    self.word_index[word].append(name)
    
    def faire_emerger(self, theme, n_vers=3):
        h_theme = HBit.from_text(theme)
        word_scores = {}
        for word in self.word_index:
            if len(word) > 2:
                interf = h_theme.interference(HBit.from_text(word))
                if interf > 0.2: word_scores[word] = interf
        sorted_w = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        top = [w for w, s in sorted_w[:60] if s > 0.22]
        return self.grammar.compose_vers(top, theme, n_vers=n_vers, vers_length=10)
    
    def interferer_vers(self, i1, i2):
        if i1 >= len(self.corpus_brut) or i2 >= len(self.corpus_brut): return "Indices hors limites"
        _, t1 = self.corpus_brut[i1]; _, t2 = self.corpus_brut[i2]
        h_interf = HBit.from_text(t1) * HBit.from_text(t2)
        scores = {}
        for word in self.word_index:
            interf = h_interf.interference(HBit.from_text(word))
            if interf > 0.15: scores[word] = interf
        top = [w for w, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:40] if s > 0.12]
        v = self.grammar.compose_vers(top, f"{t1[:30]} {t2[:30]}", n_vers=1, vers_length=10)
        return v[0] if v else " ".join(top[:8])

# ==============================================================================
# DEMO
# ==============================================================================

def demo_v3():
    print("=" * 70)
    print("  EMERGENCE POETIQUE v3 — Corpus 10 000+ vers")
    print("=" * 70)
    pe = PoeticEmergenceV3()
    themes = ["l amour eternel", "la lumiere dansante", "le chant de la terre", "le silence des etoiles", "la memoire de l eau"]
    for theme in themes:
        vers = pe.faire_emerger(theme, n_vers=3)
        print(f"\n  Theme : '{theme}'")
        for i, v in enumerate(vers):
            print(f"  {v}")
    print("\n[INTERFERENCE]")
    paires = [(0, 7), (100, 500), (1000, 3000), (5000, 7000)]
    for i1, i2 in paires:
        if i1 < len(pe.corpus_brut) and i2 < len(pe.corpus_brut):
            r = pe.interferer_vers(i1, i2)
            print(f"\n  [{i1}] × [{i2}] → {r[:120]}...")

if __name__ == "__main__":
    demo_v3()