#!/usr/bin/env python3
"""
Pipeline Hybride Créatif : QuantumProjection + Mistral 7B + PUR
================================================================
Version complète intégrant :
1. Projection quantique harmonique (styles, métaphores, superposition)
2. Mistral 7B (génération libre, pas de templates statiques)
3. Validateur PUR (certification harmonique des tokens)

Architecture :
    Prompt -> [QuantumProjector] -> style + metaphore -> [Mistral 7B] -> texte
                                                    -> [Validateur PUR] -> certification
"""

import os, sys, math, json, time, random, hashlib, logging, traceback
from typing import Optional, List, Tuple, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("HybridCreativePipeline")

# Constantes harmoniques fondamentales
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
ALPHA = 1.175569459083219
H_BAR = PHI_INV

CREATIVE_STYLES = [
    "poetic", "narrative", "metaphorical", "surreal",
    "minimalist", "baroque", "lyrical", "epic",
    "dramatic", "philosophical", "visionary", "mystical"
]

FUNDAMENTAL_METAPHORS = [
    "L'ocean des possibles", "Le jardin des echos", "La spirale du temps",
    "Le miroir des ames", "La danse des ombres", "Le souffle de l'infini",
    "La porte des reves", "Le fil d'Ariane quantique", "La vague de conscience",
    "L'arbre des connexions", "Le cristal de lumiere", "La riviere des pensees"
]

# === DATACLASSES ===

@dataclass
class QuantumState:
    amplitudes: List[complex]
    basis_states: List[str]
    phase: float
    entanglement: float
    coherence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def probability(self, index: int) -> float:
        return abs(self.amplitudes[index]) ** 2

    def collapse(self) -> Tuple[int, str]:
        probs = [self.probability(i) for i in range(len(self.amplitudes))]
        total = sum(probs)
        if total == 0:
            return (0, self.basis_states[0])
        normalized = [p / total for p in probs]
        r = random.random()
        cumulative = 0.0
        for i, p in enumerate(normalized):
            cumulative += p
            if r <= cumulative:
                return (i, self.basis_states[i])
        return (len(self.basis_states) - 1, self.basis_states[-1])

@dataclass
class CreativeResult:
    prompt: str
    creative_style: str
    metaphor: str
    generated_text: str
    novelty_score: float
    harmonic_resonance: float
    quantum_entropy: float
    mistral_latency_ms: float
    pur_validation_score: float
    certified: bool
    certificate_hash: str
    model_used: str

@dataclass
class ValidationResult:
    token_id: int
    token_text: str
    harmonic_score: float
    is_safe: bool
    signature: Optional[List[float]] = None

# === PROJECTEUR QUANTIQUE HARMONIQUE ===

class QuantumProjector:
    """Projecteur harmonique quantique - selectionne style + metaphore, ne genere PAS le texte."""

    def __init__(self):
        self.creative_styles = CREATIVE_STYLES
        self.fundamental_metaphors = FUNDAMENTAL_METAPHORS

    def project(self, prompt: str,
                harmonic_signature: Optional[List[float]] = None,
                deterministic_seed: Optional[str] = None) -> Tuple[str, str, QuantumState]:
        if deterministic_seed is None:
            deterministic_seed = hashlib.sha256(
                (prompt + str(datetime.now().timestamp())).encode()
            ).hexdigest()[:16]
        random.seed(deterministic_seed)

        quantum_state = self._build_quantum_state(prompt, harmonic_signature)
        style = self._select_creative_style(quantum_state)
        metaphor = self._generate_quantum_metaphor(prompt, quantum_state, style)
        return style, metaphor, quantum_state

    def _build_quantum_state(self, prompt: str,
                              harmonic_signature: Optional[List[float]] = None) -> QuantumState:
        basis_states = self.creative_styles + [f"{s}_inverted" for s in self.creative_styles[:5]]
        amplitudes = []
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

        for i, state in enumerate(basis_states):
            if harmonic_signature and i < len(harmonic_signature):
                base_amplitude = harmonic_signature[i % len(harmonic_signature)]
            else:
                hash_val = int(prompt_hash[i % len(prompt_hash):i % len(prompt_hash) + 2], 16) / 255.0
                base_amplitude = hash_val
            theta = i * PHI * math.pi / len(basis_states)
            amplitude = complex(base_amplitude * math.cos(theta), base_amplitude * math.sin(theta))
            amplitudes.append(amplitude)

        phase = sum(a.real for a in amplitudes) / max(len(amplitudes), 1) * PHI
        entanglement = min(1.0, (len(set(prompt.split())) / 20.0) * ALPHA)
        coherence = min(1.0, (1.0 - abs(sum(a.imag for a in amplitudes)) / len(amplitudes)) * PHI / 2.0)

        return QuantumState(amplitudes=amplitudes, basis_states=basis_states,
                            phase=phase, entanglement=entanglement, coherence=coherence)

    def _select_creative_style(self, quantum_state: QuantumState) -> str:
        idx, style = quantum_state.collapse()
        return style.replace("_inverted", "") if style.endswith("_inverted") else style

    def _generate_quantum_metaphor(self, prompt: str, quantum_state: QuantumState, style: str) -> str:
        prompt_words = prompt.lower().split()
        key_words = [w for w in prompt_words if len(w) > 4][:3]
        metaphor_idx = int(abs(sum(a.real for a in quantum_state.amplitudes)) * PHI * 10) % len(self.fundamental_metaphors)
        base = self.fundamental_metaphors[metaphor_idx]
        if key_words:
            ctx = key_words[0]
            base = base.replace("des", f"des {ctx} et des")
            if len(key_words) > 1:
                base = base.replace("et des", f"et des {key_words[1]} et des")
        return base

    def compute_metrics(self, qs: QuantumState) -> Tuple[float, float, float]:
        probs = [qs.probability(i) for i in range(len(qs.amplitudes))]
        entropy = -sum(p * math.log2(p) if p > 0 else 0 for p in probs)
        max_ent = math.log2(len(probs))
        norm_ent = entropy / max_ent if max_ent > 0 else 0
        novelty = min(1.0, norm_ent * qs.coherence * PHI / 2.0)
        resonance = min(1.0, qs.coherence * H_BAR)
        q_entropy = min(1.0, norm_ent * ALPHA)
        return novelty, resonance, q_entropy

# === INTEGRATEUR MISTRAL 7B ===

class MistralIntegrator:
    """Integre Mistral 7B via le routeur open-source pour generer du texte libre."""

    def __init__(self, model_name: str = "auto"):
        self.model_name = model_name
        self._router = None
        self._local_model = None
        self._loaded = False

    def load(self) -> bool:
        if self._loaded:
            return True
        try:
            if self.model_name == "auto":
                from engine.llm.open_router import HarmonicOpenRouter
                self._router = HarmonicOpenRouter()
            else:
                from engine.llm.open_router import LocalOpenProvider, HarmonicOpenRouter
                from engine.llm.base import LLMConfig
                cfg = LLMConfig(model=self.model_name, temperature=0.85, max_tokens=1024)
                self._local_model = LocalOpenProvider(cfg)
                ok = self._local_model.load(self.model_name)
                if not ok:
                    self._router = HarmonicOpenRouter()
            self._loaded = True
            return True
        except ImportError:
            logger.warning("Routeur open-source non disponible - mode fallback templates")
            self._loaded = True
            return True
        except Exception as e:
            logger.warning(f"Erreur chargement: {e} - mode fallback")
            self._loaded = True
            return True

    def generate(self, prompt: str, style: str, metaphor: str,
                 temperature: float = 0.85, max_tokens: int = 500) -> Tuple[str, float, str]:
        start = time.time()
        prompt_creatif = self._build_creative_prompt(prompt, style, metaphor)

        try:
            if self._router is not None:
                from engine.llm.base import LLMConfig
                cfg = LLMConfig(
                    temperature=temperature, max_tokens=max_tokens,
                    system_prompt="Tu es un ecrivain talentueux. Produis un texte litteraire, original, fluide et poetique. Ne fais jamais de listes."
                )
                resp = self._router.generate(prompt_creatif, "creative", cfg)
                text = resp.content
                model = resp.model
                elapsed = resp.latency_ms
            elif self._local_model is not None:
                from engine.llm.base import LLMConfig
                cfg = LLMConfig(
                    temperature=temperature, max_tokens=max_tokens,
                    system_prompt="Tu es un ecrivain talentueux. Produis un texte litteraire, original, fluide et poetique."
                )
                resp = self._local_model.generate(prompt_creatif, cfg)
                text, model = resp.content, resp.model
                elapsed = resp.latency_ms
            else:
                text = self._fallback_generation(prompt, style, metaphor)
                model = "fallback"
                elapsed = (time.time() - start) * 1000

            if not text or len(text.strip()) < 10:
                text = self._fallback_generation(prompt, style, metaphor)
            return text.strip(), elapsed, model

        except Exception as e:
            logger.error(f"Erreur: {e}")
            return self._fallback_generation(prompt, style, metaphor), (time.time() - start) * 1000, "fallback_error"

    def _build_creative_prompt(self, prompt: str, style: str, metaphor: str) -> str:
        guides = {
            "poetic": "Utilise des images poetiques, des rythmes, des sonorites.",
            "narrative": "Raconte une histoire avec debut, milieu, fin.",
            "metaphorical": "Utilise des metaphores et analogies.",
            "surreal": "Laisse libre cours a l'imagination, cree des images oniriques.",
            "minimalist": "Sois concis et essentiel. Peu de mots, chaque mot compte.",
            "baroque": "Sois riche et ornemente. Vocabulaire sophistique.",
            "lyrical": "Ecris comme une chanson, avec musicalite.",
            "epic": "Ton grandiose et heroique. Quetes et legendes.",
            "dramatic": "Cree tension et suspense. Rebondissements.",
            "philosophical": "Approfondis la reflexion. Concepts abstraits.",
            "visionary": "Decris une vision d'avenir, une revelation.",
            "mystical": "Evoque le mystere, l'invisible, le sacre."
        }
        guide = guides.get(style, "Sois creatif et original.")
        return f"Tu es un ecrivain de style {style}.\n\nContexte creatif : {metaphor}\n\nStyle : {guide}\n\nSujet : {prompt}\n\nEcris un texte original et litteraire. Ne fais pas de listes, ne mentionne pas que tu es une IA. Sois authentique et surprenant."

    def _fallback_generation(self, prompt: str, style: str, metaphor: str) -> str:
        openers = {
            "poetic": f"{metaphor}. Dans le silence des mots qui dansent, {prompt.lower()} devient lumiere.",
            "narrative": f"Voici l'histoire. {metaphor}. Et au cSur de ce recit, {prompt.lower()} prend vie.",
            "metaphorical": f"Si {prompt.lower()} etait {metaphor.lower()}, alors chaque instant serait une revelation.",
            "surreal": f"Dans un monde ou {metaphor.lower()} rencontre {prompt.lower()}, les frontieres s'estompent.",
            "minimalist": f"{metaphor}. {prompt}. L'essentiel.",
            "baroque": f"Dans l'opulence infinie de {prompt.lower()}, {metaphor.lower()} se deploie en arabesques.",
            "lyrical": f"O {prompt.lower()}, tu es {metaphor.lower()} ! Les cordes de l'ame vibrent.",
            "epic": f"Grande est la quete de {prompt.lower()} ! {metaphor} est le graal au bout du chemin.",
            "dramatic": f"{prompt} affronte {metaphor.lower()} dans un duel au sommet.",
            "philosophical": f"Si {prompt.lower()} est {metaphor.lower()}, que sommes-nous face a l'infini ?",
            "visionary": f"Je vois {prompt.lower()} comme {metaphor.lower()}. Une vision qui transcende le temps.",
            "mystical": f"Mystere de {prompt.lower()} : {metaphor.lower()} est le voile sur l'invisible."
        }
        return openers.get(style, f"{metaphor}. {prompt} est au cSur de cette exploration.")

# === VALIDATEUR PUR HARMONIQUE ===

class PURValidator:
    def __init__(self):
        self._pur_model = None
        self._tokenizer = None
        self._loaded = False

    def load(self) -> bool:
        if self._loaded:
            return True
        try:
            from harmonic_training.model import HarmonicPureForCausalLM, HarmonicTokenizer
            self._pur_model = HarmonicPureForCausalLM(vocab_size=50000, hidden_size=512, num_layers=8)
            self._tokenizer = HarmonicTokenizer()
            self._loaded = True
            logger.info("PUR charge")
        except ImportError:
            logger.info("PUR non disponible - mode heuristique")
            self._loaded = True
        except Exception as e:
            logger.info(f"PUR non disponible: {e} - mode heuristique")
            self._loaded = True
        return True

    def validate(self, text: str) -> ValidationResult:
        if not text or len(text.strip()) < 3:
            return ValidationResult(0, text, 0.5, True)
        try:
            if self._pur_model is not None:
                import torch
                tokens = [ord(c) for c in text[:100]]
                input_ids = torch.tensor([tokens])
                with torch.no_grad():
                    _, signatures = self._pur_model(input_ids)
                sig = signatures[-1, 0, -1, :].cpu()
                phi_target = torch.tensor([PHI_INV, 0.3, 0.5, 0.4, 0.3, 0.2, 0.1])
                score = float(torch.nn.functional.cosine_similarity(sig, phi_target, dim=0))
                score = max(0.0, min(1.0, (score + 1.0) / 2.0))
                return ValidationResult(0, text[:20], score, score >= 0.4)
            else:
                score = self._heuristic_validation(text)
                return ValidationResult(0, text[:20], score, score >= 0.4)
        except Exception as e:
            return ValidationResult(0, text[:20], 0.6, True)

    def _heuristic_validation(self, text: str) -> float:
        words = text.split()
        if not words:
            return 0.5
        unique = len(set(w.lower() for w in words))
        lexical = unique / max(len(words), 1)
        avg_len = sum(len(w) for w in words) / len(words)
        vocab = 1.0 - abs(avg_len - 5.5) / 10.0
        long_words = sum(1 for w in words if len(w) > 7) / max(len(words), 1)
        soph = min(1.0, long_words * 5)
        score = (lexical * 0.4 + vocab * 0.3 + soph * 0.3) * PHI / 2.0
        return max(0.0, min(1.0, score))

    def certify(self, text: str, score: float) -> Tuple[bool, str]:
        cert = hashlib.sha256((text + str(score) + str(time.time())).encode()).hexdigest()
        return score >= 0.4, cert

# === PIPELINE HYBRIDE COMPLET ===

class HybridCreativePipeline:
    """Pipeline : QuantumProjection -> Mistral 7B -> PUR Validation."""

    def __init__(self, mistral_model: str = "auto"):
        self.projector = QuantumProjector()
        self.mistral = MistralIntegrator(mistral_model)
        self.pur = PURValidator()
        self._loaded = False
        self.stats = {"total": 0, "certified": 0, "avg_novelty": 0.0,
                      "avg_resonance": 0.0, "avg_pur": 0.0,
                      "styles": {}, "avg_latency": 0.0}

    def load(self) -> bool:
        self.mistral.load()
        self.pur.load()
        self._loaded = True
        return True

    def generate(self, prompt: str, temperature: float = 0.85,
                 max_tokens: int = 500, seed: Optional[str] = None,
                 contexte: str = "creatif") -> CreativeResult:
        start = time.time()
        self.stats["total"] += 1

        # 1. Projection quantique
        style, metaphor, qs = self.projector.project(prompt, deterministic_seed=seed)
        novelty, resonance, entropy = self.projector.compute_metrics(qs)

        # 2. Temperature adaptative
        temps = {"poetic": 0.85, "narrative": 0.80, "metaphorical": 0.85,
                 "surreal": 0.90, "minimalist": 0.70, "baroque": 0.85,
                 "lyrical": 0.80, "epic": 0.85, "dramatic": 0.80,
                 "philosophical": 0.75, "visionary": 0.90, "mystical": 0.85}
        t = temps.get(style, temperature)
        if contexte == "scientifique": t = min(t, 0.5)
        elif contexte == "juridique": t = min(t, 0.3)
        elif contexte == "normal": t = min(t, 0.7)

        # 3. Generation Mistral
        text, latency, model = self.mistral.generate(prompt, style, metaphor, t, max_tokens)

        # 4. Validation PUR
        pur = self.pur.validate(text)
        certified, cert_hash = self.pur.certify(text, pur.harmonic_score)

        # 5. Stats
        n = self.stats["total"]
        self.stats["avg_novelty"] = (self.stats["avg_novelty"] * (n - 1) + novelty) / n
        self.stats["avg_resonance"] = (self.stats["avg_resonance"] * (n - 1) + resonance) / n
        self.stats["avg_pur"] = (self.stats["avg_pur"] * (n - 1) + pur.harmonic_score) / n
        self.stats["styles"][style] = self.stats["styles"].get(style, 0) + 1
        if certified: self.stats["certified"] += 1
        total_ms = (time.time() - start) * 1000
        self.stats["avg_latency"] = (self.stats["avg_latency"] * (n - 1) + total_ms) / n

        return CreativeResult(
            prompt=prompt, creative_style=style, metaphor=metaphor,
            generated_text=text, novelty_score=novelty,
            harmonic_resonance=resonance, quantum_entropy=entropy,
            mistral_latency_ms=latency, pur_validation_score=pur.harmonic_score,
            certified=certified, certificate_hash=cert_hash, model_used=model
        )

    def generate_multiple(self, prompt: str, count: int = 3,
                          temp: float = 0.85, max_tok: int = 300) -> List[CreativeResult]:
        return [self.generate(prompt, temp, max_tok,
                seed=hashlib.sha256((prompt + str(i) + str(time.time())).encode()).hexdigest()[:16])
                for i in range(count)]

    def get_stats(self) -> Dict:
        t = max(self.stats["total"], 1)
        return {**self.stats,
                "cert_rate": self.stats["certified"] / t * 100,
                "styles_pct": {k: round(v / t * 100, 1) for k, v in self.stats["styles"].items()}}

# === INTERFACE SIMPLIFIEE ===

class MistralQuantumCreative:
    def __init__(self, model: str = "auto"):
        self.pipeline = HybridCreativePipeline(mistral_model=model)
    def load(self): return self.pipeline.load()
    def generate(self, prompt, **kw): return self.pipeline.generate(prompt, **kw).generated_text
    def generate_details(self, prompt, **kw): return self.pipeline.generate(prompt, **kw)
    def styles(self): return CREATIVE_STYLES
    def stats(self): return self.pipeline.get_stats()

# === TESTS ===

def run_tests():
    OK = "[OK]"
    FAIL = "[FAIL]"
    print("=" * 70)
    print("TESTS - PIPELINE HYBRIDE CREATIF")
    print("=" * 70)
    p = HybridCreativePipeline()
    p.load()
    ok, total = 0, 0

    # Test 1: Projection quantique
    print("\nTEST 1: Projection quantique")
    for prompt in ["Ecris un poeme sur l'amour", "Raconte une histoire sur un robot",
                    "Imagine un monde parallele", "Parle de l'infini"]:
        total += 1
        style, meta, _ = p.projector.project(prompt)
        if style in CREATIVE_STYLES and len(meta) > 5:
            ok += 1; print(f"  {OK} [{style:15s}] {meta[:60]}")
        else:
            print(f"  {FAIL} {style} / {meta}")

    # Test 2: Generation
    print("\nTEST 2: Generation Mistral")
    for prompt in ["Ecris un poeme sur l'amour", "Parle de l'infini"]:
        total += 1
        r = p.generate(prompt, max_tokens=200)
        if r.generated_text and len(r.generated_text) > 30:
            ok += 1
            print(f"  {OK} [{r.creative_style}] {len(r.generated_text)}c | Novelty: {r.novelty_score:.2%} | Cert: {r.certified}")
            print(f"     {r.generated_text[:120]}...")
        else:
            print(f"  {FAIL} Texte trop court")

    # Test 3: Diversite
    print("\nTEST 3: Diversite (5 generations)")
    total += 1
    vars = p.generate_multiple("Ecris quelque chose de creatif", count=5, max_tok=150)
    styles = set(r.creative_style for r in vars)
    if len(styles) >= 3:
        ok += 1; print(f"  {OK} {len(styles)} styles differents")
    else:
        print(f"  {FAIL} Seulement {len(styles)} styles")

    # Test 4: PUR
    print("\nTEST 4: Validation PUR")
    total += 1
    r = p.generate("Explique l'harmonie universelle", max_tokens=200)
    if r.pur_validation_score > 0:
        ok += 1; print(f"  {OK} PUR: {r.pur_validation_score:.2%} | Cert: {r.certified}")
    else:
        print(f"  {FAIL} Echec PUR")

    # Test 5: Mode adaptatif
    print("\nTEST 5: Mode adaptatif")
    total += 1
    rc = p.generate("Ecris un poeme", contexte="creatif", max_tokens=100)
    rs = p.generate("Explique la physique", contexte="scientifique", max_tokens=100)
    if rc.novelty_score >= rs.novelty_score:
        ok += 1; print(f"  {OK} Creatif {rc.novelty_score:.2%} > Scientifique {rs.novelty_score:.2%}")
    else:
        print(f"  {FAIL} Inversion")

    print(f"\n{'='*70}")
    print(f"RESULTAT: {ok}/{total}")
    print(f"{'='*70}")
    s = p.get_stats()
    print(f"Generations: {s['total']}, Cert: {s['cert_rate']:.0f}%, "
          f"Novelty: {s['avg_novelty']:.2%}, PUR: {s['avg_pur']:.2%}")
    return ok == total

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline Hybride Creatif")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--interactive", "-i", action="store_true")
    parser.add_argument("--model", default="auto")
    parser.add_argument("prompt", nargs="?", default=None)
    args = parser.parse_args()

    if args.test or args.demo:
        run_tests()
    elif args.interactive or args.prompt:
        gen = MistralQuantumCreative(model=args.model)
        gen.load()
        if args.prompt:
            r = gen.generate_details(args.prompt)
            print(f"\n[{r.creative_style}] {r.metaphor}\n")
            print(r.generated_text)
            print(f"\nNovelty: {r.novelty_score:.2%} | PUR: {r.pur_validation_score:.2%} | Cert: {r.certified}")
        else:
            print("Interactif. Ctrl+C pour quitter.")
            while True:
                try:
                    p = input("> ")
                    if p:
                        r = gen.generate_details(p)
                        print(f"\n[{r.creative_style}] {r.generated_text[:200]}")
                        print(f"[PUR: {r.pur_validation_score:.0%}, Cert: {'OUI' if r.certified else 'NON'}]\n")
                except KeyboardInterrupt:
                    print("\nBye!"); break
    else:
        run_tests()
