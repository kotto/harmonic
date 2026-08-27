"""
⚡ test_fasttext_classifier.py — Tests du classifieur léger (FastText/sklearn)
================================================================================
Vérifie :
  - L'entraînement automatique depuis les templates
  - La généralisation aux reformulations hors patterns
  - La latence d'inférence (CPU, offline)
  - La persistance

Lancement : python -m pytest ka_server/tests/test_fasttext_classifier.py -q
"""

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'services'))


from ka_server.services.fasttext_classifier import (  # noqa: E402
    FastTextClassifier,
    generate_training_data,
)


@pytest.fixture(scope="module")
def classifier():
    """Entraîne un classifieur sur les données synthétiques (rapide)."""
    ft = FastTextClassifier()
    data = generate_training_data()
    ft.train(data)
    assert ft.is_ready
    return ft


def test_training_data_generated():
    """Les données synthétiques couvrent les 10 intentions."""
    data = generate_training_data()
    intents = set(label for _, label in data)
    assert len(intents) == 10
    assert 'identity_question' in intents
    assert 'factual_question' in intents
    assert 'storage_action' in intents
    # Au moins 1500 exemples
    assert len(data) >= 1500


def test_storage_reformulations_generalize(classifier):
    """Les reformulations de compression sont classées même hors patterns."""
    tests = [
        "j'aimerais que tu examines l'état de mon espace de stockage",
        "dis-moi ce qui prend toute la place sur mon téléphone",
        "peux-tu checker mon stockage stp",
        "fais le ménage dans mon téléphone",
    ]
    for text in tests:
        intent, conf = classifier.predict(text)
        assert intent == 'storage_action', f"'{text}' → {intent}"


def test_identity_questions(classifier):
    """Les questions d'identité sont bien classées."""
    for text in ["qui es-tu", "tu peux me dire qui tu es", "c'est quoi KA"]:
        intent, conf = classifier.predict(text)
        assert intent == 'identity_question', f"'{text}' → {intent}"


def test_factual_questions(classifier):
    """Les questions factuelles sont bien classées."""
    for text in ["c'est quoi un hologramme", "explique-moi ce qu'est un trou noir",
                 "que signifie la gravité"]:
        intent, conf = classifier.predict(text)
        assert intent == 'factual_question', f"'{text}' → {intent}"


def test_arithmetic(classifier):
    """Les calculs sont reconnus."""
    intent, conf = classifier.predict("combien ça fait 42 fois 7")
    assert intent == 'arithmetic'


def test_inference_latency(classifier):
    """L'inférence est < 5 ms (CPU, offline)."""
    # Warmup
    classifier.predict("peux-tu compresser mon téléphone")
    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        classifier.predict("peux-tu compresser mon téléphone")
        latencies.append((time.perf_counter() - t0) * 1000)
    avg = sum(latencies) / len(latencies)
    assert avg < 5.0, f"latence moyenne {avg:.2f} ms"


def test_predict_top_k(classifier):
    """Le top-k retourne des intentions ordonnées."""
    top = classifier.predict_top("peux-tu compresser mon téléphone", k=3)
    assert len(top) >= 1
    assert top[0][0] == 'storage_action'
    assert top[0][1] >= top[1][1] if len(top) > 1 else True
