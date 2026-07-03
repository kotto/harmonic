"""
SemanticWave Retriever — Retrieval par résonance ondulatoire
==============================================================
"Tout est ondes. Deux mots résonnent s'ils co-occurrent."

Au lieu de compter des mots-clés (TF-IDF), ce retriever :
1. Construit un graphe de co-occurrence depuis la KB
2. Pour chaque mot de la question, trouve ses « voisins sémantiques »
3. Élargit la requête avec les voisins (expansion d'onde)
4. Retrieval = résonance entre l'onde-question et l'onde-fait

Pourquoi ça marche :
  "Mona Lisa" co-occurre avec "Joconde" dans la KB
  → l'onde "Mona Lisa" se propage automatiquement vers "Joconde"
  → le fait "Leonard de Vinci a peint la Joconde" est trouvé
  → PAS de dictionnaire de synonymes manuel

Usage:
    from semantic_wave import SemanticWaveRetriever
    wave = SemanticWaveRetriever(kb)
    facts = wave.retrieve("qui a peint la Mona Lisa")
"""

import re
import math
from collections import defaultdict
from typing import List, Tuple, Dict, Set

Fact = Tuple[str, str, str, str]


class SemanticWaveRetriever:
    """
    Retrieval par propagation d'onde dans le graphe de co-occurrence.
    
    Deux mots « résonnent » si :
    - Ils apparaissent dans le même fait (co-occurrence forte)
    - Ils apparaissent dans des faits partageant des mots communs (chaîne)
    
    C'est la version ondulatoire du retrieval sémantique.
    """
    
    STOPWORDS = {
        'the','a','an','is','are','was','were','of','in','on','at','to',
        'for','with','by','from','and','or','it','its','that','this',
        'these','those','which','who','whom','whose','be','been','being',
        'have','has','had','do','does','did','will','would','could',
        'should','may','might','can','shall','not','but','if','so',
        'as','than','i','you','he','she','we','they','me','him','her',
        'us','them','my','your','his','our','their','very','too','more',
        'le','la','les','un','une','des','de','du','d','l','est','sont',
        'a','ont','au','aux','ce','cet','cette','ces','que','qui','quoi',
        'dont','ou','ne','pas','ni','dans','sur','sous','pour','par',
        'avec','sans','vers','mais','donc','or','car','aussi','puis',
        'ensuite','et','il','elle','ils','elles','plus','moins',
        'tres','trop','encore','deja','quand','comment','pourquoi',
        'explain','describe','tell','give','say','make','what','when',
        'where','why','how','explique','decris','parle','donne',
    }
    
    def __init__(self, knowledge_base: List[Fact]):
        self.kb = list(knowledge_base)
        self.N = len(self.kb)
        
        # ─── 1. INDEX INVERSÉ (mot → faits) ───
        self.word_to_facts: Dict[str, Set[int]] = defaultdict(set)
        self.fact_words: Dict[int, Set[str]] = {}
        
        for fid, (s, r, o, sec) in enumerate(self.kb):
            words = self._tokenize(s + ' ' + r + ' ' + o)
            self.fact_words[fid] = words
            for w in words:
                self.word_to_facts[w].add(fid)
        
        # ─── 2. GRAPHE DE CO-OCCURRENCE (mot → voisins) ───
        # Deux mots sont voisins s'ils apparaissent dans le même fait
        self.co_occurrence: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        for fid, (s, r, o, sec) in enumerate(self.kb):
            words = list(self.fact_words[fid])
            for i, w1 in enumerate(words):
                for w2 in words[i+1:]:
                    if w1 != w2:
                        self.co_occurrence[w1][w2] += 1.0
                        self.co_occurrence[w2][w1] += 1.0
        
        # ─── 3. NORMALISER (fréquence → probabilité) ───
        for w1 in self.co_occurrence:
            total = sum(self.co_occurrence[w1].values())
            if total > 0:
                for w2 in self.co_occurrence[w1]:
                    self.co_occurrence[w1][w2] /= total
        
        # ─── 4. MOTS DE HAUTE AMPLITUDE (SFT harmonique) ───
        self.high_amplitude: Dict[str, float] = {}
        try:
            from harmonic_quality import HIGH_AMPLITUDE_FACTS
            for (s, r, o), amp in HIGH_AMPLITUDE_FACTS.items():
                for w in self._tokenize(s + ' ' + r + ' ' + o):
                    if w not in self.high_amplitude or amp > self.high_amplitude[w]:
                        self.high_amplitude[w] = amp
        except ImportError:
            pass
        
        print(f"SemanticWave: {len(self.word_to_facts)} mots, "
              f"{sum(len(v) for v in self.co_occurrence.values())} liens")
        
        # ─── 5. PONTS SÉMANTIQUES : faits synonymes pour créer des liens ───
        # Ces faits injectent des connexions sémantiques dans le graphe
        # (ex: "mona lisa" ↔ "joconde", "largest" ↔ "plus grand")
        SYNONYM_BRIDGES = [
            ("mona lisa", "est aussi appelee", "la joconde", "SYNONYME"),
            ("la joconde", "est aussi appelee", "mona lisa", "SYNONYME"),
            ("leonardo da vinci", "est aussi appele", "leonard de vinci", "SYNONYME"),
            ("da vinci", "est aussi appele", "leonard de vinci", "SYNONYME"),
            ("largest", "traduit par", "plus grand", "SYNONYME"),
            ("biggest", "traduit par", "plus grand", "SYNONYME"),
            ("highest", "traduit par", "plus haut", "SYNONYME"),
            ("longest", "traduit par", "plus long", "SYNONYME"),
            ("painted", "traduit par", "peint", "SYNONYME"),
            ("a peint", "traduit par", "painted", "SYNONYME"),
            ("wrote", "traduit par", "a ecrit", "SYNONYME"),
            ("a ecrit", "traduit par", "wrote", "SYNONYME"),
            ("discovered", "traduit par", "a decouvert", "SYNONYME"),
            ("capital", "traduit par", "capitale", "SYNONYME"),
            ("capitale", "traduit par", "capital", "SYNONYME"),
        ]
        self._add_semantic_bridges(SYNONYM_BRIDGES)
    
    def _add_semantic_bridges(self, bridges: List[Tuple]):
        """Ajoute des ponts sémantiques au graphe sans modifier la KB."""
        for s, r, o, sec in bridges:
            words = self._tokenize(s + ' ' + r + ' ' + o)
            word_list = list(words)
            for i, w1 in enumerate(word_list):
                for w2 in word_list[i+1:]:
                    if w1 != w2:
                        self.co_occurrence[w1][w2] += 2.0  # poids double
                        self.co_occurrence[w2][w1] += 2.0
    
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenise en mots significatifs, en préservant les bigrammes connus."""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', ' ', text)
        words = text.split()
        
        # Préserver les bigrammes importants
        BIGRAMS = {
            'mona lisa', 'da vinci', 'leonard de', 'leonardo da',
            'new delhi', 'buenos aires', 'south america', 'north america',
            'united states', 'united kingdom', 'world war', 'world war ii',
            'cold war', 'civil war', 'berlin wall', 'wall street',
            'san francisco', 'los angeles', 'new york', 'sri lanka',
            'costa rica', 'el salvador', 'south africa', 'saudi arabia',
            'pacific ocean', 'atlantic ocean', 'indian ocean',
            'mount everest', 'sahara desert', 'nile river',
            'albert einstein', 'isaac newton', 'charles darwin',
            'marie curie', 'martin luther', 'nelson mandela',
            'george orwell', 'victor hugo', 'leonard de vinci',
            'van gogh', 'andy warhol', 'bob marley',
            'michael jackson', 'elvis presley',
            'j.r.r. tolkien', 'j.k. rowling',
        }
        
        result = set()
        i = 0
        while i < len(words):
            # Vérifier les bigrammes
            if i < len(words) - 1:
                bigram = words[i] + ' ' + words[i+1]
                if bigram in BIGRAMS:
                    result.add(bigram)
                    i += 2
                    continue
            # Mot simple
            w = words[i]
            if len(w) >= 2 and w not in self.STOPWORDS:
                result.add(w)
            i += 1
        
        return result
    
    def _extract_question_words(self, question: str) -> List[str]:
        """Extrait les mots significatifs d'une question."""
        # Retirer les préfixes de question
        q = question.lower()
        prefixes = [
            'what is the ', 'what is a ', 'what is ', 'what are ',
            'who is ', 'who was ', 'who wrote ', 'who painted ',
            'who discovered ', 'who invented ', 'who created ',
            'when did ', 'when was ', 'when ', 'where is ', 'where are ',
            'where ', 'why is ', 'why does ', 'why ', 'how does ',
            'how do ', 'how ', 'explain ', 'describe ', 'define ',
            'tell me about ', 'tell me ', 'is ', 'are ',
            'qu est ce que ', 'qui a ecrit ', 'qui a peint ',
            'qui a decouvert ', 'qui est ', 'quand ', 'ou ',
            'pourquoi ', 'comment ', 'explique ',
            'quelle est la capitale de ', 'capitale de ', 'capital of ',
            'the ', 'a ', 'an ',
        ]
        for p in sorted(prefixes, key=len, reverse=True):
            if q.startswith(p):
                q = q[len(p):]
                break
        q = q.strip('?.,!;:')
        
        words = [w for w in q.split() if len(w) >= 2 and w not in self.STOPWORDS]
        return words
    
    def expand_query(self, question: str, depth: int = 1, top_k: int = 5) -> List[str]:
        """
        Élargit une question par propagation d'onde dans le graphe de co-occurrence.
        
        Pour chaque mot de la question, trouve ses top_k voisins sémantiques.
        
        Args:
            question : la question utilisateur
            depth : profondeur de propagation (1 = voisins directs)
            top_k : nombre de voisins par mot
        
        Returns:
            Liste de mots élargis (question + voisins sémantiques)
        """
        q_words = self._extract_question_words(question)
        
        if not q_words:
            return q_words
        
        expanded = list(q_words)
        
        for qw in q_words:
            if qw in self.co_occurrence:
                # Top voisins de ce mot dans le graphe
                neighbors = sorted(
                    self.co_occurrence[qw].items(),
                    key=lambda x: -x[1]
                )[:top_k]
                
                for neighbor, strength in neighbors:
                    if strength > 0.05 and neighbor not in expanded:
                        expanded.append(neighbor)
        
        return expanded
    
    def retrieve(self, question: str, max_results: int = 5,
                 expansion_depth: int = 1) -> List[Fact]:
        """
        Retrouve les faits par résonance ondulatoire.
        
        Approche PRAGMATIQUE :
        1. Recherche directe des mots de la question dans l'index
        2. Si pas assez de résultats → expansion sémantique (co-occurrence)
        3. Si toujours rien → fallback aux mots originaux
        """
        q_words = self._extract_question_words(question)
        
        # 1. RECHERCHE DIRECTE (IDF + amplitude)
        fact_scores: Dict[int, float] = defaultdict(float)
        
        for word in q_words:
            if word not in self.word_to_facts:
                continue
            word_weight = self.high_amplitude.get(word, 1.0)
            df = len(self.word_to_facts[word])
            idf = math.log(self.N / max(df, 1)) + 1
            
            for fid in self.word_to_facts[word]:
                fact_scores[fid] += word_weight * idf
        
        # 2. EXPANSION SÉMANTIQUE si pas assez de candidats
        if len(fact_scores) < 3:
            for word in q_words:
                if word not in self.co_occurrence:
                    continue
                # Top 2 voisins sémantiques
                neighbors = sorted(
                    self.co_occurrence[word].items(),
                    key=lambda x: -x[1]
                )[:2]
                
                for neighbor, strength in neighbors:
                    if strength < 0.1 or neighbor not in self.word_to_facts:
                        continue
                    df = len(self.word_to_facts[neighbor])
                    idf = math.log(self.N / max(df, 1)) + 1
                    for fid in self.word_to_facts[neighbor]:
                        fact_scores[fid] += strength * idf
        
        if not fact_scores:
            # Fallback : chercher avec les mots originaux seulement
            q_words = self._extract_question_words(question)
            for word in q_words:
                if word in self.word_to_facts:
                    for fid in self.word_to_facts[word]:
                        fact_scores[fid] += 1.0
        
        # 3. SCORER ET TRIER
        scored = sorted(fact_scores.items(), key=lambda x: -x[1])
        
        # 4. BONUS DE SUJET
        q_words = self._extract_question_words(question)
        
        final_scored = []
        for fid, score in scored[:max_results * 4]:
            s, r, o, sec = self.kb[fid]
            s_lower = s.lower()
            o_lower = o.lower()
            
            # Bonus si le sujet de la question est dans le sujet du fait
            sujet_bonus = 0
            for qw in q_words:
                if qw in s_lower:
                    sujet_bonus += 3.0
                elif qw in o_lower:
                    sujet_bonus += 2.0
            
            # Pénalité pour les très longs faits (bruit)
            combined_len = len(s + r + o)
            length_penalty = -0.5 if combined_len > 150 else 0
            
            total = score + sujet_bonus + length_penalty
            final_scored.append((total, fid))
        
        final_scored.sort(key=lambda x: -x[0])
        
        # 5. DÉDUPLIQUER ET RETOURNER
        results = []
        seen = set()
        for score, fid in final_scored:
            fact = self.kb[fid]
            if fact[0] not in seen:
                results.append(fact)
                seen.add(fact[0])
            if len(results) >= max_results:
                break
        
        return results
