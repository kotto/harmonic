#!/usr/bin/env python3
"""
MICRO BENCHMARK (rapide <30s): Harmonic Dense vs MLP Dense sur 2k images MNIST
Sans convolution (trop lent sur CPU), pour obtenir un resultat immediat.
"""
import numpy as np, time, gzip, struct, os

PHI=(1+np.sqrt(5))/2; PI=np.pi; E=np.e
H_BASE=[PHI,PI,E,np.sqrt(2),np.sqrt(3),np.sqrt(5),E/PI,PHI*np.sqrt(2),E*PHI,PI*np.sqrt(5)]

def load():
    for k,f in {'ti':'train-images-idx3-ubyte.gz','tl':'train-labels-idx1-ubyte.gz','xi':'t10k-images-idx3-ubyte.gz','xl':'t10k-labels-idx1-ubyte.gz'}.items():
        if not os.path.exists(f):
            import urllib.request; urllib.request.urlretrieve(f'https://ossci-datasets.s3.amazonaws.com/mnist/{f}',f)
    d={}
    for k,f in {'ti':'train-images-idx3-ubyte.gz','tl':'train-labels-idx1-ubyte.gz','xi':'t10k-images-idx3-ubyte.gz','xl':'t10k-labels-idx1-ubyte.gz'}.items():
        with gzip.open(f,'rb') as fh:
            if k in['tl','xl']: struct.unpack('>II',fh.read(8)); d[k]=np.frombuffer(fh.read(),dtype=np.uint8)
            else: _,n,r,c=struct.unpack('>IIII',fh.read(16)); d[k]=np.frombuffer(fh.read(),dtype=np.uint8).reshape(n,r*c).astype(np.float64)/255.0
    return d['ti'],d['tl'],d['xi'],d['xl']

class HarmonicNet:
    def __init__(self,h=64):
        s=1/np.sqrt(784)
        self.W1=np.random.randn(784,h)*s; self.b1=np.zeros(h)
        self.hk=np.array([(i%10)+1 for i in range(h)])
        self.hv=np.array([H_BASE[k-1] for k in self.hk])
        self.W2=np.random.randn(h,10)/np.sqrt(h); self.b2=np.zeros(10)
    def fwd(self,X):
        self.z1=X@self.W1+self.b1
        self.h1=np.maximum(0,self.z1)*self.hv
        l=self.h1@self.W2+self.b2
        e=np.exp(l-l.max(1,keepdims=True)); return e/e.sum(1,keepdims=True)
    def upd(self,X,y,probs,lr=0.01):
        bs=X.shape[0]; eo=probs-y
        eh=eo@self.W2.T; eh=eh/(self.hv+1e-8)*(self.z1>0)
        gW2=self.h1.T@eo/bs; gb2=np.mean(eo,0)
        rf=1/(1+self.hv)
        gW1=X.T@(eh*rf)/bs; gb1=np.mean(eh*rf,0)
        eb=np.mean(np.abs(eo))
        self.W2-=lr*gW2;self.b2-=lr*gb2;self.W1-=lr*gW1;self.b1-=lr*gb1
        np2=self.fwd(X); ea=np.mean(np.abs(np2-y))
        return eb,ea

class MLPNet:
    def __init__(self,h=64):
        s=1/np.sqrt(784); self.W1=np.random.randn(784,h)*s; self.b1=np.zeros(h)
        self.W2=np.random.randn(h,10)/np.sqrt(h); self.b2=np.zeros(10)
    def fwd(self,X):
        self.z1=X@self.W1+self.b1; self.h1=np.maximum(0,self.z1)
        l=self.h1@self.W2+self.b2
        e=np.exp(l-l.max(1,keepdims=True)); return e/e.sum(1,keepdims=True)
    def upd(self,X,y,probs,lr=0.01):
        bs=X.shape[0]; eo=probs-y
        gW2=self.h1.T@eo/bs; gb2=np.mean(eo,0)
        eh=eo@self.W2.T; eh*=(self.z1>0)
        gW1=X.T@eh/bs; gb1=np.mean(eh,0)
        eb=np.mean(np.abs(eo))
        self.W2-=lr*gW2;self.b2-=lr*gb2;self.W1-=lr*gW1;self.b1-=lr*gb1
        np2=self.fwd(X); ea=np.mean(np.abs(np2-y))
        return eb,ea

def ce(p,y): return -np.mean(np.log(np.maximum(np.sum(p*y,1),1e-12)))

def main():
    print("="*50)
    print("  MICRO BENCHMARK (<30s): Harmonic vs MLP")
    print("="*50)
    Xtr,ytr,Xte,yte=load()
    ytr_o=np.eye(10)[ytr]; yte_o=np.eye(10)[yte]
    # Sous-ensemble: 2000 train
    n=2000; Xtr=Xtr[:n]; ytr_o=ytr_o[:n]; ytr=ytr[:n]
    Xte=Xte[:2000]; yte_o=yte_o[:2000]; yte=yte[:2000]
    print(f"  Train: {n} | Test: 2000")

    hd=128; ep=3; bs=64; lr=0.02
    results={}

    for name,Model,harm in [('MLP',MLPNet,False),('Harmonic',HarmonicNet,True)]:
        np.random.seed(42); m=Model(h=hd)
        hh={'va':[],'vl':[],'er':[]}
        t0=time.time()
        for e in range(ep):
            perm=np.random.permutation(n); Xs=Xtr[perm]; ys=ytr_o[perm]
            tl,ta=0,0
            for i in range(n//bs):
                s,e2=i*bs,(i+1)*bs; Xb,yb=Xs[s:e2],ys[s:e2]
                p=m.fwd(Xb); tl+=ce(p,yb); ta+=np.mean(np.argmax(p,1)==np.argmax(yb,1))
                eb,ea=m.upd(Xb,yb,p,lr)
            vp=m.fwd(Xte); vl=ce(vp,yte_o); va=np.mean(np.argmax(vp,1)==yte)
            hh['va'].append(float(va)); hh['vl'].append(float(vl))
            hh['er'].append(float(eb))
            print(f"  {name} Ep{e+1} | Acc={va:.4f} | Loss={vl:.4f} | Err={eb:.4f}")
            lr*=0.95
        hh['time']=time.time()-t0
        results[name]=hh

    ma=results['MLP']['va'][-1]; ha=results['Harmonic']['va'][-1]
    print(f"\n{'='*50}")
    print(f"  RESULTATS FINAUX")
    print(f"{'='*50}")
    print(f"  MLP Dense:       {ma:.4f}")
    print(f"  Harmonic Dense:  {ha:.4f}")
    print(f"  Ratio:           {ha/ma:.2%}" if ma>0 else "  N/A")
    print(f"  Ecart:           {ma-ha:.4f}")
    if ha >= ma*0.95: print(f"  VERDICT: COMPETITIF [OK]")
    elif ha >= ma*0.80: print(f"  VERDICT: PROMETTEUR")
    else: print(f"  VERDICT: INSUFFISANT")

    # Courbes
    print(f"\n  Courbes Accuracy:")
    for e in range(ep):
        print(f"  Ep{e+1}: MLP={results['MLP']['va'][e]:.4f} | Harm={results['Harmonic']['va'][e]:.4f}")

    print(f"\n  Temps: MLP={results['MLP']['time']:.1f}s | Harm={results['Harmonic']['time']:.1f}s")

    import json
    with open('mini_benchmark.json','w') as f:
        json.dump({'mlp_acc':ma,'harmonic_acc':ha,'ratio':ha/ma if ma>0 else 0,
                   'mlp_curve':results['MLP']['va'],'harmonic_curve':results['Harmonic']['va']},f)
    print(f"\n  Rapport: mini_benchmark.json")
    print(f"{'='*50}")

if __name__=='__main__': main()