re#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de Langage Harmonique Final — Qualité LLM
======================================================
Pipeline complet optimisé pour des réponses factuelles
naturelles, sans dépendance externe.

Auteur : KOTTO Alain — 19 Juin 2026
"""
import math, re, random, sys, os, time, json, glob
from typing import List, Dict, Optional
from collections import Counter
import numpy as np

phi = (1+math.sqrt(5))/2; pi=math.pi; e=math.e
sqrt2=math.sqrt(2); sqrt3=math.sqrt(3); sqrt5=math.sqrt(5)
H = np.array([phi,pi,e,sqrt2,sqrt3,sqrt5,e/pi], dtype=np.float64)
H_sum=H.sum()

# ===== NER =====
class NERRobuste:
    SCIENTIFIQUES={'einstein','newton','planck','darwin','curie','pasteur','galilée','galilee','kepler','maxwell','bohr','heisenberg','schrödinger','schrodinger','feynman','hawking','tesla','edison','bell','marconi','mendeleïev','mendeleiev','lavoisier','lemaître','lemaitre','hubble','watson','crick','franklin','wegener','boltzmann','hahn','strassmann'}
    MOIS={'janvier','février','fevrier','mars','avril','mai','juin','juillet','août','aout','septembre','octobre','novembre','décembre'}
    def extraire_valeur(self,texte):
        t=texte.replace('\u202f',' ').replace('\xa0',' ')
        m=re.search(r'\b(\d+[.,]\d+\s*[×xX]\s*10\^?[−-]?\d+\s*\S*)',t)
        if m: return m.group(1).strip()
        m=re.search(r'\b(\d+(?:\s+\d+){1,3}\s+(?:m/s|km/s|km/h|J·s|J/s|J\.s|kg|Hz|W|K|°C|N|Pa|eV))\b',t,re.I)
        if m: return m.group(1).strip()
        m=re.search(r'\b(\d+[.,]\d+(?:\s*[×xX]\s*10\^?[−-]?\d+)?\s*(?:m/s|km/s|km/h|J·s|J/s|J\.s|kg|Hz|W|K|°C|N|Pa|eV|s|m|J))\b',t,re.I)
        if m: return m.group(1).strip()
        m=re.search(r'\b(\d{5,}(?:\s+(?:m/s|km/s|km/h))?)\b',t)
        if m: return m.group(1).strip()
        return None
    def extraire_personne(self,texte):
        tl=texte.lower()
        noms=re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',texte)
        for nom in noms:
            if len(nom)>2 and nom.lower() not in self.MOIS and not any(m in nom.lower() for m in ['question','reponse','quelle','quel','comment']):
                p=nom.split()[0].lower() if nom.split() else ''
                f=nom.split()[-1].lower() if nom.split() else ''
                if p in self.SCIENTIFIQUES or f in self.SCIENTIFIQUES: return nom
        for sci in sorted(self.SCIENTIFIQUES,key=len,reverse=True):
            if sci in tl: return sci.capitalize()
        return None
    def extraire_date(self,texte):
        m=re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b',texte)
        return m.group(1) if m else None

# ===== NETTOYEUR =====
class NettoyeurAmeliore:
    def nettoyer(self,texte):
        texte=texte.strip()
        m=re.search(r'(?:question|q)\s*:\s*(.+?)\s*(?:reponse|r[eé]ponse|r)\s*:\s*(.+)',texte,re.I)
        if m: return m.group(2).strip().capitalize()+"."
        for pfx in ["reponse:","réponse:","reponse :","réponse :","information sur ","information: "]:
            if texte.lower().startswith(pfx): texte=texte[len(pfx):].strip()
        m=re.match(r'^(.+?[^0-9×xX][.])(?:\s|$)',texte)
        if m: return m.group(1).strip()
        return texte

# ===== TEMPLATES =====
T={
"valeur":["La valeur de {sujet} est {valeur}.","{sujet} vaut exactement {valeur}.","{sujet} est égal à {valeur}.","On mesure {sujet} comme étant {valeur}.","{sujet} a pour valeur {valeur}."],
"personne_decouverte":["C'est {personne} qui a découvert {sujet}.","La découverte de {sujet} est due à {personne}.","{personne} est le scientifique qui a mis en évidence {sujet}.","On doit la découverte de {sujet} à {personne}."],
"personne_definition":["{personne} est {definition}.","{personne} était {definition}.","{personne}, {definition}."],
"explication":["{sujet} fonctionne ainsi : {reponse}","Le principe de {sujet} est le suivant : {reponse}","{sujet} consiste en {reponse}","Voici comment {sujet} opère : {reponse}"],
"definition":["{sujet} est {reponse}","On appelle {sujet} {reponse}","{sujet} désigne {reponse}","Le terme {sujet} fait référence à {reponse}"],
}

# ===== POST-TRAITEMENT =====
class PostTraitement:
    def corriger(self,texte):
        texte=re.sub(r'\b(le|la)\s+([aeéèêhiouâîôû])',r"l'\2",texte)
        texte=texte.replace('de le ','du ').replace('de les ','des ').replace('à le ','au ').replace('à les ','aux ')
        texte=texte.replace('ce est ',"c'est ").replace('que il ',"qu'il ").replace('si il ',"s'il ").replace('ne est ',"n'est ")
        texte=re.sub(r'\.\s+([a-z])',lambda m:'. '+m.group(1).upper(),texte)
        if texte and texte[0].islower(): texte=texte[0].upper()+texte[1:]
        texte=re.sub(r'\s{2,}',' ',texte); texte=re.sub(r'\s+([.,;:!?])',r'\1',texte)
        texte=texte.strip()
        if texte and texte[-1] not in '.!?': texte+='.'
        texte=texte.replace('..','.').replace('  ',' ')
        return texte

# ===== GÉNÉRATEUR =====
class GenerateurLangageFinal:
    def __init__(self):
        self.ner=NERRobuste(); self.nettoyeur=NettoyeurAmeliore(); self.grammaire=PostTraitement()
    def _extraire_sujet(self,q):
        q=q.lower().strip()
        for p in ["quelle est la valeur de ","quelle est la ","quel est le ","quel est l'","quelle est l'","quel est ","quelle est ","qui a découvert ","qui a inventé ","qui est ","qui était ","comment fonctionne ","comment marche ","comment ","qu'est-ce que ","qu'est-ce qu'","c'est quoi ","pourquoi ","explique ","décris "]:
            if q.startswith(p): q=q[len(p):]; break
        for a in ["la ","le ","l'","une ","un ","des ","les "]:
            if q.startswith(a): q=q[len(a):]; break
        q=q.strip(); return q[0].upper()+q[1:] if q else "ce sujet"
    def formuler(self,question,faits):
        if not faits: return "Je ne dispose pas d'assez d'informations."
        nets=[]; 
        for f in faits:
            n=self.nettoyeur.nettoyer(f)
            if n and n not in nets: nets.append(n)
        if not nets: return "Impossible de formuler une réponse."
        fp=nets[0]; tous=' '.join(nets)
        personne=self.ner.extraire_personne(tous); valeur=self.ner.extraire_valeur(tous)
        date=self.ner.extraire_date(tous); sujet=self._extraire_sujet(question); q=question.lower()
        if any(m in q for m in ['qui est','qui était','qui a']):
            if personne:
                if any(m in q for m in ['a découvert','a inventé','découvert']):
                    tpl=random.choice(T["personne_decouverte"]); reponse=tpl.format(personne=personne,sujet=sujet)
                else:
                    tpl=random.choice(T["personne_definition"]); reponse=tpl.format(personne=personne,definition=fp.rstrip('.'))
            else: reponse=fp
        elif any(m in q for m in ['quelle est','quel est','valeur','vitesse','constante','masse']):
            if valeur: tpl=random.choice(T["valeur"]); reponse=tpl.format(sujet=sujet,valeur=valeur)
            else: reponse=fp
        elif any(m in q for m in ['comment','pourquoi','fonctionne','marche']):
            tpl=random.choice(T["explication"]); reponse=tpl.format(sujet=sujet,reponse=fp.rstrip('.'))
        elif any(m in q for m in ["qu'est-ce","c'est quoi","définition"]):
            tpl=random.choice(T["definition"]); reponse=tpl.format(sujet=sujet,reponse=fp.rstrip('.'))
        else: reponse=fp
        if date and date not in reponse: reponse+=f" Cela remonte à {date}."
        if len(nets)>1:
            f2=nets[1]
            if len(f2)>30 and f2[:30] not in reponse[:len(reponse)//2]:
                c=random.choice([" Par ailleurs, "," De plus, "," À noter que "]); reponse+=c+f2[0].lower()+f2[1:]
        reponse=self.grammaire.corriger(reponse)
        return reponse

# ===== ASSISTANT FINAL =====
class AssistantHarmoniqueFinal:
    def __init__(self): self.generateur=GenerateurLangageFinal(); self.moteur=None
    def initialiser(self):
        sys.path.insert(0,os.path.dirname(__file__))
        from assistant_harmonique_vocal import HologrammeMinimal
        self.moteur=HologrammeMinimal(); return self.moteur.charger(max_total=15000)
    def repondre(self,question):
        if not self.moteur: self.initialiser()
        r=self.moteur.rechercher(question,top_k=3)
        return self.generateur.formuler(question,[x[0] for x in r])

def demo():
    print("="*60); print("GÉNÉRATEUR FINAL — Qualité LLM"); print("="*60); print()
    a=AssistantHarmoniqueFinal(); n=a.initialiser(); print(f"  {n} connaissances\n")
    qs=["quelle est la constante de Planck","qui a découvert la relativité","comment fonctionne la photosynthèse","quelle est la vitesse de la lumière","qu'est-ce que le Big Bang","qui est Albert Einstein","quelle est la masse de l'électron","qu'est-ce que la résonance de Schumann"]
    for q in qs:
        print(f"  ❓ {q}"); r=a.repondre(q); print(f"  💬 {r}\n")
    print("="*60); print("✅ TERMINÉ"); print("="*60)

if __name__=="__main__": demo()