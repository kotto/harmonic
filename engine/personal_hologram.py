"""
Personal Hologram — L'IA qui te connaît
==========================================
KA ne se contente pas de répondre. Il observe, apprend, et construit
TON hologramme personnel — sans rien te demander.

PILIERS :
  1. OBSERVER — chaque question, correction, domaine → trace
  2. APPRENDRE — construction implicite du profil
  3. COMPRENDRE — détection de tes centres d'intérêt
  4. GUIDER — suggestions proactives, alertes, contradictions

Usage :
    from personal_hologram import PersonalHologram

    ph = PersonalHologram('user_123')
    ph.observe_question('Quel traitement pour le paludisme ?', domain='medecine')
    ph.observe_correction('paludisme causé par froid', 'paludisme causé par Plasmodium')
    
    # Après quelques jours d'usage :
    print(ph.profile())          # → "Expertise: medecine, droit"
    print(ph.suggestions())      # → "Apprends-moi la pharmacologie pour compléter"
    print(ph.contradictions())   # → "⚠️ Tu m'as appris X le 15/03, mais Y le 20/03"
"""

import os, sys, json, time, re, logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Trace:
    """Une trace d'observation."""
    type: str        # 'question', 'correction', 'specialization', 'export', 'health'
    content: str     # le contenu
    domain: str      # domaine détecté
    timestamp: float
    session: str     # identifiant de session


@dataclass
class Interest:
    """Un centre d'intérêt détecté."""
    domain: str
    score: float           # score d'intérêt 0-1
    first_seen: float      # première observation
    last_seen: float       # dernière observation
    question_count: int    # nombre de questions
    corrections_count: int # nombre de corrections
    confidence: float      # confiance de la détection 0-1


@dataclass
class ProactiveSuggestion:
    """Une suggestion proactive de KA."""
    type: str       # 'learn', 'review', 'contradiction', 'complete', 'trend'
    message: str    # message à afficher
    priority: float # 0 (info) à 1 (critique)
    reason: str     # pourquoi cette suggestion


@dataclass 
class HologramProfile:
    """Le profil complet d'un utilisateur."""
    user_id: str
    created_at: float
    last_active: float
    total_questions: int = 0
    total_corrections: int = 0
    total_specializations: int = 0
    sessions: int = 0
    top_domains: List[Interest] = field(default_factory=list)
    top_concepts: List[str] = field(default_factory=list)
    hologram_size: int = 0  # nombre de faits dans le KB personnel
    growth_rate: float = 0.0  # faits/session
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'total_questions': self.total_questions,
            'total_corrections': self.total_corrections,
            'total_specializations': self.total_specializations,
            'sessions': self.sessions,
            'top_domains': [
                {'domain': i.domain, 'score': i.score, 'confidence': i.confidence}
                for i in self.top_domains[:5]
            ],
            'top_concepts': self.top_concepts[:10],
            'hologram_size': self.hologram_size,
            'growth_rate': self.growth_rate,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONAL HOLOGRAM ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class PersonalHologram:
    """
    Moteur de l'hologramme personnel — KA qui te connaît.
    
    Observe passivement, détecte les intérêts, guide proactivement.
    """
    
    def __init__(self, user_id: str = 'anonymous'):
        self.user_id = user_id
        self.users_dir = _ENGINE_DIR / "data" / "users" / user_id
        self.users_dir.mkdir(parents=True, exist_ok=True)
        
        # Traces d'observation
        self.traces: List[Trace] = []
        self._traces_dirty = False
        
        # Session actuelle
        self.session_id = self._new_session_id()
        self.session_start = time.time()
        
        # Charger les données existantes
        self._load()
    
    def _new_session_id(self) -> str:
        return time.strftime('%Y%m%d_%H%M%S')
    
    # ═══ PERSISTANCE ═══
    
    def _load(self):
        trace_path = self.users_dir / 'hologram_traces.json'
        if trace_path.exists():
            try:
                with open(trace_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.traces = [Trace(**t) for t in data.get('traces', [])]
                self.sessions = data.get('sessions', 0) + 1
            except Exception:
                self.traces = []
                self.sessions = 1
        else:
            self.sessions = 1
    
    def _save(self):
        trace_path = self.users_dir / 'hologram_traces.json'
        data = {
            'traces': [
                {
                    'type': t.type, 'content': t.content[:200],
                    'domain': t.domain, 'timestamp': t.timestamp,
                    'session': t.session,
                }
                for t in self.traces[-500:]  # Garder les 500 dernières traces
            ],
            'sessions': self.sessions,
            'user_id': self.user_id,
        }
        with open(trace_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._traces_dirty = False
    
    # ═══ OBSERVATION PASSIVE ═══
    
    def observe(self, obs_type: str, content: str, domain: str = None):
        """
        Enregistre une observation.
        
        Args:
            obs_type: 'question', 'correction', 'specialization', 'page', 'health', 'code'
            content: le contenu de l'observation
            domain: domaine détecté (optionnel, sera auto-détecté si absent)
        """
        if domain is None:
            domain = self._detect_domain(content)
        
        trace = Trace(
            type=obs_type,
            content=content[:300],
            domain=domain or 'unknown',
            timestamp=time.time(),
            session=self.session_id,
        )
        self.traces.append(trace)
        self._traces_dirty = True
        
        # Sauvegarde périodique (toutes les 10 traces)
        if len(self.traces) % 10 == 0:
            self._save()
    
    def observe_question(self, question: str, domain: str = None):
        """KA observe une question posée par l'utilisateur."""
        self.observe('question', question, domain)
    
    def observe_correction(self, wrong: str, correct: str, domain: str = None):
        """KA observe une correction apportée par l'utilisateur."""
        self.observe('correction', f"{wrong} → {correct}", domain)
    
    def observe_specialization(self, domain: str, facts_count: int):
        """KA observe une spécialisation demandée."""
        self.observe('specialization', f"specialisation en {domain} ({facts_count} faits)", domain)
    
    def observe_page(self, topic: str):
        """KA observe la génération d'une page longue."""
        self.observe('page', topic)
    
    def observe_health(self, diagnostic: str):
        """KA observe une consultation santé."""
        self.observe('health', diagnostic[:200])
    
    # ═══ DÉTECTION DES INTÉRÊTS ═══
    
    def _detect_domain(self, text: str) -> Optional[str]:
        """Détecte le domaine d'un texte."""
        try:
            from domain_router import DOMAIN_SIGNATURES
            text_lower = text.lower()
            scores = Counter()
            for domain, sig in DOMAIN_SIGNATURES.items():
                for kw in sig['keywords']:
                    if kw in text_lower:
                        scores[domain] += 1
            if scores:
                return scores.most_common(1)[0][0]
        except ImportError:
            pass
        return None
    
    def detect_interests(self) -> List[Interest]:
        """
        Analyse toutes les traces pour détecter les centres d'intérêt.
        
        Retourne les domaines classés par pertinence.
        """
        if not self.traces:
            return []
        
        now = time.time()
        interests = {}
        
        for t in self.traces:
            if t.domain == 'unknown':
                continue
            
            if t.domain not in interests:
                interests[t.domain] = {
                    'first': t.timestamp,
                    'last': t.timestamp,
                    'questions': 0,
                    'corrections': 0,
                }
            
            data = interests[t.domain]
            data['last'] = t.timestamp
            if t.type == 'question':
                data['questions'] += 1
            elif t.type == 'correction':
                data['corrections'] += 1
        
        result = []
        for domain, data in interests.items():
            age_days = (now - data['first']) / 86400
            recency_days = (now - data['last']) / 86400
            
            # Score basé sur fréquence, récence, et engagement
            frequency = data['questions'] / max(age_days, 1)
            recency = 1.0 / max(recency_days, 0.1)
            engagement = data['corrections'] / max(data['questions'], 1)
            
            score = min(1.0, frequency * 0.4 + recency * 0.1 + engagement * 0.5)
            confidence = min(1.0, data['questions'] / 5)
            
            result.append(Interest(
                domain=domain,
                score=round(score, 2),
                first_seen=data['first'],
                last_seen=data['last'],
                question_count=data['questions'],
                corrections_count=data['corrections'],
                confidence=round(confidence, 2),
            ))
        
        result.sort(key=lambda i: i.score, reverse=True)
        return result
    
    def top_concepts(self, n: int = 10) -> List[str]:
        """Extrait les concepts les plus fréquents des questions."""
        word_counts = Counter()
        for t in self.traces:
            if t.type == 'question':
                words = re.findall(r'[a-zéèêëàâäôöîïûüç]{4,}', t.content.lower())
                for w in words:
                    if w not in {'quelle', 'comment', 'pourquoi', 'quand', 'combien',
                                 'est', 'sont', 'dans', 'avec', 'pour', 'sur', 'plus'}:
                        word_counts[w] += 1
        return [w for w, _ in word_counts.most_common(n)]
    
    # ═══ GUIDANCE PROACTIVE ═══
    
    def suggestions(self) -> List[ProactiveSuggestion]:
        """
        Génère des suggestions proactives basées sur le profil.
        
        Types :
          - 'learn' : suggère d'apprendre un domaine connexe
          - 'review' : suggère de revoir un sujet peu utilisé
          - 'contradiction' : détecte des contradictions dans les corrections
          - 'complete' : suggère de compléter un hologramme partiel
          - 'trend' : signale une tendance dans les questions
        """
        suggestions = []
        interests = self.detect_interests()
        
        if not interests:
            # Nouvel utilisateur : suggestion de bienvenue
            suggestions.append(ProactiveSuggestion(
                type='learn',
                message="👋 Bienvenue ! Dis-moi 'spécialise-toi en [ton domaine]' pour commencer.",
                priority=0.8,
                reason="Nouvel utilisateur — pas encore d'intérêts détectés.",
            ))
            return suggestions
        
        # 1. Suggérer des domaines connexes
        top = interests[0]
        related_domains = self._find_related_domains(top.domain)
        for rd in related_domains[:2]:
            already_known = any(i.domain == rd for i in interests)
            if not already_known:
                suggestions.append(ProactiveSuggestion(
                    type='learn',
                    message=f"📚 Tu t'intéresses à {top.domain}. Veux-tu que j'apprenne aussi {rd} ?",
                    priority=0.5,
                    reason=f"Domaine connexe à {top.domain} non encore exploré.",
                ))
        
        # 2. Détecter les tendances
        recent_traces = [t for t in self.traces if time.time() - t.timestamp < 86400 * 7]
        if recent_traces:
            recent_domains = Counter(t.domain for t in recent_traces if t.domain != 'unknown')
            if recent_domains:
                trending = recent_domains.most_common(1)[0]
                # Vérifier si c'est un nouveau centre d'intérêt
                old_traces = [t for t in self.traces if t.timestamp < time.time() - 86400 * 7]
                old_domains = Counter(t.domain for t in old_traces if t.domain != 'unknown')
                if trending[0] not in old_domains or recent_domains[trending[0]] > old_domains.get(trending[0], 0) * 2:
                    suggestions.append(ProactiveSuggestion(
                        type='trend',
                        message=f"📈 Je remarque que tu t'intéresses de plus en plus à {trending[0]}. "
                                f"Veux-tu que je m'y spécialise ?",
                        priority=0.6,
                        reason=f"Tendance détectée: {trending[0]} en hausse.",
                    ))
        
        # 3. Détecter les contradictions dans les corrections
        contradictions = self._detect_contradictions()
        for contra in contradictions[:2]:
            suggestions.append(ProactiveSuggestion(
                type='contradiction',
                message=f"⚠️ {contra}",
                priority=0.9,
                reason="Contradiction détectée dans les corrections.",
            ))
        
        # 4. Suggérer de compléter les hologrammes partiels
        specializations = [t for t in self.traces if t.type == 'specialization']
        if len(specializations) >= 3:
            specialized_domains = set(t.domain for t in specializations)
            # Domaines connexes non spécialisés
            for interest in interests[:3]:
                if interest.domain not in specialized_domains and interest.confidence > 0.6:
                    suggestions.append(ProactiveSuggestion(
                        type='complete',
                        message=f"🎯 Tu poses beaucoup de questions sur {interest.domain}, "
                                f"mais je n'y suis pas encore spécialisé. Veux-tu que je le fasse ?",
                        priority=0.7,
                        reason=f"Intérêt fort ({interest.confidence:.0%}) sans spécialisation.",
                    ))
        
        return suggestions[:5]  # Max 5 suggestions
    
    def _find_related_domains(self, domain: str) -> List[str]:
        """Trouve des domaines connexes à un domaine."""
        related = {
            'medecine': ['pharmacologie', 'anatomie', 'biologie', 'psychiatrie', 'chirurgie'],
            'droit': ['droit constitutionnel', 'droit pénal', 'droit fiscal', 'droit international'],
            'photographie': ['design graphique', 'vidéo', 'éclairage', 'post-production'],
            'finance': ['comptabilité', 'investissement', 'fiscalité', 'économie'],
            'technologie': ['programmation', 'cybersécurité', 'réseaux', 'data science'],
            'cuisine': ['nutrition', 'oenologie', 'pâtisserie', 'gastronomie'],
            'education': ['pédagogie', 'psychologie cognitive', 'méthodologie', 'formation'],
        }
        return related.get(domain, [])
    
    def _detect_contradictions(self) -> List[str]:
        """Détecte des contradictions potentielles dans les corrections."""
        contradictions = []
        corrections = [t for t in self.traces if t.type == 'correction']
        
        # Comparer les corrections par paires
        for i in range(len(corrections)):
            for j in range(i + 1, len(corrections)):
                ci = corrections[i]
                cj = corrections[j]
                
                # Même domaine, contenu similaire ?
                if ci.domain == cj.domain and ci.domain != 'unknown':
                    words_i = set(ci.content.lower().split())
                    words_j = set(cj.content.lower().split())
                    overlap = words_i & words_j
                    if len(overlap) > 5:
                        # Vérifier si les corrections sont contradictoires
                        ti = time.strftime('%d/%m', time.localtime(ci.timestamp))
                        tj = time.strftime('%d/%m', time.localtime(cj.timestamp))
                        contradictions.append(
                            f"Le {ti}, tu m'as appris que « {ci.content[:50]}... » "
                            f"et le {tj}, « {cj.content[:50]}... ». "
                            f"Ces deux faits semblent contradictoires. Peux-tu clarifier ?"
                        )
                        break
        
        return contradictions[:2]
    
    # ═══ PROFIL ═══
    
    def profile(self) -> HologramProfile:
        """Construit le profil complet de l'utilisateur."""
        interests = self.detect_interests()
        concepts = self.top_concepts()
        
        # Taille de l'hologramme
        holo_size = 0
        try:
            from domain_router import FeedbackEngine
            fb = FeedbackEngine()
            facts = fb.load_user_facts(self.user_id)
            holo_size = len(facts)
        except Exception:
            pass
        
        # Taux de croissance (faits par session)
        growth = holo_size / max(self.sessions, 1)
        
        # Compter les questions, corrections, spécialisations
        questions = sum(1 for t in self.traces if t.type == 'question')
        corrections = sum(1 for t in self.traces if t.type == 'correction')
        specializations = sum(1 for t in self.traces if t.type == 'specialization')
        
        # Première et dernière activité
        first = self.traces[0].timestamp if self.traces else time.time()
        last = self.traces[-1].timestamp if self.traces else time.time()
        
        return HologramProfile(
            user_id=self.user_id,
            created_at=first,
            last_active=last,
            total_questions=questions,
            total_corrections=corrections,
            total_specializations=specializations,
            sessions=self.sessions,
            top_domains=interests[:5],
            top_concepts=concepts[:10],
            hologram_size=holo_size,
            growth_rate=round(growth, 1),
        )
    
    def save(self):
        """Sauvegarde toutes les données."""
        self._save()
        log.info(f"💾 Hologramme personnel sauvé: {len(self.traces)} traces, "
                 f"{len(self.detect_interests())} intérêts")


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  🧬 PERSONAL HOLOGRAM — Démo                             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    ph = PersonalHologram('demo_user')
    
    # Simuler quelques jours d'usage
    print("=== JOUR 1: Découverte ===")
    ph.observe_question('Qui a découvert le radium ?')
    ph.observe_question('Quelle est la capitale du Brésil ?')
    ph.observe_question('Quel traitement pour le paludisme ?', domain='medecine')
    ph.observe_correction('paludisme causé par le froid', 'paludisme causé par Plasmodium', 'medecine')
    ph.observe_specialization('medecine', 119)
    
    print("=== JOUR 2: Usage médical ===")
    ph.observe_question('Symptômes du diabète type 2 ?', domain='medecine')
    ph.observe_question('Posologie paracétamol enfant ?', domain='medecine')
    ph.observe_question('Différence entre virus et bactérie ?', domain='medecine')
    ph.observe_question('Quels sont les effets secondaires de l ibuprofène ?', domain='medecine')
    
    print("=== JOUR 3: Nouveau centre d'intérêt ===")
    ph.observe_question('Code python pour trier une liste', domain='technologie')
    ph.observe_question('Comment fonctionne un algorithme de tri ?', domain='technologie')
    ph.observe_correction('Python est compilé', 'Python est interprété', 'technologie')
    
    # Profil
    print()
    print("="*50)
    print("PROFIL DÉTECTÉ")
    print("="*50)
    profile = ph.profile()
    print(f"  Questions:    {profile.total_questions}")
    print(f"  Corrections:  {profile.total_corrections}")
    print(f"  Spécialisé:   {profile.total_specializations} fois")
    print(f"  Sessions:     {profile.sessions}")
    print(f"  Hologramme:   {profile.hologram_size} faits")
    print()
    print("  Centres d'intérêt:")
    for i in profile.top_domains:
        bar = '█' * int(i.score * 20)
        print(f"    {i.domain:15s} {bar} {i.score:.0%} (confiance: {i.confidence:.0%})")
    
    # Suggestions
    print()
    print("="*50)
    print("SUGGESTIONS PROACTIVES")
    print("="*50)
    for s in ph.suggestions():
        icon = {'learn': '📚', 'review': '🔄', 'contradiction': '⚠️',
                'complete': '🎯', 'trend': '📈'}.get(s.type, '💡')
        print(f"  {icon} [{s.priority:.0%}] {s.message}")
    
    ph.save()
    print()
    print("✅ Hologramme personnel opérationnel !")
