"""
🌊 Wave Debugger — Pipeline Ondulatoire de Résolution de Bugs
===============================================================

Implémente la méthodologie en 4 étapes pour le diagnostic et la
résolution de bugs de code par le langage des ondes.

Usage :
    python wave_debugger.py                        # mode interactif
    python wave_debugger.py --bug "NullPointer"    # diagnostic rapide
    python wave_debugger.py --report bug.json      # charger un rapport existant
    python wave_debugger.py --template             # générer un template vide

Auteur : Équipe Harmonic AI
Date   : 20 Juillet 2026
"""

import sys, os, json, time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES DE DIAGNOSTIC
# ═══════════════════════════════════════════════════════════════════════════════

class InterferenceType(Enum):
    """Types d'interférence destructive."""
    OPPOSITION_PHASE    = "opposition_phase"      # π — annulation totale
    DESACCORD_FREQUENCE = "desaccord_frequence"   # Δω — battements, intermittent
    SATURATION          = "saturation"            # A > max — crash, overflow
    RESONANCE_FORCEE    = "resonance_forcee"      # ω ≠ ω_propre — forcé, instable
    ABSENCE_FREQUENCE   = "absence_frequence"     # ω ∉ spectre — null, 404
    COLLISION_PHASE     = "collision_phase"       # conflit d'accès — race condition
    DEPHASAGE_TEMPOREL  = "dephasage_temporel"    # stale reference, cache invalide
    ONDE_FANTOME        = "onde_fantome"          # memory leak, zombie
    INTERFERENCE_MULTI  = "interference_multi"    # N grand — contention, perf
    RESONANCE_PARASITE  = "resonance_parasite"    # edge case, input malveillant


class Strategy(Enum):
    """Stratégies d'onde correctrice."""
    OPPOSITION_PHASE = "A — Opposition de phase (annulation active)"
    SYNCHRONISATION  = "B — Synchronisation (réalignement)"
    FILTRAGE         = "C — Filtrage (élimination sélective)"
    DISSIPATION      = "D — Dissipation (répartition)"
    INJECTION        = "E — Injection (complétion)"
    RESTAURATION     = "F — Restauration (retour à ω_propre)"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE DE DIAGNOSTIC — Symptôme → Interférence → Stratégie
# ═══════════════════════════════════════════════════════════════════════════════

DIAGNOSTIC_TABLE = [
    # (mots-clés symptôme, interférence, stratégie, description)
    (["null", "none", "undefined", "nil", "nullpointer", "nullreference", "optional"],
     InterferenceType.ABSENCE_FREQUENCE, Strategy.INJECTION,
     "L'onde sonde frappe un nœud (amplitude nulle). La fréquence cherchée n'existe pas dans l'hologramme.",
     "Ajouter une garde : if (x == null) return default; ou utiliser Optional/Option type."),

    (["crash", "exception", "error", "panic", "fatal", "segfault", "unhandled"],
     InterferenceType.SATURATION, Strategy.DISSIPATION,
     "L'amplitude a dépassé le seuil de linéarité. L'onde a saturé le système.",
     "Ajouter try/catch, validation des entrées, ou limiter l'amplitude (rate limiting, timeout)."),

    (["race", "concurrent", "deadlock", "thread", "async", "mutex", "lock", "atomic"],
     InterferenceType.COLLISION_PHASE, Strategy.SYNCHRONISATION,
     "Deux ondes arrivent en même temps sur la même ressource. Leur interférence dépend de l'ordre d'arrivée.",
     "Ajouter lock/mutex/semaphore, file d'attente, ou rendre l'opération atomique."),

    (["loop", "infinite", "hang", "freeze", "block", "timeout", "eternal"],
     InterferenceType.SATURATION, Strategy.DISSIPATION,
     "L'onde est piégée dans une cavité résonante. Pas de condition de dissipation.",
     "Vérifier la condition de sortie, ajouter un compteur d'itérations max, ou un timeout."),

    (["leak", "memory", "oom", "out of memory", "grow", "accumulate", "zombie"],
     InterferenceType.ONDE_FANTOME, Strategy.INJECTION,
     "Une onde persiste après sa durée de vie utile. L'amplitude fantôme s'accumule.",
     "Ajouter free()/close()/dispose(), utiliser try-with-resources, ou RAII."),

    (["stale", "cache", "outdated", "old", "refresh", "invalidate", "reload"],
     InterferenceType.DEPHASAGE_TEMPOREL, Strategy.SYNCHRONISATION,
     "Une onde est figée dans le passé (t₀) tandis que l'autre évolue (t). Déphasage croissant.",
     "Capturer l'état au moment de l'usage (pas au démarrage). Invalider le cache. Refresh."),

    (["wrong", "incorrect", "bad", "invalid", "unexpected", "bug", "off by one"],
     InterferenceType.DESACCORD_FREQUENCE, Strategy.SYNCHRONISATION,
     "L'onde observée et l'onde attendue ont des fréquences proches mais déphasées.",
     "Comparer ω_observed et ω_expected pas à pas. Corriger la formule ou la logique."),

    (["regression", "broke", "was working", "used to", "before", "after update"],
     InterferenceType.RESONANCE_FORCEE, Strategy.RESTAURATION,
     "Une fréquence a été remplacée par une autre qui ne résonne pas avec les dépendances.",
     "Revenir à l'ancienne version (revert) ou mettre à jour les dépendances pour la nouvelle fréquence."),

    (["slow", "performance", "lag", "latency", "bottleneck", "overload", "cpu"],
     InterferenceType.INTERFERENCE_MULTI, Strategy.DISSIPATION,
     "Trop d'ondes interfèrent simultanément. L'information est noyée dans le bruit.",
     "Index, cache, pagination, lazy loading, réduire O(n²) → O(n log n), load balancing."),

    (["intermittent", "sometimes", "random", "flaky", "non deterministic", "heisenbug"],
     InterferenceType.DESACCORD_FREQUENCE, Strategy.FILTRAGE,
     "Le bug dépend d'une phase externe (timestamp, seed, état réseau). Parfois Δω ≈ 0, parfois non.",
     "Identifier la condition de phase déclenchante. Stabiliser ou logger l'état au moment du bug."),

    (["validation", "input", "sanitize", "escape", "injection", "xss", "malicious"],
     InterferenceType.RESONANCE_PARASITE, Strategy.FILTRAGE,
     "Une fréquence parasite (input malveillant) entre en résonance avec une vulnérabilité.",
     "Valider, sanitizer, échapper les entrées. Never trust user input."),

    (["config", "environment", "env", "setting", "variable", "dotenv"],
     InterferenceType.ABSENCE_FREQUENCE, Strategy.INJECTION,
     "La fréquence de configuration cherchée n'existe pas dans l'hologramme de l'environnement.",
     "Définir la variable d'environnement manquante. Ajouter une valeur par défaut. Documenter."),
]


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Wave:
    """Une entité du système représentée comme une onde."""
    name: str
    frequency: str = ""      # nature, identité, signature
    amplitude: str = ""      # force, intensité, importance
    phase: str = ""          # position dans le cycle, timing
    harmonics: List[str] = field(default_factory=list)  # dépendances, interactions


@dataclass
class BugReport:
    """Rapport complet de diagnostic ondulatoire."""
    # Méta
    title: str = ""
    date: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M"))
    language: str = ""
    file_path: str = ""
    
    # Étape 1 — Traduction
    waves: List[Wave] = field(default_factory=list)
    wave_expected: str = ""
    wave_observed: str = ""
    wave_trigger: str = ""
    
    # Étape 2 — Diagnostic
    symptom_description: str = ""
    interference_type: str = ""
    interference_justification: str = ""
    location: str = ""
    
    # Étape 3 — Prescription
    strategy: str = ""
    action: str = ""
    code_before: str = ""
    code_after: str = ""
    
    # Étape 4 — Vérification
    criteria: Dict[str, bool] = field(default_factory=lambda: {
        "symptom_disappeared": False,
        "no_regression": False,
        "autonomous": False,
        "harmonics_intact": False,
        "test_written": False,
    })
    healing_score: int = 0
    notes: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE DIAGNOSTIC
# ═══════════════════════════════════════════════════════════════════════════════

def diagnose(symptom: str) -> List[dict]:
    """
    Analyse un symptôme et retourne les diagnostics possibles,
    classés par pertinence.
    """
    symptom_lower = symptom.lower()
    results = []
    
    for keywords, interference, strategy, explanation, action in DIAGNOSTIC_TABLE:
        score = sum(1 for kw in keywords if kw in symptom_lower)
        if score > 0:
            results.append({
                "score": score,
                "interference": interference.value,
                "interference_label": interference.name.replace("_", " ").title(),
                "strategy": strategy.value,
                "explanation": explanation,
                "action": action,
            })
    
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def generate_report(report: BugReport) -> str:
    """Génère un rapport Markdown complet."""
    
    waves_md = ""
    for i, w in enumerate(report.waves, 1):
        waves_md += f"""### Onde n°{i} : {w.name}
- **Fréquence** (nature) : {w.frequency}
- **Amplitude** (force) : {w.amplitude}
- **Phase** (timing) : {w.phase}
- **Harmoniques** (liens) : {', '.join(w.harmonics) if w.harmonics else 'aucune'}

"""

    criteria_md = "\n".join(
        f"- [{ '✅' if v else '❌' }] **{k.replace('_', ' ').title()}**"
        for k, v in report.criteria.items()
    )
    
    score_bar = "█" * report.healing_score + "░" * (5 - report.healing_score)
    
    return f"""# 🌊 Rapport de Diagnostic Ondulatoire

**Bug :** {report.title}
**Date :** {report.date}
**Langage :** {report.language or 'N/A'}
**Fichier :** {report.file_path or 'N/A'}

---

## ÉTAPE 1 — TRADUCTION : Les ondes en jeu

### Cartographie des fréquences

{waves_md}

### Attendu vs Observé
| | Fréquence |
|---|---|
| **ω_expected** | {report.wave_expected or '—'} |
| **ω_observed**  | {report.wave_observed or '—'} |
| **ω_trigger**   | {report.wave_trigger or '—'} |

---

## ÉTAPE 2 — DIAGNOSTIC : L'interférence destructive

### Symptôme
{report.symptom_description or '—'}

### Type d'interférence
**{report.interference_type or '—'}**

### Justification
{report.interference_justification or '—'}

### Localisation
{report.location or '—'}

---

## ÉTAPE 3 — PRESCRIPTION : L'onde correctrice

### Stratégie
**{report.strategy or '—'}**

### Action concrète
{report.action or '—'}

### Code
```{report.language or 'python'}
# AVANT (buggé)
{report.code_before or '# ...'}

# APRÈS (corrigé)
{report.code_after or '# ...'}
```

---

## ÉTAPE 4 — VÉRIFICATION : L'harmonie restaurée

{criteria_md}

### Score de guérison
**{report.healing_score}/5**  {score_bar}

### Notes
{report.notes or '—'}

---

*Rapport généré par Wave Debugger — Méthodologie Ondulatoire Harmonic AI*
"""


# ═══════════════════════════════════════════════════════════════════════════════
# MODE INTERACTIF
# ═══════════════════════════════════════════════════════════════════════════════

def interactive_mode():
    """Pipeline interactif en 4 étapes."""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           🌊 WAVE DEBUGGER — Diagnostic Ondulatoire          ║
║           Pipeline interactif de résolution de bugs          ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    report = BugReport()
    
    # ── Méta ──
    report.title = input("📛 Titre du bug : ").strip() or "Bug sans nom"
    report.language = input("💻 Langage (python, js, rust, ...) : ").strip()
    report.file_path = input("📁 Fichier concerné : ").strip()
    print()
    
    # ════════════════════════════════════════════════════════════════
    # ÉTAPE 1 — TRADUIRE
    # ════════════════════════════════════════════════════════════════
    print("━" * 60)
    print("🎯 ÉTAPE 1 — TRADUIRE : Identifier les fréquences en jeu")
    print("━" * 60)
    
    report.wave_expected = input("  ω_expected (comportement attendu) : ").strip()
    report.wave_observed  = input("  ω_observed  (comportement buggé)  : ").strip()
    report.wave_trigger   = input("  ω_trigger   (déclencheur)         : ").strip()
    
    print("\n  📡 Entités impliquées (laisser vide pour terminer) :")
    i = 1
    while True:
        name = input(f"\n  Entité #{i} — nom : ").strip()
        if not name:
            break
        w = Wave(name=name)
        w.frequency  = input(f"    Fréquence (nature/type)  : ").strip()
        w.amplitude  = input(f"    Amplitude (force/poids)  : ").strip()
        w.phase      = input(f"    Phase (timing/ordre)     : ").strip()
        harmonics    = input(f"    Harmoniques (liens, séparés par ,) : ").strip()
        w.harmonics  = [h.strip() for h in harmonics.split(",") if h.strip()]
        report.waves.append(w)
        i += 1
    
    print()
    
    # ════════════════════════════════════════════════════════════════
    # ÉTAPE 2 — DIAGNOSTIQUER
    # ════════════════════════════════════════════════════════════════
    print("━" * 60)
    print("🔬 ÉTAPE 2 — DIAGNOSTIQUER : Localiser l'interférence destructive")
    print("━" * 60)
    
    symptom = input("\n  🔍 Décrivez le symptôme en quelques mots-clés :\n     ").strip()
    report.symptom_description = symptom
    
    # Auto-diagnostic
    results = diagnose(symptom)
    
    if results:
        print(f"\n  📊 Diagnostics suggérés ({len(results)} correspondances) :\n")
        for j, r in enumerate(results[:5], 1):
            print(f"  {j}. [{r['score']} match] {r['interference_label']}")
            print(f"     {r['explanation'][:100]}...")
            print(f"     💡 {r['action'][:100]}...")
            print()
        
        choice = input(f"  ✅ Choix (1-{min(5, len(results))}, ou 'autre') : ").strip()
        if choice.isdigit() and 1 <= int(choice) <= min(5, len(results)):
            r = results[int(choice) - 1]
            report.interference_type = r['interference_label']
            report.interference_justification = r['explanation']
            report.strategy = r['strategy']
            report.action = r['action']
        else:
            report.interference_type = input("  Type d'interférence : ").strip()
            report.interference_justification = input("  Justification : ").strip()
    else:
        print("\n  ⚠️ Aucun diagnostic automatique trouvé.")
        print("  Consultez la table de diagnostic manuellement.\n")
        report.interference_type = input("  Type d'interférence : ").strip()
        report.interference_justification = input("  Justification : ").strip()
    
    report.location = input("\n  📍 Localisation précise (fichier:ligne) : ").strip()
    print()
    
    # ════════════════════════════════════════════════════════════════
    # ÉTAPE 3 — PRESCRIRE
    # ════════════════════════════════════════════════════════════════
    print("━" * 60)
    print("💊 ÉTAPE 3 — PRESCRIRE : Déterminer l'onde correctrice")
    print("━" * 60)
    
    if not report.strategy:
        print("\n  Stratégies disponibles :")
        for s in Strategy:
            print(f"    {s.value}")
        report.strategy = input("\n  🧭 Stratégie choisie : ").strip()
    else:
        print(f"\n  🧭 Stratégie suggérée : {report.strategy}")
        confirm = input("  Confirmer ? (O/n) : ").strip().lower()
        if confirm == 'n':
            report.strategy = input("  Nouvelle stratégie : ").strip()
    
    if not report.action:
        report.action = input("\n  ⚡ Action concrète (en une phrase) : ").strip()
    else:
        print(f"\n  ⚡ Action suggérée : {report.action}")
        confirm = input("  Confirmer ? (O/n) : ").strip().lower()
        if confirm == 'n':
            report.action = input("  Nouvelle action : ").strip()
    
    print("\n  📝 Code (optionnel — laisser vide si non applicable) :")
    report.code_before = input("    AVANT (buggé) : ").strip()
    report.code_after  = input("    APRÈS (corrigé) : ").strip()
    print()
    
    # ════════════════════════════════════════════════════════════════
    # ÉTAPE 4 — VÉRIFIER
    # ════════════════════════════════════════════════════════════════
    print("━" * 60)
    print("✅ ÉTAPE 4 — VÉRIFIER : Mesurer l'harmonie restaurée")
    print("━" * 60)
    
    criteria_labels = {
        "symptom_disappeared": "Le symptôme a disparu",
        "no_regression": "Pas de régression (tests verts)",
        "autonomous": "Solution autonome (pas un patch temporaire)",
        "harmonics_intact": "Harmoniques intactes (fonctions voisines OK)",
        "test_written": "Test automatisé écrit (immunité acquise)",
    }
    
    for key, label in criteria_labels.items():
        ans = input(f"  {label} ? (O/n) : ").strip().lower()
        report.criteria[key] = ans != 'n'
    
    report.healing_score = sum(1 for v in report.criteria.values() if v)
    
    score_emojis = ["💀", "🩹", "🏥", "💪", "🌟", "👑"]
    print(f"\n  Score de guérison : {report.healing_score}/5  {score_emojis[report.healing_score]}")
    
    report.notes = input("\n  📝 Notes supplémentaires : ").strip()
    print()
    
    # ════════════════════════════════════════════════════════════════
    # SAUVEGARDE
    # ════════════════════════════════════════════════════════════════
    output_dir = Path(__file__).resolve().parent / "wave_reports"
    output_dir.mkdir(exist_ok=True)
    
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in report.title)[:50]
    json_path = output_dir / f"{safe_name}.json"
    md_path = output_dir / f"{safe_name}.md"
    
    # JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)
    
    # Markdown
    md_content = generate_report(report)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"📄 Rapport sauvegardé :")
    print(f"   JSON : {json_path}")
    print(f"   MD   : {md_path}")
    print(f"\n{md_content}")
    
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# MODE RAPIDE (--bug)
# ═══════════════════════════════════════════════════════════════════════════════

def quick_diagnose(symptom: str):
    """Diagnostic rapide depuis la ligne de commande."""
    results = diagnose(symptom)
    
    if not results:
        print("⚠️ Aucun diagnostic automatique trouvé.")
        print("Consultez docs/METHODOLOGIE_RESOLUTION_ONDULATOIRE.md")
        return
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║              🌊 DIAGNOSTIC ONDULATOIRE RAPIDE                ║
╠═══════════════════════════════════════════════════════════════╣
║  Symptôme : {symptom[:45]:<45} ║
╠═══════════════════════════════════════════════════════════════╣
""")
    
    for j, r in enumerate(results[:5], 1):
        bar = "█" * r['score'] + "░" * (5 - r['score'])
        print(f"""║  {j}. {r['interference_label']:<35} [{bar}] ║
║     {r['explanation'][:55]:<55} ║
║     💡 {r['action'][:55]:<55} ║
║                                                               ║""")
    
    print(f"""╚═══════════════════════════════════════════════════════════════╝

👉 Pour un diagnostic complet : python wave_debugger.py
""")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE TEMPLATE (--template)
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATE = """# 🌊 Rapport de Diagnostic Ondulatoire — [TITRE DU BUG]

**Date :** {date}
**Langage :** 
**Fichier :** 

---

## ÉTAPE 1 — TRADUIRE : Les ondes en jeu

### Cartographie des fréquences

| Entité | Fréquence (nature) | Amplitude (force) | Phase (timing) | Harmoniques (liens) |
|--------|-------------------|-------------------|----------------|---------------------|
| | | | | |
| | | | | |

### Attendu vs Observé
| | Fréquence |
|---|---|
| **ω_expected** | |
| **ω_observed**  | |
| **ω_trigger**   | |

---

## ÉTAPE 2 — DIAGNOSTIC : L'interférence destructive

### Symptôme


### Type d'interférence
(Cocher)
- [ ] Opposition de phase     - [ ] Désaccord de fréquence
- [ ] Saturation d'amplitude  - [ ] Résonance forcée
- [ ] Absence de fréquence    - [ ] Collision de phase
- [ ] Déphasage temporel      - [ ] Onde fantôme
- [ ] Interférence multiple   - [ ] Résonance parasite

### Justification


### Localisation


---

## ÉTAPE 3 — PRESCRIPTION : L'onde correctrice

### Stratégie
(Cocher)
- [ ] A — Opposition de phase    - [ ] B — Synchronisation
- [ ] C — Filtrage               - [ ] D — Dissipation
- [ ] E — Injection              - [ ] F — Restauration

### Action concrète


### Code
```python
# AVANT (buggé)


# APRÈS (corrigé)


```

---

## ÉTAPE 4 — VÉRIFIER : L'harmonie restaurée

- [ ] **Symptôme disparu** — le comportement buggé ne se produit plus
- [ ] **Pas de régression** — les tests existants passent toujours
- [ ] **Solution autonome** — pas un patch temporaire, pas de béquille
- [ ] **Harmoniques intactes** — fonctions voisines, effets de bord OK
- [ ] **Test automatisé écrit** — immunité acquise contre ce bug

### Score de guérison
**/5**

### Notes


---

*Rapport généré le {date} — Méthodologie Ondulatoire Harmonic AI*
"""


# ═══════════════════════════════════════════════════════════════════════════════
# API IMPORTABLE — Pour intégration dans KA Phone
# ═══════════════════════════════════════════════════════════════════════════════

def diagnose_for_api(symptom: str, language: str = "", code_snippet: str = "") -> dict:
    """
    Diagnostic importable par le serveur KA Phone.
    Retourne un dict structuré pour l'API /api/debug.
    """
    results = diagnose(symptom)
    
    if not results:
        return {
            "diagnosis": {
                "interference": "inconnue",
                "explanation": "Aucun diagnostic automatique trouvé. Essayez de décrire le symptôme avec plus de mots-clés techniques (null, crash, race, leak, slow, stale, etc.)",
                "strategy": "Consultez docs/METHODOLOGIE_RESOLUTION_ONDULATOIRE.md",
                "action": "Décrivez le bug plus précisément.",
                "confidence": 0.0
            },
            "all_matches": [],
            "symptom": symptom,
            "language": language,
            "methodology": "Les 4 étapes : 1) Traduire en ondes  2) Diagnostiquer l'interférence  3) Prescrire l'onde correctrice  4) Vérifier l'harmonie restaurée"
        }
    
    primary = results[0]
    
    return {
        "diagnosis": {
            "interference": primary["interference_label"],
            "interference_type": primary["interference"],
            "explanation": primary["explanation"],
            "strategy": primary["strategy"],
            "action": primary["action"],
            "confidence": min(1.0, primary["score"] / 5.0)
        },
        "all_matches": [
            {
                "interference": r["interference_label"],
                "explanation": r["explanation"][:120] + "...",
                "action": r["action"][:120] + "...",
                "score": r["score"]
            }
            for r in results[:5]
        ],
        "symptom": symptom,
        "language": language,
        "code_snippet": code_snippet[:500] if code_snippet else "",
        "methodology": {
            "step_1": "TRADUIRE — Identifier les fréquences en jeu (ω_expected, ω_observed, ω_trigger)",
            "step_2": "DIAGNOSTIQUER — Localiser l'interférence destructive",
            "step_3": "PRESCRIRE — Déterminer l'onde correctrice (Opposition/Synchro/Filtrage/Dissipation/Injection/Restauration)",
            "step_4": "VÉRIFIER — 5 critères : symptôme disparu, pas de régression, autonome, harmoniques intactes, immunité"
        },
        "wave_pipeline": {
            "problem": f"Interférence destructive : {primary['interference_label']}",
            "solution": f"Onde correctrice : {primary['strategy']}",
            "healing": "Interférence constructive restaurée → 5 critères vérifiés"
        }
    }


def format_debug_response(api_result: dict) -> str:
    """
    Formate le résultat de diagnose_for_api() en texte Markdown
    pour affichage dans le chat KA Phone.
    """
    d = api_result.get("diagnosis", {})
    matches = api_result.get("all_matches", [])
    
    confidence_bar = "█" * int(d.get("confidence", 0) * 5) + "░" * (5 - int(d.get("confidence", 0) * 5))
    
    lines = [
        f"## 🌊 Diagnostic Ondulatoire",
        f"",
        f"**Symptôme :** {api_result.get('symptom', '')[:100]}",
        f"",
        f"### 🎯 ÉTAPE 1 & 2 — Diagnostic",
        f"",
        f"| Propriété | Valeur |",
        f"|-----------|--------|",
        f"| **Interférence** | **{d.get('interference', '')}** |",
        f"| **Confiance** | {confidence_bar} ({int(d.get('confidence', 0) * 100)}%) |",
        f"",
        f"**Explication :** {d.get('explanation', '')}",
        f"",
        f"### 💊 ÉTAPE 3 — Onde correctrice",
        f"",
        f"**Stratégie :** {d.get('strategy', '')}",
        f"",
        f"**Action concrète :**",
        f"> {d.get('action', '')}",
        f"",
    ]
    
    if matches and len(matches) > 1:
        lines.append("### 📊 Diagnostics alternatifs")
        lines.append("")
        lines.append("| # | Interférence | Score | Action rapide |")
        lines.append("|---|-------------|-------|---------------|")
        for i, m in enumerate(matches[1:], 2):
            lines.append(f"| {i} | {m['interference']} | {m['score']}/5 | {m['action'][:60]}... |")
        lines.append("")
    
    lines.extend([
        f"### ✅ ÉTAPE 4 — Vérification",
        f"",
        f"1. Le symptôme a disparu ?",
        f"2. Pas de régression ?",
        f"3. Solution autonome (pas un patch) ?",
        f"4. Harmoniques intactes ?",
        f"5. Test écrit (immunité) ?",
        f"",
        f"---",
        f"*Diagnostic par Wave Debugger — Méthodologie Ondulatoire Harmonic AI*"
    ])
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN (CLI)
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    
    if "--bug" in sys.argv:
        idx = sys.argv.index("--bug")
        symptom = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        if symptom:
            quick_diagnose(symptom)
        else:
            print("Usage: python wave_debugger.py --bug \"description du symptôme\"")
        return
    
    if "--template" in sys.argv:
        output = "wave_bug_report_template.md"
        with open(output, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE.format(date=time.strftime("%Y-%m-%d %H:%M")))
        print(f"📄 Template créé : {output}")
        return
    
    if "--report" in sys.argv:
        idx = sys.argv.index("--report")
        path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            report = BugReport(**data)
            md = generate_report(report)
            print(md)
        else:
            print("Usage: python wave_debugger.py --report bug.json")
        return
    
    # Mode interactif par défaut
    interactive_mode()


if __name__ == "__main__":
    main()
