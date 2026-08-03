"""
PPWave Retriever — Retrieval par PPMI + onde spectrale
========================================================
Implémente les 5 étages diagnostiqués par l'expert :

Étage 0 : Fuzzy matching trigramme (fautes de frappe, acronymes)
Étage 1 : Résolution d'acronymes symboliques (ww2 → world war 2)
Étage 2 : Matrice PPMI (LE signal ondulatoire)
Étage 3 : SVD spectral optionnel (modes propres du graphe)
Étage 4 : Requête + scoring vectoriel
Étage 5 : Filtrage structurel (superlatifs, contraintes logiques)

PRINCIPE FONDAMENTAL : 
  PPMI est l'interférence entre mots.
  PPMI(w1, w2) = log(P(w1,w2) / (P(w1)·P(w2)))
  → Élevé pour les mots SPECIFIQUES qui co-occurrent
  → Nul pour les mots-HUB qui apparaissent partout

Usage:
    from ppwave import PPWaveRetriever
    pw = PPWaveRetriever(kb)
    facts = pw.retrieve("who painted the mona lisa")
"""

import re
import math
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Set

Fact = Tuple[str, str, str, str]


class PPWaveRetriever:
    """
    Retrieval par PPMI + onde spectrale.
    """

    STOPWORDS = {'the','a','an','is','are','was','were','of','in','on','at','to',
                 'for','with','by','from','and','or','it','its','that','this',
                 'le','la','les','un','une','des','de','du','d','l','est','sont',
                 'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
                 'avec','et','il','elle','ils','elles','ce','cet','cette','ces'}

    # Table minuscule chiffre → mot
    NUM_TO_WORD = {'2':'two','3':'three','4':'four','5':'five',
                   '6':'six','7':'seven','8':'eight','9':'nine'}

    def __init__(self, knowledge_base: List[Fact]):
        self.kb = list(knowledge_base)
        self.N = len(self.kb)

        # ─── Étage 0 : Index trigramme ───
        self._build_trigram_index()

        # ─── Étage 1 : N-grammes pour acronymes ───
        self._build_phrase_ngrams()

        # ─── Étage 2 : PPMI ───
        self._build_ppmi()

        # ─── Étage 3 : Vecteurs de triplets ───
        self._build_triplet_vectors()

        # ─── Étage 4 : Amorçage d'alias ───
        self._bootstrap_aliases()

        # ─── Étage 5 : Filtres structurels ───
        self._build_superlative_index()

    # ═══════════════════════════════════════════════════════════════
    # ÉTAGE 0 : Fuzzy matching trigramme
    # ═══════════════════════════════════════════════════════════════

    def _build_trigram_index(self):
        """Index trigramme sur le vocabulaire."""
        self.trigram_idx = defaultdict(set)
        self.vocab = set()
        for s, r, o, sec in self.kb:
            for w in (s + ' ' + r + ' ' + o).lower().split():
                w = w.strip('.,!?;:()[]{}')
                if len(w) >= 3:
                    self.vocab.add(w)
        for word in self.vocab:
            grams = {word[i:i+3] for i in range(len(word)-2)}
            for g in grams:
                self.trigram_idx[g].add(word)

    def _fuzzy_correct(self, token: str, threshold: float = 0.5) -> str:
        """Corrige un mot par similarité trigramme."""
        if token in self.vocab:
            return token
        grams = {token[i:i+3] for i in range(len(token)-2)}
        if not grams:
            return token
        candidates = set()
        for g in grams:
            candidates |= self.trigram_idx.get(g, set())
        best, best_score = token, 0.0
        for c in candidates:
            c_grams = {c[i:i+3] for i in range(len(c)-2)}
            score = len(grams & c_grams) / max(len(grams | c_grams), 1)
            if score > best_score:
                best, best_score = c, score
        return best if best_score >= threshold else token

    # ═══════════════════════════════════════════════════════════════
    # ÉTAGE 1 : Résolution d'acronymes
    # ═══════════════════════════════════════════════════════════════

    def _build_phrase_ngrams(self):
        """Extrait les n-grammes de la KB pour la résolution d'acronymes."""
        self.phrases = set()
        for s, r, o, sec in self.kb:
            for text in (s, r, o):
                words = text.lower().split()
                for n in range(2, 5):
                    for i in range(len(words) - n + 1):
                        phrase = ' '.join(words[i:i+n])
                        if len(phrase) >= 4:
                            self.phrases.add(tuple(words[i:i+n]))

    def _resolve_acronym(self, token: str) -> str:
        """Résout un acronyme : 'ww2' → 'world war ii'."""
        token_lower = token.lower()
        # Normaliser : remplacer les chiffres par leur équivalent mot
        expanded = token_lower
        for digit, word in self.NUM_TO_WORD.items():
            expanded = expanded.replace(digit, ' ' + word + ' ')
        expanded = expanded.replace('ww', 'world war ')

        # Tester les initiales des n-grammes
        for phrase_words in self.phrases:
            phrase = ' '.join(phrase_words)
            initials = ''.join(w[0] for w in phrase_words)
            # Comparer avec le token (sans les chiffres)
            token_clean = token_lower
            for d in '23456789':
                token_clean = token_clean.replace(d, '')
            if initials == token_clean:
                return phrase
        return token

    # ═══════════════════════════════════════════════════════════════
    # ÉTAGE 2 : Matrice PPMI
    # ═══════════════════════════════════════════════════════════════

    def _build_ppmi(self):
        """Construit la matrice PPMI."""
        # Comptage
        co = Counter()
        unigram = Counter()
        total_pairs = 0

        for s, r, o, sec in self.kb:
            words = [w for w in (s + ' ' + r + ' ' + o).lower().split()
                     if len(w) >= 2]
            unique = set(w for w in words if w not in self.STOPWORDS)
            for w in unique:
                unigram[w] += 1
            word_list = list(unique)
            for i, w1 in enumerate(word_list):
                for w2 in word_list[i+1:]:
                    if w1 != w2:
                        co[(w1, w2)] += 1
                        total_pairs += 1

        # Vocabulaire pour la PPMI (top mots les plus fréquents)
        vocab_size = min(2000, len(unigram))
        self.ppmi_vocab = [w for w, _ in unigram.most_common(vocab_size)]
        self.ppmi_idx = {w: i for i, w in enumerate(self.ppmi_vocab)}

        # PPMI
        V = len(self.ppmi_vocab)
        total_unigrams = sum(unigram.values())
        self.ppmi_matrix = {}  # sparse dict

        for (w1, w2), c in co.items():
            if w1 not in self.ppmi_idx or w2 not in self.ppmi_idx:
                continue
            p_xy = c / max(total_pairs, 1)
            p_x = unigram[w1] / max(total_unigrams, 1)
            p_y = unigram[w2] / max(total_unigrams, 1)
            pmi = math.log((p_xy / (p_x * p_y)) + 1e-12)
            ppmi = max(0.0, pmi)
            if ppmi > 0.0:
                self.ppmi_matrix[(w1, w2)] = ppmi
                self.ppmi_matrix[(w2, w1)] = ppmi

        # Stocker l'IDF pour le scoring
        self.idf = {}
        for w in self.ppmi_vocab:
            df = len(set(fid for fid, (s, r, o, _) in enumerate(self.kb)
                         if w in (s + ' ' + r + ' ' + o).lower()))
            self.idf[w] = math.log(self.N / max(df, 1)) + 1

        print(f"PPWave: {V} mots PPMI, {len(self.ppmi_matrix)} liens")

    # ═══════════════════════════════════════════════════════════════
    # ÉTAGE 3 : Vecteurs de triplets (sans SVD pour rester rapide)
    # ═══════════════════════════════════════════════════════════════

    def _build_triplet_vectors(self):
        """Pré-calcule un vecteur « sac de mots pondéré » par triplet."""
        # Pour chaque triplet, on stocke le set de mots + leur IDF
        self.triplet_words: Dict[int, Dict[str, float]] = {}
        for fid, (s, r, o, sec) in enumerate(self.kb):
            words = [w for w in (s + ' ' + r + ' ' + o).lower().split()
                     if len(w) >= 2 and w in self.ppmi_idx]
            if not words:
                continue
            word_counts = Counter(words)
            vec = {}
            for w, cnt in word_counts.items():
                vec[w] = cnt * self.idf.get(w, 1.0)
            # Normaliser
            norm = math.sqrt(sum(v*v for v in vec.values()))
            if norm > 0:
                vec = {w: v/norm for w, v in vec.items()}
            self.triplet_words[fid] = vec

    # ═══════════════════════════════════════════════════════════════
    # ÉTAGE 4 : Amorçage d'alias (mona lisa ↔ joconde)
    # ═══════════════════════════════════════════════════════════════

    def _bootstrap_aliases(self):
        """Détecte automatiquement les alias."""
        profile = defaultdict(set)
        for s, r, o, sec in self.kb:
            profile[s.lower()].add((r.lower(), o.lower()))
        self.aliases = []
        subjects = list(profile.keys())
        for i in range(len(subjects)):
            for j in range(i+1, len(subjects)):
                s1, s2 = subjects[i], subjects[j]
                over = len(profile[s1] & profile[s2])
                uni = len(profile[s1] | profile[s2])
                if uni > 0 and over/uni > 0.6:
                    self.aliases.append((s1, s2))

    # ═══════════════════════════════════════════════════════════════
    # ÉTAGE 5 : Filtre de superlatifs
    # ═══════════════════════════════════════════════════════════════

    def _build_superlative_index(self):
        """Index des superlatifs dans la KB."""
        self.superlatives = {}
        for fid, (s, r, o, sec) in enumerate(self.kb):
            rl = r.lower()
            for sup in ['largest', 'biggest', 'highest', 'longest',
                        'smallest', 'fastest', 'oldest',
                        'plus grand', 'plus haut', 'plus long',
                        'plus petit', 'plus rapide', 'plus vieux']:
                if sup in rl:
                    self.superlatives.setdefault(sup, []).append(fid)

    # ═══════════════════════════════════════════════════════════════
    # PIPELINE PRINCIPAL
    # ═══════════════════════════════════════════════════════════════

    def retrieve(self, question: str, max_results: int = 5) -> List[Fact]:
        """
        Retrieval complet en 5 étages.
        """
        # 0. Prétraitement
        q_lower = question.lower().strip()

        # Extraire le sujet (retirer préfixes)
        sujet = q_lower
        for p in ['what is the ', 'what is ', 'who is ', 'who wrote ', 'who painted ',
                  'who discovered ', 'when did ', 'when was ', 'when ', 'where is ',
                  'where ', 'why is ', 'why ', 'how ', 'explain ', 'describe ',
                  'capitale de ', 'capital of ', 'quelle est la capitale de ',
                  'qu est ce que ', 'qui a ']:
            if sujet.startswith(p): sujet = sujet[len(p):]; break
        sujet = sujet.strip('?.,!;:')

        # 1. Tokenisation + fuzzy matching + acronymes
        raw_tokens = [w.strip('.,!?;:()[]{}') for w in q_lower.split() if len(w) >= 2]
        tokens = []
        for t in raw_tokens:
            t = self._resolve_acronym(t)
            t = self._fuzzy_correct(t)
            if t not in self.STOPWORDS:
                tokens.append(t)

        if not tokens:
            return []

        # 2. Expansion PPMI (top 3 voisins par token)
        expanded_tokens = list(tokens)
        for t in tokens:
            if t in self.ppmi_idx:
                neighbors = []
                for (w1, w2), ppmi in self.ppmi_matrix.items():
                    if w1 == t and w2 not in expanded_tokens:
                        neighbors.append((w2, ppmi))
                neighbors.sort(key=lambda x: -x[1])
                for n, _ in neighbors[:3]:
                    if _ > 0.5:  # seuil PPMI significatif
                        expanded_tokens.append(n)

        # 3. Également ajouter les alias
        for a1, a2 in self.aliases:
            if a1 in tokens and a2 not in expanded_tokens:
                expanded_tokens.append(a2)
            if a2 in tokens and a1 not in expanded_tokens:
                expanded_tokens.append(a1)

        # 4. Scorer les triplets
        scores = {}
        for t in expanded_tokens:
            if t not in self.ppmi_idx:
                continue
            t_idf = self.idf.get(t, 1.0)
            for fid, vec in self.triplet_words.items():
                fid_int = int(fid)
                if t in vec:
                    scores[fid_int] = scores.get(fid_int, 0.0) + vec[t] * t_idf

        if not scores:
            return []

        # 5. Trier
        scored = sorted(scores.items(), key=lambda x: -x[1])

        # 6. Filtrage superlatif
        for sup in ['largest', 'biggest', 'highest', 'longest',
                    'plus grand', 'plus haut', 'plus long']:
            if sup in q_lower:
                if sup in self.superlatives:
                    superlative_fids = set(int(f) for f in self.superlatives[sup])
                    scored = [(s, int(fid)) for s, fid in scored if int(fid) in superlative_fids]
                    if scored:
                        break

        # 7. Bonus sujet
        final = []
        for score, fid in scored:
            fid = int(fid)
            s, r, o, sec = self.kb[fid]
            sl = s.lower()
            ol = o.lower()
            bonus = 0.0
            for t in tokens:
                if t in sl: bonus += 2.0
                elif t in ol: bonus += 1.0
            final.append((score + bonus, fid))

        final.sort(key=lambda x: -x[0])

        # 8. Dédupliquer
        results = []
        seen = set()
        for _, fid in final:
            fact = self.kb[int(fid)]
            if fact[0] not in seen:
                results.append(fact)
                seen.add(fact[0])
            if len(results) >= max_results:
                break

        return results
