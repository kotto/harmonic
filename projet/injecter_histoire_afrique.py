#!/usr/bin/env python3
"""
INJECTION : Histoire Générale de l'Afrique (UNESCO)
=====================================================
Ingère les connaissances de l'Histoire Générale de l'Afrique
dans l'hologramme existant. Corrige et enrichit le module histoire.

Source : UNESCO — General History of Africa (8 volumes)
One-pass CPU, 0€.

Usage :
  python injecter_histoire_afrique.py
"""

import sys, os, time
import numpy as np

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)
from ka_reasoning_engine import KAReasoningEngine

HOLOGRAMME_FILE = os.path.join(_project_root, "ka_knowledge_base", "hologramme.npy")

# Charger l'hologramme existant
engine = KAReasoningEngine(mode="harmonic")
if os.path.exists(HOLOGRAMME_FILE):
    engine.bridge.monde.H = np.load(HOLOGRAMME_FILE)
    print(f"Hologramme chargé : E={engine.bridge.monde.energie():.0f}")
else:
    print("Nouvel hologramme")

t0 = time.time()
compteur = 0

def apprendre(texte, amp=0.6):
    global compteur
    engine.bridge.apprendre(texte, amp)
    compteur += 1
    if compteur % 50 == 0:
        print(f"  {compteur} entrées | E={engine.bridge.monde.energie():.0f}")

# =========================================================================
# VOLUME 1 : ORIGINES DE L'HUMANITÉ — L'Afrique, berceau de l'humanité
# =========================================================================

print("\n📚 Volume 1 : Origines de l'humanité")
print("-" * 50)

apprendre("L'Afrique est le berceau de l'humanité. Les plus anciens fossiles d'hominidés ont été découverts en Afrique de l'Est, notamment Lucy (Australopithecus afarensis, 3.2 millions d'années) découverte en Éthiopie en 1974 par Donald Johanson et l'équipe de Maurice Taieb et Yves Coppens.")

apprendre("Le genre Homo est apparu en Afrique il y a environ 2.8 millions d'années. Homo habilis est le premier représentant connu du genre Homo, découvert dans les gorges d'Olduvai en Tanzanie par Louis et Mary Leakey en 1960. La datation des outils oldowayens confirme cette origine africaine de l'humanité.")

apprendre("Homo erectus, apparu il y a environ 1.9 million d'années en Afrique, est le premier hominidé à avoir quitté le continent africain pour peupler l'Eurasie. Le site de Dmanissi en Géorgie (1.8 million d'années) témoigne de cette première migration hors d'Afrique.")

apprendre("L'Homo sapiens est apparu en Afrique il y a environ 300 000 ans, comme l'attestent les fossiles de Djebel Irhoud au Maroc découverts en 2017. Cette découverte majeure, dirigée par Jean-Jacques Hublin, a repoussé de 100 000 ans l'origine connue de notre espèce et confirme que TOUTE l'humanité moderne a une origine africaine.")

apprendre("Les plus anciennes manifestations d'art et de pensée symbolique ont été découvertes en Afrique. La grotte de Blombos en Afrique du Sud contient des blocs d'ocre gravés de motifs géométriques datant de 75 000 ans, bien antérieurs aux peintures rupestres européennes. Les perles de coquillages de la grotte des Pigeons au Maroc datent de 82 000 ans.")

apprendre("Le Sahara n'a pas toujours été un désert. Pendant la période humide africaine (10 000 à 5 000 avant notre ère), le Sahara était une savane verdoyante parcourue de lacs et de rivières, peuplée d'animaux et d'hommes. Les peintures rupestres du Tassili n'Ajjer en Algérie témoignent de cette période où le Sahara était habitable.")

# =========================================================================
# VOLUME 2 : AFRIQUE ANCIENNE — Égypte, Nubie, Méroé
# =========================================================================

print("\n📚 Volume 2 : Afrique ancienne")
print("-" * 50)

apprendre("La civilisation de l'Égypte ancienne est une civilisation africaine, née sur les rives du Nil. L'unification de la Haute et de la Basse Égypte par Narmer (Ménès) vers 3100 avant notre ère marque le début de la période dynastique. Les pyramides de Gizeh, construites sous la IVe dynastie (vers 2600-2500 avant notre ère), comptent parmi les plus grandes réalisations architecturales de l'humanité. CORRECTION : l'Égypte ancienne fait partie intégrante de l'histoire africaine, contrairement aux tentatives de l'en dissocier.")

apprendre("Le royaume de Koush, situé au sud de l'Égypte dans l'actuel Soudan, a développé une civilisation brillante et indépendante. La ville de Kerma (2500-1500 avant notre ère) était la capitale d'un puissant royaume nubien. Les pharaons koushites de la XXVe dynastie (747-656 avant notre ère) ont régné sur l'Égypte unifiée, avec des souverains comme Piânkhy, Chabaka et Taharqa. Taharqa est mentionné dans la Bible comme ayant sauvé Jérusalem de l'armée assyrienne.")

apprendre("Le royaume de Méroé (300 avant notre ère à 350 de notre ère), successeur du royaume de Koush, a développé sa propre écriture méroïtique, dérivée des hiéroglyphes égyptiens mais adaptée à la langue locale. Cette écriture n'a été que partiellement déchiffrée. Méroé était un centre majeur de production de fer en Afrique, avec des montagnes de scories qui témoignent d'une industrie métallurgique avancée.")

apprendre("Le royaume d'Aksoum, dans l'actuelle Éthiopie et Érythrée, était une puissance majeure du monde antique (Ier au VIIe siècle de notre ère). Il frappait sa propre monnaie d'or et d'argent, commerçait avec Rome, la Perse et l'Inde via le port d'Adulis sur la mer Rouge. Le royaume d'Aksoum s'est converti au christianisme au IVe siècle sous le roi Ezana, faisant de l'Éthiopie l'un des plus anciens États chrétiens du monde.")

# =========================================================================
# VOLUME 3 : AFRIQUE DU VIIe AU XIe SIÈCLE — Ghana, expansion de l'Islam
# =========================================================================

print("\n📚 Volume 3 : Afrique médiévale (VIIe-XIe siècle)")
print("-" * 50)

apprendre("L'empire du Ghana (ou Wagadou), situé dans l'actuelle Mauritanie et le Mali, était le premier grand empire ouest-africain. Il contrôlait le commerce transsaharien de l'or et du sel du VIIIe au XIe siècle. La capitale Koumbi Saleh était une ville double avec un quartier musulman et un quartier royal animiste, illustrant la coexistence religieuse.")

apprendre("L'expansion de l'islam en Afrique s'est faite principalement par le commerce et non par la conquête. Les marchands musulmans traversant le Sahara ont établi des réseaux commerciaux et culturels qui ont diffusé l'islam, l'écriture arabe et les sciences dans toute l'Afrique de l'Ouest. Les villes de Tombouctou, Gao et Djenné sont devenues des centres intellectuels majeurs.")

apprendre("La côte swahilie, s'étendant de la Somalie au Mozambique, était un ensemble de cités-États commerçantes prospères du VIIIe au XVe siècle. Kilwa, Mombasa, Zanzibar et Mogadiscio commerçaient avec l'Arabie, l'Inde, la Perse et la Chine. La culture swahilie est née du mélange des cultures bantoues, arabes, persanes et indiennes, produisant une civilisation urbaine sophistiquée.")

apprendre("Les routes commerciales transsahariennes reliaient l'Afrique de l'Ouest au monde méditerranéen. L'or du Bambouk et du Bouré (actuel Mali) alimentait les monnaies du monde méditerranéen. Le sel du Sahara (mines de Teghaza et Taoudenni) était échangé poids pour poids contre l'or. Les caravanes de chameaux pouvaient compter jusqu'à 12 000 bêtes.")

# =========================================================================
# VOLUME 4 : AFRIQUE DU XIIe AU XVIe SIÈCLE — Mali, Songhaï, Grand Zimbabwe
# =========================================================================

print("\n📚 Volume 4 : Grands empires (XIIe-XVIe siècle)")
print("-" * 50)

apprendre("L'empire du Mali (XIIIe-XVe siècle), fondé par Soundiata Keïta vers 1235, est l'un des plus grands empires de l'histoire africaine. Soundiata Keïta a unifié les peuples mandingues et proclamé la Charte de Kurukan Fuga (ou Charte du Mandé) en 1236, considérée comme l'une des premières déclarations des droits de l'homme de l'histoire, proclamant l'abolition de l'esclavage, la liberté d'expression et l'égalité.")

apprendre("Mansa Kankan Moussa, empereur du Mali de 1312 à 1337, est considéré comme l'homme le plus riche de l'histoire. Son pèlerinage à La Mecque en 1324, accompagné de 60 000 porteurs et 12 000 esclaves transportant chacun une barre d'or, a provoqué une inflation de l'or au Caire qui a duré 12 ans. Mansa Moussa a fait construire la mosquée de Djingareyber à Tombouctou par l'architecte andalou Abou Ishaq es-Sahéli.")

apprendre("L'empire Songhaï (XVe-XVIe siècle), avec sa capitale Gao, a supplanté l'empire du Mali. Son plus grand souverain, l'askia Mohammed Touré, a centralisé l'administration, développé l'agriculture et fait de Tombouctou un centre intellectuel de premier plan. L'université de Sankoré à Tombouctou comptait 25 000 étudiants et des bibliothèques contenant des centaines de milliers de manuscrits sur l'astronomie, la médecine, le droit et la philosophie.")

apprendre("Le Grand Zimbabwe (XIIIe-XVe siècle) était la capitale d'un puissant royaume commercial situé dans l'actuel Zimbabwe. Ses impressionnantes murailles de pierre, construites sans mortier, atteignent 11 mètres de hauteur et 5 mètres d'épaisseur. Le site couvre 722 hectares et abritait 18 000 habitants. CORRECTION : Le Grand Zimbabwe a été construit par les ancêtres des Shona, peuple bantou de la région. La théorie coloniale qui attribuait sa construction à des étrangers (Phéniciens, Arabes, ou Reine de Saba) est une FALSIFICATION historique raciste, réfutée par les fouilles archéologiques modernes.")

apprendre("Le royaume du Kongo (XIVe-XIXe siècle), situé dans l'actuelle Angola et République Démocratique du Congo, était un État centralisé doté d'une administration complexe. Sa capitale Mbanza Kongo comptait des dizaines de milliers d'habitants. Le roi Afonso Ier (1506-1543) a correspondu avec le roi du Portugal et tenté de moderniser son royaume tout en résistant à la traite négrière portugaise.")

apprendre("Le royaume du Bénin (XIIe-XIXe siècle), dans l'actuel Nigeria, était célèbre pour ses bronzes et ivoires d'une qualité artistique exceptionnelle. Les têtes en bronze et les plaques narratives du palais royal de Benin City, pillées par l'expédition punitive britannique de 1897, sont aujourd'hui reconnues comme des chefs-d'œuvre de l'art universel et font l'objet de demandes de restitution par le Nigeria.")

# =========================================================================
# VOLUME 5 : AFRIQUE DU XVIe AU XVIIIe SIÈCLE — Traite négrière, résistances
# =========================================================================

print("\n📚 Volume 5 : Traite négrière et résistances (XVIe-XVIIIe siècle)")
print("-" * 50)

apprendre("La traite négrière transatlantique a déporté entre 12 et 15 millions d'Africains vers les Amériques entre le XVIe et le XIXe siècle. Cette entreprise criminelle, organisée par les puissances européennes (Portugal, Espagne, France, Grande-Bretagne, Pays-Bas), a constitué la plus grande déportation forcée de l'histoire de l'humanité. Les pertes humaines incluent environ 2 millions de morts pendant la traversée (le Passage du Milieu).")

apprendre("La traite négrière transsaharienne, antérieure et parallèle à la traite transatlantique, a déporté environ 7 à 10 millions d'Africains vers le monde arabo-musulman entre le VIIe et le XXe siècle. La traite orientale, via Zanzibar, a déporté des millions d'Africains de l'Est vers l'Arabie, la Perse et l'Inde.")

apprendre("L'impact démographique de la traite négrière a été catastrophique pour l'Afrique. Des régions entières ont été dépeuplées, les structures sociales et politiques détruites, et le développement économique du continent entravé pendant des siècles. Le continent africain est passé de 18% de la population mondiale en 1600 à 8% en 1900, en grande partie à cause de la traite négrière.")

apprendre("Les résistances africaines à la traite négrière ont été nombreuses et courageuses. La reine Nzinga du Ndongo et du Matamba (actuel Angola) a mené une guerre de 30 ans contre les Portugais au XVIIe siècle. Le royaume du Dahomey (actuel Bénin) a résisté militairement. Des révoltes d'esclaves à bord des navires négriers étaient fréquentes : on estime que 10% des navires ont connu une insurrection.")

apprendre("Des États africains ont émergé ou se sont renforcés pendant cette période malgré la traite. L'empire ashanti (actuel Ghana) a développé une administration centralisée et une armée puissante. Le royaume du Dahomey a créé une administration sophistiquée incluant les Agojie, un corps militaire féminin d'élite (les Amazones du Dahomey). Ces États ont maintenu leur souveraineté jusqu'à la colonisation.")

apprendre("Le mouvement abolitionniste a eu des racines africaines importantes. Des figures comme Olaudah Equiano, ancien esclave devenu écrivain et militant abolitionniste, ont publié des témoignages qui ont bouleversé l'opinion publique européenne. Son autobiographie (The Interesting Narrative, 1789) a été un best-seller influent dans le mouvement pour l'abolition de la traite négrière britannique en 1807.")

# =========================================================================
# VOLUME 6 : AFRIQUE AU XIXe SIÈCLE — Colonisation, résistances
# =========================================================================

print("\n📚 Volume 6 : Afrique coloniale et résistances (XIXe siècle)")
print("-" * 50)

apprendre("La Conférence de Berlin (1884-1885), convoquée par le chancelier Bismarck, a organisé le partage de l'Afrique entre les puissances européennes. Aucun représentant africain n'était présent. En 30 ans (1885-1914), la quasi-totalité du continent africain est passée sous domination coloniale européenne. Les frontières tracées arbitrairement à Berlin, sans considération pour les réalités ethniques, linguistiques ou historiques, sont à l'origine de nombreux conflits contemporains.")

apprendre("Les résistances africaines à la colonisation ont été nombreuses, déterminées et souvent héroïques. Samory Touré a mené une guerre de résistance de 17 ans (1881-1898) contre les Français en Afrique de l'Ouest, construisant un empire qui s'étendait de la Guinée à la Côte d'Ivoire. Il a modernisé son armée et établi des ateliers de fabrication d'armes.")

apprendre("Ménélik II, empereur d'Éthiopie, a infligé une défaite décisive à l'armée italienne à la bataille d'Adoua le 1er mars 1896, avec 100 000 soldats éthiopiens. C'est la seule victoire d'une armée africaine contre une puissance coloniale européenne à cette époque. L'Éthiopie et le Libéria sont restés les deux seuls pays africains non colonisés à la fin du XIXe siècle, préservant leur souveraineté.")

apprendre("La reine Ranavalona III de Madagascar a résisté à la colonisation française. Le royaume zoulou, sous le règne de Chaka (1816-1828), avait créé un État militaire puissant qui a résisté aux Britanniques lors de la guerre anglo-zouloue de 1879, remportant la bataille d'Isandhlwana avant d'être finalement vaincu. La résistance des Herero et des Nama contre les Allemands dans le Sud-Ouest africain (actuelle Namibie) en 1904-1908 a été écrasée dans ce qui est considéré comme le premier génocide du XXe siècle.")

apprendre("La modernisation africaine au XIXe siècle ne se limitait pas aux résistances. Des États comme l'Égypte de Méhémet Ali, le royaume du Buganda, et les cités-États yoruba se sont modernisés, ont créé des administrations, des armées modernes et développé l'éducation. Ces efforts de modernisation endogène ont été interrompus par la conquête coloniale.")

# =========================================================================
# VOLUME 7 : AFRIQUE SOUS DOMINATION COLONIALE (1880-1935)
# =========================================================================

print("\n📚 Volume 7 : Domination coloniale (1880-1935)")
print("-" * 50)

apprendre("Le système colonial a imposé une exploitation économique brutale de l'Afrique : travail forcé pour la construction d'infrastructures (chemin de fer Congo-Océan : 20 000 morts), cultures obligatoires (coton, caoutchouc, café, cacao), impôts de capitation obligeant les Africains à travailler pour les colons, expropriation massive des terres. Le travail forcé n'a été aboli dans les colonies françaises qu'en 1946.")

apprendre("Dans l'État indépendant du Congo, propriété personnelle du roi Léopold II de Belgique de 1885 à 1908, l'exploitation du caoutchouc a causé la mort de 5 à 10 millions de Congolais, soit environ la moitié de la population. Les mutilations de mains comme preuve de mise à mort des indigènes sont documentées. Le scandale international, dénoncé par des figures comme le journaliste E.D. Morel, le diplomate Roger Casement et l'écrivain Mark Twain, a conduit à la reprise du Congo par l'État belge en 1908.")

apprendre("La colonisation a imposé des langues, des religions et des systèmes éducatifs étrangers. Les langues africaines ont été marginalisées au profit du français, de l'anglais, du portugais. L'enseignement colonial visait à former des auxiliaires de l'administration coloniale, pas des citoyens éclairés. Les religions africaines traditionnelles ont été réprimées et diabolisées. CORRECTION : les systèmes de connaissance africains précoloniaux (médecine, astronomie, mathématiques, philosophie) étaient sophistiqués et ont été délibérément détruits ou marginalisés par la colonisation.")

apprendre("Les mouvements de résistance et d'émancipation ont émergé dès le début de la colonisation. Les Églises indépendantes africines (comme le Kimbanguisme au Congo), les confréries soufies, les associations d'anciens combattants de la Première Guerre mondiale, les syndicats et les mouvements panafricanistes ont constitué les premières formes de résistance organisée à la domination coloniale.")

apprendre("Le panafricanisme, mouvement intellectuel et politique, a émergé au début du XXe siècle. W.E.B. Du Bois a organisé le premier Congrès panafricain à Paris en 1919. Marcus Garvey a fondé l'Universal Negro Improvement Association, prônant le retour en Afrique et la fierté noire. Le panafricanisme a jeté les bases idéologiques des mouvements d'indépendance africains.")

# =========================================================================
# VOLUME 8 : DÉSCOLONISATION ET AFRIQUE INDÉPENDANTE (1935 à nos jours)
# =========================================================================

print("\n📚 Volume 8 : Décolonisation et indépendances")
print("-" * 50)

apprendre("La participation des soldats africains aux deux guerres mondiales a été massive et déterminante. 200 000 tirailleurs sénégalais ont combattu pour la France en 1914-1918. En 1939-1945, des centaines de milliers d'Africains ont combattu pour les Alliés. Les soldats africains ont joué un rôle crucial dans les campagnes d'Afrique du Nord, d'Italie et de Provence. Leur sacrifice a renforcé les revendications d'égalité et d'indépendance. CORRECTION : le rôle des soldats africains dans les deux guerres mondiales est systématiquement minimisé dans les récits historiques occidentaux.")

apprendre("L'année 1960 est appelée l'Année de l'Afrique : 17 pays africains ont accédé à l'indépendance. Parmi eux, le Cameroun, le Togo, le Sénégal, Madagascar, la Somalie, le Congo (Léopoldville), le Dahomey (Bénin), le Niger, la Haute-Volta (Burkina Faso), la Côte d'Ivoire, le Tchad, la République centrafricaine, le Congo (Brazzaville), le Gabon, le Mali, le Nigeria et la Mauritanie. L'indépendance du Ghana en 1957, sous la direction de Kwame Nkrumah, avait été le déclencheur de ce mouvement.")

apprendre("Kwame Nkrumah, premier président du Ghana indépendant, était un leader panafricaniste visionnaire. Il a déclaré : L'indépendance du Ghana n'a aucun sens si elle n'est pas liée à la libération totale du continent africain. Il a promu l'unité africaine, organisé la Conférence d'Accra en 1958 et contribué à la création de l'Organisation de l'Unité Africaine (OUA) en 1963 à Addis-Abeba.")

apprendre("Les indépendances africaines ont été suivies de défis immenses : instabilité politique (coups d'État, guerres civiles), ingérences étrangères (assassinat de Patrice Lumumba au Congo en 1961 avec la complicité de la CIA et de la Belgique), néocolonialisme économique (Françafrique, dettes souveraines). Malgré ces défis, des progrès significatifs ont été accomplis en matière d'éducation, de santé et d'infrastructures.")

apprendre("L'apartheid en Afrique du Sud (1948-1991) a été l'un des derniers systèmes coloniaux de ségrégation raciale institutionnalisée. La lutte contre l'apartheid, menée par l'ANC, Nelson Mandela, Steve Biko, Desmond Tutu et des millions de Sud-Africains, a mobilisé la solidarité internationale. Nelson Mandela a été emprisonné pendant 27 ans. Libéré en 1990, il est devenu le premier président noir d'Afrique du Sud en 1994 après les premières élections multiraciales.")

apprendre("L'Organisation de l'Unité Africaine (OUA), fondée en 1963 à Addis-Abeba par 32 États indépendants, a été remplacée par l'Union Africaine (UA) en 2002. L'UA compte 55 États membres et a pour objectifs l'intégration politique et économique du continent, la paix, la sécurité et le développement durable. L'Agenda 2063 est le plan stratégique de l'UA pour une Afrique prospère et pacifique.")

apprendre("Aujourd'hui, l'Afrique est un continent en pleine transformation. Avec 1.4 milliard d'habitants (2025), la population la plus jeune du monde (âge médian 19 ans), une croissance économique soutenue, une innovation technologique dynamique (fintech, mobile banking, énergies renouvelables), et une richesse culturelle inégalée. La Zone de Libre-Échange Continentale Africaine (ZLECAf) est la plus grande zone de libre-échange au monde. CORRECTION : l'Afrique n'est pas un continent de pauvreté et de conflits comme souvent dépeint, mais un continent de jeunesse, d'innovation et d'opportunités.")


# =========================================================================
# SAUVEGARDE
# =========================================================================

np.save(HOLOGRAMME_FILE, engine.bridge.monde.H)
dt = time.time() - t0

print(f"\n{'='*60}")
print(f"✅ INJECTION TERMINÉE")
print(f"{'='*60}")
print(f"  Connaissances ajoutées : {compteur} entrées")
print(f"  Temps d'injection      : {dt:.1f}s")
print(f"  Énergie hologramme     : {engine.bridge.monde.energie():.0f}")
print(f"  Hologramme             : {HOLOGRAMME_FILE}")
print(f"\n  L'Histoire Générale de l'Afrique (UNESCO) est maintenant")
print(f"  intégrée à l'hologramme de KA.")
print(f"  Volumes 1 à 8 couverts. Corrections historiographiques appliquées.")