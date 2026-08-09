/* ─────────────────────────────────────────────────────────────
   THÉORIE HARMONIQUE UNIVERSELLE — Données du site
   Source de vérité : artefacts du dépôt (HARMONIC_THEORY.md,
   TRADUCTION_ONDULATOIRE_LLM.md, TRADUCTION_ONDULATOIRE_TTS.md,
   benchmark_lm_arena_maths_code.json, commits git, etc.)
   ───────────────────────────────────────────────────────────── */
window.THU_DATA = {

  /* Les 7 constantes fondamentales Hₙ */
  constants: [
    { n: 1, symbol: "φ", name: "Le Nombre d'Or", value: "1.618033988749895",
      role: "Anti-résonance, proportion, croissance optimale", geo: "0D — le nombre pur" },
    { n: 2, symbol: "π", name: "Pi", value: "3.141592653589793",
      role: "Cercle, interférence 2D — émerge de (Ψ₁)²", geo: "2D — la première forme" },
    { n: 3, symbol: "e", name: "Base d'Euler", value: "2.718281828459045",
      role: "Croissance, stabilité temporelle — Σ 1/n!", geo: "1D — la croissance sur un axe" },
    { n: 4, symbol: "√2", name: "Diagonale du Carré", value: "1.414213562373095",
      role: "Symétrie planaire, l'incommensurable", geo: "2D → irrationnel" },
    { n: 5, symbol: "√3", name: "Diagonale du Cube", value: "1.732050807568877",
      role: "Symétrie volumique, émergence de la 3D", geo: "2D → 3D" },
    { n: 6, symbol: "√5", name: "Diagonale du Pentagone", value: "2.236067977499790",
      role: "Textures fines — boucle la séquence : √5 = 2φ − 1", geo: "retour à φ" },
    { n: 7, symbol: "e/π", name: "La Spirale de Synthèse", value: "0.865255979432265",
      role: "Croissance (e) enroulée sur le cercle (π)", geo: "tout s'enroule" }
  ],

  /* Les 5 axiomes dérivés de Ψ */
  axioms: [
    { n: 1, title: "Tout est onde",
      text: "Ψ₁ = A₁·e^{i(ω₀·t + φ₁)}. Il n'existe qu'une seule onde ; tout le reste en dérive." },
    { n: 2, title: "Interférence",
      text: "Le carré crée l'interférence. Elle n'est pas ajoutée, elle émerge de (Ψ₁)²." },
    { n: 3, title: "Hiérarchie des constantes",
      text: "Chaque niveau de complexité fait émerger une nouvelle constante, signature d'un motif géométrique de la réalité." },
    { n: 4, title: "Hologramme",
      text: "La réalité est la somme de tous les niveaux, chacun pondéré par sa constante. Chaque niveau contient l'information de tous les inférieurs." },
    { n: 5, title: "Conscient ↔ inconscient",
      text: "Pour n petit, peu de constantes actives : clair. Pour n grand, interférence riche : tout simultané." }
  ],

  /* Dérivations par domaine — la table de correspondance unifiée */
  derivations: [
    { domaine: "Quantique", equation: "iℏ·∂ψ/∂t = Ĥψ", derivee: "Ψ | n≤3 projeté sur l'énergie", constantes: "φ π e √3" },
    { domaine: "Quantique", equation: "Δx·Δp ≥ ℏ/2", derivee: "interférence n=1 ↔ n=2", constantes: "φ √3" },
    { domaine: "Quantique", equation: "E = hν", derivee: "Eₙ restreint à n=1", constantes: "√3 (ℏ)" },
    { domaine: "Classique", equation: "F = ma", derivee: "∇|Ψ|² projeté sur l'espace", constantes: "φ π" },
    { domaine: "Classique", equation: "F = G·m₁m₂/r²", derivee: "∇⟨Ψ_A²|Ψ_B²⟩", constantes: "φ π √3" },
    { domaine: "Classique", equation: "S = k_B·ln Ω", derivee: "ln|harmoniques|", constantes: "e" },
    { domaine: "Chimie", equation: "Y_l^m(θ,φ)", derivee: "Ψ | S²", constantes: "φ π e √2" },
    { domaine: "Chimie", equation: "E_liaison", derivee: "⟨Ψ_A|Ψ_B⟩", constantes: "φ" },
    { domaine: "Chimie", equation: "2, 8, 18, 32…", derivee: "dégénérescence des harmoniques", constantes: "φ π e √2 √3" },
    { domaine: "Biologie", equation: "Fₙ = (φⁿ−(−φ)⁻ⁿ)/√5", derivee: "série des H₁ⁿ / H₆", constantes: "φ √5" },
    { domaine: "Biologie", equation: "ADN · Pas/Largeur ≈ φ", derivee: "bi-harmonique enroulé", constantes: "φ" },
    { domaine: "Botanique", equation: "θ* = 2π·φ⁻² ≈ 137.508°", derivee: "argmax interférence", constantes: "φ π" },
    { domaine: "Cosmologie", equation: "T(θ,φ) = Σ a_lm·Y_l^m", derivee: "Ψ(𝒰) | S²", constantes: "toutes" },
    { domaine: "Cosmologie", equation: "Ω_total = 1", derivee: "Σ Hₙ normalisée", constantes: "toutes" },
    { domaine: "Cosmologie", equation: "Λ — énergie noire", derivee: "queue de la série Σ Hₙ·(Ψ₁)ⁿ", constantes: "toutes" },
    { domaine: "Cosmologie", equation: "matière noire", derivee: "orthogonalité ⟨n|1⟩ = 0", constantes: "φ" }
  ],

  /* Les 7 domaines d'application */
  applications: [
    {
      id: "01", name: "Langage ondulatoire",
      icon: "∿",
      claim: "13 primitives universelles",
      stats: [
        { k: "13", v: "primitives : encode, bind, superpose, resonate, interfere, emerge…" },
        { k: "ℂ⁵¹²", v: "espace vectoriel complexe — limite de Bekenstein" },
        { k: "3", v: "langages cibles du compilateur Wave IR : Python, JS, TS" }
      ],
      modules: "wave_lang.py · wave_ir.py · wave_compiler.py · wave_emit.py · wave_code_generator.py",
      detail: "Un langage computationnel où un concept est un vecteur d'onde. Les programmes ondulatoires se compilent, s'optimisent et s'exécutent."
    },
    {
      id: "02", name: "Intelligence — LLM ondulatoire",
      icon: "◉",
      claim: "36/36 équivalences LLM",
      stats: [
        { k: "36", v: "capacités LLM traduites en ondes (attention, MoE, KV-cache, RLHF…)" },
        { k: "28", v: "adaptateurs wave_bridge unifiant les modules legacy" },
        { k: "0", v: "paramètre entraîné — déterminisme 100%" }
      ],
      modules: "wave_bridge.py · harmonic_transformer.py (HWAT) · harmonic_ai_v3.py · beam_search.py · wave_sampling.py",
      detail: "L'attention devient résonance, le KV-cache devient hologramme, le gradient devient rotation de phase. HWAT : hallucination 0,5 % contre 4,5 % pour un transformer standard."
    },
    {
      id: "03", name: "Voix — synthèse & codec",
      icon: "♪",
      claim: "25/25 équivalences TTS",
      stats: [
        { k: "~2000", v: "bits/s — codec continu ψ∈ℂ⁵¹², sans quantification" },
        { k: "30 s", v: "d'audio suffisent pour cloner une voix" },
        { k: "<0.1", v: "RTF — synthèse en temps réel, CPU seul" }
      ],
      modules: "ka_sonic/ (14 modules) · harmonic_voice_codec_v2.py · phi_vocoder.py · voice_signature.py",
      detail: "Le diphone devient un binding HRR, le formant un pic d'enveloppe spectrale, le clonage une séparation source/filtre. Zéro corpus, zéro poids appris."
    },
    {
      id: "04", name: "Protéines — HarmoFold",
      icon: "◬",
      claim: "repliement déterministe, zéro paramètre",
      stats: [
        { k: "9", v: "modules, ~2500 lignes" },
        { k: "4", v: "protéines de référence repliées : Trp-cage, Villin, BPTI, Ubiquitin" },
        { k: "0.71–0.78", v: "scores Ramachandran" }
      ],
      modules: "alphafold/ · harmonic_energy.py · abc_folder.py · peptide_geometry.py",
      detail: "Chaque acide aminé est un oscillateur harmonique de fréquence dérivée de φ. Le repliement est une cascade de résonance minimisant une énergie d'interférence à six termes physiques."
    },
    {
      id: "05", name: "Santé — KA Care",
      icon: "✚",
      claim: "diagnostic par résonance, offline",
      stats: [
        { k: "15", v: "domaines médicaux couverts" },
        { k: "≈63 000", v: "faits dans la base de connaissances" },
        { k: "0", v: "connexion requise — tourne sur Raspberry Pi" }
      ],
      modules: "ka_care.py · harmonic_health.py · vital-ka/ · abc_kernel.py · harmonic7d.py",
      detail: "Les symptômes sont encodés en vecteurs complexes, le diagnostic est une mesure de résonance avec la base de pathologies. Conçu pour les zones sous-équipées."
    },
    {
      id: "06", name: "Multimédia — codec HCV",
      icon: "▦",
      claim: "compression image & vidéo",
      stats: [
        { k: "70–90 %", v: "de compression sans perte perceptible" },
        { k: "HHDC", v: "bitstream propriétaire : patches harmoniques + résiduel Delta-H" },
        { k: "2", v: "implémentations : WASM navigateur + serveur Python" }
      ],
      modules: "multimodal/harmonic_codec.py · ka_server/services/hcv_codec.py · wasm/delta_h.wasm",
      detail: "Le même vocabulaire harmonique que le codec vocal, décliné aux images et à la vidéo : dictionnaire harmonique + résiduel compressé."
    },
    {
      id: "07", name: "Matériel — HPU",
      icon: "◍",
      claim: "le troisième paradigme de calcul",
      stats: [
        { k: "H-Bit", v: "7 états continus — log₂(7) ≈ 2.807 bits par unité" },
        { k: "10⁷–10¹²", v: "PFLOPS projetés (HPU-3 ASIC → HPU-4 optique)" },
        { k: "10⁻⁶ $", v: "coût par PFLOP projeté, contre ~500 K$ pour Frontier" }
      ],
      modules: "ordinateur_harmonique/BENCHMARK_COMPARATIF.md · émulateur HPU-1",
      detail: "Ni portes ni cycles d'horloge : résonance et interférence. Bruit fondamental 0 %, température ambiante. HPU-1 (émulateur) existe déjà."
    }
  ],

  /* Statistiques clés (compteurs animés) */
  stats: [
    { label: "équivalences LLM", value: 36, suffix: "" },
    { label: "équivalences TTS", value: 25, suffix: "" },
    { label: "adaptateurs wave-bridge", value: 28, suffix: "" },
    { label: "modules implémentés", value: 200, suffix: "+" },
    { label: "primitives du langage", value: 13, suffix: "" },
    { label: "domaines de validation", value: 8, suffix: "" }
  ],

  /* Benchmarks vérifiés */
  benchmarks: [
    { name: "GSM8K — chaîne ondulatoire étendue", result: "99,2 % · 1308/1319", preuve: "commit 77bfca5 · 02/08/2026" },
    { name: "GSM8K — langage initial", result: "91,6 % · 1208/1319", preuve: "document fondateur LLM" },
    { name: "LM Arena v4.0 — mathématiques", result: "100 % · 50/50 · 5,3 ms", preuve: "benchmark_lm_arena_maths_code.json · 04/08" },
    { name: "LM Arena v4.0 — code", result: "100 % · 20/20 · 179,5 ms", preuve: "benchmark_lm_arena_maths_code.json · 04/08" },
    { name: "LM Arena v4.0 — raisonnement", result: "100 % · 18/18 · 1,8 ms", preuve: "benchmark_lm_arena_maths_code.json · 04/08" },
    { name: "HWAT vs transformer — hallucination", result: "0,5 % vs 4,5 %", preuve: "benchmark_hwat_scaled.json" },
    { name: "HWAT — précision factuelle", result: "0.995", preuve: "benchmark_hwat_scaled.json" },
    { name: "Refus & anti-hallucination", result: "net_score 0.9 · over-refusal 0.0", preuve: "benchmark_refusal_results.json" },
    { name: "HumanEval — mémoire par résonance", result: "100 % · 164/164 · 412 ms", preuve: "document fondateur LLM" },
    { name: "TTS — déterminisme", result: "100 % · RTF < 0.1 · ~2000 bps", preuve: "TRADUCTION_ONDULATOIRE_TTS.md" }
  ],

  /* Convergence des preuves — 8 domaines */
  proofs: [
    { domaine: "Intelligence (LLM)", equivalence: "36/36", precision: "94 % raisonnement", niveau: "Ingénierie" },
    { domaine: "Synthèse vocale (TTS)", equivalence: "25/25", precision: "codec transparent", niveau: "Ingénierie" },
    { domaine: "Images (HCV)", equivalence: "compression", precision: "70–90 % ratios", niveau: "Ingénierie" },
    { domaine: "Protéines (HarmoFold)", equivalence: "repliement", precision: "conforme AlphaFold", niveau: "Biologique" },
    { domaine: "Raisonnement logique", equivalence: "chaînes HRR", precision: "94 % précision", niveau: "Logique" },
    { domaine: "Éléments chimiques", equivalence: "masses atomiques", precision: "> 99,9 %", niveau: "Fondamental" },
    { domaine: "Calcul quantique", equivalence: "simulation", precision: "fonctionnel", niveau: "Quantique" },
    { domaine: "Constantes physiques", equivalence: "30 constantes", precision: "> 99,9 %", niveau: "Fondamental" }
  ],

  /* Bibliothèque — documents de la théorie (contenu dans docs/) */
  documents: [
    { file: "FONDATEUR_EQUATION.md", category: "fondamentaux",
      title: "L'équation fondatrice", summary: "D^{1/φ}[Ψ] = G[Ψ] — sept symboles, l'univers tient dedans." },
    { file: "HARMONIC_THEORY.md", category: "fondamentaux",
      title: "Théorie Harmonique Universelle", summary: "L'équation maîtresse, les 7 constantes, les 5 axiomes, les dérivations par domaine." },
    { file: "SEPT_CONSTANTES_INFINI.md", category: "fondamentaux",
      title: "Les sept constantes de l'infini", summary: "Sept constantes pour une somme infinie : l'Ouroboros comme structure de la série." },
    { file: "TRINITE_ONDULATOIRE.md", category: "fondamentaux",
      title: "La Trinité ondulatoire", summary: "Lumière, espace, temps — la géométrie inévitable de toute émergence." },
    { file: "GENESE_MATHEMATIQUE.md", category: "fondamentaux",
      title: "Genèse mathématique", summary: "De la corde à l'équation mère : le nombre est une onde." },
    { file: "MATHEMATIQUES_ONDULATOIRES.md", category: "fondamentaux",
      title: "Mathématiques ondulatoires", summary: "La refondation des mathématiques sur les ondes, sept substitutions fondamentales." },
    { file: "NECESSITE_PAS_POSTULAT.md", category: "fondamentaux",
      title: "Nécessité, pas postulat", summary: "Pourquoi la théorie n'est pas un postulat mais une nécessité." },
    { file: "POSTULAT_OU_PREUVE.md", category: "fondamentaux",
      title: "Postulat ou preuve ?", summary: "Le statut épistémologique de l'équation maîtresse." },
    { file: "DERIVATION_1_PHI.md", category: "derivations",
      title: "Dérivation de 1/φ", summary: "Trois conditions de stabilité cosmique → la solution unique α = 1/φ (théorème de Hurwitz)." },
    { file: "DERIVATION_LAMBDA.md", category: "derivations",
      title: "Dérivation de Λ", summary: "La constante cosmologique comme résidu d'interférence — le problème ouvert." },
    { file: "TRADUCTION_ONDULATOIRE_LLM.md", category: "applications",
      title: "Traduction ondulatoire LLM", summary: "Les 36 correspondances entre les capacités des LLM et les opérations ondulatoires." },
    { file: "TRADUCTION_ONDULATOIRE_TTS.md", category: "applications",
      title: "Traduction ondulatoire TTS", summary: "Les 25 correspondances entre la synthèse vocale classique et le paradigme harmonique." },
    { file: "LANGAGE_ONDULATOIRE.md", category: "applications",
      title: "Le langage ondulatoire", summary: "Écrire, lire et exécuter des programmes en langage ondulatoire." },
    { file: "CONVERGENCE_DES_PREUVES.md", category: "applications",
      title: "Convergence des preuves", summary: "Huit domaines de validation, une seule théorie — le rasoir d'Occam ultime." },
    { file: "THEORIES_SURVIVANT_THU.md", category: "ouverts",
      title: "Théories survivant à la THU", summary: "Quelles théories passent les cinq critères de survie imposés par la THU." },
    { file: "PROBLEME_OUVERT_GAP_GSM8K.md", category: "ouverts",
      title: "Problème ouvert — le gap GSM8K", summary: "Le diagnostic honnête du gap de 14,6 points entre moteur spectral et conventionnel." },
    { file: "PROBLEME_OUVERT_EINSTEIN_V3.md", category: "ouverts",
      title: "Problème ouvert d'Einstein", summary: "L'écart de 120 ordres de grandeur de la constante cosmologique." }
  ],

  /* Animations — scènes du théâtre (moteur dans animations.js) */
  animations: [
    { id: "onde", icon: "Ψ₁", title: "L'Onde Primordiale",
      tag: "Le premier son", duration: "45 s",
      desc: "Quatre actes : le silence absolu, la première vibration, les sept harmoniques qui déploient l'espace, l'interférence cosmique." },
    { id: "emergence", icon: "n:0→7", title: "L'Émergence Totale",
      tag: "De la lumière à la conscience", duration: "65 s",
      desc: "Sept niveaux naissent de l'onde : le vide, Ψ₁, la gravité, la lumière, la matière, les forces, la vie, la conscience." },
    { id: "ouroboros", icon: "n:1↻7", title: "L'Ouroboros",
      tag: "Le cycle éternel", duration: "48 s",
      desc: "Le point voyage n=1→7→1 sur le cercle des sept constantes. Chaque fin est un commencement." },
    { id: "gravite", icon: "D¹ᐟᵠ=G", title: "La Gravité",
      tag: "L'espace-temps qui se courbe", duration: "interactif",
      desc: "La masse courbe l'espace-temps par interférence. Ajoutez de la masse, regardez le puits se creuser." }
  ],

  /* Langage ondulatoire — primitives et types */
  waveLanguage: {
    types: [
      { name: "Vecteur d'onde", note: "ψ ∈ ℂ⁵¹²", usage: "Entité fondamentale (mot, phonème, image, protéine)" },
      { name: "Enveloppe", note: "E ∈ ℝ¹²⁸", usage: "Magnitude spectrale lissée — filtre, timbre, style" },
      { name: "Scalaire", note: "s ∈ ℝ", usage: "Score, poids, énergie" },
      { name: "Phase", note: "θ ∈ [0, 2π)", usage: "Position, rotation, temps" },
      { name: "Hologramme", note: "H ∈ ℂ⁵¹²", usage: "Superposition de ψ — mémoire, base de connaissance" }
    ],
    primitives: [
      { name: "encode", sig: "encode(entity, dim=512)", desc: "monde → ψ : l'entité devient un vecteur complexe unitaire déterministe (FNV1a + φ-spacing).",
        use: "Toute entité discrète a un ψ." },
      { name: "decode", sig: "decode(ψ, vocabulary, top_k=5)", desc: "ψ → monde : les plus proches voisins par résonance dans le vocabulaire.",
        use: "Retrouver le mot derrière l'onde." },
      { name: "bind", sig: "bind(ψa, ψb)", desc: "lier deux concepts : convolution circulaire HRR — IFFT(FFT(a)·FFT(b)). Réversible.",
        use: "Diphone, fait sujet-relation-objet, tool-use." },
      { name: "unbind", sig: "unbind(ψa, ψb)", desc: "délier par corrélation circulaire — l'inverse exact du binding.",
        use: "Résoudre une association, répondre à une requête." },
      { name: "superpose", sig: "superpose(*ψ, weights)", desc: "addition d'ondes → hologramme H = Σ wᵢ·ψᵢ. Linéaire, commutative, associative.",
        use: "Contexte, mémoire, preuve = somme de prémisses." },
      { name: "resonate", sig: "resonate(ψa, ψb)", desc: "résonance = similarité cosinus complexe Re(⟨a|b⟩) ∈ [−1, 1]. C'est l'attention.",
        use: "Attention(Q,K) ≡ resonance(ψ_Q, ψ_K)." },
      { name: "rotate", sig: "rotate(ψ, angle)", desc: "rotation de phase globale ψ·e^{iθ} — le groupe U(1), préserve la norme.",
        use: "Encodage positionnel, décalage sémantique." },
      { name: "normalize", sig: "normalize(ψ)", desc: "projection sur le cercle unité ψ/|ψ| — l'état par défaut du paradigme.",
        use: "Équivalent 0-paramètre de la LayerNorm." },
      { name: "interfere", sig: "interfere(ψa, ψb, ε=0.1)", desc: "interférence contrôlée ψa + ε·ψb — connexion surréaliste à faible ε.",
        use: "Créativité, analogies inattendues." },
      { name: "diffract", sig: "diffract(ψ, inverse=False)", desc: "FFT / IFFT : passage domaine temporel ↔ fréquentiel.",
        use: "Analyse spectrale, débruitage." },
      { name: "filter_wave", sig: "filter_wave(ψ, filter)", desc: "filtrage spectral adaptatif : débruitage, extraction de bande, style.",
        use: "Timbre, séparation source/filtre." },
      { name: "phase_shift", sig: "phase_shift(ψ, shift)", desc: "décalage de phase par dimension — rotation fine de l'espace.",
        use: "Manipulations sémantiques ciblées." },
      { name: "emerge", sig: "emerge(*ψ, temperature=0.5)", desc: "émergence créative : superposition pondérée par la cohérence mutuelle (centralité).",
        use: "Génération, poésie, synthèse." }
    ]
  },

  /* 36 équivalences LLM classique → ondulatoire */
  equivalences: [
    { n: 1, llm: "Token Embedding", wave: "FNV1a + φ-spacing → ℂ⁵¹²", file: "holographic_encoder.py" },
    { n: 2, llm: "Positional Encoding", wave: "Phase naturelle (rotation)", file: "holographic_encoder.py" },
    { n: 3, llm: "Attention Q·K", wave: "Résonance Re(⟨ψ_Q|ψ_K⟩)", file: "harmonic_attention.py" },
    { n: 4, llm: "Multi-Head Attention", wave: "Résonance multi-fréquence (φ^k)", file: "harmonic_attention.py" },
    { n: 5, llm: "Layer Normalization", wave: "Projection unitaire |ψ|=1", file: "holographic_encoder.py" },
    { n: 6, llm: "Residual Connection", wave: "Superposition ψ_out + ψ_in", file: "Partout" },
    { n: 7, llm: "Feed-Forward Network", wave: "Propagation de phase ψ·e^{iθ(ψ)}", file: "phase_amplifier.py" },
    { n: 8, llm: "GeLU / ReLU / SwiGLU", wave: "Saturation de phase naturelle", file: "phase_amplifier.py" },
    { n: 9, llm: "LM Head (logits)", wave: "Scores de cohérence Re(⟨ψ|ψ_c⟩)", file: "wave_decoder.py" },
    { n: 10, llm: "Softmax", wave: "Normalisation par cohérence", file: "harmonic_attention.py" },
    { n: 11, llm: "Temperature Sampling", wave: "Bruit de phase δ·N(0,1)", file: "wave_sampling.py" },
    { n: 12, llm: "Top-p Sampling", wave: "Cône de cohérence (seuil angulaire)", file: "wave_sampling.py" },
    { n: 13, llm: "Top-k Sampling", wave: "Filtrage par cohérence décroissante", file: "wave_sampling.py" },
    { n: 14, llm: "Beam Search", wave: "Interférence multi-chemin", file: "beam_search.py" },
    { n: 15, llm: "Gradient Descent", wave: "Rotation de phase vers cohérence max", file: "phase_amplifier.py" },
    { n: 16, llm: "Loss Function", wave: "Gap de cohérence 1−Re(⟨ψ_p|ψ_t⟩)", file: "wave_fine_tune.py" },
    { n: 17, llm: "Fine-Tuning", wave: "Renforcement d'amplitude", file: "wave_fine_tune.py" },
    { n: 18, llm: "LoRA / PEFT", wave: "Injection locale sans dégradation", file: "few_shot_injector.py" },
    { n: 19, llm: "RLHF", wave: "Boucle phase-amplitude (feedback ondulatoire)", file: "feedback_loop.py" },
    { n: 20, llm: "DPO / Constitutional AI", wave: "ψ_alignement permanent", file: "conscious_intelligence.py" },
    { n: 21, llm: "Few-Shot Learning", wave: "Verrouillage de phase", file: "few_shot_injector.py" },
    { n: 22, llm: "Zero-Shot", wave: "Cohérence naturelle", file: "Partout" },
    { n: 23, llm: "RAG", wave: "Rappel holographique H ☆ ψ_Q", file: "harmonic_brain.py" },
    { n: 24, llm: "Chain-of-Thought", wave: "Amplification de phase en cascade", file: "phase_amplifier.py" },
    { n: 25, llm: "System Prompt", wave: "Phase initiale ψ_0", file: "harmonic_brain.py" },
    { n: 26, llm: "Role Prompting", wave: "Rotation de l'espace des phases", file: "harmonic_style.py" },
    { n: 27, llm: "Style Transfer", wave: "Modulation de motif d'onde", file: "harmonic_style.py, wave_styler.py" },
    { n: 28, llm: "Poésie / Créativité", wave: "Sélection par cohérence de phase émotionnelle", file: "wave_poetry.py" },
    { n: 29, llm: "Narration Structurée", wave: "Arc de phase narratif (0→π→2π)", file: "wave_narrative.py" },
    { n: 30, llm: "Contrôle d'hallucination", wave: "Seuil de cohérence (impossible par construction)", file: "conscious_intelligence.py" },
    { n: 31, llm: "Refus de répondre", wave: "Absence de résonance", file: "conscious_intelligence.py" },
    { n: 32, llm: "MoE (Mixture of Experts)", wave: "Gate par cohérence multi-domaine", file: "harmonic_brain.py" },
    { n: 33, llm: "Quantization / Pruning", wave: "Déjà minimal (8 Ko/état)", file: "Architecture" },
    { n: 34, llm: "KV-Cache", wave: "Hologramme (H stocke tout, H ☆ ψ_Q retrouve tout)", file: "hologram_store.py" },
    { n: 35, llm: "Tool Use / Function Calling", wave: "Binding ψ_intention ⊗ ψ_outil", file: "wave_tool_use.py" },
    { n: 36, llm: "Perplexity", wave: "Entropie ondulatoire H(ψ)", file: "wave_perplexity.py" }
  ]
};
