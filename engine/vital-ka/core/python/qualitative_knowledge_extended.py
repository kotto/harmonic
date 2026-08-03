"""
Base de connaissance étendue — Culture Générale
=================================================
Faits ajoutés pour couvrir les domaines manquants :
géographie, histoire, culture générale, littérature.

Format : (sujet, relation, objet, secteur)
"""

GENERAL_KNOWLEDGE = [
    # ─── GÉOGRAPHIE ──────────────────────────────────────────────────
    ("paris", "est la capitale de", "la France", "GEOGRAPHIE"),
    ("londres", "est la capitale du", "Royaume Uni", "GEOGRAPHIE"),
    ("berlin", "est la capitale de", "l Allemagne", "GEOGRAPHIE"),
    ("tokyo", "est la capitale du", "Japon", "GEOGRAPHIE"),
    ("pekin", "est la capitale de", "la Chine", "GEOGRAPHIE"),
    ("washington", "est la capitale des", "Etats Unis", "GEOGRAPHIE"),
    ("moscou", "est la capitale de", "la Russie", "GEOGRAPHIE"),
    ("rome", "est la capitale de", "l Italie", "GEOGRAPHIE"),
    ("madrid", "est la capitale de", "l Espagne", "GEOGRAPHIE"),
    ("new delhi", "est la capitale de", "l Inde", "GEOGRAPHIE"),
    ("brasilia", "est la capitale du", "Bresil", "GEOGRAPHIE"),
    ("canberra", "est la capitale de", "l Australie", "GEOGRAPHIE"),
    ("ottawa", "est la capitale du", "Canada", "GEOGRAPHIE"),
    ("le caire", "est la capitale de", "l Egypte", "GEOGRAPHIE"),
    ("athenes", "est la capitale de", "la Grece", "GEOGRAPHIE"),
    ("la france", "est situee en", "Europe", "GEOGRAPHIE"),
    ("le japon", "est situe en", "Asie", "GEOGRAPHIE"),
    ("le bresil", "est situe en", "Amerique du Sud", "GEOGRAPHIE"),
    ("le nil", "est le plus long", "fleuve du monde", "GEOGRAPHIE"),
    ("leverest", "est le plus haut", "sommet du monde", "GEOGRAPHIE"),
    ("le sahara", "est le plus grand", "desert chaud", "GEOGRAPHIE"),
    ("la terre", "a un rayon de", "6371 km", "GEOGRAPHIE"),
    ("le soleil", "est situe a", "150 millions de km", "GEOGRAPHIE"),
    ("les oceans", "couvrent", "71 pourcents de la Terre", "GEOGRAPHIE"),
    ("paris", "est surnommee", "la ville lumiere", "GEOGRAPHIE"),
    ("la seine", "traverse", "Paris", "GEOGRAPHIE"),
    ("la france", "a pour monnaie", "l euro", "GEOGRAPHIE"),
    ("le japon", "a pour monnaie", "le yen", "GEOGRAPHIE"),
    ("les etats unis", "ont pour monnaie", "le dollar", "GEOGRAPHIE"),
    ("la terre", "tourne autour du", "soleil", "ASTRONOMIE"),
    ("la lune", "tourne autour de", "la Terre", "ASTRONOMIE"),
    ("mars", "est surnommee", "la planete rouge", "ASTRONOMIE"),
    ("jupiter", "est la plus grande", "planete du systeme solaire", "ASTRONOMIE"),
    
    # ─── HISTOIRE ─────────────────────────────────────────────────────
    ("la revolution francaise", "a eu lieu en", "1789", "HISTOIRE"),
    ("napoleon bonaparte", "est devenu empereur en", "1804", "HISTOIRE"),
    ("la premiere guerre mondiale", "a eu lieu de", "1914 a 1918", "HISTOIRE"),
    ("la seconde guerre mondiale", "a eu lieu de", "1939 a 1945", "HISTOIRE"),
    ("christophe colomb", "a decouvert", "l Amerique en 1492", "HISTOIRE"),
    ("la declaration des droits de l homme", "a ete adoptee en", "1789", "HISTOIRE"),
    ("jules cesar", "a franchi le", "Rubicon en 49 av JC", "HISTOIRE"),
    ("l empire romain", "s est effondre en", "476", "HISTOIRE"),
    ("le mur de berlin", "est tombe en", "1989", "HISTOIRE"),
    ("l homme", "a marche sur la lune en", "1969", "HISTOIRE"),
    ("la renaissance", "a debute en", "Italie au 14e siecle", "HISTOIRE"),
    ("l imprimerie", "a ete inventee par", "Gutenberg en 1440", "HISTOIRE"),
    ("leonard de vinci", "a peint", "la Joconde", "HISTOIRE"),
    ("cleopatre", "etait la reine de", "l Egypte antique", "HISTOIRE"),
    ("alexandre le grand", "a conquis", "un vaste empire en Asie", "HISTOIRE"),
    ("marie curie", "a decouvert", "le radium et le polonium", "HISTOIRE"),
    ("louis pasteur", "a developpe", "le vaccin contre la rage", "HISTOIRE"),
    ("martin luther king", "a milite pour", "les droits civiques", "HISTOIRE"),
    ("nelson mandela", "a lutte contre", "l apartheid en Afrique du Sud", "HISTOIRE"),
    ("la theorie de l evolution", "a ete proposee par", "Charles Darwin", "HISTOIRE"),
    ("la penicilline", "a ete decouverte par", "Alexander Fleming", "HISTOIRE"),
    ("le premier homme dans l espace", "etait", "Youri Gagarine", "HISTOIRE"),
    ("galilee", "a soutenu", "l heliocentrisme", "HISTOIRE"),
    ("socrate", "etait un", "philosophe grec", "HISTOIRE"),
    ("confucius", "etait un", "philosophe chinois", "HISTOIRE"),
    ("bouddha", "a fonde", "le bouddhisme", "HISTOIRE"),
    ("jeanne d arc", "a libere", "Orleans en 1429", "HISTOIRE"),
    ("la prise de la bastille", "symbolise", "la Revolution francaise", "HISTOIRE"),
    
    # ─── LITTÉRATURE / ART ───────────────────────────────────────────
    ("victor hugo", "a ecrit", "Les Miserables", "LITTERATURE"),
    ("moliere", "a ecrit", "Le Misanthrope", "LITTERATURE"),
    ("shakespeare", "a ecrit", "Romeo et Juliette", "LITTERATURE"),
    ("homere", "a ecrit", "L Odyssee", "LITTERATURE"),
    ("dante", "a ecrit", "La Divine Comedie", "LITTERATURE"),
    ("proust", "a ecrit", "A la recherche du temps perdu", "LITTERATURE"),
    ("camus", "a ecrit", "L Etranger", "LITTERATURE"),
    ("voltaire", "a ecrit", "Candide", "LITTERATURE"),
    ("la poesie", "est l art de", "la langue et du rythme", "LITTERATURE"),
    ("la peinture", "est l art de", "la couleur et de la forme", "ART"),
    ("la musique", "est l art de", "l harmonie des sons", "ART"),
    ("la sculpture", "est l art de", "la forme dans l espace", "ART"),
    ("picasso", "a fonde", "le cubisme", "ART"),
    ("van gogh", "a peint", "La Nuit etoilee", "ART"),
    ("monet", "etait un peintre", "impressionniste", "ART"),
    ("beethoven", "a compose", "la 9e symphonie", "MUSIQUE"),
    ("mozart", "a compose", "La Flute enchantee", "MUSIQUE"),
    ("bach", "a compose", "L Art de la fugue", "MUSIQUE"),
    ("le roman", "est un genre", "litteraire narratif", "LITTERATURE"),
    ("la tragedie", "est un genre", "theatral dramatique", "LITTERATURE"),
    ("la comedie", "est un genre", "theatral humoristique", "LITTERATURE"),
    ("l essai", "est un genre", "litteraire argumentatif", "LITTERATURE"),
    ("le haiku", "est une forme poetique", "japonaise de 17 syllabes", "LITTERATURE"),
    ("le sonnet", "est une forme poetique", "de 14 vers", "LITTERATURE"),
    
    # ─── CULTURE GÉNÉRALE ────────────────────────────────────────────
    ("l eau", "gele a", "0 degres Celsius", "CULTURE_G"),
    ("l eau", "bout a", "100 degres Celsius", "CULTURE_G"),
    ("le corps humain", "a un pH sanguin de", "7.4", "CULTURE_G"),
    ("le corps humain", "est compose a", "60 pourcents d eau", "CULTURE_G"),
    ("le squelette humain", "compte", "206 os", "CULTURE_G"),
    ("le coeur humain", "bat environ", "100000 fois par jour", "CULTURE_G"),
    ("le cerveau humain", "contient environ", "86 milliards de neurones", "CULTURE_G"),
    ("l adn humain", "contient environ", "3 milliards de paires de bases", "CULTURE_G"),
    ("la vitesse de la lumiere", "est de", "300000 km par seconde", "CULTURE_G"),
    ("le diamant", "est la substance la plus", "dure connue", "CULTURE_G"),
    ("le cheveu humain", "pousse d environ", "1 cm par mois", "CULTURE_G"),
    ("le Mont Everest", "culmine a", "8848 metres", "CULTURE_G"),
    ("la Grande Muraille de Chine", "s etend sur", "21000 km", "CULTURE_G"),
    ("l alphabet francais", "compte", "26 lettres", "CULTURE_G"),
    ("un jour terrestre", "dure", "24 heures", "CULTURE_G"),
    ("une annee terrestre", "dure", "365 jours", "CULTURE_G"),
    ("l annee bissextile", "a lieu tous les", "4 ans", "CULTURE_G"),
    ("le zero absolu", "est de", "-273.15 degres Celsius", "CULTURE_G"),
    ("l air", "est compose principalement", "d azote et d oxygene", "CULTURE_G"),
    ("l oxygene", "represente", "21 pourcents de l air", "CULTURE_G"),
    ("le bronze", "est un alliage de", "cuivre et d etain", "CULTURE_G"),
    ("le laiton", "est un alliage de", "cuivre et de zinc", "CULTURE_G"),
    ("le systeme metrique", "a ete cree en", "France en 1795", "CULTURE_G"),
    ("la boussole", "pointe vers", "le nord magnetique", "CULTURE_G"),
    ("l arc-en-ciel", "a", "7 couleurs", "CULTURE_G"),
    ("le cafe", "contient de la", "cafeine", "CULTURE_G"),
    ("le vin rouge", "contient des", "polyhenols antioxydants", "CULTURE_G"),
    ("la noix de coco", "est un", "fruit drupacee", "CULTURE_G"),
    ("la tomate", "est un", "fruit botaniquement", "CULTURE_G"),
    ("le chocolat", "est fabrique a partir de", "la feve de cacao", "CULTURE_G"),
    ("la soie", "est produite par", "le ver a soie", "CULTURE_G"),
    ("le miel", "est produit par", "les abeilles", "CULTURE_G"),
    ("le papier", "a ete invente en", "Chine", "CULTURE_G"),
    ("la poudre a canon", "a ete inventee en", "Chine", "CULTURE_G"),
    
    # ─── CONNAISSANCE DU SYSTÈME (pour question identité) ────────────
    ("ka", "est un systeme", "d intelligence artificielle harmonique", "IDENTITE"),
    ("ka", "utilise le principe", "ondulatoire pour raisonner", "IDENTITE"),
    ("ka", "fonctionne sans", "reseau de neurones", "IDENTITE"),
    ("ka", "ne necessite pas de", "GPU pour fonctionner", "IDENTITE"),
    ("ka", "est deterministe car", "meme question donne meme reponse", "IDENTITE"),
    ("ka", "repond en", "320 millisecondes sur CPU", "IDENTITE"),
    ("ka", "a ete cree par", "Alain Kotto", "IDENTITE"),
    ("ka", "est base sur", "la theorie de l Univers Harmonique", "IDENTITE"),
    ("ka", "utilise la derivee fractionnaire", "ABC d ordre 1 sur phi", "IDENTITE"),
    ("ka", "stocke la connaissance dans", "un hologramme de 32 Ko", "IDENTITE"),
]

# ─── AUTO-INSERTION ────────────────────────────────────────────────

def extend_knowledge_base(model):
    """
    Ajoute les faits de culture générale à un modèle.
    
    Usage:
        from qualitative_knowledge_extended import extend_knowledge_base
        extend_knowledge_base(model)
    """
    added = 0
    for fact in GENERAL_KNOWLEDGE:
        if fact not in model.knowledge_base:
            model.knowledge_base.append(fact)
            added += 1
    if added > 0:
        from harmonic_model import build_waves
        model.kx, model.ky, model.w2i = build_waves(model.knowledge_base)
    return added
