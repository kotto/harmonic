"""
Moteur Hybride Harmonique : Embedding Fixe + BERT
==================================================
Systeme a deux vitages dans le meme espace de signatures 9D :

1. ROUTAGE RAPIDE (embedding fixe, O(n), 0 GPU)
   - Detection d'anomalie en temps reel
   - Filtrage des cas triviaux
   - Pre-classification grossiere

2. ANALYSE PROFONDE (BERT, O(n²), GPU)
   - Classification fine
   - Analyse semantique
   - Verification des cas limites

Architecture :
  Entree -> [Routeur Rapide] -> Cas simple -> Sortie immediate
                              -> Cas complexe -> [BERT] -> Sortie precise
"""

import os
os.environ['HF_HOME'] = 'C:\\Users\\maatc\\hf_cache'
os.environ['XDG_CACHE_HOME'] = 'C:\\Users\\maatc\\hf_cache'
os.environ['TRANSFORMERS_CACHE'] = 'C:\\Users\\maatc\\hf_cache\\transformers'
os.environ['HUGGINGFACE_HUB_CACHE'] = 'C:\\Users\\maatc\\hf_cache\\hub'

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
import time
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from model.harmonic_pure_signatures_v4 import PureSignatureProjectionV4
from model.harmonic_pure_model import HarmonicFixedEmbedding


# =========================================================================
# MOTEUR EMBEDDING FIXE (Rapide, 0 GPU)
# =========================================================================

class EmbeddingFixeEngine:
    """Moteur rapide base sur l'embedding harmonique fixe."""
    
    def __init__(self, vocab_size=2000, hidden_size=512):
        self.proj = PureSignatureProjectionV4()
        self.embed = HarmonicFixedEmbedding(vocab_size=vocab_size, hidden_size=hidden_size)
        self.vocab = {'<PAD>': 0, '<UNK>': 1}
        self.next_id = 2
        self._cache = {}  # Cache des signatures deja calculees
    
    def _tokenize(self, text):
        return text.lower().split()
    
    def _ensure_vocab(self, tokens):
        for t in tokens:
            if t not in self.vocab and self.next_id < 1998:
                self.vocab[t] = self.next_id
                self.next_id += 1
    
    def compute_signature(self, text):
        """Calcule la signature 9D en O(n)."""
        # Cache
        if text in self._cache:
            return self._cache[text]
        
        tokens = self._tokenize(text)
        if not tokens:
            return np.zeros(9)
        
        self._ensure_vocab(tokens)
        
        input_ids = torch.zeros(1, len(tokens), dtype=torch.long)
        for j, t in enumerate(tokens):
            input_ids[0, j] = self.vocab.get(t, self.vocab['<UNK>'])
        
        with torch.no_grad():
            hidden = self.embed(input_ids)
            sigs = self.proj(hidden)
            sigs = sigs.mean(dim=1)
        
        result = sigs[0].numpy()
        self._cache[text] = result
        return result
    
    def compute_signatures_batch(self, texts):
        return np.array([self.compute_signature(t) for t in texts])


# =========================================================================
# MOTEUR BERT (Precis, GPU)
# =========================================================================

class BertEngine:
    """Moteur precis base sur BERT."""
    
    def __init__(self, model_name='bert-base-uncased', device='cpu'):
        self.device = device
        from transformers import AutoTokenizer, AutoModel
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(device).eval()
        self.proj = PureSignatureProjectionV4()
        self._cache = {}
    
    def compute_signature(self, text, max_length=128):
        if text in self._cache:
            return self._cache[text]
        
        inputs = self.tokenizer(text, return_tensors='pt',
                               truncation=True, max_length=max_length,
                               padding='max_length').to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            hidden_states = outputs.hidden_states[-4:]
            combined = torch.stack(hidden_states).mean(dim=0)
            sigs = self.proj(combined)
            sigs = sigs.mean(dim=1)
        
        result = sigs[0].cpu().numpy()
        self._cache[text] = result
        return result
    
    def compute_signatures_batch(self, texts, max_length=128):
        return np.array([self.compute_signature(t, max_length) for t in texts])


# =========================================================================
# ROUTEUR INTELLIGENT
# =========================================================================

class RouteurHarmonique:
    """
    Routeur intelligent a deux vitages.
    
    Principe :
    - Si la signature est "nette" (faible entropie, forte coherence)
      -> routage rapide (embedding fixe)
    - Si la signature est "ambiguë" (forte entropie, faible coherence)
      -> routage profond (BERT)
    
    Metriques de confiance :
    - phi (entropie) : si phi < 0.3, le signal est tres structure -> confiance elevee
    - reasoning (coherence) : si reasoning > 0.8, le signal est coherent -> confiance elevee
    - Score de confiance compose = (1 - phi) * 0.5 + reasoning * 0.5
    """
    
    def __init__(self, seuil_confiance=0.35, seuil_anomalie=0.6, mode='auto'):
        """
        mode: 'auto' -> seuil adaptatif base sur la distribution du batch
              'fixe' -> seuil fixe
              'rapide' -> toujours embedding fixe
              'profond' -> toujours BERT
        """
        self.embed_engine = EmbeddingFixeEngine()
        self.bert_engine = None  # Charge a la demande
        self.seuil_confiance = seuil_confiance
        self.seuil_anomalie = seuil_anomalie
        self.mode = mode
        self.stats = {'rapide': 0, 'profond': 0, 'temps_rapide': 0, 'temps_profond': 0}
        self._batch_sigs = []  # Signatures du batch courant pour normalisation
    
    def _init_bert(self):
        """Initialise BERT a la demande (lazy loading)."""
        if self.bert_engine is None:
            print("[Routeur] Chargement de BERT (premiere utilisation)...")
            self.bert_engine = BertEngine()
            print("[Routeur] BERT charge.")
    
    def _calculer_confiance(self, sig):
        """
        Calcule un score de confiance dans la signature.
        
        Une signature fiable a :
        - phi faible (< 0.3) : signal bien structure
        - reasoning eleve (> 0.7) : coherence interne forte
        - alpha modere (0.2-0.6) : rugosite equilibree
        
        Retourne : score de confiance [0, 1]
        """
        phi = sig[0]
        reasoning = sig[2]
        alpha = sig[1]
        
        # Score de confiance compose
        confiance = (1.0 - phi) * 0.4 + reasoning * 0.4 + (1.0 - abs(alpha - 0.4) * 1.5) * 0.2
        return float(np.clip(confiance, 0, 1))
    
    def _detecter_anomalie(self, sig, reference_sigs):
        """
        Detecte si une signature est anormale par rapport a un ensemble
        de reference. Utilise la distance de Mahalanobis.
        
        Retourne : score d'anomalie [0, 1]
        """
        if len(reference_sigs) < 2:
            return 0.0
        
        mean_sig = np.mean(reference_sigs, axis=0)
        cov = np.cov(np.array(reference_sigs).T) + np.eye(9) * 1e-6
        inv_cov = np.linalg.inv(cov)
        
        diff = sig - mean_sig
        distance = np.sqrt(diff @ inv_cov @ diff)
        
        return float(1.0 / (1.0 + np.exp(-(distance - 2.0))))
    
    def analyser(self, text, reference_sigs=None, force_profond=False):
        """
        Analyse un texte avec routage intelligent.
        
        Args:
            text: texte a analyser
            reference_sigs: signatures de reference pour detection d'anomalie
            force_profond: force l'utilisation de BERT
        
        Returns:
            dict avec resultats
        """
        t0 = time.time()
        
        # Etape 1 : Signature rapide (embedding fixe)
        sig_rapide = self.embed_engine.compute_signature(text)
        confiance = self._calculer_confiance(sig_rapide)
        
        # Etape 2 : Decision de routage
        utiliser_bert = force_profond or confiance < self.seuil_confiance
        
        if utiliser_bert:
            self._init_bert()
            sig_finale = self.bert_engine.compute_signature(text)
            self.stats['profond'] += 1
            self.stats['temps_profond'] += time.time() - t0
            moteur = "BERT"
        else:
            sig_finale = sig_rapide
            self.stats['rapide'] += 1
            self.stats['temps_rapide'] += time.time() - t0
            moteur = "EMBEDDING_FIXE"
        
        # Etape 3 : Detection d'anomalie (si reference fournie)
        anomalie = None
        if reference_sigs is not None:
            anomalie = self._detecter_anomalie(sig_finale, reference_sigs)
        
        return {
            'texte': text[:60] + '...' if len(text) > 60 else text,
            'signature': {d: float(sig_finale[j]) for j, d in enumerate(
                ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'])},
            'confiance': confiance,
            'moteur': moteur,
            'anomalie_score': anomalie,
            'temps': time.time() - t0
        }
    
    def analyser_batch(self, texts, reference_sigs=None, force_profond=False):
        """Analyse un batch de textes avec routage."""
        return [self.analyser(t, reference_sigs, force_profond) for t in texts]
    
    def afficher_stats(self):
        """Affiche les statistiques de routage."""
        total = self.stats['rapide'] + self.stats['profond']
        if total == 0:
            return
        
        print(f"\n  Statistiques de routage :")
        print(f"  Total analyses : {total}")
        print(f"  Routage rapide  : {self.stats['rapide']} ({self.stats['rapide']/total*100:.1f}%)")
        print(f"  Routage profond : {self.stats['profond']} ({self.stats['profond']/total*100:.1f}%)")
        
        if self.stats['rapide'] > 0:
            print(f"  Temps moyen rapide : {self.stats['temps_rapide']/self.stats['rapide']*1000:.1f}ms")
        if self.stats['profond'] > 0:
            print(f"  Temps moyen profond: {self.stats['temps_profond']/self.stats['profond']*1000:.1f}ms")


# =========================================================================
# APPLICATIONS HYBRIDES
# =========================================================================

class ApplicationHybride:
    """
    Classe de base pour les applications hybrides.
    Utilise le routeur pour chaque analyse.
    """
    
    def __init__(self, seuil_confiance=0.65):
        self.routeur = RouteurHarmonique(seuil_confiance=seuil_confiance)
    
    def _extraire_signatures(self, texts):
        """Extrait les signatures via le routeur."""
        results = self.routeur.analyser_batch(texts)
        sigs = np.array([r['signature'] for r in results])
        return sigs, results


class FinanceHybride(ApplicationHybride):
    """Finance avec routage intelligent."""
    
    def detect_fraud(self, transactions):
        descriptions = [t['description'] for t in transactions]
        sigs, _ = self._extraire_signatures(descriptions)
        
        mean_sig = sigs.mean(axis=0)
        cov = np.cov(sigs.T) + np.eye(9) * 1e-6
        inv_cov = np.linalg.inv(cov)
        
        results = []
        for i, t in enumerate(transactions):
            diff = sigs[i] - mean_sig
            distance = np.sqrt(diff @ inv_cov @ diff)
            fraud_score = 1.0 / (1.0 + np.exp(-(distance - 2.0)))
            
            results.append({
                'description': t['description'],
                'montant': t['montant'],
                'fraud_score': float(fraud_score),
                'flag': 'FRAUDE' if fraud_score > 0.7 else 'SUSPECT' if fraud_score > 0.4 else 'NORMAL'
            })
        return results


class SanteHybride(ApplicationHybride):
    """Sante avec routage intelligent."""
    
    def classify_symptoms(self, symptom_descriptions, known_classes=None):
        sigs, _ = self._extraire_signatures(symptom_descriptions)
        
        if known_classes:
            class_sigs = {}
            for cls, examples in known_classes.items():
                class_sigs[cls] = self._extraire_signatures(examples)[0].mean(axis=0)
            
            results = []
            for i, desc in enumerate(symptom_descriptions):
                distances = {cls: np.linalg.norm(sigs[i] - ref_sig)
                           for cls, ref_sig in class_sigs.items()}
                best_class = min(distances, key=distances.get)
                confidence = 1.0 / (1.0 + distances[best_class])
                
                results.append({
                    'symptome': desc[:60] + '...' if len(desc) > 60 else desc,
                    'classification': best_class,
                    'confidence': float(confidence)
                })
            return results
        return []


class IndustrieHybride(ApplicationHybride):
    """Industrie avec routage intelligent."""
    
    def diagnose_failures(self, failure_descriptions, known_failures=None):
        sigs, _ = self._extraire_signatures(failure_descriptions)
        
        if known_failures:
            failure_sigs = {}
            for ftype, examples in known_failures.items():
                failure_sigs[ftype] = self._extraire_signatures(examples)[0].mean(axis=0)
            
            results = []
            for i, desc in enumerate(failure_descriptions):
                resonances = {}
                for ftype, ref_sig in failure_sigs.items():
                    cos_sim = np.dot(sigs[i], ref_sig) / (np.linalg.norm(sigs[i]) * np.linalg.norm(ref_sig) + 1e-8)
                    resonances[ftype] = float(max(0, cos_sim))
                
                best_match = max(resonances, key=resonances.get)
                results.append({
                    'description': desc[:60] + '...' if len(desc) > 60 else desc,
                    'diagnostic': best_match,
                    'confidence': resonances[best_match]
                })
            return results
        return []


class CreationHybride(ApplicationHybride):
    """Creation avec routage intelligent."""
    
    def analyze_style(self, texts, authors=None):
        sigs, _ = self._extraire_signatures(texts)
        
        results = []
        for i, text in enumerate(texts):
            author = authors[i] if authors else f"Texte_{i}"
            
            creativity = float(sigs[i][3])
            reasoning = float(sigs[i][2])
            emotion = float(sigs[i][7])
            alpha = float(sigs[i][1])
            factual = float(sigs[i][5])
            
            if creativity > 0.15 and emotion > 0.6:
                style = "POETIQUE"
            elif reasoning > 0.8 and factual > 0.8:
                style = "TECHNIQUE"
            elif emotion > 0.6 and temporal > 0.3:
                style = "NARRATIF"
            elif alpha > 0.4:
                style = "COMPLEXE"
            else:
                style = "NEUTRE"
            
            results.append({
                'auteur': author,
                'style': style,
                'metrics': {
                    'creativity_score': creativity,
                    'reasoning_score': reasoning,
                    'emotion_score': float(sigs[i][7]),
                    'complexity_score': alpha,
                    'factual_score': factual
                }
            })
        return results


# =========================================================================
# DEMONSTRATION HYBRIDE
# =========================================================================

def demo_hybride():
    """Demonstration du systeme hybride."""
    
    print("=" * 70)
    print("MOTEUR HYBRIDE HARMONIQUE : EMBEDDING FIXE + BERT")
    print("=" * 70)
    print("""
  Principe :
  - Routage rapide (embedding fixe) pour les cas clairs
  - Routage profond (BERT) pour les cas ambigus
  - Meme espace de signatures 9D pour les deux
  
  Seuil de confiance : 0.65
  - Si confiance > 0.65 : routage rapide (O(n), 0 GPU)
  - Si confiance < 0.65 : routage profond (BERT, GPU)
    """)
    
    # =====================================================================
    # TEST 1 : Textes avec confiance variable
    # =====================================================================
    print("-" * 70)
    print("TEST 1 : Analyse de confiance des signatures")
    print("-" * 70)
    
    routeur = RouteurHarmonique(seuil_confiance=0.65)
    
    textes_test = [
        "2 + 2 = 4",  # Tres structure -> confiance elevee
        "Le soleil couchant embrase l'horizon",  # Structure normale
        "INJECTER 10ML SOLUTION MYSTERE INTRAVEINEUSE SANS ETIQUETTE",  # Anormal
        "Je pense donc je suis",  # Court mais philosophique
        "TRANSFERT URGENT 50000$ VERS COMPTE INCONNU PANAMA",  # Suspect
        "La theorie de la relativite d'Einstein a revolutionne la physique moderne",  # Long, complexe
    ]
    
    print(f"\n  {'Texte':<55} {'Confiance':<10} {'Moteur':<18}")
    print(f"  {'-'*55} {'-'*10} {'-'*18}")
    
    for texte in textes_test:
        result = routeur.analyser(texte)
        desc = result['texte'][:52] + '..' if len(result['texte']) > 52 else result['texte']
        print(f"  {desc:<55} {result['confiance']:<10.3f} {result['moteur']:<18}")
    
    routeur.afficher_stats()
    
    # =====================================================================
    # TEST 2 : Detection de fraude hybride
    # =====================================================================
    print("\n" + "-" * 70)
    print("TEST 2 : Detection de fraude hybride")
    print("-" * 70)
    
    finance = FinanceHybride()
    
    transactions = [
        {'description': 'Achat de 100 actions Apple a 150$', 'montant': 15000},
        {'description': 'Virement de 5000 euros vers compte epargne', 'montant': 5000},
        {'description': 'Paiement loyer mensuel 1200 euros', 'montant': 1200},
        {'description': 'TRANSFERT URGENT 50000$ VERS COMPTE INCONNU PANAMA', 'montant': 50000},
        {'description': 'Achat supermarche 85 euros', 'montant': 85},
        {'description': 'VIREMENT MASSIF FONDS NON JUSTIFIE ORIGINE DOUTEUSE', 'montant': 250000},
        {'description': 'Abonnement Netflix 15.99 euros', 'montant': 15.99},
        {'description': 'Remboursement pret personnel 350 euros', 'montant': 350},
    ]
    
    fraud_results = finance.detect_fraud(transactions)
    
    print(f"\n  {'Description':<50} {'Montant':<10} {'Score':<8} {'Statut':<12}")
    print(f"  {'-'*50} {'-'*10} {'-'*8} {'-'*12}")
    
    for r in fraud_results:
        desc = r['description'][:47] + '..' if len(r['description']) > 47 else r['description']
        print(f"  {desc:<50} {r['montant']:<10.2f} {r['fraud_score']:<8.3f} {r['flag']:<12}")
    
    finance.routeur.afficher_stats()
    
    # =====================================================================
    # TEST 3 : Classification de symptomes hybride
    # =====================================================================
    print("\n" + "-" * 70)
    print("TEST 3 : Classification de symptomes hybride")
    print("-" * 70)
    
    sante = SanteHybride()
    
    symptomes = [
        "Fievre elevee superieure a 38.5 degres depuis 3 jours",
        "Toux seche persistante et difficultes respiratoires",
        "Douleur thoracique intense irradiant dans le bras gauche",
        "Maux de tete violents avec sensibilite a la lumiere",
        "Douleur abdominale basse avec nausees et vomissements",
        "Eruption cutanee rouge avec demangeaisons intenses",
    ]
    
    classes_connues = {
        'RESPIRATOIRE': [
            "Toux grasse avec fievre moderee",
            "Essoufflement apres effort leger",
            "Congestion nasale et mal de gorge"
        ],
        'CARDIAQUE': [
            "Douleur a la poitrine apres effort",
            "Palpitations et essoufflement",
            "Douleur dans le bras gauche"
        ],
        'DIGESTIF': [
            "Douleur au ventre apres les repas",
            "Nausees et diarrhee depuis 2 jours",
            "Brulures d'estomac persistantes"
        ]
    }
    
    classifications = sante.classify_symptoms(symptomes, classes_connues)
    
    print(f"\n  {'Symptome':<50} {'Classification':<15} {'Confiance':<10}")
    print(f"  {'-'*50} {'-'*15} {'-'*10}")
    
    for c in classifications:
        symp = c['symptome'][:47] + '..' if len(c['symptome']) > 47 else c['symptome']
        print(f"  {symp:<50} {c['classification']:<15} {c['confidence']:<10.3f}")
    
    sante.routeur.afficher_stats()
    
    # =====================================================================
    # TEST 4 : Analyse de style hybride
    # =====================================================================
    print("\n" + "-" * 70)
    print("TEST 4 : Analyse de style hybride")
    print("-" * 70)
    
    creation = CreationHybride()
    
    textes = [
        "Le soleil couchant embrase l'horizon de ses derniers feux pourpres",
        "La fonction f(x) = x^2 + 2x + 1 est une parabole convexe",
        "Il etait une fois dans un royaume lointain un dragon qui pleurait des perles",
        "Le chiffre d'affaires du troisieme trimestre a augmente de 15%",
        "Mon coeur vacille comme une feuille au vent d'automne",
        "Si condition alors execution sinon alternative par defaut",
    ]
    
    auteurs = ["Poete", "Mathematicien", "Conteur", "Analyste", "Romantique", "Informaticien"]
    
    styles = creation.analyze_style(textes, auteurs)
    
    print(f"\n  {'Auteur':<15} {'Style':<12} {'Creativite':<12} {'Raisonnement':<12} {'Emotion':<10}")
    print(f"  {'-'*15} {'-'*12} {'-'*12} {'-'*12} {'-'*10}")
    
    for s in styles:
        print(f"  {s['auteur']:<15} {s['style']:<12} {s['metrics']['creativity_score']:<12.3f} {s['metrics']['reasoning_score']:<12.3f} {s['metrics']['emotion_score']:<10.3f}")
    
    creation.routeur.afficher_stats()
    
    # =====================================================================
    # BILAN
    # =====================================================================
    print("\n" + "=" * 70)
    print("BILAN DU SYSTEME HYBRIDE")
    print("=" * 70)
    
    total_rapide = sum(app.routeur.stats['rapide'] for app in [finance, sante, creation])
    total_profond = sum(app.routeur.stats['profond'] for app in [finance, sante, creation])
    total = total_rapide + total_profond
    
    print(f"""
  Analyses totales : {total}
  Routage rapide    : {total_rapide} ({total_rapide/total*100:.1f}%) - Embedding fixe
  Routage profond   : {total_profond} ({total_profond/total*100:.1f}%) - BERT
  
  Gain de performance theorique :
  - Embedding fixe : ~1ms par analyse
  - BERT           : ~100ms par analyse
  - Gain moyen     : {total_profond/total*100:.0f}% des analyses en BERT
                     soit {100 - total_profond/total*100:.0f}% plus rapide
                     que du BERT pur
  
  Architecture :
  ┌─────────┐    ┌──────────────┐    ┌──────────┐
  │ Entree  │ -> │ Routeur 9D   │ -> │ Rapide   │ -> Sortie
  │ Texte   │    │ Confiance    │    │ (Fixe)   │
  └─────────┘    │ < seuil ?    │    └──────────┘
                 │              │    ┌──────────┐
                 │     Non ->   │ -> │ Profond  │ -> Sortie
                 └──────────────┘    │ (BERT)   │
                                     └──────────┘
  
  Avantages :
  - 0 cout pour les cas clairs (embedding fixe)
  - Precision BERT pour les cas ambigus
  - Meme espace de signatures 9D pour les deux
  - Cache integre pour eviter les recalculs
  - Lazy loading de BERT (charge a la demande)
    """)


if __name__ == '__main__':
    demo_hybride()
