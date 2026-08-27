"""Wave Poet — banc d'essai complet"""
import sys
sys.path.insert(0, 'vital-ka/core/python')
from wave_poetry import WavePoet

poet = WavePoet()

print("╔══════════════════════════════════════════════════════════════╗")
print("║  WAVE POET — banc d'essai complet                           ║")
print("╚══════════════════════════════════════════════════════════════╝")
st = poet.stats()
print()
print(f"Vocabulaire poetique : {st['poetic_vocabulary']} mots")
print(f"Phases emotionnelles : {', '.join(st['phases'])}")
print(f"Dimension spectrale  : {poet.dim}")
print()

# ═══ TEST 1 : Compositions poétiques (API native) ═══
print("=" * 60)
print("TEST 1 : Compositions poetiques (API native compose)")
print("=" * 60)

themes = [
    "compression telephone",
    "liberation espace",
    "nettoyage appareil",
    "stockage plein",
    "connaissance medicale",
]

for theme in themes:
    for form in ['haiku_wave', 'free_verse', 'alexandrin']:
        try:
            r = poet.compose(theme, form=form, lines=4)
            text = r.get('text', '')
            print(f"\n Theme: {theme} | Forme: {form}")
            print(f"  {text[:120]}")
        except Exception as e:
            print(f"  ERREUR: {e}")

# ═══ TEST 2 : Vérifier si render() est caché (plugin manquant) ═══
print()
print("=" * 60)
print("TEST 2 : Verification render() — API manquante")
print("=" * 60)
print()
print("Le WavePoet actuel n'a PAS de methode render().")
print("Il a compose() qui genere des poemes a partir d'un theme,")
print("mais pas de rewrite/stylize qui transforme une phrase existante.")
print()
print("Le code dans chat.py ligne 730 appelle poet.render()")
print("→ cela generera une AttributeError au runtime")
print("→ le bloc try/except rattrape silencieusement l'erreur")
print()

# ═══ TEST 3 : Ce que compose() donne pour des intentions KA ═══
print("=" * 60)
print("TEST 3 : Compositions pour les intentions KA Mobile")
print("=" * 60)

intent_themes = [
    ("storage_action",  "mon telephone libere son espace"),
    ("storage_action",  "compression des souvenirs numeriques"),
    ("greeting",        "bonjour aide et lumiere"),
    ("factual_question","reponse de sagesse et connaissance"),
    ("arithmetic",      "chiffres et harmonies mathematiques"),
    ("comparison",      "balance et comparaison des choses"),
]

for intent, theme in intent_themes:
    try:
        r = poet.compose(theme, form='free_verse', emotion='paisible', lines=4)
        print(f"\n [{intent}] Theme: {theme}")
        print(f"  {r.get('text', '')[:160]}")
    except Exception as e:
        print(f"  ERREUR: {e}")

# ═══ CONCLUSION ═══
print()
print("=" * 60)
print("RAPPORT WAVE POET")
print("=" * 60)
print()
print("Le WavePoet est un generateur de poesie, PAS un styliseur de texte.")
print()
print("Il peut etre utile pour :")
print("  - Generer un poeme d'accueil ou de conclusion")
print("  - Creer une ambiance poetique dans l'interface KA")
print("  - Ajouter un vers inspire sur une thematique")
print()
print("Mais il NE PEUT PAS (actuellement) :")
print("  - Styliser/embellir une phrase technique existante")
print("  - Reformuler les reponses de KA")
print("  - Ajouter des emojis ou du formatage")
print()
print("Si vous voulez des phrases stylees dans les reponses KA,")
print("il faut soit :")
print(" 1. Ajouter une methode render() a WavePoet")
print(" 2. Confier le stylage au LLM (prompt systeme)")
print(" 3. Creer un module wave_stylizer dedie")
print()
print("Recommandation : ajouter render() a WavePoet ou utiliser le LLM pour")
print("le style, car compose() genere des poemes complets (pas adapte")
print("pour styliser les reponses techniques de KA Mobile).")