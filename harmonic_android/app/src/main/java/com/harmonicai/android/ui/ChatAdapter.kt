package com.harmonicai.android.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.harmonicai.android.R

/**
 * Adaptateur pour la liste des messages
 */
class ChatAdapter(
    private val messages: List<ChatMessage>
) : RecyclerView.Adapter<ChatAdapter.MessageViewHolder>() {
    
    override fun getItemCount(): Int = messages.size
    
    override fun getItemViewType(position: Int): Int {
        return if (messages[position].isUser) VIEW_TYPE_USER else VIEW_TYPE_AI
    }
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MessageViewHolder {
        val layoutId = if (viewType == VIEW_TYPE_USER) {
            R.layout.item_message_user
        } else {
            R.layout.item_message_ai
        }
        val view = LayoutInflater.from(parent.context).inflate(layoutId, parent, false)
        return MessageViewHolder(view)
    }
    
    override fun onBindViewHolder(holder: MessageViewHolder, position: Int) {
        val message = messages[position]
        holder.messageText.text = message.text
        
        if (!message.isUser) {
            // Métadonnées pour les messages AI
            val metaInfo = buildString {
                append("Résonance : ${"%.0f".format(message.resonance * 100)}%")
                append(" · ")
                append(message.processingTimeMs.let {
                    if (it < 1f) "< 1ms" else "%.1fms".format(it)
                })
                if (message.cacheHit) {
                    append(" · Cache")
                }
                if (message.category.isNotEmpty()) {
                    append(" · ${message.category}")
                }
            }
            holder.metaText?.text = metaInfo
            holder.metaText?.visibility = View.VISIBLE
        }
    }
    
    class MessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val messageText: TextView = itemView.findViewById(R.id.messageText)
        val metaText: TextView? = itemView.findViewById(R.id.metaText)
    }
    
    companion object {
        const val VIEW_TYPE_USER = 0
        const val VIEW_TYPE_AI = 1
    }
}