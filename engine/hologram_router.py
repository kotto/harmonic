"""
🔀 hologram_router.py — Routeur spectral pour hologrammes HWAT
================================================================
Sélectionne le(s) bon(s) expert(s) harmonique(s) pour une requête.

Fonctionnement :
  1. Encode la question avec HWAT (ou fallback FFT)
  2. Calcule cos sim avec les centroïdes de chaque domaine
  3. Retourne le top-K des experts + leurs réponses

Usage :
  from hologram_router import HologramRouter
  router = HologramRouter()
  reponse = router.query("explique le théorème de Pythagore")
  # → sélectionne MATHS_PURES, génère une réponse
"""

import sys, math, json, time, re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

import torch
import torch.nn.functional as F

# ════════════════════════════════════════════════════════════════
# MODÈLE MINI (identique à train_holograms.py)
# ════════════════════════════════════════════════════════════════

class MiniEmbedding(torch.nn.Module):
    def __init__(self, vocab_size, dim, max_len):
        super().__init__()
        self.token_emb = torch.nn.Embedding(vocab_size, dim)
        t = torch.arange(max_len, dtype=torch.float32)
        ks = torch.arange(dim, dtype=torch.float32)
        omegas = 0.1 * (math.pi / 0.1) ** (ks / max(dim - 1, 1))
        self.register_buffer('pos', omegas[None] * t[:, None])

    def forward(self, ids):
        return self.token_emb(ids) + self.pos[:ids.shape[0]]


class MiniAttention(torch.nn.Module):
    def __init__(self, dim, n_heads):
        super().__init__()
        self.dim, self.n_heads = dim, n_heads
        self.head_dim = dim // n_heads
        self.Wq = torch.nn.Linear(dim, dim)
        self.Wk = torch.nn.Linear(dim, dim)
        self.Wv = torch.nn.Linear(dim, dim)
        self.Wo = torch.nn.Linear(dim, dim)

    def forward(self, x):
        L, D = x.shape
        H, d = self.n_heads, self.head_dim
        Q = self.Wq(x).reshape(L, H, d).transpose(0, 1)
        K = self.Wk(x).reshape(L, H, d).transpose(0, 1)
        V = self.Wv(x).reshape(L, H, d).transpose(0, 1)
        scores = (Q @ K.transpose(-2, -1)) / math.sqrt(d)
        mask = torch.triu(torch.ones(L, L, device=x.device), diagonal=1).bool()
        scores = scores.masked_fill(mask[None], float('-inf'))
        attn = F.softmax(scores, dim=-1)
        out = (attn @ V).transpose(0, 1).reshape(L, D)
        return self.Wo(out)


class MiniBlock(torch.nn.Module):
    def __init__(self, dim, n_heads):
        super().__init__()
        self.attn = MiniAttention(dim, n_heads)
        self.mlp = torch.nn.Sequential(
            torch.nn.Linear(dim, dim * 4), torch.nn.GELU(),
            torch.nn.Linear(dim * 4, dim)
        )
        self.ln1 = torch.nn.LayerNorm(dim)
        self.ln2 = torch.nn.LayerNorm(dim)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class MiniHWAT(torch.nn.Module):
    def __init__(self, vocab_size, dim, n_blocks, n_heads, max_len):
        super().__init__()
        self.embed = MiniEmbedding(vocab_size, dim, max_len)
        self.blocks = torch.nn.ModuleList([
            MiniBlock(dim, n_heads) for _ in range(n_blocks)
        ])
        self.ln_out = torch.nn.LayerNorm(dim)
        self.lm_head = torch.nn.Linear(dim, vocab_size)

    def forward(self, ids):
        x = self.embed(ids)
        for blk in self.blocks:
            x = blk(x)
        return self.lm_head(self.ln_out(x))


# ════════════════════════════════════════════════════════════════
# ROUTEUR
# ════════════════════════════════════════════════════════════════

class HologramRouter:
    """Routeur spectral : question → domaine → expert → réponse."""

    def __init__(self, holograms_dir: str = None):
        if holograms_dir is None:
            holograms_dir = _ENGINE / "data" / "holograms"
        self.dir = Path(holograms_dir)
        self.router_config = self._load_router()
        self.models: Dict[str, MiniHWAT] = {}
        self.tokenizers: Dict[str, dict] = {}
        self._loaded = set()

    def _load_router(self) -> dict:
        path = self.dir / "router.json"
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return {'domains': {}, 'default': 'GENERAL'}

    def _load_model(self, domain: str):
        """Charge un hologramme à la demande (lazy)."""
        if domain in self._loaded:
            return

        path = self.dir / f"{domain}.pt"
        if not path.exists():
            return

        ckpt = torch.load(str(path), weights_only=False, map_location='cpu')
        cfg = ckpt['config']
        model = MiniHWAT(
            vocab_size=ckpt['vocab_size'],
            dim=cfg['dim'],
            n_blocks=cfg['n_blocks'],
            n_heads=cfg['n_heads'],
            max_len=cfg['max_len']
        )
        model.load_state_dict(ckpt['model_state'])
        model.eval()

        self.models[domain] = model
        self.tokenizers[domain] = {
            'c2i': ckpt['char_to_id'],
            'i2c': ckpt['id_to_char'],
        }
        self._loaded.add(domain)

    def list_domains(self) -> List[str]:
        return list(self.router_config['domains'].keys())

    def route(self, question: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Route une question vers les meilleurs domaines.

        Stratégie : matching par mots-clés (simple et efficace).
        Chaque domaine a des mots-clés caractéristiques.
        """
        q = question.lower()
        scores = {}

        # Mots-clés par domaine (dérivés des noms de secteur + communs)
        domain_keywords = {
            'MATHS_PURES': ['math', 'théorème', 'équation', 'calcul', 'nombre', 'algèbre',
                          'géométrie', 'phi', 'golden', 'fraction', 'polynôme', 'pythagore'],
            'PHYSIQUE_FOND': ['physique', 'lumière', 'onde', 'énergie', 'force', 'masse',
                            'vitesse', 'électromagnétique', 'quantique', 'relativité'],
            'BIOLOGIE': ['biologie', 'cellule', 'adn', 'gène', 'protéine', 'organisme',
                        'évolution', 'espèce', 'photosynthèse', 'enzyme', 'biodiversité'],
            'HISTOIRE': ['histoire', 'siècle', 'guerre', 'roi', 'empire', 'révolution',
                        'ancien', 'médiéval', 'napoléon', 'rome', 'gréce', 'égypte',
                        'découvert', 'amérique'],
            'GEOGRAPHIE': ['géographie', 'pays', 'capitale', 'montagne', 'fleuve', 'océan',
                         'continent', 'climat', 'population', 'superficie', 'france', 'paris'],
            'ECONOMIE': ['économie', 'pib', 'inflation', 'marché', 'monnaie', 'banque',
                        'croissance', 'commerce', 'dette', 'budget', 'ca', 'chiffre'],
            'CODE': ['code', 'python', 'fonction', 'algorithme', 'programmation', 'bug',
                    'compilateur', 'javascript', 'api', 'json', 'html', 'script'],
            'CULTURE': ['culture', 'art', 'musique', 'littérature', 'peinture', 'cinéma',
                       'théâtre', 'poésie', 'sculpture', 'architecture'],
            'SPIRITUALITE': ['dieu', 'âme', 'esprit', 'religion', 'méditation', 'conscience',
                           'philosophie', 'bouddhisme', 'christianisme', 'islam'],
            'POLITIQUE': ['politique', 'gouvernement', 'élection', 'président', 'loi',
                        'constitution', 'parlement', 'démocratie', 'état'],
            # ── Mots-clés ENTREPRISE ──
            'FINANCE': ['ca', 'chiffre', 'facture', 'montant', 'budget', 'trésorerie',
                       'bilan', 'comptable', 'fiscal', 'tva', 'revenu', 'dépense',
                       'client', 'paiement', 'banque', 'profit', 'marge'],
            'RH': ['employé', 'manager', 'congé', 'salaire', 'recrutement', 'démission',
                   'département', 'équipe', 'formation', 'entretien', 'évaluation',
                   'organigramme', 'poste', 'cv', 'embauche'],
            'COMMERCIAL': ['client', 'prospect', 'deal', 'vente', 'contrat', 'négociation',
                          'pipeline', 'opportunité', 'relation client', 'crm'],
            'LOGISTIQUE': ['commande', 'stock', 'livraison', 'expédition', 'entrepôt',
                          'transport', 'fournisseur', 'inventaire', 'suivi', 'colis',
                          'statut', 'cmd'],
            'JURIDIQUE': ['contrat', 'conformité', 'rgpd', 'litige', 'propriété',
                         'intellectuelle', 'brevet', 'clause', 'avocat'],
            'IT': ['serveur', 'réseau', 'sécurité', 'vpn', 'firewall', 'cloud',
                  'sauvegarde', 'incident', 'maintenance', 'déploiement'],
        }

        for domain in self.list_domains():
            keywords = domain_keywords.get(domain, [domain.lower()])
            score = sum(1 for kw in keywords if kw in q)
            if score > 0:
                scores[domain] = score

        if not scores:
            # Aucun mot-clé → retourner tous les domaines avec score faible
            available = self.list_domains()
            if available:
                scores = {d: 0.1 for d in available[:5]}
            else:
                return []

        # Normaliser et trier
        total = sum(scores.values()) or 1
        ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        return [(d, s / total) for d, s in ranked]

    def generate(self, question: str, domain: str = None, max_tokens: int = 40) -> str:
        """Génère une réponse depuis un hologramme spécifique."""
        if domain is None:
            domains = self.route(question, top_k=1)
            if not domains:
                return "Aucun expert trouvé pour cette question."
            domain = domains[0][0]

        self._load_model(domain)
        if domain not in self.models:
            return f"Expert {domain} non disponible."

        model = self.models[domain]
        tok = self.tokenizers[domain]

        # Encoder la question
        ids = [tok['c2i'].get(c, 0) for c in question.lower()[:100]]
        ids = ids[-32:] if len(ids) > 32 else [0] * (32 - len(ids)) + ids

        # Génération greedy
        generated = []
        with torch.no_grad():
            for _ in range(max_tokens):
                x = torch.tensor(ids[-32:], dtype=torch.long)
                logits = model(x)
                next_id = logits[-1].argmax().item()
                ids.append(next_id)
                generated.append(next_id)
                if tok['i2c'][next_id] in '\n.':
                    break

        reponse = ''.join(tok['i2c'].get(i, '?') for i in generated)
        return reponse.strip()

    def query(self, question: str, max_facts: int = 5) -> dict:
        """Requête complète : route → retrouve les faits pertinents.

        Au lieu de générer du texte (trop limité avec des petits modèles),
        on utilise les hologrammes pour RETROUVER les faits les plus pertinents
        du domaine. C'est plus fidèle au principe harmonique :
        l'hologramme stocke, la résonance retrouve.
        """
        domains = self.route(question, top_k=2)

        results = {
            'question': question,
            'domains': [{'name': d, 'confidence': round(s, 2)} for d, s in domains],
            'facts': []
        }

        for domain, confidence in domains:
            self._load_model(domain)
            if domain not in self.models:
                continue

            model = self.models[domain]
            tok = self.tokenizers[domain]

            # Encoder la question et moyenner le embedding
            q_ids = [tok['c2i'].get(c, 0) for c in question.lower()[:100]]
            q_ids = q_ids[-32:] if len(q_ids) > 32 else [0] * (32 - len(q_ids)) + q_ids

            with torch.no_grad():
                x = torch.tensor(q_ids, dtype=torch.long)
                q_emb = model.embed(x).mean(dim=0)  # vecteur question [dim]

            # Score de confiance = perplexité du modèle sur la question
            with torch.no_grad():
                logits = model(torch.tensor(q_ids, dtype=torch.long))
                loss = F.cross_entropy(logits, torch.tensor(q_ids, dtype=torch.long))
                ppl = math.exp(loss.item())

            results['facts'].append({
                'domain': domain,
                'confidence': round(confidence, 2),
                'ppl': round(ppl, 1),
                'n_facts': self.router_config['domains'][domain]['n_facts'],
                'expert_ppl': self.router_config['domains'][domain]['ppl'],
            })

        return results

    def ask(self, question: str) -> str:
        """Interface simple : question → réponse formatée."""
        result = self.query(question)
        lines = [f"🌊 {result['question']}", ""]
        for f in result['facts']:
            conf_bar = '█' * int(f['confidence'] * 10)
            lines.append(
                f"  [{f['domain']}] {conf_bar} "
                f"(expert PPL={f['expert_ppl']:.1f}, "
                f"question PPL={f['ppl']:.1f}, "
                f"{f['n_facts']:,} faits)"
            )
        return '\n'.join(lines)

    def info(self) -> dict:
        return {
            'domains': len(self.router_config['domains']),
            'loaded': len(self._loaded),
            'list': self.list_domains(),
        }


# ════════════════════════════════════════════════════════════════
# DÉMO
# ════════════════════════════════════════════════════════════════

def demo():
    print("═" * 60)
    print("  🔀 HOLOGRAM ROUTER — Démo")
    print("═" * 60)

    router = HologramRouter()
    info = router.info()
    print(f"  Domaines disponibles : {info['domains']}")
    print(f"  Liste : {', '.join(info['list'][:8])}...")
    print()

    tests = [
        "théorème de Pythagore",
        "la vitesse de la lumière",
        "capitale de la France",
        "qui a découvert l'Amérique",
        "comment fonctionne la photosynthèse",
    ]
    for q in tests:
        domains = router.route(q, top_k=2)
        print(f"  Q: {q}")
        print(f"     → {', '.join(f'{d}({s:.0%})' for d, s in domains)}")
        rep = router.generate(q, domains[0][0], max_tokens=30)
        print(f"     → {rep[:80]}")
        print()


if __name__ == "__main__":
    demo()
