#!/usr/bin/env python3
r"""
CONCEPT ENCODER SPECTRAL V3 — 2D SpectralEncoder + DFT Harmonique 2D
=======================================================================
Un concept = un SPECTRE 2D de fréquences (nx, ny) qui émerge de
la superposition de toutes ses instances, encodées par SpectralEncoder.

V1 : SHA-256 → quasi-orthogonal
V2 : SpectralEncoder → conversion 1D (perte d'information)
V3 : SpectralEncoder (kx, ky) → DFT harmonique 2D → spectre 2D

La sortie 2D du SpectralEncoder EST conservée. La DFT harmonique 2D
corrèle avec Ψ_{nx,ny}(x,y) = exp(i·φ·(nx·x + ny·y)).

Usage :
  python concept_encoder_spectral.py
"""

import sys, os, math, hashlib, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# ENCODAGE : SpectralEncoder 2D conservé
# ═══════════════════════════════════════════════════════════════════════════════

SPECTRAL_ENC = None

def get_encoder(corpus):
    global SPECTRAL_ENC
    from spectral_encoder import SpectralEncoder
    SPECTRAL_ENC = SpectralEncoder(max_features=4096)
    SPECTRAL_ENC.build_vocabulary(corpus)
    return SPECTRAL_ENC


def text_to_wave_2d(text, grid_size=64):
    """
    SpectralEncoder → onde gaussienne 2D centrée en (kx, ky).
    La sortie 2D du SpectralEncoder est CONSERVÉE INTÉGRALEMENT.
    """
    enc = SPECTRAL_ENC
    if enc is None:
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % 200) / 100 - 1  # [-1, 1]
        ky = (int(h[16:32], 16) % 200) / 100 - 1
    else:
        kx, ky = enc.encode(text)
        # Normaliser dans [-1, 1]
        kx = kx / 32
        ky = ky / 32
    
    # Créer une gaussienne 2D centrée en (kx, ky)
    s = grid_size
    x = np.linspace(-s/2, s/2, s)
    y = np.linspace(-s/2, s/2, s)
    X, Y = np.meshgrid(x, y)
    env = np.exp(-((X - kx * s/4)**2 + (Y - ky * s/4)**2) / (2 * 3**2))
    psi = env * np.exp(1j * (kx * X * PI + ky * Y * PI))
    return psi, X, Y, (kx, ky)


# ═══════════════════════════════════════════════════════════════════════════════
# DFT HARMONIQUE 2D
# ═══════════════════════════════════════════════════════════════════════════════

def harmonic_dft_2d(psi, n_max=30, grid_size=64):
    """
    DFT harmonique 2D : corrélation avec Ψ_{nx,ny} pour nx,ny ∈ [-n_max, n_max].
    
    Ψ_{nx,ny}(x,y) = exp(i·φ·(nx·x + ny·y))
    
    Les nx, ny sont des entiers qui représentent les MODES SPECTRAUX 2D.
    φ espace les fréquences pour éviter les collisions.
    """
    s = grid_size
    x = np.linspace(-s/2, s/2, s)
    y = np.linspace(-s/2, s/2, s)
    X, Y = np.meshgrid(x, y)
    
    results = []
    for nx in range(-n_max, n_max + 1):
        for ny in range(-n_max, n_max + 1):
            psi_mode = np.exp(1j * PHI * (nx * X + ny * Y))
            corr = np.abs(np.sum(psi * np.conj(psi_mode))) / (s * s)
            results.append(((nx, ny), corr))
    
    return results


def extract_top_modes_2d(psi, K=10, n_max=30, grid_size=64):
    """
    Extrait les K modes (nx, ny) dominants d'une onde 2D.
    Retourne [((nx, ny), amplitude), ...] trié par amplitude décroissante.
    """
    spectrum = harmonic_dft_2d(psi, n_max, grid_size)
    spectrum.sort(key=lambda x: -x[1])
    return spectrum[:K]


# ═══════════════════════════════════════════════════════════════════════════════
# CONCEPT ENCODER V3 — Spectres 2D
# ═══════════════════════════════════════════════════════════════════════════════

class ConceptEncoder:
    """
    Encodeur de concepts par émergence spectrale 2D.
    
    Chaque concept est représenté comme un SPECTRE 2D :
    une liste de modes ((nx, ny), amplitude) qui émergent
    de la superposition de toutes ses instances.
    """
    
    def __init__(self, grid_size=64, n_modes=10, n_max=30):
        self.grid = grid_size
        self.K = n_modes
        self.n_max = n_max
        self.concepts = {}
        self.all_instances = []
    
    def add_concept(self, name, instances):
        self.concepts[name] = {"instances": instances, "N": len(instances)}
        self.all_instances.extend(instances)
        return len(instances)
    
    def build(self):
        """Construit les spectres 2D pour tous les concepts."""
        if not self.all_instances:
            return
        
        print(f"\n[SpectralEncoder] Construction du vocabulaire sur {len(self.all_instances)} documents...")
        enc = get_encoder(self.all_instances)
        print(f"[SpectralEncoder] Vocabulaire : {enc.word_count} mots")
        
        for name, data in self.concepts.items():
            instances = data["instances"]
            psi_sum = np.zeros((self.grid, self.grid), dtype=np.complex128)
            positions = []
            
            for inst in instances:
                psi, _, _, (kx, ky) = text_to_wave_2d(inst, self.grid)
                psi_sum += psi
                positions.append((kx, ky))
            
            # Extraire les K modes dominants
            spectrum = extract_top_modes_2d(psi_sum, self.K, self.n_max, self.grid)
            
            data["spectrum_2d"] = spectrum
            data["positions"] = positions
            data["raw_wave"] = psi_sum
            
            print(f"  {name:20s} : {len(instances)} instances → {len(spectrum)} modes 2D")
    
    def concept_to_wave(self, name):
        """Reconstruit l'onde 2D d'un concept à partir de son spectre."""
        if name not in self.concepts or "spectrum_2d" not in self.concepts[name]:
            return None
        spectrum = self.concepts[name]["spectrum_2d"]
        s = self.grid
        x = np.linspace(-s/2, s/2, s)
        y = np.linspace(-s/2, s/2, s)
        X, Y = np.meshgrid(x, y)
        psi = np.zeros((s, s), dtype=np.complex128)
        for (nx, ny), amp in spectrum:
            psi += amp * np.exp(1j * PHI * (nx * X + ny * Y))
        return psi, X, Y
    
    def similarity(self, concept1, concept2):
        """Interférence entre les ondes 2D reconstruites de deux concepts."""
        r1 = self.concept_to_wave(concept1)
        r2 = self.concept_to_wave(concept2)
        if r1 is None or r2 is None:
            return 0.0
        psi1, _, _ = r1
        psi2, _, _ = r2
        
        dot = np.real(np.sum(psi1 * np.conj(psi2)))
        n1 = np.sqrt(np.real(np.sum(psi1 * np.conj(psi1))))
        n2 = np.sqrt(np.real(np.sum(psi2 * np.conj(psi2))))
        if n1 < 1e-10 or n2 < 1e-10:
            return 0.0
        return max(-1.0, min(1.0, dot / (n1 * n2)))
    
    def query(self, text, top_k=5):
        """Interroge avec un texte → quel concept résonne le plus ?"""
        psi_q, _, _, _ = text_to_wave_2d(text, self.grid)
        
        scores = []
        for name in self.concepts:
            r = self.concept_to_wave(name)
            if r is None:
                continue
            psi_c, _, _ = r
            dot = np.real(np.sum(psi_q * np.conj(psi_c)))
            n1 = np.sqrt(np.real(np.sum(psi_q * np.conj(psi_q))))
            n2 = np.sqrt(np.real(np.sum(psi_c * np.conj(psi_c))))
            interf = dot / (n1 * n2) if n1 > 1e-10 and n2 > 1e-10 else 0.0
            scores.append((name, max(-1.0, min(1.0, interf))))
        
        scores.sort(key=lambda x: -abs(x[1]))
        return scores[:top_k]


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def ligne(titre):
    print(f"\n{'=' * 68}")
    print(f"  {titre}")
    print(f"{'=' * 68}")


def demo():
    print("=" * 74)
    print("  CONCEPT ENCODER SPECTRAL V3 — 2D")
    print("  SpectralEncoder (kx,ky) → DFT 2D → Spectre 2D")
    print("=" * 74)
    
    enc = ConceptEncoder(grid_size=64, n_modes=10, n_max=20)
    
    ligne("DEMO 1 — Enregistrement des concepts")
    
    enc.add_concept("CAPITALE", [
        "Paris est la capitale de la France",
        "Dakar est la capitale du Senegal",
        "Bamako est la capitale du Mali",
        "Tokyo est la capitale du Japon",
        "Brasilia est la capitale du Bresil",
        "Londres est la capitale du Royaume-Uni",
        "Berlin est la capitale de l'Allemagne",
        "Rome est la capitale de l'Italie",
    ])
    
    enc.add_concept("PAYS_AFRIQUE", [
        "Le Mali est un pays d'Afrique de l'Ouest",
        "Le Senegal est un pays d'Afrique de l'Ouest",
        "Le Ghana est un pays d'Afrique de l'Ouest",
        "Le Nigeria est un pays d'Afrique",
        "L'Ethiopie est un pays d'Afrique de l'Est",
        "Le Maroc est un pays d'Afrique du Nord",
    ])
    
    enc.add_concept("FLEUVE", [
        "Le Nil est le plus long fleuve du monde",
        "Le fleuve Niger traverse le Mali",
        "Le fleuve Senegal coule en Afrique de l'Ouest",
        "Le Congo est un fleuve d'Afrique centrale",
        "L'Amazone est le plus grand fleuve par le debit",
    ])
    
    enc.add_concept("MONTAGNE", [
        "Le mont Everest est le plus haut sommet du monde",
        "Le Kilimandjaro est une montagne en Tanzanie",
        "Le Mont Blanc est le plus haut sommet d'Europe",
        "Les Alpes sont une chaine de montagnes",
        "L'Himalaya est la plus haute chaine de montagnes",
    ])
    
    for name, data in enc.concepts.items():
        print(f"  {name:20s} : {data['N']} instances")
    
    ligne("DEMO 2 — Construction des spectres 2D")
    enc.build()
    
    print(f"\n  Spectres 2D (modes dominants) :")
    for name in enc.concepts:
        spec = enc.concepts[name].get("spectrum_2d", [])
        if spec:
            modes = [f"({nx:+3d},{ny:+3d})" for (nx, ny), amp in spec[:4]]
            print(f"  {name:20s} : {', '.join(modes)}")
    
    ligne("DEMO 3 — Matrice de similarité 2D")
    concepts = ["CAPITALE", "PAYS_AFRIQUE", "FLEUVE", "MONTAGNE"]
    print(f"\n  {'':>16s}", end="")
    for c in concepts:
        print(f"  {c:>12s}", end="")
    print()
    for c1 in concepts:
        print(f"  {c1:>16s}", end="")
        for c2 in concepts:
            sim = 1.0 if c1 == c2 else enc.similarity(c1, c2)
            barre = "█" * int(abs(sim) * 10) if abs(sim) > 0.05 else "—"
            print(f"  {sim:+8.4f} {barre}", end="")
        print()
    
    ligne("DEMO 4 — Interrogation")
    queries = [
        "Ouagadougou est la capitale du Burkina Faso",
        "Le Kilimandjaro est une montagne en Afrique",
        "Le fleuve Zambèze coule en Afrique",
        "Le Cameroun est un pays d'Afrique",
    ]
    for q in queries:
        results = enc.query(q, top_k=4)
        best_name, best_interf = results[0]
        expected = {
            "Ouagadougou": "CAPITALE",
            "Kilimandjaro": "MONTAGNE",
            "Zambèze": "FLEUVE",
            "Cameroun": "PAYS_AFRIQUE",
        }
        exp = None
        for k, v in expected.items():
            if k in q:
                exp = v
                break
        ok = "✓" if best_name == exp else "✗"
        print(f"  {q[:50]:50s} → {best_name:15s} interf={best_interf:+.4f}  {ok}")


if __name__ == "__main__":
    demo()
    print("\n" + "=" * 74)
    print("  FIN — Concept Encoder Spectral V3 (2D)")
    print("=" * 74)
    print("""
    V3 — SPECTRES 2D :
      - SpectralEncoder (kx, ky) conserve en 2D
      - DFT harmonique 2D : Ψ_{nx,ny} = exp(i·φ·(nx·x + ny·y))
      - Le spectre 2D EST le concept
      - La similarite = interference entre ondes 2D reconstruites
      
    Prochain defi : PLONGEMENT SPECTRAL UNIVERSEL
      - Nombres     → spectre 1D (n)
      - Concepts    → spectre 2D (nx, ny)
      - Formes      → spectre 2D dense
      - Relations   → tenseur 3D ?
      
    Le paradigme ondulatoire unifie tout.
""")