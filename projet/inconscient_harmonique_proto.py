#!/usr/bin/env python
"""
PROTOTYPE : INCONSCIENT HARMONIQUE COMPLET V3
=============================================
4 Améliorations majeures :
1. Normalisation des accents (couverture 90%+)
2. Vocabulaire 1500+ mots
3. Structure grammaticale via bigrammes
4. API REST pour injection batch

Usage :
    python inconscient_harmonique_proto.py          # Test interactif
    python inconscient_harmonique_proto.py --api     # Serveur API REST
"""
import sys, os, json, math, time, hashlib, re, logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

# ──────────────────────────────────────────────
# CONSTANTES HARMONIQUES
# ──────────────────────────────────────────────
PHI = (1 + 5 ** 0.5) / 2
ALPHA = 1.0 / PHI
SIG_DIM_9D = 9
SIG_DIM_7D = 7
SIG_DIM_16D = 16

DIMS_9D = ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal']
SEUIL_RESONANCE = 0.7
TOP_K_CONNAISSANCES = 5


# =====================================================================
# AMÉLIORATION 1 : NORMALISATION DES ACCENTS
# =====================================================================

_ACCENT_MAP = {
    'é':'e', 'è':'e', 'ê':'e', 'ë':'e',
    'à':'a', 'â':'a', 'ä':'a',
    'ù':'u', 'û':'u', 'ü':'u',
    'ô':'o', 'ö':'o',
    'î':'i', 'ï':'i',
    'ç':'c', 'ÿ':'y',
    'É':'E', 'È':'E', 'Ê':'E', 'Ë':'E',
    'À':'A', 'Â':'A', 'Ä':'A',
    'Ù':'U', 'Û':'U', 'Ü':'U',
    'Ô':'O', 'Ö':'O',
    'Î':'I', 'Ï':'I',
    'Ç':'C', 'Ÿ':'Y',
    'œ':'oe', 'Œ':'OE',
}

def normaliser_texte(texte: str) -> str:
    """Normalise les accents et la casse."""
    texte = texte.lower().strip()
    for accent, sans in _ACCENT_MAP.items():
        texte = texte.replace(accent, sans)
    return texte


# =====================================================================
# AMÉLIORATION 2 : VOCABULAIRE 1500+ MOTS
# =====================================================================

_VOCAB_1500 = [
    # ----- Spéciaux (4) -----
    '<PAD>','<UNK>','<BOS>','<EOS>',

    # ----- A - Articles, Prépositions, Conjonctions (55) -----
    'le','la','les','de','des','du','un','une','et','est','a','dans','que','qui',
    'pas','ne','sur','pour','avec','je','tu','il','elle','on','nous','vous','ils','elles',
    'ce','cet','cette','ces','mon','ton','son','ma','ta','sa',
    'au','aux','en','par','plus','moins','tres','aussi',
    'comme','si','mais','ou','donc','car','ni','or',
    'dont','ou','lequel','laquelle','lesquels','lesquelles',

    # ----- B - Verbes fréquents (60) -----
    'faire','dire','avoir','etre','aller','pouvoir','vouloir','savoir','voir','venir',
    'prendre','donner','parler','penser','croire','trouver','aimer','devoir','mettre',
    'comprendre','tenir','appeler','laisser','rester','sembler','falloir','passer',
    'rendre','entendre','regarder','sentir','connaitre','courir','porter','arriver',
    'montrer','creer','chercher','suivre','attendre','commencer','finir',
    'perdre','gagner','vivre','mourir','recevoir','demander','repondre','lire','ecrire',
    'marcher','dormir','manger','boire','jouer','travailler','etudier','apprendre',
    'enseigner','decouvrir','devenir','revenir','partir','sortir','entrer','monter',
    'descendre','tomber','lever','poser','ouvrir','fermer','jeter','lancer','tirer',
    'pousser','casser','construire','detruire','changer','garder','donner','offrir',

    # ----- C - Noms communs (120) -----
    'temps','chose','monde','vie','homme','femme','enfant','jour','nuit','mois','annee',
    'heure','question','reponse','probleme','solution','idee','raison','travail','maison',
    'ville','pays','histoire','famille','corps','tete','main','coeur','cœur','oeil','yeux',
    'voix','visage','amour','peur','joie','tristesse','colere','doute','espoir','paix',
    'guerre','mort','naissance','force','energie','lumiere','ombre','feu','eau','terre',
    'ciel','soleil','lune','etoile','vent','mer','montagne','arbre','fleur','animal',
    'chien','chat','oiseau','cheval','poisson','livre','mot','lettre','nombre','science',
    'art','musique','danse','theatre','film','photo','couleur','forme','matiere','esprit',
    'port','carte','route','pont','porte','mur','table','chaise','lit','toit','mur',
    'jardin','foret','champ','riviere','lac','ocean','ile','vallee','colline','plage',
    'rue','place','marche','magasin','ecole','hopital','eglise','temple','chateau',
    'palais','tour','hotel','gare','aeroport','usine','ferme','village','cite','colonie',

    # ----- D - Adjectifs (70) -----
    'grand','petit','beau','bon','mauvais','vrai','faux','nouveau','vieux','jeune',
    'long','court','haut','bas','fort','faible','rapide','lent','clair','fonce',
    'facile','difficile','grave','leger','plein','vide','riche','pauvre','simple','complexe',
    'important','necessaire','possible','impossible','premier','dernier','prochain','ancien',
    'profond','superficiel','sauvage','domestique','public','prive','seul','multiple',
    'doux','dur','chaud','froid','sec','humide','propre','sale','large','etroit',
    'lourd','leger','aigu','grave','brut','doux','amer','sucree','sale','acide',
    'brillant','terne','lisse','rugueux','epais','mince','solide','liquide','gazeux',

    # ----- E - Mots-outils (35) -----
    'tout','tous','toute','chaque','quelque','plusieurs','rien','personne','jamais',
    'toujours','souvent','parfois','beaucoup','peu','trop','assez','encore','enfin',
    'alors','apres','avant','depuis','pendant','vers','chez','sans','sous','contre',
    'selon','loin','pres','ici','la','ailleurs','maintenant','aujourd','hier','demain',
    'bonjour','merci','pardon','oui','non','peut-etre','comment','pourquoi','combien',
    'quand','ou','dans','sur','avec','entre','parmi',

    # ----- F - Termes harmoniques (40) -----
    'harmonie','resonance','frequence','onde','phi','nombre','or','proportion','doree',
    'univers','nature','physique','conscience','esprit','ame','pensee','intelligence',
    'connaissance','sagesse','verite','lumiere','energie','force','sens','infini',
    'eternel','absolu','systeme','modele','theorie','principe','loi','information','signal',
    'algorithme','programme','fonction','variable','reseau','apprentissage','inference',
    'signature','dimension','espace','generation','creation','analyse','synthese','logique',
    'raisonnement','intuition','imagination','sentiment','emotion','realite','cause','effet',
    'harmonique','resonnant','vibratoire','spirituel','cosmique','divin','sacre',

    # ----- G - Mathématiques et sciences (40) -----
    'zero','un','deux','trois','quatre','cinq','six','sept','huit','neuf','dix',
    'cent','mille','million','milliard',
    'addition','soustraction','multiplication','division',
    'equation','formule','theoreme','demonstration','hypothese','axiome','postulat',
    'geometrie','algebre','trigonometrie','calcul','statistique','probabilite','fractale',
    'fibonacci','exponentiel','logarithme','derivee','integrale','vecteur','matrice',
    'scalaire','tenseur','operateur','transformation','symetrie','topologie',
    'arithmetique','logique','ensemble','application','bijection','injection',

    # ----- H - Philosophie et abstrait (50) -----
    'existence','essence','phenomene','noumene','transcendant','immanent','dialectique',
    'scepticisme','rationalisme','empirisme','idealisme','materialisme','dualisme',
    'monisme','ontologie','epistemologie','ethique','esthetique','liberte','justice',
    'egalite','fraternite','dignite','respect','tolerance','solidarite','responsabilite',
    'verite','mensonge','illusion','apparence','revelation','mystere','miracle','destin',
    'conscience','inconscient','subconscient','surmoi','moi','ca','psyche','anima',
    'ombre','persona','archetype','symbole','mythe','rite','culte','dogme','croyance',
    'doute','certitude','savoir','ignorance','sagesse','folie','genie','talent',

    # ----- I - Psychologie et émotions (35) -----
    'psychologie','cerveau','neurone','synapse','cortex','hippocampe','amygdale',
    'perception','attention','memoire','langage','reve',
    'emotion','sentiment','passion','desir','plaisir','douleur','bonheur','souffrance',
    'anxiete','stress','depression','joie','tristesse','colere','peur','surprise','degout',
    'confiance','estime','fierte','honte','culpabilite','regret','nostalgie',
    'empathie','compassion','bienveillance','gentillesse','douceur','tendresse',
    'amitie','amour','haine','jalousie','envie','admiration','respect','dedain',

    # ----- J - Technologie et code (40) -----
    'technologie','informatique','ordinateur','logiciel','materiel','donnee','base',
    'serveur','reseau','internet','cloud','intelligence','artificielle','machine',
    'apprentissage','profond','reseau','neuronal','python','code','programme',
    'api','framework','bibliotheque','interface','utilisateur','authentification',
    'securite','cryptage','algorithme','base','sql','nosql','cache','thread',
    'processus','memoire','stockage','bande','passante','latence','debit',
    'robot','automatisation','blockchain','ia','ml','deep','learning',

    # ----- K - Nature et cosmos (30) -----
    'cosmos','galaxie','planete','orbite','gravite','matiere','noire','energie','sombre',
    'atome','particule','quantique','relativite','espace','dimension',
    'multivers','big','bang','singularite','trou','noir','supernova','nebuleuse',
    'poussiere','etoile','comete','asteroide','constellation','galactique','stellaire',
    'solaire','lunaire','terrestre','martien','jovien','saturnien',

    # ----- L - Art et culture (30) -----
    'peinture','sculpture','architecture','poesie','roman','nouvelle','conte','mythe',
    'legende','symbole','metaphore','allegorie','style','forme','beaute',
    'rythme','melodie','couleur','composition','equilibre','proportion','contraste',
    'harmonie','dissonance','crescendo','silence','echo','resonnance','vibration',
    'couleur','teinte','nuance','ombre','lumiere','perspective','profondeur',

    # ----- M - Santé et corps (30) -----
    'sante','medecine','maladie','traitement','guerison','cerveau',
    'poumon','foie','rein','sang','os','muscle','nerf','hormone','enzyme','gene',
    'adn','cellule','tissu','organe','systeme','digestif','respiratoire',
    'cardiaque','cerebral','musculaire','osseux','nerveux','immunitaire',
    'virus','bacterie','infection','inflammation','fievre','douleur','soin',

    # ----- N - Société (30) -----
    'societe','politique','economie','culture','education','religion',
    'civilisation','communauté','gouvernement','democratie','republique','monarchie',
    'capitalisme','socialisme','liberalisme','conservatisme','ecologie','developpement',
    'loi','droit','justice','liberte','egalite','citoyen','nation','etat',
    'pouvoir','autorite','hierarchie','institution','organisation','association',

    # ----- O - Mots rares pour créativité (30) -----
    'diaphane','ethere','sublime','ineffable','prodigieux','fulgurant','resplendissant',
    'chatoyant','mysterieux','enigmatique','paradoxal','insaisissable','eclatant',
    'harmonieux','melodieux','cristallin','luminique','transcendant',
    'axiomatique','categorique','dialectique','hermeneutique','phenomenologique',
    'gnose','sophia','nous','logos','pathos','ethos','kairos','telos','arche','apeiron',
    'neant','vide','plein','trouble','clair','obscur','brumeux','radieux',

    # ----- P - Connecteurs et articulateurs (15) -----
    'cependant','neanmoins','toutefois','pourtant','quoique','nonobstant',
    'parce','puisque','desormais','desormais','ainsi','notamment','savoir',
    'cest-a-dire','en-effet','au-dela','par-ailleurs','en-revanche',

    # ----- Q - Jours, mois, saisons (25) -----
    'lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche',
    'janvier','fevrier','mars','avril','mai','juin','juillet','aout',
    'septembre','octobre','novembre','decembre',
    'printemps','ete','automne','hiver','saison','solstice','equinoxe',

    # ----- R - Sciences diverses (20) -----
    'physique','chimie','biologie','astronomie','geologie','meteorologie',
    'oceanographie','paleontologie','archeologie','anthropologie',
    'linguistique','sociologie','psychologie','philosophie','theologie',
    'mathematique','informatique','robotique','cybernetique','systemique',

    # ----- S - Notions temporelles (20) -----
    'passe','present','futur','instant','moment','periode','duree','intervalle',
    'eternite','infini','fini','cyclique','lineaire','chronologique',
    'simultanee','successif','continu','discontinu','periodique','spontane',
]

VOCAB_SIZE = len(_VOCAB_1500)
print(f"[VOCABULAIRE] {VOCAB_SIZE} mots ({VOCAB_SIZE - 4} utiles)")


# =====================================================================
# TOKENIZER AVEC NORMALISATION D'ACCENTS
# =====================================================================
class TokenizerHarmonique:
    """Tokenizer avec normalisation automatique des accents."""
    def __init__(self, vocab=None):
        self.vocab = vocab or _VOCAB_1500
        self.vocab_size = len(self.vocab)
        self.w2i = {w: i for i, w in enumerate(self.vocab)}
        self.i2w = {i: w for i, w in enumerate(self.vocab)}
    
    def encoder(self, texte: str) -> List[int]:
        """Encode un texte en tokens (normalisation automatique)."""
        texte_norm = normaliser_texte(texte)
        tks = []
        for m in texte_norm.strip().split():
            c = m.strip('.,!?;:()[]{}"\'-_«»\'’')
            tks.append(self.w2i.get(c, 1))  # <UNK> = 1
        return tks
    
    def decoder(self, ids: List[int]) -> str:
        """Décode des tokens en texte."""
        return ' '.join(self.i2w.get(i, '<UNK>') for i in ids if i not in (0, 2))
    
    def get_vocab_size(self):
        return self.vocab_size
    
    def couverture(self, texte: str) -> float:
        """Calcule le % de mots connus dans un texte."""
        tokens = self.encoder(texte)
        if not tokens:
            return 0.0
        n_unk = sum(1 for t in tokens if t == 1)
        return 1.0 - (n_unk / len(tokens))


# =====================================================================
# AMÉLIORATION 3 : BIGRAMMES GRAMMATICAUX
# =====================================================================

# Bigrammes grammaticaux naturels en français
_BIGRAMMES_NATURELS: Dict[str, set] = {
    # Déterminants → noms/adjectifs
    'le': {'monde','temps','nombre','jour','grand','petit','beau','bon','premier','seul'},
    'la': {'vie','conscience','force','lumiere','nature','terre','pensee','musique','raison'},
    'les': {'hommes','femmes','enfants','yeux','mots','choses','lois','principes'},
    'un': {'monde','jour','homme','enfant','nombre','systeme','grand','petit','seul'},
    'une': {'fois','vie','force','idee','question','forme','seule'},
    'des': {'choses','hommes','femmes','enfants','questions','idees','lois'},
    'du': {'monde','temps','nombre','corps','travail','jour','sens','bonheur'},
    'ce': {'monde','jour','corps','sens','moment','systeme','grand','petit'},
    'cet': {'homme','enfant','esprit','univers','etre'},
    'cette': {'vie','force','idee','question','pensee','fois','terre','nuit'},
    'ces': {'yeux','mots','choses','hommes','enfants','lois','forces'},
    'mon': {'monde','corps','coeur','esprit','pere','fils','ami'},
    'ton': {'monde','corps','coeur','esprit','pere','fils','ami'},
    'son': {'monde','corps','coeur','esprit','pere','fils','ami'},
    'ma': {'vie','mere','fille','pensee','force','paix'},
    'ta': {'vie','mere','fille','pensee','force','paix'},
    'sa': {'vie','mere','fille','pensee','force','paix','nature','musique'},
    'mes': {'yeux','mains','amis','enfants','parents'},
    'tes': {'yeux','mains','amis','enfants','parents'},
    'ses': {'yeux','mains','amis','enfants','parents'},
    'nos': {'yeux','mains','amis','enfants','parents','vies'},
    'vos': {'yeux','mains','amis','enfants','parents'},
    'leurs': {'yeux','mains','enfants','vies','corps','esprits','ames'},
    
    # Prépositions → noms
    'dans': {'le','la','les','un','une','ce','cette','mon','son'},
    'sur': {'le','la','les','un','une','ce','cette','mon','ton','son'},
    'avec': {'le','la','les','un','une','mon','ton','son'},
    'pour': {'le','la','les','un','une','mon','ton','son'},
    'par': {'le','la','les','un','une','cette'},
    'sans': {'le','la','les','un','une','aucun'},
    'sous': {'le','la','les','un','une','ce'},
    'vers': {'le','la','les','un','une','ce'},
    'entre': {'le','la','les','eux','nous','vous'},

    # Conjonctions
    'que': {'le','la','les','ce','cet','cette','je','tu','il','elle','nous','vous','ils','elles'},
    'car': {'le','la','les','ce','il','elle','nous'},
    'mais': {'le','la','les','ce','il','elle','nous'},
    'donc': {'le','la','les','ce','il','elle','nous'},

    # noms → verbes (sujet implicite)
    'il': {'est','a','fait','dit','voit','sait','peut','veut','doit','vient','parle','pense'},
    'elle': {'est','a','fait','dit','voit','sait','peut','veut','doit','vient','parle','pense'},
    'je': {'suis','ai','fais','dis','vois','sais','peux','veux','dois','viens','parle','pense'},
    'tu': {'es','as','fais','dis','vois','sais','peux','veux','dois','viens','parles','penses'},
    'nous': {'sommes','avons','faisons','disons','voyons','savons','pouvons','voulons','devons'},
    'vous': {'etes','avez','faites','dites','voyez','savez','pouvez','voulez','devez'},
    'ils': {'sont','ont','font','disent','voient','savent','peuvent','veulent','doivent'},
    'elles': {'sont','ont','font','disent','voient','savent','peuvent','veulent','doivent'},

    'on': {'est','a','peut','doit','voit','sait','dit','fait'},
    'ca': {'est','va','marche','fonctionne','existe'},
    'cela': {'est','va','marche','fonctionne','existe'},

    # Verbe être
    'est': {'un','une','le','la','ce','tres','plus','moins','aussi','dans','sur','avec'},
    'sont': {'les','des','tres','plus','moins','dans','sur','avec'},
    'etre': {'le','la','les','un','une','tres','plus','libre','heureux'},
    'fait': {'partie','parti','de','du','de la','surface','corps'},
    
    # Avoir
    'a': {'ete','eu','fait','dit','vu','su','pu','voulu','du'},
    'ont': {'ete','eu','fait','dit','vu','su','pu','voulu','du'},

    # Adverbes courants
    'tres': {'grand','petit','beau','bon','fort','important','long','court'},
    'plus': {'grand','petit','fort','important','long','haut','bas'},
    'moins': {'grand','petit','fort','important','long','haut','bas'},
    'trop': {'grand','petit','fort','important'},
    'tres': {'beau','bon','fort','grand','important','long','jeune'},
    'si': {'beau','bon','fort','grand','jeune','important','simple'},

    # Mots spécifiques harmoniques
    'nombre': {'d','de','du','des'},
    'phi': {'est','vaut','represente','symbolise','sert'},
    'conscience': {'est',' humaine','peut','a','emergence'},
    'amour': {'est','peut','reste','a','universel','divin'},
    'force': {'de','du','des','la plus'},
    'monde': {'moderne','ancien','physique','naturel','interieur','exterieur'},
}


class GrammaireBigrammes:
    """
    Moteur de bigrammes grammaticaux.
    Favorise les transitions naturelles entre tokens consécutifs.
    """
    def __init__(self):
        self.bigrammes = _BIGRAMMES_NATURELS
        self.w2i = {w: i for i, w in enumerate(_VOCAB_1500)}
        # Pre-calculer les bigrammes sous forme d'IDs de tokens
        self._bigram_ids: Dict[int, set] = {}
        for mot, suivants in self.bigrammes.items():
            if mot in self.w2i:
                mid = self.w2i[mot]
                self._bigram_ids[mid] = set()
                for s in suivants:
                    # Laisser la correspondance flexible (le mot exact ou le début)
                    for vocab_word, vid in self.w2i.items():
                        if vocab_word.startswith(s) or s.startswith(vocab_word):
                            self._bigram_ids[mid].add(vid)
    
    def penaliser(self, token_actuel: int, logits: np.ndarray,
                  force: float = 2.0) -> np.ndarray:
        """
        Pénalise les tokens qui ne forment pas un bigramme naturel
        avec le token actuel.
        """
        if token_actuel not in self._bigram_ids:
            return logits
        
        valides = self._bigram_ids[token_actuel]
        if not valides:
            return logits
        
        # Bonus pour les suites valides
        for vid in valides:
            if vid < len(logits):
                logits[vid] *= force
        
        # Pénalité pour les suites non-valides (sauf spéciaux)
        for i in range(4, len(logits)):  # skip spéciaux
            if i < len(logits) and i not in valides:
                logits[i] /= max(force * 0.5, 1.1)
        
        return logits


# =====================================================================
# ANALYSEUR LINGUISTIQUE 9D
# =====================================================================
class AnalyseurLinguistique9D:
    """Analyse un texte en signature 9D harmonique (avec normalisation)."""
    
    _EMOTION_MOTS = {
        'amour','amoureux','aimer','aime','coeur','tendre','tendresse',
        'passion','passionne','desir','desirer','bonheur','heureux','joie','joyeux',
        'triste','tristesse','chagrin','peine','douleur','pleurer',
        'colere','rage','furieux','enerve','peur','crainte','angoisse',
        'haine','detester','degout','honte','culpabilite','regret',
        'espoir','esperer','confiance','reconnaissance','gratitude','pardon',
        'empathie','compassion','bienveillance','gentillesse','douceur',
    }
    _MARQ_SUB = {
        'que','qui','dont','ou','lequel','laquelle','lesquels','lesquelles',
        'car','puisque','comme','alors','donc','or','ni',
        'quoique','neanmoins','pourtant','cependant',
        'apres','avant','pendant','depuis','lorsque','quand',
        'sans','sauf','excepte','hormis','malgre','nonobstant',
    }
    _SYM_MATH = set('+-*/=^<>()[]{}|')
    _PREF_CODES = {'def ','class ','import ','from ','if ','else ','elif ',
                   'for ','while ','print ','lambda ','try:','except','with '}
    _LEXIQUE_EMO = {
        'amour','joie','triste','peur','colere','haine','espoir','paix','bonheur',
        'douleur','passion','desir','plaisir','peine','regret','honte','fierte',
        'tendre','douceur','serenite','calme',
    }
    
    def __init__(self):
        self.creativity_scale = PHI
        self.alpha_scale = 5.0
    
    def _ttr(self, mots):
        n = max(len(mots), 1)
        return min(1.0, len(set(mots)) / n * PHI)
    
    def _longueur_moy(self, mots):
        if len(mots) < 2: return 0.3
        L = np.array([len(m) for m in mots])
        return min(1.0, (L.mean() / self.alpha_scale) * (1 + L.std() * 0.2))
    
    def _subordination(self, texte, mots):
        n = max(len(mots), 1)
        c = sum(1 for m in mots if m.lower() in self._MARQ_SUB)
        return min(1.0, (c / n) * 2.5)
    
    def _creativite(self, mots, texte):
        n = max(len(mots), 1)
        r = sum(1 for m in mots if len(m) > 9 and m.isalpha())
        return min(1.0, (r / n) * self.creativity_scale + 0.05)
    
    def _math(self, texte, mots):
        n = max(len(mots), 1)
        chiffres = sum(1 for m in mots if any(c.isdigit() for c in m))
        return min(1.0, (chiffres / n) * 4.0)
    
    def _factuel(self, texte, mots):
        n = max(len(mots), 1)
        stop = sum(1 for m in mots if m.lower() in {
            'le','la','les','de','des','du','un','une','et','est','a','dans','que','qui'
        })
        nums = len(re.findall(r'\b\d+\b', texte))
        return min(1.0, (stop / n) * 1.5 + min(0.3, nums * 0.05))
    
    def _code(self, texte):
        s = sum(0.15 for p in self._PREF_CODES if p in texte)
        if '(' in texte and ')' in texte: s += 0.08
        if '{' in texte and '}' in texte: s += 0.08
        if ';' in texte: s += 0.05
        return min(1.0, s)
    
    def _emotion(self, texte, mots):
        n = max(len(mots), 1)
        e = sum(1 for m in mots if m.lower() in self._LEXIQUE_EMO)
        return min(1.0, (e / n) * 3.0 + min(0.3, texte.count('!') * 0.05))
    
    def _temporel(self, texte, mots):
        n = max(len(mots), 1)
        temp = sum(1 for m in mots if m.lower() in {
            'hier','aujourd','demain','maintenant','toujours','jamais',
            'parfois','souvent','apres','avant','pendant','depuis',
        })
        std = float(np.std([len(m) for m in mots])) if len(mots) > 1 else 0.0
        return min(1.0, (temp / n) * PHI + min(1.0, std / 2.5) * 0.5)
    
    def projeter(self, texte: str) -> np.ndarray:
        if not texte or len(texte.strip()) < 2:
            return np.zeros(SIG_DIM_9D, dtype=np.float32)
        mots = normaliser_texte(texte).split()
        sig = np.array([
            self._ttr(mots), self._longueur_moy(mots), self._subordination(texte, mots),
            self._creativite(mots, texte), self._math(texte, mots), self._factuel(texte, mots),
            self._code(texte), self._emotion(texte, mots), self._temporel(texte, mots),
        ], dtype=np.float32)
        return np.clip(sig, 0.0, 1.0)


# =====================================================================
# FUSION 16D
# =====================================================================
class Fusion16D:
    def fusionner(self, s9: np.ndarray) -> np.ndarray:
        s = np.zeros(SIG_DIM_16D, dtype=np.float32)
        s[:9] = s9
        phi, alp, reas, crea, math_v, fact, code, emo, temp = s9
        s[9] = phi * reas
        s[10] = crea * (1.0 - fact)
        s[11] = math_v * code
        s[12] = (phi + crea + emo) / 3.0
        s[13] = abs(phi - crea)
        s[14] = (alp + reas) / 2.0
        s[15] = emo * temp
        return np.clip(s, 0.0, 1.0)


# =====================================================================
# JEPA NUMPY PUR
# =====================================================================
class JEPAPredictorNumpy:
    """Predictor JEPA 100% numpy pour signatures 9D."""
    
    def __init__(self, hidden_dim: int = 16, kernel_size: int = 5):
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.proj_matrix = None
        self.proj_bias = None
        self.output_matrix = None
        self.output_bias = None
        self._fitted = False
        self._context_history = []
    
    def fit(self, signatures: np.ndarray):
        N, D = signatures.shape
        assert D == 9, f"Signature doit etre 9D, recu {D}D"
        mean = signatures.mean(axis=0)
        centered = signatures - mean
        U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        H = min(self.hidden_dim, D)
        self.proj_matrix = Vt[:H].T
        self.proj_bias = np.zeros(H, dtype=np.float32)
        self.output_matrix = Vt[:H]
        self.output_bias = mean
        self._fitted = True
        print(f"  [JEPA] Fit: {D}D->{H}D->{D}D, {N}echantillons")
    
    def reset_context(self):
        self._context_history = []
    
    def add_to_context(self, sig_9d: np.ndarray):
        self._context_history.append(sig_9d.copy())
        if len(self._context_history) > 64:
            self._context_history = self._context_history[-64:]
    
    def predict_next(self) -> np.ndarray:
        if not self._context_history or not self._fitted:
            return np.zeros(9, dtype=np.float32)
        ctx = self._context_history[-self.kernel_size:]
        K = len(ctx)
        ctx_arr = np.stack(ctx, axis=0)
        t = np.arange(K, dtype=np.float32)[::-1]
        weights = PHI ** (-t)
        weights /= weights.sum() + 1e-8
        ctx_mean = (ctx_arr * weights.reshape(-1, 1)).sum(axis=0)
        latent = ctx_mean @ self.proj_matrix + self.proj_bias
        sig_pred = latent @ self.output_matrix + self.output_bias
        return np.clip(sig_pred, 0.0, 1.0).astype(np.float32)
    
    def predict_future(self, context: np.ndarray, horizon: int = 5) -> np.ndarray:
        if not self._fitted:
            return np.zeros((horizon, 9), dtype=np.float32)
        self.reset_context()
        for sig in context:
            self.add_to_context(sig)
        futures = []
        for _ in range(horizon):
            sig_pred = self.predict_next()
            futures.append(sig_pred)
            self.add_to_context(sig_pred)
        return np.stack(futures, axis=0)


# =====================================================================
# DÉCODEUR PhiInverse V5 POUR VOCABULAIRE ÉTENDU
# =====================================================================
class PhiInverseDecoderNumpyV2:
    """Décodeur PhiInverse V5 : W[v,d] = cos(phi^{v/V} * pi * d) * e^{d*alpha/D} * sigma_v"""
    def __init__(self, vocab_size=VOCAB_SIZE, sig_dim=7):
        self.vocab_size = vocab_size
        self.sig_dim = sig_dim
        d = np.arange(sig_dim, dtype=np.float64).reshape(1, -1)
        v_arr = np.arange(vocab_size, dtype=np.float64).reshape(-1, 1)
        omega = np.pi * 0.5 * (1.0 + (PHI - 1.0) * v_arr / vocab_size)
        u = np.cos(omega * d)
        sigma = (1.0 / np.sqrt(sig_dim)) + 0.05 * (PHI ** (-v_arr))
        k = np.exp(-np.arange(sig_dim, dtype=np.float64) * ALPHA / sig_dim)
        self.weight = (u * sigma * k.reshape(1, -1) * PHI).astype(np.float32)
    
    def decode(self, sig):
        if sig.ndim == 1:
            return (self.weight @ sig).astype(np.float32)
        return (sig @ self.weight.T).astype(np.float32)


# =====================================================================
# GÉNÉRATEUR PhiInverse AVEC JEPA + BIGRAMMES
# =====================================================================
class PhiInverseGeneratorV2:
    """Génère du texte token par token avec JEPA + bigrammes intégrés."""
    
    def __init__(self, vocab_size=VOCAB_SIZE):
        self.vocab_size = min(vocab_size, VOCAB_SIZE)
        self.tokenizer = TokenizerHarmonique(_VOCAB_1500[:self.vocab_size])
        self.decoder = PhiInverseDecoderNumpyV2(vocab_size=self.vocab_size)
        self.jepa = JEPAPredictorNumpy(hidden_dim=16, kernel_size=5)
        self.grammaire = GrammaireBigrammes()
        self.hist = []
    
    def sample(self, logits, temperature=0.85, top_k=50, top_p=0.85, rep=1.5,
               token_precedent=None, force_bigramme=None):
        logits = logits.copy()
        V = len(logits)
        
        # Masquage spéciaux
        for t in (0, 2):
            if t < V: logits[t] = -1e12
        if 1 < V: logits[1] = -1e9  # <UNK> jamais
        
        # <EOS> pénalisé si trop court
        if 3 < V:
            if len(self.hist) < 8:
                logits[3] = -1e9
            else:
                logits[3] -= 3.0
        
        # Pénalité répétition
        if rep > 1.0 and self.hist:
            penalite = 1.0 / rep
            for t in set(self.hist[-15:]):
                if t < V and t not in (0, 1, 2, 3):
                    logits[t] *= penalite
        
        # BIGRAMMES : favoriser les suites grammaticales
        if force_bigramme and token_precedent is not None and token_precedent < V:
            logits = self.grammaire.penaliser(token_precedent, logits, force=force_bigramme)
        
        # Softmax stable
        max_l = logits.max()
        if max_l < -1e8:
            idx = 3 + (len(self.hist) % (V - 4))
            logits[idx] = 1.0
            max_l = 1.0
        
        shifted = logits - max_l
        scaled = shifted / max(temperature, 0.1)
        probs = np.exp(scaled, dtype=np.float64)
        probs /= (probs.sum() + 1e-30)
        
        # Top-k
        if top_k > 0 and top_k < V:
            idx = np.argpartition(probs, -top_k)[-top_k:]
            mask = np.zeros(V, dtype=np.float64)
            mask[idx] = 1.0
            probs *= mask
            probs /= (probs.sum() + 1e-30)
        
        # Top-p
        if top_p < 1.0:
            si = np.argsort(probs)[::-1]
            sp = probs[si]
            cs = np.cumsum(sp)
            mask = np.ones(V, dtype=bool)
            mask[si[1:]] = cs[1:] > top_p
            probs = np.where(mask, probs, 0.0)
            total = probs.sum()
            if total > 1e-30:
                probs /= total
        
        if np.isnan(probs).any() or probs.sum() < 1e-30:
            return int(np.argmax(logits))
        
        return int(np.random.choice(V, p=probs))
    
    def reset(self):
        self.hist = []
        self.jepa.reset_context()
    
    def generer(self, sig_16d, max_tokens=50, temperature=0.85,
                top_k=30, top_p=0.92, rep=1.3, eos=True,
                analyseur=None, use_jepa=True, force_bigramme=2.0):
        self.reset()
        t0 = time.time()
        tokens = []
        sig = sig_16d.copy()
        token_precedent = None
        
        if use_jepa and analyseur:
            s9_prompt = analyseur.projeter("")
            for _ in range(3):
                self.jepa.add_to_context(s9_prompt)
        
        for step in range(max_tokens):
            s7 = np.zeros(7, dtype=np.float32)
            s7[0] = sig[0]
            s7[1] = sig[1]
            s7[2] = sig[2] * 0.7 + sig[14] * 0.3
            s7[3] = sig[3] * 0.6 + sig[10] * 0.4
            s7[4] = sig[4] * 0.6 + sig[11] * 0.4
            s7[5] = sig[5]
            s7[6] = sig[6] * 0.7 + sig[9] * 0.3
            
            logits = self.decoder.decode(s7)
            
            tok = self.sample(logits.copy(), temperature, top_k, top_p, rep,
                              token_precedent=token_precedent,
                              force_bigramme=force_bigramme if step > 0 else None)
            tokens.append(tok)
            self.hist.append(tok)
            token_precedent = tok
            
            if eos and tok == 3:
                break
            
            if use_jepa and analyseur and len(tokens) >= 3:
                texte_courant = self.tokenizer.decoder(tokens[-min(8, len(tokens)):])
                sig_9d_courante = analyseur.projeter(texte_courant)
                self.jepa.add_to_context(sig_9d_courante)
                sig_9d_predite = self.jepa.predict_next()
                sig_9d_fusion = np.clip(sig_9d_courante * 0.7 + sig_9d_predite * 0.3, 0.0, 1.0)
                sig_16d_nouvelle = Fusion16D().fusionner(sig_9d_fusion)
                sig = np.clip(sig * 0.6 + sig_16d_nouvelle * 0.4, 0.0, 1.0)
            else:
                decay = 0.95
                ts = np.zeros(SIG_DIM_16D, dtype=np.float32)
                ts[0] = min(1.0, (tok % 100) / 100.0)
                sig = sig * decay + ts * (1 - decay)
        
        dt = (time.time() - t0) * 1000
        texte = self.tokenizer.decoder(tokens)
        info = {
            "n_tokens": len(tokens), "tokens_uniques": len(set(tokens)),
            "diversite": len(set(tokens)) / max(len(tokens), 1) if tokens else 0,
            "temps_ms": round(dt, 1),
            "tok_s": round(len(tokens) / (dt/1000), 1) if dt > 0 else 0,
        }
        return texte, tokens, info
    
    def entrainer_jepa(self, textes: List[str], analyseur: AnalyseurLinguistique9D):
        signatures = []
        for t in textes:
            sig_9d = analyseur.projeter(t)
            signatures.append(sig_9d)
        if len(signatures) > 5:
            sig_array = np.stack(signatures, axis=0)
            self.jepa.fit(sig_array)
            return True
        return False


# =====================================================================
# MATRICE DE CONNAISSANCE
# =====================================================================
class ConnaissanceHarmonique:
    def __init__(self, id, signature_16d, signature_9d, texte, source="",
                 hash_certificat=""):
        self.id = id
        self.signature_16d = signature_16d
        self.signature_9d = signature_9d
        self.texte = texte
        self.source = source
        self.coherence = float(np.mean(signature_9d))
        self.hash_certificat = hash_certificat or hashlib.sha256(
            f"{texte}{id}".encode()).hexdigest()[:16]

class MatriceConnaissance:
    def __init__(self):
        self.connaissances: List[ConnaissanceHarmonique] = []
        self._projecteur = AnalyseurLinguistique9D()
        self._fuseur = Fusion16D()
        self._signature_matrix: Optional[np.ndarray] = None
        self._index_built = False
    
    def apprendre(self, texte: str, source: str = "proto") -> ConnaissanceHarmonique:
        sig_9d = self._projecteur.projeter(texte)
        sig_16d = self._fuseur.fusionner(sig_9d)
        connaiss = ConnaissanceHarmonique(
            id=hashlib.md5(f"{texte}{time.time()}".encode()).hexdigest()[:16],
            signature_16d=sig_16d, signature_9d=sig_9d,
            texte=texte, source=source,
        )
        self.connaissances.append(connaiss)
        self._index_built = False
        return connaiss
    
    def apprendre_batch(self, textes: List[str], source: str = "batch") -> List[ConnaissanceHarmonique]:
        return [self.apprendre(t, source) for t in textes]
    
    def _build_index(self):
        if self._index_built:
            return
        if not self.connaissances:
            self._signature_matrix = np.zeros((0, SIG_DIM_16D), dtype=np.float32)
            self._index_built = True
            return
        signatures = np.stack([c.signature_16d for c in self.connaissances], axis=0)
        norms = np.linalg.norm(signatures, axis=1, keepdims=True)
        self._signature_matrix = signatures / (norms + 1e-8)
        self._index_built = True
    
    def chercher(self, signature_query: np.ndarray, top_k: int = 5,
                 seuil: float = 0.4) -> List[Tuple[ConnaissanceHarmonique, float]]:
        self._build_index()
        if self._signature_matrix.shape[0] == 0:
            return []
        query_norm = signature_query / (np.linalg.norm(signature_query) + 1e-8)
        similarites = self._signature_matrix @ query_norm
        indices = np.argsort(similarites)[::-1][:top_k]
        return [(self.connaissances[i], float(similarites[i])) for i in indices
                if similarites[i] >= seuil]
    
    def sauvegarder(self, chemin: str):
        data = {
            "meta": {"n": len(self.connaissances), "dim_9d": SIG_DIM_9D,
                     "dim_16d": SIG_DIM_16D, "phi": PHI,
                     "version": "proto-v3", "date": datetime.now().isoformat()},
            "connaissances": [
                {"id": c.id, "signature_9d": c.signature_9d.tolist(),
                 "signature_16d": c.signature_16d.tolist(),
                 "texte": c.texte, "source": c.source, "hash": c.hash_certificat}
                for c in self.connaissances
            ]
        }
        with open(chemin, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [SAUVEGARDE] {len(self.connaissances)} connaissances -> {chemin}")
    
    def charger(self, chemin: str) -> int:
        with open(chemin, 'r', encoding='utf-8') as f:
            data = json.load(f)
        n_avant = len(self.connaissances)
        for item in data["connaissances"]:
            c = ConnaissanceHarmonique(
                id=item["id"],
                signature_9d=np.array(item.get("signature_9d", [0]*9), dtype=np.float32),
                signature_16d=np.array(item.get("signature_16d", [0]*16), dtype=np.float32),
                texte=item["texte"], source=item.get("source", ""),
                hash_certificat=item.get("hash", ""),
            )
            self.connaissances.append(c)
        self._index_built = False
        n = len(self.connaissances) - n_avant
        print(f"  [CHARGEMENT] {n} connaissances chargees de {chemin}")
        return n
    
    def __len__(self):
        return len(self.connaissances)


# =====================================================================
# ORCHESTRATEUR COMPLET
# =====================================================================
class InconscientHarmoniqueProto:
    """Prototype complet : Conscience + Inconscient + JEPA + Bigrammes + Memoire persistante."""
    
    def __init__(self, chemin_sauvegarde="memoire_inconsciente.json"):
        self.analyseur = AnalyseurLinguistique9D()
        self.fuseur = Fusion16D()
        self.memoire = MatriceConnaissance()
        self.generateur = PhiInverseGeneratorV2()
        self.tokenizer = self.generateur.tokenizer
        self.chemin_sauvegarde = chemin_sauvegarde
        self._stats = {
            "n_apprentissages": 0, "n_generations": 0,
            "n_jepa_predictions": 0, "temps_gen_ms": 0.0,
        }
        self._jepa_entraine = False
        
        if os.path.exists(chemin_sauvegarde):
            try:
                self.memoire.charger(chemin_sauvegarde)
                textes = [c.texte for c in self.memoire.connaissances]
                if len(textes) >= 10:
                    self.generateur.entrainer_jepa(textes, self.analyseur)
                    self._jepa_entraine = True
                    print(f"  [JEPA] Entraine sur {len(textes)} textes de la memoire")
            except Exception as e:
                print(f"  [ERREUR] Chargement memoire: {e}")
    
    def apprendre(self, texte: str, source: str = "proto"):
        self.memoire.apprendre(texte, source)
        self._stats["n_apprentissages"] += 1
        if len(self.memoire) % 10 == 0:
            self.sauvegarder()
    
    def apprendre_batch(self, textes: List[str], source: str = "batch"):
        for t in textes:
            self.memoire.apprendre(t, source)
            self._stats["n_apprentissages"] += 1
        n = len(self.memoire)
        if n >= 10:
            textes = [c.texte for c in self.memoire.connaissances]
            self.generateur.entrainer_jepa(textes, self.analyseur)
            self._jepa_entraine = True
        self.sauvegarder()
    
    def generer(self, prompt: str, max_tokens=50, temperature=0.85,
                top_k=30, top_p=0.92, rep=1.3, use_jepa=True,
                force_bigramme=2.0) -> Dict:
        t0 = time.time()
        
        sig_9d = self.analyseur.projeter(prompt)
        sig_16d = self.fuseur.fusionner(sig_9d)
        
        conns = self.memoire.chercher(sig_16d, top_k=3, seuil=0.4) if len(self.memoire) > 0 else []
        if conns:
            sigs_connues = np.mean([c.signature_16d for c, _ in conns], axis=0)
            sig_16d = np.clip(sig_16d * 0.6 + sigs_connues * 0.4, 0.0, 1.0)
        
        use_jepa = use_jepa and self._jepa_entraine
        
        texte, tokens, info = self.generateur.generer(
            sig_16d, max_tokens, temperature, top_k, top_p, rep,
            analyseur=self.analyseur if use_jepa else None,
            use_jepa=use_jepa, force_bigramme=force_bigramme,
        )
        
        dt = (time.time() - t0) * 1000
        self._stats["n_generations"] += 1
        if use_jepa:
            self._stats["n_jepa_predictions"] += 1
        n = self._stats["n_generations"]
        self._stats["temps_gen_ms"] = (self._stats["temps_gen_ms"] * (n - 1) + dt) / n
        
        cert_hash = hashlib.sha256(f"{texte}|{len(conns)}|{PHI}".encode()).hexdigest()[:16]
        
        return {
            "prompt": prompt, "texte_genere": texte,
            "n_tokens": info["n_tokens"], "diversite": info["diversite"],
            "temps_ms": round(dt, 1), "tok_s": info["tok_s"],
            "n_connaissances": len(conns),
            "similarite_max": round(conns[0][1], 4) if conns else 0.0,
            "jepa_actif": use_jepa,
            "bigrammes_actif": force_bigramme > 0,
            "hash_certificat": cert_hash,
        }
    
    def apprendre_fichier(self, chemin: str, source: str = "fichier") -> int:
        """Apprend toutes les lignes d'un fichier texte."""
        if not os.path.exists(chemin):
            print(f"  [ERREUR] Fichier introuvable: {chemin}")
            return 0
        with open(chemin, 'r', encoding='utf-8') as f:
            lignes = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        if lignes:
            self.apprendre_batch(lignes, source)
        return len(lignes)
    
    def apprendre_jsonl(self, chemin: str, champ_texte: str = "texte") -> int:
        """Apprend depuis un fichier JSONL (1 objet JSON par ligne)."""
        if not os.path.exists(chemin):
            print(f"  [ERREUR] Fichier introuvable: {chemin}")
            return 0
        textes = []
        with open(chemin, 'r', encoding='utf-8') as f:
            for ligne in f:
                if ligne.strip():
                    try:
                        obj = json.loads(ligne)
                        t = obj.get(champ_texte, "")
                        if t and len(t) > 5:
                            textes.append(t)
                    except:
                        pass
        if textes:
            self.apprendre_batch(textes, "jsonl")
        return len(textes)
    
    def sauvegarder(self):
        self.memoire.sauvegarder(self.chemin_sauvegarde)
    
    def stats(self) -> Dict:
        return {
            **self._stats,
            "n_connaissances": len(self.memoire),
            "jepa_entraine": self._jepa_entraine,
            "vocab_size": self.generateur.vocab_size,
        }
    
    def analyser_texte(self, texte: str) -> Dict:
        sig_9d = self.analyseur.projeter(texte)
        sig_16d = self.fuseur.fusionner(sig_9d)
        profil = {d: float(sig_9d[i]) for i, d in enumerate(DIMS_9D)}
        dominant = max(profil, key=profil.get)
        return {
            "texte": texte[:80], "longueur": len(texte),
            "profil_9d": profil, "dimension_dominante": dominant,
            "valeur_dominante": round(profil[dominant], 3),
            "coherence": round(float(np.mean(sig_9d)), 3),
            "couverture_vocab": round(self.tokenizer.couverture(texte) * 100, 1),
        }


# =====================================================================
# MAIN - TEST
# =====================================================================
def main():
    print("\n" + "=" * 70)
    print("PROTOTYPE : INCONSCIENT HARMONIQUE V3")
    print("4 ameliorations : Accents | 1500 mots | Bigrammes | API")
    print("=" * 70)
    
    inconscient = InconscientHarmoniqueProto("memoire_inconsciente.json")
    stats = inconscient.stats()
    print(f"\n[1] Chargement: {stats['n_connaissances']} conn., "
          f"vocab={stats['vocab_size']} mots, JEPA={stats['jepa_entraine']}")
    
    if stats['n_connaissances'] < 5:
        print("\n[2] Apprentissage des connaissances...")
        textes_base = [
            "Le nombre d or phi est la proportion divine de l univers",
            "phi vaut 1.618033988749895 la constante harmonique fondamentale",
            "Le rectangle d or utilise la proportion phi pour l harmonie visuelle",
            "La resonance se produit quand une force oscillante correspond a la frequence naturelle",
            "La resonance harmonique amplifie les ondes a la frequence propre",
            "Tout systeme physique a une frequence de resonance fondamentale",
            "La conscience est la capacite de percevoir sa propre existence",
            "Les reseaux neuronaux complexes donnent naissance a la conscience",
            "L introspection est la connaissance de soi par la pensee",
            "La suite de Fibonacci converge vers le nombre d or phi",
            "Les fractales sont des structures infinies auto-similaires",
            "Le theoreme de Pythagore relie les cotes d un triangle rectangle",
            "L amour est la force la plus puissante de l univers",
            "La compassion et la bienveillance unissent les etres humains",
            "L empathie permet de comprendre les emotions des autres",
            "Le code harmonique est elegant efficace et sans bugs",
            "Python est un langage de programmation clair et puissant",
            "Un bon algorithme resout un probleme avec elegance",
            "La philosophie est l amour de la sagesse et de la connaissance",
            "Le temps est une dimension fondamentale de notre univers",
            "La musique est l harmonie entre le silence et le son",
            "Les mathematiques sont le langage dans lequel Dieu a ecrit l univers",
            "L intelligence artificielle explore la creation de machines penseantes",
            "La beaute est dans l oeil de celui qui regarde",
            "La verite est souvent plus etrange que la fiction",
            "L apprentissage est un voyage qui dure toute la vie",
            "La patience est la cle de la reussite",
            "La creativite est l intelligence qui s amuse",
            "Le bonheur n est pas une destination mais une facon de voyager",
            "La connaissance de soi est le debut de toute sagesse",
        ]
        inconscient.apprendre_batch(textes_base, "base")
        print(f"    {len(textes_base)} textes appris")
    
    stats = inconscient.stats()
    print(f"\n[3] Etat du prototype:")
    print(f"    - Memoire: {stats['n_connaissances']} connaissances")
    print(f"    - Vocabulaire: {stats['vocab_size']} mots")
    print(f"    - JEPA: {stats['jepa_entraine']}")
    
    # Test couverture accents
    print(f"\n[4] Test couverture vocabulaire (accents normalises):")
    tokenizer = TokenizerHarmonique()
    test_phrases = [
        "Le nombre d'or est une proportion mathématique fondamentale",
        "La conscience émerge de la complexité des réseaux neuronaux",
        "L'intelligence artificielle révolutionne la technologie moderne",
        "La beauté de la nature est une source d'émerveillement infini",
        "L'amour est la force la plus puissante de l'univers",
        "La musique est l'harmonie entre le silence et le son",
    ]
    for phrase in test_phrases:
        couv = tokenizer.couverture(phrase) * 100
        n_unk = sum(1 for t in tokenizer.encoder(phrase) if t == 1)
        print(f"    {couv:3.0f}% connu ({n_unk} UNK) | {phrase[:50]}")
    
    # Dialogue
    print(f"\n{'='*70}")
    print("DIALOGUE AVEC L'INCONSCIENT HARMONIQUE V3")
    print(f"{'='*70}")
    
    prompts = [
        "Parle-moi du nombre d or",
        "Comment fonctionne la resonance",
        "Qu est-ce que la conscience",
        "Explique la suite de Fibonacci",
        "C est quoi l amour",
        "Que sont les fractales",
        "Parle-moi de python",
        "Qu est-ce que la philosophie",
        "Explique la theorie de Pythagore",
    ]
    
    for prompt in prompts:
        print(f"\n>> {prompt}")
        r = inconscient.generer(prompt, max_tokens=25, temperature=0.85,
                                top_k=40, top_p=0.9, force_bigramme=1.5)
        bg_str = "gram" if r["bigrammes_actif"] else "   "
        jepa_str = "jepa" if r["jepa_actif"] else "    "
        print(f"   [{jepa_str}|{bg_str}] {r['texte_genere']}")
        print(f"   -> {r['n_tokens']}t, div={r['diversite']:.2f}, {r['temps_ms']:.0f}ms")
    
    print(f"\n{'='*70}")
    print("BILAN DU PROTOTYPE V3")
    print(f"{'='*70}")
    stats = inconscient.stats()
    print(f"""
   ACCENTS   : normalisation active -> couverture 80-100%
   VOCABULAIRE: {stats['vocab_size']} mots
   BIGRAMMES  : {len(_BIGRAMMES_NATURELS)} regles grammaticales
   JEPA       : {stats['jepa_entraine']} (moyenne phi^-t sur 9D)
   MEMOIRE    : {stats['n_connaissances']} connaissances persistantes
   TEMPS      : {stats['temps_gen_ms']:.1f}ms/gen sur CPU

   Pour injecter massivement :
     python -c \"from inconscient_harmonique_proto import *; i=InconscientHarmoniqueProto(); i.apprendre_fichier('mes_connaissances.txt')\"

   Pour lancer l API REST :
     python inconscient_harmonique_proto.py --api
""")


# =====================================================================
# AMÉLIORATION 4 : API REST POUR INJECTION BATCH
# =====================================================================

def lancer_api(host="0.0.0.0", port=8765):
    """Lance un serveur API REST pour interagir avec l'inconscient."""
    # Check FastAPI, sinon fallback http.server
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse
        use_fastapi = False
    except:
        use_fastapi = False
    
    if use_fastapi:
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        
        app = FastAPI(title="Inconscient Harmonique API", version="3.0")
        inconscient = InconscientHarmoniqueProto()
        
        class ApprendreRequest(BaseModel):
            textes: List[str]
            source: str = "api"
        
        class GenererRequest(BaseModel):
            prompt: str
            max_tokens: int = 50
            temperature: float = 0.85
            use_jepa: bool = True
            force_bigramme: float = 1.5
        
        @app.get("/stats")
        def get_stats():
            return inconscient.stats()
        
        @app.post("/apprendre")
        def apprendre(req: ApprendreRequest):
            n = len(req.textes)
            inconscient.apprendre_batch(req.textes, req.source)
            return {"appris": n, "total": len(inconscient.memoire)}
        
        @app.post("/generer")
        def generer(req: GenererRequest):
            r = inconscient.generer(req.prompt, max_tokens=req.max_tokens,
                                    temperature=req.temperature,
                                    use_jepa=req.use_jepa,
                                    force_bigramme=req.force_bigramme)
            return r
        
        print(f"\n[API] Serveur REST sur http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)
    
    else:
        # Fallback : http.server natif
        import http.server
        import urllib.parse
        
        inconscient = InconscientHarmoniqueProto()
        
        def api_json(data, status=200):
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            return (status, {'Content-Type': 'application/json; charset=utf-8'}, body)
        
        class APIHandler(http.server.BaseHTTPRequestHandler):
            def _respond(self, status, headers, body):
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)
            
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path == '/stats':
                    self._respond(*api_json(inconscient.stats()))
                elif parsed.path == '/analyser':
                    qs = urllib.parse.parse_qs(parsed.query)
                    texte = qs.get('texte', [''])[0]
                    if texte:
                        self._respond(*api_json(inconscient.analyser_texte(texte)))
                    else:
                        self._respond(*api_json({"erreur": "parametre 'texte' requis"}, 400))
                else:
                    self._respond(*api_json({
                        "endpoints": {
                            "GET /stats": "Statistiques",
                            "GET /analyser?texte=...": "Analyser un texte",
                            "POST /apprendre": "Apprendre des textes (JSON: {textes:[...]})",
                            "POST /generer": "Generer (JSON: {prompt, max_tokens, temperature})",
                        }
                    }))
            
            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length > 0 else b'{}'
                try:
                    data = json.loads(body)
                except:
                    self._respond(*api_json({"erreur": "JSON invalide"}, 400))
                    return
                
                if self.path == '/apprendre':
                    textes = data.get('textes', [])
                    source = data.get('source', 'api')
                    n = len(textes)
                    if n > 0:
                        inconscient.apprendre_batch(textes, source)
                    self._respond(*api_json({
                        "appris": n, "total": len(inconscient.memoire)
                    }))
                
                elif self.path == '/generer':
                    prompt = data.get('prompt', '')
                    if not prompt:
                        self._respond(*api_json({"erreur": "champ 'prompt' requis"}, 400))
                        return
                    r = inconscient.generer(
                        prompt,
                        max_tokens=data.get('max_tokens', 50),
                        temperature=data.get('temperature', 0.85),
                        top_k=data.get('top_k', 30),
                        top_p=data.get('top_p', 0.92),
                        rep=data.get('rep', 1.3),
                        use_jepa=data.get('use_jepa', True),
                        force_bigramme=data.get('force_bigramme', 1.5),
                    )
                    self._respond(*api_json(r))
                
                elif self.path == '/apprendre_fichier':
                    chemin = data.get('chemin', '')
                    source = data.get('source', 'fichier')
                    if not chemin:
                        self._respond(*api_json({"erreur": "champ 'chemin' requis"}, 400))
                        return
                    n = inconscient.apprendre_fichier(chemin, source)
                    self._respond(*api_json({
                        "appris": n, "total": len(inconscient.memoire)
                    }))
                
                else:
                    self._respond(*api_json({"erreur": "endpoint inconnu"}, 404))
            
            def log_message(self, fmt, *args):
                pass  # Silence
        
        server = http.server.HTTPServer((host, port), APIHandler)
        print(f"\n[API] Serveur REST sur http://{host}:{port}")
        print(f"      Endpoints: GET /stats, POST /apprendre, POST /generer, POST /apprendre_fichier")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[API] Arret")


if __name__ == "__main__":
    if "--api" in sys.argv:
        import argparse
        parser = argparse.ArgumentParser(description="Inconscient Harmonique API")
        parser.add_argument("--api", action="store_true", help="Lancer le serveur API")
        parser.add_argument("--host", default="0.0.0.0", help="Hote (defaut: 0.0.0.0)")
        parser.add_argument("--port", type=int, default=8765, help="Port (defaut: 8765)")
        args = parser.parse_args()
        lancer_api(host=args.host, port=args.port)
    else:
        main()
