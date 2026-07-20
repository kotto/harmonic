"""
Pont d'import — ka_enterprise → engine (moteur commun).
Ajoute engine/ au path pour importer le moteur harmonique.
"""
import sys
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))
