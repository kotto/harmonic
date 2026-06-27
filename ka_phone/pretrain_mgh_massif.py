#!/usr/bin/env python3
"""
PRÉ-ENTRAÎNEMENT MASSIF MGH — 500k+ phrases
============================================
À exécuter UNE SEULE FOIS avant de lancer le serveur.
Peut durer 1-2 heures. Produit un MGH ultra-riche avec
vocabulaire technique, scientifique et structures complexes.

Usage :
  python ka_phone/pretrain_mgh_massif.py --n 500000   # 500k phrases (~1h)
  python ka_phone/pretrain_mgh_massif.py --n 1000000  # 1M phrases (~2h)
"""

import os, sys, time, argparse

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from mgh_generation import MGH, MGH_FILE, BIGRAM_FILE

def main():
    parser = argparse.ArgumentParser(description="Pré-entraînement massif MGH")
    parser.add_argument("--n", type=int, default=500000, help="Nombre de phrases (défaut: 500k)")
    parser.add_argument("--resume", action="store_true", help="Reprendre l'entraînement existant")
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"PRÉ-ENTRAÎNEMENT MASSIF MGH — {args.n:,} phrases")
    print("=" * 70)
    
    if args.resume:
        mgh = MGH()
        bigrams_avant = len(mgh.bigram_index)
        print(f"  Reprise : {bigrams_avant:,} bigrammes existants")
    else:
        # Supprimer les anciens fichiers pour repartir de zéro
        if os.path.exists(MGH_FILE):
            os.remove(MGH_FILE)
        if os.path.exists(BIGRAM_FILE):
            os.remove(BIGRAM_FILE)
        mgh = MGH()
        bigrams_avant = 0
        print(f"  Nouvel entraînement depuis zéro")
    
    t0 = time.time()
    
    # Entraînement massif
    count = mgh.entrainer_massif(n_phrases=args.n)
    
    dt = time.time() - t0
    minutes = dt / 60
    bigrams_apres = len(mgh.bigram_index)
    nouveaux = bigrams_apres - bigrams_avant
    
    print(f"\n{'='*70}")
    print(f"ENTRAÎNEMENT TERMINÉ")
    print(f"{'='*70}")
    print(f"  Phrases générées  : {args.n:,}")
    print(f"  Bigrammes créés   : {nouveaux:,} ({bigrams_apres:,} total)")
    print(f"  Vocabulaire       : {len(mgh.vocab)} mots")
    print(f"  Énergie hologramme: {float(np.sum(np.abs(mgh.H)**2)):.0f}")
    print(f"  Durée             : {minutes:.1f} min")
    print(f"  Vitesse           : {args.n/dt:.0f} phrases/s")
    print(f"{'='*70}")
    
    # Sauvegarde finale
    mgh._save()
    print(f"\n  ✅ Sauvegardé : {MGH_FILE}")
    print(f"  ✅ Sauvegardé : {BIGRAM_FILE}")
    print(f"\n  Le serveur KA Phone peut maintenant être lancé :")
    print(f"    python ka_phone/ka_phone_server.py --port 8900")

if __name__ == "__main__":
    import numpy as np
    main()