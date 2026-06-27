#!/usr/bin/env python3
"""
Benchmark : Boucle hologramme -> generation.
Compare la qualite des reponses AVEC et SANS hologramme.

Usage:
    python benchmark_boucle_hologramme.py
"""

import time
import sys
import os

# Ajouter le repertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from engine.harmonic_engine import (
        HarmonicResonanceEngine, HarmonicGenerator, HarmonicAnalyzer
    )
except ImportError as e:
    print(f"ERREUR import: {e}")
    sys.exit(1)


# =========================================================================
# Configuration
# =========================================================================

PROMPTS = [
    # (prompt, description)
    ("Explique le concept de relativite", "relativite"),
    ("Parle-moi de l'empire du Ghana", "empire Ghana"),
    ("Qu'est-ce que la conscience ?", "conscience"),
    ("Comment fonctionne l'apprentissage profond ?", "deep learning"),
    ("Quelle est l'importance du nombre d'or en mathematiques ?", "nombre d'or"),
    ("Explique la theorie des cordes", "theorie cordes"),
    ("Decris le cycle de l'eau", "cycle eau"),
    ("Comment se forme un arc-en-ciel ?", "arc-en-ciel"),
    ("Quels sont les principes de la mecanique quantique ?", "meca quantique"),
    ("Parle-moi de l'intelligence artificielle", "IA"),
]

N_REPETITIONS = 2  # Chaque prompt est repete N fois pour stabilite


# =========================================================================
# Metriques
# =========================================================================

class Metriques:
    """Collecte et analyse les metriques de benchmark."""
    
    def __init__(self):
        self.resultats = []
    
    def ajouter(self, prompt: str, desc: str, engine_type: str,
                 temps_ms: float, longueur: int, knowledge_used: bool,
                 top_tokens: list = None, resonance_temps: float = 0.0):
        """Ajoute un resultat de test."""
        self.resultats.append({
            "prompt": prompt,
            "description": desc,
            "engine_type": engine_type,
            "temps_ms": temps_ms,
            "longueur": longueur,
            "knowledge_used": knowledge_used,
            "top_tokens": top_tokens or [],
            "resonance_temps": resonance_temps,
        })
    
    def rapport(self) -> str:
        """Genere un rapport de synthese."""
        if not self.resultats:
            return "Aucun resultat."
        
        lignes = []
        lignes.append("=" * 70)
        lignes.append("BENCHMARK : Boucle Hologramme -> Generation")
        lignes.append("=" * 70)
        
        # Separer par type
        avec_holo = [r for r in self.resultats if r["engine_type"] == "avec_hologramme"]
        sans_holo = [r for r in self.resultats if r["engine_type"] == "sans_hologramme"]
        
        # Vérifier qu'on a des données comparables
        if not avec_holo or not sans_holo:
            lignes.append("\n[ATTENTION] Donnees incompletes pour la comparaison")
        
        # --- Stats globales ---
        lignes.append("\n--- Statistiques globales ---")
        for etype, group in [("AVEC hologramme", avec_holo), ("SANS hologramme", sans_holo)]:
            if not group:
                continue
            temps_moyen = sum(r["temps_ms"] for r in group) / len(group)
            long_moyenne = sum(r["longueur"] for r in group) / len(group)
            n_knowledge = sum(1 for r in group if r["knowledge_used"])
            lignes.append(f"  {etype:20s}: {len(group):3d} reps | "
                         f"temps moy={temps_moyen:8.1f}ms | "
                         f"long moy={long_moyenne:6.1f}c | "
                         f"knowledge={n_knowledge}/{len(group)}")
        
        # --- Comparaison par prompt ---
        lignes.append("\n--- Comparaison par prompt ---")
        for desc in sorted(set(r["description"] for r in self.resultats)):
            avec = [r for r in avec_holo if r["description"] == desc]
            sans = [r for r in sans_holo if r["description"] == desc]
            
            if avec and sans:
                a = avec[0]
                s = sans[0]
                diff_temps = a["temps_ms"] - s["temps_ms"]
                diff_long = a["longueur"] - s["longueur"]
                
                # Overhead hologramme
                overhead = ""
                if a.get("resonance_temps", 0) > 0:
                    overhead = f" (dont resonance={a['resonance_temps']:.0f}ms)"
                
                lignes.append(
                    f"  [{desc:20s}] avec={a['temps_ms']:6.1f}ms{overhead} | "
                    f"sans={s['temps_ms']:6.1f}ms | "
                    f"delta={diff_temps:+7.1f}ms | "
                    f"long={a['longueur']:+d}c"
                )
            elif avec:
                lignes.append(f"  [{desc:20s}] (avec seulement) temps={avec[0]['temps_ms']:.1f}ms")
            elif sans:
                lignes.append(f"  [{desc:20s}] (sans seulement) temps={sans[0]['temps_ms']:.1f}ms")
        
        # --- Analyse des tokens extraits ---
        lignes.append("\n--- Analyse des tokens extraits (top-3 par prompt) ---")
        for r in avec_holo[:10]:  # 10 premiers prompts
            tokens = r.get("top_tokens", [])
            if tokens:
                top3 = [(t[0], round(t[1], 3)) for t in tokens[:3]]
                lignes.append(
                    f"  [{r['description']:20s}] {top3}"
                )
            else:
                lignes.append(f"  [{r['description']:20s}] (aucun token extrait)")
        
        # --- Resume ---
        lignes.append("\n--- Resume ---")
        if avec_holo and sans_holo:
            n_holo = len(avec_holo)
            n_sans = len(sans_holo)
            n = min(n_holo, n_sans)
            
            temps_avec = sum(r["temps_ms"] for r in avec_holo[:n]) / n
            temps_sans = sum(r["temps_ms"] for r in sans_holo[:n]) / n
            
            # Overhead
            temps_resonance_moyen = sum(
                r.get("resonance_temps", 0) for r in avec_holo
            ) / max(len(avec_holo), 1)
            
            lignes.append(
                f"  Overhead resonance: {temps_resonance_moyen:.1f}ms en moyenne"
            )
            lignes.append(
                f"  Temps total AVEC:  {temps_avec:.1f}ms (dont {temps_resonance_moyen:.1f}ms resonance)"
            )
            lignes.append(
                f"  Temps total SANS: {temps_sans:.1f}ms"
            )
            lignes.append(
                f"  Ratio: {temps_avec/max(temps_sans, 0.1):.2f}x"
            )
        
        lignes.append("=" * 70)
        return "\n".join(lignes)


# =========================================================================
# Benchmark principal
# =========================================================================

def run_benchmark():
    """Execute le benchmark complet."""
    print("=" * 70)
    print("BENCHMARK : Boucle Hologramme -> Generation")
    print("=" * 70)
    
    # Creer les deux moteurs
    print("\n[1/3] Initialisation des moteurs...")
    
    print("  Creation du moteur SANS hologramme...")
    engine_sans = HarmonicResonanceEngine(use_hologram=False)
    
    print("  Creation du moteur AVEC hologramme...")
    engine_avec = HarmonicResonanceEngine(use_hologram=True)
    
    print(f"  Hologramme charge: {engine_avec.hologram_loaded}")
    
    metriques = Metriques()
    
    # Benchmark
    print(f"\n[2/3] Execution du benchmark ({len(PROMPTS)} prompts x {N_REPETITIONS} repetitions)...")
    
    for i, (prompt, desc) in enumerate(PROMPTS):
        # Afficher la progression
        print(f"\r  [{i+1}/{len(PROMPTS)}] {desc:25s}...", end="", flush=True)
        
        for rep in range(N_REPETITIONS):
            # --- SANS hologramme ---
            t0 = time.time()
            result_sans = engine_sans.chat(prompt)
            dt_sans = (time.time() - t0) * 1000
            
            metriques.ajouter(
                prompt=prompt,
                desc=desc,
                engine_type="sans_hologramme",
                temps_ms=dt_sans,
                longueur=len(result_sans["response"]),
                knowledge_used=False,
            )
            
            # --- AVEC hologramme ---
            t0 = time.time()
            result_avec = engine_avec.chat(prompt)
            dt_avec = (time.time() - t0) * 1000
            
            resonance_temps = 0.0
            if result_avec.get("knowledge_used") and "knowledge_stats" in result_avec:
                resonance_temps = result_avec["knowledge_stats"].get("temps_ms", 0)
            
            top_tokens = []
            if result_avec.get("knowledge_used") and "knowledge_stats" in result_avec:
                top_tokens = result_avec["knowledge_stats"].get("top_tokens", [])
            
            metriques.ajouter(
                prompt=prompt,
                desc=desc,
                engine_type="avec_hologramme",
                temps_ms=dt_avec,
                longueur=len(result_avec["response"]),
                knowledge_used=result_avec.get("knowledge_used", False),
                top_tokens=top_tokens,
                resonance_temps=resonance_temps,
            )
    
    print()  # Nouvelle ligne apres la progression
    
    # Rapport
    print(f"\n[3/3] Generation du rapport...")
    rapport = metriques.rapport()
    print(f"\n{rapport}")
    
    # Sauvegarder le rapport
    rapport_path = "benchmark_boucle_hologramme_results.txt"
    with open(rapport_path, "w", encoding="utf-8") as f:
        f.write(rapport)
    print(f"\nRapport sauvegarde dans: {rapport_path}")
    
    return metriques


if __name__ == '__main__':
    run_benchmark()
