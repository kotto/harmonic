/**
 * Analyseur d'URL Harmonique
 * ============================
 * Permet à l'IA Harmonique de lire et analyser le contenu
 * d'une page web à partir de son URL.
 * 
 * Fonctionnalités :
 * - Fetch du contenu via proxy CORS
 * - Extraction du texte (HTML → texte brut)
 * - Analyse harmonique 7D du contenu
 * - Résumé automatique
 * - Détection de la langue, du sujet, des mots-clés
 */

class URLHarmonicAnalyzer {
    constructor() {
        this.cache = new Map();
        this.proxyUrl = 'https://api.allorigins.win/raw?url=';
        this.timeout = 10000;
    }

    /**
     * Analyse une URL et retourne sa signature harmonique + métadonnées
     */
    async analyze(url) {
        // Nettoyer l'URL
        url = this._normalizeUrl(url);
        if (!url) {
            return this._error('URL invalide');
        }

        // Vérifier le cache
        const cacheKey = url;
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 300000) { // 5 min
                return cached.data;
            }
        }

        try {
            // 1. Fetch le contenu
            const html = await this._fetchUrl(url);
            if (!html || html.length < 50) {
                return this._error('Contenu vide ou inaccessible', url);
            }

            // 2. Extraire le texte et les métadonnées
            const extracted = this._extractContent(html, url);
            
            // 3. Analyser harmoniquement
            const analyzer = new HarmonicEngine.HarmonicAnalyzer();
            const analysis = analyzer.analyze(extracted.text);
            const signature = analysis.toVector();

            // 4. Métriques enrichies
            const words = extracted.text.split(/\s+/).filter(w => w.length > 0);
            const sentences = extracted.text.split(/[.!?]+/).filter(s => s.trim().length > 0);
            const avgWordLength = words.reduce((s, w) => s + w.length, 0) / Math.max(1, words.length);
            const avgSentenceLength = words.length / Math.max(1, sentences.length);
            
            // 5. Mots-clés (TF simple)
            const keywords = this._extractKeywords(extracted.text, 10);

            // 6. Score de qualité du contenu
            const qualityScore = Math.min(1, 
                (Math.min(1, words.length / 500) * 0.3) +  // Longueur
                (Math.min(1, avgSentenceLength / 25) * 0.2) +  // Complexité phrases
                (Math.min(1, avgWordLength / 6) * 0.2) +  // Richesse vocabulaire
                (signature[0] * 0.3)  // Diversité harmonique
            );

            const result = {
                url,
                title: extracted.title,
                description: extracted.description,
                text: extracted.text.substring(0, 3000),
                wordCount: words.length,
                sentenceCount: sentences.length,
                avgWordLength: avgWordLength.toFixed(1),
                avgSentenceLength: avgSentenceLength.toFixed(1),
                signature,
                keywords: keywords.slice(0, 10),
                qualityScore: Math.round(qualityScore * 100),
                dominantCategory: this._categorize(signature),
                language: extracted.lang || 'fr',
                timestamp: new Date().toISOString(),
                success: true
            };

            // Mettre en cache
            this.cache.set(cacheKey, { data: result, timestamp: Date.now() });

            return result;

        } catch (error) {
            return this._error(error.message, url);
        }
    }

    /**
     * Analyse une URL et retourne un résumé pour le chat
     */
    async analyzeForChat(url) {
        const result = await this.analyze(url);
        
        if (!result.success) {
            return {
                response: `❌ Impossible d'analyser l'URL : ${result.error}`,
                resonance: 0,
                category: 'URL Error'
            };
        }

        const sig = result.signature;
        const resonance = Math.sqrt(sig.reduce((s, v) => s + v*v, 0)) * PHI / 3;
        
        let response = `🔗 **Analyse d'URL :** ${result.title || result.url}\n\n`;
        response += `**Contenu :** ${result.wordCount} mots, ${result.sentenceCount} phrases\n`;
        response += `**Catégorie :** ${result.dominantCategory}\n`;
        response += `**Qualité :** ${result.qualityScore}%\n\n`;
        
        if (result.description) {
            response += `**Description :** ${result.description}\n\n`;
        }
        
        if (result.keywords.length > 0) {
            response += `**Mots-clés :** ${result.keywords.join(', ')}\n\n`;
        }
        
        // Extrait du contenu
        const preview = result.text.substring(0, 500);
        response += `**Extrait :**\n${preview}...\n\n`;
        
        // Signature harmonique
        response += `**Signature 7D :** [${sig.map(v => v.toFixed(3)).join(', ')}]\n`;
        response += `**Résonance :** ${Math.round(resonance * 100)}%`;

        return {
            response,
            resonance,
            category: 'URL Analysis',
            url: result.url,
            signature: sig
        };
    }

    _normalizeUrl(url) {
        url = url.trim();
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }
        try {
            new URL(url);
            return url;
        } catch {
            return null;
        }
    }

    async _fetchUrl(url) {
        const proxyUrl = this.proxyUrl + encodeURIComponent(url);
        const response = await fetch(proxyUrl, {
            signal: AbortSignal.timeout(this.timeout)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.text();
    }

    _extractContent(html, url) {
        // Titre
        const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
        const title = titleMatch ? titleMatch[1].trim() : '';

        // Description meta
        const descMatch = html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)["']/i);
        const description = descMatch ? descMatch[1].trim() : '';

        // Langue
        const langMatch = html.match(/<html[^>]+lang=["']([^"']+)["']/i);
        const lang = langMatch ? langMatch[1].split('-')[0] : '';

        // Texte brut
        const text = html
            .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, ' ')
            .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ' ')
            .replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, ' ')
            .replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, ' ')
            .replace(/<header[^>]*>[\s\S]*?<\/header>/gi, ' ')
            .replace(/<[^>]+>/g, ' ')
            .replace(/&[^;]+;/g, ' ')
            .replace(/\s+/g, ' ')
            .replace(/[^\w\sàâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ.,!?;:()"'-]/g, ' ')
            .trim();

        return { title, description, text, lang };
    }

    _extractKeywords(text, n = 10) {
        const stopWords = new Set([
            'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'sont',
            'dans', 'pour', 'sur', 'avec', 'par', 'pas', 'plus', 'que', 'qui', 'quoi',
            'nous', 'vous', 'ils', 'elles', 'ce', 'cet', 'cette', 'ces', 'son', 'sa',
            'ses', 'leur', 'leurs', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'notre',
            'nos', 'votre', 'vos', 'au', 'aux', 'en', 'y', 'a', 'ont', 'ont', 'fait',
            'faire', 'être', 'avoir', 'the', 'a', 'an', 'and', 'or', 'but', 'in',
            'on', 'at', 'to', 'for', 'of', 'by', 'with', 'from', 'is', 'are', 'was',
            'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that', 'these',
            'those', 'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who',
            'whom', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'because', 'as', 'until',
            'while', 'about', 'between', 'through', 'during', 'before', 'after', 'above',
            'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how'
        ]);

        const words = text.toLowerCase()
            .split(/\s+/)
            .filter(w => w.length > 3 && !stopWords.has(w))
            .map(w => w.replace(/[.,!?;:()"']/g, ''));

        const freq = {};
        for (const word of words) {
            freq[word] = (freq[word] || 0) + 1;
        }

        return Object.entries(freq)
            .sort((a, b) => b[1] - a[1])
            .slice(0, n)
            .map(([word, count]) => `${word} (${count})`);
    }

    _categorize(signature) {
        const [phi, alpha, reasoning, creative, math, factual, code] = signature;
        const categories = [
            { name: 'Article Scientifique', score: math * 0.4 + factual * 0.3 + reasoning * 0.3 },
            { name: 'Article Créatif', score: creative * 0.5 + phi * 0.3 + reasoning * 0.2 },
            { name: 'Actualité', score: factual * 0.5 + phi * 0.2 + reasoning * 0.3 },
            { name: 'Analyse Technique', score: code * 0.4 + math * 0.3 + factual * 0.3 },
            { name: 'Opinion/Éditorial', score: creative * 0.4 + reasoning * 0.4 + phi * 0.2 }
        ];
        return categories.sort((a, b) => b.score - a.score)[0].name;
    }

    _error(message, url = '') {
        return {
            url,
            success: false,
            error: message,
            signature: [0, 0, 0, 0, 0, 0, 0],
            timestamp: new Date().toISOString()
        };
    }

    clearCache() {
        this.cache.clear();
    }
}

// =========================================================================
// DÉTECTION D'URL DANS LE TEXTE
// =========================================================================

class URLDetector {
    /**
     * Détecte les URLs dans un texte
     */
    static findUrls(text) {
        const urlRegex = /(https?:\/\/[^\s]+)|(?:^|\s)([a-zA-Z0-9-]+\.(?:com|fr|org|net|io|gov|edu|info|dev|app|ai)\/[^\s]*)/g;
        const urls = [];
        let match;
        
        while ((match = urlRegex.exec(text)) !== null) {
            let url = match[1] || match[2];
            if (!url.startsWith('http')) {
                url = 'https://' + url;
            }
            // Nettoyer
            url = url.replace(/[.,!?;:)]$/, '');
            try {
                new URL(url);
                urls.push(url);
            } catch {}
        }
        
        return [...new Set(urls)]; // Déduplication
    }

    /**
     * Vérifie si un texte contient des URLs
     */
    static hasUrls(text) {
        return this.findUrls(text).length > 0;
    }
}

// =========================================================================
// EXPORT
// =========================================================================

window.HarmonicURL = {
    URLHarmonicAnalyzer,
    URLDetector
};