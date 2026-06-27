#!/usr/bin/env python3
"""Moteur de Traduction Ondulatoire - Probleme Humain -> Ondes Cosmiques"""
import numpy as np, math, sys, json, re, io
from dataclasses import dataclass

if sys.platform=='win32':
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
    sys.stderr=io.TextIOWrapper(sys.stderr.buffer,encoding='utf-8',errors='replace')

PHI=(1+math.sqrt(5))/2; PI=math.pi; E=math.e; SQ2=math.sqrt(2); SQ3=math.sqrt(3); SQ5=math.sqrt(5)

@dataclass
class H: k:int; nom:str; valeur:float; couleur:str; domaine:str; concept:str
H_ALL=[H(1,'phi',PHI,'#ff6b35','fondamentale','nombre,calcul,proportion'),
       H(2,'pi',PI,'#3ef0d8','cycle','cycle,optimisation,periodicite'),
       H(3,'e',E,'#d4a843','croissance','croissance,energie,exponentielle'),
       H(4,'sqrt2',SQ2,'#2ed573','structure','structure,ordre,dualite'),
       H(5,'sqrt3',SQ3,'#7a5cff','spatialite','espace,geometrie,triangulation'),
       H(6,'sqrt5',SQ5,'#ff4757','organique','vivant,organique,pentagonal'),
       H(7,'e/pi',E/PI,'#f0c96e','information','information,entropie,rapport'),
       H(8,'phi*sqrt2',PHI*SQ2,'#c084fc','interaction','interaction forte'),
       H(9,'e*phi',E*PHI,'#22d3ee','expansion','expansion,croissance doree'),
       H(10,'pi*sqrt5',PI*SQ5,'#fb923c','global','champ global')]

CARTE=[
 (['calcul','addition','multiplication','soustraction','division','nombre','arithmetique','equation','algebre','somme','produit','factorielle','operation','numerique','entier','reel','complexe'],[(0,.9),(2,.3),(6,.2)]),
 (['optimisation','optimal','chemin','minimum','maximum','plus court','trajectoire','minimiser','maximiser','efficace','meilleur','optimum','recherche','parcours','itineraire','route','graphe'],[(1,.9),(3,.5),(6,.3)]),
 (['energie','electron','quantique','atome','orbite','niveau','photon','particule','onde','mecanique','hamiltonien','schrodinger','probabilite','spin','fermion','boson','potentiel','puits','barriere','hydrogene','orbital'],[(2,.85),(0,.6),(8,.4),(7,.3)]),
 (['phi','nombre or','proportion','divine','fibonacci','spirale','croissance','harmonie','beaute','esthetique','proportionnel'],[(0,1.),(4,.4),(8,.5)]),
 (['equilibre','pendule','oscillation','balancier','stable','stabilite','balance','resonance','harmonique','vibration','frequence propre','periodique'],[(1,.8),(0,.5),(3,.4)]),
 (['classifier','donnees','classification','categoriser','trier','grouper','cluster','pattern','motif','reconnaissance','apprentissage','label','categorie','etiquette','supervise'],[(6,.9),(3,.5),(4,.4),(0,.3)]),
 (['gravitation','gravite','champ','force','attraction','masse','poids','newton','einstein','relativite','courbure','espace-temps','gravitationnel'],[(9,.8),(1,.6),(4,.4)]),
 (['structure','ordre','organisation','systeme','architecture','organisationnel','hierarchie','configuration','topologie'],[(3,.9),(4,.5),(7,.4)]),
 (['vivant','biologie','cellule','organique','adn','gene','evolution','espece','ecosysteme','vie','organisme','metabolisme'],[(5,.9),(0,.5),(2,.3)]),
 (['information','donnee','entropie','bit','message','signal','communication','transmission','encodage','decodage','shannon','code','langage'],[(6,.95),(3,.4),(1,.3)]),
 (['espace','distance','geometrie','dimension','volume','surface','coordonnee','position','localisation','metrique'],[(4,.9),(3,.5),(9,.3)]),
 (['temps','duree','frequence','periode','rythme','cadence','horloge','simultane','sequence','chronologie','temporel'],[(1,.9),(0,.4),(9,.3)]),
 (['expansion','univers','cosmos','galaxie','etoile','cosmologique','big bang','inflation','cosmique','astrophysique'],[(8,.9),(9,.6),(0,.5),(4,.3)]),
 (['interaction','couplage','liaison','connexion','relation','lien','connecte','reseau','interconnecte'],[(7,.9),(0,.5),(6,.4)]),
 (['probabilite','hasard','aleatoire','stochastique','chance','incertain','statistique','variance','distribution','indetermination','incertitude'],[(1,.7),(6,.7),(0,.3)]),
 (['transformation','changement','mutation','metamorphose','evolution','transition','devenir','convertir'],[(2,.8),(8,.5),(0,.4)]),
 (['dualite','opposition','complementaire','yin','yang','paradoxe','contradiction','dichotomie','binaire','symetrie','polarite'],[(3,.9),(0,.6),(6,.4)]),
 (['spirale','vortex','tourbillon','rotation','helicoidal','enroulement','courbure','torsion'],[(0,1.),(1,.6),(5,.4)]),
 (['conscience','pensee','esprit','mental','cognition','intelligence','raisonnement','logique','reflexion','comprehension'],[(6,.8),(0,.6),(3,.4)]),
 (['fractale','auto-similaire','iteration','recursif','emboitement','autosimilarite','mandelbrot','recursion','infini','repetition'],[(0,.95),(5,.5),(8,.4)]),
]

def analyser_texte(texte):
    t=texte.lower(); s=np.zeros(10); a=np.zeros(10); cd=[]
    for kw,hw in CARTE:
        nb=sum(1 for k in kw if k in t)
        if nb>0:
            boost=min(nb/len(kw),1.)
            for i,w in hw: s[i]+=w*boost; a[i]+=boost
            cd.append(f"{kw[0]}/{kw[1] if len(kw)>1 else kw[0]} (x{nb})")
    if a.sum()<0.5:
        chars=len(set(c for c in t if c.isalpha()))
        s[0]=min(chars/26,1.)*.6; s[1]=(len(t)%10)/10*.4; s[6]=min(len(t)/200,1.)*.5
        if '?' in t: s[6]+=.3; s[1]+=.2
        if re.search(r'[0-9]',t): s[0]+=.4; s[2]+=.2
        if re.search(r'[+\-*/=<>]',t): s[3]+=.5; s[0]+=.3
        for m in ['ligne','point','cercle','triangle','carre','courbe','longueur']:
            if m in t: s[4]+=.3; break
        cd.append("analyse spectrale directe")
    mx=max(s.max(),.001); amps=s/mx
    phases=np.array([((i/10)*2*PI+(PHI*i)%(2*PI))%(2*PI) for i in range(10)])
    return amps,phases,cd

def superposer_ondes(amps,phases,xr=(-3,3),np_pts=500):
    xs=np.linspace(xr[0],xr[1],np_pts)
    comps=np.zeros((10,np_pts))
    for i,h in enumerate(H_ALL): comps[i]=amps[i]*np.cos(h.valeur*xs*PI+phases[i])
    wr=np.zeros(np_pts); wi=np.zeros(np_pts)
    for i,h in enumerate(H_ALL):
        ang=h.valeur*xs*PI+phases[i]; wr+=amps[i]*np.cos(ang); wi+=amps[i]*np.sin(ang)
    return {'xs':xs,'onde_reelle':wr,'onde_imag':wi,'enveloppe':np.sqrt(wr**2+wi**2),'composantes':comps}

@dataclass
class Interference: h1:str; h2:str; type:str; force:float; coherence:float

def analyser_interferences(amps,phases):
    ifs=[]
    for i in range(10):
        for j in range(i+1,10):
            if amps[i]<.05 or amps[j]<.05: continue
            dp=abs(phases[i]-phases[j]); coh=amps[i]*amps[j]*math.cos(dp)
            if abs(coh)>.02:
                ifs.append(Interference(H_ALL[i].nom,H_ALL[j].nom,'constructive' if coh>0 else 'destructive',abs(coh),coh))
    ifs.sort(key=lambda x:-x.force)
    return ifs

@dataclass
class Sol: type_solution:str; equation:str; explication:str; harmonique_dominante:str; domaine:str; interferences:list; amplitudes:np.ndarray; concepts:list

def resoudre_par_resonance(amps,phases,texte,cd,ifs):
    imax=int(np.argmax(amps)); hd=H_ALL[imax]; t=texte.lower()

    # Detecteurs des 4 domaines mathematiques + autres
    algebre=any(m in t for m in ['polynome','racine','resoudre','discriminant','inconnue','variable','coefficient','degre','lineaire','quadratique','cubique','matrice','determinant','systeme','inconnues','substitution','elimination','factorisation','equation','factoriser'])
    geometrie=any(m in t for m in ['triangle','cercle','carre','rectangle','perimetre','aire','angle','polygone','cote','hypotenuse','sphere','cone','cube','pyramide','rayon','diametre','circonference','thales','pythagore','trigonometrie','coordonnees','quadrilatere','trapeze','losange','pentagone','hexagone'])
    analyse=any(m in t for m in ['limite','derivee','integrale','primitive','differentielle','gradient','suite','serie','convergence','divergence','continuite','derivable','asymptote','fonction','logarithme','exponentielle','taylor','maclaurin','fourier','laplace'])
    arithmetique=any(m in t for m in ['premier','diviseur','multiple','divisible','pgcd','ppcm','congruence','modulo','pair','impair','crible','eratosthene','arithmetique','entier','rationnel','fraction','numerateur','denominateur','quotient','reste','divisibilite'])
    energie=any(m in t for m in ['energie','electron','atome','niveau','quantique','photon','hamiltonien','schrodinger','spin','fermion','boson','hydrogene','orbite','orbital'])
    gravitation=any(m in t for m in ['gravit','einstein','relativite','espace-temps','courbure','pesanteur'])
    phi_t=any(m in t for m in ['phi','nombre or','proportion','fibonacci','spirale','coquillage'])
    equilibre=any(m in t for m in ['equilibre','pendule','oscillation','balancier'])
    optimisation=any(m in t for m in ['optimal','chemin','minimum','maximiser','trajectoire','optimiser','plus court'])
    classification=any(m in t for m in ['classif','categor','cluster','trier','grouper','etiquette','donnees'])
    calcul=(bool(re.search(r'[+\-*/=]',t)) and bool(re.search(r'[0-9]',t))) or any(m in t for m in ['addition','multiplication','soustraction','division','factorielle','calculer','somme','produit'])
    espace=any(m in t for m in ['espace','geometrie','dimension','distance','volume','surface','topologie'])
    vivant=any(m in t for m in ['cellule','adn','biolog','organisme','vivant','photosynthese'])

    if algebre: ts="Algebre par Resonance"; eq="Psi_alg = racines de sum a_k*H_k*x^k = 0 -> modes nuls"; ex=f"L'algebre dans l'univers consiste a trouver les points ou l'onde s'annule (noeuds). Resoudre une equation = trouver les frequences pour lesquelles l'interference est destructive totale. Les racines d'un polynome sont les modes spectraux nuls. Harmonique dominante: {hd.nom} ({hd.domaine})."
    elif geometrie: ts="Geometrie Ondulatoire"; eq="Psi_geo = contour H_k*exp(i*k*r) -> forme emergente"; ex=f"La geometrie est une interference d'ondes stationnaires. Un cercle = onde circulaire, un triangle = 3 ondes en resonance. Harmonique dominante: {hd.nom} ({hd.domaine})."
    elif analyse: ts="Analyse Harmonique"; eq="Psi_ana = d/dx(sum H_k*exp(i*phi_k*x)) -> flux spectral"; ex=f"L'analyse est l'etude des VARIATIONS du spectre. Derivee = taux de changement de phase. Integrale = somme coherente sur toutes les frequences. Limite = etat asymptotique. Harmonique: {hd.nom} ({hd.domaine})."
    elif arithmetique: ts="Arithmetique Spectrale"; eq="Psi_arith = prod H_k^{a_k} -> decomposition unique"; ex=f"L'arithmetique est une decomposition en modes propres. Un nombre premier = une harmonique pure. Factorisation = trouver les harmoniques constituantes. Harmonique: {hd.nom} ({hd.domaine})."
    elif calcul: ts="Calcul Ondulatoire"; eq="Psi_calcul = sum (a_n * H_n) par interference"; ex=f"Le calcul n'est pas sequentiel. Les nombres sont des amplitudes d'ondes. Addition=superposition, Multiplication=resonance. Harmonique: {hd.nom} ({hd.domaine})."
    elif energie: ts="Niveau d'Energie Quantique"; nm=re.search(r'n\s*=\s*(\d+)',t); n=int(nm.group(1)) if nm else 1; eq=f"E_n = -R_H / n^2 = {-13.6/(n*n):.2f} eV (n={n})"; ex=f"L'energie est une ONDE STATIONNAIRE. Condition de De Broglie: n*lambda=2*pi*r."
    elif gravitation: ts="Courbure Ondulatoire"; eq="G_mu_nu=(8*pi*G/c^4)*T_mu_nu"; ex="La gravitation est une COURBURE de la trame ondulatoire."
    elif phi_t: ts="Emergence du Nombre d'Or"; eq="phi=(1+sqrt5)/2"; ex="phi est la frequence propre de l'espace-temps."
    elif equilibre: ts="Point Fixe Oscillatoire"; eq="theta(t)=theta0*cos(omega*t)*exp(-gamma*t)"; ex="L'equilibre emerge par interference destructive."
    elif optimisation: ts="Optimisation par Resonance"; eq="Psi_opt=argmin_x |sum H_k*exp(i*phi_k*x)|^2"; ex="Minimum d'action = point de coherence maximale."
    elif classification: ts="Classification Spectrale"; eq="Psi_class=softmax(<donnees|H_k>)"; ex="Classifier = resonner les donnees avec des signatures spectrales."
    elif espace: ts="Geometrie Spectrale"; eq="Psi_espace=sum H_k*exp(i*k*x)"; ex="L'espace est une superposition d'ondes stationnaires."
    elif vivant: ts="Organisation Vivante"; eq="Psi_vie=-entropie+flux_energie"; ex="La vie = onde stationnaire entretenue."
    else: ts=f"Resonance {hd.nom}"; eq=f"Psi=sum A_k*H_k*exp(i*phi_k*x)"; ex=f"Probleme dans le domaine \"{hd.domaine}\" via {hd.nom}."

    return Sol(ts,eq,ex,hd.nom,hd.domaine,ifs[:5],amps,cd)

def traduire(texte):
    amps,phases,cd=analyser_texte(texte)
    _=superposer_ondes(amps,phases)
    ifs=analyser_interferences(amps,phases)
    return resoudre_par_resonance(amps,phases,texte,cd,ifs)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('-p','--probleme',type=str,default=None)
    args=p.parse_args()
    if args.probleme:
        s=traduire(args.probleme)
        print(f"\n  [{s.type_solution}] \"{args.probleme}\"")
        print(f"  Dominante: {s.harmonique_dominante} ({s.domaine})")
        print(f"  Equation: {s.equation}")
        print(f"  Explication: {s.explication}")