/**
 * Flux d'Actualités Temps Réel — Moteur Harmonique
 * ==================================================
 * Agrège des flux RSS/Atom, analyse harmoniquement chaque article,
 * détecte les tendances émergentes par résonance collective.
 * 
 * Fonctionnalités :
 * - Agrégation multi-sources RSS (Le Monde, BBC, Reuters, TechCrunch...)
 * - Analyse harmonique 7D de chaque article
 * - Détection de tendances (résonance croisée)
 * - Notifications push (WebSocket simulé)
 * - Dashboard temps réel
 */

// =========================================================================
// SOURCES RSS
// =========================================================================

const NEWS_SOURCES = {
    // France
    'lemonde': {
        name: 'Le Monde',
        url: 'https://www.lemonde.fr/rss/une.xml',
        lang: 'fr',
        category: 'general'
    },
    'lefigaro': {
        name: 'Le Figaro',
        url: 'https://www.lefigaro.fr/rss/figaro_actualites.xml',
        lang: 'fr',
        category: 'general'
    },
    'franceinfo': {
        name: 'France Info',
        url: 'https://www.francetvinfo.fr/titres.rss',
        lang: 'fr',
        category: 'general'
    },
    // International
    'bbc': {
        name: 'BBC News',
        url: 'https://feeds.bbci.co.uk/news/rss.xml',
        lang: 'en',
        category: 'general'
    },
    'reuters': {
        name: 'Reuters',
        url: 'https://www.reutersagency.com/feed/',
        lang: 'en',
        category: 'general'
    },
    'guardian': {
        name: 'The Guardian',
        url: 'https://www.theguardian.com/world/rss',
        lang: 'en',
        category: 'general'
    },
    // Tech
    'techcrunch': {
        name: 'TechCrunch',
        url: 'https://techcrunch.com/feed/',
        lang: 'en',
        category: 'tech'
    },
    'theverge': {
        name: 'The Verge',
        url: 'https://www.theverge.com/rss/index.xml',
        lang: 'en',
        category: 'tech'
    },
    // Science
    'nature': {
        name: 'Nature',
        url: 'https://www.nature.com/nature.rss',
        lang: 'en',
        category: 'science'
    },
    'science_daily': {
        name: 'Science Daily',
        url: 'https://www.sciencedaily.com/rss/all.xml',
        lang: 'en',
        category: 'science'
    }
};

// =========================================================================
// PARSEUR RSS (côté client via proxy CORS)
// =========================================================================

class RSSParser {
    /**
     * Parse du XML RSS/Atom en articles structurés
     */
    static parse(xmlText, sourceKey) {
        const source = NEWS_SOURCES[sourceKey] || { name: sourceKey, lang: 'en', category: 'general' };
        const articles = [];

        // RSS 2.0
        const itemRegex = /<item>([\s\S]*?)<\/item>/gi;
        let match;
        
        while ((match = itemRegex.exec(xmlText)) !== null) {
            const item = match[1];
            
            const title = this._extract(item, 'title');
            const link = this._extract(item, 'link');
            const description = this._extract(item, 'description');
            const pubDate = this._extract(item, 'pubDate');
            const creator = this._extract(item, 'dc:creator') || this._extract(item, 'author');
            const category = this._extract(item, 'category');
            
            if (title && link) {
                articles.push({
                    title: this._decode(title),
                    url: link.trim(),
                    description: this._stripHtml(this._decode(description || '')),
                    date: pubDate ? new Date(pubDate).toISOString() : new Date().toISOString(),
                    author: creator ? this._decode(creator) : '',
                    category: category ? this._decode(category) : source.category,
                    source: source.name,
                    sourceKey,
                    lang: source.lang,
                    id: this._hash(title + link)
                });
            }
        }

        // Atom
        if (articles.length === 0) {
            const entryRegex = /<entry>([\s\S]*?)<\/entry>/gi;
            while ((match = entryRegex.exec(xmlText)) !== null) {
                const entry = match[1];
                
                const title = this._extract(entry, 'title');
                const linkMatch = entry.match(/<link[^>]+href="([^"]+)"/);
                const link = linkMatch ? linkMatch[1] : '';
                const content = this._extract(entry, 'content') || this._extract(entry, 'summary');
                const published = this._extract(entry, 'published') || this._extract(entry, 'updated');
                const authorMatch = entry.match(/<author>[\s\S]*?<name>([^<]+)<\/name>[\s\S]*?<\/author>/);
                const author = authorMatch ? authorMatch[1] : '';
                
                if (title && link) {
                    articles.push({
                        title: this._decode(title),
                        url: link.trim(),
                        description: this._stripHtml(this._decode(content || '')),
                        date: published ? new Date(published).toISOString() : new Date().toISOString(),
                        author: this._decode(author),
                        category: source.category,
                        source: source.name,
                        sourceKey,
                        lang: source.lang,
                        id: this._hash(title + link)
                    });
                }
            }
        }

        return articles;
    }

    static _extract(xml, tag) {
        const regex = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, 'i');
        const match = xml.match(regex);
        return match ? match[1].trim() : '';
    }

    static _stripHtml(text) {
        return text.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    }

    static _decode(text) {
        return text
            .replace(/&/g, '&')
            .replace(/</g, '<')
            .replace(/>/g, '>')
            .replace(/"/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/&#x27;/g, "'")
            .replace(/&#x2F;/g, '/');
    }

    static _hash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash |= 0;
        }
        return 'article_' + Math.abs(hash).toString(36);
    }
}

// =========================================================================
// AGRÉGATEUR D'ACTUALITÉS
// =========================================================================

class NewsAggregator {
    constructor(options = {}) {
        this.sources = options.sources || Object.keys(NEWS_SOURCES);
        this.pollInterval = options.pollInterval || 120000; // 2 minutes
        this.maxArticles = options.maxArticles || 50;
        this.analyzer = new HarmonicEngine.HarmonicAnalyzer();
        
        // État
        this.articles = [];
        this.trends = [];
        this.lastPoll = {};
        this.isRunning = false;
        this.timer = null;
        this.onUpdate = options.onUpdate || null;
        this.onTrend = options.onTrend || null;
        
        // Cache des articles déjà vus (pour éviter les doublons)
        this.seenIds = new Set();
    }

    /**
     * Démarre l'agrégation
     */
    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this._poll();
        this.timer = setInterval(() => this._poll(), this.pollInterval);
        console.log(`📰 Agrégateur démarré (${this.sources.length} sources, intervalle ${this.pollInterval/1000}s)`);
    }

    /**
     * Arrête l'agrégation
     */
    stop() {
        this.isRunning = false;
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        console.log('📰 Agrégateur arrêté');
    }

    /**
     * Obtient les articles récents
     */
    getRecentArticles(count = 20) {
        return this.articles.slice(0, count);
    }

    /**
     * Obtient les tendances actuelles
     */
    getTrends() {
        return this.trends;
    }

    /**
     * Polling d'une source
     */
    async _poll() {
        for (const sourceKey of this.sources) {
            try {
                await this._fetchSource(sourceKey);
            } catch (e) {
                console.warn(`⚠️ Erreur source ${sourceKey}:`, e.message);
            }
        }
        
        // Analyser les tendances
        this._analyzeTrends();
    }

    /**
     * Fetch et analyse une source RSS
     */
    async _fetchSource(sourceKey) {
        const source = NEWS_SOURCES[sourceKey];
        if (!source) return;

        // Rate limiting : pas plus d'une fois toutes les 30s par source
        const now = Date.now();
        if (this.lastPoll[sourceKey] && now - this.lastPoll[sourceKey] < 30000) {
            return;
        }
        this.lastPoll[sourceKey] = now;

        // Fetch via proxy CORS
        const proxyUrl = 'https://api.allorigins.win/raw?url=';
        const response = await fetch(proxyUrl + encodeURIComponent(source.url), {
            signal: AbortSignal.timeout(10000)
        });

        if (!response.ok) return;

        const xml = await response.text();
        const articles = RSSParser.parse(xml, sourceKey);

        // Analyser et ajouter les nouveaux articles
        let newCount = 0;
        for (const article of articles) {
            if (!this.seenIds.has(article.id)) {
                this.seenIds.add(article.id);
                
                // Analyse harmonique
                const analysis = this.analyzer.analyze(
                    (article.title + ' ' + article.description).substring(0, 2000)
                );
                article.signature = analysis.toVector();
                article.resonance = Math.sqrt(
                    article.signature.reduce((s, v) => s + v*v, 0)
                ) * PHI / 3;
                article.dominantCategory = this._categorize(article.signature);
                
                this.articles.unshift(article);
                newCount++;
            }
        }

        // Trier par date
        this.articles.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        // Limiter le nombre d'articles
        if (this.articles.length > this.maxArticles) {
            this.articles = this.articles.slice(0, this.maxArticles);
        }

        // Notifier
        if (newCount > 0 && this.onUpdate) {
            this.onUpdate(articles.slice(0, newCount));
        }
    }

    /**
     * Analyse les tendances émergentes
     */
    _analyzeTrends() {
        if (this.articles.length < 3) return;

        // Regrouper par similarité de signature
        const clusters = [];
        const threshold = 0.85;

        for (const article of this.articles) {
            let added = false;
            for (const cluster of clusters) {
                const avgSig = cluster.avgSignature;
                const resonance = this._computeResonance(article.signature, avgSig);
                if (resonance > threshold) {
                    cluster.articles.push(article);
                    cluster.avgSignature = this._averageSignatures(
                        cluster.articles.map(a => a.signature)
                    );
                    added = true;
                    break;
                }
            }
            if (!added) {
                clusters.push({
                    articles: [article],
                    avgSignature: [...article.signature]
                });
            }
        }

        // Les clusters avec le plus de momentum = tendances
        const now = Date.now();
        this.trends = clusters
            .filter(c => c.articles.length >= 2)
            .map(cluster => {
                const recent = cluster.articles.filter(
                    a => now - new Date(a.date).getTime() < 3600000 // 1h
                );
                const momentum = recent.length / Math.max(1, cluster.articles.length);
                const avgResonance = cluster.articles.reduce(
                    (s, a) => s + a.resonance, 0
                ) / cluster.articles.length;
                
                // Mots-clés communs
                const words = {};
                for (const a of cluster.articles) {
                    const titleWords = a.title.toLowerCase().split(/\s+/);
                    for (const w of titleWords) {
                        if (w.length > 4) words[w] = (words[w] || 0) + 1;
                    }
                }
                const topKeywords = Object.entries(words)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([w]) => w);

                return {
                    keywords: topKeywords,
                    articleCount: cluster.articles.length,
                    momentum: Math.min(1, momentum),
                    avgResonance: Math.min(1, avgResonance),
                    topArticles: cluster.articles.slice(0, 3),
                    category: cluster.articles[0]?.dominantCategory || 'Général',
                    timestamp: new Date().toISOString()
                };
            })
            .sort((a, b) => (b.momentum * 0.6 + b.avgResonance * 0.4) - 
                           (a.momentum * 0.6 + a.avgResonance * 0.4))
            .slice(0, 10);

        // Notifier les nouvelles tendances fortes
        if (this.onTrend) {
            const strongTrends = this.trends.filter(t => t.momentum > 0.7 && t.articleCount >= 3);
            for (const trend of strongTrends) {
                this.onTrend(trend);
            }
        }
    }

    _computeResonance(sig1, sig2) {
        const dot = sig1.reduce((s, v, i) => s + v * sig2[i], 0);
        const norm1 = Math.sqrt(sig1.reduce((s, v) => s + v*v, 0));
        const norm2 = Math.sqrt(sig2.reduce((s, v) => s + v*v, 0));
        return norm1 && norm2 ? dot / (norm1 * norm2) : 0;
    }

    _averageSignatures(signatures) {
        const n = signatures.length;
        return signatures[0].map((_, i) => 
            signatures.reduce((s, sig) => s + sig[i], 0) / n
        );
    }

    _categorize(sig) {
        const [phi, alpha, reasoning, creative, math, factual, code] = sig;
        const cats = {
            'Scientifique': math * 0.4 + factual * 0.3 + reasoning * 0.3,
            'Créatif': creative * 0.6 + phi * 0.4,
            'Technique': code * 0.5 + math * 0.3 + factual * 0.2,
            'Analyse': reasoning * 0.5 + factual * 0.3 + phi * 0.2,
            'Factuel': factual * 0.6 + math * 0.2 + reasoning * 0.2
        };
        return Object.entries(cats).sort((a, b) => b[1] - a[1])[0][0];
    }
}

// =========================================================================
// DASHBOARD D'ACTUALITÉS
// =========================================================================

class NewsDashboard {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId) || this._createContainer(containerId);
        this.aggregator = new NewsAggregator({
            ...options,
            onUpdate: (articles) => this._onNewArticles(articles),
            onTrend: (trend) => this._onNewTrend(trend)
        });
        this.isOpen = false;
    }

    /**
     * Crée l'interface du dashboard
     */
    create() {
        this.container.innerHTML = `
            <div class="news-dashboard">
                <div class="news-header">
                    <span class="news-icon">📰</span>
                    <span>Actualités Harmoniques</span>
                    <span class="news-status" id="newsStatus">● Arrêté</span>
                    <button id="newsToggleBtn" class="news-toggle-btn">▶ Démarrer</button>
                </div>
                <div class="news-body hidden" id="newsBody">
                    <div class="news-trends" id="newsTrends">
                        <h4>Tendances émergentes</h4>
                        <div id="trendsList" class="trends-list">
                            <div class="trends-empty">En attente de données...</div>
                        </div>
                    </div>
                    <div class="news-feed" id="newsFeed">
                        <h4>Flux d'actualités</h4>
                        <div id="articlesList" class="articles-list">
                            <div class="articles-empty">En attente de données...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this._bindEvents();
        return this.container;
    }

    _bindEvents() {
        const btn = document.getElementById('newsToggleBtn');
        btn.addEventListener('click', () => {
            if (this.aggregator.isRunning) {
                this.aggregator.stop();
                btn.textContent = '▶ Démarrer';
                document.getElementById('newsStatus').textContent = '● Arrêté';
                document.getElementById('newsStatus').style.color = '#999';
            } else {
                this.aggregator.start();
                btn.textContent = '⏹ Arrêter';
                document.getElementById('newsStatus').textContent = '● En direct';
                document.getElementById('newsStatus').style.color = '#4CAF50';
                document.getElementById('newsBody').classList.remove('hidden');
            }
        });
    }

    _onNewArticles(articles) {
        const list = document.getElementById('articlesList');
        if (!list) return;

        // Enlever le message "vide"
        const empty = list.querySelector('.articles-empty');
        if (empty) empty.remove();

        for (const article of articles.slice(0, 5)) {
            const div = document.createElement('div');
            div.className = 'article-item';
            div.style.animation = 'fadeIn 0.3s ease';
            
            const resonancePct = Math.round((article.resonance || 0) * 100);
            const timeAgo = this._timeAgo(new Date(article.date));
            
            div.innerHTML = `
                <div class="article-source">${article.source}</div>
                <div class="article-title">
                    <a href="${article.url}" target="_blank" rel="noopener">${article.title}</a>
                </div>
                <div class="article-meta">
                    <span class="article-time">${timeAgo}</span>
                    <span class="article-category">${article.dominantCategory || ''}</span>
                    <span class="article-resonance" style="color: ${resonancePct > 70 ? '#4CAF50' : resonancePct > 40 ? '#FF9800' : '#999'}">
                        ◆ ${resonancePct}%
                    </span>
                </div>
            `;
            
            list.insertBefore(div, list.firstChild);
            
            // Limiter à 50 articles
            while (list.children.length > 50) {
                list.removeChild(list.lastChild);
            }
        }
    }

    _onNewTrend(trend) {
        const list = document.getElementById('trendsList');
        if (!list) return;

        const empty = list.querySelector('.trends-empty');
        if (empty) empty.remove();

        // Vérifier si la tendance existe déjà
        const existing = list.querySelector(`[data-keywords="${trend.keywords.join(',')}"]`);
        if (existing) {
            // Mettre à jour le momentum
            const momentumEl = existing.querySelector('.trend-momentum');
            if (momentumEl) {
                momentumEl.textContent = `🔥 ${Math.round(trend.momentum * 100)}%`;
            }
            return;
        }

        const div = document.createElement('div');
        div.className = 'trend-item';
        div.setAttribute('data-keywords', trend.keywords.join(','));
        div.style.animation = 'fadeIn 0.3s ease';
        
        div.innerHTML = `
            <div class="trend-keywords">${trend.keywords.join(' · ')}</div>
            <div class="trend-meta">
                <span class="trend-momentum">🔥 ${Math.round(trend.momentum * 100)}%</span>
                <span class="trend-articles">${trend.articleCount} articles</span>
                <span class="trend-category">${trend.category}</span>
            </div>
        `;
        
        list.insertBefore(div, list.firstChild);
        
        while (list.children.length > 10) {
            list.removeChild(list.lastChild);
        }
    }

    _timeAgo(date) {
        const seconds = Math.floor((Date.now() - date) / 1000);
        if (seconds < 60) return 'à l\'instant';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `il y a ${minutes} min`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `il y a ${hours}h`;
        const days = Math.floor(hours / 24);
        return `il y a ${days}j`;
    }

    _createContainer(id) {
        const div = document.createElement('div');
        div.id = id;
        document.body.appendChild(div);
        return div;
    }

    toggle() {
        if (this.container) {
            this.isOpen = !this.isOpen;
            this.container.classList.toggle('news-open', this.isOpen);
        }
    }
}

// =========================================================================
// EXPORT
// =========================================================================

window.HarmonicNews = {
    NewsAggregator,
    NewsDashboard,
    RSSParser,
    NEWS_SOURCES
};