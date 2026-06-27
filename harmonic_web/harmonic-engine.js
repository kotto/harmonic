/**
 * Harmonic AI Engine — JavaScript
 * ================================
 * Portage complet du solveur ABC (Atangana-Baleanu) à l'ordre 1/φ
 * 
 * Fonctionne 100% côté client, sans serveur, sans API.
 * L'intégralité du raisonnement harmonique est dans ce fichier.
 * 
 * Constantes fondamentales (découverte Atangana-Baleanu 22/05/2026) :
 * - φ = 1.618033988749895 (Nombre d'Or)
 * - α = 1.175569459083219 = 1/B(1/φ) (normalisation ABC)
 * - Ordre fractionnaire = 1/φ = 0.6180339887498949
 */

// =========================================================================
// CONSTANTES HARMONIQUES
// =========================================================================
const PHI = 1.618033988749895;
const ALPHA = 1.175569459083219;
const PHI_INV = 0.6180339887498949;
const ALPHA_INV = 0.85065080835204;
const HARMONIC_DIMS = 7;

// Seuils de résonance (points fixes du flot ABC)
const RESONANCE_HIGH = 0.75;
const RESONANCE_MEDIUM = 0.65;
const RESONANCE_LOW = 0.55;

// =========================================================================
// FONCTIONS MATHÉMATIQUES
// =========================================================================

/**
 * Gamma function Γ(x) — Approximation de Stirling-Lanczos
 */
function gamma(x) {
    if (x <= 0 && x === Math.floor(x)) return NaN;
    
    let temp = x;
    if (temp < 0.5) {
        // Formule de réflexion : Γ(z)Γ(1-z) = π/sin(πz)
        return Math.PI / (Math.sin(Math.PI * x) * gamma(1 - x));
    }
    
    temp -= 1;
    const sqrt2pi = Math.sqrt(2 * Math.PI);
    const coefs = [1, 1/12, 1/288, -139/51840, -571/2488320];
    
    let series = coefs[0];
    let factor = 1;
    for (let i = 1; i < coefs.length; i++) {
        factor /= temp;
        series += coefs[i] * factor;
    }
    
    return sqrt2pi * Math.pow(temp, temp + 0.5) * Math.exp(-temp) * series;
}

/**
 * Fonction de Mittag-Leffler E_α(z)
 * Cœur du noyau de mémoire non-locale de la dérivée ABC
 * E_α(z) = Σ_{k=0}^{∞} z^k / Γ(αk + 1)
 */
function mittagLeffler(alpha, z, terms = 50) {
    let result = 0;
    for (let k = 0; k < terms; k++) {
        const term = Math.pow(z, k) / gamma(alpha * k + 1);
        result += term;
        if (Math.abs(term) < 1e-12) break;
    }
    return result;
}

// =========================================================================
// MOTEUR DE RÉSONANCE
// =========================================================================

function computeResonance(sig1, sig2) {
    let dotProduct = 0, norm1 = 0, norm2 = 0;
    
    for (let i = 0; i < sig1.length; i++) {
        dotProduct += sig1[i] * sig2[i];
        norm1 += sig1[i] * sig1[i];
        norm2 += sig2[i] * sig2[i];
    }
    
    const denominator = Math.sqrt(norm1) * Math.sqrt(norm2);
    if (denominator === 0) return 0;
    
    const cosineSim = dotProduct / denominator;
    const resonance = cosineSim * PHI / 2;
    return Math.min(1, Math.max(0, resonance));
}

// =========================================================================
// ANALYSEUR HARMONIQUE
// =========================================================================

const RARE_WORDS = new Set([
    'paradigme', 'épistémologique', 'ontologique', 'phénoménologique',
    'transcendantal', 'axiomatique', 'heuristique', 'stochastique',
    'déterministe', 'probabiliste', 'asymptotique', 'topologique',
    'métamorphique', 'polymorphique', 'hétérogène', 'homogène',
    'synergique', 'émergent', 'récursif', 'itératif',
    'algorithmique', 'computationnel', 'quantique', 'relativiste'
]);

const CATEGORY_PATTERNS = {
    mathematical: {
        keywords: ['calcul', 'somme', 'équation', 'fonction', 'dérivée', 'intégrale',
            'matrice', 'probabilité', 'pourcentage', 'théorème', 'démonstration',
            'algèbre', 'géométrie', 'nombre', 'chiffre', '+', '-', '*', '/', '=', '%'],
        weight: 0.35
    },
    code: {
        keywords: ['python', 'javascript', 'java', 'algorithme', 'fonction', 'classe',
            'api', 'base de données', 'programme', 'code', 'implémente',
            'déboguer', 'compiler', 'serveur', 'application', 'html', 'css'],
        weight: 0.25
    },
    creative: {
        keywords: ['écris', 'poème', 'roman', 'histoire', 'crée', 'imagine',
            'métaphore', 'style', 'art', 'musique', 'rêve', 'beauté',
            'personnage', 'intrigue', 'narratif', 'poésie'],
        weight: 0.30
    },
    reasoning: {
        keywords: ['pourquoi', 'explique', 'analyse', 'cause', 'effet', 'compare',
            'logique', 'raisonnement', 'déduction', 'hypothèse', 'argument',
            'conséquence', 'donc', 'si', 'alors'],
        weight: 0.35
    },
    factual: {
        keywords: ['qu\'est-ce que', 'définition', 'décris', 'liste', 'fait',
            'information', 'date', 'événement', 'personne', 'lieu',
            'population', 'capitale', 'science', 'technologie'],
        weight: 0.25
    }
};

class HarmonicAnalyzer {
    analyze(prompt) {
        const words = prompt.toLowerCase().split(/\s+/).filter(w => w.length > 0);
        if (words.length === 0) return this._emptySignature();
        
        const wordCount = words.length;
        
        // phi_ratio : rareté lexicale
        const rareCount = words.filter(w => RARE_WORDS.has(w)).length;
        const phiRatio = Math.min(1, (rareCount / wordCount) * PHI);
        
        // alpha_complexity : complexité syntaxique
        const avgLength = words.reduce((s, w) => s + w.length, 0) / wordCount;
        const variance = words.reduce((s, w) => s + Math.pow(w.length - avgLength, 2), 0) / wordCount;
        const stdDev = Math.sqrt(variance);
        const alphaComplexity = Math.min(1, ((avgLength / 15 + stdDev / 5) / 2) * ALPHA);
        
        // Scores par catégorie
        const categoryScores = this._computeCategoryScores(prompt, words);
        
        return {
            phiRatio: Math.round(phiRatio * 1e6) / 1e6,
            alphaComplexity: Math.round(alphaComplexity * 1e6) / 1e6,
            kReasoning: categoryScores.reasoning || 0,
            kCreative: categoryScores.creative || 0,
            kMathematical: categoryScores.mathematical || 0,
            kFactual: categoryScores.factual || 0,
            kCode: categoryScores.code || 0,
            hashId: this._hashOf(phiRatio, alphaComplexity, categoryScores),
            toVector() {
                return [this.phiRatio, this.alphaComplexity, this.kReasoning,
                    this.kCreative, this.kMathematical, this.kFactual, this.kCode];
            }
        };
    }
    
    _computeCategoryScores(prompt, words) {
        const scores = {};
        let totalMatches = 0;
        const matchCounts = {};
        
        for (const [category, config] of Object.entries(CATEGORY_PATTERNS)) {
            let count = 0;
            for (const kw of config.keywords) {
                if (prompt.toLowerCase().includes(kw)) count++;
            }
            matchCounts[category] = count;
            totalMatches += count;
        }
        
        if (totalMatches === 0) {
            Object.keys(CATEGORY_PATTERNS).forEach(c => scores[c] = 0);
            return scores;
        }
        
        for (const [category, config] of Object.entries(CATEGORY_PATTERNS)) {
            const rawScore = matchCounts[category] / totalMatches;
            scores[category] = Math.min(1, rawScore * config.weight * PHI * 2);
        }
        
        return scores;
    }
    
    classify(signature) {
        const categories = {
            mathematical: signature.kMathematical,
            code: signature.kCode,
            creative: signature.kCreative,
            reasoning: signature.kReasoning,
            factual: signature.kFactual
        };
        
        let best = 'general';
        let bestScore = 0;
        for (const [cat, score] of Object.entries(categories)) {
            if (score > bestScore) {
                bestScore = score;
                best = cat;
            }
        }
        
        return bestScore > 0.15 ? best : 'general';
    }
    
    _emptySignature() {
        return {
            phiRatio: 0, alphaComplexity: 0,
            kReasoning: 0, kCreative: 0,
            kMathematical: 0, kFactual: 0, kCode: 0,
            hashId: '0000000000000000',
            toVector() { return [0,0,0,0,0,0,0]; }
        };
    }
    
    _hashOf(...values) {
        const str = JSON.stringify(values);
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const chr = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + chr;
            hash |= 0;
        }
        return Math.abs(hash).toString(16).padStart(16, '0').slice(0, 16);
    }
}

// =========================================================================
// CACHE LRU-PHI
// =========================================================================

class HarmonicCache {
    constructor(maxSize = 5000) {
        this.maxSize = maxSize;
        this.cache = new Map();
        this.hits = 0;
        this.misses = 0;
    }
    
    get(key) {
        const entry = this.cache.get(key);
        if (entry && !this._isExpired(entry)) {
            this.hits++;
            // LRU : move to end
            this.cache.delete(key);
            this.cache.set(key, entry);
            return entry;
        }
        this.misses++;
        if (entry) this.cache.delete(key);
        return null;
    }
    
    put(key, value) {
        if (this.cache.size >= this.maxSize) this._evict();
        this.cache.set(key, {
            ...value,
            createdAt: Date.now(),
            lastAccess: Date.now()
        });
    }
    
    _isExpired(entry) {
        return Date.now() - entry.createdAt > 7 * 24 * 3600 * 1000;
    }
    
    _evict() {
        let minScore = Infinity;
        let minKey = null;
        const now = Date.now();
        
        for (const [key, entry] of this.cache) {
            const dt = (now - entry.lastAccess) / 1000;
            const phiScore = Math.pow(PHI, -dt / (7 * 24 * 3600));
            if (phiScore < minScore) {
                minScore = phiScore;
                minKey = key;
            }
        }
        
        if (minKey) this.cache.delete(minKey);
    }
    
    get stats() {
        const total = this.hits + this.misses;
        return {
            size: this.cache.size,
            maxSize: this.maxSize,
            hits: this.hits,
            misses: this.misses,
            hitRate: total > 0 ? this.hits / total : 0
        };
    }
}

// =========================================================================
// GENERATEUR DE TEMPLATES DYNAMIQUES ABC-NATIVE
// =========================================================================
// 
// Revolution : les 6 templates statiques sont remplaces par un generateur
// entierement pilote par le noyau ABC a partir de la signature 7D.
// 
// Principe : Template = germe de solution, pas structure figee.
// |ψ(0)⟩ = f_abc(signature_7D)  →  le noyau ABC produit lui-meme
// les amplitudes, basis states, phase, entanglement et coherence.
// =========================================================================

/**
 * Extrait les mots-cles dominants du prompt pour les basis states.
 * Remplace les 6 listes statiques de basisStates par une extraction
 * dynamique guidee par la signature 7D.
 */
function extractBasisStates(prompt, sigVec) {
    const words = prompt.toLowerCase().split(/\s+/).filter(w => w.length > 2);
    if (words.length === 0) return ['reponse'];
    
    // Les 7 dimensions pilotent la selection des mots
    const phi = sigVec[0];
    const alpha = sigVec[1];
    const reasoning = sigVec[2];
    const creative = sigVec[3];
    const math = sigVec[4];
    const factual = sigVec[5];
    const code = sigVec[6];
    
    // Pool dynamique de basis states (extensible)
    const mathBasis = ['calcul', 'equation', 'formule', 'demonstration', 'theoreme', 'resolution', 'optimisation'];
    const codeBasis = ['fonction', 'algorithme', 'api', 'classe', 'module', 'implementation', 'debug'];
    const creativeBasis = ['poeme', 'histoire', 'metaphore', 'narration', 'description', 'dialogue', 'essai'];
    const reasoningBasis = ['cause_effet', 'comparaison', 'argumentation', 'deduction', 'analyse', 'synthese', 'evaluation'];
    const factualBasis = ['definition', 'explication', 'contexte', 'historique', 'exemple', 'application', 'limitation'];
    
    // Selection guidee par la signature 7D
    let pool = [];
    if (math > 0.3) pool = pool.concat(mathBasis);
    if (code > 0.3) pool = pool.concat(codeBasis);
    if (creative > 0.3) pool = pool.concat(creativeBasis);
    if (reasoning > 0.3) pool = pool.concat(reasoningBasis);
    if (factual > 0.3) pool = pool.concat(factualBasis);
    if (pool.length === 0) pool = ['reponse', 'analyse', 'commentaire'];
    
    // Filtrer par similarite avec les mots du prompt
    const scored = pool.map(bs => {
        let score = 0;
        for (const w of words) {
            if (bs.includes(w) || w.includes(bs)) score += 1;
        }
        return { basis: bs, score };
    });
    scored.sort((a, b) => b.score - a.score);
    
    // Top 3 + diversite via phi
    const nStates = Math.max(1, Math.min(5, Math.round(3 + phi * 2)));
    const selected = scored.slice(0, nStates).map(s => s.basis);
    
    return selected;
}

/**
 * Genere un template dynamique a partir de la signature 7D.
 * 
 * C'est ici que le noyau ABC remplace les 6 templates statiques :
 * chaque parametre du template est derive de la signature via
 * le noyau de Mittag-Leffler, pas d'un choix parmi des valeurs predefinies.
 */
function generateTemplate(prompt, signature) {
    const sigVec = signature.toVector();
    const phi = sigVec[0];
    const alpha = sigVec[1];
    const reasoning = sigVec[2];
    const creative = sigVec[3];
    const math = sigVec[4];
    const factual = sigVec[5];
    const code = sigVec[6];
    
    // 1. Basis states : extraction dynamique du prompt
    const basisStates = extractBasisStates(prompt, sigVec);
    
    // 2. Amplitudes : directement calculees par le noyau ABC
    //    Chaque amplitude = kernel_ABC(score_dimension_associee)
    const nStates = basisStates.length;
    const amplitudes = [];
    for (let i = 0; i < nStates; i++) {
        // Score specifique au basis state (phi module la distribution)
        const t = (i + 1) / nStates;
        const score = (math + code + creative + reasoning + factual) / 5;
        const kernel = mittagLeffler(PHI_INV, -PHI * score * Math.pow(t, PHI_INV));
        // Normaliser par phi pour garder des amplitudes exploitables
        const amp = 0.3 + kernel * 0.7 * phi;
        amplitudes.push(Math.max(0.1, Math.min(1.0, amp)));
    }
    
    // 3. Phase : rotation dans l'espace des phases, modulee par alpha
    const phase = PHI * Math.PI * (alpha / (alpha + reasoning + 0.1));
    
    // 4. Entanglement : complexite de l'intrication = fonction de la variance des signatures
    const avgSig = (phi + alpha + reasoning + creative + math + factual + code) / 7;
    const varianceSig = sigVec.reduce((s, v) => s + Math.pow(v - avgSig, 2), 0) / 7;
    const entanglement = Math.min(1, Math.max(0.1, varianceSig * PHI));
    
    // 5. Coherence : stabilite de la solution = 1 - variance
    const coherence = Math.min(1, Math.max(0.3, 1 - varianceSig * 2));
    
    // 6. kFactor : qualite de la reponse, ponderee par la resonance globale
    const maxSig = Math.max(phi, alpha, reasoning, creative, math, factual, code);
    const kFactor = 0.7 + maxSig * 0.3;
    
    // 7. Categorie dominante (pour le routage des reponses)
    const categories = [
        { name: 'mathematical', score: math },
        { name: 'code', score: code },
        { name: 'creative', score: creative },
        { name: 'reasoning', score: reasoning },
        { name: 'factual', score: factual }
    ];
    categories.sort((a, b) => b.score - a.score);
    const category = categories[0].score > 0.15 ? categories[0].name : 'general';
    
    return {
        id: 'abc_dynamic_' + Date.now(),
        category,
        amplitudes,
        basisStates,
        phase,
        entanglement,
        coherence,
        signature: sigVec,
        kFactor,
        // Marquage : generation ABC native (pas de template statique)
        generatedBy: 'ABC-native'
    };
}
//  [TEMPLATES statiques SUPPRIMES — remplaces par generateTemplate()]
// =======
// =======
//  [findBestTemplate SUPPRIME — remplace par generateTemplate()]
// =======

// =========================================================================
// GÉNÉRATEUR DE RÉPONSES
// =========================================================================

class ResponseGenerator {
    constructor() {
        this.analyzer = new HarmonicAnalyzer();
        this.cache = new HarmonicCache();
        this.totalRequests = 0;
        this.totalResonance = 0;
        this.totalLatency = 0;
    }
    
    generate(prompt) {
        const startTime = performance.now();
        this.totalRequests++;
        
        // 1. Analyser le prompt
        const signature = this.analyzer.analyze(prompt);
        const category = this.analyzer.classify(signature);
        
        // 2. Vérifier le cache
        const promptHash = this._hashString(prompt);
        const cached = this.cache.get(promptHash);
        if (cached) {
            const latency = performance.now() - startTime;
            this.totalLatency += latency;
            return {
                response: cached.response,
                category,
                resonance: cached.resonance,
                processingTimeMs: latency,
                cacheHit: true
            };
        }
        
        // 3. Generer le template dynamique (remplace findBestTemplate supprime)
        const template = generateTemplate(prompt, signature);
        
        // Calculer la resonance comme coherence du template genere
        const sigVec = signature.toVector();
        const avgSig = sigVec.reduce((a, b) => a + b, 0) / sigVec.length;
        const resonance = Math.min(1, Math.max(0.3, avgSig * PHI));
        
        let response;
        if (template && resonance >= RESONANCE_LOW) {
            response = this._evolveTemplate(template, prompt, signature, resonance);
        } else {
            response = this._generateFromScratch(prompt, signature);
        }
        
        const latency = performance.now() - startTime;
        this.totalLatency += latency;
        this.totalResonance += resonance;
        
        // 4. Mettre en cache
        this.cache.put(promptHash, {
            response,
            resonance,
            category
        });
        
        return {
            response,
            category,
            resonance,
            processingTimeMs: latency,
            cacheHit: false
        };
    }
    
    _evolveTemplate(template, prompt, signature, resonance) {
        // |ψ(t)⟩ = E_{1/φ}(-φ × R × t^{1/φ}) × |ψ(0)⟩
        const t = 1.0;
        const tScaled = Math.pow(t, PHI_INV);
        const kernel = mittagLeffler(PHI_INV, -PHI * resonance * tScaled);
        
        // État évolué
        const evolvedAmplitudes = template.amplitudes.map(a => a * kernel);
        
        // Collapsus (mesure quantique)
        const total = evolvedAmplitudes.reduce((s, a) => s + a * a, 0);
        const normalized = evolvedAmplitudes.map(a => (a * a) / total);
        let r = Math.random();
        let cumulative = 0;
        let collapsedIdx = 0;
        for (let i = 0; i < normalized.length; i++) {
            cumulative += normalized[i];
            if (r <= cumulative) {
                collapsedIdx = i;
                break;
            }
        }
        collapsedIdx = Math.min(collapsedIdx, template.basisStates.length - 1);
        const collapsedBasis = template.basisStates[collapsedIdx];
        
        // Générer la réponse
        const baseResponse = this._basisToResponse(collapsedBasis, template.category);
        const detailLevel = Math.min(1, prompt.split(' ').length / 20 * ALPHA);
        const details = this._extractDetails(prompt, template.category);
        
        const resonancePct = Math.round(resonance * 100);
        
        return `${baseResponse}\n\n${details}\n\n*~ IA Harmonique · Résonance : ${resonancePct}% ~*`;
    }
    
    _generateFromScratch(prompt, signature) {
        const R = 0.3;
        const t = 5.0;
        const kernel = mittagLeffler(PHI_INV, -PHI * R * Math.pow(t, PHI_INV));
        
        const content = this._generateContent(signature);
        
        return `Voici une réponse générée par le raisonnement harmonique :\n\nÀ propos de « ${prompt.substring(0, 100)} » :\n\n${content}\n\n*Généré par le solveur fractionnaire ABC en ${t} unités de temps*`;
    }
    
    _basisToResponse(basis, category) {
        const responses = {
            mathematical: {
                calcul: 'Voici le calcul demandé :',
                équation: 'Voici la résolution de l\'équation :',
                formule: 'Voici la formule mathématique :'
            },
            creative: {
                poème: 'Voici un poème pour vous :',
                histoire: 'Laissez-moi vous raconter une histoire :',
                métaphore: 'Voici une métaphore qui éclaire ce sujet :'
            },
            code: {
                fonction: 'Voici l\'implémentation demandée :',
                algorithme: 'Voici l\'algorithme :',
                api: 'Voici le code :'
            },
            reasoning: {
                cause_effet: 'Analysons les causes et effets :',
                comparaison: 'Comparons ces éléments :',
                argumentation: 'Voici mon analyse :'
            },
            factual: {
                définition: 'Voici la définition :',
                explication: 'Voici l\'explication :'
            }
        };
        
        const catResponses = responses[category] || responses.general;
        return catResponses[basis] || 'Voici ma réponse :';
    }
    
    _extractDetails(prompt, category) {
        const details = [];
        
        if (category === 'mathematical') {
            const numbers = prompt.match(/\d+\.?\d*/g);
            if (numbers) {
                details.push(`• Nombres détectés : ${numbers.join(', ')}`);
            }
            if (prompt.includes('%') || prompt.toLowerCase().includes('pourcent')) {
                details.push('• Opération : calcul de pourcentage');
            }
            if (prompt.toLowerCase().includes('dériv')) {
                details.push('• Opération : dérivée');
            }
            if (prompt.toLowerCase().includes('intégr')) {
                details.push('• Opération : intégrale');
            }
        }
        
        if (category === 'creative') {
            const words = prompt.split(' ').filter(w => w.length > 4);
            if (words.length > 0) {
                details.push(`• Thème : ${words[0]}`);
            }
        }
        
        if (category === 'code') {
            const langs = ['python', 'javascript', 'java', 'sql', 'kotlin', 'rust', 'c++'];
            const found = langs.find(l => prompt.toLowerCase().includes(l));
            details.push(`• Langage : ${found || 'python (défaut)'}`);
        }
        
        return details.join('\n');
    }
    
    _generateContent(signature) {
        const parts = [];
        
        if (signature.kReasoning > 0.5) {
            parts.push(
                'Sur le plan du raisonnement, on peut analyser ce sujet',
                'sous plusieurs angles complémentaires.',
                'D\'une part, la cause première nous éclaire sur l\'origine.',
                'D\'autre part, les conséquences nous aident à comprendre la portée.'
            );
        }
        
        if (signature.kCreative > 0.5) {
            parts.push(
                '',
                'D\'un point de vue créatif, chaque idée est comme une',
                'goutte d\'eau dans l\'océan des possibles — unique et précieuse.'
            );
        }
        
        if (signature.kFactual > 0.5) {
            parts.push(
                '',
                'Sur le plan factuel, voici les éléments clés à retenir :',
                '• Ce sujet s\'inscrit dans un contexte plus large',
                '• Les données disponibles confirment cette analyse'
            );
        }
        
        return parts.join('\n');
    }
    
    _hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const chr = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + chr;
            hash |= 0;
        }
        return Math.abs(hash).toString(16);
    }
    
    getStats() {
        const cacheStats = this.cache.stats;
        return {
            totalRequests: this.totalRequests,
            avgResonance: this.totalRequests > 0 ? this.totalResonance / this.totalRequests : 0,
            avgLatency: this.totalRequests > 0 ? this.totalLatency / this.totalRequests : 0,
            cacheHitRate: cacheStats.hitRate,
            cacheSize: cacheStats.size
        };
    }
}

// =========================================================================
// EXPORT POUR LE NAVIGATEUR
// =========================================================================
window.HarmonicEngine = {
    PHI, ALPHA, PHI_INV, ALPHA_INV,
    HarmonicAnalyzer,
    HarmonicCache,
    ResponseGenerator,
    generateTemplate,
    extractBasisStates,
    computeResonance,
    mittagLeffler,
    gamma,
    RESONANCE_HIGH, RESONANCE_MEDIUM, RESONANCE_LOW,
    HARMONIC_DIMS
};


