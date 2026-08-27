"""
🌊 okf_ingest.py — Ingestion automatique via LLM (Oracle Cloud)
=================================================================
Pipeline : Source (texte/URL) → LLM (Phi/Qwen) → faits → .md → hologramme.

Utilise le LLM distant sur Oracle Cloud (Phi-3.5-mini ou Qwen 3B)
pour extraire les connaissances d'un article ou d'un texte brut,
les structurer en triplets (sujet|relation|objet), les écrire dans
le wiki OKF, et compiler l'hologramme — le tout en automatique.

Architecture :
  Article / URL ──► LLM lit + extrait ──► okf_compiler --file ──► hologramme
                       │                      │
                       ▼                      ▼
                  faits + domaine          .md + NPZ + index

Usage :
  python ka_server/services/okf_ingest.py --text "La lumière est une onde..."
  python ka_server/services/okf_ingest.py --url https://fr.wikipedia.org/...
  python ka_server/services/okf_ingest.py --file article.md
  python ka_server/services/okf_ingest.py --interactive  # mode pas-à-pas
"""

import json
import logging
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
WIKI_DIR = _ENGINE_DIR / 'knowledge'

# ── Endpoint du LLM Oracle Cloud ──────────────────────────
_PHI_API = "http://158.178.215.219:8080"  # Oracle Cloud

# ── Domaines connus pour routage automatique ──────────────
DOMAIN_KEYWORDS = {
    'physique': [
        'lumière', 'énergie', 'atome', 'onde', 'électron', 'photon',
        'gravité', 'relativité', 'quantique', 'électricité', 'magnétisme',
        'mécanique', 'optique', 'thermodynamique', 'particule', 'matière',
    ],
    'astronomie': [
        'planète', 'étoile', 'galaxie', 'soleil', 'lune', 'système solaire',
        'trou noir', 'comète', 'astéroïde', 'orbite', 'constellation',
        'cosmologie', 'univers', 'espace',
    ],
    'biologie': [
        'cellule', 'adn', 'gène', 'protéine', 'enzyme', 'organisme',
        'bactérie', 'virus', 'photosynthèse', 'espèce', 'animal', 'plante',
        'organe', 'tissu', 'métabolisme', 'évolution',
    ],
    'informatique': [
        'ordinateur', 'algorithme', 'internet', 'programmation', 'logiciel',
        'réseau', 'donnée', 'intelligence artificielle', 'machine learning',
        'langage', 'code', 'web', 'numérique',
    ],
    'géographie': [
        'pays', 'capitale', 'continent', 'océan', 'fleuve', 'montagne',
        'population', 'frontière', 'région', 'territoire', 'climat',
    ],
    'chimie': [
        'molécule', 'atome', 'élément chimique', 'réaction', 'acide',
        'composé', 'métal', 'gaz', 'oxygène', 'hydrogène', 'carbone',
    ],
    'mathématiques': [
        'nombre', 'équation', 'théorème', 'fonction', 'géométrie',
        'algèbre', 'probabilité', 'statistique', 'calcul', 'dérivé',
        'intégrale', 'vecteur', 'matrice',
    ],
    'médecine': [
        'maladie', 'symptôme', 'traitement', 'vaccin', 'diagnostic',
        'patient', 'médicament', 'infection', 'virus', 'bactérie',
        'chirurgie', 'prévention', 'santé',
    ],
}


def _normalize(text: str) -> str:
    """Normalise : NFC + remplace les smart quotes."""
    t = unicodedata.normalize('NFC', text)
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    return t.strip()


def detect_domain(text: str) -> Tuple[str, float]:
    """
    Détecte le domaine le plus probable à partir du texte.
    Retourne (domain, confidence).
    """
    text_lower = text.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in text_lower)
        if hits > 0:
            scores[domain] = hits / len(keywords)

    if not scores:
        return ('general', 0.0)

    best = max(scores, key=scores.get)
    return (best, scores[best])


# ── APPEL AU LLM ──────────────────────────────────────────

def _call_llm(prompt: str, system: str = "", timeout: int = 60) -> Optional[str]:
    """
    Appelle le LLM sur Oracle Cloud.
    Pipeline : /phi/query (Phi-3.5-mini) ou /query (Qwen 3B).
    Fallback si l'un est indisponible.
    """
    import urllib.request as _ur
    import json as _json

    payload = _json.dumps({
        "question": prompt,
        "system": system or "Tu es un extracteur de connaissances qui répond en JSON."
    }).encode()

    # Essayer /phi/query d'abord (Phi-3.5-mini)
    for endpoint in ["/phi/query", "/query"]:
        url = _PHI_API + endpoint
        try:
            req = _ur.Request(url, data=payload,
                             headers={"Content-Type": "application/json"})
            with _ur.urlopen(req, timeout=timeout) as resp:
                data = _json.loads(resp.read().decode())
                answer = data.get("answer", "")
                if answer and len(answer) > 10:
                    return answer
        except Exception as e:
            log.debug(f"LLM {endpoint} failed: {e}")
            continue

    # Tentative avec urllib basique (fallback)
    try:
        req = _ur.Request(_PHI_API + "/phi/query", data=payload,
                         headers={"Content-Type": "application/json"})
        with _ur.urlopen(req, timeout=timeout) as resp:
            data = _json.loads(resp.read().decode())
            return data.get("answer", "")
    except Exception as e:
        log.error(f"LLM inaccessible ({_PHI_API}): {e}")
        return None


# ── PROMPT D'EXTRACTION ──────────────────────────────────

EXTRACT_SYSTEM = """Tu es un extracteur de connaissances spécialisé.
Ta mission : lire un texte source et en extraire les faits essentiels
au format structuré.

Règles :
1. Extrais UNIQUEMENT les faits explicitement présents dans le texte.
2. N'invente RIEN — si un fait n'est pas dans le texte, ne le mets pas.
3. Formate chaque fait comme : sujet | relation | objet
4. Les relations doivent être des verbes au présent (est une, a, cause, ...)
5. Sujet et objet doivent être des groupes nominaux précis.
6. Chaque fait sur UNE SEULE ligne.
7. Ajoute une ligne de métadonnées : Domain: <nom_du_domaine>

Exemples de sortie attendue :

Domain: physique
hologramme | est une | figure d'interférence qui stocke une image en trois dimensions
hologramme | a été inventé par | Dennis Gabor en 1947
holographie | permet de | restituer une image en trois dimensions

Tu ne réponds QUE par les faits et le domaine. Pas de texte avant ni après."""


def build_extract_prompt(source_text: str, source_name: str = "") -> str:
    """Construit le prompt d'extraction à partir d'un texte source."""
    src = f" (source: {source_name})" if source_name else ""
    return f"""Extrais les connaissances de ce texte{src} :

--- DÉBUT DU TEXTE ---
{source_text[:4000]}
--- FIN DU TEXTE ---

Réponds UNIQUEMENT avec les faits au format :
Domain: <domaine>
sujet | relation | objet
sujet | relation | objet
...

Ne mets RIEN d'autre que les faits et la ligne Domain."""


def parse_llm_response(response: str) -> Tuple[str, str, List[Tuple[str, str, str]]]:
    """
    Parse la réponse du LLM en (domain, title, [(s, r, o), ...]).
    """
    lines = response.strip().splitlines()
    domain = 'general'
    facts = []
    title = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Ligne Domain:
        m = re.match(r'^domain\s*:\s*(.+)$', line, re.IGNORECASE)
        if m:
            domain = m.group(1).strip().lower()
            # Normaliser le nom du domaine
            domain_map = {
                'physique': 'physique', 'physics': 'physique',
                'astro': 'astronomie', 'astronomy': 'astronomie', 'astrophysique': 'astronomie',
                'bio': 'biologie', 'biology': 'biologie',
                'info': 'informatique', 'computer': 'informatique', 'programmation': 'informatique',
                'geo': 'geographie', 'geography': 'geographie', 'geographie': 'geographie',
                'chimie': 'chimie', 'chemistry': 'chimie',
                'math': 'mathematiques', 'maths': 'mathematiques', 'mathematics': 'mathematiques',
                'med': 'medecine', 'medical': 'medecine', 'medicine': 'medecine',
            }
            domain = domain_map.get(domain, domain)
            continue

        # Ligne sujet | relation | objet
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3 and parts[0] and parts[1] and parts[2]:
            s, r, o = parts[0], parts[1], parts[2]
            # Nettoyer les éventuels tirets de liste
            s = s.lstrip('-*•').strip()
            # Premier fait → sert de titre
            if not title and len(s) < 80:
                title = s[0].upper() + s[1:] if s else ''
            # Vérifier que ce n'est pas un commentaire
            if not s.startswith('#'):
                facts.append((s, r, o))

    # Si pas de titre, prendre le premier sujet
    if not title and facts:
        title = facts[0][0][0].upper() + facts[0][0][1:] if facts[0][0] else 'Sans titre'

    # Fallback sur les mots-clés si le LLM n'a pas donné de domaine
    if domain == 'general' and facts:
        text_for_domain = ' '.join(f'{s} {r} {o}' for s, r, o in facts)
        detected, conf = detect_domain(text_for_domain)
        if conf > 0.05:
            domain = detected

    return (domain, title, facts)


# ── INGESTION PRINCIPALE ──────────────────────────────────

def download_url(url: str) -> Optional[str]:
    """Télécharge le contenu texte d'une URL."""
    try:
        import urllib.request as _ur
        req = _ur.Request(url, headers={
            'User-Agent': 'KA-Knowledge-Ingestor/1.0'
        })
        with _ur.urlopen(req, timeout=30) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            # Extraction basique de texte HTML (si c'est du HTML)
            # strips les balises, garde le texte
            import html as _html
            text = re.sub(r'<[^>]+>', ' ', content)
            text = _html.unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) < 50:
                return None
            return text[:6000]
    except Exception as e:
        log.error(f"Erreur téléchargement URL: {e}")
        return None


def ingest(source_text: str, source_name: str = "",
           interactive: bool = False, auto_confirm: bool = True) -> dict:
    """
    Pipeline complet d'ingestion : texte → LLM → faits → .md → hologramme.

    Args:
        source_text: Texte source à analyser
        source_name: Nom de la source (URL, titre de fichier...)
        interactive: Mode pas-à-pas avec confirmation humaine
        auto_confirm: Mode automatique (confirme tout)

    Returns:
        dict avec les résultats
    """
    if not source_text or len(source_text.strip()) < 20:
        return {'success': False, 'error': 'Texte source trop court'}

    log.info(f"📥 Ingestion: {source_name or source_text[:60]}...")

    # 1. Appel LLM
    log.info("   ☁️ Appel LLM (Oracle Cloud)...")
    prompt = build_extract_prompt(source_text, source_name)
    response = _call_llm(prompt, system=EXTRACT_SYSTEM)

    if not response:
        log.error("   ❌ LLM n'a pas répondu. Vérifiez le serveur Oracle.")
        return {'success': False, 'error': 'LLM indisponible'}

    # 2. Parser la réponse
    domain, title, facts = parse_llm_response(response)

    if not facts:
        log.warning("   ⚠️ Aucun fait extrait par le LLM. Réponse brute:")
        log.warning(f"   {response[:300]}")
        return {'success': False, 'error': 'Aucun fait extrait', 'raw_response': response[:500]}

    log.info(f"   🏷️ Domaine: {domain} | Titre: {title} | {len(facts)} faits extraits")

    # 3. Afficher pour confirmation
    print(f"\n📋 RÉSULTAT DE L'EXTRACTION LLM")
    print(f"   Domaine détecté : {domain}")
    print(f"   Titre proposé   : {title}")
    print(f"   {len(facts)} faits extraits :")
    for s, r, o in facts:
        print(f"     • {s} | {r} | {o}")

    if interactive:
        print("\n❓ Approuvez-vous cette extraction ?")
        respuesta = input("   [o]ui / [n]on / [e]diter le titre / [d]omain différent : ").strip().lower()
        if respuesta.startswith('n'):
            return {'success': False, 'error': 'Refusé par l\'utilisateur'}
        elif respuesta.startswith('d'):
            domain = input(f"   Nouveau domaine (parmi {', '.join(DOMAIN_KEYWORDS.keys())}): ").strip()
        elif respuesta.startswith('e'):
            title = input("   Nouveau titre : ").strip()

    # 4. Générer l'ID
    cid = re.sub(r'[^a-z0-9_]', '_', title.lower().strip())
    cid = re.sub(r'_+', '_', cid).strip('_')

    # 5. Écrire dans raw/ (sauvegarder la source)
    if source_name:
        raw_path = WIKI_DIR / 'raw' / f'{cid}_source.md'
    else:
        raw_path = WIKI_DIR / 'raw' / f'{cid}_source.md'
    raw_content = f"""---
id: {cid}_source
title: Source — {title}
date: {time.strftime('%Y-%m-%d')}
---

# Source: {source_name or "Texte saisi"}

{source_text[:5000]}
"""
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(raw_content, encoding='utf-8')
    log.info(f"   📄 Source sauvegardée: raw/{raw_path.name}")

    # 6. Appeler okf_compiler --file
    log.info("   🔄 Compilation...")
    facts_str = '\\n'.join(f"{s}|{r}|{o}" for s, r, o in facts)
    import subprocess
    cmd = [
        sys.executable, '-m', 'ka_server.services.okf_compiler',
        '--file', f'd={domain}', f'id={cid}', f't={title}',
        f'f={facts_str}', f'src={raw_path.name}', 'overwrite=yes'
    ]
    # --file mode ne supporte pas les espaces dans les paramètres via subprocess
    # On va plutôt importer et appeler directement
    from ka_server.services.okf_compiler import compile_wiki, create_file

    try:
        # Créer le fichier
        facts_list = [(s, r, o) for s, r, o in facts]
        path = create_file(domain, cid, title, facts_list, source=raw_path.name, overwrite=True)

        # Recompiler
        report = compile_wiki(action=f'ingest|{cid}')

        result = {
            'success': True,
            'domain': domain,
            'id': cid,
            'title': title,
            'facts_count': len(facts),
            'file_path': str(path.relative_to(_ENGINE_DIR)),
            'raw_source': str(raw_path.relative_to(_ENGINE_DIR)),
            'llm_response': response,
        }

        log.info(f"   ✅ Hologramme mis à jour: okf_{domain} ({report['valid_files']} fichiers, "
                 f"{sum(r['facts'] for r in report['results'].values())} faits)")

        return result

    except Exception as e:
        log.error(f"   ❌ Erreur compilation: {e}")
        return {'success': False, 'error': str(e), 'facts': facts}


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if '--text' in sys.argv:
        idx = sys.argv.index('--text')
        text = ' '.join(sys.argv[idx + 1:])
        if not text:
            print("Usage: --text \"votre texte à analyser\"")
            return
        r = ingest(text, source_name="Texte saisi",
                   interactive='--interactive' in sys.argv)
        if r.get('success'):
            print(f"\n✅ Ingestion réussie : {r['title']} ({r['domain']})")
            print(f"   {r['facts_count']} faits → {r['file_path']}")
        else:
            print(f"\n❌ Échec : {r.get('error', 'inconnu')}")
        return

    if '--url' in sys.argv:
        idx = sys.argv.index('--url')
        url = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ''
        if not url:
            print("Usage: --url https://...")
            return
        print(f"📡 Téléchargement de {url}...")
        text = download_url(url)
        if not text:
            print("❌ Impossible de télécharger le contenu.")
            return
        r = ingest(text, source_name=url,
                   interactive='--interactive' in sys.argv)
        if r.get('success'):
            print(f"\n✅ Ingestion réussie : {r['title']} ({r['domain']})")
            print(f"   {r['facts_count']} faits → {r['file_path']}")
        else:
            print(f"\n❌ Échec : {r.get('error', 'inconnu')}")
        return

    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        filepath = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ''
        if not filepath or not Path(filepath).exists():
            print("Usage: --file chemin/vers/article.md")
            return
        text = Path(filepath).read_text(encoding='utf-8')
        r = ingest(text, source_name=Path(filepath).name,
                   interactive='--interactive' in sys.argv)
        if r.get('success'):
            print(f"\n✅ Ingestion réussie : {r['title']} ({r['domain']})")
            print(f"   {r['facts_count']} faits → {r['file_path']}")
        else:
            print(f"\n❌ Échec : {r.get('error', 'inconnu')}")
        return

    if '--interactive' in sys.argv:
        print("Mode interactif. Entrez un texte ou tapez 'quit'.")
        while True:
            try:
                text = input("\n📝 Texte source : ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text or text == 'quit':
                break
            r = ingest(text, source_name="Saisie interactive",
                       interactive=True)
            if r.get('success'):
                print(f"✅ {r['title']} ({r['domain']}) — {r['facts_count']} faits")
            else:
                print(f"❌ {r.get('error', 'inconnu')}")
        return

    # Aide
    print("""🌊 OKF Ingestion — LLM (Oracle) → Wiki OKF

Usage:
  --text "votre texte"          Analyser un texte
  --url https://...             Analyser une URL
  --file chemin/article.md      Analyser un fichier
  --interactive                 Mode pas-à-pas

Options:
  --interactive                 Confirmer/extraction avant compilation

Exemples:
  python -m ka_server.services.okf_ingest --text "La lumière est une onde électromagnétique visible par l'œil humain. Elle est composée de photons et se déplace à 299 792 458 m/s dans le vide."
  python -m ka_server.services.okf_ingest --url https://fr.wikipedia.org/wiki/Hologramme
  python -m ka_server.services.okf_ingest --interactive
""")


if __name__ == '__main__':
    main()
