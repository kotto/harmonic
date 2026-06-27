#!/usr/bin/env python3
"""
Intent Router — Classifies user input into action types
========================================================
Detects: question, command (sms/call/alarm/calendar/open/weather/note/search), reminder

Returns dict with:
  - type: "question", "command", "reminder", "greeting"
  - action: "sms", "call", "alarm", "calendar", "weather", "note", "search", "open_app"
  - params: extracted parameters (contact, time, text, etc.)
  - confidence: 0-1

Usage: from intent_router import IntentRouter
       router = IntentRouter()
       result = router.route("Envoie un SMS à Marie pour dire que je serai en retard")
"""

import re, os, sys
from typing import Dict, Any, Optional

class IntentRouter:
    """Routes user input to the correct handler."""
    
    # ── COMMAND PATTERNS ──
    COMMANDS = {
        "sms": [
            r"(?:envoie|envoi|envoies|envoyer)\s+(?:un\s+)?(?:sms|message|texto)\s+(?:a|à)\s+(.+?)(?:\s*(?:pour|disant|:)\s+(.+))?",
            r"(?:sms|message|texto)\s+(?:a|à)\s+(.+?)(?:\s*:\s*(.+))?",
            r"(?:ecris|ecrire|ecrit)\s+(?:a|à)\s+(.+?)(?:\s*(?:pour|disant|:)\s+(.+))?",
        ],
        "call": [
            r"(?:appelle|appeler|appel|telephone|telephoner)\s+(?:a|à\s+)?(.+)",
            r"(?:passe|passer)\s+(?:un\s+)?coup\s+(?:de\s+)?fil\s+(?:a|à)\s+(.+)",
        ],
        "alarm": [
            r"(?:reveille|reveiller|reveil|alarme|alarm)\s+(?:moi\s+)?(?:a|à)\s+(.+?)(?:\s+(?:demain|aujourd'hui|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche))?",
            r"(?:met|mets|mettre|programme|programmer)\s+(?:un\s+)?(?:reveil|alarme)\s+(?:a|à|pour)\s+(.+)",
            r"(?:rappelle|rappeler)\s+(?:moi|nous)?\s+(?:de|d')\s+(.+?)(?:\s+(?:a|à)\s+(.+))?",
        ],
        "calendar": [
            r"(?:ajoute|ajouter|ajout|note|noter|notes)\s+(?:un\s+)?(?:rdv|rendez-vous|evenement|evenement)\s+(.+?)(?:\s+(?:le|a|à)\s+(.+))?",
            r"(?:agenda|calendrier)\s+(?:ajoute|ajouter)\s+(.+)",
        ],
        "note": [
            r"(?:note|noter|notes|enregistre|sauvegarde|memo)\s*[:\s]+(.+)",
            r"(?:prend|prends|prendre)\s+(?:une\s+)?note\s*[:\s]+(.+)",
        ],
        "search": [
            r"(?:cherche|recherche|chercher|rechercher|trouve|trouver)\s+(?:sur\s+internet\s+)?(.+)",
            r"(?:google|googlise|googliser)\s+(.+)",
        ],
        "weather": [
            r"(?:meteo|meteo|temps|weather)\s+(?:a|à|de|pour|dans)?\s*(.+)?",
            r"(?:quel|quelle)\s+(?:est\s+)?(?:le\s+)?(?:temps|meteo)\s+(?:a|à|de|pour|dans)?\s*(.+)?",
            r"(?:pleut|pleuvoir|neige|neiger)\s+(?:il\s+)?(?:a|à)?\s*(.+)?",
        ],
        "open_app": [
            r"(?:ouvre|ouvrir|lancer|lance|demarre|demarrer)\s+(?:l'|la |le |les )?(?:appli(?:cation)?\s+)?(.+)",
        ],
        "music": [
            r"(?:joue|jouer|mets|mettre|passe|passer|lance|lancer)\s+(?:de\s+la\s+|du\s+|un\s+|une\s+)?(?:musique|chanson|morceau|playlist|son|album)\s*(?:de\s+)?(.+)?",
        ],
    }
    
    # ── REMINDER PATTERNS ──
    REMINDERS = [
        r"(?:rappelle|rappeler|souviens|souvenir)\s+(?:moi|nous)?\s+(?:de|d')\s+(.+?)(?:\s+(?:demain|aujourd'hui|ce\s+soir|plus\s+tard))?",
        r"(?:n'oublie|oublie|oublier)\s+pas\s+(?:de\s+)?(.+)",
        r"(?:pense|penser)\s+(?:a|à)\s+(.+)",
    ]
    
    # ── GREETING PATTERNS ──
    GREETINGS = [
        r"^(?:bonjour|salut|coucou|hey|hello|hi|yo|bonsoir)\b",
        r"^(?:ca\s+va|comment\s+(?:ca\s+)?va|comment\s+(?:allez|vas)-?vous)",
    ]
    
    def route(self, prompt: str) -> Dict[str, Any]:
        """Main entry point: classify and route the user input."""
        p = prompt.strip()
        p_lower = p.lower()
        
        # 1. Check greetings
        for pat in self.GREETINGS:
            if re.search(pat, p_lower):
                return {
                    "type": "greeting",
                    "action": None,
                    "params": {},
                    "confidence": 0.98
                }
        
        # 2. Check commands
        for action, patterns in self.COMMANDS.items():
            for pat in patterns:
                m = re.search(pat, p_lower)
                if m:
                    params = self._extract_command_params(action, m)
                    return {
                        "type": "command",
                        "action": action,
                        "params": params,
                        "confidence": 0.90
                    }
        
        # 3. Check reminders
        for pat in self.REMINDERS:
            m = re.search(pat, p_lower)
            if m:
                return {
                    "type": "reminder",
                    "action": "reminder",
                    "params": {
                        "what": m.group(1).strip() if m.lastindex and m.lastindex >= 1 else p,
                        "when": m.group(2).strip() if m.lastindex and m.lastindex >= 2 else None,
                        "raw": p
                    },
                    "confidence": 0.88
                }
        
        # 4. Default: question
        return {
            "type": "question",
            "action": None,
            "params": {"prompt": p},
            "confidence": 0.85
        }
    
    def _extract_command_params(self, action: str, match) -> Dict[str, Any]:
        """Extract parameters from a command match."""
        groups = [g for g in match.groups() if g]
        
        params = {"raw": match.group(0)}
        
        if action == "sms":
            params["contact"] = groups[0].strip() if len(groups) > 0 else None
            params["message"] = groups[1].strip() if len(groups) > 1 else None
        elif action == "call":
            params["contact"] = groups[0].strip() if groups else None
        elif action == "alarm":
            params["time"] = groups[0].strip() if groups else None
        elif action == "calendar":
            params["title"] = groups[0].strip() if len(groups) > 0 else None
            params["when"] = groups[1].strip() if len(groups) > 1 else None
        elif action == "note":
            params["text"] = groups[0].strip() if groups else None
        elif action == "search":
            params["query"] = groups[0].strip() if groups else None
        elif action == "weather":
            params["location"] = groups[0].strip() if groups and groups[0] else "ici"
        elif action == "music":
            params["song"] = groups[0].strip() if groups and len(groups) > 1 else (groups[0].strip() if groups else None)
        elif action == "open_app":
            params["app"] = groups[0].strip() if groups else None
        
        return params


# Quick test
if __name__ == "__main__":
    router = IntentRouter()
    tests = [
        "Envoie un SMS à Marie pour dire que je serai en retard",
        "Appelle Papa",
        "Réveille-moi à 7h demain",
        "Ajoute un rendez-vous dentiste jeudi 14h",
        "Quel temps fait-il à Paris ?",
        "Ouvre WhatsApp",
        "Cherche les horaires du musée",
        "Note : acheter du pain",
        "Rappelle-moi d'acheter du pain demain",
        "Qui es-tu ?",
        "Bonjour",
        "Joue de la musique jazz",
        "Calcule 127 + 58",
    ]
    for t in tests:
        r = router.route(t)
        print(f"[{r['type']:10s}] {t[:55]:55s} → {r.get('action','?')}: {r.get('params',{})}")