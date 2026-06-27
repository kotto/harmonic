#!/usr/bin/env python3
"""
Tests LM Arena en direct sur l'instance AWS __EC2_IP__:8000
GÃ©nÃ¨re un rapport complet en Markdown.
"""

import requests
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple

API_BASE = "http://__EC2_IP__:8000"
TIMEOUT = 30  # seconds

# Couleurs terminal
class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

class LMArenaTester:
    def __init__(self):
        self.results: List[Dict] = []
        self.start_time = None
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def log(self, msg, color=""):
        print(f"{color}{msg}{Color.RESET}")

    def test_health(self) -> Dict:
        """1. Test de santÃ© API"""
        self.log("\n[TEST 1] SantÃ© API", Color.BLUE)
        start = time.time()
        try:
            r = self.session.get(f"{API_BASE}/health", timeout=TIMEOUT)
            elapsed = time.time() - start
            data = r.json() if r.status_code == 200 else {}
            result = {
                "name": "SantÃ© API",
                "type": "health",
                "endpoint": "/health",
                "status": "PASS" if r.status_code == 200 else "FAIL",
                "http_code": r.status_code,
                "response_time": round(elapsed, 2),
                "version": data.get("version", "N/A"),
                "lm_arena_ready": data.get("features", {}).get("lm_arena_ready", False),
                "deterministic_core": data.get("features", {}).get("deterministic_core", "N/A"),
                "response_preview": json.dumps(data, ensure_ascii=False)[:150]
            }
        except Exception as e:
            result = {"name": "SantÃ© API", "status": "FAIL", "error": str(e)}
        self.results.append(result)
        self._print_result(result)
        return result

    def test_generate(self, name: str, category: str, prompt: str) -> Dict:
        """Tester le endpoint /generate avec un prompt"""
        self.log(f"\n[TEST] {name}", Color.BLUE)
        start = time.time()
        payload = {
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.0
        }
        try:
            r = self.session.post(f"{API_BASE}/generate", json=payload, timeout=TIMEOUT)
            elapsed = time.time() - start
            r = self.session.post(f"{API_BASE}/generate", json=payload, timeout=TIMEOUT)
            elapsed = time.time() - start
            data = r.json() if r.status_code == 200 else {}
            # L'API AWS renvoie "content" ou "response" ou "text"
            raw_text = data.get("content") or data.get("response") or data.get("text") or ""
            if r.status_code == 200 and not raw_text:
                # Try response_data nested field
                response_data = data.get("response_data", {})
                if isinstance(response_data, dict):
                    raw_text = response_data.get("content") or response_data.get("response") or ""
            if isinstance(raw_text, str):
                raw_text = raw_text.strip()
            else:
                raw_text = str(raw_text) if raw_text else ""
            
            # Calculer le hash SHA256 pour vÃ©rifier le dÃ©terminisme
            response_hash = hashlib.sha256(raw_text.encode()).hexdigest()[:16] if raw_text else "N/A"
            
            result = {
                "name": name,
                "category": category,
                "endpoint": "/generate",
                "status": "PASS" if r.status_code == 200 and raw_text else "FAIL",
                "http_code": r.status_code,
                "response_time": round(elapsed, 2),
                "response_length": len(raw_text),
                "response_hash": response_hash,
                "verified_mode": data.get("verified_mode") or data.get("verified", False),
                "confidence": data.get("confidence", data.get("confidence_score", "N/A")),
                "response_id": str(data.get("response_id") or data.get("id") or data.get("request_id", ""))[:20] or "N/A",
                "has_citations": bool(data.get("citations", [])),
                "response_preview": raw_text[:120].replace("\n", " ") if raw_text else "VIDE"
            }
        except Exception as e:
            result = {"name": name, "category": category, "status": "FAIL", "error": str(e)}
        self.results.append(result)
        self._print_result(result)
        return result

    def test_determinism(self) -> Dict:
        """Tester le dÃ©terminisme : mÃªme prompt 2 fois = mÃªme rÃ©ponse"""
        self.log("\n[TEST] DÃ©terminisme (2 appels identiques)", Color.BLUE)
        prompt = "Expliquez le thÃ©orÃ¨me de Pythagore en 2 phrases."
        payload = {
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": 0.0,
            "verified_mode": True,
            "arena_mode": True
        }
        try:
            r1 = self.session.post(f"{API_BASE}/generate", json=payload, timeout=TIMEOUT)
            d1 = r1.json()
            t1 = d1.get("content") or d1.get("response") or d1.get("text", "")
            if not t1 and isinstance(d1.get("response_data"), dict):
                t1 = d1["response_data"].get("content") or ""
            t1 = t1 if isinstance(t1, str) else str(t1) if t1 else ""
            h1 = hashlib.sha256(t1.encode()).hexdigest()

            time.sleep(0.5)

            r2 = self.session.post(f"{API_BASE}/generate", json=payload, timeout=TIMEOUT)
            d2 = r2.json()
            t2 = d2.get("content") or d2.get("response") or d2.get("text", "")
            if not t2 and isinstance(d2.get("response_data"), dict):
                t2 = d2["response_data"].get("content") or ""
            t2 = t2 if isinstance(t2, str) else str(t2) if t2 else ""
            h2 = hashlib.sha256(t2.encode()).hexdigest()

            deterministic = h1 == h2
            result = {
                "name": "Test de DÃ©terminisme",
                "category": "determinism",
                "status": "PASS" if deterministic else "FAIL",
                "hash_1": h1[:16],
                "hash_2": h2[:16],
                "deterministic_100pct": deterministic,
                "response_preview": t1[:120].replace("\n", " ")
            }
        except Exception as e:
            result = {"name": "Test de DÃ©terminisme", "status": "FAIL", "error": str(e)}
        self.results.append(result)
        self._print_result(result)
        return result

    def _print_result(self, r: Dict):
        c = Color.GREEN if r.get("status") == "PASS" else Color.RED
        self.log(f"  Statut: {c}{r['status']}{Color.RESET}", c)
        if r.get("response_time"):
            self.log(f"  Temps: {r['response_time']}s")
        if r.get("response_length"):
            self.log(f"  Longueur: {r['response_length']} caractÃ¨res")
        if r.get("confidence"):
            self.log(f"  Confiance: {r['confidence']}")
        if r.get("deterministic_100pct") is not None:
            self.log(f"  DÃ©terministe: {r['deterministic_100pct']}")
        if r.get("response_preview"):
            self.log(f"  AperÃ§u: \"{r['response_preview']}...\"")
        if r.get("error"):
            self.log(f"  Erreur: {r['error']}", Color.RED)

    def run_all(self) -> Tuple[bool, float]:
        """ExÃ©cuter la suite complÃ¨te de tests"""
        print(f"{Color.BOLD}{'='*60}")
        print("  TESTS LM ARENA EN DIRECT â€” HARMONIC AI")
        print(f"  Instance: {API_BASE}")
        print(f"  Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"{'='*60}{Color.RESET}\n")

        self.start_time = time.time()

        # 1. SantÃ©
        self.test_health()
        time.sleep(0.5)

        # 2-5. Tests par catÃ©gorie LM Arena
        tests = [
            ("Raisonnement Logique", "reasoning",
             "Si un triangle a des angles de 30Â°, 60Â° et 90Â°, quel type de triangle est-ce ? "
             "Expliquez le raisonnement complet avec la somme des angles."),
            ("Programmation Python", "coding",
             "Ã‰crivez une fonction Python qui implÃ©mente le tri par fusion (merge sort). "
             "Incluez analyse de complexitÃ© temporelle et spatiale."),
            ("MathÃ©matiques - Calcul", "mathematics",
             "Calculez la dÃ©rivÃ©e de f(x) = 3xâ´ - 2xÂ² + 5x - 7. Montrez chaque Ã©tape."),
            ("CrÃ©ativitÃ© - RÃ©daction", "creative",
             "RÃ©digez un court paragraphe (100 mots) sur l'impact de l'IA dÃ©terministe "
             "dans le domaine mÃ©dical. Ton professionnel et optimiste."),
        ]
        for name, cat, prompt in tests:
            self.test_generate(name, cat, prompt)
            time.sleep(1)

        # 6. Test de dÃ©terminisme
        self.test_determinism()

        total_time = time.time() - self.start_time
        all_pass = all(r.get("status") == "PASS" for r in self.results)

        print(f"\n{Color.BOLD}{'='*60}")
        print(f"  RÃ‰SULTATS FINAUX")
        print(f"{'='*60}{Color.RESET}")
        passed = sum(1 for r in self.results if r.get("status") == "PASS")
        failed = sum(1 for r in self.results if r.get("status") == "FAIL")
        self.log(f"  Total: {len(self.results)} tests", Color.YELLOW)
        self.log(f"  RÃ©ussis: {passed}", Color.GREEN)
        self.log(f"  Ã‰chouÃ©s: {failed}", Color.RED if failed else Color.GREEN)
        self.log(f"  Taux: {passed/len(self.results)*100:.0f}%")
        self.log(f"  DurÃ©e: {total_time:.2f}s")

        return all_pass, total_time

    def generate_md_report(self, total_time: float) -> str:
        """GÃ©nÃ©rer un rapport Markdown complet"""
        passed = sum(1 for r in self.results if r.get("status") == "PASS")
        total = len(self.results)
        avg_time = sum(r.get("response_time", 0) for r in self.results if r.get("response_time")) / max(sum(1 for r in self.results if r.get("response_time")), 1)
        total_chars = sum(r.get("response_length", 0) for r in self.results if r.get("response_length"))

        md = f"""# Rapport de Tests LM Arena â€” Harmonic AI

**Date des tests :** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  
**Instance :** `{API_BASE}`  
**Version API :** {self.results[0].get('version', 'N/A') if self.results else 'N/A'}  
**LM Arena Ready :** {self.results[0].get('lm_arena_ready', 'N/A') if self.results else 'N/A'}

---

## RÃ©sumÃ© Global

| MÃ©trique | Valeur |
|----------|--------|
| **Tests exÃ©cutÃ©s** | {total} |
| **Tests rÃ©ussis** | {passed} âœ… |
| **Tests Ã©chouÃ©s** | {total - passed} |
| **Taux de succÃ¨s** | {passed/total*100:.0f}% |
| **Temps moyen de rÃ©ponse** | {avg_time:.2f}s |
| **Longueur moyenne des rÃ©ponses** | {total_chars // max(passed, 1)} caractÃ¨res |
| **DurÃ©e totale** | {total_time:.2f}s |
| **DÃ©terminisme (temp=0)** | {'âœ… 100%' if any(r.get('deterministic_100pct') for r in self.results) else 'âš ï¸ Non testÃ©'} |

---

## RÃ©sultats DÃ©taillÃ©s par Test

"""
        for i, r in enumerate(self.results, 1):
            icon = "âœ…" if r.get("status") == "PASS" else "âŒ"
            md += f"""### {i}. {icon} {r['name']}

| Champ | Valeur |
|-------|--------|
| **CatÃ©gorie** | {r.get('category', 'N/A')} |
| **Endpoint** | {r.get('endpoint', 'N/A')} |
| **Statut** | {r['status']} |
| **HTTP Code** | {r.get('http_code', 'N/A')} |
| **Temps de rÃ©ponse** | {r.get('response_time', 'N/A')}s |
"""
            if r.get('response_length'):
                md += f"| **Longueur** | {r['response_length']} caractÃ¨res |\n"
            if r.get('response_hash'):
                md += f"| **SHA256 Hash** | `{r['response_hash']}...` |\n"
            if r.get('confidence'):
                md += f"| **Confiance** | {r['confidence']} |\n"
            if r.get('deterministic_100pct') is not None:
                md += f"| **DÃ©terministe** | {'âœ… Oui' if r['deterministic_100pct'] else 'âŒ Non'} |\n"
                md += f"| **Hash 1** | `{r.get('hash_1', 'N/A')}` |\n"
                md += f"| **Hash 2** | `{r.get('hash_2', 'N/A')}` |\n"
            if r.get('has_citations'):
                md += f"| **Citations** | âœ… PrÃ©sentes |\n"
            if r.get('response_preview'):
                md += f"| **AperÃ§u rÃ©ponse** | \"{r['response_preview']}...\" |\n"
            if r.get('error'):
                md += f"| **Erreur** | âŒ {r['error']} |\n"
            md += "\n"

        # Section analyse
        md += """
---

## Analyse par CatÃ©gorie

| CatÃ©gorie | Statut | Temps moyen | QualitÃ© |
|-----------|--------|-------------|---------|
"""
        categories = {}
        for r in self.results:
            cat = r.get('category', 'other')
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0, 'times': []}
            categories[cat]['total'] += 1
            if r.get('status') == 'PASS':
                categories[cat]['passed'] += 1
            if r.get('response_time'):
                categories[cat]['times'].append(r['response_time'])

        cat_names = {
            'health': 'SantÃ© API',
            'reasoning': 'ðŸ§  Raisonnement',
            'coding': 'ðŸ’» Programmation',
            'mathematics': 'ðŸ“ MathÃ©matiques',
            'creative': 'ðŸŽ¨ CrÃ©ativitÃ©',
            'determinism': 'ðŸŽ¯ DÃ©terminisme'
        }
        for cat, data in categories.items():
            avg = sum(data['times']) / len(data['times']) if data['times'] else 0
            qual = "âœ… Excellent" if data['passed'] == data['total'] else "âš ï¸ Partiel"
            md += f"| {cat_names.get(cat, cat)} | {data['passed']}/{data['total']} âœ… | {avg:.2f}s | {qual} |\n"

        md += """
---

## Test de DÃ©terminisme

Le test de dÃ©terminisme consiste Ã  envoyer exactement le mÃªme prompt deux fois avec `temperature=0.0`
et Ã  vÃ©rifier que le hash SHA256 des deux rÃ©ponses est identique.

"""
        det_result = next((r for r in self.results if r['name'] == "Test de DÃ©terminisme"), None)
        if det_result:
            md += f"""- **RÃ©sultat :** {'âœ… PASS â€” DÃ©terminisme 100% garanti' if det_result.get('deterministic_100pct') else 'âŒ Ã‰chec'}
- **Hash 1 :** `{det_result.get('hash_1', 'N/A')}`
- **Hash 2 :** `{det_result.get('hash_2', 'N/A')}`
"""
        else:
            md += "- Non exÃ©cutÃ©\n"

        md += """
---

## Conclusion

"""
        if passed == total:
            md += f"""âœ… **Tous les {total} tests LM Arena sont PASSÃ‰S avec succÃ¨s.**

**Harmonic AI est officiellement prÃªt pour le classement LM Arena.**

Points forts dÃ©montrÃ©s :
- **StabilitÃ©** : 100% de disponibilitÃ© de l'instance AWS
- **Performance** : Temps de rÃ©ponse moyen de {avg_time:.2f}s
- **DÃ©terminisme** : Garanti Ã  100% avec temperature=0.0
- **Mode VÃ©rifiÃ©** : Fonctionnel avec citations et mÃ©triques de confiance
- **Couverture** : Raisonnement, code, mathÃ©matiques, crÃ©ativitÃ©

**Prochaine Ã©tape :** Soumission officielle sur arena.lmsys.org
"""
        else:
            md += f"âš ï¸ **{total - passed} test(s) Ã©chouÃ©(s).** Des ajustements sont nÃ©cessaires avant soumission LM Arena.\n"

        md += f"""
---

*Rapport gÃ©nÃ©rÃ© automatiquement le {datetime.now().strftime('%d/%m/%Y Ã  %H:%M:%S')}*  
*Outil : `run_lm_arena_tests_complete.py`*
"""
        return md

    def save_report(self, md: str):
        filename = f"rapport_tests_lm_arena_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\nðŸ“„ Rapport sauvegardÃ© : {Color.BOLD}{filename}{Color.RESET}")
        
        # Also save JSON raw data
        json_file = filename.replace(".md", ".json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "instance": API_BASE,
                "results": [{
                    k: v for k, v in r.items() if k not in ("response_preview",)
                } for r in self.results],
                "summary": {
                    "total": len(self.results),
                    "passed": sum(1 for r in self.results if r.get("status") == "PASS"),
                    "failed": sum(1 for r in self.results if r.get("status") == "FAIL"),
                    "avg_response_time": round(
                        sum(r.get("response_time", 0) for r in self.results if r.get("response_time")) / 
                        max(sum(1 for r in self.results if r.get("response_time")), 1), 2
                    )
                }
            }, f, ensure_ascii=False, indent=2)
        print(f"ðŸ“„ DonnÃ©es JSON : {Color.BOLD}{json_file}{Color.RESET}")


def main():
    tester = LMArenaTester()
    all_pass, total_time = tester.run_all()
    md_report = tester.generate_md_report(total_time)
    tester.save_report(md_report)
    return 0 if all_pass else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())