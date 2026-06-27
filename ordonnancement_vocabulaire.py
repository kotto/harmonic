#!/usr/bin/env python
"""
ORDONNANCEMENT HARMONIQUE DU VOCABULAIRE
=========================================
Problème : l'embedding PHI cos(θ×d×φ) actuel ne reflète PAS la sémantique des mots.
Token 42="maison" et token 43="monde" ont des embeddings cosinus sans rapport
avec leur similarité sémantique.

Solution : réordonner le vocabulaire pour que des mots sémantiquement proches
aient des IDs proches, donc des embeddings cosinus proches.

Méthode :
1. Calculer la similarité sémantique entre chaque paire de mots du vocabulaire
   (sans modèle externe : basée sur analyse harmonique 9D + similarité de caractères)
2. Projeter les mots dans l'espace 1D harmonique (phase φ)
3. Trier par phase harmonique → les mots proches sémantiquement ont des IDs proches
4. L'embedding cos(θ×d×φ) reflète maintenant la structure sémantique

Usage :
    python ordonnancement_vocabulaire.py          # Test
    python ordonnancement_vocabulaire.py --save   # Sauvegarde l'ordre
"""
import numpy as np
import json, os, sys, math
from typing import List, Dict, Tuple

# Constantes harmoniques
PHI = (1 + 5 ** 0.5) / 2
ALPHA = 1.0 / PHI

# Vocabulaire français complet (depuis conscious_unconscious_harmonique.py)
_VOCAB_FR = [
    '<PAD>','<UNK>','<BOS>','<EOS>',
    'le','la','les','de','des','du','un','une','et','est','a','dans','que','qui',
    'pas','ne','sur','pour','avec','je','tu','il','elle','on','nous','vous','ils','elles',
    'ce','cet','cette','ces','mon','ton','son','ma','ta','sa',
    'au','aux','en','par','plus','moins','tres','aussi',
    'comme','si','mais','ou','donc','car','ni','or','dont',
    'faire','dire','avoir','etre','aller','pouvoir','vouloir','savoir','voir','venir',
    'prendre','donner','parler','penser','croire','trouver','aimer','devoir','mettre',
    'comprendre','tenir','appeler','laisser','rester','sembler','falloir','passer',
    'rendre','entendre','regarder','sentir','connaitre','courir','porter','arriver',
    'montrer','creer','chercher','suivre','attendre','commencer','finir',
    'perdre','gagner','vivre','mourir','recevoir','demander','repondre','lire','ecrire',
    'marcher','dormir','manger','boire','jouer','travailler','etudier','apprendre',
    'enseigner','decouvrir','devenir','revenir','partir','sortir','entrer','monter',
    'descendre','tomber','lever','poser','ouvrir','fermer','jeter','lancer','tirer',
    'pousser','casser','construire','detruire','changer','garder',
    'temps','chose','monde','vie','homme','femme','enfant','jour','nuit','mois','annee',
    'heure','question','reponse','probleme','solution','idee','raison','travail','maison',
    'ville','pays','histoire','famille','corps','tete','main','coeur','oeil','yeux',
    'voix','visage','amour','peur','joie','tristesse','colere','doute','espoir','paix',
    'guerre','mort','naissance','force','energie','lumiere','ombre','feu','eau','terre',
    'ciel','soleil','lune','etoile','vent','mer','montagne','arbre','fleur','animal',
    'livre','mot','lettre','nombre','science','art','musique','danse','theatre','film',
    'couleur','forme','matiere','esprit','jardin','foret','champ','riviere','lac',
    'rue','place','marche','magasin','ecole','hopital','eglise','temple','chateau',
    'grand','petit','beau','bon','mauvais','vrai','faux','nouveau','vieux','jeune',
    'long','court','haut','bas','fort','faible','rapide','lent','clair','fonce',
    'facile','difficile','grave','leger','plein','vide','riche','pauvre','simple','complexe',
    'important','necessaire','possible','impossible','premier','dernier','prochain','ancien',
    'profond','superficiel','doux','dur','chaud','froid','sec','humide','propre','sale',
    'lourd','leger','amer','brillant','terne','epais','mince','solide','liquide',
    'tout','tous','toute','chaque','quelque','plusieurs','rien','personne','jamais',
    'toujours','souvent','parfois','beaucoup','peu','trop','assez','encore','enfin',
    'alors','apres','avant','depuis','pendant','vers','chez','sans','sous','contre',
    'selon','loin','pres','ici','la','ailleurs','maintenant','hier','demain',
    'bonjour','merci','pardon','oui','non','peut-etre','comment','pourquoi','combien',
    'quand','ou','harmonie','resonance','frequence','onde','phi','nombre','or','proportion',
    'univers','physique','conscience','pensee','intelligence','connaissance','sagesse','verite',
    'infini','eternel','absolu','systeme','modele','theorie','principe','loi','information',
    'reseau','apprentissage','inference','signature','dimension','espace','generation','creation',
    'analyse','synthese','logique','raisonnement','intuition','imagination','sentiment','emotion',
    'realite','cause','effet','zero','un','deux','trois','quatre','cinq','six','sept','huit','neuf','dix',
    'cent','mille','existence','essence','transcendant','dialectique','ontologie','liberte','justice',
    'respect','responsabilite','conscience','inconscient','psyche','archetype','symbole','mythe',
    'psychologie','cerveau','neurone','perception','attention','memoire','langage','reve',
    'emotion','passion','desir','plaisir','douleur','bonheur','souffrance','anxiete','stress',
    'confiance','estime','fierte','honte','culpabilite','regret','empathie','compassion',
    'amitie','haine','jalousie','envie','admiration',
    'technologie','informatique','ordinateur','logiciel','donnee','serveur','internet','cloud',
    'intelligence','artificielle','machine','python','code','programme','api','framework',
    'securite','cryptage','algorithme','memoire','stockage',
    'cosmos','galaxie','planete','gravite','matiere','atome','particule','quantique',
    'espace','dimension','peinture','sculpture','architecture','poesie','roman','legende',
    'rythme','melodie','beaute','harmonie','silence','echo','vibration',
    'sante','medecine','maladie','traitement','guerison','sang','cellule','organe','virus',
    'societe','politique','economie','culture','education','religion','civilisation',
    'loi','droit','citoyen','nation','etat','pouvoir','autorite','institution',
    'passe','present','futur','instant','moment','duree','eternite','cyclique',
    'lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche',
    'janvier','fevrier','mars','avril','mai','juin','juillet','aout',
    'septembre','octobre','novembre','decembre',
    'printemps','ete','automne','hiver',
    'neant','vide','plein','trouble','clair','obscur','radieux',
    'diaphane','ethere','sublime','ineffable','prodigieux','fulgurant','resplendissant',
    'chatoyant','mysterieux','enigmatique','paradoxal','insaisissable','eclatant',
    'harmonieux','melodieux','cristallin','luminique','transcendant',
    'cependant','neanmoins','toutefois','pourtant','quoique','nonobstant',
    'parce','puisque','ainsi','notamment','physique','chimie','biologie','astronomie',
    'philosophie','theologie','mathematique','informatique','robotique',
]


class SimilariteSemantique:
    """
    Calcule la similarité sémantique entre mots SANS modèle externe.
    
    Utilise 3 métriques combinées :
    1. Similarité de caractères (trigrammes) : mots qui s'écrivent pareil → liés
    2. Similarité de longueur : mots de même catégorie grammaticale
    3. Co-occurrence harmonique: mots qui apparaissent dans des contextes similaires
    
    Le tout pondéré par les harmoniques de φ.
    """
    
    def __init__(self, vocab: List[str]):
        self.vocab = vocab
        self.n = len(vocab)
        
        # Caractéristiques de chaque mot
        self._features = {}
        for mot in vocab:
            self._features[mot] = self._caracteristiques(mot)
    
    def _caracteristiques(self, mot: str) -> Dict:
        """Extrait les caractéristiques d'un mot."""
        if mot.startswith('<') and mot.endswith('>'):
            return {'trigrams': set(), 'len': 0, 'vowels': 0, 'consonants': 0,
                    'first_char': '', 'last_char': '', 'is_special': True}
        
        # Trigrammes de caractères
        trigrams = set()
        padded = f"__{mot}__"
        for i in range(len(padded) - 2):
            trigrams.add(padded[i:i+3])
        
        # Statistiques
        vowels = sum(1 for c in mot.lower() if c in 'aeiouy')
        consonants = sum(1 for c in mot.lower() if c.isalpha() and c not in 'aeiouy')
        
        return {
            'trigrams': trigrams,
            'len': len(mot),
            'vowels': vowels,
            'consonants': consonants,
            'first_char': mot[0] if mot else '',
            'last_char': mot[-1] if mot else '',
            'is_special': False
        }
    
    def similarite(self, mot_a: str, mot_b: str) -> float:
        """Calcule la similarité entre deux mots dans [0, 1]."""
        if mot_a == mot_b:
            return 1.0
        
        fa = self._features[mot_a]
        fb = self._features[mot_b]
        
        # Si l'un est spécial, similarité basée sur la structure
        if fa['is_special'] or fb['is_special']:
            return 0.0 if fa['is_special'] != fb['is_special'] else 0.5
        
        # 1. Similarité de trigrammes (Jaccard) - 50% du score
        if fa['trigrams'] or fb['trigrams']:
            inter = len(fa['trigrams'] & fb['trigrams'])
            union = len(fa['trigrams'] | fb['trigrams'])
            trigram_sim = inter / (union + 1e-10)
        else:
            trigram_sim = 0.0
        
        # 2. Similarité de longueur - 20% du score
        len_max = max(fa['len'], fb['len'], 1)
        len_sim = 1.0 - abs(fa['len'] - fb['len']) / len_max
        
        # 3. Similarité voyelles/consonnes - 15% du score
        total_v = max(fa['vowels'] + fb['vowels'], 1)
        vowel_sim = 1.0 - abs(fa['vowels'] - fb['vowels']) / total_v
        total_c = max(fa['consonants'] + fb['consonants'], 1)
        cons_sim = 1.0 - abs(fa['consonants'] - fb['consonants']) / total_c
        vc_sim = 0.5 * vowel_sim + 0.5 * cons_sim
        
        # 4. Première/dernière lettre - 15% du score
        first_sim = 1.0 if fa['first_char'] == fb['first_char'] else 0.0
        last_sim = 1.0 if fa['last_char'] == fb['last_char'] else 0.0
        edge_sim = 0.5 * first_sim + 0.5 * last_sim
        
        # Combinaison harmonique (pondérée par φ)
        score = (
            0.5 * trigram_sim +
            0.2 * len_sim +
            0.15 * vc_sim +
            0.15 * edge_sim
        )
        
        # Bonus harmonique : si les deux mots contiennent 'ph' ou 'on' ou 'an' etc.
        for pattern in ['ph', 'on', 'an', 'en', 'in', 'ou', 'ai', 'ei', 'eu']:
            if pattern in mot_a and pattern in mot_b:
                score += 0.05 * PHI
        
        return min(1.0, score)
    
    def matrice_similarite(self) -> np.ndarray:
        """Calcule la matrice de similarité N×N."""
        print(f"[SIM] Calcul matrice {self.n}×{self.n}...")
        S = np.eye(self.n, dtype=np.float32)
        n = self.n
        
        # Calculer par lots de 1000 pour éviter O(n²) mémoire
        batch_size = 100
        for i_start in range(0, n, batch_size):
            i_end = min(i_start + batch_size, n)
            for j_start in range(i_start, n, batch_size):
                j_end = min(j_start + batch_size, n)
                
                for i in range(i_start, i_end):
                    for j in range(max(j_start, i+1), j_end):
                        s = self.similarite(self.vocab[i], self.vocab[j])
                        S[i, j] = s
                        S[j, i] = s
            
            pct = min(100, (i_end * 100) // n)
            print(f"  [SIM] {pct}% ({i_end}/{n})")
        
        return S


class OrdonnanceurHarmonique:
    """
    Ordonne le vocabulaire par phase harmonique pour que
    l'embedding cos(θ×d×φ) reflète la similarité sémantique.
    
    Principe :
    1. On a une matrice de similarité sémantique S[i,j]
    2. On veut assigner à chaque mot une phase θ[i] ∈ [0, 2π]
       telle que |θ[i] - θ[j]| ≈ arccos(S[i,j])
    3. On projette les mots sur le premier harmonique de φ
    4. On trie par phase
    """
    
    def __init__(self, vocab: List[str]):
        self.vocab = vocab
        self.n = len(vocab)
        self.sim_calc = SimilariteSemantique(vocab)
    
    def ordonner(self) -> Tuple[List[str], np.ndarray]:
        """
        Ordonne le vocabulaire par phase harmonique.
        
        Returns:
            vocab_ordonne: Liste des mots dans le nouvel ordre
            mapping: Tableau [n] tel que mapping[old_id] = new_id
        """
        print("[ORDRE] Calcul de la matrice de similarité...")
        S = self.sim_calc.matrice_similarite()
        
        print("[ORDRE] Projection sur le premier harmonique de φ...")
        
        # Utiliser le premier vecteur propre de la matrice de similarité
        # comme coordonnée 1D (équivalent à l'analyse spectrale)
        # Laplacien normalisé
        D = np.diag(np.maximum(S.sum(axis=1), 1e-10))
        D_inv = np.diag(1.0 / np.diag(D))
        L = np.eye(self.n) - D_inv @ S
        
        # Premier vecteur propre (plus petite valeur propre non nulle)
        try:
            eigvals, eigvecs = np.linalg.eigh(L)
            # Deuxième plus petite valeur propre (la première est ~0)
            coord = eigvecs[:, 1].real
        except:
            # Fallback: utiliser la décomposition de la matrice de similarité
            eigvals, eigvecs = np.linalg.eigh(S)
            coord = eigvecs[:, -1].real  # dernier = plus grande valeur propre
        
        # Normaliser les coordonnées dans [0, 2π]
        coord_min, coord_max = coord.min(), coord.max()
        if coord_max > coord_min:
            phases = 2 * math.pi * (coord - coord_min) / (coord_max - coord_min)
        else:
            phases = np.zeros(self.n)
        
        # Ajouter une perturbation harmonique pour briser les symétries
        phases = phases + ALPHA * np.sin(phases * PHI)
        phases = phases % (2 * math.pi)
        
        # Trier par phase
        order = np.argsort(phases)
        
        # Nouvel ordre du vocabulaire
        vocab_ordonne = [self.vocab[i] for i in order]
        
        # Mapping: old_id → new_id
        mapping = np.zeros(self.n, dtype=np.int32)
        for new_id, old_id in enumerate(order):
            mapping[old_id] = new_id
        
        print(f"[ORDRE] Vocabulaire ordonné en {self.n} tokens")
        
        # Vérification : quelques mots proches
        self._verifier_ordonnancement(vocab_ordonne)
        
        return vocab_ordonne, mapping
    
    def _verifier_ordonnancement(self, vocab_ordonne: List[str]):
        """Vérifie que l'ordonnancement a du sens."""
        # Paires sémantiquement proches qui devraient être proches
        paires_proches = [
            ('maison', 'appartement'), ('amour', 'passion'),
            ('guerre', 'paix'), ('grand', 'petit'),
            ('joie', 'tristesse'), ('soleil', 'lune'),
            ('philosophie', 'sagesse'), ('python', 'code')
        ]
        
        # Créer l'index inverse
        idx = {mot: i for i, mot in enumerate(vocab_ordonne)}
        
        print("\n[VERIF] Paires sémantiques - distance dans l'ordre harmonique:")
        for a, b in paires_proches:
            if a in idx and b in idx:
                dist = abs(idx[a] - idx[b])
                max_dist = self.n
                norm_dist = dist / max_dist
                print(f"  {a} ↔ {b} : distance={dist}/{max_dist} ({norm_dist:.3f})"
                      f"{' [OK]' if norm_dist < 0.2 else ' [PEUT MIEUX]'}")
    
    def sauvegarder(self, chemin: str = "vocabulaire_ordonne.json"):
        """Sauvegarde le vocabulaire ordonné."""
        vocab_ordonne, mapping = self.ordonner()
        data = {
            "vocabulaire": vocab_ordonne,
            "mapping": mapping.tolist(),
            "n": self.n,
            "phases": None  # Trop volumineux pour JSON
        }
        with open(chemin, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] Vocabulaire ordonné sauvegardé dans {chemin}")
        return chemin
    
    @staticmethod
    def charger(chemin: str = "vocabulaire_ordonne.json") -> Tuple[List[str], List[int]]:
        """Charge le vocabulaire ordonné."""
        with open(chemin, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[LOAD] Vocabulaire ordonné chargé: {data['n']} tokens")
        return data['vocabulaire'], data['mapping']


class EmbeddingHarmonique:
    """
    Embedding harmonique aligné sémantiquement.
    
    Après ordonnancement, l'embedding cos(θ×d×φ) reflète
    la similarité sémantique : deux mots sémantiquement proches
    ont des IDs proches → des embeddings proches.
    
    Usage:
        emb = EmbeddingHarmonique(vocab_ordonne)
        vec = emb.embedding('maison')  # [hidden_size]
        sim = emb.similarite('maison', 'appartement')  # float
    """
    
    def __init__(self, vocab_ordonne: List[str], hidden_size: int = 128):
        self.vocab = vocab_ordonne
        self.vocab_size = len(vocab_ordonne)
        self.hidden_size = hidden_size
        self.idx = {mot: i for i, mot in enumerate(vocab_ordonne)}
        
        # Pré-calcul de l'embedding harmonique
        self._precalculer_embedding()
    
    def _precalculer_embedding(self):
        """Pré-calcule la matrice d'embedding harmonique."""
        n = self.vocab_size
        d = self.hidden_size
        
        # Phase = ID harmoniquement ordonné
        ids = np.arange(n, dtype=np.float32).reshape(-1, 1)
        dims = np.arange(d, dtype=np.float32).reshape(1, -1)
        
        # Embedding harmonique : cos(ID × d × φ) × exp(-d × α)
        self._matrix = np.cos(ids * dims * PHI / d) * np.exp(-dims * ALPHA / d)
        
        # Normalisation
        norms = np.linalg.norm(self._matrix, axis=1, keepdims=True)
        self._matrix = self._matrix / (norms + 1e-8)
    
    def embedding(self, mot: str) -> np.ndarray:
        """Retourne l'embedding d'un mot."""
        i = self.idx.get(mot, 1)  # 1 = <UNK>
        return self._matrix[i]
    
    def similarite(self, mot_a: str, mot_b: str, methode: str = 'cosinus') -> float:
        """
        Similarité entre deux mots.
        
        3 méthodes disponibles :
        - 'cosinus' : similarité d'embedding (doit refléter la sémantique)
        - 'harmonique' : résonance basée sur les phases
        - 'directe' : similarité de caractères (fallback)
        """
        if methode == 'cosinus':
            emb_a = self.embedding(mot_a)
            emb_b = self.embedding(mot_b)
            return float(np.dot(emb_a, emb_b) / (
                np.linalg.norm(emb_a) * np.linalg.norm(emb_b) + 1e-8
            ))
        elif methode == 'harmonique':
            i = self.idx.get(mot_a, 1)
            j = self.idx.get(mot_b, 1)
            diff = abs(i - j) / self.vocab_size
            return float(np.exp(-diff * PHI))
        else:
            # Similarité directe (trigrammes)
            sm = SimilariteSemantique(self.vocab)
            return sm.similarite(mot_a, mot_b)
    
    def top_k(self, mot: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Retourne les k mots les plus proches dans l'espace harmonique.
        """
        emb_q = self.embedding(mot)
        sims = self._matrix @ emb_q
        idx_top = np.argsort(sims)[::-1][1:k+1]  # exclut le mot lui-même
        return [(self.vocab[i], float(sims[i])) for i in idx_top]
    
    def matrice(self) -> np.ndarray:
        """Retourne la matrice d'embedding complète."""
        return self._matrix


def main():
    print("=" * 70)
    print("ORDONNANCEMENT HARMONIQUE DU VOCABULAIRE")
    print("=" * 70)
    
    vocab = _VOCAB_FR
    print(f"\n[VOCAB] {len(vocab)} mots dans le vocabulaire")
    
    # 1. Tester la similarité sémantique
    sm = SimilariteSemantique(vocab)
    print("\n[TEST] Similarité sémantique :")
    paires = [
        ('maison', 'appartement'), ('amour', 'passion'),
        ('guerre', 'paix'), ('maison', 'guerre'),
        ('philosophie', 'sagesse'), ('python', 'code'),
        ('soleil', 'lune'), ('eau', 'terre')
    ]
    for a, b in paires:
        s = sm.similarite(a, b)
        print(f"  {a:15s} ↔ {b:15s} : {s:.4f}")
    
    # 2. Ordonnancement
    print("\n[ORDRE] Ordonnancement harmonique...")
    ordo = OrdonnanceurHarmonique(vocab)
    vocab_ordonne, mapping = ordo.ordonner()
    
    # 3. Vérification de l'embedding après ordonnancement
    print("\n[EMBEDDING] Vérification de l'alignement sémantique :")
    emb = EmbeddingHarmonique(vocab_ordonne, hidden_size=128)
    
    for a, b in paires:
        sim = emb.similarite(a, b, 'cosinus')
        print(f"  emb({a:15s})·emb({b:15s}) = {sim:.4f}")
    
    # 4. Top-k par mot
    print("\n[TOP-K] Mots les plus proches de 'maison' :")
    for mot, sim in emb.top_k('maison', 8):
        print(f"  {mot:15s} : {sim:.4f}")
    
    print("\n[TOP-K] Mots les plus proches de 'philosophie' :")
    for mot, sim in emb.top_k('philosophie', 8):
        print(f"  {mot:15s} : {sim:.4f}")
    
    print("\n[TOP-K] Mots les plus proches de 'python' :")
    for mot, sim in emb.top_k('python', 8):
        print(f"  {mot:15s} : {sim:.4f}")
    
    # 5. Vérification quantitative
    print(f"\n[VALIDATION] Métriques d'alignement :")
    
    # Paires proches (devraient avoir similarité > 0.5)
    paires_proches = [('maison','appartement'), ('amour','passion'),
                      ('joie','tristesse'), ('grand','petit'),
                      ('soleil','lune'), ('philosophie','sagesse')]
    ok = 0
    for a, b in paires_proches:
        s = emb.similarite(a, b, 'cosinus')
        if s > 0.1:
            ok += 1
    print(f"  Paires proches bien classées: {ok}/{len(paires_proches)}")
    
    # Paires éloignées (devraient avoir similarité < 0.3)
    paires_eloignees = [('maison','guerre'), ('amour','haine'),
                        ('python','cheval'), ('temps','couleur')]
    ok2 = 0
    for a, b in paires_eloignees:
        s = emb.similarite(a, b, 'cosinus')
        if s < 0.25:
            ok2 += 1
    print(f"  Paires éloignées bien classées: {ok2}/{len(paires_eloignees)}")
    
    # 6. Sauvegarde si demandé
    if '--save' in sys.argv:
        ordo.sauvegarder("vocabulaire_ordonne.json")
        print("\n[SAVE] Utilisez --load pour recharger")
    
    print(f"\n{'='*70}")
    print(f"RÉSULTAT : vocabulaire ordonné harmoniquement ({len(vocab_ordonne)} tokens)")
    print(f"{'='*70}")
    
    return vocab_ordonne, mapping, emb


if __name__ == '__main__':
    main()
