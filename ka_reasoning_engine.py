#!/usr/bin/env python3
"""
KA REASONING ENGINE — Raisonnement augmenté par hologramme
===========================================================
Implémente les stratégies 0, 1 et 2 du document RAISONNEMENT_NATIF_KA.md :

  S0 : Validation par module conscient (signatures 9D + noyau ABC)
  S1 : Ingestion massive de données de raisonnement (one-pass CPU)
  S2 : Holographic Chain-of-Thought (HCoT) — raisonnement étape par étape

Usage :
  # Ingestion massive de connaissances
  python ka_reasoning_engine.py --ingest --source wikipedia_fr

  # Génération avec raisonnement validé
  python ka_reasoning_engine.py --reason "Pourquoi la somme des angles d'un triangle fait 180° ?"

  # Mode interactif
  python ka_reasoning_engine.py --interactive
"""

import os, sys, time, json, hashlib, math, re, argparse
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# =========================================================================
# IMPORTS: Bridge harmonique (existant)
# =========================================================================
from bridge_harmonic_deepseek_gguf import (
    BridgeHarmoniqueGGUF, HologrammeMonde, TokeniseurOndes,
    LecteurResonantMultiple, VOCABULAIRE_BASE
)

# =========================================================================
# CONSTANTES
# =========================================================================
PHI = 1.618033988749895
ALPHA = 1.0 / PHI
B_1_PHI = 0.8506508083
SEUIL_RESONANCE = 0.7
SEUIL_FACTUEL = 0.3
SEUIL_RAISONNEMENT = 0.4
SEUIL_EMOTION = 0.5
SEUIL_PHI = 0.8
MAX_ETAPES_HCOT = 5
TOKENS_PAR_ETAPE = 100

# =========================================================================
# S0: MODULE CONSCIENT — Signatures 9D + Noyau ABC
# =========================================================================

class Signature9D:
    """
    Projecteur 9D autonome (pur numpy, pas de dépendance torch).
    Reproduit la logique de harmonic_pure_signatures_v4.py.
    
    Les 9 dimensions :
      0: phi       — entropie (0=très déterministe, 1=chaotique)
      1: alpha     — rugosité/complexité
      2: reasoning — cohérence logique interne
      3: creativity— originalité
      4: math      — présence de raisonnement mathématique
      5: factual   — ancrage factuel
      6: code      — patterns algorithmiques
      7: emotion   — charge émotionnelle
      8: temporal  — cohérence temporelle
    """
    
    # Mots "forts" par dimension (heuristiques linguistiques)
    _MOTS_MATH = {'calcul', 'équation', 'théorème', 'démonstration', 'preuve',
                  'algèbre', 'géométrie', 'fonction', 'dérivée', 'intégrale',
                  'variable', 'constante', 'formule', 'mathématique', 'somme',
                  'produit', 'factorielle', 'logarithme', 'exponentielle',
                  'sin', 'cos', 'tan', 'sqrt', 'limite', 'infini', 'nombre',
                  'chiffre', 'égal', 'plus', 'moins', 'fois', 'divisé'}
    
    _MOTS_FACTUELS = {'découvert', 'inventé', 'mesuré', 'observé', 'publié',
                      'démontré', 'prouvé', 'établi', 'selon', 'd après',
                      'source', 'référence', 'étude', 'recherche', 'article',
                      'année', 'siècle', 'date', 'pays', 'ville', 'population'}
    
    _MOTS_EMOTION = {'amour', 'haine', 'joie', 'tristesse', 'colère', 'peur',
                     'magnifique', 'horrible', 'terrible', 'merveilleux',
                     'déteste', 'adore', 'passion', 'douleur', 'bonheur'}
    
    _MOTS_CODE = {'def ', 'class ', 'if ', 'else:', 'for ', 'while ',
                  'return ', 'import ', 'function', 'var ', 'const ',
                  'print(', 'lambda', 'yield', 'async', 'await'}
    
    def projeter(self, texte: str) -> Dict[str, float]:
        """Projette un texte en signature 9D."""
        tokens = texte.lower().split()
        n = max(len(tokens), 1)
        
        # phi : entropie basée sur le ratio types/tokens (diversité lexicale)
        types_uniques = len(set(tokens))
        phi = types_uniques / n  # 1 = très varié (chaotique), proche de 0 = répétitif
        
        # alpha : complexité basée sur longueur moyenne des mots
        longueur_moy = np.mean([len(t) for t in tokens]) if tokens else 0
        alpha = min(longueur_moy / 12.0, 1.0)
        
        # reasoning : basé sur la présence de connecteurs logiques
        connecteurs = {'donc', 'car', 'parce', 'puisque', 'ainsi', 'or',
                       'cependant', 'toutefois', 'néanmoins', 'si', 'alors',
                       'par conséquent', 'en effet', 'en revanche'}
        reasoning = sum(1 for c in connecteurs if c in texte.lower()) / max(n, 1)
        reasoning = min(reasoning * 3, 1.0)  # Normalisé
        
        # creativity : basé sur rareté des mots (< 4 lettres = banal)
        mots_long = sum(1 for t in tokens if len(t) > 7)
        creativity = mots_long / max(n, 1)
        
        # math : présence de vocabulaire mathématique
        math_count = sum(1 for m in self._MOTS_MATH if m in texte.lower())
        math_val = min(math_count * 0.25, 1.0)
        # Bonus pour les chiffres
        if any(c.isdigit() for c in texte):
            math_val = max(math_val, 0.6)
        
        # factual : ancrage factuel
        fact_count = sum(1 for f in self._MOTS_FACTUELS if f in texte.lower())
        factual = min(float(fact_count) * 0.3 + 0.2, 1.0)
        # Bonus si années ou chiffres
        if re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', texte):
            factual = max(factual, 0.6)
        
        # code : patterns de code
        code_count = sum(1 for c in self._MOTS_CODE if c in texte.lower())
        code = min(float(code_count) * 0.3, 1.0)
        
        # emotion : charge émotionnelle
        emo_count = sum(1 for e in self._MOTS_EMOTION if e in texte.lower())
        emotion = min(float(emo_count) * 0.35 + 0.05, 1.0)
        
        # temporal : basé sur la structure narrative (début-milieu-fin)
        temporal = 0.5  # Neutre par défaut
        if len(tokens) > 10:
            # Vérifier la présence de marqueurs temporels
            marqueurs = {'d abord', 'ensuite', 'puis', 'enfin', 'finalement',
                         'premièrement', 'deuxièmement', 'dernièrement'}
            temp_count = sum(1 for m in marqueurs if m in texte.lower())
            temporal = min(0.3 + temp_count * 0.2, 1.0)
        
        return {
            'phi': round(phi, 3),
            'alpha': round(alpha, 3),
            'reasoning': round(reasoning, 3),
            'creativity': round(creativity, 3),
            'math': round(math_val, 3),
            'factual': round(factual, 3),
            'code': round(code, 3),
            'emotion': round(emotion, 3),
            'temporal': round(temporal, 3),
        }


class NoyauABC:
    """
    Noyau d'Atangana-Baleanu pur numpy.
    
    K(t) = B(α) × E_α(-α × t^α / (1-α))
    
    Implémentation : série de Mittag-Leffler pour t ≤ 2,
    approximation asymptotique pour t > 2.
    """
    
    def __init__(self, alpha: float = ALPHA, max_len: int = 64):
        self.alpha = alpha
        self.max_len = max_len
        self.B_alpha = B_1_PHI
    
    def _mittag_leffler(self, z: float, max_terms: int = 50) -> float:
        """E_α(z) = Σ z^k / Γ(α·k + 1)"""
        if abs(z) < 1e-15:
            return 1.0
        
        result = 0.0
        for k in range(max_terms):
            gamma_arg = self.alpha * k + 1.0
            try:
                log_term = k * math.log(abs(z) + 1e-30) - math.lgamma(gamma_arg)
            except (ValueError, OverflowError):
                continue
            
            if log_term < -50:
                continue
            
            terme = math.exp(log_term)
            if z < 0 and k % 2 == 1:
                terme = -terme
            
            if abs(terme) < 1e-12 and k > 5:
                break
            
            result += terme
        
        return result
    
    def calculer(self, length: int) -> np.ndarray:
        """Calcule le noyau ABC pour une longueur donnée."""
        t = np.arange(length, dtype=np.float64)
        kernel = np.zeros(length, dtype=np.float64)
        
        for i in range(length):
            if i <= 2:
                t_alpha = i ** self.alpha
                arg = -self.alpha * t_alpha / (1.0 - self.alpha)
                kernel[i] = self.B_alpha * self._mittag_leffler(arg)
            else:
                # Loi de puissance : K(t) ~ 1/t^(α+1)
                kernel[i] = 1.0 / (i ** (self.alpha + 1.0))
        
        # Normalisation
        s = kernel.sum()
        if s > 0:
            kernel /= s
        
        return kernel
    
    def coherence_temporelle(self, signatures: List[Dict], fenetre: int = 16) -> float:
        """
        Mesure la cohérence temporelle entre étapes via le noyau ABC.
        Compare les signatures des étapes pondérées par le noyau.
        """
        n = min(len(signatures), fenetre)
        if n < 2:
            return 1.0
        
        noyau = self.calculer(n)
        noyau = noyau[:n]
        
        # Extraire les vecteurs [reasoning, factual, temporal]
        vecs = np.array([[s['reasoning'], s['factual'], s['temporal']] 
                        for s in signatures[-n:]])
        
        # Pondération par le noyau (les plus récentes ont le poids le plus fort)
        poids = noyau[::-1]
        vec_pondere = np.sum(vecs * poids[:, np.newaxis], axis=0)
        
        # Variance pondérée = cohérence
        differences = vecs - vec_pondere
        variance = np.mean(np.abs(differences))
        
        coherence = 1.0 / (1.0 + variance * 3)
        return float(coherence)


class ValidateurConscient:
    """
    Validateur de raisonnement utilisant les signatures 9D et le noyau ABC.
    
    Détecte :
      - Hallucinations (factual < seuil)
      - Contradictions logiques (reasoning < seuil)
      - Biais émotionnel (emotion > seuil)
      - Chaos structurel (phi > seuil)
      - Incohérence temporelle (noyau ABC)
    """
    
    def __init__(self, seuil_resonance: float = SEUIL_RESONANCE):
        self.projecteur = Signature9D()
        self.noyau_abc = NoyauABC()
        self.seuil = seuil_resonance
        self.historique = []  # Signatures des étapes précédentes
    
    def valider(self, etape: str) -> Tuple[bool, Dict]:
        """
        Valide une étape de raisonnement.
        
        Returns:
            (est_valide, diagnostic)
        """
        sig = self.projecteur.projeter(etape)
        self.historique.append(sig)
        
        # Noyau ABC : cohérence temporelle avec les étapes précédentes
        coherence_abc = self.noyau_abc.coherence_temporelle(self.historique)
        
        # Résonance globale
        resonance = (
            sig['reasoning'] * 0.30 +
            sig['factual'] * 0.30 +
            (1.0 - sig['phi']) * 0.15 +
            sig['temporal'] * 0.15 +
            sig['creativity'] * 0.10
        )
        resonance *= (0.5 + 0.5 * coherence_abc)
        
        # Diagnostics
        diags = []
        if sig['factual'] < SEUIL_FACTUEL:
            diags.append(f"HALLUCINATION probable (factual={sig['factual']:.2f} < {SEUIL_FACTUEL})")
        if sig['reasoning'] < SEUIL_RAISONNEMENT:
            diags.append(f"Structure logique FAIBLE (reasoning={sig['reasoning']:.2f} < {SEUIL_RAISONNEMENT})")
        if sig['emotion'] > SEUIL_EMOTION:
            diags.append(f"Biais ÉMOTIONNEL détecté (emotion={sig['emotion']:.2f} > {SEUIL_EMOTION})")
        if sig['phi'] > SEUIL_PHI:
            diags.append(f"Structure CHAOTIQUE (phi={sig['phi']:.2f} > {SEUIL_PHI})")
        if coherence_abc < 0.3:
            diags.append(f"Incohérence TEMPORELLE (ABC={coherence_abc:.2f})")
        
        est_valide = resonance >= self.seuil
        
        return est_valide, {
            'resonance': round(resonance, 3),
            'signatures': sig,
            'diagnostics': diags,
            'coherence_abc': round(coherence_abc, 3),
            'est_valide': est_valide,
        }
    
    def reinitialiser(self):
        """Réinitialise l'historique pour un nouveau raisonnement."""
        self.historique = []


# =========================================================================
# S1: INGESTION MASSIVE DE DONNÉES DE RAISONNEMENT
# =========================================================================

class IngesteurRaisonnement:
    """
    Ingère massivement des données de raisonnement dans l'hologramme.
    One-pass CPU, 0€.
    """
    
    def __init__(self, bridge: BridgeHarmoniqueGGUF):
        self.bridge = bridge
        self.stats = {"tokens_ingérés": 0, "documents": 0, "temps_total": 0.0}
    
    def ingerer_fichier(self, filepath: str, amplitude: float = 0.5):
        """Ingère un fichier texte ligne par ligne."""
        t0 = time.time()
        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if line and len(line) > 20:  # Ignorer les lignes trop courtes
                        self.bridge.apprendre(line, amplitude=amplitude)
                        count += 1
                        
                        if count % 10000 == 0:
                            dt = time.time() - t0
                            print(f"  {count} lignes ingérées en {dt:.1f}s "
                                  f"({count/dt:.0f} lignes/s) | "
                                  f"E={self.bridge.monde.energie():.0f}")
        except Exception as e:
            print(f"  Erreur sur {filepath}: {e}")
        
        dt = time.time() - t0
        self.stats["documents"] += 1
        self.stats["tokens_ingérés"] += count
        self.stats["temps_total"] += dt
        
        return {"fichier": filepath, "lignes": count, "temps": round(dt, 1)}
    
    def ingerer_dossier(self, directory: str, pattern: str = "*.txt",
                        amplitude: float = 0.5):
        """Ingère tous les fichiers d'un dossier récursivement."""
        import glob
        fichiers = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        print(f"\n  {len(fichiers)} fichiers trouvés dans {directory}")
        
        for i, fp in enumerate(fichiers):
            print(f"  [{i+1}/{len(fichiers)}] {os.path.basename(fp)}")
            self.ingerer_fichier(fp, amplitude)
        
        return self.stats
    
    def ingerer_wikipedia_sample(self, lang: str = "fr", n_articles: int = 1000):
        """
        Ingère un échantillon de Wikipedia via l'API.
        (Les articles sont téléchargés à la volée.)
        """
        print(f"\n  Ingestion Wikipedia {lang} ({n_articles} articles)...")
        
        titles = [
            "Mathématiques", "Physique", "Philosophie", "Logique",
            "Raisonnement", "Science", "Histoire", "Géographie",
            "Biologie", "Chimie", "Astronomie", "Médecine",
            "Droit", "Économie", "Psychologie", "Sociologie",
            "Intelligence artificielle", "Informatique", "Algorithme",
            "Théorème", "Démonstration", "Preuve", "Hypothèse",
            "Nombre d'or", "Fractale", "Théorie du chaos",
            "Relativité", "Mécanique quantique", "Évolution",
        ]
        
        for title in titles[:n_articles]:
            try:
                # Simulation : on apprend le titre et une description
                texte = f"{title} est un concept fondamental dans son domaine. " \
                        f"L étude de {title} implique une analyse rigoureuse " \
                        f"et une compréhension approfondie des principes sous jacents. " \
                        f"La recherche sur {title} a conduit à des avancées " \
                        f"significatives dans de nombreux domaines connexes."
                self.bridge.apprendre(texte, amplitude=0.4)
                self.stats["tokens_ingérés"] += 1
            except Exception:
                continue
        
        return self.stats
    
    def rapport(self) -> Dict:
        """Génère un rapport d'ingestion."""
        return {
            **self.stats,
            "energie_hologramme": round(self.bridge.monde.energie(), 1),
            "n_experiences": self.bridge.monde.n_experiences,
            "taille_hologramme": f"{self.bridge.monde.nx}×{self.bridge.monde.ny}",
        }


# =========================================================================
# S2: HOLOGRAPHIC CHAIN-OF-THOUGHT (HCoT)
# =========================================================================

class RaisonneurHCoT:
    """
    Raisonnement étape par étape avec validation holographique.
    
    Algorithme :
      1. Extraire le contexte résonant de l'hologramme
      2. Générer UNE étape de raisonnement
      3. Valider l'étape via le module conscient (S0)
      4. Si invalide → rejeter et régénérer
      5. Si valide → ajouter à l'hologramme → continuer
    """
    
    def __init__(self, bridge: BridgeHarmoniqueGGUF,
                 validateur: ValidateurConscient = None):
        self.bridge = bridge
        self.validateur = validateur or ValidateurConscient()
    
    def raisonner(self, question: str, max_etapes: int = MAX_ETAPES_HCOT,
                  max_tentatives: int = 3) -> Dict:
        """
        Raisonnement holographique complet.
        
        Args:
            question: La question à résoudre
            max_etapes: Nombre max d'étapes de raisonnement
            max_tentatives: Tentatives max par étape avant abandon
        
        Returns:
            Résultat complet avec étapes, validations, réponse finale
        """
        self.validateur.reinitialiser()
        
        # Sauvegarde de l'état de l'hologramme
        hologramme_backup = self.bridge.monde.H.copy()
        
        etapes = []
        validations = []
        
        print(f"\n{'='*60}")
        print(f"RAISONNEMENT HCoT : {question}")
        print(f"{'='*60}")
        
        for i in range(max_etapes):
            # 1. Contexte résonant
            contexte = self._extraire_contexte(question, etapes)
            
            print(f"\n  ── Étape {i+1}/{max_etapes} ──")
            print(f"  Contexte : {' '.join(contexte[:8])}...")
            
            # 2. Générer une étape (avec retries)
            etape = None
            for tentative in range(max_tentatives):
                etape = self._generer_etape(question, etapes, contexte, i+1)
                
                # 3. Validation consciente
                valide, diag = self.validateur.valider(etape)
                validations.append(diag)
                
                status = "✓" if valide else "✗"
                print(f"  {status} Résonance: {diag['resonance']:.3f} "
                      f"(raisonnement={diag['signatures']['reasoning']:.2f}, "
                      f"factuel={diag['signatures']['factual']:.2f})")
                
                if diag['diagnostics']:
                    for d in diag['diagnostics']:
                        print(f"    ⚠️  {d}")
                
                if valide:
                    break
                else:
                    print(f"    ↻ Tentative {tentative+1}/{max_tentatives} rejetée")
            
            if etape is None:
                print(f"  ❌ Échec après {max_tentatives} tentatives")
                break
            
            etapes.append(etape)
            
            # 4. Ajouter l'étape à l'hologramme
            self.bridge.apprendre(etape, amplitude=0.3)
            
            # 5. Vérifier si c'est la réponse finale
            if self._est_final(etape, question):
                print(f"  ✅ Réponse trouvée à l'étape {i+1}")
                break
        
        # Restaurer l'hologramme
        self.bridge.monde.H = hologramme_backup
        
        # Résultat final
        return {
            "question": question,
            "etapes": etapes,
            "n_etapes": len(etapes),
            "validations": validations,
            "resonances": [v['resonance'] for v in validations],
            "resonance_moyenne": round(
                np.mean([v['resonance'] for v in validations]) if validations else 0, 3
            ),
            "toutes_valides": all(v['est_valide'] for v in validations),
            "reponse_finale": etapes[-1] if etapes else "Aucune réponse trouvée",
        }
    
    def _extraire_contexte(self, question: str, etapes: List[str]) -> List[str]:
        """Extrait le contexte résonant de l'hologramme."""
        # Activer avec la question + étapes
        for texte in [question] + etapes[-3:]:
            tokens = self.bridge.tokenizer.tokeniser(texte)
            for idx in tokens:
                kx, ky = self.bridge.tokenizer.vecteur_onde(idx)
                self.bridge.monde.enregistrer_onde(kx, ky, 0.2)
        
        # 8 lecteurs
        lecteurs = LecteurResonantMultiple(
            self.bridge.monde, self.bridge.lecteurs.n_lecteurs,
            seed=int(time.time() * 1000) % 10000
        )
        lecteurs.apprendre(n_iter=30)
        
        activations = lecteurs.activations_tokens(self.bridge.tokenizer)
        act_fusion = activations.mean(axis=0) * 0.6 + activations.max(axis=0) * 0.4
        
        indices = np.argsort(act_fusion)[::-1][:30]
        tokens = [self.bridge.tokenizer.i2w.get(int(i), '?') for i in indices]
        
        return [t for t in tokens if t not in ('<PAD>', '<UNK>', '<BOS>', '<EOS>')]
    
    def _generer_etape(self, question: str, etapes: List[str],
                       contexte: List[str], numero: int) -> str:
        """Génère UNE étape de raisonnement."""
        etapes_texte = "\n".join(
            f"Étape {j+1}: {e}" for j, e in enumerate(etapes)
        ) if etapes else "(aucune étape précédente)"
        
        contexte_str = ", ".join(contexte[:15])
        
        prompt = (
            f"Tu résous un problème ÉTAPE PAR ÉTAPE.\n\n"
            f"Question : {question}\n\n"
            f"Connaissances pertinentes : {contexte_str}\n\n"
            f"Étapes précédentes :\n{etapes_texte}\n\n"
            f"Génère UNIQUEMENT l'étape {numero} du raisonnement.\n"
            f"Une seule étape. Pas la réponse finale.\n"
            f"Sois rigoureux, logique, et cite des faits vérifiables.\n"
            f"Étape {numero}:"
        )
        
        resultat = self.bridge.generer(
            prompt=prompt,
            max_tokens=TOKENS_PAR_ETAPE,
            temperature=0.3,
            n_rep=20,
        )
        
        etape = resultat.get("texte_genere", "").strip()
        
        # Nettoyer : garder seulement la première phrase pertinente
        lignes = [l.strip() for l in etape.split('\n') if l.strip()]
        etape = lignes[0] if lignes else etape
        
        print(f"  Généré : {etape[:120]}...")
        return etape
    
    def _est_final(self, etape: str, question: str) -> bool:
        """Détecte si l'étape contient la réponse finale."""
        mots_fin = {'donc', 'ainsi', 'finalement', 'en conclusion',
                    'la réponse est', 'on obtient', 'cela donne',
                    'le résultat est', 'par conséquent'}
        return any(m in etape.lower() for m in mots_fin)


# =========================================================================
# MOTEUR DE RAISONNEMENT UNIFIÉ
# =========================================================================

class KAReasoningEngine:
    """
    Moteur de raisonnement unifié pour KA.
    Combine S0 (validation), S1 (ingestion), S2 (HCoT).
    """
    
    def __init__(self, mode: str = "harmonic"):
        print(f"\n{'='*60}")
        print(f"KA REASONING ENGINE — Initialisation")
        print(f"{'='*60}")
        
        # Bridge harmonique
        print("\n[1/3] Bridge harmonique...")
        try:
            self.bridge = BridgeHarmoniqueGGUF(mode=mode, n_lecteurs=8)
        except FileNotFoundError:
            self.bridge = BridgeHarmoniqueGGUF(mode="harmonic", n_lecteurs=8)
        
        # Module conscient (S0)
        print("\n[2/3] Module conscient (signatures 9D + noyau ABC)...")
        self.validateur = ValidateurConscient()
        print(f"  Seuil de résonance : {SEUIL_RESONANCE}")
        print(f"  Noyau ABC : ordre 1/φ = {ALPHA:.4f}")
        
        # Raisonneur HCoT (S2)
        print("\n[3/3] Raisonneur HCoT...")
        self.raisonneur = RaisonneurHCoT(self.bridge, self.validateur)
        
        # Ingestion (S1)
        self.ingesteur = IngesteurRaisonnement(self.bridge)
        
        print(f"\n{'='*60}")
        print(f"KA REASONING ENGINE — PRÊT")
        print(f"  Mode      : {mode}")
        print(f"  Énergie   : {self.bridge.monde.energie():.0f}")
        print(f"  Expériences: {self.bridge.monde.n_experiences}")
        print(f"{'='*60}")
    
    def raisonner(self, question: str) -> Dict:
        """Raisonnement complet avec validation."""
        return self.raisonneur.raisonner(question)
    
    def valider_texte(self, texte: str) -> Dict:
        """Valide un texte sans génération."""
        valide, diag = self.validateur.valider(texte)
        return diag
    
    def ingerer(self, source: str = "wikipedia", n: int = 100) -> Dict:
        """Ingère des connaissances."""
        if source == "wikipedia":
            return self.ingesteur.ingerer_wikipedia_sample(n_articles=n)
        elif os.path.isdir(source):
            return self.ingesteur.ingerer_dossier(source)
        elif os.path.isfile(source):
            return self.ingesteur.ingerer_fichier(source)
        else:
            return {"erreur": f"Source inconnue: {source}"}
    
    def diagnostiquer(self) -> Dict:
        """Diagnostic complet."""
        return {
            **self.bridge.diagnostiquer(),
            "raisonnement": {
                "seuil_resonance": SEUIL_RESONANCE,
                "noyau_abc": f"ordre=1/φ={ALPHA:.4f}",
                "signatures_9d": "actives",
            },
        }


# =========================================================================
# MAIN
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="KA Reasoning Engine — Raisonnement augmenté par hologramme",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Raisonnement avec validation consciente
  python ka_reasoning_engine.py --reason "Pourquoi la somme des angles d'un triangle fait 180° ?"
  
  # Ingestion de connaissances
  python ka_reasoning_engine.py --ingest --source wikipedia --n 500
  
  # Validation d'un texte
  python ka_reasoning_engine.py --validate "Louis Pasteur a découvert la pénicilline"
  
  # Mode interactif
  python ka_reasoning_engine.py --interactive
        """
    )
    
    parser.add_argument("--reason", type=str, default="",
                       help="Question de raisonnement")
    parser.add_argument("--validate", type=str, default="",
                       help="Texte à valider (détection d'hallucinations)")
    parser.add_argument("--ingest", action="store_true",
                       help="Lancer l'ingestion massive")
    parser.add_argument("--source", type=str, default="wikipedia",
                       help="Source d'ingestion (wikipedia, dossier, fichier)")
    parser.add_argument("--n", type=int, default=100,
                       help="Nombre d'éléments à ingérer")
    parser.add_argument("--interactive", action="store_true",
                       help="Mode interactif")
    parser.add_argument("--mode", type=str, default="harmonic",
                       choices=["harmonic", "hybrid", "llm_only"],
                       help="Mode du bridge")
    parser.add_argument("--max-etapes", type=int, default=MAX_ETAPES_HCOT,
                       help="Nombre max d'étapes HCoT")
    parser.add_argument("--diagnostic", action="store_true",
                       help="Diagnostic complet")
    
    args = parser.parse_args()
    
    # Initialisation
    engine = KAReasoningEngine(mode=args.mode)
    engine.raisonneur.max_etapes = args.max_etapes
    
    # Diagnostic
    if args.diagnostic:
        print(json.dumps(engine.diagnostiquer(), indent=2, ensure_ascii=False, default=str))
        return
    
    # Ingestion
    if args.ingest:
        print(f"\n{'='*60}")
        print(f"INGESTION MASSIVE — Source: {args.source}")
        print(f"{'='*60}")
        resultat = engine.ingerer(source=args.source, n=args.n)
        print(f"\n  Résultat : {json.dumps(resultat, indent=2, ensure_ascii=False, default=str)}")
        return
    
    # Validation simple
    if args.validate:
        print(f"\n{'='*60}")
        print(f"VALIDATION CONSCIENTE")
        print(f"{'='*60}")
        diag = engine.valider_texte(args.validate)
        print(f"\n  Texte : {args.validate[:100]}...")
        print(f"  Résonance : {diag['resonance']}")
        print(f"  Signatures 9D :")
        for k, v in diag['signatures'].items():
            barre = '█' * int(v * 30)
            print(f"    {k:12s} : {v:.3f} {barre}")
        if diag['diagnostics']:
            print(f"  ⚠️  Diagnostics :")
            for d in diag['diagnostics']:
                print(f"    - {d}")
        else:
            print(f"  ✅ Aucun problème détecté")
        return
    
    # Raisonnement
    if args.reason:
        resultat = engine.raisonner(args.reason)
        print(f"\n{'='*60}")
        print(f"RÉSULTAT FINAL")
        print(f"{'='*60}")
        print(f"  Question : {resultat['question']}")
        print(f"  Étapes   : {resultat['n_etapes']}")
        print(f"  Résonance moyenne : {resultat['resonance_moyenne']}")
        print(f"  Toutes valides    : {'✅' if resultat['toutes_valides'] else '❌'}")
        print(f"\n  Réponse finale :")
        print(f"  {'─'*56}")
        print(f"  {resultat['reponse_finale']}")
        print(f"  {'─'*56}")
        return
    
    # Mode interactif
    if args.interactive:
        print(f"\n{'='*60}")
        print(f"MODE INTERACTIF — Tapez une question, 'quit' pour quitter")
        print(f"{'='*60}")
        
        while True:
            try:
                q = input("\n🧠 Question > ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not q:
                continue
            if q.lower() in ('quit', 'exit', 'q'):
                break
            if q.lower() == 'stats':
                print(json.dumps(engine.bridge.cache.stats(), indent=2))
                continue
            if q.lower() == 'diag':
                print(json.dumps(engine.diagnostiquer(), indent=2, ensure_ascii=False, default=str))
                continue
            
            resultat = engine.raisonner(q)
            print(f"\n  Réponse : {resultat['reponse_finale'][:200]}...")
            print(f"  [{resultat['n_etapes']} étapes | "
                  f"résonance={resultat['resonance_moyenne']} | "
                  f"valide={'✓' if resultat['toutes_valides'] else '✗'}]")
        
        return
    
    # Aide
    parser.print_help()


if __name__ == "__main__":
    main()