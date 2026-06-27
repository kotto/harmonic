#!/usr/bin/env python3
"""
GENERATE 1M HOLOGRAPHIC — Multi-couche par cycles d'amplitude
================================================================
Stratégie pour 500K+ en 8h sans arret :
  Cycle 1 (amp 0.04) : ~83K QA
  Cycle 2 (amp 0.02) : ~83K QA  
  Cycle 3 (amp 0.01) : ~83K QA
  ...continue jusqu'a 500K+
  
Chaque cycle reutilise les memes templates avec une amplitude
decroissante, creant des couches de resonance sans ecraser.

Usage :
  python ka_phone/generate_1m_holographic.py                    # Lance vers 500K
  python ka_phone/generate_1m_holographic.py --status            # Voir l'etat
"""

import os, sys, json, time, hashlib
import numpy as np

HOLOGRAM_SIZE = 256
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "holographic_1m")
HOLOGRAM_FILE = os.path.join(DATA_DIR, "hologram_1m.npy")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "checkpoint_1m.json")
os.makedirs(DATA_DIR, exist_ok=True)

QUESTION_TEMPLATES_FR = [
    "Qu'est-ce que {sujet} ?", "C'est quoi {sujet} ?", "Que signifie {sujet} ?",
    "Qui est {sujet} ?", "Qui etait {sujet} ?", "Peux-tu me parler de {sujet} ?",
    "Ou se trouve {sujet} ?", "Ou est {sujet} ?", "Dans quel pays se situe {sujet} ?",
    "Quand a eu lieu {sujet} ?", "En quelle annee {sujet} ?", "A quelle date {sujet} ?",
    "Comment fonctionne {sujet} ?", "Comment ca marche {sujet} ?", "Peux-tu expliquer {sujet} ?",
    "Pourquoi {sujet} est-il important ?", "Pourquoi {sujet} est-il celebre ?",
    "Combien de {sujet} ?", "Quel est le nombre de {sujet} ?",
    "Tu sais quoi sur {sujet} ?", "Des infos sur {sujet} ?", "Tu connais {sujet} ?",
    "Parle-moi de {sujet}", "Explique-moi {sujet}", "Dis-moi tout sur {sujet}",
]
QUESTION_TEMPLATES_EN = [
    "What is {subject}?", "Who is {subject}?", "Where is {subject}?",
    "When was {subject}?", "How does {subject} work?", "Why is {subject} important?",
    "Tell me about {subject}", "I want to know about {subject}", "Can you explain {subject}?",
]
WRAPPERS = [
    lambda q: q, lambda q: f"Je voudrais savoir : {q}", lambda q: f"Dis-moi : {q}",
    lambda q: f"Une question : {q}", lambda q: f"Peux-tu me dire : {q}",
    lambda q: f"J'ai une question : {q}", lambda q: f"J'aimerais comprendre : {q}",
]


class HolographicMillionGenerator:
    def __init__(self):
        self.hologram = np.load(HOLOGRAM_FILE) if os.path.exists(HOLOGRAM_FILE) else np.zeros((HOLOGRAM_SIZE, HOLOGRAM_SIZE), dtype=np.complex128)
        cp = json.load(open(CHECKPOINT_FILE)) if os.path.exists(CHECKPOINT_FILE) else {"cycle": 0, "stats": {"total_qa": 0}}
        self.stats = cp.get("stats", {"total_qa": 0})
        self.cycle_num = cp.get("cycle", 0)

    def _text_to_wave(self, text: str, amp: float = 0.05) -> np.ndarray:
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        ky = (int(h[16:32], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        kx = (kx - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
        ky = (ky - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
        x = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        y = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        X, Y = np.meshgrid(x, y)
        env = np.exp(-(X**2 + Y**2) / 18)
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
        return amp * env * wave

    def _save(self):
        np.save(HOLOGRAM_FILE, self.hologram)
        cp = {"cycle": self.cycle_num, "stats": self.stats,
              "energy": float(np.sum(np.abs(self.hologram)**2)),
              "density": float(np.mean(np.abs(self.hologram))),
              "last_saved": time.strftime("%Y-%m-%d %H:%M:%S")}
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(cp, f, ensure_ascii=False)

    def run_cycle(self, amplitude: float):
        sys.path.insert(0, os.path.dirname(__file__))
        from quick_facts import FACTS
        tmpls = QUESTION_TEMPLATES_FR + QUESTION_TEMPLATES_EN
        total = self.stats.get("total_qa", 0)
        for fid, (_, fact_text, keywords) in enumerate(FACTS):
            sujet = max(keywords, key=len).replace("_", " ").capitalize() if keywords else fact_text[:40]
            for t in tmpls:
                q = t.format(sujet=sujet, subject=sujet).replace("{sujet}", sujet)
                for w in WRAPPERS:
                    qw = w(q).strip()
                    self.hologram += self._text_to_wave(qw, amp=amplitude * 0.5)
                    self.hologram += self._text_to_wave(fact_text, amp=amplitude)
                    total += 1
                    if total % 2000 == 0:
                        mx = np.max(np.abs(self.hologram))
                        if mx > 500: self.hologram *= 0.98
        self.stats["total_qa"] = total
        self._save()

    def generate_for_8h(self):
        amplitudes = [0.04, 0.02, 0.01, 0.005, 0.0025, 0.0012]
        start = self.cycle_num
        # Start from whichever cycle was last saved (0 = fresh start)
        pass
        for i, amp in enumerate(amplitudes):
            if i < start: continue
            self.cycle_num = i + 1
            print(f"Cycle {i+1}/{len(amplitudes)} amp={amp:.4f} | QA={self.stats['total_qa']:,}")
            t0 = time.time()
            self.run_cycle(amplitude=amp)
            print(f"  -> {self.stats['total_qa']:,} QA ({time.time()-t0:.0f}s)")
        self._save()

    def get_status(self):
        return {"total_qa": self.stats.get("total_qa", 0), "cycle": self.cycle_num,
                "energy": float(np.sum(np.abs(self.hologram)**2)) if np.any(self.hologram) else 0,
                "density": float(np.mean(np.abs(self.hologram))),
                "last_saved": time.strftime("%Y-%m-%d %H:%M:%S")}


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--status", action="store_true")
    args = p.parse_args()
    gen = HolographicMillionGenerator()
    if args.status:
        s = gen.get_status()
        print(f"QA: {s['total_qa']:,} | Cycle: {s['cycle']} | E: {s['energy']:.0f} | Densite: {s['density']:.4f} | Save: {s['last_saved']}")
        return
    gen.generate_for_8h()


if __name__ == "__main__":
    main()