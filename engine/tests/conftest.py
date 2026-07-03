"""
Fixtures partagées pour les tests Harmonic AI.
Usage : pytest tests/ -v
"""
import sys
import os
from pathlib import Path
import pytest
import numpy as np

# Ajouter engine/ au path
_ENGINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ENGINE_DIR))

# Empêcher les imports qui déclenchent des side-effects
os.environ.setdefault('DEEPSEEK_API_KEY', 'test-key-mock')


# ═══════════════════════════════════════════════════════════════════════════════
# KB synthétique (20 faits, 6 secteurs)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def small_kb():
    """Base de connaissance synthétique pour les tests."""
    return [
        # PHYSIQUE_FOND
        ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
        ("lumiere", "se deplace a", "300000 km/s", "PHYSIQUE_FOND"),
        ("onde", "transporte", "energie sans matiere", "PHYSIQUE_FOND"),
        ("einstein", "a decouvert", "la relativite", "PHYSIQUE_FOND"),
        ("gravite", "est", "la courbure de l espace temps", "PHYSIQUE_FOND"),
        # BIOLOGIE
        ("coeur", "pompe", "le sang", "BIOLOGIE"),
        ("sang", "transporte", "l oxygene", "BIOLOGIE"),
        ("plante", "utilise", "la photosynthese", "BIOLOGIE"),
        ("photosynthese", "transforme", "la lumiere en energie", "BIOLOGIE"),
        # CONSCIENCE
        ("conscience", "est", "la perception de soi et du monde", "CONSCIENCE"),
        ("cerveau", "produit", "la pensee", "CONSCIENCE"),
        # MATHS
        ("phi", "est le", "nombre d or", "MATHS_PURES"),
        ("phi", "vaut", "1.618", "MATHS_PURES"),
        # CULTURE
        ("musique", "est", "l art des sons", "CULTURE"),
        ("mozart", "a compose", "la flute enchantee", "CULTURE"),
        # GEOGRAPHIE (nouveau secteur)
        ("paris", "est", "la capitale de la France", "GEOGRAPHIE"),
        ("france", "est", "un pays d Europe", "GEOGRAPHIE"),
        # SPIRITUALITE
        ("dieu", "est", "le principe createur", "SPIRITUALITE"),
        # EMOTION
        ("amour", "est", "la force fondamentale de l univers", "EMOTION_POS"),
        ("peur", "est", "une reaction de survie", "EMOTION_NEG"),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# Modèle sans holographique (φ-cercle classique)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def model_phi(small_kb):
    """HarmonicModel avec φ-cercle classique (pas d'encodeur holographique)."""
    from harmonic_model import HarmonicModel, build_waves

    class SimpleModel:
        def __init__(self, kb):
            self.knowledge_base = list(kb)
            self.use_holographic = False
            self.kx, self.ky, self.w2i = build_waves(self.knowledge_base)
            self.memoire = None
            self._last_topic = None

        def ask(self, question, max_words=6):
            from harmonic_model import generate
            return generate(
                question, self.kx, self.ky, self.w2i,
                knowledge_base=self.knowledge_base,
                memoire=self.memoire, max_words=max_words
            )

        def rebuild_waves(self):
            self.kx, self.ky, self.w2i = build_waves(self.knowledge_base)

    return SimpleModel(small_kb)


# ═══════════════════════════════════════════════════════════════════════════════
# Modèle avec holographique
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def model_holographic(small_kb):
    """HarmonicModel avec encodeur holographique HRR."""
    from harmonic_model import HarmonicModel
    model = HarmonicModel(use_memory=True, use_holographic=True)
    model.knowledge_base = list(small_kb)
    model.rebuild_waves()
    return model


# ═══════════════════════════════════════════════════════════════════════════════
# Moteur de raisonnement
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def engine(model_phi):
    """ReasoningEngine sur le petit modèle."""
    from reasoning_engine import ReasoningEngine
    return ReasoningEngine(model_phi)


# ═══════════════════════════════════════════════════════════════════════════════
# StyleEngine
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def styler():
    """StyleEngine frais."""
    from style_engine import StyleEngine
    return StyleEngine()


# ═══════════════════════════════════════════════════════════════════════════════
# Bootstrapper mocké (sans LLM)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def bootstrapper(small_kb):
    """HarmonicBootstrapper sans LLM (mode extraction regex uniquement)."""
    from bootstrapper import HarmonicBootstrapper
    from harmonic_model import HarmonicModel
    model = HarmonicModel(use_memory=False, use_holographic=False)
    model.knowledge_base = list(small_kb)
    model.rebuild_waves()
    boot = HarmonicBootstrapper(use_memory=False, model=model)
    # Désactiver le LLM
    import bootstrapper as bm
    bm._LLM_AVAILABLE = False
    return boot


# ═══════════════════════════════════════════════════════════════════════════════
# Client Flask de test
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def client():
    """Client de test Flask pour ka_server."""
    # Éviter le chargement complet du serveur (trop de side-effects)
    from flask import Flask
    from flask_cors import CORS
    app = Flask(__name__)
    CORS(app)
    app.config['TESTING'] = True

    # Injecter un modèle mocké
    from harmonic_model import HarmonicModel
    model = HarmonicModel(use_memory=False, use_holographic=False)
    model.knowledge_base = [
        ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
        ("einstein", "a decouvert", "la relativite", "PHYSIQUE_FOND"),
        ("gravite", "est", "la courbure de l espace temps", "PHYSIQUE_FOND"),
    ]
    model.rebuild_waves()

    class MockAI:
        def __init__(self):
            self.model = model
            self.bootstrapper = None
            self.conversation = type('obj', (object,), {
                'messages': [],
                'max_messages': 50,
                'add': lambda self, role, content: self.messages.append(
                    type('obj', (object,), {'role': role, 'content': content})()
                ),
            })()

        def ask(self, question):
            return self.model.ask(question)

        def reason(self, topic):
            return self.model.ask(topic)

        def _confidence_score(self, response, question):
            if not response or len(response) < 20:
                return 0.0
            return 0.5

        @property
        def stats(self):
            return {'faits': 3, 'vocabulaire': 10, 'experiences': 0,
                    'energie': 0, 'autonomie': 100.0, 'llm_calls': 0}

    mock_ai = MockAI()

    # Enregistrer les routes de test
    @app.route('/api/chat', methods=['POST'])
    def chat():
        from flask import request, jsonify
        data = request.get_json(force=True, silent=True) or {}
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'error': 'Message requis'}), 400
        response = mock_ai.ask(message)
        return jsonify({'response': response, 'confidence': 0.5, 'source': 'harmonic'})

    @app.route('/api/reason', methods=['POST'])
    def reason():
        from flask import request, jsonify
        data = request.get_json(force=True, silent=True) or {}
        topic = data.get('topic', '').strip()
        if not topic:
            return jsonify({'error': 'Sujet requis'}), 400
        chain = mock_ai.reason(topic)
        return jsonify({'chain': chain, 'steps': [chain], 'step_count': 1})

    @app.route('/api/stats', methods=['GET'])
    def stats():
        from flask import jsonify
        import time
        return jsonify({
            'faits': 3, 'vocabulaire': 10, 'autonomie': 100.0,
            'conversation_messages': 0, 'server_uptime': 0
        })

    @app.route('/api/health', methods=['GET'])
    def health():
        from flask import jsonify
        return jsonify({'status': 'ok', 'harmonic': True})

    return app.test_client()
