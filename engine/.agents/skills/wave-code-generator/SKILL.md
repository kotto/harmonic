---
name: wave-code-generator
description: >-
  Générer du code ondulatoire natif à partir d'une question en langage naturel (les 7 intentions :
  query, reason, creative, store_fact, compare, analogize, classify). Utilise ce skill dès que
  l'utilisateur veut transformer une question/phrase en programme ondulatoire, faire « penser en ondes »
  une IA, détecter l'intention d'une question, générer du code ENCODE/QUERY/DECODE automatiquement,
  convertir une question en AST Wave IR, ou utilise WaveCodeGenerator, wave_to_python, les 7 intentions,
  le wave_code_generator — même s'il ne demande pas explicitement « génère du code ondulatoire ».
---

# Générateur de code ondulatoire — de la question au programme

L'IA génère du code ondulatoire natif à partir d'une question en langage naturel : elle ne traduit
plus sa pensée en Python, elle écrit dans sa langue natale. La boucle :

```
Question → détection d'intention → génération d'un AST Wave IR → (exécution / compilation / retour)
```

Implémentation : `vital-ka/core/python/wave_code_generator.py` (`WaveIntentDetector`,
`WaveCodeGenerator`, `wave_to_python`). Pour l'importer, ajouter au `sys.path` les 3 dossiers
suivants (ensemble minimal vérifié) : `vital-ka/core/python`, `vital-ka/backend/hologram`
(holographic_encoder), `vital-ka/backend/inference` (prompt_parser) — le générateur dépend de
`code_generator` → `harmonic_brain`. Modules complémentaires de génération par domaine :
`wave_reasoning.py`, `wave_poetry.py`, `wave_music.py`, `wave_narrative.py`, `wave_conversation.py`,
`wave_styler.py`, `wave_code.py`, `wave_math.py`, `wave_logic.py`, `wave_graph.py`, `wave_phase.py`,
`wave_sampling.py`, `wave_tool_use.py`, `wave_synthesizer.py`, `wave_perplexity.py`,
`wave_fine_tune.py`, `wave_debugger*.py`, `wave_explainer_v2.py`, `wave_domains.py`, `wave_decoder.py`
(tous dans `vital-ka/core/python/`).

## Quand utiliser ce skill

- L'utilisateur veut générer un programme ondulatoire depuis une question (« qu'est-ce que… »,
  « pourquoi… », « imagine… », « souviens-toi… », « différence entre… », « comme… », « catégorise… »).
- Il faut détecter l'intention ondulatoire d'une phrase avant de la traiter.
- Il faut produire du code Python équivalent au programme ondulatoire (pour débogage ou intégration).
- Il faut évaluer la qualité d'un générateur (roundtrip, AST valide, 7 intentions reconnues).

## Usage

```python
from wave_code_generator import WaveCodeGenerator, wave_to_python

gen = WaveCodeGenerator(hologram_name="H_connaissances")  # optionnel : brain=…
ast = gen.generate("Quelle est la différence entre l'amour et l'amitié ?")
# ast est un Program (AST Wave IR) — voir le skill wave-ir-compiler pour l'exécuter

print(ast)          # programme ondulatoire lisible
print(wave_to_python(ast))  # équivalent Python (primitives wave_lang)
```

Détection seule :

```python
from wave_code_generator import WaveIntentDetector
detector = WaveIntentDetector()
intent, score = detector.detect_wave_intent("pourquoi le ciel est-il bleu ?")
# ("reason", 0.9…)
```

## Les 7 intentions

| Intention | Marqueurs | Pattern généré |
|---|---|---|
| **query** | « qu'est-ce que », « explique », « définis » | `ENCODE → QUERY → DECODE → RETURN` |
| **reason** | « pourquoi », « déduis », « donc » | `ENCODE → QUERY → SUPERPOSE → EMERGE → DECODE` |
| **creative** | « imagine », « crée », « et si » | `ENCODE → ENCODE → INTERFERE → DECODE` |
| **store_fact** | « souviens-toi », « mémorise » | `ENCODE → BIND_MANY → STORE → DECODE` |
| **compare** | « différence », « versus » | `ENCODE → ENCODE → RESONANCE → OPPOSE → DECODE` |
| **analogize** | « comme », « analogie » | `ENCODE → BIND → UNBIND → DECODE` |
| **classify** | « catégorise », « type » | `ENCODE → RESONANCE` avec prototypes |

## Exemple canonique (comparaison)

Question : *« Quelle est la différence entre l'amour et l'amitié ? »*

```
ψ_a = ENCODE "amour"
ψ_b = ENCODE "amitié"
similarite = RESONANCE(ψ_a, ψ_b)
ψ_diff = OPPOSE(ψ_a, ψ_b)
analyse = DECODE(ψ_diff)
RETURN analyse
```

Vérifications exigées par le document fondateur :
- roundtrip `parse(généré) → AST → re-généré` identique ✅
- AST généré valide à 100 % (validation `wave_ir.validate`)
- `wave_to_python` → code Python exécutable.

## Règles de génération

1. **Toujours commencer par ENCODE** : le monde doit entrer dans ℂ⁵¹² avant toute manipulation.
2. **Terminer par RETURN** : le résultat doit sortir (directement ou via DECODE).
3. **`store_fact` exige une phrase factuelle** : sujet, relation, objet sont extraits de la question
   (`_parse_fact`). Si la phrase n'est pas un fait (pas de verbe prédicatif), préférer `query`.
4. **`creative` choisit ε selon l'écart des concepts** : ε ≈ 0.15 pour une connexion subtile,
   0.5 pour un mélange équilibré, > 1.0 si le second concept doit dominer.
5. **Les concepts sont extraits de la question** (`_extract_concepts`) : retirer les mots-outils
   (« quelle », « est », « la », « que »…), garder les entités porteuses de sens.
6. **Langue** : `generate(question, lang='fr')` — l'encodage est indépendant de la langue (hachage
   FNV-1a), seul le vocabulaire de décodage change.
7. **Ne pas halluciner d'hologramme** : `QUERY … FROM H` suppose que l'exécuteur fournira H ;
   si aucune mémoire n'existe, basculer sur des opérations sans état (resonate sur vocabulaire,
   interfere, oppose).

## Vérification d'une génération

1. Type de retour : `Program` (AST) — pas du texte brut.
2. `validate(ast)` → liste vide.
3. Roundtrip : `parse(str(ast))` reproduit le même AST (bit à bit via `to_json`).
4. `wave_to_python(ast)` exécutable dans un environnement avec `wave_lang` importable.

## Détails

- Tableau détaillé des 7 générateurs avec exemples de sorties : `references/intentions.md`
