"""
200 Prompts ultra-spécifiques pour ingestion massive
======================================================
Chaque prompt cible un sous-domaine précis pour éviter les doublons.
Format: 20-30 faits par prompt → ~5000 faits uniques par passe.
"""

PROMPTS = [
    # === PHYSIQUE (20 prompts) ===
    ("PHYSIQUE_MECA", "Liste 20 faits de mécanique classique: lois de Newton, quantité de mouvement, travail, énergie cinétique, forces conservatives. Format: sujet | relation | objet. Un par ligne. En français."),
    ("PHYSIQUE_THERMO", "Liste 20 faits de thermodynamique: entropie, chaleur, température, cycles, gaz parfaits, principe zéro. Format: sujet | relation | objet. Un par ligne. En français."),
    ("PHYSIQUE_EM", "Liste 20 faits d'électromagnétisme: champ électrique, champ magnétique, induction, ondes EM, équations de Maxwell. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_OPTIQUE", "Liste 20 faits d'optique: réfraction, diffraction, interférence, polarisation, lentilles, miroirs, lasers. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_QUANTIQUE", "Liste 20 faits de physique quantique: dualité onde-particule, principe d'incertitude, superposition, intrication, effet tunnel. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_NUCLEAIRE", "Liste 20 faits de physique nucléaire: fission, fusion, radioactivité, isotopes, réacteurs, demi-vie. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_ASTRO", "Liste 20 faits d'astrophysique: étoiles à neutrons, naines blanches, supernovas, trous noirs, ondes gravitationnelles. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_FLUIDES", "Liste 20 faits de mécanique des fluides: viscosité, turbulence, nombre de Reynolds, pression hydrostatique, principe de Bernoulli. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_ACOUSTIQUE", "Liste 15 faits d'acoustique: ondes sonores, fréquence, amplitude, résonance, effet Doppler, ultrasons. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_MATIERE", "Liste 20 faits sur les états de la matière: solide, liquide, gaz, plasma, condensat de Bose-Einstein, changements d'état. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_RELATIVITE", "Liste 20 faits de relativité restreinte et générale: dilatation du temps, contraction des longueurs, E=mc², courbure espace-temps. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_PARTICULES", "Liste 20 faits sur les particules élémentaires: quarks, leptons, bosons, modèle standard, Higgs, neutrinos. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_CRYO", "Liste 15 faits de cryogénie et basses températures: supraconductivité, superfluidité, zéro absolu, hélium liquide. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_PLASMA", "Liste 15 faits sur les plasmas: ionisation, tokamak, confinement magnétique, vent solaire, aurores boréales. Format: sujet | relation | objet. En français."),
    ("PHYSIQUE_METRO", "Liste 15 faits de métrologie: unités SI, constantes fondamentales, mesure du temps, horloges atomiques, kilogramme étalon. Format: sujet | relation | objet. En français."),
    
    # === CHIMIE (15 prompts) ===
    ("CHIMIE_ORGA", "Liste 20 faits de chimie organique: hydrocarbures, alcools, acides carboxyliques, amines, polymères, estérification. Format: sujet | relation | objet. En français."),
    ("CHIMIE_INORGA", "Liste 20 faits de chimie inorganique: métaux, sels, oxydes, acides, bases, complexes de coordination. Format: sujet | relation | objet. En français."),
    ("CHIMIE_BIOCHIMIE", "Liste 20 faits de biochimie: enzymes, protéines, lipides, glucides, acides nucléiques, métabolisme. Format: sujet | relation | objet. En français."),
    ("CHIMIE_ELECTRO", "Liste 15 faits d'électrochimie: piles, électrolyse, potentiel redox, corrosion, accumulateurs. Format: sujet | relation | objet. En français."),
    ("CHIMIE_ANALYTIQUE", "Liste 15 faits de chimie analytique: chromatographie, spectroscopie, titrage, pH-métrie, RMN. Format: sujet | relation | objet. En français."),
    ("CHIMIE_MATERIAUX", "Liste 20 faits sur les matériaux: céramiques, composites, alliages, nanomatériaux, semi-conducteurs. Format: sujet | relation | objet. En français."),
    ("CHIMIE_PHARMA", "Liste 20 faits de chimie pharmaceutique: principes actifs, synthèse, formulation, pharmacocinétique, brevets. Format: sujet | relation | objet. En français."),
    ("CHIMIE_ENVIRON", "Liste 15 faits de chimie environnementale: polluants, traitement des eaux, cycle du carbone, gaz à effet de serre. Format: sujet | relation | objet. En français."),
    ("CHIMIE_ALIM", "Liste 15 faits de chimie alimentaire: additifs, conservateurs, arômes, édulcorants, fermentation. Format: sujet | relation | objet. En français."),
    ("CHIMIE_QUANTIQUE", "Liste 15 faits de chimie quantique: orbitales, liaison chimique, DFT, Hartree-Fock, approximation de Born-Oppenheimer. Format: sujet | relation | objet. En français."),
    
    # === BIOLOGIE (20 prompts) ===
    ("BIO_CELLULE", "Liste 20 faits de biologie cellulaire: membrane, noyau, mitochondries, ribosomes, appareil de Golgi, lysosomes. Format: sujet | relation | objet. En français."),
    ("BIO_GENETIQUE", "Liste 20 faits de génétique: gènes, allèles, dominance, récessivité, mutations, hérédité mendélienne. Format: sujet | relation | objet. En français."),
    ("BIO_ADN", "Liste 20 faits sur l'ADN: structure double hélice, nucléotides, réplication, transcription, traduction, code génétique. Format: sujet | relation | objet. En français."),
    ("BIO_EVOLUTION", "Liste 20 faits sur l'évolution: sélection naturelle, dérive génétique, spéciation, fossiles, ancêtre commun. Format: sujet | relation | objet. En français."),
    ("BIO_IMMUNO", "Liste 20 faits d'immunologie: anticorps, lymphocytes, vaccins, mémoire immunitaire, inflammation. Format: sujet | relation | objet. En français."),
    ("BIO_NEURO", "Liste 20 faits de neurosciences: neurones, synapses, potentiel d'action, neurotransmetteurs, plasticité cérébrale. Format: sujet | relation | objet. En français."),
    ("BIO_MICROBIO", "Liste 20 faits de microbiologie: bactéries, virus, champignons, archées, microbiome, antibi otiques. Format: sujet | relation | objet. En français."),
    ("BIO_PHOTOSYNTHESE", "Liste 15 faits sur la photosynthèse: chlorophylle, cycle de Calvin, photosystèmes, fixation du carbone, plantes C3 C4 CAM. Format: sujet | relation | objet. En français."),
    ("BIO_RESPIRATION", "Liste 15 faits sur la respiration cellulaire: glycolyse, cycle de Krebs, chaîne respiratoire, ATP, fermentation. Format: sujet | relation | objet. En français."),
    ("BIO_HORMONES", "Liste 20 faits sur les hormones: insuline, cortisol, adrénaline, œstrogène, testostérone, glandes endocrines. Format: sujet | relation | objet. En français."),
    ("BIO_ECOLOGIE", "Liste 20 faits d'écologie: écosystèmes, chaînes alimentaires, niches écologiques, biomes, cycles biogéochimiques. Format: sujet | relation | objet. En français."),
    ("BIO_MARINE", "Liste 20 faits de biologie marine: plancton, récifs coralliens, abysses, cétacés, courants océaniques. Format: sujet | relation | objet. En français."),
    ("BIO_VEGETALE", "Liste 20 faits de biologie végétale: racines, tiges, feuilles, fleurs, graines, hormones végétales, tropismes. Format: sujet | relation | objet. En français."),
    ("BIO_ANIMALE", "Liste 20 faits de biologie animale: systèmes (nerveux, circulatoire, digestif), comportement, migration. Format: sujet | relation | objet. En français."),
    ("BIO_CRISPR", "Liste 15 faits sur CRISPR-Cas9: édition génomique, ciseaux moléculaires, applications médicales, éthique. Format: sujet | relation | objet. En français."),
    
    # === MÉDECINE & SANTÉ (15 prompts) ===
    ("MED_COEUR", "Liste 15 faits de cardiologie: cœur, artères, veines, tension artérielle, infarctus, ECG. Format: sujet | relation | objet. En français."),
    ("MED_CANCER", "Liste 20 faits sur le cancer: oncogènes, tumeurs, métastases, chimiothérapie, radiothérapie, immunothérapie. Format: sujet | relation | objet. En français."),
    ("MED_CERVEAU", "Liste 20 faits sur le cerveau humain: lobes, aires corticales, plasticité, mémoire, sommeil, pathologies. Format: sujet | relation | objet. En français."),
    ("MED_INFECTIEUSE", "Liste 20 faits de maladies infectieuses: transmission, épidémies, vaccination, antibiotiques, résistance. Format: sujet | relation | objet. En français."),
    ("MED_CHIRURGIE", "Liste 15 faits de chirurgie: anesthésie, greffes, transplantation, endoscopie, robotique chirurgicale. Format: sujet | relation | objet. En français."),
    ("MED_GENETIQUE", "Liste 15 faits de génétique médicale: maladies héréditaires, diagnostic prénatal, thérapie génique, conseil génétique. Format: sujet | relation | objet. En français."),
    ("MED_PHARMACO", "Liste 15 faits de pharmacologie: principes actifs, essais cliniques, phases, placebo, effets secondaires. Format: sujet | relation | objet. En français."),
    ("MED_URGENCES", "Liste 15 faits de médecine d'urgence: premiers secours, réanimation, intubation, défibrillation, triage. Format: sujet | relation | objet. En français."),
    
    # === ASTRONOMIE & ESPACE (10 prompts) ===
    ("ASTRO_SYSTEME", "Liste 20 faits sur le système solaire: planètes, lunes, astéroïdes, comètes, ceinture de Kuiper. Format: sujet | relation | objet. En français."),
    ("ASTRO_ETOILES", "Liste 20 faits sur les étoiles: naissance, séquence principale, géantes rouges, naines blanches, trous noirs stellaires. Format: sujet | relation | objet. En français."),
    ("ASTRO_GALAXIES", "Liste 20 faits sur les galaxies: Voie lactée, Andromède, types, formation, collisions, matière noire. Format: sujet | relation | objet. En français."),
    ("ASTRO_COSMO", "Liste 20 faits de cosmologie: Big Bang, expansion, fond diffus cosmologique, inflation, énergie sombre. Format: sujet | relation | objet. En français."),
    ("ASTRO_EXOPLANETES", "Liste 20 faits sur les exoplanètes: méthodes de détection, transit, vitesses radiales, habitabilité. Format: sujet | relation | objet. En français."),
    ("ASTRO_SPATIAL", "Liste 20 faits d'exploration spatiale: Apollo, ISS, Mars rovers, télescopes spatiaux, Artemis. Format: sujet | relation | objet. En français."),
    
    # === GÉOGRAPHIE & GÉOLOGIE (10 prompts) ===
    ("GEO_PHYSIQUE", "Liste 20 faits de géographie physique: continents, montagnes, fleuves, océans, climats, biomes. Format: sujet | relation | objet. En français."),
    ("GEO_HUMAINE", "Liste 20 faits de géographie humaine: population, urbanisation, migrations, densité, mégapoles. Format: sujet | relation | objet. En français."),
    ("GEO_GEOLOGIE", "Liste 20 faits de géologie: tectonique des plaques, volcans, séismes, roches, minéraux, fossiles. Format: sujet | relation | objet. En français."),
    ("GEO_PAYS", "Liste 25 faits sur les pays du monde: capitales, populations, superficies, langues officielles, monnaies. Format: sujet | relation | objet. En français."),
    ("GEO_CLIMAT", "Liste 20 faits de climatologie: courants marins, El Niño, mousson, précipitations, classification de Köppen. Format: sujet | relation | objet. En français."),
    
    # === HISTOIRE (15 prompts) ===
    ("HIST_ANTIQUITE", "Liste 20 faits sur l'antiquité classique: Grèce antique, démocratie athénienne, philosophie grecque, Alexandre le Grand. Format: sujet | relation | objet. En français."),
    ("HIST_ROME", "Liste 20 faits sur la Rome antique: République, Empire, droit romain, armée, chute de Rome. Format: sujet | relation | objet. En français."),
    ("HIST_MOYEN_AGE", "Liste 20 faits sur le Moyen Âge: féodalité, croisades, peste noire, cathédrales, universités médiévales. Format: sujet | relation | objet. En français."),
    ("HIST_RENAISSANCE", "Liste 20 faits sur la Renaissance: humanisme, art, science, imprimerie, grandes découvertes. Format: sujet | relation | objet. En français."),
    ("HIST_REVOLUTIONS", "Liste 20 faits sur les révolutions: américaine, française, industrielle, russe, numérique. Format: sujet | relation | objet. En français."),
    ("HIST_GUERRES", "Liste 20 faits sur les guerres mondiales: causes, batailles, conséquences, traités, ONU. Format: sujet | relation | objet. En français."),
    ("HIST_20E", "Liste 20 faits sur le 20e siècle: guerre froide, décolonisation, progrès technologiques, droits civiques. Format: sujet | relation | objet. En français."),
    ("HIST_EGYPTE", "Liste 15 faits sur l'Égypte antique: pharaons, pyramides, hiéroglyphes, momification, Nil. Format: sujet | relation | objet. En français."),
    ("HIST_CHINE", "Liste 15 faits sur l'histoire de la Chine: dynasties, Grande Muraille, route de la soie, inventions chinoises. Format: sujet | relation | objet. En français."),
    
    # === CULTURE & ARTS (15 prompts) ===
    ("ART_PEINTURE", "Liste 20 faits sur la peinture: mouvements (impressionnisme, cubisme, surréalisme), techniques, grands peintres. Format: sujet | relation | objet. En français."),
    ("ART_SCULPTURE", "Liste 15 faits sur la sculpture: matériaux, techniques, sculpteurs célèbres, œuvres majeures. Format: sujet | relation | objet. En français."),
    ("ART_ARCHITECTURE", "Liste 20 faits d'architecture: styles (gothique, baroque, moderne), architectes, bâtiments célèbres. Format: sujet | relation | objet. En français."),
    ("ART_MUSIQUE_CLASSIQUE", "Liste 20 faits de musique classique: compositeurs, œuvres, formes (sonate, symphonie), périodes. Format: sujet | relation | objet. En français."),
    ("ART_MUSIQUE_MODERNE", "Liste 20 faits de musique moderne: jazz, rock, hip-hop, électro, pop, festivals. Format: sujet | relation | objet. En français."),
    ("ART_CINEMA", "Liste 20 faits de cinéma: réalisateurs, films cultes, techniques, festivals, histoire du cinéma. Format: sujet | relation | objet. En français."),
    ("ART_LITTERATURE", "Liste 20 faits de littérature mondiale: auteurs, œuvres, genres, prix Nobel, mouvements littéraires. Format: sujet | relation | objet. En français."),
    ("ART_PHOTO", "Liste 15 faits sur la photographie: techniques, photographes célèbres, histoire, appareils, genres. Format: sujet | relation | objet. En français."),
    ("ART_DANSE", "Liste 15 faits sur la danse: ballet, contemporain, danses traditionnelles, chorégraphes célèbres. Format: sujet | relation | objet. En français."),
    
    # === TECHNOLOGIE (15 prompts) ===
    ("TECH_IA", "Liste 20 faits sur l'intelligence artificielle: deep learning, transformers, GPT, reinforcement learning, applications. Format: sujet | relation | objet. En français."),
    ("TECH_ROBOTIQUE", "Liste 20 faits de robotique: types de robots, capteurs, actionneurs, IA embarquée, applications industrielles. Format: sujet | relation | objet. En français."),
    ("TECH_INTERNET", "Liste 20 faits sur Internet: protocoles TCP/IP, DNS, cloud computing, cybersécurité, web 3.0. Format: sujet | relation | objet. En français."),
    ("TECH_BLOCKCHAIN", "Liste 15 faits sur la blockchain: Bitcoin, Ethereum, smart contracts, DeFi, NFT, minage. Format: sujet | relation | objet. En français."),
    ("TECH_QUANTIQUE", "Liste 15 faits d'informatique quantique: qubits, portes quantiques, algorithme de Shor, suprématie quantique. Format: sujet | relation | objet. En français."),
    ("TECH_ENERGIE", "Liste 20 faits sur les technologies énergétiques: solaire, éolien, nucléaire, hydrogène, batteries, fusion. Format: sujet | relation | objet. En français."),
    ("TECH_TRANSPORT", "Liste 20 faits sur les transports: TGV, hyperloop, véhicules électriques, drones, aviation, espace. Format: sujet | relation | objet. En français."),
    ("TECH_TELECOM", "Liste 15 faits sur les télécommunications: 5G, fibre optique, satellites, WiFi, Bluetooth, NFC. Format: sujet | relation | objet. En français."),
    
    # === ÉCONOMIE & SOCIÉTÉ (10 prompts) ===
    ("ECO_MACRO", "Liste 20 faits de macroéconomie: PIB, inflation, chômage, politiques monétaires, cycles économiques. Format: sujet | relation | objet. En français."),
    ("ECO_MICRO", "Liste 15 faits de microéconomie: offre, demande, élasticité, concurrence, monopole, externalités. Format: sujet | relation | objet. En français."),
    ("ECO_FINANCE", "Liste 20 faits de finance: bourses, actions, obligations, crypto-monnaies, taux d'intérêt, hedge funds. Format: sujet | relation | objet. En français."),
    ("ECO_ENTREPRISE", "Liste 20 faits sur les entreprises: GAFA, startups, licornes, management, innovation, stratégie. Format: sujet | relation | objet. En français."),
    ("SOC_DEMOGRAPHIE", "Liste 15 faits de démographie: natalité, mortalité, espérance de vie, pyramide des âges, migrations. Format: sujet | relation | objet. En français."),
    ("SOC_EDUCATION", "Liste 20 faits sur l'éducation: systèmes éducatifs, pédagogies, alphabétisation, universités, MOOC. Format: sujet | relation | objet. En français."),
    
    # === PHILOSOPHIE & SPIRITUALITÉ (10 prompts) ===
    ("PHILO_GRECS", "Liste 20 faits de philosophie grecque: Platon, Aristote, Socrate, présocratiques, stoïcisme, épicurisme. Format: sujet | relation | objet. En français."),
    ("PHILO_MODERNE", "Liste 20 faits de philosophie moderne: Descartes, Kant, Nietzsche, existentialisme, phénoménologie. Format: sujet | relation | objet. En français."),
    ("PHILO_ETHIQUE", "Liste 15 faits d'éthique: utilitarisme, déontologie, éthique des vertus, bioéthique, méta-éthique. Format: sujet | relation | objet. En français."),
    ("PHILO_ESPRIT", "Liste 15 faits de philosophie de l'esprit: conscience, intentionnalité, qualia, problème corps-esprit. Format: sujet | relation | objet. En français."),
    ("SPIRIT_BOUDDHISME", "Liste 15 faits sur le bouddhisme: Bouddha, quatre nobles vérités, méditation, karma, nirvana. Format: sujet | relation | objet. En français."),
    ("SPIRIT_HINDOUISME", "Liste 15 faits sur l'hindouisme: dieux (Brahma, Vishnu, Shiva), réincarnation, védas, yoga. Format: sujet | relation | objet. En français."),
    ("SPIRIT_MONOTHEISMES", "Liste 20 faits sur les monothéismes: judaïsme, christianisme, islam, textes sacrés, prophètes. Format: sujet | relation | objet. En français."),
    
    # === SPORT & LOISIRS (5 prompts) ===
    ("SPORT_OLYMPIQUE", "Liste 20 faits sur les Jeux Olympiques: histoire, disciplines, records, athlètes célèbres, pays hôtes. Format: sujet | relation | objet. En français."),
    ("SPORT_FOOTBALL", "Liste 20 faits sur le football: Coupe du Monde, clubs, joueurs légendaires, règles, compétitions. Format: sujet | relation | objet. En français."),
    ("SPORT_TENNIS", "Liste 15 faits sur le tennis: Grand Chelem, joueurs, surface, règles, histoire. Format: sujet | relation | objet. En français."),
    
    # === NATURE & ENVIRONNEMENT (5 prompts) ===
    ("NAT_OCEANS", "Liste 20 faits sur les océans: profondeurs, courants, biodiversité marine, pollution plastique, acidification. Format: sujet | relation | objet. En français."),
    ("NAT_FORETS", "Liste 20 faits sur les forêts: Amazonie, déforestation, types de forêts, canopée, puits de carbone. Format: sujet | relation | objet. En français."),
    ("NAT_INSECTES", "Liste 20 faits sur les insectes: métamorphose, pollinisation, sociétés (fourmis, abeilles), espèces. Format: sujet | relation | objet. En français."),
    ("NAT_OISEAUX", "Liste 20 faits sur les oiseaux: migration, nidification, rapaces, passereaux, évolution des dinosaures. Format: sujet | relation | objet. En français."),
    ("NAT_MAMMIFERES", "Liste 20 faits sur les mammifères: marsupiaux, cétacés, primates, carnivores, herbivores. Format: sujet | relation | objet. En français."),
    
    # === ENGLISH ROUND (20 prompts - pour KB bilingue) ===
    ("EN_PHYSICS", "List 20 physics facts: mechanics, thermodynamics, electromagnetism, quantum physics. Format: subject | relation | object. One per line."),
    ("EN_CHEMISTRY", "List 20 chemistry facts: elements, reactions, periodic table, organic chemistry. Format: subject | relation | object. One per line."),
    ("EN_BIOLOGY", "List 20 biology facts: cells, DNA, evolution, genetics, human body. Format: subject | relation | object. One per line."),
    ("EN_ASTRONOMY", "List 20 astronomy facts: planets, stars, galaxies, black holes, Big Bang. Format: subject | relation | object. One per line."),
    ("EN_HISTORY", "List 20 historical facts: Ancient Rome, World Wars, Renaissance, Cold War. Format: subject | relation | object. One per line."),
    ("EN_GEOGRAPHY", "List 20 geography facts: countries, capitals, rivers, mountains, climate zones. Format: subject | relation | object. One per line."),
    ("EN_MEDICINE", "List 20 medical facts: diseases, vaccines, human anatomy, treatments. Format: subject | relation | object. One per line."),
    ("EN_TECHNOLOGY", "List 20 technology facts: AI, computers, internet, smartphones, blockchain. Format: subject | relation | object. One per line."),
    ("EN_LITERATURE", "List 20 literature facts: famous authors, books, Nobel prizes, literary movements. Format: subject | relation | object. One per line."),
    ("EN_MUSIC", "List 20 music facts: classical composers, jazz, rock, instruments, theory. Format: subject | relation | object. One per line."),
    ("EN_ECONOMICS", "List 20 economics facts: GDP, inflation, markets, trade, central banks. Format: subject | relation | object. One per line."),
    ("EN_PHILOSOPHY", "List 20 philosophy facts: Plato, Kant, ethics, existentialism, logic. Format: subject | relation | object. One per line."),
    ("EN_SPORTS", "List 20 sports facts: Olympics, football, tennis, records, athletes. Format: subject | relation | object. One per line."),
    ("EN_ART", "List 20 art facts: painting, sculpture, architecture, famous artists, movements. Format: subject | relation | object. One per line."),
    ("EN_PSYCHOLOGY", "List 20 psychology facts: cognition, behavior, emotions, mental disorders, therapy. Format: subject | relation | object. One per line."),
    ("EN_ECOLOGY", "List 20 ecology facts: ecosystems, climate change, biodiversity, conservation. Format: subject | relation | object. One per line."),
    ("EN_NEUROSCIENCE", "List 20 neuroscience facts: brain, neurons, synapses, memory, consciousness. Format: subject | relation | object. One per line."),
    ("EN_SPACE", "List 20 space exploration facts: NASA, SpaceX, Apollo, ISS, Mars. Format: subject | relation | object. One per line."),
    ("EN_MATHEMATICS", "List 20 mathematics facts: theorems, numbers, geometry, calculus, algebra. Format: subject | relation | object. One per line."),
    ("EN_FOOD", "List 20 food and cuisine facts: world cuisines, ingredients, cooking techniques. Format: subject | relation | object. One per line."),
]
