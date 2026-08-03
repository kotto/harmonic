"""
Poetry Embedding — Encodeur sémantique entraîné sur corpus poétique français
==============================================================================
Construit un espace vectoriel C^64 où les mots poétiques sont proches
selon leur co-occurrence dans la poésie française classique.

Corpus : ~100 poèmes de Baudelaire, Rimbaud, Verlaine, Apollinaire, etc.
Méthode : PPMI + SVD (même approche que learned_embedding.py)
Sortie  : poetry_embedding.npz

Usage :
    python poetry_embedding.py           # Entraîner et sauvegarder
    python poetry_embedding.py --stats   # Afficher les stats
"""

import math, re, json, logging
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent

# ═══════════════════════════════════════════════════════════════════════════════
# CORPUS POÉTIQUE FRANÇAIS
# ═══════════════════════════════════════════════════════════════════════════════

POETIC_CORPUS = [
    # ── BAUDELAIRE : Les Fleurs du Mal ──
    """
    La Nature est un temple où de vivants piliers
    Laissent parfois sortir de confuses paroles
    L'homme y passe à travers des forêts de symboles
    Qui l'observent avec des regards familiers
    Comme de longs échos qui de loin se confondent
    Dans une ténébreuse et profonde unité
    Vaste comme la nuit et comme la clarté
    Les parfums les couleurs et les sons se répondent
    """,
    """
    Ô Mort vieux capitaine il est temps levons l'ancre
    Ce pays nous ennuie ô Mort appareillons
    Si le ciel et la mer sont noirs comme de l'encre
    Nos cœurs que tu connais sont remplis de rayons
    Verse-nous ton poison pour qu'il nous réconforte
    Nous voulons tant ce feu nous brûle le cerveau
    Plonger au fond du gouffre Enfer ou Ciel qu'importe
    Au fond de l'Inconnu pour trouver du nouveau
    """,
    """
    Sois sage ô ma Douleur et tiens-toi plus tranquille
    Tu réclamais le Soir il descend le voici
    Une atmosphère obscure enveloppe la ville
    Aux uns portant la paix aux autres le souci
    Pendant que des mortels la multitude vile
    Sous le fouet du Plaisir ce bourreau sans merci
    Va cueillir des remords dans la fête servile
    Ma Douleur donne-moi la main viens par ici
    """,
    """
    Souvent pour s'amuser les hommes d'équipage
    Prennent des albatros vastes oiseaux des mers
    Qui suivent indolents compagnons de voyage
    Le navire glissant sur les gouffres amers
    À peine les ont-ils déposés sur les planches
    Que ces rois de l'azur maladroits et honteux
    Laissent piteusement leurs grandes ailes blanches
    Comme des avirons traîner à côté d'eux
    Ce voyageur ailé comme il est gauche et veule
    Lui naguère si beau qu'il est comique et laid
    L'un agace son bec avec un brûle-gueule
    L'autre mime en boitant l'infirme qui volait
    Le Poète est semblable au prince des nuées
    Qui hante la tempête et se rit de l'archer
    Exilé sur le sol au milieu des huées
    Ses ailes de géant l'empêchent de marcher
    """,
    """
    Rappelez-vous l'objet que nous vîmes mon âme
    Ce beau matin d'été si doux
    Au détour d'un sentier une charogne infâme
    Sur un lit semé de cailloux
    Les jambes en l'air comme une femme lubrique
    Brûlante et suant les poisons
    Ouvrait d'une façon nonchalante et cynique
    Son ventre plein d'exhalaisons
    Et pourtant vous serez semblable à cette ordure
    À cette horrible infection
    Étoile de mes yeux soleil de ma nature
    Vous mon ange et ma passion
    Alors ô ma beauté dites à la vermine
    Qui vous mangera de baisers
    Que j'ai gardé la forme et l'essence divine
    De mes amours décomposés
    """,
    # ── RIMBAUD ──
    """
    A noir E blanc I rouge U vert O bleu voyelles
    Je dirai quelque jour vos naissances latentes
    A noir corset velu des mouches éclatantes
    Qui bombinent autour des puanteurs cruelles
    Golfes d'ombre E candeurs des vapeurs et des tentes
    Lances des glaciers fiers rois blancs frissons d'ombelles
    I pourpres sang craché rire des lèvres belles
    Dans la colère ou les ivresses pénitentes
    U cycles vibrements divins des mers virides
    Paix des pâtis semés d'animaux paix des rides
    Que l'alchimie imprime aux grands fronts studieux
    O suprême Clairon plein des strideurs étranges
    Silences traversés des Mondes et des Anges
    O l'Oméga rayon violet de Ses Yeux
    """,
    """
    On n'est pas sérieux quand on a dix-sept ans
    Un beau soir foin des bocks et de la limonade
    Des cafés tapageurs aux lustres éclatants
    On va sous les tilleuls verts de la promenade
    Les tilleuls sentent bon dans les bons soirs de juin
    L'air est parfois si doux qu'on ferme la paupière
    Le vent chargé de bruits la ville n'est pas loin
    A des parfums de vigne et des parfums de bière
    Voilà qu'on aperçoit un tout petit chiffon
    D'azur sombre encadré d'une petite branche
    Piqué d'une mauvaise étoile qui se fond
    Avec de doux frissons petite et toute blanche
    Nuit de juin Dix-sept ans On se laisse griser
    La sève est du champagne et vous monte à la tête
    On divague on se sent aux lèvres un baiser
    Qui palpite là comme une petite bête
    """,
    """
    Elle est retrouvée Quoi L'Éternité
    C'est la mer allée Avec le soleil
    Âme sentinelle Murmurons l'aveu
    De la nuit si nulle Et du jour en feu
    Des humains suffrages Des communs élans
    Là tu te dégages Et voles selon
    Jamais l'espérance Pas d'orietur
    Science et patience Le supplice est sûr
    Plus de lendemain Braises de satin
    Votre ardeur Est le devoir
    Elle est retrouvée Quoi L'Éternité
    C'est la mer allée Avec le soleil
    """,
    """
    Par les soirs bleus d'été j'irai dans les sentiers
    Picoté par les blés fouler l'herbe menue
    Rêveur j'en sentirai la fraîcheur à mes pieds
    Je laisserai le vent baigner ma tête nue
    Je ne parlerai pas je ne penserai rien
    Mais l'amour infini me montera dans l'âme
    Et j'irai loin bien loin comme un bohémien
    Par la Nature heureux comme avec une femme
    """,
    # ── VERLAINE ──
    """
    Les sanglots longs Des violons De l'automne
    Blessent mon cœur D'une langueur Monotone
    Tout suffocant Et blême quand Sonne l'heure
    Je me souviens Des jours anciens Et je pleure
    Et je m'en vais Au vent mauvais Qui m'emporte
    Deçà delà Pareil à la Feuille morte
    """,
    """
    Il pleure dans mon cœur Comme il pleut sur la ville
    Quelle est cette langueur Qui pénètre mon cœur
    Ô bruit doux de la pluie Par terre et sur les toits
    Pour un cœur qui s'ennuie Ô le chant de la pluie
    Il pleure sans raison Dans ce cœur qui s'écœure
    Quoi nulle trahison Ce deuil est sans raison
    C'est bien la pire peine De ne savoir pourquoi
    Sans amour et sans haine Mon cœur a tant de peine
    """,
    """
    Le ciel est par-dessus le toit Si bleu si calme
    Un arbre par-dessus le toit Berce sa palme
    La cloche dans le ciel qu'on voit Doucement tinte
    Un oiseau sur l'arbre qu'on voit Chante sa plainte
    Mon Dieu mon Dieu la vie est là Simple et tranquille
    Cette paisible rumeur-là Vient de la ville
    Qu'as-tu fait ô toi que voilà Pleurant sans cesse
    Dis qu'as-tu fait toi que voilà De ta jeunesse
    """,
    """
    La lune blanche Luit dans les bois
    De chaque branche Part une voix Sous la ramée
    Ô bien-aimée
    L'étang reflète Profond miroir
    La silhouette Du saule noir Où le vent pleure
    Rêvons c'est l'heure
    Un vaste et tendre Apaisement
    Semble descendre Du firmament Que l'astre irise
    C'est l'heure exquise
    """,
    """
    Je suis venu calme orphelin
    Vers les hommes des grandes villes
    Ils ne m'ont pas trouvé malin
    Je suis venu calme orphelin
    Richesse est à moi j'ai du pain
    Mais je n'ai plus guère de bile
    Je suis venu calme orphelin
    Vers les hommes des grandes villes
    """,
    # ── APOLLINAIRE ──
    """
    Sous le pont Mirabeau coule la Seine
    Et nos amours Faut-il qu'il m'en souvienne
    La joie venait toujours après la peine
    Vienne la nuit sonne l'heure
    Les jours s'en vont je demeure
    Les mains dans les mains restons face à face
    Tandis que sous Le pont de nos bras passe
    Des éternels regards l'onde si lasse
    Vienne la nuit sonne l'heure
    Les jours s'en vont je demeure
    L'amour s'en va comme cette eau courante
    L'amour s'en va Comme la vie est lente
    Et comme l'Espérance est violente
    Vienne la nuit sonne l'heure
    Les jours s'en vont je demeure
    """,
    """
    J'ai cueilli ce brin de bruyère
    L'automne est morte souviens-t'en
    Nous ne nous verrons plus sur terre
    Odeur du temps brin de bruyère
    Et souviens-toi que je t'attends
    """,
    """
    Mon beau navire ô ma mémoire
    Avons-nous assez navigué
    Dans une onde mauvaise à boire
    Avons-nous assez divagué
    De la belle aube au triste soir
    Adieu faux amour confondu
    Avec la femme qui s'éloigne
    Avec celle que j'ai perdue
    L'année dernière en Allemagne
    Et que je ne reverrai plus
    """,
    # ── HUGO ──
    """
    Demain dès l'aube à l'heure où blanchit la campagne
    Je partirai Vois-tu je sais que tu m'attends
    J'irai par la forêt j'irai par la montagne
    Je ne puis demeurer loin de toi plus longtemps
    Je marcherai les yeux fixés sur mes pensées
    Sans rien voir au dehors sans entendre aucun bruit
    Seul inconnu le dos courbé les mains croisées
    Triste et le jour pour moi sera comme la nuit
    Je ne regarderai ni l'or du soir qui tombe
    Ni les voiles au loin descendant vers Harfleur
    Et quand j'arriverai je mettrai sur ta tombe
    Un bouquet de houx vert et de bruyère en fleur
    """,
    """
    Ô souvenirs printemps aurore
    Ô souvenirs de nos jeunes années
    Quand nous errions au bois à peine écloses encore
    Les âmes que le temps depuis a moissonnées
    Le ciel était si bleu l'espoir était si doux
    La forêt frissonnait à l'haleine de mai
    La sève débordait dans les fleurs parfumées
    Et notre cœur chantait comme un oiseau charmé
    Printemps tu fuis et l'ombre vient nous surprendre
    Jeunesse adieu feuilles qui s'envolent au vent
    Où sont-ils les amis les rêves de nos vingt ans
    La mort a pris les uns les autres sont absents
    """,
    # ── ÉLUARD ──
    """
    La terre est bleue comme une orange
    Jamais une erreur les mots ne mentent pas
    Ils ne vous donnent plus à chanter
    Au tour des baisers de s'entendre
    Les fous et les amours
    Elle sa bouche d'alliance
    Tous les secrets tous les sourires
    Et quels vêtements d'indulgence
    À la croire toute nue
    """,
    """
    Je te l'ai dit pour les nuages
    Je te l'ai dit pour l'arbre de la mer
    Pour chaque vague pour les oiseaux dans les feuilles
    Pour les cailloux du bruit
    Pour les mains familières
    Pour l'œil qui devient visage ou paysage
    Et le sommeil lui rend le ciel de sa couleur
    Pour toute la nuit bue
    Pour la grille des routes
    Pour la fenêtre ouverte pour un front découvert
    Je te l'ai dit pour tes pensées pour tes paroles
    Toute caresse toute confiance se survivent
    """,
    # ── NERVAL ──
    """
    Je suis le Ténébreux le Veuf l'Inconsolé
    Le Prince d'Aquitaine à la Tour abolie
    Ma seule Étoile est morte et mon luth constellé
    Porte le Soleil noir de la Mélancolie
    Dans la nuit du Tombeau Toi qui m'as consolé
    Rends-moi le Pausilippe et la mer d'Italie
    La fleur qui plaisait tant à mon cœur désolé
    Et la treille où le Pampre à la Rose s'allie
    Suis-je Amour ou Phébus Lusignan ou Biron
    Mon front est rouge encor du baiser de la Reine
    J'ai rêvé dans la Grotte où nage la sirène
    Et j'ai deux fois vainqueur traversé l'Achéron
    Modulant tour à tour sur la lyre d'Orphée
    Les soupirs de la Sainte et les cris de la Fée
    """,
    # ── LAMARTINE ──
    """
    Ô temps suspends ton vol et vous heures propices
    Suspendez votre cours
    Laissez-nous savourer les rapides délices
    Des plus beaux de nos jours
    Assez de malheureux ici-bas vous implorent
    Coulez coulez pour eux
    Prenez avec leurs jours les soins qui les dévorent
    Oubliez les heureux
    Mais je demande en vain quelques moments encore
    Le temps m'échappe et fuit
    Je dis à cette nuit Sois plus lente et l'aurore
    Va dissiper la nuit
    Aimons donc aimons donc de l'heure fugitive
    Hâtons-nous jouissons
    L'homme n'a point de port le temps n'a point de rive
    Il coule et nous passons
    """,
    # ── MUSSET ──
    """
    J'ai perdu ma force et ma vie
    Et mes amis et ma gaîté
    J'ai perdu jusqu'à la fierté
    Qui faisait croire à mon génie
    Quand j'ai connu la Vérité
    J'ai cru que c'était une amie
    Quand je l'ai comprise et sentie
    J'en étais déjà dégoûté
    Et pourtant elle est éternelle
    Et ceux qui se sont passés d'elle
    Ici-bas ont tout ignoré
    Dieu parle il faut qu'on lui réponde
    Le seul bien qui me reste au monde
    Est d'avoir quelquefois pleuré
    """,
    # ── LABÉ ──
    """
    Baise m'encor rebaise moy et baise
    Donne m'en un de tes plus savoureux
    Donne m'en un de tes plus amoureux
    Je t'en rendrai quatre plus chauds que braise
    Las te plains-tu ça que je ne desse
    Encore un baiser donne m'en donc deux
    Ainsi le temps nos jours semblera mieux
    Le temps perdu en amour jamais ne pèse
    """,
    # ── Poèmes modernes ──
    """
    Le silence est d'or quand la parole est d'argent
    Mais le poème est de feu quand la nuit est d'encre
    J'écris sur la peau du monde avec des mots de vent
    Et chaque syllabe est une étoile qui sombre
    Dans l'océan du sens où naviguent les rêves
    Je cherche le rivage où les souvenirs crèvent
    Comme des bulles d'air à la surface de l'eau
    Le temps est un sculpteur qui travaille au couteau
    """,
    """
    Dans le jardin secret de ma mémoire endormie
    Les roses du passé fleurissent sans raison
    Chaque pétale tombé raconte une saison
    Chaque épine plantée dessine une infamie
    Le vent de l'oubli souffle sur les plates-bandes
    Emportant les parfums des amours disparues
    Ne reste que le sel des larmes répandues
    Et l'écho lointain des anciennes sarabandes
    """,
    """
    Je voudrais être l'ombre qui protège ton sommeil
    Le souffle qui caresse tes cheveux au réveil
    La vague qui t'emporte vers des îles lointaines
    Où le soleil couchant peint les heures sereines
    Je voudrais être l'arbre où tu viens t'adosser
    Le livre que tu lis sans pouvoir le poser
    La chanson qui te suit dans les rues de ta ville
    Le silence complice d'une attente fébrile
    """,
    """
    La ville s'endort sous un manteau de brume
    Les réverbères tissent des fils de lumière
    Un chat traverse la rue comme une plume
    Et la nuit pose ses doigts sur mes paupières
    Au loin le métro gronde comme un orage
    Une fenêtre s'allume douzième étage
    Quelqu'un qui veille comme moi dans la cité
    Quelqu'un qui écrit pour ne pas oublier
    """,
    """
    Tu es le phare dans ma tempête intérieure
    Le nord magnétique de ma boussole affolée
    La note tenue dans ma symphonie mineure
    L'étoile qui guide ma barque esseulée
    Sans toi je suis un livre sans lecteur
    Une partition sans musicien
    Un jardin sans jardinier une fleur
    Un navire sans capitaine un rien
    """,
    """
    Apprends-moi la patience des pierres
    La sagesse des arbres centenaires
    La paix des lacs à l'aube naissante
    Le courage des vagues incessantes
    Apprends-moi le silence des neiges
    La douceur des soirs de sortilège
    La force tranquille des rivières
    Et la beauté des choses éphémères
    """,
    """
    Il y a des matins où le monde est trop lourd
    Où chaque pas résonne comme un tambour funèbre
    Où l'âme se recroqueville dans son velours
    Et refuse de croire aux promesses des zèbres
    Mais il y a aussi des soirs où tout s'allège
    Où le poids du jour se dissout dans le crépuscule
    Où la nuit bienveillante enveloppe de neige
    Les blessures du jour et leurs herbes minuscules
    """,
    """
    La poésie n'est pas dans les mots qu'on aligne
    Elle est dans le silence entre deux respirations
    Dans le battement d'aile d'un papillon qui cligne
    Dans l'écho d'un regard entre deux passions
    La poésie n'est pas dans les vers qu'on compose
    Elle est dans la façon dont tu baisses les yeux
    Dans la courbe fragile et douce de ta pose
    Dans l'intervalle exact entre nous deux
    """,
]

# ═══════════════════════════════════════════════════════════════════════════════
# PPMI + SVD ENCODER
# ═══════════════════════════════════════════════════════════════════════════════

STOPWORDS = {'le','la','les','de','des','du','un','une','et','est','a','que','qui',
             'quoi','dans','sur','pour','avec','par','en','pas','plus','tout','tous',
             'ce','cet','cette','ces','son','sa','ses','leur','leurs','au','aux','ou',
             'donc','car','aussi','mais','comme','bien','très','trop','peu','alors',
             'the','is','are','of','in','on','at','to','and','it','my','me','you',
             'ne','se','te','nous','vous','ils','elles','lui','leur','mon','ton','mi'}

def tokenize(text: str) -> List[str]:
    """Tokenise un texte poétique en mots significatifs."""
    text = text.lower()
    for a, b in [('é','e'),('è','e'),('ê','e'),('ë','e'),('à','a'),('â','a'),
                 ('ù','u'),('û','u'),('ô','o'),('î','i'),('ï','i'),('ç','c'),
                 ('œ','oe')]:
        text = text.replace(a, b)
    words = re.findall(r"[a-z]{2,}", text)
    return [w for w in words if w not in STOPWORDS]

def build_poetry_embedding(dim: int = 64, window: int = 5):
    """
    Construit un plongement sémantique à partir du corpus poétique.
    
    Méthode : PPMI (co-occurrence fenêtrée) → SVD → vecteurs complexes.
    """
    log.info(f"Construction embedding poétique: {len(POETIC_CORPUS)} poèmes")
    
    # 1. Tokeniser tout le corpus
    all_tokens = []
    for poem in POETIC_CORPUS:
        all_tokens.append(tokenize(poem))
    
    # 2. Vocabulaire
    word_counts = Counter()
    for tokens in all_tokens:
        word_counts.update(tokens)
    
    # Garder les mots qui apparaissent au moins 2 fois
    vocab = {w: i for i, (w, c) in enumerate(word_counts.items()) if c >= 2}
    log.info(f"  Vocabulaire: {len(vocab)} mots")
    
    if len(vocab) < 50:
        log.warning("Vocabulaire trop petit — utilisation du fallback")
        return None
    
    # 3. Co-occurrence fenêtrée
    cooc = Counter()
    for tokens in all_tokens:
        indices = [vocab[w] for w in tokens if w in vocab]
        for i, center in enumerate(indices):
            start = max(0, i - window)
            end = min(len(indices), i + window + 1)
            for j in range(start, end):
                if i != j:
                    cooc[(center, indices[j])] += 1
    
    log.info(f"  Co-occurrences: {len(cooc)} paires")
    
    # 4. Matrice PPMI (sparse)
    n = len(vocab)
    total = sum(cooc.values())
    total += 1  # éviter division par zéro
    
    # Fréquences marginales
    word_freq = np.zeros(n)
    for (i, j), count in cooc.items():
        if 0 <= i < n:
            word_freq[i] += count
    
    # Construire la matrice sparse (filtrer les indices valides)
    rows, cols, data = [], [], []
    for (i, j), count in cooc.items():
        if 0 <= i < n and 0 <= j < n:
            p_ij = count / total
            p_i = max(word_freq[i], 1) / total
            p_j = max(word_freq[j], 1) / total
            pmi = math.log(p_ij / (p_i * p_j) + 1e-10)
            ppmi = max(0, pmi)  # Positive PMI
            
            if ppmi > 0:
                rows.append(i)
                cols.append(j)
                data.append(ppmi)
    
    from scipy.sparse import csr_matrix
    ppmi_matrix = csr_matrix((data, (rows, cols)), shape=(n, n))
    log.info(f"  Matrice PPMI: {ppmi_matrix.nnz} éléments non-nuls")
    
    # 5. SVD — utiliser numpy directement pour éviter les problèmes de sparse
    # Convertir en dense (assez petit: 230×230)
    ppmi_dense = ppmi_matrix.toarray() if hasattr(ppmi_matrix, 'toarray') else ppmi_matrix
    log.info(f"  SVD: {n}×{n} dense")
    
    try:
        U, s, Vt = np.linalg.svd(ppmi_dense, full_matrices=False)
        k = min(32, len(s))
        U = U[:, :k]
        s = s[:k]
    except Exception:
        log.warning("SVD échoué, réduction de dimension")
        k = min(16, n - 1)
        U = np.random.randn(n, k).astype(np.float64)
        U = U / np.linalg.norm(U, axis=1, keepdims=True)
    
    # Trier par valeurs singulières décroissantes
    idx = np.argsort(-s)
    U = U[:, idx]
    s = s[idx]
    
    log.info(f"  U shape: {U.shape}, n={n}")
    
    # 6. Vecteurs complexes
    complex_dim = k // 2
    if complex_dim < 1:
        complex_dim = 1
    vectors = {}
    idx_to_word = {i: w for w, i in vocab.items()}
    
    for i in range(min(n, U.shape[0])):
        if i not in idx_to_word:
            continue
        real_part = U[i, :complex_dim]
        imag_part = U[i, complex_dim:2*complex_dim] if 2*complex_dim <= k else np.zeros(complex_dim)
        vec = real_part + 1j * imag_part
        norm = np.linalg.norm(vec)
        if norm > 1e-10:
            vec /= norm
        vectors[idx_to_word[i]] = vec
    
    log.info(f"  Vecteurs créés: {len(vectors)} mots dans C^{complex_dim}")
    
    return vectors, complex_dim


def save_embedding(vectors: Dict[str, np.ndarray], complex_dim: int, path: str):
    """Sauvegarde les vecteurs au format .npz."""
    words = list(vectors.keys())
    n = len(words)
    dim = vectors[words[0]].shape[0]
    
    real = np.zeros((n, dim), dtype=np.float32)
    imag = np.zeros((n, dim), dtype=np.float32)
    
    for i, w in enumerate(words):
        v = vectors[w]
        real[i] = v.real.astype(np.float32)
        imag[i] = v.imag.astype(np.float32)
    
    np.savez_compressed(path,
        words=np.array(words, dtype=object),
        real=real, imag=imag,
        complex_dim=np.array([complex_dim]),
    )
    log.info(f"Sauvegardé: {path} ({n} mots, dim={complex_dim})")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  📜 POETRY EMBEDDING — Encodeur poétique français         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--stats', action='store_true')
    args = parser.parse_args()
    
    if args.stats:
        path = _ENGINE_DIR / 'data' / 'poetry_embedding.npz'
        if path.exists():
            data = np.load(str(path), allow_pickle=True)
            print(f"Mots: {len(data['words'])}")
            print(f"Dim:  {data['complex_dim']}")
            print(f"Taille: {path.stat().st_size / 1024:.0f} KB")
            # Montrer quelques mots proches
            words = list(data['words'])
            print(f"Échantillon: {', '.join(w for w in words[:30] if len(w) > 3)[:20]}")
        else:
            print("Fichier non trouvé. Lancez sans --stats pour l'entraîner.")
    else:
        result = build_poetry_embedding(dim=64, window=5)
        if result:
            vectors, dim = result
            path = _ENGINE_DIR / 'data' / 'poetry_embedding.npz'
            path.parent.mkdir(parents=True, exist_ok=True)
            save_embedding(vectors, dim, str(path))
            print(f"\n✅ Encodeur poétique sauvegardé: {path}")
            print(f"   {len(vectors)} mots, dimension C^{dim}")
        else:
            print("\n⚠️ Échec de l'entraînement — vocabulaire insuffisant")
