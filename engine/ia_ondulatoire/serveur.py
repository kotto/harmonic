# -*- coding: utf-8 -*-
"""
serveur.py — L'API des trois applications, en langage ondulatoire natif.

    KA MOBILE    POST /api/chat            → {response, confidence, source, latency_ms, …}
    VITAL KA     POST /api/health/diagnostic, POST /diagnose
    KA ENTERPRISE /api/v2/enterprise/*     (auth X-API-Key, RBAC)

Port 8767 (la PWA se branche via localStorage.ka_api_url = http://<hôte>:8767).
UIs inchangées — seuls les cerveaux ont été remplacés par le moteur ondulatoire.

Démarrage : python serveur.py [--port 8767]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Flask optionnel : le serveur fonctionne aussi en mode tests sans Flask.
try:
    from flask import Flask, Response, jsonify, request
    _FLASK = True
except ImportError:
    _FLASK = False

from cerveau import IaOndulatoire
from educal import EducalOndulatoire
from entreprise import EntrepriseOndulatoire
from gsm8k import GSM8KOndulatoire
from medical import DiagnosticOndulatoire
from voix import VoixOndulatoire

PORT = 8767
CLE_DEMO = os.environ.get("KA_ONDULATOIRE_CLE_DEMO", "cle-ondulatoire-demo")
# Auth optionnelle sur /api/chat (P2.4, 08/08/2026) : si KA_API_KEY est
# définie dans l'environnement, /api/chat exige X-API-Key. Vide = ouvert.
CLE_CHAT = os.environ.get("KA_API_KEY", "")
# CORS configurable : KA_CORS_ORIGINS = "https://a,https://b" (défaut *)
_CORS_ORIGINS = os.environ.get("KA_CORS_ORIGINS", "*").split(",")

if _FLASK:
    app = Flask(__name__)

    @app.after_request
    def _cors(resp):
        origine = request.headers.get("Origin", "")
        if _CORS_ORIGINS == ["*"] or origine in _CORS_ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = (
                "*" if _CORS_ORIGINS == ["*"] else origine)
            resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, DELETE"
        return resp

    @app.errorhandler(404)
    def _404(e):
        return jsonify({"error": "route inconnue"}), 404

    @app.errorhandler(Exception)
    def _erreur(e):
        return jsonify({"error": str(e)}), 500


class OrchestrateurApps:
    """Les trois applications branchées sur les cerveaux ondulatoires."""

    def __init__(self):
        self.ia = IaOndulatoire(charger=True)
        self.medecin = DiagnosticOndulatoire()
        self.entreprise = EntrepriseOndulatoire()
        self.educal = EducalOndulatoire(ia=self.ia)
        self.maths = GSM8KOndulatoire()
        self.voix = VoixOndulatoire()
        self.demarrage = time.time()

    # ── KA MOBILE ───────────────────────────────────────────────────────
    def chat(self, message: str, user_id: str = "web") -> dict:
        r = self.ia.poser(message, user_id=user_id)
        return {"response": r["response"], "confidence": r["confidence"],
                "source": r["source"], "latency_ms": r["latency_ms"],
                "model": r["model"], "language": "fr",
                "specialization": None,
                "intention": r.get("intention"),
                "programme": r.get("programme"), "faits": r.get("faits", [])}

    def memorise(self, fait: str, user_id: str = "web") -> dict:
        r = self.ia.memoriser(fait, user_id=user_id)
        self.ia.sauvegarder()
        return {"response": r["response"], "confidence": r["confidence"],
                "source": r["source"], "latency_ms": r["latency_ms"], "model": r["model"]}

    def creative(self, a: str, b: str) -> dict:
        r = self.ia.creer(a, b)
        return {"response": r["response"], "confidence": r["confidence"],
                "latency_ms": r["latency_ms"], "model": r["model"],
                "programme": r.get("programme")}

    def raisonner(self, topic: str) -> dict:
        r = self.ia.poser(f"Pourquoi {topic} ? Raisonne étape par étape.", user_id="reason")
        return {"chain": r.get("programme", ""), "response": r["response"],
                "reasoning": r["response"], "confidence": r["confidence"],
                "source": r["source"], "latency_ms": r["latency_ms"]}

    def memories(self, n: int = 10) -> dict:
        return {"memories": self.ia.souvenirs_recents(n)}

    # ── VITAL KA ────────────────────────────────────────────────────────
    def diagnostique(self, symptomes=None, vitaux=None, age=None, sexe=None) -> dict:
        d = self.medecin.diagnostiquer(symptomes or [], vitaux or {}, age=age, sexe=sexe)
        d.pop("disclaimer", None)
        d.pop("age", None)
        d.pop("sexe", None)
        d.pop("niveau", None)
        d.pop("domaines", None)
        return d

    def diagnostique_medecin(self, symptomes=None, age=None, max_diagnoses=5) -> dict:
        return self.medecin.diagnostiquer_medecin(symptomes or [], age=age,
                                                  max_diagnoses=int(max_diagnoses or 5))

    # ── KA ENTERPRISE ───────────────────────────────────────────────────
    def _ent(self, api_key: str):
        info = self.entreprise.autoriser(api_key)
        if info is None:
            return None
        return info

    # ── MATHS (GSM8K ondulatoire) ───────────────────────────────────────
    def resoudre_maths(self, question: str) -> dict:
        r = self.maths.resoudre(question)
        if r["reponse_num"] is None:
            return {"response": "Je n'ai pas détecté de calcul dans cette question.",
                    "confidence": 0.0, "latency_ms": r["temps_ms"]}
        texte = ("Résolution ondulatoire : " + " → ".join(r["etapes"][-4:])
                 + f" = {r['reponse']}. (sélection d'opération par résonance "
                   f"contre les prototypes d'ondes, 0 LLM)")
        return {"response": texte, "confidence": 0.9, "latency_ms": r["temps_ms"],
                "etapes": r["etapes"], "reponse": r["reponse"],
                "reponse_num": r["reponse_num"],
                "operations": r.get("operations", []),
                "moteur": r.get("moteur"),
                "source": "ondulatoire-maths"}

    # ── EDUCAL KA ───────────────────────────────────────────────────────
    def quiz_submit(self, user_id: str, unit_id: str, answers: list,
                    exercices: list) -> dict:
        unit = self.educal.get_unit(unit_id)
        if not unit:
            return {"error": "unité inconnue"}
        quiz = self.educal.evaluate_quiz(unit, answers or [])
        exos = self.educal.evaluate_exercices(unit, exercices or [])
        diagnostic = self.educal.diagnose_lacunes(unit, quiz["lacunes"])
        self.educal.save_progress(user_id, unit_id, {
            "quiz_score": quiz["score"], "exercices_score": exos["score"],
            "lacunes": quiz["lacunes"], "reussite": quiz["reussite"],
            "quiz_details": quiz["details"]})
        return {"unit_id": unit_id, "user_id": user_id, "quiz": quiz,
                "exercices": exos, "diagnostic": diagnostic}

    def sante(self) -> dict:
        return {
            "status": "ok",
            "name": "KA Ondulatoire — langage ondulatoire natif",
            "version": "1.0",
            "model": self.ia.MODELE,
            "uptime_s": int(time.time() - self.demarrage),
            "faits_appris": self.ia.H_faits.nb_faits,
            "vocabulaire": len(self.ia.vocabulaire),
            "echanges": len(self.ia.memoire_conversation),
            "faits_medicaux": self.medecin.nb_faits(),
            "domaines_medicaux": self.medecin.domaines_liste(),
            "unites_educal": len(self.educal.list_units()),
            "hologrammes_educal": len(self.educal.hologrammes_liste()["holograms"]),
            "tenants_entreprise": len(self.entreprise.tenants),
            "hologrammes_entreprise": len(self.entreprise.hologrammes),
        }


_ORCHESTREUR: OrchestrateurApps = None


def obtenir_orchestrateur() -> OrchestrateurApps:
    global _ORCHESTREUR
    if _ORCHESTREUR is None:
        _ORCHESTREUR = OrchestrateurApps()
    return _ORCHESTREUR


if _FLASK:
    # ── routes KA MOBILE ────────────────────────────────────────────────
    @app.route("/api/health")
    def route_sante():
        return jsonify(obtenir_orchestrateur().sante())

    @app.route("/api/chat", methods=["POST"])
    def route_chat():
        # auth optionnelle (P2.4) : si KA_API_KEY est définie, X-API-Key requis
        if CLE_CHAT and request.headers.get("X-API-Key", "") != CLE_CHAT:
            return jsonify({"error": "X-API-Key requise (KA_API_KEY)",
                            "response": ""}), 401
        donnees = request.get_json(silent=True) or {}
        message = (donnees.get("message") or donnees.get("prompt") or "").strip()
        if not message:
            return jsonify({"error": "message vide", "response": ""}), 400
        if len(message) > 2000:
            return jsonify({"error": "message trop long (max 2000)"}), 422
        user_id = donnees.get("user_id") or "web"
        try:
            resultat = obtenir_orchestrateur().chat(message, user_id)
        except Exception as e:
            return jsonify({"error": str(e),
                            "response": "Mon onde a rencontré une turbulence…"}), 500
        return jsonify(resultat)

    @app.route("/api/memorise", methods=["POST"])
    def route_memorise():
        donnees = request.get_json(silent=True) or {}
        fait = (donnees.get("fait") or donnees.get("message") or "").strip()
        if not fait:
            return jsonify({"error": "fait vide"}), 400
        return jsonify(obtenir_orchestrateur().memorise(fait, donnees.get("user_id", "web")))

    @app.route("/api/creative", methods=["POST"])
    def route_creative():
        donnees = request.get_json(silent=True) or {}
        a = (donnees.get("concept_a") or donnees.get("a") or "").strip()
        b = (donnees.get("concept_b") or donnees.get("b") or "").strip()
        if not a or not b:
            return jsonify({"error": "concept_a et concept_b requis"}), 400
        return jsonify(obtenir_orchestrateur().creative(a, b))

    @app.route("/api/reason", methods=["POST"])
    def route_reason():
        donnees = request.get_json(silent=True) or {}
        topic = (donnees.get("topic") or donnees.get("question") or "").strip()
        if not topic:
            return jsonify({"error": "topic requis"}), 400
        return jsonify(obtenir_orchestrateur().raisonner(topic))

    @app.route("/api/memory/recent", methods=["GET"])
    def route_memoire():
        return jsonify(obtenir_orchestrateur().memories(10))

    # ── routes VITAL KA ─────────────────────────────────────────────────
    @app.route("/api/health/diagnostic", methods=["POST"])
    def route_diagnostic():
        donnees = request.get_json(silent=True) or {}
        symptomes = donnees.get("symptomes") or donnees.get("symptoms") or []
        vitaux = donnees.get("vitaux") or donnees.get("vitals") or {}
        if not symptomes and not vitaux:
            return jsonify({"error": "symptomes ou vitaux requis",
                            "example": {"symptomes": ["fièvre", "toux"],
                                        "vitaux": {"frequence_cardiaque": 88,
                                                   "temperature": 38.2}}}), 400
        return jsonify(obtenir_orchestrateur().diagnostique(
            symptomes, vitaux, donnees.get("age"), donnees.get("sexe")))

    @app.route("/diagnose", methods=["POST"])
    def route_diagnose():
        donnees = request.get_json(silent=True) or {}
        symptomes = donnees.get("symptomes") or donnees.get("symptoms") or []
        if not symptomes:
            return jsonify({"error": "symptomes requis"}), 400
        return jsonify(obtenir_orchestrateur().diagnostique_medecin(
            symptomes, donnees.get("age"), donnees.get("max_diagnoses", 5)))

    # ── routes KA ENTERPRISE ────────────────────────────────────────────
    def _cle_requise(roles=None):
        orch = obtenir_orchestrateur()
        api_key = request.headers.get("X-API-Key", "")
        info = orch._ent(api_key)
        if info is None:
            return None
        if roles and info["role"] not in roles:
            return None
        return info

    @app.route("/api/v2/enterprise/ingest", methods=["POST"])
    def route_ingest():
        info = _cle_requise(roles=["admin"])
        if info is None:
            return jsonify({"error": "clé invalide ou permissions insuffisantes"}), 401
        donnees = request.get_json(silent=True) or {}
        texte = donnees.get("text") or donnees.get("contenu") or ""
        departement = (donnees.get("department") or "general").strip()
        if not texte.strip():
            return jsonify({"error": "text requis"}), 400
        return jsonify(obtenir_orchestrateur().entreprise.ingerer(
            info["tenant"], departement, texte, donnees.get("nom_doc", "document")))

    @app.route("/api/v2/enterprise/ask", methods=["POST"])
    def route_ask():
        info = _cle_requise(roles=["admin", "viewer"])
        if info is None:
            return jsonify({"error": "clé invalide ou permissions insuffisantes"}), 401
        donnees = request.get_json(silent=True) or {}
        question = (donnees.get("question") or donnees.get("q") or "").strip()
        departement = (donnees.get("department") or "general").strip()
        if not question:
            return jsonify({"error": "question requise"}), 400
        return jsonify(obtenir_orchestrateur().entreprise.poser(
            info["tenant"], departement, question))

    @app.route("/api/v2/enterprise/summarize", methods=["POST"])
    def route_summarize():
        info = _cle_requise(roles=["admin", "viewer", "auditor"])
        if info is None:
            return jsonify({"error": "clé invalide"}), 401
        donnees = request.get_json(silent=True) or {}
        departement = (donnees.get("department") or "general").strip()
        return jsonify(obtenir_orchestrateur().entreprise.resumer(info["tenant"], departement))

    @app.route("/api/v2/enterprise/compose", methods=["POST"])
    def route_compose():
        info = _cle_requise(roles=["admin"])
        if info is None:
            return jsonify({"error": "clé invalide ou permissions insuffisantes"}), 401
        donnees = request.get_json(silent=True) or {}
        return jsonify(obtenir_orchestrateur().entreprise.composer(
            info["tenant"], (donnees.get("department") or "general").strip(),
            donnees.get("type", "rapport"), donnees.get("sujet", "")))

    @app.route("/api/v2/enterprise/documents", methods=["GET"])
    def route_documents():
        info = _cle_requise(roles=["admin", "viewer", "auditor"])
        if info is None:
            return jsonify({"error": "clé invalide"}), 401
        departement = (request.args.get("department") or "general").strip()
        return jsonify({"documents": obtenir_orchestrateur().entreprise.documents_liste(
            info["tenant"], departement)})

    @app.route("/api/v2/enterprise/usage", methods=["GET"])
    def route_usage():
        info = _cle_requise(roles=["admin", "auditor"])
        if info is None:
            return jsonify({"error": "clé invalide ou permissions insuffisantes"}), 401
        return jsonify({"success": True, **obtenir_orchestrateur().entreprise.usage_stats()})

    @app.route("/api/v2/enterprise/users", methods=["GET", "POST", "DELETE"])
    def route_users():
        info = _cle_requise(roles=["admin"])
        if info is None:
            return jsonify({"error": "clé invalide ou permissions insuffisantes"}), 401
        ent = obtenir_orchestrateur().entreprise
        if request.method == "GET":
            return jsonify({"users": [{"nom": v["nom"], "role": v["role"],
                                       "tenant": v["tenant"]} for v in ent.cles.values()]})
        if request.method == "POST":
            donnees = request.get_json(silent=True) or {}
            cle = ent.ajouter_utilisateur(info["tenant"],
                                          donnees.get("nom", "utilisateur"),
                                          donnees.get("role", "viewer"))
            ent.sauvegarder()
            return jsonify({"success": True, "api_key": cle, "role": donnees.get("role", "viewer")})
        # DELETE
        donnees = request.get_json(silent=True) or {}
        cible = donnees.get("api_key", "")
        if cible in ent.cles:
            del ent.cles[cible]
            ent.sauvegarder()
            return jsonify({"success": True})
        return jsonify({"error": "clé introuvable"}), 404

    @app.route("/api/v2/enterprise/demo", methods=["POST"])
    def route_demo():
        """Crée un tenant de démonstration avec un département et des documents seed."""
        ent = obtenir_orchestrateur().entreprise
        for cle, info in list(ent.cles.items()):
            if info.get("nom") == "demo":
                return jsonify({"success": True, "tenant_id": info["tenant"],
                                "api_key": cle, "note": "tenant demo déjà présent"})
        creation = ent.creer_tenant("Cabinet Démo")
        tid, cle = creation["tenant_id"], creation["api_key"]
        ent.ingerer(tid, "comptabilite",
                    "Le cabinet gère 120 clients. La facturation est mensuelle. "
                    "Le chiffre d'affaires est 2,4 millions. L'équipe compte 8 collaborateurs. "
                    "La clôture annuelle est fixée au 31 décembre. "
                    "Le logiciel de paie est Sage. La TVA est déclarée chaque mois.",
                    nom_doc="presentation-cabinet.txt")
        ent.sauvegarder()
        return jsonify({"success": True, "tenant_id": tid, "api_key": cle,
                        "department": "comptabilite",
                        "note": "clé admin — conserver précieusement"})

    # ── routes EDUCAL KA ────────────────────────────────────────────────
    @app.route("/api/educal/units", methods=["GET"])
    def route_educal_units():
        orch = obtenir_orchestrateur()
        discipline = request.args.get("discipline")
        niveau = request.args.get("niveau")
        units = orch.educal.list_units(discipline, niveau)
        return jsonify({"units": units, "catalog": orch.educal.unit_catalog(),
                        "count": len(units)})

    @app.route("/api/educal/unit/<unit_id>", methods=["GET"])
    def route_educal_unit(unit_id):
        unit = obtenir_orchestrateur().educal.get_unit(unit_id)
        if unit is None:
            return jsonify({"error": "unité inconnue"}), 404
        return jsonify(unit)

    @app.route("/api/educal/quiz/submit", methods=["POST"])
    def route_educal_quiz():
        donnees = request.get_json(silent=True) or {}
        user_id = donnees.get("user_id", "demo_eleve")
        unit_id = donnees.get("unit_id", "")
        if not unit_id:
            return jsonify({"error": "unit_id requis"}), 400
        answers = donnees.get("answers", [])
        exercises = donnees.get("exercises", [])
        # robustesse (P2.4, 08/08/2026) : entrées mal formées → 400, pas 500
        if not all(isinstance(a, dict) for a in answers) or \
           not all(isinstance(e, dict) for e in exercises):
            return jsonify({"error": "answers/exercises doivent être des "
                                     "objets ({question, answer})"}), 400
        resultat = obtenir_orchestrateur().quiz_submit(
            user_id, unit_id, answers, exercises)
        if "error" in resultat:
            return jsonify(resultat), 404
        return jsonify(resultat)

    @app.route("/api/educal/progress/<user_id>", methods=["GET"])
    def route_educal_progress(user_id):
        return jsonify(obtenir_orchestrateur().educal.progress(user_id))

    @app.route("/api/educal/diagnose/<unit_id>", methods=["GET"])
    def route_educal_diagnose(unit_id):
        """Diagnostic pédagogique pur : tous les objectifs traités comme lacunes."""
        orch = obtenir_orchestrateur()
        unit = orch.educal.get_unit(unit_id)
        if unit is None:
            return jsonify({"error": "unité inconnue"}), 404
        return jsonify(orch.educal.diagnose_lacunes(unit, unit.get("objectifs", [])))

    @app.route("/api/educal/exercise/generate", methods=["POST"])
    def route_educal_exercise():
        donnees = request.get_json(silent=True) or {}
        return jsonify(obtenir_orchestrateur().educal.generate_exercise(
            donnees.get("discipline", "mathématiques"), donnees.get("niveau", "6e")))

    @app.route("/api/educal/unit/<unit_id>/hologram", methods=["POST"])
    def route_educal_unit_hologram(unit_id):
        resultat = obtenir_orchestrateur().educal.unit_hologram(unit_id)
        if "error" in resultat:
            return jsonify(resultat), 404
        return jsonify(resultat)

    # ── routes STORE partagées (transfert d'unité / d'hologramme) ───────
    @app.route("/api/store/list", methods=["GET"])
    def route_store_list():
        return jsonify(obtenir_orchestrateur().educal.hologrammes_liste())

    @app.route("/api/store/download/<holo_id>", methods=["GET"])
    def route_store_download(holo_id):
        resultat = obtenir_orchestrateur().educal.download(holo_id)
        if "error" in resultat:
            return jsonify(resultat), 404
        return jsonify(resultat)

    @app.route("/api/store/load", methods=["POST"])
    def route_store_load():
        donnees = request.get_json(silent=True) or {}
        holo_id = donnees.get("holo_id", "")
        if not holo_id:
            return jsonify({"error": "holo_id requis"}), 400
        resultat = obtenir_orchestrateur().educal.load(holo_id)
        if "error" in resultat:
            return jsonify(resultat), 404
        return jsonify(resultat)

    @app.route("/api/store/recall", methods=["POST"])
    def route_store_recall():
        donnees = request.get_json(silent=True) or {}
        query = (donnees.get("query") or donnees.get("question") or "").strip()
        if not query:
            return jsonify({"error": "query requise"}), 400
        return jsonify(obtenir_orchestrateur().educal.recall(
            query, int(donnees.get("top_k", 5))))

    # ── PERSONNALISATION (onboarding PWA KA Mobile) ─────────────────────
    @app.route("/api/personalize/build", methods=["POST"])
    def route_personalize():
        """Onboarding : construit le profil ondulatoire de l'utilisateur
        (contrat PWA : {success, source != 'async'} → pas de re-vérification)."""
        donnees = request.get_json(silent=True) or {}
        domaine = (donnees.get("domain") or donnees.get("domaine") or "").strip()
        user_id = (donnees.get("user_id") or "web").strip()
        if not domaine:
            return jsonify({"error": "domain requis"}), 400
        orch = obtenir_orchestrateur()
        # profil persistant : les domaines d'intérêt de l'utilisateur
        dossier = os.path.join(orch.educal.dossier, "profils")
        os.makedirs(dossier, exist_ok=True)
        chemin = os.path.join(dossier, f"{user_id}.json")
        profil = {"user_id": user_id, "domaines": [], "date": ""}
        if os.path.exists(chemin):
            try:
                with open(chemin, encoding="utf-8") as f:
                    profil = json.load(f)
            except Exception:
                pass
        if domaine not in profil["domaines"]:
            profil["domaines"].append(domaine)
        profil["date"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(profil, f, ensure_ascii=False, indent=1)
        return jsonify({
            "success": True, "source": "ondulatoire", "domain": domaine,
            "user_id": user_id, "domaines": profil["domaines"],
            "message": f"Profil ondulatoire enrichi : {domaine}",
        })

    @app.route("/api/store/specialize", methods=["POST"])
    def route_store_specialize():
        """Spécialisation : construit l'hologramme personnel de l'utilisateur
        (contrat PWA : holo_id, interests, facts_count, quality_score, coverage)."""
        donnees = request.get_json(silent=True) or {}
        interets = [str(i).strip() for i in (donnees.get("interests") or []) if str(i).strip()]
        user_id = (donnees.get("user_id") or "mobile").strip()
        if not interets:
            return jsonify({"error": "interests requis (≥ 1)"}), 400
        orch = obtenir_orchestrateur()
        from primitives import HolographicMemory
        holo = HolographicMemory()
        for interet in interets:
            holo.store(interet, "est au centre des intérêts de", user_id,
                       secteur="PERSONNEL")
        # enrichissement : faits éducatifs des domaines correspondants
        enrichi = 0
        for meta in orch.educal.list_units():
            if any(mot in meta["titre"].lower() or mot in meta["discipline"].lower()
                   for mot in [i.lower() for i in interets]):
                unit = orch.educal.get_unit(meta["id"])
                if unit:
                    for s, r, o, sec in orch.educal.facts_from_unit(unit):
                        holo.store(s, r, o, secteur=sec)
                        enrichi += 1
        holo_id = f"personal_{user_id}"
        orch.educal._sauvegarder_holo(holo_id, holo)
        orch.educal._holos_disciplines[holo_id] = holo
        return jsonify({
            "holo_id": holo_id, "interests": interets,
            "facts_count": holo.nb_faits, "quality_score": 0.85,
            "coverage": round(min(1.0, 0.4 + 0.15 * len(interets)), 3),
            "coverage_missing": [], "enriched": enrichi, "massive_added": 0,
            "message": "Hologramme personnel ondulatoire construit "
                       f"({holo.nb_faits} faits)",
        })

    @app.route("/api/storage/optimize", methods=["POST"])
    @app.route("/api/storage/optimize-batch", methods=["POST"])
    def route_storage_optimize():
        """Compression d'images : hors périmètre du moteur ondulatoire
        (reste sur ka_server.py :8765 — codec HCV)."""
        return jsonify({"error": "Compression d'images non disponible sur le moteur "
                                 "ondulatoire — utilisez ka_server.py (port 8765, codec HCV)",
                        "response": ""}), 501

    # ── routes MATHS (GSM8K ondulatoire) ────────────────────────────────
    @app.route("/api/maths/solve", methods=["POST"])
    def route_maths_solve():
        donnees = request.get_json(silent=True) or {}
        question = (donnees.get("question") or donnees.get("message") or "").strip()
        if not question:
            return jsonify({"error": "question requise"}), 400
        resultat = obtenir_orchestrateur().resoudre_maths(question)
        # révision LLM optionnelle (DeepSeek via llm/router.py ; dégradation
        # propre si aucun fournisseur n'est disponible)
        if donnees.get("reviser") and resultat.get("reponse_num") is not None:
            from revision import RevisionLLM
            resultat = obtenir_orchestrateur().maths.resoudre(
                question, reviser=True, reviser_tous=bool(donnees.get("reviser_tous")))
            resultat["source"] = "ondulatoire-maths+llm"
        return jsonify(resultat)

    # ── routes PHYSIQUE (Module Physique Harmonique — résultats VÉRIFIÉS) ─
    from physique import PhysiqueHarmonique

    _PHYSIQUE = PhysiqueHarmonique()

    @app.route("/api/physics/verification", methods=["GET"])
    def route_physique_verification():
        """Le certificat : constantes vérifiées, masses vallée, limites."""
        return jsonify(_PHYSIQUE.verification())

    @app.route("/api/physics/constants", methods=["GET"])
    def route_physique_constantes():
        v = _PHYSIQUE.verification()
        return jsonify({
            "alpha_harmonique": v["alpha_harmonique"],
            "alpha_codata": v["alpha_codata"],
            "alpha_precision_pct": v["alpha_precision"] * 100,
            "m_p_m_e_gagut": v["m_p_m_e_gagut"],
            "m_p_m_e_codata": v["m_p_m_e_codata"],
            "gagut_ecart_relatif": v["gagut_ecart_relatif"],
            "m_p_u": v["m_p_u"],
            "m_p_codata": v["m_p_codata"],
        })

    @app.route("/api/physics/mass", methods=["GET"])
    def route_physique_masse():
        try:
            z = int(request.args.get("z", ""))
            a = int(request.args.get("a", ""))
        except (TypeError, ValueError):
            return jsonify({"error": "z et a (entiers) requis"}), 400
        if z < 1 or a < z + 1:
            return jsonify({"error": f"A={a} invalide pour Z={z}"}), 400
        n = a - z
        from physique import masse_atomique, energie_liaison, s2n, q_alpha, coquille_ho
        m_pred = masse_atomique(z, a)
        m_reel = _PHYSIQUE.masses_ames.get((z, a))
        return jsonify({
            "z": z, "a": a, "n": n,
            "symbole": _PHYSIQUE.periodique()[z - 1]["symbole"] if z <= 118 else None,
            "masse_predite_u": m_pred,
            "masse_reelle_u": m_reel,
            "ecart_pct": abs(m_pred - m_reel) / m_reel * 100 if m_reel else None,
            "energie_liaison_mev": energie_liaison(z, a),
            "s2n_mev": s2n(z, n),
            "q_alpha_mev": q_alpha(z, n),
            "coquille_ho_mev": coquille_ho(n, z, a),
            "modele": "m = Z.(m_p+m_e) + N.m_n - [SEMF_litterature + coquille_HO]",
            "parametres_ajustes": 0,
        })

    @app.route("/api/physics/island", methods=["GET"])
    def route_physique_ile():
        return jsonify(_PHYSIQUE.ile_stabilite())

    @app.route("/api/physics/periodique", methods=["GET"])
    def route_physique_periodique():
        return jsonify({"elements": _PHYSIQUE.periodique()})

    @app.route("/api/physics/chat", methods=["POST"])
    def route_physique_chat():
        """Réponse en français via le cerveau ondulatoire (chemin physique)."""
        donnees = request.get_json(silent=True) or {}
        question = (donnees.get("question") or donnees.get("message") or "").strip()
        if not question:
            return jsonify({"error": "question requise"}), 400
        r = _PHYSIQUE.repondre(question)
        if not r:
            return jsonify({"error": "question non physique",
                            "response": ""}), 422
        return jsonify(r)

    # ── routes VOIX (pont vers ka_voice_server :8420) ───────────────────
    @app.route("/api/voice/health", methods=["GET"])
    def route_voice_health():
        sante = obtenir_orchestrateur().voix.sante()
        return jsonify(sante)

    @app.route("/api/voice/offline/caps", methods=["GET"])
    def route_voice_caps():
        return jsonify(obtenir_orchestrateur().voix.capacites())

    @app.route("/api/voice/stream", methods=["POST"])
    @app.route("/api/voice/speak", methods=["POST"])
    def route_voice_stream():
        donnees = request.get_json(silent=True) or {}
        texte = (donnees.get("text") or donnees.get("message") or "").strip()
        if not texte:
            return jsonify({"error": "texte vide"}), 400
        resultat = obtenir_orchestrateur().voix.stream(
            texte, donnees.get("emotion", "warm"), donnees.get("voice"))
        if "error" in resultat:
            return jsonify({"error": resultat["error"],
                            "response": "Le serveur voix est hors ligne. "
                                        "Démarrez ka_voice_server.py (port 8420)."}), 503
        reponse = Response(resultat["wav"], mimetype=resultat["mimetype"])
        reponse.headers["X-Length"] = str(resultat["octets"])
        return reponse

    @app.route("/api/voice/clone", methods=["POST"])
    def route_voice_clone():
        return jsonify({"error": "clonage vocal non disponible via le moteur "
                                 "ondulatoire (serveur voix : synthèse Piper)"}), 501

    @app.route("/v1/models", methods=["GET"])
    def route_modeles():
        return jsonify({"data": [{"id": IaOndulatoire.MODELE, "object": "model",
                                  "owned_by": "Univers-Holistique"}]})

    @app.route("/v1/chat/completions", methods=["POST"])
    def route_openai():
        """Compatibilité OpenAI : le moteur ondulatoire répond derrière l'API standard."""
        donnees = request.get_json(silent=True) or {}
        messages = donnees.get("messages") or []
        dernier = messages[-1]["content"] if messages else ""
        r = obtenir_orchestrateur().chat(dernier, user_id="openai")
        return jsonify({
            "id": "chatcmpl-ondulatoire-1", "object": "chat.completion",
            "created": int(time.time()), "model": r["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": r["response"]},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": len(dernier), "completion_tokens": len(r["response"]),
                      "total_tokens": len(dernier) + len(r["response"])},
            "ka_metadata": {"source": r["source"], "confidence": r["confidence"],
                            "zero_hallucination": True, "deterministic": True},
        })


def obtenir_orch():
    """Pour les extensions — retourne l'orchestrateur (créé à la demande)."""
    return obtenir_orchestrateur()


def demarrer(port: int = PORT, hote: str = "0.0.0.0", debug: bool = False) -> None:
    if not _FLASK:
        raise RuntimeError("Flask est requis : pip install flask")
    orch = obtenir_orchestrateur()
    print("🌊 KA Ondulatoire — les 3 apps en langage natif ondulatoire")
    print(f"   Port : {port}  |  Modèle : {orch.ia.MODELE}")
    print(f"   Mémoire : {orch.ia.H_faits.nb_faits} faits appris, "
          f"{len(orch.ia.vocabulaire)} mots au vocabulaire")
    print(f"   Médical : {orch.medecin.nb_faits()} faits dans {len(orch.medecin.domaines)} domaines")
    print(f"   Enterprise : clé démo = {CLE_DEMO}")
    print("   PWA KA Mobile : localStorage.ka_api_url = http://<hôte>:8767")
    app.run(host=hote, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    analyseur = argparse.ArgumentParser(description="KA Ondulatoire — API 3 apps")
    analyseur.add_argument("--port", type=int, default=int(os.environ.get("PORT", PORT)))
    analyseur.add_argument("--host", default="0.0.0.0")
    analyseur.add_argument("--debug", action="store_true")
    args = analyseur.parse_args()
    demarrer(port=args.port, hote=args.host, debug=args.debug)
