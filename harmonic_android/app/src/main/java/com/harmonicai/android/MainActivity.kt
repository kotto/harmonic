package com.harmonicai.android

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import com.harmonicai.android.databinding.ActivityMainBinding
import com.harmonicai.android.ui.ChatAdapter
import com.harmonicai.android.ui.MainViewModel
import com.harmonicai.android.ui.StatsData

/**
 * MainActivity de l'IA Harmonique
 * Interface de chat avec le moteur ABC embarqué
 * 
 * Aucune connexion Internet nécessaire !
 * L'intégralité du raisonnement harmonique est dans le moteur Android.
 */
class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    private val viewModel: MainViewModel by viewModels()
    private lateinit var chatAdapter: ChatAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // ViewBinding
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        // Support ActionBar
        setSupportActionBar(binding.toolbar)
        supportActionBar?.title = getString(R.string.app_name)
        
        setupRecyclerView()
        setupSendButton()
        setupObservers()
        setupStatsButton()
        setupClearButton()
    }
    
    private fun setupRecyclerView() {
        chatAdapter = ChatAdapter(emptyList())
        binding.recyclerView.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = chatAdapter
            setHasFixedSize(true)
        }
    }
    
    private fun setupSendButton() {
        binding.sendButton.setOnClickListener {
            val text = binding.inputEditText.text.toString().trim()
            if (text.isNotEmpty()) {
                viewModel.sendMessage(text)
                binding.inputEditText.text?.clear()
            }
        }
        
        // Envoyer avec la touche Entrée du clavier
        binding.inputEditText.setOnEditorActionListener { _, _, _ ->
            val text = binding.inputEditText.text.toString().trim()
            if (text.isNotEmpty()) {
                viewModel.sendMessage(text)
                binding.inputEditText.text?.clear()
            }
            true
        }
    }
    
    private fun setupObservers() {
        // Messages
        viewModel.messages.observe(this, Observer { messages ->
            chatAdapter = ChatAdapter(messages)
            binding.recyclerView.adapter = chatAdapter
            chatAdapter.notifyDataSetChanged()
            
            // Scroll to bottom
            if (messages.isNotEmpty()) {
                binding.recyclerView.smoothScrollToPosition(messages.size - 1)
            }
        })
        
        // Chargement
        viewModel.isLoading.observe(this, Observer { loading ->
            binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
            binding.sendButton.isEnabled = !loading
            binding.inputEditText.isEnabled = !loading
        })
        
        // Erreur
        viewModel.error.observe(this, Observer { error ->
            error?.let {
                Toast.makeText(this, it, Toast.LENGTH_LONG).show()
                viewModel.clearError()
            }
        })
        
        // Stats
        viewModel.stats.observe(this, Observer { stats ->
            updateStatsUI(stats)
        })
    }
    
    private fun setupStatsButton() {
        binding.statsButton.setOnClickListener {
            val stats = viewModel.stats.value
            if (stats != null) {
                binding.statsCard.visibility = 
                    if (binding.statsCard.visibility == View.VISIBLE) View.GONE 
                    else View.VISIBLE
            }
        }
    }
    
    private fun setupClearButton() {
        binding.clearButton.setOnClickListener {
            viewModel.clearMessages()
            binding.statsCard.visibility = View.GONE
        }
    }
    
    private fun updateStatsUI(stats: StatsData) {
        binding.statsRequests.text = "Requêtes : ${stats.totalRequests}"
        binding.statsResonance.text = "Résonance : ${"%.1f".format(stats.avgResonance * 100)}%"
        binding.statsLatency.text = "Latence moyenne : ${"%.2f".format(stats.avgLatencyMs)}ms"
        binding.statsCache.text = "Cache : ${"%.0f".format(stats.cacheHitRate * 100)}% hits"
        
        // Visibilité du panneau stats après clic sur le bouton
    }
}