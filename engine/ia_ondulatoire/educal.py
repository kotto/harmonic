# -*- coding: utf-8 -*-
"""
educal.py — EDUCAL KA en langage ondulatoire natif.

Jumeau éducatif de VITAL KA sur le nouveau moteur ondulatoire (ia_ondulatoire) :
chaque discipline est un hologramme, chaque leçon est une « unité éducative
transférable » (protocole store identique au médical), le cerveau ondulatoire
joue le tuteur — diagnostic des lacunes par résonance (ENCODE → SUPERPOSE →
RESONATE → EMERGE → DÉCODER) et révision par rappel holographique.

Le contenu pédagogique (data/educal_units/*.json) et l'admin-server FastAPI :8001
sont conservés tels quels — seule la pile d'exécution est remplacée.

Contrats reproduits (ka_server :8765) :
    GET  /api/educal/units · GET /api/educal/unit/<id>
    POST /api/educal/quiz/submit · GET /api/educal/progress/<user_id>
    GET  /api/educal/diagnose/<unit_id> · POST /api/educal/exercise/generate
    POST /api/educal/unit/<id>/hologram
    GET  /api/store/download/<holo_id> · POST /api/store/load · POST /api/store/recall
"""

from __future__ import annotations

import json
import math
import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from primitives import DEFAULT_DIM, HolographicMemory, Wave, encode

DOSSIER_UNITES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "data", "educal_units")
DOSSIER_DONNEES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "data", "ia_ondulatoire")

# 5 familles de templates du tuteur (déterministe, 0 LLM)
FAMILLES_TUTEUR = ["achat", "vitesse", "regle_de_trois", "partage", "reste"]

# mapping discipline → hologramme (identique à l'existant)
DISCIPLINE_HOLO = {
    "mathématiques": "edu_mathematiques", "maths": "edu_mathematiques",
    "français": "edu_langues", "francais": "edu_langues",
    "sciences": "edu_sciences", "histoire": "edu_histoire_geo",
    "géographie": "edu_histoire_geo", "geographie": "edu_histoire_geo",
    "philosophie": "edu_philosophie", "méthodologie": "edu_competences",
    "methodologie": "edu_competences",
}


def _num(texte: str) -> Optional[float]:
    """Nombre extrait d'une chaîne (« 5/8 » → 0.625, « 2,4 millions » → 2400000)."""
    t = str(texte).strip().replace(",", ".").replace(" ", "")
    if "million" in t:
        m = re.search(r"([\d.]+)", t)
        return float(m.group(1)) * 1e6 if m else None
    m = re.search(r"(-?\d+(?:\.\d+)?)(?:/(\d+(?:\.\d+)?))?", t)
    if not m:
        return None
    if m.group(2):
        den = float(m.group(2))
        return float(m.group(1)) / den if den else None
    return float(m.group(1))


def _num_match(attendu, donne: Any, tol: float = 1e-6) -> bool:
    """Comparaison tolérante (numérique ou fraction)."""
    if attendu is None:
        return False
    if str(donne).strip().lower() == str(attendu).strip().lower():
        return True
    a, b = _num(attendu), _num(donne)
    return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(a))


class EducalOndulatoire:
    """Le cerveau éducatif : catalogue, hologrammes disciplinaires, correction,
    diagnostic par résonance, progression, tuteur, unités transférables."""

    def __init__(self, ia=None, dim: int = DEFAULT_DIM,
                 dossier_unites: str = DOSSIER_UNITES,
                 dossier_donnees: str = DOSSIER_DONNEES):
        self.dim = dim
        self.dossier_unites = dossier_unites
        self.dossier = dossier_donnees
        self.ia = ia                                   # IaOndulatoire (pour /store/load → H_connaissances)
        self._holos_disciplines: Dict[str, HolographicMemory] = {}
        self._holos_unites: Dict[str, HolographicMemory] = {}
        self._charger_holos_persistes()

    # ────────────────────────────────────────────────────────────────────
    # Catalogue & leçons — le contenu JSON existant est lu tel quel
    # ────────────────────────────────────────────────────────────────────
    def _fichiers_unites(self) -> List[str]:
        if not os.path.isdir(self.dossier_unites):
            return []
        return sorted(os.path.join(self.dossier_unites, f)
                      for f in os.listdir(self.dossier_unites) if f.endswith(".json"))

    def list_units(self, discipline: str = None, niveau: str = None) -> List[Dict]:
        units = []
        for p in self._fichiers_unites():
            try:
                with open(p, encoding="utf-8") as f:
                    u = json.load(f)
            except Exception:
                continue
            if discipline and u.get("discipline", "").lower() != discipline.lower():
                continue
            if niveau and u.get("niveau", "").lower() != niveau.lower():
                continue
            units.append({
                "id": u.get("id"), "discipline": u.get("discipline"),
                "niveau": u.get("niveau"), "programme": u.get("programme", ""),
                "titre": u.get("titre"),
                "nb_exercices": len(u.get("exercices", [])),
                "nb_quiz": len(u.get("quiz", [])),
                "nb_faits": len(u.get("facts", [])),
                "objectifs": u.get("objectifs", []),
                "prerequis": u.get("prerequis", []),
            })
        return units

    def get_unit(self, unit_id: str) -> Optional[Dict]:
        unit_id = unit_id.strip().replace("/", "").replace("\\", "")
        chemin = os.path.join(self.dossier_unites, f"{unit_id}.json")
        if not os.path.exists(chemin):
            return None
        try:
            with open(chemin, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def unit_catalog(self) -> Dict:
        cat: Dict[str, Any] = {}
        for u in self.list_units():
            disc = u["discipline"]
            cat.setdefault(disc, {})
            cat[disc].setdefault(u["niveau"], []).append(u)
        return cat

    def facts_from_unit(self, unit: Dict) -> List[Tuple[str, str, str, str]]:
        faits = []
        for f in unit.get("facts", []):
            if isinstance(f, (list, tuple)) and len(f) >= 3:
                faits.append((str(f[0]), str(f[1]), str(f[2]),
                              str(f[3]) if len(f) > 3 else "EDUCATION"))
            elif isinstance(f, dict):
                faits.append((str(f.get("sujet", "")), str(f.get("relation", "")),
                              str(f.get("objet", "")), str(f.get("secteur", "EDUCATION"))))
        return faits

    # ────────────────────────────────────────────────────────────────────
    # Hologrammes disciplinaires — remplacement de educal_build_holograms.py
    # ────────────────────────────────────────────────────────────────────
    def _holo_discipline(self, holo_id: str) -> HolographicMemory:
        """H_edu_<discipline> : superposition des faits de toutes les unités
        qui déclarent cet hologramme. Construit au premier accès, persisté."""
        if holo_id in self._holos_disciplines:
            return self._holos_disciplines[holo_id]
        holo = HolographicMemory(self.dim)
        for u in self.list_units():
            unit = self.get_unit(u["id"])
            if not unit:
                continue
            if (unit.get("hologramme_associe") or "official_education") == holo_id:
                for s, r, o, sec in self.facts_from_unit(unit):
                    holo.store(s, r, o, secteur=sec)
        self._holos_disciplines[holo_id] = holo
        self._sauvegarder_holo(holo_id, holo)
        return holo

    def _holo_unite(self, unit_id: str) -> HolographicMemory:
        """Hologramme d'une unité éducative (8-10 faits) — l'« unité transférable »."""
        if unit_id in self._holos_unites:
            return self._holos_unites[unit_id]
        unit = self.get_unit(unit_id)
        holo = HolographicMemory(self.dim)
        if unit:
            for s, r, o, sec in self.facts_from_unit(unit):
                holo.store(s, r, o, secteur=sec)
        self._holos_unites[unit_id] = holo
        self._sauvegarder_holo(f"unit_{unit_id}", holo)
        return holo

    def _sauvegarder_holo(self, nom: str, holo: HolographicMemory) -> None:
        dossier = os.path.join(self.dossier, "educal")
        try:
            holo.sauvegarder(os.path.join(dossier, f"{nom}.npz"))
        except Exception:
            pass

    def _charger_holos_persistes(self) -> None:
        dossier = os.path.join(self.dossier, "educal")
        if not os.path.isdir(dossier):
            return
        for f in os.listdir(dossier):
            if not f.endswith(".npz"):
                continue
            nom = f[:-4]
            holo = HolographicMemory(self.dim)
            if holo.charger(os.path.join(dossier, f)):
                if nom.startswith("unit_"):
                    self._holos_unites[nom[5:]] = holo
                else:
                    self._holos_disciplines[nom] = holo

    def hologrammes_liste(self) -> List[Dict]:
        """Contrat GET /api/store/list (sous-ensemble éducation)."""
        holo = []
        for holo_id, mem in self._holos_disciplines.items():
            holo.append({"id": holo_id, "domain": "education", "name": holo_id,
                         "facts_count": mem.nb_faits, "quality_score": 1.0,
                         "author": "Univers-Holistique", "type": "education",
                         "description": f"Hologramme disciplinaire {holo_id}",
                         "sectors": sorted({f.secteur for f in mem._faits})})
        for unit_id, mem in self._holos_unites.items():
            holo.append({"id": f"unit_{unit_id}", "domain": "education", "name": unit_id,
                         "facts_count": mem.nb_faits, "quality_score": 1.0,
                         "author": "Univers-Holistique", "type": "unite_transferable",
                         "description": f"Unité éducative transférable {unit_id}",
                         "sectors": sorted({f.secteur for f in mem._faits})})
        return {"holograms": holo,
                "stats": {"count": len(holo),
                          "faits": sum(h["facts_count"] for h in holo)}}

    # ────────────────────────────────────────────────────────────────────
    # Correction — mêmes règles que l'existant (evaluate_quiz/exercices)
    # ────────────────────────────────────────────────────────────────────
    def evaluate_quiz(self, unit: Dict, answers: List[Dict]) -> Dict:
        quiz = unit.get("quiz", [])
        details, correct_count, lacunes = [], 0, []
        seuil = unit.get("evaluation", {}).get("seuil_reussite", 0.8)
        for i, q in enumerate(quiz):
            ans = next((a for a in answers
                        if str(a.get("question", a.get("index", -1))) == str(i)
                        or a.get("question", a.get("index", -1)) == i), None)
            if ans is None:
                details.append({"question": i, "repondu": False, "correct": False,
                                "objectif": q.get("objectif", "")})
                if q.get("objectif"):
                    lacunes.append(q["objectif"])
                continue
            donne = ans.get("answer")
            correct = _num_match(q.get("correct_index"), donne) or \
                (isinstance(donne, int) and donne == q.get("correct_index"))
            details.append({"question": i, "repondu": True, "correct": correct,
                            "objectif": q.get("objectif", "")})
            if correct:
                correct_count += 1
            elif q.get("objectif"):
                lacunes.append(q["objectif"])
        total = len(quiz)
        score = round(correct_count / total, 3) if total else 0.0
        reussite = score >= seuil
        if reussite:
            feedback = "Bravo ! Quiz réussi — objectifs maîtrisés."
        else:
            feedback = ("Lacunes détectées sur : " + ", ".join(dict.fromkeys(lacunes))
                        + " — revois les faits proposés ci-dessous.")
        return {"score": score, "correct": correct_count, "total": total,
                "seuil_reussite": seuil, "feedback": feedback,
                "lacunes": list(dict.fromkeys(lacunes)), "details": details,
                "reussite": reussite}

    def evaluate_exercices(self, unit: Dict, answers: List[Dict]) -> Dict:
        exos = unit.get("exercices", [])
        details, correct_count = [], 0
        for i, ex in enumerate(exos):
            ans = next((a for a in answers
                        if str(a.get("exercice", a.get("index", -1))) == str(i)
                        or a.get("exercice", a.get("index", -1)) == i), None)
            if ans is None:
                details.append({"exercice": i, "repondu": False, "correct": False})
                continue
            donne = ans.get("reponse")
            attendu = ex.get("reponse")
            ok = _num_match(attendu, donne) if attendu is not None else False
            details.append({"exercice": i, "repondu": True, "correct": ok,
                            "attendu": attendu, "etapes": ex.get("etapes", [])})
            if ok:
                correct_count += 1
        total = len(exos)
        return {"score": round(correct_count / total, 3) if total else 0.0,
                "correct": correct_count, "total": total, "details": details}

    # ────────────────────────────────────────────────────────────────────
    # Diagnostic pédagogique — la résonance ondulatoire (équivalent du
    # diagnostic médical de medical.py, transposé aux objectifs)
    # ────────────────────────────────────────────────────────────────────
    def diagnose_lacunes(self, unit: Dict, lacunes: List[str]) -> Dict:
        holo_id = unit.get("hologramme_associe") or "official_education"
        if not lacunes:
            return {"holo_id": holo_id, "lacunes": [], "faits_a_revoir": [],
                    "message": "Aucune lacune détectée — maîtrise confirmée"}
        holo = self._holo_discipline(holo_id)
        faits_a_revoir = []
        for obj in lacunes[:5]:
            psi_obj = encode(obj, self.dim)
            for fait, score in holo.interroger(psi_obj, top_k=3, seuil=0.02):
                faits_a_revoir.append({"objectif": obj, "fait": fait.texte(),
                                       "secteur": fait.secteur, "score": round(score, 3)})
        return {"holo_id": holo_id, "lacunes": lacunes,
                "faits_a_revoir": faits_a_revoir,
                "message": (f"{len(faits_a_revoir)} faits à revoir résonnent avec "
                            f"l'hologramme {holo_id}")}

    # ────────────────────────────────────────────────────────────────────
    # Progression — carnet d'apprentissage (persistance JSON)
    # ────────────────────────────────────────────────────────────────────
    def _chemin_progress(self, user_id: str) -> str:
        return os.path.join(self.dossier, "educal_progress", f"{user_id}.json")

    def load_progress(self, user_id: str) -> Dict:
        chemin = self._chemin_progress(user_id)
        if os.path.exists(chemin):
            try:
                with open(chemin, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"user_id": user_id, "unites_validees": {}, "sessions": [], "skills": {}}

    def save_progress(self, user_id: str, unit_id: str, payload: Dict) -> Dict:
        prog = self.load_progress(user_id)
        unit = self.get_unit(unit_id)
        session = {"unit_id": unit_id, "ts": time.time(),
                   "date": time.strftime("%Y-%m-%d %H:%M"),
                   "quiz_score": payload.get("quiz_score"),
                   "exercices_score": payload.get("exercices_score"),
                   "lacunes": payload.get("lacunes", [])}
        prog["last_unit"] = unit_id
        prog["sessions"].append(session)
        if payload.get("reussite"):
            prog["unites_validees"][unit_id] = time.strftime("%Y-%m-%d")
        # compétences : chaque objectif validé devient un skill (1.0), échoué → 0.0
        if unit and payload.get("quiz_details"):
            for d in payload["quiz_details"]:
                obj = d.get("objectif")
                if obj:
                    prog["skills"][obj] = 1.0 if d.get("correct") else 0.0
        os.makedirs(os.path.dirname(self._chemin_progress(user_id)), exist_ok=True)
        with open(self._chemin_progress(user_id), "w", encoding="utf-8") as f:
            json.dump(prog, f, ensure_ascii=False, indent=1)
        return prog

    def progress(self, user_id: str) -> Dict:
        prog = self.load_progress(user_id)
        prog["next_units"] = self.next_units(user_id, prog.get("last_unit", ""))
        return prog

    def next_units(self, user_id: str, unit_id: str) -> List[str]:
        current = self.get_unit(unit_id) if unit_id else None
        if not current:
            # aucune unité suivie : propose la discipline la plus représentée
            disci = {}
            for u in self.list_units():
                disci[u["discipline"]] = disci.get(u["discipline"], 0) + 1
            disc = max(disci, key=disci.get) if disci else None
            return [u["id"] for u in self.list_units(discipline=disc)][:5]
        prog = self.load_progress(user_id)
        suggestions = []
        for u in self.list_units(discipline=current.get("discipline")):
            if u["id"] == unit_id:
                continue
            if current.get("id") in u.get("prerequis", []):
                suggestions.append(u["id"])
        reste = [u["id"] for u in self.list_units(discipline=current.get("discipline"))
                 if u["id"] != unit_id and u["id"] not in suggestions]
        reste.sort(key=lambda uid: prog["unites_validees"].get(uid, "0000"))
        return suggestions + reste[:5]

    # ────────────────────────────────────────────────────────────────────
    # Tuteur — génération d'exercices (5 familles, déterministe, 0 LLM)
    # ────────────────────────────────────────────────────────────────────
    def generate_exercise(self, discipline: str, niveau: str) -> Dict:
        """Génère un exercice : template narratif × méthode résonnée dans
        l'hologramme de discipline (programme ondulatoire exécuté)."""
        famille = random.choice(FAMILLES_TUTEUR)
        exo = self._template(famille)
        holo_id = DISCIPLINE_HOLO.get((discipline or "").lower(), "official_education")
        # la méthode : l'hologramme de discipline résonne avec le nom de la famille
        methode = self._methode_ondulatoire(holo_id, famille, exo)
        return {
            "question": exo["question"], "etapes": exo["etapes"],
            "reponse": exo["reponse"], "methode": methode,
            "moteur": "langage-ondulatoire-v1 (déterministe, 0 LLM)",
            "famille": famille, "hologramme": holo_id,
        }

    def _template(self, famille: str) -> Dict:
        rng = random.Random()
        if famille == "achat":
            prix, n = rng.randint(2, 9) * 100, rng.randint(2, 12)
            total = prix * n
            return {"question": f"Un cahier coûte {prix} francs. Combien coûtent {n} cahiers ?",
                    "etapes": [f"{prix} × {n} = {total}", f"→ {total} francs"],
                    "reponse": str(total)}
        if famille == "vitesse":
            d, t = rng.randint(3, 8) * 20, rng.randint(2, 5)
            v = d // t
            return {"question": f"Une voiture parcourt {d} km en {t} heures. "
                                f"Quelle est sa vitesse moyenne ?",
                    "etapes": [f"vitesse = distance ÷ temps = {d} ÷ {t}",
                               f"→ {v} km/h"],
                    "reponse": str(v)}
        if famille == "regle_de_trois":
            n, m, k = rng.randint(2, 6), rng.randint(4, 10) * 5, rng.randint(2, 9)
            temps = m * k // n
            return {"question": f"Pour fabriquer {n} objets, une machine met {m} minutes. "
                                f"Combien de temps pour {k} objets ?",
                    "etapes": [f"règle de trois : {m} × {k} ÷ {n}",
                               f"→ {temps} minutes"],
                    "reponse": str(temps)}
        if famille == "partage":
            s, p = rng.randint(4, 10) * 100, rng.randint(2, 6)
            part = s // p
            return {"question": f"On partage {s} francs équitablement entre {p} personnes. "
                                f"Combien chacun reçoit-il ?",
                    "etapes": [f"{s} ÷ {p} = {part}", f"→ {part} francs chacun"],
                    "reponse": str(part)}
        # reste
        s, a = rng.randint(6, 12) * 100, rng.randint(1, 4) * 100
        reste = s - a
        return {"question": f"Tu as {s} francs et tu achètes un article à {a} francs. "
                            f"Combien te reste-t-il ?",
                "etapes": [f"{s} − {a} = {reste}", f"→ {reste} francs"],
                "reponse": str(reste)}

    def _methode_ondulatoire(self, holo_id: str, famille: str, exo: Dict) -> str:
        """Exécute un programme ondulatoire (reason) contre l'hologramme de
        discipline pour faire émerger la méthode ; fallback = étapes du template."""
        try:
            from generateur import GenerateurOndulatoire
            from moteur import MoteurOndulatoire
            from ir import valider
            question = exo["question"]
            prog, _ = GenerateurOndulatoire(dim=self.dim).generer(
                f"Quelle méthode utiliser pour : {question}")
            holo = self._holo_discipline(holo_id)
            if valider(prog, hologrammes=[holo_id]):
                env = MoteurOndulatoire(dim=self.dim).executer(
                    prog, hologrammes={holo_id: holo})
                faits = env.get("psi_r")
                recos = faits.faits if faits else []
                if recos:
                    noms = "; ".join(f.texte() for f, _ in recos[:3])
                    return (f"Résonance ondulatoire ({holo_id}) : {noms}. "
                            f"Étapes : {' → '.join(exo['etapes'])}")
        except Exception:
            pass
        return "Méthode : " + " → ".join(exo["etapes"])

    # ────────────────────────────────────────────────────────────────────
    # Unité éducative transférable — hologramme ↔ téléchargement ↔ injection
    # ────────────────────────────────────────────────────────────────────
    def unit_hologram(self, unit_id: str) -> Dict:
        """Construit (ou récupère) l'hologramme de l'unité — geste médical de VITAL KA."""
        unit = self.get_unit(unit_id)
        if not unit:
            return {"error": "unité inconnue"}
        holo = self._holo_unite(unit_id)
        return {"holo_id": f"unit_{unit_id}", "facts_count": holo.nb_faits,
                "cached": holo.nb_faits > 0, "secteurs": sorted(
                    {f.secteur for f in holo._faits})}

    def download(self, holo_id: str) -> Dict:
        """Exporte l'hologramme : faits + ψ en polaire (compatibilité transport)."""
        mem = self._trouver_holo(holo_id)
        if mem is None:
            return {"error": "hologramme inconnu"}
        faits = [[f.sujet, f.relation, f.objet, f.secteur] for f in mem._faits]
        psi_data = []
        for f in mem._faits[:20]:
            psi = f.psi
            psi_data.append({"sujet": f.sujet, "relation": f.relation, "objet": f.objet,
                             "magnitude": [round(float(abs(x)), 6) for x in psi],
                             "phase": [round(float(np.angle(x)), 6) for x in psi]})
        return {"holo_id": holo_id, "facts": faits, "count": len(faits),
                "has_psi_data": True, "psi_data": psi_data, "dim": self.dim}

    def load(self, holo_id: str, ia=None) -> Dict:
        """Injecte l'hologramme dans la mémoire du cerveau (H_connaissances)."""
        mem = self._trouver_holo(holo_id)
        if mem is None:
            return {"error": "hologramme inconnu"}
        cerveau = ia or self.ia
        if cerveau is None:
            return {"error": "cerveau indisponible"}
        n = 0
        for f in mem._faits:
            if f.relation:
                cerveau.H_connaissances.store(f.sujet, f.relation, f.objet,
                                              secteur=f.secteur, amplitude=2.0)
            else:
                cerveau.H_connaissances.store_psi(f.psi, f.sujet, amplitude=2.0)
            n += 1
        return {"success": True, "holo_id": holo_id, "facts_loaded": n,
                "message": f"{n} faits actifs (H injecté dans H_connaissances)"}

    def recall(self, query: str, top_k: int = 5) -> Dict:
        """Rappel holographique dans le cerveau : la résonance retourne les faits."""
        cerveau = self.ia
        if cerveau is None:
            return {"query": query, "results": [], "count": 0,
                    "message": "cerveau indisponible"}
        psi_q = encode(query, self.dim)
        resultats = []
        for mem in (cerveau.H_connaissances, cerveau.H_faits):
            for fait, score in mem.interroger(psi_q, top_k=top_k, seuil=0.0):
                resultats.append({"fait": fait.texte(), "secteur": fait.secteur,
                                  "score": round(score, 3)})
        resultats.sort(key=lambda r: -r["score"])
        return {"query": query, "results": resultats[:top_k], "count": len(resultats)}

    def _trouver_holo(self, holo_id: str) -> Optional[HolographicMemory]:
        if holo_id.startswith("unit_"):
            return self._holo_unite(holo_id[5:])
        return self._holos_disciplines.get(holo_id)
