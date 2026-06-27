# =========================================================================
# Transformation PPMI (Pointwise Mutual Information) avec lissage Levy & Goldberg
# =========================================================================
def construire_ppmi(cooc: Dict[int, Dict[int, int]],
                    freq: Dict[int, int],
                    n_textes: int,
                    seuil_min_count: int = 1,
                    alpha: float = 0.75) -> Dict[int, Dict[int, float]]:
    """Transforme la matrice de co-occurrence en PPMI avec lissage Levy & Goldberg.

    Formule standard:
      PMI(t1,t2) = log2(N * count(t1,t2) / (freq[t1] * freq[t2]))

    Mais sur petit corpus (108 textes), la PMI brute sur-evalue les paires rares.
    On utilise le context distribution smoothing de Levy & Goldberg (2015) :
      
      PMI_alpha(t1,t2) = log(p_xy / (p_x * p_y_smoothed))
      
      ou:
        p_xy = count(t1,t2) / N_cooc         (probabilite jointe)
        p_x  = freq[t1] / sum(freq)           (probabilite marginale de t1)
        p_y_smoothed = freq[t2]^alpha / sum(freq^alpha)   (marginale lissée de t2)
        alpha = 0.75 (recommande par Levy & Goldberg)

    Ce lissage aplatit la distribution des frequences contextuelles et empeche
    les paires rares (vues dans 1-2 textes) d'avoir des PMI artificiellement eleves.

    PPMI = max(0, PMI_alpha)

    Exemple avec alpha=0.75:
      - Stopword "de" (freq=104) avec "la" (freq=99), count=99 :
        p_xy=99/51068, p_x=104/861, p_y_smoothed=99^0.75/sum(freq^0.75)
        PMI ≈ 0.0 → elimine par PPMI
      - Token domaine "ghana" (freq=5) avec "empire" (freq=8), count=4 :
        PMI ≈ 2.8 → garde (signal semantique fort)

    Args:
        cooc: Matrice de co-occurrence (counts bruts)
        freq: Frequence de chaque token
        n_textes: Ignore (conserve pour compatibilite API)
        seuil_min_count: Ignorer les co-occurrences < ce seuil (defaut: 1)
        alpha: Exposant de lissage contextuel (defaut: 0.75)

    Returns:
        ppmi[t1][t2] = valeur PPMI (float, > 0), arrondie a 4 decimales
    """
    # Total des co-occurrences (nombre total de paires)
    N_cooc = sum(c for row in cooc.values() for c in row.values())
    
    # Frequences lissées : freq[t]^alpha
    smoothed = {t: f ** alpha for t, f in freq.items()}
    total_smoothed = sum(smoothed.values())
    
    # Frequences brutes pour p_x
    total_freq = sum(freq.values())
    
    ppmi: Dict[int, Dict[int, float]] = {}
    total_pairs_avant = sum(len(v) for v in cooc.values())
    
    for t1, voisins in cooc.items():
        p_x = freq.get(t1, 1) / total_freq
        if p_x <= 0:
            continue
        
        ppmi[t1] = {}
        for t2, count in voisins.items():
            if count < seuil_min_count:
                continue
            
            # Probabilite conjointe
            p_xy = count / N_cooc
            
            # Probabilite marginale lissée de t2
            p_y_smoothed = smoothed.get(t2, 0) / total_smoothed
            if p_y_smoothed <= 0:
                continue
            
            # PMI avec lissage (log naturel, pas log2 - seule l'echelle change)
            pmi = math.log(p_xy / (p_x * p_y_smoothed) + 1e-12)
            
            if pmi > 0:  # Seules les valeurs positives (PPMI)
                ppmi[t1][t2] = round(pmi, 4)
    
    total_pairs_apres = sum(len(v) for v in ppmi.values())
    reduction = (1 - total_pairs_apres / total_pairs_avant) * 100
    print(f"  PPMI construite: {len(ppmi)} tokens, {total_pairs_apres} paires")
    print(f"  Reduction: {reduction:.1f}% (paires non-informatives eliminees)")
    print(f"  Lissage alpha={alpha}: les paires rares ne sont plus sur-ponderees")
    
    return ppmi
    print(f"  Lissage alpha={alpha}: les paires rares ne sont plus sur-ponderees")
    
    return ppmi


# =========================================================================
# Construction de la matrice de co-occurrence
# =========================================================================
