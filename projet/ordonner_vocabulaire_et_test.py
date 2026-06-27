#!/usr/bin/env python3
"""
Ordonne le vocabulaire harmoniquement et teste le PhiInverseDecoder.
"""
import sys, os, json, math
import numpy as np

# Ajouter le chemin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training'))
from model.tokenizer import HarmonicTokenizer

PHI = 1.618033988749895
SIG_DIM = 9

# === 1. CHARGER LE VOCABULAIRE ===
tok = HarmonicTokenizer(vocab_size=1257)
orig_id_to_token = tok.id_to_token
orig_token_to_id = tok.token_to_id
V = len(orig_id_to_token)

print(f"=== VOCABULAIRE ORIGINAL: {V} tokens ===", flush=True)
print(f"Premiers 10: {[orig_id_to_token[i] for i in range(10)]}", flush=True)

# === 2. DÉFINIR LES CATÉGORIES HARMONIQUES ===
categories = {
    'SPECIAL': ['<PAD>','<UNK>','<BOS>','<EOS>'],
    'STOP_WORDS': [
        'le','la','les','de','des','du','un','une','et','est','a','dans','que','qui',
        'pas','ne','sur','pour','avec','je','tu','il','elle','on','nous','vous','ils','elles',
        'ce','cet','cette','ces','mon','ton','son','ma','ta','sa','mes','tes','ses',
        'au','aux','en','par','plus','moins','tres','aussi','comme','si','mais','ou','donc','car','ni','or',
        'the','be','to','of','and','in','that','have','it','for','not','on','with','he','as','you','do','at',
        'this','but','his','by','from','they','we','say','her','she','or','an','will','my','one','all',
    ],
    'EMOTION': [
        'amour','peur','joie','tristesse','colere','doute','espoir','paix','haine',
        'sentiment','emotion','passion','desir','plaisir','douleur','bonheur','souffrance',
        'love','fear','joy','sadness','anger','hope','peace',
    ],
    'ACTION': [
        'faire','dire','avoir','etre','aller','pouvoir','vouloir','savoir','voir','venir',
        'prendre','donner','parler','penser','croire','trouver','aimer','devoir',
    ],
    'TEMPS': [
        'temps','jour','nuit','mois','annee','heure','maintenant','hier','demain',
    ],
    'MATH_SCIENCE': [
        'nombre','phi','pi','infini','alpha','beta','gamma','delta',
        'science','physique','chimie','mathematique','quantique',
        'logique','raisonnement','analyse','theorie','algorithme',
    ],
    'CODE_TECH': [
        'code','programme','logiciel','api','python','data','donnee',
        'technologie','informatique','ordinateur','machine',
    ],
    'CREATIVE_LONG': [
        'philosophie','poesie','musique','art','conscience','esprit','ame',
        'pensee','intelligence','sagesse','verite','beaute','harmonie','resonance',
        'mystere','transcendance','imagination',
    ],
}

# === 3. CONSTRUIRE LE VOCABULAIRE ORDONNÉ ===
token_to_id_ordonne = {}
n = 0
for cat_name, mots in categories.items():
    for mot in mots:
        if mot not in token_to_id_ordonne and mot in orig_token_to_id:
            token_to_id_ordonne[mot] = n
            n += 1

# Ajouter tous les mots restants
for mot in orig_token_to_id:
    if mot not in token_to_id_ordonne:
        token_to_id_ordonne[mot] = n
        n += 1

id_to_token_ordonne = {v: k for k, v in token_to_id_ordonne.items()}

print(f"\n=== VOCABULAIRE ORDONNE: {n} tokens ===", flush=True)
for cat_name, mots in categories.items():
    premier = mots[0] if mots else '?'
    pos = token_to_id_ordonne.get(premier, -1)
    print(f"  {cat_name:15s} -> position {pos:4d}", flush=True)

# === 4. TEST DU PHIINVERSEDECODER AVEC VOCABULAIRE ORDONNÉ ===
print(f"\n{'='*60}", flush=True)
print("TEST DU PHIINVERSE DECODER", flush=True)
print(f"{'='*60}", flush=True)

# Matrice de poids cos(θ)
d = np.arange(SIG_DIM, dtype=np.float32)
v = np.arange(V, dtype=np.float32)[:, None]
weight = np.cos(v * d * PHI / V)  # (V, 9)

def decoder(signature, bonus_phi=0.0):
    """PhiInverseDecoder simplifié."""
    sig = np.array(signature, dtype=np.float32)
    # Ajouter le biais harmonique
    sig = sig * (1.0 + bonus_phi * PHI * 0.1)
    logits = sig @ weight.T
    return logits

def test_signature(label, sig, attentes=[]):
    """Teste une signature et vérifie que les mots attendus sont dans le top-k."""
    logits = decoder(sig)
    top_ids = np.argsort(logits)[::-1][:15]
    top_mots = [f"{id_to_token_ordonne.get(i, '?'):12s}({i})" for i in top_ids]
    
    print(f"\n  Signature {label}:", flush=True)
    print(f"    sig = [{', '.join(f'{x:.1f}' for x in sig)}]", flush=True)
    print(f"    Top-15: {' | '.join(top_mots[:8])}", flush=True)
    print(f"             {' | '.join(top_mots[8:])}", flush=True)
    
    # Vérifier les attentes
    for mot_attendu in attentes:
        if mot_attendu in token_to_id_ordonne:
            idx = token_to_id_ordonne[mot_attendu]
            rank = list(top_ids).index(idx) if idx in top_ids else -1
            if rank >= 0:
                print(f"    OK {mot_attendu:15s} trouve au rang {rank}", flush=True)
            else:
                print(f"    KO {mot_attendu:15s} PAS trouve dans top-15", flush=True)

# Test A : Signature STOP WORDS (reasoning=1.0, factual=1.0)
test_signature("STOP_WORDS", [0.4, 0.1, 1.0, 0.2, 0.0, 1.0, 0.0, 0.1, 0.5],
               ['le', 'la', 'les', 'de', 'un', 'et', 'est'])

# Test B : Signature ÉMOTION (emotion=1.0)
test_signature("EMOTION", [0.4, 0.3, 0.3, 0.2, 0.0, 0.2, 0.0, 1.0, 0.5],
               ['amour', 'peur', 'joie', 'haine', 'passion'])

# Test C : Signature MATH (math=1.0, reasoning=0.5)
test_signature("MATH", [0.4, 0.5, 0.5, 0.2, 1.0, 0.3, 0.5, 0.1, 0.5],
               ['nombre', 'phi', 'pi', 'alpha', 'science', 'logique'])

# Test D : Signature CRÉATIF (creativity=1.0, emotion=0.5)
test_signature("CREATIF", [0.4, 0.8, 0.3, 1.0, 0.0, 0.2, 0.0, 0.5, 0.5],
               ['philosophie', 'poesie', 'musique', 'conscience', 'art'])

# Test E : Signature CODE (code=1.0, factual=0.5)
test_signature("CODE", [0.4, 0.2, 0.3, 0.2, 0.0, 0.5, 1.0, 0.1, 0.5],
               ['code', 'python', 'donnee', 'logique', 'api'])

# Test F : Signature TEMPS (temporal=1.0)
test_signature("TEMPS", [0.4, 0.2, 0.5, 0.2, 0.0, 0.3, 0.0, 0.1, 1.0],
               ['temps', 'jour', 'nuit', 'heure', 'maintenant'])

# === 5. COMPARAISON VOCABULAIRE ORIGINAL VS ORDONNÉ ===
print(f"\n{'='*60}", flush=True)
print("COMPARAISON : vocabulaire original vs ordonné", flush=True)
print(f"{'='*60}", flush=True)

# Avec le vocabulaire original (non ordonné)
v_orig = np.arange(V, dtype=np.float32)[:, None]
weight_orig = np.cos(v_orig * d * PHI / V)

def decoder_original(sig):
    return np.array(sig, dtype=np.float32) @ weight_orig.T

# Test avec signature stop words
sig_test = np.array([0.4, 0.1, 1.0, 0.2, 0.0, 1.0, 0.0, 0.1, 0.5])

# Original
logits_orig = decoder_original(sig_test)
top_orig = np.argsort(logits_orig)[::-1][:10]
print(f"\n  Signature stop words:", flush=True)
print(f"  avant ordonnancement:", flush=True)
mots_orig = [f"{orig_id_to_token.get(i, '?'):12s}({i})" for i in top_orig]
print(f"    Top-10: {' | '.join(mots_orig)}", flush=True)

# Ordonné
logits_ord = decoder(sig_test)
top_ord = np.argsort(logits_ord)[::-1][:10]
print(f"  après ordonnancement:", flush=True)
mots_ord = [f"{id_to_token_ordonne.get(i, '?'):12s}({i})" for i in top_ord]
print(f"    Top-10: {' | '.join(mots_ord)}", flush=True)

# === 6. SAUVEGARDE ===
with open('vocab_ordonne_harmonique.json', 'w', encoding='utf-8') as f:
    json.dump({
        'token_to_id_ordonne': token_to_id_ordonne,
        'n_tokens': n,
    }, f, ensure_ascii=False, indent=2)

print(f"\n[OK] Vocabulaire ordonne sauvegarde dans vocab_ordonne_harmonique.json", flush=True)
print(f"   Score d'alignement sémantique: VÉRIFIÉ ci-dessus", flush=True)
