#!/usr/bin/env python3
"""
ia_v2_modele_reduit.py — MODÈLE RÉDUIT DE L'IA HARMONIQUE V2
=============================================================
Deux couches, zéro paramètre ajusté dans le stockage.

INCONSCIENT : Noyau doré K(t) = B·E_{1/φ}(−φ·t^{1/φ})
    · Chaque exposition laisse une trace K(t−t_k)
    · 3-5 répétitions → amplitude > seuil → APPRIS
    · Pas de répétition → queue en t^{-0,618} → OUBLI

CONSCIENT : Représentations apprises (co-occurrence) + Résonance
    · Interroge l'inconscient : quels motifs ont survécu ?
    · Binding HRR → relie les traces
    · Résonance → répond ou REFUSE
"""
import json,math,os,time,numpy as np
PHI=(1+math.sqrt(5))/2;A=1/PHI;PI=math.pi;DIM=64
from validation_coeff_quantiques import E_alpha,B_ALPHA

# ══════════════════════════════════════════════════════════════════════
# INCONSCIENT — stockage par répétition via le noyau doré
# ══════════════════════════════════════════════════════════════════════
class Inconscient:
    def __init__(self,seuil=2.5,decay=0.01):
        self.traces={};self.t=0;self.seuil=seuil;self.decay=decay
    
    def kernel(self,dt):
        """Trace résiduelle après délai dt — le noyau doré."""
        if dt<=0:return 1.0
        return B_ALPHA*abs(E_alpha(-PHI*dt**A,A))
    
    def exposer(self,mot):
        """Une occurrence du mot — ajoute la trace et fait vieillir."""
        self.t+=1
        # Ajout de la trace actuelle
        if mot not in self.traces:self.traces[mot]=[]
        self.traces[mot].append(self.t)
        # Vieillissement : chaque trace décroît selon le noyau
        for m in list(self.traces.keys()):
            self.traces[m]=[tk for tk in self.traces[m] if self.kernel(self.t-tk)>self.decay]
            if not self.traces[m]:del self.traces[m]
    
    def amplitude(self,mot):
        """Amplitude cumulée des traces du mot — la force de la mémoire."""
        if mot not in self.traces:return 0.0
        return sum(self.kernel(self.t-tk) for tk in self.traces[mot])
    
    def connus(self):
        """Mots dont l'amplitude dépasse le seuil → APPRIS."""
        return {m for m in self.traces if self.amplitude(m)>=self.seuil}
    
    def tous(self):
        return {m:self.amplitude(m) for m in self.traces}

# ══════════════════════════════════════════════════════════════════════
# CONSCIENT — représentations apprises + résonance
# ══════════════════════════════════════════════════════════════════════
class Conscient:
    def __init__(self,inconscient):
        self.inc=inconscient;self.emb={};self.rng=np.random.default_rng(42)
    
    def apprendre_embeddings(self,corpus):
        """Co-occurrences → embeddings simples (PPMI réduit)."""
        vocab=set()
        for phrase in corpus:
            for m in phrase:vocab.add(m)
        for m in vocab:
            self.emb[m]=self.rng.normal(0,0.1,DIM)  # initialisation
        # Co-occurrence : rapproche les mots qui apparaissent ensemble
        lr=0.05
        for _ in range(100):
            for phrase in corpus:
                for i,m1 in enumerate(phrase):
                    for m2 in phrase[max(0,i-2):i+3]:
                        if m1!=m2 and m1 in self.emb and m2 in self.emb:
                            self.emb[m1]+=lr*(self.emb[m2]-self.emb[m1]*0.1)
    
    def resonance(self,mot,connus):
        """Quel mot connu résonne le plus avec le mot donné ?"""
        if mot not in self.emb:return None,0.0
        best,best_score=None,-1
        for c in connus:
            if c in self.emb:
                score=abs(np.dot(self.emb[mot],self.emb[c]))
                if score>best_score:best_score,best=c,score
        seuil_resonance=0.15
        return (best,best_score) if best_score>seuil_resonance else (None,best_score)
    
    def associer(self,mot):
        """Trouve l'association consciente pour un mot."""
        connus=self.inc.connus()
        best,score=self.resonance(mot,connus)
        return best,score

# ══════════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ══════════════════════════════════════════════════════════════════════
def main():
    t0=time.time()
    print("="*65)
    print("IA HARMONIQUE V2 — Modèle Réduit (Inconscient + Conscient)")
    print("="*65)
    
    inc=Inconscient(seuil=2.5)
    cs=Conscient(inc)
    
    # Phase 1 : Apprentissage inconscient par exposition répétée
    print("\n─ PHASE 1 : L'INCONSCIENT (exposition répétée)")
    exposures=[
        "chat","chien","chat","oiseau","chat","chien","chat","chat",
        "poisson","chien","chat","oiseau","poisson","chien","poisson",
        "cheval","chat","poisson","cheval","poisson","cheval","cheval"
    ]
    for mot in exposures:
        inc.exposer(mot)
        amp=inc.amplitude(mot);connu="✅ APPRIS" if mot in inc.connus() else ""
        if amp>0.05:print(f"  « {mot:10s} » amplitude={amp:.2f} {connu}")
    
    print(f"\n  ─────")
    status=inc.tous()
    for mot,amp in sorted(status.items(),key=lambda x:-x[1]):
        connu="✅ APPRIS" if mot in inc.connus() else ""
        print(f"  {mot:10s} : amplitude={amp:.2f} {connu}")
    
    # Phase 2 : Oubli
    print(f"\n─ PHASE 2 : L'OUBLI (sans répétition, la trace s'efface)")
    for _ in range(15):
        inc.exposer("___vide___")
    status2=inc.tous()
    for mot,amp in sorted(status2.items(),key=lambda x:-x[1]):
        oublie="💨 OUBLIÉ" if mot not in inc.connus() else "✅ survit"
        print(f"  {mot:10s} : amplitude={amp:.2f} {oublie}")
    
    # Phase 3 : Conscient — association
    print(f"\n─ PHASE 3 : LE CONSCIENT (résonance avec l'inconscient)")
    corpus=[["chat","félin","animal"],["chien","canin","animal"],
            ["oiseau","volant","animal"],["poisson","nage","animal"],
            ["cheval","équidé","animal"]]
    cs.apprendre_embeddings(corpus)
    print("  Embeddings appris (co-occurrence).")
    for q in ["félin","canin","volant","nage","équidé"]:
        assoc,score=cs.associer(q)
        if assoc:print(f"  « {q:10s} » → résonne avec « {assoc} » (score={score:.2f})")
        else:print(f"  « {q:10s} » → aucune résonance — REFUS")
    
    print(f"\n─ ARCHITECTURE FINALE")
    print("  INCONSCIENT : noyau K(t) stocke par répétition (zéro paramètre)")
    print("  CONSCIENT   : embeddings appris + résonance (peu de paramètres)")
    print("  REFUS       : si rien ne résonne → silence calibré")
    
    dep={"modele":"inconscient (K(t)) + conscient (embeddings + resonance)",
         "seuil_inconscient":inc.seuil,"mots_appris":list(inc.connus()),
         "date":time.strftime("%Y-%m-%d %H:%M:%S")}
    p=os.path.join("data","benchmarks","ia_v2_modele_reduit_report.json")
    os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)
    print(f"\nRapport : {p} · {time.time()-t0:.1f}s")

if __name__=="__main__":main()
