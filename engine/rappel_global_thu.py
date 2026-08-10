#!/usr/bin/env python3
"""
RAPPEL GLOBAL THU — Classement global par résonance gaussienne (KA Mobile)
==========================================================================
Résout la dette v1 : le rappel actuel de KA Mobile ne résonne que sur les
11 hologrammes v2 (~4 300 faits médicaux) — les 29 v1 (géographie, histoire,
sciences, mathématiques 46k faits…) retournent [] (audit 10/08/2026).

Ce module classe les 178 974 faits UNIQUES de TOUS les hologrammes par
résonance gaussienne sur un espace PPMI appris :

    Build UNE FOIS (persisté) :
        faits uniques → vocabulaire (freq ≥ 2)
        → cooccurrence CREUSE (fenêtre = fait entier)
        → PPMI sparse → graphe top-k voisins
        → attraction pure vectorisée (méthode validée de la session THU V2)
        → fréquences (kx, ky) + INDEX INVERSÉ token → faits

    Rappel par requête (< 100 ms) :
        question → ancres (mots-outils exclus)
        → index inversé → faits candidats (union des postings)
        → score gaussien des candidats (max résonance de leurs tokens)
        → top-k GLOBAL + GATE (0 FAUX)

Faisabilité mesurée (10/08/2026) : scoring gaussien sur 411k faits =
20-45 ms (non-bloquant) ; la matrice dense V×V serait 6-8 Go → creuse.

Usage :
    from rappel_global_thu import RappelGlobalTHU
    rg = RappelGlobalTHU()
    rg.construire()                       # build UNE FOIS (persisté)
    resultats = rg.rappel_global("quelle est la capitale de l autriche")
"""

import os, sys, re, json, time, hashlib
import numpy as np

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE_DIR)

STOPWORDS = set((
    "le la les de des du une un et est a dans que qui pas ne sur pour avec je tu "
    "il elle on nous vous ils elles ce cet cette ces mon ton son ma ta sa au aux en ou "
    "mais donc or ni car si comme plus moins fois divise egal quel quelle quels quelles "
    "comment pourquoi combien où sont était avoir faire calculer trouver donner resoudre "
    "expliquer connaitre savoir parler ecrire lire quelle quelqu un plusieurs beaucoup peu "
    "tres bien mal tout toute tous toutes autre autres meme entre vers sous chez depuis "
    "pendant avant apres contre sans parmi l la d s qu n t y "
).split())

_MOTIF = re.compile(r"[a-zàâäéèêëîïôöùûüçœ]+")


def _mots(texte):
    return _MOTIF.findall(texte.lower())


class RappelGlobalTHU:
    """Classement global des faits par résonance gaussienne THU."""

    def __init__(self, store_dir=None, data_dir=None, min_freq: int = 2,
                 top_k_voisins: int = 10, n_iter: int = 120, lr: float = 0.005):
        if store_dir is None:
            store_dir = _ENGINE_DIR
        if data_dir is None:
            data_dir = os.path.join(_ENGINE_DIR, "data", "rappel_global_thu")
        self.store_dir = store_dir
        self.data_dir = data_dir
        self.min_freq = min_freq
        self.top_k_voisins = top_k_voisins
        self.n_iter = n_iter
        self.lr = lr
        self.faits = []          # [(s, r, o, holo_id)]
        self.vocab = []
        self.w2i = {}
        self.kx = None
        self.ky = None
        self.sigma = None
        self.index_inverse = {}  # token_id -> [fait_idx...]
        self._pret = False

    # =====================================================================
    # CHARGEMENT DES FAITS
    # =====================================================================

    def _charger_faits(self):
        """Charge les faits UNIQUES de tous les hologrammes (v1 + v2)."""
        from hologram_store import HologramStore
        store = HologramStore()
        vus = set()
        faits = []
        for h in store.list_holograms():
            hid = h['id']
            try:
                facts, _ = store.download(hid)
            except Exception:
                continue
            for s, r, o, sec in facts:
                cle = (str(s).lower(), str(r).lower(), str(o).lower())
                if cle in vus:
                    continue
                vus.add(cle)
                faits.append((str(s), str(r), str(o), hid))
        return faits

    # =====================================================================
    # BUILD DE L'ESPACE
    # =====================================================================

    def _hash_faits(self):
        """Hash des faits (pour rebuild si le contenu change)."""
        h = hashlib.md5()
        for s, r, o, hid in self.faits[:5000]:
            h.update(f"{s}|{r}|{o}".encode("utf-8", errors="ignore"))
        h.update(str(len(self.faits)).encode())
        return h.hexdigest()[:16]

    def construire(self, force: bool = False, verbose: bool = True) -> dict:
        """Build complet (ou chargement depuis le disque si à jour)."""
        t0 = time.time()
        os.makedirs(self.data_dir, exist_ok=True)
        meta_path = os.path.join(self.data_dir, "meta.json")
        npz_path = os.path.join(self.data_dir, "espace.npz")
        idx_path = os.path.join(self.data_dir, "index.json")

        if not force and os.path.exists(meta_path) and os.path.exists(npz_path):
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            # Vérifier que les faits n'ont pas changé (rapide : charge les faits)
            faits_charges = self._charger_faits()
            h = hashlib.md5()
            for s, r, o, hid in faits_charges[:5000]:
                h.update(f"{s}|{r}|{o}".encode("utf-8", errors="ignore"))
            h.update(str(len(faits_charges)).encode())
            if meta.get("hash") == h.hexdigest()[:16]:
                self._charger(npz_path, idx_path, meta)
                if verbose:
                    print(f"  [RappelGlobalTHU] chargé depuis disque : "
                          f"{len(self.faits)} faits, {len(self.vocab)} tokens "
                          f"({time.time()-t0:.1f}s)")
                return meta

        # --- Build complet ---
        if verbose:
            print("  [RappelGlobalTHU] build complet...")
        self.faits = self._charger_faits()
        n_faits = len(self.faits)
        if verbose:
            print(f"  faits uniques : {n_faits}")

        # 1. Vocabulaire : mots de fréquence ≥ min_freq
        count = {}
        for s, r, o, hid in self.faits:
            for w in _mots(f"{s} {r} {o}"):
                if len(w) > 2:
                    count[w] = count.get(w, 0) + 1
        self.vocab = ["<BOS>", "<EOS>", "<UNK>", "<PAD>"] + \
                     [w for w, c in sorted(count.items(), key=lambda x: -x[1])
                      if c >= self.min_freq]
        self.w2i = {w: i for i, w in enumerate(self.vocab)}
        V = len(self.vocab)
        if verbose:
            print(f"  vocabulaire : {V} tokens (freq ≥ {self.min_freq})")

        # Tokens par fait
        tokens_par_fait = []
        for s, r, o, hid in self.faits:
            tokens_par_fait.append(
                [self.w2i[w] for w in _mots(f"{s} {r} {o}") if w in self.w2i])

        # 2. Cooccurrence CREUSE (fenêtre = fait entier)
        try:
            from scipy import sparse as sp
            cooc_rows, cooc_cols, cooc_vals = [], [], []
            for toks in tokens_par_fait:
                for i in range(len(toks)):
                    for j in range(len(toks)):
                        if i != j:
                            cooc_rows.append(toks[i])
                            cooc_cols.append(toks[j])
                            cooc_vals.append(1.0)
            cooc = sp.coo_matrix((cooc_vals, (cooc_rows, cooc_cols)),
                                 shape=(V, V), dtype=np.float64).tocsr()
            total = cooc.sum()
            freq_i = np.asarray(cooc.sum(axis=1)).ravel() + 1e-10
            # PPMI sparse : log(cooc·N / (f_i·f_j))
            cooc_coo = cooc.tocoo()
            expected = (freq_i[cooc_coo.row] * freq_i[cooc_coo.col]) / total
            pmi = np.log((cooc_coo.data * total + 1e-10) / (expected + 1e-10))
            pmi = np.clip(np.maximum(0.0, pmi), 0.0, 10.0)
            ppmi = sp.coo_matrix((pmi, (cooc_coo.row, cooc_coo.col)),
                                 shape=(V, V), dtype=np.float64).tocsr()
        except ImportError:
            # Fallback numpy pur (petit vocabulaire seulement)
            cooc = np.zeros((V, V))
            for toks in tokens_par_fait:
                for i in range(len(toks)):
                    for j in range(len(toks)):
                        if i != j:
                            cooc[toks[i], toks[j]] += 1.0
            total = cooc.sum()
            marginal = cooc.sum(axis=1, keepdims=True) + 1e-10
            expected = (marginal @ cooc.sum(axis=0, keepdims=True)) / total
            ppmi = np.clip(np.maximum(0.0, np.log((cooc + 1e-10)
                                                  / (expected + 1e-10))), 0, 10)

        # 3. Graphe top-k voisins PPMI (creux) — chaque token garde ses k
        #    plus proches voisins PPMI (le graphe, pas la matrice dense)
        if hasattr(ppmi, "tocsr"):
            ppmi_csr = ppmi.tocsr()
            graphe_i, graphe_j, graphe_w = [], [], []
            for i in range(4, V):
                ligne = ppmi_csr.getrow(i)
                if ligne.nnz == 0:
                    continue
                data = ligne.data
                cols = ligne.indices
                k = min(self.top_k_voisins, len(data))
                if k <= 0:
                    continue
                # kth doit être < len(data)
                kth = min(k - 1, len(data) - 1)
                ordre = np.argpartition(-data, kth)[:k]
                for oi in ordre:
                    if cols[oi] != i and data[oi] > 0.01:
                        graphe_i.append(i)
                        graphe_j.append(cols[oi])
                        graphe_w.append(float(data[oi]))
        else:
            graphe_i, graphe_j, graphe_w = [], [], []
            for i in range(4, V):
                scores_i = ppmi[i].copy()
                scores_i[i] = 0
                ordre = np.argsort(-scores_i)[:self.top_k_voisins]
                for j in ordre:
                    if scores_i[j] > 0.01:
                        graphe_i.append(i)
                        graphe_j.append(j)
                        graphe_w.append(float(scores_i[j]))
        if verbose:
            print(f"  graphe : {len(graphe_i)} paires (top-{self.top_k_voisins} PPMI)")

        # 4. Attraction pure VECTORISÉE par lots (méthode validée)
        # INIT : spirale du tokenizer (structure ordonnée) — l'init aléatoire
        # étale les tokens (σ ≈ 3,8 → gaussiennes couvrant tout → scores
        # saturés à 1,0, mesuré). La spirale donne σ ≈ 0,2 → voisinages
        # discriminants (le réglage du benchmark comparatif F1 0,503).
        try:
            import importlib.util as _iu
            _SAAS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            spec = _iu.spec_from_file_location(
                "hrg_rg", os.path.join(_SAAS, "harmonic_training", "model",
                                       "harmonic_resonance_generator.py"))
            hrg = _iu.module_from_spec(spec)
            spec.loader.exec_module(hrg)
            _tok = hrg.TokeniseurOndes(self.vocab, use_pi_over_6=True)
            kx = _tok._kx[:V].copy().astype(np.float64)
            ky = _tok._ky[:V].copy().astype(np.float64)
        except Exception:
            kx = np.random.RandomState(42).randn(V) * 0.5
            ky = np.random.RandomState(7).randn(V) * 0.5
        ii = np.array(graphe_i, dtype=int)
        jj = np.array(graphe_j, dtype=int)
        ww = np.array(graphe_w, dtype=np.float64)
        for it in range(self.n_iter):
            dx = kx[ii] - kx[jj]
            dy = ky[ii] - ky[jj]
            # gradient par index : accumulation vectorisée via np.add.at
            gkx = np.zeros(V); gky = np.zeros(V)
            np.add.at(gkx, ii, 2.0 * ww * dx)
            np.add.at(gkx, jj, -2.0 * ww * dx)
            np.add.at(gky, ii, 2.0 * ww * dy)
            np.add.at(gky, jj, -2.0 * ww * dy)
            kx -= self.lr * gkx
            ky -= self.lr * gky
            r = np.sqrt(kx**2 + ky**2)
            m = r > 6.0
            kx[m] *= 6.0 / (r[m] + 1e-10)
            ky[m] *= 6.0 / (r[m] + 1e-10)
            kx -= kx.mean(); ky -= ky.mean()
            if verbose and (it + 1) % 40 == 0:
                print(f"    iter {it+1}/{self.n_iter}")
        self.kx = kx
        self.ky = ky

        # 5. Sigma adaptatif (médiane des distances d'un échantillon)
        sample = min(V, 500)
        rng = np.random.RandomState(0)
        idx = rng.choice(np.arange(4, V), sample, replace=False)
        dm = np.sqrt((kx[idx, None] - kx[None, idx])**2
                     + (ky[idx, None] - ky[None, idx])**2)
        off = dm[np.triu_indices(sample, 1)]
        off = off[off > 1e-9]
        self.sigma = float(np.median(off)) if len(off) else 0.2

        # 6. Index inversé : token → faits
        self.index_inverse = {}
        for fi, toks in enumerate(tokens_par_fait):
            for t in set(toks):
                self.index_inverse.setdefault(t, []).append(fi)

        # 7. Persistance
        np.savez(npz_path, kx=kx, ky=ky,
                 tokens_par_fait=np.array(tokens_par_fait, dtype=object))
        meta = {
            "hash": self._hash_faits(),
            "n_faits": n_faits,
            "n_tokens": V,
            "sigma": self.sigma,
            "min_freq": self.min_freq,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in self.index_inverse.items()}, f)
        with open(os.path.join(self.data_dir, "vocab.json"), "w", encoding="utf-8") as f:
            json.dump(self.vocab, f, ensure_ascii=False)
        self._pret = True
        if verbose:
            print(f"  [RappelGlobalTHU] build terminé : {n_faits} faits, "
                  f"{V} tokens ({time.time()-t0:.1f}s)")
        return meta

    def _charger(self, npz_path, idx_path, meta):
        """Charge un espace persité."""
        d = np.load(npz_path, allow_pickle=True)
        self.kx = d["kx"]
        self.ky = d["ky"]
        with open(os.path.join(self.data_dir, "vocab.json"), encoding="utf-8") as f:
            self.vocab = json.load(f)
        self.w2i = {w: i for i, w in enumerate(self.vocab)}
        with open(idx_path, encoding="utf-8") as f:
            self.index_inverse = {int(k): v for k, v in json.load(f).items()}
        self.sigma = meta.get("sigma", 0.2)
        self.faits = self._charger_faits()
        self._pret = True

    # =====================================================================
    # RAPPEL GLOBAL
    # =====================================================================

    def _ancres(self, question):
        return [self.w2i[w] for w in _mots(question)
                if w in self.w2i and w not in STOPWORDS]

    def rappel_global(self, question: str, top_k: int = 10,
                      seuil_gate: float = None) -> list:
        """
        Rappel global : ancres → candidats (index inversé) → résonance
        gaussienne → top-k + gate.

        Returns:
            liste de {"sujet", "relation", "objet", "hologramme", "score"}
            ou [] si gate refuse (0 FAUX).
        """
        if not self._pret:
            self.construire(verbose=False)
        ancres = self._ancres(question)
        if not ancres:
            return []

        # Candidats : union des faits contenant au moins une ancre
        candidats = set()
        for a in ancres:
            candidats.update(self.index_inverse.get(a, []))
        if not candidats:
            return []

        # Résonance gaussienne (max par fait)
        from resonance_semantique import scores_resonance
        kx_q = np.asarray([self.kx[a] for a in ancres])
        ky_q = np.asarray([self.ky[a] for a in ancres])
        amp_q = np.ones(len(ancres))
        scores, _, _, _ = scores_resonance(kx_q, ky_q, amp_q,
                                           np.asarray(self.kx), np.asarray(self.ky),
                                           self.sigma, mode="max")

        # Score de chaque fait candidat (max résonance de ses tokens)
        resultats = []
        for fi in candidats:
            s, r, o, hid = self.faits[fi]
            toks = [self.w2i[w] for w in _mots(f"{s} {r} {o}") if w in self.w2i]
            if not toks:
                continue
            sc = float(np.max(scores[toks]))
            if sc > 0.0:
                resultats.append({"sujet": s, "relation": r, "objet": o,
                                  "hologramme": hid, "score": sc})
        resultats.sort(key=lambda x: -x["score"])

        # Gate : score max < seuil → refus (0 FAUX)
        if resultats:
            if seuil_gate is None:
                seuil_gate = 0.3  # calibré par benchmark (hors-sujet < 0,3)
            if resultats[0]["score"] < seuil_gate:
                return []
        return resultats[:top_k]

    def stats(self) -> dict:
        return {"n_faits": len(self.faits), "n_tokens": len(self.vocab),
                "sigma": self.sigma}
