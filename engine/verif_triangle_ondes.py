#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verif_triangle_ondes.py — Énumération machine du « triangle ondulatoire » à 3 modes
====================================================================================
Paquet première frappe jauge (MSH 5.x) : SU(3) ∩ grammaire ondulatoire.

Question falsifiable :
    Soit un système ondulatoire fermé de trois modes complexes
    Psi_1, Psi_2, Psi_3, avec UNE loi de conservation :
    la norme totale  N = sum_i |Psi_i|^2  (« fermeture » du triangle).
    Combien de canaux bilinéaires indépendants  Psi_i * conj(Psi_j)
    survivent une fois la phase globale factorisée ?

Prédiction du théorème du triangle (THEOREME_TRIANGLE_SU3.md) :
    9 formes bilinéaires totales (le cône Hermitien, 3 x 3)
      - 1 singulet invariant (la norme elle-même, jauge globale U(1))
      = 8 canaux dynamiques portés par les 8 générateurs sans trace,
    et le groupe des rotations qui préserve la norme modulo la phase
    globale est exactement SU(3) — comptage des gluons du MS : 3^2 - 1 = 8.

Verdict machine :
    TOUTES les vérifications sous tolérance -> VERDICT : TRIANGLE CONFIRME
    Une seule échoue                        -> VERDICT : REFUTÉ (mur des défaites)

Usage :  python verif_triangle_ondes.py
Sortie : rapport console + resultat_triangle_ondes.json (même dossier)
"""

import json
import sys

import numpy as np

SEED = 27                 # déterministe : mêmes nombres à chaque exécution
TOL_ALGEBRA = 1e-12       # tolérance sur identités algébriques exactes
TOL_UNITARY = 1e-12       # tolérance sur orthonormalité / unitarité
RNG = np.random.default_rng(SEED)


# ----------------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------------

def hermitian_coords(M):
    """Coordonnées réelles (9) d'une matrice Hermitienne 3x3."""
    return np.array([
        M[0, 0].real, M[1, 1].real, M[2, 2].real,
        M[0, 1].real, M[0, 1].imag,
        M[0, 2].real, M[0, 2].imag,
        M[1, 2].real, M[1, 2].imag,
    ])


HERMITIAN_BASIS = []
for _k in range(9):
    _E = np.zeros((3, 3), dtype=complex)
    _pos = [(0, 0), (1, 1), (2, 2), (0, 1), (0, 1), (0, 2), (0, 2), (1, 2), (1, 2)][_k]
    _signs = [1.0, 1.0, 1.0, 1.0, 1.0j, 1.0, 1.0j, 1.0, 1.0j][_k]
    _E[_pos] += _signs
    if _pos[0] != _pos[1]:
        _E[_pos[::-1]] += np.conj(_signs)
    HERMITIAN_BASIS.append(_E)

IDENTITY = np.eye(3, dtype=complex)


def gell_mann():
    """Les 8 matrices de Gell-Mann, normalisées tr(la lb) = 2 delta_ab."""
    lam = []
    for p, q in ((0, 1), (0, 2), (1, 2)):
        sym = np.zeros((3, 3), dtype=complex); sym[p, q] = 1.0; sym[q, p] = 1.0
        anti = np.zeros((3, 3), dtype=complex); anti[p, q] = -1.0j; anti[q, p] = 1.0j
        lam.append(sym); lam.append(anti)
    diag3 = np.diag([1.0, -1.0, 0.0]).astype(complex)
    diag8 = np.diag([1.0, 1.0, -2.0]).astype(complex) / np.sqrt(3.0)
    lam.insert(2, diag3)
    lam.append(diag8)
    return lam


def random_unitary(n, rng):
    """Matrice unitaire n x n par QR d'une gaussienne complexe (déterministe via rng)."""
    z = (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))) / np.sqrt(2.0)
    q, r = np.linalg.qr(z)
    phases = np.diag(r) / np.abs(np.diag(r))
    return q * phases


def random_su3(rng):
    """SU(3) : unitaire tirée puis corrigée pour det = 1 (retire un facteur U(1))."""
    u = random_unitary(3, rng)
    det = np.linalg.det(u)
    return u * np.conj(det) ** (1.0 / 3.0)


def extract_u1_angle(M):
    """Angle de la composante U(1) globale d'un élément de U(3) : arg(det M)."""
    return float(np.angle(np.linalg.det(M)))


# ----------------------------------------------------------------------------
# Vérifications P0..P7 — chaque fonction renvoie un dict standardisé
# ----------------------------------------------------------------------------

def p0_recensement_bilineaires():
    """Énumère les 9 formes bilinéaires Psi_i conj(Psi_j) et classe le singulet."""
    rows = []
    for i in range(3):
        for j in range(3):
            kind = "SINGULET (trace)" if i == j else "canal hors-diagonal"
            rows.append({"forme": f"Psi_{i+1}*conj(Psi_{j+1})", "classe": kind})
    # Le cône Hermitien est exactement leur enveloppe réelle : rang complet ?
    rank_full = int(np.linalg.matrix_rank(np.array([hermitian_coords(E) for E in HERMITIAN_BASIS])))
    # Filtre sans trace : retire la direction identité
    c_id = hermitian_coords(IDENTITY)
    without_trace = np.array([hermitian_coords(E) for E in HERMITIAN_BASIS])
    sans_trace = without_trace - np.outer(without_trace @ c_id / (c_id @ c_id), c_id)
    rank_traceless = int(np.linalg.matrix_rank(sans_trace))
    return {
        "nom": "P0 énumération des formes bilinéaires",
        "attendu": "rang(cône)=9 ; rang(hors trace)=8",
        "mesuré": f"{rank_full} ; {rank_traceless}",
        "ok": rank_full == 9 and rank_traceless == 8,
        "detail": rows,
        "err": 0.0,
    }


def p1_census_generateurs():
    """Espace réel des générateurs Hermitiens sans trace : dimension attendue 8."""
    lam = gell_mann()
    coords = np.array([hermitian_coords(L) for L in lam])
    rank_lam = int(np.linalg.matrix_rank(coords))
    norms_err = max(abs(np.trace(La @ Lb).real - (2.0 if a == b else 0.0))
                    for a, La in enumerate(lam) for b, Lb in enumerate(lam))
    traces = max(abs(np.trace(L)) for L in lam)
    return {
        "nom": "P1 recensement des générateurs (Gell-Mann)",
        "attendu": "8 générateurs indépendants ; tr=0 ; tr(la lb)=2 delta",
        "mesuré": f"rang={rank_lam} ; err_traces={traces:.2e} ; err_norme={norms_err:.2e}",
        "ok": rank_lam == 8 and traces < TOL_ALGEBRA and norms_err < TOL_ALGEBRA,
        "err": float(max(traces, norms_err)),
    }


def p2_algebre_f_abc():
    """Structure f_abc extraite numériquement et comparée aux valeurs exactes."""
    lam = gell_mann()
    exact = {
        (1, 2, 3): 1.0,
        (1, 4, 7): 0.5, (2, 4, 6): 0.5, (2, 5, 7): 0.5, (3, 4, 5): 0.5,
        (1, 5, 6): -0.5, (3, 6, 7): -0.5,
        (4, 5, 8): np.sqrt(3) / 2, (6, 7, 8): np.sqrt(3) / 2,
    }
    max_err = 0.0

    def f_coeffs(a, b):
        comm = lam[a] @ lam[b] - lam[b] @ lam[a]
        fa = [(np.trace(comm @ lam[c]) / 4j).real for c in range(8)]
        fi = [(np.trace(comm @ lam[c]) / 4j).imag for c in range(8)]
        return fa, fi

    # antisymétrie stricte : aucune partie imaginaire résiduelle dans f extraits
    for a in range(8):
        for b in range(a + 1, 8):
            _, fi = f_coeffs(a, b)
            max_err = max(max_err, max(abs(v) for v in fi))
    # les 9 constantes indépendantes connues sont-elles retrouvées ?
    const_err = 0.0
    for (a, b, c), val in exact.items():
        fa, _ = f_coeffs(a - 1, b - 1)
        const_err = max(const_err, abs(fa[c - 1] - val))
    # décompte structurel : paires porteuses ET triples antisymétriques distincts
    nonzero_pairs = 0
    triples = set()
    for a in range(8):
        for b in range(a + 1, 8):
            fa, _ = f_coeffs(a, b)
            lit = [c + 1 for c in range(8) if abs(fa[c]) > 1e-8]
            if lit:
                nonzero_pairs += 1
                for c in lit:
                    triples.add(tuple(sorted((a + 1, b + 1, c))))
    # NB : 25 paires (pas 27) car (4,5) et (6,7) portent chacune deux constantes
    return {
        "nom": "P2 algèbre : constantes de structure f_abc",
        "attendu": "9 valeurs indépendantes {±1, ±1/2, ±√3/2}, "
                   "9 triples antisymétriques, 25 paires porteuses",
        "mesuré": f"triples={len(triples)} ; paires={nonzero_pairs} ; "
                  f"err_constantes={const_err:.2e} ; err_imaginaire={max_err:.2e}",
        "ok": const_err < TOL_ALGEBRA and max_err < TOL_ALGEBRA
              and len(triples) == 9 and nonzero_pairs == 25,
        "err": float(max(const_err, max_err)),
        "triples": sorted(t for t in triples),
    }


def p3_cloture_octet():
    """Le bloc des 8 canaux est stable par SU(3) : rotation orthogonale exacte."""
    lam = gell_mann()
    su_list = [random_su3(RNG) for _ in range(200)]
    max_orth = 0.0
    max_singlet = 0.0
    max_det_dev = 0.0
    for u in su_list[:50]:
        w = np.array([[np.real(np.trace(lam[a] @ (u @ lam[b] @ u.conj().T))) / 2.0
                       for b in range(8)] for a in range(8)])
        max_orth = max(max_orth, float(np.linalg.norm(w.T @ w - np.eye(8))))
    for u3 in su_list[:150]:
        state = RNG.standard_normal(3) + 1j * RNG.standard_normal(3)
        state /= np.linalg.norm(state)
        z = np.outer(state, state.conj())
        transformed = u3 @ z @ u3.conj().T
        # singulet préservé exactement
        max_singlet = max(max_singlet, abs(np.trace(transformed) - np.trace(z)))
        # départ de SU(3) : det = 1, donc aucun drainage hors de l'octet
        max_det_dev = max(max_det_dev, abs(np.linalg.det(u3) - 1.0))
    return {
        "nom": "P3 clôture de l'octet par SU(3)",
        "attendu": "rotation orthogonale dans les 8 canaux ; singulet figé ; det(SU)=1",
        "mesuré": f"orthogonalité={max_orth:.2e} ; singulet={max_singlet:.2e} ; det={max_det_dev:.2e}",
        "ok": max_orth < TOL_UNITARY and max_singlet < TOL_ALGEBRA and max_det_dev < TOL_ALGEBRA,
        "err": float(max(max_orth, max_singlet, max_det_dev)),
    }


def p4_singulet_unique_invariant():
    """Sous-espace commun fixe par action adjointe de U(3) aléatoire : span(I), dim 1.

    Base (Λ_1..Λ_8, I) normalisée en norme de Hilbert-Schmidt : le produit
    scalaire tr(A B) devient δ_ab, le critère « vecteur fixe » est alors
    rigoureusement (K − I)y = 0 avec K la matrice d'action conjuguée.
    """
    nine = gell_mann() + [IDENTITY]
    orthon = []
    for b in nine:
        norm = np.sqrt(np.real(np.trace(b @ b)))
        orthon.append(b / norm)
    m_stack = []
    for _ in range(40):
        u = random_unitary(3, RNG)
        conj_action = np.array([[np.real(np.trace(orthon[a] @ (u @ orthon[b] @ u.conj().T)))
                                 for b in range(9)] for a in range(9)])
        # empiler les MATRICES (pas des aplatissements) : l'axe 1 doit rester
        # l'axe de coordonnées pour que le noyau commun ait un sens
        m_stack.append(conj_action - np.eye(9))
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
    """Witness d'irréductibilité : une PAIRE GÉNÉRIQUE de générateurs sans
    trace (tirée du rng déterministe) sature l'octet entier par clôture de
    crochets — aucun sous-découpage en familles plus petites n'existe.

    NB de la session : la paire canonique (Λ_1, Λ_4) est DÉGÉNÉRÉE —
    {Λ_1, Λ_4, [Λ_4,Λ_7]} referme une su(2) stricte (trajectoire 2→3→3→3).
    Seule une paire générique témoigne contre tout sous-découpage.
    """
    lam = gell_mann()

    def random_traceless(rng):
        h = rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3))
        h = (h + h.conj().T) / 2.0
        return h - np.trace(h).real * IDENTITY / 3.0

    current = [random_traceless(RNG), random_traceless(RNG)]
    seen_ranks = []

    def rank_of(mats):
        return int(np.linalg.matrix_rank(np.array([hermitian_coords(L) for L in mats])))

    # Clôture de Lie pilotée par le RANG (terminaison garantie) :
    # un seul représentant canonique par direction indépendante, donc au
    # plus 8 représentants et C(8,2)=28 crochets par passe — aucun risque
    # d'explosion en quasi-duplicatas numériques.
    rank_now = rank_of(current)
    for _ in range(12):
        seen_ranks.append(rank_now)
        if rank_now >= 8:
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
                    if rank_now >= 8:
                        break
            if rank_now >= 8:
                break
        if not grew_this_pass:
            break
    final_rank = rank_now
    grew = any(b > a for a, b in zip(seen_ranks, seen_ranks[1:]))
    return {
        "nom": "P5 irréductibilité de l'octet (paire générique)",
        "attendu": "saturations finales = 8 ; croissance visible depuis la paire",
        "mesuré": f"saturé à {final_rank} ; trajectoire {seen_ranks}",
        "ok": final_rank == 8 and grew and len(seen_ranks) >= 3,
        "err": 0.0,
    }


def p6_decouplage_phase_globale():
    """Sur le triangle : dynamique relative (SU(3)) et phase commune (U(1)) se factorisent."""
    def loop_hamiltonian(theta12, theta23, theta31, couplings):
        h = np.zeros((3, 3), dtype=complex)
        links = ((0, 1, theta12), (1, 2, theta23), (2, 0, theta31))
        for k, (p, q, th) in enumerate(links):
            amp = couplings[k]
            h[p, q] += amp * np.exp(1j * th)
            h[q, p] += amp * np.exp(-1j * th)
        return h

    couplings = (0.7 + 0.6 * RNG.random(), 0.4 + 0.9 * RNG.random(), 1.1 * RNG.random() + 0.2)
    h0 = loop_hamiltonian(0.31, -0.87, 0.53, couplings)
    assert abs(np.trace(h0)) < TOL_ALGEBRA, "boucle bilinéaire : diagonale nulle"
    h_global = h0 + 1.37 * IDENTITY     # même dynamique + phase commune arbitraire

    times = [0.05 * t for t in range(1, 41)]
    state0 = RNG.standard_normal(3) + 1j * RNG.standard_normal(3)
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
    # det de l'évolution sans trace : resté 1 (aucun déphasage global engendré)
    ut = evecs0 @ np.diag(np.exp(-1j * evals0 * 2.0)) @ evecs0.conj().T
    det_err = float(abs(np.linalg.det(ut) - 1.0))
    # avec trace : angle accumulé = tr(H)*t exactement (modulo branche 2π)
    ut_gauged = evecsG @ np.diag(np.exp(-1j * evalsG * 2.0)) @ evecsG.conj().T
    angle_pred = float(np.angle(np.exp(-1j * np.trace(h_global).real * 2.0)))
    angle_meas = extract_u1_angle(ut_gauged)
    wrap = np.exp(1j * (angle_meas - angle_pred))
    angle_gap = float(abs(wrap - 1.0))

    return {
        "nom": "P6 découplage U(1) x SU(3) sur la boucle",
        "attendu": "chevauchement=1 ; norme conservée ; det(sans trace)=1 ; angle = tr(H)t",
        "mesuré": f"overlap={max_phase_err:.2e} ; norme={max_norm_err:.2e} ; "
                  f"det={det_err:.2e} ; angle={angle_gap:.2e}",
        "ok": max_phase_err < TOL_UNITARY and max_norm_err < TOL_UNITARY
              and det_err < TOL_ALGEBRA and angle_gap < 1e-9,
        "err": float(max(max_phase_err, max_norm_err, det_err, angle_gap)),
    }


CHECKS = [p0_recensement_bilineaires, p1_census_generateurs, p2_algebre_f_abc,
          p3_cloture_octet, p4_singulet_unique_invariant, p5_irreductibilite,
          p6_decouplage_phase_globale]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 78)
    print(" VÉRIFICATION MACHINE — TRIANGLE ONDULATOIRE À 3 MODES (paquet SU(3))")
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
                print(f"       · {ligne['forme']:<28} -> {ligne['classe']}")

    print("\n" + "-" * 78)
    print(" COMPTAGE CONTRE PRÉDICTION")
    print("-" * 78)
    print("  Formes bilinéaires totales          : 9   (cone Hermitien 3x3, comme 3(x)(3bar)")
    print("  Singulet conservé (norme/jauge U(1)): 1   (la trace, unique invariant P4)")
    print("  Canaux dynamiques indépendants      : 8   <- prédiction théorème triangle")
    print("  Décompte des gluons du MS           : 8   (SU(3), 3^2 - 1)")

    all_ok = all(r["ok"] for r in results)
    verdict = ("VERDICT : TRIANGLE CONFIRMÉ (machine)" if all_ok
               else "VERDICT : RÉFUTÉ — entrée au mur des défaites")
    print("\n" + "=" * 78)
    print(f" {verdict}")
    print("=" * 78)

    report = {
        "script": "verif_triangle_ondes.py",
        "seed": SEED,
        "tolerance_algebre": TOL_ALGEBRA,
        "tolerance_unitarite": TOL_UNITARY,
        "verdict": "TRIANGLE_CONFIRME" if all_ok else "REFUTE",
        "echecs": [r["nom"] for r in results if not r["ok"]],
        "controles": [
            {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v)
             for k, v in r.items()}
            for r in results
        ],
    }
    out_path = "resultat_triangle_ondes.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=True, indent=2)
    print(f" rapport JSON écrit : {out_path}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
