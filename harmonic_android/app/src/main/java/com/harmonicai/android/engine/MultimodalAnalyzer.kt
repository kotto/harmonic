package com.harmonicai.android.engine

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.media.MediaMetadataRetriever
import android.net.Uri
import kotlin.math.*

/**
 * Analyseur multimodal pour Android
 * ====================================
 * Extrait la signature harmonique 7D à partir de fichiers :
 * - Images : Bitmap → histogrammes + entropie + contraste
 * - Audio : via MediaMetadataRetriever → spectre → signature
 * - Documents : extraction texte → analyseur existant
 * 
 * Utilise uniquement les API Android natives.
 * Aucune bibliothèque externe.
 */

data class FileAnalysisResult(
    val signature: FloatArray,      // Signature 7D
    val metadata: Map<String, Any>,  // Métadonnées
    val summary: String             // Résumé textuel
)

class ImageAnalyzer(private val context: Context) {
    
    fun analyze(uri: Uri): FileAnalysisResult {
        val bitmap = MediaStoreHelper.loadBitmap(context, uri, 256)
            ?: return defaultResult("image")
        
        val pixels = IntArray(bitmap.width * bitmap.height)
        bitmap.getPixels(pixels, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)
        
        // 1. φ_ratio : entropie
        val histogram = computeHistogram(pixels)
        val entropy = computeEntropy(histogram)
        val phiRatio = min(1f, entropy / 8f * HarmonicConstants.PHI / 2f)
        
        // 2. α_complexity : contraste
        val intensities = pixels.map { 
            0.299f * Color.red(it) + 0.587f * Color.green(it) + 0.114f * Color.blue(it) 
        }
        val mean = intensities.average().toFloat()
        val variance = intensities.map { (it - mean).pow(2) }.average().toFloat()
        val stdDev = sqrt(variance)
        val alphaComplexity = min(1f, stdDev / 128f * HarmonicConstants.ALPHA)
        
        // 3. k_creative : harmonie des couleurs
        val rMean = pixels.map { Color.red(it) }.average().toFloat()
        val gMean = pixels.map { Color.green(it) }.average().toFloat()
        val bMean = pixels.map { Color.blue(it) }.average().toFloat()
        val allMean = (rMean + gMean + bMean) / 3f
        val channelVar = ((rMean - allMean).pow(2) + (gMean - allMean).pow(2) + (bMean - allMean).pow(2)) / 3f
        val colorHarmony = max(0f, 1f - sqrt(channelVar) / 128f)
        val kCreative = min(1f, colorHarmony * HarmonicConstants.PHI / 2f)
        
        // 4. k_mathematical : ratio d'aspect / φ
        val aspectRatio = bitmap.width.toFloat() / bitmap.height.toFloat()
        val phiDiff = abs(aspectRatio / HarmonicConstants.PHI - 1f)
        val kMathematical = min(1f, max(0f, 1f - phiDiff * 3f))
        
        // 5. k_factual : détection de bords
        val edgeScore = computeEdgeScore(pixels, bitmap.width, bitmap.height)
        val kFactual = min(1f, edgeScore * 2f)
        
        // 6. k_reasoning
        val kReasoning = 0.1f + phiRatio * 0.3f
        
        // 7. k_code
        val kCode = 0f
        
        val signature = floatArrayOf(
            phiRatio, alphaComplexity, kReasoning, kCreative,
            kMathematical, kFactual, kCode
        )
        
        val metadata = mapOf<String, Any>(
            "width" to bitmap.width,
            "height" to bitmap.height,
            "aspectRatio" to "%.2f".format(aspectRatio),
            "entropy" to "%.2f".format(entropy),
            "contrast" to "%.1f".format(stdDev),
            "size" to "0",
            "format" to "image"
        )
        
        val summary = "Image ${bitmap.width}×${bitmap.height} — entropie ${"%.2f".format(entropy)}"
        
        return FileAnalysisResult(signature, metadata, summary)
    }
    
    private fun computeHistogram(pixels: IntArray): IntArray {
        val hist = IntArray(256)
        for (pixel in pixels) {
            val gray = (0.299f * Color.red(pixel) + 0.587f * Color.green(pixel) + 
                        0.114f * Color.blue(pixel)).toInt().coerceIn(0, 255)
            hist[gray]++
        }
        return hist
    }
    
    private fun computeEntropy(histogram: IntArray): Float {
        val total = histogram.sum().toFloat()
        if (total == 0f) return 0f
        var entropy = 0f
        for (count in histogram) {
            if (count > 0) {
                val p = count / total
                entropy -= p * log2(p)
            }
        }
        return entropy
    }
    
    private fun computeEdgeScore(pixels: IntArray, w: Int, h: Int): Float {
        var edgeCount = 0
        val step = 4
        var totalSamples = 0
        
        for (y in step until h - step step step) {
            for (x in step until w - step step step) {
                totalSamples++
                val idx = y * w + x
                val idxLeft = y * w + (x - step)
                val idxRight = y * w + (x + step)
                val idxUp = (y - step) * w + x
                val idxDown = (y + step) * w + x
                
                val gx = abs(Color.red(pixels[idxRight]) - Color.red(pixels[idxLeft])).toFloat()
                val gy = abs(Color.red(pixels[idxDown]) - Color.red(pixels[idxUp])).toFloat()
                val grad = sqrt(gx * gx + gy * gy)
                
                if (grad > 40f) edgeCount++
            }
        }
        
        return if (totalSamples > 0) edgeCount.toFloat() / totalSamples else 0f
    }
    
    private fun defaultResult(type: String) = FileAnalysisResult(
        signature = floatArrayOf(0f, 0f, 0f, 0f, 0f, 0f, 0f),
        metadata = mapOf("format" to type, "error" to "Impossible de charger le fichier"),
        summary = "Erreur d'analyse"
    )
}

/**
 * Analyseur audio Android
 * Utilise MediaMetadataRetriever pour extraire les métadonnées
 * L'analyse spectrale poussée nécessite une bibliothèque native
 */
class AudioAnalyzer(private val context: Context) {
    
    fun analyze(uri: Uri): FileAnalysisResult {
        val mmr = MediaMetadataRetriever()
        try {
            mmr.setDataSource(context, uri)
            
            val durationStr = mmr.extractMetadata(
                MediaMetadataRetriever.METADATA_KEY_DURATION
            ) ?: "0"
            val duration = durationStr.toLongOrNull()?.let { it / 1000 } ?: 0
            
            // Signature basée sur les métadonnées disponibles
            val phiRatio = min(1f, duration.toFloat() / 600f * HarmonicConstants.PHI / 3f)
            val alphaComplexity = 0.3f
            val kCreative = 0.5f
            val kMathematical = 0.2f
            val kFactual = 0.1f
            val kReasoning = 0.1f + phiRatio * 0.2f
            val kCode = 0f
            
            val signature = floatArrayOf(
                phiRatio, alphaComplexity, kReasoning, kCreative,
                kMathematical, kFactual, kCode
            )
            
            val metadata = mapOf<String, Any>(
                "duration" to "${duration}s",
                "format" to "audio"
            )
            
            val summary = "Audio — durée ${duration}s"
            
            return FileAnalysisResult(signature, metadata, summary)
            
        } catch (e: Exception) {
            return FileAnalysisResult(
                signature = floatArrayOf(0f, 0f, 0f, 0f, 0f, 0f, 0f),
                metadata = mapOf("format" to "audio", "error" to e.message ?: "?"),
                summary = "Erreur d'analyse audio"
            )
        } finally {
            mmr.release()
        }
    }
}

/**
 * Analyseur de documents Android
 */
class DocumentAnalyzer(private val context: Context) {
    
    fun analyze(uri: Uri): FileAnalysisResult {
        try {
            val inputStream = context.contentResolver.openInputStream(uri)
            val text = inputStream?.bufferedReader()?.use { it.readText() } ?: ""
            
            if (text.isEmpty()) {
                return FileAnalysisResult(
                    signature = floatArrayOf(0f, 0f, 0f, 0f, 0f, 0f, 0f),
                    metadata = mapOf("format" to "document", "wordCount" to 0),
                    summary = "Document vide"
                )
            }
            
            // Utiliser l'analyseur existant
            val analyzer = HarmonicAnalyzer()
            val sig = analyzer.analyze(text)
            
            val signature = sig.toVector()
            val metadata = mapOf<String, Any>(
                "wordCount" to text.split(Regex("\\s+")).size,
                "charCount" to text.length,
                "format" to "document"
            )
            
            val summary = "Document — ${metadata["wordCount"]} mots"
            
            return FileAnalysisResult(signature, metadata, summary)
            
        } catch (e: Exception) {
            return FileAnalysisResult(
                signature = floatArrayOf(0f, 0f, 0f, 0f, 0f, 0f, 0f),
                metadata = mapOf("format" to "document", "error" to e.message ?: "?"),
                summary = "Erreur de lecture"
            )
        }
    }
}

/**
 * Utilitaire pour charger un Bitmap Android
 */
object MediaStoreHelper {
    fun loadBitmap(context: Context, uri: Uri, maxSize: Int = 1024): Bitmap? {
        return try {
            val inputStream = context.contentResolver.openInputStream(uri)
            val options = BitmapFactory.Options().apply {
                inJustDecodeBounds = true
            }
            BitmapFactory.decodeStream(inputStream, null, options)
            inputStream?.close()
            
            // Calculer le facteur d'échantillonnage
            val scaleFactor = maxOf(
                options.outWidth / maxSize,
                options.outHeight / maxSize,
                1
            )
            
            val sampleOptions = BitmapFactory.Options().apply {
                inSampleSize = scaleFactor
            }
            
            val result = context.contentResolver.openInputStream(uri)?.use {
                BitmapFactory.decodeStream(it, null, sampleOptions)
            }
            
            result
            
        } catch (e: Exception) {
            null
        }
    }
}

/**
 * Compatibilité couleur Android (API < 26)
 */
private object Color {
    fun red(pixel: Int) = (pixel shr 16) and 0xFF
    fun green(pixel: Int) = (pixel shr 8) and 0xFF
    fun blue(pixel: Int) = pixel and 0xFF
}

/**
 * Extension pour fusionner plusieurs signatures
 */
object SignatureFusion {
    fun fuse(signatures: List<FloatArray>): FloatArray {
        if (signatures.isEmpty()) return FloatArray(7)
        if (signatures.size == 1) return signatures[0]
        
        val n = signatures.size
        val weights = signatures.map { sig ->
            0.3f + 0.7f * sqrt(sig.sumOf { it * it })
        }
        val totalW = weights.sum()
        val normalizedW = weights.map { it / totalW }
        
        val merged = FloatArray(7)
        for (i in 0 until n) {
            for (k in 0 until 7) {
                merged[k] += signatures[i][k] * normalizedW[i]
            }
        }
        
        // Termes d'intrication
        for (i in 0 until n) {
            for (j in (i + 1) until n) {
                val R_ij = ResonanceEngine.compute(signatures[i], signatures[j])
                val pairCount = n * (n - 1) / 2
                for (k in 0 until 7) {
                    merged[k] += R_ij * HarmonicConstants.PHI_INV / pairCount
                }
            }
        }
        
        return merged.map { min(1f, max(0f, it)) }.toFloatArray()
    }
}

/**
 * Classe unifiée AttachedFile pour Android
 */
data class AttachedFile(
    val uri: Uri,
    val name: String,
    val size: Long,
    val mimeType: String,
    val type: String,  // "image", "audio", "video", "document"
    var analysisResult: FileAnalysisResult? = null
) {
    val isAnalyzed: Boolean get() = analysisResult != null
    
    fun analyze(context: Context) {
        when (type) {
            "image" -> {
                val analyzer = ImageAnalyzer(context)
                analysisResult = analyzer.analyze(uri)
            }
            "audio" -> {
                val analyzer = AudioAnalyzer(context)
                analysisResult = analyzer.analyze(uri)
            }
            "document" -> {
                val analyzer = DocumentAnalyzer(context)
                analysisResult = analyzer.analyze(uri)
            }
            else -> {
                analysisResult = FileAnalysisResult(
                    signature = floatArrayOf(0f, 0f, 0f, 0f, 0f, 0f, 0f),
                    metadata = mapOf("format" to type),
                    summary = "Type non supporté"
                )
            }
        }
    }
    
    companion object {
        fun detectType(name: String): String {
            val ext = name.substringAfterLast('.', "").lowercase()
            return when (ext) {
                in listOf("jpg", "jpeg", "png", "gif", "bmp", "webp") -> "image"
                in listOf("mp3", "wav", "ogg", "flac", "aac", "m4a") -> "audio"
                in listOf("mp4", "avi", "mov", "mkv", "webm") -> "video"
                in listOf("txt", "md", "json", "csv", "pdf", "docx") -> "document"
                else -> "unknown"
            }
        }
    }
}