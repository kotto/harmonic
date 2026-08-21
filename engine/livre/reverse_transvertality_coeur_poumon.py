import numpy as np
phi = (1 + np.sqrt(5)) / 2

print("=== Connexion ville-ville : Coeur (75 BPM) <-> Respiration (15 cycles/min) ===")
print()

# E6 M1 : S/D = 1/phi a 75 BPM (1.25 Hz)
# E6 M2 : I/E = 1/phi a 15 cycles/min (0.25 Hz)
HR = 75.0  # battements/min
RR = 15.0  # cycles/min

print(f"Frequence cardiaque  : {HR} BPM = {HR/60:.4f} Hz")
print(f"Frequence respiratoire : {RR} /min = {RR/60:.4f} Hz")
print(f"Rapport HR/RR        : {HR/RR:.2f}")
print()

# Analyse harmonique du rapport 5
sqrt5 = np.sqrt(5)
deux_phi_moins_1 = 2*phi - 1
print(f"sqrt(5)            = {sqrt5:.10f}")
print(f"2*phi - 1          = {deux_phi_moins_1:.10f}")
print(f"(2*phi - 1)^2      = {deux_phi_moins_1**2:.10f}")
print(f"HR/RR              = {HR/RR:.2f}")
print()

# Verification : HR/RR = (2*phi-1)^2
print(f"=== HR/RR = (2phi-1)^2 ? ===")
print(f"HR/RR = {HR/RR}")
print(f"(2phi-1)^2 = {deux_phi_moins_1**2:.10f}")
print(f"Difference = {abs(HR/RR - deux_phi_moins_1**2):.10f}")
print()

# Verification : chaque oscillateur satisfait individuellement 1/phi
print(f"=== Verification des ratios individuels (E6) ===")
# Coeur : S/D = 1/phi a 75 BPM
S_D_75 = 0.613  # du depot E6, a 75 BPM
print(f"Coeur : S/D a 75 BPM = {S_D_75:.4f} (attendu 1/phi = {1/phi:.4f}, ecart {-0.8:.1f}%)")

# Respiration : I/E = 1/phi a 15/min
I_E_15 = 0.600  # du depot E6, a 15/min
print(f"Respiration : I/E a 15/min = {I_E_15:.4f} (attendu 1/phi = {1/phi:.4f}, ecart {-2.9:.1f}%)")
print()

# Significance physique
print(f"=== Signification physique ===")
print(f"Deux oscillateurs (coeur, poumons) operent chacun a 1/phi")
print(f"Le rapport de leurs frequences est (2phi-1)^2 = 5 = (sqrt(5))^2")
print(f"sqrt(5) = 2phi-1 = {deux_phi_moins_1} est H6 (symetrie du vivant)")
print()
print(f"Prediction :")
print(f"  Pour tout mammifere au repos, HR/RR = (2phi-1)^2 = 5 ± 0.5")
print(f"  Et les rapports internes S/D et I/E valent 1/phi ± 0.05")
print(f"  Test : metaanalyse des HR/RR dans la litterature de physiologie")
print(f"  Comparee (mammiferes) : souris 600/120=5, chien 90/18=5, elephant?")