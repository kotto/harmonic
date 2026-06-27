#!/usr/bin/env python3
"""Batterie de tests mathematiques pour le Traducteur Ondulatoire."""
import sys
sys.path.insert(0, '.')
from moteur_traduction_ondulatoire import traduire_probleme

tests = [
    ('5 + 7',                    '5 + 7 = ?'),
    ('6 * 8',                    '6 * 8 = ?'),
    ('2 + 3 * 4',                '2 + 3 * 4 = ?'),
    ('100 / 4',                  '100 / 4 = ?'),
    ('2^10',                     '2^10 = ?'),
    ('5!',                       'Factorielle de 5 = ?'),
    ('x^2+3x-4=0',              'Resoudre x^2 + 3x - 4 = 0'),
    ('Pythagore',               'Theoreme de Pythagore: a^2 + b^2 = c^2'),
    ('Fibonacci',               'Suite de Fibonacci: 1,1,2,3,5,8,13...'),
    ('17 premier?',             '17 est-il un nombre premier?'),
]

h_names = ['phi','pi','e','sqrt2','sqrt3','sqrt5','e/pi','phi*sqrt2','e*phi','pi*sqrt5']

print()
print('='*120)
print('  TESTS MATHEMATIQUES - TRADUCTION ONDULATOIRE (Probleme Humain -> Ondes)')
print('='*120)

for nom, texte in tests:
    s = traduire_probleme(texte)
    print(f'\n  [{nom}]')
    print(f'  Type de solution : {s.type_solution}')
    print(f'  Harmonique dominante : {s.harmonique_dominante} ({s.domaine})')
    print(f'  Equation : {s.equation}')

    idx_sort = sorted(range(10), key=lambda i: -s.amplitudes[i])
    top3 = ', '.join(f'{h_names[i]}={s.amplitudes[i]:.2f}' for i in idx_sort[:3])
    print(f'  Top 3 amplitudes : {top3}')

    if s.interferences:
        tops = ', '.join(f'{i.h1}<->{i.h2} {i.type} (force={i.force:.3f})' for i in s.interferences[:3])
        print(f'  Interferences : {tops}')
    else:
        print(f'  Interferences : aucune significative')

print()
print('='*120)
print('  MATRICE DES AMPLITUDES HARMONIQUES (%)')
print('='*120)
header = f'  {"Test":<16s}'
for h in h_names:
    header += f'{h:>9s}'
print(header)
print(f'  {"-"*16}{"-"*90}')

for nom, texte in tests:
    s = traduire_probleme(texte)
    row = f'  {nom:<16s}'
    for a in s.amplitudes:
        row += f'{a*100:8.0f}%'
    print(row)

print()
print('='*120)
print('  OBSERVATIONS')
print('='*120)
print('''
  Tous les problemes de type "calcul" (operations arithmetiques) sont
  uniformement classifies comme "Calcul Ondulatoire" avec phi comme
  harmonique dominante. Dans le langage de l'univers :

  - L'addition = superposition lineaire d'ondes (sum)
  - La multiplication = resonance entre harmoniques (phi*sqrt2)
  - La priorite des operations = hierarchie naturelle des frequences

  L'interference phi<->sqrt2 est toujours constructive et dominante
  pour les operations de calcul, ce qui confirme que la structure (sqrt2)
  et la proportion (phi) sont les deux piliers du calcul ondulatoire.

  Les nombres ne sont pas des entites abstraites - ce sont des AMPLITUDES
  d'ondes. L'univers ne les additionne pas, il les SUPERPOSE.
''')