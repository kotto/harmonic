#!/usr/bin/env python3
"""gw150914_analyse.py — Analyse ringdown GW150914 : Mittag-Leffler vs standard"""
import requests, json, math, os, time, io, numpy as np
from scipy.optimize import curve_fit
PHI=(1+math.sqrt(5))/2;A=1/PHI;PI=math.pi;GPS=1126259462.4
from validation_coeff_quantiques import E_alpha

print("="*60)
print("GW150914 — ringdown : Mittag-Leffler vs exponentielle")
print("="*60)

# Téléchargement HDF5
bloc=(int(GPS)//4096)*4096;ok=False
for fmt,ext in [("4KHZ_R1","hdf5"),("4KHZ_R1","hdf5")]:
    url=f"https://www.gw-openscience.org/archive/data/O1/{bloc}/H-H1_GWOSC_{fmt}-{bloc}-4096.{ext}"
    try:
        r=requests.get(url,timeout=60)
        if r.status_code==200:ok=True;break
    except:pass

if ok:
    print(f"Données réelles téléchargées : {len(r.content)} octets")
    import h5py
    with h5py.File(io.BytesIO(r.content),'r') as f:
        strain=f['strain']['Strain'][:]
        gps0=f['strain']['Strain'].attrs['Xstart']
        dt=1.0/f['strain']['Strain'].attrs['Xspacing']
    t=gps0+np.arange(len(strain))*dt;i0=np.argmin(np.abs(t-GPS))
    i1=i0+int(0.005/dt);i2=i0+int(0.050/dt)
    t_ring=t[i1:i2]-GPS;h_ring=strain[i1:i2]
    from scipy.signal import butter,filtfilt
    b,a=butter(4,[200/(1/dt/2),300/(1/dt/2)],'band');h_filt=filtfilt(b,a,h_ring)
    source="GW150914 réel (LIGO H1)"
else:
    print("Données LIGO indisponibles — signal synthétique avec bruit LIGO-like")
    np.random.seed(42);FS=4096;T=0.06;N=int(T*FS);t_ring=np.linspace(0,T,N)
    GAM=PI*250/8;f_R=250
    h_signal=np.exp(-GAM*t_ring)*np.cos(2*PI*f_R*t_ring)
    h_filt=h_signal+np.random.normal(0,0.25,len(t_ring))
    source="GW150914 synthétique (bruit LIGO-like)"

# Ajustement standard
def exp_fit(t,A0,gam,phi):return A0*np.exp(-gam*t)*np.cos(2*PI*250*t+phi)
# Ajustement THU
def ml_fit(t,A0,gam,phi):
    try:
        out=np.array([A0*abs(E_alpha(-gam*max(ti,1e-10)**A,A))*np.cos(2*PI*250*ti+phi) for ti in t])
        if np.any(~np.isfinite(out)):return np.ones(len(t))*1e9
        return out
    except:return np.ones(len(t))*1e9

try:
    from scipy.optimize import curve_fit
    p_std,_=curve_fit(exp_fit,t_ring,h_filt,p0=[1.0,100,0],
                       bounds=([0,10,-PI],[1e3,5000,PI]),maxfev=20000)
    p_thu,_=curve_fit(ml_fit,t_ring,h_filt,p0=[1.0,100,0],
                       bounds=([0,10,-PI],[1e3,5000,PI]),maxfev=20000)
    r_std=np.sum((h_filt-exp_fit(t_ring,*p_std))**2)
    r_thu=np.sum((h_filt-ml_fit(t_ring,*p_thu))**2)
    n=len(t_ring);k=3
    BIC_std=n*np.log(r_std/n)+k*np.log(n)
    BIC_thu=n*np.log(r_thu/n)+k*np.log(n)
    BF=np.exp((BIC_std-BIC_thu)/2)
    print(f"\nSource : {source}")
    print(f"Résidus std : {r_std:.4e}  ·  Résidus THU : {r_thu:.4e}")
    print(f"Facteur de Bayes (THU/standard) = {BF:.1f}")
    if BF>3:print("→ ✅ INDICATION POSITIVE pour la mémoire d'or")
    elif BF<1/3:print("→ ❌ CONTRAINTE — le modèle standard est favorisé")
    else:print("→ ⚠️ INDÉTERMINÉ — données insuffisantes pour trancher")
except Exception as e:
    print(f"Ajustement échoué : {e}");BF=1.0

dep={"source":source,"BF":float(BF) if 'BF' in dir() else 1.0,
     "date":time.strftime("%Y-%m-%d %H:%M:%S")}
p=os.path.join("data","benchmarks","gw150914_analyse_report.json")
os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)
print(f"Rapport : {p}")
