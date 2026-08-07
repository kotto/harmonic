// Configuration du frontend Harmonic AI SaaS
const CONFIG = {
    // URLs des services backend
    API_BASE_URL: 'http://localhost:9000/api/v1',
    DEEPSEEK_API_URL: 'http://__EC2_IP__:8000',
    AUDIO_SERVICE_URL: 'http://localhost:9017',
    VIDEO_SERVICE_URL: 'http://localhost:9018',
    
    // New service endpoints (relative to API_BASE_URL)
    ENDPOINTS: {
        DATACENTER: '/datacenter',
        HPC: '/hpc',
        KNOWLEDGE: '/knowledge',
        REASONING: '/reasoning',
        CODE: '/code',
        WAVE: '/wave',
    },
    
    // Configuration des limites
    MAX_FILE_SIZE: {
        AUDIO: 100 * 1024 * 1024, // 100MB
        VIDEO: 500 * 1024 * 1024, // 500MB
        IMAGE: 10 * 1024 * 1024   // 10MB
    },
    
    // Formats de fichiers supportÃ©s
    SUPPORTED_FORMATS: {
        AUDIO: ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'],
        VIDEO: ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'],
        IMAGE: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    },
    
    // Modes de traitement disponibles
    PROCESSING_MODES: {
        AUDIO: {
            HCS_RESTORE: {
                name: 'HCS Restore',
                description: 'Restauration audio complÃ¨te avec technologie harmonique',
                estimatedTime: '2-5 minutes',
                cost: 5
            },
            HCS_SPATIAL: {
                name: 'HCS Spatial',
                description: 'AmÃ©lioration spatiale 3D immersive',
                estimatedTime: '3-7 minutes',
                cost: 8
            },
            HCS_CLARITY: {
                name: 'HCS Clarity',
                description: 'ClartÃ© et nettetÃ© optimale',
                estimatedTime: '1-3 minutes',
                cost: 3
            },
            HCS_DYNAMIC: {
                name: 'HCS Dynamic',
                description: 'Plage dynamique Ã©tendue',
                estimatedTime: '2-4 minutes',
                cost: 6
            }
        },
        VIDEO: {
            HCS_4K_CLARITY: {
                name: 'HCS 4K Clarity',
                description: 'Upscaling 4K avec clartÃ© optimale',
                estimatedTime: '5-15 minutes',
                cost: 15
            },
            HCS_8K_MASTER: {
                name: 'HCS 8K Master',
                description: 'Masterisation 8K professionnelle',
                estimatedTime: '10-30 minutes',
                cost: 30
            },
            HCS_HDR_VISION: {
                name: 'HCS HDR Vision',
                description: 'Conversion HDR avancÃ©e',
                estimatedTime: '8-20 minutes',
                cost: 25
            },
            HCS_FRAME_GEN: {
                name: 'HCS Frame Generation',
                description: 'GÃ©nÃ©ration de frames intermÃ©diaires',
                estimatedTime: '15-40 minutes',
                cost: 40
            },
            HCS_MOVIE_CONTINUOUS: {
                name: 'HCS Movie Continuous',
                description: 'GÃ©nÃ©ration de films continus',
                estimatedTime: '30-60 minutes',
                cost: 100
            }
        }
    },
    
    // Plans d'abonnement
    SUBSCRIPTION_PLANS: {
        FREE: {
            name: 'Free',
            price: 0,
            features: [
                '10 minutes de traitement audio/mois',
                '5 minutes de traitement vidÃ©o/mois',
                'Chat LM Arena limitÃ©',
                'Support communautaire'
            ],
            limits: {
                audio: 600, // secondes
                video: 300, // secondes
                chat: 50 // messages
            }
        },
        PRO: {
            name: 'Pro',
            price: 49,
            features: [
                '5 heures de traitement audio/mois',
                '2 heures de traitement vidÃ©o/mois',
                'Chat LM Arena illimitÃ©',
                'Tous les modes audio',
                'Modes vidÃ©o jusqu\'Ã  4K',
                'Support prioritaire'
            ],
            limits: {
                audio: 18000, // secondes
                video: 7200, // secondes
                chat: -1 // illimitÃ©
            }
        },
        ENTERPRISE: {
            name: 'Enterprise',
            price: 299,
            features: [
                'Traitement audio/vidÃ©o illimitÃ©',
                'Tous les modes avancÃ©s',
                'GÃ©nÃ©ration de films continus',
                'API dÃ©diÃ©e',
                'Support 24/7',
                'Facturation personnalisÃ©e'
            ],
            limits: {
                audio: -1, // illimitÃ©
                video: -1, // illimitÃ©
                chat: -1 // illimitÃ©
            }
        }
    },
    
    // Configuration UI
    UI: {
        THEME: {
            DARK: 'dark',
            LIGHT: 'light',
            DEFAULT: 'dark'
        },
        ANIMATIONS: {
            ENABLED: true,
            DURATION: 300
        },
        NOTIFICATIONS: {
            TIMEOUT: 5000,
            POSITION: 'top-right'
        }
    },
    
    // Configuration sÃ©curitÃ©
    SECURITY: {
        SESSION_TIMEOUT: 24 * 60 * 60 * 1000, // 24 heures
        TOKEN_REFRESH_INTERVAL: 30 * 60 * 1000, // 30 minutes
        MAX_LOGIN_ATTEMPTS: 5,
        LOCKOUT_DURATION: 15 * 60 * 1000 // 15 minutes
    },
    
    // Configuration monitoring
    MONITORING: {
        ENABLED: true,
        SENTRY_DSN: '',
        LOG_LEVEL: 'info',
        METRICS_INTERVAL: 60000 // 1 minute
    }
};

// Fonctions utilitaires
const Utils = {
    // Formater la taille des fichiers
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Formater la durÃ©e
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    },
    
    // Valider le format de fichier
    validateFileFormat(file, type) {
        const extension = file.name.split('.').pop().toLowerCase();
        return CONFIG.SUPPORTED_FORMATS[type.toUpperCase()].includes(extension);
    },
    
    // Valider la taille du fichier
    validateFileSize(file, type) {
        return file.size <= CONFIG.MAX_FILE_SIZE[type.toUpperCase()];
    },
    
    // GÃ©nÃ©rer un ID unique
    generateId() {
        return 'id_' + Math.random().toString(36).substr(2, 9);
    },
    
    // Formater la date
    formatDate(date) {
        return new Date(date).toLocaleString('fr-FR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Copier dans le presse-papier
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Texte copiÃ© dans le presse-papier');
        }).catch(err => {
            console.error('Erreur lors de la copie:', err);
        });
    }
};

// Export pour utilisation globale
window.HarmonicConfig = CONFIG;
window.HarmonicUtils = Utils;