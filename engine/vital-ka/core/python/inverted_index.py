"""
Inverted Index Retriever — Solution structurelle au problème de retrieval
=========================================================================
Au lieu de scanner TOUS les faits à chaque question (O(N)),
on construit un INDEX INVERSÉ (mot → liste de faits) au démarrage.
La retrieval devient O(1) par mot-clé.

C'est exactement ce que font les moteurs de recherche.
C'est ce que fait le cerveau : pas de scan exhaustif, un index.

Usage:
    from inverted_index import InvertedIndex
    
    idx = InvertedIndex(kb)           # construit l'index (1 fois)
    results = idx.search(question)    # retrieval rapide
"""

import re
import math
from collections import defaultdict
from typing import List, Tuple, Set, Dict


class InvertedIndex:
    """
    Index inversé pour retrieval rapide de faits.
    
    Architecture :
      - word_to_facts : {mot: {fact_id: positions}}
      - fact_list : [fact1, fact2, ...]
      - fact_words : {fact_id: set(mots)} pour scoring TF-IDF
    
    Scoring : TF-IDF simplifié
      score(fait, question) = Σ IDF(mot) × TF(mot, fait)
      où IDF(mot) = log(N / df(mot))
      et TF(mot, fait) = count(mot dans fait) / longueur(fait)
    """
    
    # Stopwords FR + EN
    STOPWORDS = {
        # FR
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'd', 'l',
        'et', 'est', 'sont', 'a', 'ont', 'au', 'aux', 'ce', 'cet', 'cette', 'ces',
        'que', 'qui', 'quoi', 'dont', 'ou', 'ne', 'pas', 'ni',
        'dans', 'sur', 'sous', 'pour', 'par', 'avec', 'sans', 'vers',
        'mais', 'donc', 'or', 'car', 'aussi', 'puis', 'ensuite',
        'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses',
        'notre', 'votre', 'leur', 'leurs',
        'plus', 'moins', 'tres', 'trop', 'encore', 'deja',
        'tu', 'vous', 'nous', 'on', 'il', 'elle', 'ils', 'elles',
        'explique', 'expliquer', 'expliquez', 'decris', 'decrire',
        'parle', 'parler', 'donne', 'donner', 'dis', 'dire',
        'fait', 'fais', 'faire', 'peux', 'peut', 'pouvoir',
        'veux', 'veut', 'vouloir', 'voudrais',
        'sais', 'sait', 'savoir', 'connais', 'connaitre',
        'quand', 'comment', 'pourquoi',
        # EN
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'shall',
        'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from',
        'it', 'its', 'and', 'or', 'not', 'but', 'if', 'so', 'as', 'than',
        'that', 'this', 'these', 'those', 'which', 'who', 'whom', 'whose',
        'i', 'you', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'our', 'their',
        'more', 'less', 'very', 'too', 'also', 'still', 'already',
        'explain', 'describe', 'tell', 'give', 'say', 'make',
        'want', 'know', 'think', 'feel',
        'what', 'when', 'where', 'why', 'how',
    }
    
    # Synonymes pour expansion de requête
    SYNONYMS = {
        'mona lisa': ['joconde'],
        'joconde': ['mona lisa'],
        'da vinci': ['leonard de vinci', 'leonardo'],
        'davinci': ['leonard de vinci'],
        'leonardo': ['leonard de vinci'],
        'moon': ['lune'],
        'lune': ['moon'],
        'earth': ['terre'],
        'terre': ['earth'],
        'sun': ['soleil'],
        'soleil': ['sun'],
        'gravity': ['gravite'],
        'gravite': ['gravity'],
        'light': ['lumiere'],
        'lumiere': ['light'],
        'water': ['eau'],
        'eau': ['water'],
        'dna': ['adn'],
        'adn': ['dna'],
        'usa': ['etats unis', 'america'],
        'america': ['etats unis', 'usa'],
        'uk': ['royaume uni', 'britain'],
        'britain': ['royaume uni', 'uk'],
        'largest': ['plus grand', 'biggest'],
        'biggest': ['plus grand', 'largest'],
        'highest': ['plus haut'],
        'longest': ['plus long'],
        'painted': ['peint', 'a peint'],
        'peint': ['painted', 'a peint'],
        'wrote': ['ecrit', 'a ecrit'],
        'ecrit': ['wrote', 'a ecrit'],
        'discovered': ['decouvert', 'a decouvert'],
        'decouvert': ['discovered', 'a decouvert'],
        'invented': ['invente', 'a invente'],
        'invente': ['invented', 'a invente'],
        'capital': ['capitale'],
        'capitale': ['capital'],
        'ocean': ['ocean'],
        'country': ['pays'],
        'pays': ['country'],
        'world': ['monde'],
        'monde': ['world'],
    }
    
    def __init__(self, knowledge_base: List[Tuple]):
        """Construit l'index inversé à partir de la base de connaissance."""
        self.fact_list = list(knowledge_base)
        self.N = len(self.fact_list)
        
        # Index inversé : mot → {fact_id}
        self.word_to_facts: Dict[str, Set[int]] = defaultdict(set)
        
        # Mots de chaque fait (pour TF-IDF)
        self.fact_words: Dict[int, List[str]] = {}
        
        # Fréquence de document (pour IDF)
        self.df: Dict[str, int] = defaultdict(int)
        
        # Construire l'index
        for fid, (s, r, o, sec) in enumerate(self.fact_list):
            combined = (s + ' ' + r + ' ' + o).lower()
            words = self._tokenize(combined)
            self.fact_words[fid] = words
            unique_words = set(words)
            for w in unique_words:
                self.word_to_facts[w].add(fid)
                self.df[w] += 1
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenise un texte en mots significatifs."""
        # Nettoyer
        text = text.lower()
        text = re.sub(r'[^\w\s-]', ' ', text)  # garder alphanum et tirets
        words = text.split()
        # Filtrer stopwords et mots courts
        words = [w for w in words if len(w) >= 2 and w not in self.STOPWORDS]
        return words
    
    def _idf(self, word: str) -> float:
        """Inverse Document Frequency."""
        df = self.df.get(word, 0)
        if df == 0:
            return 0.0
        return math.log(self.N / df)
    
    def search(self, question: str, max_results: int = 5) -> List[Tuple]:
        """
        Recherche les faits les plus pertinents pour une question.
        
        Algorithme :
        1. Tokeniser la question
        2. Expandre avec synonymes
        3. Pour chaque mot-clé, récupérer les faits de l'index
        4. Scorer par TF-IDF
        5. Retourner les top-k
        """
        q_lower = question.lower()
        
        # 1. Extraire le sujet (retirer préfixes de question)
        sujet = q_lower
        prefixes = [
            'what is the ', 'what is a ', 'what is an ', 'what is ', 'what are ',
            'who is ', 'who was ', 'who wrote ', 'who painted ', 'who discovered ',
            'who invented ', 'who created ', 'who founded ', 'who composed ',
            'when did ', 'when was ', 'when ', 'where is ', 'where are ', 'where ',
            'why is ', 'why does ', 'why do ', 'why ', 'how does ', 'how do ',
            'how to ', 'how ', 'explain ', 'describe ', 'define ',
            'tell me about ', 'tell me ', 'can you help me understand ',
            'can you ', 'help me ', 'name three ', 'name ',
            'is ', 'are ', 'the ', 'a ', 'an ',
            "qu'est ce que ", "qu'est-ce que ", 'qu est ce que ',
            'qui a ecrit ', 'qui a peint ', 'qui a decouvert ',
            'qui a invente ', 'qui a cree ', 'qui a fonde ',
            'qui a compose ', 'qui est ', 'qui etait ',
            'quand ', 'ou ', 'pourquoi ', 'comment ',
            'explique ', 'definis ', 'parle de ', 'parle moi de ',
            'quelle est la capitale de ', 'quel est la capitale de ',
            'capitale de ', 'capital of ', 'donne moi ',
        ]
        for prefix in sorted(prefixes, key=len, reverse=True):
            if sujet.startswith(prefix):
                sujet = sujet[len(prefix):].strip()
                break
        sujet = sujet.strip('?.,!;:')
        
        # 2. Tokeniser et expandre
        q_words = self._tokenize(q_lower)
        
        # Expandre avec synonymes
        expanded = list(q_words)
        for w in q_words:
            if w in self.SYNONYMS:
                for syn in self.SYNONYMS[w]:
                    if syn not in expanded:
                        expanded.append(syn)
        
        # Aussi expandre des paires de mots (ex: "mona lisa")
        q_text = ' '.join(q_words)
        for syn_key, syn_vals in self.SYNONYMS.items():
            if syn_key in q_text:
                for sv in syn_vals:
                    sv_words = sv.split()
                    for sw in sv_words:
                        if sw not in expanded and len(sw) >= 2:
                            expanded.append(sw)
        
        # 3. Récupérer les faits candidats depuis l'index
        candidate_facts: Dict[int, float] = defaultdict(float)
        
        for word in expanded:
            if word not in self.word_to_facts:
                continue
            idf = self._idf(word)
            for fid in self.word_to_facts[word]:
                # TF = count du mot dans le fait / longueur du fait
                fact_ws = self.fact_words[fid]
                tf = fact_ws.count(word) / max(len(fact_ws), 1)
                candidate_facts[fid] += idf * tf
        
        # 4. Bonus pour les faits qui contiennent le SUJET exact
        sujet_words = self._tokenize(sujet)
        for fid in list(candidate_facts.keys()):
            s, r, o, sec = self.fact_list[fid]
            fact_combined = (s + ' ' + o).lower()
            
            # Bonus si le sujet apparaît dans le sujet du fait
            if sujet in s.lower():
                candidate_facts[fid] *= 3.0
            # Bonus si le sujet apparaît dans l'objet du fait
            elif sujet in o.lower():
                candidate_facts[fid] *= 2.0
            # Bonus si les mots du sujet apparaissent
            else:
                sw_match = sum(1 for sw in sujet_words if sw in fact_combined)
                if sw_match >= len(sujet_words) * 0.6:
                    candidate_facts[fid] *= 1.5
        
        # 5. Pénalité pour les collisions de nombres
        q_numbers = [w for w in q_lower.split() if w.isdigit()]
        if q_numbers:
            for fid in list(candidate_facts.keys()):
                s, r, o, sec = self.fact_list[fid]
                combined = (s + ' ' + r + ' ' + o).lower()
                for qn in q_numbers:
                    for fw in combined.split():
                        if fw.isdigit() and fw != qn:
                            candidate_facts[fid] *= 0.1  # grosse pénalité
                        elif qn in fw and fw != qn and fw.isdigit():
                            candidate_facts[fid] *= 0.01  # énorme pénalité
        
        # 6. Trier et dédupliquer
        sorted_fids = sorted(candidate_facts.items(), key=lambda x: -x[1])
        
        results = []
        seen_sujets = set()
        for fid, score in sorted_fids:
            if score < 0.01:
                continue
            fact = self.fact_list[fid]
            if fact[0] not in seen_sujets:
                results.append(fact)
                seen_sujets.add(fact[0])
            if len(results) >= max_results:
                break
        
        return results


def build_index(knowledge_base: List[Tuple]) -> InvertedIndex:
    """Construit un index inversé à partir d'une base de connaissance."""
    return InvertedIndex(knowledge_base)
