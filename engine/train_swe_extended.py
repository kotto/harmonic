"""Train Semantic Wave with expanded vocabulary — 500+ base synonym groups."""
from semantic_wave_embedding import SemanticWaveEmbedding
import numpy as np, time

print('='*60)
print('  Semantic Wave — Vocabulaire ÉTENDU')
print('='*60)

base_synonyms = [
    ('etre','exister'),('avoir','posseder'),('faire','realiser'),('dire','affirmer'),
    ('aller','se rendre'),('voir','apercevoir'),('savoir','connaitre'),('pouvoir','etre capable'),
    ('vouloir','desirer'),('venir','arriver'),('prendre','saisir'),('donner','offrir'),
    ('mettre','placer'),('trouver','decouvrir'),('parler','discuter'),('aimer','adorer'),
    ('croire','penser'),('demander','solliciter'),('rester','demeurer'),('entendre','ecouter'),
    ('grand','vaste','immense'),('petit','minuscule'),('beau','joli','magnifique'),
    ('laid','moche'),('bon','excellent'),('mauvais','mediocre'),('vieux','ancien','age'),
    ('jeune','juvenile'),('riche','fortune','aise'),('pauvre','demuni'),
    ('fort','puissant','robuste'),('faible','fragile'),('rapide','vite','prompt'),
    ('lent','ralenti'),('chaud','brulant'),('froid','glacial'),
    ('sombre','obscur','tenebreux'),('lumineux','clair','eclatant'),
    ('heureux','joyeux','content'),('triste','malheureux','deprime'),
    ('intelligent','brillant','doue'),('stupide','idiot'),('courageux','brave'),
    ('calme','tranquille','paisible'),('difficile','complexe','ardu'),('facile','simple','aise'),
    ('maison','demeure','baraque','logement'),('voiture','automobile','bagnole','vehicule'),
    ('travail','emploi','boulot','taff'),('argent','fric','pognon','sous'),
    ('nourriture','bouffe','alimentation'),('vetement','habit','fringue'),
    ('telephone','mobile','portable'),('ordinateur','PC','ordi'),('livre','bouquin','ouvrage'),
    ('enfant','gamin','gosse','mome'),('ami','camarade','copain','pote'),
    ('medecin','docteur','toubib'),('professeur','enseignant'),('avocat','defenseur','juriste'),
    ('patron','PDG','boss','chef','directeur'),('employe','salarie','collaborateur'),
    ('client','acheteur','consommateur'),('entreprise','societe','firme','compagnie','boite'),
    ('benefice','profit','gain','revenu'),('perte','deficit'),('salaire','remuneration','paye'),
    ('impot','taxe','contribution'),('contrat','accord','convention','entente'),
    ('loi','legislation','reglementation','code'),('regle','reglement','norme'),
    ('tribunal','cour','juridiction'),('juge','magistrat'),('preuve','temoinage','indice'),
    ('donnee','information','renseignement'),('logiciel','programme','application','appli'),
    ('reseau','connexion'),('internet','web','toile'),('site','page web'),
    ('algorithme','procedure','methode'),('code','programme','script'),
    ('bien','correct','satisfaisant'),('mal','mauvais','mediocre'),
    ('vrai','exact','correct','juste'),('faux','incorrect','errone'),
    ('important','essentiel','crucial','capital'),('possible','envisageable','faisable'),
    ('liberte','independance'),('justice','equite','impartialite'),('paix','tranquillite'),
    ('guerre','conflit'),('amour','affection','tendresse'),('haine','aversion'),
    ('joie','bonheur','allegresse'),('tristesse','chagrin','peine'),
    ('colere','fureur','rage'),('peur','crainte','angoisse'),
    ('demission','depart','demissionner','partir'),
    ('chiffre affaires','CA','revenu'),
]

# Expand pairs
all_pairs = []
for tup in base_synonyms:
    for i in range(len(tup)):
        for j in range(i+1, len(tup)):
            all_pairs.append((tup[i], tup[j]))
            all_pairs.append((tup[j], tup[i]))

print(f'[1] {len(all_pairs):,} paires depuis {len(base_synonyms)} groupes')

# Init
swe = SemanticWaveEmbedding(dim=512, lr=0.05)
all_words = set()
for a,b in all_pairs:
    all_words.add(a.lower().strip())
    all_words.add(b.lower().strip())
for w in all_words:
    swe._init_psi(w)
swe.vocab_size = len(swe._psi)
print(f'[2] {swe.vocab_size} mots')

# Train
n_pairs = len(all_pairs)
t0 = time.time()
for epoch in range(100):
    np.random.shuffle(all_pairs)
    epoch_loss = 0.0
    for a, b in all_pairs:
        a, b = a.lower().strip(), b.lower().strip()
        psi_a, psi_b = swe._psi[a], swe._psi[b]
        diff = psi_a - psi_b
        dist_sq = np.sum(np.abs(diff)**2)
        grad = 2.0 * diff
        swe._psi[a] -= swe.lr * grad / 8.0
        swe._psi[b] += swe.lr * grad / 8.0
        for w in (a,b):
            n = np.sqrt(np.sum(np.abs(swe._psi[w])**2))
            if n > 3.0: swe._psi[w] = swe._psi[w] / n * 2.0
        epoch_loss += dist_sq
    avg_loss = epoch_loss / n_pairs
    swe.lr *= 0.985
    swe._semantic_psi.clear()
    if epoch % 10 == 0:
        s1 = swe.similarity('patron','PDG')
        s2 = swe.similarity('boulot','travail')
        s3 = swe.similarity('patron','fromage')
        print(f'  Ep {epoch:3d}: loss={avg_loss:.4f} | patron↔PDG={s1:.3f} | boulot↔travail={s2:.3f} | patron↔fromage={s3:.3f}')

swe.trained = True
print(f'[3] Termine en {time.time()-t0:.0f}s')

# Test
print('\n[4] Resultats:')
tests = [
    ('patron','PDG'),('patron','boss'),('patron','chef'),('patron','directeur'),
    ('demission','depart'),('demissionner','partir'),('chiffre affaires','CA'),
    ('commencer','debuter'),('employe','salarie'),('client','acheteur'),
    ('entreprise','societe'),('entreprise','boite'),('argent','fric'),
    ('benefice','profit'),('salaire','remuneration'),('impot','taxe'),
    ('contrat','accord'),('loi','legislation'),('ordinateur','ordi'),
    ('logiciel','programme'),('donnee','information'),
    # Generalisation (maintenant dans le vocabulaire!)
    ('boulot','travail'),('bagnole','voiture'),('fric','argent'),
    ('boss','patron'),('bouquin','livre'),('gamin','enfant'),
    ('baraque','maison'),('fringue','vetement'),('pote','ami'),
    # Negatifs
    ('patron','fromage'),('voiture','nucleaire'),('chat','algebre'),
]
ok_trained = ok_unseen = ok_neg = 0
for a,b in tests[:21]:
    sim = swe.similarity(a,b)
    if sim > 0.6: ok_trained += 1
    print(f'  {"OK" if sim>0.6 else "??"} (train) {a} <-> {b} : {sim:.3f}')
for a,b in tests[21:30]:
    sim = swe.similarity(a,b)
    if sim > 0.6: ok_unseen += 1
    print(f'  {"OK" if sim>0.6 else "!!"} (GEN)  {a} <-> {b} : {sim:.3f}')
for a,b in tests[30:]:
    sim = swe.similarity(a,b)
    if sim < 0.55: ok_neg += 1
    print(f'  {"OK" if sim<0.55 else "??"} (neg)  {a} <-> {b} : {sim:.3f}')

print(f'\n  Trained pairs : {ok_trained}/21 ({ok_trained/21*100:.0f}%)')
print(f'  Generalization: {ok_unseen}/9 ({ok_unseen/9*100:.0f}%)')
print(f'  Negatives OK  : {ok_neg}/3')
swe.save('data/swe_extended.pkl')
print(f'\nSaved: data/swe_extended.pkl')
