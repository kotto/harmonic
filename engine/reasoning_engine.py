"""
Reasoning Engine v2 — Architecture généralisée
===============================================
Un seul moteur pour tous les domaines.
Le domaine est DÉTECTÉ dans les faits, pas prédéfini.
Le rendu s'adapte au domaine.

Principe : Ψₐ · Ψ_b = Ψ_{a+b} est universel.
"""

import re, math, random
from typing import List, Dict, Tuple, Optional
from collections import Counter
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DOMAINES ET LEURS VOCABULAIRES DE RENDU
# ═══════════════════════════════════════════════════════════════════════════════

DOMAIN_VOCABULARY = {
    "PHYSIQUE": {
        "connectors": ["ce qui implique que", "ce qui genere", "ce qui produit", "par consequent"],
        "verbs": ["provoque", "genere", "induit", "entraine", "cause"],
        "intro": "D'un point de vue physique,",
        "conclusion": "Ainsi, le phenomene physique est explique.",
    },
    "BIOLOGIE": {
        "connectors": ["ce qui permet de", "ce qui declenche", "ce qui active", "ce qui conduit a"],
        "verbs": ["active", "declenche", "permet", "assure", "regule"],
        "intro": "Sur le plan biologique,",
        "conclusion": "Ainsi, le mecanisme vivant est decrit.",
    },
    "MATHS": {
        "connectors": ["ce qui equivaut a", "ce qui implique mathematiquement", "d'ou", "par deduction"],
        "verbs": ["equivaut", "implique", "demontre", "prouve", "etablit"],
        "intro": "Mathematiquement,",
        "conclusion": "Ainsi, la relation mathematique est etablie.",
    },
    "CONSCIENCE": {
        "connectors": ["ce qui revele que", "ce qui eclaire", "ce qui fait emerger", "ce qui ouvre sur"],
        "verbs": ["revele", "eclaire", "fait emerger", "ouvre sur", "permet de comprendre"],
        "intro": "Sur le plan de la conscience,",
        "conclusion": "Ainsi, la dimension consciente est exploree.",
    },
    "EMOTION": {
        "connectors": ["ce qui fait ressentir", "ce qui touche a", "ce qui eveille", "ce qui emeut"],
        "verbs": ["touche", "emeut", "eveille", "fait ressentir", "trouble"],
        "intro": "Emotionnellement,",
        "conclusion": "Ainsi, la dimension affective est revelee.",
    },
    "HISTOIRE": {
        "connectors": ["ce qui a conduit a", "ce qui a entraine", "ce qui a provoque", "ce qui a abouti a"],
        "verbs": ["a conduit a", "a entraine", "a provoque", "a abouti a", "a engendre"],
        "intro": "Historiquement,",
        "conclusion": "Ainsi, l'enchainement historique est retrace.",
    },
    "PHILOSOPHIE": {
        "connectors": ["ce qui questionne", "ce qui interroge", "ce qui met en lumiere", "ce qui revele"],
        "verbs": ["questionne", "interroge", "revele", "eclaire", "transcende"],
        "intro": "Philosophiquement,",
        "conclusion": "Ainsi, la question fondamentale est exploree.",
    },
    "GENERAL": {
        "connectors": ["ce qui signifie que", "ce qui implique", "ce qui conduit a", "par consequent"],
        "verbs": ["implique", "conduit a", "signifie", "entraine", "produit"],
        "intro": "",
        "conclusion": "Ainsi, le raisonnement est etabli.",
    },
}

# Mapping secteur → domaine de rendu
SECTOR_TO_DOMAIN = {
    'PHYSIQUE_FOND': 'PHYSIQUE', 'PHYSIQUE_APPLI': 'PHYSIQUE',
    'BIOLOGIE': 'BIOLOGIE', 'ECOLOGIE': 'BIOLOGIE',
    'MATHS_PURES': 'MATHS', 'MATHS_APPLI': 'MATHS',
    'CONSCIENCE': 'CONSCIENCE', 'INTELLIGENCE': 'CONSCIENCE',
    'EMOTION_POS': 'EMOTION', 'EMOTION_NEG': 'EMOTION',
    'ASTRONOMIE': 'PHYSIQUE', 'COSMOLOGIE': 'PHYSIQUE',
    'PASSE': 'HISTOIRE', 'FUTUR': 'HISTOIRE',
    'CULTURE': 'GENERAL', 'POLITIQUE': 'HISTOIRE',
    'CREATION': 'GENERAL', 'EXPRESSION': 'GENERAL',
    'NATURE_ANIM': 'BIOLOGIE', 'NATURE_VEGET': 'BIOLOGIE',
    'CORPS_ORGANES': 'BIOLOGIE', 'CORPS_SENS': 'BIOLOGIE',
    'METAPHYSIQUE': 'PHILOSOPHIE', 'SPIRITUALITE': 'PHILOSOPHIE',
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. TROUVEUR DE CHEMINS (universel)
# ═══════════════════════════════════════════════════════════════════════════════

_STOPWORDS = {'le','la','les','de','des','du','un','une','et','est','a','dans',
              'que','qui','pas','ne','sur','pour','avec','ce','cette','ces','cet',
              'au','aux','en','plus','moins','tout','tous','son','sa','ses','par',
              'the','and','that','have','for','not','with','this','but','his','from',
              'they','will','been','when','are','was','has','had','its','all','can'}

def _meaningful_words(text: str) -> set:
    return set(w for w in re.findall(r'\b[a-zà-ÿ]{3,}\b', text.lower()) if w not in _STOPWORDS)

def _overlap(a: str, b: str) -> float:
    wa, wb = _meaningful_words(a), _meaningful_words(b)
    if not wa or not wb: return 0.0
    return len(wa & wb) / max(len(wa), len(wb))

def find_paths(knowledge_base: list, question: str, max_depth: int = 3,
               max_paths: int = 3) -> List[List[Tuple[str, str, str, str]]]:
    """Trouve les chemins de resonance universels."""
    q_words = _meaningful_words(question)
    
    scored_starts = []
    for s, r, o, sec in knowledge_base:
        all_w = _meaningful_words(s + ' ' + r + ' ' + o)
        overlap = q_words & all_w
        if overlap:
            score = len(overlap) / max(len(q_words), 1)
            if score > 0.15:
                scored_starts.append((score, s, r, o, sec))
    scored_starts.sort(key=lambda x: -x[0])
    
    paths = []
    for _, s, r, o, sec in scored_starts[:5]:
        path = [(s, r, o, sec)]
        current_obj = o
        seen = {s}
        depth = 0
        while depth < max_depth:
            best_score, best_next = 0.2, None
            for s2, r2, o2, sec2 in knowledge_base:
                if s2 in seen: continue
                score = _overlap(current_obj, s2)
                if score > best_score:
                    best_score = score
                    best_next = (s2, r2, o2, sec2)
            if best_next:
                path.append(best_next)
                current_obj = best_next[2]; seen.add(best_next[0]); depth += 1
            else: break
        if len(path) >= 2: paths.append(path)
    
    unique, seen_sigs = [], set()
    for p in paths:
        sig = tuple(s for s, r, o, sec in p)
        if sig not in seen_sigs: seen_sigs.add(sig); unique.append(p)
    unique.sort(key=lambda p: -len(p))
    return unique[:max_paths]

# ═══════════════════════════════════════════════════════════════════════════════
# 3. DETECTEUR DE DOMAINE (automatique)
# ═══════════════════════════════════════════════════════════════════════════════

def detect_domain(path: List[Tuple[str, str, str, str]]) -> str:
    """Detecte le domaine dominant d'un chemin.
    Le PREMIER fait donne le domaine principal.
    Les faits suivants peuvent appartenir a d'autres domaines
    (le raisonnement traverse les frontieres)."""
    if not path:
        return 'GENERAL'
    # Le domaine du premier fait est le domaine de la question
    first_sector = path[0][3]
    return SECTOR_TO_DOMAIN.get(first_sector, 'GENERAL')

# ═══════════════════════════════════════════════════════════════════════════════
# 4. RENDU ADAPTATIF (vocabulaire selon domaine)
# ═══════════════════════════════════════════════════════════════════════════════

def render_path(path: List[Tuple[str, str, str, str]], question: str,
                domain: str = None) -> str:
    """Rend un chemin en langage naturel adapte au domaine."""
    if domain is None:
        domain = detect_domain(path)
    
    vocab = DOMAIN_VOCABULARY.get(domain, DOMAIN_VOCABULARY['GENERAL'])
    
    if not path:
        return "Aucun chemin de resonance trouve."
    
    # Construire les phrases
    sentences = []
    for i, (s, r, o, sec) in enumerate(path):
        s_cap = s[0].upper() + s[1:] if s else '?'
        if i == 0:
            sentences.append(f"{s_cap} {r} {o}")
        else:
            connector = vocab['connectors'][min(i-1, len(vocab['connectors'])-1)]
            prev_obj = path[i-1][2]
            curr_subj = s
            link_words = _meaningful_words(prev_obj) & _meaningful_words(curr_subj)
            link = list(link_words)[0] if link_words else None
            if link:
                sentences.append(f"{connector} {link} {r} {o}")
            else:
                sentences.append(f"{connector} {s} {r} {o}")
    
    # Assemblage
    result = ', '.join(sentences) + '.'
    
    # Introduction et conclusion adaptees au domaine
    intro = vocab['intro']
    conclusion = vocab['conclusion']
    
    if intro:
        result = f"{intro} {result}"
    if conclusion and len(path) >= 2:
        result += f" {conclusion}"
    
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# 5. MOTEUR UNIFIE
# ═══════════════════════════════════════════════════════════════════════════════

class ReasoningEngine:
    """
    Moteur de raisonnement generalise.
    Un seul moteur. Tous les domaines.
    Le domaine est detecte, pas predéfini.
    Le style est elegant, pas robotique.
    """
    
    def __init__(self, model, use_llm_style: bool = False):
        self.model = model
        from style_engine import StyleEngine
        self.styler = StyleEngine(use_llm=use_llm_style)
    
    def reason(self, question: str, max_depth: int = 3) -> str:
        """Raisonnement generalise avec style elegant."""
        paths = find_paths(self.model.knowledge_base, question, max_depth)
        
        if not paths:
            return self.model.ask(question)
        
        path = paths[0]
        domain = detect_domain(path)
        return self.styler.render(path, question, domain)
    
    def reason_multi(self, question: str, max_depth: int = 3) -> str:
        """Raisonnement multi-perspective."""
        paths = find_paths(self.model.knowledge_base, question, max_depth)
        
        if not paths:
            return self.model.ask(question)
        
        if len(paths) == 1:
            return self.reason(question, max_depth)
        
        parts = []
        for i, path in enumerate(paths[:2]):
            domain = detect_domain(path)
            rendered = self.styler.render(path, question, domain)
            if i == 0:
                parts.append(rendered)
            else:
                parts.append(f"Sous un autre angle, {rendered}")
        return ' '.join(parts)
    
    def create(self, domain1: str = None, domain2: str = None,
               concept: str = None, n_ideas: int = 3) -> List[str]:
        """
        CREE des connexions nouvelles par INTERFERENCE D'ONDES.
        
        Au lieu de chercher des mots communs (approche lexicale),
        on mesure l'INTERFERENCE entre les ondes φ des concepts
        de domaines differents. Deux concepts peuvent resonner
        sans partager aucun mot.
        
        C'est Ψ_domaine1 · Ψ_domaine2 = Ψ_connexion_nouvelle
        """
        kb = self.model.knowledge_base
        kx, ky, w2i = self.model.kx, self.model.ky, self.model.w2i
        
        # Grouper par domaine
        facts_by_domain = {}
        for s, r, o, sec in kb:
            dom = SECTOR_TO_DOMAIN.get(sec, 'GENERAL')
            if dom not in facts_by_domain:
                facts_by_domain[dom] = []
            facts_by_domain[dom].append((s, r, o, sec))
        
        domains = list(facts_by_domain.keys())
        if len(domains) < 2:
            return ["Pas assez de domaines pour creer."]
        
        all_ideas = []
        
        for d1 in domains:
            for d2 in domains:
                if d1 >= d2:
                    continue
                
                # Pour chaque paire de domaines, mesurer l'interference
                # entre les concepts principaux (sujets des faits)
                pairs = []
                for s1, r1, o1, _ in facts_by_domain[d1][:20]:
                    if s1 not in w2i:
                        continue
                    for s2, r2, o2, _ in facts_by_domain[d2][:20]:
                        if s2 not in w2i:
                            continue
                        # Interference entre les ondes des deux sujets
                        i1, i2 = w2i[s1], w2i[s2]
                        dot = kx[i1]*kx[i2] + ky[i1]*ky[i2]
                        interference = (dot + 1.0) / 2.0  # [0, 1]
                        # On cherche des interferences MODEREES (ni trop proches, ni trop eloignees)
                        # car ce sont les plus creatives
                        if 0.3 < interference < 0.8:
                            pairs.append((interference, s1, r1, o1, d1, s2, r2, o2, d2))
                
                # Garder les meilleures paires (interference creative)
                pairs.sort(key=lambda x: -abs(x[0] - 0.55))  # plus proche de 0.55 = creatif
                
                for _, s1, r1, o1, d1, s2, r2, o2, d2 in pairs[:2]:
                    templates = [
                        "Les concepts de {s1} ({d1}) et {s2} ({d2}) entrent en resonance. "
                        "En {d1}, {s1} {r1} {o1}. En {d2}, {s2} {r2} {o2}. "
                        "Leur interference suggere une connexion inedite entre ces deux univers.",
                        
                        "Une connexion inattendue emerge : {s1} ({d1}) et {s2} ({d2}). "
                        "D'un cote, {s1} {r1} {o1}. De l'autre, {s2} {r2} {o2}. "
                        "L'interference de leurs ondes revele un pont entre {d1} et {d2}.",
                    ]
                    idea = random.choice(templates).format(
                        s1=s1, r1=r1, o1=o1, d1=d1,
                        s2=s2, r2=r2, o2=o2, d2=d2)
                    all_ideas.append(idea)
        
        # Diversite : une idee par paire de domaines
        selected = []
        seen_pairs = set()
        for idea in all_ideas:
            doms = re.findall(r'\(([A-Z]+)\)', idea)
            pair = tuple(sorted(doms[:2])) if len(doms) >= 2 else None
            if pair and pair not in seen_pairs:
                selected.append(idea)
                seen_pairs.add(pair)
            if len(selected) >= n_ideas:
                break
        
        return selected[:n_ideas]
    
    def metaphor(self, theme: str = None, n_metaphores: int = 3) -> List[str]:
        """
        Genere des METAPHORES poetiques par interference.
        
        Une metaphore nait quand deux concepts de domaines DIFFERENTS
        interferent de maniere MODEREE (0.3-0.6). Ni trop proches
        (banal), ni trop eloignes (absurde). C'est l'entre-deux
        qui produit l'etincelle poetique.
        
        Args:
            theme: theme central (ou None pour exploration libre)
            n_metaphores: nombre de metaphores
        
        Returns:
            Liste de metaphores
        """
        kx, ky, w2i = self.model.kx, self.model.ky, self.model.w2i
        kb = self.model.knowledge_base
        
        # Collecter les sujets par domaine
        subjects_by_domain = {}
        for s, r, o, sec in kb:
            dom = SECTOR_TO_DOMAIN.get(sec, 'GENERAL')
            if dom not in subjects_by_domain:
                subjects_by_domain[dom] = []
            if s in w2i and s not in subjects_by_domain[dom]:
                subjects_by_domain[dom].append(s)
        
        domains = list(subjects_by_domain.keys())
        metaphores = []
        
        for d1 in domains:
            for d2 in domains:
                if d1 >= d2:
                    continue
                for s1 in subjects_by_domain[d1][:15]:
                    if s1 not in w2i: continue
                    for s2 in subjects_by_domain[d2][:15]:
                        if s2 not in w2i: continue
                        i1, i2 = w2i[s1], w2i[s2]
                        dot = kx[i1]*kx[i2] + ky[i1]*ky[i2]
                        interf = (dot + 1.0) / 2.0
                        # Zone metaphorique : 0.35-0.65
                        if 0.35 < interf < 0.65:
                            templates = [
                                "{s1} est le {s2} de l'ame.",
                                "Comme {s1} epouse {s2}, le silence epouse la nuit.",
                                "Il y a du {s1} dans chaque {s2}, et du {s2} dans chaque {s1}.",
                                "{s1} danse avec {s2} dans le jardin des idees.",
                                "Si {s1} etait une note, {s2} serait son harmonique.",
                            ]
                            metaphores.append(random.choice(templates).format(s1=s1, s2=s2))
                            if len(metaphores) >= n_metaphores * 3:
                                break
                    if len(metaphores) >= n_metaphores * 3: break
                if len(metaphores) >= n_metaphores * 3: break
            if len(metaphores) >= n_metaphores * 3: break
        
        # Dedup et diversite
        seen = set()
        unique = []
        for m in metaphores:
            key = m[:40]
            if key not in seen:
                seen.add(key)
                unique.append(m)
        
        return unique[:n_metaphores]
    
    def haiku(self, theme: str = None) -> str:
        """
        Genere un HAIKU par interference.
        
        Structure : 3 vers (5-7-5 syllabes approx.)
        Les concepts sont selectionnes par interference creative.
        """
        kx, ky, w2i = self.model.kx, self.model.ky, self.model.w2i
        kb = self.model.knowledge_base
        
        # Trouver 3 concepts qui interferent de maniere creative
        subjects = []
        for s, r, o, sec in kb:
            if s in w2i and s not in subjects:
                subjects.append(s)
        
        if len(subjects) < 3:
            return "Pas assez de concepts pour un haiku."
        
        # Selectionner 3 concepts avec interferences mutuelles interessantes
        best_trio = None
        best_score = 0
        for _ in range(100):
            i1, i2, i3 = random.sample(range(min(50, len(subjects))), 3)
            s1, s2, s3 = subjects[i1], subjects[i2], subjects[i3]
            if s1 not in w2i or s2 not in w2i or s3 not in w2i:
                continue
            interfs = []
            for a, b in [(i1,i2), (i2,i3), (i1,i3)]:
                dot = kx[w2i[subjects[a]]]*kx[w2i[subjects[b]]] + ky[w2i[subjects[a]]]*ky[w2i[subjects[b]]]
                interfs.append((dot+1)/2)
            # Score : variance des interferences (diversite creative)
            score = np.std(interfs) + (0.3 < np.mean(interfs) < 0.7) * 0.1
            if score > best_score:
                best_score = score
                best_trio = (s1, s2, s3)
        
        if not best_trio:
            return "L'interference ne trouve pas son chemin."
        
        s1, s2, s3 = best_trio
        templates = [
            f"{s1} dans le vent\n{s2} murmure a {s3}\nle secret des ondes",
            f"Un {s1} eclot\n{s2} et {s3} se repondent\nl'univers respire",
            f"Dans le {s1} profond\n{s2} caresse {s3}\nl'instant suspendu",
        ]
        return random.choice(templates)
    
    def surreal(self, n_images: int = 3) -> List[str]:
        """
        Genere des IMAGES SURREALISTES par interference eloignee (0.1-0.3).
        
        Le surrealisme nait de la rencontre de concepts TRES eloignes
        qui interferent faiblement — l'etincelle du hasard objectif.
        """
        kx, ky, w2i = self.model.kx, self.model.ky, self.model.w2i
        kb = self.model.knowledge_base
        
        subjects = []
        for s, r, o, sec in kb:
            if s in w2i and len(s) > 3 and s not in subjects:
                subjects.append(s)
        
        images = []
        for _ in range(200):
            i1, i2 = random.sample(range(len(subjects)), 2)
            s1, s2 = subjects[i1], subjects[i2]
            if s1 not in w2i or s2 not in w2i: continue
            dot = kx[w2i[s1]]*kx[w2i[s2]] + ky[w2i[s1]]*ky[w2i[s2]]
            interf = (dot + 1.0) / 2.0
            if 0.15 < interf < 0.35:  # zone surrealiste
                templates = [
                    f"J'ai vu un {s1} qui buvait du {s2} a la terrasse d'un cafe.",
                    f"Le {s1} ouvrit ses ailes de {s2} et s'envola vers le nord.",
                    f"Dans la foret de {s1}, les {s2} chantent a l'envers.",
                    f"Un {s1} fondait lentement sur le rebord du {s2}.",
                ]
                images.append(random.choice(templates).format(s1=s1, s2=s2))
                if len(images) >= n_images:
                    break
        
        return images[:n_images]


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from harmonic_model import HarmonicModel
    
    print("=" * 60)
    print("REASONING ENGINE v2 — Architecture généralisée")
    print("  Un moteur. Domaine détecté automatiquement.")
    print("=" * 60)
    
    model = HarmonicModel(use_memory=False)
    engine = ReasoningEngine(model)
    
    tests = [
        ("pourquoi le coeur pompe le sang", "BIOLOGIE"),
        ("explique la lumiere", "PHYSIQUE"),
        ("qu est ce que la gravite", "PHYSIQUE"),
        ("comment fonctionne la resonance", "PHYSIQUE"),
        ("qu est ce que la conscience", "CONSCIENCE"),
        ("parle moi de l amour", "EMOTION"),
        ("explique le nombre d or", "MATHS"),
        ("qu est ce que dieu", "PHILOSOPHIE"),
    ]
    
    for q, expected_domain in tests:
        paths = find_paths(model.knowledge_base, q)
        if paths:
            domain = detect_domain(paths[0])
            response = render_path(paths[0], q, domain)
            match = "✅" if domain == expected_domain else "⚠️"
            print(f"\n{match} [{domain}] >> {q}")
            print(f"   << {response[:150]}...")


if __name__ == '__main__':
    demo()
