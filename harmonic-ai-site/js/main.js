/* ==========================================================================
   Harmonic AI - JavaScript Principal
   Fonctionnalités interactives et gestion du site
   ========================================================================== */

// Configuration globale
const CONFIG = {
    apiEndpoint: 'https://api.harmonic.ai/v1',
    demoMode: true,
    animationEnabled: true,
    language: 'fr'
};

// État de l'application
const APP_STATE = {
    currentLanguage: 'fr',
    mobileMenuOpen: false,
    scrollPosition: 0,
    animations: []
};

// Initialisation du site
document.addEventListener('DOMContentLoaded', function() {
    console.log('Harmonic AI - Site institutionnel initialisé');
    
    // Initialiser les composants
    initNavigation();
    initLanguageSwitcher();
    initAnimations();
    initDemoCard();
    initContactForm();
    initScrollAnimations();
    initParticles();
    
    // Vérifier les préférences utilisateur
    checkUserPreferences();
    
    // Événements globaux
    setupGlobalEvents();
});

/* ==========================================================================
   Navigation
   ========================================================================== */

function initNavigation() {
    const navbar = document.querySelector('.navbar');
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (!navbar || !mobileMenuBtn || !navLinks) return;
    
    // Gestion du scroll pour la navbar
    window.addEventListener('scroll', function() {
        const scrollY = window.scrollY;
        
        if (scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        // Mettre à jour la position de scroll
        APP_STATE.scrollPosition = scrollY;
    });
    
    // Menu mobile
    mobileMenuBtn.addEventListener('click', function() {
        APP_STATE.mobileMenuOpen = !APP_STATE.mobileMenuOpen;
        navLinks.classList.toggle('active');
        
        // Animation de l'icône hamburger
        const icon = mobileMenuBtn.querySelector('i') || mobileMenuBtn;
        if (APP_STATE.mobileMenuOpen) {
            icon.style.transform = 'rotate(90deg)';
        } else {
            icon.style.transform = 'rotate(0deg)';
        }
    });
    
    // Fermer le menu mobile en cliquant sur un lien
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function() {
            if (APP_STATE.mobileMenuOpen) {
                navLinks.classList.remove('active');
                APP_STATE.mobileMenuOpen = false;
                
                const icon = mobileMenuBtn.querySelector('i') || mobileMenuBtn;
                icon.style.transform = 'rotate(0deg)';
            }
        });
    });
}

/* ==========================================================================
   Sélecteur de langue
   ========================================================================== */

function initLanguageSwitcher() {
    const languageButtons = document.querySelectorAll('.language-switcher button');
    
    if (!languageButtons.length) return;
    
    languageButtons.forEach(button => {
        button.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            
            if (lang && lang !== APP_STATE.currentLanguage) {
                switchLanguage(lang);
            }
        });
    });
    
    // Définir le bouton actif
    updateLanguageButtons();
}

function switchLanguage(lang) {
    console.log(`Changement de langue: ${lang}`);
    
    // Mettre à jour l'état
    APP_STATE.currentLanguage = lang;
    CONFIG.language = lang;
    
    // Mettre à jour les boutons
    updateLanguageButtons();
    
    // Rediriger vers la version appropriée
    if (lang === 'en') {
        window.location.href = 'index-en.html';
    } else {
        window.location.href = 'index.html';
    }
}

function updateLanguageButtons() {
    const languageButtons = document.querySelectorAll('.language-switcher button');
    
    languageButtons.forEach(button => {
        const lang = button.getAttribute('data-lang');
        
        if (lang === APP_STATE.currentLanguage) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
}

/* ==========================================================================
   Animations
   ========================================================================== */

function initAnimations() {
    if (!CONFIG.animationEnabled) return;
    
    // Observer pour les animations au scroll
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                
                // Animation spécifique selon la classe
                if (entry.target.classList.contains('staggered-item')) {
                    animateStaggeredItem(entry.target);
                }
                
                if (entry.target.classList.contains('solution-card')) {
                    animateSolutionCard(entry.target);
                }
            }
        });
    }, observerOptions);
    
    // Observer les éléments avec animation au scroll
    document.querySelectorAll('.animate-on-scroll').forEach(element => {
        observer.observe(element);
    });
    
    // Initialiser les animations de survol
    initHoverAnimations();
}

function initHoverAnimations() {
    // Effet de survol pour les cartes de solution
    document.querySelectorAll('.solution-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
            this.style.boxShadow = 'var(--shadow-xl)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'var(--shadow-md)';
        });
    });
    
    // Effet de survol pour les liens de navigation
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.color = 'var(--color-primary-light)';
        });
        
        link.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.color = '';
            }
        });
    });
}

function animateStaggeredItem(element) {
    const index = Array.from(element.parentNode.children).indexOf(element);
    const delay = index * 100;
    
    element.style.animationDelay = `${delay}ms`;
    element.classList.add('fade-in');
}

function animateSolutionCard(card) {
    card.classList.add('slide-in-left');
}

/* ==========================================================================
   Carte de démonstration
   ========================================================================== */

function initDemoCard() {
    const demoCard = document.querySelector('.demo-card');
    const demoContent = document.querySelector('.demo-content');
    
    if (!demoCard || !demoContent) return;
    
    // Contenu de démonstration
    const demoResponses = {
        fr: {
            question: "Qui es-tu?",
            response: "Je suis Deterministic AI, une IA conçue par Harmonic AI Corporation.",
            explanation: "Cette réponse est garantie déterministe : même prompt ⇒ même sortie."
        },
        en: {
            question: "Who are you?",
            response: "I am Deterministic AI, an AI designed by Harmonic AI Corporation.",
            explanation: "This response is deterministically guaranteed: same prompt ⇒ same output."
        }
    };
    
    // Mettre à jour le contenu selon la langue
    function updateDemoContent(lang) {
        const content = demoResponses[lang];
        
        demoContent.innerHTML = `
            <div class="demo-question">
                <strong>Q:</strong> ${content.question}
            </div>
            <div class="demo-answer">
                <strong>A:</strong> ${content.response}
            </div>
            <div class="demo-explanation">
                <em>${content.explanation}</em>
            </div>
        `;
    }
    
    // Initialiser avec la langue actuelle
    updateDemoContent(APP_STATE.currentLanguage);
    
    // Animation de la carte
    demoCard.classList.add('animate-on-scroll');
    
    // Effet de survol
    demoCard.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.02)';
        this.style.transition = 'transform 0.3s ease';
    });
    
    demoCard.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
}

/* ==========================================================================
   Formulaire de contact
   ========================================================================== */

function initContactForm() {
    const contactForm = document.querySelector('.contact-form');
    
    if (!contactForm) return;
    
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validation basique
        const formData = new FormData(this);
        const isValid = validateForm(formData);
        
        if (isValid) {
            submitContactForm(formData);
        }
    });
    
    // Validation en temps réel
    const inputs = contactForm.querySelectorAll('.form-input, .form-textarea');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            clearFieldError(this);
        });
    });
}

function validateForm(formData) {
    let isValid = true;
    
    // Vérifier les champs requis
    const requiredFields = ['name', 'email', 'message'];
    
    requiredFields.forEach(fieldName => {
        const value = formData.get(fieldName);
        
        if (!value || value.trim() === '') {
            markFieldError(fieldName, 'Ce champ est requis');
            isValid = false;
        }
    });
    
    // Validation d'email
    const email = formData.get('email');
    if (email && !isValidEmail(email)) {
        markFieldError('email', 'Veuillez entrer une adresse email valide');
        isValid = false;
    }
    
    return isValid;
}

function validateField(field) {
    const fieldName = field.name;
    const value = field.value.trim();
    
    if (!value) {
        markFieldError(fieldName, 'Ce champ est requis');
        return false;
    }
    
    if (fieldName === 'email' && !isValidEmail(value)) {
        markFieldError(fieldName, 'Veuillez entrer une adresse email valide');
        return false;
    }
    
    clearFieldError(fieldName);
    return true;
}

function markFieldError(fieldName, message) {
    const field = document.querySelector(`[name="${fieldName}"]`);
    const formGroup = field.closest('.form-group');
    
    if (formGroup) {
        formGroup.classList.add('error');
        
        // Ajouter ou mettre à jour le message d'erreur
        let errorElement = formGroup.querySelector('.error-message');
        
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            formGroup.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
        errorElement.style.color = 'var(--color-secondary)';
        errorElement.style.fontSize = '0.875rem';
        errorElement.style.marginTop = '0.25rem';
    }
}

function clearFieldError(fieldName) {
    const field = document.querySelector(`[name="${fieldName}"]`);
    const formGroup = field?.closest('.form-group');
    
    if (formGroup) {
        formGroup.classList.remove('error');
        
        const errorElement = formGroup.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function submitContactForm(formData) {
    console.log('Envoi du formulaire de contact:', Object.fromEntries(formData));
    
    // Simulation d'envoi
    const submitBtn = document.querySelector('.contact-form .btn-primary');
    const originalText = submitBtn.textContent;
    
    submitBtn.textContent = 'Envoi en cours...';
    submitBtn.disabled = true;
    
    setTimeout(() => {
        // Simulation de réponse
        showNotification('Message envoyé avec succès !', 'success');
        
        // Réinitialiser le formulaire
        document.querySelector('.contact-form').reset();
        
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }, 1500);
}

/* ==========================================================================
   Animations au scroll
   ========================================================================== */

function initScrollAnimations() {
    // Observer pour les animations complexes
    const complexObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Animation spécifique selon le type d'élément
                if (entry.target.classList.contains('tech-item')) {
                    animateTechItem(entry.target);
                }
                
                if (entry.target.classList.contains('sector-card')) {
                    animateSectorCard(entry.target);
                }
                
                if (entry.target.classList.contains('value-item')) {
                    animateValueItem(entry.target);
                }
            }
        });
    }, {
        threshold: 0.2
    });
    
    // Observer les éléments complexes
    document.querySelectorAll('.tech-item, .sector-card, .value-item').forEach(element => {
        complexObserver.observe(element);
    });
}

function animateTechItem(element) {
    element.classList.add('slide-in-right');
    
    // Effet de couleur progressive
    setTimeout(() => {
        element.style.borderColor = 'var(--color-primary)';
        element.style.color = 'var(--color-primary)';
    }, 300);
}

function animateSectorCard(element) {
    element.classList.add('float-element');
    
    // Animation de l'icône
    const icon = element.querySelector('.sector-icon');
    if (icon) {
        icon.style.transform = 'scale(1.2)';
        icon.style.transition = 'transform 0.5s ease';
        
        setTimeout(() => {
            icon.style.transform = 'scale(1)';
        }, 500);
    }
}

function animateValueItem(element) {
    const number = element.querySelector('.value-number');
    
    if (number) {
        // Animation de comptage
        const targetValue = parseInt(number.textContent);
        let currentValue = 0;
        const increment = targetValue / 50;
        const duration = 1000;
        const stepTime = duration / 50;
        
        const timer = setInterval(() => {
            currentValue += increment;
            
            if (currentValue >= targetValue) {
                currentValue = targetValue;
                clearInterval(timer);
            }
            
            number.textContent = Math.round(currentValue);
        }, stepTime);
    }
}

/* ==========================================================================
   Particules et effets visuels
   ========================================================================== */

function initParticles() {
    if (!CONFIG.animationEnabled) return;
    
    const heroSection = document.querySelector('.hero');
    
    if (!heroSection) return;
    
    // Créer des particules
    for (let i = 0; i < 15; i++) {
        createParticle(heroSection);
    }
}

function createParticle(container) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    
    // Position aléatoire
    const size = Math.random() * 4 + 2;
    const posX = Math.random() * 100;
    const posY = Math.random() * 100;
    
    // Style
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    particle.style.left = `${posX}%`;
    particle.style.top = `${posY}%`;
    
    // Opacité aléatoire
    particle.style.opacity = Math.random() * 0.3 + 0.1;
    
    // Durée d'animation aléatoire
    const duration = Math.random() * 10 + 5;
    particle.style.animationDuration = `${duration}s`;
    
    container.appendChild(particle);
    
    // Nettoyer les particules périodiquement
    setTimeout(() => {
        if (particle.parentNode) {
            particle.parentNode.removeChild(particle);
            createParticle(container);
        }
    }, duration * 1000);
}

/* ==========================================================================
   Préférences utilisateur
   ========================================================================== */

function checkUserPreferences() {
    // Vérifier la préférence de réduction de mouvement
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
        CONFIG.animationEnabled = false;
        document.body.classList.add('reduced-motion');
    }
    
    // Vérifier le thème préféré
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (prefersDarkMode) {
        // Option pour un futur mode sombre
        // document.body.classList.add('dark-mode');
    }
}

/* ==========================================================================
   Événements globaux
   ========================================================================== */

function setupGlobalEvents() {
    // Gestion des erreurs
    window.addEventListener('error', function(e) {
        console.error('Erreur JavaScript:', e.error);
    });
    
    // Gestion des promesses non capturées
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Promesse non capturée:', e.reason);
    });
    
    // Mettre à jour les animations lors du redimensionnement
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        
        resizeTimeout = setTimeout(function() {
            updateAnimationsForViewport();
        }, 250);
    });
}

function updateAnimationsForViewport() {
    const isMobile = window.innerWidth < 768;
    
    // Ajuster les animations pour mobile
    if (isMobile) {
        document.body.classList.add('mobile-view');
    } else {
        document.body.classList.remove('mobile-view');
    }
}

/* ==========================================================================
   Utilitaires
   ========================================================================== */

function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.padding = 'var(--space-md) var(--space-lg)';
    notification.style.background = type === 'success' ? 'var(--color-accent-green)' : 'var(--color-primary)';
    notification.style.color = 'var(--color-white)';
    notification.style.borderRadius = 'var(--border-radius-md)';
    notification.style.boxShadow = 'var(--shadow-lg)';
    notification.style.zIndex = 'var(--z-tooltip)';
    notification.style.opacity = '0';
    notification.style.transform = 'translateY(-20px)';
    notification.style.transition = 'all 0.3s ease';
    
    // Ajouter au document
    document.body.appendChild(notification);
    
    // Animation d'entrée
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);
    
    // Supprimer après 5 secondes
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Export pour utilisation globale
window.HarmonicAI = {
    config: CONFIG,
    state: APP_STATE,
    utils: {
        showNotification,
        switchLanguage
    }
};