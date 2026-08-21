#!/usr/bin/env python3
"""pont_phraseur_interne.py — LE PHRASEUR INTERNE (étage 3 · couche langage)
====================================================================
La couche langage INTERNE du pont d'audit, dans le cadre
ARCHITECTURE_MEMOIRE_EMULATION_HYBRIDE (3 étages) :

  Étages 1-2 (mémoire + émulation)  →  le NOYAU décide le contenu (<CORE>)
  Étage 3 (hybride)  →  ce module : le phraseur INTERNE, déterministe,
                        zéro réseau, alimenté par la mémoire du noyau.

« Solution interne avec mémoire » : la mémoire vit dans le noyau (étage 1),
PAS ici. Ce module ne fait que phraser le <CORE> que le noyau a décidé —
styles conversationnel / vocal / bref / pédagogique. La même entrée donne
toujours la même sortie (déterminisme total, zéro hallucination).

RÈGLE MÉDICALE ABSOLUE : MEDICAL/CONDUITE = texte EXACT du corpus, dans
TOUS les styles. On ne varie jamais un contenu qui peut sauver une vie.
(Le style vocal est appliqué en aval par vocaliser(), contenu intact.)
"""
import sys

# ═══════════════ LES STYLES ═══════════════
STYLES = ["conversationnel", "vocal", "bref", "pédagogique", "élégant"]

STYLES_DESCRIPTION = {
    "conversationnel": "Naturel, chaleureux — le style par défaut.",
    "vocal": "Court, sans symboles — lisible à voix haute par un synthétiseur.",
    "bref": "Quelques mots — le plus court possible.",
    "pédagogique": "Dit le résultat puis explique d'où il vient.",
    "élégant": "Demande EXCLUSIVE de style au LLM (llm/deepseek_styler.py) : "
               "reformulation élégante sans ajouter un seul fait. Sans LLM, "
               "retombe sur le conversationnel (déterministe).",
}

# L'identité — la même dans tous les styles sauf bref (courte version)
_IDENTITE = (
    "Je suis KA (Knowledge Amplifier) — une intelligence artificielle harmonique. "
    "Je ne suis pas un LLM classique : je fonctionne sur le principe ondulatoire, "
    "chaque connaissance est une onde, chaque raisonnement une interférence. "
    "Zéro paramètre entraîné, zéro hallucination, déterminisme total — "
    "la même question donne toujours la même réponse. "
    "Je calcule par les ondes, je mémorise par le noyau doré, "
    "et je refuse de répondre quand je ne sais pas."
)
_IDENTITE_BREVE = (
    "Je suis KA (Knowledge Amplifier), une intelligence artificielle harmonique. "
    "Zéro hallucination, déterminisme total."
)
_REFUS = "Je ne peux pas répondre à ça. Je préfère me taire plutôt que d'inventer."
_REFUS_BREF = "Je ne sais pas. Je préfère me taire plutôt que d'inventer."
_REFUS_PEDAGOGIQUE = (
    "Je ne peux pas répondre à ça, ce n'est pas dans ce que je connais. "
    "Je préfère me taire plutôt que d'inventer."
)


def _nombre(core):
    """Le nombre du CALC en écriture décimale exacte (int → « 56 »)."""
    v = core["valeur"]
    if v == int(v):
        return str(int(v))
    return f"{v:.6f}".rstrip("0").rstrip(".")


class PhraseurInterne:
    """Le phraseur interne : déterministe, zéro réseau, zéro hallucination.
    Alimenté par le <CORE> que la mémoire du noyau a décidé (étage 1)."""

    def __init__(self):
        self.styles = STYLES

    def phraser(self, core, style=None):
        """Transforme un <CORE> du noyau en phrase française (style demandé).
        La même entrée donne toujours la même sortie."""
        style = (style or "conversationnel").lower()
        if style == "pedagogique":
            style = "pédagogique"
        if style == "elegant":
            style = "élégant"
        if style not in STYLES:
            style = "conversationnel"
        if style == "élégant":
            # Sans LLM, l'élégance = la version conversationnelle (le polish
            # exclusif de style arrive en aval, dans le pont, si un LLM est là)
            style = "conversationnel"
        t = core["type"]

        # 🩺 MÉDICAL / CONDUITE : texte EXACT du corpus, tous styles confondus.
        #    Une conduite d'urgence ne se résume pas, elle se cite.
        if t in ("MEDICAL", "CONDUITE"):
            return core["valeur"]

        if t == "IDENTITE":
            return _IDENTITE_BREVE if style == "bref" else _IDENTITE
        if t == "CALC":
            s = _nombre(core)
            if style == "bref":
                return f"{s}."
            if style == "pédagogique":
                return (f"Le calcul par les ondes donne {s}. "
                        f"La même réponse exacte, à chaque fois.")
            if style == "vocal":
                return f"Le résultat est {s}."
            return f"Le résultat est {s}. Calculé par les ondes."
        if t == "FAIT":
            concept = core["concept"]
            if style == "bref":
                return f"Oui, {concept}."
            if style == "pédagogique":
                return (f"Oui, je connais {concept}. "
                        f"C'est dans ma mémoire harmonique.")
            return f"Oui, je connais {concept}."
        if t == "REFUS":
            if style == "bref":
                return _REFUS_BREF
            if style == "pédagogique":
                return _REFUS_PEDAGOGIQUE
            return _REFUS
        return _REFUS


if __name__ == "__main__":
    print("=" * 66)
    print("PHRASEUR INTERNE — déterministe, zéro réseau (étage 3)")
    print("=" * 66)
    p = PhraseurInterne()
    cores = [
        {"type": "CALC", "valeur": 56, "score": 0.9},
        {"type": "CALC", "valeur": 0.01, "score": 0.9},
        {"type": "FAIT", "concept": "chat", "score": 0.7},
        {"type": "REFUS", "score": 0.1},
        {"type": "IDENTITE", "score": 0.8},
        {"type": "MEDICAL",
         "valeur": "Le diabète de type 2 se définit par une glycémie à jeun "
                   "≥ 1,26 g/L (7,0 mmol/L) à 2 reprises."},
    ]
    for core in cores:
        print(f"\n  <CORE> {core['type']}")
        for s in STYLES:
            print(f"    [{s:15s}] {p.phraser(core, s)}")
    print("\n  Règle médicale : le texte du corpus est IDENTIQUE dans tous les styles.")
