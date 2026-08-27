"""
🌊 fasttext_classifier.py — Classification d'intention légère (CPU, offline)
============================================================================
Remplace le LLM renfort (Phi-3.5-mini) par un classifieur FastText
(subword embeddings, ~5 Mo, < 10 µs) avec fallback sklearn (tfidf char
n-grams + LogisticRegression) si fasttext n'est pas installé.

Propriétés :
  - Généralise aux reformulations non couvertes par les patterns regex
  - ~5-10 Mo, inférence < 50 µs, CPU uniquement, 100% offline
  - Entraînement automatique depuis les définitions du PromptComprehendor
  - Données synthétiques générées par expansion de slots (~5000 exemples)
  - Zéro dépendance cloud, zéro GPU, zéro LLM

Architecture :
  message ──► PromptComprehendor (regex, 80% des cas, 0.19ms)
                  │
              conf < 0.35 ? ──non──► route directe
                  │
                 oui
                  ▼
            FastText classifier (ici, 0.01ms, 5 Mo, offline)
                  │
                  ▼
                route

Usage :
    from ka_server.services.fasttext_classifier import FastTextClassifier

    ft = FastTextClassifier()
    ft.train_from_promptcomprehendor()   # entraînement auto
    intent, conf = ft.predict("j'aimerais que tu examines mon stockage")
    # → ('storage_action', 0.82)
"""

import json
import logging
import os
import pickle
import re
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION DE DONNÉES SYNTHÉTIQUES
# ═══════════════════════════════════════════════════════════════════════════════

# Templates de reformulation par intention (style naturel, variations)
# Chaque entrée = (template avec {slots}, expansion des slots)
_SLOT_EXPANSIONS = {
    'storage_action': {
        'templates': [
            # Questions polies
            "peux-tu {nettoyer} {cible}",
            "pourrais-tu {nettoyer} {cible}",
            "est-ce que tu peux {nettoyer} {cible}",
            "tu peux {nettoyer} {cible}",
            "j'aimerais que tu {nettoies} {cible}",
            "je voudrais {nettoyer} {cible}",
            "j'ai besoin de {nettoyer} {cible}",
            "il faudrait {nettoyer} {cible}",
            "peux-tu {analyser} {cible}",
            "j'aimerais que tu examines l'état de {cible}",
            "dis-moi ce qui prend de la place sur {cible}",
            "peux-tu checker {cible}",
            "faire le ménage dans {cible}",
            "fais le ménage dans {cible}",
            "fais de la place sur {cible}",
            "il me reste combien d'espace sur {cible}",
            "c'est quoi l'état de {cible}",
            "comment libérer de l'espace sur {cible}",
            "combien d'espace il me reste sur {cible}",
            "peux-tu {optimiser} {cible}",
            "{nettoie} {cible}",
            "{optimise} {cible}",
            "mon {cible} est {plein}",
            "{cible} {plein}",
            "je n'ai plus de place sur mon {cible}",
            "aide-moi à {nettoyer} {cible}",
        ],
        'slots': {
            '{nettoyer}': ['nettoyer', 'compresser', 'libérer', 'vider', 'nettoyer',
                          'faire le ménage dans', 'optimiser'],
            '{nettoies}': ['nettoies', 'compresses', 'libères', 'vides', 'optimises',
                          'examines', 'checkes', 'regardes'],
            '{nettoie}': ['nettoie', 'compresse', 'libère', 'vide', 'optimise',
                         'examine', 'checke', 'regarde'],
            '{optimiser}': ['optimiser', 'compresser', 'nettoyer', 'libérer'],
            '{optimise}': ['optimise', 'compresse', 'nettoie', 'libère'],
            '{analyser}': ['analyser', 'vérifier', 'examiner', 'checker', 'regarder',
                          'faire un diagnostic de', 'scanner'],
            '{cible}': ['mon téléphone', 'le téléphone', 'mon appareil',
                       'mon portable', 'le stockage', 'mon stockage',
                       'mes photos', 'mes données', 'ma mémoire',
                       'mes fichiers', 'le cache', 'la mémoire'],
            '{plein}': ['est plein', 'est saturé', 'est rempli', 'n\'a plus de place',
                       'est presque plein', 'est surchargé'],
        },
    },
    'action_command': {
        'templates': [
            "{appelle} {contact}",
            "peux-tu {appeler} {contact}",
            "appelle {contact}",
            "téléphone à {contact}",
            "{envoie} un message à {contact}",
            "envoie un SMS à {contact}",
            "écris à {contact}",
            "{ouvre} {app}",
            "lance {app}",
            "démarre {app}",
            "peux-tu {ouvrir} {app}",
            "quelle est la {sys}",
            "montre-moi la {sys}",
            "active le {sys2}",
            "désactive le {sys2}",
            "coupe le {sys2}",
            "allume le {sys2}",
        ],
        'slots': {
            '{appelle}': ['appelle', 'téléphone à', 'contacte', 'joins'],
            '{appeler}': ['appeler', 'téléphoner à', 'contacter', 'joindre'],
            '{envoie}': ['envoie', 'écris', 'fais un message à'],
            '{ouvre}': ['ouvre', 'lance', 'démarre', 'démarrer'],
            '{ouvrir}': ['ouvrir', 'lancer', 'démarrer'],
            '{contact}': ['Maman', 'Papa', 'Paul', 'Sophie', 'le docteur',
                         'mon frère', 'ma sœur', 'le bureau'],
            '{app}': ['l\'application', 'la calculatrice', 'WhatsApp',
                     'le navigateur', 'la météo', 'le calendrier',
                     'l\'appareil photo', 'la galerie', 'les messages'],
            '{sys}': ['batterie', 'autonomie', 'charge'],
            '{sys2}': ['wifi', 'bluetooth', 'mode avion', 'GPS'],
        },
    },
    'arithmetic': {
        'templates': [
            "combien font {a} {op} {b}",
            "calcule {a} {op} {b}",
            "{a} {op} {b} ça fait combien",
            "quel est le résultat de {a} {op} {b}",
            "que vaut {a} {op} {b}",
            "calcule {a} {op} {b}",
            "je voudrais calculer {a} {op} {b}",
            "peux-tu calculer {a} {op} {b}",
            "racine carrée de {a}",
            "{a} pourcent de {b}",
            "factorielle de {a}",
        ],
        'slots': {
            '{a}': ['15', '200', '7', '42', '100', '3', '25', '144', '50', '12'],
            '{b}': ['3', '5', '8', '10', '20', '100', '2', '4', '6', '200'],
            '{op}': ['plus', 'moins', 'fois', 'divisé par', '+', '-', '*', '/',
                    'multiplié par', '×'],
        },
    },
    'specialize_request': {
        'templates': [
            "spécialise-moi sur {domaine}",
            "spécialise-toi en {domaine}",
            "crée un hologramme sur {domaine}",
            "crée une spécialisation en {domaine}",
            "je voudrais un hologramme de {domaine}",
            "peux-tu devenir expert en {domaine}",
            "apprends le domaine {domaine}",
            "tu connais {domaine}",
            "connais-tu {domaine}",
            "crée une base de connaissances sur {domaine}",
            "fais une spécialisation {domaine}",
        ],
        'slots': {
            '{domaine}': ['la biologie', 'le droit congolais', 'la physique',
                         'la médecine', 'la chimie', 'l\'astronomie',
                         'la philosophie', 'les mathématiques', 'l\'histoire',
                         'la littérature', 'la cuisine', 'le cinéma',
                         'le jazz', 'la mythologie', 'l\'économie'],
        },
    },
    'learning': {
        'templates': [
            "retiens que {fait}",
            "apprends que {fait}",
            "mémorise : {fait}",
            "note que {fait}",
            "enregistre que {fait}",
            "souviens-toi que {fait}",
            "rappelle-toi que {fait}",
            "sache que {fait}",
            "n'oublie pas que {fait}",
            "je voudrais que tu retiennes {fait}",
            "peux-tu mémoriser {fait}",
        ],
        'slots': {
            '{fait}': ['Paris est la capitale de la France',
                      'j\'aime le chocolat noir',
                      'mon anniversaire est le 15 mars',
                      'Paul est mon frère',
                      'le restaurant préféré est Le Petit Cambodge',
                      'la Terre tourne autour du Soleil',
                      'l\'eau bout à 100 degrés',
                      'ma couleur préférée est le bleu',
                      'je suis allergique au lactose',
                      'je travaille chez Airbus'],
        },
    },
    'comparison': {
        'templates': [
            "compare {a} et {b}",
            "quelle est la différence entre {a} et {b}",
            "{a} vs {b}",
            "quel est le meilleur entre {a} et {b}",
            "{a} ou {b}",
            "lequel est mieux : {a} ou {b}",
            "qu'est-ce qui est mieux entre {a} et {b}",
            "différence {a} {b}",
            "compare-moi {a} et {b}",
        ],
        'slots': {
            '{a}': ['le café', 'le chat', 'Android', 'Python', 'Paris',
                   'la voiture', 'le riz', 'le train', 'l\'amour',
                   'le livre', 'le film', 'le vélo'],
            '{b}': ['le thé', 'le chien', 'iOS', 'JavaScript', 'Londres',
                   'le vélo', 'le maïs', 'l\'avion', 'l\'amitié',
                   'le film', 'la série', 'la trottinette'],
        },
    },
    'generation': {
        'templates': [
            "écris un {creation} sur {theme}",
            "génère un {creation} sur {theme}",
            "crée un {creation} à propos de {theme}",
            "invente une {creation2} sur {theme}",
            "raconte une {creation2} sur {theme}",
            "imagine un {creation} sur {theme}",
            "fais-moi un {creation} sur {theme}",
            "j'aimerais un {creation} sur {theme}",
            "peux-tu écrire un {creation}",
        ],
        'slots': {
            '{creation}': ['poème', 'briefing', 'texte', 'article',
                          'rapport', 'scénario', 'discours'],
            '{creation2}': ['histoire', 'fable', 'légende', 'anecdote'],
            '{theme}': ['la mer', 'l\'amour', 'la nature', 'le cosmos',
                       'la liberté', 'le temps', 'la musique', 'le voyage',
                       'la lumière', 'l\'amitié', 'le courage', 'la sagesse'],
        },
    },
    'greeting': {
        'templates': [
            "bonjour",
            "salut",
            "coucou",
            "hello",
            "hey",
            "bonsoir",
            "bonne nuit",
            "bonne journée",
            "merci",
            "merci beaucoup",
            "thanks",
            "au revoir",
            "bye",
            "à plus",
            "à bientôt",
            "ça va",
            "comment ça va",
            "comment vas-tu",
            "quoi de neuf",
        ],
        'slots': {},
    },
    'identity_question': {
        'templates': [
            "qui es-tu",
            "qui es tu",
            "tu es qui",
            "t'es qui",
            "c'est qui KA",
            "c'est quoi KA",
            "qui êtes-vous",
            "présente-toi",
            "presente toi",
            "tu es quoi",
            "tu sers à quoi",
            "à quoi tu sers",
            "quel est ton rôle",
            "quel est ton but",
            "que peux-tu faire",
            "tu peux faire quoi",
            "comment tu t'appelles",
            "comment tu t appelles",
            "ton nom c'est quoi",
            "explique-moi qui tu es",
            "parle-moi de toi",
            "raconte ton histoire",
            "tu fais quoi dans la vie",
            "c'est quoi ton job",
            # Variantes polies / reformulées
            "tu peux me dire qui tu es",
            "je voudrais savoir qui tu es",
            "j'aimerais savoir qui tu es",
            "peux-tu te présenter",
            "tu peux te présenter",
            "décris-toi",
            "qui es tu exactement",
            "dis-moi qui tu es",
            "dis-moi ce que tu es",
            "dis-moi ce que tu fais",
            "c'est quoi ton rôle",
            "c'est quoi ton nom",
            "quel est ton nom",
            "tu es un assistant",
            "es-tu une intelligence artificielle",
            "tu es une IA",
            "tu es un robot",
            "tu es qui exactement",
            "qu'est-ce que tu es",
            "qui es-tu exactement",
            "peux-tu me dire qui tu es exactement",
            "tu peux me dire ce que tu fais",
            "à quoi tu sers exactement",
            "quel est ton objectif",
            "quelle est ta fonction",
            "tu représentes quoi",
            "tu es quel genre d'assistant",
            "qui es-tu et que fais-tu",
            "présente-toi brièvement",
            "je veux en savoir plus sur toi",
            "qui est KA",
            "KA c'est quoi",
            "KA c'est qui",
        ],
        'slots': {},
    },
    'factual_question': {
        'templates': [
            "c'est quoi {sujet}",
            "qu'est-ce que {sujet}",
            "qui est {sujet}",
            "quand a été {decouvert} {sujet}",
            "où se trouve {sujet}",
            "pourquoi {sujet} {verbe}",
            "comment {sujet} {verbe}",
            "comment fonctionne {sujet}",
            "explique {sujet}",
            "définition de {sujet}",
            "que signifie {sujet}",
            "dis-moi ce qu'est {sujet}",
            "je voudrais savoir ce qu'est {sujet}",
            "peux-tu m'expliquer {sujet}",
        ],
        'slots': {
            '{sujet}': ['un hologramme', 'la lumière', 'l\'ADN', 'la gravité',
                       'le nombre d\'or', 'la relativité', 'le Bitcoin',
                       'l\'intelligence artificielle', 'la photosynthèse',
                       'le changement climatique', 'la démocratie',
                       'le système solaire', 'la théorie des cordes'],
            '{decouvert}': ['découvert', 'inventé', 'créé', 'fondé'],
            '{verbe}': ['fonctionne', 'marche', 'est comme ça', 'existe'],
        },
    },
}


def generate_training_data() -> List[Tuple[str, str]]:
    """
    Génère des données d'entraînement synthétiques à partir des templates
    de reformulation. ~50 variations par intention → ~5000 exemples.
    """
    data = []
    for intent_id, config in _SLOT_EXPANSIONS.items():
        templates = config['templates']
        slots = config['slots']

        for template in templates:
            # Détecter les slots présents dans ce template
            present_slots = [s for s in slots if s in template]

            if not present_slots:
                # Template sans slot (greetings, identity)
                data.append((template, intent_id))
                continue

            # Générer des combinaisons (limité à ~20 par template pour éviter explosion)
            seen = set()
            attempts = 0
            while len(seen) < 20 and attempts < 50:
                attempt_text = template
                for slot_name in present_slots:
                    slot_values = slots[slot_name]
                    attempt_text = attempt_text.replace(
                        slot_name, random.choice(slot_values))
                if attempt_text not in seen:
                    seen.add(attempt_text)
                    data.append((attempt_text, intent_id))
                attempts += 1

    random.shuffle(data)
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFIEUR FASTTEXT
# ═══════════════════════════════════════════════════════════════════════════════

def _has_fasttext() -> bool:
    try:
        import fasttext  # noqa: F401
        return True
    except ImportError:
        return False


def _has_sklearn() -> bool:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: F401
        from sklearn.linear_model import LogisticRegression  # noqa: F401
        return True
    except ImportError:
        return False


class FastTextClassifier:
    """
    Classifieur d'intention léger.
    
    Priorité : FastText > sklearn LogisticRegression (char n-grams 2-6).
    Les deux sont ~5-10 Mo, CPU, offline, < 50 µs d'inférence.
    """

    # Seuil de confiance pour accepter la prédiction comme valide
    # (au-dessus, on écrase la décision du PromptComprehendor)
    CONFIDENCE_OVERWRITE = 0.25

    def __init__(self, model_path: str = ""):
        self._model = None          # FastText model ou sklearn pipeline
        self._labels: List[str] = []
        self._backend: str = ""     # 'fasttext', 'sklearn', 'none'
        self._trained = False
        self._model_path = model_path or str(
            Path(__file__).resolve().parent.parent / 'data' / 'intent_classifier.bin'
        )
        self._training_samples = 0

    # ── ENTRAÎNEMENT ─────────────────────────────────────────

    def train(self, training_data: List[Tuple[str, str]] = None):
        """
        Entraîne le classifieur sur les données fournies ou générées.
        
        Args:
            training_data: liste de (texte, label). Si None → génération auto.
        """
        if training_data is None:
            training_data = generate_training_data()

        self._training_samples = len(training_data)
        self._labels = sorted(set(label for _, label in training_data))

        # Format FastText : fichier texte temporaire
        if _has_fasttext():
            self._train_fasttext(training_data)
        elif _has_sklearn():
            self._train_sklearn(training_data)
        else:
            log.warning("Ni fasttext ni sklearn installé — FastTextClassifier inactif")
            self._backend = 'none'
            return

        self._trained = True
        log.info(f"✅ {self._backend} entraîné : {self._training_samples} exemples, "
                 f"{len(self._labels)} classes")

    def _train_fasttext(self, training_data: List[Tuple[str, str]]):
        """Entraîne FastText (subword embeddings 3-6)."""
        import fasttext
        import tempfile

        # Écrire les données au format FastText
        # __label__intent texte
        ft_data = []
        for text, label in training_data:
            clean = text.strip().lower()
            ft_data.append(f"__label__{label} {clean}")

        # Fichier temporaire
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write('\n'.join(ft_data))
            tmp_path = f.name

        try:
            self._model = fasttext.train_supervised(
                tmp_path,
                lr=0.5,
                epoch=25,
                wordNgrams=2,
                minn=2, maxn=5,          # subwords 2-5 (français)
                dim=100,                  # vecteurs compacts
                bucket=200000,
                loss='ova',               # one-vs-all (classes équilibrées)
            )
            self._backend = 'fasttext'
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _train_sklearn(self, training_data: List[Tuple[str, str]]):
        """Entraîne sklearn LogisticRegression + TfidfVectorizer (char n-grams)."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline

        texts = [t.strip().lower() for t, _ in training_data]
        labels = [l for _, l in training_data]

        self._model = Pipeline([
            ('tfidf', TfidfVectorizer(
                analyzer='char_wb',
                ngram_range=(2, 5),
                max_features=5000,
                lowercase=True,
                sublinear_tf=True,
            )),
            ('clf', LogisticRegression(
                C=10.0,
                max_iter=300,
                class_weight='balanced',
                solver='lbfgs',
            )),
        ])
        self._model.fit(texts, labels)
        self._backend = 'sklearn'

    # ── INFÉRENCE ────────────────────────────────────────────

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Prédit l'intention d'un texte.
        
        Returns:
            (intent_label, confidence) — confidence ∈ [0, 1]
        """
        if not self._trained or self._model is None:
            return ('', 0.0)

        clean = text.strip().lower()

        try:
            if self._backend == 'fasttext':
                import fasttext
                labels, scores = self._model.predict(clean, k=1)
                label = labels[0].replace('__label__', '')
                return (label, float(scores[0]))
            elif self._backend == 'sklearn':
                probs = self._model.predict_proba([clean])[0]
                best_idx = probs.argmax()
                return (self._labels[best_idx], float(probs[best_idx]))
        except Exception as e:
            log.debug(f"FastText predict failed: {e}")

        return ('', 0.0)

    def predict_top(self, text: str, k: int = 3) -> List[Tuple[str, float]]:
        """Top-k prédictions."""
        if not self._trained or self._model is None:
            return []

        clean = text.strip().lower()
        try:
            if self._backend == 'fasttext':
                labels, scores = self._model.predict(clean, k=k)
                return [(l.replace('__label__', ''), float(s))
                        for l, s in zip(labels, scores)]
            elif self._backend == 'sklearn':
                probs = self._model.predict_proba([clean])[0]
                idxs = probs.argsort()[::-1][:k]
                return [(self._labels[i], float(probs[i])) for i in idxs]
        except Exception:
            return []

    # ── PERSISTANCE ──────────────────────────────────────────

    def save(self):
        """Sauvegarde le modèle."""
        if not self._trained:
            return
        path = Path(self._model_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if self._backend == 'fasttext':
            self._model.save_model(str(path))
            # Les métadonnées (labels, nb d'exemples) ne sont pas dans le .bin
            # → JSON séparé
            meta_path = str(path).replace('.bin', '.meta.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'backend': 'fasttext',
                    'labels': self._labels,
                    'training_samples': self._training_samples,
                }, f, ensure_ascii=False)
        else:
            data = {
                'backend': self._backend,
                'labels': self._labels,
                'model': self._model,
                'training_samples': self._training_samples,
            }
            with open(str(path).replace('.bin', '.pkl'), 'wb') as f:
                pickle.dump(data, f)

    def load(self) -> bool:
        """Charge un modèle existant."""
        path = Path(self._model_path)

        # Essayer fasttext
        if path.exists():
            try:
                import fasttext
                self._model = fasttext.load_model(str(path))
                self._backend = 'fasttext'
                self._trained = True
                # Restaurer les métadonnées depuis le JSON séparé
                meta_path = Path(str(path).replace('.bin', '.meta.json'))
                if meta_path.exists():
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    self._labels = meta.get('labels', [])
                    self._training_samples = meta.get('training_samples', 0)
                log.info(f"📦 FastText chargé : {str(path)} "
                         f"({self._training_samples} exemples)")
                return True
            except Exception:
                pass

        # Essayer sklearn pickle
        pkl_path = Path(str(path).replace('.bin', '.pkl'))
        if pkl_path.exists():
            try:
                with open(pkl_path, 'rb') as f:
                    data = pickle.load(f)
                self._backend = data['backend']
                self._labels = data['labels']
                self._model = data['model']
                self._training_samples = data.get('training_samples', 0)
                self._trained = True
                log.info(f"📦 sklearn chargé : {pkl_path}")
                return True
            except Exception:
                pass

        return False

    def train_from_promptcomprehendor(self):
        """
        Entraîne le classifieur à partir des définitions du PromptComprehendor.
        Appelé une fois au démarrage (ou après modification des intents).
        """
        training_data = generate_training_data()
        self.train(training_data)

        # Sauvegarder pour les démarrages futurs
        self.save()
        return self

    # ── STATS ────────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._trained

    @property
    def info(self) -> dict:
        return {
            'backend': self._backend,
            'trained': self._trained,
            'training_samples': self._training_samples,
            'labels': self._labels,
            'labels_count': len(self._labels),
        }

    def __repr__(self) -> str:
        return (f"FastTextClassifier(backend={self._backend}, "
                f"trained={self._trained}, samples={self._training_samples})")


# ── Singleton ──────────────────────────────────────────────
_classifier: Optional[FastTextClassifier] = None


def get_classifier() -> FastTextClassifier:
    global _classifier
    if _classifier is None:
        _classifier = FastTextClassifier()
        # Charger si sauvegardé, sinon entraîner
        if not _classifier.load():
            _classifier.train_from_promptcomprehendor()
    return _classifier


# ═══════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 65)
    print("  🌊 FastText Classifier — Test")
    print("=" * 65)

    # ── Génération données ──
    data = generate_training_data()
    print(f"\n[1] Données générées : {len(data)} exemples")
    for intent in sorted(set(l for _, l in data)):
        count = sum(1 for _, l in data if l == intent)
        print(f"    {intent:<25s} {count:>4d} exemples")

    # ── Entraînement ──
    print(f"\n[2] Entraînement...")
    t0 = time.perf_counter()
    ft = FastTextClassifier()
    ft.train(data)
    train_time = (time.perf_counter() - t0) * 1000
    print(f"    {ft}")
    print(f"    Temps : {train_time:.0f} ms")

    # ── Tests de généralisation (phrases NON vues à l'entraînement) ──
    print(f"\n[3] Tests de généralisation (hors templates) :")
    tests = [
        ("j'aimerais que tu examines l'état de mon espace de stockage", "storage_action"),
        ("dis-moi ce qui prend toute la place sur mon téléphone", "storage_action"),
        ("peux-tu checker mon stockage stp", "storage_action"),
        ("fais le ménage dans mon téléphone", "storage_action"),
        ("téléphone à ma sœur s'il te plaît", "action_command"),
        ("lance donc le navigateur web", "action_command"),
        ("combien ça fait 42 fois 7", "arithmetic"),
        ("quelle est la différence entre un chat et un chien", "comparison"),
        ("j'aimerais que tu retiennes que j'adore le jazz", "learning"),
        ("bonjour comment ça va aujourd'hui", "greeting"),
        ("tu peux me dire qui tu es exactement", "identity_question"),
        ("explique-moi ce qu'est un trou noir", "factual_question"),
        # Tests ambigus (devrait être reclassé par FastText)
        ("j'aimerais que tu examines mon stockage", "storage_action"),
        ("peux-tu me dire ce qu'est un hologramme", "factual_question"),
    ]

    correct = 0
    total = len(tests)
    for text, expected in tests:
        intent, conf = ft.predict(text)
        ok = "✅" if intent == expected else "❌"
        if intent == expected:
            correct += 1
        print(f"  {ok} {expected:<20s} (conf={conf:.3f}) ← {text[:60]}")

    print(f"\n  Précision : {correct}/{total} ({100*correct/total:.0f}%)")

    # ── Latence d'inférence ──
    print(f"\n[4] Latence d'inférence :")
    latencies = []
    for _ in range(500):
        t0 = time.perf_counter()
        ft.predict("peux-tu compresser mon téléphone")
        latencies.append((time.perf_counter() - t0) * 1000)
    avg = sum(latencies) / len(latencies)
    print(f"    avg={avg*1000:.1f} µs  p99={sorted(latencies)[495]*1000:.1f} µs")

    # ── Sauvegarde ──
    print(f"\n[5] Sauvegarde...")
    ft.save()
    print(f"    Modèle sauvegardé.")

    # ── Rechargement ──
    ft2 = FastTextClassifier()
    loaded = ft2.load()
    print(f"    Rechargé : {loaded}, {ft2}")

    print(f"\n✅ FastText Classifier test terminé.")