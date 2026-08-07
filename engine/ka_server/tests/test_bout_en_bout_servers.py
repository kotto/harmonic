# -*- coding: utf-8 -*-
"""Validation de bout en bout des 3 serveurs KA (flux Vital Ka complet)."""
import json
import time
import urllib.request

ADMIN = "http://127.0.0.1:8000"
INFER = "http://127.0.0.1:8010"
MODU = "http://127.0.0.1:8765"

pass_count = 0
fail_count = 0


def check(name, cond, detail=""):
    global pass_count, fail_count
    if cond:
        pass_count += 1
        print("✅ " + name + (("  [" + str(detail) + "]") if detail else ""))
    else:
        fail_count += 1
        print("❌ " + name + (("  [" + str(detail) + "]") if detail else ""))


def call(method, url, body=None, headers=None):
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            raw = r.read().decode("utf-8", "ignore")
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw
    except Exception as e:
        return 0, str(e)


# ═══════════════════════════════════════════════════════════════════════
print("═══ 1. WALLET UM (admin-server 8000) ═══")
# 1a. Créer un compte patient
s, d = call("POST", ADMIN + "/api/v1/wallet/create", {"owner_id": "KAUSERPATIENT1", "role": "patient", "public_id": "KAPATIENT1"})
check("create wallet patient", s in (200, 201, 409), str(s) + " " + str(d)[:120])
# 1b. Créditer (solidarité)
s, d = call("POST", ADMIN + "/api/v1/wallet/credit", {"owner_id": "KAUSERPATIENT1", "amount_um": 500, "type": "solidarite_credit", "reference": "don-001"})
check("credit 500 UM", s == 200, str(s) + " " + str(d)[:100])
# 1c. Balance (walletId local accepté)
s, d = call("GET", ADMIN + "/api/v1/wallet/KAUSERPATIENT1/balance")
bal = d.get("balance_um") if isinstance(d, dict) else None
check("balance patient (walletId)", s == 200 and bal >= 500.0, str(s) + " " + str(d)[:100])
# 1d. Créer un compte pharmacien
s, d = call("POST", ADMIN + "/api/v1/wallet/create", {"owner_id": "KAUSERPHARMA1", "role": "pharmacie", "public_id": "KAPHARMA1"})
check("create wallet pharmacien", s in (200, 201, 409), str(s))
s, d = call("POST", ADMIN + "/api/v1/wallet/credit", {"owner_id": "KAUSERPHARMA1", "amount_um": 100, "type": "payment"})
check("credit pharmacien 100", s == 200, str(s))
# 1e. Paiement patient → pharmacien (ordonnance)
s, d = call("POST", ADMIN + "/api/v1/wallet/pay", {"from_owner_id": "KAUSERPATIENT1", "to_owner_id": "KAUSERPHARMA1", "amount_um": 150, "reference": "RX-2026-001"})
check("pay 150 UM patient→pharma", s == 200 and str(d.get("status")).lower() == "completed", str(s) + " " + str(d)[:120])
# 1f. Ledger du patient (walletId local)
s, d = call("GET", ADMIN + "/api/v1/wallet/KAUSERPATIENT1/ledger?limit=5")
txs = d.get("transactions") or d.get("ledger") or d.get("items") or []
check("ledger patient", s == 200 and len(txs) >= 1, str(s) + " " + str(len(txs)) + " tx")

# ═══════════════════════════════════════════════════════════════════════
print("\n═══ 2. DOSSIER MÉDICAL (admin-server 8000) ═══")
s, d = call("POST", ADMIN + "/api/v1/records", {"patient_id": "KAUSERPATIENT1", "profile": {"age": 45, "sexe": "F"}, "antecedents": ["hypertension"], "allergies": ["penicilline"]})
check("créer dossier", s in (200, 201, 409), str(s) + (" (déjà créé)" if s == 409 else ""))
s, d = call("GET", ADMIN + "/api/v1/records/KAUSERPATIENT1")
check("lire dossier", s == 200 and bool(d.get("patient_id")), str(s) + " " + str(d)[:80])

# ═══════════════════════════════════════════════════════════════════════
print("\n═══ 3. TÉLÉCONSULTATION (admin-server 8000) ═══")
s, d = call("POST", ADMIN + "/api/v1/teleconsult/link", {"patient_id": "KAUSERPATIENT1", "medecin_id": "DOCTOR-DIASPORA-1"})
token = d.get("token") or (d.get("link") or "").split("/")[-1]
check("créer lien téléconsult", s in (200, 201) and bool(token), str(s) + " " + str(d)[:80])
if token:
    s, d = call("GET", ADMIN + "/api/v1/teleconsult/" + token)
    check("valider lien (30 min)", s == 200, str(s))
    s, d = call("POST", ADMIN + "/api/v1/teleconsult/" + token + "/accept", {"medecin_id": "DOCTOR-DIASPORA-1"})
    check("accepter téléconsult", s == 200, str(s))

# ═══════════════════════════════════════════════════════════════════════
print("\n═══ 4. DIAGNOSTIC IA (inference 8010) ═══")
s, d = call("POST", INFER + "/diagnose", {"symptoms": ["fièvre", "toux", "fatigue"], "patient_age": 45, "max_diagnoses": 3})
diags = d.get("diagnoses") if isinstance(d, dict) else []
check("/diagnose : hypothèses", s == 200 and len(diags) >= 1, str(s) + " " + str(diags)[:120])
check("/diagnose : contrat app (text/score/secteur)", s == 200 and all("text" in x and "score" in x and "secteur" in x for x in diags))
s, d = call("POST", INFER + "/api/health/diagnostic", {"symptomes": ["palpitations"], "vitaux": {"frequence_cardiaque": 88}})
check("/api/health/diagnostic", s == 200, str(s))

# ═══════════════════════════════════════════════════════════════════════
print("\n═══ 5. RAISONNEMENT (modulaire 8765) ═══")
s, d = call("POST", MODU + "/api/chat", {"message": "quel est le double de 21 ?"})
check("émergence : double de 21 = 42", s == 200 and d.get("result") == 42.0, str(d.get("result")))
s, d = call("POST", MODU + "/api/chat", {"message": "combien font trois plus quatre ?"})
check("émergence : trois plus quatre = 7", s == 200 and d.get("result") == 7.0, str(d.get("result")))

print(f"\n═══════ VALIDATION BOUT EN BOUT : {pass_count} ✅ / {fail_count} ❌ ═══════")
import sys
sys.exit(1 if fail_count else 0)
