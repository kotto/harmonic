# -*- coding: utf-8 -*-
"""
entreprise.py — KA Enterprise en langage ondulatoire natif.

Chaque département d'un tenant possède son propre hologramme : les documents
ingérés sont découpés en faits (sujet relation objet) puis liés par BIND_MANY
et superposés (STORE). Les questions font résonner l'hologramme du département
(QUERY → EMERGE → DÉCODER) et retournent les sources.

    POST /api/v2/enterprise/ingest  {department, text|file}  → STORE
    POST /api/v2/enterprise/ask     {department, question}   → QUERY → EMERGE → DÉCODER
    POST /api/v2/enterprise/summarize/compose                → EMERGE / INTERFERE
    GET  /api/v2/enterprise/documents|usage                  → état
Auth : X-API-Key (RBAC admin/viewer/auditor) — persistance data/ia_ondulatoire/enterprise.json
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional

from primitives import DEFAULT_DIM, HolographicMemory, Wave, encode, resonate, superpose

DOSSIER_DONNEES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "data", "ia_ondulatoire")

RELATIONS = ["est", "a", "fournit", "gère", "gere", "produit", "assure", "délivre",
             "delivre", "contient", "compte", "utilise", "dépend de", "depend de",
             "signifie", "prévoit", "prevoit", "vise", "coûte", "coute", "représente",
             "represente", "permet", "nécessite", "necessite", "s'applique à",
             "s'applique a", "suit", "respecte", "mesure", "surveille", "documente"]


def _clé_role(role: str) -> bool:
    return role in ("admin", "viewer", "auditor")


def _nettoyer(mot: str) -> str:
    """Normalise un token : ponctuation ôtée, article défini retiré.
    « Le cabinet » → « cabinet » ; « 120 clients. » → « 120 clients »."""
    mot = mot.strip(" .!?,;:'\"()[]{}")
    for article in ("le ", "la ", "les ", "l'", "un ", "une ", "des ", "du ", "de "):
        if mot.lower().startswith(article):
            mot = mot[len(article):]
            break
    return mot.strip()


class EntrepriseOndulatoire:
    """Le cerveau enterprise : un hologramme par département, le langage ondulatoire partout."""

    def __init__(self, dim: int = DEFAULT_DIM, dossier_donnees: str = DOSSIER_DONNEES):
        self.dim = dim
        self.dossier = dossier_donnees
        self.tenants: Dict[str, Dict[str, Any]] = {}          # tenant_id → {nom, departements: {nom: holo}}
        self.hologrammes: Dict[Tuple[str, str], HolographicMemory] = {}
        self.documents: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        self.cles: Dict[str, Dict[str, str]] = {}             # api_key → {tenant, role, nom}
        self.usage: List[Dict[str, Any]] = []
        self.charger()

    # ── tenants & clés ──────────────────────────────────────────────────
    def creer_tenant(self, nom: str) -> Dict[str, str]:
        tenant_id = uuid.uuid4().hex[:8]
        self.tenants[tenant_id] = {"nom": nom, "departements": {}}
        cle = self._nouvelle_cle(tenant_id, "admin", f"admin-{nom}")
        return {"tenant_id": tenant_id, "api_key": cle, "nom": nom}

    def departement(self, tenant_id: str, nom: str) -> HolographicMemory:
        if tenant_id not in self.tenants:
            raise KeyError(f"tenant inconnu : {tenant_id}")
        if (tenant_id, nom) not in self.hologrammes:
            self.hologrammes[(tenant_id, nom)] = HolographicMemory(self.dim)
            self.tenants[tenant_id]["departements"][nom] = {"documents": 0, "faits": 0}
            self.documents[(tenant_id, nom)] = []
        return self.hologrammes[(tenant_id, nom)]

    def _nouvelle_cle(self, tenant_id: str, role: str, nom: str) -> str:
        cle = uuid.uuid4().hex
        self.cles[cle] = {"tenant": tenant_id, "role": role, "nom": nom}
        return cle

    def ajouter_utilisateur(self, tenant_id: str, nom: str, role: str = "viewer") -> str:
        if not _clé_role(role):
            raise ValueError("rôle invalide (admin/viewer/auditor)")
        return self._nouvelle_cle(tenant_id, role, nom)

    def autoriser(self, api_key: str, roles: Optional[List[str]] = None) -> Optional[Dict[str, str]]:
        info = self.cles.get(api_key)
        if info is None:
            return None
        if roles and info["role"] not in roles:
            return None
        return info

    # ── ingestion : texte → faits → STORE ───────────────────────────────
    def ingerer(self, tenant_id: str, departement: str, texte: str,
                nom_doc: str = "document") -> Dict[str, Any]:
        """Découpe le texte en faits, les lie (BIND_MANY) et les superpose dans l'hologramme."""
        holo = self.departement(tenant_id, departement)
        debut = time.time()
        triplets = self._extraire_faits(texte, departement)
        n = 0
        for s, r, o in triplets:
            holo.store(s, r, o, secteur=departement, doc_id=nom_doc)
            n += 1
        doc_id = uuid.uuid4().hex[:8]
        self.documents[(tenant_id, departement)].append(
            {"doc_id": doc_id, "nom": nom_doc, "faits": n,
             "date": time.strftime("%Y-%m-%dT%H:%M:%S")})
        self.tenants[tenant_id]["departements"][departement]["documents"] += 1
        self.tenants[tenant_id]["departements"][departement]["faits"] += n
        self._log(tenant_id, departement, "ingest", {"doc": nom_doc, "faits": n})
        return {"success": True, "doc_id": doc_id, "faits_ajoutes": n,
                "total_faits": holo.nb_faits, "elapsed_ms": int((time.time() - debut) * 1000)}

    def _extraire_faits(self, texte: str, departement: str) -> List[tuple]:
        """Phrases → triplets (sujet, relation, objet). Heuristiques + patrons regex."""
        triplets: List[tuple] = []
        phrases = re.split(r"(?<=[.!?])\s+|\n+", texte)
        for phrase in phrases:
            p = phrase.strip()
            if not p or len(p) < 8:
                continue
            triple = self._patron_relation(p)
            if triple:
                triplets.append(triple)
                continue
            # paires clé : valeur (« Budget : 12 M »)
            m = re.match(r"^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_ \-]{1,60})\s*[:\-]\s*(.{4,120})$", p)
            if m:
                triplets.append((m.group(1).strip(), "vaut", m.group(2).strip()))
                continue
            # phrase sans patron : sujet = département/topic, relation = « concerne »
            mots = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9'\-]+", p)
            sujet = mots[0].lower() if mots else departement
            triplets.append((departement, "concerne", p[:140]))
        return triplets

    def _patron_relation(self, phrase: str) -> Optional[tuple]:
        for rel in RELATIONS:
            m = re.search(r"\b(.{2,60}?)\s+(?:ne\s+)?(?:se\s+)?(?:n'|l'|le |la |les )?"
                          + re.escape(rel) + r"\b\s+(.+)$", phrase, re.IGNORECASE)
            if m:
                sujet = _nettoyer(m.group(1))
                objet = _nettoyer(m.group(2))
                if sujet and objet and len(sujet) >= 2:
                    return (sujet.lower(), rel.lower(), objet)
        return None

    # ── question : QUERY → EMERGE → DÉCODER ─────────────────────────────
    def poser(self, tenant_id: str, departement: str, question: str) -> Dict[str, Any]:
        """Interroge l'hologramme du département par résonance (QUERY).

        L'onde de la question est la superposition des mots pleins — la question
        est un paquet de concepts (§5.2.6) — plus l'onde de la phrase entière.
        Les candidats résonants sont re-triés par recouvrement lexical (la
        résonance sélectionne, le lexique épingle le fait exact)."""
        debut = time.time()
        holo = self.departement(tenant_id, departement)
        tokens = [t for t in re.findall(r"[a-zàâäéèêëîïôöùûüç]+", question.lower())
                  if len(t) > 2 and t not in
                  {"est", "quoi", "que", "quelle", "quel", "combien", "dans", "avec",
                   "pour", "sur", "entre", "liste", "donne", "moi", "le", "la", "les",
                   "une", "des", "the", "how", "what", "are", "is", "of"}]
        ondes = [encode(question, self.dim)]
        ondes += [encode(_nettoyer(m), self.dim) for m in dict.fromkeys(tokens)][:8]
        psi_q = superpose(*ondes)

        # score hybride : résonance ondulatoire + bonus de recouvrement lexical
        # (la résonance sélectionne le domaine, le lexique épingle le fait exact)
        def score_lexical(fait) -> int:
            texte = f"{fait.sujet} {fait.relation} {fait.objet}".lower()
            return sum(1 for t in tokens if t in texte)

        scores = []
        for fait in holo._faits:
            s_res = resonate(psi_q, fait.psi)
            scores.append((fait, s_res + 0.18 * score_lexical(fait)))
        scores.sort(key=lambda t: t[1], reverse=True)
        faits = [t for t in scores if t[1] > 0.0][:6] or scores[:4]
        if not faits:
            reponse = (f"Je n'ai rien trouvé dans l'hologramme du département "
                       f"« {departement} » ({holo.nb_faits} faits). Ingérez des documents "
                       f"pour enrichir ma mémoire ondulatoire.")
            confiance = 0.0
            sources = []
        else:
            meilleur, score = faits[0]
            reponse = "D'après ma mémoire ondulatoire : " + "; ".join(
                f.texte() for f, _ in faits[:4]) + "."
            confiance = round(min(0.99, max(0.0, score)), 3)
            sources = [{"sujet": f.sujet, "relation": f.relation, "objet": f.objet,
                        "score": round(s, 3), "doc": f.doc_id} for f, s in faits]
        self._log(tenant_id, departement, "ask", {"question": question, "confiance": confiance})
        return {
            "question": question, "answer": reponse, "confidence": confiance,
            "sources": sources, "department": departement,
            "response_id": uuid.uuid4().hex[:12],
            "elapsed_ms": int((time.time() - debut) * 1000),
            "admitted_uncertainty": round(1.0 - confiance, 3),
        }

    # ── résumé / composition : EMERGE / INTERFERE ───────────────────────
    def resumer(self, tenant_id: str, departement: str, max_faits: int = 5) -> Dict[str, Any]:
        """EMERGE : les faits les plus cohérents entre eux émergent en résumé."""
        holo = self.departement(tenant_id, departement)
        psi = holo.unbind_raw(encode(departement, self.dim))
        faits = holo.interroger(psi, top_k=max_faits, seuil=0.0)
        texte = (f"Résumé émergent du département « {departement} » "
                 f"({holo.nb_faits} faits) : " + "; ".join(f.texte() for f, _ in faits) + ".")
        return {"summary": texte, "faits_utilises": len(faits),
                "elapsed_ms": 1, "department": departement}

    def composer(self, tenant_id: str, departement: str, type_doc: str = "rapport",
                 sujet: str = "") -> Dict[str, Any]:
        """INTERFERE : un rapport émerge en interférant les faits dominants du département."""
        holo = self.departement(tenant_id, departement)
        psi_q = encode(sujet or departement, self.dim)
        faits = holo.interroger(psi_q, top_k=4, seuil=0.0)
        lignes = [f.texte() for f, _ in faits]
        intro = f"{type_doc.capitalize()} sur « {sujet or departement} »"
        corps = " ; ".join(lignes) if lignes else "aucun fait disponible"
        texte = f"{intro}.\n{corps}."
        return {"type": type_doc, "contenu": texte, "faits_utilises": len(lignes),
                "department": departement}

    # ── état & usage ────────────────────────────────────────────────────
    def documents_liste(self, tenant_id: str, departement: str) -> List[Dict[str, Any]]:
        return self.documents.get((tenant_id, departement), [])

    def usage_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        logs = self.usage
        if tenant_id:
            logs = [l for l in logs if l["tenant"] == tenant_id]
        par_endpoint: Dict[str, int] = {}
        for l in logs:
            par_endpoint[l["type"]] = par_endpoint.get(l["type"], 0) + 1
        return {"total_requetes": len(logs), "par_endpoint": par_endpoint,
                "tenants": len(self.tenants),
                "faits_totaux": sum(h.nb_faits for h in self.hologrammes.values()),
                "utilisateurs": len(self.cles)}

    def _log(self, tenant: str, departement: str, type_: str, details: dict) -> None:
        self.usage.append({"tenant": tenant, "department": departement, "type": type_,
                           "date": time.strftime("%Y-%m-%dT%H:%M:%S"), **details})
        if len(self.usage) > 500:
            self.usage = self.usage[-250:]

    # ── persistance ─────────────────────────────────────────────────────
    def sauvegarder(self, dossier: Optional[str] = None) -> str:
        dossier = dossier or self.dossier
        os.makedirs(dossier, exist_ok=True)
        for (tid, dep), holo in self.hologrammes.items():
            holo.sauvegarder(os.path.join(dossier, f"ent_{tid}_{dep}.npz"))
        etat = {
            "tenants": self.tenants, "cles": self.cles,
            "documents": {f"{tid}::{dep}": docs for (tid, dep), docs in self.documents.items()},
            "usage": self.usage[-250:],
        }
        with open(os.path.join(dossier, "enterprise.json"), "w", encoding="utf-8") as f:
            json.dump(etat, f, ensure_ascii=False, indent=1)
        return dossier

    def charger(self, dossier: Optional[str] = None) -> bool:
        dossier = dossier or self.dossier
        chemin = os.path.join(dossier, "enterprise.json")
        if not os.path.exists(chemin):
            return False
        try:
            with open(chemin, encoding="utf-8") as f:
                etat = json.load(f)
            self.tenants = etat.get("tenants", {})
            self.cles = etat.get("cles", {})
            for cle, docs in etat.get("documents", {}).items():
                tid, dep = cle.split("::", 1)
                self.documents[(tid, dep)] = docs
            self.usage = etat.get("usage", [])
            for (tid, dep), _docs in list(self.documents.items()):
                holo = self.departement(tid, dep)
                holo.charger(os.path.join(dossier, f"ent_{tid}_{dep}.npz"))
            return True
        except Exception:
            return False
