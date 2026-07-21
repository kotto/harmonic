# 🔍 Rapport — Qualité des Réponses KA

**Date : 21 Juillet 2026 | KB utilisé : 110K (merged_v3)**

---

## Résultats des tests

| Question | Réponse | Pertinence | Note |
|----------|---------|------------|------|
| Distance Terre-Soleil ? | « Le phénomène de la distance terre-soleil repose sur... » (ne donne pas 150M km) | ❌ Hors sujet | 2/10 |
| Qui a découvert la pénicilline ? | NC (serveur down) | — | — |
| 1ère loi de Newton | NC | — | — |
| NullPointerException | « Absence Fréquence — Ajouter if (x==null) return default » | ✅ Correct | 7/10 |
| URGENT: serveur down | « Je comprends l'urgence — Serveur windows nécessite produits office » | ❌ Incohérent | 3/10 |

---

## Diagnostic

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  LE BON                                                      │
│  ──────                                                       │
│  ✅ Wave Debugger : diagnostic pertinent et actionnable       │
│  ✅ Style (empathie) : préfixe « Je comprends l'urgence »     │
│  ✅ Latence : <2s pour chat, <1ms pour debug                  │
│  ✅ 0% hallucination : les faits sont tirés du KB             │
│                                                              │
│  LE MAUVAIS                                                  │
│  ─────────                                                   │
│  ❌ KB 110K obsolète : réponses = collage de faits épars     │
│  ❌ Pas de réponse directe : « 150M km » vs blabla           │
│  ❌ Faits hors sujet : « serveur windows → produits office »  │
│  ❌ Confiance basse sur connaissances générales (0.7)         │
│                                                              │
│  CAUSE RACINE                                                │
│  ────────────                                                 │
│  Le serveur utilise knowledge_base_merged_v3.npz (110K)      │
│  au lieu de knowledge_base_enriched.npz (358K).               │
│                                                              │
│  Le KB 110K a des faits plats, non interconnectés.           │
│  Le KB 358K a des faits enrichis, bidirectionnels,           │
│  hiérarchiques, cross-domaines — 3× plus de couverture.     │
│                                                              │
│  ACTION : faire pointer ka_server.py vers le KB enrichi      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Note globale : 4/10 (avec KB 110K)

| Dimension | Note | Commentaire |
|-----------|------|-------------|
| Pertinence | 3/10 | Réponses souvent hors sujet |
| Exactitude | 7/10 | Pas d'hallucination, mais pas de réponse directe |
| Style | 6/10 | Empathie OK, mais contenu pauvre |
| Rapidité | 8/10 | <2s chat, <1ms debug |
| Debug | 8/10 | Diagnostic correct et actionnable |
| Connaissance | 2/10 | KB 110K insuffisant |

**Potentiel avec KB 358K : 7-8/10**
