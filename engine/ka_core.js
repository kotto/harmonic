// Vital Ka — Core Diagnostic Engine (auto-extracted)
// DO NOT EDIT MANUALLY — regenerated from vital_ka.html

const DB = {
  "COVID-19":{s:["fièvre","toux_sèche","fatigue","anosmie","agueusie","essoufflement","courbatures","maux_de_tête"],g:"ÉLEVÉE",u:true,c:"Isolement immédiat. Test PCR. Consultation si essoufflement.",d:"24-48h"},
  "Grippe":{s:["fièvre","toux_grasse","courbatures","maux_de_tête","fatigue","frissons","mal_de_gorge"],g:"MODÉRÉE",u:false,c:"Repos, paracétamol, hydratation.",d:"3-5 jours"},
  "Infarctus":{s:["douleur_thoracique","essoufflement","sueurs_froides","nausées","douleur_bras_gauche","angoisse","palpitations"],g:"URGENCE VITALE",u:true,c:"Appeler le 15 IMMÉDIATEMENT.",d:"IMMÉDIAT"},
  "AVC":{s:["paralysie_visage","faiblesse_bras","trouble_parole","confusion","perte_équilibre","maux_de_tête_violents","trouble_vision"],g:"URGENCE VITALE",u:true,c:"Appeler le 15 IMMÉDIATEMENT.",d:"IMMÉDIAT"},
  "Bronchite":{s:["toux_grasse","expectorations","fièvre_modérée","fatigue","essoufflement_léger"],g:"MODÉRÉE",u:false,c:"Repos, hydratation, antitussif.",d:"5-7 jours"},
  "Pneumonie":{s:["fièvre_élevée","toux_grasse","essoufflement","douleur_thoracique","frissons","fatigue_intense","expectorations_colorées"],g:"ÉLEVÉE",u:true,c:"Consultation urgente. Radio pulmonaire. Antibiotiques.",d:"24h"},
  "Angine":{s:["mal_de_gorge_intense","fièvre","ganglions","difficulté_avaler","amygdales_rouges","absence_de_toux"],g:"MODÉRÉE",u:false,c:"Consultation. Antibiotiques si streptocoque positif.",d:"48h"},
  "Rhume":{s:["nez_bouché","éternuements","mal_de_gorge_léger","toux_légère","fatigue_légère","écoulement_nasal"],g:"FAIBLE",u:false,c:"Repos, hydratation, lavage de nez.",d:"Inutile"},
  "Gastro":{s:["diarrhée","vomissements","nausées","douleurs_abdominales","fièvre_modérée","fatigue"],g:"MODÉRÉE",u:false,c:"Réhydratation (SRO). Repas légers.",d:"48h"},
  "Appendicite":{s:["douleur_abdominale_droite","fièvre_modérée","nausées","vomissements","perte_appétit","douleur_rebond"],g:"URGENCE VITALE",u:true,c:"Appeler le 15. Risque de péritonite.",d:"IMMÉDIAT"},
  "Crise_asthme":{s:["essoufflement","sifflement_respiratoire","toux_sèche","oppression_thoracique","difficulté_parler"],g:"ÉLEVÉE",u:true,c:"Ventoline. Si pas d'amélioration: 15.",d:"IMMÉDIAT si sévère"},
  "Allergie_sévère":{s:["urticaire","gonflement_visage","démangeaisons","difficulté_respirer","nausées","chute_tension"],g:"URGENCE VITALE",u:true,c:"Adrénaline si dispo. Appeler le 15.",d:"IMMÉDIAT"},
  "Migraine":{s:["maux_de_tête_intenses","nausées","photophobie","phonophobie","aura_visuelle","fatigue"],g:"MODÉRÉE",u:false,c:"Repos dans le noir, triptans si prescrits.",d:"Si > 72h"},
  "Infection_urinaire":{s:["brûlures_urinaires","envies_fréquentes","urines_troubles","douleur_bas_ventre","fièvre_modérée"],g:"MODÉRÉE",u:false,c:"Consultation. Antibiotiques si confirmé.",d:"48-72h"},
  "Phlébite":{s:["douleur_mollet","gonflement_jambe","rougeur","chaleur_locale","douleur_pied","fièvre_modérée"],g:"ÉLEVÉE",u:true,c:"Consultation urgente. Écho-doppler. Anticoagulants.",d:"24h"},
  "Embolie_pulmonaire":{s:["essoufflement_brutal","douleur_thoracique","toux_sang","malaise","tachycardie","sueurs","angoisse"],g:"URGENCE VITALE",u:true,c:"Appeler le 15 IMMÉDIATEMENT.",d:"IMMÉDIAT"},
  "Méningite":{s:["fièvre_élevée","maux_de_tête_violents","raideur_nuque","photophobie","vomissements","confusion","taches_rouges"],g:"URGENCE VITALE",u:true,c:"Appeler le 15 IMMÉDIATEMENT.",d:"IMMÉDIAT"},
  "Dépression":{s:["tristesse_persistante","perte_intérêt","fatigue","troubles_sommeil","perte_appétit","idées_noires","isolement"],g:"ÉLEVÉE",u:false,c:"Consultation médecin ou psychiatre.",d:"1-2 semaines"},
  "Septicémie":{s:["fièvre_élevée","frissons_intenses","confusion","respiration_rapide","peau_marbree","chute_tension","fatigue_extrême"],g:"URGENCE VITALE",u:true,c:"Appeler le 15 IMMÉDIATEMENT.",d:"IMMÉDIAT"},
  "Crise_angoisse":{s:["palpitations","sueurs","tremblements","sensation_étouffement","douleur_thoracique","peur_mourir","vertiges"],g:"MODÉRÉE",u:false,c:"Respiration lente et profonde. Rassurer.",d:"Si récurrentes"},
  "Paludisme_simple":{s:["fièvre_cyclique","frissons","sueurs","maux_de_tête","nausées","fatigue_intense","douleurs_musculaires"],g:"ÉLEVÉE",u:true,c:"Test goutte épaisse + TDR. ACT 3 jours si confirmé.",d:"24h"},
  "Paludisme_grave":{s:["fièvre_élevée","confusion","convulsions","respiration_rapide","prostration","ictère","urines_foncées"],g:"URGENCE VITALE",u:true,c:"TRANSFERT URGENT HÔPITAL. Artésunate IV.",d:"IMMÉDIAT"},
  "Dengue":{s:["fièvre_élevée","maux_de_tête_intenses","douleurs_rétro_orbitaires","douleurs_articulaires","douleurs_musculaires","éruption_cutanée","nausées","fatigue"],g:"ÉLEVÉE",u:true,c:"Paracétamol UNIQUEMENT. Hydratation. Pas d'AINS.",d:"24-48h"},
  "Dengue_sévère":{s:["fièvre_élevée","choc","saignements","détresse_respiratoire","douleur_abdominale_intense","vomissements_persistants","léthargie"],g:"URGENCE VITALE",u:true,c:"HOSPITALISATION URGENTE. Réanimation.",d:"IMMÉDIAT"},
  "Chikungunya":{s:["fièvre_brutale","polyarthralgie","douleurs_articulaires_intenses","douleurs_musculaires","maux_de_tête","éruption_cutanée","fatigue"],g:"MODÉRÉE",u:false,c:"Paracétamol + AINS si dengue exclue. Repos.",d:"1-2 semaines"},
  "Choléra":{s:["diarrhée_aqueuse_profuse","vomissements","déshydratation_sévère","crampes_musculaires","oligurie","yeux_enfoncés","pli_cutané"],g:"URGENCE VITALE",u:true,c:"RÉHYDRATATION IMMÉDIATE. SRO ou Ringer Lactate IV.",d:"IMMÉDIAT"},
  "Fièvre_jaune":{s:["fièvre_brutale","frissons","ictère","hémorragies","oligurie","bradycardie","nausées"],g:"URGENCE VITALE",u:true,c:"Hospitalisation. Soins de support. Vaccination préventive.",d:"IMMÉDIAT"},
  "Zika":{s:["fièvre_modérée","éruption_cutanée","conjonctivite","douleurs_articulaires","maux_de_tête","prurit"],g:"FAIBLE",u:false,c:"Repos, paracétamol. Protection piqûres. Prudence grossesse.",d:"Si suspicion grossesse"},
  "Leptospirose":{s:["fièvre_élevée","frissons","maux_de_tête_violents","myalgies_mollets","conjonctivite","ictère","oligurie"],g:"ÉLEVÉE",u:true,c:"Hospitalisation. Pénicilline IV ou Doxycycline.",d:"IMMÉDIAT"},
  "Bilharziose":{s:["hématurie","douleurs_abdominales","diarrhée_sanglante","hépatomégalie","fatigue_chronique","anémie"],g:"MODÉRÉE",u:false,c:"Praziquantel 40mg/kg dose unique.",d:"Programmé"},
  "Trypanosomiase":{s:["chancre_inoculation","fièvre_irrégulière","céphalées","prurit_intense","troubles_sommeil","confusion","ataxie"],g:"URGENCE VITALE",u:true,c:"Ponction lombaire. Pentamidine ou Eflornithine IV.",d:"IMMÉDIAT"},
  "Leishmaniose":{s:["fièvre_prolongée","splénomégalie_massive","hépatomégalie","pancytopénie","amaigrissement","fatigue_extrême","pâleur"],g:"URGENCE VITALE",u:true,c:"Amphotéricine B liposomale IV. Hospitalisation.",d:"IMMÉDIAT"},
  "Onchocercose":{s:["prurit_intense","lésions_cutanées","nodules_sous_cutanés","troubles_vision","cécité_progressive","dépigmentation"],g:"MODÉRÉE",u:false,c:"Ivermectine 150µg/kg dose unique. Renouveler 6-12 mois.",d:"Programmé"},
  "Filariose":{s:["lymphœdème","éléphantiasis","hydrocèle","lymphangite","fièvre","frissons","douleur_ganglionnaire"],g:"MODÉRÉE",u:false,c:"Ivermectine + Albendazole. Soins locaux.",d:"Programmé"},
  "Typhoïde":{s:["fièvre_progressive","maux_de_tête","douleurs_abdominales","constipation","bradycardie_relative","splénomégalie","taches_roses","abattement"],g:"ÉLEVÉE",u:true,c:"Hémoculture. Ceftriaxone IV 7-14 jours.",d:"48h"},
  "Diabète_décompensé":{s:["soif_intense","envies_fréquentes_uriner","fatigue","vision_floue","perte_poids","haleine_fruitée","respiration_rapide"],g:"URGENCE VITALE",u:true,c:"Appeler le 15. Risque d'acidocétose.",d:"IMMÉDIAT"},
  "Palu_femme_enceinte":{s:["fièvre","frissons","fatigue_intense","maux_de_tête","nausées_accentuées","douleurs_abdominales","pâleur"],g:"URGENCE VITALE",u:true,c:"Hospitalisation. Quinine+Clindamycine (T1) ou ACT (T2-3).",d:"IMMÉDIAT"},
  "Palu_enfant":{s:["fièvre_élevée","frissons","vomissements","refus_alimentation","convulsions","respiration_rapide","léthargie"],g:"URGENCE VITALE",u:true,c:"Hospitalisation si < 5 ans. ACT pédiatrique.",d:"IMMÉDIAT"},
  "Pyélonéphrite":{s:["fièvre_élevée","frissons","douleur_lombaire","brûlures_urinaires","nausées","fatigue_intense"],g:"ÉLEVÉE",u:true,c:"Consultation urgente. Antibiotiques IV possibles.",d:"24h"},
  "Lombalgie":{s:["douleur_lombaire","raideur_dos","difficulté_mouvement","douleur_jambe","spasme_musculaire"],g:"MODÉRÉE",u:false,c:"Repos relatif, antalgiques, chaleur locale.",d:"1-2 semaines"}
};

// ═══════════════════════════════════════════════
// ENCODEUR
// ═══════════════════════════════════════════════

const F = ["douleur", "fievre", "respiratoire", "digestif", "neurologique", "cardiaque", "cutane", "musculaire", "articulaire", "ORL", "urinaire", "psychologique", "general", "tete", "thorax", "abdomen", "renale", "hematologique", "urgence_hemorragique", "urgence_hydrique", "age_0_12", "age_13_17", "age_18_40", "age_41_65", "age_66_plus", "gender_male", "gender_female", "severity_mild", "severity_moderate", "severity_severe", "severity_critical", "system_respiratory", "system_cardiovascular", "system_digestive", "system_neurological", "system_musculoskeletal", "system_dermatological", "system_urinary", "system_ENT", "system_psychological", "vital_fever", "vital_tachycardia", "vital_tachypnea", "vital_normal", "risk_elderly", "psy_mood_basse", "psy_mood_haute", "psy_pensee", "psy_perception", "psy_cognition"];

const symptomMap = {
  "fièvre":"fievre,general","fièvre_élevée":"fievre,general","fièvre_modérée":"fievre,general","fièvre_brutale":"fievre,general","fièvre_cyclique":"fievre,general","fièvre_progressive":"fievre,general","fièvre_irrégulière":"fievre,general","fièvre_prolongée":"fievre,general",
  "toux_sèche":"respiratoire,ORL","toux_grasse":"respiratoire,ORL","toux_légère":"respiratoire","toux_sang":"respiratoire,cardiaque","expectorations":"respiratoire","expectorations_colorées":"respiratoire",
  "essoufflement":"respiratoire,cardiaque","essoufflement_léger":"respiratoire","essoufflement_brutal":"respiratoire,cardiaque","respiration_rapide":"respiratoire,general","sifflement_respiratoire":"respiratoire","oppression_thoracique":"respiratoire,thorax","détresse_respiratoire":"respiratoire,cardiaque",
  "fatigue":"general","fatigue_intense":"general","fatigue_extrême":"general","fatigue_chronique":"general","fatigue_légère":"general",
  "douleur_thoracique":"douleur,thorax,cardiaque","douleur_abdominale":"douleur,abdomen,digestif","douleur_abdominale_droite":"douleur,abdomen,digestif","douleur_abdominale_intense":"douleur,abdomen,digestif","douleurs_abdominales":"douleur,abdomen,digestif","douleur_lombaire":"douleur,musculaire","douleur_bras_gauche":"douleur,cardiaque","douleur_mollet":"douleur,musculaire","douleurs_articulaires":"douleur,articulaire","douleurs_articulaires_intenses":"douleur,articulaire","douleurs_musculaires":"douleur,musculaire","douleurs_rétro_orbitaires":"tete,douleur","douleur_ganglionnaire":"douleur,general","douleur_bas_ventre":"douleur,abdomen,digestif,urinaire","douleur_pied":"douleur,articulaire","douleur_jambe":"douleur,musculaire","douleur_rebond":"douleur,abdomen,digestif",
  "maux_de_tête":"douleur,tete","maux_de_tête_violents":"douleur,tete,neurologique","maux_de_tête_intenses":"douleur,tete,neurologique","céphalées":"douleur,tete",
  "nausées":"digestif,general","nausées_accentuées":"digestif,general","vomissements":"digestif,general","vomissements_persistants":"digestif,general","diarrhée":"digestif","diarrhée_sanglante":"digestif","diarrhée_aqueuse_profuse":"digestif,general","constipation":"digestif",
  "frissons":"fievre,general","frissons_intenses":"fievre,general","sueurs":"fievre,general","sueurs_froides":"general,cardiaque",
  "anosmie":"ORL,neurologique","agueusie":"ORL,neurologique","mal_de_gorge":"douleur,ORL","mal_de_gorge_léger":"douleur,ORL","mal_de_gorge_intense":"douleur,ORL","nez_bouché":"ORL","éternuements":"ORL","écoulement_nasal":"ORL","ganglions":"ORL,general",
  "courbatures":"douleur,musculaire,general","myalgies_mollets":"musculaire,douleur","polyarthralgie":"articulaire,douleur","raideur_articulaire":"articulaire","spasme_musculaire":"musculaire,douleur","crampes_musculaires":"musculaire,douleur,general",
  "palpitations":"cardiaque","tachycardie":"cardiaque","bradycardie":"cardiaque","bradycardie_relative":"cardiaque","angoisse":"psychologique,cardiaque","chute_tension":"cardiaque,general","choc":"cardiaque,general","choc_hypovolémique":"cardiaque,general",
  "confusion":"neurologique,general","convulsions":"neurologique,general","trouble_parole":"neurologique","trouble_vision":"neurologique,tete","perte_équilibre":"neurologique","vertiges":"neurologique,general","ataxie":"neurologique","tremblements":"neurologique,general","léthargie":"neurologique,psychologique,general","prostration":"neurologique,general",
  "paralysie_visage":"neurologique,tete","faiblesse_bras":"neurologique,musculaire","photophobie":"neurologique,tete","phonophobie":"neurologique,tete",
  "éruption_cutanée":"cutane","urticaire":"cutane","prurit":"cutane","prurit_intense":"cutane","démangeaisons":"cutane","taches_roses":"cutane","taches_rouges":"cutane","peau_marbree":"cutane","rougeur":"cutane","lésions_cutanées":"cutane","dépigmentation":"cutane","nodules_sous_cutanés":"cutane","chancre_inoculation":"cutane","gonflement_visage":"cutane,tete","gonflement_jambe":"cutane,musculaire","chaleur_locale":"general","lymphœdème":"cutane,general","éléphantiasis":"cutane,general","lymphangite":"cutane,general","pli_cutané":"cutane,general",
  "ictère":"digestif,general","hémorragies":"cutane,general,urgence_hemorragique","saignements":"cutane,general,urgence_hemorragique","saignements_muqueuses":"cutane,general,urgence_hemorragique","hématurie":"urinaire,general","urines_foncées":"urinaire,general","urines_troubles":"urinaire",
  "oligurie":"urinaire,general,renale","anurie":"urinaire,general,renale","insuffisance_rénale":"urinaire,general,renale","brûlures_urinaires":"urinaire,douleur","envies_fréquentes":"urinaire","envies_fréquentes_uriner":"urinaire","hydrocèle":"urinaire,general",
  "splénomégalie":"general","splénomégalie_massive":"general","hépatomégalie":"digestif,general","amaigrissement":"general,digestif","pâleur":"cutane,general,hematologique","anémie":"general,hematologique","pancytopénie":"general,hematologique",
  "conjonctivite":"ORL,cutane","yeux_enfoncés":"general,tete","cécité_progressive":"neurologique,tete","vision_floue":"neurologique,tete",
  "tristesse_persistante":"psychologique","perte_intérêt":"psychologique","idées_noires":"psychologique","isolement":"psychologique","peur_mourir":"psychologique,cardiaque","troubles_sommeil":"psychologique,general","abattement":"general,psychologique",
  "soif_intense":"general,digestif","perte_appétit":"digestif,general","refus_alimentation":"digestif,general","haleine_fruitée":"general,digestif","perte_poids":"general,digestif",
  "raideur_nuque":"neurologique,musculaire,tete","raideur_dos":"musculaire","difficulté_mouvement":"musculaire,articulaire","difficulté_avaler":"ORL","difficulté_parler":"neurologique","difficulté_respirer":"respiratoire,cardiaque","sensation_étouffement":"respiratoire,psychologique",
  "amygdales_rouges":"ORL","absence_de_toux":"ORL","malaise":"general,cardiaque","déshydratation_sévère":"general,digestif,urgence_hydrique","aura_visuelle":"neurologique,tete",
  // ── Compléments : tokens JSON orphelins (couverture 100% des fichiers standard) ──
  "anémie_sévère":"general,hematologique","adénopathies":"ORL,general","douleur_thoracique_légère":"douleur,thorax,cardiaque","douleurs_miction":"urinaire,douleur","geignement":"neurologique,ORL","hypotonie":"neurologique,musculaire","lymphadénopathie":"ORL,general","myalgie":"douleur,musculaire","troubles_vision":"neurologique,tete","œdème_membre":"cutane,musculaire","constipation_ou_diarrhée":"digestif",

  // ══════════════════════════════════════════════════════════════════════════
  // EXTENSION — tokenisation des 8 fichiers "conditions" (NTD, VIH/TB, pédiatrie,
  // urgences, santé mentale, chroniques, mère-enfant, malnutrition).
  // Chaque token mappe vers des features ∈ F (validé par test_tokenization).
  // ══════════════════════════════════════════════════════════════════════════

  // ── Psychiatrique — humeur/élan vital (dims psy_mood_*) ──
  "humeur_dépressive":"psy_mood_basse,psychologique","tristesse":"psy_mood_basse,psychologique","mélancolie":"psy_mood_basse,psychologique","désespoir":"psy_mood_basse,psychologique","anhédonie":"psy_mood_basse,psychologique","culpabilisation":"psy_mood_basse,psychologique","sentiment_culpabilité":"psy_mood_basse,psychologique","perte_plaisir":"psy_mood_basse,psychologique","pensées_mort":"psy_mood_basse,psychologique","idées_suicidaires":"psy_mood_basse,psychologique","antécédent_suicide":"psy_mood_basse,psychologique","plan_suicide":"psy_mood_basse,psychologique","don_biens":"psy_mood_basse,psychologique","manie":"psy_mood_haute,psychologique","humeur_élevée":"psy_mood_haute,psychologique","euphorie":"psy_mood_haute,psychologique","énergie_accrue":"psy_mood_haute,psychologique","fuite_idées":"psy_mood_haute,psychologique","distractibilité":"psy_mood_haute,psychologique","dépenses_excessives":"psy_mood_haute,psychologique","hypersexualité":"psy_mood_haute,psychologique","idées_grandeur":"psy_mood_haute,psychologique","logorrhée":"psy_mood_haute,psychologique",

  // ── Psychiatrique — pensée / perception / cognition ──
  "hallucinations":"psy_perception,neurologique","hallucinations_auditives":"psy_perception,neurologique","délires":"psy_pensee,neurologique","désorganisation_pensée":"psy_pensee,neurologique","comportement_bizarre":"psy_pensee,psychologique","retrait_social":"psy_pensee,psychologique","apragmatisme":"psy_pensee,psychologique","émoussement_affectif":"psy_pensee,psychologique","cauchemars":"psy_perception,psychologique","flashbacks":"psy_perception,psychologique","souvenirs_intrusifs":"psy_perception,psychologique","évitements":"psy_pensee,psychologique","hypervigilance":"psy_pensee,psychologique","sursauts":"psy_pensee,psychologique","détachement":"psy_pensee,psychologique","anesthésie_émotionnelle":"psy_pensee,psychologique","insomnie":"psychologique,general","insomnie_sévère":"psychologique,general","irritabilité":"psychologique,general","tension_musculaire":"musculaire,psychologique","baisse_concentration":"psy_cognition,psychologique","difficulté_concentration":"psy_cognition,psychologique","soucis_incontrôlables":"psy_pensee,psychologique","troubles_appétit":"digestif,psychologique","ralentissement_psychomoteur":"musculaire,psy_mood_basse","troubles_mémoire":"psy_cognition,neurologique","troubles_mémoire_récente":"psy_cognition,neurologique","désorientation":"psy_cognition,neurologique","désorientation_temporo_spatiale":"psy_cognition,neurologique","apraxie":"psy_cognition,neurologique","agnosie":"psy_cognition,neurologique","troubles_fonctions_exécutives":"psy_cognition,neurologique","changement_personnalité":"psy_pensee,psychologique","troubles_comportement":"psy_pensee,psychologique","perte_connaissance":"neurologique,general","suspension_conscience":"neurologique,psy_cognition","angoisse_anticipatoire":"psychologique,cardiaque",

  // ── Cardiovasculaire / métabolique ──
  "hypotension":"cardiaque,general","hypertension":"cardiaque","turgescence_jugulaire":"cardiaque","orthopnée":"respiratoire,cardiaque","crépitants_pulmonaires":"respiratoire,cardiaque","ralentissement_débit":"cardiaque","polyurie":"urinaire,general","polydipsie":"general,digestif","polyphagie":"digestif,general","cicatrisation_lente":"cutane,general","infections_récidivantes":"general","pica":"digestif,general","koïlonychie":"cutane,hematologique","goitre":"cutane,tete","crétinisme":"psy_cognition,neurologique","héméralopie":"neurologique,tete","taches_bitot":"ORL,cutane","xérophtalmie":"ORL,cutane","kératomalacie":"ORL,cutane","hypertension_intracrânienne":"neurologique,tete",

  // ── Neurologique ──
  "coma":"neurologique,general","épilepsie":"neurologique","convulsions_tonico_cloniques":"neurologique,general","morsure_langue":"neurologique,digestif","perte_urine":"urinaire,neurologique","somnolence":"neurologique,general","paresthésies":"neurologique,cutane","hydrophobie":"psychologique,digestif","aérophobie":"psychologique,respiratoire","paralysie_ascendante":"neurologique,musculaire","agressivité":"psy_pensee,psychologique","hypertonie":"neurologique,musculaire","fontanelle_bombée":"neurologique,tete","asymétrie_pupillaire":"neurologique,tete","saignement_lcr":"neurologique,cutane,urgence_hemorragique","écoulement_lcr":"neurologique,ORL","troubles_langage":"neurologique,ORL","perte_équilibre":"neurologique","détresse_respiratoire":"respiratoire,cardiaque","apnée":"respiratoire,neurologique","cyanose":"respiratoire,cutane,cardiaque","tirage":"respiratoire","stridor":"respiratoire,ORL","hypothermie":"general","hypertérmie":"fievre,general",

  // ── Cutané tropical (NTD, dermatoses) ──
  "tache_hypopigmentée":"cutane","tache_hypoesthésique":"cutane,neurologique","ulcérations_trophiques":"cutane","sillons_scabieux":"cutane","vésicules":"cutane","papules":"cutane","lésions_grattage":"cutane","atteinte_génitale":"cutane,urinaire","fistules":"cutane","grains_noirs":"cutane","déformation":"musculaire,cutane","extension_osseuse":"musculaire,cutane","œdèmes_bilatéraux":"cutane,general","dermatose_desquamante":"cutane","dermatose":"cutane","cheveux_décolorés":"cutane","cheveux_cassants":"cutane","hépatomégalie":"digestif,general","grosse_rate":"general","pannus_cornéen":"ORL,tete","trichiasis":"ORL,tete","opacité_cornéenne":"ORL,tete,neurologique","papilles_hypertrophiques":"ORL","coryza":"ORL","énanthème_koplik":"ORL,cutane","exanthème_maculopapuleux":"cutane","exanthème":"cutane","tache_cutanée":"cutane","dermatose_peau":"cutane",

  // ── Digestif / gynéco / rénal ──
  "dysenterie":"digestif,hematologique","selles_sanglantes":"digestif,urgence_hemorragique","selles_décolorées":"digestif","douleur_hypocondre_droit":"douleur,digestif","douleur_épigastrique":"douleur,abdomen,digestif","polyphagie":"digestif,general","dyspareunie":"urinaire,douleur","pertes_vaginales":"urinaire","prurit_vulvaire":"cutane,urinaire","odeur_poisson":"urinaire","écoulement_urétral":"urinaire","prurit_urétral":"urinaire","ulcération_génitale":"cutane,urinaire,urgence_hemorragique","adénopathie_inguinale":"ORL,general","protéinurie":"urinaire,renale","œdème_visage":"cutane,tete","douleur_mamelon":"douleur,cutane","crevasses":"cutane","sein_rouge":"cutane","vermifuge":"digestif","occlusion":"digestif,abdomen","ver_selles":"digestif","kystes_larvaires":"cutane,neurologique","pancytopénie":"general,hematologique",

  // ── Urgences / traumatologie ──
  "pas_de_réponse":"neurologique,general","pas_respiration":"respiratoire,neurologique","gasps":"respiratoire,neurologique","pas_pouls":"cardiaque,general","attrape_gorge":"respiratoire","incapacité_parler":"ORL,respiratoire","incapacité_tousser":"respiratoire","fréalité":"general","temps_recoloration":"cardiaque","déformation":"musculaire","impotence_fonctionnelle":"musculaire","crépitus":"musculaire","lésion_cutanée":"cutane","douleur_locale":"douleur","œdème_progressif":"cutane","troubles_coagulation":"hematologique,general","myalgie_venin":"musculaire,douleur","plaie_pénétrante":"cutane,urgence_hemorragique","perte_conscience":"neurologique,general","coma":"neurologique,general","hypotension_anaphylaxie":"cardiaque,general","obésité":"general","plaque_rouge":"cutane","douleur_osseuse":"douleur,musculaire","splénomégalie":"general","prostration":"neurologique,general","léthargie":"neurologique,psychologique,general",

  // ── Pédiatrie / infectieux ──
  "refus_téter":"digestif,general","refus_aliment":"digestif,general","boit_avidement":"digestif,general","agité":"psychologique,general","irritable":"psychologique,general","fonte_musculaire":"musculaire,general","apathie":"psychologique,general","hypoesthésie":"neurologique,cutane","anesthésie":"neurologique,cutane","épaississement_nerveux":"neurologique","paralysie_griffe":"neurologique,musculaire","foot_drop":"neurologique,musculaire","anneaux_selles":"digestif","candidose_orale":"ORL","zona_étendu":"cutane,neurologique","herpès_chronique":"cutane","pneumocystose":"respiratoire","asthénie":"general","sueurs_nocturnes":"general,fievre","candidose":"ORL,cutane","leucoplasie_chevelue":"cutane,ORL","fièvre_prolongée":"fievre,general","bronchectasie":"respiratoire","sous_pièce":"general",
  "otalgie":"ORL,douleur","otalgie_douleur":"douleur,ORL","anorexie":"digestif,general",

  // ══════════════════════════════════════════════════════════════════════════
  // EFFETS THÉRAPEUTIQUES — pour l'encodage harmonique des plantes
  // (résonance patient↔plante via cosineSim dans l'espace F)
  // ══════════════════════════════════════════════════════════════════════════
  "antipyrétique":"fievre,general","anti_inflammatoire":"douleur,general","antalgique":"douleur",
  "antipaludique":"fievre,general","antibactérien":"general,digestif","antiviral":"general,ORL",
  "antifongique":"cutane","antispasmodique":"musculaire,douleur","diurétique":"urinaire,renale",
  "hépatoprotecteur":"digestif,general","immunostimulant":"general","antioxydant":"general",
  "cicatrisant":"cutane,general","vermifuge":"digestif","laxatif":"digestif",
  "antidiarrhéique":"digestif","antihypertenseur":"cardiaque,general",
  "hypoglycémiant":"digestif,general","antianémique":"hematologique,general",
  "sédatif":"psychologique,neurologique","anxiolytique":"psychologique",
  "antidépresseur":"psychologique,psy_mood_basse","anticonvulsivant":"neurologique",
  "expectorant":"respiratoire","antitussif":"respiratoire,ORL",
  "antiulcéreux":"digestif","émollient":"cutane","galactogène":"general",
  "emménagogue":"urinaire","antiseptique":"cutane,general",
  "hémostatique":"urgence_hemorragique","bronchodilatateur":"respiratoire",
  "antiémétique":"digestif","antiprurigineux":"cutane",
  "décongestionnant":"ORL,respiratoire","vasodilatateur":"cardiaque",
  "rubéfiant":"musculaire,douleur","astringent":"digestif,cutane",
  "tonique":"general","dépuratif":"digestif,renale","cholérétique":"digestif",
  "antihémorragique":"urgence_hemorragique","cicatrisant_os":"musculaire,articulaire",
  "orexigène":"digestif","purgatif":"digestif","sudorifique":"fievre,cutane",
  "calmant":"psychologique,neurologique","hypotenseur":"cardiaque",
  "cardiotonique":"cardiaque","antirhumatismal":"articulaire,douleur",
  "vulnéraire":"cutane","antiarthritique":"articulaire,douleur","anthelminthique":"digestif"
};

function encodeSympt(text){
  var words=text.toLowerCase().replace(/[,;.!?]/g,' ').split(/\s+/).filter(function(w){return w.length>1});
  var vec={};
  for(var i=0;i<words.length;i++){
    var w=words[i];
    var feats=symptomMap[w];
    if(feats){var fl=feats.split(',');for(var j=0;j<fl.length;j++){var f=fl[j];if(F.indexOf(f)>=0)vec[f]=(vec[f]||0)+1}}
  }
  var age=parseInt(document.getElementById('patientAge')?.value)||0;
  var gender=document.getElementById('patientGender')?.value||'';
  if(age>0){if(age<=12)vec['age_0_12']=1;else if(age<=17)vec['age_13_17']=1;else if(age<=40)vec['age_18_40']=1;else if(age<=65)vec['age_41_65']=1;else vec['age_66_plus']=1;if(age>50)vec['risk_elderly']=1;}
  if(gender==='homme')vec['gender_male']=1;else if(gender==='femme')vec['gender_female']=1;
  var count=0;for(var k in vec)if(vec[k]>0)count++;if(count<=4)vec['severity_mild']=1;else if(count<=8)vec['severity_moderate']=1;else vec['severity_severe']=1;
  var txt=text.toLowerCase();
  if(/toux|essoufflement|respir|sifflement/.test(txt))vec['system_respiratory']=1;
  if(/douleur_thoracique|palpitations|cardiaque|tachycardie/.test(txt))vec['system_cardiovascular']=1;
  if(/diarrhee|vomissements|nausees|abdominal|digestif/.test(txt))vec['system_digestive']=1;
  if(/confusion|convulsions|paralysie|tete|neurologique/.test(txt))vec['system_neurological']=1;
  if(/muscul|articul|courbature|lombaire/.test(txt))vec['system_musculoskeletal']=1;
  if(/eruption|cutanee|demangeaison|urticaire|peau/.test(txt))vec['system_dermatological']=1;
  if(/urine|urinaires|miction/.test(txt))vec['system_urinary']=1;
  if(/gorge|nez|eternuement|ORL|bouche/.test(txt))vec['system_ENT']=1;
  if(/tristesse|angoisse|peur|idees_noires|isolement/.test(txt))vec['system_psychological']=1;
  if(/fievre/.test(txt))vec['vital_fever']=1;
  if(/tachycardie|palpitations/.test(txt))vec['vital_tachycardia']=1;
  if(/essoufflement|respiration_rapide/.test(txt))vec['vital_tachypnea']=1;
  if(!/fievre|tachycardie|essoufflement/.test(txt))vec['vital_normal']=1;
  return vec;
}
function cosineSim(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (const k of F) { const va = a[k] || 0, vb = b[k] || 0; dot += va * vb; na += va * va; nb += vb * vb; }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-10);
}

// ═══════════════════════════════════════════════
// CHARGEUR ASYNCHRONE — fusionne les JSON de pathologies par-dessus DB dur
// DB dur reste la sécurité offline (si fetch échoue, le diagnostic fonctionne).
// ═══════════════════════════════════════════════
let _merged = null;           // base fusionnée (DB dur + JSON)
let _vectors = {};            // vecteurs maladie précalculés : { nomPathologie: vec }
let _loadingPromise = null;   // idempotence

// Normalise une clé de nom de pathologie (PB → PB, accents conservés mais trim/underscores)
function _normName(n) { return String(n || '').trim(); }

// Normalise la gravité (JSON "URGENCE_VITALE" → DB "URGENCE VITALE")
function _normGravite(g) {
  if (!g) return 'MODÉRÉE';
  return String(g).replace(/_/g, ' ').trim();
}

// Convertit une entrée JSON (schéma symptomes/gravite/urgence/conduite/delai_consultation
// OU schéma "conditions" avec tokens/urgence/conduite) vers le schéma DB canonique (s/g/u/c/d).
// Champs riches (traitement, signes_alarme...) conservés pour l'affichage détaillé.
function _adaptEntry(raw, key) {
  // Symptômes : tokens (conditions, prioritaire) || symptomes (fichiers standard) || []
  const s = Array.isArray(raw.tokens) ? raw.tokens : (Array.isArray(raw.symptomes) ? raw.symptomes : []);

  // Gravité : gravite (normalisé) OU dérivé de urgence boolean (conditions)
  let g = _normGravite(raw.gravite || '');
  if ((!g || g === 'MODÉRÉE') && raw.urgence === true) g = 'URGENCE VITALE';

  const adapted = {
    s: s,
    g: g,
    u: !!raw.urgence,
    c: raw.conduite || '',
    d: raw.delai_consultation || raw.delai || (raw.urgence ? 'IMMÉDIAT' : 'Programmé')
  };
  // Champs riches optionnels (pour l'IA/explication, sans impact sur le scoring)
  if (raw.traitement) adapted.traitement = raw.traitement;
  if (raw.signes_alarme) adapted.signes_alarme = raw.signes_alarme;
  if (raw.signes_gravite) adapted.signes_gravite = raw.signes_gravite;
  if (raw.seuils) adapted.seuils = raw.seuils;
  if (raw.module) adapted.module = raw.module;
  if (raw.nom) adapted.nom = raw.nom;
  return adapted;
}

// Construit la base fusionnée depuis les JSON, par-dessus DB dur.
// DB dur est prioritaire en cas de conflit de nom (préserve les références
// existantes dans vital_ka_ai.js SPECIALTIES.diseases[]).
//
// ALIAS : certains JSON utilisent des noms différents pour la même pathologie
// que le DB dur canonique (ex: "Grippe_saisonnière" vs "Grippe", "Paludisme"
// en doublon de "Paludisme_simple"). On mappe ces doublons vers le nom DB dur,
// et on ignore l'entrée JSON si le canonique existe déjà (évite les doublons
// qui pollueraient le top-5 avec deux fois la même maladie).
const _NAME_ALIASES = {
  'Paludisme': 'Paludisme_simple',
  'Grippe_saisonnière': 'Grippe',
  'Infarctus_du_myocarde': 'Infarctus',
  'Bronchite_aiguë': 'Bronchite',
  'Angine_bactérienne': 'Angine',
  'Gastro_entérite': 'Gastro',
  'Crise_dasthme': 'Crise_asthme',
  'Crise_dangoisse': 'Crise_angoisse',
  'Dépression_majeure': 'Dépression',
  'Fièvre_typhoïde': 'Typhoïde',
  'Leishmaniose_viscérale': 'Leishmaniose',
  'Filariose_lymphatique': 'Filariose',
  'Lombalgie_aiguë': 'Lombalgie',
  'Paludisme_femme_enceinte': 'Palu_femme_enceinte',
  'Paludisme_enfant': 'Palu_enfant'
};

function _buildMerged(jsonSources) {
  const merged = {};
  // 1. D'abord les entrées JSON (seront écrasées par DB dur si conflit)
  for (const src of jsonSources) {
    if (!src) continue;
    const coll = src.pathologies || src.maladies || src.conditions || {};
    for (const [key, raw] of Object.entries(coll)) {
      let name = _normName(key);
      // Résolution d'alias : doublon JSON → nom DB canonique
      name = _NAME_ALIASES[name] || name;
      if (name && !merged[name]) merged[name] = _adaptEntry(raw, key);
    }
  }
  // 2. Puis DB dur par-dessus (prioritaire)
  for (const [name, d] of Object.entries(DB)) merged[name] = d;
  return merged;
}

// Précalcule les vecteurs maladie (évite encodeSympt à chaque diagnose — et évite
// la lecture DOM inutile sur le vecteur maladie, qui ne contient pas âge/genre).
function _precomputeVectors(db) {
  const v = {};
  for (const [name, d] of Object.entries(db)) {
    if (d && Array.isArray(d.s)) v[name] = encodeSympt(d.s.join(' '));
  }
  return v;
}

// Charge les JSON et construit la base fusionnée. Échec fetch → DB dur seul (offline OK).
async function loadDB() {
  const jsonSources = [];
  const files = [
    'data/vital_ka_diseases.json', 'data/vital_ka_malaria.json', 'data/vital_ka_tropical.json',
    // Conditions tokenisées (NTD, VIH/TB, pédiatrie, urgences, santé mentale,
    // chroniques, mère-enfant, malnutrition) — lues pour le scoring si tokens présents.
    'data/vital_ka_ntd.json', 'data/vital_ka_vih_tb.json', 'data/vital_ka_pediatrie.json',
    'data/vital_ka_urgences.json', 'data/vital_ka_sante_mentale.json', 'data/vital_ka_chroniques.json',
    'data/vital_ka_mere_enfant.json', 'data/vital_ka_malnutrition.json'
  ];
  const results = await Promise.allSettled(
    files.map(f => fetch(f).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }))
  );
  results.forEach((res, i) => {
    if (res.status === 'fulfilled') jsonSources.push(res.value);
    else console.warn('[KA Core] Base non chargée:', files[i], res.reason);
  });
  _merged = _buildMerged(jsonSources);
  _vectors = _precomputeVectors(_merged);
  return _merged;
}

// Idempotent : charge une seule fois, met en cache la promesse.
async function ensureDB() {
  if (_merged) return _merged;
  if (!_loadingPromise) _loadingPromise = loadDB();
  return _loadingPromise;
}

// Retourne la base fusionnée si chargée, sinon DB dur (fallback synchrone).
function getDB() {
  return _merged || DB;
}

// Retourne le vecteur précalculé d'une pathologie (ou encode à la volée si absent).
function getVector(name) {
  if (_vectors[name]) return _vectors[name];
  const d = getDB()[name];
  return d ? encodeSympt(d.s.join(' ')) : {};
}

// Nombre de pathologies diagnosables (pour affichage/telemetry).
function dbSize() {
  return Object.keys(getDB()).length;
}

// ═══════════════════════════════════════════════
// MOTEUR DE RÈGLES DE SEUILS
// Évalue les règles déclaratives (champ "seuils" des conditions JSON)
// et retourne un score [0..1] par condition quand les seuils sont atteints.
// Les règles ne remplacent pas le scoring vectoriel — elles le complètent
// (le score final = max(cosine, ruleScore)).
// ═══════════════════════════════════════════════

// Lit les inputs cliniques du DOM (MUAC, FR, température, TA, etc.)
// Retourne un objet patientData pour evaluateRules.
function readPatientData(symptomTokens) {
  const d = {
    age: parseInt(document.getElementById('patientAge')?.value) || 0,
    gender: (document.getElementById('patientGender')?.value || '').toLowerCase(),
    symptoms: symptomTokens || [],
    // Signes vitaux (optionnels — absents = undefined, la règle ignore le test)
    muac: parseFloat(document.getElementById('vitalMuac')?.value) || undefined,
    fr: parseFloat(document.getElementById('vitalFR')?.value) || undefined,
    temp: parseFloat(document.getElementById('vitalTemp')?.value) || undefined,
    ta_syst: parseFloat(document.getElementById('vitalTASyst')?.value) || undefined,
    ta_diast: parseFloat(document.getElementById('vitalTADiast')?.value) || undefined,
    poids: parseFloat(document.getElementById('vitalPoids')?.value) || undefined,
    surface_pct: parseFloat(document.getElementById('vitalSurface')?.value) || undefined,
    // Dérivés
    age_months: undefined, // calculé si age ≤ 5 ans (0-60 mois)
    age_jours: undefined   // calculé si age = 0 (< 1 an, en jours approximatif)
  };
  if (d.age <= 5) d.age_months = d.age * 12; // approximation (devrait être l'âge réel en mois)
  if (d.age === 0) d.age_jours = 7; // approximation nouveau-né
  return d;
}

// Évalue une règle unique. Retourne true si tous les critères matchent,
// MAIS exige qu'au moins un critère soit effectivement testé (non-skippé).
function _matchRule(rule, pt, mergedDB) {
  let tested = false;
  // Test de champ numérique
  if (rule.field && pt[rule.field] !== undefined) {
    tested = true;
    const val = pt[rule.field];
    const rv = rule.value;
    let ok = false;
    if (rule.op === 'lt') ok = val < rv;
    else if (rule.op === 'lte') ok = val <= rv;
    else if (rule.op === 'gt') ok = val > rv;
    else if (rule.op === 'gte') ok = val >= rv;
    else if (rule.op === 'eq') ok = val === rv;
    else if (rule.op === 'between') ok = Array.isArray(rv) && val >= rv[0] && val <= rv[1];
    else ok = true;
    if (!ok) return false;
  }
  // Test d'âge (mois) — requis si la règle le spécifie
  if (rule.age_range) {
    tested = true;
    if (pt.age_months === undefined) return false;
    if (pt.age_months < rule.age_range[0] || pt.age_months > rule.age_range[1]) return false;
  }
  // Test de symptômes (tous doivent être présents dans le vecteur patient)
  if (rule.symptoms && rule.symptoms.length) {
    tested = true;
    for (const s of rule.symptoms) {
      if (!pt.symptoms.includes(s)) return false;
    }
  }
  // Refuse les règles qui ne testent rien (vacuously true → faux positifs)
  return tested;
}

// Évalue les règles de seuils pour toutes les conditions de la base.
// Retourne un objet { conditionName: ruleScore }.
function evaluateRules(patientData, mergedDB) {
  const db = mergedDB || getDB();
  const scores = {};
  for (const [name, d] of Object.entries(db)) {
    const seuils = d.seuils;
    if (!seuils || !Array.isArray(seuils.rules)) continue;
    const logic = seuils.logic || 'any';
    let bestScore = 0;
    let allMatch = true, anyMatch = false;
    for (const rule of seuils.rules) {
      const matched = _matchRule(rule, patientData, db);
      if (matched) {
        anyMatch = true;
        if ((rule.score || 0) > bestScore) bestScore = rule.score;
      } else {
        allMatch = false;
      }
    }
    const triggered = (logic === 'any') ? anyMatch : allMatch;
    if (triggered && bestScore > 0) scores[name] = bestScore;
  }
  return scores;
}
