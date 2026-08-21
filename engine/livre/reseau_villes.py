print("=== RESEAU DES CONNEXIONS VILLE-VILLE ===")
print()

# Les 10 villes/domaines
villes = {
    "Coeur":    {"freq_Hz": 1.250, "ratio": 1/1.618, "depot": "E6-M1", "H": "1/phi, sqrt5"},
    "Poumons": {"freq_Hz": 0.250, "ratio": 1/1.618, "depot": "E6-M2", "H": "1/phi, sqrt5"},
    "Cerveau": {"freq_Hz": 8.40,  "ratio": 1.618, "depot": "E5", "H": "phi"},
    "Eau":     {"T_K": 310.15, "deltaE_meV": 12.86, "ratio": 1/1.618, "depot": "E4", "H": "phi, LDL/HDL"},
    "Proteines":{"score": 0.75, "param": "zero training", "depot": "HarmoFold", "H": "c_k = 1/Gamma(k/phi+1)"},
    "Physique": {"param": "alpha=0.00729735", "precision": "2.4e-7", "depot": "T4+T5", "H": "pi,e,phi,sqrt2,sqrt3"},
    "Signal":  {"ratio_compression": 64.6, "dico": 248, "depot": "HCV", "H": "7 constantes"},
    "IA":      {"score": 99.33, "param": "zero param", "depot": "ch27", "H": "phi"},
    "Chimie":  {"nb_periodes": 118, "depot": "A5", "H": "2n^2"},
}

print("Connexions DEJA ETABLIES :")
print()
print("  [Coeur] --(S/D=1/phi, 75BPM)---------")
print("      |                                 |")
print("      |  HR/RR = 5 = (sqrt5)^2          |")
print("      |  = (2phi-1)^2                   |")
print("      |                                 v")
print("  [Poumons] --(I/E=1/phi, 15/min)------")
print()
print("  [Cerveau] --(beta/alpha=phi)-----[Physique]--(gc=2.60Hz)")
print()
print("  [Physique] --(T*=37C)---------[Eau]--(LDL/HDL=1/phi)")
print()
print("  [Physique] --(Zf/Zm=phi)---[Coeur]--(S/D=1/phi, Gamma=1/phi^3)")
print()

print("Connexions EN EXPLORATION :")
print()
# Eau <-> Coeur (temperature du sang -> viscosite -> frequence cardiaque optimale)
print("  1.  [Eau] <--> [Coeur]")
print("        Visco: eau a 37C structure optimale")
print("        -> coeur pompe sang 92% eau")
print("        -> viscosite reglee sur 1/phi a 37C?")
print()

# Eau <-> Proteines (solvatation optimale a 37C)
print("  2.  [Eau] <--> [Proteines]")
print("        HarmoFold replie dans l'eau")
print("        -> l'eau a 37C est optimale pour le repliement")
print("        -> energie de solvatation suit 1/Gamma?")
print()

# Coeur <-> Cerveau (baroreflexe, couplage HRV)
print("  3.  [Coeur] <--> [Cerveau]")
print("        Baroreflexe: coeur <-> systeme nerveux autonome")
print("        -> frequence cardiaque module l'EEG")
print("        -> beta/alpha suit-il les variations de HR?")
print()

# Compression <-> IA (sparsite harmonique)
print("  4.  [Signal] <--> [IA]")
print("        Compression 64.6:1 -> signaux naturels parcimonieux")
print("        IA 99.33% -> concepts bien separes par phi")
print("        -> 64.6 s'exprime-t-il en fonction des H_n?")
print()

print("Connexions FORTES, prediction claire :")
print()
print("  A. [Coeur] x [Poumons] = HR/RR = 5 = (2phi-1)^2")
print("     Pred: pour tout mammifere, HR/RR ≈ 5 ± 0.5")
print("     Test: metaanalyse physiologique")
print()

print("  B. [Eau] x [Cerveau] = T* (37C) module beta/alpha")
print("     Pred: en hypothermie (33C) ou fievre (39C),")
print("           le rapport beta/alpha s'ecarte de phi")
print("           suivant exp(-12.86meV/kB·T)")
print("     Test: EEG pendant hypothermie therapeutique")
print()

print("  C. [Eau] x [Proteines] = energie de solvatation harmonique")
print("     Pred: le potentiel chimique des acides amines")
print("           a 37C suit la serie c_k = 1/Gamma(k/phi+1)")
print("     Test: donnees de solvatation existantes (Nozaki-Tanford)")
print()