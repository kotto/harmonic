#!/usr/bin/env python3
"""
VÉRIFICATEUR DE COHÉRENCE — Assainit les hologrammes par domaine
=================================================================
La spécialisation par domaine est l'architecture optimale (mesurée :
elle bat le classement global), MAIS elle n'est optimale QUE quand le
domaine est propre. Mesure du 10/08/2026 : 20,9 % de contradictions
internes dans les hologrammes officiels (346/1653 faits — même sujet,
même relation, objets différents).

Ce module :
    1. DÉTECTE les contradictions : (sujet, relation) → objets multiples
    2. RÉSOUT par vote majoritaire : l'objet le plus fréquent pour un
       (sujet, relation) est conservé, les autres sont écartés
    3. RAPPORTE la propreté par domaine (taux de contradiction, faits
       conservés) — la « qualité réelle », distincte de la qualité
       déclarée (mesurée non prédictive : nature déclare 0,650 mais a
       22,2 % de contradictions)

Limite honnête : le vote majoritaire rend le domaine COHÉRENT (interne),
pas nécessairement VRAI (externe) — si la majorité est fausse (ex. 3×
« Zurich7 » contre 1× « Amsterdam »), la cohérence garde le faux. La
corroboration externe (wiki, sources) est la porte suivante.

Usage :
    from verificateur_coherence import VerificateurCoherence
    vc = VerificateurCoherence()
    rapport = vc.analyser(holo_id)          # propreté d'un domaine
    faits_propres = vc.assainir(holo_id)    # faits cohérents
"""

import sys, os, json
from collections import defaultdict

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE_DIR)


def _norm(texte):
    """Normalise un texte pour la comparaison (minuscules, espaces)."""
    return " ".join(str(texte).lower().strip().split())


class VerificateurCoherence:
    """Détecte et résout les contradictions internes d'un hologramme."""

    def __init__(self, store=None):
        if store is None:
            from hologram_store import HologramStore
            store = HologramStore()
        self.store = store

    # =====================================================================
    # ANALYSE
    # =====================================================================

    def _grouper_par_cle(self, facts):
        """(sujet, relation) normalisés → {objet normalisé: [faits bruts]}"""
        groupes = defaultdict(list)
        for s, r, o, sec in facts:
            cle = (_norm(s), _norm(r))
            obj = _norm(o)
            groupes[cle].append({"objet_norm": obj, "objet": o,
                                 "sujet": s, "relation": r, "secteur": sec})
        return groupes

    def analyser(self, holo_id: str) -> dict:
        """
        Rapport de cohérence d'un hologramme.

        Returns:
            {faits, contradictions, taux, groupes_contradictoires}
        """
        facts, _ = self.store.download(holo_id)
        if not facts:
            return {"faits": 0, "contradictions": 0, "taux": 0.0,
                    "groupes_contradictoires": []}

        groupes = self._grouper_par_cle(facts)
        n_contrad = 0
        groupes_contrad = []
        for cle, items in groupes.items():
            objets_distincts = {it["objet_norm"] for it in items}
            if len(objets_distincts) > 1:
                # Nombre de faits MINORITAIRES (ce que le vote majoritaire
                # écarte réellement) : total − occurrences de l'objet gagnant
                from collections import Counter
                comptage = Counter(it["objet_norm"] for it in items)
                gagnant = comptage.most_common(1)[0][1]
                n_contrad += len(items) - gagnant
                groupes_contrad.append({
                    "sujet": items[0]["sujet"],
                    "relation": items[0]["relation"],
                    "objets": sorted(objets_distincts)[:5],
                    "n_objets": len(objets_distincts),
                    "a_ecarter": len(items) - gagnant,
                })
        return {
            "faits": len(facts),
            "contradictions": n_contrad,
            "taux": round(n_contrad / max(1, len(facts)), 4),
            "groupes_contradictoires": groupes_contrad,
        }

    def analyser_tous(self, prefixe: str = "official_") -> dict:
        """Rapport de cohérence de tous les hologrammes d'un préfixe."""
        rapport = {}
        for h in self.store.list_holograms():
            if not h["id"].startswith(prefixe):
                continue
            rapport[h["id"]] = self.analyser(h["id"])
        return rapport

    # =====================================================================
    # ASSAINISSEMENT
    # =====================================================================

    def assainir(self, holo_id: str, verbose: bool = True) -> list:
        """
        Faits cohérents d'un hologramme (vote majoritaire par clé).

        Pour chaque (sujet, relation) : l'objet le plus fréquent est
        conservé ; les objets minoritaires sont écartés.

        Returns:
            liste de faits (s, r, o, secteur) cohérents.
        """
        facts, _ = self.store.download(holo_id)
        if not facts:
            return []
        groupes = self._grouper_par_cle(facts)

        propres = []
        n_ecartes = 0
        for cle, items in groupes.items():
            # Vote majoritaire : l'objet le plus fréquent
            comptage = defaultdict(int)
            for it in items:
                comptage[it["objet_norm"]] += 1
            gagnant = max(comptage.items(), key=lambda x: x[1])[0]
            for it in items:
                if it["objet_norm"] == gagnant:
                    propres.append((it["sujet"], it["relation"],
                                    it["objet"], it["secteur"]))
                else:
                    n_ecartes += 1
        if verbose:
            print(f"  [Verif] {holo_id} : {len(facts)} → {len(propres)} faits "
                  f"({n_ecartes} écartés)")
        return propres

    def assainir_tous(self, prefixe: str = "official_", verbose: bool = True) -> dict:
        """Assainit tous les hologrammes d'un préfixe."""
        resultats = {}
        for h in self.store.list_holograms():
            if not h["id"].startswith(prefixe):
                continue
            resultats[h["id"]] = self.assainir(h["id"], verbose=verbose)
        return resultats

    def rapport_proprete(self, prefixe: str = "official_") -> dict:
        """
        Rapport de propreté global : taux de contradiction par domaine,
        ordonné du plus propre au plus bruité.
        """
        rapport = self.analyser_tous(prefixe)
        lignes = []
        for hid, r in rapport.items():
            lignes.append((hid, r["faits"], r["contradictions"], r["taux"]))
        lignes.sort(key=lambda x: x[3])
        return {
            "domaines": [
                {"hologramme": hid, "faits": f, "contradictions": c,
                 "taux": t}
                for hid, f, c, t in lignes
            ],
            "total_faits": sum(l[1] for l in lignes),
            "total_contradictions": sum(l[2] for l in lignes),
            "taux_global": round(
                sum(l[2] for l in lignes) / max(1, sum(l[1] for l in lignes)), 4),
        }


if __name__ == "__main__":
    vc = VerificateurCoherence()
    print("=" * 70)
    print("VÉRIFICATEUR DE COHÉRENCE — propreté des domaines officiels")
    print("=" * 70)
    rapport = vc.rapport_proprete()
    for d in rapport["domaines"]:
        print(f"  {d['hologramme']:<28} {d['faits']:>5} faits | "
              f"{d['contradictions']:>4} contradict. | {d['taux']:>6.1%}")
    print(f"\n  GLOBAL : {rapport['total_faits']} faits, "
          f"{rapport['total_contradictions']} contradictions "
          f"({rapport['taux_global']:.1%})")
