# Les 7 adaptateurs wave_bridge — références

Source : `DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md` §9, implémentation
`vital-ka/core/python/wave_bridge.py`.

## PsiDiphoneBank — banque de diphones holographique

Remplace `ka_sonic/psi_diphone_bank.py` (~300 lignes).

| Méthode | Rôle |
|---|---|
| `PsiDiphoneBank(dim=512)` | constructeur (dim par défaut du langage) |
| `encode_diphone(phone_a, phone_b) -> np.ndarray` | ψ du diphone = `bind(encode(a), encode(b))` |
| `store(phone_a, phone_b, audio)` | mémorise le diphone dans l'hologramme |
| `query(phone_a, phone_b, ...)` | récupère l'audio le plus résonant |
| `query_by_psi(psi_query, ...)` | récupération par onde directe |
| `size() -> int` | nombre de diphones stockés |

## ABCMemoryKernel — mémoire fractionnaire ABC

Remplace `alphafold/abc_folder.py` (~100 lignes).

| Méthode | Rôle |
|---|---|
| `ABCMemoryKernel(alpha=ALPHA, max_history=100)` | α par défaut = 1/φ ≈ 0.618 |
| `__call__(t) -> float` | poids du souvenir à l'instant t |
| `store(gradient)` | enregistre un gradient dans l'historique |
| `compute_effective_force(current_force)` | force effective pondérée par la mémoire |
| `clear()` | vide l'historique |

## HarmonicEnergyCore — énergie harmonique des protéines

Remplace `alphafold/harmonic_energy.py` (~150 lignes).

| Méthode | Rôle |
|---|---|
| `HarmonicEnergyCore(lambda_h=4.0, epsilon=1e-8)` | paramètres du potentiel |
| `compute(psi_residues, ...)` | énergie harmonique d'une chaîne de résidus |
| `compute_electrostatic_interference(psi_a, psi_b)` | interférence électrostatique entre résidus |

## SpectralAnalyzer — analyse spectrale vocale

Remplace `harmonic_voice_codec_v2.py` (~200 lignes).

| Méthode | Rôle |
|---|---|
| `SpectralAnalyzer(dim=1024)` | analyseur (dim 1024 pour l'audio) |
| `analyze(signal) -> np.ndarray` | analyse (diffract) |
| `spectrum(signal) -> np.ndarray` | magnitude spectrale |
| `synthesize(freqs) -> np.ndarray` | synthèse inverse |
| `filter(signal, ...)` | filtrage spectral (filter_wave) |
| `harmonic_decomposition(signal, ...)` | décomposition en harmoniques |
| `formant_extract(signal, ...)` | extraction des formants |

## VoiceSignature — signature vocale

Remplace `ka_sonic/voice_signature.py` (~80 lignes).

| Méthode | Rôle |
|---|---|
| `VoiceSignature(dim=512)` | constructeur |
| `extract(audio) -> np.ndarray` | ψ-signature de la voix (spectrum) |
| `compare(sig_a, sig_b) -> float` | similarité entre deux signatures (resonate) |
| `match(query_sig, ...)` | recherche la voix la plus proche |

## GlottalSource — source glottale

Remplace `ka_sonic/glottal_synth.py` (~60 lignes).

| Méthode | Rôle |
|---|---|
| `GlottalSource(f0=120.0, n_harmonics=40, ...)` | f0 et nombre d'harmoniques |
| `synthesize(duration=0.05, ...) -> np.ndarray` | synthèse (superpose + phase_shift des harmoniques) |

## HarmonicCloner — clonage de voix

Remplace `ka_sonic/harmonic_cloner.py` (~60 lignes).

| Méthode | Rôle |
|---|---|
| `HarmonicCloner(dim=1024)` | cloner vocal |
| `extract_spectral_envelope(audio)` | enveloppe spectrale de la source |
| `warp_spectrum(source_audio, ...)` | déformation spectrale (filter_wave) |
| `clone(source_audio, ...)` | voix clonée avec l'enveloppe cible (resonate/filter) |

## Table de correspondance récapitulative

| Adaptateur | Module original | Lignes remplacées | Primitives backend |
|---|---|---|---|
| PsiDiphoneBank | ka_sonic/psi_diphone_bank.py | ~300 | HolographicMemory, encode, bind |
| ABCMemoryKernel | alphafold/abc_folder.py | ~100 | abc_kernel, abc_forget |
| HarmonicEnergyCore | alphafold/harmonic_energy.py | ~150 | resonate, coherence |
| SpectralAnalyzer | harmonic_voice_codec_v2.py | ~200 | diffract, spectrum, filter_wave |
| VoiceSignature | ka_sonic/voice_signature.py | ~80 | spectrum, resonate |
| GlottalSource | ka_sonic/glottal_synth.py | ~60 | superpose, phase_shift |
| HarmonicCloner | ka_sonic/harmonic_cloner.py | ~60 | filter_wave, resonate |

## Adaptateurs LLM (Phase 6 — Juillet 2026)

Les 7 adaptateurs ci-dessous appliquent le même pattern « drop-in replacement »
aux modules LLM, apportant au domaine du langage la même intégrité architecturale
que celle déjà obtenue côté TTS/Audio.

| Adaptateur | Module original | Lignes remplacées | Primitives backend |
|---|---|---|---|
| CoherenceAttention | harmonic_attention.py | ~200 | resonate, coherence, superpose |
| HolographicEncoderBridge | holographic_encoder.py | ~150 | encode, bind, unbind, HolographicMemory |
| PhasePropagator | phase_amplifier.py | ~180 | phase_shift, rotate, resonate, superpose |
| WaveDecoderBridge | wave_decoder.py | ~120 | resonate, coherence, decode |
| HolographicRAG | harmonic_brain.py (RAG) | ~100 | HolographicMemory, resonate, bind_many |
| FewShotPhaseLock | few_shot_injector.py | ~80 | superpose, amplify, phase_shift |
| CoherenceGate | conscious_intelligence.py | ~100 | coherence, filter_wave, resonate |

### CoherenceAttention — attention harmonique par cohérence

Remplace `harmonic_attention.py` (~200 lignes).

| Méthode | Rôle |
|---|---|
| `CoherenceAttention(dim=512, alpha=0.3, power=2.0)` | constructeur |
| `contextualize(tokens, alpha, power) -> Dict[str, np.ndarray]` | contextualise chaque token par résonance : `psi_i' = normalize(psi_i + alpha * Σ_j C_ij^p * psi_j)` |
| `contextualize_query(query, alpha) -> np.ndarray` | psi contextuel moyen de la requête |
| `disambiguate(word, context, candidate_senses) -> (psi, scores)` | désambiguïsation par cohérence contextuelle |
| `inject_into_encoder(tokens)` / `restore_encoder()` | injection/restauration dans l'encodeur |
| `__enter__` / `__exit__` | context manager |

### HolographicEncoderBridge — encodeur holographique unifié

Remplace `holographic_encoder.py` (~150 lignes).

| Méthode | Rôle |
|---|---|
| `HolographicEncoderBridge(dim=512)` | constructeur avec HolographicMemory interne |
| `encode_word(word) / encode_word_fast(word)` | encodage FNV1a + φ-spacing → ψ |
| `bind(a, b) / unbind(a, b)` | binding HRR par convolution/corrélation circulaire |
| `encode_fact(sujet, relation, objet) -> np.ndarray` | ψ_fait = bind_many(ψ_s, ψ_r, ψ_o) |
| `store(fact_vector) / store_fact(s, r, o)` | stockage holographique H += amplitude * ψ |
| `query(query_vector) -> np.ndarray` | corrélation circulaire : memory ☆ query |
| `resonance_score(word, query) / resonance_scores_batch(...)` | scores de résonance |
| `vocab_size / energy / similarity / collision_check` | propriétés et diagnostics |

### PhasePropagator — propagation de phase

Remplace `phase_amplifier.py` (~180 lignes).

| Méthode | Rôle |
|---|---|
| `PhasePropagator(brain, dim=512, encoder)` | constructeur |
| `propagate(question, max_depth, threshold) -> PropagationChain` | propagation sur chemin unique avec amplification |
| `propagate_multi(question, ...) -> List[PropagationChain]` | beam search multi-branches |
| `explain(chain) -> str` | traduction de la chaîne en langage naturel |
| `reason_deep(question, max_depth) -> str` | interface simplifiée : conclusion textuelle |
| `reason_deep_multi(question, ...) -> str` | interface simplifiée multi-branches |

### WaveDecoderBridge — décodeur ondulatoire

Remplace `wave_decoder.py` (~120 lignes).

| Méthode | Rôle |
|---|---|
| `WaveDecoderBridge(encoder, knowledge_base, vocab_limit)` | constructeur |
| `decode(question, max_words, max_sentences) -> str` | décodage pur : clustering de phase + émergence |
| `decode_rich(question) -> str` | décodage riche avec HolographicMemory |
| `compute_signature(question) -> dict` | signature spectrale 9D de la question |

### HolographicRAG — RAG holographique

Remplace la partie RAG de `harmonic_brain.py` (~100 lignes).

| Méthode | Rôle |
|---|---|
| `HolographicRAG(dim=512, use_holographic=True)` | constructeur |
| `ingest(sujet, relation, objet, secteur) -> Dict` | stockage H += amplitude * ψ_fait |
| `ingest_batch(facts) -> int` | ingestion par lot |
| `retrieve(question, threshold, max_results)` | recherche lexicale + bonus spectral |
| `retrieve_resonance(question, max_results, sector_boost)` | recherche par résonance holographique pure |
| `psi_dominant` (property) | ψ moyen des 10 faits dominants |
| `ruminate(max_pairs)` | consolidation nocturne par interférence de paires |
| `reinforce(fact) / weaken(fact)` | renforcement/affaiblissement adaptatif |
| `stats` (property) | statistiques de la mémoire |

### FewShotPhaseLock — verrouillage de phase

Remplace `few_shot_injector.py` (~80 lignes).

| Méthode | Rôle |
|---|---|
| `FewShotPhaseLock(brain, dim=512, encoder)` | constructeur |
| `inject(examples, pattern_type, ttl_seconds) -> Optional[str]` | injection de pattern : ψ_pattern = mean(ψ_out_i - ψ_in_i) |
| `process(examples, query, pattern_type, ttl) -> Dict` | few-shot complet : injecte + traite |
| `consolidate(pattern_id)` | convertit un pattern mature en faits permanents |
| `auto_consolidate() -> int` | consolidation automatique des patterns éligibles |
| `stats` (property) | patterns actifs, total injecté, cohérence moyenne |

### CoherenceGate — porte de cohérence

Remplace `conscious_intelligence.py` (~100 lignes).

| Méthode | Rôle |
|---|---|
| `CoherenceGate(store)` | constructeur |
| `reason(question, candidates, parsed) -> (answer, confidence, method)` | 5 stratégies : résonance directe, chaînage, analogie, généralisation, fallback |

## Adaptateurs LLM v2 (Phase 7 — Août 2026)

Les 5 adaptateurs ci-dessous complètent la couverture LLM : les équivalences
#11-14, #19, #35, #36 sont désormais pontées (25/36 équivalences LLM couvertes).

| Adaptateur | Module original | Lignes remplacées | Primitives backend |
|---|---|---|---|
| FeedbackLoopBridge | feedback_loop.py | ~150 | coherence, amplify, oppose |
| WaveSamplingBridge | wave_sampling.py | ~200 | coherence, phase_shift, rotate |
| WaveToolUseBridge | wave_tool_use.py | ~250 | bind, unbind, resonate |
| WaveBeamSearchBridge | beam_search.py | ~170 | resonate, superpose, interfere |
| WavePerplexityBridge | wave_perplexity.py | ~220 | energy, spectrum, coherence |

### FeedbackLoopBridge — boucle de feedback RLHF

Remplace `feedback_loop.py` (~150 lignes).

| Méthode | Rôle |
|---|---|
| `FeedbackLoopBridge(brain, dim, learning_rate)` | constructeur |
| `process_feedback(response_psi, human_score, target_text) -> Dict` | boucle phase-amplitude : ψ ← ψ + η·(r − cohérence)·ψ_cible |
| `reinforce(psi, amplitude=+0.2)` | renforcement local (score > 0.7) |
| `weaken(psi, amplitude=-0.2)` | affaiblissement local (score < 0.3) |
| `train(pairs, n_cycles) -> Dict` | entraînement par lot (texte, score_humain) |
| `evaluate(psi) -> float` | écho de phase : prédiction du score humain par résonance |

### WaveSamplingBridge — échantillonnage ondulatoire

Remplace `wave_sampling.py` (~200 lignes).

| Méthode | Rôle |
|---|---|
| `WaveSamplingBridge(vocabulary, dim)` | constructeur |
| `coherence_scores(psi_context, candidates) -> Dict` | scores Re(⟨ψ_ctx\|ψ_mot⟩) |
| `sample(psi_context, temperature, top_p, top_k) -> str` | pipeline complet : cohérence → top-k → top-p → température |
| `deterministic(psi_context) -> str` | T=0 : cohérence maximale |
| `creative(psi_context, creativity) -> str` | haute température (T=1.05) |
| `precise(psi_context) -> str` | basse température (T=0.2) |
| `apply_phase_noise(psi, temperature)` | bruit de phase ψ·exp(i·T·N(0,1)·0.5) |
| `coherence_cone_filter(scores, angle)` | cône de cohérence (seuil angulaire) |
| `entropy(scores) / perplexity(scores)` | entropie de Shannon / exp(H) |

### WaveToolUseBridge — appel d'outil ondulatoire

Remplace `wave_tool_use.py` (~250 lignes).

| Méthode | Rôle |
|---|---|
| `WaveToolUseBridge(dim)` | constructeur avec registre d'outils |
| `register(tool)` | enregistre un outil (encodé en ψ) |
| `resolve(intention, threshold) -> ToolCall` | résolution hybride : résonance + bonus lexical avec stemming |
| `execute(call) -> Any` | exécute l'outil avec les paramètres extraits |
| `resolve_and_execute(intention) -> (result, call)` | résolution + exécution |
| `_extract_params(intention, tool)` | extraction de paramètres par cohérence avec les noms |

### WaveBeamSearchBridge — recherche en faisceau ondulatoire

Remplace `beam_search.py` (~170 lignes).

| Méthode | Rôle |
|---|---|
| `WaveBeamSearchBridge(vocabulary, beam_width, dim)` | constructeur |
| `search(psi_context, max_steps, interference_strength) -> List[WavePath]` | faisceau avec interférence croisée entre chemins |
| `best_sequence(psi_context, max_steps) -> List[str]` | séquence du meilleur chemin |
| `best_text(psi_context, max_steps) -> str` | meilleur chemin en texte |
| `interference_matrix(paths) -> np.ndarray` | matrice M[i,j] = Re(⟨ψ_i\|ψ_j⟩) |
| `select_constructive(paths, threshold)` | garde les chemins en interférence constructive |

### WavePerplexityBridge — perplexité ondulatoire

Remplace `wave_perplexity.py` (~220 lignes).

| Méthode | Rôle |
|---|---|
| `wave_entropy(psi) -> float` | entropie de Von Neumann H = −Σ\|ψᵢ\|²log\|ψᵢ\|² |
| `wave_perplexity(psi) -> float` | exp(entropie) |
| `coherence_shannon_entropy(scores)` | entropie de Shannon des scores |
| `coherence_perplexity(scores)` | exp(entropie de cohérence) |
| `confidence(scores) -> float` | (max − moyenne) / (max + ε) |
| `coherence_margin(scores) -> float` | écart top-1 / top-2 |
| `generation_quality(seq, vocab) -> Dict` | analyse d'une séquence générée |
| `compare_distributions(a, b) -> Dict` | divergence JS approchée + top-3 |

## Adaptateurs LLM v3 (Phase 8 — Août 2026)

Les 6 adaptateurs ci-dessous couvrent les équivalences #16-17, #25, #28, #29, #32
(+ synthèse bonus) : 25 adaptateurs au total (7 TTS + 18 LLM).

| Adaptateur | Module original | Lignes remplacées | Primitives backend |
|---|---|---|---|
| WaveFineTuneBridge | wave_fine_tune.py | ~150 | bind, normalize, energy |
| DomainGateBridge | harmonic_brain.py (gate MoE) | ~150 | encode, resonate, coherence, superpose |
| SystemPromptBridge | harmonic_engine.py + spectral_hop.py | ~60 | encode, rotate, phase_shift |
| WavePoetryBridge | wave_poetry.py | ~500 | bind, coherence, phase_shift, superpose |
| WaveNarrativeBridge | wave_narrative.py | ~350 | bind, coherence, superpose(ABC) |
| WaveSynthesizerBridge | wave_synthesizer.py | ~150 | superpose, resonate, decode |

### WaveFineTuneBridge — fine-tuning ALS

Remplace `wave_fine_tune.py` (~150 lignes).

| Méthode | Rôle |
|---|---|
| `WaveFineTuner(encoder, learning_rate, lambda_reg)` | constructeur |
| `fine_tune(kb, epochs, verbose) -> dict` | ALS dans le domaine de Fourier, régularisé SVD |
| `_optimize_by_role(facts_by_role, vocab, epoch) -> int` | optimisation fermée par fréquence |
| `_compute_loss(kb, vocab) -> float` | L = Σ\|ψ_s ⊛ ψ_r − ψ_o\|² via bind + energy |

### DomainGateBridge — gate MoE

Remplace la partie gate de `harmonic_brain.py` (~150 lignes).

| Méthode | Rôle |
|---|---|
| `DomainGateBridge(dim)` | constructeur, imports DOMAIN_KEYWORDS/SECTOR_MAP de harmonic_brain |
| `detect(question, max_domains) -> List[str]` | résonance ψ_question↔ψ_domaine + chevauchement lexical |
| `route(sujet, relation, objet, secteur) -> Optional[str]` | secteur → domaine |
| `merge(domain_candidates, max_results) -> List` | fusion cross-domaine avec bonus 1 + 0.2·(N−1) |
| `stats` (property) | domaines, secteur_map_size |

### SystemPromptBridge — phase initiale ψ₀

Remplace `harmonic_engine._build_harmonic_system_prompt` + `spectral_hop.psi_0` (~60 lignes).

| Méthode | Rôle |
|---|---|
| `SystemPromptBridge(dim)` | constructeur |
| `build(category, knowledge_context, ...) -> str` | template par catégorie + contexte holographique |
| `initial_phase(prompt, category) -> np.ndarray` | ψ₀ = rotate(encode(prompt), angle_catégorie) |
| `orient(psi, category) -> np.ndarray` | rotation de l'espace des phases (role prompting #26) |

### WavePoetryBridge — poète ondulatoire

Remplace `wave_poetry.py` (~500 lignes).

| Méthode | Rôle |
|---|---|
| `WavePoetryBridge(dim)` | constructeur, imports POETIC_VOCABULARY/VERSE_STRUCTURES |
| `compose(theme, form, emotion, lines, personal_facts) -> dict` | ψ_thème ⊗ ψ_émotion (phase_shift) → sélection par résonance |
| `compose_personal(theme, user_id, personal_facts) -> dict` | interférence avec l'hologramme personnel |
| `stats() -> dict` | vocabulaire, phases, formes |
| `_select_words_diverse(psi, phase, count)` | sélection diversifiée par coherence |
| `_french_grammar(line) -> str` | élision, genre, espaces |

### WaveNarrativeBridge — narrateur ondulatoire

Remplace `wave_narrative.py` (~350 lignes).

| Méthode | Rôle |
|---|---|
| `WaveNarrativeBridge(dim)` | constructeur, imports CONNECTOR_BANK/SENTENCE_STRUCTURES |
| `synthesize(facts, topic, section_type, style) -> str` | ψ_facts = superpose(weights ABC) ⊗ ψ_narrative → phrases |
| `synthesize_paragraph(facts, topic, section_type) -> str` | alias |
| `_select_connector(phase, prev_fact, curr_fact) -> str` | connecteur par résonance de phase |
| `_detect_fact_type(relation) -> str` | definition/action/property |

### WaveSynthesizerBridge — synthétiseur de paragraphes

Remplace `wave_synthesizer.py` (~150 lignes).

| Méthode | Rôle |
|---|---|
| `WaveSynthesizerBridge(encoder)` | constructeur |
| `synthesize(facts, question) -> str` | superposition → mots dominants → assemblage |
| `_superpose(facts) -> np.ndarray` | Ψ = superpose(ψ_faits) |
| `_extract_dominant(psi, top_k) -> List[str]` | resonate avec le vocabulaire |
| `_assemble(subject, words, facts) -> str` | template d'assemblage |

## Adaptateurs LLM v4 (Phase 9 — Août 2026)

Les 3 adaptateurs ci-dessous complètent la couverture : 28 adaptateurs au total
(7 TTS + 21 LLM). Équivalences #26-27 et #34 (KV-Cache persisté) désormais couvertes.

| Adaptateur | Module original | Lignes remplacées | Primitives backend |
|---|---|---|---|
| WaveStylerBridge | wave_styler.py | ~350 | encode, coherence |
| HarmonicStyleBridge | harmonic_style.py | ~200 | phase_shift, rotate, encode |
| HologramLoaderBridge | hologram_store.py | ~300 | HolographicRAG.ingest (numpy I/O) |

### WaveStylerBridge — styler rédactionnel

Remplace `wave_styler.py` (~350 lignes).

| Méthode | Rôle |
|---|---|
| `WaveStylerBridge(encoder, dim)` | constructeur |
| `detect_register(question) -> str` | mots-clés (mots complets, anti-faux-positifs) + résonance ψ_question↔ψ_registre |
| `render(facts, question, style, personality) -> str` | templates FR + **sélection de structure par cohérence** (déterministe) |
| `_select_structure(templates, question, i)` | la structure qui RÉSONE le plus avec la question |

**Améliorations :** sélection par résonance au lieu de `random.choice` ;
bug latent corrigé (`'subordonnee'` vs `'subordonnée'` — les subordonnées
n'étaient jamais sélectionnées) ; mots-clés courts matchés par mots complets
(`'ca'` ne matche plus `'implications'`).

### HarmonicStyleBridge — styler empathique

Remplace `harmonic_style.py` (~200 lignes).

| Méthode | Rôle |
|---|---|
| `HarmonicStyleBridge(dim)` | constructeur, imports TONALITIES/ALTERNATIVES de harmonic_style |
| `style(response, user_message, style_level) -> str` | empathie → vocabulaire → diversité |
| `detect_tone(message) -> str` | détection de tonalité par mots-clés |
| `emotional_rotation(message) -> np.ndarray` | **nouveau** : ψ = phase_shift(encode(message), θ_tonalité) |
| `emotional_coherence(a, b) -> float` | **nouveau** : alignement émotionnel (empathie mesurée) |

**Améliorations :** rotation de phase émotionnelle réelle (délégation wave_lang)
— l'original n'avait ZÉRO math ondulatoire.

### HologramLoaderBridge — chargeur .npz → RAG

Remplace `hologram_store.py` côté lecture (~300 lignes).

| Méthode | Rôle |
|---|---|
| `HologramLoaderBridge(rag, store_dir)` | constructeur, import lazy de HologramStore (backend/hologram) |
| `load(holo_id) -> int` | download() → ingest_batch() |
| `load_all(holo_type) -> Dict[str, int]` | charge tous les hologrammes listés |
| `load_npz(path, secteur_fallback) -> int` | 2 formats : columnar (subjects/relations/...) + 'facts' (tuples) |
| `stats` (property) | loaded_holograms, total_facts_loaded, rag_facts |

## Table de correspondance récapitulative (28 adaptateurs)

| # | Adaptateur | Module original | Primitives backend |
|---|---|---|---|
| 1 | PsiDiphoneBank | ka_sonic/psi_diphone_bank.py | HolographicMemory, encode, bind |
| 2 | ABCMemoryKernel | alphafold/abc_folder.py | abc_kernel, abc_forget |
| 3 | HarmonicEnergyCore | alphafold/harmonic_energy.py | resonate, coherence |
| 4 | SpectralAnalyzer | harmonic_voice_codec_v2.py | diffract, spectrum, filter_wave |
| 5 | VoiceSignature | ka_sonic/voice_signature.py | spectrum, resonate |
| 6 | GlottalSource | ka_sonic/glottal_synth.py | superpose, phase_shift |
| 7 | HarmonicCloner | ka_sonic/harmonic_cloner.py | filter_wave, resonate |
| 8 | CoherenceAttention | harmonic_attention.py | resonate, coherence, superpose |
| 9 | HolographicEncoderBridge | holographic_encoder.py | encode, bind, unbind, HolographicMemory |
| 10 | PhasePropagator | phase_amplifier.py | phase_shift, rotate, resonate, superpose |
| 11 | WaveDecoderBridge | wave_decoder.py | resonate, coherence, decode |
| 12 | HolographicRAG | harmonic_brain.py (RAG) | HolographicMemory, resonate, bind_many |
| 13 | FewShotPhaseLock | few_shot_injector.py | superpose, amplify, phase_shift |
| 14 | CoherenceGate | conscious_intelligence.py | coherence, filter_wave, resonate |
| 15 | FeedbackLoopBridge | feedback_loop.py | coherence, amplify, oppose |
| 16 | WaveSamplingBridge | wave_sampling.py | coherence, phase_shift, rotate |
| 17 | WaveToolUseBridge | wave_tool_use.py | bind, unbind, resonate |
| 18 | WaveBeamSearchBridge | beam_search.py | resonate, superpose, interfere |
| 19 | WavePerplexityBridge | wave_perplexity.py | energy, spectrum, coherence |
| 20 | WaveFineTuneBridge | wave_fine_tune.py | bind, normalize, energy |
| 21 | DomainGateBridge | harmonic_brain.py (gate MoE) | encode, resonate, coherence, superpose |
| 22 | SystemPromptBridge | harmonic_engine.py + spectral_hop.py | encode, rotate, phase_shift |
| 23 | WavePoetryBridge | wave_poetry.py | bind, coherence, phase_shift, superpose |
| 24 | WaveNarrativeBridge | wave_narrative.py | bind, coherence, superpose(ABC) |
| 25 | WaveSynthesizerBridge | wave_synthesizer.py | superpose, resonate, decode |
| 26 | WaveStylerBridge | wave_styler.py | encode, coherence |
| 27 | HarmonicStyleBridge | harmonic_style.py | phase_shift, rotate, encode |
| 28 | HologramLoaderBridge | hologram_store.py | HolographicRAG.ingest, numpy |
