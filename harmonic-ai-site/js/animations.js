/* ==========================================================================
   Harmonic AI - Animations JavaScript
   Effets interactifs avancés et animations fluides
   ========================================================================== */

// Gestionnaire d'animations
class AnimationManager {
    constructor() {
        this.animations = new Map();
        this.activeAnimations = new Set();
        this.rafId = null;
        this.lastTime = 0;
        
        // Configuration
        this.config = {
            fps: 60,
            maxParticles: 100,
            particleLifetime: 5000,
            enablePhysics: true
        };
    }
    
    // Initialiser le gestionnaire
    init() {
        console.log('Animation Manager initialisé');
        this.setupEventListeners();
        this.startAnimationLoop();
    }
    
    // Démarrer la boucle d'animation
    startAnimationLoop() {
        const animate = (currentTime) => {
            this.rafId = requestAnimationFrame(animate);
            
            const deltaTime = currentTime - this.lastTime;
            this.lastTime = currentTime;
            
            // Mettre à jour toutes les animations actives
            this.updateAnimations(deltaTime);
        };
        
        this.rafId = requestAnimationFrame(animate);
    }
    
    // Arrêter la boucle d'animation
    stopAnimationLoop() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
    }
    
    // Mettre à jour les animations
    updateAnimations(deltaTime) {
        this.activeAnimations.forEach(animationId => {
            const animation = this.animations.get(animationId);
            if (animation && animation.update) {
                animation.update(deltaTime);
            }
        });
    }
    
    // Ajouter une animation
    addAnimation(id, animation) {
        this.animations.set(id, animation);
        this.activeAnimations.add(id);
        
        if (animation.init) {
            animation.init();
        }
        
        console.log(`Animation ajoutée: ${id}`);
    }
    
    // Supprimer une animation
    removeAnimation(id) {
        const animation = this.animations.get(id);
        
        if (animation && animation.destroy) {
            animation.destroy();
        }
        
        this.animations.delete(id);
        this.activeAnimations.delete(id);
        
        console.log(`Animation supprimée: ${id}`);
    }
    
    // Configurer les écouteurs d'événements
    setupEventListeners() {
        // Gérer la visibilité de la page
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAnimations();
            } else {
                this.resumeAnimations();
            }
        });
        
        // Gérer le redimensionnement
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }
    
    // Mettre en pause les animations
    pauseAnimations() {
        this.activeAnimations.forEach(animationId => {
            const animation = this.animations.get(animationId);
            if (animation && animation.pause) {
                animation.pause();
            }
        });
    }
    
    // Reprendre les animations
    resumeAnimations() {
        this.activeAnimations.forEach(animationId => {
            const animation = this.animations.get(animationId);
            if (animation && animation.resume) {
                animation.resume();
            }
        });
    }
    
    // Gérer le redimensionnement
    handleResize() {
        this.animations.forEach(animation => {
            if (animation && animation.onResize) {
                animation.onResize();
            }
        });
    }
}

// Animation de gradient harmonique
class HarmonicGradientAnimation {
    constructor(element) {
        this.element = element;
        this.angle = 0;
        this.speed = 0.5;
        this.colors = [
            '#1a237e', // Primary
            '#534bae', // Primary Light
            '#7b1fa2', // Accent Purple
            '#ff6f00', // Secondary
            '#ffa040'  // Secondary Light
        ];
    }
    
    init() {
        if (!this.element) return;
        
        // Appliquer le gradient initial
        this.updateGradient();
        
        // Démarrer l'animation
        this.startTime = Date.now();
    }
    
    update(deltaTime) {
        this.angle += this.speed * (deltaTime / 1000);
        
        if (this.angle >= 360) {
            this.angle = 0;
        }
        
        this.updateGradient();
    }
    
    updateGradient() {
        const gradient = `linear-gradient(${this.angle}deg, ${this.colors.join(', ')})`;
        this.element.style.backgroundImage = gradient;
    }
    
    pause() {
        this.speed = 0;
    }
    
    resume() {
        this.speed = 0.5;
    }
    
    destroy() {
        this.element.style.backgroundImage = '';
    }
}

// Animation de particules
class ParticleSystem {
    constructor(container, options = {}) {
        this.container = container;
        this.particles = [];
        this.options = {
            count: options.count || 30,
            size: options.size || { min: 1, max: 4 },
            speed: options.speed || { min: 0.5, max: 2 },
            colors: options.colors || ['#1a237e', '#ff6f00', '#7b1fa2'],
            lifetime: options.lifetime || 5000,
            ...options
        };
        
        this.canvas = null;
        this.ctx = null;
        this.width = 0;
        this.height = 0;
    }
    
    init() {
        // Créer le canvas
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'particle-canvas';
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '1';
        
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        
        // Initialiser les dimensions
        this.resize();
        
        // Créer les particules
        this.createParticles();
    }
    
    createParticles() {
        for (let i = 0; i < this.options.count; i++) {
            this.particles.push(this.createParticle());
        }
    }
    
    createParticle() {
        const color = this.options.colors[
            Math.floor(Math.random() * this.options.colors.length)
        ];
        
        return {
            x: Math.random() * this.width,
            y: Math.random() * this.height,
            size: Math.random() * (this.options.size.max - this.options.size.min) + this.options.size.min,
            speedX: (Math.random() - 0.5) * 2 * this.options.speed.max,
            speedY: (Math.random() - 0.5) * 2 * this.options.speed.max,
            color: color,
            opacity: Math.random() * 0.5 + 0.1,
            createdAt: Date.now(),
            lifetime: Math.random() * this.options.lifetime + 3000
        };
    }
    
    update(deltaTime) {
        // Effacer le canvas
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        const currentTime = Date.now();
        
        // Mettre à jour et dessiner chaque particule
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const particle = this.particles[i];
            
            // Vérifier la durée de vie
            if (currentTime - particle.createdAt > particle.lifetime) {
                this.particles.splice(i, 1);
                this.particles.push(this.createParticle());
                continue;
            }
            
            // Mettre à jour la position
            particle.x += particle.speedX * (deltaTime / 16);
            particle.y += particle.speedY * (deltaTime / 16);
            
            // Rebond sur les bords
            if (particle.x < 0 || particle.x > this.width) {
                particle.speedX *= -1;
            }
            
            if (particle.y < 0 || particle.y > this.height) {
                particle.speedY *= -1;
            }
            
            // Dessiner la particule
            this.drawParticle(particle);
        }
    }
    
    drawParticle(particle) {
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        this.ctx.fillStyle = particle.color;
        this.ctx.globalAlpha = particle.opacity;
        this.ctx.fill();
        this.ctx.globalAlpha = 1;
    }
    
    resize() {
        const rect = this.container.getBoundingClientRect();
        this.width = rect.width;
        this.height = rect.height;
        
        if (this.canvas) {
            this.canvas.width = this.width;
            this.canvas.height = this.height;
        }
    }
    
    onResize() {
        this.resize();
    }
    
    destroy() {
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        
        this.particles = [];
    }
}

// Animation de texte défilant
class ScrollingTextAnimation {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            speed: options.speed || 50,
            direction: options.direction || 'left',
            pauseOnHover: options.pauseOnHover || true,
            ...options
        };
        
        this.scrollPosition = 0;
        this.isPaused = false;
        this.clone = null;
    }
    
    init() {
        if (!this.element) return;
        
        // Créer un clone du contenu pour un défilement continu
        this.createClone();
        
        // Configurer le conteneur
        this.setupContainer();
        
        // Démarrer l'animation
        this.startTime = Date.now();
    }
    
    createClone() {
        this.clone = this.element.cloneNode(true);
        this.clone.className = 'scrolling-text-clone';
        this.element.parentNode.appendChild(this.clone);
    }
    
    setupContainer() {
        const container = this.element.parentNode;
        container.style.position = 'relative';
        container.style.overflow = 'hidden';
        container.style.whiteSpace = 'nowrap';
        
        this.element.style.display = 'inline-block';
        this.clone.style.display = 'inline-block';
        
        // Événement de survol
        if (this.options.pauseOnHover) {
            container.addEventListener('mouseenter', () => this.pause());
            container.addEventListener('mouseleave', () => this.resume());
        }
    }
    
    update(deltaTime) {
        if (this.isPaused) return;
        
        // Calculer le déplacement
        const movement = this.options.speed * (deltaTime / 1000);
        
        if (this.options.direction === 'left') {
            this.scrollPosition -= movement;
        } else {
            this.scrollPosition += movement;
        }
        
        // Réinitialiser la position si nécessaire
        const elementWidth = this.element.offsetWidth;
        
        if (Math.abs(this.scrollPosition) >= elementWidth) {
            this.scrollPosition = 0;
        }
        
        // Appliquer la transformation
        this.element.style.transform = `translateX(${this.scrollPosition}px)`;
        this.clone.style.transform = `translateX(${this.scrollPosition + elementWidth}px)`;
    }
    
    pause() {
        this.isPaused = true;
    }
    
    resume() {
        this.isPaused = false;
    }
    
    destroy() {
        if (this.clone && this.clone.parentNode) {
            this.clone.parentNode.removeChild(this.clone);
        }
        
        this.element.style.transform = '';
    }
}

// Animation de compteur numérique
class CounterAnimation {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            startValue: options.startValue || 0,
            endValue: options.endValue || 100,
            duration: options.duration || 2000,
            format: options.format || 'number',
            suffix: options.suffix || '',
            prefix: options.prefix || '',
            ...options
        };
        
        this.currentValue = this.options.startValue;
        this.startTime = null;
        this.isAnimating = false;
    }
    
    init() {
        // Initialiser l'affichage
        this.updateDisplay();
    }
    
    start() {
        if (this.isAnimating) return;
        
        this.isAnimating = true;
        this.startTime = Date.now();
        this.currentValue = this.options.startValue;
        
        // Démarrer la boucle d'animation
        this.animate();
    }
    
    animate() {
        if (!this.isAnimating) return;
        
        const currentTime = Date.now();
        const elapsed = currentTime - this.startTime;
        const progress = Math.min(elapsed / this.options.duration, 1);
        
        // Fonction d'easing
        const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4);
        const easedProgress = easeOutQuart(progress);
        
        // Calculer la valeur actuelle
        this.currentValue = this.options.startValue + 
            (this.options.endValue - this.options.startValue) * easedProgress;
        
        // Mettre à jour l'affichage
        this.updateDisplay();
        
        // Continuer l'animation si nécessaire
        if (progress < 1) {
            requestAnimationFrame(() => this.animate());
        } else {
            this.isAnimating = false;
        }
    }
    
    updateDisplay() {
        let displayValue;
        
        switch (this.options.format) {
            case 'percent':
                displayValue = `${Math.round(this.currentValue)}%`;
                break;
            case 'currency':
                displayValue = `$${Math.round(this.currentValue).toLocaleString()}`;
                break;
            case 'compact':
                displayValue = this.formatCompact(this.currentValue);
                break;
            default:
                displayValue = Math.round(this.currentValue).toLocaleString();
        }
        
        this.element.textContent = `${this.options.prefix}${displayValue}${this.options.suffix}`;
    }
    
    formatCompact(value) {
        if (value >= 1000000) {
            return `${(value / 1000000).toFixed(1)}M`;
        } else if (value >= 1000) {
            return `${(value / 1000).toFixed(1)}K`;
        }
        return Math.round(value).toString();
    }
    
    pause() {
        this.isAnimating = false;
    }
    
    resume() {
        if (this.startTime) {
            this.startTime = Date.now() - (Date.now() - this.startTime);
            this.animate();
        }
    }
    
    destroy() {
        this.isAnimating = false;
        this.element.textContent = '';
    }
}

// Animation de morphing de forme
class ShapeMorphAnimation {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            shapes: options.shapes || [
                '30% 70% 70% 30% / 30% 30% 70% 70%',
                '58% 42% 75% 25% / 76% 46% 54% 24%',
                '50% 50% 33% 67% / 55% 27% 73% 45%',
                '33% 67% 58% 42% / 63% 68% 32% 37%'
            ],
            duration: options.duration || 20000,
            ...options
        };
        
        this.currentShapeIndex = 0;
        this.progress = 0;
        this.isAnimating = false;
    }
    
    init() {
        // Appliquer la forme initiale
        this.applyShape(this.options.shapes[0]);
        
        // Démarrer l'animation
        this.start();
    }
    
    start() {
        if (this.isAnimating) return;
        
        this.isAnimating = true;
        this.startTime = Date.now();
        this.animate();
    }
    
    animate() {
        if (!this.isAnimating) return;
        
        const currentTime = Date.now();
        const elapsed = currentTime - this.startTime;
        const shapeDuration = this.options.duration / this.options.shapes.length;
        
        this.currentShapeIndex = Math.floor(elapsed / shapeDuration) % this.options.shapes.length;
        this.progress = (elapsed % shapeDuration) / shapeDuration;
        
        // Interpolation entre les formes
        const nextShapeIndex = (this.currentShapeIndex + 1) % this.options.shapes.length;
        const interpolatedShape = this.interpolateShapes(
            this.options.shapes[this.currentShapeIndex],
            this.options.shapes[nextShapeIndex],
            this.progress
        );
        
        // Appliquer la forme interpolée
        this.applyShape(interpolatedShape);
        
        // Continuer l'animation
        requestAnimationFrame(() => this.animate());
    }
    
    interpolateShapes(shapeA, shapeB, progress) {
        // Extraire les valeurs des formes
        const valuesA = shapeA.match(/\d+/g).map(Number);
        const valuesB = shapeB.match(/\d+/g).map(Number);
        
        // Interpoler chaque valeur
        const interpolatedValues = valuesA.map((value, index) => {
            return value + (valuesB[index] - value) * progress;
        });
        
        // Reconstruire la chaîne de forme
        return `${interpolatedValues[0]}% ${interpolatedValues[1]}% ${interpolatedValues[2]}% ${interpolatedValues[3]}% / ${interpolatedValues[4]}% ${interpolatedValues[5]}% ${interpolatedValues[6]}% ${interpolatedValues[7]}%`;
    }
    
    applyShape(shape) {
        this.element.style.borderRadius = shape;
    }
    
    pause() {
        this.isAnimating = false;
    }
    
    resume() {
        this.isAnimating = true;
        this.startTime = Date.now() - this.progress * (this.options.duration / this.options.shapes.length);
        this.animate();
    }
    
    destroy() {
        this.isAnimating = false;
        this.element.style.borderRadius = '';
    }
}

// Initialisation globale des animations
function initAdvancedAnimations() {
    // Créer le gestionnaire d'animations
    const animationManager = new AnimationManager();
    animationManager.init();
    
    // Ajouter les animations spécifiques
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        // Gradient harmonique
        const gradientAnim = new HarmonicGradientAnimation(heroSection);
        animationManager.addAnimation('hero-gradient', gradientAnim);
        
        // Système de particules
        const particleSystem = new ParticleSystem(heroSection, {
            count: 25,
            size: { min: 1, max: 3 },
            speed: { min: 0.3, max: 1.5 }
        });
        animationManager.addAnimation('hero-particles', particleSystem);
    }
    
    // Animation des compteurs
    document.querySelectorAll('.value-number').forEach((element, index) => {
        const endValue = parseInt(element.textContent);
        const counter = new CounterAnimation(element, {
            startValue: 0,
            endValue: endValue,
            duration: 1500 + index * 300,
            format: 'number'
        });
        
        animationManager.addAnimation(`counter-${index}`, counter);
        
        // Démarrer l'animation quand l'élément est visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    counter.start();
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        observer.observe(element);
    });
    
    // Animation de morphing pour les éléments décoratifs
    document.querySelectorAll('.morph-shape').forEach((element, index) => {
        const morphAnim = new ShapeMorphAnimation(element, {
            duration: 20000 + index * 5000
        });
        
        animationManager.addAnimation(`morph-${index}`, morphAnim);
    });
    
    // Exporter le gestionnaire pour une utilisation globale
    window.HarmonicAI.animations = animationManager;
    
    console.log('Animations avancées initialisées');
}

// Initialiser quand le DOM est chargé
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAdvancedAnimations);
} else {
    initAdvancedAnimations();
}