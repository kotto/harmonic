#!/usr/bin/env python3
"""
KA-Next -- HOLOGRAPHIC ENSEMBLE (Mixture of Holograms)
=========================================================
Architecture multi-hologrammes connectés par φ.
Chaque hologramme 64×64 est un "expert" spécialisé dans un domaine.
L'interférence entre hologrammes sert de mécanisme de routage (gating).

Preuve de concept : l'ingestion UNESCO 64×64 a démontré 21 entrées/sec,
                   des motifs d'interférence nets, et l'émergence de √2.
                   Le 1024×1024 a dilué ces motifs d'un facteur 256×.

Solution : N hologrammes 64×64 spécialisés + cross-résonance φ.

Architecture :
  DOMAINS = {
    "geography":  Hologramme 64×64 des capitales/pays/fleuves,
    "history":    Hologramme 64×64 des dates/empires/événements,
    "science":    Hologramme 64×64 de physique/chimie/bio,
    "mathematics": Hologramme 64×64 des formules/théorèmes,
    "philosophy": Hologramme 64×64 des sagesses/concepts,
    "technology": Hologramme 64×64 de l'informatique/IA,
    "general":    Hologramme 64×64 de connaissances générales,
  }

Routage :
  Question → onde Ψ_q
  → Résonance avec CHAQUE hologramme de domaine
  → top-K hologrammes sélectionnés (gating par φ)
  → Faits extraits des hologrammes gagnants
  → Réponse par interférence inter-hologrammes

Usage :
  python holographic_ensemble.py --build-all   # Construire tous les hologrammes
  python holographic_ensemble.py --query "..."  # Requête
  python holographic_ensemble.py --serve        # Serveur
"""

import os, sys, math, json, time, hashlib, re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

# Importer l'encodeur spectral (TF-IDF → ondes sémantiques)
try:
    from spectral_encoder import SpectralEncoder
    SPECTRAL_AVAILABLE = True
except ImportError:
    SPECTRAL_AVAILABLE = False

PHI = (1 + math.sqrt(5)) / 2
HOLO_SIZE = 64  # Taille optimale prouvée par l'ingestion UNESCO

DATA_DIR = BASE_DIR.parent / "data" / "holograms"
os.makedirs(DATA_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DÉFINITION DES DOMAINES DE CONNAISSANCE
# ═══════════════════════════════════════════════════════════════════════════════

DOMAIN_DEFINITIONS = {
    "geography": {
        "name": "Géographie",
        "color": "#4CAF50",
        "salt": "geo_domain_phi_1",
        "description": "Capitales, pays, continents, fleuves, montagnes",
        "facts": [
            "La capitale du Senegal est Dakar.",
            "La capitale de la France est Paris.",
            "La capitale du Mali est Bamako.",
            "La capitale de l'Ethiopie est Addis-Abeba.",
            "La capitale de l'Iran est Teheran.",
            "La capitale du Japon est Tokyo.",
            "La capitale du Bresil est Brasilia.",
            "La capitale de l'Egypte est Le Caire.",
            "La capitale du Ghana est Accra.",
            "La capitale du Nigeria est Abuja.",
            "Le Nil est le plus long fleuve du monde, 6650 km.",
            "Le mont Everest est le plus haut sommet, 8849 metres.",
            "Le Sahara est le plus grand desert chaud, 9.2 millions de km2.",
            "L'Afrique compte 54 pays et 1.4 milliard d'habitants.",
            "L'Asie compte 4.7 milliards d'habitants, 60% de l'humanite.",
            "L'Europe compte 750 millions d'habitants et 44 pays.",
            "Les 7 continents : Afrique, Amerique du Nord, Amerique du Sud, Antarctique, Asie, Europe, Oceanie.",
            "La France se situe en Europe. Sa monnaie est l'euro.",
            "Le Canada est le deuxieme plus grand pays du monde par superficie.",
            "La Russie est le plus grand pays du monde, 17.1 millions de km2.",
        ]
    },
    "history": {
        "name": "Histoire",
        "color": "#FF5722",
        "salt": "hist_domain_phi_1",
        "description": "Dates, empires, événements, civilisations",
        "facts": [
            "La Revolution francaise a debute en 1789.",
            "La Seconde Guerre mondiale s'est deroulee de 1939 a 1945.",
            "L'Empire romain est tombe en 476 apres JC.",
            "Christophe Colomb a atteint les Ameriques en 1492.",
            "L'Empire du Mali fut fonde par Soundiata Keita vers 1230.",
            "Mansa Moussa, empereur du Mali, fit un pelerinage a La Mecque en 1324 avec tant d'or qu'il destabilisa l'economie egyptienne.",
            "L'universite de Sankore a Tombouctou avait 25000 etudiants au 14e siecle.",
            "Le royaume de Kouch (Nubie) a regne sur l'Egypte pendant la 25e dynastie (-747 a -656).",
            "L'Ethiopie a vaincu l'Italie a la bataille d'Adoua en 1896.",
            "La conference de Berlin de 1884-1885 a partage l'Afrique entre puissances europeennes.",
            "Le Ghana fut le premier pays d'Afrique subsaharienne independant en 1957, dirige par Kwame Nkrumah.",
            "L'Egypte ancienne (Kemet) est nee dans la vallee du Nil vers -3150.",
            "Les manuscrits de Tombouctou comptent plus de 700 000 documents.",
            "Le royaume du Benin (1180-1897) produisait des bronzes d'exception.",
            "Les 42 lois de Maat (Egypte ancienne) sont anterieures aux 10 commandements.",
        ]
    },
    "science": {
        "name": "Sciences",
        "color": "#2196F3",
        "salt": "sci_domain_phi_1",
        "description": "Physique, chimie, biologie, astronomie",
        "facts": [
            "La lumiere voyage a 299 792 458 metres par seconde dans le vide.",
            "La gravitation universelle de Newton (1687) : F = G * m1 * m2 / r^2.",
            "Einstein a publie la relativite generale en 1915 : la masse courbe l'espace-temps.",
            "Le Big Bang s'est produit il y a 13.8 milliards d'annees.",
            "L'energie noire constitue 68% de l'univers, la matiere noire 27%.",
            "La mecanique quantique decrit le monde subatomique avec le principe d'incertitude de Heisenberg.",
            "Max Planck a introduit le quantum d'action h en 1900.",
            "Darwin a publie L'Origine des especes en 1859 : evolution par selection naturelle.",
            "L'ADN, support de l'heredite, a ete decouvert par Watson et Crick en 1953.",
            "Le tableau periodique de Mendeleiev (1869) organise les 118 elements chimiques.",
            "L'eau H2O est le solvant universel de la vie.",
            "La tectonique des plaques (Wegener, 1912) explique la derive des continents.",
            "La Terre a 4.54 milliards d'annees.",
            "Les 4 lois de la thermodynamique gouvernent l'energie et l'entropie.",
            "Boltzmann a relie entropie et probabilite : S = k * log(W).",
        ]
    },
    "mathematics": {
        "name": "Mathématiques",
        "color": "#FFD700",
        "salt": "math_domain_phi_1",
        "description": "Constantes, théorèmes, calculs",
        "facts": [
            "pi = 3.14159... est le rapport entre la circonference d'un cercle et son diametre.",
            "e = 2.71828... est la base du logarithme naturel.",
            "phi = 1.618034... est le nombre d'or, solution de x^2 = x + 1.",
            "i^2 = -1 definit l'unite imaginaire.",
            "Le theoreme de Pythagore : a^2 + b^2 = c^2 pour un triangle rectangle.",
            "2 + 2 = 4. 12 * 15 = 180. 15 * 15 = 225.",
            "La racine carree de 144 est 12.",
            "La racine carree de 2 est approximativement 1.4142.",
            "Un nombre premier est divisible uniquement par 1 et lui-meme.",
            "Le logarithme neperien ln(e) = 1.",
            "La derivee de x^n est n * x^(n-1).",
            "L'integrale de x^n est x^(n+1) / (n+1) pour n != -1.",
            "La formule d'Euler : e^(i*pi) + 1 = 0 relie 5 constantes fondamentales.",
            "La suite de Fibonacci : 0, 1, 1, 2, 3, 5, 8, 13, 21... ratio -> phi.",
            "Le theoreme fondamental de l'algebre : tout polynome de degre n a exactement n racines complexes.",
        ]
    },
    "philosophy": {
        "name": "Philosophie & Sagesse",
        "color": "#9C27B0",
        "salt": "phil_domain_phi_1",
        "description": "Éthique, sagesses, concepts philosophiques",
        "facts": [
            "Maat (Egypte ancienne) : principe cosmique d'ordre, verite, justice, equilibre. 42 lois.",
            "Ubuntu (philosophie bantoue) : Je suis parce que nous sommes. Solidarite, communaute.",
            "Stoicisme (Zenon, -300) : distinguer ce qui depend de nous de ce qui n'en depend pas.",
            "Socrate (-470 a -399) : Je sais que je ne sais rien. La maieutique par le dialogue.",
            "Les Lumieres (18e siecle) : Sapere aude (ose savoir). Voltaire, Rousseau, Kant.",
            "Marc Aurele : Ce qui ne me detruit pas me renforce.",
            "Confucius (-551 a -479) : Ne fais pas a autrui ce que tu ne voudrais pas qu'on te fasse.",
            "Bouddha (-563 a -483) : Quatre Nobles Verites. La souffrance vient de l'attachement.",
            "Descartes (1596-1650) : Je pense, donc je suis. Cogito ergo sum.",
            "Nietzsche (1844-1900) : Ce qui ne me tue pas me rend plus fort.",
            "La philosophie est l'amour de la sagesse (philo-sophia en grec).",
        ]
    },
    "technology": {
        "name": "Technologie & IA",
        "color": "#00BCD4",
        "salt": "tech_domain_phi_1",
        "description": "Informatique, programmation, IA, internet",
        "facts": [
            "La machine de Turing (1936) definit le calcul universel.",
            "Internet utilise le protocole TCP/IP cree en 1974.",
            "Le Web a ete invente par Tim Berners-Lee en 1989 au CERN.",
            "Python est un langage de programmation polyvalent cree par Guido van Rossum.",
            "JavaScript est le langage du Web, cree par Brendan Eich en 1995.",
            "L'intelligence artificielle utilise des reseaux de neurones pour apprendre.",
            "Les transformers (Vaswani et al., 2017) ont revolutionne le traitement du langage.",
            "Un ordinateur quantique utilise des qubits en superposition.",
            "L'algorithme de Shor peut factoriser des nombres en temps polynomial sur un ordinateur quantique.",
            "Le chiffrement RSA repose sur la difficulte de factoriser de grands nombres.",
            "Le DNS traduit les noms de domaine en adresses IP.",
            "Git est un systeme de controle de version cree par Linus Torvalds.",
            "Linux est un systeme d'exploitation open source cree par Linus Torvalds en 1991.",
        ]
    },
    "general": {
        "name": "Connaissances générales",
        "color": "#888888",
        "salt": "gen_domain_phi_1",
        "description": "Culture générale, divers",
        "facts": [
            "La Joconde a ete peinte par Leonard de Vinci.",
            "Le sushi est un plat traditionnel japonais.",
            "Le football est le sport le plus populaire au monde.",
            "La Tour Eiffel a ete construite en 1889 a Paris.",
            "La Grande Muraille de Chine fait environ 21 000 km de long.",
            "Le corps humain adulte compte 206 os.",
            "L'eau bout a 100 degres Celsius au niveau de la mer.",
            "Le symbole chimique de l'or est Au.",
            "Le symbole chimique de l'hydrogene est H.",
            "Balance commerciale = exports - imports.",
            "La vitesse du son dans l'air est d'environ 343 metres par seconde.",
        ]
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# HOLOGRAMME 64×64 (taille optimale validée UNESCO)
# ═══════════════════════════════════════════════════════════════════════════════

class Hologram64:
    """Un hologramme 64×64 spécialisé dans un domaine."""

    def __init__(self, domain_id: str, size: int = HOLO_SIZE):
        self.domain_id = domain_id
        self.size = size
        self.domain_info = DOMAIN_DEFINITIONS.get(domain_id, DOMAIN_DEFINITIONS["general"])
        self.salt = self.domain_info["salt"]
        self.hologram = np.zeros((size, size), dtype=np.complex128)
        self.positions: List[Tuple[float, float]] = []
        self.fact_texts: List[str] = []
        self.n_ingested = 0
        self.energy = 0.0
        self.spectral_encoder = None  # Encodeur spectral (TF-IDF → ondes)
        self._load_or_build()

    def _init_spectral_encoder(self):
        """Initialise l'encodeur spectral sur le corpus du domaine."""
        if not SPECTRAL_AVAILABLE:
            return
        if self.spectral_encoder is not None:
            return
        # Construire le vocabulaire à partir des faits du domaine + des faits déjà ingérés
        all_facts = list(self.domain_info.get("facts", [])) + self.fact_texts
        if len(all_facts) < 3:
            return
        self.spectral_encoder = SpectralEncoder(max_features=4096)
        self.spectral_encoder.build_vocabulary(all_facts)

    def _load_or_build(self):
        """Charge depuis le disque ou construit."""
        path = DATA_DIR / f"hologram64_{self.domain_id}.npy"
        if path.exists():
            self.hologram = np.load(path)
            self.energy = float(np.sum(np.abs(self.hologram) ** 2))
            # Charger positions et textes depuis data.json
            data_path = DATA_DIR / f"hologram64_{self.domain_id}_data.json"
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.positions = [(kx, ky) for kx, ky in data.get("positions", [])]
                self.fact_texts = data.get("texts", [])
                self.n_ingested = data.get("n_ingested", len(self.fact_texts))
            else:
                # Fallback : faits du domaine
                facts = self.domain_info.get("facts", [])
                for text in facts:
                    kx, ky = self._text_to_wave(text)
                    self.positions.append((kx, ky))
                    self.fact_texts.append(text)
                self.n_ingested = len(facts)
            # RÉINITIALISER l'encodeur spectral avec le corpus chargé
            if SPECTRAL_AVAILABLE and self.fact_texts:
                self._init_spectral_encoder()
            print(f"  [{self.domain_id}] Charge : {self.hologram.shape}, energie={self.energy:.0f}, faits={self.n_ingested}")
        else:
            print(f"  [{self.domain_id}] Nouvel hologramme 64x64 cree")

    def _text_to_wave(self, text: str) -> Tuple[float, float]:
        """
        SHA-256 + sel de domaine -> (kx, ky).
        Pour le lookup intra-domaine, SHA-256 est plus discriminant
        que le SpectralEncoder (qui a trop peu de vocabulaire).
        Le SpectralEncoder est utilisé uniquement pour le GATING
        (resonance()), où sa cohérence sémantique est utile.
        """
        salted = self.salt + text
        h = hashlib.sha256(salted.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (self.size * 100)) / 100.0
        ky = (int(h[16:32], 16) % (self.size * 100)) / 100.0
        return (kx - self.size / 2) / self.size * 20, (ky - self.size / 2) / self.size * 20

    def _text_to_wave_spectral(self, text: str) -> Tuple[float, float]:
        """
        Encode avec SpectralEncoder (TF-IDF → onde). Utilisé pour le
        GATING inter-domaine, où la cohérence sémantique est cruciale.
        """
        if self.spectral_encoder is not None:
            try:
                return self.spectral_encoder.encode(text, self.size)
            except Exception:
                pass
        return self._text_to_wave(text)

    def ingest(self, text: str, amplitude: float = 0.15):
        """Ingère un fait dans cet hologramme. Méthode directe (validée UNESCO)."""
        kx, ky = self._text_to_wave(text)
        x = np.linspace(-self.size / 2, self.size / 2, self.size)
        y = np.linspace(-self.size / 2, self.size / 2, self.size)
        X, Y = np.meshgrid(x, y)
        sigma = 3.0  # Gaussienne plus étroite pour 64x64 = haute densité
        env = np.exp(-(X ** 2 + Y ** 2) / (2 * sigma ** 2))
        wave = amplitude * env * np.exp(1j * (kx * X / 20 + ky * Y / 20))
        self.hologram += wave
        if np.max(np.abs(self.hologram)) > 100:
            self.hologram *= 0.95
        self.positions.append((kx, ky))
        self.fact_texts.append(text)
        self.n_ingested += 1

    def build_from_domain_facts(self):
        """Construit l'hologramme à partir des faits du domaine."""
        facts = self.domain_info.get("facts", [])
        print(f"  [{self.domain_id}] Ingestion de {len(facts)} faits...")
        # Initialiser l'encodeur spectral AVANT l'ingestion
        self._init_spectral_encoder()
        if self.spectral_encoder:
            print(f"    Encodeur spectral : {self.spectral_encoder.word_count} mots")
        t0 = time.time()
        for text in facts:
            self.ingest(text)
        dt = max(time.time() - t0, 0.001)
        self.energy = float(np.sum(np.abs(self.hologram) ** 2))
        print(f"  [{self.domain_id}] {len(facts)} faits en {dt:.1f}s ({len(facts)/dt:.0f}/s) | energie={self.energy:.0f}")

    def resonance(self, query: str) -> float:
        """
        Calcule la force de résonance d'une question avec cet hologramme.
        Utilise le SpectralEncoder pour le gating sémantique.
        """
        if not self.positions:
            return 0.0
        
        # GATING : utiliser l'onde SPECTRALE pour déterminer si la question
        # appartient à ce domaine. Le SpectralEncoder capture la similarité
        # thématique (ex: "capitale", "fleuve" → géographie)
        kx_q, ky_q = self._text_to_wave_spectral(query)
        
        min_dist = float('inf')
        for kx_f, ky_f in self.positions[:min(50, len(self.positions))]:
            # Utiliser les positions spectrales pour les 50 premiers faits
            # (les faits du domaine de base, qui définissent la thématique)
            dist = math.sqrt((kx_q - kx_f) ** 2 + (ky_q - ky_f) ** 2)
            if dist < min_dist:
                min_dist = dist
        
        score = 1.0 / (1.0 + min_dist * 2)  # Distance spectrale
        
        # Bonus sémantique
        semantic = 0.0
        for fact_text in self.fact_texts:
            boost = self._semantic_boost(query, fact_text)
            if boost > semantic:
                semantic = boost
        
        return min(1.0, score * 0.7 + semantic * 0.3)

    def query(self, text: str, k: int = 5) -> List[Dict]:
        """Recherche les faits les plus résonants dans cet hologramme.
        
        Combine :
          - Distance dans l'espace de phase (onde → onde)
          - Similarité sémantique (mots communs)
          - Énergie holographique locale
        """
        kx_q, ky_q = self._text_to_wave(text)
        scored = []
        for i, fact_text in enumerate(self.fact_texts):
            if i >= len(self.positions):
                continue
            kx_f, ky_f = self.positions[i]
            # Distance de phase
            dist = math.sqrt((kx_q - kx_f) ** 2 + (ky_q - ky_f) ** 2)
            phase_score = 0.5 / (0.5 + dist)  # Normalisé entre 0 et 1
            # Énergie locale au point du fait
            cx = int(kx_f * self.size / 20 + self.size / 2) % self.size
            cy = int(ky_f * self.size / 20 + self.size / 2) % self.size
            r = 2
            h, w = self.hologram.shape
            patch = self.hologram[max(0, cy - r):min(h, cy + r),
                                  max(0, cx - r):min(w, cx + r)]
            local_e = float(np.sum(np.abs(patch) ** 2))
            energy_score = min(1.0, local_e / max(self.energy / self.n_ingested, 1e-10) * 5)
            # Similarité sémantique
            semantic = self._semantic_boost(text, fact_text)
        # Score combiné : 20% phase (SHA-256, discriminant) + 10% énergie + 70% sémantique
            combined = 0.2 * phase_score + 0.1 * energy_score + 0.7 * semantic
            scored.append({"text": fact_text, "score": combined, "distance": dist,
                          "phase_score": phase_score, "semantic": semantic,
                          "energy_score": energy_score})
        scored.sort(key=lambda x: -x["score"])
        return scored[:k]

    def _semantic_boost(self, prompt: str, fact: str) -> float:
        """Intersection de mots significatifs."""
        def words(t):
            return {w.strip('.,;:!?()[]{}"\'-').lower() for w in t.lower().split()
                    if len(w.strip('.,;:!?()[]{}"\'-')) > 3}
        qw = words(prompt)
        fw = words(fact)
        if not qw or not fw:
            return 0.0
        common = qw & fw
        return len(common) / max(len(qw), 1) + (0.5 if max(qw, key=len) in fw else 0)

    def save(self):
        """Sauvegarde l'hologramme + positions + textes."""
        path = DATA_DIR / f"hologram64_{self.domain_id}.npy"
        np.save(path, self.hologram)
        # Sauvegarder positions et textes
        data_path = DATA_DIR / f"hologram64_{self.domain_id}_data.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump({"positions": [[round(kx,6), round(ky,6)] for kx,ky in self.positions],
                       "texts": self.fact_texts, "n_ingested": self.n_ingested,
                       "energy": float(self.energy)}, f, ensure_ascii=False)

    def audit(self) -> Dict:
        """Audit rapide."""
        amp = np.abs(self.hologram)
        return {
            "domain": self.domain_id,
            "size": f"{self.size}x{self.size}",
            "energy": self.energy,
            "max_amp": float(np.max(amp)),
            "mean_amp": float(np.mean(amp)),
            "nonzero_pct": round(np.count_nonzero(amp > 0.01) / (self.size * self.size) * 100, 1),
            "n_facts": self.n_ingested,
            "density": round(self.n_ingested / (self.size * self.size) * 1000, 1),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ENSEMBLE HOLOGRAPHIQUE (Mixture of Holograms)
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicEnsemble:
    """
    Ensemble de N hologrammes 64×64 spécialisés, connectés par φ.
    
    Routage (gating) :
      1. La question est projetée dans chaque espace de domaine
      2. La force de résonance détermine quels hologrammes sont activés
      3. Les faits sont extraits des top-K hologrammes
      4. La réponse est l'interférence pondérée de ces faits
    """

    def __init__(self, domains: List[str] = None):
        if domains is None:
            domains = list(DOMAIN_DEFINITIONS.keys())
        self.domains = domains
        self.holograms: Dict[str, Hologram64] = {}
        self.stats = {"total_queries": 0, "total_time_ms": 0}

    def build_all(self, force_rebuild: bool = False):
        """Construit tous les hologrammes de l'ensemble."""
        print("=" * 60)
        print("  CONSTRUCTION DE L'ENSEMBLE HOLOGRAPHIQUE")
        print(f"  {len(self.domains)} domaines, hologrammes {HOLO_SIZE}x{HOLO_SIZE}")
        print("=" * 60)

        for domain_id in self.domains:
            holo = Hologram64(domain_id)
            if force_rebuild or holo.n_ingested == 0:
                holo.build_from_domain_facts()
                holo.save()
            self.holograms[domain_id] = holo

        print(f"\n  Ensemble construit : {len(self.holograms)} hologrammes")
        total_facts = sum(h.n_ingested for h in self.holograms.values())
        total_energy = sum(h.energy for h in self.holograms.values())
        print(f"  Total faits : {total_facts}")
        print(f"  Energie totale : {total_energy:.0f}")
        print("=" * 60)

    def query(self, prompt: str, top_k_holos: int = 3, 
              facts_per_holo: int = 5) -> Dict[str, Any]:
        """
        Requête distribuée sur l'ensemble holographique.
        
        1. Calcule la résonance avec chaque hologramme
        2. Sélectionne les top-K hologrammes (gating)
        3. Extrait les faits de chaque hologramme sélectionné
        4. Assemble la réponse par interférence pondérée
        """
        if not self.holograms:
            return {"text": "Ensemble non construit. Lancez build_all() d'abord.",
                    "error": "not_built"}

        t0 = time.time()
        self.stats["total_queries"] += 1

        # ── Étape 1 : Résonance avec chaque hologramme ──
        holo_scores = {}
        for domain_id, holo in self.holograms.items():
            score = holo.resonance(prompt)
            holo_scores[domain_id] = score

        # ── Étape 2 : Sélection des top-K hologrammes ──
        ranked_holos = sorted(holo_scores.items(), key=lambda x: -x[1])
        top_holos = ranked_holos[:top_k_holos]

        # ── Étape 3 : Extraction des faits ──
        all_facts = []
        domain_contributions = []
        for domain_id, resonance_score in top_holos:
            if resonance_score < 0.05:
                continue  # Résonance trop faible, ignorer
            holo = self.holograms[domain_id]
            facts = holo.query(prompt, k=facts_per_holo)
            for f in facts:
                # Pondérer par la résonance du domaine
                f["domain"] = domain_id
                f["domain_name"] = DOMAIN_DEFINITIONS[domain_id]["name"]
                f["domain_resonance"] = resonance_score
                f["weighted_score"] = f["score"] * resonance_score
            all_facts.extend(facts)
            domain_contributions.append({
                "domain": domain_id,
                "name": DOMAIN_DEFINITIONS[domain_id]["name"],
                "resonance": round(resonance_score, 4),
                "facts_found": len(facts)
            })

        # Trier par score pondéré
        all_facts.sort(key=lambda x: -x["weighted_score"])

        # ── Étape 4 : Assemblage de la réponse ──
        lines = []

        # Meilleur fait (tous domaines confondus)
        if all_facts:
            best = all_facts[0]
            if best["weighted_score"] > 0.3:
                lines.append(best["text"])
                confidence = best["weighted_score"]
            elif best["weighted_score"] > 0.1:
                lines.append(f"D'après l'ensemble holographique "
                            f"(résonance {best['weighted_score']:.0%}) :")
                lines.append(best["text"])
                confidence = best["weighted_score"] * 0.8
            else:
                lines.append("L'ensemble holographique contient des informations partielles :")
                for f in all_facts[:5]:
                    domain_tag = f"[{f.get('domain_name', '?')}]"
                    lines.append(f"  {domain_tag} [{f['weighted_score']:.0%}] {f['text']}")
                confidence = 0.2
        else:
            lines.append("Aucun hologramme n'a résonné avec cette question.")
            confidence = 0.0

        # Résumé des domaines activés
        lines.append("")
        lines.append(f"[Ensemble holographique : {len(domain_contributions)} domaines activés]")
        for dc in domain_contributions:
            bar = "#" * int(dc["resonance"] * 20) + "-" * (20 - int(dc["resonance"] * 20))
            lines.append(f"  {dc['name']:20s} [{bar}] {dc['resonance']:.0%}")

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        self.stats["total_time_ms"] += elapsed_ms

        return {
            "text": "\n".join(lines),
            "source": "holographic_ensemble",
            "confidence": round(confidence, 2),
            "domains_activated": domain_contributions,
            "top_facts": all_facts[:5],
            "total_facts_retrieved": len(all_facts),
            "temps_ms": elapsed_ms
        }

    def ingest_quickfacts(self):
        """
        Ingère massivement les 1030 faits QuickFacts dans les hologrammes
        de l'ensemble. Chaque fait est routé automatiquement vers le
        domaine correspondant par classification sémantique.
        """
        try:
            from quick_facts import QuickFacts
            qf = QuickFacts()
        except ImportError:
            print("QuickFacts non disponible")
            return {"error": "QuickFacts non disponible"}

        all_facts = qf.facts
        print(f"\n{'=' * 60}")
        print(f"  INGESTION MASSIVE — {len(all_facts)} faits QuickFacts")
        print(f"  Distribution automatique vers les 7 domaines")
        print(f"{'=' * 60}")

        # Classification automatique par mots-clés
        domain_keywords = {
            "geography": ["capitale", "pays", "continent", "fleuve", "mont", "sommet",
                         "desert", "mer", "ocean", "population", "monnaie", "superficie",
                         "geographie", "se situe", "frontiere", "kilometre", "km"],
            "history": ["siecle", "empire", "royaume", "guerre", "revolution", "independance",
                       "president", "roi", "pharaon", "dynastie", "date", "fondé", "antique",
                       "histoire", "civilisation", "ancestrale", "millenaire", "colonie"],
            "science": ["physique", "chimie", "biologie", "astronomie", "gravité", "newton",
                       "einstein", "quantique", "atome", "évolution", "darwin", "planète",
                       "lumière", "vitesse", "énergie", "matière", "étoile", "système",
                       "scientifique", "decouvert", "loi", "theorie", "element"],
            "mathematics": ["math", "calcul", "nombre", "équation", "racine", "carré",
                          "théorème", "pythagore", "addition", "multiplication", "division",
                          "soustraction", "angle", "triangle", "cercle", "logarithme"],
            "philosophy": ["philosophie", "sagesse", "ethique", "morale", "socrate",
                          "platon", "aristote", "descartes", "kant", "nietzsche",
                          "conscience", "pensée", "raison", "esprit", "âme", "vertu",
                          "stoicien", "maat", "ubuntu", "bantou"],
            "technology": ["ordinateur", "internet", "code", "python", "programmation",
                          "algorithme", "turing", "web", "donnée", "réseau", "ia",
                          "intelligence artificielle", "machine", "numérique"],
            "culture": ["litterature", "musique", "cinema", "peinture", "sculpture", "architecture",
                       "artiste", "ecrivain", "compositeur", "realisateur", "roman", "poeme",
                       "symphonie", "opera", "theatre", "ballet", "danse", "chanson", "film",
                       "acteur", "peintre", "tableau", "muse", "prix nobel litterature"],
            "economics": ["pib", "economie", "finance", "monnaie", "bourse", "inflation", "deflation",
                         "chomage", "commerce", "banque", "budget", "impot", "fiscalite",
                         "croissance", "recession", "capital", "marche", "entreprise", "action",
                         "dette", "investissement", "fond monetaire", "banque mondiale"],
            "health": ["sante", "medecine", "maladie", "traitement", "vaccin", "virus", "bacterie",
                      "cancer", "diabete", "hypertension", "cardiaque", "chirurgie", "anatomie",
                      "medicament", "antibiotique", "vitamine", "nutrition", "sommeil",
                      "exercice", "organe", "coeur", "cerveau", "sang", "cellule", "infection"],
            "nature": ["animal", "plante", "ecosysteme", "climat", "environnement", "biodiversite",
                      "foret", "ocean", "desert", "corail", "espece", "pollution", "rechauffement",
                      "ecologie", "faune", "flore", "habitat", "migration", "extinction",
                      "conservation", "parc national", "riviere", "montagne", "volcan"],
            "sports": ["sport", "football", "tennis", "basket", "rugby", "athletisme", "natation",
                      "cyclisme", "formule", "olympique", "champion", "record", "competition",
                      "tournoi", "coupe monde", "entraineur", "stade", "match", "but", "essai",
                      "medaille", "jeux olympiques", "marathon", "gymnastique", "boxe", "judo"],
            "general": []  # domaine par défaut
        }

        routed = {d: [] for d in self.domains}
        t0 = time.time()
        total_ingested = 0

        for fid, text, keywords in all_facts:
            text_lower = text.lower()
            best_domain = "general"
            best_score = 0

            for domain, dkws in domain_keywords.items():
                if not dkws:
                    continue
                score = sum(1 for kw in dkws if kw in text_lower)
                if score > best_score:
                    best_score = score
                    best_domain = domain

            routed[best_domain].append(text)

        # Ingérer dans chaque hologramme (positions SHA-256 pour lookup)
        for domain_id, facts in routed.items():
            if domain_id not in self.holograms:
                self.holograms[domain_id] = Hologram64(domain_id)
            holo = self.holograms[domain_id]
            n_before = holo.n_ingested
            for text in facts:
                holo.ingest(text, amplitude=0.08)
                total_ingested += 1
            n_new = holo.n_ingested - n_before
            
            # Initialiser le SpectralEncoder pour le GATING uniquement
            if SPECTRAL_AVAILABLE and holo.fact_texts:
                holo._init_spectral_encoder()
                    
            print(f"  [{domain_id:15s}] {n_new:4d} faits -> total {holo.n_ingested:4d} | E={holo.energy:.0f}")

        dt = time.time() - t0
        print(f"\n  Total ingéré : {total_ingested} faits en {dt:.1f}s ({total_ingested/dt:.0f}/s)")
        print(f"{'=' * 60}")

        # Sauvegarder
        for holo in self.holograms.values():
            holo.save()

        return {"total": total_ingested, "time_seconds": round(dt, 1),
                "rate": round(total_ingested / dt, 0) if dt > 0 else 0}

    def audit_all(self):
        """Audit de tous les hologrammes."""
        print(f"\n{'=' * 60}")
        print(f"  AUDIT DE L'ENSEMBLE HOLOGRAPHIQUE")
        print(f"{'=' * 60}")
        for domain_id, holo in self.holograms.items():
            a = holo.audit()
            print(f"  {a['domain']:15s} | {a['size']} | E={a['energy']:.0f} | "
                  f"faits={a['n_facts']:3d} | densite={a['density']:.0f} | "
                  f"actif={a['nonzero_pct']}%")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="KA-Next -- Ensemble Holographique")
    parser.add_argument("--build-all", action="store_true", help="Construire tous les hologrammes")
    parser.add_argument("--query", type=str, default=None, help="Requete")
    parser.add_argument("--audit", action="store_true", help="Auditer l'ensemble")
    parser.add_argument("--demo", action="store_true", help="Demo interactive")

    args = parser.parse_args()

    ensemble = HolographicEnsemble()

    if args.build_all:
        ensemble.build_all(force_rebuild=True)
        ensemble.audit_all()

    elif args.query:
        ensemble.build_all(force_rebuild=False)
        result = ensemble.query(args.query)
        print(f"\n{'=' * 60}")
        print(f"  REPONSE : {args.query[:80]}")
        print(f"{'=' * 60}")
        print(result["text"])
        print(f"\n  Temps: {result['temps_ms']}ms | Confiance: {result['confidence']}")

    elif args.audit:
        ensemble.build_all(force_rebuild=False)
        ensemble.audit_all()

    elif args.demo:
        ensemble.build_all(force_rebuild=False)
        questions = [
            "Quelle est la capitale du Senegal ?",
            "Combien font 12 x 15 ?",
            "Qui a decouvert l'ADN ?",
            "Qu'est-ce que le stoicisme ?",
            "Quand a debute la Revolution francaise ?",
            "Quelle est la vitesse de la lumiere ?",
        ]
        for q in questions:
            print(f"\n{'=' * 60}")
            print(f"  Q: {q}")
            print(f"{'=' * 60}")
            result = ensemble.query(q)
            safe = result["text"][:400].encode('ascii', errors='replace').decode('ascii')
            print(safe)
            print(f"  --- {result['temps_ms']}ms | confiance={result['confidence']}")

    else:
        print("=" * 60)
        print("  KA-Next -- ENSEMBLE HOLOGRAPHIQUE")
        print(f"  {len(DOMAIN_DEFINITIONS)} domaines, hologrammes {HOLO_SIZE}x{HOLO_SIZE}")
        print("=" * 60)
        print("\nCommandes :")
        print("  python holographic_ensemble.py --build-all")
        print("  python holographic_ensemble.py --query \"...\"")
        print("  python holographic_ensemble.py --demo")
        print("  python holographic_ensemble.py --audit")


if __name__ == "__main__":
    main()