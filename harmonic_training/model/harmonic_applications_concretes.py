"""
Applications Concretes des Signatures Harmoniques 9D
=====================================================
Classification, clustering et optimisation dans 4 domaines :
1. FINANCE  : Detection de fraude, analyse de sentiment de marche
2. SANTE    : Classification de symptomes, analyse de prescriptions
3. INDUSTRIE: Diagnostic de pannes, optimisation de maintenance
4. CREATION : Analyse de style, detection de plagiat, recommandation

Chaque application utilise les signatures 9D (phi, alpha, reasoning,
creativity, math, factual, code, emotion, temporal) comme descripteurs
universels, sans entrainement.
"""

import os
os.environ['HF_HOME'] = 'E:\\hf_cache'
os.environ['XDG_CACHE_HOME'] = 'E:\\hf_cache'

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import cdist
from model.harmonic_pure_signatures_v4 import PureSignatureProjectionV4
from model.harmonic_pure_model import HarmonicFixedEmbedding


# =========================================================================
# MOTEUR DE SIGNATURES 9D (sans BERT pour rapidite)
# =========================================================================

class SignatureEngine9D:
    """
    Moteur universel de signatures 9D.
    Utilise l'embedding harmonique fixe pour un calcul rapide.
    """
    
    def __init__(self, vocab_size=2000, hidden_size=512):
        self.proj = PureSignatureProjectionV4()
        self.embed = HarmonicFixedEmbedding(vocab_size=vocab_size, hidden_size=hidden_size)
        self.vocab = {'<PAD>': 0, '<UNK>': 1}
        self.next_id = 2
    
    def _tokenize(self, text):
        """Tokenisation simple mot par mot."""
        return text.lower().split()
    
    def _ensure_vocab(self, tokens):
        """Ajoute les tokens inconnus au vocabulaire."""
        for t in tokens:
            if t not in self.vocab and self.next_id < 1998:
                self.vocab[t] = self.next_id
                self.next_id += 1
    
    def compute_signature(self, text):
        """
        Calcule la signature 9D d'un texte.
        Retourne un array numpy de forme (9,).
        """
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
        
        return sigs[0].numpy()
    
    def compute_signatures_batch(self, texts):
        """Calcule les signatures 9D pour une liste de textes."""
        return np.array([self.compute_signature(t) for t in texts])


# =========================================================================
# 1. FINANCE : Detection de Fraude et Analyse de Marche
# =========================================================================

class FinanceHarmonicAnalyzer:
    """
    Analyse financiere par signatures harmoniques 9D.
    
    Applications :
    - Detection de fraude : les transactions frauduleuses ont des
      signatures anormales (alpha eleve, reasoning faible)
    - Sentiment de marche : les news positives vs negatives ont
      des profils emotion/temporal distincts
    - Clustering de secteurs : les entreprises d'un meme secteur
      partagent des signatures similaires
    """
    
    def __init__(self):
        self.engine = SignatureEngine9D()
        self.name = "Finance"
    
    def detect_fraud(self, transactions):
        """
        Detecte les transactions frauduleuses par anomalie de signature.
        
        Args:
            transactions: liste de dicts {'description': str, 'montant': float}
        
        Returns:
            liste de dicts avec score de fraude (0-1)
        """
        descriptions = [t['description'] for t in transactions]
        sigs = self.engine.compute_signatures_batch(descriptions)
        
        # Signature moyenne (profil normal)
        mean_sig = sigs.mean(axis=0)
        
        # Distance de Mahalanobis simplifiee
        cov = np.cov(sigs.T) + np.eye(9) * 1e-6
        inv_cov = np.linalg.inv(cov)
        
        results = []
        for i, t in enumerate(transactions):
            diff = sigs[i] - mean_sig
            distance = np.sqrt(diff @ inv_cov @ diff)
            
            # Normalisation en score de fraude [0, 1]
            fraud_score = 1.0 / (1.0 + np.exp(-(distance - 2.0)))
            
            # Analyse du profil de signature
            profile = self._make_profile(sigs[i])
            
            results.append({
                'description': t['description'],
                'montant': t['montant'],
                'fraud_score': float(fraud_score),
                'anomaly_distance': float(distance),
                'signature': profile,
                'flag': 'FRAUDE' if fraud_score > 0.7 else 'SUSPECT' if fraud_score > 0.4 else 'NORMAL'
            })
        
        return results
    
    def _make_profile(self, sig):
        return {
            'phi': float(sig[0]), 'alpha': float(sig[1]),
            'reasoning': float(sig[2]), 'creativity': float(sig[3]),
            'math': float(sig[4]), 'factual': float(sig[5]),
            'code': float(sig[6]), 'emotion': float(sig[7]),
            'temporal': float(sig[8])
        }
    
    def analyze_market_sentiment(self, news_articles):
        """
        Analyse le sentiment de marche a partir d'articles.
        
        Args:
            news_articles: liste de textes
        
        Returns:
            dict avec scores de sentiment par article
        """
        sigs = self.engine.compute_signatures_batch(news_articles)
        
        sentiment_scores = []
        for i, article in enumerate(news_articles):
            emotion = sigs[i][7]
            temporal = sigs[i][8]
            alpha = sigs[i][1]
            reasoning = sigs[i][2]
            
            sentiment = (emotion * 0.4 + temporal * 0.3 - alpha * 0.2 + reasoning * 0.1)
            sentiment = float(np.clip(sentiment, 0, 1))
            
            if sentiment > 0.6:
                label = "POSITIF"
            elif sentiment > 0.4:
                label = "NEUTRE"
            else:
                label = "NEGATIF"
            
            sentiment_scores.append({
                'article': article[:80] + '...' if len(article) > 80 else article,
                'sentiment_score': sentiment,
                'label': label,
                'emotion': float(sigs[i][7]),
                'temporal': float(sigs[i][8]),
                'alpha': float(sigs[i][1])
            })
        
        scores = [s['sentiment_score'] for s in sentiment_scores]
        
        return {
            'articles': sentiment_scores,
            'global_sentiment': float(np.mean(scores)),
            'volatility': float(np.std(scores)),
            'positif_pct': sum(1 for s in sentiment_scores if s['label'] == 'POSITIF') / len(sentiment_scores) * 100,
            'negatif_pct': sum(1 for s in sentiment_scores if s['label'] == 'NEGATIF') / len(sentiment_scores) * 100,
            'neutre_pct': sum(1 for s in sentiment_scores if s['label'] == 'NEUTRE') / len(sentiment_scores) * 100
        }


# =========================================================================
# 2. SANTE : Classification de Symptomes et Prescriptions
# =========================================================================

class SanteHarmonicAnalyzer:
    """
    Analyse medicale par signatures harmoniques 9D.
    """
    
    def __init__(self):
        self.engine = SignatureEngine9D()
        self.name = "Sante"
    
    def classify_symptoms(self, symptom_descriptions, known_classes=None):
        """Classifie des descriptions de symptomes."""
        sigs = self.engine.compute_signatures_batch(symptom_descriptions)
        
        if known_classes:
            class_sigs = {}
            for cls, examples in known_classes.items():
                class_sigs[cls] = self.engine.compute_signatures_batch(examples).mean(axis=0)
            
            results = []
            for i, desc in enumerate(symptom_descriptions):
                distances = {cls: np.linalg.norm(sigs[i] - ref_sig)
                           for cls, ref_sig in class_sigs.items()}
                best_class = min(distances, key=distances.get)
                confidence = 1.0 / (1.0 + distances[best_class])
                
                results.append({
                    'symptome': desc[:60] + '...' if len(desc) > 60 else desc,
                    'classification': best_class,
                    'confidence': float(confidence),
                    'distances': {k: float(v) for k, v in distances.items()},
                    'signature': self._make_profile(sigs[i])
                })
            return results
        else:
            n_clusters = min(3, len(symptom_descriptions))
            if n_clusters < 2:
                return [{'symptome': d, 'cluster': 0} for d in symptom_descriptions]
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(sigs)
            sil_score = silhouette_score(sigs, clusters)
            
            results = []
            for i, desc in enumerate(symptom_descriptions):
                results.append({
                    'symptome': desc[:60] + '...' if len(desc) > 60 else desc,
                    'cluster': int(clusters[i]),
                    'signature': self._make_profile(sigs[i])
                })
            
            return {'clusters': results, 'silhouette_score': float(sil_score), 'n_clusters': n_clusters}
    
    def _make_profile(self, sig):
        return {d: float(sig[j]) for j, d in enumerate(
            ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'])}
    
    def analyze_prescription_coherence(self, prescriptions):
        """Analyse la coherence de prescriptions medicales."""
        sigs = self.engine.compute_signatures_batch(prescriptions)
        
        results = []
        for i, presc in enumerate(prescriptions):
            factual = sigs[i][5]
            reasoning = sigs[i][2]
            alpha = sigs[i][1]
            creativity = sigs[i][3]
            
            coherence = (factual * 0.35 + reasoning * 0.35 + 
                        (1 - alpha) * 0.15 + (1 - creativity) * 0.15)
            coherence = float(np.clip(coherence, 0, 1))
            
            results.append({
                'prescription': presc[:60] + '...' if len(presc) > 60 else presc,
                'coherence_score': coherence,
                'factual': float(factual),
                'reasoning': float(reasoning),
                'alpha': float(alpha),
                'creativity': float(creativity),
                'flag': 'COHERENT' if coherence > 0.6 else 'A_VERIFIER' if coherence > 0.4 else 'ANORMAL'
            })
        
        return results


# =========================================================================
# 3. INDUSTRIE : Diagnostic de Pannes et Maintenance
# =========================================================================

class IndustrieHarmonicAnalyzer:
    """
    Analyse industrielle par signatures harmoniques 9D.
    """
    
    def __init__(self):
        self.engine = SignatureEngine9D()
        self.name = "Industrie"
    
    def _make_profile(self, sig):
        return {d: float(sig[j]) for j, d in enumerate(
            ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'])}
    
    def diagnose_failures(self, failure_descriptions, known_failures=None):
        """Diagnostique des pannes industrielles."""
        sigs = self.engine.compute_signatures_batch(failure_descriptions)
        
        if known_failures:
            failure_sigs = {}
            for ftype, examples in known_failures.items():
                failure_sigs[ftype] = self.engine.compute_signatures_batch(examples).mean(axis=0)
            
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
                    'confidence': resonances[best_match],
                    'resonances': resonances,
                    'signature': self._make_profile(sigs[i])
                })
            return results
        else:
            mean_sig = sigs.mean(axis=0)
            std_sig = sigs.std(axis=0) + 1e-6
            
            results = []
            for i, desc in enumerate(failure_descriptions):
                z_scores = np.abs((sigs[i] - mean_sig) / std_sig)
                anomaly_score = float(np.mean(z_scores) / 3.0)
                anomaly_score = min(1.0, anomaly_score)
                
                dominant_dim = ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'][
                    np.argmax(z_scores)]
                
                results.append({
                    'description': desc[:60] + '...' if len(desc) > 60 else desc,
                    'anomaly_score': anomaly_score,
                    'dominant_dimension': dominant_dim,
                    'z_scores': {d: float(z_scores[j]) for j, d in enumerate(
                        ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'])}
                })
            return results
    
    def optimize_maintenance(self, maintenance_logs):
        """Optimise la maintenance par clustering des signatures."""
        sigs = self.engine.compute_signatures_batch(maintenance_logs)
        
        n_clusters = min(4, len(maintenance_logs))
        if n_clusters < 2:
            return [{'log': l, 'group': 0} for l in maintenance_logs]
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(sigs)
        
        cluster_profiles = {}
        for c in range(n_clusters):
            mask = clusters == c
            if mask.sum() > 0:
                cluster_profiles[c] = {
                    'size': int(mask.sum()),
                    'mean_signature': {d: float(sigs[mask].mean(axis=0)[j]) 
                                      for j, d in enumerate(
                        ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'])},
                    'priority': 'URGENT' if sigs[mask].mean(axis=0)[1] > 0.5 else 'NORMAL' if sigs[mask].mean(axis=0)[1] > 0.3 else 'PLANIFIE'
                }
        
        results = []
        for i, log in enumerate(maintenance_logs):
            results.append({
                'log': log[:60] + '...' if len(log) > 60 else log,
                'group': int(clusters[i]),
                'profile': cluster_profiles[int(clusters[i])]
            })
        
        return {'logs': results, 'cluster_profiles': cluster_profiles, 'n_clusters': n_clusters}


# =========================================================================
# 4. CREATION : Analyse de Style et Recommandation
# =========================================================================

class CreationHarmonicAnalyzer:
    """
    Analyse creative par signatures harmoniques 9D.
    """
    
    def __init__(self):
        self.engine = SignatureEngine9D()
        self.name = "Creation"
    
    def _make_profile(self, sig):
        return {d: float(sig[j]) for j, d in enumerate(
            ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'])}
    
    def analyze_style(self, texts, authors=None):
        """Analyse le style d'ecriture par signatures 9D."""
        sigs = self.engine.compute_signatures_batch(texts)
        
        results = []
        for i, text in enumerate(texts):
            author = authors[i] if authors else f"Texte_{i}"
            
            creativity = float(sigs[i][3])
            reasoning = float(sigs[i][2])
            emotion = float(sigs[i][7])
            temporal = float(sigs[i][8])
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
                'signature': self._make_profile(sigs[i]),
                'metrics': {
                    'creativity_score': creativity,
                    'reasoning_score': reasoning,
                    'emotion_score': emotion,
                    'temporal_score': temporal,
                    'complexity_score': alpha,
                    'factual_score': factual
                }
            })
        
        return results
    
    def detect_plagiarism(self, original_texts, suspect_texts, threshold=0.85):
        """Detecte le plagiat par similarite de signatures."""
        orig_sigs = self.engine.compute_signatures_batch(original_texts)
        susp_sigs = self.engine.compute_signatures_batch(suspect_texts)
        
        reports = []
        for i, suspect in enumerate(suspect_texts):
            best_match_idx = -1
            best_similarity = 0
            
            for j, original in enumerate(original_texts):
                cos_sim = np.dot(susp_sigs[i], orig_sigs[j]) / (
                    np.linalg.norm(susp_sigs[i]) * np.linalg.norm(orig_sigs[j]) + 1e-8)
                
                if cos_sim > best_similarity:
                    best_similarity = cos_sim
                    best_match_idx = j
            
            is_plagiarism = best_similarity > threshold
            
            reports.append({
                'suspect': suspect[:60] + '...' if len(suspect) > 60 else suspect,
                'best_match': original_texts[best_match_idx][:60] + '...' if best_match_idx >= 0 else 'N/A',
                'similarity': float(best_similarity),
                'is_plagiarism': is_plagiarism,
                'alert': 'PLAGIAT' if is_plagiarism else 'OK',
                'signature_distance': float(np.linalg.norm(susp_sigs[i] - orig_sigs[best_match_idx])) if best_match_idx >= 0 else 999
            })
        
        return reports
    
    def recommend_content(self, query_text, content_library, top_k=3):
        """Recommande du contenu par resonance harmonique."""
        query_sig = self.engine.compute_signature(query_text)
        lib_sigs = self.engine.compute_signatures_batch(content_library)
        
        resonances = []
        for i, content in enumerate(content_library):
            cos_sim = np.dot(query_sig, lib_sigs[i]) / (
                np.linalg.norm(query_sig) * np.linalg.norm(lib_sigs[i]) + 1e-8)
            resonances.append((i, float(cos_sim)))
        
        resonances.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for idx, score in resonances[:top_k]:
            recommendations.append({
                'content': content_library[idx][:80] + '...' if len(content_library[idx]) > 80 else content_library[idx],
                'resonance_score': score,
                'index': idx
            })
        
        return {
            'query': query_text[:60] + '...' if len(query_text) > 60 else query_text,
            'recommendations': recommendations,
            'query_signature': {d: float(query_sig[j]) for j, d in enumerate(
                ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'])}
        }


# =========================================================================
# ANALYSEUR HARMONIQUE UNIFIE
# =========================================================================

class HarmonicApplicationAnalyzer:
    """
    Analyseur harmonique unifie couvrant les 4 domaines.
    
    Usage:
        analyzer = HarmonicApplicationAnalyzer()
        
        # Finance
        fraude = analyzer.finance.detect_fraud(transactions)
        sentiment = analyzer.finance.analyze_market_sentiment(news)
        
        # Sante
        diagnostics = analyzer.sante.classify_symptoms(symptomes)
        coherence = analyzer.sante.analyze_prescription_coherence(presc)
        
        # Industrie
        pannes = analyzer.industrie.diagnose_failures(descriptions)
        maintenance = analyzer.industrie.optimize_maintenance(logs)
        
        # Creation
        styles = analyzer.creation.analyze_style(textes)
        plagiat = analyzer.creation.detect_plagiarism(originaux, suspects)
        recommandations = analyzer.creation.recommend_content(query, library)
    """
    
    def __init__(self):
        """Initialise les 4 analyseurs specialises."""
        self.finance = FinanceHarmonicAnalyzer()
        self.sante = SanteHarmonicAnalyzer()
        self.industrie = IndustrieHarmonicAnalyzer()
        self.creation = CreationHarmonicAnalyzer()
    
    def analyze_text(self, text):
        """
        Analyse un texte avec tous les domaines simultanement.
        
        Args:
            text: Texte a analyser
        
        Returns:
            dict complet avec signatures et analyses
        """
        engine = SignatureEngine9D()
        sig = engine.compute_signature(text)
        
        return {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'signature_9d': {d: float(sig[j]) for j, d in enumerate(
                ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal'])},
            'vector': sig.tolist(),
            'domains': {
                'finance': self._analyze_finance_dimensions(sig),
                'sante': self._analyze_sante_dimensions(sig),
                'industrie': self._analyze_industrie_dimensions(sig),
                'creation': self._analyze_creation_dimensions(sig)
            }
        }
    
    def _analyze_finance_dimensions(self, sig):
        emotion, temporal, alpha, reasoning = sig[7], sig[8], sig[1], sig[2]
        sentiment = float(np.clip(emotion * 0.4 + temporal * 0.3 - alpha * 0.2 + reasoning * 0.1, 0, 1))
        return {
            'sentiment_score': sentiment,
            'label': 'POSITIF' if sentiment > 0.6 else 'NEGATIF' if sentiment < 0.4 else 'NEUTRE',
            'risk_indicator': float(np.clip(alpha * 0.6 + (1 - reasoning) * 0.4, 0, 1))
        }
    
    def _analyze_sante_dimensions(self, sig):
        factual, reasoning, alpha, creativity = sig[5], sig[2], sig[1], sig[3]
        coherence = float(np.clip(factual * 0.35 + reasoning * 0.35 + (1 - alpha) * 0.15 + (1 - creativity) * 0.15, 0, 1))
        return {
            'coherence': coherence,
            'flag': 'COHERENT' if coherence > 0.6 else 'A_VERIFIER' if coherence > 0.4 else 'ANORMAL'
        }
    
    def _analyze_industrie_dimensions(self, sig):
        anomaly = float(np.clip(np.mean(np.abs(sig - np.array([0.5]*9))) / 0.5, 0, 1))
        return {
            'anomaly_score': anomaly,
            'maintenance_priority': 'URGENT' if anomaly > 0.7 else 'NORMAL' if anomaly > 0.4 else 'PLANIFIE'
        }
    
    def _analyze_creation_dimensions(self, sig):
        creativity, emotion, reasoning, factual = sig[3], sig[7], sig[2], sig[5]
        if creativity > 0.15 and emotion > 0.6:
            style = "POETIQUE"
        elif reasoning > 0.8 and factual > 0.8:
            style = "TECHNIQUE"
        elif emotion > 0.6:
            style = "NARRATIF"
        else:
            style = "NEUTRE"
        return {'style': style, 'creativity_score': float(creativity)}
    
    def get_domain_analyzers(self):
        """Retourne la liste des analyseurs disponibles."""
        return {
            'finance': self.finance,
            'sante': self.sante,
            'industrie': self.industrie,
            'creation': self.creation
        }


# =========================================================================
# FONCTION D'ANALYSE RAPIDE
# =========================================================================

def analyze_harmonic_applications(texts=None, domain='all'):
    """
    Fonction d'analyse rapide pour les applications harmoniques.
    
    Args:
        texts: Liste de textes a analyser (utilise des exemples par defaut si None)
        domain: 'finance', 'sante', 'industrie', 'creation', ou 'all'
    
    Returns:
        Resultats d'analyse structures
    """
    analyzer = HarmonicApplicationAnalyzer()
    
    if texts is None:
        texts = [
            "Analyse du marche financier avec tendance haussiere",
            "Le patient presente des symptomes de fievre et toux persistante",
            "Maintenance preventive du moteur electrique principal",
            "Poeme sur la beaute de la nature et des saisons",
        ]
    
    results = {}
    for i, text in enumerate(texts):
        results[f'texte_{i}'] = analyzer.analyze_text(text)
    
    return results


# =========================================================================
# DEMONSTRATION COMPLETE
# =========================================================================

def demo_all_applications():
    """Demonstration des 4 domaines d'application."""
    
    print("=" * 70)
    print("APPLICATIONS CONCRETES DES SIGNATURES HARMONIQUES 9D")
    print("=" * 70)
    
    # =====================================================================
    # 1. FINANCE
    # =====================================================================
    print("\n" + "=" * 70)
    print("[1] FINANCE : Detection de Fraude et Sentiment de Marche")
    print("=" * 70)
    
    finance = FinanceHarmonicAnalyzer()
    
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
    
    print(f"\n  Detection de fraude :")
    print(f"  {'Description':<50} {'Montant':<10} {'Score':<8} {'Statut':<12}")
    print(f"  {'-'*50} {'-'*10} {'-'*8} {'-'*12}")
    
    for r in fraud_results:
        desc = r['description'][:47] + '..' if len(r['description']) > 47 else r['description']
        print(f"  {desc:<50} {r['montant']:<10.2f} {r['fraud_score']:<8.3f} {r['flag']:<12}")
    
    # Sentiment de marche
    news = [
        "Le marche boursier atteint des sommets historiques portes par l'innovation technologique",
        "Crise economique imminente : les analystes previennent d'un krach boursier",
        "Nouveau partenariat strategique entre les deux plus grandes banques europeennes",
        "Les taux d'interet restent stables malais les tensions geopolitiques",
        "Innovation majeure dans le secteur des energies renouvelables",
        "Faillite retentissante d'une entreprise du CAC 40",
    ]
    
    sentiment = finance.analyze_market_sentiment(news)
    
    print(f"\n  Sentiment de marche :")
    print(f"  Global: {sentiment['global_sentiment']:.3f} | Volatilite: {sentiment['volatility']:.3f}")
    print(f"  Positifs: {sentiment['positif_pct']:.0f}% | Negatifs: {sentiment['negatif_pct']:.0f}% | Neutres: {sentiment['neutre_pct']:.0f}%")
    
    for a in sentiment['articles'][:3]:
        print(f"  [{a['label']:<7}] {a['article'][:60]}")
    
    # =====================================================================
    # 2. SANTE
    # =====================================================================
    print("\n" + "=" * 70)
    print("[2] SANTE : Classification de Symptomes et Prescriptions")
    print("=" * 70)
    
    sante = SanteHarmonicAnalyzer()
    
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
    
    print(f"\n  Classification des symptomes :")
    print(f"  {'Symptome':<50} {'Classification':<15} {'Confiance':<10}")
    print(f"  {'-'*50} {'-'*15} {'-'*10}")
    
    for c in classifications:
        symp = c['symptome'][:47] + '..' if len(c['symptome']) > 47 else c['symptome']
        print(f"  {symp:<50} {c['classification']:<15} {c['confidence']:<10.3f}")
    
    # Prescriptions
    prescriptions = [
        "Prendre 2 comprimes de paracetamol 500mg matin et soir pendant 5 jours",
        "Appliquer la creme antibiotique sur la plaie 3 fois par jour",
        "INJECTER 10ML SOLUTION MYSTERE INTRAVEINEUSE SANS ETIQUETTE",
        "Repos strict pendant 48h et hydratation reguliere",
        "Prendre 1 comprime de metformine 850mg avant chaque repas",
    ]
    
    coherence = sante.analyze_prescription_coherence(prescriptions)
    
    print(f"\n  Analyse de coherence des prescriptions :")
    print(f"  {'Prescription':<55} {'Score':<8} {'Statut':<12}")
    print(f"  {'-'*55} {'-'*8} {'-'*12}")
    
    for p in coherence:
        presc = p['prescription'][:52] + '..' if len(p['prescription']) > 52 else p['prescription']
        print(f"  {presc:<55} {p['coherence_score']:<8.3f} {p['flag']:<12}")
    
    # =====================================================================
    # 3. INDUSTRIE
    # =====================================================================
    print("\n" + "=" * 70)
    print("[3] INDUSTRIE : Diagnostic de Pannes et Maintenance")
    print("=" * 70)
    
    industrie = IndustrieHarmonicAnalyzer()
    
    pannes = [
        "Moteur principal emet un bruit de grincement anormal a haute vitesse",
        "Temperature du reacteur depasse le seuil critique de securite",
        "Variation inexpliquee de la pression hydraulique dans le circuit principal",
        "Arret imprevu de la chaine de production ligne 3",
        "Vibrations excessives detectees sur le rotor principal",
        "Defaut d'etancheite sur la vanne de regulation principale",
    ]
    
    pannes_connues = {
        'MECANIQUE': [
            "Bruit de roulement anormal au niveau de l'axe",
            "Vibration excessive du moteur electrique",
            "Jeu anormal dans les roulements"
        ],
        'THERMIQUE': [
            "Surchauffe du systeme de refroidissement",
            "Temperature anormale du fluide caloporteur",
            "Declenchement du thermostat de securite"
        ],
        'HYDRAULIQUE': [
            "Fuite au niveau du joint de verin",
            "Pression insuffisante dans le circuit hydraulique",
            "Baisse de debit de la pompe principale"
        ]
    }
    
    diagnostics = industrie.diagnose_failures(pannes, pannes_connues)
    
    print(f"\n  Diagnostic de pannes :")
    print(f"  {'Description':<50} {'Diagnostic':<15} {'Confiance':<10}")
    print(f"  {'-'*50} {'-'*15} {'-'*10}")
    
    for d in diagnostics:
        desc = d['description'][:47] + '..' if len(d['description']) > 47 else d['description']
        print(f"  {desc:<50} {d['diagnostic']:<15} {d['confidence']:<10.3f}")
    
    # Maintenance
    logs = [
        "Remplacement des filtres a huile effectue apres 500h de fonctionnement",
        "Inspection visuelle du circuit electrique RAS",
        "VIDANGE URGENTE EFFECTUEE SUITE A FUITE HUILE MOTEUR PRINCIPAL",
        "Graissage des roulements de la pompe centrifuge",
        "Calibration des capteurs de temperature zone 4",
        "Remplacement courroie de transmission usee",
    ]
    
    maintenance = industrie.optimize_maintenance(logs)
    
    print(f"\n  Optimisation de maintenance :")
    print(f"  {'Log':<50} {'Groupe':<8} {'Priorite':<10}")
    print(f"  {'-'*50} {'-'*8} {'-'*10}")
    
    for l in maintenance['logs']:
        log = l['log'][:47] + '..' if len(l['log']) > 47 else l['log']
        print(f"  {log:<50} {l['group']:<8} {l['profile']['priority']:<10}")
    
    # =====================================================================
    # 4. CREATION
    # =====================================================================
    print("\n" + "=" * 70)
    print("[4] CREATION : Analyse de Style et Recommandation")
    print("=" * 70)
    
    creation = CreationHarmonicAnalyzer()
    
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
    
    print(f"\n  Analyse de style :")
    print(f"  {'Auteur':<15} {'Style':<12} {'Creativite':<12} {'Raisonnement':<12} {'Emotion':<10}")
    print(f"  {'-'*15} {'-'*12} {'-'*12} {'-'*12} {'-'*10}")
    
    for s in styles:
        print(f"  {s['auteur']:<15} {s['style']:<12} {s['metrics']['creativity_score']:<12.3f} {s['metrics']['reasoning_score']:<12.3f} {s['metrics']['emotion_score']:<10.3f}")
    
    # Detection de plagiat
    originaux = [
        "Le vent souffle sur la plaine et les arbres dansent",
        "La theorie de la relativite d'Einstein a revolutionne la physique",
        "Dans la foret profonde vivait un sage ermite",
    ]
    
    suspects = [
        "La brise agite la prairie et les feuilles valsent",
        "La relativite einsteinienne a transforme notre comprehension de l'univers",
        "Aujourd'hui il fait beau et je vais me promener",
    ]
    
    plagiat = creation.detect_plagiarism(originaux, suspects)
    
    print(f"\n  Detection de plagiat :")
    print(f"  {'Suspect':<50} {'Similarite':<12} {'Alerte':<10}")
    print(f"  {'-'*50} {'-'*12} {'-'*10}")
    
    for p in plagiat:
        print(f"  {p['suspect']:<50} {p['similarity']:<12.3f} {p['alert']:<10}")
    
    # Recommandation de contenu
    bibliotheque = [
        "Les mysteres de l'univers et les trous noirs",
        "Poemes d'amour et de passion eternelle",
        "Guide pratique du developpement web moderne",
        "Recits fantastiques de dragons et de heros legendaires",
        "Analyse financiere des marches boursiers",
        "Traitement du signal et analyse harmonique",
    ]
    
    requetes = [
        "Je cherche des histoires de creatures magiques",
        "J'ai besoin d'informations sur la bourse",
        "Parle-moi d'amour et de sentiments",
    ]
    
    print(f"\n  Recommandation de contenu :")
    for requete in requetes:
        reco = creation.recommend_content(requete, bibliotheque)
        print(f"\n  Requete: {reco['query']}")
        for r in reco['recommendations']:
            print(f"    -> {r['content']} (resonance: {r['resonance_score']:.3f})")
    
    # =====================================================================
    # 5. ANALYSEUR UNIFIE
    # =====================================================================
    print("\n" + "=" * 70)
    print("[5] ANALYSEUR HARMONIQUE UNIFIE (4 domaines simultanes)")
    print("=" * 70)
    
    unified = HarmonicApplicationAnalyzer()
    test_texts = [
        "Lancement d'une OPA sur le groupe industriel europeen",
        "Diagnostic de panne du systeme de refroidissement du reacteur",
    ]
    
    for text in test_texts:
        result = unified.analyze_text(text)
        print(f"\n  Texte: {result['text']}")
        print(f"  Signature: {result['vector'][:4]}...")
        print(f"  Finance: {result['domains']['finance']['label']} (risque={result['domains']['finance']['risk_indicator']:.2f})")
        print(f"  Sante: {result['domains']['sante']['flag']} (coherence={result['domains']['sante']['coherence']:.2f})")
        print(f"  Industrie: priorite {result['domains']['industrie']['maintenance_priority']} (anomalie={result['domains']['industrie']['anomaly_score']:.2f})")
        print(f"  Creation: style {result['domains']['creation']['style']} (creativite={result['domains']['creation']['creativity_score']:.2f})")
    
    # =====================================================================
    # CONCLUSION
    # =====================================================================
    print("\n" + "=" * 70)
    print("CONCLUSION : 4 DOMAINES, 1 MOTEUR, 0 ENTRAINEMENT")
    print("=" * 70)
    print("""
  Les signatures harmoniques 9D permettent de :
  
  FINANCE   : Detection de fraude par anomalie de signature
              Analyse de sentiment de marche en temps reel
  
  SANTE     : Classification de symptomes sans apprentissage
              Detection de prescriptions anormales
  
  INDUSTRIE : Diagnostic de pannes par resonance harmonique
              Optimisation de maintenance par clustering
  
  CREATION  : Analyse de style d'ecriture
              Detection de plagiat par similarite
              Recommandation de contenu par resonance
  
  ANALYSEUR UNIFIE : Les 4 domaines analyses simultanement
  
  Avantages cles :
  - Zero entrainement : les formules sont analytiques
  - Interpretable : chaque dimension a un sens physique
  - Universel : les memes 9 dimensions pour tous les domaines
  - Rapide : calcul en O(n) sans GPU necessaire
  - Evolutif : peut etre combine avec BERT pour plus de precision
    """)


if __name__ == '__main__':
    demo_all_applications()
