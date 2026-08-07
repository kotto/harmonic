# -*- coding: utf-8 -*-
"""
medical.py — Vital KA en langage ondulatoire natif : le diagnostic harmonique.

Les 62 356 faits médicaux (data/medical_holograms/*_facts.json, format
[{s, r, o, sec}]) sont encodés nativement (FNV-1a × φ-spacing) puis liés par
BIND_MANY dans un hologramme par secteur. Le diagnostic est une expérience
d'interférence :

    ENCODE(symptômes) → SUPERPOSE → RESONATE (vs hologrammes par domaine)
        → EMERGE (pathologies cohérentes) → DÉCODER (diagnostic + conduite)

Contrats reproduits :
    POST /api/health/diagnostic   (ka_server racine — écran SANTÉ de la PWA)
    POST /diagnose                (vital-ka backend inference — app médecin)
"""

from __future__ import annotations

import glob
import json
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from primitives import DEFAULT_DIM, HolographicMemory, Wave, encode, superpose

DOSSIER_MEDICAL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "data", "medical_holograms")

DISCLAIMER = ("⚠️ Analyse harmonique d'aide à la décision — ne remplace pas un avis "
              "médical professionnel. En cas de signe de gravité, consultez un médecin.")

# fréquence de résonance par domaine (Hz) — table thérapeutique harmonique
FREQUENCES = {
    "infectieux": (528.0, "réparation cellulaire et harmonisation du terrain"),
    "respiratoire": (396.0, "libération des tensions respiratoires"),
    "energetique": (852.0, "rééquilibrage des centres énergétiques"),
    "douleur": (174.0, "soulagement et apaisement de la douleur"),
    "digestif": (417.0, "déblocage et revitalisation digestive"),
    "nerveux": (639.0, "réharmonisation du système nerveux"),
    "cutane": (741.0, "purification et régénération cutanée"),
    "general": (528.0, "équilibre global de l'organisme"),
}

VITAUX_NORMAUX = {
    "frequence_cardiaque": (60.0, 100.0, "bpm"),
    "saturation_oxygene": (95.0, 100.0, "%"),
    "temperature": (36.5, 37.5, "°C"),
    "pression_systolique": (90.0, 140.0, "mmHg"),
    "pression_diastolique": (60.0, 90.0, "mmHg"),
}


def normaliser_mot(texte: str) -> str:
    """Normalise pour l'encodage : minuscules, sans accents, non-alphanumériques → '_'.
    « toux sèche » et « toux_sèche » deviennent tous deux « toux_seche »."""
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    texte = re.sub(r"[^a-z0-9]+", "_", texte).strip("_")
    return texte or "_"


class DiagnosticOndulatoire:
    """Le diagnostic vital KA : résonance des symptômes contre les hologrammes médicaux."""

    def __init__(self, dim: int = DEFAULT_DIM, dossier: str = DOSSIER_MEDICAL):
        self.dim = dim
        self.dossier = dossier
        self.domaines: Dict[str, HolographicMemory] = {}
        self._charge = False
        self._graine_connaissance()

    # ── chargement des hologrammes médicaux ─────────────────────────────
    def _graine_connaissance(self) -> None:
        """Base minimale embarquée (fonctionne même sans data/medical_holograms).
        Direction canonique des faits : pathologie → présente_symptôme → symptôme."""
        faits = [
            # infectieux / respiratoire
            ("infection respiratoire", "présente_symptôme", "fièvre", "respiratoire"),
            ("infection respiratoire", "présente_symptôme", "toux sèche", "respiratoire"),
            ("infection respiratoire", "présente_symptôme", "fatigue", "respiratoire"),
            ("paludisme", "présente_symptôme", "frissons", "infectieux"),
            ("paludisme", "présente_symptôme", "fièvre", "infectieux"),
            ("anémie", "présente_symptôme", "fatigue", "energetique"),
            ("insuffisance cardiaque", "présente_symptôme", "essoufflement", "respiratoire"),
            ("grippe", "présente_symptôme", "fièvre", "infectieux"),
            ("grippe", "présente_symptôme", "courbatures", "infectieux"),
            ("migraine", "présente_symptôme", "maux de tête", "nerveux"),
            ("angine de poitrine", "présente_symptôme", "douleur thoracique", "douleur"),
            ("gastrite", "présente_symptôme", "douleur abdominale", "digestif"),
            ("gastro-entérite", "présente_symptôme", "nausée", "digestif"),
            ("gastro-entérite", "présente_symptôme", "diarrhée", "digestif"),
            ("allergie", "présente_symptôme", "éruption cutanée", "cutane"),
            ("hypotension", "présente_symptôme", "vertiges", "nerveux"),
            ("anxiété", "présente_symptôme", "insomnie", "nerveux"),
            # gravité / conduite
            ("infection respiratoire", "gravité", "MODÉRÉE", "general"),
            ("insuffisance cardiaque", "gravité", "ÉLEVÉE", "general"),
            ("angine de poitrine", "gravité", "ÉLEVÉE", "general"),
            ("infection respiratoire", "conduite_à_tenir",
             "Repos, hydratation, consultation si fièvre persistante.", "general"),
            ("paludisme", "conduite_à_tenir", "Test rapide + traitement antipaludéen.", "general"),
            ("gastrite", "conduite_à_tenir", "Repas légers, éviter épices et alcool.", "general"),
            ("grippe", "conduite_à_tenir", "Repos et paracétamol si fièvre élevée.", "general"),
            ("insuffisance cardiaque", "conduite_à_tenir", "Consultation cardiologique rapide.", "general"),
        ]
        for s, r, o, sec in faits:
            self.domaines.setdefault(sec, HolographicMemory(self.dim, normaliser=normaliser_mot)) \
                .store(s, r, o, secteur=sec)

    def charger_holo_reels(self, dossier: Optional[str] = None) -> int:
        """Charge les *_facts.json de data/medical_holograms en hologrammes par secteur."""
        dossier = dossier or self.dossier
        if self._charge:
            return self.nb_faits()
        total = 0
        for chemin in sorted(glob.glob(os.path.join(dossier, "*_facts.json"))):
            nom = os.path.basename(chemin).replace("_facts.json", "")
            try:
                with open(chemin, encoding="utf-8") as f:
                    faits = json.load(f)
            except Exception:
                continue
            holo = self.domaines.setdefault(nom, HolographicMemory(self.dim, normaliser=normaliser_mot))
            for f in faits:
                holo.store(str(f.get("s", "")), str(f.get("r", "")), str(f.get("o", "")),
                           secteur=str(f.get("sec", nom)))
                total += 1
        self._charge = True
        return total

    def nb_faits(self) -> int:
        return sum(h.nb_faits for h in self.domaines.values())

    def domaines_liste(self) -> List[str]:
        return sorted(self.domaines.keys())

    # ── le diagnostic proprement dit ────────────────────────────────────
    def diagnostiquer(self, symptomes: List[str], vitaux: Optional[Dict[str, float]] = None,
                      age: Optional[int] = None, sexe: Optional[str] = None) -> Dict[str, Any]:
        """Expérience d'interférence : symptômes → résonance → émergence → diagnostic."""
        self.charger_holo_reels()
        symptomes = [s.strip() for s in (symptomes or []) if s and s.strip()]
        vitaux = {k: v for k, v in (vitaux or {}).items() if v is not None}

        resultats = self._resonance_symptomes(symptomes)
        analyse_vitales = self._analyse_vitales(vitaux)

        # score harmonique global : résonance calibrée + couverture
        if resultats["resultats"]:
            top = resultats["resultats"][0]["score_resonance"]
            couverture = resultats["couverture"]
            score_global = min(0.97, 0.35 + 0.30 * couverture + 0.15 * min(1.0, couverture / 0.5)
                               + 0.20 * top)
            score_global = round(score_global, 2)
        else:
            score_global = round(min(0.97, 0.30 + 0.15 * analyse_vitales["score_harmonique_global"]), 2)

        pathologie = resultats["resultats"][0] if resultats["resultats"] else None
        recommandations, contexte = self._recommandations(pathologie, analyse_vitales, symptomes)

        diagnostic_harmonique = {
            "pathologie_principale": pathologie["pathologie"] if pathologie else "Aucune pathologie dominante détectée",
            "constante_alteree": analyse_vitales["constante_alteree"] or "aucune",
            "mecanisme_harmonique": (f"Superposition de {len(symptomes)} ondes-symptômes résonnant "
                                     f"avec {self.nb_faits()} faits médicaux ; émergence par cohérence "
                                     f"de phase des pathologies candidates."),
            "score_confiance": round(pathologie["score_resonance"], 3) if pathologie else 0.0,
        }

        return {
            "score_harmonique_global": score_global,
            "diagnostic_harmonique": diagnostic_harmonique,
            "analyse_symptomes": resultats,
            "analyse_vitales": analyse_vitales,
            "frequences_therapeutiques": self._frequences(pathologie, resultats["resultats"]),
            "recommandations": recommandations,
            "disclaimer": DISCLAIMER,
            "age": age, "sexe": sexe,
            "niveau": self._niveau(score_global),
            "domaines": self.domaines_liste(),
        }

    def _resonance_symptomes(self, symptomes: List[str]) -> Dict[str, Any]:
        """Chaque symptôme est encodé puis fait résonner l'ensemble des hologrammes.
        Les pathologies candidates sont les sujets des faits « présente_symptôme »
        (les faits gravité/conduite/traitement ne sont pas des pathologies)."""
        if not symptomes:
            return {"resultats": [], "couverture": 0.0, "symptomes_analyses": []}
        psi_sym = superpose(*[encode(normaliser_mot(s), self.dim) for s in symptomes])
        scores_pathologies: Dict[str, float] = {}
        nb_symptomes_retrouves = 0
        for holo in self.domaines.values():
            for (fait, score) in holo.interroger(psi_sym, top_k=40, seuil=0.02):
                if "symptome" not in normaliser_mot(fait.relation):
                    continue                      # gravité, conduite, traitement…
                scores_pathologies[fait.sujet] = max(scores_pathologies.get(fait.sujet, 0.0), score)
        # couverture : combien de symptômes résonnent individuellement
        for s in symptomes:
            if any(res for (f, res) in self._resonance_individuelle(s, top=3)):
                nb_symptomes_retrouves += 1
        couverture = nb_symptomes_retrouves / max(1, len(symptomes))
        resultats = [{"pathologie": p, "score_resonance": round(s, 4)}
                     for p, s in sorted(scores_pathologies.items(), key=lambda t: -t[1])[:8]]
        return {"resultats": resultats, "couverture": round(couverture, 2),
                "symptomes_analyses": symptomes}

    def _resonance_individuelle(self, symptome: str, top: int = 3):
        psi = encode(normaliser_mot(symptome), self.dim)
        tous = []
        for holo in self.domaines.values():
            tous.extend(holo.interroger(psi, top_k=top, seuil=0.05))
        tous.sort(key=lambda t: -t[1])
        return tous[:top]

    def _analyse_vitales(self, vitaux: Dict[str, float]) -> Dict[str, Any]:
        scores = {}
        constante_alteree = ""
        plus_grand_ecart = 0.0
        for cle, (mini, maxi, unite) in VITAUX_NORMAUX.items():
            if cle not in vitaux:
                continue
            valeur = float(vitaux[cle])
            centre = (mini + maxi) / 2
            ecart_pct = round((valeur - centre) / centre * 100, 1)
            score = round(max(0.0, 1.0 - abs(ecart_pct) / 50.0), 3)
            scores[cle] = {"valeur": valeur, "unite": unite, "ecart_pct": ecart_pct,
                           "score_coherence": score, "normal": mini <= valeur <= maxi}
            if not scores[cle]["normal"] and abs(ecart_pct) > plus_grand_ecart:
                plus_grand_ecart = abs(ecart_pct)
                constante_alteree = cle
        if scores:
            score_global = round(sum(s["score_coherence"] for s in scores.values()) / len(scores), 3)
        else:
            score_global = 1.0
        return {"score_harmonique_global": score_global, "scores_individuels": scores,
                "constante_alteree": constante_alteree, "vitaux_analyses": list(scores.keys())}

    def _frequences(self, pathologie: Optional[dict], resultats: List[dict]) -> List[dict]:
        """Les fréquences thérapeutiques dérivées de la résonance du diagnostic."""
        if not resultats:
            return [{"freq_hz": 528.0, "effet": "équilibre global de l'organisme"}]
        freq = []
        for r in resultats[:2]:
            f, effet = FREQUENCES.get(self._domaine_de(r["pathologie"]), FREQUENCES["general"])
            freq.append({"freq_hz": f, "effet": effet})
        return freq

    def _domaine_de(self, pathologie: str) -> str:
        for sec, holo in self.domaines.items():
            if any(f.sujet == pathologie for f in holo._faits):
                return sec
        return "general"

    def _recommandations(self, pathologie: Optional[dict],
                         analyse_vitales: dict, symptomes: List[str]) -> Tuple[List[str], Dict[str, str]]:
        recos: List[str] = []
        contexte: Dict[str, str] = {}
        if pathologie:
            cible = normaliser_mot(pathologie["pathologie"])
            for holo in self.domaines.values():
                for fait in holo._faits:
                    if normaliser_mot(fait.sujet) != cible:
                        continue
                    if fait.relation == "conduite_à_tenir":
                        recos.append(f"{pathologie['pathologie']} : {fait.objet}")
                    elif fait.relation == "gravité":
                        contexte["gravité"] = fait.objet
                    elif fait.relation == "délai_consultation":
                        contexte["délai_consultation"] = fait.objet
        if analyse_vitales["constante_alteree"]:
            recos.append(f"Constante altérée : {analyse_vitales['constante_alteree']} — "
                         f"vérification à prévoir.")
        if not symptomes:
            recos.append("Aucun symptôme fourni : le diagnostic repose uniquement sur les vitales.")
        recos.append("Consultation médicale recommandée si les symptômes persistent.")
        return recos, contexte

    def _niveau(self, score: float) -> str:
        if score >= 0.75:
            return "élevé"
        if score >= 0.5:
            return "modéré"
        return "faible"

    # ── contrat /diagnose (app médecin) ─────────────────────────────────
    def diagnostiquer_medecin(self, symptomes: List[str], age: Optional[int] = None,
                              max_diagnoses: int = 5) -> Dict[str, Any]:
        """Contrat vitale-ka /diagnose : {diagnoses, disclaimer, score_harmonique, …}."""
        d = self.diagnostiquer(symptomes, age=age)
        n = min(max_diagnoses, len(d["analyse_symptomes"]["resultats"]))
        return {
            "diagnoses": [
                {"text": (f"Résonance {r['score_resonance']:.2f} — {r['pathologie']} "
                          f"(domaine {self._domaine_de(r['pathologie'])})"),
                 "diagnosis": r["pathologie"], "score": r["score_resonance"],
                 "secteur": self._domaine_de(r["pathologie"])}
                for r in d["analyse_symptomes"]["resultats"][:n]
            ],
            "disclaimer": DISCLAIMER,
            "score_harmonique": d["score_harmonique_global"],
            "niveau": d["niveau"],
            "domaines": d["domaines"],
            "vitals_check": d["analyse_vitales"],
            "recommandations": d["recommandations"],
        }
