"""
Knowledge Enricher — Blocs de savoir profonds
=============================================
Complète la KB de triplets superficiels avec des blocs de savoir :
des paragraphes explicatifs denses (3-5 phrases) générés une seule
fois par le LLM, puis stockés et réutilisés.

Structure de données :
  enrichissements = {
    "lumiere": {
      "bloc": "La lumière est une onde électromagnétique qui se propage
               à environ 300 000 km/s dans le vide. Elle est composée de
               photons, des particules sans masse. Son comportement est
               à la fois ondulatoire et corpusculaire (dualité onde-corpuscule)...",
      "type": "definition",
      "source": "deepseek|curated",
      "timestamp": 1234567890
    },
    ...
  }

Persistance :
  - Sauvegardé en JSON dans data/enrichissements.json
  - Chargé au démarrage si disponible
  - Mis à jour progressivement (quand le LLM fallback répond)

Usage :
  from knowledge_enricher import KnowledgeEnricher
  enricher = KnowledgeEnricher()
  bloc = enricher.get_bloc("lumiere")  # None si pas encore enrichi
  enricher.enrich_from_llm("lumiere", llm_response)
"""

import os, sys, json, time, logging
from pathlib import Path
from typing import Dict, Optional, List

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
_ENRICH_PATH = _ENGINE_DIR / 'data' / 'enrichissements.json'


class KnowledgeEnricher:
    """
    Gère les blocs de savoir enrichis (paragraphes explicatifs).

    Au lieu de répondre avec des triplets superficiels, le système peut
    utiliser ces blocs pour donner des explications riches et naturelles.
    """

    def __init__(self, path: Optional[Path] = None):
        self.path = path or _ENRICH_PATH
        self._blocs: Dict[str, dict] = {}
        self._load()

    # ═════════════════════════════════════════════════════════════════════════
    # PERSISTANCE
    # ═════════════════════════════════════════════════════════════════════════

    def _load(self):
        """Charge les enrichissements depuis le disque."""
        try:
            if self.path.exists():
                with open(self.path, 'r', encoding='utf-8') as f:
                    self._blocs = json.load(f)
                log.info(f"  📚 {len(self._blocs)} blocs de savoir chargés")
        except Exception as e:
            log.warning(f"Erreur chargement enrichissements: {e}")
            self._blocs = {}

    def save(self):
        """Sauvegarde les enrichissements sur le disque."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self._blocs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning(f"Erreur sauvegarde enrichissements: {e}")

    # ═════════════════════════════════════════════════════════════════════════
    # ACCÈS
    # ═════════════════════════════════════════════════════════════════════════

    def get_bloc(self, sujet: str, question_type: str = 'definition') -> Optional[str]:
        """
        Retourne le bloc explicatif le plus adapté au type de question.

        Args:
            sujet: mot-clé du sujet (ex: "lumiere", "gravite")
            question_type: 'definition' | 'mecanisme' | 'importance' | 'historique' | 'exemple'

        Returns:
            paragraphe explicatif adapté, ou None
        """
        sujet = sujet.lower().strip()
        data = self._find_entry(sujet)
        if not data:
            return None

        # Si le bloc est segmenté → choisir le segment adapté
        if 'definition' in data:
            # Chercher le segment le plus pertinent
            if question_type == 'definition':
                text = data.get('definition', '')
                # Ajouter un segment complémentaire si disponible
                if data.get('mecanisme') and len(text) < 200:
                    text += ' ' + data['mecanisme']
                return text
            elif question_type in ('mecanisme', 'procedure'):
                return data.get('mecanisme') or data.get('definition', '')
            elif question_type == 'identite':
                return data.get('historique') or data.get('definition', '')
            elif question_type == 'comparaison':
                return data.get('exemple') or data.get('mecanisme') or data.get('definition', '')
            # Importance / "pourquoi X est important"
            elif 'important' in question_type or question_type == 'importance':
                return data.get('importance') or data.get('definition', '')
            else:
                return data.get('definition', '')
        else:
            # Bloc legacy non segmenté : retourner tel quel
            return data.get('bloc', '')

    def get_all_context(self, sujet: str) -> Optional[str]:
        """
        Retourne TOUS les segments fusionnés (pour une réponse complète).
        Utile pour les questions très générales ("parle-moi de X").
        """
        sujet = sujet.lower().strip()
        data = self._find_entry(sujet)
        if not data:
            return None

        segments = []
        for key in ('definition', 'mecanisme', 'importance', 'historique', 'exemple'):
            if key in data and data[key]:
                segments.append(data[key])

        if segments:
            return ' '.join(segments)
        return data.get('bloc', None)

    def _find_entry(self, sujet: str) -> Optional[dict]:
        """Recherche l'entrée la plus proche pour un sujet donné."""
        if sujet in self._blocs:
            return self._blocs[sujet]
        # Recherche par préfixe
        for key, val in self._blocs.items():
            if sujet.startswith(key) or key.startswith(sujet):
                return val
        return None

    def has_bloc(self, sujet: str) -> bool:
        """Vérifie si un sujet a déjà un bloc explicatif."""
        return self.get_bloc(sujet) is not None

    @property
    def count(self) -> int:
        """Nombre de blocs enrichis."""
        return len(self._blocs)

    @property
    def sujets(self) -> List[str]:
        """Liste des sujets enrichis."""
        return list(self._blocs.keys())

    # ═════════════════════════════════════════════════════════════════════════
    # ENRICHISSEMENT
    # ═════════════════════════════════════════════════════════════════════════

    def enrich_from_llm(self, sujet: str, llm_response: str,
                        q_type: str = 'definition'):
        """
        Enrichit la base avec une réponse LLM de haute qualité.

        La réponse est nettoyée et stockée comme bloc explicatif
        pour ce sujet. Les futures questions sur ce sujet utiliseront
        directement ce bloc sans rappeler le LLM.

        Args:
            sujet: sujet de la connaissance
            llm_response: réponse du LLM (texte brut)
            q_type: type de question (definition, mecanisme, etc.)
        """
        sujet = sujet.lower().strip()

        # Nettoyer la réponse LLM
        bloc = self._clean_llm_response(llm_response)

        if len(bloc) < 50:
            log.debug(f"Bloc trop court pour '{sujet}', ignoré")
            return

        self._blocs[sujet] = {
            'bloc': bloc,
            'type': q_type,
            'source': 'llm',
            'timestamp': time.time(),
        }

        log.info(f"  ✨ Bloc de savoir ajouté: '{sujet}' ({len(bloc)} car.)")
        self.save()

    def enrich_curated(self, sujet: str, data, q_type: str = 'definition'):
        """
        Ajoute un bloc de savoir curated (vérifié humainement).

        Args:
            sujet: sujet
            data: soit un str (bloc legacy), soit un dict segmenté {definition, mecanisme, importance, ...}
            q_type: type de question (ignoré si data est un dict)
        """
        sujet = sujet.lower().strip()
        if isinstance(data, str):
            self._blocs[sujet] = {
                'bloc': data.strip(),
                'type': q_type,
                'source': 'curated',
                'timestamp': time.time(),
            }
        else:
            data = dict(data)
            data['source'] = 'curated'
            data['timestamp'] = time.time()
            self._blocs[sujet] = data
        self.save()

    def enrich_from_facts(self, sujet: str, facts: list) -> str:
        """
        Construit un bloc de savoir synthétique à partir de faits existants.
        Ne remplace pas un vrai enrichissement LLM mais fournit un texte
        plus dense que des triplets isolés.

        Args:
            sujet: sujet
            facts: liste de (sujet, relation, objet, secteur)

        Returns:
            bloc synthétique
        """
        if not facts:
            return ""

        phrases = []
        for s, r, o, _ in facts[:5]:
            phrases.append(f"{s} {r} {o}")

        bloc = '. '.join(phrases) + '.'
        return bloc

    # ═════════════════════════════════════════════════════════════════════════
    # NETTOYAGE
    # ═════════════════════════════════════════════════════════════════════════

    def _clean_llm_response(self, text: str) -> str:
        """Nettoie une réponse LLM pour en faire un bloc de savoir propre."""
        # Retirer les marqueurs markdown
        text = text.replace('**', '').replace('*', '').replace('_', '')
        text = text.replace('```', '').replace('`', '')

        # Retirer les en-têtes type "### Définition"
        lines = text.strip().split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                continue
            if line.startswith('- ') or line.startswith('• '):
                line = line[2:]
            if line:
                clean_lines.append(line)

        text = ' '.join(clean_lines)

        # Limiter la taille (max ~500 caractères pour rester concis)
        if len(text) > 600:
            # Couper à la fin de la phrase la plus proche
            cut = text[:500]
            last_dot = cut.rfind('.')
            if last_dot > 200:
                text = cut[:last_dot + 1]

        return text.strip()

    # ═════════════════════════════════════════════════════════════════════════
    # CURATION INITIALE
    # ═════════════════════════════════════════════════════════════════════════

    def load_curated_defaults(self):
        """
        Charge une base initiale de blocs curated pour les sujets
        les plus importants. Ces blocs sont écrits manuellement
        et garantissent une qualité minimale sans dépendre du LLM.
        """
        curated = {
            # ═══════════════════════════════════════════════════════════════
            # PHYSIQUE (segmentés)
            # ═══════════════════════════════════════════════════════════════
            'lumiere': {
                'definition': (
                    "La lumière est une onde électromagnétique qui se propage "
                    "à environ 300 000 km/s dans le vide. Elle est composée de "
                    "photons, des particules élémentaires sans masse."
                ),
                'mecanisme': (
                    "La lumière se propage grâce à l'oscillation couplée des "
                    "champs électrique et magnétique qui s'auto-entretiennent. "
                    "Contrairement aux ondes sonores, elle n'a pas besoin de "
                    "milieu matériel et peut traverser le vide spatial."
                ),
                'importance': (
                    "La lumière est essentielle à la vie sur Terre : elle "
                    "alimente la photosynthèse, régule les rythmes biologiques "
                    "et nous permet de percevoir le monde par la vision. Sans "
                    "elle, notre planète serait un désert glacé."
                ),
                'historique': (
                    "La nature de la lumière a été débattue pendant des siècles. "
                    "Newton la voyait comme un flux de corpuscules, Huygens "
                    "comme une onde. Au XIXe siècle, Maxwell l'a unifiée avec "
                    "l'électromagnétisme, et Einstein a introduit le photon "
                    "en 1905, révélant sa double nature onde-particule."
                ),
            },
            'gravite': {
                'definition': (
                    "La gravité est la force d'attraction universelle qui "
                    "s'exerce entre tous les corps dotés d'une masse. Elle "
                    "est décrite par la loi de Newton (F = Gm₁m₂/r²) à "
                    "l'échelle quotidienne."
                ),
                'mecanisme': (
                    "Selon la relativité générale d'Einstein, la gravité "
                    "n'est pas une force mais une courbure de l'espace-temps. "
                    "La masse déforme la géométrie de l'espace autour d'elle, "
                    "et les objets suivent les géodésiques de cet espace courbe. "
                    "C'est ainsi que la Terre reste en orbite autour du Soleil."
                ),
                'importance': (
                    "Sans la gravité, les galaxies ne se formeraient pas, "
                    "les étoiles ne s'allumeraient pas et les planètes ne "
                    "pourraient pas exister. Elle est la force dominante à "
                    "l'échelle cosmologique et la raison pour laquelle nous "
                    "avons une atmosphère et des océans."
                ),
            },
            'mecanique quantique': {
                'definition': (
                    "La mécanique quantique est la branche de la physique "
                    "qui décrit le comportement de la matière et de l'énergie "
                    "à l'échelle atomique et subatomique."
                ),
                'mecanisme': (
                    "Elle repose sur des principes contre-intuitifs : la "
                    "superposition (une particule peut être dans plusieurs "
                    "états à la fois), l'intrication (deux particules restent "
                    "liées quelle que soit la distance) et le principe "
                    "d'incertitude d'Heisenberg (on ne peut connaître "
                    "simultanément position et vitesse avec précision infinie). "
                    "Ces phénomènes ont été vérifiés expérimentalement des "
                    "milliers de fois."
                ),
                'importance': (
                    "La mécanique quantique est au cœur de la technologie "
                    "moderne : lasers, transistors, IRM médicale, GPS, et "
                    "ordinateurs quantiques en émergence. Elle a révolutionné "
                    "notre compréhension de la réalité elle-même."
                ),
            },
            'relativite': {
                'definition': (
                    "La relativité est la théorie physique formulée par "
                    "Albert Einstein au début du XXe siècle, comprenant la "
                    "relativité restreinte (1905) et la relativité générale "
                    "(1915)."
                ),
                'mecanisme': (
                    "La relativité restreinte montre que le temps et l'espace "
                    "sont relatifs au référentiel de l'observateur : plus on "
                    "se déplace vite, plus le temps ralentit. La relativité "
                    "générale décrit la gravitation comme une courbure de "
                    "l'espace-temps par la masse. L'équation E=mc² établit "
                    "l'équivalence masse-énergie."
                ),
                'importance': (
                    "Sans la relativité, le GPS serait inopérant en quelques "
                    "heures : les corrections relativistes sont nécessaires "
                    "pour synchroniser les satellites. La relativité est "
                    "essentielle à la cosmologie moderne et à notre "
                    "compréhension des trous noirs."
                ),
            },

            # ═══════════════════════════════════════════════════════════════
            # BIOLOGIE (segmentés)
            # ═══════════════════════════════════════════════════════════════
            'evolution': {
                'definition': (
                    "L'évolution est le processus par lequel les espèces "
                    "vivantes se transforment au fil des générations sous "
                    "l'effet de la sélection naturelle et des mutations "
                    "génétiques."
                ),
                'mecanisme': (
                    "Proposée par Charles Darwin en 1859, la sélection "
                    "naturelle favorise les individus les mieux adaptés à "
                    "leur environnement, qui survivent et se reproduisent "
                    "davantage. Les mutations aléatoires de l'ADN créent "
                    "la diversité sur laquelle la sélection agit. Ce double "
                    "mécanisme — variation + sélection — explique "
                    "l'extraordinaire diversité du vivant."
                ),
                'importance': (
                    "L'évolution est le principe unificateur de la biologie "
                    "moderne. Elle explique l'origine des espèces, la "
                    "résistance aux antibiotiques, l'émergence de nouveaux "
                    "virus, et notre propre histoire évolutive. « Rien n'a "
                    "de sens en biologie, si ce n'est à la lumière de "
                    "l'évolution » (Dobzhansky)."
                ),
                'exemple': (
                    "Un exemple classique est l'évolution des pinsons des "
                    "Galápagos, dont le bec s'est adapté aux graines "
                    "disponibles sur chaque île. Autre exemple : la "
                    "résistance des bactéries aux antibiotiques, observable "
                    "en quelques années seulement."
                ),
            },
            'cerveau': {
                'definition': (
                    "Le cerveau est l'organe central du système nerveux, "
                    "siège de la pensée, des émotions et de la conscience. "
                    "Il contient environ 86 milliards de neurones "
                    "interconnectés."
                ),
                'mecanisme': (
                    "Les neurones communiquent par des signaux électriques "
                    "et chimiques via les synapses. La plasticité cérébrale "
                    "permet au cerveau de se réorganiser en permanence : "
                    "chaque apprentissage renforce ou crée de nouvelles "
                    "connexions synaptiques. Les neurotransmetteurs comme "
                    "la dopamine et la sérotonine modulent l'humeur et la "
                    "motivation."
                ),
                'importance': (
                    "Le cerveau consomme 20% de l'énergie du corps pour "
                    "seulement 2% de sa masse. Il est responsable de tout "
                    "ce qui fait notre humanité : langage, créativité, "
                    "mémoire, conscience de soi. Sa compréhension est l'un "
                    "des plus grands défis scientifiques du XXIe siècle."
                ),
            },

            # ═══════════════════════════════════════════════════════════════
            # ASTRONOMIE (segmentés)
            # ═══════════════════════════════════════════════════════════════
            'big bang': {
                'definition': (
                    "Le Big Bang est la théorie cosmologique dominante "
                    "décrivant l'origine de l'Univers il y a 13,8 milliards "
                    "d'années."
                ),
                'mecanisme': (
                    "L'Univers était initialement concentré en un point "
                    "infiniment dense et chaud — une singularité — qui "
                    "s'est brutalement expansé. Il ne s'agit pas d'une "
                    "explosion dans l'espace, mais de l'expansion de "
                    "l'espace lui-même. Les preuves incluent le fond diffus "
                    "cosmologique (rayonnement fossile), l'expansion des "
                    "galaxies (loi de Hubble) et l'abondance des éléments "
                    "légers (hydrogène, hélium)."
                ),
                'importance': (
                    "Le Big Bang est le cadre théorique qui unifie toute "
                    "la cosmologie moderne. Il explique la formation des "
                    "premières particules, des atomes, puis des étoiles et "
                    "des galaxies. Sans cette théorie, nous ne pourrions "
                    "pas comprendre l'histoire de notre Univers."
                ),
            },

            # ═══════════════════════════════════════════════════════════════
            # CONSCIENCE / ESPRIT (segmentés)
            # ═══════════════════════════════════════════════════════════════
            'conscience': {
                'definition': (
                    "La conscience est la capacité d'un être à percevoir "
                    "soi-même et son environnement, à éprouver des "
                    "sensations subjectives (qualia) et à avoir une "
                    "expérience intérieure du monde."
                ),
                'mecanisme': (
                    "La conscience émerge de l'activité complexe du cerveau, "
                    "particulièrement du cortex cérébral et du thalamus. "
                    "Les neurosciences identifient des corrélats neuronaux "
                    "(activité synchronisée) mais le « problème difficile » "
                    "reste : comment l'activité objective de neurones "
                    "produit-elle l'expérience subjective ?"
                ),
                'importance': (
                    "La conscience est ce qui donne un sens à notre "
                    "existence. Sans elle, il n'y aurait ni art, ni science, "
                    "ni morale, ni questionnement. Comprendre la conscience, "
                    "c'est comprendre ce qui fait de nous des êtres humains."
                ),
            },

            # ═══════════════════════════════════════════════════════════════
            # TECHNOLOGIE (segmentés)
            # ═══════════════════════════════════════════════════════════════
            'intelligence artificielle': {
                'definition': (
                    "L'intelligence artificielle (IA) est le domaine de "
                    "l'informatique visant à créer des machines capables "
                    "de simuler des capacités cognitives humaines : "
                    "apprentissage, raisonnement, perception, langage."
                ),
                'mecanisme': (
                    "L'IA moderne repose principalement sur l'apprentissage "
                    "automatique (machine learning) et les réseaux de "
                    "neurones profonds (deep learning). Ces systèmes "
                    "apprennent à partir de données massives en ajustant "
                    "des millions de paramètres par rétropropagation du "
                    "gradient. Les modèles de langage (LLMs) prédisent le "
                    "mot suivant dans une phrase, acquérant ainsi des "
                    "capacités de raisonnement émergentes."
                ),
                'importance': (
                    "L'IA transforme déjà la médecine (diagnostic), les "
                    "transports (véhicules autonomes), l'industrie "
                    "(robotique), la création (art génératif) et la "
                    "recherche scientifique (repliement des protéines). "
                    "Elle soulève des questions éthiques majeures sur "
                    "l'emploi, les biais algorithmiques et le contrôle "
                    "des systèmes autonomes."
                ),
            },

            # ═══════════════════════════════════════════════════════════════
            # SOCIÉTÉ (segmentés)
            # ═══════════════════════════════════════════════════════════════
            'democratie': {
                'definition': (
                    "La démocratie est un système politique où le pouvoir "
                    "appartient au peuple, exercé directement ou par des "
                    "représentants élus lors d'élections libres."
                ),
                'mecanisme': (
                    "Elle repose sur la séparation des pouvoirs (exécutif, "
                    "législatif, judiciaire), la liberté d'expression, le "
                    "pluralisme politique et l'État de droit. Les élections "
                    "régulières permettent aux citoyens de choisir leurs "
                    "dirigeants et de les sanctionner. Une presse libre et "
                    "une société civile active sont essentielles au "
                    "fonctionnement démocratique."
                ),
                'importance': (
                    "La démocratie est le seul système qui garantit à la "
                    "fois la liberté individuelle et la souveraineté "
                    "populaire. Elle permet l'alternance pacifique du "
                    "pouvoir et protège contre la tyrannie. Malgré ses "
                    "imperfections, aucun autre système n'a produit autant "
                    "de prospérité et de paix durable."
                ),
            },
            'liberte': {
                'definition': (
                    "La liberté est la capacité d'agir selon sa propre "
                    "volonté, sans contrainte extérieure excessive."
                ),
                'mecanisme': (
                    "En philosophie, la liberté oppose le déterminisme "
                    "(tout événement a une cause) au libre arbitre (l'être "
                    "humain peut choisir). En politique, elle s'exerce dans "
                    "le cadre de la loi : la liberté des uns s'arrête là "
                    "où commence celle des autres. Les droits fondamentaux "
                    "(expression, conscience, association) en sont les "
                    "garanties institutionnelles."
                ),
                'importance': (
                    "La liberté est la valeur fondatrice des sociétés "
                    "démocratiques modernes. Sans elle, il n'y a ni "
                    "créativité, ni innovation, ni épanouissement "
                    "personnel. C'est le premier des droits humains, "
                    "celui qui rend tous les autres possibles."
                ),
            },
            'atome': (
                "L'atome est la plus petite unité de matière qui conserve "
                "les propriétés d'un élément chimique. Il est constitué d'un "
                "noyau central (protons et neutrons) autour duquel gravitent "
                "des électrons. Le nombre de protons détermine l'élément "
                "chimique. La taille d'un atome est de l'ordre de 0,1 "
                "nanomètre. La matière ordinaire est entièrement composée "
                "d'atomes, ce qui en fait la brique fondamentale de l'univers "
                "matériel."
            ),
            'electromagnetisme': (
                "L'électromagnétisme est l'une des quatre forces fondamentales "
                "de la nature. Il décrit l'interaction entre les particules "
                "chargées électriquement. James Clerk Maxwell a unifié "
                "l'électricité et le magnétisme en une seule théorie au "
                "XIXe siècle. Les ondes électromagnétiques incluent la "
                "lumière visible, les rayons X, les ondes radio et les "
                "micro-ondes. Cette force est responsable de la cohésion "
                "des atomes et de presque tous les phénomènes quotidiens."
            ),
            'thermodynamique': (
                "La thermodynamique est la science qui étudie les échanges "
                "d'énergie, notamment sous forme de chaleur et de travail. "
                "Elle repose sur quatre principes fondamentaux, dont le "
                "premier (conservation de l'énergie) et le second (l'entropie "
                "d'un système isolé ne peut qu'augmenter). Ces lois expliquent "
                "pourquoi une machine perpétuelle est impossible et pourquoi "
                "le temps semble s'écouler dans une seule direction."
            ),
            'energie': (
                "L'énergie est la capacité d'un système à produire un "
                "travail ou de la chaleur. Elle se présente sous de multiples "
                "formes : cinétique (mouvement), potentielle (position), "
                "thermique (chaleur), chimique (liaisons), nucléaire (noyau) "
                "et électromagnétique (lumière). Le premier principe de la "
                "thermodynamique établit que l'énergie ne se crée ni ne se "
                "détruit : elle se transforme. C'est une grandeur qui se "
                "conserve dans tous les processus physiques."
            ),
            'onde': (
                "Une onde est une perturbation qui se propage dans un milieu "
                "ou dans l'espace, transportant de l'énergie sans transporter "
                "de matière. On distingue les ondes mécaniques (son, vagues) "
                "qui nécessitent un milieu matériel, et les ondes "
                "électromagnétiques (lumière, radio) qui se propagent dans "
                "le vide. Les ondes sont caractérisées par leur fréquence, "
                "leur longueur d'onde et leur amplitude. Le phénomène "
                "d'interférence, où deux ondes se combinent, est au cœur "
                "de la physique ondulatoire."
            ),

            # ─── BIOLOGIE (suite) ──────────────────────────────────────────
            'cellule': (
                "La cellule est l'unité fondamentale de tous les êtres "
                "vivants. On distingue les cellules procaryotes (sans noyau, "
                "comme les bactéries) et les cellules eucaryotes (avec noyau, "
                "comme les cellules animales et végétales). Chaque cellule "
                "contient une membrane, un cytoplasme et du matériel "
                "génétique. Les organismes unicellulaires sont constitués "
                "d'une seule cellule, tandis que le corps humain en compte "
                "environ 37 000 milliards."
            ),
            'coeur': (
                "Le cœur est un organe musculaire creux qui fonctionne comme "
                "une pompe, assurant la circulation du sang dans tout "
                "l'organisme. Il est divisé en quatre cavités : deux "
                "oreillettes et deux ventricules. Le cœur bat en moyenne "
                "70 fois par minute au repos, soit plus de 100 000 fois "
                "par jour. Il est le centre du système cardiovasculaire et "
                "sa fonction est vitale pour l'apport d'oxygène et de "
                "nutriments aux organes."
            ),
            'systeme immunitaire': (
                "Le système immunitaire est l'ensemble des mécanismes de "
                "défense qui protègent l'organisme contre les infections "
                "(virus, bactéries, parasites) et les cellules anormales "
                "(cancer). Il comprend l'immunité innée (barrières physiques "
                "comme la peau, réaction inflammatoire rapide) et l'immunité "
                "adaptative (lymphocytes T et B, anticorps spécifiques). "
                "La vaccination consiste à entraîner ce système en lui "
                "présentant un agent inoffensif pour qu'il développe une "
                "mémoire immunitaire."
            ),
    
            # ─── CONSCIENCE / ESPRIT ────────────────────────────────────
                'meditation': (
                "La méditation est une pratique mentale qui consiste à "
                "focaliser son attention de manière soutenue, souvent sur "
                "la respiration, les sensations corporelles ou un mantra. "
                "Issue de traditions spirituelles millénaires (bouddhisme, "
                "hindouisme), elle a été validée scientifiquement pour ses "
                "bienfaits : réduction du stress, amélioration de la "
                "concentration, régulation des émotions. Les neurosciences "
                "montrent que la méditation régulière modifie durablement "
                "la structure et le fonctionnement du cerveau."
            ),
            'reve': (
                "Le rêve est une production mentale involontaire survenant "
                "principalement pendant le sommeil paradoxal. Les rêves "
                "peuvent être des scénarios complexes impliquant des images, "
                "des sons, des émotions. Selon les neurosciences, ils "
                "joueraient un rôle dans la consolidation de la mémoire et "
                "la régulation émotionnelle. Freud y voyait la « voie royale "
                "vers l'inconscient », révélant des désirs refoulés."
            ),

            # ─── PHILOSOPHIE ───────────────────────────────────────────
            'philosophie': (
                "La philosophie est la discipline qui questionne les "
                "fondements de la réalité, de la connaissance, de la morale, "
                "de l'existence et du langage. Socrate, Platon et Aristote "
                "en ont posé les bases dans la Grèce antique. Elle se "
                "distingue de la science par sa méthode : le raisonnement "
                "critique et l'argumentation logique plutôt que "
                "l'expérimentation. La philosophie ne prétend pas apporter "
                "des réponses définitives mais apprendre à poser les bonnes "
                "questions."
            ),
            'ethique': (
                "L'éthique est la branche de la philosophie qui s'interroge "
                "sur ce qui est bien, juste et moralement souhaitable. Elle "
                "se distingue de la morale (ensemble de règles) en ce qu'elle "
                "est une réflexion critique sur les principes qui guident "
                "l'action. Les grands courants incluent le déontologisme "
                "(Kant : respecter des règles universelles), l'utilitarisme "
                "(Bentham : maximiser le bien-être collectif) et l'éthique "
                "des vertus (Aristote : cultiver son caractère)."
            ),
            'existence': (
                "L'existence est le fait d'être, de se trouver dans la "
                "réalité. La philosophie existentialiste (Sartre, Camus, "
                "Heidegger) place l'existence avant l'essence : l'être "
                "humain n'a pas de nature prédéfinie, il se construit par "
                "ses choix et ses actes. Cette liberté radicale s'accompagne "
                "d'une responsabilité totale et parfois d'un sentiment "
                "d'absurde face à un monde sans sens préétabli."
            ),

            # ─── MATHS ─────────────────────────────────────────────────
            'nombre d or': (
                "Le nombre d'or, noté φ (phi), vaut environ 1,618. Il "
                "est défini par la relation φ = 1 + 1/φ. Ce nombre "
                "irrationnel apparaît dans la suite de Fibonacci, dans "
                "la géométrie du pentagone régulier et dans de nombreuses "
                "proportions naturelles (coquillages, disposition des "
                "feuilles, galaxies spirales). Depuis l'Antiquité, il "
                "est considéré comme une proportion esthétique idéale "
                "en architecture et en art."
            ),
            'theoreme de pythagore': (
                "Le théorème de Pythagore établit que dans un triangle "
                "rectangle, le carré de l'hypoténuse est égal à la somme "
                "des carrés des deux autres côtés (a² + b² = c²). Découvert "
                "par les Babyloniens bien avant Pythagore (VIe siècle av. "
                "J.-C.), il est l'un des théorèmes les plus fondamentaux "
                "de la géométrie euclidienne. Il a d'innombrables "
                "applications en physique, en ingénierie et en navigation."
            ),

            # ─── ASTRONOMIE / COSMOLOGIE ────────────────────────────────
                'trou noir': (
                "Un trou noir est une région de l'espace-temps où la gravité "
                "est si intense que rien, pas même la lumière, ne peut s'en "
                "échapper. Il se forme lorsqu'une étoile massive s'effondre "
                "en fin de vie. La limite au-delà de laquelle rien ne peut "
                "ressortir s'appelle l'horizon des événements. En 2019, la "
                "première image d'un trou noir a été obtenue par le "
                "télescope Event Horizon, confirmant les prédictions de la "
                "relativité générale."
            ),
            'systeme solaire': (
                "Le système solaire est constitué du Soleil et de l'ensemble "
                "des corps qui gravitent autour de lui : huit planètes "
                "(Mercure, Vénus, Terre, Mars, Jupiter, Saturne, Uranus, "
                "Neptune), leurs lunes, les astéroïdes et les comètes. Il "
                "s'est formé il y a environ 4,6 milliards d'années par "
                "effondrement d'un nuage de gaz et de poussière. La Terre "
                "est la seule planète connue à abriter la vie."
            ),
            'soleil': (
                "Le Soleil est l'étoile au centre du système solaire. C'est "
                "une sphère de plasma composée principalement d'hydrogène "
                "et d'hélium. En son cœur, la fusion nucléaire transforme "
                "l'hydrogène en hélium, libérant une énergie colossale qui "
                "nous parvient sous forme de lumière et de chaleur. Le "
                "Soleil est âgé de 4,6 milliards d'années et en est à "
                "mi-vie. Sans lui, la vie sur Terre serait impossible."
            ),

            # ─── CULTURE ────────────────────────────────────────────────
            'musique': (
                "La musique est l'art de combiner les sons et les silences "
                "dans le temps. Elle repose sur des éléments fondamentaux : "
                "le rythme (durée), la mélodie (succession de notes), "
                "l'harmonie (superposition de notes) et le timbre (couleur "
                "sonore). Présente dans toutes les cultures humaines depuis "
                "la préhistoire, la musique joue un rôle social, rituel, "
                "émotionnel et esthétique. Elle est à la fois un langage "
                "universel et une expression intime de l'identité culturelle."
            ),
            'litterature': (
                "La littérature est l'ensemble des œuvres écrites auxquelles "
                "on reconnaît une valeur esthétique. Elle englobe des genres "
                "multiples : poésie, roman, théâtre, essai. Des œuvres comme "
                "l'Iliade d'Homère, Don Quichotte de Cervantès ou À la "
                "recherche du temps perdu de Proust ont façonné notre "
                "compréhension de la condition humaine. La littérature "
                "est un miroir de la société et un espace d'exploration "
                "de l'imaginaire."
            ),
            'cinema': (
                "Le cinéma est l'art de créer des œuvres par l'image "
                "animée et le son. Né à la fin du XIXe siècle avec les "
                "frères Lumière, il a connu une évolution technique "
                "fulgurante : du muet au parlant, du noir et blanc à la "
                "couleur, de la pellicule au numérique. Art populaire par "
                "excellence, le cinéma est aussi un puissant moyen "
                "d'expression artistique, de divertissement et de "
                "transmission d'idées."
            ),

            # ─── HISTOIRE ───────────────────────────────────────────────
            'revolution francaise': (
                "La Révolution française (1789-1799) est une période de "
                "bouleversements politiques et sociaux majeurs en France. "
                "Elle a renversé la monarchie absolue, aboli les privilèges "
                "féodaux et proclamé les droits de l'homme. La prise de la "
                "Bastille le 14 juillet 1789 en est le symbole. La "
                "Révolution a profondément transformé la société française "
                "et a influencé durablement l'histoire politique mondiale."
            ),
            'seconde guerre mondiale': (
                "La Seconde Guerre mondiale (1939-1945) est le conflit le "
                "plus meurtrier de l'histoire, opposant les Alliés (France, "
                "Royaume-Uni, URSS, États-Unis) aux forces de l'Axe "
                "(Allemagne nazie, Italie fasciste, Japon impérial). Elle "
                "a causé plus de 60 millions de morts, dont 6 millions de "
                "Juifs exterminés dans la Shoah. Elle s'est achevée par "
                "les bombes atomiques sur Hiroshima et Nagasaki et la "
                "création de l'ONU pour préserver la paix."
            ),

            # ─── GÉOGRAPHIE ─────────────────────────────────────────────
            'terre': (
                "La Terre est la troisième planète du système solaire et "
                "la seule connue à abriter la vie. Elle s'est formée il y "
                "a environ 4,6 milliards d'années. Sa surface est couverte "
                "à 71% d'eau, ce qui lui vaut le surnom de planète bleue. "
                "Elle possède un satellite naturel, la Lune, qui stabilise "
                "son axe de rotation et provoque les marées. L'atmosphère "
                "terrestre, riche en oxygène, protège la vie des radiations "
                "solaires nocives."
            ),
            'france': (
                "La France est un pays d'Europe occidentale, membre fondateur "
                "de l'Union européenne. Sa capitale est Paris. Avec une "
                "superficie de 640 000 km², c'est le plus grand pays de "
                "l'UE. La France est une république laïque, démocratique "
                "et sociale, héritière de la Révolution de 1789. Sa culture "
                "a profondément influencé le monde dans les domaines de la "
                "philosophie, de la littérature, de la gastronomie et de "
                "la mode."
            ),

            # ─── SPIRITUALITÉ ───────────────────────────────────────────
            'dieu': (
                "Dieu est le concept d'un être suprême, créateur et "
                "ordonnateur de l'univers dans de nombreuses traditions "
                "religieuses et philosophiques. Dans le monothéisme "
                "(judaïsme, christianisme, islam), Dieu est unique, "
                "transcendant et omniscient. D'autres traditions le "
                "conçoivent différemment : panthéisme (Dieu est l'univers), "
                "déisme (Dieu créateur non interventionniste), polythéisme "
                "(plusieurs dieux). La question de l'existence de Dieu est "
                "au cœur de la philosophie de la religion."
            ),
            'spiritualite': (
                "La spiritualité est la dimension de l'expérience humaine "
                "qui cherche un sens, une connexion à quelque chose de plus "
                "grand que soi. Elle peut être religieuse (liée à une "
                "tradition et des textes sacrés) ou laïque (méditation, "
                "contemplation de la nature). La spiritualité répond à des "
                "besoins humains fondamentaux : trouver un sens à "
                "l'existence, faire face à la souffrance et à la mort, "
                "ressentir un lien avec l'univers."
            ),
            'ame': (
                "L'âme est le principe de vie, de pensée et d'identité "
                "d'un être, distinct du corps matériel selon de nombreuses "
                "traditions. Dans la philosophie de Platon, l'âme est "
                "immatérielle et immortelle. Dans la tradition chrétienne, "
                "elle est créée par Dieu et survit à la mort. Les "
                "neurosciences modernes tendent à expliquer les fonctions "
                "attribuées à l'âme par l'activité cérébrale, mais la "
                "question de son existence reste un débat philosophique "
                "et spirituel."
            ),

            # ─── ÉMOTIONS ───────────────────────────────────────────────
            'amour': (
                "L'amour est un sentiment intense d'affection, d'attachement "
                "et de désir envers une personne, un être vivant ou un idéal. "
                "Les philosophes grecs distinguaient plusieurs formes "
                "d'amour : éros (désir passionné), philia (amitié), agapè "
                "(amour universel et désintéressé). Les neurosciences "
                "montrent que l'amour active des circuits cérébraux de "
                "récompense impliquant la dopamine et l'ocytocine. L'amour "
                "est un thème central dans l'art, la littérature et la "
                "spiritualité de toutes les cultures."
            ),
            'peur': (
                "La peur est une émotion primaire déclenchée par la "
                "perception d'un danger, réel ou imaginaire. Elle active "
                "l'amygdale cérébrale et déclenche la réponse de lutte ou "
                "de fuite : accélération du rythme cardiaque, libération "
                "d'adrénaline, hypervigilance. Essentielle à la survie, "
                "la peur peut devenir pathologique quand elle est excessive "
                "ou irrationnelle (phobies, anxiété généralisée). La "
                "gestion de la peur est un enjeu central de la psychologie."
            ),
            'joie': (
                "La joie est une émotion positive caractérisée par un "
                "sentiment de bien-être, de satisfaction et de plénitude. "
                "Elle est associée à la libération de dopamine et de "
                "sérotonine dans le cerveau. Contrairement au plaisir "
                "(sensation immédiate), la joie est souvent plus durable "
                "et liée au sens que l'on donne à sa vie. Les philosophies "
                "antiques (stoïcisme, épicurisme) et contemporaines "
                "(psychologie positive) cherchent à comprendre comment "
                "cultiver la joie durablement."
            ),

            # ─── SANTÉ ──────────────────────────────────────────────────
            'vaccin': (
                "Un vaccin est une préparation biologique qui stimule le "
                "système immunitaire pour le protéger contre une maladie "
                "infectieuse. Il contient un agent pathogène affaibli ou "
                "inactivé, ou simplement une protéine caractéristique du "
                "virus ou de la bactérie. La vaccination a permis "
                "d'éradiquer la variole et de réduire drastiquement la "
                "mortalité due à la polio, la rougeole et le tétanos. "
                "Elle est l'une des plus grandes avancées de la médecine."
            ),
            'maladie': (
                "Une maladie est une altération de la santé qui perturbe "
                "le fonctionnement normal de l'organisme. Elle peut être "
                "causée par des agents infectieux (virus, bactéries, "
                "parasites), des facteurs génétiques, environnementaux "
                "ou liés au mode de vie. La médecine distingue les maladies "
                "aiguës (apparition brutale, durée limitée) et chroniques "
                "(évolution lente, durable). La prévention, le diagnostic "
                "précoce et le traitement sont les trois piliers de la "
                "lutte contre les maladies."
            ),
            'medecine': (
                "La médecine est la science et l'art de prévenir, "
                "diagnostiquer et traiter les maladies. Elle puise ses "
                "fondements dans les sciences biologiques (anatomie, "
                "physiologie, pharmacologie) et s'appuie sur une démarche "
                "clinique rigoureuse : observation, diagnostic, pronostic "
                "et thérapeutique. Depuis Hippocrate, la médecine a "
                "considérablement évolué, intégrant les avancées de la "
                "génétique, de l'imagerie médicale et de l'intelligence "
                "artificielle."
            ),

            # ─── TECHNOLOGIE ────────────────────────────────────────────
            'internet': (
                "Internet est un réseau mondial d'ordinateurs interconnectés "
                "qui permet l'échange d'informations à l'échelle planétaire. "
                "Né dans les années 1960 comme projet militaire américain "
                "(ARPANET), il s'est démocratisé dans les années 1990 avec "
                "le World Wide Web. Internet a révolutionné la communication, "
                "le commerce, l'éducation et la culture. Aujourd'hui, plus "
                "de 5 milliards de personnes y ont accès, ce qui en fait "
                "l'une des infrastructures les plus importantes de "
                "l'humanité."
            ),
                'ordinateur': (
                "Un ordinateur est une machine électronique programmable "
                "capable de traiter des informations selon des instructions "
                "prédéfinies. Il repose sur l'architecture de von Neumann : "
                "une unité de calcul (processeur), une mémoire et des "
                "périphériques d'entrée-sortie. Le premier ordinateur "
                "moderne, l'ENIAC, date de 1945. Depuis, la puissance de "
                "calcul a été multipliée par des milliards, rendant possible "
                "la révolution numérique."
            ),

            # ─── ÉCONOMIE ───────────────────────────────────────────────
            'economie': (
                "L'économie est la science qui étudie la production, la "
                "distribution et la consommation des biens et services "
                "dans une société. Elle se divise en microéconomie "
                "(comportement des agents individuels : ménages, "
                "entreprises) et macroéconomie (phénomènes globaux : "
                "croissance, inflation, chômage). Adam Smith, avec La "
                "Richesse des nations (1776), est considéré comme le "
                "père de l'économie moderne. Les politiques économiques "
                "visent à concilier croissance, emploi et stabilité."
            ),
            'monnaie': (
                "La monnaie est un instrument d'échange accepté par une "
                "communauté pour faciliter les transactions économiques. "
                "Elle remplit trois fonctions : unité de compte (mesure "
                "de la valeur), moyen de paiement (intermédiaire des "
                "échanges) et réserve de valeur (conservation du pouvoir "
                "d'achat). Elle a évolué du troc aux pièces métalliques, "
                "puis aux billets, à la monnaie scripturale (comptes "
                "bancaires) et aujourd'hui aux cryptomonnaies (Bitcoin)."
            ),

            # ─── LANGAGE / COMMUNICATION ────────────────────────────────
            'langage': (
                "Le langage est la capacité de communiquer des idées, des "
                "émotions et des informations par un système de signes. "
                "Spécificité humaine (bien que certains animaux aient des "
                "formes de communication élaborées), le langage articulé "
                "repose sur la double articulation : les phonèmes (sons) "
                "se combinent en morphèmes (unités de sens). On estime qu'il "
                "existe environ 7 000 langues dans le monde. Le langage "
                "structure notre pensée et notre rapport au réel."
            ),
            'ecriture': (
                "L'écriture est un système de représentation graphique "
                "d'une langue. Apparue indépendamment en Mésopotamie "
                "(écriture cunéiforme, vers 3400 av. J.-C.), en Égypte "
                "(hiéroglyphes) et en Chine, elle a transformé les "
                "sociétés humaines en permettant la conservation et la "
                "transmission du savoir au-delà de la mémoire orale. "
                "L'invention de l'alphabet par les Phéniciens puis "
                "l'imprimerie par Gutenberg ont démocratisé l'accès "
                "à l'écrit."
            ),

            # ─── ART ────────────────────────────────────────────────────
            'peinture': (
                "La peinture est l'art de représenter des images sur une "
                "surface en y appliquant des pigments. Les premières "
                "peintures connues sont les fresques rupestres de la "
                "préhistoire (Lascaux, -17 000 ans). La peinture a "
                "traversé de nombreux courants : classicisme, romantisme, "
                "impressionnisme, cubisme, art abstrait. Des artistes "
                "comme Léonard de Vinci, Rembrandt, Van Gogh ou Picasso "
                "ont chacun révolutionné la manière de voir et de "
                "représenter le monde."
            ),

            # ─── SOCIÉTÉ ────────────────────────────────────────────────
                    'justice': (
                "La justice est le principe moral et institutionnel qui "
                "vise à rendre à chacun ce qui lui est dû. La justice "
                "distributive (Aristote) concerne la répartition équitable "
                "des biens et des honneurs. La justice corrective répare "
                "les torts causés. Le système judiciaire (tribunaux, juges, "
                "lois) est l'institution chargée d'appliquer la justice. "
                "L'équilibre entre justice et efficacité est un défi "
                "permanent des sociétés."
            ),

            # ─── NATURE ─────────────────────────────────────────────────
            'eau': (
                "L'eau est une molécule composée de deux atomes d'hydrogène "
                "et d'un atome d'oxygène (H₂O). Elle est indispensable à "
                "toute forme de vie connue. Ses propriétés sont "
                "exceptionnelles : c'est un excellent solvant, sa densité "
                "maximale est à 4°C (la glace flotte), elle a une forte "
                "capacité thermique. Sur Terre, 97% de l'eau est salée "
                "(océans) et seulement 3% est douce. Le cycle de l'eau "
                "fait circuler cette ressource en permanence."
            ),
            'air': (
                "L'air est le mélange de gaz qui constitue l'atmosphère "
                "terrestre. Il est composé principalement de diazote (78%) "
                "et de dioxygène (21%), avec des traces d'argon, de "
                "dioxyde de carbone et d'autres gaz. L'oxygène de l'air "
                "est essentiel à la respiration de la plupart des êtres "
                "vivants. La pollution atmosphérique, causée par les "
                "activités humaines, dégrade la qualité de l'air et "
                "contribue au changement climatique."
            ),
            'feu': (
                "Le feu est la manifestation visible d'une réaction de "
                "combustion : une substance (combustible) réagit avec "
                "l'oxygène (comburant) en dégageant de la chaleur et de "
                "la lumière. La domestication du feu par l'homme, il y a "
                "environ 400 000 ans, a été une révolution : cuisson des "
                "aliments, chauffage, protection contre les prédateurs. "
                "Le feu reste un symbole puissant associé à la connaissance "
                "(Prométhée), à la purification et à la destruction."
            ),

            # ─── TEMPS ──────────────────────────────────────────────────
            'temps': (
                "Le temps est la dimension dans laquelle les événements "
                "se succèdent. En physique classique (Newton), le temps "
                "est absolu et universel. En relativité (Einstein), il "
                "est relatif : il s'écoule différemment selon la vitesse "
                "et la gravité. En philosophie, le temps est une énigme : "
                "« Qu'est-ce que le temps ? Si personne ne me le demande, "
                "je le sais ; si je veux l'expliquer, je ne le sais plus » "
                "(Saint Augustin). La flèche du temps, liée à "
                "l'augmentation de l'entropie, explique pourquoi nous nous "
                "souvenons du passé mais pas du futur."
            ),
            'espace': (
                "L'espace est l'étendue tridimensionnelle dans laquelle "
                "les objets existent et se déplacent. En physique classique, "
                "l'espace est un contenant absolu (Newton). En relativité "
                "générale (Einstein), l'espace et le temps forment une "
                "entité unique, l'espace-temps, qui se courbe en présence "
                "de masse. L'exploration spatiale, débutée en 1957 avec "
                "Spoutnik, a permis à l'humanité de poser le pied sur la "
                "Lune (1969) et d'explorer le système solaire."
            ),

            # ═══════════════════════════════════════════════════════════════
            # EXTENSION — 140+ sujets supplémentaires
            # ═══════════════════════════════════════════════════════════════

            # ─── PHYSIQUE (suite) ────────────────────────────────────────
            'force': (
                "Une force est une interaction qui modifie le mouvement d'un "
                "corps ou le déforme. En physique classique (Newton), la "
                "force est définie par F = ma : elle est proportionnelle à "
                "la masse et à l'accélération. Il existe quatre forces "
                "fondamentales dans l'univers : la gravitation, "
                "l'électromagnétisme, l'interaction forte (qui lie les "
                "noyaux atomiques) et l'interaction faible (responsable "
                "de la radioactivité)."
            ),
            'particule': (
                "Une particule est le plus petit constituant élémentaire "
                "de la matière ou d'une interaction. Les particules "
                "élémentaires incluent les quarks (constituants des protons "
                "et neutrons), les leptons (comme l'électron), et les "
                "bosons (comme le photon, médiateur de la force "
                "électromagnétique). Le Modèle Standard de la physique "
                "des particules décrit 17 particules fondamentales."
            ),
            'matiere': (
                "La matière est tout ce qui possède une masse et occupe "
                "un volume. Elle est composée d'atomes, eux-mêmes "
                "constitués de protons, neutrons et électrons. La matière "
                "existe sous quatre états principaux : solide, liquide, "
                "gazeux et plasma. L'antimatière, composée d'antiparticules, "
                "s'annihile au contact de la matière en libérant de "
                "l'énergie pure selon E = mc²."
            ),
            'magnetisme': (
                "Le magnétisme est la force d'attraction ou de répulsion "
                "qui s'exerce entre des matériaux aimantés ou des charges "
                "électriques en mouvement. Il est produit par le mouvement "
                "des électrons dans les atomes. Le champ magnétique "
                "terrestre protège notre planète du vent solaire. "
                "L'électroaimant, inventé au XIXe siècle, est à la base "
                "des moteurs électriques et des générateurs."
            ),
            'electricite': (
                "L'électricité est un phénomène physique lié au "
                "déplacement de charges électriques, généralement des "
                "électrons. Elle peut être statique (accumulation de "
                "charges) ou dynamique (courant électrique). Découverte "
                "progressivement par Gilbert, Franklin, Volta et Faraday, "
                "elle est devenue la forme d'énergie la plus utilisée "
                "dans le monde moderne, alimentant l'industrie, les "
                "transports et les technologies numériques."
            ),
            'son': (
                "Le son est une onde mécanique qui se propage dans un "
                "milieu matériel (air, eau, solide) par compression et "
                "dilatation successives. Il ne peut pas se propager dans "
                "le vide. Sa vitesse dans l'air est d'environ 340 m/s. "
                "Le son est caractérisé par sa fréquence (hauteur, en "
                "hertz), son amplitude (volume) et son timbre (forme "
                "d'onde). L'oreille humaine perçoit les fréquences "
                "entre 20 Hz et 20 000 Hz."
            ),
            'chaleur': (
                "La chaleur est un transfert d'énergie thermique entre "
                "deux systèmes à des températures différentes. Elle se "
                "propage par conduction (contact direct), convection "
                "(mouvement de fluide) et rayonnement (ondes "
                "électromagnétiques). La chaleur est mesurée en joules "
                "et ne doit pas être confondue avec la température, qui "
                "mesure l'agitation moléculaire moyenne."
            ),
            'pression': (
                "La pression est la force exercée par unité de surface "
                "(P = F/S). Elle se mesure en pascals (Pa). La pression "
                "atmosphérique au niveau de la mer est d'environ 101 325 "
                "Pa. Dans un fluide, la pression augmente avec la "
                "profondeur. Le principe de Pascal établit qu'une "
                "variation de pression en un point d'un fluide se "
                "transmet intégralement à tout le fluide."
            ),

            # ─── CHIMIE ──────────────────────────────────────────────────
            'chimie': (
                "La chimie est la science qui étudie la composition, "
                "la structure, les propriétés et les transformations de "
                "la matière. Elle se divise en chimie organique (composés "
                "du carbone), inorganique, physique et analytique. "
                "Lavoisier, considéré comme le père de la chimie moderne, "
                "a établi la loi de conservation de la masse. La chimie "
                "est au cœur de l'industrie pharmaceutique, des matériaux "
                "et de l'énergie."
            ),
            'reaction chimique': (
                "Une réaction chimique est une transformation au cours "
                "de laquelle des substances (réactifs) se transforment "
                "en de nouvelles substances (produits) par rupture et "
                "formation de liaisons chimiques. Les réactions obéissent "
                "à la conservation de la masse et de l'énergie. Elles "
                "peuvent être classées en synthèse, décomposition, "
                "combustion, oxydoréduction ou précipitation."
            ),

            # ─── BIOLOGIE (suite) ────────────────────────────────────────
            'corps humain': (
                "Le corps humain est l'ensemble des structures biologiques "
                "qui constituent un être humain. Il est composé d'environ "
                "37 000 milliards de cellules organisées en tissus, "
                "organes et systèmes. Les principaux systèmes incluent "
                "le système nerveux (cerveau, nerfs), cardiovasculaire "
                "(cœur, vaisseaux), respiratoire (poumons), digestif "
                "(estomac, intestins), musculaire et squelettique."
            ),
            'respiration': (
                "La respiration est le processus par lequel les êtres "
                "vivants absorbent l'oxygène et rejettent le dioxyde de "
                "carbone. Chez l'humain, l'air entre par le nez ou la "
                "bouche, passe par la trachée, les bronches, et atteint "
                "les alvéoles pulmonaires où les échanges gazeux avec "
                "le sang ont lieu. La respiration cellulaire utilise "
                "l'oxygène pour produire de l'énergie (ATP)."
            ),
            'squelette': (
                "Le squelette humain est constitué de 206 os qui "
                "soutiennent le corps, protègent les organes vitaux "
                "(crâne pour le cerveau, cage thoracique pour le cœur "
                "et les poumons) et permettent le mouvement grâce aux "
                "articulations. Les os sont des tissus vivants qui se "
                "renouvellent constamment. Ils stockent le calcium et "
                "produisent les cellules sanguines dans la moelle osseuse."
            ),
            'digestion': (
                "La digestion est le processus de transformation des "
                "aliments en nutriments assimilables par l'organisme. "
                "Elle commence dans la bouche (mastication, salive), se "
                "poursuit dans l'estomac (acides, enzymes) et s'achève "
                "dans l'intestin grêle où les nutriments passent dans "
                "le sang. Le gros intestin absorbe l'eau et élimine "
                "les déchets."
            ),
            'reproduction': (
                "La reproduction est le processus biologique par lequel "
                "les êtres vivants engendrent une descendance. Elle peut "
                "être asexuée (un seul parent, clone génétique) comme "
                "chez les bactéries, ou sexuée (deux parents, brassage "
                "génétique) comme chez la plupart des animaux. La "
                "reproduction sexuée favorise la diversité génétique, "
                "essentielle à l'évolution."
            ),
            'bacterie': (
                "Les bactéries sont des micro-organismes unicellulaires "
                "procaryotes (sans noyau). Elles sont parmi les plus "
                "anciennes formes de vie sur Terre (3,5 milliards "
                "d'années). Certaines sont pathogènes (causant des "
                "maladies), d'autres sont bénéfiques (flore intestinale, "
                "fermentation). Elles se reproduisent par division "
                "cellulaire et peuvent échanger du matériel génétique."
            ),
            'virus': (
                "Un virus est un agent infectieux microscopique qui ne "
                "peut se reproduire qu'en infectant une cellule hôte. "
                "Il est constitué d'un matériel génétique (ADN ou ARN) "
                "entouré d'une capside protéique. Les virus sont à la "
                "limite du vivant : ils ne possèdent pas de métabolisme "
                "propre. La vaccination et les antiviraux sont les "
                "principales défenses contre les infections virales."
            ),
            'champignon': (
                "Les champignons (Fungi) forment un règne distinct des "
                "plantes et des animaux. Ils sont hétérotrophes (ils se "
                "nourrissent de matière organique) et se reproduisent "
                "par des spores. Certains sont comestibles (champignons "
                "de Paris, cèpes), d'autres toxiques (amanite phalloïde). "
                "Ils jouent un rôle écologique crucial comme décomposeurs."
            ),

            # ─── ÉCOLOGIE ────────────────────────────────────────────────
            'ecosysteme': (
                "Un écosystème est un ensemble formé par une communauté "
                "d'êtres vivants (biocénose) et leur environnement "
                "physique (biotope), en interaction constante. Les "
                "écosystèmes peuvent être terrestres (forêts, déserts) "
                "ou aquatiques (océans, lacs). Les flux d'énergie "
                "(chaînes alimentaires) et les cycles de matière (eau, "
                "carbone, azote) y sont essentiels."
            ),
            'biodiversite': (
                "La biodiversité désigne la variété des formes de vie "
                "sur Terre, à tous les niveaux : génétique (diversité "
                "des gènes), spécifique (diversité des espèces) et "
                "écosystémique (diversité des habitats). Elle est menacée "
                "par la destruction des habitats, la pollution, le "
                "changement climatique et la surexploitation. Sa "
                "préservation est un enjeu mondial."
            ),
            'climat': (
                "Le climat est l'ensemble des conditions météorologiques "
                "moyennes (température, précipitations, vent) sur une "
                "longue période dans une région donnée. Il se distingue "
                "de la météo (conditions à court terme). Le système "
                "climatique terrestre est influencé par l'effet de serre, "
                "les courants océaniques, l'activité solaire et les "
                "activités humaines."
            ),

            # ─── MATHÉMATIQUES ────────────────────────────────────────────
            'algebre': (
                "L'algèbre est la branche des mathématiques qui étudie "
                "les structures, les relations et les quantités en "
                "utilisant des symboles et des lettres pour représenter "
                "des nombres. Elle permet de résoudre des équations, "
                "de modéliser des problèmes et de généraliser des motifs "
                "arithmétiques. Al-Khwarizmi (IXe siècle) en est le "
                "fondateur ; le mot 'algorithme' dérive de son nom."
            ),
            'geometrie': (
                "La géométrie est l'étude des formes, des tailles, des "
                "positions et des propriétés de l'espace. Née dans "
                "l'Égypte antique pour mesurer les terres, elle a été "
                "formalisée par Euclide (~300 av. J.-C.). On distingue "
                "la géométrie plane (2D), la géométrie dans l'espace "
                "(3D), et les géométries non-euclidiennes (courbes)."
            ),
            'calcul': (
                "Le calcul (ou analyse) est la branche des mathématiques "
                "qui étudie les variations (dérivées), les accumulations "
                "(intégrales) et les limites. Développé indépendamment "
                "par Newton et Leibniz au XVIIe siècle, il est l'outil "
                "fondamental de la physique, de l'ingénierie et de "
                "l'économie pour modéliser des phénomènes continus."
            ),
            'probabilite': (
                "La probabilité mesure la chance qu'un événement se "
                "produise, sur une échelle de 0 (impossible) à 1 "
                "(certain). Elle est née de l'étude des jeux de hasard "
                "(Pascal, Fermat, XVIIe siècle) et est devenue "
                "essentielle en statistique, en physique quantique, "
                "en finance et en intelligence artificielle."
            ),
            'statistique': (
                "La statistique est la science de la collecte, de "
                "l'analyse et de l'interprétation des données. Elle "
                "se divise en statistique descriptive (résumer les "
                "données) et statistique inférentielle (tirer des "
                "conclusions). La moyenne, la médiane, l'écart-type "
                "et la corrélation sont des concepts fondamentaux."
            ),
            'logique': (
                "La logique est l'étude des principes du raisonnement "
                "valide. Aristote en a posé les bases avec le syllogisme. "
                "La logique formelle moderne (Boole, Frege, Russell) "
                "utilise des symboles et des règles d'inférence. Elle "
                "est essentielle en mathématiques, en informatique "
                "(circuits logiques) et en philosophie."
            ),
            'fractale': (
                "Une fractale est une figure géométrique dont la "
                "structure se répète à différentes échelles "
                "(autosimilarité). Décrites par Mandelbrot dans les "
                "années 1970, les fractales modélisent des phénomènes "
                "naturels irréguliers : côtes maritimes, nuages, "
                "ramifications des arbres, vaisseaux sanguins, galaxies."
            ),
            'zero': (
                "Le zéro est un concept mathématique fondamental "
                "représentant l'absence de quantité. Inventé "
                "indépendamment par les Babyloniens, les Mayas et "
                "les Indiens, il a été transmis à l'Occident via les "
                "mathématiciens arabes. Le zéro joue un double rôle : "
                "nombre (cardinal du vide) et chiffre (notation "
                "positionnelle)."
            ),
            'infini': (
                "L'infini est le concept de ce qui n'a pas de limite "
                "ou de fin. En mathématiques, Cantor a montré qu'il "
                "existe plusieurs tailles d'infini (infinis dénombrable "
                "et continu). Le symbole ∞ a été introduit par Wallis "
                "en 1655. L'infini apparaît en calcul (limites), en "
                "cosmologie (univers infini ?) et en philosophie."
            ),

            # ─── ASTRONOMIE / ESPACE ─────────────────────────────────────
            'lune': (
                "La Lune est l'unique satellite naturel de la Terre, "
                "situé à environ 384 400 km. Elle s'est formée il y a "
                "4,5 milliards d'années, probablement suite à une "
                "collision entre la Terre et un corps de la taille de "
                "Mars. Elle provoque les marées et stabilise l'axe de "
                "rotation terrestre. Le 20 juillet 1969, Neil Armstrong "
                "fut le premier homme à y poser le pied."
            ),
            'mars': (
                "Mars est la quatrième planète du système solaire, "
                "surnommée la planète rouge à cause de l'oxyde de fer "
                "à sa surface. Elle possède le plus haut volcan du "
                "système solaire (Olympus Mons, 21 km) et des calottes "
                "polaires de glace. La NASA y envoie des rovers depuis "
                "1997. Mars est la cible prioritaire des futures "
                "missions habitées."
            ),
            'jupiter': (
                "Jupiter est la plus grande planète du système solaire "
                "(318 fois la masse de la Terre). C'est une géante "
                "gazeuse composée principalement d'hydrogène et "
                "d'hélium. Sa Grande Tache Rouge est une tempête "
                "anticyclonique plus grande que la Terre, active "
                "depuis au moins 350 ans. Jupiter possède 95 lunes "
                "connues, dont Ganymède (la plus grande du système solaire)."
            ),
            'voie lactee': (
                "La Voie lactée est la galaxie spirale qui abrite notre "
                "système solaire. Elle contient entre 100 et 400 "
                "milliards d'étoiles et s'étend sur environ 100 000 "
                "années-lumière de diamètre. Notre Soleil se trouve "
                "dans le bras d'Orion, à environ 27 000 années-lumière "
                "du centre galactique. La Voie lactée fait partie du "
                "Groupe Local de galaxies."
            ),
            'exoplanete': (
                "Une exoplanète est une planète située en dehors du "
                "système solaire, en orbite autour d'une autre étoile. "
                "La première a été confirmée en 1995 (51 Pegasi b). "
                "Depuis, plus de 5 500 exoplanètes ont été découvertes. "
                "Certaines se trouvent dans la 'zone habitable' de leur "
                "étoile, où l'eau liquide pourrait exister en surface."
            ),

            # ─── MÉDECINE / SANTÉ ────────────────────────────────────────
            'cancer': (
                "Le cancer est une maladie caractérisée par une "
                "prolifération anormale et incontrôlée de cellules. "
                "Il peut toucher presque tous les tissus du corps. "
                "Les causes incluent des mutations génétiques, "
                "l'exposition à des carcinogènes (tabac, alcool, "
                "UV) et certains virus. Les traitements incluent "
                "la chirurgie, la chimiothérapie, la radiothérapie "
                "et l'immunothérapie."
            ),
            'diabete': (
                "Le diabète est une maladie chronique caractérisée "
                "par un excès de sucre dans le sang (hyperglycémie). "
                "Le type 1 est auto-immun (le pancréas ne produit "
                "plus d'insuline). Le type 2, le plus fréquent, est "
                "lié à une résistance à l'insuline, souvent associée "
                "au surpoids et à la sédentarité. Il touche plus de "
                "500 millions de personnes dans le monde."
            ),
            'coeur humain': (
                "Le cœur humain est un organe musculaire creux divisé "
                "en quatre cavités : deux oreillettes et deux "
                "ventricules. Il bat en moyenne 70 fois par minute au "
                "repos et pompe environ 5 litres de sang par minute. "
                "Les maladies cardiovasculaires (infarctus, AVC) sont "
                "la première cause de mortalité dans le monde."
            ),
            'sommeil': (
                "Le sommeil est un état physiologique de repos "
                "caractérisé par une diminution de la conscience et "
                "de l'activité motrice. Il alterne des phases de "
                "sommeil lent (réparateur) et de sommeil paradoxal "
                "(rêves). Un adulte a besoin de 7 à 9 heures de "
                "sommeil par nuit. Le sommeil est essentiel à la "
                "consolidation de la mémoire et à la régénération "
                "cellulaire."
            ),
            'nutrition': (
                "La nutrition est l'ensemble des processus par lesquels "
                "l'organisme utilise les aliments pour fonctionner. "
                "Les nutriments essentiels incluent les glucides "
                "(énergie), les lipides (réserve), les protéines "
                "(construction), les vitamines et les minéraux "
                "(régulation). Une alimentation équilibrée est "
                "fondamentale pour la santé et la prévention des "
                "maladies chroniques."
            ),

            # ─── TECHNOLOGIE ─────────────────────────────────────────────
            'telephone': (
                "Le téléphone est un appareil de communication qui "
                "permet de transmettre la voix à distance. Alexander "
                "Graham Bell a déposé le premier brevet en 1876. Il "
                "a évolué du téléphone fixe au mobile (années 1980), "
                "puis au smartphone (2007, iPhone) qui intègre "
                "Internet, appareil photo, GPS et applications."
            ),
            'robot': (
                "Un robot est une machine programmable capable "
                "d'exécuter des tâches de manière autonome ou "
                "semi-autonome. Le mot vient du tchèque 'robota' "
                "(travail forcé), inventé par Karel Čapek en 1920. "
                "Les robots industriels révolutionnent la "
                "manufacture ; les robots humanoïdes et les drones "
                "autonomes ouvrent de nouvelles frontières."
            ),
            'energie nucleaire': (
                "L'énergie nucléaire provient de la fission des atomes "
                "lourds (uranium, plutonium) ou de la fusion des atomes "
                "légers (hydrogène). La fission est utilisée dans les "
                "centrales nucléaires pour produire de l'électricité "
                "(10% de la production mondiale). La fusion, qui "
                "alimente le Soleil, promet une énergie propre et "
                "illimitée mais n'est pas encore maîtrisée."
            ),
            'energie renouvelable': (
                "Les énergies renouvelables sont issues de sources "
                "naturelles qui se renouvellent à l'échelle humaine : "
                "solaire (panneaux photovoltaïques), éolienne "
                "(turbines), hydraulique (barrages), géothermique "
                "(chaleur terrestre) et biomasse. Elles sont "
                "essentielles à la transition énergétique pour "
                "réduire les émissions de gaz à effet de serre."
            ),
            'imprimante 3d': (
                "L'impression 3D est une technique de fabrication "
                "additive qui construit un objet couche par couche "
                "à partir d'un modèle numérique. Elle utilise des "
                "matériaux variés : plastique, résine, métal, béton. "
                "Elle permet le prototypage rapide, la personnalisation "
                "de masse (prothèses, implants) et la construction de "
                "bâtiments. La bio-impression 3D vise à créer des "
                "tissus vivants."
            ),
            'blockchain': (
                "La blockchain (chaîne de blocs) est une technologie "
                "de registre distribué et décentralisé où les "
                "transactions sont enregistrées de manière immuable "
                "et transparente. Chaque bloc contient un ensemble de "
                "transactions validées et est lié au bloc précédent "
                "par un hash cryptographique. Le Bitcoin (2009) en "
                "est la première application majeure."
            ),

            # ─── ÉCONOMIE / FINANCE ──────────────────────────────────────
            'capitalisme': (
                "Le capitalisme est un système économique fondé sur "
                "la propriété privée des moyens de production, la "
                "recherche du profit et la libre concurrence sur les "
                "marchés. Il a émergé en Europe à partir du XVIe "
                "siècle. Adam Smith en a théorisé les principes dans "
                "'La Richesse des nations' (1776). Le capitalisme a "
                "généré une croissance sans précédent mais aussi des "
                "inégalités."
            ),
            'marche': (
                "Un marché est le lieu réel ou virtuel où se "
                "rencontrent l'offre (vendeurs) et la demande "
                "(acheteurs) pour échanger des biens, des services "
                "ou des actifs financiers. Le prix d'équilibre se "
                "fixe au point où l'offre égale la demande. Les "
                "marchés peuvent être concurrentiels, monopolistiques "
                "ou oligopolistiques."
            ),
            'inflation': (
                "L'inflation est la hausse générale et durable des "
                "prix dans une économie. Elle est mesurée par l'indice "
                "des prix à la consommation (IPC). Une inflation "
                "modérée (2-3%) est considérée comme saine. "
                "L'hyperinflation (comme en Allemagne en 1923 ou au "
                "Zimbabwe en 2008) détruit la valeur de la monnaie. "
                "Les banques centrales la contrôlent via les taux "
                "d'intérêt."
            ),
            'chomage': (
                "Le chômage désigne la situation des personnes en "
                "âge de travailler, sans emploi et en recherche "
                "active d'un emploi. Il est mesuré par le taux de "
                "chômage (chômeurs / population active). Ses causes "
                "incluent les cycles économiques, les mutations "
                "technologiques et l'inadéquation des compétences. "
                "Il a des conséquences sociales et psychologiques "
                "importantes."
            ),
            'pib': (
                "Le PIB (Produit Intérieur Brut) est la valeur totale "
                "des biens et services produits dans un pays pendant "
                "une année. Il mesure la richesse créée et la "
                "croissance économique. Le PIB par habitant donne "
                "une indication du niveau de vie moyen. Ses limites "
                "incluent l'absence de mesure du bien-être, des "
                "inégalités et de l'impact environnemental."
            ),

            # ─── PSYCHOLOGIE ─────────────────────────────────────────────
            'psychologie': (
                "La psychologie est la science qui étudie les "
                "comportements, les processus mentaux et les émotions "
                "humains. Elle englobe la psychologie clinique "
                "(thérapies), cognitive (mémoire, attention), sociale "
                "(interactions), développementale (enfance à "
                "vieillesse) et neuropsychologie (lien cerveau-"
                "comportement). Freud, Piaget et Skinner en sont des "
                "figures majeures."
            ),
            'inconscient': (
                "L'inconscient désigne l'ensemble des processus "
                "mentaux qui échappent à la conscience. Freud en a "
                "fait le pilier de la psychanalyse : il contiendrait "
                "les pulsions, les souvenirs refoulés et les désirs "
                "inavoués. Les neurosciences modernes confirment que "
                "la plupart des processus cérébraux sont inconscients."
            ),
            'memoire': (
                "La mémoire est la capacité de stocker, conserver et "
                "restituer des informations. On distingue la mémoire "
                "sensorielle (très brève), la mémoire à court terme "
                "(de travail) et la mémoire à long terme (sémantique, "
                "épisodique, procédurale). L'hippocampe joue un rôle "
                "clé dans la consolidation. La mémoire est plastique "
                "et peut être améliorée par l'entraînement."
            ),
            'intelligence': (
                "L'intelligence est la capacité de comprendre, "
                "d'apprendre, de raisonner et de s'adapter à des "
                "situations nouvelles. Elle n'est pas unique : "
                "Gardner propose 8 types d'intelligence (linguistique, "
                "logique, spatiale, musicale, corporelle, "
                "interpersonnelle, intrapersonnelle, naturaliste). "
                "Le QI (quotient intellectuel) en est une mesure "
                "partielle et controversée."
            ),
            'emotion': (
                "Une émotion est une réaction affective brève et "
                "intense à un stimulus, impliquant des composantes "
                "physiologiques (rythme cardiaque), expressives "
                "(visage) et subjectives (ressenti). Les émotions "
                "de base incluent la joie, la tristesse, la peur, "
                "la colère, la surprise et le dégoût. Elles guident "
                "la prise de décision et les relations sociales."
            ),
            'stress': (
                "Le stress est la réponse de l'organisme à une "
                "demande d'adaptation. Il active le système nerveux "
                "sympathique (adrénaline, cortisol). Un stress aigu "
                "peut améliorer la performance ; un stress chronique "
                "est néfaste (anxiété, dépression, maladies "
                "cardiovasculaires). La méditation, l'exercice et "
                "le sommeil aident à le réguler."
            ),
            'depression': (
                "La dépression est un trouble mental caractérisé par "
                "une tristesse persistante, une perte d'intérêt et "
                "une fatigue chronique. Elle touche environ 5% de la "
                "population mondiale. Ses causes sont multifactorielles "
                "(génétique, biochimie, environnement, psychologie). "
                "Elle se traite par psychothérapie et/ou antidépresseurs."
            ),

            # ─── LINGUISTIQUE ─────────────────────────────────────────────
            'grammaire': (
                "La grammaire est l'ensemble des règles qui régissent "
                "la structure d'une langue : morphologie (forme des "
                "mots), syntaxe (ordre des mots) et phonologie (sons). "
                "Chaque langue a sa grammaire propre. La grammaire "
                "française distingue le genre (masculin/féminin), le "
                "nombre (singulier/pluriel) et la conjugaison des "
                "verbes."
            ),
            'linguistique': (
                "La linguistique est la science qui étudie le langage "
                "humain dans toutes ses dimensions : phonétique (sons), "
                "sémantique (sens), pragmatique (usage), sociolinguistique "
                "(contexte social). Saussure en a posé les fondements "
                "modernes avec la distinction signifiant/signifié. "
                "Chomsky a révolutionné le domaine avec la grammaire "
                "générative."
            ),

            # ─── ART (suite) ──────────────────────────────────────────────
            'art': (
                "L'art est l'expression créative de l'être humain, "
                "visant à produire une expérience esthétique, "
                "émotionnelle ou intellectuelle. Il englobe les arts "
                "visuels (peinture, sculpture), les arts de la scène "
                "(théâtre, danse), la musique et la littérature. "
                "L'art est présent dans toutes les cultures depuis "
                "la préhistoire (Lascaux, -17 000 ans)."
            ),
            'sculpture': (
                "La sculpture est l'art de créer des formes en trois "
                "dimensions par modelage, taille, assemblage ou "
                "moulage. Michel-Ange, Rodin et Brancusi en sont des "
                "maîtres. Les matériaux incluent la pierre (marbre), "
                "le métal (bronze), le bois et les matériaux "
                "contemporains (plastique, acier)."
            ),
            'architecture': (
                "L'architecture est l'art et la technique de concevoir "
                "et construire des bâtiments. Elle répond à trois "
                "principes (Vitruve) : solidité (firmitas), utilité "
                "(utilitas) et beauté (venustas). Les grands styles "
                "incluent le gothique (cathédrales), le classique, "
                "le baroque, le modernisme et l'architecture durable."
            ),
            'danse': (
                "La danse est l'art du mouvement corporel, souvent "
                "rythmé par la musique. Pratique universelle depuis "
                "la préhistoire, elle peut être rituelle, sociale "
                "ou artistique. Les styles incluent le ballet "
                "classique, la danse contemporaine, le hip-hop, "
                "les danses traditionnelles et le tango."
            ),
            'theatre': (
                "Le théâtre est l'art de représenter une action "
                "dramatique devant un public par des acteurs. Né "
                "dans la Grèce antique (Eschyle, Sophocle, Euripide), "
                "il a évolué à travers Shakespeare, Molière, Brecht "
                "et Beckett. Le théâtre mêle texte, jeu, mise en "
                "scène, décors et interaction avec le public."
            ),
            'photographie': (
                "La photographie est l'art et la technique de "
                "capturer la lumière pour créer des images durables. "
                "Inventée par Niépce et Daguerre au XIXe siècle, "
                "elle est passée de l'argentique au numérique. "
                "La photographie est à la fois un outil documentaire, "
                "artistique et scientifique."
            ),

            # ─── HISTOIRE ────────────────────────────────────────────────
            'prehistoire': (
                "La Préhistoire est la période de l'histoire humaine "
                "antérieure à l'invention de l'écriture (vers 3400 "
                "av. J.-C.). Elle couvre le Paléolithique (pierre "
                "taillée, chasseurs-cueilleurs), le Néolithique "
                "(agriculture, sédentarisation, pierre polie) et "
                "l'Âge des métaux (cuivre, bronze, fer). Lascaux "
                "et Stonehenge en sont des témoignages."
            ),
            'antiquite': (
                "L'Antiquité est la période qui va de l'invention de "
                "l'écriture (3400 av. J.-C.) à la chute de l'Empire "
                "romain d'Occident (476 ap. J.-C.). Elle englobe les "
                "civilisations mésopotamienne, égyptienne, grecque, "
                "romaine, perse, chinoise et indienne. La démocratie, "
                "la philosophie et le droit y prennent racine."
            ),
            'moyen age': (
                "Le Moyen Âge est la période de l'histoire européenne "
                "entre l'Antiquité et la Renaissance (Ve-XVe siècles). "
                "Il est marqué par la féodalité, l'Église catholique, "
                "les croisades, les châteaux forts et l'art gothique. "
                "Loin de l'image d''âge sombre', il a vu naître les "
                "universités et des avancées techniques majeures."
            ),
            'renaissance': (
                "La Renaissance est un mouvement culturel et "
                "artistique né en Italie au XVe siècle, marquant "
                "le passage du Moyen Âge aux Temps modernes. Elle "
                "se caractérise par un retour aux sources antiques, "
                "l'humanisme, le développement des sciences et des "
                "arts. Léonard de Vinci, Michel-Ange, Raphaël et "
                "Gutenberg en sont les figures emblématiques."
            ),
            'guerre': (
                "La guerre est un conflit armé entre États, groupes "
                "ou factions, visant à imposer sa volonté par la "
                "force. Clausewitz la définit comme 'la continuation "
                "de la politique par d'autres moyens'. Les guerres "
                "peuvent être totales (mondiales), civiles, de "
                "libération ou économiques. Le droit international "
                "humanitaire (Conventions de Genève) encadre les "
                "conflits."
            ),
            'paix': (
                "La paix est l'état d'absence de conflit armé et de "
                "violence organisée. Elle peut être négative (simple "
                "absence de guerre) ou positive (justice sociale, "
                "droits humains, développement). L'ONU, fondée en "
                "1945, a pour mission de maintenir la paix mondiale. "
                "Gandhi et Martin Luther King ont montré la force de "
                "la non-violence."
            ),

            # ─── GÉOGRAPHIE ──────────────────────────────────────────────
            'afrique': (
                "L'Afrique est le deuxième continent par la surface "
                "(30 millions km²) et la population (1,4 milliard "
                "d'habitants). Berceau de l'humanité, elle compte "
                "54 pays d'une grande diversité culturelle et "
                "linguistique. Le Sahara, le Nil, le Kilimandjaro "
                "et la forêt du Congo en sont des repères "
                "géographiques majeurs."
            ),
            'asie': (
                "L'Asie est le plus grand continent (44 millions "
                "km²) et le plus peuplé (4,7 milliards d'habitants). "
                "Elle abrite les civilisations les plus anciennes "
                "(Chine, Inde, Mésopotamie). L'Himalaya, le Gange, "
                "la Grande Muraille et les mégalopoles de Tokyo et "
                "Shanghai illustrent sa diversité."
            ),
            'europe': (
                "L'Europe est un continent de 10 millions km², "
                "berceau de la civilisation occidentale. Elle "
                "compte environ 750 millions d'habitants répartis "
                "en 44 pays. L'Union européenne (27 membres) est "
                "une union politique et économique unique. Les "
                "Alpes, le Danube, le Parthénon et la Tour Eiffel "
                "sont des symboles européens."
            ),
            'ocean': (
                "Les océans couvrent 71% de la surface terrestre. "
                "On en distingue cinq : Pacifique (le plus grand), "
                "Atlantique, Indien, Arctique et Austral. Ils "
                "régulent le climat, abritent une biodiversité "
                "immense et fournissent des ressources (pêche, "
                "transport, énergie). La profondeur moyenne est "
                "de 3 800 mètres."
            ),
            'desert': (
                "Un désert est une région aride recevant moins de "
                "250 mm de précipitations par an. Le Sahara (9 "
                "millions km²) est le plus grand désert chaud. "
                "Les déserts peuvent être chauds (Sahara, Atacama) "
                "ou froids (Antarctique, Gobi). La vie s'y adapte "
                "de façon remarquable (cactus, chameaux, serpents)."
            ),
            'foret': (
                "Les forêts couvrent environ 31% des terres "
                "émergées. Elles sont essentielles au climat "
                "(puits de carbone), à la biodiversité (80% des "
                "espèces terrestres) et aux sociétés humaines "
                "(bois, nourriture, médicaments). L'Amazonie, "
                "la taïga sibérienne et la forêt du Congo sont "
                "les plus grandes forêts du monde."
            ),

            # ─── SPORTS ──────────────────────────────────────────────────
            'sport': (
                "Le sport est une activité physique pratiquée "
                "individuellement ou collectivement, à des fins "
                "de compétition, de loisir ou de santé. Les Jeux "
                "Olympiques modernes (1896, Coubertin) rassemblent "
                "les nations. Les sports les plus populaires "
                "mondialement sont le football (4 milliards de "
                "fans), le cricket et le basketball."
            ),
            'football': (
                "Le football (soccer) est un sport collectif "
                "opposant deux équipes de 11 joueurs, dont le but "
                "est de marquer en envoyant un ballon dans le but "
                "adverse. Né en Angleterre au XIXe siècle, il est "
                "devenu le sport le plus populaire au monde. La "
                "Coupe du Monde (FIFA), créée en 1930, est "
                "l'événement sportif le plus regardé."
            ),

            # ─── CUISINE / ALIMENTATION ──────────────────────────────────
            'pain': (
                "Le pain est un aliment de base fait de farine, "
                "d'eau, de sel et de levure, cuit au four. Il "
                "existe depuis au moins 14 000 ans. La baguette "
                "française est inscrite au patrimoine culturel "
                "immatériel de l'UNESCO (2022). Le pain est un "
                "symbole universel de nourriture et de partage."
            ),
            'vin': (
                "Le vin est une boisson alcoolisée obtenue par "
                "fermentation du raisin. Sa production (viticulture) "
                "remonte à au moins 6 000 ans (Géorgie, Iran). La "
                "France, l'Italie et l'Espagne sont les plus grands "
                "producteurs. Le vin est au cœur de nombreuses "
                "traditions culturelles et religieuses."
            ),
            'cafe': (
                "Le café est une boisson préparée à partir des "
                "graines torréfiées du caféier. Originaire "
                "d'Éthiopie, il s'est répandu dans le monde arabe "
                "au XVe siècle puis en Europe. Deuxième boisson la "
                "plus consommée après l'eau, le café contient de "
                "la caféine, un stimulant du système nerveux."
            ),

            # ─── TRANSPORTS ──────────────────────────────────────────────
            'avion': (
                "L'avion est un aéronef plus lourd que l'air, "
                "propulsé par des moteurs et sustenté par des ailes "
                "fixes. Les frères Wright ont réalisé le premier "
                "vol motorisé en 1903. L'aviation commerciale "
                "transporte plus de 4 milliards de passagers par "
                "an. Le Concorde (1976-2003) a volé à Mach 2 "
                "(2 200 km/h)."
            ),
            'automobile': (
                "L'automobile est un véhicule à moteur conçu pour "
                "le transport routier. Karl Benz a construit la "
                "première en 1885. Henry Ford a démocratisé sa "
                "production avec le travail à la chaîne (1908). "
                "Aujourd'hui, plus d'un milliard de voitures "
                "circulent dans le monde. La transition vers "
                "l'électrique est en cours."
            ),
            'train': (
                "Le train est un véhicule ferroviaire tracté par "
                "une locomotive. La première ligne (Stockton-"
                "Darlington, 1825) a révolutionné le transport. "
                "Le TGV français (1981) a atteint 574 km/h en "
                "record. Le train est le mode de transport terrestre "
                "le plus efficace énergétiquement."
            ),

            # ─── PHILOSOPHIE ─────────────────────────────────────────────
            'bonheur': (
                "Le bonheur est un état de satisfaction durable et "
                "d'épanouissement. Aristote le voyait comme la fin "
                "suprême de l'existence (eudémonisme). Les stoïciens "
                "le plaçaient dans la vertu, les épicuriens dans le "
                "plaisir modéré. La psychologie positive moderne "
                "étudie les facteurs du bonheur : relations, sens, "
                "engagement."
            ),
            'morale': (
                "La morale est l'ensemble des règles et des valeurs "
                "qui distinguent le bien du mal, guidant les actions "
                "humaines. Elle peut être fondée sur la religion, la "
                "raison (Kant : impératif catégorique), les "
                "conséquences (utilitarisme) ou les vertus (Aristote). "
                "L'éthique est la réflexion philosophique sur la morale."
            ),
            'verite': (
                "La vérité est la correspondance entre une proposition "
                "et la réalité. En philosophie, plusieurs théories "
                "s'affrontent : correspondance (Aristote), cohérence "
                "(idéalisme), pragmatisme (James : ce qui fonctionne "
                "est vrai). En science, la vérité est provisoire et "
                "fondée sur la vérification empirique."
            ),
            'beaute': (
                "La beauté est la qualité de ce qui est esthétiquement "
                "agréable à percevoir. Platon la voyait comme une "
                "Idée pure. Kant la définit comme 'ce qui plaît "
                "universellement sans concept'. La beauté peut être "
                "objective (symétrie, proportions, nombre d'or) ou "
                "subjective ('la beauté est dans l'œil de celui qui "
                "regarde')."
            ),
            'hasard': (
                "Le hasard est l'absence de cause déterminée ou "
                "prévisible. En philosophie, il s'oppose au "
                "déterminisme. En physique quantique, l'école de "
                "Copenhague affirme que certains événements sont "
                "fondamentalement aléatoires. En mathématiques, "
                "le hasard est modélisé par les probabilités."
            ),

            # ─── POLITIQUE / DROIT ────────────────────────────────────────
            'etat': (
                "L'État est l'organisation politique et juridique "
                "d'un pays, exerçant son autorité sur un territoire "
                "et une population. Max Weber le définit par le "
                "monopole de la violence légitime. L'État de droit "
                "garantit que tous, y compris les gouvernants, sont "
                "soumis aux lois. La séparation des pouvoirs "
                "(Montesquieu) en est un principe clé."
            ),
            'constitution': (
                "La constitution est la loi fondamentale d'un État "
                "qui définit l'organisation des pouvoirs publics et "
                "garantit les droits fondamentaux des citoyens. "
                "La première constitution écrite fut celle des "
                "États-Unis (1787). La Constitution française de "
                "1958 fonde la Ve République."
            ),
            'election': (
                "L'élection est le processus par lequel les citoyens "
                "choisissent leurs représentants politiques par le "
                "vote. Le suffrage universel (tous les citoyens "
                "votent) est un pilier de la démocratie. Les modes "
                "de scrutin (majoritaire, proportionnel) influencent "
                "la représentation politique."
            ),
            'president': (
                "Le président est le chef de l'État dans une "
                "république. En France, le président de la "
                "République est élu au suffrage universel direct "
                "pour 5 ans. Il nomme le Premier ministre, peut "
                "dissoudre l'Assemblée nationale et est le chef "
                "des armées. Aux États-Unis, le président est à "
                "la fois chef de l'État et du gouvernement."
            ),
            'onu': (
                "L'ONU (Organisation des Nations Unies) est une "
                "organisation internationale fondée en 1945 pour "
                "maintenir la paix, promouvoir les droits humains "
                "et favoriser la coopération entre les nations. "
                "Elle compte 193 États membres. Le Conseil de "
                "sécurité (5 membres permanents dont la France) "
                "peut autoriser l'usage de la force."
            ),

            # ─── RELIGIONS ───────────────────────────────────────────────
            'christianisme': (
                "Le christianisme est une religion monothéiste "
                "fondée sur la vie et l'enseignement de Jésus de "
                "Nazareth. Avec 2,4 milliards de fidèles, c'est "
                "la religion la plus pratiquée. La Bible est son "
                "texte sacré. Il se divise en trois branches "
                "principales : catholicisme, orthodoxie et "
                "protestantisme."
            ),
            'islam': (
                "L'islam est une religion monothéiste fondée par "
                "le prophète Mahomet au VIIe siècle en Arabie. "
                "Avec 1,9 milliard de fidèles, c'est la deuxième "
                "religion mondiale. Le Coran est son livre sacré. "
                "Les cinq piliers de l'islam sont la profession de "
                "foi, la prière, l'aumône, le jeûne du Ramadan "
                "et le pèlerinage à La Mecque."
            ),
            'bouddhisme': (
                "Le bouddhisme est une religion et une philosophie "
                "fondée par Siddhartha Gautama (le Bouddha) au Ve "
                "siècle av. J.-C. en Inde. Il enseigne la voie "
                "de la libération de la souffrance par la "
                "compréhension des Quatre Nobles Vérités et la "
                "pratique du Noble Chemin Octuple. Il compte "
                "environ 500 millions d'adeptes."
            ),
            'judaisme': (
                "Le judaïsme est la religion monothéiste la plus "
                "ancienne, fondée sur l'alliance entre Dieu et "
                "le peuple d'Israël. La Torah en est le texte "
                "fondateur. Avec environ 15 millions de fidèles, "
                "c'est la plus petite des trois religions "
                "abrahamiques. Le shabbat, la circoncision et "
                "les fêtes (Pessah, Yom Kippour) rythment la "
                "vie juive."
            ),

            # ─── MYTHOLOGIE ──────────────────────────────────────────────
            'mythologie': (
                "La mythologie est l'ensemble des récits légendaires "
                "d'une civilisation, mettant en scène des dieux, "
                "des héros et des créatures surnaturelles. Les "
                "mythologies grecque (Zeus, Hercule), nordique "
                "(Odin, Thor), égyptienne (Osiris, Isis) et "
                "hindoue (Vishnu, Shiva) ont profondément "
                "influencé l'art et la pensée humaine."
            ),

            # ─── ANIMAUX ─────────────────────────────────────────────────
            'chat': (
                "Le chat domestique (Felis catus) est un mammifère "
                "carnivore de la famille des félidés. Domestiqué "
                "il y a environ 10 000 ans au Proche-Orient, il "
                "est aujourd'hui l'un des animaux de compagnie "
                "les plus répandus. Excellents chasseurs, les "
                "chats possèdent une vision nocturne exceptionnelle "
                "et un sens de l'équilibre remarquable."
            ),
            'chien': (
                "Le chien (Canis familiaris) est le premier animal "
                "domestiqué par l'homme, il y a 15 000 à 40 000 "
                "ans. Descendant du loup gris, il présente une "
                "diversité morphologique unique avec plus de 350 "
                "races reconnues. Les chiens ont un odorat 40 fois "
                "plus développé que l'homme et sont utilisés pour "
                "la chasse, la garde, le sauvetage et l'assistance."
            ),
            'cheval': (
                "Le cheval (Equus caballus) est un grand mammifère "
                "herbivore domestiqué il y a environ 5 500 ans "
                "dans les steppes d'Asie centrale. Il a transformé "
                "les sociétés humaines : transport, agriculture, "
                "guerre. Aujourd'hui, il est principalement utilisé "
                "pour les loisirs et les sports équestres."
            ),

            # ─── PLANTES ─────────────────────────────────────────────────
            'arbre': (
                "Un arbre est une plante ligneuse pérenne comportant "
                "un tronc, des branches et des feuilles. Les arbres "
                "peuvent vivre des milliers d'années (séquoias, "
                "oliviers). Ils produisent de l'oxygène, stockent "
                "le carbone, abritent la biodiversité et fournissent "
                "bois, fruits et ombre. La déforestation menace "
                "l'équilibre climatique mondial."
            ),
        }

        added = 0
        for sujet, bloc in curated.items():
            if not self.has_bloc(sujet):
                self.enrich_curated(sujet, bloc, 'definition')
                added += 1

        if added > 0:
            log.info(f"  📚 {added} blocs curated chargés")
        return added


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    print("=" * 60)
    print("KNOWLEDGE ENRICHER — Démo")
    print("=" * 60)

    enricher = KnowledgeEnricher()
    enricher.load_curated_defaults()

    print(f"\n{enricher.count} blocs de savoir disponibles:")
    for sujet in enricher.sujets:
        bloc = enricher.get_bloc(sujet)
        print(f"\n  [{sujet}]")
        print(f"  {bloc[:120]}...")


if __name__ == '__main__':
    demo()
