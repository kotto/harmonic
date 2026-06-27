#!/usr/bin/env python3
"""
BENCHMARK RAPIDE: HarmonicConv vs CNN (sous-ensemble MNIST)
============================================================
Version allegee: 10k images, 5 epochs, 2 modeles seulement.
Temps estime: ~2 minutes.
"""

import numpy as np
import time, os, gzip, struct, json

PHI=(1+np.sqrt(5))/2; PI=np.pi; E=np.e; SQ2=np.sqrt(2); SQ3=np.sqrt(3); SQ5=np.sqrt(5)
H_BASE=np.array([PHI,PI,E,SQ2,SQ3,SQ5,E/PI,PHI*SQ2,E*PHI,PI*SQ5])

def load_mnist(d='.'):
    files={'train_images':'train-images-idx3-ubyte.gz','train_labels':'train-labels-idx1-ubyte.gz','test_images':'t10k-images-idx3-ubyte.gz','test_labels':'t10k-labels-idx1-ubyte.gz'}
    urls={k:f'https://ossci-datasets.s3.amazonaws.com/mnist/{f}' for k,f in files.items()}
    data={}
    for k,f in files.items():
        p=os.path.join(d,f)
        if not os.path.exists(p):
            import urllib.request
            urllib.request.urlretrieve(urls[k],p)
        with gzip.open(p,'rb') as fh:
            if 'labels' in k:
                struct.unpack('>II',fh.read(8))
                data[k]=np.frombuffer(fh.read(),dtype=np.uint8)
            else:
                _,num,rows,cols=struct.unpack('>IIII',fh.read(16))
                data[k]=np.frombuffer(fh.read(),dtype=np.uint8).reshape(num,rows,cols).astype(np.float64)/255.0
    return data['train_images'],data['train_labels'],data['test_images'],data['test_labels']

def oh(l,n=10):
    o=np.zeros((len(l),n));o[np.arange(len(l)),l]=1;return o

# ===== CONV RAPIDE (vectorielle, pas im2col) =====
def conv2d_fast(X,W,b):
    """Convolution par boucle sur filtres (16 filtres, 5x5)."""
    N,Hin,Win=X.shape;out_ch,_,kh,kw=W.shape
    Hout=Hin-kh+1;Wout=Win-kw+1
    out=np.zeros((N,out_ch,Hout,Wout))
    for oc in range(out_ch):
        for i in range(kh):
            for j in range(kw):
                out[:,oc,:,:]+=X[:,i:i+Hout,j:j+Wout]*W[oc,0,i,j]
        out[:,oc,:,:]+=b[oc]
    return out

class HarmonicConv:
    def __init__(self,hd=64,seed=42):
        np.random.seed(seed)
        self.conv_W=np.random.randn(16,1,5,5)*0.1; self.conv_b=np.zeros(16)
        self.dim=16*12*12
        self.W1=np.random.randn(self.dim,hd)/np.sqrt(self.dim); self.b1=np.zeros(hd)
        self.hk=np.array([(i%10)+1 for i in range(hd)])
        self.hv=np.array([H_BASE[k-1] for k in self.hk])
        self.W2=np.random.randn(hd,10)/np.sqrt(hd); self.b2=np.zeros(10)
        self.np=16*25+16+self.dim*hd+hd+hd*10+10
    def forward(self,X):
        c=conv2d_fast(X,self.conv_W,self.conv_b)
        c=np.maximum(0,c)
        # MaxPool 2x2
        N,oc,h,w=c.shape
        p=np.zeros((N,oc,h//2,w//2))
        for i in range(h//2):
            for j in range(w//2):
                p[:,:,i,j]=c[:,:,i*2:i*2+2,j*2:j*2+2].max(axis=(2,3))
        self.flat=p.reshape(N,-1)
        self.z1=self.flat@self.W1+self.b1
        self.h1=np.maximum(0,self.z1)*self.hv
        logits=self.h1@self.W2+self.b2
        e=np.exp(logits-logits.max(1,keepdims=True))
        return e/e.sum(1,keepdims=True)
    def predict(self,X): return np.argmax(self.forward(X),1)
    def update(self,X,y,probs,lr=0.01):
        bs=X.shape[0]; eo=probs-y
        eh=eo@self.W2.T; hi=1/(self.hv+1e-8)
        ehc=eh*hi*(self.z1>0)
        gW2=self.h1.T@eo/bs; gb2=np.mean(eo,0)
        rf=1/(1+self.hv)
        gW1=self.flat.T@(ehc*rf)/bs; gb1=np.mean(ehc*rf,0)
        # backward to conv weights
        eflat=(ehc*rf)@self.W1.T
        ep=eflat.reshape(self.flat.shape[0],16,12,12)
        ec=np.zeros((bs,16,24,24))
        for i in range(bs):
            for oc2 in range(16):
                for hh in range(12):
                    for ww in range(12):
                        patch=c[i,oc2,hh*2:hh*2+2,ww*2:ww*2+2]
                        mi=np.unravel_index(patch.argmax(),(2,2))
                        ec[i,oc2,hh*2+mi[0],ww*2+mi[1]]=ep[i,oc2,hh,ww]
        ec*=(c>0)
        gcw=np.zeros_like(self.conv_W); gcb=np.zeros(16)
        for oc2 in range(16):
            gcb[oc2]=ec[:,oc2,:,:].sum()
            for i in range(5):
                for j in range(5):
                    gcw[oc2,0,i,j]=(X[:,i:i+24,j:j+24]*ec[:,oc2,:,:]).sum()
        gcw/=bs; gcb/=bs
        eb=np.mean(np.abs(eo))
        self.W2-=lr*gW2;self.b2-=lr*gb2;self.W1-=lr*gW1;self.b1-=lr*gb1
        self.conv_W-=lr*gcw;self.conv_b-=lr*gcb
        np2=self.forward(X)
        ea=np.mean(np.abs(np2-y))
        return {'before':eb,'after':ea,'ok':ea<=eb*1.1}

class ClassicConv:
    def __init__(self,hd=64,seed=42):
        np.random.seed(seed)
        self.conv_W=np.random.randn(16,1,5,5)*0.1; self.conv_b=np.zeros(16)
        self.dim=16*12*12
        self.W1=np.random.randn(self.dim,hd)/np.sqrt(self.dim); self.b1=np.zeros(hd)
        self.W2=np.random.randn(hd,10)/np.sqrt(hd); self.b2=np.zeros(10)
        self.np=16*25+16+self.dim*hd+hd+hd*10+10
    def forward(self,X):
        c=conv2d_fast(X,self.conv_W,self.conv_b)
        self.cr=np.maximum(0,c)
        N,oc,h,w=self.cr.shape
        self.pool=np.zeros((N,oc,h//2,w//2))
        for i in range(h//2):
            for j in range(w//2):
                self.pool[:,:,i,j]=self.cr[:,:,i*2:i*2+2,j*2:j*2+2].max(axis=(2,3))
        self.flat=self.pool.reshape(N,-1)
        self.z1=self.flat@self.W1+self.b1
        self.h1=np.maximum(0,self.z1)
        logits=self.h1@self.W2+self.b2
        e=np.exp(logits-logits.max(1,keepdims=True))
        return e/e.sum(1,keepdims=True)
    def predict(self,X): return np.argmax(self.forward(X),1)
    def update(self,X,y,probs,lr=0.01):
        bs=X.shape[0]; eo=probs-y
        gW2=self.h1.T@eo/bs; gb2=np.mean(eo,0)
        eh=eo@self.W2.T; eh*=(self.z1>0)
        gW1=self.flat.T@eh/bs; gb1=np.mean(eh,0)
        eflat=eh@self.W1.T; ep=eflat.reshape(bs,16,12,12)
        ec=np.zeros((bs,16,24,24))
        for i in range(bs):
            for oc2 in range(16):
                for hh in range(12):
                    for ww in range(12):
                        patch=self.cr[i,oc2,hh*2:hh*2+2,ww*2:ww*2+2]
                        mi=np.unravel_index(patch.argmax(),(2,2))
                        ec[i,oc2,hh*2+mi[0],ww*2+mi[1]]=ep[i,oc2,hh,ww]
        ec*=(self.cr>0)
        gcw=np.zeros_like(self.conv_W); gcb=np.zeros(16)
        for oc2 in range(16):
            gcb[oc2]=ec[:,oc2,:,:].sum()
            for i in range(5):
                for j in range(5):
                    gcw[oc2,0,i,j]=(X[:,i:i+24,j:j+24]*ec[:,oc2,:,:]).sum()
        gcw/=bs; gcb/=bs
        self.W2-=lr*gW2;self.b2-=lr*gb2;self.W1-=lr*gW1;self.b1-=lr*gb1
        self.conv_W-=lr*gcw;self.conv_b-=lr*gcb
        return np.mean(np.abs(eo))

def ce(p,y): return -np.mean(np.log(np.maximum(np.sum(p*y,1),1e-12)))

def train(m,Xtr,ytr,Xte,yte,ep=5,bs=64,lr=0.02,harm=False):
    n=Xtr.shape[0]; nb=n//bs
    h={'tl':[],'ta':[],'vl':[],'va':[],'cr':[],'t':[]}
    for e in range(ep):
        t0=time.time(); perm=np.random.permutation(n); Xs=Xtr[perm]; ys=ytr[perm]
        tl,ta,co=0,0,0
        for i in range(nb):
            s,e2=i*bs,(i+1)*bs; Xb,yb=Xs[s:e2],ys[s:e2]
            p=m.forward(Xb); tl+=ce(p,yb); ta+=np.mean(np.argmax(p,1)==np.argmax(yb,1))
            if harm:
                info=m.update(Xb,yb,p,lr)
                if info['ok']: co+=1
            else: m.update(Xb,yb,p,lr)
        vp=m.forward(Xte); vl=ce(vp,yte); va=np.mean(np.argmax(vp,1)==np.argmax(yte,1))
        h['tl'].append(tl/nb);h['ta'].append(ta/nb);h['vl'].append(vl);h['va'].append(va)
        h['t'].append(time.time()-t0)
        if harm: h['cr'].append(co/nb)
        nm='Harm' if harm else 'CNN'
        crs=f' G=0:{co/nb:.2f}' if harm else ''
        print(f"  Ep{e+1}/{ep} {nm} | L:{tl/nb:.3f}->{vl:.3f} | A:{ta/nb:.3f}->{va:.3f}{crs} | {h['t'][-1]:.1f}s")
        lr*=0.95
    return h

def main():
    print("="*60)
    print("  BENCHMARK RAPIDE: HarmonicConv vs CNN (10k MNIST)")
    print("="*60)
    Xtr,ytr_raw,Xte,yte_raw=load_mnist('.')
    ytr=oh(ytr_raw); yte=oh(yte_raw)
    print(f"  Train: {Xtr.shape[0]} | Test: {Xte.shape[0]}")
    # Sous-ensemble pour rapidite
    Xtr=Xtr[:10000]; ytr=ytr[:10000]
    HD=64; EP=5; BS=64; LR=0.02

    print("\n[1] CNN Classique...")
    cnn=ClassicConv(hd=HD); print(f"  Params: {cnn.np:,}")
    h_cnn=train(cnn,Xtr,ytr,Xte,yte,ep=EP,bs=BS,lr=LR,harm=False)

    print("\n[2] HarmonicConv (reinjection spectrale)...")
    hcn=HarmonicConv(hd=HD); print(f"  Params: {hcn.np:,}")
    h_hcn=train(hcn,Xtr,ytr,Xte,yte,ep=EP,bs=BS,lr=LR,harm=True)

    print(f"\n{'='*55}")
    print(f"  RESULTATS")
    print(f"{'='*55}")
    ca=h_cnn['va'][-1]; ha=h_hcn['va'][-1]
    print(f"  CNN Classique:      {ca:.4f}")
    print(f"  HarmonicConv:       {ha:.4f}")
    print(f"  Ratio:              {ha/ca:.2%}" if ca>0 else "  N/A")
    print(f"  Ecart:              {ca-ha:.4f}")
    if 'cr' in h_hcn:
        print(f"  G=0 HarmonicConv:   {np.mean(h_hcn['cr']):.2%}")

    print(f"\n  Courbes Accuracy (Test):")
    for e in range(EP):
        print(f"  Ep{e+1}: CNN={h_cnn['va'][e]:.4f} | Harm={h_hcn['va'][e]:.4f}")

    report={'cnn_acc':float(ca),'harmonic_acc':float(ha),'ratio':float(ha/ca) if ca>0 else 0,
            'cnn_curve':[float(x) for x in h_cnn['va']],
            'harmonic_curve':[float(x) for x in h_hcn['va']]}
    with open('benchmark_rapide.json','w') as f: json.dump(report,f,indent=2)
    print(f"\n  Rapport: benchmark_rapide.json")
    print(f"{'='*55}")
    print(f"  FIN")
    print(f"{'='*55}")

if __name__=='__main__': main()