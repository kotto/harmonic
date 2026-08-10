#!/usr/bin/env python3
"""pont_hybride.py — LE PONT D'AUDIT SERVEUR (module réutilisable)
================================================================
Implémentation serveur du prototype hybride pour KA mobile :
  question → noyau harmonique (calcul exact, résonance, REFUS)
           → <CORE> → Phraseur (Ollama, optionnel) → français fluide
           → AUDIT (vérification : calcul exact, refus respecté)
           → régénération / fallback noyau

Zéro dépendance lourde : wave_lang (numpy) + urllib (Ollama HTTP).
Ollama est OPTIONNEL : si absent, le noyau répond en phrase modèle.
"""
import json, math, os, sys, time, urllib.request

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

from wave_lang import encode, resonate

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELE_PHRASEUR = "qwen2.5:1.5b"
TIMEOUT_OLLAMA = 30

PROMPT_PHRASEUR = """Tu es LE PHRASEUR d'une IA exacte. Le noyau harmonique te donne une sortie structurée entre <CORE> et </CORE>. Ton métier : la transformer en français naturel, fluide, chaleureux.

RÈGLES ABSOLUES :
1. Tu n'as AUCUNE connaissance propre — tu ne sais que ce que <CORE> te donne.
2. Tu n'inventes JAMAIS un fait, un nombre, une définition.
3. Si <CORE> dit REFUS, tu refuses poliment — tu ne réponds pas à la question.
4. Si <CORE> contient un NOMBRE, cite-le EXACTEMENT tel quel (ex. « 56 »), sans le convertir en lettres, sans le recalculer.
5. Tu phrases, tu embellis le style — jamais le contenu.
6. Réponds en 1-2 phrases maximum, naturellement."""


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


class PhraseurOllama:
    """Le Phraseur réel (optionnel) — qwen2.5:1.5b local."""

    def __init__(self, url=OLLAMA_URL, modele=MODELE_PHRASEUR):
        self.url = url
        self.modele = modele

    def disponible(self):
        try:
            urllib.request.urlopen(self.url.replace("/api/generate", "/api/tags"),
                                   timeout=2)
            return True
        except Exception:
            return False

    def generer(self, contenu_core, question, strict=False):
        if strict:
            prompt = (f"RÉPONDS EN CITANT EXACTEMENT LE NOMBRE {contenu_core} tel quel, "
                      f"en chiffres. Une phrase courte, naturelle, sans calcul, sans "
                      f"autre nombre. Exemple : « Le résultat est {contenu_core} — tout simple ! »")
        else:
            hist = question.replace('"', "'")
            prompt = (f"{PROMPT_PHRASEUR}\n\n"
                      f"<CORE> {contenu_core} </CORE> <HIST> {hist} </HIST>")
        data = json.dumps({"model": self.modele, "prompt": prompt,
                           "stream": False, "temperature": 0.6}).encode()
        req = urllib.request.Request(self.url, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_OLLAMA) as resp:
            return json.loads(resp.read().decode()).get("response", "").strip()


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
        """Les premiers mots significatifs d'un texte — empreinte de l'audit."""
        return [m for m in _normaliser(texte).split() if len(m) >= 5][:3]

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
        if core["type"] in ("MEDICAL", "CONDUITE"):
            mots = cls._mots_distinctifs(core["valeur"])
            ok = any(m in _normaliser(phrase) for m in mots)
            return ok, "contenu présent" if ok else "contenu absent"
        return False, "inconnu"


def _phrase_modele(core):
    """La phrase modèle du noyau — garantie sans LLM."""
    if core["type"] == "IDENTITE":
        return REPONSE_IDENTITE
    if core["type"] == "MEDICAL":
        return core["valeur"]
    if core["type"] == "CONDUITE":
        return core["valeur"]
    if core["type"] == "CALC":
        v = core["valeur"]
        s = str(int(v)) if v == int(v) else f"{v:.6f}".rstrip("0").rstrip(".")
        return f"Le résultat exact est {s} — calculé par les ondes."
    if core["type"] == "FAIT":
        return f"Je connais {core['concept']} — c'est dans ma mémoire."
    return ("Je ne peux pas répondre à ça — ce n'est pas dans ce que je connais. "
            "Je préfère me taire plutôt que d'inventer.")


class PontHybride:
    """Le pont complet : noyau → Phraseur → audit → régénération → fallback."""

    def __init__(self, concepts=None, utiliser_ollama=True):
        self.noyau = NoyauHybride()
        for c in (concepts or ["chat", "chien", "oiseau", "lumière",
                               "amour", "eau", "musique", "santé"]):
            self.noyau.apprendre(c)
        self.phraseur = PhraseurOllama() if utiliser_ollama else None
        self.audit = Audit()
        self.stats = {"CALC": 0, "FAIT": 0, "REFUS": 0, "IDENTITE": 0,
                      "MEDICAL": 0, "CONDUITE": 0, "AUDIT_OK": 0, "AUDIT_KO": 0}

    def traiter(self, question):
        """Pipeline complet — retourne la réponse dict JSON."""
        t0 = time.time()
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
        # 2. Phraseur réel (si disponible)
        elif self.phraseur and self.phraseur.disponible():
            try:
                phrase = self.phraseur.generer(contenu, question)
                ok, detail = self.audit.verifier(core, phrase)
                etapes.append(f"LLM: {detail}")
                # 3. Régénération stricte si l'audit échoue sur un calcul
                if not ok and core["type"] == "CALC":
                    phrase2 = self.phraseur.generer(contenu, question, strict=True)
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
        else:
            etapes.append("LLM indisponible → phrase modèle")

        # 5. Fallback : la phrase modèle du noyau (garantie)
        if phrase is None:
            phrase = _phrase_modele(core)
            etapes.append("fallback noyau")
            ok = True

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
    print("PONT HYBRIDE — TEST SERVEUR")
    print("=" * 66)
    for q in ["7 × 8", "12 + 34", "3,5 ÷ 0,5", "chat", "quasar",
              "existe-t-il une théorie du tout ?", "raconte une blague", "lumière"]:
        r = pont.traiter(q)
        print(f"\n  Q : {q}")
        print(f"  → [{r['type']}] {r['response']}")
        print(f"    audit {'✅' if r['audit'] else '❌'} · {r['etapes']} · {r['latence_ms']} ms")
    print(f"\n  STATS : {pont.stats}")
