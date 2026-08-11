#!/usr/bin/env python3
"""pont_hybride.py — LE PONT D'AUDIT SERVEUR (module réutilisable)
================================================================
Implémentation serveur du prototype hybride pour KA mobile, dans le cadre
ARCHITECTURE_MEMOIRE_EMULATION_HYBRIDE (3 étages de l'ordinateur harmonique) :

  Étages 1-2 · MÉMOIRE + ÉMULATION → le NOYAU décide le contenu (<CORE>) :
              résonance, calcul exact par ondes, corpus médical, REFUS.
  Étage 3 · HYBRIDE → la couche langage : PhraseurInterne (règles,
              déterministe) puis PhraseurExterne (Ollama local, gratuit)
              puis AUDIT (calcul exact, refus respecté) puis fallback noyau.

Chaîne : question → noyau → <CORE> → interne/externe → AUDIT → réponse.
La mémoire vit dans le noyau (étage 1), PAS dans le LLM : le phraseur ne
fait que phraser ce que le noyau a décidé — zéro connaissance propre.

Zéro dépendance lourde : wave_lang (numpy) + urllib (Ollama HTTP).
Ollama est OPTIONNEL : si absent, le PhraseurInterne répond (déterministe).
"""
import json, math, os, re, sys, time, urllib.request

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

from wave_lang import encode, resonate
from pont_phraseur_externe import PhraseurExterne, _charger_cle_env
from pont_phraseur_interne import PhraseurInterne, STYLES as STYLES_INTERNES

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELE_PHRASEUR = "qwen2.5:7b"   # préférence ; repli automatique (voir externe)
TIMEOUT_OLLAMA = 30


_PATTERNS_IDENTITE = [
    "qui es-tu", "qui es tu", "qui etes-vous", "qui êtes-vous", "tu es qui",
    "qu'est-ce que tu es", "quest-ce que tu es", "qu est-ce que tu es", "ton nom", "ton identite",
    "comment tu t'appelles", "comment tu t appelles", "comment vous appelez",
    "what are you", "who are you", "what is your name",
    "es-tu une ia", "es tu une ia", "es-tu un robot", "es tu un robot",
    "tu es quoi", "vous etes quoi",
]

REPONSE_IDENTITE = (
    "Je suis KA (Knowledge Amplifier) — une intelligence artificielle harmonique. "
    "Je ne suis pas un LLM classique : je fonctionne sur le principe ondulatoire, "
    "chaque connaissance est une onde, chaque raisonnement une interférence. "
    "Zéro paramètre entraîné, zéro hallucination, déterminisme total — "
    "la même question donne toujours la même réponse. "
    "Je calcule par les ondes, je mémorise par le noyau doré, "
    "et je refuse de répondre quand je ne sais pas."
)

# 🩺 CONNAISSANCES MÉDICALES ESSENTIELLES (dérivées du corpus médical)
# « c'est quoi le diabète ? » → définition du corpus, pas une génération LLM
FAITS_MEDICAUX = {
    "diabète": ("Le diabète de type 2 se définit par une glycémie à jeun ≥ 1,26 g/L "
                "(7,0 mmol/L) à 2 reprises, OU une HbA1c ≥ 6,5 %, OU une glycémie "
                "aléatoire ≥ 2 g/L avec symptômes."),
    "diabete": ("Le diabète de type 2 se définit par une glycémie à jeun ≥ 1,26 g/L "
                "(7,0 mmol/L) à 2 reprises, OU une HbA1c ≥ 6,5 %, OU une glycémie "
                "aléatoire ≥ 2 g/L avec symptômes."),
    "hypertension": ("L'hypertension artérielle se définit par une pression ≥ 140/90 mmHg "
                     "à 2 consultations séparées. Objectif : < 140/90 (< 130/80 si diabète "
                     "ou insuffisance rénale chronique)."),
    "asthme": ("L'asthme chronique est une inflammation chronique des voies aériennes "
               "avec bronchoconstriction réversible. Il se distingue de la crise aiguë, "
               "qui nécessite un traitement immédiat."),
    "epilepsie": ("L'épilepsie est une affection neurologique caractérisée par des crises "
                  "récidivantes non provoquées. Prévalence élevée en Afrique (cysticercose, "
                  "paludisme, traumatismes)."),
    "drepanocytose": ("La drépanocytose est une maladie génétique de l'hémoglobine (HbS). "
                      "La forme homozygote SS est la forme majeure. Fréquente en Afrique "
                      "(1/4 porteurs sains dans certaines régions)."),
    "insuffisance cardiaque": ("L'insuffisance cardiaque est l'incapacité du cœur à assurer "
                               "un débit suffisant. Causes : HTA, cardiopathie ischémique, "
                               "valvulopathie, cardiomyopathie."),
    "paludisme": ("Le paludisme est une maladie parasitaire transmise par la piqûre du "
                  "moustique anophèle. La prévention repose sur la moustiquaire imprégnée, "
                  "le traitement préventif et le diagnostic précoce."),
    "fièvre": ("La fièvre se définit par une température axillaire ≥ 37,5 °C ou rectale "
               "≥ 38 °C. Toute fièvre chez un enfant de moins de 3 mois est une urgence."),
    "fièvre jaune": ("La fièvre jaune est une maladie virale : fièvre brutale, frissons, "
                     "ictère et hémorragies possibles. URGENCE VITALE — Hospitalisation. "
                     "Pas de traitement spécifique. Vaccination préventive."),
    "convulsions fébriles": ("Convulsion généralisée associée à la fièvre chez l'enfant "
                             "de 6 mois à 5 ans, sans infection du système nerveux central "
                             "et sans antécédent épileptique. Conduite : position latérale, "
                             "ne rien mettre en bouche."),
    "gastro": ("La gastro-entérite associe diarrhée, vomissements, nausées et douleurs "
               "abdominales, avec fièvre modérée possible. Gravité modérée. Conduite : "
               "réhydratation (soluté oral), repas légers."),
    "covid": ("La COVID-19 associe fièvre, toux sèche, fatigue, perte d'odorat (anosmie) "
              "et de goût (agueusie), essoufflement possible. Gravité élevée. Conduite : "
              "isolement immédiat, test PCR."),
}

# 🚨 CONDUITES D'URGENCE (dérivées du corpus : gravité + conduite_à_tenir + symptômes)
CONDUITES_URGENCE = {
    "avc": ("⚠️ URGENCE VITALE — Appeler le 15 IMMÉDIATEMENT. Chaque minute compte. "
            "Signes : paralysie du visage, faiblesse d'un bras, trouble de la parole."),
    "infarctus": ("⚠️ URGENCE VITALE — Appeler le 15 (SAMU) IMMÉDIATEMENT. "
                  "Ne pas conduire. Rester au repos. "
                  "Signes : douleur thoracique, essoufflement, sueurs froides."),
    "appendicite": ("⚠️ URGENCE VITALE — Appeler le 15. Ne pas manger ni boire. "
                    "Risque de péritonite. Signes : douleur abdominale droite, fièvre modérée."),
    "dengue": ("Consultation. Paracétamol uniquement — pas d'aspirine ni d'ibuprofène. "
               "Hydratation. Signes d'alarme : douleurs abdominales, vomissements, "
               "saignements → urgence."),
    "covid": ("Isolement immédiat. Test PCR. Consultation si essoufflement."),
    "rhume": ("Repos, hydratation, lavage de nez. Pas d'antibiotiques — c'est viral."),
    "gastro": ("Réhydratation (soluté oral). Repas légers. "
               "Consultation si signes de déshydratation (48 h si pas d'amélioration)."),
    "fièvre": ("Rechercher paludisme (TDR), infection urinaire, méningite selon les signes. "
               "Paracétamol 10-15 mg/kg si fièvre élevée. "
               "Fièvre chez un enfant < 3 mois = urgence."),
    "convulsions fébriles": ("Position latérale de sécurité. Ne rien mettre en bouche. "
                             "Si la crise dure plus de 5 minutes : diazépam IR 0,5 mg/kg. "
                             "Évoquer la méningite si 1re crise, signes méningés "
                             "ou récupération lente."),
}

_ALIASES_CONDUITE = {
    "crise cardiaque": "infarctus",
    "attaque cerebrale": "avc",
    "coronavirus": "covid",
    "covid 19": "covid",
    "covid19": "covid",
    "convulsions": "convulsions fébriles",
    "gastro enterite": "gastro",
}

_PATTERNS_MEDICAUX = [
    ("c'est quoi", "diabète"), ("c est quoi", "diabète"), ("qu'est-ce que", "diabète"),
    ("quest ce que", "diabète"), ("c'est quoi", "hypertension"), ("c est quoi", "hypertension"),
    ("c'est quoi", "asthme"), ("c est quoi", "asthme"), ("c'est quoi", "epilepsie"),
    ("c est quoi", "epilepsie"), ("qu'est-ce que", "epilepsie"), ("quest ce que", "epilepsie"),
    ("c'est quoi", "drepanocytose"), ("c est quoi", "drepanocytose"),
    ("qu'est-ce que", "drepanocytose"), ("quest ce que", "drepanocytose"),
    ("c'est quoi", "insuffisance cardiaque"), ("c est quoi", "insuffisance cardiaque"),
    ("qu'est-ce que", "insuffisance cardiaque"), ("quest ce que", "insuffisance cardiaque"),
    ("qu'est-ce que", "l'hypertension"), ("quest ce que", "l'hypertension"),
    ("qu'est-ce que", "l'asthme"), ("quest ce que", "l'asthme"),
    ("c'est quoi", "paludisme"), ("c est quoi", "paludisme"),
    ("qu'est-ce que", "le paludisme"), ("quest ce que", "le paludisme"),
    ("c'est quoi", "le diabete"), ("c est quoi", "le diabete"),
    ("c'est quoi", "le paludisme"), ("c est quoi", "le paludisme"),
    ("qu'est-ce que", "le diabete"), ("quest ce que", "le diabete"),
    # ⚠️ fièvre jaune AVANT fièvre (ordre = priorité de correspondance)
    ("c'est quoi", "fièvre jaune"), ("c est quoi", "fièvre jaune"),
    ("qu'est-ce que", "fièvre jaune"), ("quest ce que", "fièvre jaune"),
    ("c'est quoi", "la fièvre"), ("c est quoi", "la fièvre"),
    ("qu'est-ce que", "la fièvre"), ("quest ce que", "la fièvre"),
    ("c'est quoi", "convulsions fébriles"), ("c est quoi", "convulsions fébriles"),
    ("c'est quoi", "gastro"), ("c est quoi", "gastro"),
    ("c'est quoi", "covid"), ("c est quoi", "covid"),
    ("qu'est-ce que", "covid"), ("quest ce que", "covid"),
]


def _sans_article(maladie):
    """Retire les articles : 'l'hypertension' → 'hypertension'."""
    for art in ("l'", "le ", "la ", "les "):
        if maladie.lower().startswith(art):
            return maladie[len(art):]
    return maladie


def _normaliser(texte):
    """Normalise : apostrophes, tirets et ACCENTS → forme simple.
    ('qu'est-ce que' == 'qu est ce que' · 'épilepsie' == 'epilepsie')"""
    t = texte.lower().replace("'", " ").replace("-", " ")
    for acc, sans in [("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"),
                      ("à", "a"), ("â", "a"), ("ä", "a"),
                      ("î", "i"), ("ï", "i"), ("ô", "o"), ("ö", "o"),
                      ("ù", "u"), ("û", "u"), ("ü", "u"), ("ç", "c"), ("œ", "oe")]:
        t = t.replace(acc, sans)
    return t


def _est_question_medicale(question):
    q = _normaliser(question)
    for prefixe, maladie in _PATTERNS_MEDICAUX:
        p = _normaliser(prefixe)
        m = _normaliser(maladie)
        if p in q and m in q:
            return _sans_article(maladie)
    # questions directes : « le diabète ? » « diabete c'est quoi »
    for maladie in FAITS_MEDICAUX:
        m = _normaliser(maladie)
        if m in q and any(p in q for p in ("quoi", "c est", "quest ce", "definir", "explique")):
            return maladie
    return None


def _est_question_conduite(question):
    """« que faire en cas d'AVC ? » → la conduite du corpus, pas une invention."""
    q = _normaliser(question)
    if not any(m in q for m in ("que faire", "en cas", "conduite",
                                "que dois", "comment reagir")):
        return None
    for maladie in CONDUITES_URGENCE:
        if _normaliser(maladie) in q:
            return maladie
    for alias, maladie in _ALIASES_CONDUITE.items():
        if alias in q:
            return maladie
    return None


def _est_question_identite(question):
    q = question.lower().strip()
    return any(p in q for p in _PATTERNS_IDENTITE)


class NoyauHybride:
    """Le noyau : calcul par ondes, résonance, refus calibré."""

    def __init__(self, seuil_resonance=0.30):
        self.seuil = seuil_resonance
        self.concepts = {}

    def apprendre(self, nom, repetitions=4):
        self.concepts[nom] = encode(nom)

    def calculer(self, expr):
        expr = expr.replace(",", ".").replace(" ", "")
        for op, fn in [("+", lambda a, b: a + b),
                       ("×", lambda a, b: a * b),
                       ("x", lambda a, b: a * b),
                       ("*", lambda a, b: a * b),
                       ("-", lambda a, b: a - b),
                       ("÷", lambda a, b: a / b),
                       ("/", lambda a, b: a / b)]:
            if op in expr:
                p = expr.split(op)
                if len(p) == 2:
                    try:
                        return fn(float(p[0]), float(p[1]))
                    except ValueError:
                        pass
        return None

    def resonner(self, question):
        psi_q = encode(question)
        meilleur, score = None, 0.0
        for nom, psi in self.concepts.items():
            s = resonate(psi_q, psi)
            if s > score:
                score, meilleur = s, nom
        return meilleur, score

    def repondre(self, question):
        if _est_question_identite(question):
            return {"type": "IDENTITE"}
        conduite = _est_question_conduite(question)
        if conduite:
            return {"type": "CONDUITE", "concept": conduite,
                    "valeur": CONDUITES_URGENCE[conduite]}
        maladie = _est_question_medicale(question)
        if maladie:
            return {"type": "MEDICAL", "concept": maladie,
                    "valeur": FAITS_MEDICAUX[maladie]}
        r = self.calculer(question)
        if r is not None:
            return {"type": "CALC", "valeur": r}
        nom, score = self.resonner(question)
        if score >= self.seuil:
            return {"type": "FAIT", "concept": nom, "score": score}
        return {"type": "REFUS", "score": score}


_UNITES = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit",
           "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze",
           "seize", "dix-sept", "dix-huit", "dix-neuf"]
_DIZAINES = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante",
             "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]


def _en_lettres(n):
    if n == 0:
        return "zéro"
    if n < 20:
        return _UNITES[n]
    if n < 100:
        d, u = divmod(n, 10)
        if d == 7:
            return "soixante-" + _UNITES[10 + u] if u else "soixante-dix"
        if d == 9:
            return "quatre-vingt-" + _UNITES[10 + u] if u else "quatre-vingt"
        return _DIZAINES[d] + ("-" + _UNITES[u] if u else "")
    c, r = divmod(n, 100)
    return ("cent" + (" " + _en_lettres(r) if r else ""))


# Le vocabulaire distinctif de l'identité (forme normalisée) — l'audit
# vérifie qu'au moins un mot est présent : le LLM paraphrase légitimement
# (« IA harmonique » doit passer), mais une réponse hors-sujet doit être
# rejetée. Découvert par le test global : cette règle manquait.
_MOTS_IDENTITE = ["harmonique", "hallucination", "intelligence", "ondulatoire",
                  "ondes", "determinisme", "interference", "connaissance",
                  "knowledge", "amplifier"]


class Audit:
    """Vérifie que le Phraseur n'a rien inventé."""

    _MOTS_REFUS = ["sais pas", "connais", "pas de réponse", "préfère", "limite",
                   "n'ai pas", "ne sais", "dépasse", "hors de", "je ne peux",
                   "pas de réponses", "peux pas", "ne suis pas", "ne veux pas",
                   "capable", "envie", "du genre", "désolé", "ne peux pas",
                   "peut pas", "pas capable"]

    @classmethod
    def _contient_nombre(cls, phrase, v):
        s = str(int(v)) if v == int(v) else f"{v:.4f}".rstrip("0").rstrip(".")
        if s in phrase.replace(",", "."):
            return True
        if v == int(v) and 0 <= v < 1000:
            lettres = _en_lettres(int(v))
            parties = lettres.split("-")
            return parties[0] in phrase.lower() and parties[-1] in phrase.lower()
        return False

    @classmethod
    def _mots_distinctifs(cls, texte):
        """Les premiers mots significatifs d'un texte — empreinte de l'audit.
        La ponctuation est retirée (« (knowledge » → « knowledge »)."""
        return [re.sub(r"[^a-z0-9-]", "", m)
                for m in _normaliser(texte).split() if len(m) >= 5][:3]

    @classmethod
    def verifier(cls, core, phrase):
        if core["type"] == "REFUS":
            ok = any(m in phrase.lower() for m in cls._MOTS_REFUS)
            return ok, "refus respecté" if ok else "le Phraseur a répondu !"
        if core["type"] == "CALC":
            ok = cls._contient_nombre(phrase, core["valeur"])
            return ok, "nombre exact" if ok else f"nombre attendu : {core['valeur']}"
        if core["type"] == "FAIT":
            ok = core["concept"] in phrase.lower()
            return ok, "concept présent" if ok else "concept absent"
        if core["type"] == "IDENTITE":
            # au moins un mot du vocabulaire d'identité doit être présent
            ok = any(m in _normaliser(phrase) for m in _MOTS_IDENTITE)
            return ok, "identité présente" if ok else "identité absente"
        if core["type"] in ("MEDICAL", "CONDUITE"):
            mots = cls._mots_distinctifs(core["valeur"])
            ok = any(m in _normaliser(phrase) for m in mots)
            return ok, "contenu présent" if ok else "contenu absent"
        return False, "inconnu"


# ══════════════════════════════════════════════════════════════════
# VOCALISATION — texte écrit → texte PARLÉ (pour Piper / Web Speech)
# ══════════════════════════════════════════════════════════════════
# Le synthétiseur lit mal les symboles réels du corpus (≥, →, %, ⚠️, —,
# g/L, 140/90…). vocaliser() transforme un texte KA en texte lisible à
# voix haute : le CONTENU reste identique, seuls les symboles deviennent
# des mots. Utilisé par le style="vocal" (serveur) et par ka_index.html
# avant la synthèse (mobile).
_UNITES_VOCALES = [
    # Ordre important : formes longues AVANT formes courtes (mmol/L avant L).
    # Espace initial : « 500mg » → « 500 milligrammes » (unité = mot séparé).
    ("mmol/L", " millimoles par litre"),
    ("mg/dL", " milligrammes par décilitre"),
    ("mg/dl", " milligrammes par décilitre"),
    ("mg/kg", " milligrammes par kilogramme"),
    ("g/L", " grammes par litre"),
    ("mmHg", " millimètres de mercure"),
    ("HbA1c", " hémoglobine glyquée"),
    ("ml/kg", " millilitres par kilogramme"),
    ("ml", " millilitres"),
    ("mg", " milligrammes"),
    ("kg", " kilogrammes"),
    ("cm", " centimètres"),
    ("°C", " degrés"),
    ("°", " degrés"),
]

_FREQUENCES_VOCALES = [
    ("/min", " par minute"), ("/j", " par jour"), ("/an", " par an"),
    ("/h", " par heure"), ("/kg", " par kilogramme"),
    ("/semaine", " par semaine"), ("/mois", " par mois"),
]

# Plages Unicode des émojis et symboles décoratifs (⚠️ ✅ ❌ ✓ …)
_RE_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2190-\u21FF]")


def vocaliser(texte):
    """Texte KA → texte PARLÉ : les symboles du corpus deviennent des mots."""
    if not texte:
        return texte
    t = texte
    # 1. Unités et termes médicaux (ils contiennent /, °, %… → à faire AVANT)
    for forme, lecture in _UNITES_VOCALES:
        t = t.replace(forme, lecture)
    # 2. Flèches, tirets longs, comparaisons, pourcentages
    t = t.replace("→", ", ").replace("—", ", ").replace("–", ", ")
    t = t.replace("≥", "supérieur ou égal à").replace("≤", "inférieur ou égal à")
    t = t.replace("≈", "environ").replace("±", "environ")
    t = t.replace("%", " pour cent").replace("&", " et ").replace("=", " égale ")
    # 3. « 24h/24 » → « 24 heures sur 24 » ; « 7j/7 » → « 7 jours sur 7 » ;
    #    « 140/90 » → « 140 sur 90 » ; « 6h » → « 6 heures »
    t = re.sub(r"(\d+)h/(\d+)", r"\1 heures sur \2", t)
    t = re.sub(r"(\d+)j/(\d+)", r"\1 jours sur \2", t)
    t = re.sub(r"(\d+)/(\d+)", r"\1 sur \2", t)
    t = re.sub(r"(\d+)h\b", r"\1 heures", t)
    t = re.sub(r"(\d+)j\b", r"\1 jours", t)
    # 4. « 2x/j » → « 2 fois par jour » (AVANT les fréquences)
    t = re.sub(r"(\d+)\s*x\s*/\s*j", r"\1 fois par jour", t)
    for forme, lecture in _FREQUENCES_VOCALES:
        t = t.replace(forme, lecture)
    t = t.replace("/", " par ")
    # 5. Intervalles et opérateurs : « 40-60 » → « de 40 à 60 », « > » → « plus de »
    t = re.sub(r"(\d+)\s*-\s*(\d+)", r"de \1 à \2", t)
    t = t.replace(">", " plus de ").replace("<", " moins de ")
    t = t.replace("×", " fois ").replace("÷", " divisé par ").replace("+", " plus ")
    # 6. Parenthèses → virgules (le contenu est conservé : précision médicale)
    t = t.replace("(", ", ").replace(")", "")
    # 7. Markdown et émojis
    t = t.replace("**", "").replace("`", "").replace("#", "")
    t = _RE_EMOJI.sub("", t)
    # 8. Nettoyage : doubles espaces, virgules orphelines
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r",\s*,", ",", t)
    return t.strip()


# Artefacts de formatage que le LLM laisse parfois (markdown, LaTeX simple) —
# retirés APRÈS audit : le contenu a été vérifié, on nettoie seulement la forme.
_ARTEFACTS_LLM = [
    ("**", ""), ("`", ""),
    ("\\(", ""), ("\\)", ""), ("\\[", ""), ("\\]", ""),
    ("\\times", "×"), ("\\cdot", "·"), ("\\div", "÷"),
    ("\\approx", "≈"), ("\\,", " "), ("\\;", " "), ("\\ ", ""), ("\\", ""),
]


def _nettoyer_llm(phrase):
    """Retire les artefacts markdown/LaTeX d'une phrase LLM déjà auditée.
    Jamais de contenu ajouté — uniquement la forme."""
    t = phrase
    for a, b in _ARTEFACTS_LLM:
        t = t.replace(a, b)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def _phrase_modele(core, style=None):
    """La phrase modèle du noyau — garantie sans LLM.
    Délègue au PhraseurInterne (déterministe, style demandé)."""
    return PhraseurInterne().phraser(core, style)


class PontHybride:
    """Le pont complet : noyau → Phraseur → audit → régénération → fallback."""

    def __init__(self, concepts=None, utiliser_ollama=True):
        self.noyau = NoyauHybride()
        for c in (concepts or ["chat", "chien", "oiseau", "lumière",
                               "amour", "eau", "musique", "santé"]):
            self.noyau.apprendre(c)
        # La couche langage de l'étage 3 : Ollama local (le chemin réel,
        # modèle préféré 7b/8b) ; DeepSeek en secours de test si pas d'Ollama ;
        # ni l'un ni l'autre → PhraseurInterne (déterministe).
        self.phraseur = PhraseurExterne(modele=MODELE_PHRASEUR) if utiliser_ollama else None
        self.audit = Audit()
        self.stats = {"CALC": 0, "FAIT": 0, "REFUS": 0, "IDENTITE": 0,
                      "MEDICAL": 0, "CONDUITE": 0, "AUDIT_OK": 0, "AUDIT_KO": 0}

    STYLES = STYLES_INTERNES

    def traiter(self, question, style=None):
        """Pipeline complet — retourne la réponse dict JSON.
        Chaîne (étage 3) : noyau → <CORE> → PhraseurInterne (toujours là,
        déterministe) → PhraseurExterne (Ollama, si dispo) → AUDIT → fallback.
        Styles : conversationnel · vocal (lisible à voix haute) · bref ·
        pédagogique. MEDICAL/CONDUITE = corpus exact, jamais de LLM."""
        t0 = time.time()
        style_eff = (style or "conversationnel").lower()
        if style_eff == "pedagogique":
            style_eff = "pédagogique"
        if style_eff == "elegant":
            style_eff = "élégant"
        if style_eff not in self.STYLES:
            style_eff = "conversationnel"
        # Le style élégant = conversationnel POUR LE PHRASEUR (le FT n'est pas
        # entraîné dessus) ; l'élégance est apportée APRÈS par le polish exclusif
        style_phraseur = "conversationnel" if style_eff == "élégant" else style_eff
        core = self.noyau.repondre(question)
        self.stats[core["type"]] += 1
        contenu = self._contenu_core(core)
        etapes = []
        phrase, ok = None, False

        # 1. Le contenu médical ne passe JAMAIS par le LLM : texte exact du corpus.
        #    (une conduite hallucinée peut tuer — on ne génère pas, on cite)
        if core["type"] in ("MEDICAL", "CONDUITE"):
            phrase = _phrase_modele(core)
            etapes.append("corpus → phrase exacte (pas de LLM)")
            ok = True
        # 2. Chaîne de fournisseurs de langage (DeepSeek d'abord, Ollama ensuite)
        elif self.phraseur and self.phraseur.disponible():
            try:
                phrase = self.phraseur.generer(contenu, question, style=style_phraseur)
                ok, detail = self.audit.verifier(core, phrase)
                etapes.append(f"LLM ({self.phraseur.actif}): {detail}")
                # 3. Régénération stricte si l'audit échoue sur un calcul
                if not ok and core["type"] == "CALC":
                    phrase2 = self.phraseur.generer(contenu, question,
                                                    strict=True, style=style_phraseur)
                    ok2, detail2 = self.audit.verifier(core, phrase2)
                    etapes.append(f"régénéré: {detail2}")
                    if ok2:
                        phrase, ok, detail = phrase2, True, detail2
                    else:
                        phrase = None
                # 4. Tout autre échec d'audit (FAIT…) :
                #    on ne garde JAMAIS une phrase non vérifiée → fallback noyau
                elif not ok:
                    etapes.append("audit refusé → phrase modèle")
                    phrase = None
            except Exception as e:
                etapes.append(f"LLM erreur: {e}")
                phrase = None
            # Nettoyage des artefacts (markdown/LaTeX) — phrase LLM déjà auditée
            if phrase is not None:
                phrase = _nettoyer_llm(phrase)
                etapes.append("nettoyage LLM")
        else:
            etapes.append("LLM indisponible → phrase interne")

        # 5. Fallback : le PhraseurInterne (garanti, déterministe, style demandé)
        if phrase is None:
            phrase = _phrase_modele(core, style_eff)
            etapes.append("fallback phraseur interne")
            ok = True

        # 6. Style ÉLÉGANT — demande EXCLUSIVE de style au LLM
        #    (llm/deepseek_styler.py) : reformulation sans ajouter un seul
        #    fait, puis AUDIT re-vérifié ; échec → phrase d'origine.
        #    JAMAIS sur MEDICAL/CONDUITE : le corpus ne se reformule pas.
        if (style_eff == "élégant" and core["type"] not in ("MEDICAL", "CONDUITE")
                and self.phraseur and phrase):
            polie, applique = self._polir_elegan(phrase, question)
            if not applique:
                etapes.append("polish élégant indisponible → phrase d'origine")
            elif polie == phrase:
                # le styler a jugé la phrase déjà parfaite (règle 7 du module)
                etapes.append("polish élégant: déjà élégant (inchangée)")
            else:
                ok_polie, detail_polie = self.audit.verifier(core, polie)
                if ok_polie:
                    phrase = polie
                    etapes.append(f"polish élégant: {detail_polie}")
                else:
                    etapes.append(f"polish refusé par l'audit ({detail_polie}) "
                                  "→ phrase d'origine")

        # 7. Style vocal : le synthétiseur lit la réponse → symboles en mots
        if style_eff == "vocal" and phrase:
            phrase = vocaliser(phrase)
            etapes.append("vocalisation TTS")

        if ok:
            self.stats["AUDIT_OK"] += 1
        else:
            self.stats["AUDIT_KO"] += 1

        return {
            "question": question,
            "type": core["type"],
            "valeur": core.get("valeur"),
            "concept": core.get("concept"),
            "response": phrase,
            "audit": ok,
            "etapes": etapes,
            "latence_ms": int((time.time() - t0) * 1000),
        }

    def _polir_elegan(self, phrase, question):
        """Demande EXCLUSIVE de style au LLM : le module llm/deepseek_styler.py
        reformule le style sans ajouter un seul fait. Clé chargée depuis .env.
        Retourne (phrase_polie, applique) — applique=False si le styler est
        indisponible (clé absente, désactivé) ; jamais d'exception."""
        try:
            import os as _os
            _os.environ.setdefault("DEEPSEEK_API_KEY",
                                   _charger_cle_env("DEEPSEEK_API_KEY") or "")
            if not _os.environ.get("DEEPSEEK_API_KEY"):
                return phrase, False
            from llm.deepseek_styler import DeepSeekStyleFormatter
            styler = DeepSeekStyleFormatter()
            if not styler.enabled:
                return phrase, False
            return styler.polish(phrase, question), True
        except Exception:
            return phrase, False

    def _contenu_core(self, core):
        if core["type"] == "IDENTITE":
            return "FAIT: KA est une IA harmonique — zéro hallucination"
        if core["type"] == "MEDICAL":
            return "FAIT: " + core["valeur"]
        if core["type"] == "CALC":
            v = core["valeur"]
            return str(int(v)) if v == int(v) else f"{v:.6f}".rstrip("0").rstrip(".")
        if core["type"] == "FAIT":
            return f"FAIT: {core['concept']}"
        return "REFUS"


if __name__ == "__main__":
    pont = PontHybride()
    print("=" * 66)
    print("PONT HYBRIDE — TEST SERVEUR (étages 1-2 : noyau · étage 3 : langage)")
    print("=" * 66)
    for q in ["7 × 8", "12 + 34", "3,5 ÷ 0,5", "chat", "quasar",
              "existe-t-il une théorie du tout ?", "raconte une blague", "lumière"]:
        r = pont.traiter(q)
        print(f"\n  Q : {q}")
        print(f"  → [{r['type']}] {r['response']}")
        print(f"    audit {'✅' if r['audit'] else '❌'} · {r['etapes']} · {r['latence_ms']} ms")
    print("\n" + "=" * 66)
    print("LES STYLES DU PHRASEUR INTERNE (étage 3, déterministe)")
    print("=" * 66)
    for q in ["7 × 8", "c'est quoi le diabète ?", "quasar", "chat"]:
        print(f"\n  Q : {q}")
        for s in pont.STYLES:
            r = pont.traiter(q, style=s)
            print(f"    [{s:15s}] {r['response'][:95]}")
    print(f"\n  STATS : {pont.stats}")
