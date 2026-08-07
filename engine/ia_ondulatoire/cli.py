# -*- coding: utf-8 -*-
"""
cli.py — Dialogue interactif avec la nouvelle IA ondulatoire.

    python cli.py

Commandes :
    /aide         — aide
    /memorise X est Y — apprendre un fait
    /sauve        — persister la mémoire
    /charge       — recharger la mémoire depuis le disque
    /etat         — statistiques de l'IA
    /quitter      — quitter

Chaque question suit la boucle fermée (§8.1) : le programme ondulatoire généré
est affiché avant la réponse — l'IA écrit réellement dans sa langue natale.
"""

from __future__ import annotations

import sys

import ir
from cerveau import IaOndulatoire


def _barre(texte: str) -> None:
    print("─" * 60)


def principal() -> None:
    ia = IaOndulatoire(charger=True)
    print()
    print("🌊  IA ONDULATOIRE — langage natif : ENCODE → MANIPULER → DÉCODER")
    print(f"    Mémoire : {ia.H_faits.nb_faits} faits appris · "
          f"{len(ia.vocabulaire)} mots au vocabulaire · ℂ⁵¹²")
    print("    Tape /aide pour les commandes, /quitter pour sortir.")
    print()
    while True:
        try:
            question = input("❓ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n🌊 Au revoir !")
            sys.exit(0)
        if not question:
            continue
        if question in ("/quitter", "/quit", "/exit", "exit", "quit"):
            print("🌊 Au revoir ! Que tes ondes restent cohérentes.")
            sys.exit(0)
        if question == "/aide":
            print("   /memorise <fait> — « /memorise la lumière est une onde »")
            print("   /sauve · /charge · /etat · /quitter")
            continue
        if question.startswith("/memorise "):
            r = ia.memoriser(question[len("/memorise "):])
            print(f"💾 {r['response']}")
            continue
        if question == "/sauve":
            chemin = ia.sauvegarder()
            print(f"💾 Mémoire sauvegardée dans {chemin}")
            continue
        if question == "/charge":
            ok = ia.charger()
            print(f"💾 {('Mémoire rechargée' if ok else 'Aucune mémoire sur disque')}")
            continue
        if question == "/etat":
            for cle, val in ia.stats().items():
                print(f"   {cle:<22} : {val}")
            continue

        r = ia.poser(question)
        print()
        _barre("")
        print("🌊 Programme ondulatoire généré :")
        print(r.get("programme", ""))
        _barre("")
        print(f"🤖 {r['response']}")
        print(f"   [confiance {r['confidence']:.2f} · intention {r.get('intention', '?')} · "
              f"{r['latency_ms']} ms]")
        print()


if __name__ == "__main__":
    principal()
