"""
Afrique Curated — 8 tomes UNESCO dans le moteur actuel
==========================================================
Injecte les 40+ connaissances de l'Histoire Générale de l'Afrique
(UNESCO, 8 volumes) directement dans le KnowledgeEnricher.
"""

def get_africa_blocks():
    """Retourne les blocs curated pour chaque tome."""
    return {
        # ── VOLUME 1 : ORIGINES ──
        "afrique berceau humanite": (
            "L'Afrique est le berceau de l'humanité. Les plus anciens fossiles "
            "d'hominidés ont été découverts en Afrique de l'Est, notamment Lucy "
            "(Australopithecus afarensis, 3,2 millions d'années) découverte en "
            "Éthiopie en 1974. Le genre Homo est apparu en Afrique il y a 2,8 "
            "millions d'années. Homo sapiens est apparu en Afrique il y a 300 000 "
            "ans, comme l'attestent les fossiles de Djebel Irhoud au Maroc (2017). "
            "TOUTE l'humanité moderne a une origine africaine."
        ),
        "lucy australopitheque": (
            "Lucy est le surnom du fossile d'Australopithecus afarensis découvert "
            "en 1974 à Hadar, en Éthiopie, par Donald Johanson, Maurice Taieb et "
            "Yves Coppens. Daté de 3,2 millions d'années, c'est l'un des plus "
            "anciens et des plus complets squelettes d'hominidé jamais trouvés. "
            "Lucy marchait debout (bipédie) mais conservait des adaptations au "
            "grimper. Elle est conservée au Musée national d'Éthiopie à Addis-Abeba."
        ),
        "sahara ancien": (
            "Le Sahara n'a pas toujours été un désert. Pendant la période humide "
            "africaine (10 000 à 5 000 avant notre ère), c'était une savane "
            "verdoyante parcourue de lacs et de rivières, peuplée d'animaux et "
            "d'hommes. Les peintures rupestres du Tassili n'Ajjer en Algérie "
            "témoignent de cette période. Le Sahara s'est asséché progressivement "
            "pour devenir le désert que nous connaissons aujourd'hui."
        ),

        # ── VOLUME 2 : AFRIQUE ANCIENNE ──
        "egypte antique afrique": (
            "La civilisation de l'Égypte ancienne est une civilisation africaine, "
            "née sur les rives du Nil. L'unification par Narmer (Ménès) vers 3100 "
            "avant notre ère marque le début de la période dynastique. Les pyramides "
            "de Gizeh (IVe dynastie, 2600-2500 av. J.-C.) comptent parmi les plus "
            "grandes réalisations architecturales de l'humanité. CORRECTION : "
            "l'Égypte ancienne fait partie intégrante de l'histoire africaine."
        ),
        "royaume koush nubie": (
            "Le royaume de Koush (Soudan actuel) a développé une civilisation "
            "brillante. Kerma (2500-1500 av. J.-C.) en était la capitale. Les "
            "pharaons koushites de la XXVe dynastie (747-656 av. J.-C.) ont régné "
            "sur l'Égypte unifiée, avec Piânkhy, Chabaka et Taharqa. Taharqa est "
            "mentionné dans la Bible. Le royaume de Méroé (300 av. J.-C. à 350 ap. "
            "J.-C.) a développé sa propre écriture méroïtique et était un centre "
            "majeur de production de fer."
        ),
        "royaume aksoum ethiopie": (
            "Le royaume d'Aksoum (Éthiopie/Érythrée, Ier-VIIe s.) était une "
            "puissance majeure du monde antique. Il frappait sa propre monnaie, "
            "commerçait avec Rome, la Perse et l'Inde via le port d'Adulis. "
            "Converti au christianisme au IVe siècle sous le roi Ezana, l'Éthiopie "
            "est l'un des plus anciens États chrétiens du monde. Les stèles "
            "d'Aksoum et l'église Sainte-Marie-de-Sion en sont les témoins."
        ),

        # ── VOLUME 3 : MÉDIÉVAL ──
        "empire ghana wagadou": (
            "L'empire du Ghana (Wagadou), situé dans l'actuelle Mauritanie et "
            "Mali, était le premier grand empire ouest-africain (VIIIe-XIe s.). "
            "Il contrôlait le commerce transsaharien de l'or et du sel. Sa "
            "capitale Koumbi Saleh était une ville double avec quartier musulman "
            "et quartier royal animiste. Il a décliné sous les attaques des "
            "Almoravides au XIe siècle."
        ),
        "tombouctou": (
            "Tombouctou, au Mali, était l'un des grands centres intellectuels du "
            "monde médiéval. L'université de Sankoré comptait 25 000 étudiants. "
            "Les bibliothèques de Tombouctou contenaient des centaines de milliers "
            "de manuscrits sur l'astronomie, la médecine, le droit, les "
            "mathématiques et la philosophie. La mosquée de Djingareyber a été "
            "construite sous Mansa Moussa par l'architecte andalou es-Sahéli."
        ),
        "cote swahilie": (
            "La côte swahilie (Somalie au Mozambique, VIIIe-XVe s.) était un "
            "ensemble de cités-États commerçantes prospères. Kilwa, Mombasa, "
            "Zanzibar et Mogadiscio commerçaient avec l'Arabie, l'Inde, la Perse "
            "et la Chine. La culture swahilie est née du mélange des cultures "
            "bantoues, arabes et persanes. Le kiswahili est aujourd'hui parlé "
            "par plus de 100 millions de personnes."
        ),

        # ── VOLUME 4 : GRANDS EMPIRES ──
        "empire mali soundiata": (
            "L'empire du Mali (XIIIe-XVe s.) fut fondé par Soundiata Keïta vers "
            "1235. Soundiata unifia les peuples mandingues et proclama la Charte "
            "de Kurukan Fuga (1236), considérée comme l'une des premières "
            "déclarations des droits humains : abolition de l'esclavage, liberté "
            "d'expression, égalité. L'empire du Mali contrôlait les riches mines "
            "d'or du Bambouk et du Bouré."
        ),
        "mansa moussa": (
            "Mansa Kankan Moussa, empereur du Mali (1312-1337), est considéré "
            "comme l'homme le plus riche de l'histoire. Son pèlerinage à La "
            "Mecque en 1324, accompagné de 60 000 porteurs et 12 000 esclaves "
            "transportant de l'or, a provoqué une inflation au Caire qui dura "
            "12 ans. Il fit construire la mosquée de Djingareyber à Tombouctou "
            "et développa l'éducation et l'architecture dans tout l'empire."
        ),
        "empire songhai": (
            "L'empire Songhaï (XVe-XVIe s.), avec Gao pour capitale, supplanta "
            "l'empire du Mali. L'askia Mohammed Touré centralisa l'administration "
            "et fit de Tombouctou un centre intellectuel de premier plan. "
            "L'armée marocaine, équipée d'armes à feu, mit fin à l'empire en "
            "1591 lors de la bataille de Tondibi."
        ),
        "grand zimbabwe": (
            "Le Grand Zimbabwe (XIIIe-XVe s.) était la capitale d'un puissant "
            "royaume commercial. Ses murailles de pierre atteignent 11 m de "
            "hauteur, construites sans mortier. Le site couvre 722 hectares "
            "pour 18 000 habitants. CORRECTION : construit par les ancêtres des "
            "Shona. La théorie coloniale l'attribuant aux Phéniciens ou à la "
            "Reine de Saba est une FALSIFICATION raciste, réfutée par "
            "l'archéologie moderne."
        ),
        "royaume benin bronzes": (
            "Le royaume du Bénin (XIIe-XIXe s., Nigeria actuel) était célèbre "
            "pour ses bronzes et ivoires d'une qualité artistique exceptionnelle. "
            "Les têtes en bronze et plaques narratives du palais royal, pillées "
            "par l'expédition britannique de 1897, sont des chefs-d'œuvre de "
            "l'art universel. Le Nigeria demande leur restitution aux musées "
            "occidentaux."
        ),

        # ── VOLUME 5 : TRAITE NÉGRIÈRE ──
        "traite negriere transatlantique": (
            "La traite négrière transatlantique a déporté 12 à 15 millions "
            "d'Africains vers les Amériques (XVIe-XIXe s.), la plus grande "
            "déportation forcée de l'histoire. Environ 2 millions sont morts "
            "pendant la traversée (le Passage du Milieu). La traite "
            "transsaharienne a déporté 7 à 10 millions d'Africains vers le "
            "monde arabo-musulman. L'impact démographique fut catastrophique : "
            "l'Afrique est passée de 18% à 8% de la population mondiale entre "
            "1600 et 1900."
        ),
        "reine nzinga": (
            "La reine Nzinga du Ndongo et du Matamba (Angola actuel) a mené "
            "une guerre de 30 ans contre les Portugais au XVIIe siècle. "
            "Stratège militaire et diplomate, elle a négocié avec les Portugais "
            "tout en menant des opérations de guérilla. Elle a offert refuge "
            "aux esclaves en fuite et est devenue un symbole de la résistance "
            "africaine à la traite négrière et à la colonisation."
        ),
        "olaudah equiano": (
            "Olaudah Equiano (1745-1797), ancien esclave devenu écrivain et "
            "militant abolitionniste, a publié son autobiographie 'The "
            "Interesting Narrative' en 1789. Ce témoignage bouleversant de "
            "l'expérience de la traite négrière est devenu un best-seller et "
            "a joué un rôle crucial dans le mouvement pour l'abolition de la "
            "traite britannique en 1807."
        ),

        # ── VOLUME 6 : COLONISATION ──
        "conference berlin partage afrique": (
            "La Conférence de Berlin (1884-1885), convoquée par Bismarck, a "
            "organisé le partage de l'Afrique entre puissances européennes. "
            "Aucun Africain n'était présent. En 30 ans, la quasi-totalité du "
            "continent passa sous domination coloniale. Les frontières tracées "
            "arbitrairement à Berlin, sans considération pour les réalités "
            "ethniques ou historiques, sont à l'origine de nombreux conflits "
            "contemporains."
        ),
        "samory toure": (
            "Samory Touré (1830-1900) a mené une guerre de résistance de 17 ans "
            "(1881-1898) contre les Français en Afrique de l'Ouest. Il construisit "
            "un empire s'étendant de la Guinée à la Côte d'Ivoire, modernisa son "
            "armée et établit des ateliers de fabrication d'armes. Capturé en "
            "1898, il fut exilé au Gabon où il mourut."
        ),
        "bataille adoua menelik": (
            "Ménélik II, empereur d'Éthiopie, infligea une défaite décisive à "
            "l'armée italienne à la bataille d'Adoua le 1er mars 1896. "
            "100 000 soldats éthiopiens vainquirent 17 000 Italiens. C'est "
            "l'unique victoire d'une armée africaine contre une puissance "
            "coloniale à cette époque. L'Éthiopie préserva ainsi sa souveraineté."
        ),
        "chaka zoulou": (
            "Chaka (1787-1828), roi des Zoulous, créa un État militaire puissant "
            "en Afrique australe. Il révolutionna les tactiques militaires "
            "(formation en cornes de buffle), l'armement (lance courte iklwa) "
            "et l'organisation sociale. Son empire résista aux Britanniques, "
            "remportant la bataille d'Isandhlwana en 1879 avant d'être vaincu."
        ),

        # ── VOLUME 7 : DOMINATION COLONIALE ──
        "congo leopold exploitation": (
            "Dans l'État indépendant du Congo, propriété personnelle du roi "
            "Léopold II de Belgique (1885-1908), l'exploitation du caoutchouc "
            "a causé la mort de 5 à 10 millions de Congolais. Les mutilations "
            "de mains étaient documentées. Le scandale international dénoncé "
            "par E.D. Morel, Roger Casement et Mark Twain conduisit la Belgique "
            "à reprendre le Congo en 1908."
        ),
        "panafricanisme": (
            "Le panafricanisme est un mouvement intellectuel et politique visant "
            "l'unité et la solidarité des peuples africains. W.E.B. Du Bois "
            "organisa le premier Congrès panafricain à Paris en 1919. Marcus "
            "Garvey fonda l'UNIA prônant le retour en Afrique. Le panafricanisme "
            "jeta les bases idéologiques des mouvements d'indépendance africains."
        ),

        # ── VOLUME 8 : DÉSCOLONISATION ──
        "annee afrique 1960 independances": (
            "L'année 1960 est l'Année de l'Afrique : 17 pays accédèrent à "
            "l'indépendance. Le Ghana de Kwame Nkrumah, indépendant dès 1957, "
            "avait ouvert la voie. Nkrumah déclara : 'L'indépendance du Ghana "
            "n'a aucun sens si elle n'est pas liée à la libération totale du "
            "continent africain.' L'OUA fut fondée en 1963 à Addis-Abeba."
        ),
        "patrice lumumba": (
            "Patrice Lumumba (1925-1961), premier Premier ministre du Congo "
            "indépendant, fut assassiné le 17 janvier 1961 avec la complicité "
            "de la CIA et de la Belgique. Son discours du 30 juin 1960, "
            "dénonçant l'exploitation coloniale devant le roi des Belges, "
            "reste un moment fondateur de la dignité africaine. Il est "
            "considéré comme un héros national et un martyr de la libération "
            "africaine."
        ),
        "nelson mandela apartheid": (
            "Nelson Mandela (1918-2013) lutta contre l'apartheid en Afrique du "
            "Sud. Emprisonné 27 ans (1962-1990), il devint le premier président "
            "noir d'Afrique du Sud en 1994. Prix Nobel de la paix 1993 avec "
            "Frederik de Klerk. Sa philosophie de réconciliation ('ubuntu') a "
            "inspiré le monde entier. L'apartheid, système de ségrégation "
            "raciale (1948-1991), fut vaincu par la lutte du peuple sud-africain "
            "et la solidarité internationale."
        ),
        "union africaine ua": (
            "L'Union Africaine (UA), fondée en 2002, succède à l'OUA. Elle "
            "compte 55 États membres. Ses objectifs : intégration politique et "
            "économique, paix, sécurité, développement durable. L'Agenda 2063 "
            "est son plan stratégique. La ZLECAf (Zone de Libre-Échange "
            "Continentale Africaine) est la plus grande zone de libre-échange "
            "au monde. L'Afrique compte 1,4 milliard d'habitants, l'âge médian "
            "le plus jeune du monde (19 ans)."
        ),
    }


def inject_africa_into_enricher(enricher):
    """Injecte les 8 tomes dans l'enricher."""
    blocks = get_africa_blocks()
    added = 0
    for sujet, texte in blocks.items():
        if not enricher.has_bloc(sujet):
            enricher.enrich_curated(sujet, texte, 'definition')
            added += 1
    return added
