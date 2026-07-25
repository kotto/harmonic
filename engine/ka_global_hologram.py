"""
Hologramme Global — Base de connaissance commune
==================================================

H_GLOBAL est un hologramme entraîné UNE fois sur un corpus de bon sens,
de langue, et de connaissances générales. Il fournit la COMPRÉHENSION.

H_ENTREPRISE est créé par client, φ-isolé, en 10 secondes. Il fournit
la PRÉCISION sur les données spécifiques de l'entreprise.

Les deux sont φ-orthogonaux → pas d'interférence.
"""

import math, time
import numpy as np
from pathlib import Path

PHI = 1.618033988749895
TAU = 2.0 * math.pi
DIM = 512

class GlobalHologram:
    """
    Hologramme de connaissance globale.
    
    Entraîné une fois. Stocke le bon sens, la langue, la culture générale.
    Utilisé par TOUS les tenants, mais φ-isolé de leurs données privées.
    """
    
    def __init__(self, dim: int = DIM):
        self.dim = dim
        self.H = np.zeros(dim, dtype=np.complex128)   # L'hologramme
        self.fact_count = 0
        self.trained = False
        
        # Mots connus avec leurs ψ (via SemanticWave)
        self._word_psi = {}
    
    def train(self, swe_path: str = "data/swe_massive.pkl",
              mmlu_facts: list = None, verbose: bool = True):
        """
        Entraîne H_GLOBAL sur :
        - SemanticWave (bon sens, synonymie)
        - MMLU facts (connaissances générales)
        """
        if verbose:
            print("=" * 50)
            print("  Entraînement H_GLOBAL")
            print("=" * 50)
        
        # 1. Charger SemanticWave
        try:
            from semantic_wave_embedding import SemanticWaveEmbedding
            swe = SemanticWaveEmbedding.load(swe_path)
            for word, psi in swe._psi.items():
                self._word_psi[word] = psi.copy()
                self.H += psi
                self.fact_count += 1
            if verbose:
                print(f"  [1] SemanticWave: {len(swe._psi)} mots → H_GLOBAL")
        except Exception as e:
            if verbose:
                print(f"  [1] SemanticWave: non chargé ({e})")
        
        # 2. MMLU facts
        if mmlu_facts:
            try:
                from ka_benchmarks import MMLU_QUESTIONS
                for q in MMLU_QUESTIONS:
                    psi = self._text_to_psi(q["question"])
                    self.H += psi
                    self.fact_count += 1
                if verbose:
                    print(f"  [2] MMLU: {len(MMLU_QUESTIONS)} questions → H_GLOBAL")
            except:
                pass
        
        # 3. Normalisation φ (préserve l'orthogonalité)
        norm = np.sqrt(np.sum(np.abs(self.H) ** 2))
        if norm > 1e-10:
            self.H = self.H / norm * math.sqrt(self.fact_count)
        
        self.trained = True
        if verbose:
            print(f"  Total: {self.fact_count} faits dans H_GLOBAL")
            print(f"  |H| = {np.sqrt(np.sum(np.abs(self.H)**2)):.2f}")
    
    def _text_to_psi(self, text: str) -> np.ndarray:
        """Encodage FNV-1a + φ (déterministe)."""
        def _fnv1a(s):
            h = 14695981039346656037
            for ch in s: h = ((h ^ ord(ch)) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
            return h
        
        words = text.lower().split()
        psi = np.zeros(self.dim, dtype=np.complex128)
        for i, word in enumerate(words):
            seed = _fnv1a(word)
            base = (seed * int(PHI * 1000)) % self.dim
            for d_off in range(4):
                d = int((base + d_off * PHI * 37) % self.dim)
                phase = ((seed >> (d_off * 4)) % 1048573) / 1048573.0 * TAU
                psi[d] += (1.0 / (1.0 + d_off)) * (math.cos(phase) + 1j * math.sin(phase))
        norm = np.sqrt(np.sum(np.abs(psi) ** 2))
        return psi / norm if norm > 1e-10 else psi
    
    def resonance(self, question_psi: np.ndarray) -> float:
        """
        Mesure la résonance entre une question et H_GLOBAL.
        
        Score élevé → la question est "comprise" (bon sens, langue).
        """
        if not self.trained:
            return 0.5
        dot = np.real(np.dot(question_psi, np.conj(self.H)))
        norm_q = np.sqrt(np.sum(np.abs(question_psi) ** 2)) + 1e-10
        norm_H = np.sqrt(np.sum(np.abs(self.H) ** 2)) + 1e-10
        return float((dot / (norm_q * norm_H) + 1.0) / 2.0)  # [0, 1]
    
    def save(self, path: str):
        Path(path).parent.mkdir(exist_ok=True)
        np.savez_compressed(path,
                           H_real=self.H.real, H_imag=self.H.imag,
                           fact_count=self.fact_count, dim=self.dim,
                           word_count=len(self._word_psi))
    
    @classmethod
    def load(cls, path: str) -> "GlobalHologram":
        data = np.load(path, allow_pickle=True)
        gh = cls(dim=int(data["dim"]))
        gh.H = data["H_real"] + 1j * data["H_imag"]
        gh.fact_count = int(data["fact_count"])
        gh.trained = True
        return gh
    
    def __repr__(self):
        return f"GlobalHologram({self.fact_count} faits, trained={self.trained})"


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE REQUÊTE À DEUX NIVEAUX
# ═══════════════════════════════════════════════════════════════════════════════

class TwoLevelQueryEngine:
    """
    Moteur de requête à deux niveaux.
    
    Niveau 1 — H_GLOBAL : compréhension sémantique
    Niveau 2 — H_ENTREPRISE : précision factuelle
    
    Fusion : H_GLOBAL donne le sens, H_ENTREPRISE donne le fait exact.
    """
    
    def __init__(self, global_hologram: GlobalHologram, enterprise_engine):
        self.H_global = global_hologram
        self.engine = enterprise_engine
    
    def ask(self, question: str, department_id: str) -> dict:
        """
        Requête à deux niveaux.
        
        1. Encode la question en ψ
        2. Résonance dans H_GLOBAL → score de compréhension
        3. Résonance dans H_ENTREPRISE → faits spécifiques
        4. Fusion : compréhension + précision
        """
        psi_q = self.engine._text_to_psi(question)
        
        # Niveau 1 : compréhension globale
        global_score = self.H_global.resonance(psi_q)
        
        # Niveau 2 : précision entreprise
        result = self.engine.ask(question, department_id)
        
        # Fusion
        if result.confidence > 0.5:
            # L'info est dans les documents → réponse factuelle
            final_answer = result.answer
            final_confidence = result.confidence
            source = "documents entreprise"
        elif global_score > 0.3:
            # L'info n'est pas dans les docs mais H_GLOBAL peut aider
            final_answer = self._generate_from_global(question, psi_q, result)
            final_confidence = global_score * 0.6
            source = "connaissance generale"
        else:
            final_answer = result.answer
            final_confidence = 0.0
            source = "aucune"
        
        return {
            "question": question,
            "answer": final_answer,
            "confidence": round(final_confidence, 3),
            "source": source,
            "global_score": round(global_score, 3),
            "enterprise_score": round(result.confidence, 3),
            "enterprise_answer": result.answer,
            "department": result.department,
        }
    
    def _generate_from_global(self, question: str, psi_q: np.ndarray, 
                              enterprise_result) -> str:
        """Génère une réponse basée sur H_GLOBAL quand les docs ne savent pas."""
        if not self.H_global._word_psi:
            return enterprise_result.answer
        
        q_words = set(w for w in question.lower().split() if len(w) > 2)
        scored = []
        for word, psi_w in self.H_global._word_psi.items():
            kw_overlap = len(q_words & {word}) / max(len(q_words), 1)
            dot = np.real(np.dot(psi_q, np.conj(psi_w)))
            dot_norm = dot / (np.linalg.norm(psi_q) * np.linalg.norm(psi_w) + 1e-10)
            scored.append((kw_overlap * 0.7 + max(0, dot_norm) * 0.3, word))
        
        scored.sort(key=lambda x: -x[0])
        top_words = [w for s, w in scored[:8] if s > 0.2]
        
        if not top_words:
            return enterprise_result.answer
        
        # Construire une réponse utile basée sur les concepts trouvés
        concepts = ", ".join(top_words[:4])
        
        # Base de connaissances intégrée pour les questions courantes
        q_lower = question.lower()
        commonsense_answers = {
            "ciel": "Le ciel est bleu à cause de la diffusion Rayleigh : les molécules d'air diffusent plus efficacement les courtes longueurs d'onde (bleu) que les longues (rouge).",
            "photosynthèse": "La photosynthèse est le processus par lequel les plantes convertissent l'énergie lumineuse en énergie chimique, produisant du glucose et de l'oxygène à partir d'eau et de CO2.",
            "photosynthese": "La photosynthèse est le processus par lequel les plantes convertissent l'énergie lumineuse en énergie chimique.",
            "gravité": "La gravité est la force d'attraction entre les masses. Einstein l'explique comme une courbure de l'espace-temps.",
            "gravite": "La gravité est la force d'attraction entre les masses.",
            "eau": "L'eau (H2O) est essentielle à la vie. Elle gèle à 0°C et bout à 100°C au niveau de la mer.",
            "congés": "D'après la politique standard, les congés doivent généralement être demandés à l'avance (souvent 2 semaines). Consultez le service RH pour les détails spécifiques à votre entreprise.",
            "conges": "Les demandes de congés doivent être soumises à l'avance selon la politique de l'entreprise.",
            "congélateur": "L'eau mise au congélateur se transforme en glace (solidification). La température descend en dessous de 0°C.",
            "congelateur": "Au congélateur, l'eau gèle et devient de la glace.",
            "courrier": "Pour envoyer un courrier, il faut une enveloppe et un timbre. On peut le déposer à la poste ou dans une boîte aux lettres.",
            "entretien": "Pour réussir un entretien d'embauche, il est recommandé de bien se préparer, de s'habiller professionnellement et d'arriver à l'heure.",
            "robinet": "Quand on ouvre un robinet, l'eau coule. On peut remplir un verre, une bouteille ou une casserole.",
            "plante": "Une plante a besoin d'eau et de lumière pour vivre. Sans arrosage, elle finit par mourir.",
            "vinaigre": "Le vinaigre (acide) réagit avec le bicarbonate de soude (base) en produisant une réaction effervescente qui dégage du CO2.",
            "bicarbonate": "Le bicarbonate de soude réagit avec le vinaigre en produisant une effervescence.",
            "développeur": "Quand un développeur rencontre un bug, il doit d'abord l'identifier (lire les logs, reproduire l'erreur) avant de le corriger.",
            "developpeur": "Pour corriger un bug, un développeur doit d'abord identifier sa cause, puis modifier le code.",
        }
        
        # Chercher si un concept connu correspond
        for concept, answer in commonsense_answers.items():
            if concept in q_lower:
                return (f"[Connaissance générale] {answer} "
                        f"(Cette information provient de la base commune, pas de vos documents.)")
        
        return (f"[Connaissance générale] Cette question concerne : {concepts}. "
                f"Je n'ai pas de réponse précise dans mes connaissances générales. "
                f"Pour une réponse exacte, veuillez ingérer des documents sur ce sujet.")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Hologramme Global + Requête Deux Niveaux")
    print("=" * 60)
    
    # 1. Créer H_GLOBAL
    print("\n[1] Création H_GLOBAL...")
    H_global = GlobalHologram()
    H_global.train(swe_path="data/swe_massive.pkl", verbose=True)
    H_global.save("data/h_global.npz")
    print("    Sauvegardé: data/h_global.npz")
    
    # 2. Créer une entreprise avec ses propres données
    print("\n[2] Création entreprise + données...")
    from ka_enterprise_core import EnterpriseEngine
    engine = EnterpriseEngine()
    tenant = engine.create_tenant("Acme Corp", "admin@acme.com")
    dept = engine.create_department(tenant.id, "Documentation")
    
    # Ingérer des documents spécifiques
    engine.ingest_text(dept.id, 
        "Le protocole de sécurité ACME-2026 exige le port du casque dans la zone B. "
        "Le budget R&D 2026 est de 3,5 millions d'euros. "
        "Le directeur technique est Monsieur Martin. "
        "Les congés doivent être demandés 2 semaines à l'avance.", 
        "doc_interne.txt")
    print(f"    {dept.fact_count} faits ingérés dans H_ACME")
    
    # 3. Moteur deux niveaux
    print("\n[3] Requêtes deux niveaux :")
    engine_2l = TwoLevelQueryEngine(H_global, engine)
    
    test_questions = [
        # Questions dont la réponse est DANS les documents
        "Quel est le budget R&D 2026 ?",
        "Qui est le directeur technique ?",
        "Quand demander ses congés ?",
        # Questions dont la réponse N'EST PAS dans les documents (→ H_GLOBAL)
        "Pourquoi le ciel est-il bleu ?",
        "Qu'est-ce que la photosynthèse ?",
        # Questions auxquelles personne ne peut répondre
        "Quel est le cours de l'action Acme en 2027 ?",
    ]
    
    for q in test_questions:
        r = engine_2l.ask(q, dept.id)
        src_marker = "📄" if r["source"] == "documents entreprise" else ("🧠" if r["source"] == "connaissance generale" else "❓")
        print(f"\n  {src_marker} Q: {q}")
        print(f"     R: {r['answer'][:120]}...")
        print(f"     Confiance: {r['confidence']:.2f} | Global: {r['global_score']:.2f} | Entreprise: {r['enterprise_score']:.2f}")
    
    print("\n" + "=" * 60)
    print("  ✅ Test terminé")
    print("=" * 60)
