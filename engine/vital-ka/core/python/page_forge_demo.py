"""
PageForge Demo — Interface Interactive de Démonstration
========================================================
Conversation logique pour co-écrire des pages avec l'IA Harmonique.

Usage :
    python page_forge_demo.py              → mode interactif
    python page_forge_demo.py --quick "La photosynthèse" → one-shot
    python page_forge_demo.py --demo       → démonstration automatique
"""

import sys, os, time, math, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from page_forge import (
    PageForge, PageState, StyleConfig, StyleLevel,
    DOCUMENT_TYPES, quick_page
)


# ═══════════════════════════════════════════════════════════════════════════════
# TERMINAL COLORS
# ═══════════════════════════════════════════════════════════════════════════════

class Color:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'


def c(text, color):
    """Applique une couleur."""
    if os.environ.get('NO_COLOR') or sys.platform == 'win32':
        return text
    return f"{color}{text}{Color.RESET}"


# ═══════════════════════════════════════════════════════════════════════════════
# BANNIÈRE
# ═══════════════════════════════════════════════════════════════════════════════

def banner():
    print(c("""
╔══════════════════════════════════════════════════════════╗
║   📄  PAGEFORGE  —  Forge de Pages Harmonique            ║
║        ψ_skeleton ⊗ Σ coh·ψ_fact = Page cohérente        ║
║        Zéro hallucination · 100% local · Sans GPU         ║
╚══════════════════════════════════════════════════════════╝""", Color.CYAN))


def show_help():
    """Affiche l'aide."""
    print(f"""
{c('🛠️  COMMANDES', Color.BOLD)}

{c('Création', Color.YELLOW)}
  {c('écris', Color.DIM)} une page sur [sujet]     → Créer une nouvelle page
  {c('génère', Color.DIM)}                          → Générer tout le contenu
  {c('plan', Color.DIM)}                            → Afficher le squelette

{c('Édition du plan', Color.YELLOW)}
  {c('ajoute', Color.DIM)} [titre]                  → Ajouter une section
  {c('supprime', Color.DIM)} [section]              → Supprimer une section
  {c('type', Color.DIM)} [article|rapport|...]       → Changer le type

{c('Édition du contenu', Color.YELLOW)}
  {c('développe', Color.DIM)} [section]             → Développer
  {c('résume', Color.DIM)} [section]                → Condenser
  {c('reformule', Color.DIM)} [section]             → Reformuler

{c('Style', Color.YELLOW)}
  {c('style', Color.DIM)} [académique|vulgarisé|poétique|technique]
  {c('rends', Color.DIM)} le/la plus [style]         → Ajuster le style

{c('Export', Color.YELLOW)}
  {c('export', Color.DIM)} [md|html]                 → Sauvegarder
  {c('affiche', Color.DIM)}                          → Voir le Markdown

{c('Navigation', Color.YELLOW)}
  {c('aide', Color.DIM)} ou {c('?', Color.DIM)}      → Cette aide
  {c('stats', Color.DIM)}                            → Statistiques de la page
  {c('quit', Color.DIM)} ou {c('q', Color.DIM)}      → Quitter
""")


def show_page_stats(page: PageState):
    """Affiche les statistiques de la page."""
    completed = sum(1 for s in page.sections if s.content)
    total = len(page.sections)
    print(f"""
{c('📊 STATISTIQUES DE LA PAGE', Color.BOLD)}
  {c('Sujet', Color.DIM)}       : {page.topic}
  {c('Type', Color.DIM)}        : {page.doc_type}
  {c('Style', Color.DIM)}       : {page.style.level.value}
  {c('Sections', Color.DIM)}    : {completed}/{total} complétées
  {c('Mots totaux', Color.DIM)} : {page.total_words()}
  {c('Tours', Color.DIM)}       : {page.turn_count}
""")


def show_skeleton(page: PageState):
    """Affiche le squelette de la page."""
    print(f"\n{c(f'📋 PLAN : {page.title or page.topic}', Color.BOLD)}")
    print(f"   {c(f'Type: {page.doc_type} | Style: {page.style.level.value}', Color.DIM)}")
    for i, s in enumerate(page.sections):
        status = c('✅', Color.GREEN) if s.content else c('⏳', Color.YELLOW)
        words = f"({s.word_count} mots)" if s.word_count else ""
        print(f"  {i+1}. {status} {c(s.title, Color.WHITE)} {c(words, Color.DIM)}")


def show_page_content(page: PageState):
    """Affiche le contenu de la page."""
    print(f"\n{c('═' * 60, Color.CYAN)}")
    print(c(f"  {page.title or page.topic}", Color.BOLD))
    print(c('═' * 60, Color.CYAN))

    for section in page.sections:
        if section.content:
            print(f"\n{c(section.title.upper(), Color.YELLOW)}")
            print(section.content)

    if not any(s.content for s in page.sections):
        print(c("\n  Aucune section générée. Tapez 'génère' pour créer le contenu.", Color.DIM))

    print(c('\n' + '═' * 60, Color.CYAN))


# ═══════════════════════════════════════════════════════════════════════════════
# BOUCLE DE CONVERSATION
# ═══════════════════════════════════════════════════════════════════════════════

def conversation_loop(forge: PageForge):
    """Boucle interactive de conversation pour co-écrire une page."""
    print(c("\n💡 Pour commencer, écrivez par exemple :", Color.DIM))
    print(c('   "écris une page sur la photosynthèse"', Color.GRAY))
    print(c('   Tapez "aide" pour voir toutes les commandes.\n', Color.DIM))

    page = forge.get_current_page()
    turn = 0

    while True:
        turn += 1
        try:
            user_input = input(c(f'\n[{turn}] ', Color.DIM) + c('Vous > ', Color.GREEN)).strip()
        except (EOFError, KeyboardInterrupt):
            print(c('\n👋 Au revoir !', Color.YELLOW))
            break

        if not user_input:
            continue

        # Quitter
        if user_input.lower() in ('quit', 'q', 'exit', '/quit'):
            if page and any(s.content for s in page.sections):
                save = input(c('Sauvegarder avant de quitter ? [o/N] ', Color.YELLOW)).strip().lower()
                if save in ('o', 'oui', 'y', 'yes'):
                    md = forge.to_markdown(page)
                    filename = f"page_{page.topic.lower().replace(' ', '_')[:30]}.md"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(md)
                    print(c(f'✅ Sauvegardé : {filename}', Color.GREEN))
            print(c('👋 Au revoir !', Color.YELLOW))
            break

        # Aide
        if user_input.lower() in ('aide', 'help', '?'):
            show_help()
            continue

        # Stats
        if user_input.lower() == 'stats':
            if page:
                show_page_stats(page)
            else:
                print(c("Aucune page en cours.", Color.DIM))
            continue

        # Afficher le plan
        if user_input.lower() in ('plan', 'squelette', 'skeleton', 'outline', 'montre le plan'):
            if page:
                show_skeleton(page)
            else:
                print(c("Aucune page en cours. Créez-en une avec 'écris une page sur...'", Color.DIM))
            continue

        # Afficher le contenu
        if user_input.lower().startswith('affiche'):
            if page:
                show_page_content(page)
            else:
                print(c("Aucune page en cours.", Color.DIM))
            continue

        # Générer toute la page
        if user_input.lower() in ('génère', 'genere', 'génère la page', 'genere la page',
                                   'weave all', 'tisse tout'):
            if page:
                print(c('⏳ Génération de la page complète...', Color.YELLOW))
                t0 = time.time()

                # Générer chaque section non remplie
                psi_prev = None
                psi_skeleton = forge._build_skeleton_wave(page)

                for section in page.sections:
                    if not section.content:
                        psi_section = forge.propagator.propagate(psi_prev, section.title, psi_skeleton)
                        section.psi = psi_section
                        forge.weaver.weave(section, page)
                    psi_prev = section.psi

                page.psi_page = psi_skeleton
                page.updated_at = time.time()
                page.turn_count += 1

                elapsed = time.time() - t0
                print(c(f'✅ Page générée en {elapsed:.2f}s — {page.total_words()} mots', Color.GREEN))
                show_page_content(page)
            else:
                print(c("Créez d'abord une page avec 'écris une page sur [sujet]'", Color.DIM))
            continue

        # Créer une nouvelle page
        creation_match = False
        creation_patterns = [
            (r"(?:écris|ecris|crée|cree|rédige|redige|génère|genere)\s+(?:une\s+)?(?:page|article|rapport|lettre|tutoriel)\s+(?:sur\s+|à\s+propos\s+de\s+|au\s+sujet\s+de\s+)?(.+)", 'article'),
            (r"(?:écris|ecris|crée|cree|rédige|redige|génère|genere)\s+(?:un\s+)?(?:rapport)\s+(?:sur\s+|à\s+propos\s+de\s+)?(.+)", 'rapport'),
            (r"(?:parle|explique|décris|decris)\s+(?:moi\s+)?(?:de\s+|du\s+|des\s+|d'\s*)?(.+)", 'article'),
        ]

        for pattern, default_type in creation_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                topic = match.group(1).strip().rstrip('.').rstrip('?').rstrip('!')
                print(c(f'\n📝 Création de la page sur "{topic}"...', Color.YELLOW))

                # Détecter le type
                doc_type = default_type
                type_keywords = {
                    'rapport': 'rapport',
                    'lettre': 'lettre',
                    'tutoriel': 'tutoriel',
                    'page web': 'page_web',
                    'article': 'article',
                }
                for kw, dt in type_keywords.items():
                    if kw in user_input.lower():
                        doc_type = dt
                        break

                page = forge.generate_outline(topic, doc_type)
                print(c(f'✅ Plan créé ({len(page.sections)} sections, type: {doc_type})', Color.GREEN))
                show_skeleton(page)
                print(c('\n💡 Tapez "génère" pour créer le contenu, ou modifiez le plan.', Color.DIM))
                creation_match = True
                break

        if creation_match:
            continue

        # Changer le type
        if user_input.lower().startswith('type '):
            target = user_input[5:].strip().lower()
            if target in DOCUMENT_TYPES:
                if page:
                    doc_config = DOCUMENT_TYPES[target]
                    # Recréer les sections
                    sections = forge.skeleton_gen.generate(page.topic, target)
                    page.doc_type = target
                    page.sections = sections
                    print(c(f'✅ Type changé en "{target}" — plan mis à jour.', Color.GREEN))
                    show_skeleton(page)
                else:
                    print(c("Créez d'abord une page.", Color.DIM))
            else:
                types = ', '.join(DOCUMENT_TYPES.keys())
                print(c(f"Types disponibles : {types}", Color.DIM))
            continue

        # Changer le style
        if user_input.lower().startswith('style '):
            target = user_input[6:].strip().lower()
            style_map = {
                'académique': StyleLevel.ACADEMIQUE, 'academique': StyleLevel.ACADEMIQUE,
                'vulgarisé': StyleLevel.VULGARISE, 'vulgarise': StyleLevel.VULGARISE,
                'poétique': StyleLevel.POETIQUE, 'poetique': StyleLevel.POETIQUE,
                'technique': StyleLevel.TECHNIQUE,
                'journalistique': StyleLevel.JOURNALISTIQUE,
                'conversationnel': StyleLevel.CONVERSATIONNEL,
            }
            if target in style_map and page:
                page.style.level = style_map[target]
                print(c(f'✅ Style changé en "{page.style.level.value}".', Color.GREEN))
            else:
                print(c("Styles : académique, vulgarisé, poétique, technique, journalistique, conversationnel", Color.DIM))
            continue

        # Raccourci pour "rends le plus X"
        restyle_match = re.search(r"rends?\s+(?:le|la|les|plus|moins)\s*(.+)", user_input.lower())
        if restyle_match and page:
            target = restyle_match.group(1).strip()
            style_map = {
                'académique': StyleLevel.ACADEMIQUE, 'academique': StyleLevel.ACADEMIQUE,
                'vulgarisé': StyleLevel.VULGARISE, 'vulgarise': StyleLevel.VULGARISE,
                'poétique': StyleLevel.POETIQUE, 'poetique': StyleLevel.POETIQUE,
                'technique': StyleLevel.TECHNIQUE,
                'simple': StyleLevel.VULGARISE,
                'formel': StyleLevel.ACADEMIQUE,
                'créatif': StyleLevel.POETIQUE, 'creatif': StyleLevel.POETIQUE,
                'détaillé': StyleLevel.TECHNIQUE, 'detaille': StyleLevel.TECHNIQUE,
            }
            if target in style_map:
                page.style.level = style_map[target]
                print(c(f'✅ Style ajusté → {page.style.level.value}', Color.GREEN))
            else:
                print(c(f"Style '{target}' non reconnu. Styles : académique, vulgarisé, poétique, technique", Color.DIM))
            continue

        # Développer une section
        if user_input.lower().startswith(('développe ', 'developpe ', 'détaille ', 'detail ', 'expand ')):
            if page:
                target = user_input.split(' ', 1)[1] if ' ' in user_input else ''
                section = page.get_section(target) if target else None
                if section:
                    print(c(f'⏳ Développement de "{section.title}"...', Color.YELLOW))
                    psi_skeleton = forge._build_skeleton_wave(page) if not page.psi_page else page.psi_page
                    psi_section = forge.propagator.propagate(
                        page.sections[page.section_index(section.id) - 1].psi if page.section_index(section.id) > 0 else None,
                        section.title + " (détaillé)",
                        psi_skeleton
                    )
                    section.psi = psi_section
                    forge.weaver.weave(section, page)
                    print(c(f'✅ Section développée ({section.word_count} mots)', Color.GREEN))
                    print(section.content[:300] + ('...' if len(section.content) > 300 else ''))
                else:
                    print(c(f"Section '{target}' non trouvée. Sections : {[s.id for s in page.sections]}", Color.DIM))
            else:
                print(c("Créez d'abord une page.", Color.DIM))
            continue

        # Résumer une section
        if user_input.lower().startswith(('résume ', 'resume ', 'condense ')):
            if page:
                target = user_input.split(' ', 1)[1] if ' ' in user_input else ''
                section = page.get_section(target) if target else None
                if section and section.content:
                    sentences = [s.strip() for s in section.content.split('.') if s.strip()]
                    section.content = '. '.join(sentences[:2]) + '.'
                    section.word_count = len(section.content.split())
                    print(c(f'✅ Section condensée ({section.word_count} mots)', Color.GREEN))
                    print(section.content)
                else:
                    print(c(f"Section '{target}' non trouvée ou vide.", Color.DIM))
            else:
                print(c("Créez d'abord une page.", Color.DIM))
            continue

        # Reformuler
        if user_input.lower().startswith(('reformule ', 'rephrase ')):
            if page:
                target = user_input.split(' ', 1)[1] if ' ' in user_input else ''
                section = page.get_section(target) if target else None
                if section and section.content:
                    forge.weaver.weave(section, page)
                    print(c(f'✅ Section reformulée ({section.word_count} mots)', Color.GREEN))
                    print(section.content[:300] + ('...' if len(section.content) > 300 else ''))
                else:
                    print(c(f"Section '{target}' non trouvée.", Color.DIM))
            else:
                print(c("Créez d'abord une page.", Color.DIM))
            continue

        # Ajouter une section
        if user_input.lower().startswith(('ajoute ', 'ajouter ')):
            if page:
                target = user_input.split(' ', 1)[1] if ' ' in user_input else ''
                if target:
                    new_id = target.lower().replace(' ', '_')[:30]
                    new_section = type(page.sections[0])(
                        id=new_id,
                        title=target,
                        position_angle=math.pi / 2,
                    ) if page.sections else None

                    if new_section:
                        concl_idx = page.section_index('conclusion')
                        if concl_idx >= 0:
                            page.sections.insert(concl_idx, new_section)
                        else:
                            page.sections.append(new_section)
                        print(c(f'✅ Section "{target}" ajoutée.', Color.GREEN))
                        show_skeleton(page)
            else:
                print(c("Créez d'abord une page.", Color.DIM))
            continue

        # Supprimer une section
        if user_input.lower().startswith(('supprime ', 'enlève ', 'enleve ', 'retire ', 'efface ')):
            if page:
                target = user_input.split(' ', 1)[1] if ' ' in user_input else ''
                idx = page.section_index(target)
                if idx >= 0:
                    removed = page.sections.pop(idx)
                    print(c(f'✅ Section "{removed.title}" supprimée.', Color.GREEN))
                    show_skeleton(page)
                else:
                    print(c(f"Section '{target}' non trouvée.", Color.DIM))
            else:
                print(c("Créez d'abord une page.", Color.DIM))
            continue

        # Export
        if user_input.lower().startswith('export'):
            if page:
                fmt = user_input.split(' ')[1] if len(user_input.split(' ')) > 1 else 'md'
                if fmt in ('md', 'markdown'):
                    output = forge.to_markdown(page)
                    ext = 'md'
                elif fmt == 'html':
                    output = forge.to_html(page)
                    ext = 'html'
                else:
                    output = forge.to_markdown(page)
                    ext = 'md'

                filename = f"page_{page.topic.lower().replace(' ', '_')[:30]}.{ext}"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(c(f'✅ Exporté : {filename} ({len(output)} caractères)', Color.GREEN))
            else:
                print(c("Aucune page à exporter.", Color.DIM))
            continue

        # Commande non reconnue
        print(c(f"🤔 Commande non reconnue : '{user_input[:50]}'", Color.YELLOW))
        print(c('   Tapez "aide" pour voir les commandes disponibles.', Color.DIM))


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO AUTOMATIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def auto_demo():
    """Démonstration automatique de PageForge."""
    print(c("🤖 DÉMO AUTOMATIQUE", Color.BOLD))

    forge = PageForge()

    topics = [
        ("La photosynthèse : comment les plantes transforment la lumière en énergie", "article"),
        ("Le paludisme : causes, symptômes et traitements", "rapport"),
    ]

    for topic, doc_type in topics:
        print(f"\n{c('─' * 60, Color.CYAN)}")
        print(c(f"📄 Génération : {topic}", Color.BOLD))
        print(c(f"   Type : {doc_type}", Color.DIM))

        t0 = time.time()
        page = forge.generate(topic, doc_type)
        elapsed = time.time() - t0

        print(c(f"   ⏱️  {elapsed:.2f}s | 📊 {page.total_words()} mots | 📋 {len(page.sections)} sections", Color.GREEN))

        # Afficher le squelette
        show_skeleton(page)

        # Afficher un extrait de chaque section
        for s in page.sections:
            if s.content:
                preview = s.content[:120].replace('\n', ' ')
                print(c(f"   📍 {s.title[:30]}: ", Color.DIM) + c(f"{preview}...", Color.GRAY))

    # Test export
    print(f"\n{c('─' * 60, Color.CYAN)}")
    print(c("📦 Test export...", Color.BOLD))
    page = forge.get_current_page()
    if page:
        md = forge.to_markdown(page)
        filename = f"demo_page_{page.topic.lower().replace(' ', '_')[:30]}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md)
        print(c(f"   ✅ Exporté : {filename} ({len(md)} car.)", Color.GREEN))

        html = forge.to_html(page)
        filename_html = f"demo_page_{page.topic.lower().replace(' ', '_')[:30]}.html"
        with open(filename_html, 'w', encoding='utf-8') as f:
            f.write(html)
        print(c(f"   ✅ Exporté : {filename_html} ({len(html)} car.)", Color.GREEN))

    print(c("\n✅ Démo terminée !", Color.GREEN))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='PageForge — Forge de Pages Harmonique')
    parser.add_argument('--quick', type=str, help='Génération rapide one-shot (topic)')
    parser.add_argument('--type', type=str, default='article', help='Type de document')
    parser.add_argument('--demo', action='store_true', help='Démonstration automatique')
    parser.add_argument('--export', type=str, help='Exporter en md ou html après génération')

    args = parser.parse_args()

    if args.demo:
        banner()
        auto_demo()
        return

    if args.quick:
        banner()
        topic = args.quick
        doc_type = args.type
        print(c(f'\n⏳ Génération de la page sur "{topic}"...', Color.YELLOW))

        forge = PageForge()
        t0 = time.time()
        page = forge.generate(topic, doc_type)
        elapsed = time.time() - t0

        print(c(f'✅ Généré en {elapsed:.2f}s — {page.total_words()} mots', Color.GREEN))
        show_skeleton(page)
        print()

        if args.export == 'html':
            print(forge.to_html(page))
        elif args.export == 'md':
            print(forge.to_markdown(page))
        else:
            show_page_content(page)

        # Sauvegarder automatiquement
        ext = args.export if args.export in ('md', 'html') else 'md'
        if ext == 'html':
            output = forge.to_html(page)
        else:
            output = forge.to_markdown(page)
        filename = f"page_{topic.lower().replace(' ', '_')[:30]}.{ext}"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(output)
        print(c(f'\n💾 Sauvegardé : {filename}', Color.GREEN))
        return

    # Mode interactif par défaut
    banner()
    forge = PageForge()
    conversation_loop(forge)


if __name__ == '__main__':
    main()
