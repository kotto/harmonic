"""
🌊 surface_grammar.py — Grammaire ondulatoire de surface (la FORME apprise)
=============================================================================
Port auto-contenu vers ka_server (depuis HARMONIC AI V 5).

La FORME apprise d'un LLM, sans LLM : une distribution de surface est un
champ de phases, appris par RENFORCEMENT D'AMPLITUDE sur les seules
réponses vérifiées (jamais sur du contenu non validé).

Trois briques :
  A. MORPHOLOGIE      — conjugaison 3e pers. sing/plur + participe passé,
                       accord genre/nombre. La grammaire est une DONNÉE.
  B. COMPOSITION      — syntagmes (sujet / prédicat / complément) composés
                       par cohérence de phase, pondérés par l'amplitude apprise.
  C. RENFORCEMENT (E) — SurfaceMemory : α par structure, persisté en JSON.
                       r > 0.7 → α += η ; r < 0.3 → α −= η.

Contrat inchangé : la surface ne produit JAMAIS un mot hors des faits.
Seuls les mots fonctionnels (articles, prépositions, auxiliaires) sont
ajoutés — le sujet, le prédicat et le complément viennent du fait vérifié.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# A. MORPHOLOGIE
# ═══════════════════════════════════════════════════════════════════════════════

# Verbes irréguliers : (singulier, pluriel, participe passé, infinitif)
_IRREGULAR_VERBS = {
    'est': ('est', 'sont', 'été', 'être'), 'etre': ('est', 'sont', 'été', 'être'),
    'a': ('a', 'ont', 'eu', 'avoir'), 'avoir': ('a', 'ont', 'eu', 'avoir'),
    'fait': ('fait', 'font', 'fait', 'faire'), 'faire': ('fait', 'font', 'fait', 'faire'),
    'peut': ('peut', 'peuvent', 'pu', 'pouvoir'), 'pouvoir': ('peut', 'peuvent', 'pu', 'pouvoir'),
    'veut': ('veut', 'veulent', 'voulu', 'vouloir'), 'vouloir': ('veut', 'veulent', 'voulu', 'vouloir'),
    'doit': ('doit', 'doivent', 'dû', 'devoir'), 'devoir': ('doit', 'doivent', 'dû', 'devoir'),
    'sait': ('sait', 'savent', 'su', 'savoir'), 'savoir': ('sait', 'savent', 'su', 'savoir'),
    'va': ('va', 'vont', 'allé', 'aller'), 'aller': ('va', 'vont', 'allé', 'aller'),
    'vient': ('vient', 'viennent', 'venu', 'venir'), 'venir': ('vient', 'viennent', 'venu', 'venir'),
    'tient': ('tient', 'tiennent', 'tenu', 'tenir'), 'tenir': ('tient', 'tiennent', 'tenu', 'tenir'),
    'prend': ('prend', 'prennent', 'pris', 'prendre'), 'prendre': ('prend', 'prennent', 'pris', 'prendre'),
    'met': ('met', 'mettent', 'mis', 'mettre'), 'mettre': ('met', 'mettent', 'mis', 'mettre'),
    'dit': ('dit', 'disent', 'dit', 'dire'), 'dire': ('dit', 'disent', 'dit', 'dire'),
    'voit': ('voit', 'voient', 'vu', 'voir'), 'voir': ('voit', 'voient', 'vu', 'voir'),
    'croit': ('croit', 'croient', 'cru', 'croire'), 'croire': ('croit', 'croient', 'cru', 'croire'),
    'boit': ('boit', 'boivent', 'bu', 'boire'), 'boire': ('boit', 'boivent', 'bu', 'boire'),
    'recoit': ('reçoit', 'reçoivent', 'reçu', 'recevoir'), 'recevoir': ('reçoit', 'reçoivent', 'reçu', 'recevoir'),
    'connait': ('connaît', 'connaissent', 'connu', 'connaître'),
    'nait': ('naît', 'naissent', 'né', 'naître'),
    'vit': ('vit', 'vivent', 'vécu', 'vivre'), 'vivre': ('vit', 'vivent', 'vécu', 'vivre'),
    'suit': ('suit', 'suivent', 'suivi', 'suivre'), 'suivre': ('suit', 'suivent', 'suivi', 'suivre'),
    'ecrit': ('écrit', 'écrivent', 'écrit', 'écrire'), 'ecrire': ('écrit', 'écrivent', 'écrit', 'écrire'),
    'lit': ('lit', 'lisent', 'lu', 'lire'), 'lire': ('lit', 'lisent', 'lu', 'lire'),
    'conduit': ('conduit', 'conduisent', 'conduit', 'conduire'),
    'produit': ('produit', 'produisent', 'produit', 'produire'),
    'traduit': ('traduit', 'traduisent', 'traduit', 'traduire'),
    'construit': ('construit', 'construisent', 'construit', 'construire'),
    'reduit': ('réduit', 'réduisent', 'réduit', 'réduire'),
    'introduit': ('introduit', 'introduisent', 'introduit', 'introduire'),
    'permet': ('permet', 'permettent', 'permis', 'permettre'),
    'transmet': ('transmet', 'transmettent', 'transmis', 'transmettre'),
    'commet': ('commet', 'commettent', 'commis', 'commettre'),
    'promet': ('promet', 'promettent', 'promis', 'promettre'),
    'soumet': ('soumet', 'soumettent', 'soumis', 'soumettre'),
    'admet': ('admet', 'admettent', 'admis', 'admettre'),
    'remet': ('remet', 'remettent', 'remis', 'remettre'),
    'decouvre': ('découvre', 'découvrent', 'découvert', 'découvrir'),
    'offre': ('offre', 'offrent', 'offert', 'offrir'),
    'ouvre': ('ouvre', 'ouvrent', 'ouvert', 'ouvrir'),
    'souffre': ('souffre', 'souffrent', 'souffert', 'souffrir'),
    'couvre': ('couvre', 'couvrent', 'couvert', 'couvrir'),
    'apparait': ('apparaît', 'apparaissent', 'apparu', 'apparaître'),
    'disparait': ('disparaît', 'disparaissent', 'disparu', 'disparaître'),
    'est ne': ('est né', 'sont nés', 'né', 'naître'),
    'a ete': ('a été', 'ont été', 'été', 'être'),
    'est utilise': ('est utilisé', 'sont utilisés', 'utilisé', 'utiliser'),
    'est lie': ('est lié', 'sont liés', 'lié', 'lier'),
    'est cause': ('est causé', 'sont causés', 'causé', 'causer'),
    'est utilisee': ('est utilisée', 'sont utilisées', 'utilisée', 'utiliser'),
    'est liee': ('est liée', 'sont liées', 'liée', 'lier'),
    'est transmis': ('est transmis', 'sont transmis', 'transmis', 'transmettre'),
    'se divise': ('se divise', 'se divisent', 'divisé', 'diviser'),
    'se fait': ('se fait', 'se font', 'fait', 'faire'),
}

# Verbes réguliers en -er
_REGULAR_ER = {
    'cause', 'provoque', 'regule', 'contient', 'entraine', 'protege',
    'transporte', 'secrete', 'synthetise', 'neutralise', 'favorise',
    'libere', 'stimule', 'bloque', 'administre', 'compose', 'forme',
    'constitue', 'divise', 'augmente', 'empeche', 'elimine', 'absorbe',
    'digere', 'filtre', 'purifie', 'mesure', 'realise', 'influence',
    'detecte', 'observe', 'etudie', 'traite', 'diagnostique', 'decrit',
    'explique', 'montre', 'indique', 'suggere', 'confirme', 'demontre',
    'affirme', 'semble', 'reste', 'existe', 'touche', 'affecte', 'evite',
    'recommande', 'utilise', 'concerne', 'vise', 'regarde', 'decoule',
    'contribue', 'participe', 'aide', 'demarre', 'debute', 'commence',
    'cesse', 'continue', 'poursuit', 'aboutit', 'mene', 'genere',
    'suscite', 'souligne', 'precise', 'ajoute', 'rappelle', 'signale',
    'note', 'mentionne', 'cite', 'evoque', 'resume', 'rassemble',
    'regroupe', 'classe', 'appelle', 'fixe', 'limite', 'autorise',
    'oblige', 'incite', 'pousse', 'conseille', 'exige', 'demande',
    'expose', 'determine', 'prouve', 'finance', 'recense', 'implique',
    'reunit', 'presente', 'controle', 'permet', 'orbite', 'gravite',
    'tourne', 'relie', 'separe', 'porte', 'fournit', 'donne',
}

# Verbes réguliers en -ir
_REGULAR_IR = {
    'finit', 'choisit', 'reussit', 'remplit', 'agit', 'reagit', 'saisit',
    'garantit', 'investit', 'etablit', 'definit', 'elargit', 'grandit',
    'vieillit', 'guerit', 'reunit',
}

# Verbes réguliers en -re
_REGULAR_RE = {
    'repond', 'attend', 'entend', 'descend', 'vend', 'perd', 'mord',
    'tord', 'fend', 'fond', 'correspond', 'rend', 'defend', 'pretend',
    'etend', 'suspend', 'depend',
}

# Participe passé : accord genre/nombre
_PARTICIPLE_ACCORD = {
    'é': ('ée', 'és', 'ées'), 'i': ('ie', 'is', 'ies'),
    'u': ('ue', 'us', 'ues'), 's': ('se', 's', 'ses'),
}

# Lexique de genre minimal (auto-contenu — pas de dépendance french_corrector)
GENDER = {
    'lumiere': 'f', 'terre': 'f', 'eau': 'f', 'france': 'f', 'cellule': 'f',
    'proteine': 'f', 'insuline': 'f', 'hormone': 'f', 'enzyme': 'f',
    'matiere': 'f', 'energie': 'f', 'information': 'f', 'molecule': 'f',
    'substance': 'f', 'maladie': 'f', 'bacterie': 'f',
    'étoile': 'f', 'etoile': 'f', 'galaxie': 'f', 'planete': 'f', 'ville': 'f',
    'soleil': 'm', 'cœur': 'm', 'coeur': 'm', 'cerveau': 'm', 'corps': 'm',
    'sang': 'm', 'gène': 'm', 'gene': 'm', 'atome': 'm', 'électron': 'm',
    'electron': 'm', 'cristal': 'm', 'metal': 'm', 'gaz': 'm',
    'acide': 'm', 'glucose': 'm', 'sucre': 'm', 'chocolat': 'm',
    'restaurant': 'm', 'telephone': 'm', 'ordinateur': 'm',
    'nombre': 'm', 'onde': 'f',
}


def _gender_of(noun: str) -> str:
    """Genre d'un nom (lexique local, défaut masculin)."""
    return GENDER.get(noun.lower().rstrip('sx'), GENDER.get(noun.lower(), 'm'))


def conjugate(sing: str) -> Tuple[str, str, str]:
    """(singulier, pluriel, participe passé) pour un verbe à la 3e personne."""
    v = sing.strip().lower()
    if v in _IRREGULAR_VERBS:
        s, p, pp, _ = _IRREGULAR_VERBS[v]
        return s, p, pp
    if v.endswith('e'):
        base = v[:-1]
        return f'{base}e', f'{base}ent', f'{base}é'
    if v.endswith('it'):
        base = v[:-2]
        return f'{base}it', f'{base}issent', f'{base}i'
    if v.endswith(('d', 't')):
        return v, f'{v}ent', f'{v}u'
    return v, v, v


def participle_agree(pp: str, gender: str = 'm', number: str = 's') -> str:
    """Accord du participe passé : (genre, nombre)."""
    if gender == 'm' and number == 's':
        return pp
    for key, forms in _PARTICIPLE_ACCORD.items():
        if pp.endswith(key):
            idx = (1 if gender == 'f' else 0) + (1 if number == 'p' else 0)
            return pp[:-len(key)] + forms[min(idx, 3)]
    return pp


# ═══════════════════════════════════════════════════════════════════════════════
# B. COMPOSITION PAR PHASE — syntagmes
# ═══════════════════════════════════════════════════════════════════════════════

_SUJET_SN = {
    'm': ['le {s}', '{S}', 'ce {s}', 'un {s}'],
    'f': ['la {s}', '{S}', 'cette {s}', 'une {s}'],
}
_SUJET_PLURIEL = {
    'm': ['les {s}', '{S}', 'ces {s}'],
    'f': ['les {s}', '{S}', 'ces {s}'],
}
_EXPANSIONS = {
    'est': ['', ' bien ', ' en réalité ', ' notamment '],
    'sont': ['', ' bien ', ' en réalité '],
    'permet': ['', ' notamment ', ' en particulier '],
    'permet de': ['', ' notamment ', ' en particulier '],
    'contient': ['', ' notamment ', ' également '],
    'regule': ['', ' notamment ', ' en particulier '],
    'produit': ['', ' notamment ', ' également '],
    'cause': ['', ' notamment ', ' en particulier '],
    'provoque': ['', ' notamment ', ' en particulier '],
    'transporte': ['', ' notamment ', ' également '],
    'synthetise': ['', ' notamment ', ' également '],
    'traite': ['', ' notamment ', ' en particulier '],
    'filtre': ['', ' notamment ', ' également '],
}

# Relations « verbales » connues — normalisées (sans accents) pour le matching
# contre le vocabulaire de memory_first qui strip les accents.
KNOWN_VERB_RELATIONS = {
    'est', 'est un', 'est une', 'a', 'a pour', 'a pour vitesse',
    'cause', 'provoque', 'contient', 'permet', 'produit', 'traite',
    'filtre', 'regule', 'synthetise', 'transporte',
    'est cause par', 'est causé par', 'est cause', 'est causé',
    'est compose de', 'est composée de', 'contient',
    'a ete invente par', 'a été inventé par',
    'a ete decouvert par', 'a été découvert par',
}


def _normalize_ascii(text: str) -> str:
    """Version ASCII d'un texte (sans accents) pour matching tolérant."""
    import unicodedata
    return unicodedata.normalize('NFD', text.lower()) \
        .encode('ascii', 'ignore').decode('ascii')


def _phase(seed: str, salt: str = '') -> float:
    """Phase déterministe φ-spacée dans [0, 1)."""
    h = hashlib.sha256(f"{seed}|{salt}".encode()).digest()
    return int.from_bytes(h[:4], 'big') / 2**32


def _pick_weighted(options: List[str], seed: str, salt: str,
                   memory: 'SurfaceMemory', used: set) -> str:
    """Choix d'un syntagme : phase pondérée par l'amplitude apprise.
    Biais par défaut : défini (le/la) > démonstratif > indéfini > forme nue.
    L'amplitude apprise (feedback) peut surpasser ces biais avec le temps."""
    if not options:
        return ''
    scores = []
    for i, opt in enumerate(options):
        if opt in used:
            continue
        amplitude = memory.amplitude(f'surface|{opt}')
        phase_v = _phase(seed, salt + str(i))
        # Biais article : défini +0.50, démonstratif +0.30, indéfini +0.15,
        # forme nue 0.00. Le feedback appris (amplitude ±0.2) peut dépasser
        # ces constantes mais pas au démarrage à froid.
        opt_clean = opt.strip().format(s='', S='')  # strip template vars
        if any(opt_clean.startswith(p) for p in ('le ', 'la ', 'les ')):
            default_bias = 0.50
        elif any(opt_clean.startswith(p) for p in ('ce ', 'cette ', 'ces ')):
            default_bias = 0.30
        elif any(opt_clean.startswith(p) for p in ('un ', 'une ', 'des ')):
            default_bias = 0.15
        else:
            default_bias = 0.0
        scores.append((amplitude + phase_v * 0.05 + default_bias, opt))
    if not scores:
        return options[0]
    scores.sort(key=lambda x: -x[0])
    return scores[0][1]


# ═══════════════════════════════════════════════════════════════════════════════
# C. RENFORCEMENT DE LA FORME (E)
# ═══════════════════════════════════════════════════════════════════════════════

class SurfaceMemory:
    """
    α par structure de surface, persisté en JSON.
    r > 0.7 renforce les structures utilisées, r < 0.3 les affaiblit.
    """

    ETA = 0.2
    THRESH_HIGH = 0.7
    THRESH_LOW = 0.3

    def __init__(self, path: Optional[Path] = None):
        self.path = path or (Path(__file__).resolve().parent.parent
                             / 'data' / 'surface_memory.json')
        self._amplitudes: Dict[str, float] = {}
        self._last_used: List[str] = []
        self.load()

    def load(self):
        try:
            if self.path.exists():
                self._amplitudes = json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:
            self._amplitudes = {}

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._amplitudes, ensure_ascii=False,
                                            indent=1), encoding='utf-8')
        except Exception:
            pass

    def amplitude(self, key: str) -> float:
        return self._amplitudes.get(key, 0.0)

    def record(self, keys: List[str]):
        self._last_used = list(keys)

    @property
    def last_used(self) -> List[str]:
        return self._last_used

    def reinforce(self, keys: List[str], delta: float = None):
        delta = delta or self.ETA
        for k in keys:
            self._amplitudes[k] = self._amplitudes.get(k, 0.0) + delta
        self.save()

    def weaken(self, keys: List[str], delta: float = None):
        delta = delta or self.ETA
        for k in keys:
            self._amplitudes[k] = max(0.0, self._amplitudes.get(k, 0.0) - delta)
        self.save()

    def apply_feedback(self, rating: float, keys: Optional[List[str]] = None) -> Dict:
        keys = keys if keys is not None else self._last_used
        if rating >= self.THRESH_HIGH and keys:
            self.reinforce(keys)
            return {'decision': 'reinforce', 'keys': keys, 'eta': self.ETA}
        if rating <= self.THRESH_LOW and keys:
            self.weaken(keys)
            return {'decision': 'weaken', 'keys': keys, 'eta': self.ETA}
        return {'decision': 'neutral', 'keys': keys}

    def stats(self) -> Dict:
        return {'structures_apprises': len(self._amplitudes),
                'top': sorted(self._amplitudes.items(), key=lambda x: -x[1])[:8]}


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION DE SURFACE
# ═══════════════════════════════════════════════════════════════════════════════

# Radicaux d'articles (mots fonctionnels) à ne pas empiler
_ARTICLE_RE = re.compile(
    r'^(?:le |la |les |l[\'’]|un |une |des |du |ce |cette |ces |mon |ton |son |ma |ta |sa |mes |tes |ses '
    r'|notre |votre |leur |nos |vos |leurs |au |aux |du |des )', re.IGNORECASE)


def _has_article(noun: str) -> bool:
    """Vrai si le nom commence déjà par un déterminant."""
    return bool(_ARTICLE_RE.match(noun))


def _strip_article(noun: str) -> str:
    """Retire le déterminant initial (pour éviter « le le chat »)."""
    return _ARTICLE_RE.sub('', noun, count=1).strip()


def _pluralize_noun(noun: str, gender: str) -> str:
    """Pluriel simple des noms."""
    n = noun.rstrip('sx') if noun.endswith(('s', 'x')) else noun
    if n.endswith('al'):
        return n[:-2] + 'aux'
    if n.endswith(('eau', 'au', 'eu')):
        return n + 'x'
    if n.endswith(('s', 'x', 'z')):
        return n
    return n + 's'


def surface(fact: Tuple[str, str, str], mem: Optional[SurfaceMemory] = None,
            plural_subject: bool = False, variation: int = 0) -> Tuple[str, List[str]]:
    """
    Génère une phrase pour un fait vérifié (triplet sujet/relation/objet).
    Retourne (phrase, clés_de_structure).
    """
    if mem is None:
        mem = SurfaceMemory(path=None)

    s, r, o = str(fact[0]).strip(), str(fact[1]).strip(), str(fact[2]).strip()
    if not s:
        return '', []

    gender = _gender_of(s)
    used = set()

    # Si le sujet a déjà un déterminant → l'utiliser tel quel (évite « le le chat »)
    if _has_article(s):
        sn = s[0].upper() + s[1:] if s[0].islower() else s
    # Noms propres (capitalisés mais sans article) → pas d'article
    elif s[:1].isupper() and not plural_subject:
        sn = s
    elif plural_subject:
        sn_opts = _SUJET_PLURIEL.get(gender, _SUJET_PLURIEL['m'])
        sn = _pick_weighted(sn_opts, f'{s}|{o}', f'sn{variation}', mem, used)
        sn = sn.format(s=_pluralize_noun(s, gender), S=s.capitalize())
    else:
        sn_opts = _SUJET_SN.get(gender, _SUJET_SN['m'])
        # Biais par défaut — préférer le défini (le/la) pour les noms
        # communs, puis le démonstratif (ce/cette), puis l'indéfini,
        # puis la forme nue (la plus froide).
        if gender == 'f':
            bias_opts = ['la {s}', 'cette {s}', 'une {s}', '{S}']
        else:
            bias_opts = ['le {s}', 'ce {s}', 'un {s}', '{S}']
        sn = _pick_weighted(bias_opts, f'{s}|{o}', f'sn{variation}', mem, used)
        sn = sn.format(s=s, S=s.capitalize())
    used.add(sn)

    r_key = r.lower().strip()
    expansions = _EXPANSIONS.get(r_key, [''])
    expansion = _pick_weighted(expansions, f'{r}|{o}', f'exp{variation}', mem, used)
    used.add(f'exp|{expansion}' if expansion else 'exp|')

    co = o.rstrip('.!?;:')
    # Normaliser les espaces (l'expansion peut contenir des espaces de bord)
    phrase = f'{sn} {r}{expansion} {co}'.strip()
    phrase = re.sub(r'\s+', ' ', phrase) + '.'
    if phrase.startswith('le ') or phrase.startswith('la '):
        phrase = phrase[0].upper() + phrase[1:]

    keys = [f'surface|{sn}', f'pred|{r}', f'exp|{expansion}', f'obj|{co[:30]}']
    mem.record(keys)
    return phrase, keys


def paraphrase(fact: Tuple[str, str, str], n: int = 3) -> List[str]:
    """n surfaces différentes pour le même fait (même ψ_sens)."""
    out = []
    mem = SurfaceMemory(path=None)
    for i in range(n):
        phrase, _ = surface(fact, mem, variation=i)
        if phrase and phrase not in out:
            out.append(phrase)
        if len(out) >= n:
            break
    return out


def fact_from_text(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Extrait un triplet (sujet, relation, objet) d'une phrase factuelle simple.
    Le découpage utilise des frontières de mot (word boundaries) pour éviter
    les faux positifs (« restaurant » contient « est », « habite » contient « a »).
    """
    t = text.strip().rstrip('.')

    relations = [
        'est causé par', 'est cause par', 'est composé de', 'est composée de',
        'est un', 'est une', 'contient', 'provoque', 'cause',
        'permet', 'produit', 'est', 'a',
    ]

    for rel in relations:
        pattern = re.compile(r'(?<![A-Za-zÀ-ÿ])' + re.escape(rel) +
                             r'(?![A-Za-zÀ-ÿ])')
        m = pattern.search(t)
        if m:
            sujet = t[:m.start()].strip()
            objet = t[m.end():].strip()
            if sujet and objet:
                return (sujet, rel, objet)
    return None


def phrase_fact(sujet: str, relation: str, objet: str,
                mem: Optional[SurfaceMemory] = None) -> str:
    """
    Phrase naturelle à partir d'un triplet (sujet, relation, objet).
    Fallback SÛR : si la relation n'est pas un verbe connu, on garde le
    triplet brut (« X conduit Y » ne devient pas une phrase cassée).
    """
    r_norm = _normalize_ascii(relation).strip()
    # Matching tolérant : la relation stockée peut être « a ete invente par »
    # alors que KNOWN_VERB_RELATIONS contient « a été inventé par »
    is_known = (r_norm in KNOWN_VERB_RELATIONS)
    if not is_known:
        # Chercher aussi dans les valeurs normalisées
        for k in KNOWN_VERB_RELATIONS:
            if r_norm == _normalize_ascii(k):
                is_known = True
                break
    
    if not is_known:
        o_clean = objet.strip().rstrip('.!?;:')
        return f"{sujet} {relation} {o_clean}.".strip()

    phrase, _ = surface((sujet, relation, objet.rstrip('.!?;:')), mem)
    return phrase if phrase else f"{sujet} {relation} {objet.rstrip('.!?;:')}.".strip()


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=== MORPHOLOGIE ===")
    for v in ['cause', 'finit', 'attend', 'est', 'permet', 'produit', 'transmet']:
        s, p, pp = conjugate(v)
        print(f'  {v:12s} → sing={s:12s} plur={p:14s} pp={pp}')
    print("  pp accord: causé(f,p) =", participle_agree('causé', 'f', 'p'))

    print("\n=== PHRASE_FACT (fallback sûr) ===")
    for fact in [
        ('lumiere', 'est une', 'onde electromagnetique'),
        ('soleil', 'est', 'une etoile'),
        ('COVID-19', 'conduite', 'Isolement immédiat. Test PCR.'),
        ('phi', 'est', 'nombre d or'),
    ]:
        print('  •', phrase_fact(*fact))

    print("\n=== VARIÉTÉ (paraphrase) ===")
    fait = ('le diabete de type 1', 'est cause par', 'une deficience en insuline')
    for p in paraphrase(fait, 3):
        print('  •', p)
