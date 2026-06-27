"""
Tokenizer Harmonique PUR — Version BPE simplifiée
===================================================
Tokenizer base sur les mots frequents (français + anglais) pour
le modele HarmonicPureForCausalLM.

Vocabulaire de 5000 tokens :
- 0: <PAD>
- 1: <UNK>
- 2: <BOS>
- 3: <EOS>
- 4-4999: mots frequents

Pour un vrai LLM de production, utiliser un vrai tokenizer BPE
(huggingface tokenizers). Ici on fait un tokenizer minimal mais
fonctionnel pour la Phase 1.
"""

import re
import json
from typing import List, Dict, Optional
from pathlib import Path


# =========================================================================
# VOCABULAIRE DE BASE
# =========================================================================

# 2000 mots français les plus fréquents
FRENCH_WORDS = [
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "est",
    "a", "dans", "que", "qui", "pas", "ne", "sur", "pour", "avec",
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "ce", "cet", "cette", "ces", "mon", "ton", "son", "ma", "ta", "sa",
    "mes", "tes", "ses", "nos", "vos", "leurs",
    "au", "aux", "en", "par", "plus", "moins", "tres", "aussi",
    "comme", "si", "mais", "ou", "donc", "car", "ni", "or",
    "faire", "fais", "fait", "dire", "dit", "dis", "avoir", "a",
    "etre", "suis", "es", "est", "sommes", "etes", "sont", "sois",
    "aller", "vais", "va", "vas", "allons", "allez", "vont",
    "pouvoir", "peux", "peut", "pouvons", "pouvez", "peuvent",
    "vouloir", "veux", "veut", "voulons", "voulez", "veulent",
    "savoir", "sais", "sait", "savons", "savez", "savent",
    "voir", "vois", "voit", "voyons", "voyez", "voient",
    "venir", "viens", "vient", "venons", "venez", "viennent",
    "prendre", "prends", "prend", "prenons", "prenez", "prennent",
    "donner", "donne", "donnes", "donnons", "donnez", "donnent",
    "parler", "parle", "parles", "parlons", "parlez", "parlent",
    "temps", "chose", "monde", "vie", "homme", "femme", "enfant",
    "jour", "nuit", "ans", "mois", "semaine", "annee", "heure",
    "question", "reponse", "probleme", "solution", "idee", "raison",
    "travail", "maison", "ville", "pays", "eau", "feu", "terre",
    "ciel", "soleil", "lune", "etoile", "nombre", "lettre", "mot",
    "phrase", "histoire", "page", "livre", "titre", "nom", "prenom",
    "grand", "petit", "beau", "bon", "mauvais", "vrai", "faux",
    "nouveau", "vieux", "jeune", "long", "court", "haut", "bas",
    "plein", "vide", "fort", "faible", "lent", "rapide", "clair",
    "sombre", "chaud", "froid", "doux", "dur", "facile", "difficile",
    "important", "necessaire", "possible", "impossible", "certain",
    "premier", "dernier", "prochain", "suivant", "autre", "meme",
    "tout", "tous", "toute", "toutes", "chaque", "quelque", "plusieurs",
    "aucun", "nul", "rien", "personne", "jamais", "toujours",
    "souvent", "parfois", "rarement", "beaucoup", "peu", "trop",
    "assez", "environ", "presque", "encore", "deja", "enfin",
    "alors", "apres", "avant", "depuis", "pendant", "durant",
    "jusque", "vers", "chez", "entre", "sans", "sous", "devant",
    "derriere", "contre", "malgre", "selon", "grace", "loin",
    "pres", "ici", "la", "ailleurs", "partout", "dessus", "dessous",
    "maintenant", "aujourdhui", "hier", "demain", "bientot",
    "tard", "tot", "matin", "soir", "midi", "minuit",
    "bonjour", "bonsoir", "salut", "adieu", "merci", "pardon",
    "oui", "non", "peut-etre", "voici", "voila", "comment",
    "pourquoi", "combien", "quel", "quelle", "quels", "quelles",
    "ceci", "cela", "ca", "ici", "la-bas",
    "harmonie", "resonance", "frequence", "vibration", "onde",
    "phi", "nombre", "or", "divin", "proportion", "doree",
    "cosmos", "univers", "nature", "mathematique", "physique",
    "conscience", "esprit", "ame", "pensee", "intelligence",
    "connaissance", "sagesse", "verite", "beaute", "amour",
    "paix", "joie", "lumiere", "energie", "force",
    "harmonique", "resonnant", "vibratoire", "spirituel",
    "science", "technologie", "innovation", "creation",
    "algorithme", "donnee", "information", "reseau", "neurone",
    "apprentissage", "profond", "modele", "entrainement",
    "langage", "texte", "token", "sequence", "contexte",
    "attention", "memoire", "emotion", "raisonnement",
    "creativite", "intuition", "logique", "analyse", "synthese",
    "epsilon", "alpha", "beta", "gamma", "delta", "theta", "omega",
    "infini", "zero", "unite", "dualite", "triade",
    "matiere", "energie", "espace", "temps", "lumière",
    "electron", "proton", "neutron", "atome", "molecule",
    "cellule", "vie", "evolution", "adaptation", "selection",
    "systeme", "complexe", "chaos", "ordre", "fractale",
    "geometrie", "symetrie", "harmonie", "musique", "silence",
    "art", "poesie", "danse", "couleur", "forme",
    "profondeur", "hauteur", "largeur", "dimension", "mesure",
    "poids", "masse", "vitesse", "acceleration", "force",
    "travail", "puissance", "efficacite", "rendement", "performance",
    "amelioration", "progres", "developpement", "croissance",
    "avenir", "destin", "liberte", "volonte", "action",
    "cause", "effet", "hasard", "necessite", "contingence",
    "theorie", "pratique", "experience", "observation", "mesure",
    "hypothese", "these", "antithese", "synthese", "dialectique",
    "methode", "technique", "outil", "instrument", "machine",
    "automatique", "artificiel", "naturel", "humain", "divin",
    "langage", "parole", "ecriture", "lecture", "comprehension",
    "traduction", "interpretation", "sens", "signification",
    "question", "repondre", "demander", "expliquer", "comprendre",
    "apprendre", "enseigner", "former", "eduquer", "instruire",
    "recherche", "decouverte", "invention", "innovation",
    "revolution", "transformation", "changement", "mutation",
    "quantique", "classique", "relativite", "gravite", "champ",
    "particule", "onde", "dualite", "superposition",
    "intrication", "decoherence", "mesure", "observateur",
    "probabilite", "statistique", "distribution", "moyenne",
    "variance", "ecart", "correlation", "causalite",
    "fractale", "iteration", "attracteur", "bifurcation",
    "limite", "continuite", "derivee", "integrale",
    "differentiel", "fractionnaire", "atangana", "baleanu",
    "noyau", "memoire", "non-locale", "convolution",
    "signal", "bruit", "filtre", "transformation",
    "fourier", "wavelet", "harmonique", "spectre",
    "complexite", "entropie", "information", "ordre",
    "emergence", "auto-organisation", "resilience", "robustesse",
    "seuil", "critique", "transition", "phase",
    "equilibre", "stabilite", "instabilite", "fluctuation",
    "cycle", "rythme", "periode", "frequence", "amplitude",
    "phase", "decalage", "interference", "resonance",
    "echo", "reflet", "miroir", "symetrie", "dissymetrie",
    "pattern", "motif", "structure", "organisation",
    "hierarchie", "niveau", "echelle", "dimension",
    "macro", "micro", "meso", "nano", "cosmique",
    "observation", "theorie", "modele", "simulation",
    "prediction", "controle", "optimisation", "decision",
    "strategie", "plan", "objectif", "mission", "vision",
    "valeur", "ethique", "morale", "principe", "regle",
    "loi", "norme", "standard", "qualite", "excellence",
    "perfection", "limite", "defaut", "erreur", "echec",
    "reussite", "succes", "victoire", "triomphe", "gloire",
    "humilite", "courage", "perseverance", "patience",
    "confiance", "espoir", "foi", "certitude", "doute",
    "dualite", "contraire", "oppose", "complementaire",
    "yin", "yang", "ombre", "lumiere", "masculin", "feminin",
    "actif", "passif", "receptif", "emettant", "attirant",
    "repoussant", "liant", "separant", "unissant", "divisant",
    "harmonieux", "dissonant", "consonant", "melodique",
    "rythmique", "tonal", "atonal", "modal", "polyphonique",
    "symphonie", "concerto", "sonate", "cantate", "oratorio",
    "virtuose", "maestro", "compositeur", "interpretation",
    "note", "accord", "gamme", "intervalle", "octave",
    "quinte", "quarte", "tierce", "seconde", "septieme",
    "do", "re", "mi", "fa", "sol", "la", "si",
    "piano", "violon", "guitare", "flute", "harpe",
    "instrument", "orchestre", "cheur", "soliste",
    "resonnance", "vibration", "frequence", "harmonique",
    "fondamental", "partiel", "timbre", "intensite",
    "pythagore", "platon", "aristote", "euclide", "archimede",
    "newton", "einstein", "planck", "schrodinger", "heisenberg",
    "bohr", "dirac", "feynman", "hawking", "turing",
    "godel", "cantor", "ramanujan", "euler", "gauss",
    "riemann", "poincare", "hilbert", "neumann", "shannon",
    "fibonacci", "lucas", "pell", "fermat", "leibniz",
    "descartes", "kant", "hegel", "nietzsche", "spinoza",
    "kotto", "alain", "createur", "chercheur", "pionnier",
    "inspiration", "revelation", "intuition", "genie",
    "visionnaire", "explorateur", "decouvreur", "inventeur",
    "atlantide", "atlante", "atlanteum", "atlantien",
    "mysterium", "scientia", "harmonia", "universalis",
    "aether", "prima", "materia", "anima", "mundi",
    "lapis", "philosophalis", "magnum", "opus",
]

# 2000 mots anglais les plus fréquents
ENGLISH_WORDS = [
    "the", "be", "to", "of", "and", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say",
    "her", "she", "or", "an", "will", "my", "one", "all",
    "would", "there", "their", "what", "so", "up", "out",
    "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just",
    "him", "know", "take", "people", "into", "year",
    "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its",
    "over", "think", "also", "back", "after", "use",
    "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these",
    "give", "day", "most", "us",
    "great", "between", "need", "large", "often", "hand",
    "high", "place", "small", "under", "long", "right",
    "still", "house", "world", "last", "school", "never",
    "own", "country", "help", "every", "start", "group",
    "city", "point", "play", "form", "child", "little",
    "state", "system", "program", "number", "water",
    "part", "case", "fact", "company", "money", "service",
    "life", "line", "end", "health", "reason", "power",
    "law", "result", "car", "city", "problem", "community",
    "name", "president", "team", "minute", "idea", "kid",
    "body", "information", "back", "parent", "face", "level",
    "office", "door", "road", "point", "market", "center",
    "war", "class", "note", "force", "price", "material",
    "nature", "color", "food", "sex", "art", "science",
    "region", "real", "energy", "music", "data", "space",
    "word", "nature", "earth", "love", "light", "think",
    "feel", "hear", "speak", "write", "read", "learn",
    "teach", "build", "grow", "find", "keep", "bring",
    "leave", "show", "move", "live", "believe", "hold",
    "try", "ask", "tell", "need", "want", "change",
    "follow", "turn", "set", "run", "begin", "mean",
    "let", "open", "create", "produce", "develop",
    "increase", "reduce", "improve", "support", "allow",
    "include", "require", "provide", "consider", "appear",
    "happen", "remember", "expect", "decide", "accept",
    "complete", "understand", "suggest", "explain",
    "recognize", "achieve", "prepare", "discover",
    "receive", "describe", "determine", "obtain",
    "contain", "perform", "maintain", "establish",
    "cognitive", "neural", "network", "deep", "learning",
    "machine", "intelligence", "artificial", "algorithm",
    "model", "training", "data", "feature", "layer",
    "attention", "transformer", "embedding", "token",
    "weight", "gradient", "optimization", "loss",
    "prediction", "classification", "regression",
    "generation", "understanding", "reasoning",
    "consciousness", "awareness", "perception",
    "quantum", "physics", "mathematics", "universe",
    "consciousness", "mind", "brain", "thought",
    "frequency", "vibration", "wave", "particle",
    "resonance", "harmonic", "golden", "ratio",
    "phi", "fibonacci", "spiral", "fractal",
    "chaos", "complexity", "emergence", "pattern",
    "symmetry", "beauty", "truth", "wisdom",
    "knowledge", "science", "philosophy", "mystery",
    "spiritual", "transcendence", "enlightenment",
    "limitation", "possibility", "potential",
    "innovation", "revolution", "transformation",
    "evolution", "adaptation", "selection",
    "survival", "growth", "development",
    "communication", "language", "meaning",
    "expression", "creation", "imagination",
    "intuition", "inspiration", "genius",
    "harmonious", "balanced", "integrated",
    "unified", "holistic", "systemic",
    "deep", "profound", "essential", "fundamental",
    "universal", "eternal", "infinite", "absolute",
    "relative", "dynamic", "static", "fluid",
    "flexible", "adaptive", "resilient", "robust",
    "efficient", "effective", "optimal", "perfect",
    "sacred", "geometry", "proportion", "divine",
    "ancient", "wisdom", "tradition", "modern",
    "future", "vision", "dream", "reality",
    "exploration", "discovery", "adventure",
    "journey", "path", "way", "method",
    "practice", "experience", "experiment",
    "observation", "analysis", "synthesis",
    "theory", "hypothesis", "proof", "evidence",
    "logic", "reason", "rational", "empirical",
    "intuitive", "creative", "imaginative",
    "innovative", "original", "unique", "special",
    "extraordinary", "remarkable", "amazing",
    "wonderful", "beautiful", "magnificent",
    "splendid", "glorious", "majestic", "sublime",
    "elegant", "graceful", "refined", "cultured",
    "sophisticated", "complex", "nuanced",
    "subtle", "delicate", "precise", "accurate",
    "exact", "perfect", "flawless", "impeccable",
    "code", "program", "software", "system",
    "interface", "application", "platform",
    "technology", "digital", "virtual",
    "cyber", "space", "network", "cloud",
    "compute", "process", "memory", "storage",
    "analysis", "visualization", "simulation",
    "design", "architecture", "framework",
    "library", "module", "component", "function",
    "variable", "constant", "parameter", "argument",
    "input", "output", "process", "result",
    "success", "achievement", "mastery",
    "excellence", "quality", "perfection",
    "wisdom", "knowledge", "understanding",
    "compassion", "kindness", "love", "peace",
    "joy", "happiness", "fulfillment",
    "purpose", "meaning", "significance",
    "quest", "search", "inquiry", "question",
    "answer", "solution", "resolution",
    "key", "secret", "mystery", "revelation",
    "insight", "understanding", "awareness",
    "presence", "mindfulness", "attention",
    "focus", "concentration", "meditation",
    "contemplation", "reflection", "observation",
    "stillness", "silence", "emptiness", "fullness",
    "nothingness", "everything", "oneness",
    "unity", "diversity", "harmony", "balance",
    "resonance", "sympathy", "empathy", "connection",
    "relationship", "bond", "link", "bridge",
    "portal", "gateway", "threshold", "beginning",
    "end", "cycle", "circle", "sphere", "cube",
    "tetrahedron", "octahedron", "dodecahedron",
    "icosahedron", "platonic", "solid", "polyhedron",
    "pi", "euler", "infinity", "zero", "one",
    "dimension", "frequency", "vibration",
    "kotto", "alain", "harmonia", "universalis",
    "harmonic", "ai", "artificial", "intelligence",
    "consciousness", "evolution", "humanity",
    "future", "technology", "spirituality",
    "integration", "transformation", "awakening",
    "breakthrough", "paradigm", "shift",
    "new", "era", "age", "dawn", "light",
]

# Caracteres de ponctuation courants
PUNCTUATION = [
    ".", ",", "!", "?", ";", ":", "\"", "'", "(", ")",
    "[", "]", "{", "}", "-", "_", "—", "…",
    "/", "\\", "@", "#", "$", "%", "&", "*",
    "+", "=", "~", "`", "<", ">", "|",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "φ", "π", "∞", "√", "∑", "∏", "∫", "∂", "∆", "∇",
    "∈", "∉", "⊂", "⊃", "∩", "∪", "∧", "∨", "¬", "⇒",
    "⇔", "∀", "∃", "∄", "≈", "≠", "≡", "≤", "≥",
]


def build_vocab(vocab_size: int = 5000) -> Dict[str, int]:
    """
    Construit un vocabulaire de taille donnee.
    
    Args:
        vocab_size: Taille du vocabulaire (max 5000)
    
    Returns:
        token_to_id: Dictionnaire mot -> id
    """
    vocab_size = min(vocab_size, 5000)
    
    # Tokens speciaux
    token_to_id = {
        "<PAD>": 0,
        "<UNK>": 1,
        "<BOS>": 2,
        "<EOS>": 3,
    }
    
    # Mots francais
    remaining = vocab_size - len(token_to_id)
    half = remaining // 2
    
    for word in FRENCH_WORDS:
        if len(token_to_id) >= vocab_size:
            break
        if word not in token_to_id:
            token_to_id[word] = len(token_to_id)
    
    for word in ENGLISH_WORDS:
        if len(token_to_id) >= vocab_size:
            break
        if word not in token_to_id:
            token_to_id[word] = len(token_to_id)
    
    # Ponctuation
    for p in PUNCTUATION:
        if len(token_to_id) >= vocab_size:
            break
        if p not in token_to_id:
            token_to_id[p] = len(token_to_id)
    
    return token_to_id


class HarmonicTokenizer:
    """
    Tokenizer harmonique base sur un vocabulaire de mots frequents.
    
    Usage:
        tokenizer = HarmonicTokenizer(vocab_size=5000)
        tokens = tokenizer.encode("Bonjour le monde")
        texte = tokenizer.decode(tokens)
    """
    
    def __init__(self, vocab_size: int = 5000):
        self.vocab_size = min(vocab_size, 5000)
        self.token_to_id = build_vocab(self.vocab_size)
        self.id_to_token = {v: k for k, v in self.token_to_id.items()}
        
        self.pad_id = 0
        self.unk_id = 1
        self.bos_id = 2
        self.eos_id = 3
    
    @property
    def vocab_size(self):
        return self._vocab_size
    
    @vocab_size.setter
    def vocab_size(self, value):
        self._vocab_size = min(value, 5000)
    
    def get_vocab_size(self) -> int:
        """Retourne la taille reelle du vocabulaire."""
        return len(self.token_to_id)
    
    def _tokenize_word(self, word: str) -> List[str]:
        """
        Decoupe un mot en sous-mots si necessaire.
        
        Pour le moment, garde les mots entiers.
        Les mots inconnus sont remplaces par <UNK>.
        """
        # Nettoyer le mot (minuscules, enlever accents simples)
        word = word.lower().strip()
        if not word:
            return []
        return [word]
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """
        Encode un texte en tokens.
        
        Args:
            text: Texte a encoder
            add_special_tokens: Ajouter <BOS> et <EOS>
        
        Returns:
            List d'ids de tokens
        """
        # Decouper en mots (separation basique)
        words = re.findall(r"\w+|[^\w\s]", text.lower())
        
        tokens = []
        for word in words:
            if word in self.token_to_id:
                tokens.append(self.token_to_id[word])
            else:
                tokens.append(self.unk_id)
        
        if add_special_tokens:
            tokens = [self.bos_id] + tokens + [self.eos_id]
        
        return tokens
    
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode des tokens en texte.
        
        Args:
            token_ids: Liste d'ids de tokens
            skip_special_tokens: Ignorer <PAD>, <BOS>, <EOS>, <UNK>
        
        Returns:
            Texte decode
        """
        special = {self.pad_id, self.bos_id, self.eos_id}
        if skip_special_tokens:
            special.add(self.unk_id)
        
        words = []
        for tid in token_ids:
            if skip_special_tokens and tid in special:
                if tid == self.unk_id:
                    words.append("<?>")
                continue
            word = self.id_to_token.get(tid, "<?>")
            words.append(word)
        
        return " ".join(words)
    
    def encode_batch(self, texts: List[str]) -> List[List[int]]:
        """Encode un batch de textes."""
        return [self.encode(t) for t in texts]
    
    def save(self, path: str):
        """Sauvegarde le vocabulaire."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.token_to_id, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str, vocab_size: int = 5000):
        """Charge un vocabulaire sauvegarde."""
        with open(path, 'r', encoding='utf-8') as f:
            token_to_id = json.load(f)
        instance = cls(vocab_size=len(token_to_id))
        instance.token_to_id = token_to_id
        instance.id_to_token = {v: k for k, v in token_to_id.items()}
        return instance
    
    def __len__(self):
        return len(self.token_to_id)


# =========================================================================
# TEST
# =========================================================================

def test_tokenizer():
    """Teste le tokenizer."""
    tokenizer = HarmonicTokenizer(vocab_size=5000)
    
    print(f"Vocabulaire: {tokenizer.get_vocab_size()} tokens")
    
    # Tests d'encodage
    texts = [
        "Bonjour le monde",
        "Hello world",
        "Le nombre d or phi vaut 1.618",
        "Harmonic resonance is beautiful",
        "φ = 1.618033988749895",
    ]
    
    for text in texts:
        tokens = tokenizer.encode(text)
        decoded = tokenizer.decode(tokens)
        coverage = sum(1 for t in tokens if t != tokenizer.unk_id) / max(len(tokens), 1)
        print(f"\n  Texte: {text}")
        print(f"  Tokens: {tokens}")
        print(f"  Decode: {decoded}")
        print(f"  Couverture: {coverage:.0%}")
    
    print(f"\n[OK] Tokenizer operationnel ({tokenizer.get_vocab_size()} tokens)")
    return tokenizer


if __name__ == '__main__':
    test_tokenizer()
