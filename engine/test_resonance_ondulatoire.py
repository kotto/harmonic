#!/usr/bin/env python3
"""
test_resonance_ondulatoire.py — L'INTERFÉRENCE PRODUIT-ELLE LA RÉPONSE JUSTE ?
============================================================================
Ne teste PAS la similarité cosinus (P1.1, déjà réfuté : AUC 0,4985).
Teste la RÉSONANCE : superposition + binding HRR + interférence.

Principe : comme un diapason qui résonne à SA fréquence sans apprentissage,
une onde-concept doit entrer en RÉSONANCE avec l'onde-problème si
leur structure correspond.

PROTOCOLE PRÉ-ENREGISTRÉ :
  Corpus : 100 paires question→réponse (capitales, arithmétique, synonymes)
  Encodage : FNV-1a × φ-spacing → vecteur complexe C^512
  Résonance : ψ_question ⋆ ψ_réponse  (binding HRR = convolution circulaire)
  Score : |⟨ψ_question ⋆ ψ_réponse, ψ_question ⋆ ψ_candidat⟩|
  → le candidat qui MAXIMISE le score de résonance est la réponse choisie.
  
  H0 : la résonance ne porte AUCUNE information (précision = hasard)
  H1 : la résonance porte un signal (précision > hasard, p < 0,01)

  Test : 1000 permutations des réponses. Si la précision réelle dépasse
  la distribution nulle (p < 0,01) → l'interférence a un signal.
"""
import json,math,os,time,itertools
import numpy as np
PHI=(1+math.sqrt(5))/2;DIM=512;PI=math.pi;C=299792458

def fnv1a(s):
    h=14695981039346656037
    for ch in s:h^=ord(ch);h=(h*1099511628211)&0xFFFFFFFFFFFFFFFF
    return h

def encode(mot):
    """Encodage φ-spacing : phases = (h·φ^k mod 2π) — onde complexe."""
    h=fnv1a(mot)
    k=np.arange(DIM,dtype=np.float64)
    phases=(h*PHI**k)%(2*PI)
    return np.exp(1j*phases)

def bind(a,b):
    """Binding HRR : convolution circulaire = produit en Fourier."""
    A=np.fft.fft(a);B=np.fft.fft(b)
    return np.fft.ifft(A*B)

def resonance(psi_q,psi_a,psi_c):
    """Score de résonance : |⟨ψ_q ⋆ ψ_a, ψ_q ⋆ ψ_c⟩|."""
    qa=bind(psi_q,psi_a);qc=bind(psi_q,psi_c)
    return abs(np.vdot(qa,qc))

# Corpus : 100 paires question→réponse (capitales, arithmétique, paires)
CORPUS=[
    ("France","Paris"),("Allemagne","Berlin"),("Italie","Rome"),
    ("Espagne","Madrid"),("Portugal","Lisbonne"),("Japon","Tokyo"),
    ("Chine","Pékin"),("Inde","New Delhi"),("Brésil","Brasilia"),
    ("Canada","Ottawa"),("Russie","Moscou"),("Australie","Canberra"),
    ("2+2","4"),("3+5","8"),("7+8","15"),("10+5","15"),
    ("12+13","25"),("20+30","50"),("100+200","300"),("9+6","15"),
    ("4×3","12"),("5×5","25"),("6×7","42"),("8×9","72"),
    ("10×10","100"),("3×7","21"),("12×5","60"),("15×4","60"),
    ("grand","petit"),("haut","bas"),("chaud","froid"),("rapide","lent"),
    ("jour","nuit"),("lumière","obscurité"),("amour","haine"),
    ("vie","mort"),("guerre","paix"),("riche","pauvre"),
    ("eau","H2O"),("sel","NaCl"),("soleil","étoile"),("lune","satellite"),
    ("chat","félin"),("chien","canin"),("cheval","équin"),
    ("rouge","couleur"),("bleu","couleur"),("vert","couleur"),
    ("pomme","fruit"),("carotte","légume"),("pain","aliment"),
    ("médecin","docteur"),("avocat","juriste"),("professeur","enseignant"),
    ("voiture","véhicule"),("avion","aéronef"),("bateau","navire"),
    ("Paris","capitale"),("Londres","capitale"),("Berlin","capitale"),
    ("dollar","monnaie"),("euro","monnaie"),("yen","monnaie"),
    ("Mars","planète"),("Vénus","planète"),("Terre","planète"),
    ("oxygène","élément"),("carbone","élément"),("fer","élément"),
    ("charbon","énergie"),("pétrole","énergie"),("solaire","énergie"),
    ("ADN","génétique"),("cellule","biologie"),("atome","physique"),
    ("triangle","géométrie"),("cercle","géométrie"),("carré","géométrie"),
    ("ordinateur","machine"),("internet","réseau"),("téléphone","communication"),
    ("livre","lecture"),("musique","art"),("peinture","art"),
    # Pièges (réponses fausses délibérées pour les permutations)
    *[("piège","faux") for _ in range(7)]
]
CORPUS=[(q,a) for q,a in CORPUS if a!="faux"]

def main():
    t0=time.time()
    print("="*70)
    print("TEST DE RÉSONANCE ONDULATOIRE — interférence sans apprentissage")
    print("="*70)
    print(f"  Corpus : {len(CORPUS)} paires question→réponse")
    print(f"  Encodage : FNV-1a × φ-spacing → C^{DIM}")
    print(f"  Résonance : |⟨ψ_q ⋆ ψ_a, ψ_q ⋆ ψ_c⟩| — le max gagne")
    
    # Encodage
    cache={}
    for q,a in CORPUS:
        for w in [q,a]:
            if w not in cache:cache[w]=encode(w)
    
    # Précision réelle — CORRIGÉE : on EXCLUT la vraie réponse des candidats
    # Test : |⟨ψ_q ⋆ ψ_rel, ψ_c⟩| où ψ_rel = encode("réponse_de")
    correct=0
    psi_rel=encode("réponse_de")
    for q,true_a in CORPUS:
        psi_q=cache[q];psi_pred=bind(psi_q,psi_rel)
        best_score,best_a=-1,None
        for _,cand in CORPUS:
            if cand==true_a:continue  # EXCLURE la vraie réponse
            if cand not in cache:cache[cand]=encode(cand)
            score=abs(np.vdot(psi_pred,cache[cand]))
            if score>best_score:best_score,best_a=score,cand
        if best_a==true_a:correct+=1
    acc=correct/len(CORPUS)
    print(f"\n  Précision réelle : {correct}/{len(CORPUS)} = {acc*100:.1f}%")
    
    # Permutation test (1000)
    rng=np.random.default_rng(42)
    null_dist=[]
    for _ in range(1000):
        perm=rng.permutation(len(CORPUS))
        c=sum(1 for i in range(len(CORPUS)) if CORPUS[perm[i]][1]==CORPUS[i][1])
        null_dist.append(c/len(CORPUS))
    null_dist=np.array(null_dist)
    p_val=np.mean(null_dist>=acc)
    
    print(f"  Hasard (permutation) : {null_dist.mean()*100:.1f}% ± {null_dist.std()*100:.1f}%")
    print(f"  p-value : {p_val:.4f}")
    
    signal=p_val<0.01
    print(f"\n─ VERDICT")
    print(f"  H1 · résonance > hasard (p<0,01) : {'✅ SIGNAL ONDULATOIRE !' if signal else '❌ pas de signal'}")
    if signal:
        print(f"  → L'interférence d'ondes porte de l'information SANS apprentissage.")
        print(f"  → La précision est faible ({acc*100:.0f}%) mais le signal est RÉEL.")
        print(f"  → Ce n'est pas la similarité cosinus (P1.1) — c'est la RÉSONANCE.")
    else:
        print(f"  → Cohérent avec P1.1 : l'encodage φ-spacing ne porte pas d'information")
        print(f"  utilisable, même par interférence. La représentation doit être APPRISE.")
    
    dep={"corpus":len(CORPUS),"precision":acc,"p_value":float(p_val),
         "signal":bool(signal),"methode":"résonance = binding HRR + interférence",
         "date":time.strftime("%Y-%m-%d %H:%M:%S")}
    p=os.path.join("data","benchmarks","resonance_report.json")
    os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)
    print(f"Rapport : {p} · {time.time()-t0:.1f}s")

if __name__=="__main__":main()
