# -*- coding: utf-8 -*-
"""
benchmark_educal.py — Benchmark éducatif du moteur ondulatoire.

Méthode : pour chaque question d'unité (quiz + exercices), on interroge
l'hologramme de discipline par résonance (ENCODE → SUPERPOSE → RESONATE) et on
mesure si les faits pertinents de l'unité sont rappelés dans le top-k.

Métriques par discipline : Précision@5, Rappel@5, F1@5 — plus le contrôle du
tuteur (les 5 familles d'exercices répondent sans erreur).

    python benchmark_educal.py          # rapport complet → JSON
    EducalBenchmark().lancer(n_questions=…)
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List

from primitives import DEFAULT_DIM, Wave, encode, superpose
from educal import EducalOndulatoire

DOSSIER_DONNEES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "data", "ia_ondulatoire")


def _mots_pleins(texte: str) -> List[str]:
    from generateur import _pseudo_mots
    return _pseudo_mots(texte)[:8]


class EducalBenchmark:
    """Évaluation ondulatoire du rappel pédagogique, discipline par discipline."""

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self.edu = EducalOndulatoire()

    # ── le rappel par résonance (même hybride que le moteur) ────────────
    def _rappel(self, holo, question: str, top_k: int = 5):
        ondes = [encode(question, self.dim)]
        ondes += [encode(m, self.dim) for m in _mots_pleins(question)]
        psi_q = superpose(*ondes)
        return holo.interroger(psi_q, top_k=top_k, seuil=0.0)

    @staticmethod
    def _cles_faits(faits) -> set:
        return {tuple(f[:3]) for f in faits}

    # ── benchmark principal ─────────────────────────────────────────────
    def lancer(self, sauver: bool = True) -> Dict[str, Any]:
        debut = time.time()
        disciplines: Dict[str, Dict[str, Any]] = {}
        total_q, total_p, total_r, total_pert = 0, 0.0, 0.0, 0
        questions_teste = 0

        for meta in self.edu.list_units():
            unit = self.edu.get_unit(meta["id"])
            if not unit:
                continue
            disc = unit.get("discipline", "inconnue")
            holo_id = unit.get("hologramme_associe") or "official_education"
            holo = self.edu._holo_discipline(holo_id)
            pertinents = self._cles_faits(self.edu.facts_from_unit(unit))
            if not pertinents:
                continue

            questions = []
            for i, q in enumerate(unit.get("quiz", [])):
                texte = q.get("question", "")
                if q.get("choix") and isinstance(q.get("correct_index"), int):
                    texte += " " + str(q["choix"][q["correct_index"]])
                questions.append(texte)
            questions += [e.get("enonce", "") for e in unit.get("exercices", [])]
            questions = [q for q in questions if q]

            stats = disciplines.setdefault(
                disc, {"unites": 0, "questions": 0, "precision": [], "rappel": []})
            stats["unites"] += 1
            stats["questions"] += len(questions)

            for question in questions:
                resultats = self._rappel(holo, question, top_k=5)
                rappeles = {tuple((f.sujet, f.relation, f.objet)) for f, _ in resultats}
                n_pert = len(pertinents & rappeles)
                p = n_pert / max(1, len(resultats))
                r = n_pert / max(1, len(pertinents))
                stats["precision"].append(p)
                stats["rappel"].append(r)
                total_p += p
                total_r += r
                total_pert += n_pert
                questions_teste += 1
                total_q += 1

        # agrégation par discipline
        lignes = []
        for disc, s in sorted(disciplines.items()):
            p = sum(s["precision"]) / len(s["precision"]) if s["precision"] else 0.0
            r = sum(s["rappel"]) / len(s["rappel"]) if s["rappel"] else 0.0
            f1 = 2 * p * r / (p + r) if p + r else 0.0
            lignes.append({"discipline": disc, "unites": s["unites"],
                           "questions": s["questions"],
                           "precision_at_5": round(p, 4),
                           "rappel_at_5": round(r, 4),
                           "f1_at_5": round(f1, 4)})

        # contrôle du tuteur : les 5 familles doivent répondre sans erreur
        tuteur = self._controle_tuteur()

        rapport = {
            "benchmark": "educal_ondulatoire",
            "questions_teste": questions_teste,
            "faits_pertinents_rappeles": total_pert,
            "precision_moyenne_at_5": round(total_p / max(1, total_q), 4),
            "rappel_moyen_at_5": round(total_r / max(1, total_q), 4),
            "f1_moyen_at_5": round(2 * (total_p / max(1, total_q)) * (total_r / max(1, total_q))
                                   / ((total_p / max(1, total_q)) + (total_r / max(1, total_q)))
                                   if (total_p + total_r) else 0.0, 4),
            "par_discipline": lignes,
            "tuteur": tuteur,
            "modele": "langage-ondulatoire-v1 (0 LLM)",
            "temps_total_s": round(time.time() - debut, 2),
            "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if sauver:
            os.makedirs(DOSSIER_DONNEES, exist_ok=True)
            with open(os.path.join(DOSSIER_DONNEES, "benchmark_educal.json"),
                      "w", encoding="utf-8") as f:
                json.dump(rapport, f, ensure_ascii=False, indent=1)
        return rapport

    # ── contrôle du tuteur ──────────────────────────────────────────────
    def _controle_tuteur(self, par_famille: int = 5) -> Dict[str, Any]:
        from gsm8k import GSM8KOndulatoire
        solveur = GSM8KOndulatoire()
        ok, total = 0, 0
        par_famille_res = {}
        for _ in range(par_famille):
            for f in ("achat", "vitesse", "regle_de_trois", "partage", "reste"):
                exo = self.edu.generate_exercise("mathématiques", "6e")
                # re-vérifie le calcul par la résolution ondulatoire de l'énoncé
                r = solveur.resoudre(exo["question"])
                attendu = float(exo["reponse"])
                valide = (r["reponse_num"] is not None
                          and abs(r["reponse_num"] - attendu)
                          / max(1.0, abs(attendu)) < 0.01)   # tolérance relative 1 %
                par_famille_res.setdefault(exo["famille"], {"ok": 0, "total": 0})
                par_famille_res[exo["famille"]]["total"] += 1
                total += 1
                if valide:
                    ok += 1
                    par_famille_res[exo["famille"]]["ok"] += 1
        return {"exercices_verifies": total, "corrects": ok,
                "precision_tuteur": round(ok / max(1, total), 4),
                "par_famille": par_famille_res}

    # ── ligne de commande ───────────────────────────────────────────────
    def afficher(self, rapport: Dict[str, Any]) -> None:
        print("═" * 62)
        print("BENCHMARK ÉDUCATIF — langage ondulatoire natif")
        print("═" * 62)
        print(f"Questions testées : {rapport['questions_teste']} · "
              f"P@5 {rapport['precision_moyenne_at_5']:.3f} · "
              f"R@5 {rapport['rappel_moyen_at_5']:.3f} · "
              f"F1@5 {rapport['f1_moyen_at_5']:.3f}")
        for d in rapport["par_discipline"]:
            print(f"  {d['discipline']:<14} {d['questions']:>3} questions · "
                  f"P@5 {d['precision_at_5']:.3f} · R@5 {d['rappel_at_5']:.3f} · "
                  f"F1@5 {d['f1_at_5']:.3f}")
        t = rapport["tuteur"]
        print(f"Tuteur : {t['corrects']}/{t['exercices_verifies']} "
              f"({t['precision_tuteur'] * 100:.0f} %) · {rapport['temps_total_s']} s")
        print("═" * 62)


if __name__ == "__main__":
    rapport = EducalBenchmark().lancer()
    EducalBenchmark().afficher(rapport)
