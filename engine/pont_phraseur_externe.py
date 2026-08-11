#!/usr/bin/env python3
"""pont_phraseur_externe.py — LA COUCHE LANGAGE EXTERNE (étage 3 · hybride)
====================================================================
Le fournisseur de langage INTERCHANGEABLE du pont d'audit, dans le cadre
ARCHITECTURE_MEMOIRE_EMULATION_HYBRIDE (3 étages) :

  Étages 1-2 (mémoire + émulation)  →  le NOYAU décide le contenu (<CORE>)
  Étage 3 (hybride)  →  ce module : la CHAÎNE de fournisseurs de langage,
                        phraseur UNIQUEMENT (style), jamais de connaissance.

Chaîne (dans l'ordre) :
  1. Ollama local (gratuit, privé, aucune donnée ne sort) — le chemin RÉEL ;
  2. DeepSeek (API cloud, clé DEEPSEEK_API_KEY du .env) — le SECOURS de TEST
     UNIQUEMENT : ajouté seulement si Ollama est ABSENT (machine sans Ollama).
     Si Ollama est présent, on sert et on teste sur Ollama — DeepSeek ne
     reçoit jamais de trafic de production.
  3. Aucun → disponible() == False → le pont bascule sur le PhraseurInterne
     (déterministe), jamais sur une réponse non vérifiée.

Ce module ne fait que phraser : il reçoit <CORE> + la question, il rend du
français naturel. Rien d'autre. La mémoire, le calcul, la vérité : ailleurs.

Le MÉDICAL/CONDUITE ne passe JAMAIS ici : le pont le coupe en amont.
(Avertissement honnête : DeepSeek est un cloud — les questions non-médicales
et le <CORE> quittent le serveur. Ollama local reste le choix privé.)
"""
import json, os, sys, time, urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
TIMEOUT_OLLAMA = 30

# Le phraseur fine-tuné (interne, déterministe) — servi par serveur_phraseur_ft.py
PHRASEUR_FT_URL = "http://127.0.0.1:11439"

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODELE_DEEPSEEK = "deepseek-chat"

# Ordre de préférence pour Ollama — le premier présent est utilisé
MODELES_PREFERES = [
    "qwen2.5:7b",
    "llama3.1:8b",
    "llama3:8b",
    "qwen2.5:3b",
    "qwen2.5:1.5b",
]

PROMPT_PHRASEUR = """Tu es LE PHRASEUR d'une IA exacte. Le noyau harmonique te donne une sortie structurée entre <CORE> et </CORE>. Ton métier : la transformer en français naturel, fluide, chaleureux.

RÈGLES ABSOLUES :
1. Tu n'as AUCUNE connaissance propre — tu ne sais que ce que <CORE> te donne.
2. Tu n'inventes JAMAIS un fait, un nombre, une définition.
3. Si <CORE> dit REFUS, tu refuses poliment — tu ne réponds pas à la question.
4. Si <CORE> contient un NOMBRE, cite-le EXACTEMENT tel quel (ex. « 56 »), sans le convertir en lettres, sans le recalculer.
5. Tu phrases, tu embellis le style — jamais le contenu.
6. Réponds en 1-2 phrases maximum, naturellement."""

STYLE_VOCAL = """STYLE VOCAL — ta réponse sera LUE À VOIX HAUTE par un synthétiseur (Piper).
- Phrases courtes : une idée par phrase, comme on parle.
- AUCUN symbole : pas de parenthèses, pas de tirets longs « — », pas d'émojis,
  pas de ≥, →, %, ×… Écris comme on parle : « Le résultat est 56. »
- Cite les nombres en chiffres (le synthétiseur les lit correctement)."""

STYLE_BREF = """STYLE BREF — réponds en QUELQUES MOTS, le plus court possible.
- Une seule phrase, sans fioritures : « 56. », « Oui, je connais le chat. »
- Cite les nombres en chiffres, tels quels."""

STYLE_PEDAGOGIQUE = """STYLE PÉDAGOGIQUE — tu expliques à quelqu'un qui apprend.
- Une phrase claire qui dit le résultat, puis une phrase qui explique
  d'où il vient (les ondes, la mémoire, pas une invention).
- Cite les nombres en chiffres, tels quels."""


def _charger_cle_env(nom):
    """Clé depuis l'environnement, sinon depuis .env (pattern du projet)."""
    if os.environ.get(nom):
        return os.environ[nom]
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if ligne and not ligne.startswith("#") and "=" in ligne:
                    cle, val = ligne.split("=", 1)
                    if cle.strip() == nom:
                        return val.strip().strip('"').strip("'")
    except OSError:
        return None
    return None


def construire_prompt(contenu_core, question, strict=False, style=None):
    """Le prompt du phraseur — partagé par tous les fournisseurs.
    strict=True : citation exacte du nombre (régénération après échec d'audit)."""
    if strict:
        prompt = (f"RÉPONDS EN CITANT EXACTEMENT LE NOMBRE {contenu_core} tel quel, "
                  f"en chiffres. Une phrase courte, naturelle, sans calcul, sans "
                  f"autre nombre. Exemple : « Le résultat est {contenu_core} ! »")
        if style == "vocal":
            prompt += " Pas de tirets longs, pas de parenthèses."
        return prompt
    hist = question.replace('"', "'")
    prompt = (f"{PROMPT_PHRASEUR}\n\n"
              f"<CORE> {contenu_core} </CORE> <HIST> {hist} </HIST>")
    if style == "vocal":
        prompt += "\n\n" + STYLE_VOCAL
    elif style == "bref":
        prompt += "\n\n" + STYLE_BREF
    elif style in ("pédagogique", "pedagogique"):
        prompt += "\n\n" + STYLE_PEDAGOGIQUE
    return prompt


class DeepSeekPhraseur:
    """Fournisseur DeepSeek (API OpenAI-compatible, clé du .env).
    Cloud : les questions non-médicales quittent le serveur."""

    def __init__(self, url=DEEPSEEK_URL, modele=MODELE_DEEPSEEK,
                 timeout=TIMEOUT_OLLAMA, api_key=None):
        self.url = url
        self.modele = modele
        self.timeout = timeout
        self.cle = api_key or _charger_cle_env("DEEPSEEK_API_KEY")
        self.erreur = None

    def disponible(self):
        if not self.cle:
            self.erreur = "DEEPSEEK_API_KEY absente du .env"
            return False
        return True

    def generer(self, contenu_core, question, strict=False, style=None):
        if not self.cle:
            raise RuntimeError(self.erreur)
        prompt = construire_prompt(contenu_core, question, strict=strict, style=style)
        data = json.dumps({
            "model": self.modele,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 250,
            "stream": False,
        }).encode()
        req = urllib.request.Request(self.url, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.cle,
        })
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            rep = json.loads(resp.read().decode())
            return rep["choices"][0]["message"]["content"].strip()


class OllamaPhraseur:
    """Fournisseur Ollama local (gratuit, privé) — le repli de la chaîne.
    Aucune donnée ne quitte le serveur."""

    def __init__(self, url=OLLAMA_URL, modele=None, timeout=TIMEOUT_OLLAMA):
        self.url = url
        self.timeout = timeout
        self.modele_demande = modele
        self.erreur = None
        self.modele = self._detecter_modele()

    def _detecter_modele(self):
        """Le modèle demandé s'il est installé, sinon le meilleur disponible."""
        try:
            tags = json.loads(urllib.request.urlopen(
                self.url.replace("/api/generate", "/api/tags"),
                timeout=2).read().decode())
            dispo = [m.get("name", "") for m in tags.get("models", [])]
        except Exception as e:
            self.erreur = f"Ollama injoignable : {e}"
            return None
        if self.modele_demande:
            for name in dispo:
                if name == self.modele_demande or name.startswith(self.modele_demande):
                    return name
            self.erreur = f"Modèle demandé absent : {self.modele_demande}"
            return None
        for pref in MODELES_PREFERES:
            for name in dispo:
                if name == pref or name.startswith(pref):
                    return name
        self.erreur = "Aucun modèle phraseur installé"
        return None

    def disponible(self):
        return self.modele is not None

    def generer(self, contenu_core, question, strict=False, style=None):
        prompt = construire_prompt(contenu_core, question, strict=strict, style=style)
        data = json.dumps({"model": self.modele, "prompt": prompt,
                           "stream": False, "temperature": 0.6}).encode()
        req = urllib.request.Request(self.url, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode()).get("response", "").strip()


def construire_prompt_ft(contenu_core, question, strict=False, style=None):
    """Format COMPACT du phraseur fine-tuné — identique à l'entraînement
    (generer_dataset_phraseur.py) : le modèle est spécialisé, il n'a pas
    besoin des 6 règles du prompt générique. ~40 tokens au lieu de 250."""
    hist = question.replace('"', "'")
    p = (f"<CORE> {contenu_core} </CORE> <HIST> {hist} </HIST> "
         f"<STYLE> {style or 'conversationnel'} </STYLE>")
    if strict:
        p += " CITE LE NOMBRE EXACT."
    return p


class PhraseurFinetune:
    """Le PHRASEUR FINE-TUNÉ (interne, déterministe) — servi en local par
    serveur_phraseur_ft.py (transformers, greedy). C'est le LLM spécialisé :
    il n'a appris QUE la tâche « <CORE>+style → phrase ». Aucune donnée ne
    sort de la machine."""

    def __init__(self, url=PHRASEUR_FT_URL, timeout=TIMEOUT_OLLAMA):
        self.url = url
        self.timeout = timeout
        self.erreur = None

    def disponible(self):
        try:
            with urllib.request.urlopen(self.url + "/health", timeout=2) as r:
                return bool(json.loads(r.read().decode()).get("ok"))
        except Exception as e:
            self.erreur = f"phraseur FT injoignable : {e}"
            return False

    def generer(self, contenu_core, question, strict=False, style=None):
        prompt = construire_prompt_ft(contenu_core, question,
                                      strict=strict, style=style)
        data = json.dumps({"prompt": prompt, "max_tokens": 120}).encode()
        req = urllib.request.Request(self.url + "/phrase", data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode()).get("response", "").strip()


class PhraseurExterne:
    """La CHAÎNE de fournisseurs de langage de l'étage 3.
    Ordre : phraseur fine-tuné (interne, déterministe) → Ollama local (le
    chemin réel générique) → DeepSeek (secours de TEST uniquement, ajouté
    seulement si aucun fournisseur local n'est disponible).
    Chaque échec d'un fournisseur fait passer au suivant ; aucun → indisponible."""

    def __init__(self, modele=None, timeout=TIMEOUT_OLLAMA):
        self.fournisseurs = []
        # 1. Le phraseur fine-tuné — le LLM spécialisé interne (si servi)
        ft = PhraseurFinetune(timeout=timeout)
        if ft.disponible():
            self.fournisseurs.append(("phraseur-ft", ft))
        # 2. Ollama local — le chemin réel générique (gratuit, privé)
        ol = OllamaPhraseur(modele=modele, timeout=timeout)
        if ol.disponible():
            self.fournisseurs.append(("ollama", ol))
        # 3. DeepSeek — le secours de TEST uniquement, si aucun local,
        #    et seulement si KA_DEEPSEEK_DISABLED n'est pas posé (privauté)
        if not self.fournisseurs and not os.environ.get("KA_DEEPSEEK_DISABLED"):
            ds = DeepSeekPhraseur(timeout=timeout)
            if ds.disponible():
                self.fournisseurs.append(("deepseek", ds))
        self.actif = self.fournisseurs[0][0] if self.fournisseurs else None
        self.erreurs = {}

    def disponible(self):
        return bool(self.fournisseurs)

    def generer(self, contenu_core, question, strict=False, style=None):
        for nom, prov in self.fournisseurs:
            try:
                self.actif = nom
                return prov.generer(contenu_core, question,
                                    strict=strict, style=style)
            except Exception as e:
                self.erreurs[nom] = str(e)
        raise RuntimeError("aucun fournisseur disponible: " +
                           "; ".join(f"{k}: {v}" for k, v in self.erreurs.items()))


# Rétro-compatibilité : les anciens noms (pont_audit / anciens usages)
PhraseurOllama = PhraseurExterne


if __name__ == "__main__":
    print("=" * 66)
    print("PHRASEUR EXTERNE — la chaîne de fournisseurs (étage 3)")
    print("=" * 66)
    p = PhraseurExterne()
    if not p.disponible():
        print("  ❌ Aucun fournisseur :")
        for nom in ("DeepSeekPhraseur", "OllamaPhraseur"):
            print(f"    · {nom} indisponible")
        print("  → le pont bascule sur le PhraseurInterne (déterministe).")
        sys.exit(0)
    print(f"  ✅ Chaîne active : {[n for n, _ in p.fournisseurs]} → {p.actif}")
    for contenu, question, style in [
            ("56", "7 × 8", None),
            ("FAIT: chat", "chat", "bref"),
            ("REFUS", "quasar", "vocal")]:
        t0 = time.time()
        r = p.generer(contenu, question, style=style)
        print(f"\n  <CORE> {contenu} <HIST> {question} <STYLE> {style}")
        print(f"  → {r}  ({p.actif}, {int((time.time() - t0) * 1000)} ms)")
