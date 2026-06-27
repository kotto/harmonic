#!/usr/bin/env python3
"""
ENCODEUR SPECTRAL STABLE — Version robuste et rapide
=====================================================
Encodeur appris: 784 -> 128 -> 10 (spectre)
Decodeur:        10 -> 128 -> 784
Contrainte spectrale: MSE entre amplitudes et distribution H_k
SGD standard sans backward manuel fragile.
Resultat en < 30 secondes, sans NaN.
"""
import numpy as np, time, gzip, struct, os, json

PHI=(1+np.sqrt(5))/2; PI=np.pi; E=np.e; SQ2=np.sqrt(2); SQ3=np.sqrt(3); SQ5=np.sqrt(5)
H_BASE=np.array([PHI,PI,E,SQ2,SQ3,SQ5,E/PI,PHI*SQ2,E*PHI,PI*SQ5])
H_NAMES=['phi','pi','e','sqrt2','sqrt3','sqrt5','e/pi','phi*sqrt2','e*phi','pi*sqrt5']

class StableSpectralEncoder:
    """Autoencodeur simple et stable pour apprentissage du spectre harmonique."""
    def __init__(self, d, seed=42):
        np.random.seed(seed)
        s1,s2=1/np.sqrt(d),1/np.sqrt(128)
        self.W1=np.random.randn(d,128)*s1; self.b1=np.zeros(128)
        self.W2=np.random.randn(128,10)*s2; self.b2=np.zeros(10)
        self.W3=np.random.randn(10,128)*0.1; self.b3=np.zeros(128)
        self.W4=np.random.randn(128,d)*0.1; self.b4=np.zeros(d)
        self.np=sum(w.size for w in [self.W1,self.W2,self.W3,self.W4])

    def forward(self,X):
        h1=np.maximum(0,X@self.W1+self.b1)
        z2=h1@self.W2+self.b2
        sp=np.exp(z2-np.max(z2,1,keepdims=True)); sp/=sp.sum(1,keepdims=True)
        h3=np.maximum(0,sp@self.W3+self.b3)
        recon=1/(1+np.exp(-(h3@self.W4+self.b4)))
        self.cache={'X':X,'h1':h1,'z2':z2,'sp':sp,'h3':h3,'rec':recon}
        return sp,recon

    def encode(self,X):
        h1=np.maximum(0,X@self.W1+self.b1)
        z2=h1@self.W2+self.b2
        sp=np.exp(z2-np.max(z2,1,keepdims=True)); sp/=sp.sum(1,keepdims=True)
        return sp

    def train_step(self,X,lr=0.01):
        sp,rec=self.forward(X)
        bs=X.shape[0]; c=self.cache
        # Reconstruction MSE
        drec=2*(rec-X)/bs; dsig=drec*rec*(1-rec)
        gW4=c['h3'].T@dsig; gb4=dsig.sum(0); dh3=dsig@self.W4.T
        gd3=dh3*(c['h3']>0)
        gW3=c['sp'].T@gd3; gb3=gd3.sum(0); dsp=gd3@self.W3.T
        # Softmax backward
        dsoft=dsp*sp-sp*(dsp*sp).sum(1,keepdims=True)
        gW2=c['h1'].T@dsoft; gb2=dsoft.sum(0); dh1=dsoft@self.W2.T
        gz1=dh1*(c['h1']>0)
        gW1=X.T@gz1; gb1=gz1.sum(0)
        # Contrainte spectrale
        mean_sp=sp.mean(0); h_n=H_BASE/H_BASE.sum()
        amp_n=mean_sp/(mean_sp.sum()+1e-8)
        grad_sp_loss=0.1*2*(amp_n-h_n)/10
        gW2+=c['h1'].T@(grad_sp_loss[np.newaxis,:]*sp*(1-sp))/bs
        # Conservation
        ni=np.mean(np.linalg.norm(X,1)); no=np.mean(np.linalg.norm(rec,1))
        gc=0.05*2*(no-ni)*(rec/(no*bs+1e-8))
        gW4+=c['h3'].T@(gc*rec*(1-rec))
        # Update
        for w,g in [(self.W1,gW1),(self.b1,gb1),(self.W2,gW2),(self.b2,gb2),
                     (self.W3,gW3),(self.b3,gb3),(self.W4,gW4),(self.b4,gb4)]:
            w-=lr*np.clip(g,-1,1)
        # Metriques
        loss=np.mean((rec-X)**2)
        ms=sp.mean(0); ms_n=ms/(ms.sum()+1e-8)
        sloss=np.mean((ms_n-h_n)**2)
        corr=np.corrcoef(ms,H_BASE)[0,1]
        return {'loss':float(loss),'spectral':float(sloss),'corr':float(corr),
                'grad_norm':float(np.linalg.norm(gW1))}

def load_mnist(d='.'):
    files={'ti':'train-images-idx3-ubyte.gz','tl':'train-labels-idx1-ubyte.gz',
           'xi':'t10k-images-idx3-ubyte.gz','xl':'t10k-labels-idx1-ubyte.gz'}
    urls={k:f'https://ossci-datasets.s3.amazonaws.com/mnist/{f}' for k,f in files.items()}
    data={}
    for k,f in files.items():
        p=os.path.join(d,f)
        if not os.path.exists(p):
            import urllib.request; urllib.request.urlretrieve(urls[k],p)
        with gzip.open(p,'rb') as fh:
            if k in['tl','xl']: struct.unpack('>II',fh.read(8)); data[k]=np.frombuffer(fh.read(),np.uint8)
            else: _,n,r,c=struct.unpack('>IIII',fh.read(16)); data[k]=np.frombuffer(fh.read(),np.uint8).reshape(n,r*c).astype(np.float64)/255.
    return data['ti'],data['tl'],data['xi'],data['xl']

def main():
    print("="*60)
    print("  ENCODEUR SPECTRAL STABLE (sans NaN)")
    print("  784 -> 128 -> 10 -> 128 -> 784")
    print("="*60)

    Xtr,_,Xte,_=load_mnist('.'); n=10000
    X_tr,X_te=Xtr[:n],Xte[:2000]
    print(f"  Train: {n} | Test: 2000")

    enc=StableSpectralEncoder(784)
    print(f"  Params: {enc.np:,}")

    EP,BS,LR=20,128,0.01; nb=n//BS
    h={'loss':[],'spectral':[],'corr':[]}
    t0=time.time()

    for ep in range(EP):
        perm=np.random.permutation(n); Xs=X_tr[perm]
        tl,tsl,tco=0,0,0
        for i in range(nb):
            s,e=i*BS,(i+1)*BS; Xb=Xs[s:e]
            info=enc.train_step(Xb,LR)
            tl+=info['loss']; tsl+=info['spectral']; tco+=info['corr']
        al,asl,aco=tl/nb,tsl/nb,tco/nb
        h['loss'].append(al); h['spectral'].append(asl); h['corr'].append(aco)
        sp,_=enc.forward(X_te)
        ms=sp.mean(0); test_corr=np.corrcoef(ms,H_BASE)[0,1]
        print(f"  Ep{ep+1:2d} | Recon:{al:.4f} Spectral:{asl:.4f} "
              f"Corr:{aco:.4f} TestCorr:{test_corr:.4f} | {time.time()-t0:.1f}s")
        LR*=0.95
        if np.isnan(al): print("  NaN detecte, arret."); break

    tt=time.time()-t0
    sp,_=enc.forward(X_te)
    ms=sp.mean(0); final_corr=np.corrcoef(ms,H_BASE)[0,1]

    print(f"\n{'='*60}")
    print(f"  RESULTATS (Temps: {tt:.1f}s)")
    print(f"{'='*60}")
    print(f"\n  Distribution apprise vs H_k:")
    print(f"  {'Harmonique':<14} | {'H_k':>8} | {'Ampl. apprise':>14} | {'H_k norm':>10} | {'Ratio':>8}")
    print(f"  {'-'*14}+{'-'*10}+{'-'*16}+{'-'*12}+{'-'*10}")
    hn=H_BASE/H_BASE.sum()
    for k in range(10):
        a=ms[k]; r=a/hn[k] if hn[k]>0 else 0; bar='#'*int(a*80)
        print(f"  H_{k+1} ({H_NAMES[k]:<8}) | {H_BASE[k]:8.3f} | "
              f"{a:7.4f} {bar:<7} | {hn[k]:10.4f} | {r:8.4f}")
    print(f"\n  Correlation spectre <-> H_k: {final_corr:.4f}")
    if final_corr>0.7: print("  >>> ENCODEUR APPRIS LA STRUCTURE HARMONIQUE! <<<")
    elif final_corr>0.4: print("  >>> Capture partielle <<<")
    else: print("  >>> Insuffisant <<<")

    # Projection naive pour comparaison
    def naive(d):
        f=d.flatten(); fn=f/(np.linalg.norm(f)+1e-8)
        s=np.zeros(10)
        for k in range(10):
            pk=H_BASE[k]*(PHI**(k+1)); s[k]=abs(np.dot(fn,np.ones_like(fn)*pk/np.sqrt(len(fn))))
        ss=s.sum()
        return s/(ss+1e-8)
    nse=np.array([naive(x) for x in X_te[:500]])
    nc=np.corrcoef(nse.mean(0),H_BASE)[0,1]
    print(f"\n  Correlation naive: {nc:.4f}")
    print(f"  Encodeur appris:   {final_corr:.4f}")
    if final_corr>nc: print("  >>> ENCODEUR APPRIS SURPASSE PROJECTION NAIVE! <<<")
    else: print("  >>> Plus d'entrainement necessaire <<<")

    with open('spectral_encoder_stable.json','w') as f:
        json.dump({'final_corr':float(final_corr),'naive_corr':float(nc),
                   'mean_spectrum':[float(x) for x in ms],
                   'history':{k:[float(x) for x in v] for k,v in h.items()}},f,indent=2)
    print(f"\n  Rapport: spectral_encoder_stable.json")
    print(f"{'='*60}")

if __name__=='__main__': main()