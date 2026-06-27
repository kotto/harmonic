"""
Applications Concretes des Signatures Harmoniques 9D (Version BERT)
===================================================================
Version utilisant BERT (vrai LLM) pour des signatures plus discriminantes.

4 domaines d'application :
1. FINANCE   : Detection de fraude, sentiment de marche
2. SANTE     : Classification de symptomes, coherence prescriptions
3. INDUSTRIE : Diagnostic de pannes, optimisation maintenance
4. CREATION  : Analyse de style, plagiat, recommandation
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
from transformers import AutoTokenizer, AutoModel
from model.harmonic_pure_signatures_v4 import PureSignatureProjectionV4


# =========================================================================
# MOTEUR DE SIGNATURES 9D VIA BERT
# =========================================================================

class BertSignatureEngine:
    """
    Moteur de signatures 9D base sur BERT.
    Utilise les hidden states profonds pour des signatures plus riches.
    """
    
    def __init__(self, model_name='bert-base-uncased', device='cpu'):
        self.device = device
        print(f"[BERT] Chargement de {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(device).eval()
        self.proj = PureSignatureProjectionV4()
        print(f"[BERT] Modele charge avec {sum(p.numel() for p in self.model.parameters()):,} parametres")
    
    def compute_signature(self, text, max_length=128):
        """
        Calcule la signature 9D d'un texte via BERT.
        """
        inputs = self.tokenizer(text, return_tensors='pt', 
                               truncation=True, max_length=max_length,
                               padding='max_length').to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            
            # Utiliser les 4 dernieres couches cachees
            hidden_states = outputs.hidden_states[-4:]  # 4 couches
            combined = torch.stack(hidden_states).mean(dim=0)  # (1, seq_len, 768)
            
            # Appliquer la projection harmonique 9D
            sigs = self.proj(combined)  # (1, seq_len, 9)
            sigs = sigs.mean(dim=1)     # (1, 9)
        
        return sigs[0].cpu().numpy()
    
    def compute_signatures_batch(self, texts, max_length=128):
        """Calcule les signatures 9D pour une liste de textes."""
        return np.array([self.compute_signature(t, max_length) for t in texts])


# =========================================================================
# 1. FINANCE
# =========================================================================

class FinanceAnalyzerBERT:
    def __init__(self):
        self.engine = BertSignatureEngine()
    
    def detect_fraud(self, transactions):
        """Detection de fraude par anomalie de signature BERT."""
        descriptions = [t['description'] for t in transactions]
        sigs = self.engine.compute_signatures_batch(descriptions)
        
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
                'anomaly_distance': float(distance),
                'flag': 'FRAUDE' if fraud_score > 0.7 else 'SUSPECT' if fraud_score > 0.4 else 'NORMAL'
            })
        return results
    
    def analyze_market_sentiment(self, news_articles):
        """Analyse de sentiment de marche via BERT."""
        sigs = self.engine.compute_signatures_batch(news_articles)
        
        sentiment_scores = []
        for i, article in enumerate(news_articles):
            emotion = sigs[i][7]
            temporal = sigs[i][8]
            alpha = sigs[i][1]
            reasoning = sigs[i][2]
            
            # Score compose avec normalisation adaptative
            raw = emotion * 0.4 + temporal * 0.3 - alpha * 0.2 + reasoning * 0.1
            sentiment = float(np.clip((raw + 0.5) / 1.5, 0, 1))
            
            if sentiment > 0.55:
                label = "POSITIF"
            elif sentiment > 0.40:
                label = "NEUTRE"
            else:
                label = "NEGATIF"
            
            sentiment_scores.append({
                'article': article[:80] + '...' if len(article) > 80 else article,
                'sentiment_score': sentiment,
                'label': label
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
# 2. SANTE
# =========================================================================

class SanteAnalyzerBERT:
    def __init__(self):
        self.engine = BertSignatureEngine()
    
    def classify_symptoms(self, symptom_descriptions, known_classes=None):
        """Classification de symptomes via BERT."""
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
                    'distances': {k: float(v) for k, v in distances.items()}
                })
            return results
        return []
    
    def analyze_prescription_coherence(self, prescriptions):
        """Analyse de coherence des prescriptions via BERT."""
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
                'flag': 'COHERENT' if coherence > 0.6 else 'A_VERIFIER' if coherence > 0.4 else 'ANORMAL'
            })
        return results


# =========================================================================
# 3. INDUSTRIE
# =========================================================================

class IndustrieAnalyzerBERT:
    def __init__(self):
        self.engine = BertSignatureEngine()
    
    def diagnose_failures(self, failure_descriptions, known_failures=None):
        """Diagnostic de pannes via resonance BERT."""
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
                    'resonances': resonances
                })
            return results
        return []
    
    def optimize_maintenance(self, maintenance_logs):
        """Optimisation de maintenance par clustering BERT."""
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
# 4. CREATION
# =========================================================================

class CreationAnalyzerBERT:
    def __init__(self):
        self.engine = BertSignatureEngine()
    
    def analyze_style(self, texts, authors=None):
        """Analyse de style via BERT."""
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
        """Detection de plagiat via similarite BERT."""
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
            
            reports.append({
                'suspect': suspect[:60] + '...' if len(suspect) > 60 else suspect,
                'best_match': original_texts[best_match_idx][:60] + '...' if best_match_idx >= 0 else 'N/A',
                'similarity': float(best_similarity),
                'alert': 'PLAGIAT' if best_similarity > threshold else 'OK'
            })
        return reports
    
    def recommend_content(self, query_text, content_library, top_k=3):
        """Recommandation de contenu par resonance BERT."""
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
                'resonance_score': score
            })
        
        return {'query': query_text[:60] + '...' if len(query_text) > 60 else query_text,
                'recommendations': recommendations}


# =========================================================================
# DEMONSTRATION COMPLETE (BERT)
# =========================================================================

def demo_bert_applications():
    """Demonstration des 4 domaines avec BERT."""
    
    print("=" * 70)
    print("APPLICATIONS CONCRETES - SIGNATURES 9D VIA BERT")
    print("=" * 70)
    
    # =====================================================================
    # 1. FINANCE
    # =====================================================================
    print("\n" + "=" * 70)
    print("[1] FINANCE : Detection de Fraude et Sentiment de Marche")
    print("=" * 70)
    
    finance = FinanceAnalyzerBERT()
    
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
    
    print(f"\n  Detection de fraude (BERT) :")
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
    
    print(f"\n  Sentiment de marche (BERT) :")
    print(f"  Global: {sentiment['global_sentiment']:.3f} | Volatilite: {sentiment['volatility']:.3f}")
    print(f"  Positifs: {sentiment['positif_pct']:.0f}% | Negatifs: {sentiment['negatif_pct']:.0f}% | Neutres: {sentiment['neutre_pct']:.0f}%")
    
    for a in sentiment['articles']:
        print(f"  [{a['label']:<7}] {a['article'][:60]}")
    
    # =====================================================================
    # 2. SANTE
    # =====================================================================
    print("\n" + "=" * 70)
    print("[2] SANTE : Classification de Symptomes et Prescriptions")
    print("=" * 70)
    
    sante = SanteAnalyzerBERT()
    
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
    
    print(f"\n  Classification des symptomes (BERT) :")
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
    
    print(f"\n  Analyse de coherence des prescriptions (BERT) :")
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
    
    industrie = IndustrieAnalyzerBERT()
    
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
    
    print(f"\n  Diagnostic de pannes (BERT) :")
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
    
    print(f"\n  Optimisation de maintenance (BERT) :")
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
    
    creation = CreationAnalyzerBERT()
    
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
    
    print(f"\n  Analyse de style (BERT) :")
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
    
    print(f"\n  Detection de plagiat (BERT) :")
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
    
    print(f"\n  Recommandation de contenu (BERT) :")
    for requete in requetes:
        reco = creation.recommend_content(requete, bibliotheque)
        print(f"\n  Requete: {reco['query']}")
        for r in reco['recommendations']:
            print(f"    -> {r['content']} (resonance: {r['resonance_score']:.3f})")
    
    # =====================================================================
    # CONCLUSION
    # =====================================================================
    print("\n" + "=" * 70)
    print("CONCLUSION : BERT + SIGNATURES 9D = ANALYSE SEMANTIQUE PROFONDE")
    print("=" * 70)
    print("""
  BERT apporte une comprehension semantique qui manque a l'embedding fixe :
  
  - Signatures plus coherentes semantiquement
  - Meilleure discrimination entre classes proches
  - Comprehension du contexte (pas juste des mots isoles)
  - Robustesse aux variations de formulation
  
  L'embedding fixe reste utile pour :
  - Le prototypage rapide (0 GPU, 0 telechargement)
  - Les analyses discriminantes locales
  - Les environnements sans acces a internet
    """)


if __name__ == '__main__':
    demo_bert_applications()
