import os, time
os.environ['HARMONIC_NO_LLM'] = '1'
from harmonic_ai import HarmonicAI

ai = HarmonicAI(enable_bootstrapper=False)

tests = [
    ('Write exactly 3 sentences about the Sun.', 'INSTRUCTION'),
    ('If a train travels 60 km/h for 2.5 hours, how far does it go?', 'MATH'),
    ('What is the largest country in the world by area?', 'GEO'),
    ('Why do leaves change color in autumn?', 'SCIENCE'),
    ('Write a creative one-line story about a robot learning to dream.', 'WRITING'),
    ('If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?', 'REASONING'),
    ('Explique brievement ce qu est la photosynthese.', 'FR_SCIENCE'),
    ('Who painted the Mona Lisa?', 'CULTURE'),
    ('What ocean lies between Africa and Australia?', 'GEO'),
    ('Can you help me understand what gravity is?', 'CONVERSATION'),
    ('Name three countries in South America and their capitals.', 'MULTI_PART'),
    ('What is an algorithm?', 'DEFINITION'),
    ('Quand a eu lieu la chute du mur de Berlin?', 'FR_HIST'),
    ('Is drinking coffee good or bad for you?', 'NUANCE'),
    ('What is 25 percent of 200?', 'MATH'),
]

print('=' * 65)
print('EVALUATION LM ARENA - Real Votant Perspective')
print('=' * 65)
print()

scores = []

for q, cat in tests:
    ai.conversation.clear()
    r = ai.ask(q)
    if not r: r = '(vide)'
    rl = r.lower()

    s = 0

    # 1. Pertinence (0-3)
    if len(r) < 10:
        s += 0
    elif 'e est la base du logarithme' in rl:
        s += 0
    elif any(kw in rl for kw in q.lower().split() if len(kw) > 4):
        s += 2
    else:
        s += 1

    # 2. Factuel (0-3)
    fact_ok = False
    if 'sun' in q.lower() and any(w in rl for w in ['star','soleil','hydrogen','energy']):
        fact_ok = True
    if 'train' in q.lower() and '150' in r:
        fact_ok = True
    if 'largest country' in q.lower() and 'russia' in rl:
        fact_ok = True
    if 'leaves' in q.lower() and any(w in rl for w in ['chlorophyll','chlorophylle','pigment','green']):
        fact_ok = True
    if 'robot' in q.lower() and any(w in rl for w in ['robot','machine','dream','reve']):
        fact_ok = True
    if 'roses' in q.lower() and ('no' in rl or 'non' in rl or 'not' in rl):
        fact_ok = True
    if 'photosynthese' in q.lower() and any(w in rl for w in ['lumiere','light','energy','plante','plant']):
        fact_ok = True
    if 'mona lisa' in q.lower() and any(w in rl for w in ['vinci','leonard','leonardo']):
        fact_ok = True
    if 'ocean' in q.lower() and 'indian' in rl:
        fact_ok = True
    if 'gravity' in q.lower() and any(w in rl for w in ['gravit','masse','mass','force','attraction']):
        fact_ok = True
    if 'algorithm' in q.lower() and any(w in rl for w in ['etape','step','instruction','problem','calcul']):
        fact_ok = True
    if 'berlin' in q.lower() and '1989' in r:
        fact_ok = True
    if 'coffee' in q.lower() and any(w in rl for w in ['caffeine','benefit','risk','good','bad']):
        fact_ok = True
    if '25 percent' in q.lower() and '50' in r:
        fact_ok = True

    s += 3 if fact_ok else 0

    # 3. Clarte (0-2)
    if len(r) > 50 and r.count('.') >= 2:
        s += 2
    elif len(r) > 30:
        s += 1

    # 4. Longueur (0-2)
    if len(r) > 80:
        s += 2
    elif len(r) > 40:
        s += 1

    s = min(10, s)
    scores.append(s)

    v = 'COMPETITIF' if s >= 7 else ('ACCEPTABLE' if s >= 5 else ('FAIBLE' if s >= 3 else 'ECHEC'))
    print('[{}] {}/10 | {}'.format(v, s, q[:55]))
    print('  KA: {}...'.format(r[:100].replace(chr(10),' ')))
    print()

avg = sum(scores) / len(scores)
wins = sum(1 for s in scores if s >= 5)
comp = sum(1 for s in scores if s >= 7)
fails = sum(1 for s in scores if s < 3)

print('=' * 65)
print('BILAN')
print('=' * 65)
print('Score moyen     : {:.1f}/10'.format(avg))
print('Acceptables (5+): {}/{}'.format(wins, len(scores)))
print('Competitifs (7+): {}/{}'.format(comp, len(scores)))
print('Echecs (<3)     : {}/{}'.format(fails, len(scores)))
print()

if avg >= 7.0:
    elo = 1050 + (avg - 7.0) * 50
elif avg >= 5.5:
    elo = 950 + (avg - 5.5) * 40
elif avg >= 4.0:
    elo = 880 + (avg - 4.0) * 30
else:
    elo = 800 + (avg - 2.0) * 30
elo = max(750, elo)

print('ELO estime : ~{:.0f}'.format(elo))
print()
print('CLASSEMENT ESTIME :')
models = [
    ('GPT-4 Turbo', 1280), ('Claude 3.5 Sonnet', 1270),
    ('Gemini 1.5 Pro', 1240), ('Llama 3 70B', 1150),
    ('Mistral Large', 1130), ('Gemma 2 27B', 1050),
    ('IA Harmonique KA', int(elo)),
    ('Phi-3 Medium', 980), ('Baseline', 800),
]
models.sort(key=lambda x: -x[1])
for i, (n, e) in enumerate(models):
    m = ' <--- KA' if 'Harmonique' in n else ''
    print('  {:2d}. {:25s} ELO {}{}'.format(i+1, n, e, m))
print()
if elo >= 1050:
    print('RECOMMANDATION: SOUMETTRE - competitif science/geo/histoire')
elif elo >= 980:
    print('RECOMMANDATION: SOUMETTRE AVEC ATTENTE')
elif elo >= 900:
    print('RECOMMANDATION: ATTENDRE - ameliorer raisonnement')
else:
    print('RECOMMANDATION: NE PAS SOUMETTRE ENCORE')
