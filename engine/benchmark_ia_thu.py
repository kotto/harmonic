#!/usr/bin/env python3
"""benchmark_ia_thu.py — POSITIONAL MEMORY : apprise vs dorée (THU V2)
Protocole pré-enregistré. Seul axe : poids de position. Zéro paramètre pour THU."""
import json,math,os,time,numpy as np
PHI=(1+math.sqrt(5))/2;A=1/PHI
from validation_coeff_quantiques import E_alpha,B_ALPHA

D=16;L_MAX=60;VOCAB=12;N_KEYS=4;SONDE=VOCAB-1
N_STEPS=500;BATCH=32;LR=0.04;SEED=42;GAPS=[5,20,50]

def golden_weights(L):
    w=np.array([1.0]+[B_ALPHA*E_alpha(-PHI*t**A).real for t in range(1,L)])
    return w/w.sum()

def generer_batch(rng,G,batch=BATCH):
    cle=rng.integers(0,N_KEYS,batch);L=G+2
    x=np.zeros((batch,L),dtype=int);y=np.zeros(batch,dtype=int)
    for i in range(batch):
        x[i]=np.concatenate([[cle[i]],rng.integers(N_KEYS,VOCAB-1,G),[SONDE]])
        y[i]=cle[i]
    return x,y

def entrainer_eval(use_golden,rng):
    E=np.random.default_rng(SEED).normal(0,0.12,(VOCAB,D))
    W=np.random.default_rng(SEED+1).normal(0,0.12,(N_KEYS,D))
    pw=(golden_weights(L_MAX) if use_golden else
        np.abs(np.random.default_rng(SEED+2).normal(0,0.1,L_MAX)))
    pw/=pw.sum()
    for step in range(N_STEPS):
        G=int(rng.integers(5,41));x,y=generer_batch(rng,G);ts=x.shape[1]-1
        ex=E[x[:,ts-1::-1]];ctx=np.einsum('btd,t->bd',ex[:,:ts],pw[:ts])/pw[:ts].sum()
        z=ctx@W.T;p=np.exp(z-z.max(1,keepdims=True));p/=p.sum(1,keepdims=True)
        g=(p-np.eye(N_KEYS)[y]);W-=LR*g.T@ctx/len(x)
        gC=g@W/len(x);gE=np.zeros_like(E)
        for i in range(len(x)):
            for tau in range(ts):gE[x[i,ts-1-tau]]+=gC[i]*pw[tau]
        E-=LR*gE
        if not use_golden:
            gp=np.zeros(L_MAX)
            for i in range(len(x)):
                for tau in range(ts):gp[tau]+=np.dot(gC[i],E[x[i,ts-1-tau]])
            pw-=LR*0.005*gp/len(x);pw=np.abs(pw);pw/=pw.sum()+1e-12
    accs={}
    for G in GAPS:
        x,y=generer_batch(rng,G,batch=300);ts=x.shape[1]-1
        ex=E[x[:,ts-1::-1]];ctx=np.einsum('btd,t->bd',ex[:,:ts],pw[:ts])/pw[:ts].sum()
        accs[G]=float(np.mean(np.argmax(ctx@W.T,axis=1)==y))
    return accs

def main():
    t0=time.time();rng=np.random.default_rng(SEED+99)
    print("="*60)
    print("BENCHMARK IA : Poids de position — appris vs dorés (THU)")
    print("="*60)
    print("\n─ Standard (poids APPRIS) :")
    acc_std=entrainer_eval(False,rng)
    for G in GAPS:print(f"  Gap={G:2d} : {acc_std[G]*100:.1f}%")
    print("\n─ THU V2 (poids DORÉS, zéro paramètre) :")
    acc_thu=entrainer_eval(True,rng)
    for G in GAPS:print(f"  Gap={G:2d} : {acc_thu[G]*100:.1f}%")
    n_std=D*VOCAB+N_KEYS*D+L_MAX;n_thu=n_std-L_MAX
    c1=acc_thu[GAPS[-1]]>=acc_std[GAPS[-1]]-0.05
    c2=min(acc_thu.values())>0.30
    c3=n_thu<n_std
    print(f"\n─ VERDICT")
    print(f"  C1 · THU ≥ Std −5% : {'✅' if c1 else '❌'}")
    print(f"  C2 · Apprenable : {'✅' if c2 else '❌'}")
    print(f"  C3 · Moins de params ({n_thu} vs {n_std}) : {'✅' if c3 else '❌'}")
    ok=c1 and c2 and c3
    print(f"  → {'✅ MÉMOIRE DORÉE REMPLACE LES POIDS APPRIS' if ok else '❌ NÉGATIF'}")
    dep={"acc_std":acc_std,"acc_thu":acc_thu,"verdict":ok,"date":time.strftime("%Y-%m-%d %H:%M:%S")}
    p=os.path.join("data","benchmarks","ia_benchmark_report.json")
    os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)
    print(f"Rapport : {p} · {time.time()-t0:.1f}s")
if __name__=="__main__":main()
