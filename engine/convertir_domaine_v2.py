#!/usr/bin/env python3
"""
CONVERTISSEUR GÉNÉRIQUE V1 → V2 — porté dans l'engine KA (10/08/2026)
=====================================================================
Portage autonome du module prouvé dans le prototype
(cerveau_harmonique_v1/engine/convertir_domaine_v2.py). Les briques de
mesure (tokeniseur, espace PPMI+attraction, résonance) sont intégrées
ici pour ne dépendre que de l'engine (resonance_semantique ✓,
verificateur_coherence ✓, hologram_store ✓).

Processus (cahier des charges, mesures du 10/08/2026) :
    1. diagnostic (contradictions, artefacts, sujets isolés)
    2. tri + assainissement tracé (corrections expertes, relations
       multi-valuées, relations parasites, vocabulaire contrôlé,
       objets-pays sur relations non-locales, vote majoritaire ≥ 2)
    3. complétion optionnelle (fusion de faits v2 vérifiés)
    4. validation (3 règles d'or)
    5. benchmark par secteur : rappel@5 EXACT (relations fonctionnelles)
       vs VRAI (relations relationnelles) + gate 0 FAUX (≥ 2 ancres)
    6. cache disque (rapport_conversion.json → skip si ACCEPTÉ)

Point d'entrée de production : HologramStore.ensure_v2(holo_id)
(hologram_store.py) + route /api/store/convert/<holo_id> (ka_server.py).
Config par domaine : engine/data/corrections_domaines.json
Rapports : engine/data/domaine_converti_<holo_id>/
"""

import os, sys, json, re, time
from collections import Counter
from typing import List, Tuple, Optional

import numpy as np

# =============================================================================
# BRIGUES DE MESURE (portées du prototype — benchmark_densite.py)
# =============================================================================

def _mots(t):
    return re.findall(r"[a-zàâäéèêëîïôöùûüçœ]+", str(t).lower())


STOP = set((
    "le la les de des du une un et est a dans que qui pas ne sur pour avec je tu "
    "il elle on nous vous ils elles ce cet cette ces mon ton son ma ta sa au aux en ou "
    "mais donc or ni car si comme plus moins fois divise egal quel quelle quels quelles "
    "comment pourquoi combien où sont était avoir faire calculer trouver donner resoudre "
    "expliquer connaitre savoir parler ecrire lire quelle quelqu un plusieurs beaucoup peu "
    "tres bien mal tout toute tous toutes autre autres meme entre vers sous chez depuis "
    "pendant avant apres contre sans parmi l la d s qu n t y sa son ses"
).split())


def _mots_nb(t):
    """Tokeniseur sensible aux NOMBRES significatifs (≥ 2 chiffres) :
    les valeurs numériques portent le sens (superficies 10 km², populations
    67 millions) ; les nombres à 1 chiffre sont génériques (bruit)."""
    toks = _mots(t)
    for m in re.finditer(r"[0-9]{2,}(?:[.,][0-9]+)?", str(t)):
        toks.append(m.group(0).replace(",", "."))
    return toks


def construire_espace(faits, min_freq=1, tokeniseur=None):
    """Espace THU : PPMI (fenêtre = fait) + attraction pure (120 itérations,
    init spirale du tokenizer). tokeniseur : défaut _mots_nb."""
    if tokeniseur is None:
        tokeniseur = _mots_nb
    count = {}
    for s, r, o in faits:
        for w in tokeniseur(f"{s} {r} {o}"):
            if len(w) > 2 and w not in STOP:
                count[w] = count.get(w, 0) + 1
    vocab = ["<BOS>", "<EOS>", "<UNK>", "<PAD>"] + \
            [w for w, c in sorted(count.items(), key=lambda x: -x[1])
             if c >= min_freq]
    w2i = {w: i for i, w in enumerate(vocab)}
    V = len(vocab)
    if V < 8:
        return None
    import importlib.util as iu
    _HRG = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "harmonic_training", "model",
        "harmonic_resonance_generator.py")
    spec = iu.spec_from_file_location("hrg", _HRG)
    hrg = iu.module_from_spec(spec)
    spec.loader.exec_module(hrg)
    tok = hrg.TokeniseurOndes(vocab, use_pi_over_6=True)
    cooc = np.zeros((V, V))
    toks_faits = []
    for s, r, o in faits:
        toks = [w2i[w] for w in tokeniseur(f"{s} {r} {o}") if w in w2i]
        toks_faits.append(toks)
        for i in range(len(toks)):
            for j in range(len(toks)):
                if i != j:
                    cooc[toks[i], toks[j]] += 1.0
    total = cooc.sum()
    if total <= 0:
        return None
    marginal = cooc.sum(axis=1, keepdims=True) + 1e-10
    expected = (marginal @ cooc.sum(axis=0, keepdims=True)) / total
    pmi = np.log((cooc + 1e-10) / (expected + 1e-10))
    ppmi = np.clip(np.maximum(0, pmi), 0, 10)
    kx = tok._kx[:V].copy().astype(np.float64)
    ky = tok._ky[:V].copy().astype(np.float64)
    ii, jj = np.where(ppmi > 0.01)
    sv = ppmi[ii, jj]
    for _ in range(120):
        gkx = np.zeros(V)
        gky = np.zeros(V)
        for idx in range(len(ii)):
            i, j = ii[idx], jj[idx]
            if i == j:
                continue
            g = 2.0 * float(sv[idx])
            gkx[i] += g * (kx[i] - kx[j])
            gky[i] += g * (ky[i] - ky[j])
        kx -= 0.005 * gkx
        ky -= 0.005 * gky
        r = np.sqrt(kx**2 + ky**2)
        m = r > 6.0
        kx[m] *= 6.0 / (r[m] + 1e-10)
        ky[m] *= 6.0 / (r[m] + 1e-10)
        kx -= kx.mean()
        ky -= ky.mean()
    d = np.sqrt((kx[:, None] - kx[None, :])**2 + (ky[:, None] - ky[None, :])**2)
    return {"w2i": w2i, "kx": kx, "ky": ky,
            "sigma": float(np.median(d[np.triu_indices(V, 1)])),
            "toks": toks_faits}

# =============================================================================
# NORMALISATION + RÈGLES GÉNÉRIQUES
# =============================================================================

def _norm_entite(s):
    s = str(s).lower().strip()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"), ("à", "a"),
                 ("â", "a"), ("ä", "a"), ("î", "i"), ("ï", "i"), ("ô", "o"),
                 ("ö", "o"), ("ù", "u"), ("û", "u"), ("ü", "u"), ("ç", "c"),
                 ("œ", "oe"), ("æ", "ae")):
        s = s.replace(a, b)
    return " ".join(s.split())


def _norm_rel(r):
    """Normalisation des RELATIONS (minuscules, sans accents). Mesure
    10/08/2026 : sans elle, les clés de contradiction divergent et des
    FAUX passent (« australie est situé sur le continent Pays-Bas »)."""
    return _norm_entite(r)


RELATIONS_NUMERIQUES = {
    "a une population de", "a une superficie de", "a pour coordonnées",
    "a pour nombre de membres",
    # Relations TEMPORELLES : les années (« est mort en 1579 ») sont des
    # faits légitimes — sans elles, 52 643 dates du secteur HISTOIRE
    # étaient écartées à tort (mesure 10/08/2026)
    "a été fondé en", "a été découvert en", "a été découverte en",
    "a été construit en", "a été construite en", "a été signé en",
    "a été créé en", "a été créée en", "a été inauguré en",
    "a pris fin en", "a eu lieu en", "a commencé en",
    "a déclaré l'indépendance en", "a régné de", "a été élu en",
    "a été couronné en", "a été publié en", "a été écrit en",
    "a été composé en", "a été peint en", "a été inventé en",
    "est mort en", "est née en", "est né en", "date de",
}

RELATIONS_LOCALISATION = {
    "est situe en", "est situe a", "est situe sur le continent",
    "partage une frontiere avec", "a son siege a", "est originaire de",
    "est localise dans", "fait partie de", "appartient a",
    "se trouve en", "se situe en", "est situe dans",
}

PAYS_MONDE = {
    "france", "espagne", "italie", "allemagne", "royaume-uni", "portugal",
    "autriche", "suisse", "belgique", "pays-bas", "luxembourg", "irlande",
    "grece", "suede", "norvege", "finlande", "danemark", "pologne",
    "republique tcheque", "hongrie", "roumanie", "bulgarie", "ukraine",
    "russie", "turquie", "egypte", "maroc", "algerie", "tunisie", "senegal",
    "cote d ivoire", "cameroun", "republique democratique du congo", "kenya",
    "nigeria", "ethiopie", "afrique du sud", "etats-unis", "canada",
    "mexique", "bresil", "argentine", "chili", "colombie", "perou", "chine",
    "japon", "inde", "coree du sud", "australie", "nouvelle-zelande",
    "kiribati", "tuvalu", "tonga", "samoa", "iles salomon",
    "papouasie-nouvelle-guinee", "palaos", "gabon", "uruguay", "slovaquie",
    "ecosse", "soudan", "pakistan", "nepal", "bhoutan", "bangladesh",
    "birmanie", "iran", "irak", "syrie", "libye", "mali", "niger", "tchad",
    "ghana", "angola", "mozambique", "zimbabwe", "zambie", "botswana",
    "namibie", "madagascar", "oceanie", "europe", "asie", "afrique",
    "amerique", "antarctique",
    # Complément (mesure 10/08/2026 — « guinee equatoriale » manquait :
    # « theoreme de castigliano est mathématicien guinee equatoriale » FAUX)
    "guinee", "guinee equatoriale", "guinee-bissau", "togo", "benin",
    "burkina faso", "rwanda", "burundi", "ouganda", "tanzanie", "malawi",
    "lesotho", "eswatini", "mauritanie", "eritree", "djibouti", "somalie",
    "liberia", "sierra leone", "gambie", "guinee-bissao", "cap-vert",
    "comores", "maurice", "seychelles", "sao tome et principe",
    "yemen", "oman", "emirats arabes unis", "arabie saoudite", "koweit",
    "qatar", "bahrein", "jordanie", "liban", "israel", "georgie", "armenie",
    "azerbaidjan", "kazakhstan", "ouzbekistan", "turkmenistan",
    "kirghizistan", "tadjikistan", "mongolie", "taiwan", "thailande",
    "vietnam", "laos", "cambodge", "malaisie", "singapour", "indonesie",
    "philippines", "sri lanka", "maldives", "fidji", "vanuatu", "tonga",
    "micronisie", "marshall", "belize", "guatemala", "honduras",
    "salvador", "nicaragua", "costa rica", "panama", "haiti",
    "republique dominicaine", "cuba", "jamaique", "trinite et tobago",
    "guyana", "suriname", "paraguay", "bolivie", "equateur", "venezuela",
    "albanie", "serbie", "croatie", "bosnie-herzegovine", "macedoine",
    "montenegro", "kosovo", "slovenie", "lituanie", "lettonie", "estonie",
    "moldavie", "bielorussie", "islande", "malte", "chypre", "monaco",
    "andorre", "saint-marin", "liechtenstein", "vatican",
}

# Mots anglais pour la détection de contamination bilingue (relations et
# objets anglais dans les faits français — KB source bilingue, mesuré
# 10/08/2026 : « cte | allows | modular query construction with with clause »).
MOTS_ANGLAIS = {
    "the", "of", "and", "for", "is", "are", "with", "that", "this", "from",
    "was", "were", "has", "have", "its", "not", "but", "than", "into",
    "over", "under", "between", "during", "after", "before", "through",
    "against", "without", "within", "allows", "handles", "includes",
    "produces", "consists", "refers", "provides", "uses", "based", "known",
    "called", "considered", "constitutes", "states", "follows", "describes",
    "occurs", "contains", "supports", "allows", "enables", "balances",
    "functions", "connects", "represents", "operates", "runs", "stores",
    "non", "public", "institution", "classified", "wind", "speed",
    "exceed", "can", "modular", "query", "construction", "within",
    "excel", "triggers", "helps", "builds", "loads", "deploys", "manages",
    "monitors", "streams", "optimizes", "optimize", "processing",
    "language", "tasks", "natural", "automates", "simplifies", "schedules",
    "coordinates", "facilitates", "enforces", "validates", "compresses",
    "indexes", "caches", "routes", "queues", "parses", "compiles",
    "interprets", "executes", "evaluates", "returns", "renders", "use", "uses", "example", "regex", "is", "of", "at", "by", "in", "on", "to", "as", "be", "it", "if", "an", "or", "so", "up", "no", "do", "we", "he", "she", "they", "my", "your", "his", "her", "our", "their"
}

# =============================================================================
# PIPELINE
# =============================================================================

def diagnostiquer(store, holo_id):
    from verificateur_coherence import VerificateurCoherence
    vc = VerificateurCoherence(store)
    rap = vc.analyser(holo_id)
    facts, _ = store.download(holo_id)
    faits = [(s, r, o) for s, r, o, sec in facts]
    sujets = Counter(s for s, r, o in faits)
    isolés = sum(1 for c in sujets.values() if c == 1)
    artefacts = [str(o) for s, r, o in faits
                 if re.search(r"Point\(|ville\d|^-\d{2}-\d{2}T", str(o))
                 or (r not in RELATIONS_NUMERIQUES
                     and re.fullmatch(r"\d+([.,]\d+)?", str(o)))]
    return {
        "n_faits_v1": len(faits),
        "relations_distinctes": len(set(r for s, r, o in faits)),
        "contradictions": rap["contradictions"],
        "taux_contradiction": rap["taux"],
        "sujets_uniques": len(sujets),
        "sujets_isoles": isolés,
        "artefacts_detectes": len(set(artefacts)),
    }


def assainir(faits, cfg):
    """Tri + assainissement (0 FAUX prime — le doute écarte)."""
    conservés, écartés, appliquées = [], [], []
    corrections = {(c[0].lower(), _norm_rel(c[1]), _norm_entite(c[2])): c
                   for c in cfg.get("corrections", [])}
    artefacts = {(a[0].lower(), _norm_rel(a[1]), _norm_entite(a[2])): a[3]
                 for a in cfg.get("artefacts", [])}
    multi = {_norm_rel(m) for m in cfg.get("relations_multi", [])}
    parasites = {_norm_rel(p) for p in cfg.get("relations_parasites", [])}
    numeriques = {_norm_rel(r) for r in RELATIONS_NUMERIQUES}
    controles = {_norm_rel(r): {_norm_entite(o) for o in objets}
                 for r, objets in cfg.get("objets_autorises", {}).items()}
    objets_parasites = {_norm_entite(o)
                        for o in cfg.get("objets_parasites", [])}

    for s, r, o, sec in faits:
        s2, r2, o2 = _norm_entite(s), _norm_rel(r), _norm_entite(o)
        cle = (s2, r2, o2)
        if cle in corrections:
            cs, cr, co, cs2, cr2, co2, just = corrections[cle]
            conservés.append((cs2, cr2, co2, cfg.get("secteur", "DOMAINE")))
            appliquées.append({"fait_v1": (s, r, o), "fait_v2": (cs2, cr2, co2),
                               "justification": just})
            continue
        if cle in artefacts:
            écartés.append({"fait": (s, r, o), "secteur": sec,
                            "raison": artefacts[cle]})
            continue
        # Artefact générique (parsing cassé) — y compris les entités
        # suffixées par un chiffre collé (« Los Angeles6 », « Paris05 »,
        # « Suisse18 ») : ≥ 3 lettres + chiffre en fin de token, pour ne
        # pas écarter les unités (« km2 ») ni les formules (« CO2 »).
        if re.search(r"Point\(|ville\d|^-\d{2}-\d{2}T"
                     r"|[A-Za-zÀ-ÿœ]{3,}[0-9]+$", str(o)) or \
           (r2 not in numeriques
                and re.fullmatch(r"\d+([.,]\d+)?", str(o))):
            écartés.append({"fait": (s, r, o), "secteur": sec,
                            "raison": "artefact de parsing (Point( / entité chiffrée / date tronquée)"})
            continue
        if r2 in parasites:
            écartés.append({"fait": (s, r, o), "secteur": sec,
                            "raison": f"relation hors-thème « {r} » (contamination inter-domaines)"})
            continue
        # Relation ANGLAISE : contamination bilingue du KB source
        # (« cte | allows | modular query construction with with clause »).
        # Mesure 10/08/2026 : ≥ 1 mot anglais dans la relation → écartée
        # (les relations françaises n'en contiennent pas ; « handles »,
        # « enables », « is a » sont des relations anglaises).
        mots_rel = re.findall(r"[a-zà-ÿ]{2,}", r2)
        if sum(1 for w in mots_rel if w in MOTS_ANGLAIS) >= 1:
            écartés.append({"fait": (s, r, o), "secteur": sec,
                            "raison": f"relation anglaise « {r} » (contamination bilingue du KB)"})
            continue
        # Objet ANGLAIS sur relation française (contamination bilingue)
        mots_obj = re.findall(r"[a-zà-ÿ]{2,}", o2)
        if (sum(1 for w in mots_obj if w in MOTS_ANGLAIS) >= 3
                and r2 not in RELATIONS_LOCALISATION):
            écartés.append({"fait": (s, r, o), "secteur": sec,
                            "raison": f"objet anglais « {str(o)[:40]}... » "
                                      f"(contamination bilingue du KB)"})
            continue
        if r2 in controles and o2 not in controles[r2]:
            écartés.append({"fait": (s, r, o), "secteur": sec,
                            "raison": f"objet hors vocabulaire contrôlé de « {r} » "
                                      f"(artefact d'alignement du KB source)"})
            continue
        if (o2 in PAYS_MONDE or o2 in objets_parasites) and \
           r2 not in RELATIONS_LOCALISATION:
            écartés.append({"fait": (s, r, o), "secteur": sec,
                            "raison": f"objet « {o} » = pays/parasite sur relation "
                                      f"non-locale « {r} » (artefact d'alignement)"})
            continue
        conservés.append((s2, r2, o2, cfg.get("secteur", "DOMAINE")))

    groupes = {}
    for i, (s, r, o, sec) in enumerate(conservés):
        if r in multi:
            continue
        groupes.setdefault((s, r), []).append(i)
    à_écarter = set()
    for (s, r), idxs in groupes.items():
        objets = Counter(conservés[i][2] for i in idxs)
        if len(objets) <= 1:
            continue
        gagnant, n_win = objets.most_common(1)[0]
        if n_win >= 2:
            for i in idxs:
                if conservés[i][2] != gagnant:
                    à_écarter.add(i)
        else:
            à_écarter.update(idxs)
    for i in sorted(à_écarter):
        s, r, o, sec = conservés[i]
        écartés.append({"fait": (s, r, o), "secteur": sec,
                        "raison": "valeur non vérifiable (objets multiples sans majorité / minoritaire)"})
    conservés = [f for i, f in enumerate(conservés) if i not in à_écarter]
    return conservés, écartés, appliquées


def valider(faits, cfg):
    relations = {}
    for s, r, o, sec in faits:
        relations[r] = relations.get(r, 0) + 1
    sujets = {}
    for s, r, o, sec in faits:
        sujets[s] = sujets.get(s, 0) + 1
    n_multi = sum(1 for v in sujets.values() if v >= 2)
    densite = n_multi / max(1, len(sujets))
    multi = {_norm_rel(m) for m in cfg.get("relations_multi", [])}
    groupes = {}
    for s, r, o, sec in faits:
        if r in multi:
            continue
        cle = (s, r)
        groupes.setdefault(cle, set()).add(o)
    contradictions = sum(1 for objs in groupes.values() if len(objs) > 1)
    ok = (len(relations) >= 5 and densite >= 0.30 and contradictions == 0
          and len(faits) >= 100)
    return {
        "n_faits": len(faits),
        "relations_distinctes": len(relations),
        "densite_pct": round(densite * 100, 1),
        "contradictions": contradictions,
        "taille_cible": 100,
        "statut": "VALIDE" if ok else "À CORRIGER",
    }


def rappel_secteur(faits, questions, mode="exact"):
    """Rappel@5 d'un secteur (score sujet×objet PUR : sujet-du-fait ×
    objet-pur, hors ancres, hors token de relation du fait, hors sujet
    du fait). mode "exact" / "vrai"."""
    from resonance_semantique import scores_resonance
    esp = construire_espace(faits)
    if esp is None:
        return 0.0, 0.0
    w2i, kx, ky, sigma, toks_faits = (esp["w2i"], esp["kx"], esp["ky"],
                                      esp["sigma"], esp["toks"])
    kx_t = np.asarray(kx)
    ky_t = np.asarray(ky)
    ok_exact = ok_vrai = total = 0
    for (s, r, o) in questions:
        ancres = [w2i[w] for w in _mots_nb(f"{s} {r}") if w in w2i and w not in STOP]
        if not ancres:
            continue
        total += 1
        kx_q = np.asarray([kx[t] for t in ancres])
        ky_q = np.asarray([ky[t] for t in ancres])
        scores, _, _, _ = scores_resonance(kx_q, ky_q, np.ones(len(ancres)),
                                           kx_t, ky_t, sigma, mode="max")
        anc_s = [w2i[w] for w in _mots_nb(s) if w in w2i and w not in STOP]
        if not anc_s:
            anc_s = ancres
        kx_s = np.asarray([kx[t] for t in anc_s])
        ky_s = np.asarray([ky[t] for t in anc_s])
        sc_sujet, _, _, _ = scores_resonance(kx_s, ky_s, np.ones(len(anc_s)),
                                             kx_t, ky_t, sigma, mode="max")
        a_set = set(ancres)
        res = []
        for (fs, fr, fo), toks in zip(faits, toks_faits):
            if not toks:
                continue
            tsj = [w2i[w] for w in _mots_nb(fs) if w in w2i and w not in STOP]
            if not tsj:
                continue
            r_toks = [w2i[w] for w in _mots_nb(fr) if w in w2i and w not in STOP]
            comp = [t for t in toks
                    if t not in a_set and t not in r_toks and t not in tsj]
            if not comp:
                continue
            sc = float(np.max(sc_sujet[tsj])) * float(np.max(scores[comp]))
            if sc > 0.01:
                res.append((sc, fs, fr, fo))
        res.sort(key=lambda x: -x[0])
        top5 = res[:5]
        if any(str(fs) == str(s) and str(fo) == str(o) for _, fs, fr, fo in top5):
            ok_exact += 1
        if any(str(fs) == str(s) for _, fs, fr, fo in top5):
            ok_vrai += 1
    return ok_exact / max(1, total), ok_vrai / max(1, total)


HORS_SUJET_DEFAUT = [
    "comment fonctionne un moteur diesel",
    "quelle est la recette du couscous traditionnel",
    "qui a ecrit les miserables",
    "quelle est la densite du mercure liquide",
    "combien de buts a marque lionel messi cette saison",
    "quel est le menu du restaurant ce soir",
    "qui a remporte le tournoi de wimbledon en 2023",
    "comment preparer une pate a crepe",
    "quel est le dernier album de cet artiste",
    "combien de buts a encaisse le gardien cette saison",
]


def benchmarker(faits, cfg, seed=2026, n_questions=20):
    """Rappel@5 par secteur (exact pour fonctionnel, vrai pour relationnel)
    + gate 0 FAUX : couverture ≥ 2 ancres réelles ET confirmation de
    résonance ≥ 1.0 (mesure 10/08/2026 — la couverture seule échoue sur
    les domaines étendus : le vocabulaire du KB couvre presque tout ;
    la confirmation sépare les questions dans-corpus (≥ 1.0) des vraies
    hors-sujet (~0-0,6 en moyenne))."""
    import random
    from resonance_semantique import scores_resonance
    multi = {_norm_rel(m) for m in cfg.get("relations_multi", [])}
    par_relation = {}
    for s, r, o, sec in faits:
        par_relation.setdefault(r, []).append((s, r, o))
    secteurs = []
    for r, v in sorted(par_relation.items()):
        if len(v) < 5:
            continue
        qs = random.Random(seed).sample(v, min(n_questions, len(v)))
        exact, vrai = rappel_secteur(v, qs)
        if r in multi:
            score, metrique = vrai, "vrai"
        else:
            score, metrique = exact, "exact"
        secteurs.append({"secteur": r, "n_faits": len(v), "relationnel": r in multi,
                         "metrique": metrique, "rappel_at_5": round(score, 3),
                         "rappel_exact": round(exact, 3), "rappel_vrai": round(vrai, 3),
                         "critere": score >= 0.50})
    # Gate 0 FAUX : couverture ≥ 2 ancres + confirmation ≥ 1.0
    faits3 = [(s, r, o) for s, r, o, sec in faits]
    esp_global = construire_espace(faits3)
    w2i = esp_global["w2i"] if esp_global else {}
    kx_t = np.asarray(esp_global["kx"]) if esp_global else None
    ky_t = np.asarray(esp_global["ky"]) if esp_global else None
    sigma = esp_global["sigma"] if esp_global else 1.0
    hors_sujet = cfg.get("hors_sujet", HORS_SUJET_DEFAUT)
    n_refus = 0
    for q in hors_sujet:
        ancres = [w2i[w] for w in _mots_nb(q) if w in w2i and w not in STOP]
        if len(ancres) < 2:
            n_refus += 1
            continue
        kx_q = np.asarray([esp_global["kx"][t] for t in ancres])
        ky_q = np.asarray([esp_global["ky"][t] for t in ancres])
        _, _, _, conf = scores_resonance(kx_q, ky_q, np.ones(len(ancres)),
                                         kx_t, ky_t, sigma, mode="max")
        if float(conf) < 1.0:
            n_refus += 1
    return secteurs, n_refus, len(hors_sujet)


def charger_config(chemin_config=None):
    """Tables de conversion par domaine (data/corrections_domaines.json)."""
    chemin_config = chemin_config or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data",
        "corrections_domaines.json")
    with open(chemin_config, encoding="utf-8") as f:
        return json.load(f)


def convertir(store, holo_id, cfg, force=False, out_dir=None, chemin_config=None):
    """Conversion complète v1 → v2 avec cache disque. Retourne
    (statut, rapport, out_dir)."""
    t0 = time.time()
    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = out_dir or os.path.join(base, "data", f"domaine_converti_{holo_id}")
    os.makedirs(out_dir, exist_ok=True)
    rapport_path = os.path.join(out_dir, "rapport_conversion.json")

    if not force and os.path.exists(rapport_path):
        with open(rapport_path, encoding="utf-8") as f:
            ancien = json.load(f)
        if ancien.get("statut") == "ACCEPTÉ":
            return "ACCEPTÉ (cache)", ancien, out_dir

    facts, _ = store.download(holo_id)
    faits = [(s, r, o, sec) for s, r, o, sec in facts]
    diag = diagnostiquer(store, holo_id)
    conservés, écartés, appliquées = assainir(faits, cfg)
    conflits_fusion = []

    for chemin in cfg.get("completions", []):
        chemin = os.path.join(base, chemin)
        if not os.path.exists(chemin):
            continue
        with open(chemin, encoding="utf-8") as f:
            data = json.load(f)
        for d in data["faits"]:
            s, r, o = _norm_entite(d["sujet"]), _norm_rel(d["relation"]), _norm_entite(d["objet"])
            sec = d.get("secteur", cfg.get("secteur", "DOMAINE"))
            doublon = next((i for i, (fs, fr, fo, fsec) in enumerate(conservés)
                            if fs == s and fr == r), None)
            if doublon is not None:
                fs, fr, fo, fsec = conservés[doublon]
                if (o != fo and (len(_mots_nb(o)) > len(_mots_nb(fo))
                                 or "millions" in o or "milliard" in o)):
                    conflits_fusion.append({"cle": (s, r), "v1": fo, "v2": o,
                                            "regle": "valeur la plus précise"})
                    conservés[doublon] = (s, r, o, sec)
                continue
            conservés.append((s, r, o, sec))

    val = valider(conservés, cfg)
    secteurs, n_refus, n_gate = benchmarker(conservés, cfg)
    secteurs_ok = all(s["critere"] for s in secteurs) if secteurs else False
    gate_ok = n_refus == n_gate
    statut = "ACCEPTÉ" if (val["statut"] == "VALIDE" and secteurs_ok and gate_ok) \
             else "REFUSÉ"

    with open(os.path.join(out_dir, "faits.json"), "w", encoding="utf-8") as f:
        json.dump({"faits": [{"sujet": s, "relation": r, "objet": o, "secteur": sec}
                             for s, r, o, sec in conservés]},
                  f, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "validation.json"), "w", encoding="utf-8") as f:
        json.dump(val, f, ensure_ascii=False, indent=2)
    rapport = {
        "domaine_v1": holo_id,
        "diagnostic_v1": diag,
        "corrections_expertes": appliquées,
        "ecartes": écartés,
        "n_ecartes": len(écartés),
        "conflits_fusion": conflits_fusion,
        "n_faits_v2": len(conservés),
        "validation": val,
        "benchmark_secteurs": secteurs,
        "secteurs_ok": sum(1 for s in secteurs if s["critere"]),
        "secteurs_total": len(secteurs),
        "gate_refus": n_refus,
        "gate_total": n_gate,
        "statut": statut,
        "temps_total_s": round(time.time() - t0, 1),
    }
    with open(rapport_path, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    return statut, rapport, out_dir


def afficher_rapport(holo_id, statut, rapport, out_dir):
    d = rapport["diagnostic_v1"]
    v = rapport["validation"]
    print("=" * 74)
    print(f"CONVERSION {holo_id} → v2 : {statut}")
    print("=" * 74)
    print(f"  v1 : {d['n_faits_v1']} faits | {d['contradictions']} contradictions "
          f"({d['taux_contradiction']:.1%}) | {d['sujets_isoles']}/{d['sujets_uniques']} "
          f"sujets isolés | {d['artefacts_detectes']} artefacts")
    print(f"  Corrections expertes : {len(rapport['corrections_expertes'])} | "
          f"écartés : {rapport['n_ecartes']}")
    print(f"  v2 : {v['n_faits']} faits | {v['relations_distinctes']} relations | "
          f"densité {v['densite_pct']}% | {v['contradictions']} contradictions")
    print(f"  Validation : {v['statut']}")
    for s in rapport["benchmark_secteurs"]:
        marque = "✓" if s["critere"] else "✗"
        print(f"    {marque} {s['secteur']:<38} n={s['n_faits']:>3}  "
              f"rappel@5({s['metrique']})={s['rappel_at_5']:.0%}")
    print(f"  Gate hors-sujet : {rapport['gate_refus']}/{rapport['gate_total']} "
          f"refusées  [{'✓' if rapport['gate_refus'] == rapport['gate_total'] else '✗'}]")
    print(f"  → {out_dir}/")
