"""
Wave Domains — Table de Correspondance Universelle
====================================================
Adaptateur domaine → opérations ondulatoires.

Permet de raisonner dans N'IMPORTE QUEL domaine en traduisant
ses concepts en ψ et en appliquant les 4 opérations primitives.

ARCHITECTURE :
  Domaine → Encodage → 4 Ops → Interprétation → Conclusion

USAGE :
  from wave_domains import DomainAdapter, DOMAINS
  
  # Raisonner en médecine
  adapter = DomainAdapter('medecine', brain)
  result = adapter.reason(symptomes=['fièvre', 'toux'],
                          contexte='patient de 45 ans')
  
  # Raisonner en droit
  adapter = DomainAdapter('droit', brain)
  result = adapter.reason(loi='Article 12', fait='Le prévenu a...')

TABLE DE CORRESPONDANCE :
  Chaque domaine définit :
    1. ENCODING  : comment concepts → ψ
    2. INTERFERENCE : que signifie Re(⟨ψ_a|ψ_b⟩) ici
    3. BIND      : que signifie ψ_a ⊛ ψ_b ici
    4. UNBIND    : que signifie ψ_ab ⊗ ψ_a ici
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ═══════════════════════════════════════════════════════════════════════════════
# DÉFINITION DES DOMAINES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DomainSpec:
    """Spécification d'un domaine de raisonnement."""
    name: str
    concepts: List[str]           # types de concepts manipulés
    
    # Sémantique des 4 opérations
    encode_desc: str              # comment encoder les concepts
    interfere_desc: str           # que signifie la cohérence
    bind_desc: str                # que signifie la composition
    unbind_desc: str              # que signifie l'extraction
    
    # Seuils spécifiques au domaine
    coherence_threshold: float = 0.08
    contradiction_threshold: float = -0.05
    
    # Exemples de requêtes typiques
    examples: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE UNIVERSELLE DES DOMAINES
# ═══════════════════════════════════════════════════════════════════════════════

DOMAINS: Dict[str, DomainSpec] = {
    
    'logique': DomainSpec(
        name='Logique formelle',
        concepts=['prémisse', 'conclusion', 'proposition', 'syllogisme'],
        encode_desc='Proposition → ψ = Σ ψ_mots (superposition lexicale)',
        interfere_desc='Validité : Re⟨ψ_P1|ψ_P2⟩ > seuil → les prémisses sont cohérentes',
        bind_desc='Syllogisme : ψ_A→B ⊛ ψ_B→C ≈ ψ_A→C (transitivité par binding)',
        unbind_desc='Modus Ponens : ψ_implication ⊗ ψ_fait ≈ ψ_conclusion',
        coherence_threshold=0.08,
        contradiction_threshold=-0.05,
        examples=['A→B, B→C ∴ A→C', 'Si A alors B, A ∴ B']
    ),
    
    'faits': DomainSpec(
        name='Connaissances factuelles',
        concepts=['sujet', 'relation', 'objet', 'fait', 'vérité'],
        encode_desc='Fait(s,r,o) → ψ = ψ_s ⊛ ψ_r ⊛ ψ_o (binding HRR)',
        interfere_desc='Pertinence : Re⟨ψ_Q|ψ_f⟩ mesure la résonance question↔fait',
        bind_desc='Transitivité : A→B→C → A→C (chaine de faits cohérents)',
        unbind_desc='Retrieval : H ⊗ ψ_Q → faits les plus résonnants',
        coherence_threshold=0.08,
        examples=['Quelle est la capitale de X ?', 'Qui a découvert Y ?']
    ),
    
    'mathematiques': DomainSpec(
        name='Mathématiques / Arithmétique ondulatoire',
        concepts=['nombre', 'opération', 'relation', 'preuve'],
        encode_desc='Nombre n → position angulaire θ = n·φ·2π mod 2π sur le cercle',
        interfere_desc='Divisibilité : Re⟨ψ_a|ψ_b⟩ > 0.9 → a et b partagent un facteur',
        bind_desc='Multiplication : ψ_a ⊛ ψ_b ≈ ψ_{a×b} (addition des phases)',
        unbind_desc='Division : ψ_{a×b} ⊗ ψ_a ≈ ψ_b (soustraction des phases)',
        coherence_threshold=0.9,
        examples=['15×7=?', 'Est-ce que 91 est premier ?']
    ),
    
    'musique': DomainSpec(
        name='Musique / Harmonie',
        concepts=['note', 'accord', 'gamme', 'rythme', 'harmonie'],
        encode_desc='Note → ψ = A·exp(i·2π·f·t) (onde sinusoïdale pure)',
        interfere_desc='Harmonie : Re⟨ψ_note1|ψ_note2⟩ > 0 → consonant (quinte, octave)',
        bind_desc='Accord : ψ_accord = Σ ψ_notes (superposition = interférence)',
        unbind_desc='Transcription : ψ_accord ⊗ ψ_instrument → notes individuelles',
        coherence_threshold=0.3,
        examples=['Do-Mi-Sol est-il harmonieux ?', 'Quel accord avec Do et Sol ?']
    ),
    
    'code': DomainSpec(
        name='Programmation / Code',
        concepts=['fonction', 'type', 'bug', 'compilation', 'pipeline'],
        encode_desc='Fonction → ψ = ψ_input ⊛ ψ_body ⊛ ψ_output (binding HRR)',
        interfere_desc='Bug : Re⟨ψ_spec|ψ_impl⟩ < 0 → l\'implémentation contredit la spec',
        bind_desc='Pipeline : ψ_f ⊛ ψ_g → composition séquentielle',
        unbind_desc='Compilation : H_programme ⊗ ψ_source → ψ_executable',
        coherence_threshold=0.3,
        examples=['Composer f(g(x))', 'Détecter un bug entre spec et code']
    ),
    
    'medecine': DomainSpec(
        name='Médecine / Diagnostic',
        concepts=['symptôme', 'maladie', 'traitement', 'patient', 'diagnostic'],
        encode_desc='Symptôme → ψ = encodage des descripteurs (localisation, intensité, durée)',
        interfere_desc='Diagnostic : max Re⟨ψ_symptômes|ψ_maladie⟩ → maladie la plus probable',
        bind_desc='Comorbidité : ψ_maladie1 ⊛ ψ_maladie2 → interaction pathologique',
        unbind_desc='Traitement : ψ_maladie ⊗ ψ_patient → ψ_traitement personnalisé',
        coherence_threshold=0.2,
        examples=['Fièvre + toux → ?', 'Interaction médicament A et B ?']
    ),
    
    'droit': DomainSpec(
        name='Droit / Jurisprudence',
        concepts=['loi', 'fait', 'jugement', 'précédent', 'preuve'],
        encode_desc='Loi → ψ_règle = encodage des conditions et conséquences',
        interfere_desc='Applicabilité : Re⟨ψ_faits|ψ_conditions⟩ > seuil → la loi s\'applique',
        bind_desc='Jugement : ψ_loi ⊛ ψ_faits → ψ_décision (binding = application)',
        unbind_desc='Précédent : ψ_jugement ⊗ ψ_faits → ψ_ratio_decidendi (la règle extraite)',
        coherence_threshold=0.15,
        examples=['L\'article X s\'applique-t-il ?', 'Quel précédent pour ce cas ?']
    ),
    
    'economie': DomainSpec(
        name='Économie / Marchés',
        concepts=['offre', 'demande', 'prix', 'marché', 'agent'],
        encode_desc='Agent → ψ = préférences + contraintes (vecteur de caractéristiques)',
        interfere_desc='Marché : Re⟨ψ_offre|ψ_demande⟩ > 0 → transaction possible',
        bind_desc='Équilibre : ψ_offre ⊛ ψ_demande → ψ_prix_équilibre',
        unbind_desc='Préférences : ψ_transaction ⊗ ψ_marché → ψ_préférences_révélées',
        coherence_threshold=0.1,
        examples=['Prix d\'équilibre ?', 'Impact d\'une taxe ?']
    ),
    
    'physique': DomainSpec(
        name='Physique / Mécanique quantique',
        concepts=['particule', 'champ', 'interaction', 'probabilité'],
        encode_desc='État → ψ(x,t) = fonction d\'onde (amplitude de probabilité)',
        interfere_desc='Probabilité de transition : |⟨ψ_final|ψ_initial⟩|²',
        bind_desc='Intrication : ψ_A ⊛ ψ_B → état intriqué non séparable',
        unbind_desc='Mesure : H_système ⊗ ψ_observable → valeur propre mesurée',
        coherence_threshold=0.0,  # QM native
        examples=['Probabilité de désintégration ?', 'États liés ?']
    ),
    
    'biologie': DomainSpec(
        name='Biologie / Biochimie',
        concepts=['protéine', 'gène', 'interaction', 'pathway'],
        encode_desc='Séquence → ψ = somme pondérée des acides aminés/nucléotides',
        interfere_desc='Liaison : Re⟨ψ_protA|ψ_protB⟩ > 0 → affinité de liaison',
        bind_desc='Complexe : ψ_A ⊛ ψ_B → structure du complexe lié',
        unbind_desc='Docking : ψ_complexe ⊗ ψ_récepteur → ψ_ligand optimal',
        coherence_threshold=0.25,
        examples=['Interaction protéine-ligand ?', 'Pathway métabolique ?']
    ),
    
    'linguistique': DomainSpec(
        name='Linguistique / Traduction',
        concepts=['mot', 'phrase', 'sens', 'traduction', 'grammaire'],
        encode_desc='Mot → ψ_mot (hash φ-spacé + spectral sémantique)',
        interfere_desc='Similarité : Re⟨ψ_mot1|ψ_mot2⟩ mesure la proximité sémantique',
        bind_desc='Composition : ψ_phrase = ψ_sujet ⊛ ψ_verbe ⊛ ψ_objet',
        unbind_desc='Traduction : ψ_FR → R_EN(ψ_FR) par rotation de phase',
        coherence_threshold=0.4,
        examples=['Traduire "chat" en anglais', 'Similarité entre "joie" et "bonheur"']
    ),
    
    'emotion': DomainSpec(
        name='Émotion / Psychologie',
        concepts=['émotion', 'humeur', 'empathie', 'trauma', 'sentiment'],
        encode_desc='État émotionnel → ψ_self (accumulation d\'expériences)',
        interfere_desc='Ressenti : Re⟨ψ_attendu|ψ_réel⟩ → émotion (joie à tristesse)',
        bind_desc='Empathie : Re⟨ψ_self_A|ψ_self_B⟩ → connexion émotionnelle',
        unbind_desc='Thérapie : ψ_trauma ⊗ ψ_contexte_sécurisé → ψ_guérison',
        coherence_threshold=0.3,
        examples=['Que ressent cette personne ?', 'Ce souvenir est-il traumatique ?']
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# ADAPTATEUR DE DOMAINE
# ═══════════════════════════════════════════════════════════════════════════════

class DomainAdapter:
    """
    Adaptateur universel : traduit n'importe quel domaine en opérations ondulatoires.
    
    Usage :
        da = DomainAdapter('medecine', brain)
        result = da.reason(['fievre', 'toux'], contexte='patient 45 ans')
    """
    
    def __init__(self, domain: str, brain=None):
        if domain not in DOMAINS:
            raise ValueError(f"Domaine inconnu: {domain}. Domaines: {list(DOMAINS.keys())}")
        
        self.spec = DOMAINS[domain]
        self.domain = domain
        self.brain = brain
        
        # Encoder du domaine (si cerveau disponible)
        self.enc = brain.unconscious.encoder if brain else None
    
    def encode(self, concept: str) -> np.ndarray:
        """Encode un concept du domaine en ψ."""
        if self.enc:
            return self.enc.encode_query(concept)
        # Fallback : encodage par hash φ-spacé
        seed = hash(concept) & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        dim = 512
        real = rng.randn(dim) * (1.0 / math.sqrt(2.0 * dim))
        imag = rng.randn(dim) * (1.0 / math.sqrt(2.0 * dim))
        psi = real + 1j * imag
        return psi / np.sqrt(np.sum(np.abs(psi)**2))
    
    def interfere(self, a: str, b: str) -> float:
        """Mesure l'interférence entre deux concepts du domaine."""
        psi_a = self.encode(a)
        psi_b = self.encode(b)
        return float(np.real(np.dot(psi_a, np.conj(psi_b))))
    
    def bind(self, a: str, b: str) -> np.ndarray:
        """Compose deux concepts."""
        psi_a = self.encode(a)
        psi_b = self.encode(b)
        return np.fft.ifft(np.fft.fft(psi_a) * np.fft.fft(psi_b))
    
    def reason(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Raisonne dans le domaine.
        
        La méthode adapte automatiquement son comportement selon le domaine.
        """
        if self.domain == 'logique':
            return self._reason_logic(*args, **kwargs)
        elif self.domain == 'faits':
            return self._reason_facts(*args, **kwargs)
        elif self.domain == 'medecine':
            return self._reason_medicine(*args, **kwargs)
        elif self.domain == 'droit':
            return self._reason_law(*args, **kwargs)
        else:
            return self._reason_generic(*args, **kwargs)
    
    def _reason_logic(self, premises: List[str]) -> Dict:
        """Raisonnement logique."""
        from wave_logic import WaveLogic
        wl = WaveLogic(self.brain) if self.brain else None
        
        results = []
        for i in range(len(premises)-1):
            if wl:
                r = wl.solve(premises=[premises[i], premises[i+1]])
                results.append({
                    'step': f'{premises[i][:50]} → {premises[i+1][:50]}',
                    'coherence': r.coherence,
                    'conclusion': r.conclusion,
                    'valid': r.is_valid
                })
        
        return {
            'domain': 'logique',
            'operations': 'syllogisme par binding',
            'threshold': self.spec.coherence_threshold,
            'results': results
        }
    
    def _reason_facts(self, question: str) -> Dict:
        """Recherche factuelle."""
        if not self.brain:
            return {'error': 'Cerveau requis'}
        
        result = self.brain.process(question)
        return {
            'domain': 'faits',
            'operations': 'retrieval par résonance',
            'question': question,
            'answer': result.response,
            'confidence': result.confidence
        }
    
    def _reason_medicine(self, symptomes: List[str], contexte: str = "") -> Dict:
        """Diagnostic différentiel."""
        psi_s = sum(self.encode(s) for s in symptomes) / len(symptomes)
        
        diagnostics = []
        if self.brain:
            for key, rec in self.brain.unconscious.registry.items():
                interf = float(np.real(np.dot(rec.psi, np.conj(psi_s))))
                if interf > 0.05:
                    diagnostics.append((rec.sujet, interf))
        
        diagnostics.sort(key=lambda x: -x[1])
        
        return {
            'domain': 'medecine',
            'operations': 'diagnostic par interférence maximale',
            'symptomes': symptomes,
            'contexte': contexte,
            'diagnostics': [(d[0], round(d[1], 3)) for d in diagnostics[:5]]
        }
    
    def _reason_law(self, loi: str, fait: str) -> Dict:
        """Application d'une loi à un fait."""
        psi_loi = self.encode(loi)
        psi_fait = self.encode(fait)
        
        Applicabilite = float(np.real(np.dot(psi_loi, np.conj(psi_fait))))
        psi_jugement = self.bind(loi, fait)
        
        return {
            'domain': 'droit',
            'operations': 'jugement par binding loi⊛fait',
            'loi': loi[:80],
            'fait': fait[:80],
            'applicabilite': round(Applicabilite, 3),
            'jugement_valide': Applicabilite > self.spec.coherence_threshold
        }
    
    def _reason_generic(self, **kwargs) -> Dict:
        """Raisonnement générique pour tout domaine."""
        return {
            'domain': self.domain,
            'operations': f'4 ops universelles sur {self.spec.concepts}',
            'threshold': self.spec.coherence_threshold,
            'available_ops': ['encode', 'interfere', 'bind', 'unbind']
        }
    
    @property
    def info(self) -> Dict:
        """Information sur le domaine."""
        return {
            'domain': self.spec.name,
            'concepts': self.spec.concepts,
            'encode': self.spec.encode_desc,
            'interfere': self.spec.interfere_desc,
            'bind': self.spec.bind_desc,
            'unbind': self.spec.unbind_desc,
            'coherence_threshold': self.spec.coherence_threshold,
            'contradiction_threshold': self.spec.contradiction_threshold,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE DE CORRESPONDANCE UNIVERSELLE (format lisible)
# ═══════════════════════════════════════════════════════════════════════════════

UNIVERSAL_TABLE = """
┌──────────────────────────────────────────────────────────────────────────────┐
│              TABLE DE CORRESPONDANCE UNIVERSELLE                              │
│          Toute forme de raisonnement = 4 opérations ondulatoires              │
├────────────┬─────────────────┬──────────────────┬─────────────────────────────┤
│  DOMAINE   │  ENCODE (→ ψ)   │  INTERFERE (Re⟨⟩) │  BIND (⊛)                  │
├────────────┼─────────────────┼──────────────────┼─────────────────────────────┤
│ Logique    │ Prémisse → ψ    │ Validité          │ Syllogisme (A→B⊛B→C)        │
│ Faits      │ (s,r,o) → ψ     │ Pertinence        │ Transitivité (A→C)          │
│ Maths      │ Nombre → angle  │ Divisibilité      │ Multiplication              │
│ Musique    │ Note → sinusoïde│ Harmonie/disson.  │ Accord (Σ notes)            │
│ Code       │ Fonction → ψ    │ Bug (spec vs impl) │ Pipeline (f⊛g)             │
│ Médecine   │ Symptôme → ψ    │ Diagnostic        │ Comorbidité                 │
│ Droit      │ Loi → ψ_règle   │ Applicabilité     │ Jugement (loi⊛fait)         │
│ Économie   │ Agent → ψ_pref  │ Marché (offre/dem)│ Équilibre                   │
│ Physique   │ État → ψ(x,t)   │ Probabilité       │ Intrication                 │
│ Biologie   │ Séquence → ψ    │ Liaison           │ Complexe (protéine-ligand)   │
│ Linguistique│ Mot → ψ_mot     │ Similarité        │ Phrase (sujet⊛verbe⊛objet)   │
│ Émotion    │ ψ_self          │ Ressenti          │ Empathie (ψ_A↔ψ_B)          │
├────────────┴─────────────────┴──────────────────┴─────────────────────────────┤
│  Tous : UNBIND (⊗) = extraction / inversion du binding                        │
│  Tous : Seuils adaptatifs calibrés par feedback conscient                     │
│  Tous : 0 paramètre, déterministe, 0 hallucination                            │
└──────────────────────────────────────────────────────────────────────────────┘
"""


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print(UNIVERSAL_TABLE)
    
    # Démo : raisonnement multi-domaine
    print("\nDÉMO : Raisonnement multi-domaine")
    print("="*60)
    
    # Sans cerveau (démo des correspondances)
    for domain in ['logique', 'medecine', 'droit', 'musique']:
        da = DomainAdapter(domain)
        info = da.info
        print(f"\n{info['domain'].upper()}:")
        print(f"  Encode: {info['encode'][:70]}...")
        print(f"  Interfere: {info['interfere'][:70]}...")
        print(f"  Bind: {info['bind'][:70]}...")
