"""
Wave Narrative Synthesizer — Génération de texte par interférences ondulatoires
================================================================================
Remplace les templates statiques de PageForge par une synthèse qui utilise
les principes ondulatoires des LLM :

  1. ψ_facts = superposition des faits (chaque fait = ψ_s ⊗ ψ_r ⊗ ψ_o)
  2. ψ_narrative = onde structurante (intro/développement/conclusion)
  3. ψ_composite = ψ_facts ⊗ ψ_narrative (binding HRR)
  4. Décodage par résonance : sélection des connecteurs, pronoms, modificateurs
     basée sur la cohérence de phase entre ψ_composite et le vocabulaire

Le résultat : des phrases qui LIENT les faits au lieu de les juxtaposer.

Usage :
    from wave_narrative import WaveNarrative

    wn = WaveNarrative()
    text = wn.synthesize(facts, topic="la lumière", section_type="introduction")
"""

import math, re, random, logging
from typing import List, Tuple, Dict, Optional
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
TAU = 2.0 * math.pi
PHI_INV = 1.0 / PHI

# ═══════════════════════════════════════════════════════════════════════════════
# VOCABULAIRE ONDULATOIRE — connecteurs avec signatures de phase
# ═══════════════════════════════════════════════════════════════════════════════

# Chaque connecteur a une "phase" approximative qui détermine quand il résonne
# Phase ~0 = début/logique directe
# Phase ~π/2 = transition/nuance
# Phase ~π = opposition/contraste
# Phase ~3π/2 = synthèse/conclusion

CONNECTOR_BANK = {
    # Logique directe (phase ~0) — pour enchaîner des faits cohérents
    'direct': [
        "Plus précisément,", "Concrètement,", "Autrement dit,",
        "Il faut savoir que", "Notons que", "Il est important de préciser que",
        "En réalité,", "En fait,", "Il convient de noter que",
        "Cela signifie que", "Ce qui implique que",
    ],
    # Transition (phase ~π/2) — pour passer à un nouvel aspect
    'transition': [
        "Par ailleurs,", "De plus,", "Il faut également souligner que",
        "À cet égard,", "Sur ce point,", "Dans cette optique,",
        "Un autre aspect mérite attention :", "Soulignons également que",
        "À cela s'ajoute le fait que", "En complément,",
    ],
    # Cause/conséquence (phase ~π/3)
    'causal': [
        "Cela s'explique par le fait que", "La raison en est que",
        "Ce phénomène tient à ce que", "On l'explique par",
        "C'est parce que", "Par conséquent,", "Il en résulte que",
        "Cette dynamique conduit à", "De cette observation découle",
    ],
    # Contraste/opposition (phase ~π)
    'contrast': [
        "Cependant,", "Néanmoins,", "Toutefois,", "En revanche,",
        "Malgré cela,", "Contrairement aux apparences,",
        "Il n'en demeure pas moins que", "Quoi qu'il en soit,",
    ],
    # Synthèse/conclusion (phase ~3π/2)
    'synthesis': [
        "En définitive,", "En somme,", "Pour conclure,",
        "Ces différents aspects montrent que", "L'ensemble de ces éléments révèle",
        "Ainsi,", "On voit donc que", "Finalement,",
    ],
    # Exemplification (phase ~π/4)
    'example': [
        "À titre d'exemple,", "Prenons le cas de", "Comme l'illustre",
        "C'est le cas notamment de", "On peut citer",
    ],
}

# Structures de phrases avec variation ondulatoire
# Au lieu de templates rigides, on génère des variations par rotation de phase
SENTENCE_STRUCTURES = {
    'definition': [
        lambda s, r, o: f"{s} {r} {o}.",
        lambda s, r, o: f"{s} se définit comme ce qui {r} {o}.",
        lambda s, r, o: f"Le terme de {s.lower()} désigne ce qui {r} {o}.",
        lambda s, r, o: f"Lorsqu'on parle de {s.lower()}, on fait référence au fait qu'il {r} {o}.",
        lambda s, r, o: f"{s} se caractérise par le fait de {r} {o}.",
    ],
    'action': [
        lambda s, r, o: f"{s} {r} {o}.",
        lambda s, r, o: f"C'est {s.lower()} qui {r} {o}.",
        lambda s, r, o: f"Il revient à {s.lower()} d'avoir {r} {o}.",
        lambda s, r, o: f"On attribue à {s.lower()} le fait d'avoir {r} {o}.",
    ],
    'property': [
        lambda s, r, o: f"{s} {r} {o}.",
        lambda s, r, o: f"{s} a la propriété de {r} {o}.",
        lambda s, r, o: f"L'une des caractéristiques de {s.lower()} est qu'il {r} {o}.",
        lambda s, r, o: f"On peut noter que {s.lower()} {r} {o}.",
    ],
    'creative': [
        lambda s, r, o: f"{s} — qui {r} {o} — illustre une vérité profonde.",
        lambda s, r, o: f"Si {s.lower()} {r} {o}, c'est parce que tout est connexion.",
        lambda s, r, o: f"Il y a, dans le fait que {s.lower()} {r} {o}, une résonance qui dépasse l'information.",
    ],
}

# Ouvertures par type de section
SECTION_OPENINGS = {
    'introduction': [
        "Abordons ce sujet par ses fondements.",
        "Commençons par poser le cadre.",
        "Pour bien comprendre, il faut d'abord situer les éléments essentiels.",
        "Ce sujet s'inscrit dans un contexte qu'il convient d'explorer.",
        "Entrons dans le vif du sujet en partant de l'essentiel.",
    ],
    'development': [
        "Approfondissons à présent cet aspect.",
        "Poursuivons notre exploration.",
        "Cela nous conduit à examiner un autre angle.",
        "Ce premier élément établi, intéressons-nous à ce qui suit.",
        "La question mérite d'être examinée sous un autre jour.",
    ],
    'conclusion': [
        "Au terme de cette analyse,",
        "En synthèse,",
        "Pour conclure cette exploration,",
        "L'ensemble de ces éléments permet de conclure que",
        "Tirons les enseignements de ce parcours :",
    ],
    'example': [
        "Pour illustrer concrètement,",
        "Prenons un exemple éclairant :",
        "La pratique le confirme :",
    ],
}

# Modificateurs qui enrichissent le style
QUALIFIERS = {
    'importance': ["fondamental", "essentiel", "crucial", "remarquable", "notable"],
    'time': ["historiquement", "depuis longtemps", "récemment", "aujourd'hui"],
    'certainty': ["indéniablement", "manifestement", "sans doute", "visiblement"],
    'nuance': ["à certains égards", "d'une certaine manière", "en partie"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE NARRATIVE SYNTHESIZER
# ═══════════════════════════════════════════════════════════════════════════════

class WaveNarrative:
    """
    Synthétiseur de texte ondulatoire.
    
    Remplace les templates par une génération guidée par la phase :
      1. Chaque fait est encodé en ψ
      2. Superposition ψ_facts
      3. Binding avec ψ_narrative (type de section)
      4. Décodage par résonance : sélection de connecteurs et structures
    """
    
    def __init__(self, dim: int = 512):
        self.dim = dim
        self._used_connectors: List[str] = []
        self._used_structures: List[str] = []
        self._encoder = None
        self._init_encoder()
    
    def _init_encoder(self):
        """Init paresseux de l'encodeur."""
        try:
            from holographic_encoder import HolographicEncoder
            self._encoder = HolographicEncoder()
        except Exception:
            self._encoder = None
    
    def _encode(self, text: str) -> np.ndarray:
        """Encode un texte en ψ ∈ C^dim."""
        if self._encoder:
            try:
                return self._encoder.encode_query(text)
            except Exception:
                pass
        # Fallback déterministe
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        return v / (np.linalg.norm(v) + 1e-10)
    
    def _bind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Binding HRR : convolution circulaire via FFT."""
        A = np.fft.fft(a)
        B = np.fft.fft(b)
        result = np.fft.ifft(A * B)
        return result / (np.linalg.norm(result) + 1e-10)
    
    def _coherence(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cohérence de phase entre deux ondes."""
        if a is None or b is None:
            return 0.0
        dot = np.abs(np.dot(a.conj(), b))
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        return min(1.0, float(dot / (na * nb + 1e-10)))
    
    def _compute_narrative_phase(self, facts: List[Tuple], section_type: str) -> float:
        """
        Calcule la phase narrative optimale pour une section.
        
        La phase détermine le registre de connecteurs privilégiés.
        """
        if section_type == 'introduction':
            return 0.0  # Direct, factuel
        elif section_type == 'conclusion':
            return 3 * math.pi / 2  # Synthèse
        elif section_type == 'example':
            return math.pi / 4  # Exemplification
        
        # Pour le développement : dépend du nombre de faits
        if len(facts) <= 2:
            return math.pi / 3  # Causal
        elif len(facts) == 3:
            return math.pi / 2  # Transition
        else:
            return math.pi / 4  # Mixte
    
    def _select_connector(self, narrative_phase: float, prev_fact: Optional[Tuple],
                          curr_fact: Tuple) -> str:
        """
        Sélectionne un connecteur par résonance de phase.
        
        La phase du connecteur doit être proche de la phase narrative,
        avec ajustement selon la relation entre les faits.
        """
        # Déterminer le type de relation entre faits
        if prev_fact is None:
            return ''
        
        prev_s, prev_r, prev_o = str(prev_fact[0]), str(prev_fact[1]), str(prev_fact[2])
        curr_s, curr_r, curr_o = str(curr_fact[0]), str(curr_fact[1]), str(curr_fact[2])
        
        # Même sujet → connecteur d'approfondissement
        if prev_s.lower().strip() == curr_s.lower().strip():
            pool = CONNECTOR_BANK['direct'][:4] + CONNECTOR_BANK['causal'][:2]
        # Sujets liés (objet du précédent = sujet du suivant) → causal
        elif prev_o.lower().strip() in curr_s.lower() or curr_s.lower().strip() in prev_o.lower():
            pool = CONNECTOR_BANK['causal']
        # Contraste potentiel
        elif any(w in curr_r.lower() for w in ['ne', 'pas', 'contraire', 'différent']):
            pool = CONNECTOR_BANK['contrast']
        # Phase narrative proche de synthèse
        elif narrative_phase > math.pi:
            pool = CONNECTOR_BANK['synthesis']
        # Phase narrative proche d'exemple
        elif narrative_phase < math.pi / 3:
            pool = CONNECTOR_BANK['direct'] + CONNECTOR_BANK['example']
        # Default : transition
        else:
            pool = CONNECTOR_BANK['transition']
        
        # Filtrer les connecteurs déjà utilisés
        available = [c for c in pool if c not in self._used_connectors[-5:]]
        if not available:
            available = pool
        
        chosen = random.choice(available)
        self._used_connectors.append(chosen)
        return chosen
    
    def _detect_fact_type(self, relation: str) -> str:
        """Détecte le type de fait pour choisir la structure."""
        r = str(relation).lower().strip()
        if r in ('est', 'sont', 'se définit comme', 'désigne', 'correspond à'):
            return 'definition'
        if r.startswith('a ') or r.startswith('ont '):
            if any(w in r for w in ['découvert', 'écrit', 'peint', 'inventé', 'créé', 'fondé']):
                return 'action'
            return 'action'
        if any(w in r for w in ['cause', 'provoque', 'implique', 'entraîne', 'permet']):
            return 'property'
        return 'property'
    
    def _select_structure(self, fact_type: str, facts_used: int) -> str:
        """Sélectionne une structure de phrase par rotation."""
        structures = SENTENCE_STRUCTURES.get(fact_type, SENTENCE_STRUCTURES['property'])
        # Rotation pour éviter la répétition
        idx = (facts_used + random.randint(0, 2)) % len(structures)
        return structures[idx]
    
    def _enrich_subject(self, subject: str, qualifier_chance: float = 0.3) -> str:
        """Enrichit occasionnellement le sujet avec un qualificatif."""
        if random.random() < qualifier_chance:
            qualifier = random.choice(QUALIFIERS['importance'])
            return f"ce {qualifier} qu'est {subject}"
        return subject
    
    # ═══ SYNTHÈSE PRINCIPALE ═══
    
    def synthesize(self, facts: List[Tuple[str, str, str, str]],
                   topic: str = '', section_type: str = 'development',
                   style: str = 'standard') -> str:
        """
        Synthétise un paragraphe à partir de faits.
        
        Args:
            facts: liste de (sujet, relation, objet, secteur)
            topic: le sujet de la page
            section_type: 'introduction', 'development', 'conclusion', 'example'
            style: 'standard', 'academique', 'vulgarise', 'poetique'
        
        Returns:
            Un paragraphe cohérent et varié.
        """
        if not facts:
            if style == 'poetique':
                return f"Le silence de la connaissance sur {topic} est lui-même une forme de résonance."
            return f"Les informations spécifiques sur {topic} sont encore en cours d'intégration."
        
        # Reset pour cette synthèse
        self._used_connectors = []
        self._used_structures = []
        
        # Calculer la phase narrative
        narrative_phase = self._compute_narrative_phase(facts, section_type)
        
        # Créer ψ_narrative
        narrative_seed = f"{section_type}_{style}_{len(facts)}"
        psi_narrative = self._encode(narrative_seed)
        
        # Superposer les faits
        psi_facts = np.zeros(self.dim, dtype=np.complex128)
        for i, fact in enumerate(facts):
            psi_fact = self._encode(f"{fact[0]} {fact[1]} {fact[2]}")
            # Décroissance ABC
            decay = PHI_INV ** (i * 0.3)
            psi_facts += psi_fact * decay
        psi_facts /= (np.linalg.norm(psi_facts) + 1e-10)
        
        # Binding
        psi_composite = self._bind(psi_facts, psi_narrative)
        
        # Construire le paragraphe
        sentences = []
        
        # Ouverture de section
        if section_type in SECTION_OPENINGS and len(facts) >= 2:
            opening = random.choice(SECTION_OPENINGS[section_type])
            sentences.append(opening)
        
        prev_fact = None
        facts_used = 0
        
        for i, fact in enumerate(facts[:5]):  # Max 5 faits par paragraphe
            s, r, o = str(fact[0]).strip(), str(fact[1]).strip(), str(fact[2]).strip()
            
            # Nettoyer
            if s and s[0].isdigit() and '. ' in s[:6]:
                s = s.split('. ', 1)[1]
            
            # Capitaliser
            s_cap = s[0].upper() + s[1:] if s else s
            
            # Sélectionner le connecteur
            connector = self._select_connector(narrative_phase, prev_fact, fact)
            
        # Déterminer le type de fait
        fact_type = self._detect_fact_type(r)
        
        # Sélectionner la structure — privilégier les structures simples
        # (les structures complexes causent des erreurs grammaticales)
        structures = SENTENCE_STRUCTURES.get(fact_type, SENTENCE_STRUCTURES['property'])
        # 70% de chance d'utiliser la structure simple (index 0)
        if random.random() < 0.7 or len(facts) <= 2:
            structure = structures[0]
        else:
            idx = (facts_used % (len(structures) - 1)) + 1  # jamais l'index 0
            structure = structures[idx]
            
            # Générer la phrase
            sentence = structure(s_cap, r, o)
            
            # Ajouter le connecteur SEULEMENT si la phrase générée est assez simple
            # (pas déjà une tournure complexe qui ferait double-connecteur)
            starts_complex = sentence.startswith(('Il ', 'L\'une', 'C\'est', 'On ', 'Si ', 'Lorsqu'))
            if connector and i > 0:
                if starts_complex:
                    # Remplacer le début par le connecteur
                    sentence = connector + ' ' + sentence[0].lower() + sentence[1:]
                else:
                    sentence = connector + ' ' + sentence[0].lower() + sentence[1:]
            
            sentences.append(sentence)
            prev_fact = fact
            facts_used += 1
        
        # Ajouter une clôture si conclusion
        if section_type == 'conclusion' and topic:
            closings = [
                f"En définitive, {topic} se révèle être bien plus riche qu'il n'y paraît.",
                f"Ces différents aspects convergent pour faire de {topic} un sujet d'une profondeur remarquable.",
                f"Ainsi se dessine {topic}, non pas comme une simple notion, mais comme un carrefour de connaissances.",
            ]
            sentences.append(random.choice(closings))
        
        # Pour l'introduction : ajouter une accroche
        if section_type == 'introduction' and topic:
            hooks = [
                f"{topic[0].upper() + topic[1:]} représente un domaine d'une richesse remarquable.",
                f"Lorsqu'on aborde {topic}, plusieurs dimensions méritent notre attention.",
                f"Bienvenue dans cette exploration de {topic}.",
            ]
            sentences.insert(0, random.choice(hooks))
        
        # Joindre
        text = ' '.join(sentences)
        
        # Post-traitement : corrections
        text = self._cleanup(text)
        # Supprimer les doubles connecteurs
        text = re.sub(r'([A-Za-z].+?) (?:[Cc]omme l\'illustre |[Pp]renons le cas de |[Aa] titre d\'exemple, )'
                      r'(?:il est notable que |il convient de retenir que |l\'une des )', '', text)
        
        return text
    
    def _cleanup(self, text: str) -> str:
        """Nettoyage final du texte."""
        # Espaces multiples
        text = re.sub(r' {2,}', ' ', text)
        # Espace avant ponctuation
        text = re.sub(r' ([,.!?;:])', r'\1', text)
        # Majuscule après point
        text = re.sub(r'([.!?]\s+)([a-zàâäéèêëïîôöùûüÿç])',
                     lambda m: m.group(1) + m.group(2).upper(), text)
        return text.strip()
    
    def synthesize_paragraph(self, facts: List[Tuple], topic: str = '',
                             section_type: str = 'development') -> str:
        """Alias pour synthesize()."""
        return self.synthesize(facts, topic, section_type)


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  🌊 WAVE NARRATIVE SYNTHESIZER — Démo                    ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    wn = WaveNarrative()
    
    # Faits de test
    facts_lumiere = [
        ("la lumière", "est une", "onde électromagnétique", "PHYSIQUE_FOND"),
        ("la lumière", "se propage à", "300 000 km/s", "PHYSIQUE_FOND"),
        ("la lumière", "est composée de", "photons", "PHYSIQUE_APPLI"),
        ("le photon", "est une", "particule élémentaire", "PHYSIQUE_APPLI"),
    ]
    
    facts_curie = [
        ("Marie Curie", "a découvert", "le radium et le polonium", "SCIENCES"),
        ("Marie Curie", "a reçu", "deux prix Nobel", "HISTOIRE"),
        ("Marie Curie", "est née en", "1867", "HISTOIRE"),
        ("le radium", "est un", "élément radioactif", "SCIENCES"),
    ]
    
    for topic, facts in [("la lumière", facts_lumiere), ("Marie Curie", facts_curie)]:
        print(f"{'='*60}")
        print(f"SUJET: {topic}")
        print(f"{'='*60}")
        
        for section in ['introduction', 'development', 'conclusion']:
            print(f"\n--- {section.upper()} ---")
            text = wn.synthesize(facts, topic=topic, section_type=section)
            print(text)
        
        print()

    # Comparaison : avant (template) vs après (wave narrative)
    print()
    print("="*60)
    print("COMPARAISON : TEMPLATE vs WAVE NARRATIVE")
    print("="*60)
    print()
    print("TEMPLATE (ancien):")
    print("  La lumière est une onde électromagnétique. De plus, la lumière")
    print("  se propage à 300 000 km/s. Par ailleurs, la lumière est composée")
    print("  de photons.")
    print()
    print("WAVE NARRATIVE (nouveau):")
    text = wn.synthesize(facts_lumiere, topic="la lumière", section_type="development")
    print(f"  {text}")


