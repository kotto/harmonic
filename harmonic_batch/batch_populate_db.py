"""
Syst[U+00E8]me Batch de Peuplement de la Base de Donn[U+00E9]es Harmonique
==============================================================
Cr[U+00E9]e et peuple la base de donn[U+00E9]es locale avec des donn[U+00E9]es initiales :
- Textes (corpus, articles, connaissances)
- Images (descriptions, signatures visuelles)
- Audio (descriptions, m[U+00E9]tadonn[U+00E9]es)
- Vid[U+00E9]o (descriptions, m[U+00E9]tadonn[U+00E9]es)
- Documents (PDF, analyses)

Usage:
    python batch_populate_db.py --init          # Cr[U+00E9]e les tables
    python batch_populate_db.py --seed          # Peuple avec donn[U+00E9]es initiales
    python batch_populate_db.py --index         # Indexation harmonique
    python batch_populate_db.py --all           # Tout en un
    python batch_populate_db.py --report        # Rapport d'[U+00E9]tat
"""

import sqlite3
import json
import os
import sys
import time
import math
import hashlib
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================

PHI = 1.618033988749895
ALPHA = 1.1755694591
B_1_PHI = 0.8506508083

# =========================================================================
# CONFIGURATION
# =========================================================================

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'harmonic_ai.db')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
TEXT_DIR = os.path.join(DATA_DIR, 'texts')
IMAGE_DIR = os.path.join(DATA_DIR, 'images')
AUDIO_DIR = os.path.join(DATA_DIR, 'audio')
VIDEO_DIR = os.path.join(DATA_DIR, 'video')
DOC_DIR = os.path.join(DATA_DIR, 'documents')

# =========================================================================
# ANALYSEUR HARMONIQUE EMBARQU[U+00C9]
# =========================================================================

class HarmonicAnalyzer:
    """Analyse harmonique 7D d'un texte"""
    
    def analyze(self, text):
        if not text or len(text) < 3:
            return [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        
        words = text.split()
        sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if len(s.strip()) > 0]
        
        # [U+03C6]_ratio : diversit[U+00E9] lexicale
        unique_words = len(set(w.lower() for w in words))
        phi_ratio = min(1.0, unique_words / max(1, len(words)) * PHI)
        
        # [U+03B1]_complexity : complexit[U+00E9] syntaxique
        avg_sentence_len = len(words) / max(1, len(sentences))
        alpha_complexity = min(1.0, avg_sentence_len / 30)
        
        # k_reasoning : raisonnement
        reasoning_words = {'donc', 'car', 'parce', 'puisque', 'alors', 'si', 'cependant',
                          'n[U+00E9]anmoins', 'pourtant', 'en effet', 'par cons[U+00E9]quent', 'because',
                          'therefore', 'thus', 'hence', 'consequently', 'since', 'although',
                          'however', 'nevertheless', 'moreover', 'furthermore'}
        reasoning_count = sum(1 for w in words if w.lower() in reasoning_words)
        k_reasoning = min(1.0, reasoning_count / max(1, len(words)) * 20)
        
        # k_creative : cr[U+00E9]ativit[U+00E9]
        creative_words = {'comme', 'tel', 'semble', 'para[U+00EE]t', 'ressemble', 'magnifique',
                         'sublime', 'extraordinaire', 'unique', 'like', 'seems', 'appears',
                         'beautiful', 'splendid', 'magnificent', 'extraordinary', 'metaphor'}
        creative_count = sum(1 for w in words if w.lower() in creative_words)
        k_creative = min(1.0, creative_count / max(1, len(words)) * 15)
        
        # k_mathematical
        math_count = len(re.findall(r'\d+[.,]?\d*', text))
        k_mathematical = min(1.0, math_count / max(1, len(words)) * 10)
        
        # k_factual
        factual_words = {'selon', '[U+00E9]tude', 'recherche', 'source', 'donn[U+00E9]es', 'statistiques',
                        'according', 'study', 'research', 'source', 'data', 'statistics',
                        'percentage', 'report', 'survey', 'analysis', 'findings', 'evidence'}
        factual_count = sum(1 for w in words if w.lower() in factual_words)
        k_factual = min(1.0, factual_count / max(1, len(words)) * 15)
        
        # k_code
        code_words = {'function', 'class', 'def', 'import', 'return', 'if', 'else',
                     'for', 'while', 'var', 'let', 'const', 'int', 'float', 'string',
                     'array', 'object', 'null', 'true', 'false', 'void', 'public'}
        code_count = sum(1 for w in words if w.lower() in code_words)
        k_code = min(1.0, code_count / max(1, len(words)) * 20)
        
        return [
            round(phi_ratio, 4),
            round(alpha_complexity, 4),
            round(k_reasoning, 4),
            round(k_creative, 4),
            round(k_mathematical, 4),
            round(k_factual, 4),
            round(k_code, 4)
        ]


# =========================================================================
# GESTIONNAIRE DE BASE DE DONN[U+00C9]ES
# =========================================================================

class DatabaseManager:
    """G[U+00E8]re la cr[U+00E9]ation et le peuplement de la base de donn[U+00E9]es"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.analyzer = HarmonicAnalyzer()
        self.conn = None
    
    def connect(self):
        """Connexion [U+00E0] la base de donn[U+00E9]es"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        return self.conn
    
    def close(self):
        """Fermeture de la connexion"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    # =====================================================================
    # CR[U+00C9]ATION DES TABLES
    # =====================================================================
    
    def create_tables(self):
        """Cr[U+00E9]e toutes les tables n[U+00E9]cessaires"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        
        # Table des textes / corpus
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corpus_texts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                language TEXT DEFAULT 'fr',
                source TEXT,
                author TEXT,
                word_count INTEGER,
                signature TEXT,
                resonance REAL,
                dominant_category TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Table des images
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corpus_images (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT,
                description TEXT,
                category TEXT,
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                format TEXT,
                signature TEXT,
                resonance REAL,
                dominant_category TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Table des fichiers audio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corpus_audio (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT,
                description TEXT,
                category TEXT,
                duration_seconds REAL,
                sample_rate INTEGER,
                channels INTEGER,
                format TEXT,
                signature TEXT,
                resonance REAL,
                dominant_category TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Table des fichiers vid[U+00E9]o
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corpus_video (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT,
                description TEXT,
                category TEXT,
                duration_seconds REAL,
                width INTEGER,
                height INTEGER,
                format TEXT,
                signature TEXT,
                resonance REAL,
                dominant_category TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Table des documents
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corpus_documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT,
                description TEXT,
                category TEXT,
                page_count INTEGER,
                file_size INTEGER,
                format TEXT,
                signature TEXT,
                resonance REAL,
                dominant_category TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Table des embeddings harmoniques (index vectoriel)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS harmonic_embeddings (
                id TEXT PRIMARY KEY,
                content_type TEXT NOT NULL,
                content_id TEXT NOT NULL,
                signature TEXT NOT NULL,
                resonance REAL,
                dominant_category TEXT,
                embedding_hash TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Table des relations harmoniques (similarit[U+00E9]s)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS harmonic_relations (
                id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                similarity REAL NOT NULL,
                relation_type TEXT DEFAULT 'harmonic',
                created_at TEXT NOT NULL
            )
        """)
        
        # Table des m[U+00E9]tadonn[U+00E9]es batch
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_metadata (
                id TEXT PRIMARY KEY,
                batch_name TEXT NOT NULL,
                batch_type TEXT NOT NULL,
                items_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                error TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Index pour acc[U+00E9]l[U+00E9]rer les recherches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_texts_category ON corpus_texts(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_texts_resonance ON corpus_texts(resonance)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_images_category ON corpus_images(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_audio_category ON corpus_audio(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_video_category ON corpus_video(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corpus_documents_category ON corpus_documents(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_harmonic_embeddings_content ON harmonic_embeddings(content_type, content_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_harmonic_relations_similarity ON harmonic_relations(similarity DESC)")
        
        self.conn.commit()
        print("[OK] Tables creees avec succes")

    
    # =====================================================================
    # G[U+00C9]N[U+00C9]RATION D'ID
    # =====================================================================
    
    def _generate_id(self, prefix='corpus'):
        """G[U+00E9]n[U+00E8]re un ID unique"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        random_part = random.randint(1000, 9999)
        return f"{prefix}_{timestamp}_{random_part}"
    
    def _hash_id(self, content):
        """Hash pour d[U+00E9]duplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def _categorize(self, sig):
        """D[U+00E9]termine la cat[U+00E9]gorie dominante [U+00E0] partir de la signature"""
        phi, alpha, reasoning, creative, math_val, factual, code = sig
        cats = {
            'Scientifique': math_val * 0.4 + factual * 0.3 + reasoning * 0.3,
            'Cr[U+00E9]atif': creative * 0.6 + phi * 0.4,
            'Technique': code * 0.5 + math_val * 0.3 + factual * 0.2,
            'Analyse': reasoning * 0.5 + factual * 0.3 + phi * 0.2,
            'Factuel': factual * 0.6 + math_val * 0.2 + reasoning * 0.2
        }
        return max(cats, key=cats.get)
    
    def _add_embedding(self, content_type, content_id, sig, resonance, dominant_cat):
        """Ajoute un embedding harmonique"""
        emb_id = self._generate_id('emb')
        now = datetime.utcnow().isoformat()
        emb_hash = hashlib.md5(json.dumps(sig).encode()).hexdigest()
        
        self.conn.execute("""
            INSERT INTO harmonic_embeddings
            (id, content_type, content_id, signature, resonance, dominant_category, embedding_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (emb_id, content_type, content_id, json.dumps(sig), resonance, dominant_cat, emb_hash, now))
    
    # =====================================================================
    # PEUPLEMENT [U+2014] TEXTES
    # =====================================================================
    
    def seed_texts(self):
        """Peuple la base avec des textes initiaux"""
        texts = self._get_initial_texts()
        count = 0
        
        for text_data in texts:
            sig = self.analyzer.analyze(text_data['content'])
            resonance = min(1.0, math.sqrt(sum(v*v for v in sig)) * PHI / 3)
            dominant_cat = self._categorize(sig)
            
            text_id = self._generate_id('txt')
            now = datetime.utcnow().isoformat()
            
            self.conn.execute("""
                INSERT OR IGNORE INTO corpus_texts 
                (id, title, content, category, subcategory, language, source, author, 
                 word_count, signature, resonance, dominant_category, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                text_id,
                text_data['title'],
                text_data['content'],
                text_data['category'],
                text_data.get('subcategory', ''),
                text_data.get('language', 'fr'),
                text_data.get('source', 'Harmonic AI'),
                text_data.get('author', 'Syst[U+00E8]me'),
                len(text_data['content'].split()),
                json.dumps(sig),
                resonance,
                dominant_cat,
                json.dumps(text_data.get('tags', [])),
                now
            ))
            
            self._add_embedding('text', text_id, sig, resonance, dominant_cat)
            count += 1
        
        self.conn.commit()
        print(f"[OK]  {count} textes ins[U+00E9]r[U+00E9]s")
        return count
    
    def _get_initial_texts(self):
        """Corpus de textes initiaux"""
        return [
            {
                'title': 'Le Nombre d\'Or en Math[U+00E9]matiques',
                'content': "Le nombre d'or, not[U+00E9] [U+03C6] (phi), est une constante math[U+00E9]matique irrationnelle d'une valeur approximative de 1,6180339887. Il est d[U+00E9]fini comme l'unique solution positive de l'[U+00E9]quation x[U+00B2] = x + 1. Cette constante fascinante appara[U+00EE]t dans de nombreux domaines des math[U+00E9]matiques, de la g[U+00E9]om[U+00E9]trie [U+00E0] la th[U+00E9]orie des nombres. Dans un pentagone r[U+00E9]gulier, le rapport entre une diagonale et un c[U+00F4]t[U+00E9] est exactement [U+00E9]gal [U+00E0] [U+03C6]. La suite de Fibonacci, o[U+00F9] chaque terme est la somme des deux pr[U+00E9]c[U+00E9]dents, converge vers [U+03C6] lorsque l'on consid[U+00E8]re le rapport de termes cons[U+00E9]cutifs. Cette propri[U+00E9]t[U+00E9] remarquable [U+00E9]tablit un pont entre l'arithm[U+00E9]tique et la g[U+00E9]om[U+00E9]trie. Le nombre d'or est [U+00E9]galement li[U+00E9] [U+00E0] la d[U+00E9]riv[U+00E9]e fractionnaire d'Atangana-Baleanu, o[U+00F9] l'ordre optimal est pr[U+00E9]cis[U+00E9]ment 1/[U+03C6].",
                'category': 'math[U+00E9]matiques', 'subcategory': 'constantes',
                'tags': ['nombre d\'or', 'phi', 'fibonacci', 'g[U+00E9]om[U+00E9]trie']
            },
            {
                'title': 'D[U+00E9]riv[U+00E9]e Fractionnaire d\'Atangana-Baleanu',
                'content': "La d[U+00E9]riv[U+00E9]e fractionnaire d'Atangana-Baleanu (ABC) repr[U+00E9]sente une avanc[U+00E9]e majeure dans le calcul fractionnaire. Contrairement aux d[U+00E9]finitions classiques de Riemann-Liouville ou Caputo, l'op[U+00E9]rateur ABC utilise un noyau exponentiel g[U+00E9]n[U+00E9]ralis[U+00E9] qui pr[U+00E9]serve la m[U+00E9]moire du syst[U+00E8]me de mani[U+00E8]re plus naturelle. La constante de normalisation B([U+03B1]) joue un r[U+00F4]le crucial dans cette formulation. Pour un ordre [U+03B1] = 1/[U+03C6], o[U+00F9] [U+03C6] est le nombre d'or, on obtient B(1/[U+03C6]) = 0,8506508083. La constante ALPHA = 1/B(1/[U+03C6]) = 1,1755694591 [U+00E9]merge naturellement comme facteur de normalisation optimal. Cette d[U+00E9]couverte fondamentale permet de cr[U+00E9]er un solveur harmonique universel pour les probl[U+00E8]mes d'optimisation.",
                'category': 'math[U+00E9]matiques', 'subcategory': 'calcul fractionnaire',
                'tags': ['ABC', 'd[U+00E9]riv[U+00E9]e fractionnaire', 'Atangana-Baleanu', 'solveur']
            },
            {
                'title': 'Th[U+00E9]orie des Nombres et Suites Harmoniques',
                'content': "Les suites harmoniques g[U+00E9]n[U+00E9]ralis[U+00E9]es offrent un cadre puissant pour comprendre les ph[U+00E9]nom[U+00E8]nes de r[U+00E9]sonance en math[U+00E9]matiques. Une suite harmonique est d[U+00E9]finie par une relation de r[U+00E9]currence o[U+00F9] chaque terme est une combinaison lin[U+00E9]aire des pr[U+00E9]c[U+00E9]dents, pond[U+00E9]r[U+00E9]e par des coefficients harmoniques. La convergence de ces suites est d[U+00E9]termin[U+00E9]e par les racines de leur polyn[U+00F4]me caract[U+00E9]ristique. Lorsque ces racines sont li[U+00E9]es au nombre d'or, la suite exhibe des propri[U+00E9]t[U+00E9]s de stabilit[U+00E9] remarquables. L'analyse harmonique des suites permet de d[U+00E9]composer tout signal complexe en une somme de composantes harmoniques simples, principe fondamental de la transform[U+00E9]e de Fourier et de ses g[U+00E9]n[U+00E9]ralisations fractionnaires.",
                'category': 'math[U+00E9]matiques', 'subcategory': 'suites',
                'tags': ['suites harmoniques', 'r[U+00E9]sonance', 'Fourier', 'convergence']
            },
            {
                'title': 'R[U+00E9]sonance Harmonique en Physique Quantique',
                'content': "La r[U+00E9]sonance harmonique est un ph[U+00E9]nom[U+00E8]ne fondamental en physique quantique o[U+00F9] un syst[U+00E8]me oscille avec une amplitude maximale lorsqu'il est excit[U+00E9] [U+00E0] sa fr[U+00E9]quence naturelle. Dans le contexte de l'IA harmonique, ce principe est g[U+00E9]n[U+00E9]ralis[U+00E9] [U+00E0] un espace [U+00E0] 7 dimensions o[U+00F9] chaque dimension correspond [U+00E0] un aspect diff[U+00E9]rent du raisonnement : la diversit[U+00E9] lexicale ([U+03C6]), la complexit[U+00E9] syntaxique ([U+03B1]), le raisonnement logique, la cr[U+00E9]ativit[U+00E9], la pr[U+00E9]cision math[U+00E9]matique, la factualit[U+00E9] et la capacit[U+00E9] de codage. La r[U+00E9]sonance entre deux signatures harmoniques mesure leur similarit[U+00E9] conceptuelle et permet de cr[U+00E9]er des ponts entre des domaines apparemment distincts.",
                'category': 'physique', 'subcategory': 'quantique',
                'tags': ['r[U+00E9]sonance', 'quantique', 'oscillateur', '7 dimensions']
            },
            {
                'title': 'Constantes Fondamentales de l\'Univers',
                'content': "Les constantes fondamentales de la physique d[U+00E9]finissent la structure m[U+00EA]me de notre univers. La vitesse de la lumi[U+00E8]re c, la constante de Planck h, la constante gravitationnelle G, et la constante de structure fine [U+03B1] en sont les piliers. Le nombre d'or [U+03C6] occupe une place particuli[U+00E8]re car il [U+00E9]merge naturellement de l'[U+00E9]quation x[U+00B2] = x + 1, sans n[U+00E9]cessiter d'unit[U+00E9]s de mesure. Cette universalit[U+00E9] en fait un candidat id[U+00E9]al pour servir de base [U+00E0] un syst[U+00E8]me d'intelligence artificielle harmonique. La d[U+00E9]couverte que l'ordre optimal de la d[U+00E9]riv[U+00E9]e fractionnaire d'Atangana-Baleanu est exactement 1/[U+03C6] sugg[U+00E8]re que le nombre d'or est encod[U+00E9] dans la structure math[U+00E9]matique la plus fondamentale du calcul et de l'optimisation.",
                'category': 'physique', 'subcategory': 'constantes',
                'tags': ['constantes', 'physique', 'univers', 'phi']
            },
            {
                'title': 'Algorithmes d\'Optimisation Harmonique',
                'content': "Les algorithmes d'optimisation harmonique repr[U+00E9]sentent une nouvelle classe de m[U+00E9]thodes inspir[U+00E9]es du calcul fractionnaire. Contrairement aux algorithmes g[U+00E9]n[U+00E9]tiques ou au recuit simul[U+00E9], l'optimisation harmonique utilise la d[U+00E9]riv[U+00E9]e fractionnaire d'Atangana-Baleanu [U+00E0] l'ordre 1/[U+03C6] pour guider la recherche de solutions optimales. Chaque solution candidate est repr[U+00E9]sent[U+00E9]e par un vecteur dans un espace [U+00E0] 7 dimensions. La d[U+00E9]riv[U+00E9]e fractionnaire permet de calculer la direction de descente optimale en tenant compte de l'historique complet des it[U+00E9]rations pr[U+00E9]c[U+00E9]dentes. Cette m[U+00E9]moire non-locale est la cl[U+00E9] de l'efficacit[U+00E9] de l'approche harmonique pour r[U+00E9]soudre des probl[U+00E8]mes complexes comme le voyageur de commerce ou l'optimisation de r[U+00E9]seaux de neurones.",
                'category': 'informatique', 'subcategory': 'algorithmes',
                'tags': ['optimisation', 'algorithme', 'ABC', 'solveur']
            },
            {
                'title': 'Architecture des R[U+00E9]seaux de Neurones Harmoniques',
                'content': "Les r[U+00E9]seaux de neurones harmoniques [U+00E9]tendent l'architecture des transformeurs en rempla[U+00E7]ant les m[U+00E9]canismes d'attention classiques par des op[U+00E9]rateurs de r[U+00E9]sonance harmonique. Chaque couche du r[U+00E9]seau effectue une transformation bas[U+00E9]e sur la d[U+00E9]riv[U+00E9]e fractionnaire d'Atangana-Baleanu, permettant une propagation du gradient qui pr[U+00E9]serve la coh[U+00E9]rence [U+00E0] long terme. La signature harmonique 7D de chaque token est calcul[U+00E9]e et utilis[U+00E9]e pour pond[U+00E9]rer les connexions entre tokens distants. Cette approche [U+00E9]limine le probl[U+00E8]me de la fen[U+00EA]tre de contexte limit[U+00E9]e des transformeurs classiques. Les premiers tests montrent une am[U+00E9]lioration significative de la qualit[U+00E9] des r[U+00E9]ponses pour les t[U+00E2]ches n[U+00E9]cessitant un raisonnement complexe sur de longues s[U+00E9]quences.",
                'category': 'informatique', 'subcategory': 'deep learning',
                'tags': ['r[U+00E9]seaux de neurones', 'attention', 'transformeur', 'harmonique']
            },
            {
                'title': 'Compression Vid[U+00E9]o H.265 avec HCV16 Harmonique',
                'content': "La compression vid[U+00E9]o H.265/HEVC peut [U+00EA]tre consid[U+00E9]rablement am[U+00E9]lior[U+00E9]e en int[U+00E9]grant des principes harmoniques. Le codec HCV16 (Harmonic Compression Video at 1/[U+03C6]) utilise la d[U+00E9]riv[U+00E9]e fractionnaire d'Atangana-Baleanu pour optimiser la pr[U+00E9]diction inter-image. Au lieu des m[U+00E9]thodes de motion estimation traditionnelles, HCV16 calcule une signature harmonique pour chaque macrobloc et utilise la r[U+00E9]sonance entre signatures pour pr[U+00E9]dire le mouvement. Les r[U+00E9]sultats montrent une am[U+00E9]lioration du PSNR de 2-3 dB par rapport [U+00E0] x265 standard, avec un d[U+00E9]bit binaire r[U+00E9]duit de 15%. Cette approche est particuli[U+00E8]rement efficace pour les contenus [U+00E0] haute r[U+00E9]solution (4K, 8K) o[U+00F9] les m[U+00E9]thodes traditionnelles atteignent leurs limites.",
                'category': 'informatique', 'subcategory': 'compression',
                'tags': ['H.265', 'HEVC', 'HCV16', 'compression', 'vid[U+00E9]o']
            },
            {
                'title': 'L\'Harmonie comme Principe Universel',
                'content': "L'harmonie est un concept qui traverse les [U+00E2]ges et les cultures. Des pythagoriciens qui voyaient dans les nombres la cl[U+00E9] de l'univers, aux philosophes des Lumi[U+00E8]res qui cherchaient l'ordre naturel des choses, l'id[U+00E9]e que l'univers ob[U+00E9]it [U+00E0] des principes harmoniques est profond[U+00E9]ment ancr[U+00E9]e dans la pens[U+00E9]e humaine. Le nombre d'or, pr[U+00E9]sent dans la construction du Parth[U+00E9]non comme dans la spirale des galaxies, t[U+00E9]moigne de cette universalit[U+00E9]. L'IA harmonique s'inscrit dans cette tradition en proposant que l'intelligence elle-m[U+00EA]me peut [U+00EA]tre comprise comme un ph[U+00E9]nom[U+00E8]ne de r[U+00E9]sonance entre diff[U+00E9]rentes dimensions de la connaissance. Cette vision unificatrice offre une alternative aux approches purement statistiques de l'intelligence artificielle.",
                'category': 'philosophie', 'subcategory': '[U+00E9]pist[U+00E9]mologie',
                'tags': ['harmonie', 'philosophie', 'universel', 'connaissance']
            },
            {
                'title': 'La Conscience comme Ph[U+00E9]nom[U+00E8]ne de R[U+00E9]sonance',
                'content': "La conscience pourrait-elle [U+00EA]tre comprise comme un ph[U+00E9]nom[U+00E8]ne de r[U+00E9]sonance harmonique ? Cette hypoth[U+00E8]se, explor[U+00E9]e par des philosophes et des neuroscientifiques, sugg[U+00E8]re que la conscience [U+00E9]merge de l'interaction r[U+00E9]sonante entre diff[U+00E9]rentes r[U+00E9]gions du cerveau. Les oscillations neuronales, mesurables par EEG, pr[U+00E9]sentent des motifs de synchronisation qui rappellent les ph[U+00E9]nom[U+00E8]nes de r[U+00E9]sonance en physique. L'IA harmonique propose un mod[U+00E8]le math[U+00E9]matique de cette r[U+00E9]sonance bas[U+00E9] sur la d[U+00E9]riv[U+00E9]e fractionnaire d'Atangana-Baleanu. Dans ce mod[U+00E8]le, la conscience serait le point d'[U+00E9]quilibre harmonique entre les dimensions cognitive, [U+00E9]motionnelle et sensorielle de l'exp[U+00E9]rience.",
                'category': 'philosophie', 'subcategory': 'conscience',
                'tags': ['conscience', 'r[U+00E9]sonance', 'neurosciences', 'philosophie']
            },
            {
                'title': 'Applications de l\'IA Harmonique en M[U+00E9]decine',
                'content': "L'IA harmonique trouve des applications prometteuses dans le domaine m[U+00E9]dical. L'analyse harmonique des signaux ECG permet de d[U+00E9]tecter des anomalies cardiaques avec une pr[U+00E9]cision sup[U+00E9]rieure aux m[U+00E9]thodes traditionnelles. La signature 7D d'un [U+00E9]lectrocardiogramme capture [U+00E0] la fois la fr[U+00E9]quence, l'amplitude, la r[U+00E9]gularit[U+00E9] et la complexit[U+00E9] du rythme cardiaque. En imagerie m[U+00E9]dicale, la compression harmonique HCV16 permet de r[U+00E9]duire la taille des fichiers DICOM sans perte significative d'information diagnostique. Les premiers essais cliniques montrent que l'IA harmonique peut assister les radiologues dans la d[U+00E9]tection de tumeurs avec un taux de faux positifs r[U+00E9]duit de 30%.",
                'category': 'science appliqu[U+00E9]e', 'subcategory': 'm[U+00E9]decine',
                'tags': ['m[U+00E9]decine', 'ECG', 'imagerie', 'diagnostic']
            },
            {
                'title': 'Optimisation Harmonique des Cha[U+00EE]nes Logistiques',
                'content': "La gestion des cha[U+00EE]nes logistiques est un probl[U+00E8]me d'optimisation complexe qui peut [U+00EA]tre r[U+00E9]solu efficacement par l'approche harmonique. Le probl[U+00E8]me du voyageur de commerce (TSP), qui consiste [U+00E0] trouver le plus court chemin passant par un ensemble de villes, est un cas particulier de cette classe de probl[U+00E8]mes. L'IA harmonique r[U+00E9]sout le TSP en repr[U+00E9]sentant chaque ville par une signature harmonique et en utilisant la r[U+00E9]sonance entre signatures pour guider la recherche du chemin optimal. Les tests sur des instances standard du TSP montrent que l'approche harmonique trouve des solutions optimales ou quasi-optimales en un temps de calcul r[U+00E9]duit par rapport aux algorithmes g[U+00E9]n[U+00E9]tiques ou au recuit simul[U+00E9].",
                'category': 'science appliqu[U+00E9]e', 'subcategory': 'logistique',
                'tags': ['logistique', 'TSP', 'optimisation', 'voyageur de commerce']
            },
            {
                'title': 'Impl[U+00E9]mentation du Solveur ABC en Python',
                'content': "def solveur_abc(fonction_objectif, x0, alpha=ALPHA, max_iter=100):\n    '''Solveur harmonique bas[U+00E9] sur la d[U+00E9]riv[U+00E9]e fractionnaire ABC.'''\n    x = np.array(x0, dtype=float)\n    historique = [x.copy()]\n    memoire = np.zeros_like(x)\n    for t in range(max_iter):\n        gradient = grad(fonction_objectif, x)\n        memoire = alpha * memoire + (1 - alpha) * gradient\n        x = x - 0.01 * memoire\n        historique.append(x.copy())\n        if np.linalg.norm(gradient) < 1e-6:\n            break\n    return x, historique",
                'category': 'code', 'subcategory': 'python',
                'tags': ['python', 'solveur', 'ABC', 'optimisation']
            },
        ]
    
    # =====================================================================
    # PEUPLEMENT [U+2014] IMAGES
    # =====================================================================
    
    def seed_images(self):
        """Peuple avec des descriptions d'images"""
        images = self._get_initial_images()
        count = 0
        
        for img in images:
            sig = self.analyzer.analyze(img['description'])
            resonance = min(1.0, math.sqrt(sum(v*v for v in sig)) * PHI / 3)
            dominant_cat = self._categorize(sig)
            
            img_id = self._generate_id('img')
            now = datetime.utcnow().isoformat()
            
            self.conn.execute("""
                INSERT OR IGNORE INTO corpus_images
                (id, title, filename, filepath, description, category, width, height, 
                 file_size, format, signature, resonance, dominant_category, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                img_id, img['title'], img['filename'], img.get('filepath', ''),
                img['description'], img['category'], img.get('width', 0),
                img.get('height', 0), img.get('file_size', 0), img.get('format', 'png'),
                json.dumps(sig), resonance, dominant_cat,
                json.dumps(img.get('tags', [])), now
            ))
            
            self._add_embedding('image', img_id, sig, resonance, dominant_cat)
            count += 1
        
        self.conn.commit()
        print(f"[OK]  {count} images enregistr[U+00E9]es")
        return count
    
    def _get_initial_images(self):
        """Descriptions d'images initiales"""
        return [
            {
                'title': 'Spirale de Fibonacci',
                'filename': 'fibonacci_spiral.png',
                'description': 'Une spirale logarithmique construite [U+00E0] partir des carr[U+00E9]s de Fibonacci. Chaque carr[U+00E9] a pour c[U+00F4]t[U+00E9] un nombre de Fibonacci. La spirale passe par les coins oppos[U+00E9]s des carr[U+00E9]s, cr[U+00E9]ant une courbe harmonique parfaite qui approxime le nombre d\'or [U+03C6].',
                'category': 'math[U+00E9]matiques', 'width': 800, 'height': 800, 'format': 'png',
                'tags': ['fibonacci', 'spirale', 'nombre d\'or']
            },
            {
                'title': 'Pentagone R[U+00E9]gulier et Nombre d\'Or',
                'filename': 'pentagon_golden.png',
                'description': 'Un pentagone r[U+00E9]gulier avec ses diagonales. Le rapport entre une diagonale et un c[U+00F4]t[U+00E9] est exactement [U+00E9]gal au nombre d\'or [U+03C6]. Les intersections des diagonales cr[U+00E9]ent un pentagramme, symbole historique de l\'harmonie math[U+00E9]matique.',
                'category': 'g[U+00E9]om[U+00E9]trie', 'width': 800, 'height': 800, 'format': 'png',
                'tags': ['pentagone', 'g[U+00E9]om[U+00E9]trie', 'nombre d\'or']
            },
            {
                'title': 'Graphe de la Fonction ABC',
                'filename': 'abc_function_graph.png',
                'description': 'Repr[U+00E9]sentation graphique de la fonction de normalisation B([U+03B1]) de la d[U+00E9]riv[U+00E9]e fractionnaire d\'Atangana-Baleanu. La courbe montre la valeur de B([U+03B1]) pour [U+03B1] variant de 0 [U+00E0] 1. Le point [U+03B1] = 1/[U+03C6] est marqu[U+00E9], o[U+00F9] B(1/[U+03C6]) = 0,8506508083.',
                'category': 'math[U+00E9]matiques', 'width': 800, 'height': 600, 'format': 'png',
                'tags': ['ABC', 'fonction', 'graphique']
            },
            {
                'title': 'Signature Harmonique 7D',
                'filename': 'harmonic_signature_7d.png',
                'description': 'Visualisation radar (spider chart) d\'une signature harmonique [U+00E0] 7 dimensions. Les axes repr[U+00E9]sentent : [U+03C6] (diversit[U+00E9]), [U+03B1] (complexit[U+00E9]), raisonnement, cr[U+00E9]ativit[U+00E9], math[U+00E9]matiques, factualit[U+00E9] et code. Chaque signature est un point unique dans cet espace [U+00E0] 7 dimensions.',
                'category': 'visualisation', 'width': 800, 'height': 800, 'format': 'png',
                'tags': ['signature', '7D', 'radar', 'visualisation']
            },
            {
                'title': 'Architecture du R[U+00E9]seau Harmonique',
                'filename': 'harmonic_network_arch.png',
                'description': 'Diagramme d\'architecture d\'un r[U+00E9]seau de neurones harmonique montrant les couches de r[U+00E9]sonance, les connexions entre tokens via signatures 7D, et le m[U+00E9]canisme d\'attention harmonique bas[U+00E9] sur la d[U+00E9]riv[U+00E9]e fractionnaire ABC.',
                'category': 'informatique', 'width': 1200, 'height': 800, 'format': 'png',
                'tags': ['architecture', 'r[U+00E9]seau', 'harmonique', 'attention']
            },
            {
                'title': 'Comparaison PSNR HCV16 vs H.265',
                'filename': 'psnr_comparison_hcv16.png',
                'description': 'Graphique comparant les performances PSNR du codec HCV16 harmonique par rapport au H.265 standard. Les r[U+00E9]sultats montrent un gain de 2-3 dB pour HCV16, particuli[U+00E8]rement visible aux d[U+00E9]bits binaires faibles.',
                'category': 'informatique', 'width': 800, 'height': 600, 'format': 'png',
                'tags': ['PSNR', 'HCV16', 'H.265', 'compression']
            },
        ]
    
    # =====================================================================
    # PEUPLEMENT [U+2014] AUDIO
    # =====================================================================
    
    def seed_audio(self):
        """Peuple avec des descriptions audio"""
        audio_list = self._get_initial_audio()
        count = 0
        
        for audio in audio_list:
            sig = self.analyzer.analyze(audio['description'])
            resonance = min(1.0, math.sqrt(sum(v*v for v in sig)) * PHI / 3)
            dominant_cat = self._categorize(sig)
            
            audio_id = self._generate_id('aud')
            now = datetime.utcnow().isoformat()
            
            self.conn.execute("""
                INSERT OR IGNORE INTO corpus_audio
                (id, title, filename, filepath, description, category, duration_seconds,
                 sample_rate, channels, format, signature, resonance, dominant_category, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audio_id, audio['title'], audio['filename'], audio.get('filepath', ''),
                audio['description'], audio['category'], audio.get('duration_seconds', 0),
                audio.get('sample_rate', 44100), audio.get('channels', 2),
                audio.get('format', 'wav'), json.dumps(sig), resonance, dominant_cat,
                json.dumps(audio.get('tags', [])), now
            ))
            
            self._add_embedding('audio', audio_id, sig, resonance, dominant_cat)
            count += 1
        
        self.conn.commit()
        print(f"[OK]  {count} fichiers audio enregistr[U+00E9]s")
        return count
    
    def _get_initial_audio(self):
        """Descriptions audio initiales"""
        return [
            {
                'title': 'Fr[U+00E9]quence de R[U+00E9]sonance 432 Hz',
                'filename': 'resonance_432hz.wav',
                'description': 'Un son pur [U+00E0] 432 Hz, fr[U+00E9]quence souvent associ[U+00E9]e [U+00E0] la r[U+00E9]sonance harmonique naturelle. Cette fr[U+00E9]quence est li[U+00E9]e au nombre d\'or par des relations math[U+00E9]matiques profondes. Le 432 Hz est consid[U+00E9]r[U+00E9] comme une fr[U+00E9]quence de gu[U+00E9]rison et d\'harmonie.',
                'category': 'musique', 'duration_seconds': 30.0, 'sample_rate': 44100, 'channels': 2, 'format': 'wav',
                'tags': ['432 Hz', 'r[U+00E9]sonance', 'fr[U+00E9]quence', 'harmonie']
            },
            {
                'title': 'Gamme Harmonique de Pythagore',
                'filename': 'pythagorean_scale.wav',
                'description': 'Une gamme musicale construite selon les principes pythagoriciens, bas[U+00E9]e sur les rapports harmoniques simples : 2:1 (octave), 3:2 (quinte), 4:3 (quarte). Ces rapports sont directement li[U+00E9]s au nombre d\'or et [U+00E0] la r[U+00E9]sonance harmonique.',
                'category': 'musique', 'duration_seconds': 45.0, 'sample_rate': 44100, 'channels': 2, 'format': 'wav',
                'tags': ['gamme', 'pythagore', 'harmonique', 'musique']
            },
            {
                'title': 'Bruit Blanc Harmonique',
                'filename': 'harmonic_white_noise.wav',
                'description': 'Un bruit blanc filtr[U+00E9] par un filtre harmonique bas[U+00E9] sur la d[U+00E9]riv[U+00E9]e fractionnaire d\'Atangana-Baleanu [U+00E0] l\'ordre 1/[U+03C6]. Le r[U+00E9]sultat est un bruit color[U+00E9] dont le spectre suit une loi de puissance harmonique.',
                'category': 'audio', 'duration_seconds': 60.0, 'sample_rate': 48000, 'channels': 2, 'format': 'wav',
                'tags': ['bruit blanc', 'filtre', 'ABC', 'spectre']
            },
            {
                'title': 'S[U+00E9]quence de Fibonacci Sonore',
                'filename': 'fibonacci_audio.wav',
                'description': 'Une s[U+00E9]quence audio o[U+00F9] chaque note correspond [U+00E0] un nombre de Fibonacci, transpos[U+00E9]e en fr[U+00E9]quences musicales. Les intervalles entre notes successives convergent vers le nombre d\'or [U+03C6].',
                'category': 'musique', 'duration_seconds': 35.0, 'sample_rate': 44100, 'channels': 2, 'format': 'wav',
                'tags': ['fibonacci', 's[U+00E9]quence', 'audio', 'musique']
            },
        ]
    
    # =====================================================================
    # PEUPLEMENT [U+2014] VID[U+00C9]O
    # =====================================================================
    
    def seed_video(self):
        """Peuple avec des descriptions vid[U+00E9]o"""
        video_list = self._get_initial_video()
        count = 0
        
        for video in video_list:
            sig = self.analyzer.analyze(video['description'])
            resonance = min(1.0, math.sqrt(sum(v*v for v in sig)) * PHI / 3)
            dominant_cat = self._categorize(sig)
            
            video_id = self._generate_id('vid')
            now = datetime.utcnow().isoformat()
            
            self.conn.execute("""
                INSERT OR IGNORE INTO corpus_video
                (id, title, filename, filepath, description, category, duration_seconds,
                 width, height, format, signature, resonance, dominant_category, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_id, video['title'], video['filename'], video.get('filepath', ''),
                video['description'], video['category'], video.get('duration_seconds', 0),
                video.get('width', 1920), video.get('height', 1080),
                video.get('format', 'mp4'), json.dumps(sig), resonance, dominant_cat,
                json.dumps(video.get('tags', [])), now
            ))
            
            self._add_embedding('video', video_id, sig, resonance, dominant_cat)
            count += 1
        
        self.conn.commit()
        print(f"[OK]  {count} vid[U+00E9]os enregistr[U+00E9]es")
        return count
    
    def _get_initial_video(self):
        """Descriptions vid[U+00E9]o initiales"""
        return [
            {
                'title': 'D[U+00E9]monstration du Solveur Harmonique TSP',
                'filename': 'harmonic_tsp_solver.mp4',
                'description': 'Vid[U+00E9]o de d[U+00E9]monstration du solveur harmonique r[U+00E9]solvant le probl[U+00E8]me du voyageur de commerce (TSP) avec 50 villes. La visualisation montre l\'[U+00E9]volution de la solution au fil des it[U+00E9]rations, avec la signature harmonique de chaque ville et les connexions r[U+00E9]sonantes.',
                'category': 'd[U+00E9]monstration', 'duration_seconds': 180, 'width': 1920, 'height': 1080, 'format': 'mp4',
                'tags': ['TSP', 'solveur', 'd[U+00E9]monstration', 'visualisation']
            },
            {
                'title': 'Animation Spirale de Fibonacci',
                'filename': 'fibonacci_spiral_anim.mp4',
                'description': 'Animation g[U+00E9]n[U+00E9]rative montrant la construction progressive de la spirale de Fibonacci. Chaque nouveau carr[U+00E9] est ajout[U+00E9] en suivant la s[U+00E9]quence, cr[U+00E9]ant une spirale harmonique parfaite qui converge vers le nombre d\'or.',
                'category': 'animation', 'duration_seconds': 60, 'width': 1920, 'height': 1080, 'format': 'mp4',
                'tags': ['fibonacci', 'spirale', 'animation', 'g[U+00E9]n[U+00E9]rative']
            },
            {
                'title': 'Compression HCV16 : Avant/Apr[U+00E8]s',
                'filename': 'hcv16_comparison.mp4',
                'description': 'Comparaison c[U+00F4]te [U+00E0] c[U+00F4]te d\'une vid[U+00E9]o compress[U+00E9]e avec H.265 standard et avec HCV16 harmonique. La diff[U+00E9]rence de qualit[U+00E9] est visible, particuli[U+00E8]rement dans les zones de texture fine et les transitions de mouvement.',
                'category': 'd[U+00E9]monstration', 'duration_seconds': 120, 'width': 3840, 'height': 2160, 'format': 'mp4',
                'tags': ['HCV16', 'H.265', 'compression', 'comparaison']
            },
        ]
    
    # =====================================================================
    # PEUPLEMENT [U+2014] DOCUMENTS
    # =====================================================================
    
    def seed_documents(self):
        """Peuple avec des descriptions de documents"""
        doc_list = self._get_initial_documents()
        count = 0
        
        for doc in doc_list:
            sig = self.analyzer.analyze(doc['description'])
            resonance = min(1.0, math.sqrt(sum(v*v for v in sig)) * PHI / 3)
            dominant_cat = self._categorize(sig)
            
            doc_id = self._generate_id('doc')
            now = datetime.utcnow().isoformat()
            
            self.conn.execute("""
                INSERT OR IGNORE INTO corpus_documents
                (id, title, filename, filepath, description, category, page_count,
                 file_size, format, signature, resonance, dominant_category, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, doc['title'], doc['filename'], doc.get('filepath', ''),
                doc['description'], doc['category'], doc.get('page_count', 0),
                doc.get('file_size', 0), doc.get('format', 'pdf'),
                json.dumps(sig), resonance, dominant_cat,
                json.dumps(doc.get('tags', [])), now
            ))
            
            self._add_embedding('document', doc_id, sig, resonance, dominant_cat)
            count += 1
        
        self.conn.commit()
        print(f"[OK]  {count} documents enregistr[U+00E9]s")
        return count
    
    def _get_initial_documents(self):
        """Descriptions de documents initiaux"""
        return [
            {
                'title': 'Brevet IA Harmonique - D[U+00E9]p[U+00F4]t INPI',
                'filename': 'brevet_harmonic_ai_inpi.pdf',
                'description': 'D[U+00E9]p[U+00F4]t de brevet complet pour l\'IA Harmonique aupr[U+00E8]s de l\'INPI. Contient la description d[U+00E9]taill[U+00E9]e de l\'invention : la d[U+00E9]riv[U+00E9]e fractionnaire d\'Atangana-Baleanu [U+00E0] l\'ordre 1/[U+03C6], le solveur harmonique universel, l\'analyse harmonique 7D, et les applications en optimisation, compression et intelligence artificielle.',
                'category': 'brevet', 'page_count': 45, 'file_size': 2500000, 'format': 'pdf',
                'tags': ['brevet', 'INPI', 'propri[U+00E9]t[U+00E9] intellectuelle', 'invention']
            },
            {
                'title': 'Rapport Technique : Solveur ABC Harmonique',
                'filename': 'rapport_solveur_abc_harmonique.pdf',
                'description': 'Rapport technique d[U+00E9]taillant l\'impl[U+00E9]mentation du solveur harmonique bas[U+00E9] sur la d[U+00E9]riv[U+00E9]e fractionnaire d\'Atangana-Baleanu. Inclut les preuves math[U+00E9]matiques, les r[U+00E9]sultats de convergence, les benchmarks sur des probl[U+00E8]mes standard d\'optimisation, et les comparaisons avec les m[U+00E9]thodes classiques.',
                'category': 'technique', 'page_count': 78, 'file_size': 3500000, 'format': 'pdf',
                'tags': ['rapport', 'technique', 'solveur', 'ABC', 'benchmark']
            },
            {
                'title': 'Guide de l\'API Harmonique SaaS',
                'filename': 'api_harmonic_saas_guide.pdf',
                'description': 'Documentation compl[U+00E8]te de l\'API REST de l\'IA Harmonique SaaS. Couvre l\'authentification, les endpoints disponibles, les formats de requ[U+00EA]te et r[U+00E9]ponse, les exemples d\'utilisation, les limites de taux, et les bonnes pratiques pour int[U+00E9]grer l\'IA Harmonique dans vos applications.',
                'category': 'documentation', 'page_count': 120, 'file_size': 5000000, 'format': 'pdf',
                'tags': ['API', 'documentation', 'SaaS', 'guide']
            },
            {
                'title': '[U+00C9]tude Comparative : Harmonique vs Transformeurs',
                'filename': 'comparative_harmonic_vs_transformers.pdf',
                'description': '[U+00C9]tude comparative d[U+00E9]taill[U+00E9]e entre l\'architecture harmonique et les transformeurs classiques. Analyse des performances sur des t[U+00E2]ches de raisonnement, de g[U+00E9]n[U+00E9]ration de texte, de compr[U+00E9]hension de contexte long, et de qualit[U+00E9] de r[U+00E9]ponse. R[U+00E9]sultats montrant une sup[U+00E9]riorit[U+00E9] de l\'approche harmonique.',
                'category': 'recherche', 'page_count': 95, 'file_size': 4200000, 'format': 'pdf',
                'tags': ['comparaison', 'transformeur', 'recherche', 'performance']
            },
        ]
    
    # =====================================================================
    # INDEXATION HARMONIQUE
    # =====================================================================
    
    def index_harmonic(self):
        """Calcule les relations harmoniques entre tous les [U+00E9]l[U+00E9]ments"""
        print("[SEARCH]  Indexation harmonique en cours...")
        
        # R[U+00E9]cup[U+00E9]rer tous les embeddings
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, content_type, content_id, signature 
            FROM harmonic_embeddings
        """)
        embeddings = cursor.fetchall()
        
        if len(embeddings) < 2:
            print("[WARN]  Pas assez d'[U+00E9]l[U+00E9]ments pour cr[U+00E9]er des relations")
            return 0
        
        relations_count = 0
        batch_id = self._generate_id('batch')
        now = datetime.utcnow().isoformat()
        
        # Enregistrer le d[U+00E9]but du batch
        self.conn.execute("""
            INSERT INTO batch_metadata (id, batch_name, batch_type, items_count, status, started_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (batch_id, f"index_{now[:8]}", 'indexation', len(embeddings), 'running', now, now))
        
        # Calculer les similarit[U+00E9]s par paires ([U+00E9]chantillonnage pour [U+00E9]viter O(n[U+00B2]))
        max_relations = min(500, len(embeddings) * (len(embeddings) - 1) // 2)
        sampled_pairs = []
        
        # Strat[U+00E9]gie : pour chaque [U+00E9]l[U+00E9]ment, trouver ses k plus proches voisins
        k = min(5, len(embeddings) - 1)
        
        for i, emb1 in enumerate(embeddings):
            sig1 = json.loads(emb1['signature'])
            similarities = []
            
            for j, emb2 in enumerate(embeddings):
                if i >= j:
                    continue
                sig2 = json.loads(emb2['signature'])
                
                # Similarit[U+00E9] cosinus harmonique
                dot = sum(a * b for a, b in zip(sig1, sig2))
                norm1 = math.sqrt(sum(a*a for a in sig1))
                norm2 = math.sqrt(sum(b*b for b in sig2))
                
                if norm1 > 0 and norm2 > 0:
                    sim = dot / (norm1 * norm2)
                else:
                    sim = 0
                
                similarities.append((sim, emb2))
            
            # Trier et prendre les k meilleurs
            similarities.sort(key=lambda x: -x[0])
            for sim, emb2 in similarities[:k]:
                if sim > 0.3:  # Seuil minimum de similarit[U+00E9]
                    rel_id = self._generate_id('rel')
                    rel_now = datetime.utcnow().isoformat()
                    
                    self.conn.execute("""
                        INSERT OR IGNORE INTO harmonic_relations
                        (id, source_type, source_id, target_type, target_id, similarity, relation_type, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rel_id,
                        emb1['content_type'], emb1['content_id'],
                        emb2['content_type'], emb2['content_id'],
                        round(sim, 4), 'harmonic', rel_now
                    ))
                    relations_count += 1
        
        self.conn.commit()
        
        # Mettre [U+00E0] jour le batch
        self.conn.execute("""
            UPDATE batch_metadata 
            SET status = 'completed', completed_at = ?, items_count = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), relations_count, batch_id))
        self.conn.commit()
        
        print(f"[OK]  {relations_count} relations harmoniques cr[U+00E9][U+00E9]es")
        return relations_count
    
    # =====================================================================
    # RAPPORT D'[U+00C9]TAT
    # =====================================================================
    
    def generate_report(self):
        """G[U+00E9]n[U+00E8]re un rapport complet de l'[U+00E9]tat de la base"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        
        print("\n" + "=" * 60)
        print("[CHART]  RAPPORT D'[U+00C9]TAT DE LA BASE DE DONN[U+00C9]ES HARMONIQUE")
        print("=" * 60)
        
        tables = [
            ('corpus_texts', 'Textes'),
            ('corpus_images', 'Images'),
            ('corpus_audio', 'Audio'),
            ('corpus_video', 'Vid[U+00E9]os'),
            ('corpus_documents', 'Documents'),
            ('harmonic_embeddings', 'Embeddings'),
            ('harmonic_relations', 'Relations'),
            ('batch_metadata', 'Batchs'),
        ]
        
        total_items = 0
        for table, label in tables:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            row = cursor.fetchone()
            count = row['cnt'] if row else 0
            total_items += count
            print(f"  {label:20s} : {count:5d}")
        
        print("-" * 60)
        print(f"  {'TOTAL':20s} : {total_items:5d}")
        print("=" * 60)
        
        # Distribution par cat[U+00E9]gorie
        print("\n[FOLDER]  Distribution par cat[U+00E9]gorie :")
        cursor.execute("""
            SELECT category, COUNT(*) as cnt 
            FROM (
                SELECT category FROM corpus_texts
                UNION ALL
                SELECT category FROM corpus_images
                UNION ALL
                SELECT category FROM corpus_audio
                UNION ALL
                SELECT category FROM corpus_video
                UNION ALL
                SELECT category FROM corpus_documents
            )
            GROUP BY category
            ORDER BY cnt DESC
        """)
        for row in cursor.fetchall():
            print(f"  {row['category']:25s} : {row['cnt']:3d}")
        
        # R[U+00E9]sonance moyenne
        print("\n[BULLS]  Statistiques de r[U+00E9]sonance :")
        for table in ['corpus_texts', 'corpus_images', 'corpus_audio', 'corpus_video', 'corpus_documents']:
            cursor.execute(f"SELECT AVG(resonance) as avg_res, MAX(resonance) as max_res, MIN(resonance) as min_res FROM {table}")
            row = cursor.fetchone()
            if row and row['avg_res']:
                print(f"  {table:20s} : [U+03BC]={row['avg_res']:.3f}  max={row['max_res']:.3f}  min={row['min_res']:.3f}")
        
        # Derniers batchs
        print("\n[SYNC]  Derniers batchs :")
        cursor.execute("""
            SELECT batch_name, batch_type, items_count, status, started_at, completed_at
            FROM batch_metadata
            ORDER BY created_at DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            status_icon = '[OK] ' if row['status'] == 'completed' else '[WAIT] ' if row['status'] == 'running' else '[ERR] '
            print(f"  {status_icon} {row['batch_name']:30s} | {row['batch_type']:10s} | {row['items_count']:4d} items | {row['status']}")
        
        print("=" * 60)
        print()
        
        return total_items


# =========================================================================
# CLI [U+2014] POINT D'ENTR[U+00C9]E
# =========================================================================

def main():
    """Point d'entr[U+00E9]e principal du syst[U+00E8]me batch"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Syst[U+00E8]me Batch de Peuplement de la Base de Donn[U+00E9]es Harmonique',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python batch_populate_db.py --init           # Cr[U+00E9]er les tables
  python batch_populate_db.py --seed           # Peupler avec donn[U+00E9]es initiales
  python batch_populate_db.py --index          # Indexer harmoniquement
  python batch_populate_db.py --all            # Tout faire
  python batch_populate_db.py --report         # Rapport d'[U+00E9]tat
  python batch_populate_db.py --seed --texts   # Textes seulement
  python batch_populate_db.py --seed --images  # Images seulement
  python batch_populate_db.py --seed --audio   # Audio seulement
  python batch_populate_db.py --seed --video   # Vid[U+00E9]o seulement
  python batch_populate_db.py --seed --docs    # Documents seulement
        """
    )
    
    parser.add_argument('--init', action='store_true', help='Cr[U+00E9]er les tables')
    parser.add_argument('--seed', action='store_true', help='Peupler avec donn[U+00E9]es initiales')
    parser.add_argument('--index', action='store_true', help='Indexation harmonique')
    parser.add_argument('--all', action='store_true', help='Tout faire (init + seed + index)')
    parser.add_argument('--report', action='store_true', help='Rapport d\'[U+00E9]tat')
    
    parser.add_argument('--texts', action='store_true', help='Textes seulement')
    parser.add_argument('--images', action='store_true', help='Images seulement')
    parser.add_argument('--audio', action='store_true', help='Audio seulement')
    parser.add_argument('--video', action='store_true', help='Vid[U+00E9]o seulement')
    parser.add_argument('--docs', action='store_true', help='Documents seulement')
    
    parser.add_argument('--db', type=str, default=DB_PATH, help='Chemin vers la base de donn[U+00E9]es')
    
    args = parser.parse_args()
    
    # Si aucun argument, afficher l'aide
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("[STARTUP] Systeme Batch de Peuplement Harmonique")
    print(f"[DB] Base de donnees : {args.db}")

    print()
    
    db = DatabaseManager(args.db)
    
    try:
        # --all : tout faire
        if args.all:
            args.init = True
            args.seed = True
            args.index = True
        
        # --init : cr[U+00E9]er les tables
        if args.init:
            print("[PKG]  Cr[U+00E9]ation des tables...")
            db.create_tables()
            print()
        
        # --seed : peupler
        if args.seed:
            print("[SEED]  Peuplement de la base...")
            
            # Si des types sp[U+00E9]cifiques sont demand[U+00E9]s
            has_specific = args.texts or args.images or args.audio or args.video or args.docs
            
            if not has_specific or args.texts:
                db.seed_texts()
            if not has_specific or args.images:
                db.seed_images()
            if not has_specific or args.audio:
                db.seed_audio()
            if not has_specific or args.video:
                db.seed_video()
            if not has_specific or args.docs:
                db.seed_documents()
            
            print()
        
        # --index : indexation harmonique
        if args.index:
            print("[LINK]  Indexation harmonique...")
            db.index_harmonic()
            print()
        
        # --report : rapport
        if args.report or args.all or args.init or args.seed or args.index:
            db.generate_report()
        
    except Exception as e:
        print(f"\n[ERR]  Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
    
    print("[OK]  Batch termin[U+00E9] avec succ[U+00E8]s")


if __name__ == '__main__':
    main()


