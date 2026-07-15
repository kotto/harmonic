"""
Wave Poetry — Générateur de poésie par interférences ondulatoires
====================================================================
Les LLM écrivent de la poésie parce que l'attention = résonance.
Nous pouvons faire la même chose — explicitement.

PRINCIPES ONDULATOIRES DE LA POÉSIE :

  1. RIME = cohérence de phase terminale
     Deux mots riment quand leurs ψ ont des composantes fréquentielles
     similaires dans les derniers phonèmes. C'est une cohérence de phase
     localisée en fin de vecteur.

  2. RYTHME = modulation périodique d'amplitude
     Les syllabes accentuées sont des pics d'amplitude. Le mètre
     (alexandrin, octosyllabe) est une fréquence de modulation.

  3. ALLITÉRATION = filtrage spectral
     Répéter un son = appliquer un filtre passe-bande au spectre
     des mots sélectionnés.

  4. LIGNE = discontinuité de phase
     Un saut de ligne crée un déphasage. Le ψ se réinitialise
     partiellement, créant une respiration visuelle.

  5. ÉMOTION = rotation de phase sectorielle
     Un poème triste active les secteurs EMOTION_NEG.
     Un poème d'amour active EMOTION_POS.
     Cette activation module quels mots résonnent.

  6. POÉSIE PERSONNELLE = interférence ψ_topic ⊗ ψ_hologramme
     Le poème le plus puissant est celui qui fait interférer
     le thème poétique avec l'hologramme personnel de l'utilisateur.

Usage :
    from wave_poetry import WavePoet

    poet = WavePoet()
    
    # Poème général
    poem = poet.compose("la mer", form="free_verse")
    
    # Poème personnel (basé sur l'hologramme)
    poem = poet.compose_personal("Ma pratique médicale", personal_facts=[...])
"""

import math, re, random, logging
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
TAU = 2.0 * math.pi
PHI_INV = 1.0 / PHI

# ═══════════════════════════════════════════════════════════════════════════════
# VOCABULAIRE POÉTIQUE — mots avec signatures ondulatoires
# ═══════════════════════════════════════════════════════════════════════════════

# Banque de mots poétiques classés par "phase émotionnelle"
POETIC_VOCABULARY = {
    # Phase ~0 : Lumière, espoir, naissance, amour (EMOTION_POS)
    'lumiere': [
        'aube', 'aurore', 'clarté', 'éclat', 'rayon', 'flamme', 'étincelle',
        'soleil', 'étoile', 'ciel', 'azur', 'or', 'blancheur', 'aile',
        'source', 'printemps', 'fleur', 'rosée', 'chant', 'rire', 'sourire',
        'joie', 'bonheur', 'grâce', 'beauté', 'tendresse', 'douceur', 'caresse',
        'baiser', 'étreinte', 'regard', 'promesse', 'espoir', 'aube', 'matin',
        'renouveau', 'naissance', 'germer', 'éclore', 'fleurir', 'rayonner',
        'briller', 'luire', 'resplendir', 'illuminer', 'éblouir', 'scintiller',
        'cristal', 'diamant', 'perle', 'rosée', 'pétale', 'pollen', 'nectar',
        'miel', 'ambre', 'nacre', 'ivoire', 'saphir', 'émeraude', 'rubis',
        'enfant', 'berceau', 'innocence', 'pureté', 'virginité', 'premier',
        'arc-en-ciel', 'colombe', 'alouette', 'rossignol', 'papillon', 'libellule',
    ],
    # Phase ~π/4 : Nature, éléments, paysages
    'nature': [
        'mer', 'océan', 'vague', 'marée', 'écume', 'embrun', 'rivage', 'grève',
        'plage', 'dune', 'falaise', 'rocher', 'galet', 'coquillage', 'corail',
        'forêt', 'bois', 'sous-bois', 'clairière', 'feuillage', 'ramure', 'branchage',
        'mousse', 'lichen', 'fougère', 'champignon', 'écorce', 'sève', 'résine',
        'montagne', 'sommet', 'cime', 'pic', 'crête', 'versant', 'vallée', 'gouffre',
        'torrent', 'cascade', 'source', 'ruisseau', 'rivière', 'fleuve', 'lac', 'étang',
        'vent', 'brise', 'bourrasque', 'tempête', 'ouragan', 'cyclone', 'zéphyr', 'souffle',
        'pluie', 'averse', 'ondée', 'giboulée', 'bruine', 'grêle', 'neige', 'givre',
        'orage', 'foudre', 'éclair', 'tonnerre', 'nuage', 'brume', 'brouillard', 'rosée',
    ],
    # Phase ~π/3 : Mouvement, vie, passage, voyage
    'mouvement': [
        'vent', 'vague', 'fleuve', 'course', 'danse', 'souffle', 'élan',
        'flux', 'marée', 'rivière', 'nuage', 'oiseau', 'feuille', 'pollen',
        'sillage', 'trace', 'chemin', 'pas', 'route', 'voyage', 'errance',
        'dérive', 'traversée', 'passage', 'franchir', 'gravir', 'descendre',
        'courir', 'voler', 'planer', 'glisser', 'couler', 'rouler', 'bondir',
        'sauter', 'fendre', 'traverser', 'parcourir', 'cheminer', 'vagabonder',
        'pèlerin', 'nomade', 'voyageur', 'marin', 'navigateur', 'explorateur',
        'boussole', 'voile', 'navire', 'barque', 'radeau', 'pirogue', 'caravelle',
    ],
    # Phase ~π/2 : Mystère, rêve, intériorité, nuit
    'mystere': [
        'ombre', 'nuit', 'silence', 'secret', 'mémoire', 'âme', 'cœur',
        'rêve', 'profondeur', 'abîme', 'brume', 'brouillard', 'voile',
        'écho', 'reflet', 'miroir', 'lune', 'éther', 'infini', 'néant',
        'mystère', 'énigme', 'labyrinthe', 'dédale', 'arcane', 'oracle',
        'songe', 'chimère', 'fantôme', 'spectre', 'apparition', 'mirage',
        'crépuscule', 'minuit', 'aube', 'pénombre', 'ténèbres', 'obscurité',
        'sommeil', 'éveil', 'insomnie', 'torpeur', 'léthargie', 'hypnose',
        'ailleurs', 'invisible', 'inaudible', 'impalpable', 'insaisissable',
        'astral', 'cosmique', 'sidéral', 'stellaire', 'galactique', 'céleste',
    ],
    # Phase ~π : Douleur, mélancolie, perte, automne (EMOTION_NEG)
    'douleur': [
        'larme', 'pleur', 'blessure', 'cicatrice', 'absence', 'vide',
        'hiver', 'nuit', 'cendre', 'poussière', 'ruine', 'débris',
        'orage', 'pluie', 'froid', 'cri', 'silence', 'pierre', 'fer', 'sel',
        'deuil', 'chagrin', 'peine', 'souffrance', 'douleur', 'tourment',
        'angoisse', 'détresse', 'désespoir', 'mélancolie', 'nostalgie',
        'regret', 'remords', 'solitude', 'isolement', 'abandon', 'exil',
        'automne', 'feuille morte', 'déclin', 'crépuscule', 'soir', 'adieu',
        'sépulture', 'tombe', 'ossuaire', 'poussière', 'ossements', 'relique',
        'fêlure', 'brisure', 'fracture', 'déchirure', 'plaie', 'meurtrissure',
        'sang', 'sueur', 'larme', 'cendre', 'fumée', 'braise', 'étincelle',
    ],
    # Phase ~5π/4 : Temps, mémoire, histoire
    'temps': [
        'temps', 'heure', 'instant', 'moment', 'éternité', 'siècle', 'âge',
        'passé', 'présent', 'futur', 'avenir', 'jadis', 'naguère', 'autrefois',
        'souvenir', 'mémoire', 'oubli', 'réminiscence', 'nostalgie', 'regret',
        'horloge', 'sablier', 'clepsydre', 'cadran', 'aiguille', 'balancier',
        'saison', 'printemps', 'été', 'automne', 'hiver', 'équinoxe', 'solstice',
        'jeunesse', 'maturité', 'vieillesse', 'enfance', 'adolescence', 'sagesse',
        'cycle', 'ronde', 'spirale', 'retour', 'recommencement', 'renaissance',
        'ruine', 'vestige', 'trace', 'empreinte', 'fossile', 'sédiment', 'strate',
    ],
    # Phase ~3π/2 : Sagesse, paix, acceptation, mort
    'sagesse': [
        'paix', 'calme', 'sérénité', 'sagesse', 'patience', 'terre',
        'racine', 'arbre', 'pierre', 'montagne', 'horizon', 'ciel',
        'éternité', 'repos', 'sommeil', 'oubli', 'pardon', 'aube', 'fin',
        'mort', 'tombeau', 'cercueil', 'linceul', 'épitaphe', 'dernier',
        'silence', 'acceptation', 'résignation', 'détachement', 'renoncement',
        'plénitude', 'complétude', 'achèvement', 'accomplissement', 'parachèvement',
        'essence', 'substance', 'quintessence', 'absolu', 'totalité', 'unité',
        'moine', 'ermite', 'sage', 'ancêtre', 'aïeul', 'vieillard', 'ancien',
        'temple', 'sanctuaire', 'autel', 'offrande', 'encens', 'prière', 'méditation',
    ],
    # Phase ~7π/4 : Feu, passion, intensité
    'passion': [
        'feu', 'brasier', 'incendie', 'volcan', 'lave', 'magma', 'fournaise',
        'passion', 'désir', 'ardeur', 'fièvre', 'ivresse', 'extase', 'fureur',
        'colère', 'rage', 'courroux', 'ire', 'foudre', 'éclair', 'tempête',
        'cri', 'hurlement', 'rugissement', 'clameur', 'tumulte', 'vacarme',
        'rouge', 'pourpre', 'cramoisi', 'écarlate', 'vermillon', 'incarnat',
        'sang', 'cœur', 'pouls', 'battement', 'palpitation', 'pulsation',
        'guerre', 'combat', 'lutte', 'bataille', 'duel', 'joute', 'assaut',
    ],
}

# Connecteurs poétiques — variations de phase légère
POETIC_CONNECTORS = [
    "où", "et", "qui", "que", "dans", "sous", "sur", "vers",
    "parmi", "entre", "comme", "ainsi", "tel", "telle",
    "là-bas", "ici", "toujours", "jamais", "encore", "déjà",
    "doucement", "lentement", "silencieux", "immobile",
    "invisible", "lointain", "profond", "ancien",
]

# Structures de vers par forme poétique
VERSE_STRUCTURES = {
    'free_verse': [
        lambda s, v, o: f"{s} {v} {o}",
        lambda s, v, o: f"{o} du {s}",
        lambda s, v, o: f"dans le {s}, {o}",
        lambda s, v, o: f"{s} et {o}",
        lambda s, v, o: f"le {s} de l'{o}",
    ],
    'alexandrin': [
        # 12 syllabes — structure classique
        lambda s, v, o: f"Quand le {s} profond {v} vers l'{o} éternel",
        lambda s, v, o: f"Le {s} silencieux {v} l'{o} du temps",
    ],
    'haiku_wave': [
        # 5-7-5 syllabes adaptées au français
        lambda s, v, o: f"{s} dans le {v}",
        lambda s, v, o: f"{o} du {s} ancien",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE POET
# ═══════════════════════════════════════════════════════════════════════════════

class WavePoet:
    """
    Poète ondulatoire — génère de la poésie par résonance de phase.
    
    Contrairement aux templates (qui remplissent des blancs), 
    le WavePoet sélectionne des mots par cohérence avec l'intention poétique.
    """
    
    def __init__(self, dim: int = None):
        self._learned = None
        self._poetry_emb = None
        self.dim = dim or 512
        self._init_encoder()  # Peut ajuster self.dim si un encodeur est chargé
        
        self._word_cache: Dict[str, np.ndarray] = {}
        self._build_poetic_cache()
    
    def _init_encoder(self):
        """Initialise l'encodeur sémantique. Priorité: poetry_embedding > learned_embedding > hash."""
        self._encoder = None
        self._learned = None
        self._poetry_emb = None
        
        import os
        emb_dir = os.path.dirname(__file__)
        
        # 1. Tenter l'encodeur poétique (spécialisé)
        poetry_path = os.path.join(emb_dir, 'data', 'poetry_embedding.npz')
        if os.path.exists(poetry_path):
            try:
                from learned_embedding import LearnedEmbedding
                self._poetry_emb = LearnedEmbedding()
                self._poetry_emb.load(poetry_path)
                log.info(f"Encodeur poétique chargé: {len(self._poetry_emb.vectors)} mots poétiques")
            except Exception as e:
                log.info(f"Encodeur poétique non chargé: {e}")
        
        # 2. Fallback: encodeur général
        if self._poetry_emb is None:
            gen_path = os.path.join(emb_dir, 'data', 'learned_embedding.npz')
            if os.path.exists(gen_path):
                try:
                    from learned_embedding import LearnedEmbedding
                    self._learned = LearnedEmbedding()
                    self._learned.load(gen_path)
                    log.info(f"Encodeur général chargé: {len(self._learned.vectors)} mots")
                except Exception as e:
                    log.info(f"Encodeur général non chargé: {e}")
        
        # Ajuster la dimension
        if self._poetry_emb and self._poetry_emb.is_trained:
            self.dim = self._poetry_emb.complex_dim  # 16
        elif self._learned and self._learned.is_trained:
            self.dim = self._learned.complex_dim  # 64
        else:
            self.dim = 512
    
    def _encode(self, text: str) -> np.ndarray:
        """Encode un texte en ψ. Priorité: poetry_emb > learned_emb > hash."""
        # 1. Tenter l'encodeur poétique
        for emb in [self._poetry_emb, self._learned]:
            if emb and emb.is_trained:
                words = text.lower().split()
                vectors = []
                for w in words:
                    w_clean = w.strip('.,;:!?()[]{}«»\"\'')
                    if w_clean in emb.vectors:
                        vectors.append(emb.vectors[w_clean])
                if vectors:
                    result = sum(vectors) / len(vectors)
                    return result / (np.linalg.norm(result) + 1e-10)
        
        # 2. Fallback: hash déterministe
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        return v / (np.linalg.norm(v) + 1e-10)
    
    def _coherence(self, a: np.ndarray, b: np.ndarray) -> float:
        if a is None or b is None:
            return 0.0
        dot = np.abs(np.dot(a.conj(), b))
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        return min(1.0, float(dot / (na * nb + 1e-10)))
    
    def _bind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        A = np.fft.fft(a)
        B = np.fft.fft(b)
        result = np.fft.ifft(A * B)
        return result / (np.linalg.norm(result) + 1e-10)
    
    def _build_poetic_cache(self):
        """Pré-encode les mots poétiques avec l'encodeur poétique."""
        all_words = set()
        for phase, words in POETIC_VOCABULARY.items():
            all_words.update(words)
        
        poetry_hits = 0
        for word in all_words:
            psi = self._encode(word)
            self._word_cache[word] = psi
            if self._poetry_emb and word in self._poetry_emb.vectors:
                poetry_hits += 1
        
        log.info(f"Cache poétique: {len(self._word_cache)} mots "
                 f"({poetry_hits} dans l'encodeur poétique, dim={self.dim})")
    
    def _french_grammar(self, line: str) -> str:
        """Corrige la grammaire française de base (élision, espaces)."""
        # Élision : le/la → l' devant voyelle ou h muet
        line = re.sub(r'\ble\s+([aeiouyâêîôûäëïöüÿh])', r"l'\1", line)
        line = re.sub(r'\bla\s+([aeiouyâêîôûäëïöüÿh])', r"l'\1", line)
        line = re.sub(r'\bde le\b', 'du', line)
        line = re.sub(r'\bde les\b', 'des', line)
        line = re.sub(r'\bà le\b', 'au', line)
        line = re.sub(r'\bà les\b', 'aux', line)
        line = re.sub(r'\bde\s+([aeiouyâêîôûäëïöüÿh])', r"d'\1", line)
        # Genre : remplacer 'le' devant mots féminins courants (approximation)
        feminine = {'tombe', 'vallée', 'rosée', 'aurore', 'poussière', 'feuille',
                    'cicatrice', 'blessure', 'larme', 'cendre', 'pluie', 'neige',
                    'foudre', 'brume', 'colombe', 'alouette', 'libellule',
                    'pierre', 'terre', 'racine', 'sève', 'mousse', 'fougère',
                    'forêt', 'clairière', 'montagne', 'cime', 'crête',
                    'source', 'rivière', 'cascade', 'grève', 'dune', 'falaise',
                    'écorce', 'résine', 'braise', 'fumée', 'trace', 'empreinte',
                    'mémoire', 'souffrance', 'douleur', 'angoisse', 'détresse',
                    'solitude', 'plénitude', 'quintessence', 'essence',
                    'fièvre', 'ivresse', 'extase', 'fureur', 'colère', 'rage',
                    'guerre', 'bataille', 'lutte', 'joute', 'saison',
                    'chaleur', 'fraîcheur', 'douceur', 'tendresse',
                    'sagesse', 'patience', 'sérénité', 'paix', 'joie',
                    'beauté', 'grâce', 'pureté', 'innocence', 'enfance',
                    'jeunesse', 'maturité', 'vieillesse', 'renaissance',
                    'naissance', 'mort', 'nuit', 'mer', 'fin'}
        for fem in feminine:
            line = re.sub(r'\ble\s+(' + fem + r')\b', r'la \1', line)
        # Nettoyage
        line = re.sub(r' {2,}', ' ', line)
        line = line.strip()
        return line[0].upper() + line[1:] if line else line
    
    def _select_words_diverse(self, psi_intention, emotional_phase, count, exclude=None):
        """
        Sélection diversifiée : prend des mots de différentes phases
        pour éviter la répétition monotone.
        """
        if exclude is None:
            exclude = set()
        
        all_phases = list(POETIC_VOCABULARY.keys())
        # Prioriser la phase émotionnelle, puis alterner
        ordered_phases = [emotional_phase] + [p for p in all_phases if p != emotional_phase]
        
        selected = []
        used = set(exclude)
        phase_idx = 0
        
        while len(selected) < count and phase_idx < len(ordered_phases) * 3:
            phase = ordered_phases[phase_idx % len(ordered_phases)]
            candidates = POETIC_VOCABULARY.get(phase, [])
            
            # Trouver le meilleur mot de cette phase pas encore utilisé
            best = None
            best_coh = 0
            for word in candidates:
                if word in used:
                    continue
                psi_word = self._word_cache.get(word)
                if psi_word is not None:
                    coh = self._coherence(psi_intention, psi_word) + random.uniform(-0.03, 0.03)
                    if coh > best_coh:
                        best_coh = coh
                        best = word
            
            if best:
                selected.append(best)
                used.add(best)
            
            phase_idx += 1
        
        return selected
    
    def _find_rhyme(self, word: str, phase: str, used: set) -> Optional[str]:
        """
        Trouve un mot qui rime par cohérence de phase terminale.
        
        La rime n'est pas une correspondance de lettres — c'est une
        cohérence de phase dans les derniers phonèmes du mot.
        """
        psi_word = self._word_cache.get(word)
        if psi_word is None:
            return None
        
        candidates = POETIC_VOCABULARY.get(phase, [])
        # Ajouter des mots de toutes les phases
        for words in POETIC_VOCABULARY.values():
            candidates.extend(words)
        
        best = None
        best_coh = 0
        
        for candidate in candidates:
            if candidate in used or candidate == word:
                continue
            psi_candidate = self._word_cache.get(candidate)
            if psi_candidate is None:
                continue
            
            # Mesurer la cohérence (rime = haute cohérence)
            coh = self._coherence(psi_word, psi_candidate)
            
            # Bonus pour similarité phonétique approximative
            # (fin de mot similaire = rime traditionnelle)
            if len(word) >= 3 and len(candidate) >= 3:
                if word[-2:] == candidate[-2:]:
                    coh += 0.3
                if word[-3:] == candidate[-3:]:
                    coh += 0.5
            
            if coh > best_coh and candidate not in used:
                best_coh = coh
                best = candidate
        
        return best
    
    def _determine_emotional_phase(self, theme: str, emotion: str = None) -> str:
        """Détermine la phase émotionnelle dominante du poème."""
        theme_lower = theme.lower()
        
        # Détection par mots-clés
        sadness = ['triste', 'mort', 'perte', 'deuil', 'absence', 'pleur', 'larme',
                   'mélancolie', 'nostalgie', 'regret', 'adieu']
        joy = ['joie', 'amour', 'bonheur', 'fête', 'rire', 'sourire', 'lumière',
               'espoir', 'printemps', 'aube', 'naissance', 'célébration']
        mystery = ['rêve', 'mystère', 'nuit', 'ombre', 'secret', 'âme', 'infini',
                   'étrange', 'magie', 'surnaturel']
        peace = ['paix', 'calme', 'sagesse', 'acceptation', 'sérénité', 'repos']
        
        for word in sadness:
            if word in theme_lower: return 'douleur'
        for word in joy:
            if word in theme_lower: return 'lumiere'
        for word in mystery:
            if word in theme_lower: return 'mystere'
        for word in peace:
            if word in theme_lower: return 'sagesse'
        
        if emotion:
            mapping = {'triste': 'douleur', 'joyeux': 'lumiere', 'mystérieux': 'mystere',
                      'paisible': 'sagesse', 'dynamique': 'mouvement'}
            return mapping.get(emotion, 'mystere')
        
        return 'mystere'  # Phase par défaut = mystère/intériorité
    
    # ═══ COMPOSITION ═══
    
    def compose(self, theme: str, form: str = 'free_verse', 
                emotion: str = None, lines: int = 8,
                personal_facts: List[str] = None) -> dict:
        """
        Compose un poème par interférences ondulatoires.
        
        Args:
            theme: le thème du poème
            form: 'free_verse', 'alexandrin', 'haiku_wave', 'sonnet_wave'
            emotion: 'triste', 'joyeux', 'mystérieux', 'paisible', 'dynamique'
            lines: nombre de vers (approx.)
            personal_facts: faits personnels à intégrer (pour poésie personnelle)
        
        Returns:
            dict avec 'text', 'form', 'theme', 'emotion', 'rhyme_scheme'
        """
        # 1. Encoder l'intention poétique
        psi_theme = self._encode(theme)
        emotional_phase = self._determine_emotional_phase(theme, emotion)
        
        # 2. Créer ψ_emotion par rotation de phase
        phase_angles = {
            'lumiere': 0.0,
            'mouvement': math.pi / 3,
            'mystere': math.pi / 2,
            'douleur': math.pi,
            'sagesse': 3 * math.pi / 2,
        }
        theta = phase_angles.get(emotional_phase, math.pi / 2)
        psi_emotion = np.exp(1j * theta) * np.ones(self.dim, dtype=np.complex128)
        
        # 3. Binding : ψ_poétique = ψ_thème ⊗ ψ_émotion
        psi_poetic = self._bind(psi_theme, psi_emotion)
        
        # 4. Si contexte personnel : interférence avec ψ_personnel
        if personal_facts:
            psi_personal = np.zeros(self.dim, dtype=np.complex128)
            for fact in personal_facts[:5]:
                psi_fact = self._encode(fact)
                psi_personal += psi_fact
            psi_personal /= (np.linalg.norm(psi_personal) + 1e-10)
            psi_poetic = 0.7 * psi_poetic + 0.3 * psi_personal
        
        # 5. Sélectionner les mots par résonance (diversifiée)
        all_words = self._select_words_diverse(psi_poetic, emotional_phase, count=lines * 2 + 6)
        
        # 6. Construire les vers
        poem_lines = []
        used_rhyme_words = set()
        n_words = len(all_words)
        
        for i in range(min(lines, n_words // 2)):
            word_a = all_words[i]
            word_b = all_words[i + lines] if i + lines < n_words else all_words[-1]
            
            structures = VERSE_STRUCTURES.get(form, VERSE_STRUCTURES['free_verse'])
            structure = structures[i % len(structures)]
            
            # Construire le vers
            line = structure(word_a, ' ', word_b)
            line = re.sub(r' {2,}', ' ', line).strip()
            
            # Ajouter un connecteur si le vers est trop court
            if len(line.split()) < 3:
                connector = random.choice(POETIC_CONNECTORS[:15])
                line = f"{word_a} {connector} le {word_b}"
            
            # Appliquer la grammaire française
            line = self._french_grammar(line)
            
            if line and len(line) > 4:
                poem_lines.append(line)
        
        # 7. Ajouter une chute (dernier vers marquant)
        if poem_lines and lines >= 4 and n_words > lines:
            final_word = all_words[-1]
            closings = [
                f"et demeure l'{final_word}.",
                f"où seul l'{final_word} répond.",
                f"comme un dernier {final_word}.",
                f"dans le silence de l'{final_word}.",
                f"vers l'{final_word} éternel.",
            ]
            closing = random.choice(closings)
            closing = self._french_grammar(closing)
            poem_lines.append(closing)
        
        poem_text = '\n'.join(poem_lines)
        
        return {
            'text': poem_text,
            'form': form,
            'theme': theme,
            'emotion': emotional_phase,
            'lines': len(poem_lines),
            'words_used': len(set(all_words)),
            'vocab_size': len(POETIC_VOCABULARY),
        }
    
    def compose_personal(self, theme: str, user_id: str = None,
                         personal_facts: List[str] = None,
                         form: str = 'free_verse') -> dict:
        """
        Compose un poème PERSONNEL basé sur l'hologramme utilisateur.
        
        C'est ici que KA devient unique : le poème n'est pas générique,
        il est tissé à partir des traces, corrections, et connaissances
        que l'utilisateur a accumulées.
        """
        facts = personal_facts or []
        
        # Si pas de faits fournis, essayer de charger depuis l'hologramme
        if not facts and user_id:
            try:
                from personal_hologram import PersonalHologram
                ph = PersonalHologram(user_id)
                profile = ph.profile()
                if profile.top_concepts:
                    facts = [f"Tu t'intéresses à {c}" for c in profile.top_concepts[:5]]
                # Ajouter les domaines
                for interest in profile.top_domains[:3]:
                    facts.append(f"Tu explores le domaine {interest.domain}")
            except Exception:
                pass
        
        if facts:
            theme = f"{theme} — pour toi"
        
        return self.compose(theme, form=form, personal_facts=facts)
    
    def stats(self) -> dict:
        return {
            'poetic_vocabulary': len(self._word_cache),
            'phases': list(POETIC_VOCABULARY.keys()),
            'forms': list(VERSE_STRUCTURES.keys()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  🌊 WAVE POETRY — Démonstration                            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    poet = WavePoet()
    
    # Test 1 : Poèmes par thème et émotion
    tests = [
        ("la mer", "free_verse", "mystérieux"),
        ("l'amour perdu", "free_verse", "triste"),
        ("le printemps", "free_verse", "joyeux"),
        ("la sagesse", "alexandrin", "paisible"),
        ("l'infini", "haiku_wave", "mystérieux"),
    ]
    
    for theme, form, emotion in tests:
        print(f"{'='*50}")
        print(f"  Thème: {theme} | Forme: {form} | Émotion: {emotion}")
        print(f"{'='*50}")
        result = poet.compose(theme, form=form, emotion=emotion)
        print(result['text'])
        print(f"  -- {result['lines']} vers, rime: {result['has_rhyme']}")
        print()
    
    # Test 2 : Poème personnel (avec hologramme simulé)
    print(f"{'='*50}")
    print(f"  POÈME PERSONNEL (simulation)")
    print(f"{'='*50}")
    personal = poet.compose_personal(
        "ta pratique médicale",
        personal_facts=[
            "Tu m'as appris le protocole paludisme",
            "Tu poses souvent des questions sur le diagnostic",
            "Hier tu as cherché choc septique trois fois",
            "Ta spécialité est la médecine tropicale",
            "Tu consultes 50 patients par jour",
        ]
    )
    print(personal['text'])
    print()
    
    # Test 3 : Comparaison avec l'ancien générateur (templates)
    print(f"{'='*50}")
    print(f"  COMPARAISON : Template vs Wave")
    print(f"{'='*50}")
    print()
    print("TEMPLATE (ancien creative_generator.py) :")
    print("  Dans le rêve du monde,")
    print("  où les vents s'effeuillent,")
    print("  je cherche le ciel")
    print("  qui habite chaque ombre.")
    print()
    print("WAVE (nouveau wave_poetry.py) :")
    result = poet.compose("le monde", emotion="mystérieux")
    print("  " + result['text'].replace('\n', '\n  '))
    print()
    print(f"  Mots uniques : {result['words_used']} | Rime : {result['has_rhyme']}")
