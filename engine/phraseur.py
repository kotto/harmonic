#!/usr/bin/env python3
"""
phraseur.py — Moteur de phrasage stylé pour KA Hologramme
==========================================================

Intègre le PhraseurInterne (templates déterministes) et le modèle
fine-tuné (SmolLM2-135M + LoRA) pour générer des réponses naturelles
dans 4 styles : conversationnel, vocal, bref, pédagogique.

Usage :
  from phraseur import phraser
  reponse = phraser(question, operations, resultat, style="conversationnel")
"""

import sys, os, json, re
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════════════════
# 1. PHRASEUR INTERNE (déterministe, zéro paramètre, fallback)
# ═══════════════════════════════════════════════════════════════════════════

STYLES = ["conversationnel", "vocal", "bref", "pédagogique", "élégant"]

# Templates par style
_TEMPLATES = {
    "conversationnel": {
        "CALC": "Le calcul donne {resultat}. {explication}",
        "FINANCE": "Le résultat financier est {resultat}. {explication}",
        "SANTE": "Voici ce que je sais : {resultat}. {explication}",
    },
    "vocal": {
        "CALC": "Résultat : {resultat}. {explication}",
        "FINANCE": "Résultat financier : {resultat}. {explication}",
        "SANTE": "Information : {resultat}. {explication}",
    },
    "bref": {
        "CALC": "{resultat}.",
        "FINANCE": "{resultat}.",
        "SANTE": "{resultat}.",
    },
    "pédagogique": {
        "CALC": "Le calcul harmonique donne {resultat}. Démonstration : {explication}",
        "FINANCE": "Le calcul financier donne {resultat}. Démonstration : {explication}",
        "SANTE": "Voici l'information : {resultat}. Détail : {explication}",
    },
}

# Conclusions contextuelles
_CONCLUSIONS = {
    "gain": "💰 Le gain total s'élève à {r}.",
    "rapporte": "💰 Le gain total s'élève à {r}.",
    "profit": "💰 Le profit est de {r}.",
    "perte": "📉 La perte totale s'élève à {r}.",
    "perd": "📉 La perte totale s'élève à {r}.",
    "total": "📊 Le résultat est {r}.",
    "augmentation": "📈 L'augmentation est de {r}.",
    "augmente": "📈 L'augmentation est de {r}.",
    "cout": "💵 Le coût est de {r}.",
    "coût": "💵 Le coût est de {r}.",
    "investissement": "💎 Le retour sur investissement est de {r}.",
    "loan": "🏦 Les intérêts du prêt sont de {r}.",
    "prêt": "🏦 Les intérêts du prêt sont de {r}.",
    "pret": "🏦 Les intérêts du prêt sont de {r}.",
    "salaire": "👔 L'augmentation de salaire est de {r}.",
    "salary": "👔 L'augmentation de salaire est de {r}.",
    "impot": "🧾 Le montant est de {r}.",
    "impôt": "🧾 Le montant est de {r}.",
    "tax": "🧾 Le montant est de {r}.",
}


def _detecter_type(question: str) -> str:
    """Détecte le type de question pour choisir le bon template."""
    q = question.lower()
    for kw, _ in _CONCLUSIONS.items():
        if kw in q:
            # Retourner le mot-clé pour choisir la conclusion
            return kw
    return "CALC"


def _formater_nombre(v: float) -> str:
    """Formate un nombre lisiblement."""
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ")


def _explication_etapes(operations_text: str) -> str:
    """Génère l'explication des étapes à partir des opérations."""
    ops = []
    for token in operations_text.replace('\n', ' ').split():
        m = re.match(r'(INIT|MUL|SUB|ADD|DIV)\(([^)]+)\)', token.strip())
        if not m:
            continue
        try:
            v = float(m.group(2))
        except ValueError:
            continue
        ops.append((m.group(1), v))

    if not ops:
        return ""

    parties = []
    acc = None
    for op, val in ops:
        vs = _formater_nombre(val)
        if op == 'INIT':
            acc = val
            parties.append(f"valeur initiale : {vs}")
        elif op == 'MUL':
            if acc is not None:
                r = acc * val
                parties.append(f"× {vs} → {_formater_nombre(acc)} × {vs} = {_formater_nombre(r)}")
                acc = r
        elif op == 'DIV':
            if acc is not None:
                r = acc / val if val else acc
                parties.append(f"÷ {vs} → {_formater_nombre(r)}")
                acc = r
        elif op == 'ADD':
            if acc is not None:
                r = acc + val
                parties.append(f"+ {vs} → {_formater_nombre(r)}")
                acc = r
        elif op == 'SUB':
            if acc is not None:
                r = acc - val
                parties.append(f"− {vs} → {_formater_nombre(r)}")
                acc = r

    return " · ".join(parties)


class PhraseurInterne:
    """Phraseur déterministe : templates + contexte."""

    def phraser(self, question: str, operations_text: str, resultat: float,
                style: str = "conversationnel", type_reponse: str = "CALC") -> str:
        style = style.lower()
        if style not in STYLES:
            style = "conversationnel"
        if style == "élégant":
            style = "conversationnel"

        resultat_str = _formater_nombre(resultat)
        explication = _explication_etapes(operations_text)

        # Conclusion contextuelle
        concl = ""
        for kw, template in _CONCLUSIONS.items():
            if kw in question.lower():
                concl = template.format(r=resultat_str)
                break

        # Template par style
        tpls = _TEMPLATES.get(style, _TEMPLATES["conversationnel"])
        tpl = tpls.get(type_reponse, tpls.get("CALC", "{resultat}."))

        if style == "bref":
            return resultat_str + "."
        if style == "vocal":
            return f"Résultat : {resultat_str}. {explication}" if explication else f"Résultat : {resultat_str}."

        return f"{concl} {explication}".strip() if concl and explication else resultat_str


# ═══════════════════════════════════════════════════════════════════════════
# 2. PHRASEUR EXTERNE (modèle fine-tuné SmolLM2-135M + LoRA)
# ═══════════════════════════════════════════════════════════════════════════

_PHRASEUR_FT = None
_TOK_PHRASEUR = None


def _charger_phraseur_ft():
    """Charge le modèle fine-tuné SmolLM2-135M (une seule fois)."""
    global _PHRASEUR_FT, _TOK_PHRASEUR
    if _PHRASEUR_FT is not None:
        return True

    chemin_lora = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "data", "phraseur", "lora_best")
    if not os.path.exists(chemin_lora):
        return False

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        _TOK_PHRASEUR = AutoTokenizer.from_pretrained(
            "HuggingFaceTB/SmolLM2-135M-Instruct")
        base = AutoModelForCausalLM.from_pretrained(
            "HuggingFaceTB/SmolLM2-135M-Instruct", torch_dtype="auto",
            low_cpu_mem_usage=True)
        _PHRASEUR_FT = PeftModel.from_pretrained(base, chemin_lora)
        _PHRASEUR_FT.eval()
        return True
    except Exception as e:
        print(f"  ⚠️ Phraseur FT non chargé : {e}")
        return False


def phraser_ft(question: str, operations_text: str, resultat: float,
               style: str = "conversationnel") -> Optional[str]:
    """Utilise le modèle fine-tuné pour générer une réponse naturelle.

    Format d'entrée : <CORE> {resultat} </CORE> <HIST> {operations} </HIST> <STYLE> {style} </STYLE>
    """
    if not _charger_phraseur_ft():
        return None

    resultat_str = _formater_nombre(resultat)
    prompt = (f"<CORE> {resultat_str} </CORE> "
              f"<HIST> {operations_text} </HIST> "
              f"<STYLE> {style} </STYLE>")

    try:
        import torch
        inputs = _TOK_PHRASEUR(prompt, return_tensors="pt", max_length=96,
                               truncation=True)
        with torch.no_grad():
            out = _PHRASEUR_FT.generate(**inputs, max_new_tokens=64,
                                         num_beams=1)
        return _TOK_PHRASEUR.decode(out[0], skip_special_tokens=True)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. INTERFACE UNIFIÉE
# ═══════════════════════════════════════════════════════════════════════════

_PHRASEUR = PhraseurInterne()


def phraser(question: str, operations_text: str, resultat: float,
            style: str = "conversationnel", type_reponse: str = "CALC") -> str:
    """Point d'entrée unique : tente le modèle FT, fallback PhraseurInterne.

    Args:
        question: La question posée
        operations_text: Les opérations (ex: "INIT(5000) MUL(0.08)")
        resultat: Le résultat numérique du codec ψ
        style: Style de réponse (conversationnel, vocal, bref, pédagogique)
        type_reponse: Type de réponse (CALC, FINANCE, SANTE...)

    Retourne:
        La réponse rédigée
    """
    # Essayer le modèle fine-tuné d'abord
    ft = phraser_ft(question, operations_text, resultat, style)
    if ft and ft.strip():
        return ft.strip()

    # Fallback : PhraseurInterne déterministe
    return _PHRASEUR.phraser(question, operations_text, resultat, style, type_reponse)


def demo():
    """Démo du phraseur."""
    tests = [
        ("Un investissement de 5000€ rapporte 8%. Quel est le gain ?",
         "INIT(5000) MUL(0.08)", 400.0, "conversationnel"),
        ("Un capital de 10000€ perd 15%. Quelle est la perte ?",
         "INIT(10000) MUL(0.15) SUB(1500)", 1500.0, "vocal"),
        ("Un salaire de 3000€ avec augmentation de 10%.",
         "INIT(3000) MUL(0.1) ADD(300)", 300.0, "bref"),
        ("Un prêt de 20000€ à 5% sur un an.",
         "INIT(20000) MUL(0.05)", 1000.0, "pédagogique"),
    ]

    print(f"{'═'*60}")
    print(f"  PHRASEUR — 4 styles, 4 questions")
    print(f"{'═'*60}\n")

    for question, ops, resultat, style in tests:
        rep = phraser(question, ops, resultat, style)
        print(f"  📌 {question}")
        print(f"  🎨 Style : {style}")
        print(f"  🔧 Ops   : {ops}")
        print(f"  💬 → {rep}")
        print()


if __name__ == '__main__':
    demo()