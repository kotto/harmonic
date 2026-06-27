package com.harmonicai.android.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.harmonicai.android.engine.ResponseGenerator
import com.harmonicai.android.engine.ResponseResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * ViewModel principal de l'IA Harmonique
 * Gère l'état de l'interface et la communication avec le moteur ABC
 */
class MainViewModel : ViewModel() {
    
    private val generator = ResponseGenerator()
    
    // État des messages
    private val _messages = MutableLiveData<MutableList<ChatMessage>>(mutableListOf())
    val messages: LiveData<MutableList<ChatMessage>> = _messages
    
    // État de chargement
    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> = _isLoading
    
    // État d'erreur
    private val _error = MutableLiveData<String?>(null)
    val error: LiveData<String?> = _error
    
    // Statistiques
    private val _stats = MutableLiveData(StatsData())
    val stats: LiveData<StatsData> = _stats
    
    // Message en cours
    private val _currentResponse = MutableLiveData("")
    val currentResponse: LiveData<String> = _currentResponse
    
    fun sendMessage(text: String) {
        if (text.isBlank() || _isLoading.value == true) return
        
        // Ajouter le message utilisateur
        val userMsg = ChatMessage(
            text = text,
            isUser = true,
            timestamp = System.currentTimeMillis()
        )
        val currentList = _messages.value?.toMutableList() ?: mutableListOf()
        currentList.add(userMsg)
        _messages.value = currentList
        
        // Lancer la génération
        _isLoading.value = true
        _error.value = null
        _currentResponse.value = ""
        
        viewModelScope.launch {
            try {
                val result = withContext(Dispatchers.Default) {
                    generator.generate(text)
                }
                
                // Ajouter la réponse
                val aiMsg = ChatMessage(
                    text = result.response,
                    isUser = false,
                    timestamp = System.currentTimeMillis(),
                    category = result.category,
                    resonance = result.resonance,
                    processingTimeMs = result.processingTimeMs,
                    cacheHit = result.cacheHit
                )
                
                val updatedList = _messages.value?.toMutableList() ?: mutableListOf()
                updatedList.add(aiMsg)
                _messages.value = updatedList
                _currentResponse.value = result.response
                
                // Mettre à jour les stats
                updateStats(result)
                
            } catch (e: Exception) {
                _error.value = "Erreur : ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    private fun updateStats(result: ResponseResult) {
        val currentStats = _stats.value ?: StatsData()
        _stats.value = currentStats.copy(
            totalRequests = currentStats.totalRequests + 1,
            cacheHits = currentStats.cacheHits + if (result.cacheHit) 1 else 0,
            avgResonance = (currentStats.avgResonance * currentStats.totalRequests + result.resonance) / 
                          (currentStats.totalRequests + 1),
            avgLatencyMs = (currentStats.avgLatencyMs * currentStats.totalRequests + result.processingTimeMs) /
                          (currentStats.totalRequests + 1)
        )
    }
    
    fun clearMessages() {
        _messages.value = mutableListOf()
        _error.value = null
    }
    
    fun clearError() {
        _error.value = null
    }
}

/**
 * Message de chat
 */
data class ChatMessage(
    val text: String,
    val isUser: Boolean,
    val timestamp: Long,
    val category: String = "",
    val resonance: Float = 0f,
    val processingTimeMs: Float = 0f,
    val cacheHit: Boolean = false
)

/**
 * Statistiques de l'IA
 */
data class StatsData(
    val totalRequests: Int = 0,
    val cacheHits: Int = 0,
    val avgResonance: Float = 0f,
    val avgLatencyMs: Float = 0f
) {
    val cacheHitRate: Float
        get() = if (totalRequests > 0) cacheHits.toFloat() / totalRequests else 0f
}