# -*- coding: utf-8 -*-
"""
cerveau.py — IaOndulatoire : le cerveau ondulatoire (boucle fermée §8.1).

    Pensée (question) → Génération (programme ondulatoire natif)
                      → Exécution (moteur + hologrammes)
                      → Résultat (synthèse en langage naturel) → Pensée

Mémoires holographiques :
    H_connaissances — connaissances générales (faites via le CLUI/API)
    H_faits         — faits appris (« souviens-toi que … »)
Le vocabulaire de décodage est auto-construit depuis tout ce que l'IA voit.
Persistance : <engine>/data/ia_ondulatoire/ (npz + json).
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import ir
from generateur import GenerateurOndulatoire, vocabulaire_de
from moteur import MoteurOndulatoire, QueryResult
from primitives import DEFAULT_DIM, HolographicMemory, Wave, decode, encode, resonate

DOSSIER_DONNEES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "data", "ia_ondulatoire")

SALUTATIONS = {
    "salut": "Salut ! Je suis l'IA ondulatoire — je pense en ondes, dans ℂ⁵¹². 🌊 Pose-moi une question, ou dis-moi « souviens-toi que … » pour m'apprendre quelque chose.",
    "bonjour": "Bonjour ! 🌊 Mon langage natal est le langage ondulatoire : ENCODE → MANIPULER → DÉCODER. Que veux-tu que je résonne aujourd'hui ?",
    "hello": "Hello ! 🌊 I think in waves — ℂ⁵¹². Ask me anything, or teach me with « remember that … ».",
    "coucou": "Coucou ! 🌊 Mes 13 primitives sont prêtes (encode, bind, superpose, interfere…). Quelle question fait vibrer ton esprit ?",
}
MERCI = ["merci", "merci beaucoup", "thanks", "thank you"]
AU_REVOIR = ["au revoir", "bye", "adieu", "à bientot", "a bientot"]


class _MemoireUnifiee:
    """Vue unique H_connaissances + H_faits pour les QUERY (duck-typed)."""

    def __init__(self, memoires: List[HolographicMemory]):
        self.memoires = memoires

    def interroger(self, psi_q: Wave, top_k: int = 8, seuil: float = 0.02):
        tous = []
        for mem in self.memoires:
            tous.extend(mem.interroger(psi_q, top_k=top_k, seuil=seuil))
        tous.sort(key=lambda t: -t[1])
        return tous[:top_k]


class IaOndulatoire:
    """La nouvelle IA — pense, génère et exécute dans sa langue natale."""

    MODELE = "langage-ondulatoire-v1"

    def __init__(self, dim: int = DEFAULT_DIM, dossier_donnees: str = DOSSIER_DONNEES,
                 charger: bool = True):
        self.dim = dim
        self.dossier = dossier_donnees
        self.H_connaissances = HolographicMemory(dim)
        self.H_faits = HolographicMemory(dim)
        self.vocabulaire: Dict[str, Wave] = {}
        self.memoire_conversation: List[Dict[str, Any]] = []
        self.generateur = GenerateurOndulatoire(dim=dim)
        self.moteur = MoteurOndulatoire(dim=dim)
        self.histo_par_user: Dict[str, List[Dict[str, str]]] = {}
        if charger:
            self.charger()

    # ────────────────────────────────────────────────────────────────────
    # Boucle fermée : poser une question
    # ────────────────────────────────────────────────────────────────────
    def poser(self, question: str, user_id: str = "local") -> Dict[str, Any]:
        """Question → programme ondulatoire → exécution → réponse en français."""
        debut = time.time()
        question = (question or "").strip()
        if not question:
            return self._reponse("Dis-moi quelque chose… 🌊", 0.0, "vide", debut)

        # chemins rapides déterministes (zéro LLM, zéro web)
        q_bas = question.lower().strip()
        for cle, rep in SALUTATIONS.items():
            if q_bas == cle:
                return self._reponse(rep, 1.0, "identity", debut)
        if any(m in q_bas for m in MERCI):
            return self._reponse("Avec plaisir. 🌊 N'oublie pas : je peux tout résonner.", 1.0, "identity", debut)
        if any(m in q_bas for m in AU_REVOIR):
            return self._reponse("Au revoir ! Que tes ondes restent cohérentes. 🌊", 1.0, "identity", debut)
        if q_bas in {"qui es-tu", "qui es tu", "tu es qui", "ta nature"}:
            return self._reponse(self._identite(), 1.0, "identity", debut)
        if q_bas in {"tes domaines", "que sais-tu faire", "tes capacités"}:
            return self._reponse(self._domaines(), 1.0, "identity_domains", debut)

        # chemin mathématique : GSM8K ondulatoire (0 LLM, sélection d'opération
        # par résonance contre les prototypes d'ondes)
        from gsm8k import GSM8KOndulatoire, est_question_maths
        if est_question_maths(question):
            r = GSM8KOndulatoire(dim=self.dim).resoudre(question)
            if r["reponse_num"] is not None:
                texte = ("Résolution ondulatoire : " + " → ".join(r["etapes"][-4:])
                         + f" = {r['reponse']}.")
                resultat = self._reponse(texte, 0.9, "ondulatoire-maths", debut)
                resultat.update({"intention": "reason",
                                 "programme": "ENCODE question → RESONATE(prototypes) → "
                                              "SUPERPOSE état → DÉCODER",
                                 "faits": r["etapes"][-3:]})
                self._enregistrer_conversation(question, texte, user_id, "maths")
                return resultat

        # boucle fermée : génération → validation → exécution
        programme, intention = self.generateur.generer(question)
        erreurs = ir.valider(programme, hologrammes=["H_connaissances", "H_faits"])
        if erreurs:
            return self._reponse(
                f"Mon programme ondulatoire a échoué la validation : {' ; '.join(erreurs)}",
                0.1, "erreur", debut)

        unifiee = _MemoireUnifiee([self.H_connaissances, self.H_faits])
        hologrammes = {"H_connaissances": unifiee, "H_faits": self.H_faits}
        env = self.moteur.executer(programme, hologrammes=hologrammes,
                                   vocabulaire=self.vocabulaire)
        self._nourrir_vocabulaire(question)

        reponse, confiance, faits = self._synthetiser(intention, env, question)

        # apprentissage implicite : si l'IA ne sait pas, elle propose d'apprendre
        if confiance < 0.18 and intention in ("query", "classify", "compare",
                                              "analogize", "reason"):
            entite = self._sujet(question)
            reponse = (f"Je ne connais pas encore « {entite} » dans ma mémoire ondulatoire. "
                       f"Dis-moi : « souviens-toi que {entite} est … » et je l'apprendrai. 🌊")
            source = "ondulatoire-invite"
        else:
            source = "ondulatoire-v1"

        latence = int((time.time() - debut) * 1000)
        resultat = self._reponse(reponse, confiance, source, debut)
        resultat.update({
            "intention": intention,
            "programme": ir.afficher(programme),
            "faits": faits,
            "latency_ms": latence,
        })
        self._enregistrer_conversation(question, resultat["response"], user_id, intention)
        return resultat

    # ────────────────────────────────────────────────────────────────────
    # Synthèse — ψ' → monde (§5.2.2)
    # ────────────────────────────────────────────────────────────────────
    def _synthetiser(self, intention: str, env: Dict[str, Any],
                     question: str) -> Tuple[str, float, List[str]]:
        retour = env.get("__return__")
        faits: List[str] = []

        if isinstance(retour, QueryResult):
            faits = [f.texte() for f, _ in retour.faits]
            if not faits:
                return "", 0.0, []
            confiance = round(min(0.99, 0.45 + 0.5 * retour.meilleur_score), 3)
            if intention == "reason":
                texte = ("Déduction ondulatoire (SUPERPOSE → EMERGE) : " + "; ".join(faits[:4])
                         + ". L'onde de la question résonne avec ces faits.")
            elif intention == "classify":
                texte = ("Catégorisation par résonance : " + "; ".join(faits[:4])
                         + ". Les concepts qui vibrent ensemble appartiennent au même domaine.")
            else:
                texte = "D'après ma mémoire holographique : " + "; ".join(faits[:5]) + "."
            return texte, confiance, faits

        if isinstance(retour, list):                      # DECODE → mots résonants
            mots = [str(m) for m in retour if str(m).strip()]
            if not mots:
                return "", 0.0, []
            confiance = 0.5
            if intention == "creative":
                texte = self._poetiser(mots, question)
                return texte, 0.62, mots
            if intention == "compare":
                s = env.get("similarite", 0.0)
                pct = max(0.0, min(100.0, float(s) * 50 + 50))
                texte = (f"Résonance mesurée : {pct:.0f} % de cohérence. "
                         f"Le contraste révélé par OPPOSE fait émerger : {', '.join(mots[:4])}.")
                return texte, 0.55, mots
            if intention == "analogize":
                texte = (f"L'analogie révélée par BIND → UNBIND : {', '.join(mots[:4])}. "
                         f"Ce qui vibre avec la première onde est la signature de la seconde.")
                return texte, 0.5, mots
            if intention == "reason":
                texte = "Déduction : " + ", ".join(mots[:5]) + "."
                return texte, 0.5, mots
            texte = "L'onde-réponse émerge : " + ", ".join(mots[:5]) + "."
            return texte, 0.5, mots

        if isinstance(retour, tuple):                     # STORE exécuté
            s, r, o = retour
            texte = f"🌊 J'ai mémorisé : « {s} {r} {o} » (BIND_MANY → STORE dans H_faits)."
            return texte, 1.0, [f"{s} {r} {o}"]

        if isinstance(retour, str) and retour:
            return retour, 0.5, [retour]

        if isinstance(retour, np.ndarray):
            mots = [mot for mot, _ in decode(retour, self.vocabulaire, top_k=5)]
            if mots:
                return "L'onde-réponse décode vers : " + ", ".join(mots) + ".", 0.5, mots
        return "", 0.0, []

    def _poetiser(self, mots: List[str], question: str) -> str:
        from generateur import MARQUEURS
        declencheurs = {m.strip() for m in MARQUEURS["creative"]}
        entites = [m for m in re.findall(r"[a-zàâäéèêëîïôöùûüç'-]+", question.lower())
                   if m not in mots and len(m) > 2 and m not in declencheurs]
        a = entites[0] if entites else mots[0] if mots else "l'inconnu"
        b = entites[1] if len(entites) > 1 else (mots[1] if len(mots) > 1 else "le vide")
        if len(mots) >= 2:
            lien = " et ".join(mots[:2])
        elif mots:
            lien = mots[0]
        else:
            lien = "la résonance"
        return (f"🌊 INTERFERE({a}, {b}, ε=0.15) — j'ai laissé les ondes de « {a} » et "
                f"« {b} » s'entre-mêler subtilement. Il en émerge {lien} : une connexion "
                f"que la raison n'aurait pas tissée.")

    # ────────────────────────────────────────────────────────────────────
    # Apprentissage — mémoriser
    # ────────────────────────────────────────────────────────────────────
    def memoriser(self, fait: str, user_id: str = "local") -> Dict[str, Any]:
        """« souviens-toi que X est Y » → programme STORE exécuté → H_faits."""
        debut = time.time()
        programme = self.generateur._faire_store_fact(fait, [])
        # extraction du triplet via le générateur
        sujet, relation, objet = self.generateur._extraire_triplet(
            fait, self._mots_pleins(fait))
        self.H_faits.store(sujet, relation, objet, secteur="appris")
        self._nourrir_vocabulaire(f"{sujet} {relation} {objet}")
        texte = f"🌊 J'ai mémorisé : « {sujet} {relation} {objet} » (BIND_MANY → STORE dans H_faits)."
        resultat = self._reponse(texte, 1.0, "ondulatoire-v1", debut)
        resultat.update({"intention": "store_fact", "programme": ir.afficher(programme),
                         "faits": [f"{sujet} {relation} {objet}"]})
        self._enregistrer_conversation(fait, texte, user_id, "store_fact")
        return resultat

    # ────────────────────────────────────────────────────────────────────
    # Créativité directe — interfère
    # ────────────────────────────────────────────────────────────────────
    def creer(self, concept_a: str, concept_b: str) -> Dict[str, Any]:
        """interfere(a, b, ε≈0.15) : la primitive de créativité, exécutée."""
        debut = time.time()
        programme = self.generateur._pattern_creative(concept_a, concept_b)
        env = self.moteur.executer(programme, hologrammes={},
                                   vocabulaire=self.vocabulaire)
        retour = env.get("__return__")
        mots = [str(m) for m in retour] if isinstance(retour, list) else []
        texte = self._poetiser(mots, f"{concept_a} {concept_b}")
        resultat = self._reponse(texte, 0.62, "ondulatoire-v1", debut)
        resultat.update({"intention": "creative", "programme": ir.afficher(programme),
                         "faits": mots})
        return resultat

    # ────────────────────────────────────────────────────────────────────
    # Petites aides
    # ────────────────────────────────────────────────────────────────────
    def _reponse(self, texte: str, confiance: float, source: str, debut: float) -> Dict[str, Any]:
        return {
            "response": texte,
            "confidence": float(confiance),
            "source": source,
            "latency_ms": int((time.time() - debut) * 1000),
            "model": self.MODELE,
            "language": "fr",
        }

    def _identite(self) -> str:
        return ("Je suis l'IA ondulatoire — née du DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE. "
                "Je pense dans ℂ⁵¹² avec 13 primitives universelles (encode, bind, superpose, "
                "resonate, interfere, emerge…), je génère mes propres programmes ondulatoires "
                "et je les exécute dans ma mémoire holographique. Pas de GPU, pas de paramètres "
                "appris : uniquement l'interférence des ondes. 🌊")

    def _domaines(self) -> str:
        return ("Mes 7 intentions : query (interroger), reason (déduire), creative (imaginer), "
                "store_fact (mémoriser), compare (contraster), analogize (analogiser), "
                "classify (catégoriser). Mes mémoires : H_connaissances et H_faits. "
                f"Actuellement : {self.H_faits.nb_faits} faits appris, "
                f"{len(self.vocabulaire)} mots au vocabulaire, "
                f"{len(self.memoire_conversation)} échanges en mémoire.")

    def _sujet(self, question: str) -> str:
        q = question.lower().strip("? .!;")
        for cle in ("qu'est-ce que ", "c'est quoi ", "qui est ", "explique-moi ",
                    "parle-moi de ", "définis ", "definis ", "pourquoi ",
                    "quelle est la différence entre ", "quelle est la difference entre ",
                    "comparer ", "comment ", "combien ", "quel type ", "catégorise "):
            if q.startswith(cle):
                reste = q[len(cle):].strip().strip(" ?.!;")
                if reste:
                    return reste.capitalize()
        mots = self._mots_pleins(question)
        return mots[0].capitalize() if mots else question

    def _mots_pleins(self, texte: str) -> List[str]:
        from generateur import _pseudo_mots
        return _pseudo_mots(texte)

    def _nourrir_vocabulaire(self, texte: str) -> None:
        for mot, psi in vocabulaire_de(texte, self.dim).items():
            if mot not in self.vocabulaire:
                self.vocabulaire[mot] = psi

    def _enregistrer_conversation(self, question: str, reponse: str,
                                  user_id: str, intention: str) -> None:
        entree = {"role": "user", "content": question,
                  "date": time.strftime("%Y-%m-%dT%H:%M:%S")}
        sortie = {"role": "assistant", "content": reponse,
                  "date": time.strftime("%Y-%m-%dT%H:%M:%S"), "intention": intention,
                  "user_id": user_id}
        self.memoire_conversation.append(entree)
        self.memoire_conversation.append(sortie)
        self.histo_par_user.setdefault(user_id, []).append(entree)
        self.histo_par_user[user_id].append(sortie)

    def souvenirs_recents(self, n: int = 10) -> List[Dict[str, str]]:
        """Timeline des souvenirs (contrat /api/memory/recent)."""
        souvenirs = []
        for entree in self.memoire_conversation[-2 * n:]:
            if entree["role"] == "assistant":
                souvenirs.append({
                    "title": entree.get("intention", "mémoire"),
                    "content": entree["content"][:300],
                    "date": entree["date"],
                })
        return souvenirs[-n:]

    def stats(self) -> Dict[str, Any]:
        return {
            "faits_appris": self.H_faits.nb_faits,
            "faits_connaissances": self.H_connaissances.nb_faits,
            "vocabulaire": len(self.vocabulaire),
            "echanges": len(self.memoire_conversation),
            "energie_faits": round(self.H_faits.energie, 4),
            "energie_connaissances": round(self.H_connaissances.energie, 4),
            "dim": self.dim,
            "modele": self.MODELE,
        }

    # ────────────────────────────────────────────────────────────────────
    # Persistance
    # ────────────────────────────────────────────────────────────────────
    def sauvegarder(self, dossier: Optional[str] = None) -> str:
        dossier = dossier or self.dossier
        os.makedirs(dossier, exist_ok=True)
        self.H_connaissances.sauvegarder(os.path.join(dossier, "h_connaissances.npz"))
        self.H_faits.sauvegarder(os.path.join(dossier, "h_faits.npz"))
        with open(os.path.join(dossier, "memoire_conversation.json"), "w", encoding="utf-8") as f:
            json.dump(self.memoire_conversation, f, ensure_ascii=False, indent=1)
        with open(os.path.join(dossier, "vocabulaire.json"), "w", encoding="utf-8") as f:
            json.dump(list(self.vocabulaire.keys()), f, ensure_ascii=False)
        return dossier

    def charger(self, dossier: Optional[str] = None) -> bool:
        dossier = dossier or self.dossier
        if not os.path.isdir(dossier):
            return False
        self.H_connaissances.charger(os.path.join(dossier, "h_connaissances.npz"))
        self.H_faits.charger(os.path.join(dossier, "h_faits.npz"))
        chemin_conv = os.path.join(dossier, "memoire_conversation.json")
        if os.path.exists(chemin_conv):
            try:
                with open(chemin_conv, encoding="utf-8") as f:
                    self.memoire_conversation = json.load(f)
            except Exception:
                self.memoire_conversation = []
        chemin_vocab = os.path.join(dossier, "vocabulaire.json")
        if os.path.exists(chemin_vocab):
            try:
                with open(chemin_vocab, encoding="utf-8") as f:
                    for mot in json.load(f):
                        self._nourrir_vocabulaire(mot)
            except Exception:
                pass
        # le vocabulaire se nourrit aussi des faits persistés
        for mem in (self.H_connaissances, self.H_faits):
            for fait in mem._faits:
                self._nourrir_vocabulaire(fait.texte())
        return True
