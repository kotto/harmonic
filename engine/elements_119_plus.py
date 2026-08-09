#!/usr/bin/env python3
"""elements_119_plus.py — LA SUITE DU TABLEAU : Z=119 à 200"""
import json,math,os,time;PHI=(1+math.sqrt(5))/2;A=1/PHI

def madelung(n_max=10):
    sous=[]
    for n in range(1,n_max+1):
        for l in range(min(4,n)):  # s,p,d,f — et g (l=4) à partir de n=5
            if l<=3 or (l==4 and n>=5):sous.append((n,l,2*(2*l+1)))
    return sorted(sous,key=lambda s:(s[0]+s[1],s[0]))

def generer(Z_max=200):
    sous=madelung(10)
    # Ajout g (l=4) à partir de n=5
    for n in range(5,10):
        sous.append((n,4,2*(2*4+1)))  # 5g,6g,... capacité 18
    sous=sorted(sous,key=lambda s:(s[0]+s[1],s[0]))
    rempli=[0]*len(sous);elements=[]
    for Z in range(1,Z_max+1):
        for idx,(n,l,cap) in enumerate(sous):
            if rempli[idx]<cap:rempli[idx]+=1;break
        config="".join(f"{n}{'spdfg'[l]}{rempli[i]}" for i,(n,l,_) in enumerate(sous) if rempli[i]>0)
        periode=max(n for i,(n,l,_) in enumerate(sous) if rempli[i]>0)
        ns=sum(rempli[i] for i,(n,l,_) in enumerate(sous) if n==periode and l==0)
        np_=sum(rempli[i] for i,(n,l,_) in enumerate(sous) if n==periode and l==1)
        nd=sum(rempli[i] for i,(n,l,_) in enumerate(sous) if n==periode-1 and l==2)
        nf=sum(rempli[i] for i,(n,l,_) in enumerate(sous) if n==periode-2 and l==3)
        ng=sum(rempli[i] for i,(n,l,_) in enumerate(sous) if l==4)
        if periode==1 and ns==2:groupe=18
        elif np_>0:groupe=10+ns+np_
        elif nd>0:groupe=ns+nd
        elif nf>0 or ng>0:groupe=3  # f-block et g-block → groupe 3
        else:groupe=ns
        elements.append({"Z":Z,"periode":periode,"groupe":groupe,"config":config[-40:]})
    return elements

def main():
    el=generer(200)
    # Nobles
    nobles=[e for e in el if e["groupe"]==18]
    # Périodes
    for p in range(8,11):
        per=[e for e in el if e["periode"]==p]
        if per:print(f"Période {p}: Z={per[0]['Z']}–{per[-1]['Z']} ({len(per)} éléments)")

    print(f"\nNouveaux gaz nobles (>118):")
    for e in nobles:
        if e["Z"]>118:print(f"  Z={e['Z']:4d} : {e['config'][-30:]}")
    
    print(f"\nBloc g (l=4 — premiers éléments avec électrons g):")
    g_block=[e for e in el if 'g' in e['config'] and e['Z']>=121]
    for e in g_block[:10]:print(f"  Z={e['Z']:4d} P{e['periode']} G{e['groupe']:2d} : {e['config'][-30:]}")
    print(f"  ... ({len(g_block)} éléments dans le bloc g)")

    print(f"\nÎle de stabilité prédite (magique N≈184, Z≈120-126):")
    for z in range(119,127):
        e=next(x for x in el if x['Z']==z)
        print(f"  Z={z:3d} P{e['periode']} G{e['groupe']:2d} : {e['config'][-30:]}")
    
    dep={"nouveaux_nobles":[e['Z'] for e in nobles if e['Z']>118],
         "bloc_g_Z_debut":g_block[0]['Z'] if g_block else None,
         "ile_stabilite_Z_119_126":"magique N≈184",
         "date":time.strftime("%Y-%m-%d %H:%M:%S")}
    p=os.path.join("data","benchmarks","elements_119_plus_report.json")
    os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)

if __name__=="__main__":main()
