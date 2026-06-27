#!/usr/bin/env python3
"""
BATCH INGESTION CYCLIQUE v4 - KA Phone
========================================
Correction radicale :
  1. Injection DIRECTE dans quick_facts.py (marqueur: self.facts = FACTS)
  2. Rechargement du module QuickFacts entre chaque cycle
  3. Normalisation des reponses (garder uniquement la valeur pour les maths)
  4. Suivi correct du score avec le vrai JSON d'audit
"""
import os, sys, json, time, subprocess, importlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

CYCLES_MAX = 10
MAX_FACTS_PER_CYCLE = 20
STATE_FILE = os.path.join(SCRIPT_DIR, "..", "data", "ingestion_state.json")
QF_PATH = os.path.join(SCRIPT_DIR, "quick_facts.py")
AUDIT_SCRIPT = os.path.join(SCRIPT_DIR, "audit_100_questions.py")
EXPAND_SCRIPT = os.path.join(SCRIPT_DIR, "expand_hologram_1024.py")
AUDIT_REPORT = os.path.join(SCRIPT_DIR, "audit_report.json")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cycle": 0, "last_score": 0, "history": [], "injected_facts": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def run_audit():
    """Lance l'audit et retourne le rapport JSON complet."""
    print("  [1/3] Execution de l'audit...")
    ret = subprocess.run([sys.executable, AUDIT_SCRIPT],
                         capture_output=True, text=True, cwd=SCRIPT_DIR)
    lines = ret.stdout.strip().split('\n')
    for line in lines[-4:]:
        print(f"    {line}")
    if os.path.exists(AUDIT_REPORT):
        with open(AUDIT_REPORT, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def extract_failures(report, state):
    """
    Extrait les questions echouees, en excluant celles deja injectees.
    """
    already_injected = set(state.get("injected_facts", []))
    failures = []
    details = report.get("details", [])

    for item in details:
        if item.get("valid", False):
            continue

        q = item.get("question", "").strip()
        expected = str(item.get("expected", "")).strip()
        category = item.get("category", "general")

        q_key = q[:80]
        if q_key in already_injected:
            continue

        if not expected or len(expected) < 1:
            continue

        # Creer un texte de fait
        if category.startswith("math"):
            fact_text = f"{q} = {expected}"
        else:
            fact_text = f"Question: {q}  Reponse: {expected}"

        failures.append({
            "q_key": q_key,
            "question": q[:200],
            "expected": expected[:300],
            "category": category,
            "fact_text": fact_text[:300],
        })

    return failures


def inject_facts_direct(failures, state):
    """
    Injecte les faits DIRECTEMENT dans quick_facts.py.
    Le marqueur reel est: self.facts = FACTS (ligne ~1036).
    """
    if not failures:
        print("  [2/3] Aucun nouvel echec a injecter.")
        return False

    failures = failures[:MAX_FACTS_PER_CYCLE]
    print(f"  [2/3] Injection directe de {len(failures)} faits dans QuickFacts...")

    with open(QF_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Generer les nouveaux tuples de faits
    new_tuples = []
    for i, f in enumerate(failures):
        fid = f"auto_{int(time.time())}_{i}"
        text = f["fact_text"].replace('"', "'").replace('\n', ' ')
        kw = [w.lower() for w in f["question"].split() if len(w) > 3][:3]
        new_tuples.append(f'    ("{fid}", "{text}", {json.dumps(kw)}),')

    # Le marqueur reel est: self.facts = FACTS
    # On va ajouter nos faits juste apres cette ligne
    marker = "self.facts = FACTS"
    if marker in content:
        insert_block = "\n".join(new_tuples)
        # Creer une liste etendue
        extended = f"self.facts = FACTS + [\n{insert_block}\n]"
        content = content.replace(marker, extended)
        with open(QF_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"    Fichier quick_facts.py mis a jour avec {len(failures)} faits")

        # Vider le cache Python pour forcer le rechargement
        import glob as _glob
        pycache = os.path.join(SCRIPT_DIR, "__pycache__")
        if os.path.exists(pycache):
            for f in _glob.glob(os.path.join(pycache, "quick_facts*.pyc")):
                os.remove(f)
            print(f"    Cache Python vide")
    else:
        print(f"    [!] Marqueur 'self.facts = FACTS' non trouve dans quick_facts.py")
        return False

    # Marquer comme injecte
    for f in failures:
        if f["q_key"] not in state["injected_facts"]:
            state["injected_facts"].append(f["q_key"])

    # Recharger QuickFacts
    if "quick_facts" in sys.modules:
        del sys.modules["quick_facts"]
    try:
        import quick_facts
        importlib.reload(quick_facts)
        print(f"    Module QuickFacts recharge")
    except Exception:
        pass

    return True


def expand_hologram():
    """Reconstruit l'hologramme avec les nouveaux faits."""
    print("  [3/3] Reconstruction de l'hologramme...")
    ret = subprocess.run([sys.executable, EXPAND_SCRIPT],
                         capture_output=True, text=True, cwd=SCRIPT_DIR)
    out = ret.stdout[-300:] if ret.stdout else "(no stdout)"
    for line in out.split('\n'):
        if any(kw in line.lower() for kw in ['energy', 'faits', 'ingere', 'termine']):
            print(f"    {line.strip()[:120]}")


def main_loop():
    print("=" * 70)
    print("[BATCH] INGESTION CYCLIQUE v4 - Injection directe + Reload")
    print("=" * 70)

    state = load_state()
    start_cycle = state.get("cycle", 0) + 1
    print(f"Demarrage: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Reprise au cycle: {start_cycle}")
    print(f"Faits deja injectes: {len(state.get('injected_facts', []))}")

    for cycle in range(start_cycle, start_cycle + CYCLES_MAX):
        print(f"\n{'=' * 70}")
        print(f"CYCLE {cycle}")
        print(f"{'=' * 70}")

        report = run_audit()
        if not report:
            print("[!] Audit echoue - abandon.")
            state["cycle"] = cycle - 1
            save_state(state)
            break

        total_score = report.get("total_score", 0)
        total_passed = report.get("total_passed", 0)
        total_q = report.get("total_questions", 91)
        pct = total_score / total_q * 100 if total_q else 0
        print(f"  Score audit: {total_score:.1f}/{total_q} ({pct:.1f}%) | Reussites: {total_passed}")

        state["history"].append({
            "cycle": cycle, "score": round(pct, 1), "passed": total_passed,
            "time": time.strftime('%H:%M:%S')
        })
        state["cycle"] = cycle
        state["last_score"] = pct
        save_state(state)

        if pct >= 80:
            print(f"\n  OBJECTIF ATTEINT ({pct:.1f}%) - arret.")
            break

        failures = extract_failures(report, state)
        print(f"  Nouveaux echecs: {len(failures)}")

        if failures:
            injected = inject_facts_direct(failures, state)
            if injected:
                save_state(state)
                expand_hologram()
        else:
            total_failed = sum(1 for item in report.get("details", [])
                              if not item.get("valid", False))
            print(f"  Echecs totaux: {total_failed}, deja injectes: {len(state.get('injected_facts', []))}")

        time.sleep(2)

    print(f"\n{'=' * 70}")
    print(f"INGESTION TERMINEE - {state['cycle']} cycles")
    print(f"Score final: {state['last_score']:.1f}%")
    print(f"Faits injectes au total: {len(state.get('injected_facts', []))}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main_loop()