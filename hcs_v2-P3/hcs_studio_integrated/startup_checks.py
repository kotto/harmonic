#!/usr/bin/env python3
"""
HCS Studio - Validation des modules au démarrage
A importer au tout début du serveur: from startup_checks import verify_modules

Leve RuntimeError si un module critique est absent, 
affiche des avertissements pour les modules optionnels.
"""
import sys
import os
import importlib

# --- Configuration ---
CORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '')

# Modules CRITIQUES : absence = crash serveur impossible
REQUIRED_MODULES = {
    "core.hybrid_compressor":     "HybridCompressor",
    "core.k_factor_engine":       "KFactorEngine",
    "core.webp_optimizer":        "WebPOptimizer",
    "core.quantum_harmonic_compressor": "QuantumHarmonicCompressor",
}

# Modules OPTIONNELS : absence = dégradation silencieuse documentée
OPTIONAL_MODULES = {
    "core.harmonic_upscaler":     "HarmonicUpscalerAPI",
    "cv2":                        None,  # OpenCV
    "PIL":                        None,  # Pillow
    "numpy":                      None,  # NumPy
}


def _fmt(ok: bool) -> str:
    return "[OK]" if ok else "[KO]"


def verify_modules(strict: bool = True) -> dict:
    """
    Vérifie la disponibilité de tous les modules HCS.

    Args:
        strict: Si True, leve RuntimeError si un module requis est absent.
                Si False, retourne simplement le rapport.

    Returns:
        dict avec clés 'required', 'optional', 'all_ok'
    """
    # Assure que le core est dans sys.path
    if CORE_PATH not in sys.path:
        sys.path.insert(0, CORE_PATH)

    report = {"required": {}, "optional": {}, "all_ok": True, "errors": []}

    # --- Vérification modules requis ---
    for module_path, class_name in REQUIRED_MODULES.items():
        ok = False
        error = None
        try:
            mod = importlib.import_module(module_path)
            if class_name:
                if not hasattr(mod, class_name):
                    raise ImportError(f"Classe {class_name!r} absente dans {module_path}")
            ok = True
        except Exception as exc:
            error = str(exc)
            report["all_ok"] = False
            report["errors"].append(f"[REQUIS] {module_path}: {error}")

        report["required"][module_path] = {
            "ok": ok,
            "class": class_name,
            "error": error,
        }
        status = _fmt(ok)
        label = f"{module_path}::{class_name}" if class_name else module_path
        print(f"  {status} [REQUIS]  {label}" + (f"  -> {error}" if error else ""))

    # --- Vérification modules optionnels ---
    for module_path, class_name in OPTIONAL_MODULES.items():
        ok = False
        error = None
        try:
            mod = importlib.import_module(module_path)
            if class_name and not hasattr(mod, class_name):
                raise ImportError(f"Classe {class_name!r} absente")
            ok = True
        except Exception as exc:
            error = str(exc)

        report["optional"][module_path] = {
            "ok": ok,
            "class": class_name,
            "error": error,
        }
        status = _fmt(ok)
        label = f"{module_path}::{class_name}" if class_name else module_path
        print(f"  {status} [OPT]     {label}" + (f"  -> {error}" if error else ""))

    # --- Lever l'erreur si requis et strict ---
    if strict and not report["all_ok"]:
        raise RuntimeError(
            "HCS Studio: modules requis manquants:\n" +
            "\n".join(f"  - {e}" for e in report["errors"])
        )

    return report


def print_startup_banner():
    """Affiche la banniere de demarrage avec bilan modules."""
    print("=" * 60)
    print("  HCS Studio server - Verification modules")
    print("=" * 60)
    result = verify_modules(strict=True)
    n_req = len(result["required"])
    n_opt = len(result["optional"])
    ok_req = sum(1 for v in result["required"].values() if v["ok"])
    ok_opt = sum(1 for v in result["optional"].values() if v["ok"])
    print(f"  Requis  : {ok_req}/{n_req}")
    print(f"  Optionnels: {ok_opt}/{n_opt}")
    all_ok = result["all_ok"]
    print(f"  Statut : {'[OK] Pret' if all_ok else '[WARN] Degrade - verifiez les erreurs ci-dessus'}")
    print("=" * 60)
    return result


if __name__ == "__main__":
    # Execution directe = diagnostic
    print_startup_banner()
