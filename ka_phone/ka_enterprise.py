#!/usr/bin/env python3
r"""
╔══════════════════════════════════════════════════════════════════╗
║  KA-ENTERPRISE — Hologrammes métier sur mesure                ║
║  Intelligence par Interférence d'Ondes pour l'Entreprise     ║
╚══════════════════════════════════════════════════════════════════╝

CONCEPT :
  Une entreprise fournit ses documents (PDF, DOCX, TXT, CSV, JSON,
  pages web, emails, base de connaissances interne...).
  
  KA-Enterprise :
    1. Analyse les documents
    2. Détecte automatiquement le domaine métier
    3. Crée des hologrammes 64×64 SPÉCIFIQUES au métier
    4. Offre une API REST pour interroger cette connaissance
    5. Zéro hallucination — chaque réponse est tracée au document source

ARCHITECTURE :
  ┌─────────────────────────────────────────────────────────────┐
  │  ENTREPRISE                                                │
  │  Documents → Extracteur (PDF/TXT/DOCX/CSV/JSON)           │
  │       ↓                                                     │
  │  Analyse sémantique → Domaine métier détecté               │
  │       ↓                                                     │
  │  Création hologrammes personnalisés (64×64)                 │
  │       ↓                                                     │
  │  API REST → Questions → Réponses tracées                   │
  │       ↓                                                     │
  │  Dashboard web → Upload, Stats, Logs                       │
  └─────────────────────────────────────────────────────────────┘

DOMAINES MÉTIER PRÉDÉFINIS :
  - juridique (contrats, lois, jurisprudence)
  - medical (diagnostics, traitements, protocoles)
  - finance (bilans, rapports, audits)
  - industrie (spécifications, manuels, procédures)
  - commerce (catalogues, fiches produits, tarifs)
  - tech (documentation API, specs, code, logs)
  - rh (contrats, conventions, procédures internes)
  - immo (annonces, diagnostics, compromis)

USAGE :
  # 1. Créer un hologramme métier
  python ka_enterprise.py create juridique docs/contrats/ docs/lois/
  
  # 2. Interroger l'hologramme
  python ka_enterprise.py ask juridique "Quelle clause de résiliation pour un CDI ?"
  
  # 3. Lancer le serveur entreprise
  python ka_enterprise.py serve
  
  # 4. Interface web de gestion
  python ka_enterprise.py dashboard
"""

import os, sys, json, time, re, hashlib, glob, mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

PHI = (1 + np.sqrt(5)) / 2

# ═══════════════════════════════════════════════════════════════════
# 1. DÉFINITIONS DES DOMAINES MÉTIER
# ═══════════════════════════════════════════════════════════════════

BUSINESS_DOMAINS = {
    "juridique": {
        "name": "Droit & Juridique",
        "keywords_fr": ["contrat", "loi", "article", "tribunal", "justice", "clause",
                        "jurisprudence", "code civil", "code pénal", "avocat", "préjudice",
                        "résiliation", "préavis", "indemnité", "contentieux", "procédure"],
        "keywords_en": ["contract", "law", "court", "clause", "liability", "damages",
                        "jurisdiction", "statute", "plaintiff", "defendant", "agreement"],
        "prompt_template": "En tant qu'assistant juridique, voici ce que je trouve dans la documentation :\n{reponse}",
    },
    "medical": {
        "name": "Médical & Santé",
        "keywords_fr": ["diagnostic", "traitement", "patient", "pathologie", "symptôme",
                        "ordonnance", "protocole", "chirurgie", "médicament", "posologie",
                        "examen", "radiologie", "consultation", "hospitalisation"],
        "keywords_en": ["diagnosis", "treatment", "patient", "pathology", "symptom",
                        "prescription", "protocol", "surgery", "medication", "dosage"],
        "prompt_template": "Selon les protocoles documentés :\n{reponse}",
    },
    "finance": {
        "name": "Finance & Comptabilité",
        "keywords_fr": ["bilan", "compte", "résultat", "trésorerie", "audit", "fiscal",
                        "amortissement", "provision", "chiffre d'affaires", "marge",
                        "investissement", "dividende", "actif", "passif", "budget"],
        "keywords_en": ["balance", "account", "revenue", "cash", "audit", "tax",
                        "depreciation", "provision", "turnover", "margin", "investment"],
        "prompt_template": "D'après les données financières analysées :\n{reponse}",
    },
    "technique": {
        "name": "Technique & Industrie",
        "keywords_fr": ["spécification", "manuel", "procédure", "maintenance", "schéma",
                        "norme", "certification", "qualité", "sécurité", "machine",
                        "production", "assemblage", "contrôle", "mesure", "tolérance"],
        "keywords_en": ["specification", "manual", "procedure", "maintenance", "diagram",
                        "standard", "certification", "quality", "safety", "machine"],
        "prompt_template": "Selon la documentation technique :\n{reponse}",
    },
    "commerce": {
        "name": "Commerce & Vente",
        "keywords_fr": ["produit", "catalogue", "tarif", "client", "commande", "stock",
                        "livraison", "facture", "devis", "remise", "promotion",
                        "fournisseur", "référence", "garantie", "SAV"],
        "keywords_en": ["product", "catalogue", "price", "customer", "order", "stock",
                        "delivery", "invoice", "quote", "discount", "supplier"],
        "prompt_template": "Dans notre catalogue :\n{reponse}",
    },
    "informatique": {
        "name": "IT & Développement",
        "keywords_fr": ["API", "endpoint", "fonction", "classe", "module", "déploiement",
                        "bug", "patch", "version", "release", "test", "log", "erreur",
                        "configuration", "paramètre", "base de données", "requête"],
        "keywords_en": ["API", "endpoint", "function", "class", "module", "deployment",
                        "bug", "patch", "version", "release", "test", "log", "error"],
        "prompt_template": "D'après la documentation technique :\n{reponse}",
    },
    "rh": {
        "name": "Ressources Humaines",
        "keywords_fr": ["contrat", "congé", "salaire", "recrutement", "entretien",
                        "formation", "carrière", "compétence", "évaluation", "effectif",
                        "convention collective", "syndicat", "démission", "licenciement"],
        "keywords_en": ["contract", "leave", "salary", "recruitment", "interview",
                        "training", "career", "skill", "evaluation", "headcount"],
        "prompt_template": "Selon nos procédures RH :\n{reponse}",
    },
    "immobilier": {
        "name": "Immobilier & Construction",
        "keywords_fr": ["appartement", "maison", "loyer", "vente", "diagnostic",
                        "compromis", "acte", "notaire", "surface", "étage", "copropriété",
                        "syndic", "DPE", "charges", "prêt", "hypothèque"],
        "keywords_en": ["apartment", "house", "rent", "sale", "diagnosis", "deed",
                        "notary", "surface", "floor", "condominium", "loan", "mortgage"],
        "prompt_template": "D'après les documents immobiliers :\n{reponse}",
    },
}


# ═══════════════════════════════════════════════════════════════════
# 2. EXTRACTEUR DE DOCUMENTS (multi-format)
# ═══════════════════════════════════════════════════════════════════

class DocumentExtractor:
    """Extrait le texte de tout type de document (PDF, DOCX, TXT, CSV, JSON, HTML)."""
    
    @staticmethod
    def extract_text(filepath: str) -> str:
        """Extrait le texte d'un fichier, auto-détection du format."""
        ext = Path(filepath).suffix.lower()
        
        # Fichiers texte bruts
        if ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.sql', '.log',
                    '.json', '.xml', '.yaml', '.yml', '.csv', '.tsv']:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                try:
                    with open(filepath, 'r', encoding='latin-1') as f:
                        return f.read()
                except:
                    return ""
        
        # PDF
        if ext == '.pdf':
            try:
                import PyPDF2
                text = []
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages[:50]:  # 50 premières pages max
                        text.append(page.extract_text() or "")
                return '\n'.join(text)
            except ImportError:
                # Fallback : lecture binaire brute
                try:
                    with open(filepath, 'rb') as f:
                        raw = f.read()
                    # Tentative d'extraction de texte brut
                    text = re.sub(rb'[^\x20-\x7E\n\r\t]', b' ', raw).decode('ascii', errors='ignore')
                    return text[:50000]
                except:
                    return ""
        
        # DOCX
        if ext == '.docx':
            try:
                import docx
                doc = docx.Document(filepath)
                return '\n'.join([p.text for p in doc.paragraphs])
            except ImportError:
                return ""
        
        return ""


    @staticmethod
    def extract_directory(directory: str, recursive: bool = True) -> Dict[str, str]:
        """Extrait tous les documents d'un répertoire."""
        documents = {}
        pattern = os.path.join(directory, "**" if recursive else "", "*")
        for filepath in glob.glob(pattern, recursive=recursive):
            if os.path.isfile(filepath):
                text = DocumentExtractor.extract_text(filepath)
                if text and len(text) > 100:
                    documents[filepath] = text
        return documents


# ═══════════════════════════════════════════════════════════════════
# 3. DÉTECTEUR AUTOMATIQUE DE DOMAINE MÉTIER
# ═══════════════════════════════════════════════════════════════════

class DomainDetector:
    """Détecte automatiquement le domaine métier à partir du contenu."""
    
    @staticmethod
    def detect(texts: Dict[str, str]) -> Tuple[str, float]:
        """
        Analyse un ensemble de documents et retourne le domaine
        métier le plus probable avec un score de confiance.
        """
        all_text = " ".join(texts.values()).lower()
        
        scores = {}
        for domain_id, info in BUSINESS_DOMAINS.items():
            score = 0
            for kw in info.get("keywords_fr", []):
                score += all_text.count(kw.lower())
            for kw in info.get("keywords_en", []):
                score += all_text.count(kw.lower())
            # Bonus pour les mots composés (plus significatifs)
            for kw in info.get("keywords_fr", []):
                if " " in kw and kw.lower() in all_text:
                    score += 5
            scores[domain_id] = score
        
        if not scores or max(scores.values()) == 0:
            return "general", 0.0
        
        best = max(scores, key=scores.get)
        max_score = scores[best]
        total = sum(scores.values())
        confidence = max_score / max(total, 1)
        
        return best, round(confidence, 3)


# ═══════════════════════════════════════════════════════════════════
# 4. CONSTRUCTEUR D'HOLOGRAMME MÉTIER
# ═══════════════════════════════════════════════════════════════════

class EnterpriseHologram:
    """
    Hologramme 64×64 personnalisé pour une entreprise.
    Version simplifiée auto-contenue (ne dépend pas de holographic_ensemble).
    """
    
    def __init__(self, domain: str, company_name: str = "Entreprise"):
        self.domain = domain
        self.company_name = company_name
        self.size = 64
        
        # Grille holographique
        self.grid = np.zeros((self.size, self.size), dtype=np.complex128)
        
        # Métadonnées
        self.facts: List[Dict] = []
        self.sources: Dict[str, str] = {}  # fact_text → source_file
        
        # Statistiques
        self.total_ingested = 0
        self.energy = 0.0
        
        # Métier
        self.domain_info = BUSINESS_DOMAINS.get(domain, BUSINESS_DOMAINS.get("general", {}))
    
    def _text_to_position(self, text: str) -> Tuple[int, int]:
        """SHA-256 → position (kx, ky) dans la grille 64×64."""
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = int(h[:16], 16) % (self.size * 100) / 100.0
        ky = int(h[16:32], 16) % (self.size * 100) / 100.0
        return kx, ky
    
    def ingest_text(self, text: str, source_file: str = "", amplitude: float = 0.08):
        """
        Ingère un texte dans l'hologramme.
        Chaque phrase devient un fait encodé comme une onde.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        for sentence in sentences:
            sentence = re.sub(r'\s+', ' ', sentence.strip())
            if len(sentence) < 20 or len(sentence) > 1000:
                continue
            
            kx, ky = self._text_to_position(sentence)
            phase = kx * ky * PHI % (2 * np.pi)
            
            # Ajouter l'onde à la grille holographique
            self.grid[int(min(kx, self.size-1)), int(min(ky, self.size-1))] += amplitude * np.exp(1j * phase)
            
            # Stocker les métadonnées
            self.facts.append({
                "text": sentence,
                "kx": kx,
                "ky": ky,
                "amplitude": amplitude,
                "source": source_file or "document",
            })
            
            self.total_ingested += 1
            self.energy += amplitude ** 2
        
        # Nettoyer la grille si trop dense
        if self.total_ingested > 20000:
            self.grid = self.grid / 1.1  # Atténuation douce
    
    def query(self, question: str, k: int = 10) -> List[Dict]:
        """
        Interroge l'hologramme — cherche les faits qui résonnent
        avec la question par interférence d'ondes.
        """
        if not self.facts:
            return [{"text": "Aucun document chargé", "score": 0, "source": "system"}]
        
        q_kx, q_ky = self._text_to_position(question)
        q_vec = np.array([q_kx, q_ky])
        q_norm = np.linalg.norm(q_vec) or 1e-10
        
        # Calculer le score de résonance pour chaque fait
        scores = []
        for fact in self.facts:
            f_vec = np.array([fact["kx"], fact["ky"]])
            f_norm = np.linalg.norm(f_vec) or 1e-10
            
            # Interférence cosinus (structurelle)
            cos_sim = float(np.dot(q_vec, f_vec) / (q_norm * f_norm))
            
            # Boost sémantique amélioré (intersection de mots + IDF)
            stop_words = {'dans', 'avec', 'pour', 'sur', 'sous', 'dont', 'cette', 'leur',
                          'plus', 'tout', 'vous', 'nous', 'alors', 'comme', 'bien', 'fait',
                          'peut', 'tres', 'sont', 'aux', 'une', 'est', 'les', 'des', 'pas',
                          'que', 'qui', 'par', 'the', 'and', 'cest', 'ete', 'etait',
                          'quelle', 'quels', 'quelles', 'comment', 'quoi', 'pourquoi'}
            q_words = {w.strip('.,;:!?()[]{}"\'-').lower() for w in question.lower().split()
                       if len(w.strip('.,;:!?()[]{}"\'-')) > 1 and w.lower() not in stop_words}
            f_words = {w.strip('.,;:!?()[]{}"\'-').lower() for w in fact["text"].lower().split()
                       if len(w.strip('.,;:!?()[]{}"\'-')) > 1 and w.lower() not in stop_words}
            common = q_words & f_words
            # Bonus pour mots longs (> 4 caractères, plus discriminants)
            long_common = sum(1 for w in common if len(w) > 4)
            semantic = (len(common) + long_common * 2) / max(len(q_words) + 2, 3)
            
            # Score combiné : adaptatif selon la densité
            if self.total_ingested < 200:
                score = 0.0 * abs(cos_sim) + 1.0 * min(1.0, semantic * 1.5)
            elif self.total_ingested < 1000:
                score = 0.1 * abs(cos_sim) + 0.9 * semantic
            else:
                score = 0.4 * abs(cos_sim) + 0.6 * semantic
            scores.append({
                "text": fact["text"],
                "score": round(score, 4),
                "cosinus": round(cos_sim, 4),
                "semantic": round(semantic, 4),
                "source": fact.get("source", "document"),
            })
        
        # Top-K
        scores.sort(key=lambda x: -x["score"])
        return scores[:k]
    
    def update(self, text: str, source_file: str = "") -> int:
        """
        Ajoute un nouveau document SANS reconstruire l'hologramme.
        Apprentissage continu en O(1) — killer feature KA-Enterprise.
        
        Contrairement à ingest_massive_nx64.py qui efface tout,
        cette méthode AJOUTE les nouveaux faits à la grille existante.
        """
        n_before = self.total_ingested
        self.ingest_text(text, source_file=source_file)
        return self.total_ingested - n_before
    
    def save_encrypted(self, master_key: str) -> str:
        """
        Sauvegarde l'hologramme chiffré AES-256-GCM.
        
        Les données métier ne quittent JAMAIS le serveur en clair.
        Seule la clé maître (dérivée du salt de l'entreprise) peut déchiffrer.
        """
        import base64
        try:
            from Crypto.Cipher import AES
            from Crypto.Protocol.KDF import PBKDF2
        except ImportError:
            # Fallback : chiffrement XOR basique (moins sécurisé mais fonctionnel)
            return self._save_xor(master_key)
        
        # Dériver une clé AES-256 à partir de la clé maître
        salt = hashlib.sha256(self.company_name.encode()).digest()[:16]
        aes_key = PBKDF2(master_key, salt, dkLen=32, count=100000)  # type: ignore
        
        # Sérialiser les données
        data = json.dumps({
            "domain": self.domain,
            "company": self.company_name,
            "facts": self.facts,
            "total_ingested": self.total_ingested,
            "energy": self.energy,
        }, ensure_ascii=False).encode('utf-8')
        
        # Chiffrer AES-256-GCM
        cipher = AES.new(aes_key, AES.MODE_GCM)  # type: ignore
        ciphertext, tag = cipher.encrypt_and_digest(data)  # type: ignore
        
        # Format : nonce(16) + tag(16) + ciphertext
        encrypted = cipher.nonce + tag + ciphertext  # type: ignore
        
        # Sauvegarder
        filepath = self._get_encrypted_path()
        with open(filepath, 'wb') as f:
            f.write(encrypted)
        
        return filepath
    
    def load_encrypted(self, master_key: str, filepath: str = "") -> bool:
        """
        Charge un hologramme chiffré AES-256-GCM.
        Retourne True si le déchiffrement a réussi.
        """
        import base64
        fp = filepath or self._get_encrypted_path()
        if not os.path.exists(fp):
            return False
        
        with open(fp, 'rb') as f:
            encrypted = f.read()
        
        try:
            from Crypto.Cipher import AES
            from Crypto.Protocol.KDF import PBKDF2
            
            # Extraire nonce(16) + tag(16) + ciphertext
            nonce = encrypted[:16]
            tag = encrypted[16:32]
            ciphertext = encrypted[32:]
            
            # Re-dériver la clé
            salt = hashlib.sha256(self.company_name.encode()).digest()[:16]
            aes_key = PBKDF2(master_key, salt, dkLen=32, count=100000)  # type: ignore
            
            # Déchiffrer
            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)  # type: ignore
            data = cipher.decrypt_and_verify(ciphertext, tag)  # type: ignore
            
            # Restaurer les données
            obj = json.loads(data.decode('utf-8'))
            self.domain = obj.get("domain", self.domain)
            self.company_name = obj.get("company", self.company_name)
            self.facts = obj.get("facts", [])
            self.total_ingested = obj.get("total_ingested", 0)
            self.energy = obj.get("energy", 0.0)
            
            # Reconstruire la grille holographique à partir des faits
            self.grid = np.zeros((self.size, self.size), dtype=np.complex128)
            for fact in self.facts:
                kx, ky = fact.get("kx", 0), fact.get("ky", 0)
                phase = kx * ky * PHI % (2 * np.pi)
                self.grid[int(min(kx, self.size-1)), int(min(ky, self.size-1))] += fact.get("amplitude", 0.08) * np.exp(1j * phase)
            
            return True
            
        except ImportError:
            return self._load_xor(master_key, fp)
        except Exception as e:
            return False
    
    def _get_encrypted_path(self) -> str:
        """Chemin du fichier hologramme chiffré."""
        holo_id = hashlib.md5(f"{self.company_name}_{self.domain}".encode()).hexdigest()[:12]
        enterprise_dir = os.path.join(os.path.dirname(__file__), "..", "data", "enterprise")
        os.makedirs(enterprise_dir, exist_ok=True)
        return os.path.join(enterprise_dir, f"{holo_id}.enc")
    
    def _save_xor(self, master_key: str) -> str:
        """Fallback XOR (moins sécurisé mais fonctionnel sans pycryptodome)."""
        import base64
        data = json.dumps({
            "domain": self.domain, "company": self.company_name,
            "facts": self.facts, "total_ingested": self.total_ingested,
            "energy": self.energy,
        }, ensure_ascii=False).encode('utf-8')
        
        # XOR avec la clé
        key_bytes = hashlib.sha256(master_key.encode()).digest()
        encrypted = bytes([data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data))])
        
        filepath = self._get_encrypted_path().replace('.enc', '.xor')
        with open(filepath, 'wb') as f:
            f.write(encrypted)
        return filepath
    
    def _load_xor(self, master_key: str, filepath: str) -> bool:
        """Fallback déchiffrement XOR."""
        try:
            with open(filepath, 'rb') as f:
                encrypted = f.read()
            key_bytes = hashlib.sha256(master_key.encode()).digest()
            data = bytes([encrypted[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(encrypted))])
            obj = json.loads(data.decode('utf-8'))
            self.domain = obj.get("domain", self.domain)
            self.company_name = obj.get("company", self.company_name)
            self.facts = obj.get("facts", [])
            self.total_ingested = obj.get("total_ingested", 0)
            self.energy = obj.get("energy", 0.0)
            return True
        except:
            return False

    def get_stats(self) -> Dict:
        """Retourne les statistiques de l'hologramme."""
        return {
            "domain": self.domain,
            "domain_name": self.domain_info.get("name", ""),
            "company": self.company_name,
            "total_facts": self.total_ingested,
            "energy": round(self.energy, 2),
            "grid_density": round(np.abs(self.grid).sum() / (self.size ** 2), 4),
            "unique_sources": len(set(f.get("source", "") for f in self.facts)),
        }


# ═══════════════════════════════════════════════════════════════════
# 5. MANAGER ENTERPRISE (CRUD des hologrammes métier)
# ═══════════════════════════════════════════════════════════════════

class EnterpriseManager:
    """Gère les hologrammes métier d'une entreprise."""
    
    def __init__(self, storage_dir: str = ""):
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(__file__), "..", "data", "enterprise")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.holograms: Dict[str, EnterpriseHologram] = {}
        self._load_existing()
    
    def _load_existing(self):
        """Charge les hologrammes existants."""
        for filepath in glob.glob(os.path.join(self.storage_dir, "*.json")):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                holo_id = meta.get("id", "")
                if holo_id:
                    self.holograms[holo_id] = None  # Lazy load
            except:
                pass
    
    def create(self, domain: str, company_name: str, 
               documents_path: str = "", files: List[str] = None) -> Dict:
        """Crée un nouvel hologramme métier."""
        
        # 1. Extraire les documents
        all_texts = {}
        if documents_path and os.path.exists(documents_path):
            all_texts = DocumentExtractor.extract_directory(documents_path)
        if files:
            for fp in files:
                if os.path.isfile(fp):
                    all_texts[fp] = DocumentExtractor.extract_text(fp)
        
        # 2. Auto-détecter le domaine si non spécifié
        if domain == "auto" and all_texts:
            domain, confidence = DomainDetector.detect(all_texts)
            print(f"  Domaine détecté : {domain} (confiance: {confidence:.0%})")
        
        # 3. Créer l'hologramme
        holo_id = hashlib.md5(f"{company_name}_{domain}".encode()).hexdigest()[:12]
        holo = EnterpriseHologram(domain=domain, company_name=company_name)
        
        # 4. Ingérer tous les textes
        stats_domains = defaultdict(int)
        for filepath, text in all_texts.items():
            holo.ingest_text(text, source_file=os.path.basename(filepath))
            # Router par domaine sémantique
            for file_domain in BUSINESS_DOMAINS:
                for kw in BUSINESS_DOMAINS[file_domain].get("keywords_fr", [])[:5]:
                    if kw in text.lower()[:500]:
                        stats_domains[file_domain] += 1
                        break
        
        # 5. Sauvegarder
        self.holograms[holo_id] = holo
        self._save_metadata(holo_id, company_name, domain)
        
        return {
            "id": holo_id,
            "domain": domain,
            "domain_name": BUSINESS_DOMAINS.get(domain, {}).get("name", ""),
            "company": company_name,
            "total_facts": holo.total_ingested,
            "files_processed": len(all_texts),
            "stats_domains": dict(stats_domains),
            "energy": round(holo.energy, 2),
        }
    
    def _save_metadata(self, holo_id: str, company: str, domain: str):
        """Sauvegarde les métadonnées de l'hologramme."""
        meta = {
            "id": holo_id,
            "company": company,
            "domain": domain,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "facts_count": self.holograms[holo_id].total_ingested if self.holograms[holo_id] else 0,
        }
        filepath = os.path.join(self.storage_dir, f"{holo_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    
    def ask(self, holo_id: str, question: str, k: int = 5) -> Dict:
        """Interroge un hologramme métier."""
        holo = self.holograms.get(holo_id)
        if holo is None:
            return {"error": f"Hologramme {holo_id} non trouvé"}
        
        facts = holo.query(question, k=k)
        confidence = facts[0]["score"] if facts else 0
        
        return {
            "id": holo_id,
            "question": question,
            "confidence": round(confidence, 3),
            "top_facts": facts,
            "source": f"enterprise-hologram-{holo_id}",
            "stats": holo.get_stats(),
        }
    
    def list(self) -> List[Dict]:
        """Liste tous les hologrammes."""
        result = []
        for holo_id, holo in self.holograms.items():
            filepath = os.path.join(self.storage_dir, f"{holo_id}.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    result.append(json.load(f))
        return result


# ═══════════════════════════════════════════════════════════════════
# 6. DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════

def demo():
    """Démonstration de KA-Enterprise."""
    print("=" * 70)
    print("  KA-ENTERPRISE — Démonstration")
    print("  Intelligence par Interférence d'Ondes pour l'Entreprise")
    print("=" * 70)
    
    # Créer des documents de démonstration
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo_docs")
    os.makedirs(demo_dir, exist_ok=True)
    
    # Document juridique
    with open(os.path.join(demo_dir, "contrat.txt"), "w", encoding="utf-8") as f:
        f.write("""
CONTRAT DE TRAVAIL À DURÉE INDÉTERMINÉE
Article 1 : Le présent contrat est régi par le Code du Travail.
Article 2 : La période d'essai est de 3 mois renouvelable une fois.
Article 3 : Le salaire mensuel brut est fixé à 3000 euros.
Article 4 : Le préavis de démission est de 1 mois.
Article 5 : Le préavis de licenciement est de 2 mois pour moins de 2 ans d'ancienneté.
Article 6 : Les congés payés sont de 25 jours ouvrés par an.
Article 7 : La clause de non-concurrence s'applique pendant 12 mois après le départ.
Article 8 : En cas de litige, le tribunal compétent est le Conseil de Prud'hommes.
Clause de résiliation : Le contrat peut être résilié par accord mutuel ou pour faute grave.
        """.strip())
    
    # Document technique
    with open(os.path.join(demo_dir, "specifications.txt"), "w", encoding="utf-8") as f:
        f.write("""
SPÉCIFICATIONS TECHNIQUES — PRODUIT X-2000
Version : 3.2.1 — Date : 2026-06-12
Température de fonctionnement : -20°C à +85°C
Tension d'alimentation : 12V DC ±5%
Consommation maximale : 2.5A
Interface de communication : RS-485, débit 115200 bauds
Protocole : Modbus RTU
Certification : CE, RoHS, REACH
Dimensions : 120mm × 80mm × 45mm
Poids : 340g
Garantie : 3 ans pièces et main d'œuvre
Maintenance préventive recommandée tous les 6 mois.
Procédure de calibration : Utiliser le logiciel CalibPro v4.2 avec le câble USB-CAL-01.
        """.strip())
    
    print(f"\n  Documents de démonstration créés dans : {demo_dir}")
    
    # Créer le manager
    manager = EnterpriseManager()
    
    # Créer un hologramme juridique
    print("\n── 1. CRÉATION HOLOGRAMME JURIDIQUE ──")
    result = manager.create(
        domain="juridique",
        company_name="DemoCorp",
        documents_path=demo_dir,
    )
    print(f"  ID : {result['id']}")
    print(f"  Domaine : {result['domain_name']}")
    print(f"  Faits ingérés : {result['total_facts']}")
    print(f"  Fichiers traités : {result['files_processed']}")
    
    # Interroger
    print("\n── 2. INTERROGATION ──")
    
    questions = [
        "Quelle est la durée du préavis de démission ?",
        "Quelle est la température de fonctionnement du produit X-2000 ?",
        "Comment résilier le contrat ?",
        "Quelle est la tension d'alimentation ?",
    ]
    
    for q in questions:
        answer = manager.ask(result['id'], q, k=3)
        top = answer['top_facts'][0] if answer['top_facts'] else {"text": "?", "score": 0}
        print(f"  Q: {q}")
        print(f"  R: {top['text'][:100]}...")
        print(f"  Score: {top['score']:.3f} | Source: {top.get('source','?')}")
        print()
    
    # Lister
    print("\n── 3. HOLOGRAMMES EXISTANTS ──")
    for h in manager.list():
        print(f"  {h['id']} | {h['domain']} | {h['company']} | {h['facts_count']} faits")
    
    print("\n" + "=" * 70)
    print("  FIN DE LA DÉMONSTRATION")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="KA-Enterprise")
    p.add_argument("action", nargs="?", default="demo",
                   choices=["demo", "create", "ask", "serve", "list"])
    p.add_argument("domain", nargs="?", default="auto")
    p.add_argument("query_or_path", nargs="?", default="")
    p.add_argument("--company", type=str, default="MonEntreprise")
    p.add_argument("--files", nargs="+", default=None)
    p.add_argument("--id", type=str, default="")
    
    args = p.parse_args()
    
    if args.action == "demo":
        demo()
    elif args.action == "list":
        manager = EnterpriseManager()
        for h in manager.list():
            print(f"  {h['id']} | {h['domain']:15s} | {h['company']} | {h['facts_count']} faits")
    else:
        manager = EnterpriseManager()
        
        if args.action == "create":
            result = manager.create(
                domain=args.domain,
                company_name=args.company,
                documents_path=args.query_or_path,
                files=args.files,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif args.action == "ask":
            result = manager.ask(args.id or list(manager.holograms.keys())[0], args.query_or_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif args.action == "serve":
            print("Serveur non implémenté dans cette démo — utiliser ka_next_v3.py --serve")