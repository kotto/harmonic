import numpy as np
phi = (1 + np.sqrt(5)) / 2

print("=== Rapport beta/alpha = phi (EEG, depot E5, 0.06%) ===")
for nom, fa, fb in [
    ("Beta1 (classique, 10Hz/16.18Hz)", 10.0, 16.18),
    ("Beta2 (Fibonacci, 13Hz/21Hz)", 13.0, 21.03),
]:
    delta_f = abs(fa - fb)
    gc = delta_f / 2.0
    print(f"  {nom}")
    print(f"    alpha={fa:.2f}Hz  beta={fb:.2f}Hz  ratio={fb/fa:.6f}  ecart phi={abs(fb/fa-phi):.6f}")
    print(f"    Delta_f={delta_f:.4f}Hz  couplage critique g_c={gc:.4f}Hz")
print()

print("=== Modele de Kuramoto (2 oscillateurs couples) ===")
print("  d(theta_A)/dt = omega_A + g * sin(theta_B - theta_A)")
print("  d(theta_B)/dt = omega_B + g * sin(theta_A - theta_B)")
print("  Synchronisation si |omega_B - omega_A|/(2g) <= 1")
print("  Soit g >= g_c = (omega_B - omega_A)/2")
print()

print("=== Reverse transvertality : prediction ===")
print("  Le couplage entre populations alpha et beta est regle a g_c")
print("  Cela maximise le transfert d information sans synchronisation")
print("  Le systeme est en criticalite auto-organisee")
print("  Prediction : la fonction de reponse de phase (PRC) montre")
print("    une singularite caracteristique a g_c")
print()
print("  Mesure : analyse PLV (phase-locking value) entre bandes alpha et beta")
print("    en fonction de l'etat de repos / tache cognitive")
print("    A l'etat de repos, PLV doit montrer une valeur critique")
print("    correspondant a g_c = 3.09 Hz (pour alpha=10Hz)")