#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verif_dyade_ondes.py — Énumération machine de la « dyade ondulatoire » à 2 modes
=================================================================================
Domino n°3 de la campagne jauge (MSH 5.x) : SU(2) ∩ grammaire ondulatoire.

Question falsifiable :
    Soit un système ondulatoire fermé de DEUX modes complexes Ψ₁, Ψ₂
    avec une seule loi de conservation :  N = |Ψ₁|² + |Ψ₂|².
    Combien de canaux bilinéaires indépendants Ψᵢ·conj(Ψⱼ) survivent,
    une fois la phase globale factorisée ?

Prédiction (THEOREME_DYADE_SU2.md) :
    4 formes bilinéaires − 1 singulet (la norme) = 3 canaux dynamiques,
    portés par les matrices de Pauli : l'algèbre est su(2), avec les
    constantes ε_abc ∈ {0, ±1} (Levi-Civita). Comptage MS analogue :
    les 3 champs de jauge faibles W¹, W², W³ avant brisure (2² − 1 = 3).

Différentiateur propre à su(2) — la DOUBLE COUVERTURE (P7) :
    la rotation d'état U(δ) = exp(−i δ/2 · n̂·σ) fait tourner le canal
    de l'angle δ exactement, autour de l'axe n̂ exactement : le canal
    voit un SO(3), l'état un SU(2) à deux feuillets. C'est le siège
    structurel du spinorial — et là où `rotate` (π → −1, [T] Livre I)
    devient loi, pas décor.

Verdict machine :
    TOUTES les vérifications sous tolérance -> VERDICT : DYADE CONFIRMÉE
    Une seule échoue                        -> VERDICT : RÉFUTÉ (mur des défaites)

Usage :  python verif_dyade_ondes.py
Sortie : rapport console + resultat_dyade_ondes.json (même dossier)
"""

import json
import sys

import numpy as np

SEED = 27                 # déterministe (séquence distincte du script triangle)
TOL_ALGEBRA = 1e-12
TOL_UNITARY = 1e-12
RNG = np.random.default_rng(SEED)


# ----------------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------------

def hermitian_coords2(M):
    """Coordonnées réelles (4) d'une matrice Hermitienne 2x2."""
    return np.array([
        M[0, 0].real, M[1, 1].real,
        M[0, 1].real, M[0, 1].imag,
    ])


HERMITIAN_BASIS2 = []
for _k in range(4):
    _E = np.zeros((2, 2), dtype=complex)
    _pos = [(0, 0), (1, 1), (0, 1), (0, 1)][_k]
    _sign = [1.0, 1.0, 1.0, 1.0j][_k]
    _E[_pos] += _sign
    if _pos[0] != _pos[1]:
        _E[_pos[::-1]] += np.conj(_sign)
    HERMITIAN_BASIS2.append(_E)

IDENTITY2 = np.eye(2, dtype=complex)


def pauli():
    """Les 3 matrices de Pauli, normalisées tr(σa σb) = 2 δ_ab."""
    s1 = np.array([[0, 1], [1, 0]], dtype=complex)
    s2 = np.array([[0, -1j], [1j, 0]], dtype=complex)
    s3 = np.array([[1, 0], [0, -1]], dtype=complex)
    return [s1, s2, s3]


def random_unitary2(n, rng):
    """Unitaire n×n par QR d'une gaussienne complexe (déterministe via rng)."""
    z = (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))) / np.sqrt(2.0)
    q, r = np.linalg.qr(z)
    phases = np.diag(r) / np.abs(np.diag(r))
    return q * phases


def random_su2(rng):
    """SU(2) : unitaire 2×2 corrigée pour det = 1 (retire le facteur U(1))."""
    u = random_unitary2(2, rng)
    det = np.linalg.det(u)
    return u * np.conj(det) ** 0.5


# ----------------------------------------------------------------------------
# Vérifications P0..P7
# ----------------------------------------------------------------------------

def p0_recensement_bilineaires():
    """Énumère les 4 formes Ψᵢ·conj(Ψⱼ) ; cône Hermitien 2x2 : rang 4, hors trace 3."""
    rows = []
    for i in range(2):
        for j in range(2):
            kind = "SINGULET (trace)" if i == j else "canal hors-diagonal"
            rows.append({"forme": f"Psi_{i+1}*conj(Psi_{j+1})", "classe": kind})
    basis = np.array([hermitian_coords2(E) for E in HERMITIAN_BASIS2])
    rank_full = int(np.linalg.matrix_rank(basis))
    c_id = hermitian_coords2(IDENTITY2)
    sans_trace = basis - np.outer(basis @ c_id / (c_id @ c_id), c_id)
    rank_traceless = int(np.linalg.matrix_rank(sans_trace))
    return {
        "nom": "P0 énumération des formes bilinéaires",
        "attendu": "rang(cône)=4 ; rang(hors trace)=3",
        "mesuré": f"{rank_full} ; {rank_traceless}",
        "ok": rank_full == 4 and rank_traceless == 3,
        "detail": rows,
        "err": 0.0,
    }


def p1_census_generateurs():
    """3 générateurs de Pauli indépendants, tr=0, tr(σa σb)=2δ_ab."""
    sigma = pauli()
    coords = np.array([hermitian_coords2(S) for S in sigma])
    rank = int(np.linalg.matrix_rank(coords))
    norms_err = max(abs(np.trace(Sa @ Sb).real - (2.0 if a == b else 0.0))
                    for a, Sa in enumerate(sigma) for b, Sb in enumerate(sigma))
    traces = max(abs(np.trace(S)) for S in sigma)
    return {
        "nom": "P1 recensement des générateurs (Pauli)",
        "attendu": "3 générateurs indépendants ; tr=0 ; tr(σa σb)=2δ",
        "mesuré": f"rang={rank} ; err_traces={traces:.2e} ; err_norme={norms_err:.2e}",
        "ok": rank == 3 and traces < TOL_ALGEBRA and norms_err < TOL_ALGEBRA,
        "err": float(max(traces, norms_err)),
    }


def p2_constantes_levi_civita():
    """Constantes de structure ε_abc ∈ {0, ±1} extraites numériquement."""
    sigma = pauli()
    const_err = 0.0
    lit_pairs = 0
    for a in range(3):
        for b in range(a + 1, 3):
            comm = sigma[a] @ sigma[b] - sigma[b] @ sigma[a]
            fa = [(np.trace(comm @ sigma[c]) / 4j).real for c in range(3)]
            fi = [(np.trace(comm @ sigma[c]) / 4j).imag for c in range(3)]
            const_err = max(const_err, max(abs(v) for v in fi))
            if any(abs(v) > 1e-8 for v in fa):
                # la seule triple est {1,2,3} ; valeurs dominantes ±1
                const_err = max(const_err,
                                max(abs(v - round(v)) for v in fa))
                lit_pairs += 1
    return {
        "nom": "P2 algèbre : constantes de structure ε_abc",
        "attendu": "3 paires porteuses, valeurs entières ±1 (Levi-Civita), imaginaire nulle",
        "mesuré": f"paires={lit_pairs} ; err={const_err:.2e}",
        "ok": const_err < TOL_ALGEBRA and lit_pairs == 3,
        "err": float(const_err),
    }


def p3_cloture_triade():
    """La triade (3 canaux) est stable par SU(2) : rotation orthogonale exacte."""
    sigma = pauli()
    su_list = [random_su2(RNG) for _ in range(200)]
    max_orth = 0.0
    max_singlet = 0.0
    max_det_dev = 0.0
    for u in su_list[:50]:
        w = np.array([[np.real(np.trace(sigma[a] @ (u @ sigma[b] @ u.conj().T))) / 2.0
                       for b in range(3)] for a in range(3)])
        max_orth = max(max_orth, float(np.linalg.norm(w.T @ w - np.eye(3))))
    for u2 in su_list[:150]:
        state = RNG.standard_normal(2) + 1j * RNG.standard_normal(2)
        state /= np.linalg.norm(state)
        z = np.outer(state, state.conj())
        transformed = u2 @ z @ u2.conj().T
        max_singlet = max(max_singlet, abs(np.trace(transformed) - np.trace(z)))
        max_det_dev = max(max_det_dev, abs(np.linalg.det(u2) - 1.0))
    return {
        "nom": "P3 clôture de la triade par SU(2)",
        "attendu": "rotation orthogonale dans les 3 canaux ; singulet figé ; det(SU)=1",
        "mesuré": f"orthogonalité={max_orth:.2e} ; singulet={max_singlet:.2e} ; det={max_det_dev:.2e}",
        "ok": max_orth < TOL_UNITARY and max_singlet < TOL_ALGEBRA and max_det_dev < TOL_ALGEBRA,
        "err": float(max(max_orth, max_singlet, max_det_dev)),
    }


def p4_singulet_unique_invariant():
    """Sous-espace commun fixe de l'action adjointe U(2) : span(I), dim 1.

    Base (σ₁,σ₂,σ₃,I) normalisée en norme de Hilbert-Schmidt ; empilement
    des MATRICES (pas des aplatissements) pour préserver l'axe de
    coordonnées (leçon de la session triangle).
    """
    four = pauli() + [IDENTITY2]
    orthon = []
    for b in four:
        norm = np.sqrt(np.real(np.trace(b @ b)))
        orthon.append(b / norm)
    m_stack = []
    for _ in range(40):
        u = random_unitary2(2, RNG)
        k_mat = np.array([[np.real(np.trace(orthon[a] @ (u @ orthon[b] @ u.conj().T)))
                           for b in range(4)] for a in range(4)])
        m_stack.append(k_mat - np.eye(4))
    m = np.vstack(m_stack)
    sv = np.linalg.svd(m, compute_uv=False)
    dim_fixed = int(np.sum(sv < 1e-9))
    return {
        "nom": "P4 unicité du singulet invariant",
        "attendu": "dimension du sous-espace fixe = 1 (l'identité seule)",
        "mesuré": f"dim={dim_fixed} ; plus petite val. singulière={sv[-1]:.2e} ; "
                  f"suivante={sv[-2]:.2e}",
        "ok": dim_fixed == 1,
        "err": 0.0,
    }


def p5_irreductibilite():
    """Witness : une paire générique de générateurs sans trace sature le rang 3
    par clôture de crochets (critère d'accroissement de RANG — terminaison
    garantie, leçon du triangle)."""
    def random_traceless(rng):
        h = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
        h = (h + h.conj().T) / 2.0
        return h - np.trace(h).real * IDENTITY2 / 2.0

    current = [random_traceless(RNG), random_traceless(RNG)]
    seen_ranks = []

    def rank_of(mats):
        return int(np.linalg.matrix_rank(np.array([hermitian_coords2(L) for L in mats])))

    rank_now = rank_of(current)
    for _ in range(12):
        seen_ranks.append(rank_now)
        if rank_now >= 3:
            break
        grew_this_pass = False
        snapshot = list(current)
        for i in range(len(snapshot)):
            for j in range(i + 1, len(snapshot)):
                br = snapshot[i] @ snapshot[j] - snapshot[j] @ snapshot[i]
                norm = float(np.linalg.norm(br))
                if norm < 1e-12:
                    continue
                cand_dir = br / norm
                # invariant essentiel : [A,B] est ANTI-Hermitien ; la clôture
                # de Lie doit vivre chez les Hermitiens -> stocker br/1j
                cand = cand_dir / 1j
                if rank_of(current + [cand]) > rank_now:
                    current.append(cand)
                    rank_now += 1
                    grew_this_pass = True
                    if rank_now >= 3:
                        break
            if rank_now >= 3:
                break
        if not grew_this_pass:
            break
    final_rank = rank_now
    grew = any(b > a for a, b in zip(seen_ranks, seen_ranks[1:]))
    return {
        "nom": "P5 irréductibilité de la triade (paire générique)",
        "attendu": "saturations finales = 3 ; croissance visible depuis la paire",
        "mesuré": f"saturé à {final_rank} ; trajectoire {seen_ranks}",
        "ok": final_rank == 3 and grew and len(seen_ranks) >= 2,
        "err": 0.0,
    }


def p6_decouplage_phase_globale():
    """Lien unique (pas de boucle à 2 nœuds) : l'échange bilinéaire Ψ₁↔Ψ₂
    est sans diagonale ⇒ traceless ⇒ la dynamique se factorise en
    (phase commune = tr(H)t) × (précession relative SU(2))."""
    amp = 0.6 + 0.8 * RNG.random()
    theta = 0.41
    h0 = np.array([[0, amp * np.exp(1j * theta)],
                   [amp * np.exp(-1j * theta), 0]], dtype=complex)
    assert abs(np.trace(h0)) < TOL_ALGEBRA, "échange bilinéaire : diagonale nulle"
    h_global = h0 + 1.11 * IDENTITY2

    times = [0.05 * t for t in range(1, 41)]
    state0 = RNG.standard_normal(2) + 1j * RNG.standard_normal(2)
    state0 /= np.linalg.norm(state0)

    evals0, evecs0 = np.linalg.eigh(h0)
    evalsG, evecsG = np.linalg.eigh(h_global)

    def evol(evals, evecs, t):
        # forme EXPLICITE diag : (vec 1D * matrice) broadcaste sur le dernier
        # axe et produit evecs·evecsᵀ·diag — unitaire mais FAUX (bug établi au
        # cas minimal le 27/08/2026, écart 8,4×10⁻¹ sur exemple 2x2).
        return evecs @ np.diag(np.exp(-1j * evals * t)) @ (evecs.conj().T @ state0)

    max_phase_err = 0.0
    max_norm_err = 0.0
    for t in times:
        s_plain = evol(evals0, evecs0, t)
        s_gauged = evol(evalsG, evecsG, t)
        overlap = abs(np.vdot(s_plain, s_gauged))
        max_phase_err = max(max_phase_err, abs(overlap - 1.0))
        max_norm_err = max(max_norm_err, abs(np.linalg.norm(s_plain) - 1.0))
    ut = evecs0 @ np.diag(np.exp(-1j * evals0 * 2.0)) @ evecs0.conj().T
    det_err = float(abs(np.linalg.det(ut) - 1.0))
    ut_g = evecsG @ np.diag(np.exp(-1j * evalsG * 2.0)) @ evecsG.conj().T
    angle_pred = float(np.angle(np.exp(-1j * np.trace(h_global).real * 2.0)))
    angle_meas = float(np.angle(np.linalg.det(ut_g)))
    wrap = np.exp(1j * (angle_meas - angle_pred))
    angle_gap = float(abs(wrap - 1.0))
    return {
        "nom": "P6 découplage U(1) x SU(2) sur l'échange",
        "attendu": "chevauchement=1 ; norme conservée ; det(sans trace)=1 ; angle=tr(H)t",
        "mesuré": f"overlap={max_phase_err:.2e} ; norme={max_norm_err:.2e} ; "
                  f"det={det_err:.2e} ; angle={angle_gap:.2e}",
        "ok": max_phase_err < TOL_UNITARY and max_norm_err < TOL_UNITARY
              and det_err < TOL_ALGEBRA and angle_gap < 1e-9,
        "err": float(max(max_phase_err, max_norm_err, det_err, angle_gap)),
    }


def p7_double_couverture():
    """LE différentiateur su(2) : U(δ) = exp(−i δ/2 · n̂·σ) tourne la triade
    de l'angle δ EXACTEMENT, autour de l'axe n̂ EXACTEMENT.

    L'état parcourt δ/2 (le feuillet), le canal parcourt δ (l'espace) :
    facteur 2 structurel — le siège du spinorial et de la résonance
    −1 de `rotate(π)` (Livre I §⑦, [T]).
    """
    sigma = pauli()

    def adjoint_rotation(u):
        return np.array([[np.real(np.trace(sigma[a] @ (u @ sigma[b] @ u.conj().T))) / 2.0
                          for b in range(3)] for a in range(3)])

    max_angle_err = 0.0
    min_axis_align = 1.0
    trials = 120
    for _ in range(trials):
        axis = RNG.standard_normal(3)
        axis /= np.linalg.norm(axis)
        delta = 0.3 + 2.4 * RNG.random()      # évite les pôles 0 et 2π
        gen = sum(axis[k] * sigma[k] for k in range(3))
        # hermitisation de sûreté (la combinaison l'est déjà : mix convexe de Pauli)
        gen = (gen + gen.conj().T) / 2.0
        # forme fermée d'Euler-quaternionique — aucune reconstruction via
        # vecteurs propres : exp(-i θ/2 · n̂·σ) = cos(θ/2)·I − i·sin(θ/2)·n̂·σ
        u_delta = np.cos(delta / 2.0) * np.eye(2) - 1j * np.sin(delta / 2.0) * gen
        w = adjoint_rotation(u_delta)
        # extraction axe/angle par la formule de Rodrigues inverse
        v = np.array([w[2, 1] - w[1, 2], w[0, 2] - w[2, 0], w[1, 0] - w[0, 1]])
        s = np.linalg.norm(v)
        phi = float(np.arctan2(s / 2.0, (np.trace(w) - 1.0) / 2.0))
        if s < 1e-12:
            continue
        rot_axis = v / s
        max_angle_err = max(max_angle_err, abs(phi - delta))
        min_axis_align = min(min_axis_align, float(abs(np.dot(axis, v / s))))
    return {
        "nom": "P7 double couverture : canal δ ↔ état δ/2, même axe",
        "attendu": "angle_extrait = δ (120 axes aléatoires) ; axe aligné à 10⁻¹²",
        "mesuré": f"err_angle={max_angle_err:.2e} ; alignement_min={min_axis_align:.12f} "
                  f"(1 − |cos| ≤ {1.0 - min_axis_align:.2e})",
        "ok": max_angle_err < 1e-9 and 1.0 - min_axis_align < 1e-9,
        "err": float(max(max_angle_err, 1.0 - min_axis_align)),
    }


CHECKS = [p0_recensement_bilineaires, p1_census_generateurs, p2_constantes_levi_civita,
          p3_cloture_triade, p4_singulet_unique_invariant, p5_irreductibilite,
          p6_decouplage_phase_globale, p7_double_couverture]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 78)
    print(" VÉRIFICATION MACHINE — DYADE ONDULATOIRE À 2 MODES (domino SU(2)/ROTATE)")
    print(f" graine déterministe = {SEED} · tolérances algèbre={TOL_ALGEBRA:g}, unitarité={TOL_UNITARY:g}")
    print("=" * 78)

    results = []
    for fn in CHECKS:
        res = fn()
        results.append(res)
        marker = "[OK]" if res["ok"] else "[ECHEC]"
        print(f"\n{marker} {res['nom']}")
        print(f"     attendu : {res['attendu']}")
        print(f"     mesuré  : {res['mesuré']}")
        if res["nom"].startswith("P0"):
            for ligne in res["detail"]:
                print(f"       · {ligne['forme']:<24} -> {ligne['classe']}")

    print("\n" + "-" * 78)
    print(" COMPTAGE CONTRE PRÉDICTION")
    print("-" * 78)
    print("  Formes bilinéaires totales          : 4   (cone Hermitien 2x2, comme 2(x)(2bar)")
    print("  Singulet conservé (norme/jauge U(1)): 1   (la trace, unique invariant P4)")
    print("  Canaux dynamiques indépendants      : 3   <- prédiction dyade")
    print("  Champs de jauge faibles du MS       : 3   (SU(2), 2^2 - 1 : W1 W2 W3 avant brisure)")
    print("  Double couverture (P7)              : canal = 2 x angle d'état  (spinorial)")

    all_ok = all(r["ok"] for r in results)
    verdict = ("VERDICT : DYADE CONFIRMÉE (machine)" if all_ok
               else "VERDICT : RÉFUTÉ — entrée au mur des défaites")
    print("\n" + "=" * 78)
    print(f" {verdict}")
    print("=" * 78)

    report = {
        "script": "verif_dyade_ondes.py",
        "seed": SEED,
        "tolerance_algebre": TOL_ALGEBRA,
        "tolerance_unitarite": TOL_UNITARY,
        "verdict": "DYADE_CONFIRMEE" if all_ok else "REFUTE",
        "echecs": [r["nom"] for r in results if not r["ok"]],
        "controles": [
            {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v)
             for k, v in r.items()}
            for r in results
        ],
    }
    out_path = "resultat_dyade_ondes.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=True, indent=2)
    print(f" rapport JSON écrit : {out_path}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
