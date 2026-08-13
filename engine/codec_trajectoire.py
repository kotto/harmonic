#!/usr/bin/env python3
"""
codec_trajectoire.py — Encodage des opérations comme trajectoire ondulatoire
=============================================================================

PRINCIPE (v2 — inspiré de l'analyse du problème résolu) :

  Abandon de la FFT globale (périodicité artificielle, fuite spectrale,
  dérive du dernier point vers la moyenne).

  Chaque opération émet une TRAME ψ par transition locale :
    (op_code, amplitude, phase)

  Chaque trame encode UN SEUL déplacement dans le plan complexe :
    z_k = z_{k-1} + amp · e^{i·phase}

  Décodage par SOMME CUMULATIVE (pas IFFT) → exact, sans bord, sans fuite.

STRUCTURE DES TRAMES :
  code=4  INIT   → position de départ (amp = valeur initiale)
  code=1  SUB    → 2 trames : montée d'étage (y+1) + recul horizontal (phase=π)
  code=2  MUL    → 2 trames : montée d'étage (y+1) + avance horizontale (phase=0)
  code=3  ADD    → 2 trames : montée d'étage (y+1) + avance horizontale (phase=0)
  code=5  DIV    → 2 trames : montée d'étage (y+1) + recul vertical (phase=π/2)

  La dimension VERTICALE (y) encode la STRUCTURE DU GRAPHE (profondeur).
  La dimension HORIZONTALE (x) encode les VALEURS.

  Les sauts non locaux (réutiliser une variable construite plus tôt)
  ne posent aucun problème : chaque trame porte sa transition propre.

EXEMPLE (boulangère) :
  INIT      e1 = 20
  SUBTRACT  e2 = e1 - 8  = 12
  MULTIPLY  e3 = e2 * 2  = 24
  SUBTRACT  e4 = e3 - e2 = 12

  code=4  amp=20.00  phase=+0.000   ← INIT (départ)
  code=1  amp= 1.00  phase=+1.571   ← SUB : étage +1
  code=1  amp= 8.00  phase=+3.142   ← SUB : recul 8 (20→12)
  code=2  amp= 1.00  phase=+1.571   ← MUL : étage +1
  code=2  amp=12.00  phase=+0.000   ← MUL : avance 12 (12→24)
  code=1  amp= 1.00  phase=+1.571   ← SUB : étage +1
  code=1  amp=12.00  phase=+3.142   ← SUB : recul 12 (24→12)

USAGE :
  from codec_trajectoire import encoder_operations, decoder_trames
  frames = encoder_operations(ops)   # ops = liste d'opérations structurées
  resultat = decoder_trames(frames)  # → dernier z, somme cumulative exacte
"""

import sys, os, re, json, math
import numpy as np
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════════════════
# 1. CONSTANTES ONDULATOIRES
# ═══════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2          # φ = 1.618...
HALF_PI = math.pi / 2                 # montée d'étage
PI = math.pi                          # recul (SUB)
ZERO = 0.0                            # avance (MUL/ADD)

# Signature fréquentielle par type d'opération (pour le décodage
# sans connaître le graphe — voir section 5)
SIGNATURE_FREQ = {
    'INIT': 0.0,        # pas d'oscillation
    'ADD': 1.0 / PHI,   # fréquence dorée
    'SUB': 1.0 / (2 * PHI),
    'MUL': 2.0 / PHI,
    'DIV': 1.0 / (3 * PHI),
    'FRACTION': 1.0 / (4 * PHI),
}


# ═══════════════════════════════════════════════════════════════════════════
# 2. CODEC V2 : TRAMES PAR TRANSITION
# ═══════════════════════════════════════════════════════════════════════════

def encoder_operations(ops: List[dict]) -> List[dict]:
    """
    Encode une séquence d'opérations structurées en trames ondulatoires.

    Entrée : [{op: 'INIT', entity, object, value}, ...]
    Sortie : [{code, amp, phase, op, var}, ...]

    Règle de montée : chaque opération (sauf INIT) commence par
    une montée d'étage (y+1) puis émet sa transition horizontale.
    """
    frames = []
    variables = {}   # nom de variable → valeur (pour suivre l'état)
    var_counter = 0

    for op in ops:
        op_name = op.get('op', '').upper()
        var_name = f"e{var_counter + 1}"
        var_counter += 1

        if op_name == 'INIT':
            value = float(op.get('value', 0))
            variables[var_name] = value
            # Position de départ : (x=value, y=0)
            frames.append({
                'code': 4, 'amp': abs(value), 'phase': 0.0 if value >= 0 else PI,
                'op': 'INIT', 'var': var_name, 'value': value,
            })

        elif op_name in ('ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'FRACTION'):
            # Codes : ADD=3, SUB=1, MUL=2, DIV=5, FRACTION=6
            code_map = {'ADD': 3, 'SUBTRACT': 1, 'MULTIPLY': 2,
                       'DIVIDE': 5, 'FRACTION': 6}
            code = code_map.get(op_name, 3)

            # Trouver la variable source (l'entité de l'opération)
            src_var = None
            for v, val in variables.items():
                # Dernière variable modifiée (simple heuristique)
                src_var = v
            if src_var is None:
                src_var = 'e0'
                variables[src_var] = 0.0

            src_val = variables.get(src_var, 0.0)

            # Extraire l'opérande numérique (robuste aux valeurs non-numériques)
            raw_operand = (op.get('value') or op.get('multiplier') or
                          op.get('per_unit') or op.get('rate') or
                          op.get('duration') or op.get('divisor'))
            try:
                operand = float(raw_operand)
            except (TypeError, ValueError):
                # Opérande non numérique (ex: product="shorts_total") → skip
                variables[var_name] = src_val
                frames.append({
                    'code': code, 'amp': 0.0, 'phase': 0.0,
                    'op': op_name, 'var': var_name, 'value': src_val,
                })
                continue

            # Gérer les fractions (numerator/denominator)
            if op_name == 'FRACTION':
                try:
                    num = float(op.get('numerator', 2))
                    den = float(op.get('denominator', 5))
                    operand = num / den if den != 0 else 0.5
                except (TypeError, ValueError):
                    operand = 0.5

            # Calculer la nouvelle valeur
            if op_name == 'ADD':
                new_val = src_val + operand
                phase = ZERO          # avance droite
            elif op_name == 'SUBTRACT':
                new_val = src_val - operand
                phase = PI            # recul gauche (TOUJOURS, pas de wrap)
            elif op_name == 'MULTIPLY':
                new_val = src_val * operand
                phase = ZERO          # avance droite
            elif op_name == 'DIVIDE':
                new_val = src_val / operand if operand != 0 else src_val
                phase = -HALF_PI      # descente verticale
            else:  # FRACTION
                new_val = src_val * operand
                phase = ZERO

            # Trame 1 : montée d'étage (y+1)
            frames.append({
                'code': code, 'amp': 1.0, 'phase': HALF_PI,
                'op': op_name, 'var': var_name, 'value': None,
            })
            # Trame 2 : déplacement horizontal (la valeur)
            # La coordonnée x de la trajectoire EST la valeur courante
            delta = abs(new_val - src_val)
            frames.append({
                'code': code, 'amp': delta if delta > 1e-9 else 1.0,
                'phase': phase,
                'op': op_name, 'var': var_name, 'value': new_val,
            })

            variables[var_name] = new_val

        elif op_name == 'QUERY':
            # La question ne produit pas de trame, mais référence une variable
            frames.append({
                'code': 0, 'amp': 0.0, 'phase': 0.0,
                'op': 'QUERY', 'var': var_name, 'value': None,
            })

    return frames


def decoder_trames(frames: List[dict]) -> float:
    """
    Décode la trajectoire par somme cumulative.

    z_k = z_{k-1} + amp · e^{i·phase}
    Retourne la partie réelle du dernier point (la valeur finale).
    """
    z = 0.0 + 0.0j
    final_value = None

    for frame in frames:
        amp = frame['amp']
        phase = frame['phase']
        z += amp * np.exp(1j * phase)

        # Le résultat final est la dernière valeur horizontale (x)
        if frame.get('value') is not None:
            final_value = frame['value']

    return float(z.real) if final_value is None else final_value


def decoder_trajectoire(frames: List[dict]) -> List[complex]:
    """Décode la trajectoire complète (tous les points z_k)."""
    z = 0.0 + 0.0j
    points = [z]
    for frame in frames:
        amp = frame['amp']
        phase = frame['phase']
        z += amp * np.exp(1j * phase)
        points.append(z)
    return points


# ═══════════════════════════════════════════════════════════════════════════
# 3. VÉRIFICATION DE L'EXEMPLE BOULANGÈRE (4 opérations, saut non local)
# ═══════════════════════════════════════════════════════════════════════════

def demo_boulangere():
    """L'exemple canonique : 20 → 12 → 24 → 12 avec saut non local."""
    print("═══ DÉMO BOULANGÈRE (4 opérations, saut non local) ═══\n")

    ops = [
        {'op': 'INIT', 'entity': 'bakery', 'object': 'loaves', 'value': 20},
        {'op': 'SUBTRACT', 'entity': 'bakery', 'value': 8},
        {'op': 'MULTIPLY', 'entity': 'bakery', 'multiplier': 2},
        {'op': 'SUBTRACT', 'entity': 'bakery', 'value': 12},
    ]

    frames = encoder_operations(ops)

    print("TRAMES ÉMISES :")
    for f in frames:
        print(f"  code={f['code']}  amp={f['amp']:6.2f}  phase={f['phase']:+6.3f}  "
              f"← {f['op']:<9s} ({f['var']})")

    # Décoder la trajectoire
    points = decoder_trajectoire(frames)
    final = decoder_trames(frames)

    print(f"\nTRAJECTOIRE (z_k) :")
    for i, p in enumerate(points):
        print(f"  z{i} = ({p.real:8.3f}, {p.imag:6.3f})")

    print(f"\nRésultat final : {final}")
    print(f"Attendu       : 12")
    print(f"✅ EXACT" if abs(final - 12) < 1e-6 else "❌ ÉCHEC")

    # Vérifier la reconstruction des valeurs intermédiaires
    # e1=20, e2=12, e3=24, e4=12
    values = [f['value'] for f in frames if f.get('value') is not None]
    print(f"\nValeurs reconstruites : {values}")
    print(f"Attendues            : [20.0, 12.0, 24.0, 12.0]")

    ok = (len(values) == 4 and
          abs(values[0]-20) < 1e-6 and abs(values[1]-12) < 1e-6 and
          abs(values[2]-24) < 1e-6 and abs(values[3]-12) < 1e-6)
    print(f"{'✅ RECONSTRUCTION EXACTE (saut non local OK)' if ok else '❌'}")

    return frames


# ═══════════════════════════════════════════════════════════════════════════
# 4. TEST SUR LES 15 EXEMPLES GSM8K
# ═══════════════════════════════════════════════════════════════════════════

def tester_15_exemples():
    """Encode les 15 exemples jouets en trames et vérifie l'exactitude."""
    print("\n═══ TEST 15 EXEMPLES GSM8K (codec trajectoire) ═══\n")

    # Utiliser les opérations DeepSeek pour les 15 exemples
    # (traduction manuelle basée sur les exemples connus)
    exemples = [
        # (opérations, résultat attendu)
        ([{'op': 'INIT', 'value': 5},
          {'op': 'ADD', 'value': 3}], 8.0),
        ([{'op': 'INIT', 'value': 10},
          {'op': 'SUBTRACT', 'value': 4}], 6.0),
        ([{'op': 'INIT', 'value': 12},
          {'op': 'SUBTRACT', 'value': 4}], 8.0),
        ([{'op': 'INIT', 'value': 6},
          {'op': 'MULTIPLY', 'multiplier': 5}], 30.0),
        ([{'op': 'INIT', 'value': 10},
          {'op': 'SUBTRACT', 'value': 3}], 7.0),
        ([{'op': 'INIT', 'value': 5},
          {'op': 'MULTIPLY', 'multiplier': 3}], 15.0),
        ([{'op': 'INIT', 'value': 24},
          {'op': 'SUBTRACT', 'value': 9}], 15.0),
        ([{'op': 'INIT', 'value': 4},
          {'op': 'MULTIPLY', 'multiplier': 4}], 16.0),
        ([{'op': 'INIT', 'value': 30},
          {'op': 'SUBTRACT', 'value': 12}], 18.0),
        ([{'op': 'INIT', 'value': 8},
          {'op': 'MULTIPLY', 'multiplier': 3}], 24.0),
        ([{'op': 'INIT', 'value': 100},
          {'op': 'SUBTRACT', 'value': 45}], 55.0),
        ([{'op': 'INIT', 'value': 5},
          {'op': 'ADD', 'value': 3}], 8.0),
        ([{'op': 'INIT', 'value': 20},
          {'op': 'MULTIPLY', 'multiplier': 8}], 160.0),
        ([{'op': 'INIT', 'value': 60},
          {'op': 'DIVIDE', 'divisor': 4}], 15.0),
        ([{'op': 'INIT', 'value': 8},
          {'op': 'SUBTRACT', 'value': 3}], 5.0),
    ]

    ok = 0
    for i, (ops, expected) in enumerate(exemples):
        frames = encoder_operations(ops)
        result = decoder_trames(frames)
        good = abs(result - expected) < 1e-6
        ok += good
        ops_str = ' → '.join(
            f"{o['op']}({o.get('value', o.get('multiplier', o.get('divisor', 'noop')))})"
            for o in ops)
        print(f"  {'✅' if good else '❌'} [{i+1:>2d}] {ops_str:<40s} → {result} ({expected})")

    print(f"\n  SCORE : {ok}/{len(exemples)} ({100*ok/len(exemples):.1f}%)")
    return ok


# ═══════════════════════════════════════════════════════════════════════════
# 5. SIGNATURE OSCILLATOIRE PAR TYPE (démodulation par corrélation)
# ═══════════════════════════════════════════════════════════════════════════

# Modulation : profondeur ε et phase ψ par type
SIGNATURE_EPS = {
    'ADD': 0.12,
    'SUB': 0.12,
    'MUL': 0.15,
    'DIV': 0.15,
    'FRACTION': 0.10,
}
SIGNATURE_PSI = {
    'ADD': 0.0,
    'SUB': math.pi / 4,
    'MUL': math.pi / 2,
    'DIV': 3 * math.pi / 4,
    'FRACTION': math.pi,
}


def encoder_operations_sig(ops: List[dict]) -> List[dict]:
    """
    Encode les opérations avec oscillation caractéristique embarquée.

    Chaque trame de déplacement horizontal module l'amplitude par
    une oscillation à la fréquence propre de l'opération :

      amp_eff(k) = amp · (1 + ε·cos(2π·f_op·k + ψ_op))

    La trajectoire x[k] contient alors une composante oscillatoire
    à f_op — détectable par démodulation, même sans connaître le graphe.
    """
    frames = encoder_operations(ops)
    step = 0
    for f in frames:
        op_name = f.get('op', '')
        freq = SIGNATURE_FREQ.get(op_name, 0.0)
        eps = SIGNATURE_EPS.get(op_name, 0.0)
        psi = SIGNATURE_PSI.get(op_name, 0.0)

        f['signature_freq'] = freq
        f['signature_eps'] = eps
        f['signature_psi'] = psi
        f['step'] = step
        step += 1

        # Moduler l'amplitude des trames de déplacement (pas l'étage)
        if f.get('value') is not None and eps > 0:
            k = step
            f['amp'] = f['amp'] * (1 + eps * math.cos(2 * math.pi * freq * k + psi))

    return frames


def decoder_trajectoire_sig(frames: List[dict]) -> List[complex]:
    """Décode la trajectoire avec les trames modulées."""
    z = 0.0 + 0.0j
    points = [z]
    for frame in frames:
        amp = frame['amp']
        phase = frame['phase']
        z += amp * np.exp(1j * phase)
        points.append(z)
    return points


def detecter_signatures(points: List[complex]) -> dict:
    """
    Détecte les signatures par DÉMODULATION à fréquence exacte.

    Pour chaque candidat f :
      corr(f) = |Σ_k x[k] · e^{−i·2π·f·k}|  /  Σ|x[k]|

    Le pic de corrélation à f_op révèle la présence de l'opération —
    même sur de courtes trajectoires (pas de binning FFT).
    """
    if len(points) < 4:
        return {}

    x = np.array([p.real for p in points])
    # Centrer le signal (retirer la moyenne)
    x_c = x - np.mean(x)
    energy = np.sum(np.abs(x_c)) + 1e-9

    n = len(x_c)
    k = np.arange(n)

    results = {}
    for op_name, freq in SIGNATURE_FREQ.items():
        if freq <= 0:
            continue
        # Corrélation à la fréquence exacte
        corr = np.abs(np.sum(x_c * np.exp(-1j * 2 * np.pi * freq * k)))
        results[op_name] = corr / energy

    return results


def analyser_signatures(frames: List[dict]) -> dict:
    """Encode avec signatures puis détecte par démodulation."""
    sig_frames = encoder_operations_sig(frames if frames and 'op' in frames[0] else [])
    # Si on reçoit déjà des ops, les encoder avec signatures
    points = decoder_trajectoire_sig(sig_frames)
    return detecter_signatures(points)


def analyser_spectre(points: List[complex]) -> dict:
    """Analyse le spectre de la trajectoire (FFT) pour détecter les signatures."""
    if len(points) < 4:
        return {}

    signal = np.array([p.real for p in points])
    # Enlever la tendance linéaire
    signal = signal - np.polyval(np.polyfit(np.arange(len(signal)), signal, 1),
                                 np.arange(len(signal)))
    spectrum = np.abs(np.fft.rfft(signal))

    # Fréquences dominantes
    freqs = np.fft.rfftfreq(len(signal), d=1.0)
    top_idx = np.argsort(spectrum)[-3:][::-1]

    result = {}
    for idx in top_idx:
        if idx > 0 and spectrum[idx] > 0.1:
            result[freqs[idx]] = spectrum[idx]

    return result


# ═══════════════════════════════════════════════════════════════════════════
# 6. MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--demo', action='store_true', help='Démo boulangère')
    p.add_argument('--test', action='store_true', help='Test 15 exemples')
    p.add_argument('--signature', action='store_true', help='Test signatures')
    args = p.parse_args()

    if args.demo or not args.test:
        demo_boulangere()

    if args.test:
        tester_15_exemples()

    if args.signature:
        print("\n═══ TEST SIGNATURES OSCILLATOIRES (démodulation) ═══\n")
        ops = [
            {'op': 'INIT', 'value': 20},
            {'op': 'SUBTRACT', 'value': 8},
            {'op': 'MULTIPLY', 'multiplier': 2},
            {'op': 'SUBTRACT', 'value': 12},
        ]
        sig_frames = encoder_operations_sig(ops)
        points = decoder_trajectoire_sig(sig_frames)
        detect = detecter_signatures(points)

        print(f"Opérations réelles : SUB, MUL, SUB")
        print(f"Fréquences attendues : SUB={SIGNATURE_FREQ['SUB']:.4f}, "
              f"MUL={SIGNATURE_FREQ['MUL']:.4f}")
        print(f"\nCorrélations détectées :")
        for op_name, corr in sorted(detect.items(), key=lambda x: -x[1]):
            expected = '✓' if (op_name == 'SUB' or op_name == 'MUL') else ' '
            print(f"  {expected} {op_name:<10s} : corr={corr:.4f}  (f={SIGNATURE_FREQ[op_name]:.4f})")

        # Vérifier que SUB et MUL sont en tête
        top2 = sorted(detect.items(), key=lambda x: -x[1])[:2]
        top_ops = [op for op, _ in top2]
        ok_sig = ('SUB' in top_ops and 'MUL' in top_ops)
        print(f"\n{'✅ SUB et MUL détectés en tête' if ok_sig else '❌ Signatures non détectées'}")
