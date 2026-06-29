"""
Style Engine — Rendu élégant du raisonnement
=============================================
Transforme les chemins de resonance en francais naturel et elegant.

3 niveaux :
  1. TEMPLATES RICHES : 12+ variantes par domaine
  2. CONNECTEURS INTELLIGENTS : détection du flux logique
  3. POLISSAGE LLM : DeepSeek pour l'élégance finale (optionnel)

Usage:
  styler = StyleEngine()
  elegant = styler.render(path, question, domain)
"""

import re, math, random, os
from typing import List, Dict, Tuple, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# 1. TEMPLATES RICHES PAR DOMAINE
# ═══════════════════════════════════════════════════════════════════════════════

RICH_TEMPLATES = {
    "PHYSIQUE": {
        "single": [
            "{sujet} {relation} {objet}. C'est un principe fondamental de la physique.",
            "En physique, {sujet} {relation} {objet}. Ce phenomene est bien etabli.",
            "Le concept est clair : {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "Pour comprendre ce phenomene, partons du principe que {sujet} {relation} {objet}.",
            "L'explication physique commence par un fait essentiel : {sujet} {relation} {objet}.",
            "Tout commence par une observation fondamentale : {sujet} {relation} {objet}.",
            "Le point de depart est le suivant : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ceci implique directement que {sujet} {relation} {objet}.",
            "De ce fait, {sujet} {relation} {objet}.",
            "Par voie de consequence, {sujet} {relation} {objet}.",
            "Ce qui nous conduit a : {sujet} {relation} {objet}.",
            "Et cela signifie que {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, par une chaine de causalite physique, {premier_sujet} est intimement lie a {dernier_objet}.",
            "En definitive, {premier_sujet} et {dernier_objet} sont les deux faces d'un meme phenomene.",
            "La boucle est bouclee : {premier_sujet} → {dernier_objet}.",
        ],
    },
    "BIOLOGIE": {
        "single": [
            "{sujet} {relation} {objet}. C'est un mecanisme essentiel du vivant.",
            "En biologie, {sujet} {relation} {objet}. Cette fonction est vitale.",
        ],
        "chain_intro": [
            "Pour saisir ce mecanisme biologique, observons d'abord que {sujet} {relation} {objet}.",
            "Le vivant fonctionne par etapes : d'abord, {sujet} {relation} {objet}.",
            "Partons d'un fait biologique elementaire : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ce qui permet alors de {sujet} {relation} {objet}.",
            "Cette etape declenche le processus suivant : {sujet} {relation} {objet}.",
            "Ensuite, {sujet} {relation} {objet}.",
            "Ce mecanisme active a son tour : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, le vivant orchestre une cascade ou {premier_sujet} aboutit a {dernier_objet}.",
            "Ce chemin biologique revele comment {premier_sujet} est essentiel a {dernier_objet}.",
        ],
    },
    "CONSCIENCE": {
        "single": [
            "{sujet} {relation} {objet}. C'est une realite de l'experience humaine.",
            "Du point de vue de la conscience, {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "L'exploration de la conscience commence par ce constat : {sujet} {relation} {objet}.",
            "Pour eclairer cette question, partons de l'evidence que {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ce qui nous fait prendre conscience que {sujet} {relation} {objet}.",
            "Cela ouvre sur une dimension plus profonde : {sujet} {relation} {objet}.",
            "Cette realisation eclaire a son tour le fait que {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, {premier_sujet} et {dernier_objet} sont relies par le fil de la conscience.",
            "L'experience consciente tisse un lien entre {premier_sujet} et {dernier_objet}.",
        ],
    },
    "PHILOSOPHIE": {
        "single": [
            "{sujet} {relation} {objet}. C'est une question qui traverse les siecles.",
            "La philosophie nous enseigne que {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "La reflexion philosophique debute par une interrogation : {sujet} {relation} {objet}.",
            "Les penseurs ont etabli que {sujet} {relation} {objet}. Mais cela souleve une autre question.",
        ],
        "chain_link": [
            "Ce qui nous amene a considerer que {sujet} {relation} {objet}.",
            "Cette idee en implique une autre : {sujet} {relation} {objet}.",
            "La pensee progresse : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Au terme de cette reflexion, {premier_sujet} apparait comme le fondement de {dernier_objet}.",
            "Ainsi, la sagesse nous revele le lien profond entre {premier_sujet} et {dernier_objet}.",
        ],
    },
    "MATHS": {
        "single": [
            "{sujet} {relation} {objet}. C'est une verite mathematique.",
            "Mathematiquement, {sujet} {relation} {objet}. Cela se demontre rigoureusement.",
        ],
        "chain_intro": [
            "Le raisonnement mathematique s'appuie sur un premier fait : {sujet} {relation} {objet}.",
            "Partons d'une proposition etablie : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ce qui implique logiquement que {sujet} {relation} {objet}.",
            "De cette proposition decoule : {sujet} {relation} {objet}.",
            "Le theoreme suivant en resulte : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Par deduction, {premier_sujet} est mathematiquement lie a {dernier_objet}.",
            "La demonstration est complete : {premier_sujet} ⇒ {dernier_objet}.",
        ],
    },
    "EMOTION": {
        "single": [
            "{sujet} {relation} {objet}. C'est une verite du coeur.",
            "Sur le plan emotionnel, {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "L'emotion nous revele d'abord que {sujet} {relation} {objet}.",
            "Le coeur sait que {sujet} {relation} {objet}. Et cela nous conduit plus loin.",
        ],
        "chain_link": [
            "Ce qui fait resonner en nous que {sujet} {relation} {objet}.",
            "Cette emotion en eveille une autre : {sujet} {relation} {objet}.",
            "Le sentiment s'approfondit : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, {premier_sujet} et {dernier_objet} vibrent sur la meme corde affective.",
            "L'ame humaine relie {premier_sujet} a {dernier_objet} par le fil de l'emotion.",
        ],
    },
    "HISTOIRE": {
        "single": [
            "{sujet} {relation} {objet}. C'est un fait historique avere.",
            "L'histoire nous apprend que {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "Pour comprendre cet enchainement, rappelons d'abord que {sujet} {relation} {objet}.",
            "Le recit historique commence ainsi : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Cet evenement a entraine que {sujet} {relation} {objet}.",
            "Ce qui a conduit a ce que {sujet} {relation} {objet}.",
            "La suite des evenements nous mene a : {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "Ainsi, la chaine historique revele comment {premier_sujet} a abouti a {dernier_objet}.",
            "Le fil de l'histoire tisse un lien entre {premier_sujet} et {dernier_objet}.",
        ],
    },
    "GENERAL": {
        "single": [
            "{sujet} {relation} {objet}. Voila l'essentiel.",
            "On peut affirmer que {sujet} {relation} {objet}.",
        ],
        "chain_intro": [
            "Pour comprendre, notons d'abord que {sujet} {relation} {objet}.",
            "Le point de depart est simple : {sujet} {relation} {objet}.",
        ],
        "chain_link": [
            "Ce qui signifie que {sujet} {relation} {objet}.",
            "Par consequent, {sujet} {relation} {objet}.",
            "Et donc, {sujet} {relation} {objet}.",
        ],
        "chain_conclusion": [
            "En resume, {premier_sujet} est fondamentalement lie a {dernier_objet}.",
            "Tout cela montre que {premier_sujet} et {dernier_objet} sont connectes.",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MOTEUR DE STYLE
# ═══════════════════════════════════════════════════════════════════════════════

class StyleEngine:
    """
    Transforme un chemin de raisonnement en francais elegant.
    """
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self._used_templates = {}  # pour eviter les repetitions
    
    def render(self, path, question: str, domain: str) -> str:
        """Rend un chemin en langage naturel elegant."""
        if not path:
            return "Aucun chemin de resonance trouve."
        
        templates = RICH_TEMPLATES.get(domain, RICH_TEMPLATES['GENERAL'])
        
        if len(path) == 1:
            return self._render_single(path[0], templates)
        else:
            return self._render_chain(path, templates)
    
    def _render_single(self, fact, templates) -> str:
        """Rend un fait unique."""
        s, r, o, sec = fact
        tmpl = random.choice(templates['single'])
        return tmpl.format(sujet=s.capitalize(), relation=r, objet=o)
    
    def _render_chain(self, path, templates) -> str:
        """Rend une chaine de raisonnement."""
        sentences = []
        
        # Introduction
        s0, r0, o0, _ = path[0]
        intro_tmpl = random.choice(templates['chain_intro'])
        sentences.append(intro_tmpl.format(sujet=s0.capitalize(), relation=r0, objet=o0))
        
        # Liens intermediaires
        for i in range(1, len(path)):
            s, r, o, _ = path[i]
            link_tmpl = random.choice(templates['chain_link'])
            sentences.append(link_tmpl.format(sujet=s, relation=r, objet=o))
        
        # Conclusion
        if len(path) >= 2:
            premier_sujet = path[0][0].capitalize()
            dernier_objet = path[-1][2]
            concl_tmpl = random.choice(templates['chain_conclusion'])
            conclusion = concl_tmpl.format(
                premier_sujet=premier_sujet,
                dernier_objet=dernier_objet
            )
            sentences.append(conclusion)
        
        return ' '.join(sentences)
    
    def polish_with_llm(self, raw_text: str, domain: str) -> str:
        """
        Polissage final par DeepSeek pour une elegance maximale.
        Ne change pas les faits — ameliore uniquement le style.
        """
        if not self.use_llm:
            return raw_text
        
        try:
            import os, sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from llm.router import HarmonicLLM
            llm = HarmonicLLM()
            
            prompt = (
                f"Reecris ce texte en francais elegant et naturel, SANS changer "
                f"les faits ni ajouter d'information. Domaine : {domain}.\n\n"
                f"Texte : {raw_text}\n\n"
                f"Version elegante :"
            )
            resp = llm.generate(prompt, category="creative")
            if resp.content and len(resp.content) > 20:
                return resp.content.strip()
        except Exception:
            pass
        
        return raw_text


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from harmonic_model import HarmonicModel
    from reasoning_engine import find_paths, detect_domain
    
    print("=" * 60)
    print("STYLE ENGINE — Francais elegant par domaine")
    print("=" * 60)
    
    model = HarmonicModel(use_memory=False)
    styler = StyleEngine()
    
    tests = [
        "pourquoi le coeur pompe le sang",
        "explique la lumiere",
        "qu est ce que la conscience",
        "comment fonctionne la resonance",
        "explique le nombre d or",
        "qu est ce que dieu",
    ]
    
    for q in tests:
        paths = find_paths(model.knowledge_base, q)
        if paths:
            domain = detect_domain(paths[0])
            elegant = styler.render(paths[0], q, domain)
            print(f"\n[{domain}] >> {q}")
            print(f"       << {elegant}")


if __name__ == '__main__':
    demo()
