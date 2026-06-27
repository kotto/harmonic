/**
 * Moteur de Recherche Web Harmonique
 * =====================================
 * Recherche sur Internet, analyse harmonique des résultats,
 * synthèse multi-sources avec classement par résonance.
 * 
 * Architecture :
 * 1. API DuckDuckGo (gratuite, sans clé) → résultats bruts
 * 2. Fetch CORS proxy → contenu des pages
 * 3. Analyse harmonique 7D de chaque page
 * 4. Fusion des signatures → résonance croisée
 * 5. Synthèse textuelle classée par résonance
 * 
 * Limitations CORS : utilise DuckDuckGo API (pas de clé requise)
 * Pour le fetch de pages, on utilise un proxy CORS public.
 */

// =========================================================================
// CONSTANTES
// =========================================================================

const SEARCH_CONFIG = {
    // API DuckDuckGo (pas de clé requise)
    duckduckgo: {
        baseUrl: 'https://api.duckduckgo.com/',
        params: { format: 'json', no_html: 1, skip_disambig: 1 }
    },
    // Proxy CORS pour fetch les pages (limité mais fonctionnel)
    corsProxy: 'https://api.allorigins.win/raw?url=',
    // Fallback : extraction des extraits DuckDuckGo sans fetch
    maxResults: 8,
    maxCharsPerPage: 5000,
    timeout: 8000
};

// =========================================================================
// MOTEUR DE RECHERCHE
// =========================================================================

class WebSearchEngine {
    constructor() {
        this.cache = new Map();
        this.lastSearchTime = 0;
        this.minInterval = 1000; // 1s entre requêtes
    }

    /**
     * Recherche sur le web et retourne des résultats analysés.
     * @param {string} query - La requête de recherche
     * @param {number} maxResults - Nombre max de résultats
     * @returns {Promise<SearchResult>}
     */
    async search(query, maxResults = SEARCH_CONFIG.maxResults) {
        const cacheKey = query.toLowerCase().trim();
        
        // Vérifier le cache
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 60000) { // 1 min de cache
                return cached.data;
            }
        }

        // Rate limiting
        const now = Date.now();
        if (now - this.lastSearchTime < this.minInterval) {
            await new Promise(r => setTimeout(r, this.minInterval - (now - this.lastSearchTime)));
        }
        this.lastSearchTime = Date.now();

        try {
            // Étape 1 : Recherche DuckDuckGo
            const rawResults = await this._searchDuckDuckGo(query, maxResults);
            
            // Étape 2 : Pour chaque résultat, essayer de fetch le contenu
            const analyzedResults = [];
            for (const result of rawResults) {
                const analyzed = await this._analyzeResult(result);
                analyzedResults.push(analyzed);
            }

            // Étape 3 : Classement par résonance avec la requête
            const querySig = new HarmonicEngine.HarmonicAnalyzer().analyze(query);
            const ranked = this._rankByResonance(analyzedResults, querySig.toVector());

            // Étape 4 : Synthèse harmonique
            const synthesis = this._synthesize(ranked, query);

            const searchResult = {
                query,
                timestamp: new Date().toISOString(),
                totalResults: ranked.length,
                results: ranked,
                synthesis,
                querySignature: querySig.toVector(),
                metadata: {
                    source: 'DuckDuckGo',
                    cacheHit: false
                }
            };

            // Mettre en cache
            this.cache.set(cacheKey, { data: searchResult, timestamp: Date.now() });

            return searchResult;

        } catch (error) {
            console.error('Erreur de recherche web:', error);
            return {
                query,
                timestamp: new Date().toISOString(),
                totalResults: 0,
                results: [],
                synthesis: `Erreur de recherche : ${error.message}`,
                querySignature: [0, 0, 0, 0, 0, 0, 0],
                metadata: { source: 'error', error: error.message }
            };
        }
    }

    /**
     * Recherche via DuckDuckGo API (gratuite, sans clé)
     */
    async _searchDuckDuckGo(query, maxResults) {
        const url = new URL(SEARCH_CONFIG.duckduckgo.baseUrl);
        url.searchParams.set('q', query);
        url.searchParams.set('format', 'json');
        url.searchParams.set('no_html', '1');
        url.searchParams.set('skip_disambig', '1');
        url.searchParams.set('t', 'harmonic_ai');

        const response = await fetch(url.toString(), {
            signal: AbortSignal.timeout(SEARCH_CONFIG.timeout)
        });

        if (!response.ok) {
            throw new Error(`DuckDuckGo API error: ${response.status}`);
        }

        const data = await response.json();
        const results = [];

        // Résultats principaux (RelatedTopics)
        if (data.RelatedTopics) {
            for (const topic of data.RelatedTopics) {
                if (topic.Result && results.length < maxResults) {
                    results.push({
                        title: topic.Text ? topic.Text.split(' - ')[0] : topic.Result,
                        url: topic.FirstURL || '',
                        snippet: topic.Text || topic.Result || '',
                        source: 'duckduckgo'
                    });
                }
                // Sous-sujets
                if (topic.Topics && results.length < maxResults) {
                    for (const sub of topic.Topics) {
                        if (results.length < maxResults) {
                            results.push({
                                title: sub.Text ? sub.Text.split(' - ')[0] : sub.Result,
                                url: sub.FirstURL || '',
                                snippet: sub.Text || sub.Result || '',
                                source: 'duckduckgo'
                            });
                        }
                    }
                }
            }
        }

        // Résultat abstrait (Abstract)
        if (data.Abstract && data.Abstract.length > 50 && results.length < maxResults) {
            results.unshift({
                title: data.Heading || 'Résumé',
                url: data.AbstractURL || '',
                snippet: data.Abstract,
                source: 'duckduckgo_abstract'
            });
        }

        return results.slice(0, maxResults);
    }

    /**
     * Analyse harmonique d'un résultat de recherche
     */
    async _analyzeResult(result) {
        const analyzer = new HarmonicEngine.HarmonicAnalyzer();
        
        // Analyser le snippet
        const snippetAnalysis = analyzer.analyze(result.snippet || result.title);
        const snippetSig = snippetAnalysis.toVector();

        // Essayer de fetch le contenu de la page
        let pageContent = '';
        let pageAnalysis = null;

        if (result.url) {
            pageContent = await this._fetchPageContent(result.url);
            if (pageContent) {
                pageAnalysis = analyzer.analyze(pageContent.substring(0, SEARCH_CONFIG.maxCharsPerPage));
            }
        }

        // Fusionner les signatures (snippet + page si disponible)
        let finalSignature;
        if (pageAnalysis) {
            const signatures = [snippetSig, pageAnalysis.toVector()];
            finalSignature = HarmonicMultimodal.fuseSignatures(signatures);
        } else {
            finalSignature = snippetSig;
        }

        // Métadonnées enrichies
        const wordCount = (result.snippet + ' ' + (pageContent || '')).split(/\s+/).length;
        const hasNumbers = /\d+/.test(result.snippet);
        const hasQuestions = /\?/.test(result.snippet);
        const hasQuotes = /["""]/.test(result.snippet);

        return {
            ...result,
            signature: finalSignature,
            snippetSig: snippetSig,
            pageContent: pageContent ? pageContent.substring(0, 500) + '...' : null,
            wordCount,
            hasNumbers,
            hasQuestions,
            hasQuotes,
            // Catégorie harmonique dominante
            dominantCategory: this._categorize(finalSignature),
            // Score de confiance
            confidence: Math.sqrt(finalSignature.reduce((s, v) => s + v*v, 0)) * PHI / 3
        };
    }

    /**
     * Fetch le contenu d'une page via proxy CORS
     */
    async _fetchPageContent(url) {
        try {
            const proxyUrl = SEARCH_CONFIG.corsProxy + encodeURIComponent(url);
            const response = await fetch(proxyUrl, {
                signal: AbortSignal.timeout(SEARCH_CONFIG.timeout)
            });

            if (!response.ok) return '';

            const html = await response.text();
            
            // Extraction basique du texte (sans bibliothèque DOM)
            const text = html
                .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, ' ')
                .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ' ')
                .replace(/<[^>]+>/g, ' ')
                .replace(/&[^;]+;/g, ' ')
                .replace(/\s+/g, ' ')
                .trim();

            return text.substring(0, SEARCH_CONFIG.maxCharsPerPage);

        } catch (e) {
            // Proxy peut échouer, ce n'est pas bloquant
            return '';
        }
    }

    /**
     * Classement par résonance avec la requête
     */
    _rankByResonance(results, querySig) {
        return results
            .map(result => {
                const resonance = computeResonance(querySig, result.signature);
                return { ...result, resonance };
            })
            .sort((a, b) => b.resonance - a.resonance);
    }

    /**
     * Catégorisation harmonique
     */
    _categorize(signature) {
        const [phi, alpha, reasoning, creative, math, factual, code] = signature;
        const categories = [
            { name: 'Scientifique', score: math * 0.4 + factual * 0.3 + reasoning * 0.3 },
            { name: 'Créatif', score: creative * 0.6 + phi * 0.4 },
            { name: 'Technique', score: code * 0.5 + math * 0.3 + factual * 0.2 },
            { name: 'Analyse', score: reasoning * 0.5 + factual * 0.3 + phi * 0.2 },
            { name: 'Factuel', score: factual * 0.6 + math * 0.2 + reasoning * 0.2 }
        ];
        return categories.sort((a, b) => b.score - a.score)[0].name;
    }

    /**
     * Synthèse harmonique multi-sources
     */
    _synthesize(results, query) {
        if (results.length === 0) {
            return 'Aucun résultat trouvé.';
        }

        const topResults = results.slice(0, 5);
        const avgResonance = topResults.reduce((s, r) => s + r.resonance, 0) / topResults.length;
        
        // Compter les catégories
        const catCount = {};
        for (const r of topResults) {
            catCount[r.dominantCategory] = (catCount[r.dominantCategory] || 0) + 1;
        }
        const mainCategory = Object.entries(catCount).sort((a, b) => b[1] - a[1])[0][0];

        // Détection de consensus
        const signatures = topResults.map(r => r.signature);
        const fused = HarmonicMultimodal.fuseSignatures(signatures);
        const consensus = Math.sqrt(fused.reduce((s, v) => s + v*v, 0)) * PHI / 3;

        return {
            summary: `Synthèse de ${topResults.length} sources — catégorie dominante : ${mainCategory}`,
            consensus: Math.min(1, consensus),
            avgResonance: Math.min(1, avgResonance),
            mainCategory,
            sourceCount: topResults.length,
            topSources: topResults.map(r => ({
                title: r.title,
                url: r.url,
                resonance: r.resonance,
                category: r.dominantCategory
            }))
        };
    }

    /**
     * Vider le cache
     */
    clearCache() {
        this.cache.clear();
    }
}

// =========================================================================
// INTERFACE UTILISATEUR DE RECHERCHE
// =========================================================================

class SearchUI {
    constructor(options = {}) {
        this.engine = new WebSearchEngine();
        this.onResult = options.onResult || null;
        this.container = null;
        this.isOpen = false;
    }

    /**
     * Crée l'interface de recherche dans un conteneur
     */
    create(containerId = 'searchContainer') {
        this.container = document.getElementById(containerId) || this._createContainer(containerId);
        this.container.innerHTML = `
            <div class="search-bar">
                <input type="text" id="searchQuery" placeholder="Rechercher sur le web..." />
                <button id="searchBtn" class="search-btn">
                    <svg viewBox="0 0 24 24" width="18" height="18">
                        <path fill="#888" d="M15.5,14h-0.79l-0.28,-0.27C15.41,12.59 16,11.11 16,9.5 16,5.91 13.09,3 9.5,3S3,5.91 3,9.5 5.91,16 9.5,16c1.61,0 3.09,-0.59 4.23,-1.57l0.27,0.28v0.79l5,4.99L20.49,19l-4.99,-5zM9.5,14C7.01,14 5,11.99 5,9.5S7.01,5 9.5,5 14,7.01 14,9.5 11.99,14 9.5,14z"/>
                    </svg>
                </button>
            </div>
            <div id="searchResults" class="search-results"></div>
            <div id="searchLoading" class="search-loading hidden">
                <div class="spinner"></div>
                <span>Recherche harmonique en cours...</span>
            </div>
        `;

        this._bindEvents();
        return this.container;
    }

    _createContainer(id) {
        const div = document.createElement('div');
        div.id = id;
        document.body.appendChild(div);
        return div;
    }

    _bindEvents() {
        const input = document.getElementById('searchQuery');
        const btn = document.getElementById('searchBtn');

        const doSearch = () => {
            const query = input.value.trim();
            if (query) this.search(query);
        };

        btn.addEventListener('click', doSearch);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') doSearch();
        });
    }

    /**
     * Lance une recherche et affiche les résultats
     */
    async search(query) {
        this._showLoading();
        this._clearResults();

        try {
            const result = await this.engine.search(query);
            this._displayResults(result, query);

            if (this.onResult) {
                this.onResult(result);
            }

        } catch (error) {
            this._displayError(error.message);
        } finally {
            this._hideLoading();
        }
    }

    _displayResults(result, query) {
        const container = document.getElementById('searchResults');
        if (!container) return;

        if (result.totalResults === 0) {
            container.innerHTML = `<div class="search-empty">Aucun résultat pour "${query}"</div>`;
            return;
        }

        let html = '';

        // Synthèse
        if (result.synthesis && typeof result.synthesis === 'object') {
            const s = result.synthesis;
            const consensusPct = Math.round(s.consensus * 100);
            const resonancePct = Math.round(s.avgResonance * 100);
            
            html += `
                <div class="search-synthesis">
                    <div class="synthesis-header">
                        <span class="synthesis-icon">φ</span>
                        <span>Synthèse Harmonique</span>
                    </div>
                    <div class="synthesis-body">
                        <p>${s.summary}</p>
                        <div class="synthesis-metrics">
                            <span class="metric">
                                <span class="metric-label">Consensus</span>
                                <span class="metric-value ${consensusPct > 70 ? 'high' : consensusPct > 40 ? 'mid' : 'low'}">
                                    ${consensusPct}%
                                </span>
                            </span>
                            <span class="metric">
                                <span class="metric-label">Résonance</span>
                                <span class="metric-value ${resonancePct > 70 ? 'high' : resonancePct > 40 ? 'mid' : 'low'}">
                                    ${resonancePct}%
                                </span>
                            </span>
                            <span class="metric">
                                <span class="metric-label">Sources</span>
                                <span class="metric-value">${s.sourceCount}</span>
                            </span>
                            <span class="metric">
                                <span class="metric-label">Catégorie</span>
                                <span class="metric-value cat">${s.mainCategory}</span>
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }

        // Résultats classés
        html += '<div class="results-list">';
        for (const r of result.results) {
            const resonancePct = Math.round((r.resonance || 0) * 100);
            const confidencePct = Math.round((r.confidence || 0) * 100);
            
            html += `
                <div class="search-result-item" style="border-left-color: ${this._resonanceColor(r.resonance || 0)}">
                    <div class="result-header">
                        <a href="${r.url}" target="_blank" rel="noopener" class="result-title">
                            ${r.title || 'Sans titre'}
                        </a>
                        <span class="result-source">${new URL(r.url).hostname || ''}</span>
                    </div>
                    <div class="result-snippet">${r.snippet || ''}</div>
                    <div class="result-meta">
                        <span class="result-resonance" style="color: ${this._resonanceColor(r.resonance || 0)}">
                            ◆ ${resonancePct}% résonance
                        </span>
                        <span class="result-category">${r.dominantCategory || 'Général'}</span>
                        <span class="result-confidence">${confidencePct}% confiance</span>
                    </div>
                    ${r.pageContent ? `<div class="result-preview">${r.pageContent.substring(0, 200)}...</div>` : ''}
                </div>
            `;
        }
        html += '</div>';

        // Signature de la requête
        html += `
            <div class="search-signature">
                <span class="sig-label">Signature harmonique de la requête :</span>
                <span class="sig-values">[${result.querySignature.map(v => v.toFixed(2)).join(', ')}]</span>
            </div>
        `;

        container.innerHTML = html;
    }

    _resonanceColor(resonance) {
        if (resonance > 0.7) return '#4CAF50';
        if (resonance > 0.4) return '#FF9800';
        return '#999';
    }

    _displayError(message) {
        const container = document.getElementById('searchResults');
        if (container) {
            container.innerHTML = `<div class="search-error">⚠️ ${message}</div>`;
        }
    }

    _showLoading() {
        const loading = document.getElementById('searchLoading');
        if (loading) loading.classList.remove('hidden');
    }

    _hideLoading() {
        const loading = document.getElementById('searchLoading');
        if (loading) loading.classList.add('hidden');
    }

    _clearResults() {
        const container = document.getElementById('searchResults');
        if (container) container.innerHTML = '';
    }

    /**
     * Ouvre/ferme le panneau de recherche
     */
    toggle() {
        if (this.container) {
            this.isOpen = !this.isOpen;
            this.container.classList.toggle('search-open', this.isOpen);
            if (this.isOpen) {
                document.getElementById('searchQuery')?.focus();
            }
        }
    }

    open() {
        if (this.container) {
            this.isOpen = true;
            this.container.classList.add('search-open');
            document.getElementById('searchQuery')?.focus();
        }
    }

    close() {
        if (this.container) {
            this.isOpen = false;
            this.container.classList.remove('search-open');
        }
    }
}

// =========================================================================
// EXPORT
// =========================================================================

window.HarmonicSearch = {
    WebSearchEngine,
    SearchUI
};
