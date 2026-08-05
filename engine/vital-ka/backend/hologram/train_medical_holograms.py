"""
🏥 train_medical_holograms.py — Hologrammes HWAT médicaux par spécialité
==========================================================================
Entraîne un petit HWAT par domaine médical (spécialité) au lieu d'un
modèle monolithique. Chaque hologramme est un expert harmonique.

Sources de données :
  - 14+ JSON vital_ka (paludisme, pédiatrie, VIH/TB, pharmacie, urgences,
    santé mentale, phytothérapie, NTD, mère-enfant, vaccination, chroniques, malnutrition)
  - real_clinical_dataset.json (100K cas cliniques réels)
  - knowledge_base_50k.npz (faits généraux pour le domaine GENERAL)

Architecture :
  KB médicale → grouper par spécialité → pour chaque spécialité :
    → convertir faits en phrases naturelles
    → tokeniser (vocab local au domaine)
    → entraîner MiniHWAT (dim=32, 1 bloc, 3-5 époques)
    → sauvegarder hologramme + faits originaux (retrieval)

Routeur : cos sim(signature question, centroïdes) → top-K experts

Lancer : python train_medical_holograms.py
Sortie : data/medical_holograms/{secteur}.pt + router.json
Temps estimé : ~15-45 min pour 12-15 domaines sur CPU
"""

import sys, math, time, os, json, random, re, gc
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

import torch
import torch.nn as nn
import torch.nn.functional as F

# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════

DIM = 32             # petit modèle par domaine
N_BLOCKS = 1         # 1 bloc suffit pour un domaine
N_HEADS = 2          # 32/2 = 16 dims/tête
MAX_LEN = 40
LR = 0.002
EPOCHS = 4           # suffisant pour spécialisation
MIN_FACTS = 30         # min faits pour entraîner un hologramme (médical : tous les domaines comptent)
MAX_DOMAINS = 20     # max domaines à entraîner
VOCAB_PER_DOMAIN = 2500  # vocab max par domaine
MAX_CLINICAL_CASES = 60000  # cas cliniques max à parcourir
MAX_FACTS_PER_SECTOR = 60000  # faits max par secteur pour équilibrer
MAX_CHARS_PER_DOMAIN = 400000  # limite mémoire par domaine
PRINT_EVERY = 50

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# ════════════════════════════════════════════════════════════════
# 1. EXTRACTION DES FAITS MÉDICAUX
# ════════════════════════════════════════════════════════════════

def load_vital_ka_json(name: str) -> dict:
    """Charge un JSON vital_ka."""
    path = _ENGINE / "data" / f"{name}.json"
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def extract_facts_from_diseases(data: dict, sector: str) -> list:
    """vital_ka_diseases.json → faits (sujet, relation, objet, secteur)."""
    facts = []
    maladies = data.get('maladies', {})
    for nom, info in maladies.items():
        nom = str(nom).replace('_', ' ')
        # Symptômes
        for sym in info.get('symptomes', []):
            facts.append((nom, 'présente_symptôme', str(sym), sector))
        # Gravité
        facts.append((nom, 'gravité', str(info.get('gravite', '')), sector))
        # Conduite à tenir
        if info.get('conduite'):
            facts.append((nom, 'conduite_à_tenir', str(info['conduite']), sector))
        # Délai consultation
        if info.get('delai_consultation'):
            facts.append((nom, 'délai_consultation', str(info['delai_consultation']), sector))
        # Traitement (si présent)
        if isinstance(info.get('traitement'), dict):
            for k, v in info['traitement'].items():
                facts.append((nom, f'traitement_{k}', str(v), sector))
    return facts


def _flatten_value(path: str, val) -> list:
    """Aplatit récursivement une valeur en liste (chemin, valeur_texte)."""
    out = []
    if isinstance(val, dict):
        for k, v in val.items():
            out.extend(_flatten_value(f"{path}_{k}", v))
    elif isinstance(val, list):
        for i, v in enumerate(val[:10]):
            out.extend(_flatten_value(f"{path}_{i}", v))
    elif isinstance(val, (str, int, float, bool)):
        s = str(val).strip()
        if len(s) > 1 and len(s) < 300:
            out.append((path, s))
    return out


def extract_facts_from_conditions(data: dict, sector: str) -> list:
    """JSON avec clé 'conditions' (structures hétérogènes) → faits.
    Gère : nom, symptomes, classification (dict), etapes (dict),
    traitement, seuils, conduite, methode, signes_indicateurs...
    """
    facts = []
    conditions = data.get('conditions', {})
    # malaria utilise 'pathologies' et diseases utilise 'maladies'/'modules'
    if not conditions:
        conditions = data.get('pathologies', {})
    if not conditions and isinstance(data.get('modules'), dict):
        conditions = {k: v for k, v in data['modules'].items()
                      if isinstance(v, dict) and ('nom' in v or any(
                          kk in v for kk in ('symptomes', 'traitement', 'conduite')))}

    items = conditions.items() if isinstance(conditions, dict) else [
        (str(c.get('nom', c.get('condition', f'cond_{i}'))), c)
        for i, c in enumerate(conditions) if isinstance(c, dict)]

    for key, info in items:
        if not isinstance(info, dict):
            continue
        # Nom propre si dispo, sinon la clé
        nom = str(info.get('nom', key)).replace('_', ' ')
        # Symptômes (souvent 'symptomes' ou 'signes_indicateurs')
        for sym_key in ('symptomes', 'signes_indicateurs', 'signes_cliniques', 'signes'):
            syms = info.get(sym_key, [])
            if isinstance(syms, list):
                for sym in syms[:12]:
                    facts.append((nom, 'présente_symptôme', str(sym), sector))
                break
        # Aplatir toutes les autres valeurs (traitement, conduite, classification, etapes...)
        for k, v in info.items():
            if k in ('nom', 'symptomes', 'signes_indicateurs', 'signes_cliniques', 'signes'):
                continue
            if isinstance(v, dict):
                # Classification / etapes : chaque sous-item devient un fait
                for sk, sv in v.items():
                    sub = _flatten_value(sk, sv)
                    for path, txt in sub:
                        facts.append((nom, f'{k}_{path}', txt, sector))
            elif isinstance(v, list):
                for i, item in enumerate(v[:10]):
                    if isinstance(item, dict):
                        for sk2, sv2 in item.items():
                            sub = _flatten_value(sk2, sv2)
                            for path, txt in sub:
                                facts.append((nom, f'{k}_{path}', txt, sector))
                    else:
                        facts.append((nom, k, str(item), sector))
            elif isinstance(v, (str, int, float, bool)):
                s = str(v).strip()
                if len(s) > 1 and len(s) < 300:
                    facts.append((nom, k, s, sector))
    return facts


def extract_facts_from_medicaments(data: dict, sector: str) -> list:
    """vital_ka_pharmacie.json → faits sur les médicaments."""
    facts = []
    meds = data.get('medicaments', {})
    if isinstance(meds, list):
        for m in meds:
            nom = str(m.get('nom', '')).replace('_', ' ')
            if not nom:
                continue
            for k in ['classe', 'voie', 'dose_adulte', 'dose_enfant',
                      'dose_pediatrique', 'grossesse', 'contre_indications',
                      'effets_secondaires', 'stockage']:
                if m.get(k):
                    facts.append((nom, k, str(m[k]), sector))
            for ind in m.get('indications', []):
                facts.append((nom, 'indication', str(ind), sector))
    elif isinstance(meds, dict):
        for nom, m in meds.items():
            nom = str(nom).replace('_', ' ')
            if not isinstance(m, dict):
                continue
            for k in ['classe', 'voie', 'dose_adulte', 'dose_enfant',
                      'dose_pediatrique', 'grossesse', 'contre_indications',
                      'effets_secondaires', 'stockage']:
                if m.get(k):
                    facts.append((nom, k, str(m[k]), sector))
            for ind in m.get('indications', []):
                facts.append((nom, 'indication', str(ind), sector))

    # Interactions médicamenteuses
    inter = data.get('interactions_medicamenteuses', {})
    if isinstance(inter, dict):
        for pair, desc in inter.items():
            p = str(pair).replace('_', ' + ')
            facts.append((p, 'interaction', str(desc), sector))
    return facts


def extract_facts_from_plantes(data: dict, sector: str) -> list:
    """vital_ka_phytotherapie.json → faits sur les plantes médicinales."""
    facts = []
    plantes = data.get('plantes', {})
    if isinstance(plantes, list):
        for p in plantes:
            nom = str(p.get('nom', '')).replace('_', ' ')
            if not nom:
                continue
            for k in ['indication', 'usage', 'mode_preparation', 'dose',
                      'contre_indication', 'effets_secondaires', 'partie_utilisee']:
                if p.get(k):
                    val = p[k]
                    if isinstance(val, list):
                        for v in val:
                            facts.append((nom, k, str(v), sector))
                    else:
                        facts.append((nom, k, str(val), sector))
    elif isinstance(plantes, dict):
        for nom, p in plantes.items():
            nom = str(nom).replace('_', ' ')
            if not isinstance(p, dict):
                continue
            for k in ['indication', 'usage', 'mode_preparation', 'dose',
                      'contre_indication', 'effets_secondaires', 'partie_utilisee']:
                if p.get(k):
                    val = p[k]
                    if isinstance(val, list):
                        for v in val:
                            facts.append((nom, k, str(v), sector))
                    else:
                        facts.append((nom, k, str(val), sector))
    return facts


def extract_facts_from_vaccins(data: dict, sector: str) -> list:
    """vital_ka_vaccination.json → faits sur les vaccins."""
    facts = []
    vaccins = data.get('vaccins', {})
    items = vaccins.items() if isinstance(vaccins, dict) else [
        (str(v.get('nom', i)), v) for i, v in enumerate(vaccins)]
    for nom, v in items:
        nom = str(nom).replace('_', ' ')
        if not isinstance(v, dict):
            continue
        for k in ['age_recommande', 'dose', 'voie', 'contre_indications',
                  'effets_secondaires', 'calendrier', 'maladies_previent']:
            if v.get(k):
                facts.append((nom, k, str(v[k]), sector))
    return facts


def load_clinical_cases(max_cases: int = MAX_CLINICAL_CASES) -> list:
    """real_clinical_dataset.json → faits cliniques (symptômes → diagnostic).
    Limité à ~MAX_FACTS_PER_SECTOR pour équilibrer avec les autres secteurs."""
    path = _ENGINE / "data" / "real_clinical_dataset.json"
    if not path.exists():
        print("  ⚠ real_clinical_dataset.json absent")
        return []
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []

    facts = []
    seen_diags = set()
    for case in data[:max_cases]:
        diag = str(case.get('diagnosis', '')).strip()
        symptoms = str(case.get('symptoms', '')).strip()
        if not diag or not symptoms:
            continue
        diag = diag.replace('_', ' ').strip()
        syms = [s.strip() for s in symptoms.split(',') if s.strip()]
        # Échantillonner par diagnostic pour couvrir tous les cas cliniques
        if len(facts) >= MAX_FACTS_PER_SECTOR:
            break
        for sym in syms[:8]:
            facts.append((diag, 'présente_symptôme', sym, 'CLINIQUE'))
        if case.get('age') and diag not in seen_diags:
            facts.append((diag, 'âge_fréquent', str(case['age']), 'CLINIQUE'))
        if case.get('gender') and diag not in seen_diags:
            facts.append((diag, 'sexe_fréquent', str(case['gender']), 'CLINIQUE'))
        seen_diags.add(diag)
    return facts


def load_general_kb() -> list:
    """knowledge_base_50k.npz → faits généraux de santé (domaine GENERAL).
    Ne garde que les faits liés à la santé/médecine pour éviter d'ajouter
    des secteurs non médicaux (CULTURE, ASTRONOMIE...) au mélange."""
    facts = []
    health_keywords = ('santé', 'sante', 'maladie', 'médical', 'medical', 'symptôme',
                       'symptome', 'traitement', 'médecin', 'medecin', 'hôpital',
                       'hopital', 'médicament', 'medicament', 'patient', 'diagnostic',
                       'infection', 'virus', 'bactérie', 'bacterie', 'fièvre', 'fievre',
                       'douleur', 'corps', 'sang', 'cœur', 'coeur', 'cerveau', 'vaccin')
    for src in ["data/bootstrapper_output/knowledge_base_50k.npz"]:
        path = _ENGINE / src
        if not path.exists():
            continue
        data = np.load(str(path), allow_pickle=True)
        arr = data[list(data.keys())[0]]
        for row in arr[:20000]:
            if len(row) >= 4:
                text = f"{row[0]} {row[1]} {row[2]}".lower()
                if any(kw in text for kw in health_keywords):
                    facts.append((str(row[0]), str(row[1]), str(row[2]), 'GENERAL'))
    return facts


def build_medical_facts() -> list:
    """Construit la base de faits médicale complète."""
    facts = []
    sources = {
        # (nom_fichier, extracteur, secteur)
        'vital_ka_diseases':     (extract_facts_from_diseases, 'MALADIES'),
        'vital_ka_malaria':      (extract_facts_from_conditions, 'PALUDISME'),
        'vital_ka_pediatrie':    (extract_facts_from_conditions, 'PEDIATRIE'),
        'vital_ka_vih_tb':       (extract_facts_from_conditions, 'VIH_TB'),
        'vital_ka_urgences':     (extract_facts_from_conditions, 'URGENCES'),
        'vital_ka_sante_mentale':(extract_facts_from_conditions, 'SANTE_MENTALE'),
        'vital_ka_ntd':          (extract_facts_from_conditions, 'MNT'),
        'vital_ka_mere_enfant':  (extract_facts_from_conditions, 'MERE_ENFANT'),
        'vital_ka_chroniques':   (extract_facts_from_conditions, 'CHRONIQUES'),
        'vital_ka_malnutrition': (extract_facts_from_conditions, 'NUTRITION'),
        'vital_ka_pharmacie':    (extract_facts_from_medicaments, 'PHARMACIE'),
        'vital_ka_phytotherapie':(extract_facts_from_plantes, 'PHYTOTHERAPIE'),
        'vital_ka_vaccination':  (extract_facts_from_vaccins, 'VACCINATION'),
    }

    for name, (extractor, sector) in sources.items():
        data = load_vital_ka_json(name)
        if data is None:
            print(f"  ⚠ {name}.json absent")
            continue
        f = extractor(data, sector)
        print(f"  📄 {name:<28} → {len(f):>5d} faits ({sector})")
        facts.extend(f)

    # Cas cliniques réels
    print(f"\n  🏥 Chargement des cas cliniques réels (max {MAX_CLINICAL_CASES})...")
    clinical = load_clinical_cases()
    print(f"  📄 real_clinical_dataset.json → {len(clinical):,} faits (CLINIQUE)")
    facts.extend(clinical)

    # KB générale
    print(f"\n  📚 Chargement de la KB générale...")
    general = load_general_kb()
    print(f"  📄 knowledge_base_50k.npz → {len(general):,} faits (GENERAL)")
    facts.extend(general)

    print(f"\n  ✅ TOTAL : {len(facts):,} faits médicaux")
    return facts


# ════════════════════════════════════════════════════════════════
# 2. GROUPEMENT PAR SECTEUR + CONVERSION EN PHRASES
# ════════════════════════════════════════════════════════════════

def group_by_sector(facts: list) -> dict:
    """Groupe les faits par secteur médical, trié par taille décroissante.
    Garde uniquement les secteurs médicaux + GENERAL (rejet des secteurs
    non médicaux hérités de la KB générale : CULTURE, ASTRONOMIE...)."""
    MEDICAL_SECTORS = {
        'MALADIES', 'PALUDISME', 'PEDIATRIE', 'VIH_TB', 'URGENCES',
        'SANTE_MENTALE', 'MNT', 'MERE_ENFANT', 'CHRONIQUES', 'NUTRITION',
        'PHARMACIE', 'PHYTOTHERAPIE', 'VACCINATION', 'CLINIQUE', 'GENERAL',
    }
    groups = defaultdict(list)
    for s, r, o, sec in facts:
        sec = str(sec).strip().upper()
        if sec in MEDICAL_SECTORS:
            groups[sec].append((str(s), str(r), str(o), sec))
    sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))
    print(f"\n  Secteurs médicaux : {len(groups)}")
    for sec, items in sorted_groups[:20]:
        print(f"    {sec}: {len(items):,} faits")
    return dict(sorted_groups)


def fact_to_sentence(fact: tuple) -> str:
    """Convertit un fait médical en 1 phrase naturelle."""
    s, r, o, sec = fact
    s = s.strip().strip('"\'')
    o = o.strip().strip('"\'')
    r_clean = r.strip().lower().replace(' ', '_')

    # Règles médicales spécifiques
    if r_clean in ('présente_symptôme', 'presente_symptome', 'symptome', 'symptômes'):
        return f"{s} présente le symptôme {o}."
    if r_clean in ('indication',):
        return f"{s} est indiqué pour {o}."
    if r_clean.startswith('traitement'):
        return f"Le traitement {r_clean.replace('traitement_', '')} de {s} est {o}."
    if r_clean in ('dose_adulte', 'dose_enfant', 'dose_pediatrique', 'dose'):
        return f"La dose de {s} est {o}."
    if r_clean == 'contre_indications':
        return f"Contre-indication de {s} : {o}."
    if r_clean == 'effets_secondaires':
        return f"Les effets secondaires de {s} sont {o}."
    if r_clean == 'gravité':
        return f"La gravité de {s} est {o}."
    if r_clean == 'conduite_à_tenir':
        return f"Conduite à tenir pour {s} : {o}."
    if r_clean == 'délai_consultation':
        return f"Le délai de consultation pour {s} est {o}."
    if r_clean == 'interaction':
        return f"Interaction : {s} → {o}."
    if r_clean == 'classe':
        return f"{s} appartient à la classe {o}."
    if r_clean == 'voie':
        return f"La voie d'administration de {s} est {o}."
    if r_clean == 'grossesse':
        return f"{s} pendant la grossesse : {o}."
    if r_clean == 'âge_fréquent':
        return f"{s} survient fréquemment à l'âge {o}."
    if r_clean == 'sexe_fréquent':
        return f"{s} survient fréquemment chez {o}."
    if r_clean in ('prévention', 'prevention'):
        return f"La prévention de {s} est {o}."
    if r_clean == 'urgences' or r_clean == 'urgence':
        return f"{s} est une urgence : {o}."

    # Règles génériques
    if 'est_un' in r_clean or 'constitue' in r_clean:
        return f"{s} est {o}."
    if 'signifie' in r_clean:
        return f"{s} signifie {o}."
    return f"{s} {r.replace('_', ' ')} {o}."


# ════════════════════════════════════════════════════════════════
# 3. MODÈLE HWAT MINI (inline pour indépendance)
# ════════════════════════════════════════════════════════════════

class MiniEmbedding(nn.Module):
    def __init__(self, vocab_size, dim, max_len):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, dim)
        t = torch.arange(max_len, dtype=torch.float32)
        ks = torch.arange(dim, dtype=torch.float32)
        omegas = 0.1 * (math.pi / 0.1) ** (ks / max(dim - 1, 1))
        self.register_buffer('pos', omegas[None] * t[:, None])

    def forward(self, ids):
        return self.token_emb(ids) + self.pos[:ids.shape[0]]


class MiniAttention(nn.Module):
    def __init__(self, dim, n_heads):
        super().__init__()
        self.dim, self.n_heads = dim, n_heads
        self.head_dim = dim // n_heads
        self.Wq = nn.Linear(dim, dim)
        self.Wk = nn.Linear(dim, dim)
        self.Wv = nn.Linear(dim, dim)
        self.Wo = nn.Linear(dim, dim)

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


class MiniBlock(nn.Module):
    def __init__(self, dim, n_heads):
        super().__init__()
        self.attn = MiniAttention(dim, n_heads)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * 4), nn.GELU(),
            nn.Linear(dim * 4, dim)
        )
        self.ln1 = nn.LayerNorm(dim)
        self.ln2 = nn.LayerNorm(dim)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class MiniHWAT(nn.Module):
    """HWAT miniature pour un domaine spécialisé."""
    def __init__(self, vocab_size, dim=DIM, n_blocks=N_BLOCKS,
                 n_heads=N_HEADS, max_len=MAX_LEN):
        super().__init__()
        self.embed = MiniEmbedding(vocab_size, dim, max_len)
        self.blocks = nn.ModuleList([
            MiniBlock(dim, n_heads) for _ in range(n_blocks)
        ])
        self.ln_out = nn.LayerNorm(dim)
        self.lm_head = nn.Linear(dim, vocab_size)

    def forward(self, ids):
        x = self.embed(ids)
        for blk in self.blocks:
            x = blk(x)
        return self.lm_head(self.ln_out(x))


# ════════════════════════════════════════════════════════════════
# 4. ENTRAÎNEMENT D'UN HOLOGRAMME MÉDICAL
# ════════════════════════════════════════════════════════════════

def train_hologram(sector: str, facts: list, output_dir: Path) -> dict:
    """Entraîne un HWAT spécialisé sur un secteur médical."""
    t0 = time.time()
    n_facts = len(facts)

    # Échantillonner si trop de faits (équilibre entre secteurs)
    if n_facts > MAX_FACTS_PER_SECTOR:
        facts = facts[:MAX_FACTS_PER_SECTOR]
        n_facts = len(facts)

    # Corpus
    sentences = [fact_to_sentence(f) for f in facts]
    text = ' '.join(sentences)
    if len(text) > MAX_CHARS_PER_DOMAIN:
        text = text[:MAX_CHARS_PER_DOMAIN]
        print(f"     ⚠ {sector} tronqué à {MAX_CHARS_PER_DOMAIN:,} chars")

    # Tokenisation caractères (simple, rapide, vocab local au domaine)
    chars = sorted(set(text))
    c2i = {c: i for i, c in enumerate(chars)}
    i2c = {i: c for i, c in enumerate(chars)}
    vocab_size = len(chars)
    if vocab_size > VOCAB_PER_DOMAIN:
        # Limiter le vocabulaire : garder les caractères les plus fréquents
        counts = Counter(text)
        keep = [c for c, _ in counts.most_common(VOCAB_PER_DOMAIN)]
        c2i = {c: i for i, c in enumerate(keep)}
        i2c = {i: c for i, c in enumerate(keep)}
        vocab_size = VOCAB_PER_DOMAIN
    ids = np.array([c2i.get(c, 0) for c in text], dtype=np.int64)

    # Batches
    seq_len = MAX_LEN
    n_batches = max(1, (len(ids) - 1) // seq_len)
    batches = []
    for i in range(min(n_batches, 2000)):  # max 2000 batches/époque
        start = i * seq_len
        x = torch.from_numpy(ids[start:start + seq_len].copy())
        y = torch.from_numpy(ids[start + 1:start + 1 + seq_len].copy())
        if len(x) < seq_len or len(y) < seq_len:
            break
        batches.append((x, y))

    if len(batches) < 5:
        return {'sector': sector, 'status': 'skipped', 'reason': 'trop peu de batches'}

    # Modèle
    model = MiniHWAT(vocab_size, dim=DIM, n_blocks=N_BLOCKS,
                     n_heads=N_HEADS, max_len=MAX_LEN)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.CrossEntropyLoss()

    # Entraînement
    for epoch in range(1, EPOCHS + 1):
        epoch_loss = 0.0
        for x, y in batches:
            logits = model(x)
            loss = criterion(logits, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

    avg_loss = epoch_loss / len(batches)
    ppl = math.exp(avg_loss)
    dt = time.time() - t0

    # Sauvegarde
    save_path = output_dir / f"{sector}.pt"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'sector': sector,
        'model_state': model.state_dict(),
        'char_to_id': c2i,
        'id_to_char': i2c,
        'vocab_size': vocab_size,
        'config': {'dim': DIM, 'n_blocks': N_BLOCKS, 'n_heads': N_HEADS, 'max_len': MAX_LEN},
        'n_facts': n_facts,
        'avg_loss': avg_loss,
        'ppl': ppl,
    }, str(save_path))

    print(f"  ✅ {sector:<20} | {n_facts:>6,} faits | "
          f"loss={avg_loss:.3f} ppl={ppl:.1f} | {dt:.0f}s | {save_path.name}")

    # ── Sauvegarder les faits originaux pour retrieval ──
    facts_path = output_dir / f"{sector}_facts.json"
    with open(facts_path, 'w', encoding='utf-8') as f:
        json.dump([{'s': f[0], 'r': f[1], 'o': f[2], 'sec': f[3]}
                   for f in facts], f, ensure_ascii=False, indent=1)
    print(f"     📋 {len(facts)} faits sauvegardés → {facts_path.name}")

    return {
        'sector': sector,
        'path': str(save_path),
        'n_facts': n_facts,
        'vocab_size': vocab_size,
        'loss': avg_loss,
        'ppl': ppl,
    }


# ════════════════════════════════════════════════════════════════
# 5. CONSTRUCTION DU ROUTEUR + TEST
# ════════════════════════════════════════════════════════════════

def build_router(holograms: list, output_dir: Path):
    """Construit le routeur spectral : centroïdes + mapping."""
    router = {
        'domains': {},
        'default': 'MALADIES',
    }

    for h in holograms:
        sector = h['sector']
        router['domains'][sector] = {
            'path': h['path'],
            'n_facts': h['n_facts'],
            'ppl': h['ppl'],
            'vocab_size': h.get('vocab_size', 0),
        }

    router_path = output_dir / "router.json"
    with open(router_path, 'w', encoding='utf-8') as f:
        json.dump(router, f, indent=2, ensure_ascii=False)

    print(f"\n  📡 Routeur sauvegardé: {router_path}")
    print(f"     Domaines: {len(router['domains'])}")
    return router


def test_hologram_retrieval(output_dir: Path):
    """Teste le retrieval : requête → top-K faits les plus similaires."""
    facts_dir = output_dir
    test_queries = [
        "fièvre",
        "paludisme",
        "toux",
        "vaccin",
    ]
    print(f"\n  🧪 Test retrieval ({len(test_queries)} requêtes) :")
    for q in test_queries:
        results = []
        for facts_path in sorted(facts_dir.glob("*_facts.json")):
            with open(facts_path, encoding='utf-8') as f:
                facts = json.load(f)
            sector = facts_path.name.replace('_facts.json', '')
            for fact in facts[:200]:
                text = f"{fact['s']} {fact['r']} {fact['o']}"
                # Score simple : occurrence de mots de la requête
                q_words = set(q.lower().split())
                score = sum(1 for w in q_words if w in text.lower())
                if score > 0:
                    results.append((score, sector, fact))
        results.sort(key=lambda x: -x[0])
        print(f"    '{q}' → {len(results)} faits, top: "
              f"{results[0][1] if results else '—'} | "
              f"{results[0][2]['s'] if results else ''} {results[0][2]['r'] if results else ''} "
              f"{results[0][2]['o'][:60] if results else ''}")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("═" * 65)
    print("  🏥 HOLOGRAMMES HWAT MÉDICAUX — Experts par spécialité")
    print("═" * 65)

    # 1. Construire la base de faits médicale
    print("\n📂 Construction de la base de faits médicale...")
    all_facts = build_medical_facts()

    # 2. Grouper par secteur
    groups = group_by_sector(all_facts)

    # 3. Filtrer les secteurs éligibles
    output_dir = _ENGINE / "data" / "medical_holograms"
    output_dir.mkdir(parents=True, exist_ok=True)

    eligible = [(sec, facts) for sec, facts in groups.items()
                if len(facts) >= MIN_FACTS and len(sec.strip()) > 2]
    eligible = eligible[:MAX_DOMAINS]

    print(f"\n🎯 {len(eligible)} domaines éligibles (≥{MIN_FACTS} faits)")
    print(f"   Configuration : dim={DIM}, blocs={N_BLOCKS}, époques={EPOCHS}")
    print()

    # 4. Entraîner un hologramme par domaine
    t0_total = time.time()
    results = []

    for i, (sector, facts) in enumerate(eligible):
        print(f"  [{i+1}/{len(eligible)}] {sector} ({len(facts):,} faits)...")
        result = train_hologram(sector, facts, output_dir)
        results.append(result)
        gc.collect()

    dt_total = time.time() - t0_total
    trained = [r for r in results if 'loss' in r]
    print(f"\n  ⏱️ Temps total: {dt_total/60:.1f} min "
          f"({dt_total/max(len(eligible),1):.0f}s/hologramme)")

    # 5. Construire le routeur
    build_router(trained, output_dir)

    # 6. Test retrieval
    test_hologram_retrieval(output_dir)

    # 7. Résumé
    print(f"\n{'═'*65}")
    print(f"  RÉSUMÉ")
    print(f"{'═'*65}")
    print(f"  Hologrammes entraînés : {len(trained)}")
    print(f"  Temps total : {dt_total/60:.1f} min")
    if trained:
        best = min(trained, key=lambda r: r['ppl'])
        worst = max(trained, key=lambda r: r['ppl'])
        print(f"  Meilleur : {best['sector']} (PPL {best['ppl']:.1f})")
        print(f"  Moins bon : {worst['sector']} (PPL {worst['ppl']:.1f})")
    print(f"\n  ✅ Hologrammes médicaux prêts dans : {output_dir}/")


if __name__ == "__main__":
    main()