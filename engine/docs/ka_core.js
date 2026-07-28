// KA Care — Core Diagnostic Engine (auto-extracted)
// DO NOT EDIT MANUALLY — regenerated from ka_care.html

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

const F = ["douleur", "fievre", "respiratoire", "digestif", "neurologique", "cardiaque", "cutane", "musculaire", "articulaire", "ORL", "urinaire", "psychologique", "general", "tete", "thorax", "abdomen", "renale", "hematologique", "urgence_hemorragique", "urgence_hydrique", "age_0_12", "age_13_17", "age_18_40", "age_41_65", "age_66_plus", "gender_male", "gender_female", "severity_mild", "severity_moderate", "severity_severe", "severity_critical", "system_respiratory", "system_cardiovascular", "system_digestive", "system_neurological", "system_musculoskeletal", "system_dermatological", "system_urinary", "system_ENT", "system_psychological", "vital_fever", "vital_tachycardia", "vital_tachypnea", "vital_normal", "risk_elderly"];

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
  "amygdales_rouges":"ORL","absence_de_toux":"ORL","malaise":"general,cardiaque","déshydratation_sévère":"general,digestif,urgence_hydrique","aura_visuelle":"neurologique,tete"
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
