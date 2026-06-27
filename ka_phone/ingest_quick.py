#!/usr/bin/env python3
"""Quick direct ingestion - 38 faits en quelques secondes."""
import numpy as np, math, time, hashlib, os, sys

PHI = (1+math.sqrt(5))/2
SIZE = 1024
DATA_DIR = os.path.join(os.path.dirname(__file__) or '.', '..', 'data', 'emergence')
os.makedirs(DATA_DIR, exist_ok=True)

h = np.zeros((SIZE, SIZE), dtype=np.complex128)

def add_fact(text, amp=0.05):
    global h
    hh = hashlib.sha256(text.encode()[:200]).hexdigest()
    kx = (int(hh[:16],16) % (SIZE*100))/100.0
    ky = (int(hh[16:32],16) % (SIZE*100))/100.0
    kx = (kx-SIZE/2)/SIZE*20
    ky = (ky-SIZE/2)/SIZE*20
    x = np.linspace(-SIZE/2, SIZE/2, SIZE)
    y = np.linspace(-SIZE/2, SIZE/2, SIZE)
    X, Y = np.meshgrid(x, y)
    env = np.exp(-(X**2+Y**2)/(2*4.0**2))
    h += amp * env * np.exp(1j*(kx*X/20 + ky*Y/20))
    if np.max(np.abs(h)) > 500:
        h *= 0.95

facts = [
    "Afrique berceau humanite Homo sapiens decouvert Ethiopie 195000 ans Maroc 300000 ans",
    "Egypte ancienne Kemet civilisation africaine vallee Nil -3150 unification Narmer pyramides",
    "Royaume Kouch Nubie Soudan 25e dynastie pharaons noirs -747 a -656 Ethiopie Axoum",
    "Empire Mali 1230-1670 Soundiata Keita Mansa Moussa pelerinage Mecque 1324 or",
    "Universite Sankore Tombouctou Mali 25000 etudiants astronomie mathematiques medecine",
    "Royaume Benin 1180-1897 bronzes art mondial maitrise technique exceptionnelle",
    "Grand Zimbabwe 1100-1450 capitale empire constructions pierre sans mortier 11m",
    "Ethiopie bataille Adoua 1896 seul pays africain vaincre colonisation europeenne",
    "Conference Berlin 1884-1885 partage Afrique sans participation africaine",
    "Ghana independance 1957 Kwame Nkrumah premier pays Afrique subsaharienne",
    "Organisation Unite Africaine 1963 Union Africaine 2002 ZLECAf panafricanisme",
    "Manuscrits Tombouctou 700000+ couvrent tous domaines savoir tradition ecrite",
    "Philosophie Ubuntu bantoue je suis parce que nous sommes solidarite interconnexion",
    "Maat Egypte ancienne 42 lois ordre verite justice equilibre ethique cosmique",
    "Gravitation Newton 1687 F=G*m1*m2/r2 Einstein relativite generale 1915 espace-temps",
    "Mecanique quantique Heisenberg incertitude dualite onde-particule superposition Planck h",
    "Maxwell 1865 electromagnetisme lumiere onde c=299792458 m/s equations unifiees",
    "Thermodynamique entropie Boltzmann S=k*log(W) conservation energie zero absolu",
    "Darwin 1859 evolution selection naturelle ADN Watson Crick 1953 heredite ancetre commun",
    "Big Bang 13.8 milliards annees energie noire 68% matiere noire 27% univers expansion",
    "Mathematiques pi=3.14159 e=2.71828 phi=1.618034 nombre or i2=-1 constantes universelles",
    "Tectonique plaques Wegener 1912 derive continents Terre 4.54 milliards annees geologie",
    "Atome noyau protons neutrons electrons Mendeleiev 1869 tableau periodique 118 elements",
    "Chimie organique carbone 4 liaisons eau H2O solvant universel liaison covalente",
    "Machine Turing 1936 calcul universel P vs NP probleme millenaire informatique",
    "Intelligence artificielle deep learning transformers Vaswani 2017 attention NLP",
    "Ordinateur quantique qubits superposition algorithme Shor intrication teleportation",
    "Internet TCP/IP 1974 HTTP Tim Berners-Lee 1989 DNS 5 milliards utilisateurs 2025",
    "Python JavaScript Rust C Haskell langages programmation informatique software",
    "Stoicisme Zenon -300 distinguer depend de nous serenite Marc Aurele sagesse",
    "Socrate -470 -399 je sais que je ne sais rien maieutique dialogue philosophie",
    "Lumieres XVIIIe Voltaire Rousseau Diderot Kant Sapere aude ose savoir droits Homme",
    "Afrique 54 pays 1.4 milliard habitants 2000+ langues Sahara Nil 6650km",
    "Asie 4.7 milliards 60% humanite Everest 8849m Inde Chine 1.4G Russie",
    "Europe 750 millions 44 pays UE 27 Schengen Renaissance Lumieres Revolution",
    "Ameriques Maya Azteque Inca Amazonie 6.7M km2 USA premiere economie",
    "Oceanie Australie Nouvelle-Zelande culture aborigene 60000 ans corail 2300km",
    "Moyen-Orient berceau 3 monotheismes Mesopotamie ecriture cuneiforme petrole",
]

t0 = time.time()
for i, text in enumerate(facts):
    add_fact(text)
dt = time.time() - t0

energy = np.sum(np.abs(h)**2)
nonzero = np.count_nonzero(np.abs(h) > 1e-10)

path = os.path.join(DATA_DIR, 'abc_hologram_1024.npy')
np.save(path, h)

print(f"Ingestion: {len(facts)} faits en {dt:.1f}s ({len(facts)/dt:.0f}/sec)")
print(f"Energy: {energy:.0f} | Max: {np.max(np.abs(h)):.4f} | Mean: {np.mean(np.abs(h)):.6f}")
print(f"Non-zero: {nonzero:,} ({nonzero/(1024*1024)*100:.1f}%)")
print(f"File: {path} ({os.path.getsize(path)//1024} KB)")

# FFT emergence check
amp = np.abs(h)
fft = np.fft.fftshift(np.abs(np.fft.fft2(amp)))
c = 512
radial = np.zeros(200)
counts = np.zeros(200)
for i in range(1024):
    for j in range(1024):
        r = int(math.sqrt((i-c)**2 + (j-c)**2))
        if r < 200:
            radial[r] += fft[i,j]
            counts[r] += 1
radial = np.divide(radial, np.maximum(counts, 1))

peaks = []
for i in range(5, 195):
    if radial[i] > radial[i-1] and radial[i] > radial[i+1] and radial[i] > np.mean(radial[:200]):
        peaks.append((i, radial[i]))

print(f"FFT peaks: {len(peaks)}")
for p in peaks[:8]:
    print(f"  r={p[0]} amp={p[1]:.4f}")

if len(peaks) >= 2:
    for i in range(len(peaks)-1):
        r = peaks[i+1][0] / peaks[i][0]
        tag = ""
        if abs(r - math.sqrt(2)) < 0.05:
            tag = f" [sqrt(2)={math.sqrt(2):.4f} EMERGENT!]"
        elif abs(r - PHI) < 0.05:
            tag = f" [phi={PHI:.4f} EMERGENT!]"
        elif abs(r - math.pi/2) < 0.05:
            tag = f" [pi/2={math.pi/2:.4f} EMERGENT!]"
        print(f"  Ratio {peaks[i][0]}->{peaks[i+1][0]}: {r:.4f}{tag}")

print("DONE")