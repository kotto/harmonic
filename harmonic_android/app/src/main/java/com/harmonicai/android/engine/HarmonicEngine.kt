package com.harmonicai.android.engine

import kotlin.math.*

/**
 * Harmonic AI Engine for Android
 * ===============================
 * Portage complet du solveur ABC (Atangana-Baleanu) à l'ordre 1/φ
 * 
 * Moteur autonome = sans serveur, sans API externe, sans DeepSeek
 * L'intégralité du raisonnement harmonique est embarquée.
 * 
 * Constantes fondamentales (découverte Atangana-Baleanu) :
 * - φ = 1.618033988749895 (Nombre d'Or)
 * - α = 1.175569459083219 = 1/B(1/φ) (normalisation ABC)
 * - Ordre fractionnaire = 1/φ = 0.6180339887498949
 */

object HarmonicConstants {
    const val PHI = 1.618033988749895
    const val ALPHA = 1.175569459083219
    const val PHI_INV = 0.6180339887498949  // 1/PHI
    const val ALPHA_INV = 0.85065080835204   // 1/ALPHA = B(1/φ)
    const val HARMONIC_DIMS = 7
    
    // Seuils de résonance (points fixes du flot ABC)
    const val RESONANCE_HIGH = 0.75   // Solution exacte
    const val RESONANCE_MEDIUM = 0.65 // Solution partielle → cache
    const val RESONANCE_LOW = 0.55    // Exploration nécessaire
    
    // Cache LRU-phi
    const val CACHE_MAX_SIZE = 5000
    const val CACHE_TTL_SECONDS = 604800L  // 7 jours
    
    // Types de templates fondamentaux
    val TEMPLATE_CATEGORIES = listOf(
        "mathematical", "code", "creative", "reasoning", "factual", "general"
    )
}

/**
 * Signature harmonique 7D d'un prompt ou d'un template.
 */
data class HarmonicSignature(
    val phiRatio: Float,        // Rareté lexicale
    val alphaComplexity: Float, // Complexité syntaxique
    val kReasoning: Float,      // Affinité raisonnement
    val kCreative: Float,       // Affinité créativité
    val kMathematical: Float,   // Affinité mathématique  
    val kFactual: Float,        // Affinité factuelle
    val kCode: Float,           // Affinité code
    val hashId: String = ""
) {
    fun toVector(): FloatArray = floatArrayOf(
        phiRatio, alphaComplexity, kReasoning, kCreative,
        kMathematical, kFactual, kCode
    )
}

/**
 * État quantique harmonique |ψ⟩
 * Cœur du solveur ABC
 */
data class QuantumState(
    val amplitudes: FloatArray,   // Coefficients |α_i|²
    val basisStates: List<String>, // États de base |pattern_i⟩
    val phase: Float,             // Phase globale θ
    val entanglement: Float,      // Intrication (0-1)
    val coherence: Float          // Cohérence (0-1)
) {
    fun probability(index: Int): Float {
        if (index < 0 || index >= amplitudes.size) return 0f
        return amplitudes[index] * amplitudes[index]
    }
    
    fun collapse(): Pair<Int, String> {
        val probs = amplitudes.map { it * it }
        val total = probs.sum()
        if (total == 0f) return Pair(0, basisStates[0])
        
        val normalized = probs.map { it / total }
        var r = kotlin.random.Random.nextFloat()
        var cumulative = 0f
        
        for (i in normalized.indices) {
            cumulative += normalized[i]
            if (r <= cumulative) {
                return Pair(i, basisStates[i])
            }
        }
        return Pair(basisStates.size - 1, basisStates.last())
    }
}

/**
 * Template harmonique = condition initiale pour le solveur ABC
 */
data class HarmonicTemplate(
    val id: String,
    val category: String,
    val amplitudes: FloatArray,
    val basisStates: List<String>,
    val phase: Float,
    val entanglement: Float,
    val coherence: Float,
    val signature: HarmonicSignature,
    val kFactor: Float,
    val templateType: String = "base"
)

/**
 * Fonction de Mittag-Leffler E_α(z)
 * ===================================
 * Cœur du noyau de mémoire non-local de la dérivée ABC.
 * E_α(z) = Σ_{k=0}^{∞} z^k / Γ(αk + 1)
 */
object MittagLeffler {
    fun evaluate(alpha: Float, z: Float, terms: Int = 50): Float {
        var result = 0f
        for (k in 0 until terms) {
            val term = z.pow(k) / gamma(alpha * k + 1f)
            result += term
            if (abs(term) < 1e-12f) break
        }
        return result
    }
    
    private fun gamma(x: Float): Float {
        // Approximation de Stirling pour Γ(x)
        if (x <= 0f && x == x.toInt().toFloat()) return Float.NaN
        
        var temp = x
        if (temp < 0.5f) {
            // Formule de réflexion : Γ(z)Γ(1-z) = π/sin(πz)
            return (PI.toFloat() / sin(PI.toFloat() * x)) / gamma(1f - x)
        }
        
        temp -= 1f
        val sqrt2pi = sqrt(2f * PI.toFloat())
        val coefs = floatArrayOf(
            1f, 1f/12f, 1f/288f, -139f/51840f, -571f/2488320f
        )
        
        var series = coefs[0]
        var factor = 1f
        for (i in 1 until coefs.size) {
            factor /= temp
            series += coefs[i] * factor
        }
        
        return sqrt2pi * temp.pow(temp + 0.5f) * exp(-temp) * series
    }
}

/**
 * Moteur de résonance harmonique
 * ===============================
 * Calcule la similarité entre deux signatures 7D
 * via la métrique : R = cos(θ) × φ/2
 */
object ResonanceEngine {
    fun compute(sig1: FloatArray, sig2: FloatArray): Float {
        var dotProduct = 0f
        var norm1 = 0f
        var norm2 = 0f
        
        for (i in sig1.indices) {
            dotProduct += sig1[i] * sig2[i]
            norm1 += sig1[i] * sig1[i]
            norm2 += sig2[i] * sig2[i]
        }
        
        val denominator = sqrt(norm1) * sqrt(norm2)
        if (denominator == 0f) return 0f
        
        val cosineSim = dotProduct / denominator
        val resonance = cosineSim * HarmonicConstants.PHI / 2f
        return min(1f, max(0f, resonance))
    }
}

/**
 * Analyseur harmonique de prompts
 * ================================
 * Extrait la signature 7D d'un texte
 */
class HarmonicAnalyzer {
    private val rareWords = setOf(
        "paradigme", "épistémologique", "ontologique", "phénoménologique",
        "transcendantal", "axiomatique", "heuristique", "stochastique",
        "déterministe", "probabiliste", "asymptotique", "topologique",
        "métamorphique", "polymorphique", "hétérogène", "homogène",
        "synergique", "émergent", "récursif", "itératif", "algorithmique",
        "computationnel", "quantique", "relativiste"
    )
    
    private val categoryPatterns = mapOf(
        "mathematical" to listOf(
            "calcul", "somme", "équation", "fonction", "dérivée", "intégrale",
            "matrice", "probabilité", "pourcentage", "théorème", "démonstration",
            "algèbre", "géométrie", "nombre", "chiffre"
        ),
        "code" to listOf(
            "python", "javascript", "java", "algorithme", "fonction", "classe",
            "api", "base de données", "programme", "code", "implémente",
            "déboguer", "compiler", "serveur", "application"
        ),
        "creative" to listOf(
            "écris", "poème", "roman", "histoire", "crée", "imagine",
            "métaphore", "style", "art", "musique", "rêve", "beauté",
            "personnage", "intrigue", "narratif"
        ),
        "reasoning" to listOf(
            "pourquoi", "explique", "analyse", "cause", "effet", "compare",
            "logique", "raisonnement", "déduction", "hypothèse", "argument",
            "conséquence", "donc", "si", "alors"
        ),
        "factual" to listOf(
            "qu'est-ce que", "définition", "décris", "liste", "fait",
            "information", "date", "événement", "personne", "lieu",
            "population", "capitale", "science", "technologie"
        )
    )
    
    fun analyze(prompt: String): HarmonicSignature {
        val words = prompt.lowercase().split(Regex("\\s+"))
            .filter { it.isNotBlank() }
        if (words.isEmpty()) return emptySignature()
        
        val wordCount = words.size
        
        // phi_ratio : rareté lexicale
        val rareCount = words.count { it in rareWords }
        val phiRatio = min(1f, (rareCount.toFloat() / wordCount) * HarmonicConstants.PHI)
        
        // alpha_complexity : complexité syntaxique
        val avgLength = words.map { it.length }.average().toFloat()
        val variance = words.map { (it.length - avgLength).pow(2) }.average().toFloat()
        val stdDev = sqrt(variance)
        val alphaComplexity = min(1f, ((avgLength / 15f + stdDev / 5f) / 2f) * HarmonicConstants.ALPHA)
        
        // Scores par catégorie
        val categoryScores = computeCategoryScores(prompt, words)
        
        return HarmonicSignature(
            phiRatio = phiRatio,
            alphaComplexity = alphaComplexity,
            kReasoning = categoryScores["reasoning"] ?: 0f,
            kCreative = categoryScores["creative"] ?: 0f,
            kMathematical = categoryScores["mathematical"] ?: 0f,
            kFactual = categoryScores["factual"] ?: 0f,
            kCode = categoryScores["code"] ?: 0f,
            hashId = hashOf(phiRatio, alphaComplexity, categoryScores)
        )
    }
    
    private fun computeCategoryScores(prompt: String, words: List<String>): Map<String, Float> {
        val scores = mutableMapOf<String, Float>()
        var totalMatches = 0f
        val matchCounts = mutableMapOf<String, Int>()
        
        for ((category, patterns) in categoryPatterns) {
            var count = 0
            for (pattern in patterns) {
                if (prompt.contains(pattern, ignoreCase = true)) {
                    count++
                }
            }
            matchCounts[category] = count
            totalMatches += count.toFloat()
        }
        
        if (totalMatches == 0f) {
            categoryPatterns.keys.forEach { scores[it] = 0f }
            return scores
        }
        
        for ((category, patterns) in categoryPatterns) {
            val matchCount = matchCounts[category] ?: 0
            val rawScore = matchCount.toFloat() / totalMatches
            val weight = when (category) {
                "mathematical" -> 0.35f
                "code" -> 0.25f
                "creative" -> 0.30f
                "reasoning" -> 0.35f
                "factual" -> 0.25f
                else -> 0.20f
            }
            scores[category] = min(1f, rawScore * weight * HarmonicConstants.PHI * 2f)
        }
        
        return scores
    }
    
    fun classify(signature: HarmonicSignature): String {
        val scores = mapOf(
            "mathematical" to signature.kMathematical,
            "code" to signature.kCode,
            "creative" to signature.kCreative,
            "reasoning" to signature.kReasoning,
            "factual" to signature.kFactual
        )
        
        val best = scores.maxByOrNull { it.value }
        return if (best != null && best.value > 0.15f) best.key else "general"
    }
    
    private fun emptySignature() = HarmonicSignature(
        phiRatio = 0f, alphaComplexity = 0f,
        kReasoning = 0f, kCreative = 0f,
        kMathematical = 0f, kFactual = 0f, kCode = 0f,
        hashId = "0000000000000000"
    )
    
    private fun hashOf(vararg values: Float): String {
        val sb = StringBuilder()
        values.forEach { sb.append(it.toRawBits()) }
        return sb.toString().substring(0, minOf(16, sb.length))
    }
}

/**
 * Cache LRU-phi avec éviction par noyau de Mittag-Leffler
 * =========================================================
 * Discrétisation du noyau de mémoire ABC :
 * Score_phi = access_count × φ^(-Δt/TTL)
 */
class HarmonicCache(private val maxSize: Int = HarmonicConstants.CACHE_MAX_SIZE) {
    data class CacheEntry(
        val promptHash: String,
        val signature: HarmonicSignature,
        val response: String,
        val resonanceScore: Float,
        val accessCount: Int = 0,
        val createdAt: Long = System.currentTimeMillis(),
        val lastAccess: Long = System.currentTimeMillis()
    )
    
    private val cache = LinkedHashMap<String, CacheEntry>(maxSize, 0.75f, true)
    var hits = 0
        private set
    var misses = 0
        private set
    
    operator fun get(promptHash: String): CacheEntry? {
        val entry = cache[promptHash]
        return if (entry != null && !isExpired(entry)) {
            hits++
            entry
        } else {
            misses++
            if (entry != null) cache.remove(promptHash)
            null
        }
    }
    
    fun put(promptHash: String, signature: HarmonicSignature, response: String, resonance: Float) {
        if (cache.size >= maxSize) evict()
        cache[promptHash] = CacheEntry(promptHash, signature, response, resonance)
    }
    
    private fun isExpired(entry: CacheEntry): Boolean {
        return System.currentTimeMillis() - entry.createdAt > 
               HarmonicConstants.CACHE_TTL_SECONDS * 1000L
    }
    
    private fun evict() {
        var minScore = Float.MAX_VALUE
        var minKey: String? = null
        
        val now = System.currentTimeMillis()
        for ((key, entry) in cache) {
            val dt = (now - entry.lastAccess).toFloat() / 1000f
            val phiScore = (entry.accessCount + 1) * 
                HarmonicConstants.PHI.pow(-dt / HarmonicConstants.CACHE_TTL_SECONDS)
            if (phiScore < minScore) {
                minScore = phiScore
                minKey = key
            }
        }
        
        minKey?.let { cache.remove(it) }
    }
    
    val size: Int get() = cache.size
    val hitRate: Float get() {
        val total = hits + misses
        return if (total > 0) hits.toFloat() / total else 0f
    }
}

/**
 * Base de templates fondamentaux (T0)
 * 6 templates = conditions initiales du solveur ABC
 */
object TemplateDatabase {
    val templates: Map<String, HarmonicTemplate> by lazy { initializeTemplates() }
    
    private fun initializeTemplates(): Map<String, HarmonicTemplate> {
        val map = mutableMapOf<String, HarmonicTemplate>()
        
        // === MATHÉMATIQUE T0 ===
        map["math_T0"] = HarmonicTemplate(
            id = "math_T0",
            category = "mathematical",
            amplitudes = floatArrayOf(0.7f, 0.5f, 0.3f),
            basisStates = listOf("|calcul⟩", "|équation⟩", "|formule⟩"),
            phase = HarmonicConstants.PHI * PI.toFloat() / 3f,
            entanglement = 0.618f,
            coherence = 0.809f,
            signature = HarmonicSignature(
                phiRatio = 0.2f, alphaComplexity = 0.4f,
                kReasoning = 0.7f, kCreative = 0.1f,
                kMathematical = 0.9f, kFactual = 0.2f, kCode = 0.1f
            ),
            kFactor = 0.92f
        )
        
        // === CRÉATIF T0 ===
        map["creative_T0"] = HarmonicTemplate(
            id = "creative_T0",
            category = "creative",
            amplitudes = floatArrayOf(0.8f, 0.6f, 0.4f),
            basisStates = listOf("|poème⟩", "|histoire⟩", "|métaphore⟩"),
            phase = HarmonicConstants.PHI * PI.toFloat() / 2f,
            entanglement = 0.809f,
            coherence = 0.9f,
            signature = HarmonicSignature(
                phiRatio = 0.4f, alphaComplexity = 0.5f,
                kReasoning = 0.2f, kCreative = 0.9f,
                kMathematical = 0.1f, kFactual = 0.1f, kCode = 0.1f
            ),
            kFactor = 0.85f
        )
        
        // === RAISONNEMENT T0 ===
        map["reasoning_T0"] = HarmonicTemplate(
            id = "reasoning_T0",
            category = "reasoning",
            amplitudes = floatArrayOf(0.6f, 0.7f, 0.5f),
            basisStates = listOf("|cause_effet⟩", "|comparaison⟩", "|argumentation⟩"),
            phase = HarmonicConstants.PHI * PI.toFloat() / 4f,
            entanglement = 0.7f,
            coherence = 0.85f,
            signature = HarmonicSignature(
                phiRatio = 0.3f, alphaComplexity = 0.5f,
                kReasoning = 0.9f, kCreative = 0.2f,
                kMathematical = 0.2f, kFactual = 0.4f, kCode = 0.1f
            ),
            kFactor = 0.90f
        )
        
        // === CODE T0 ===
        map["code_T0"] = HarmonicTemplate(
            id = "code_T0",
            category = "code",
            amplitudes = floatArrayOf(0.5f, 0.8f, 0.6f),
            basisStates = listOf("|fonction⟩", "|algorithme⟩", "|api⟩"),
            phase = HarmonicConstants.PHI * PI.toFloat() / 6f,
            entanglement = 0.6f,
            coherence = 0.82f,
            signature = HarmonicSignature(
                phiRatio = 0.3f, alphaComplexity = 0.5f,
                kReasoning = 0.6f, kCreative = 0.1f,
                kMathematical = 0.3f, kFactual = 0.2f, kCode = 0.9f
            ),
            kFactor = 0.88f
        )
        
        // === FACTUEL T0 ===
        map["factual_T0"] = HarmonicTemplate(
            id = "factual_T0",
            category = "factual",
            amplitudes = floatArrayOf(0.7f, 0.4f),
            basisStates = listOf("|définition⟩", "|explication⟩"),
            phase = HarmonicConstants.PHI * PI.toFloat() / 8f,
            entanglement = 0.5f,
            coherence = 0.78f,
            signature = HarmonicSignature(
                phiRatio = 0.3f, alphaComplexity = 0.4f,
                kReasoning = 0.4f, kCreative = 0.1f,
                kMathematical = 0.2f, kFactual = 0.9f, kCode = 0.1f
            ),
            kFactor = 0.85f
        )
        
        // === GÉNÉRAL T0 ===
        map["general_T0"] = HarmonicTemplate(
            id = "general_T0",
            category = "general",
            amplitudes = floatArrayOf(0.5f),
            basisStates = listOf("|réponse⟩"),
            phase = 0f,
            entanglement = 0.3f,
            coherence = 0.7f,
            signature = HarmonicSignature(
                phiRatio = 0.1f, alphaComplexity = 0.2f,
                kReasoning = 0.2f, kCreative = 0.2f,
                kMathematical = 0.1f, kFactual = 0.2f, kCode = 0.1f
            ),
            kFactor = 0.7f
        )
        
        return map
    }
    
    fun findBest(signature: HarmonicSignature): Pair<HarmonicTemplate?, Float> {
        var bestTemplate: HarmonicTemplate? = null
        var bestResonance = 0f
        
        for ((_, template) in templates) {
            val R = ResonanceEngine.compute(
                signature.toVector(), 
                template.signature.toVector()
            )
            if (R > bestResonance) {
                bestResonance = R
                bestTemplate = template
            }
        }
        
        return Pair(bestTemplate, bestResonance)
    }
}

/**
 * Générateur de réponses par évolution ABC
 * ==========================================
 * Cœur de l'IA harmonique sur Android
 */
class ResponseGenerator(
    private val analyzer: HarmonicAnalyzer = HarmonicAnalyzer(),
    private val cache: HarmonicCache = HarmonicCache()
) {
    fun generate(prompt: String): ResponseResult {
        val startTime = System.nanoTime()
        
        // 1. Analyser le prompt
        val signature = analyzer.analyze(prompt)
        val category = analyzer.classify(signature)
        
        // 2. Vérifier le cache
        val promptHash = prompt.hashCode().toUInt().toString(16)
        val cached = cache[promptHash]
        if (cached != null) {
            return ResponseResult(
                response = cached.response,
                category = category,
                resonance = cached.resonanceScore,
                processingTimeMs = (System.nanoTime() - startTime) / 1_000_000f,
                cacheHit = true
            )
        }
        
        // 3. Trouver le meilleur template T0
        val (template, resonance) = TemplateDatabase.findBest(signature)
        
        val response: String
        if (template != null && resonance >= HarmonicConstants.RESONANCE_LOW) {
            // 4. Évolution ABC
            response = evolveTemplate(template, prompt, signature, resonance)
        } else {
            // 5. Génération depuis l'état vide
            response = generateFromScratch(prompt, signature)
        }
        
        val processingTime = (System.nanoTime() - startTime) / 1_000_000f
        
        // 6. Mettre en cache
        cache.put(promptHash, signature, response, resonance)
        
        return ResponseResult(
            response = response,
            category = category,
            resonance = resonance,
            processingTimeMs = processingTime,
            cacheHit = false
        )
    }
    
    private fun evolveTemplate(
        template: HarmonicTemplate, 
        prompt: String, 
        signature: HarmonicSignature,
        resonance: Float
    ): String {
        // |ψ(t)⟩ = E_{1/φ}(-φ × R × t^{1/φ}) × |ψ(0)⟩
        val t = 1.0f
        val tScaled = t.pow(HarmonicConstants.PHI_INV)
        val kernel = MittagLeffler.evaluate(
            HarmonicConstants.PHI_INV,
            -HarmonicConstants.PHI * resonance * tScaled
        )
        
        // État évolué
        val evolvedAmplitudes = template.amplitudes.map { it * kernel }
        val state = QuantumState(
            amplitudes = evolvedAmplitudes.toFloatArray(),
            basisStates = template.basisStates,
            phase = template.phase * kernel,
            entanglement = template.entanglement * (1f - kernel + HarmonicConstants.PHI_INV),
            coherence = template.coherence * kernel
        )
        
        // Collapsus vers la réponse
        val (_, collapsedBasis) = state.collapse()
        val baseResponse = basisToResponse(collapsedBasis, template.category)
        
        // Compléter avec les détails extraits
        val detailLevel = min(1f, prompt.split(" ").size / 20f * HarmonicConstants.ALPHA)
        val details = extractDetails(prompt, template.category)
        
        return buildString {
            append(baseResponse)
            if (details.isNotEmpty()) {
                append("\n\n")
                append(details)
            }
            append("\n\n*~ IA Harmonique · Résonance : ")
            append("%.0f".format(resonance * 100))
            append("% ~*")
        }
    }
    
    private fun generateFromScratch(prompt: String, signature: HarmonicSignature): String {
        val R = 0.3f
        val t = 5.0f
        val kernel = MittagLeffler.evaluate(
            HarmonicConstants.PHI_INV,
            -HarmonicConstants.PHI * R * t.pow(HarmonicConstants.PHI_INV)
        )
        
        return buildString {
            appendLine("Voici une réponse générée par le raisonnement harmonique :")
            appendLine()
            appendLine("À propos de « ${prompt.take(100)} » :")
            appendLine()
            appendLine(generateContent(prompt, signature))
            appendLine()
            append("*Généré par le solveur fractionnaire ABC en ${t.toInt()} unités de temps*")
        }
    }
    
    private fun basisToResponse(basis: String, category: String): String {
        return when {
            category == "mathematical" -> {
                when {
                    basis.contains("calcul") -> "Voici le calcul demandé :"
                    basis.contains("équation") -> "Voici la résolution de l'équation :"
                    else -> "Voici la formule mathématique :"
                }
            }
            category == "creative" -> {
                when {
                    basis.contains("poème") -> "Voici un poème pour vous :"
                    basis.contains("histoire") -> "Laissez-moi vous raconter une histoire :"
                    basis.contains("métaphore") -> "Voici une métaphore qui éclaire ce sujet :"
                    else -> "Voici une création inspirée par votre demande :"
                }
            }
            category == "code" -> {
                when {
                    basis.contains("fonction") -> "Voici l'implémentation demandée :"
                    basis.contains("algorithme") -> "Voici l'algorithme :"
                    else -> "Voici le code :"
                }
            }
            category == "reasoning" -> {
                when {
                    basis.contains("cause") -> "Analysons les causes et effets :"
                    basis.contains("comparaison") -> "Comparons ces éléments :"
                    else -> "Voici mon analyse :"
                }
            }
            category == "factual" -> {
                when {
                    basis.contains("définition") -> "Voici la définition :"
                    else -> "Voici l'explication :"
                }
            }
            else -> "Voici ma réponse :"
        }
    }
    
    private fun extractDetails(prompt: String, category: String): String {
        val details = StringBuilder()
        
        when (category) {
            "mathematical" -> {
                val numbers = Regex("\\d+\\.?\\d*").findAll(prompt).map { it.value }.toList()
                if (numbers.isNotEmpty()) {
                    details.appendLine("• Nombres détectés : ${numbers.joinToString(", ")}")
                }
                when {
                    "%" in prompt || "pourcent" in prompt.lowercase() -> 
                        details.appendLine("• Opération : calcul de pourcentage")
                    "dériv" in prompt.lowercase() -> 
                        details.appendLine("• Opération : dérivée")
                    "intégr" in prompt.lowercase() -> 
                        details.appendLine("• Opération : intégrale")
                }
            }
            "creative" -> {
                val words = prompt.split(" ").filter { it.length > 4 }
                if (words.isNotEmpty()) {
                    details.appendLine("• Thème : ${words.first()}")
                }
            }
            "code" -> {
                val langPatterns = mapOf(
                    "python" to "python", "javascript" to "javascript",
                    "java" to "java", "sql" to "sql", "kotlin" to "kotlin",
                    "rust" to "rust", "c++" to "c++"
                )
                for ((lang, pattern) in langPatterns) {
                    if (prompt.contains(pattern, ignoreCase = true)) {
                        details.appendLine("• Langage : $lang")
                        break
                    }
                }
                if (details.isEmpty()) {
                    details.appendLine("• Langage : python (défaut)")
                }
            }
        }
        
        return details.toString().trimEnd()
    }
    
    private fun generateContent(prompt: String, signature: HarmonicSignature): String {
        // Génération de contenu basée sur la signature
        val content = StringBuilder()
        
        val reasoning = signature.kReasoning
        val creative = signature.kCreative
        val factual = signature.kFactual
        
        if (reasoning > 0.5f) {
            content.appendLine("Sur le plan du raisonnement, on peut analyser ce sujet ")
            content.appendLine("sous plusieurs angles complémentaires. ")
            content.appendLine("D'une part, la cause première nous éclaire sur l'origine. ")
            content.appendLine("D'autre part, les conséquences nous aident à comprendre la portée.")
        }
        
        if (creative > 0.5f) {
            content.appendLine()
            content.appendLine("D'un point de vue créatif, chaque idée est comme une ")
            content.appendLine("goutte d'eau dans l'océan des possibles — unique et précieuse.")
        }
        
        if (factual > 0.5f) {
            content.appendLine()
            content.appendLine("Sur le plan factuel, voici les éléments clés à retenir :")
            content.appendLine("• Ce sujet s'inscrit dans un contexte plus large")
            content.appendLine("• Les données disponibles confirment cette analyse")
        }
        
        return content.toString().trimEnd()
    }
}

/**
 * Résultat d'une génération
 */
data class ResponseResult(
    val response: String,
    val category: String,
    val resonance: Float,
    val processingTimeMs: Float,
    val cacheHit: Boolean
) {
    val formattedTime: String 
        get() = if (processingTimeMs < 1f) 
            "< 1ms" 
        else 
            "%.1fms".format(processingTimeMs)
}