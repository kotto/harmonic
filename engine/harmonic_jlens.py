"""
Harmonic J-Lens — Visualisation de l'Espace de Raisonnement
=============================================================
Inspiré de la découverte d'Anthropic (Juillet 2026) : J-space, une zone
émergente dans Claude où les concepts « pensés mais non dits » résident.

Notre version est EXPLICITE et MATHÉMATIQUE — pas émergente.

PRINCIPE :
  J-space = le sous-espace de C^512 où ψ_question et ψ_facts interfèrent
  constructivement. C'est notre « ConscientFilter » rendu visible.

PROPRIÉTÉS MIROIR (Anthropic → Harmonique) :
  1. Verbal Report      → Decoding ψ_J → langage
  2. Directed Modulation → ψ_context += α·Σ coh·ψ_fact
  3. Internal Reasoning  → PhaseAmplifier propagation
  4. Flexible Generalization → Secteurs (24 × 15°)
  5. Selectivity (<10%)  → ConsciousFilter (~10 faits)

Usage :
    from harmonic_jlens import JLens

    jlens = JLens()
    ai = HarmonicAI()
    ai.attach_jlens(jlens)

    ai.ask("Explique la photosynthèse")
    jlens.render()  # → visualisation ASCII de J-space
    jlens.to_html() # → visualisation HTML interactive
"""

import math, time, json, logging
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field

import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES DE VISUALISATION
# ═══════════════════════════════════════════════════════════════════════════════

# Couleurs par secteur (24 secteurs → 24 teintes)
SECTOR_COLORS = {
    'PHYSIQUE_FOND':  '#FF6B6B', 'PHYSIQUE_APPLI': '#FF8E8E',
    'MATHS_PURES':    '#4ECDC4', 'MATHS_APPLI':    '#7EDDD6',
    'BIOLOGIE':       '#45B7D1', 'ECOLOGIE':       '#96E6A1',
    'CONSCIENCE':     '#DDA0DD', 'INTELLIGENCE':   '#BB8FCE',
    'EMOTION_POS':    '#F9CA24', 'EMOTION_NEG':    '#FFA502',
    'ASTRONOMIE':     '#6C5CE7', 'COSMOLOGIE':     '#A29BFE',
    'HISTOIRE':       '#FD79A8', 'FUTUR':          '#E84393',
    'CULTURE':        '#FDCB6E', 'POLITIQUE':      '#E17055',
    'CREATION':       '#00B894', 'EXPRESSION':     '#55EFC4',
    'NATURE_ANIM':    '#00CEC9', 'NATURE_VEGET':   '#81ECEC',
    'CORPS_ORGANES':  '#FF7675', 'CORPS_SENS':     '#FAB1A0',
    'METAPHYSIQUE':   '#636E72', 'SPIRITUALITE':   '#B2BEC3',
    'SANTE':          '#E74C3C', 'TECHNOLOGIE':    '#3498DB',
    'ECONOMIE':       '#2ECC71', 'GEOGRAPHIE':     '#1ABC9C',
    'GENERAL':        '#95A5A6', 'SFT':            '#F1C40F',
}

# Secteurs simplifiés (12 domaines) pour l'affichage compact
DOMAIN_COLORS = {
    'PHYSIQUE':  '#FF6B6B', 'MATHS':     '#4ECDC4', 'BIOLOGIE': '#45B7D1',
    'CONSCIENCE':'#DDA0DD', 'EMOTION':   '#F9CA24', 'ASTRONOMIE':'#6C5CE7',
    'HISTOIRE': '#FD79A8', 'CULTURE':   '#FDCB6E', 'NATURE':   '#00CEC9',
    'CORPS':    '#FF7675', 'PHILOSOPHIE':'#636E72', 'SANTE':    '#E74C3C',
    'TECH':     '#3498DB', 'ECONOMIE':  '#2ECC71', 'GEO':      '#1ABC9C',
    'GENERAL':  '#95A5A6', 'SFT':       '#F1C40F',
}

def _sector_to_domain(sector: str) -> str:
    """Mappe un secteur à son domaine parent."""
    mapping = {
        'PHYSIQUE_FOND':'PHYSIQUE','PHYSIQUE_APPLI':'PHYSIQUE',
        'MATHS_PURES':'MATHS','MATHS_APPLI':'MATHS',
        'BIOLOGIE':'BIOLOGIE','ECOLOGIE':'BIOLOGIE',
        'CONSCIENCE':'CONSCIENCE','INTELLIGENCE':'CONSCIENCE',
        'EMOTION_POS':'EMOTION','EMOTION_NEG':'EMOTION',
        'ASTRONOMIE':'ASTRONOMIE','COSMOLOGIE':'ASTRONOMIE',
        'HISTOIRE':'HISTOIRE','FUTUR':'HISTOIRE',
        'CULTURE':'CULTURE','POLITIQUE':'CULTURE',
        'CREATION':'CULTURE','EXPRESSION':'CULTURE',
        'NATURE_ANIM':'NATURE','NATURE_VEGET':'NATURE',
        'CORPS_ORGANES':'CORPS','CORPS_SENS':'CORPS',
        'METAPHYSIQUE':'PHILOSOPHIE','SPIRITUALITE':'PHILOSOPHIE',
        'SANTE':'SANTE','TECHNOLOGIE':'TECH',
        'ECONOMIE':'ECONOMIE','GEOGRAPHIE':'GEO',
        'GENERAL':'GENERAL','SFT':'SFT',
    }
    return mapping.get(sector, 'GENERAL')


# ═══════════════════════════════════════════════════════════════════════════════
# J-SPACE ENTRY
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class JEntry:
    """Un concept actif dans J-space à un instant donné."""
    concept: str           # le concept (sujet ou objet du fait)
    sector: str            # secteur harmonique
    domain: str            # domaine parent
    coherence: float       # cohérence avec ψ_question (0-1)
    amplitude: float       # amplitude dans le cerveau
    role: str              # 'subject', 'object', 'relation', 'inferred'
    timestamp: float = 0.0


@dataclass
class JSnapshot:
    """Un instantané complet de J-space."""
    question: str
    psi_question: Optional[np.ndarray]
    entries: List[JEntry] = field(default_factory=list)
    psi_context: Optional[np.ndarray] = None
    confidence: float = 0.0
    response_preview: str = ''
    timestamp: float = 0.0
    
    @property
    def active_concepts(self) -> List[str]:
        return [e.concept for e in self.entries[:10]]
    
    @property
    def domain_distribution(self) -> Counter:
        return Counter(e.domain for e in self.entries)
    
    @property
    def mean_coherence(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.coherence for e in self.entries) / len(self.entries)
    
    @property
    def jspace_size(self) -> int:
        """Nombre de concepts actifs (> seuil)."""
        return sum(1 for e in self.entries if e.coherence > 0.5)


# ═══════════════════════════════════════════════════════════════════════════════
# J-LENS PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class JLens:
    """
    Harmonic J-Lens — Visualise l'espace de raisonnement en direct.
    
    Capture les ψ à chaque étape du pipeline harmonique et les projette
    dans un espace lisible, comme le J-lens d'Anthropic mais mathématique.
    """
    
    def __init__(self, dim: int = 512, history_size: int = 20):
        self.dim = dim
        self.history: List[JSnapshot] = []
        self.history_size = history_size
        self.current: Optional[JSnapshot] = None
        
        # Compteurs pour les stats
        self.total_questions = 0
        self.total_facts_observed = 0
        self.domain_activation = Counter()
    
    # ═══ CAPTURE ═══
    
    def capture(self, question: str, psi_q: Optional[np.ndarray] = None,
                facts: List[Tuple] = None, psi_context: Optional[np.ndarray] = None,
                confidence: float = 0.0, response: str = ''):
        """
        Capture un instantané de J-space.
        
        Args:
            question: la question posée
            psi_q: le vecteur ψ de la question (C^512)
            facts: liste de (sujet, relation, objet, secteur, score)
            psi_context: le vecteur ψ du contexte accumulé
            confidence: score de confiance
            response: début de la réponse
        """
        self.total_questions += 1
        
        snapshot = JSnapshot(
            question=question,
            psi_question=psi_q,
            psi_context=psi_context,
            confidence=confidence,
            response_preview=response[:120] if response else '',
            timestamp=time.time(),
        )
        
        if facts:
            for fact in facts:
                if len(fact) >= 4:
                    s, r, o, sec = fact[0], fact[1], fact[2], fact[3]
                    score = fact[4] if len(fact) >= 5 else 0.5
                    
                    # Calculer la cohérence si ψ_q est disponible
                    coh = score if psi_q is None else min(1.0, score)
                    
                    domain = _sector_to_domain(str(sec))
                    
                    # Ajouter le sujet comme entrée J-space
                    if str(s).strip():
                        snapshot.entries.append(JEntry(
                            concept=str(s)[:60], sector=str(sec), domain=domain,
                            coherence=coh, amplitude=score, role='subject',
                            timestamp=time.time()
                        ))
                    
                    # Ajouter l'objet comme entrée J-space
                    if str(o).strip() and str(o).strip() != str(s).strip():
                        snapshot.entries.append(JEntry(
                            concept=str(o)[:60], sector=str(sec), domain=domain,
                            coherence=coh * 0.8, amplitude=score * 0.8, role='object',
                            timestamp=time.time()
                        ))
                    
                    self.domain_activation[domain] += coh
        
        # Trier par cohérence
        snapshot.entries.sort(key=lambda e: e.coherence, reverse=True)
        
        self.current = snapshot
        self.history.append(snapshot)
        self.total_facts_observed += len(snapshot.entries)
        
        # Limiter l'historique
        if len(self.history) > self.history_size:
            self.history = self.history[-self.history_size:]
    
    # ═══ RENDU ASCII ═══
    
    def render(self, width: int = 70) -> str:
        """
        Rendu ASCII de J-space.
        Affiche les concepts actifs, leurs secteurs, et les patterns d'interférence.
        """
        if not self.current:
            return "J-Space: aucun instantané capturé."
        
        snap = self.current
        lines = []
        
        # En-tête
        lines.append("╔" + "═" * (width - 2) + "╗")
        title = f" J-SPACE HARMONIQUE — '{snap.question[:40]}'"
        lines.append("║" + title.ljust(width - 2) + "║")
        lines.append("╠" + "═" * (width - 2) + "╣")
        
        # Stats
        lines.append("║  {:48s} ║".format(
            f"Concepts actifs: {snap.jspace_size} | Cohérence: {snap.mean_coherence:.2f} | Confiance: {snap.confidence:.2f}"
        ))
        lines.append("╠" + "─" * (width - 2) + "╣")
        
        # Domaines actifs (barre horizontale)
        domains = snap.domain_distribution
        if domains:
            max_d = max(domains.values())
            bar_line = "║ Domaines: "
            for domain, count in domains.most_common(8):
                bar_len = max(1, int(10 * count / max_d))
                color_code = DOMAIN_COLORS.get(domain, '#999')
                bar_line += f"[{domain[:4]}:{'█' * bar_len}] "
            lines.append(bar_line.ljust(width - 2) + "║")
        
        lines.append("╠" + "─" * (width - 2) + "╣")
        
        # Top concepts actifs
        lines.append("║ TOP 10 — CONCEPTS EN J-SPACE:" + " " * (width - 28) + "║")
        for i, entry in enumerate(snap.entries[:10]):
            coh_bar = '█' * int(entry.coherence * 20)
            coh_spc = ' ' * (20 - int(entry.coherence * 20))
            role_icon = {'subject': 'S', 'object': 'O', 'relation': 'R', 'inferred': 'I'}.get(entry.role, '?')
            concept = entry.concept[:35]
            domain = entry.domain[:6]
            lines.append("║ {:2d}. [{:1s}] {:35s} |{:20s}| {:6s} ║".format(
                i + 1, role_icon, concept, coh_bar, domain
            ))
        
        # Interférence pattern
        if snap.jspace_size >= 2:
            lines.append("╠" + "─" * (width - 2) + "╣")
            lines.append("║ INTERFÉRENCES:" + " " * (width - 16) + "║")
            entries = snap.entries[:8]
            for i in range(min(3, len(entries) - 1)):
                e1, e2 = entries[i], entries[i + 1]
                interference = e1.coherence * e2.coherence
                if e1.domain == e2.domain:
                    pattern = "CONSTRUCTIVE ⟹ RENFORCEMENT"
                elif interference > 0.3:
                    pattern = "CROISÉE ⟹ CRÉATIVITÉ"
                else:
                    pattern = "FAIBLE"
                lines.append("║  {:20s} × {:20s} → {} ║".format(
                    e1.concept[:20], e2.concept[:20], pattern
                ))
        
        # Réponse preview
        if snap.response_preview:
            lines.append("╠" + "─" * (width - 2) + "╣")
            lines.append("║ RÉPONSE:" + " " * (width - 11) + "║")
            preview = snap.response_preview[:width - 6]
            lines.append("║  {} ║".format(preview))
        
        lines.append("╚" + "═" * (width - 2) + "╝")
        
        return '\n'.join(lines)
    
    # ═══ RENDU HTML ═══
    
    def to_html(self) -> str:
        """Rendu HTML interactif de J-space avec couleurs sectorielles."""
        if not self.current:
            return "<p>J-Space: aucun instantané.</p>"
        
        snap = self.current
        
        # Construire les entrées J-space
        entries_html = ''
        for i, e in enumerate(snap.entries[:15]):
            color = SECTOR_COLORS.get(e.sector, '#95A5A6')
            coh_pct = int(e.coherence * 100)
            entries_html += f'''
            <div style="display:flex;align-items:center;margin:4px 0;padding:6px;
                        background:rgba(255,255,255,0.03);border-radius:6px;">
              <span style="color:{color};font-weight:bold;min-width:60px;">[{e.domain[:6]}]</span>
              <span style="flex:1;color:#e0e0e0;">{e.concept[:50]}</span>
              <span style="color:#888;min-width:40px;text-align:right;">{e.role[:1]}</span>
              <div style="width:100px;height:8px;background:#333;border-radius:4px;margin-left:8px;">
                <div style="width:{coh_pct}%;height:100%;background:{color};border-radius:4px;"></div>
              </div>
              <span style="color:#888;min-width:40px;text-align:right;">{coh_pct}%</span>
            </div>'''
        
        # Distribution des domaines
        domains = snap.domain_distribution
        max_d = max(domains.values()) if domains else 1
        domain_bars = ''
        for domain, count in domains.most_common(10):
            pct = int(100 * count / max_d)
            color = DOMAIN_COLORS.get(domain, '#999')
            domain_bars += f'''
            <div style="display:flex;align-items:center;margin:2px 0;">
              <span style="color:{color};min-width:70px;">{domain}</span>
              <div style="flex:1;height:12px;background:#222;border-radius:6px;">
                <div style="width:{pct}%;height:100%;background:{color};border-radius:6px;"></div>
              </div>
              <span style="color:#888;margin-left:8px;">{count}</span>
            </div>'''
        
        # Historique
        history_html = ''
        for h in self.history[-8:]:
            active = h.jspace_size
            coh = h.mean_coherence
            color = '#4ECDC4' if coh > 0.5 else '#F9CA24' if coh > 0.3 else '#FF6B6B'
            history_html += f'''
            <div style="display:flex;align-items:center;margin:2px 0;font-size:12px;">
              <span style="color:#888;min-width:80px;">{time.strftime('%H:%M:%S', time.localtime(h.timestamp))}</span>
              <span style="color:{color};">{'█' * min(20, active)}{'░' * max(0, 20-active)}</span>
              <span style="color:#ccc;margin-left:8px;flex:1;">{h.question[:40]}</span>
              <span style="color:#888;">coh={coh:.2f}</span>
            </div>'''
        
        return f'''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>J-Space Harmonique</title>
<style>
  body {{ font-family:'Segoe UI',sans-serif; background:#0a0a1a; color:#e0e0e0;
         max-width:800px; margin:0 auto; padding:20px; }}
  .card {{ background:#111133; border:1px solid #222244; border-radius:12px;
          padding:16px; margin:12px 0; }}
  h2 {{ color:#c9a0dc; margin:0 0 8px 0; font-size:18px; }}
  .stat {{ display:inline-block; background:#1a1a3a; padding:8px 14px;
          border-radius:8px; margin:4px; text-align:center; }}
  .stat-value {{ font-size:24px; font-weight:bold; color:#c9a0dc; }}
  .stat-label {{ font-size:11px; color:#888; }}
</style>
</head>
<body>

<h1 style="color:#f0e6ff;text-align:center;">🌊 J-Space Harmonique</h1>
<p style="text-align:center;color:#888;">
  Inspiré du J-lens d'Anthropic — version ondulatoire explicite
</p>

<div class="card">
  <h2>📊 Session</h2>
  <div class="stat"><div class="stat-value">{self.total_questions}</div><div class="stat-label">questions</div></div>
  <div class="stat"><div class="stat-value">{self.total_facts_observed}</div><div class="stat-label">faits observés</div></div>
  <div class="stat"><div class="stat-value">{snap.jspace_size}</div><div class="stat-label">en J-space</div></div>
  <div class="stat"><div class="stat-value">{snap.mean_coherence:.2f}</div><div class="stat-label">cohérence</div></div>
</div>

<div class="card">
  <h2>🧠 Question: {snap.question[:60]}</h2>
  <div style="margin:8px 0;color:#888;">Réponse: {snap.response_preview[:100]}...</div>
</div>

<div class="card">
  <h2>🎯 Concepts Actifs en J-Space</h2>
  {entries_html}
</div>

<div class="card">
  <h2>📈 Domaines Activés</h2>
  {domain_bars}
</div>

<div class="card">
  <h2>⏱️ Historique J-Space</h2>
  {history_html}
</div>

<p style="text-align:center;color:#555;font-size:11px;">
  J-Space Harmonique · Construit sur C⁵¹² · ψ = Σ H_n · (ψ₁)^n
</p>

</body>
</html>'''
    
    # ═══ STATS ═══
    
    def stats(self) -> dict:
        return {
            'total_questions': self.total_questions,
            'total_facts_observed': self.total_facts_observed,
            'current_jspace_size': self.current.jspace_size if self.current else 0,
            'mean_coherence': self.current.mean_coherence if self.current else 0,
            'top_domains': self.domain_activation.most_common(5),
            'history_size': len(self.history),
        }
    
    def __repr__(self) -> str:
        s = self.stats()
        return (f"JLens(q={s['total_questions']}, J={s['current_jspace_size']}, "
                f"coh={s['mean_coherence']:.2f})")


# ═══════════════════════════════════════════════════════════════════════════════
# INTÉGRATION AVEC HARMONIC AI
# ═══════════════════════════════════════════════════════════════════════════════

def attach_to_harmonic_ai(ai, jlens: JLens = None):
    """
    Attache un JLens à une instance HarmonicAI.
    Monkey-patch ask() et page() pour capturer J-space.
    """
    if jlens is None:
        jlens = JLens()
    
    original_ask = ai.ask
    original_page = ai.page
    
    def ask_with_jlens(question: str) -> str:
        response = original_ask(question)
        
        # Capturer les faits utilisés
        try:
            from page_forge import _FAST_RETRIEVER
            if _FAST_RETRIEVER:
                results = _FAST_RETRIEVER.retrieve(question, max_facts=10, min_score=0.3)
                facts = [(s, r, o, sec, score) for s, r, o, sec, score in results[:10]]
                jlens.capture(question, facts=facts, response=response[:200] if response else '')
        except Exception:
            jlens.capture(question, response=response[:200] if response else '')
        
        return response
    
    def page_with_jlens(topic: str, doc_type: str = 'article') -> str:
        response = original_page(topic, doc_type)
        try:
            from page_forge import _FAST_RETRIEVER
            if _FAST_RETRIEVER:
                results = _FAST_RETRIEVER.retrieve(topic, max_facts=15, min_score=0.2)
                facts = [(s, r, o, sec, score) for s, r, o, sec, score in results[:15]]
                jlens.capture(topic, facts=facts, response=response[:200] if response else '')
        except Exception:
            jlens.capture(topic, response=response[:200] if response else '')
        return response
    
    ai.ask = ask_with_jlens
    ai.page = page_with_jlens
    ai.jlens = jlens
    
    return jlens


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("╔══════════════════════════════════════════════════════╗")
    print("║   🌊 J-LENS HARMONIQUE — Démo                        ║")
    print("║   Visualisation de l'espace de raisonnement           ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    
    # Test sans HarmonicAI (juste le JLens avec des données simulées)
    jlens = JLens()
    
    # Simuler des questions
    questions = [
        ("Qui a découvert le radium ?", [
            ("marie curie", "a découvert", "le radium et le polonium", "SFT", 5.0),
            ("curie", "a découvert", "la radioactivité", "SCIENCES", 4.0),
            ("marie curie", "a reçu", "deux prix Nobel", "SFT", 3.5),
        ]),
        ("Explique la photosynthèse", [
            ("photosynthèse", "transforme", "la lumière en énergie chimique", "BIOLOGIE", 4.5),
            ("chloroplaste", "est le siège de", "la photosynthèse", "BIOLOGIE", 4.0),
            ("photosynthèse", "produit", "de l'oxygène", "BIOLOGIE", 3.8),
            ("lumière", "est absorbée par", "la chlorophylle", "BIOLOGIE", 3.5),
            ("plantes", "utilisent", "la photosynthèse", "BIOLOGIE", 3.0),
        ]),
        ("Quelle est la capitale de la France ?", [
            ("paris", "est la capitale de", "la france", "SFT", 5.0),
            ("france", "a une population de", "67 millions", "GEOGRAPHIE", 2.0),
        ]),
    ]
    
    for q, facts in questions:
        jlens.capture(q, facts=facts, response=f"Réponse à: {q[:50]}...")
        print(jlens.render())
        print()
    
    # Sauvegarder HTML
    html = jlens.to_html()
    with open('jlens_demo.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ HTML sauvegardé: jlens_demo.html")
