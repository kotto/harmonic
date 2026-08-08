# -*- coding: utf-8 -*-
"""
tests_e2e.py — P2.4 TESTS BOUT EN BOUT DES ROUTES (25+ routes)
===============================================================
Démarre le serveur sur un port de test (8799), teste chaque route avec
le statut HTTP et la forme JSON attendus. Exit non nul en cas d'échec.

Usage : python tests_e2e.py
"""

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error

PORT = 8800 + (os.getpid() % 200)   # port aléatoire : évite les serveurs périmés qui traînent (double bind Windows)
BASE = f"http://127.0.0.1:{PORT}"
TESTS = []


def test(nom, condition, detail=""):
    TESTS.append((nom, bool(condition), detail))
    print(f"  {'OK ' if condition else 'KO '} {nom}" + (f" — {detail}" if detail else ""))


def requete(chemin, methode="GET", corps=None, entetes=None, cle=None):
    url = BASE + chemin
    donnees = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(url, data=donnees, method=methode)
    req.add_header("Content-Type", "application/json")
    if cle:
        req.add_header("X-API-Key", cle)
    for k, v in (entetes or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def lancer_serveur():
    env = dict(os.environ, PORT=str(PORT))
    proc = subprocess.Popen(
        [sys.executable, "serveur.py", "--port", str(PORT), "--host", "127.0.0.1"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            st, _ = requete("/api/health")
            if st == 200:
                return proc
        except Exception:
            time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("serveur non démarré")


def arreter(proc):
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


print("P2.4 TESTS BOUT EN BOUT — démarrage du serveur sur :" + str(PORT))
proc = lancer_serveur()
try:
    # ── santé ───────────────────────────────────────────────────────────
    st, d = requete("/api/health")
    test("GET /api/health", st == 200 and "faits_appris" in d)

    # ── KA MOBILE ──────────────────────────────────────────────────────
    st, d = requete("/api/chat", "POST", {"message": "bonjour"})
    test("POST /api/chat (salutation)", st == 200 and d.get("source") == "identity")
    st, d = requete("/api/chat", "POST", {"message": "quelle est la masse du fer 56"})
    test("POST /api/chat (physique)", st == 200
         and d.get("source") == "ondulatoire-physique"
         and "55.93" in d.get("response", ""))
    st, d = requete("/api/chat", "POST", {"message": "combien font 17 + 25"})
    test("POST /api/chat (maths)", st == 200 and d.get("source") == "ondulatoire-maths")
    st, d = requete("/api/chat", "POST", {"message": "capitale du Botswana"})
    test("POST /api/chat (refus honnête)", st == 200
         and "je ne connais pas" in d.get("response", "").lower())
    st, d = requete("/api/chat", "POST", {"message": ""})
    test("POST /api/chat (vide → 400)", st == 400)
    st, d = requete("/api/chat", "POST", {"message": "x" * 2500})
    test("POST /api/chat (trop long → 422)", st == 422)

    st, d = requete("/api/memorise", "POST", {"fait": "Le test e2e est passé"})
    test("POST /api/memorise", st == 200 and "mémorisé" in d.get("response", ""))
    st, d = requete("/api/creative", "POST", {"a": "mer", "b": "ciel"})
    test("POST /api/creative", st == 200 and "response" in d)
    st, d = requete("/api/reason", "POST", {"question": "pourquoi le ciel est bleu"})
    test("POST /api/reason", st in (200, 422))
    st, d = requete("/api/memory/recent")
    test("GET /api/memory/recent", st == 200)

    # ── PHYSIQUE ───────────────────────────────────────────────────────
    st, d = requete("/api/physics/verification")
    test("GET /api/physics/verification", st == 200
         and d.get("vallee_noyaux") == 536)
    st, d = requete("/api/physics/constants")
    test("GET /api/physics/constants", st == 200 and "alpha_harmonique" in d)
    st, d = requete("/api/physics/mass?z=26&a=56")
    test("GET /api/physics/mass?z=26&a=56", st == 200
         and abs(d.get("masse_predite_u", 0) - 55.9329) < 0.01)
    st, d = requete("/api/physics/mass?z=26")
    test("GET /api/physics/mass (z seul → 400)", st == 400)
    st, d = requete("/api/physics/island")
    test("GET /api/physics/island", st == 200 and len(d.get("elements", [])) == 23)
    st, d = requete("/api/physics/periodique")
    test("GET /api/physics/periodique", st == 200 and len(d.get("elements", [])) == 118)
    st, d = requete("/api/physics/chat", "POST", {"question": "masse du plomb 208"})
    test("POST /api/physics/chat", st == 200 and d.get("type") == "isotope")

    # ── VITAL KA ───────────────────────────────────────────────────────
    st, d = requete("/api/health/diagnostic", "POST",
                    {"symptomes": ["fièvre", "toux"]})
    test("POST /api/health/diagnostic", st == 200 and "analyse_symptomes" in d)
    st, d = requete("/api/health/diagnostic", "POST", {"symptomes": []})
    test("POST /api/health/diagnostic (vide → 400)", st == 400)
    st, d = requete("/diagnose", "POST", {"symptomes": ["maux de tête"]})
    test("POST /diagnose", st == 200 and "diagnoses" in d)

    # ── KA ENTERPRISE (la clé vient de /demo — jamais devinée) ─────────
    st, d = requete("/api/v2/enterprise/demo", "POST")
    test("POST enterprise/demo (crée la clé)", st == 200 and "api_key" in d)
    cle_ent = d.get("api_key", "")
    st, d = requete("/api/v2/enterprise/ingest", "POST",
                    {"text": "Le rapport trimestriel est positif."},
                    cle=cle_ent)
    test("POST enterprise/ingest (clé /demo)", st == 200)
    st, d = requete("/api/v2/enterprise/ingest", "POST",
                    {"text": "test"})
    test("POST enterprise/ingest (sans clé → 401)", st == 401)
    st, d = requete("/api/v2/enterprise/ask", "POST",
                    {"question": "résumé ?"}, cle=cle_ent)
    test("POST enterprise/ask", st == 200)
    st, d = requete("/api/v2/enterprise/usage", cle=cle_ent)
    test("GET enterprise/usage", st == 200 and "total_requetes" in d)

    # ── EDUCAL KA ──────────────────────────────────────────────────────
    st, d = requete("/api/educal/units")
    test("GET /api/educal/units", st == 200 and "catalog" in d)
    premiere_unite = None
    for dis in (d.get("catalog") or {}).values():
        for liste in dis.values() if isinstance(dis, dict) else []:
            if liste:
                premiere_unite = liste[0].get("id")
                break
        if premiere_unite:
            break
    st, d = requete("/api/educal/quiz/submit", "POST",
                    {"unit_id": premiere_unite or "edu_francais_grammaire_6e",
                     "answers": [{"question": 0, "answer": "A"}],
                     "user_id": "e2e"})
    test("POST /api/educal/quiz/submit", st == 200 and "quiz" in d)
    st, d = requete("/api/educal/quiz/submit", "POST",
                    {"unit_id": premiere_unite or "edu_francais_grammaire_6e",
                     "answers": ["A", "B"]})
    test("POST /api/educal/quiz/submit (mal formé → 400)", st == 400)
    st, d = requete("/api/educal/progress/testuser")
    test("GET /api/educal/progress", st == 200)

    # ── MATHS (route restaurée 08/08/2026) ─────────────────────────────
    st, d = requete("/api/maths/solve", "POST", {"question": "combien font 6 fois 7"})
    test("POST /api/maths/solve", st == 200 and d.get("reponse_num") == 42)
    st, d = requete("/api/maths/solve", "POST", {"question": ""})
    test("POST /api/maths/solve (vide → 400)", st == 400)

    # ── VOIX (dégradation propre si Piper éteint) ──────────────────────
    st, d = requete("/api/voice/health")
    test("GET /api/voice/health", st == 200 and "status" in d)
    st, d = requete("/api/voice/offline/caps")
    test("GET /api/voice/offline/caps", st == 200)

    # ── STORE / PERSONALIZE ────────────────────────────────────────────
    st, d = requete("/api/store/list")
    test("GET /api/store/list", st == 200)
    st, d = requete("/api/personalize/build", "POST", {"domaine": "general"})
    test("POST /api/personalize/build", st in (200, 501))

    # ── 404 ────────────────────────────────────────────────────────────
    st, d = requete("/api/route-inexistante")
    test("GET route inconnue → 404", st == 404)

finally:
    arreter(proc)

n_ok = sum(1 for _, ok, _ in TESTS if ok)
print("=" * 60)
print(f"BILAN E2E : {n_ok}/{len(TESTS)} routes OK")
sys.exit(0 if n_ok == len(TESTS) else 1)
