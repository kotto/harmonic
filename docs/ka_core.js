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

// ═══════════════════════════════════════════════
// DIAGNOSTIC
// ═══════════════════════════════════════════════
function diagnose() {
  const text = document.getElementById('symptoms').value.trim();
  if (!text) return;
  
  const btn = document.getElementById('diagnoseBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Analyse en cours...';
  
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '<div class="card"><div class="loading"><div class="spinner"></div><p>Analyse des symptômes...</p></div></div>';
  resultsDiv.style.display = 'block';
  
  setTimeout(() => {
    const patientVec = encodeSymptoms(text);
    const scores = [];
    
    for (const [name, data] of Object.entries(DB)) {
      const diseaseVec = encodeSymptoms(data.s.join(' '));
      const score = cosineSim(patientVec, diseaseVec);
      scores.push({ name, score, ...data });
    }
    
    scores.sort((a, b) => b.score - a.score);
    
    const top = scores[0];
    const hasUrgent = scores.some(s => s.u && s.score > 0.5);
    
    let html = '<div class="card">';
    
    if (top.u && top.score > 0.5) {
      html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px"><span class="badge-urgent">🚨 URGENCE VITALE</span><span style="font-weight:700;color:var(--urgent)">' + top.name + '</span></div>';
    }
    
    html += '<h2>📊 Résultats du diagnostic</h2>';
    html += '<p style="color:var(--muted);font-size:0.85em;margin-bottom:12px">Basé sur ' + Object.keys(DB).length + ' pathologies — analyse par résonance harmonique</p>';
    
    for (const r of scores.slice(0, 5)) {
      const conf = r.score > 0.8 ? 'high' : r.score > 0.5 ? 'medium' : 'low';
      const confLabel = r.score > 0.8 ? 'Très élevée' : r.score > 0.5 ? 'Élevée' : r.score > 0.3 ? 'Modérée' : 'Faible';
      const urgencyClass = (r.u && r.score > 0.5) ? ' urgent' : '';
      
      html += '<div class="result-item' + urgencyClass + '">';
      html += '<div class="maladie-name">';
      if (r.u && r.score > 0.5) html += '<span style="font-size:1.2em">🚨</span>';
      html += r.name + ' <span style="font-weight:400;color:var(--muted);font-size:0.8em">(' + confLabel + ')</span>';
      html += '<button class="why-btn" onclick="event.stopPropagation();explainDiagnosis(\'' + r.name + '\',' + r.score + ',\'' + (r.s||[]).join(',') + '\')">🔍 Pourquoi ?</button>';
      html += '</div>';
      
      html += '<div class="confidence-bar"><div class="confidence-fill ' + conf + '" style="width:' + Math.round(r.score * 100) + '%"></div></div>';
      html += '<div class="result-meta">';
      html += '<span>🎯 ' + (r.score * 100).toFixed(1) + '%</span>';
      html += '<span>⚡ ' + r.g + '</span>';
      html += '<span>⏱ ' + r.d + '</span>';
      html += '</div>';
      html += '<div class="result-conduite' + urgencyClass + '">▶ ' + r.c + '</div>';
      html += '</div>';
    }
    
    html += '<p style="color:var(--muted);font-size:0.78em;margin-top:12px;text-align:center">Ce dispositif est une <strong>aide au diagnostic</strong>. Il ne remplace pas un médecin.<br>En cas d\'urgence, appelez le <strong>15</strong> (SAMU).</p>';
    html += '</div>';
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    btn.disabled = false;
    btn.textContent = '🔍 Nouveau diagnostic';
    
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
  }, 150);
}

// ═══════════════════════════════════════════════
// QUICK SYMPTOMS
// ═══════════════════════════════════════════════
const quickSymptoms = [
  'fièvre','toux','fatigue','maux de tête','douleur thoracique',
  'essoufflement','nausées','diarrhée','frissons','courbatures',
  'mal de gorge','éruption cutanée','vertiges','confusion','vomissements'
];

const qsDiv = document.getElementById('quickSymptoms');
quickSymptoms.forEach(s => {
  const btn = document.createElement('button');
  btn.textContent = s;
  btn.onclick = function() {
    this.classList.toggle('selected');
    const ta = document.getElementById('symptoms');
    const current = ta.value.split(',').map(x => x.trim()).filter(x => x);
    if (this.classList.contains('selected')) {
      if (!current.includes(s)) current.push(s);
    } else {
      const idx = current.indexOf(s);
      if (idx >= 0) current.splice(idx, 1);
    }
    ta.value = current.join(', ');
  };
  qsDiv.appendChild(btn);
});

// Démos rapides
const demoTexts = {
  'COVID-like': 'fièvre, toux sèche, fatigue, perte d odorat, courbatures',
  'Infarctus': 'douleur thoracique, essoufflement, sueurs froides, nausées, douleur bras gauche',
  'Rhume': 'nez bouché, éternuements, mal de gorge léger, fatigue légère',
  'Gastro': 'diarrhée, vomissements, nausées, douleurs abdominales',
  'AVC': 'paralysie visage, trouble parole, perte équilibre, confusion',
  'Paludisme': 'fièvre cyclique, frissons, sueurs, maux de tête, fatigue intense',
  'Dengue': 'fièvre élevée, douleurs rétro orbitaires, douleurs articulaires, éruption cutanée',
  'Choléra': 'diarrhée aqueuse profuse, vomissements, déshydratation sévère, crampes musculaires'
};

// Ajouter les boutons de démo sous le textarea
const demoDiv = document.createElement('div');
demoDiv.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;';
Object.entries(demoTexts).forEach(([name, text]) => {
  const b = document.createElement('button');
  b.textContent = name;
  b.style.cssText = 'padding:5px 10px;border-radius:14px;font-size:0.75em;cursor:pointer;border:1px solid #3a3a3a;background:#1a1a1a;color:#999;font-family:inherit;';
  b.onclick = () => { document.getElementById('symptoms').value = text; diagnose(); };
  demoDiv.appendChild(b);
});
document.querySelector('.input-group').after(demoDiv);

// ═══════════════════════════════════════════════
// MODAL D'EXPLICATION
// ═══════════════════════════════════════════════
function closeModal() {
  document.getElementById('modalOverlay').classList.remove('active');
}

function explainDiagnosis(name, score, diseaseSympts) {
  const patientText = document.getElementById('symptoms').value.trim();
  const patientWords = patientText.toLowerCase().replace(/[,;.!?]/g,' ').split(/\s+/).filter(w=>w.length>1);
  const diseaseWords = diseaseSympts.split(',');
  
  const matched = []; const missed = [];
  for (const ds of diseaseWords) {
    const dw = ds.trim().replace(/_/g, ' ');
    let found = false;
    for (const pw of patientWords) {
      if (dw.includes(pw) || pw.includes(dw) || (symptomMap[pw] && diseaseSympts.includes(pw))) {
        matched.push(dw); found = true; break;
      }
    }
    if (!found) missed.push(dw);
  }
  
  const pct = (score * 100).toFixed(1);
  const confLabel = score > 0.8 ? 'Très élevée' : score > 0.5 ? 'Élevée' : score > 0.3 ? 'Modérée' : 'Faible';
  
  const pVec = encodeSymptoms(patientText);
  const dVec = encodeSymptoms(diseaseSympts);
  const common = [];
  for (const f of F) { if ((pVec[f]||0) > 0 && (dVec[f]||0) > 0) common.push(f); }
  
  let html = '<button class="close-btn" onclick="closeModal()">✕</button>';
  html += '<h2>🔍 ' + name + '</h2>';
  html += '<p style="color:var(--muted);margin-bottom:16px">Score : <strong style="color:var(--accent)">' + pct + '%</strong> — ' + confLabel + '</p>';
  
  if (common.length > 0) {
    html += '<p style="font-size:0.85em;margin-bottom:12px"><strong style="color:#6fcf97">Features activées en commun :</strong><br>' + common.map(f => '<code style="background:#2a2a2a;padding:2px 6px;border-radius:3px;color:#d4a853;margin:2px">' + f + '</code>').join(' ') + '</p>';
  }
  
  html += '<div class="match-grid">';
  html += '<div><strong style="color:#6fcf97">✅ Présents (' + matched.length + ')</strong>';
  for (const m of matched) html += '<div class="match-item">✓ ' + m + '</div>';
  html += '</div><div><strong style="color:#e08585">❌ Absents (' + missed.length + ')</strong>';
  for (const m of missed) html += '<div class="match-item miss">✗ ' + m + '</div>';
  html += '</div></div>';
  
  html += '<p class="explain-text"><strong style="color:var(--accent)">Interprétation :</strong> ';
  if (score > 0.8) html += 'Très forte résonance. Diagnostic à considérer en priorité.';
  else if (score > 0.5) html += 'Bonne résonance mais certains signes clés sont absents. À confirmer.';
  else html += 'Résonance modérée. Peu probable mais ne peut être exclue.';
  html += '</p>';
  
  document.getElementById('modalContent').innerHTML = html;
  document.getElementById('modalOverlay').classList.add('active');
}

function showScreen(name){
document.querySelectorAll('.screen').forEach(function(s){s.classList.remove('active')});
var el=document.getElementById('screen-'+name);
if(el)el.classList.add('active');
document.getElementById('bottomNav').style.display=(name==='splash')?'none':'flex';
document.querySelectorAll('.nav-item').forEach(function(n){n.classList.toggle('active',n.dataset.screen===name)});
if(name==='history')renderHistory();if(name==='vitals')renderVitals();if(name==='patients')renderPatients();
}
function renderHistory(){
var el=document.getElementById('historyList');if(!el)return;
if(typeof diagnosticHistory==='undefined'||!diagnosticHistory.length){el.innerHTML='<div class="card"><p style="text-align:center;color:var(--muted);margin:20px">Aucun diagnostic pour le moment.</p></div>';return}
var h='';for(var i=0;i<Math.min(diagnosticHistory.length,20);i++){var d=diagnosticHistory[i];var dt=new Date(d.date);
h+='<div class="history-item'+(d.urgent?' urgent':'')+'"><div class="date">'+dt.toLocaleDateString('fr-FR',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})+'</div><strong>'+d.diagnosis+'</strong> <span style="color:var(--accent);font-weight:700">'+d.score+'%</span><div style="font-size:.8em;color:var(--muted);margin-top:4px">'+d.symptoms.substring(0,80)+'</div></div>'}
el.innerHTML=h;
}
function renderVitals(){
var el=document.getElementById('vitalsContent');if(!el)return;
var hr=68+Math.floor(Math.random()*10),spo2=96+Math.floor(Math.random()*4),temp=(36.3+Math.random()*1.2).toFixed(1),bp=(110+Math.floor(Math.random()*20))+'/'+(70+Math.floor(Math.random()*15));
el.innerHTML='<div class="card"><h3>Constantes Vitales</h3><div class="vital-grid"><div class="vital-card"><div class="value">'+hr+'</div><div class="label">BPM Cardiaque</div></div><div class="vital-card"><div class="value">'+bp+'</div><div class="label">mmHg Tension</div></div><div class="vital-card"><div class="value">'+spo2+'%</div><div class="label">SpO2 Oxygene</div></div><div class="vital-card"><div class="value">'+temp+'°C</div><div class="label">Temperature</div></div></div><p style="font-size:.7em;color:var(--muted);text-align:center;margin-top:12px">Simulation</p></div>';
}
function renderPatients(){
var el=document.getElementById('patientsList');if(!el)return;
var pts=loadPatients();var keys=Object.keys(pts);
var h='<div style="margin-bottom:12px;display:flex;gap:8px"><input id="newPatientInput" placeholder="Nom du patient..." style="flex:1;background:#141414;color:#d4c8a0;border:1px solid #2a2a2a;padding:10px 14px;border-radius:10px;font-size:14px;font-family:inherit"><button class="btn btn-sm btn-primary" style="width:auto;padding:8px 16px" onclick="addPatient()">Ajouter</button></div>';
if(!keys.length)h+='<div class="card"><p style="text-align:center;color:var(--muted)">Aucun patient.</p></div>';
for(var i=keys.length-1;i>=Math.max(0,keys.length-10);i--){var id=keys[i];var p=pts[id];
h+='<div class="patient-row" onclick="currentPatient={id:&quot;'+id+'&quot;,...loadPatients()[&quot;'+id+'&quot;]};showScreen(&quot;resonance&quot;);refreshPatientSelect()"><div class="avatar">'+(p.name||'?')[0].toUpperCase()+'</div><div class="info"><div class="name">'+p.name+'</div><div class="meta">'+(p.history?p.history.length:0)+' diagnostics</div></div><span style="color:var(--accent);font-size:1.2em">›</span></div>'}
el.innerHTML=h;
}
function addPatient(){var n=(document.getElementById('newPatientInput')?.value||'').trim();if(!n)return;var pts=loadPatients();var id='p'+Date.now();pts[id]={name:n,history:[],createdAt:new Date().toISOString()};savePatients(pts);document.getElementById('newPatientInput').value='';renderPatients();refreshPatientSelect()}

function updateDossier(){if(!currentPatient){document.getElementById('dossierAvatar').textContent='?';document.getElementById('dossierName').textContent='Patient anonyme';document.getElementById('dossierId').textContent='';return}document.getElementById('dossierAvatar').textContent=(currentPatient.name||'?')[0].toUpperCase();document.getElementById('dossierName').textContent=currentPatient.name;document.getElementById('dossierId').textContent='ID: '+currentPatient.id;}
var origOnPatientSelect = onPatientSelect;
onPatientSelect = function(id){origOnPatientSelect(id);updateDossier();}

function importPatientData(){
KA_BRIDGE.readTransferCode(function(pkg){
var id=KA_BRIDGE.importToKACare(pkg);
if(id){alert('Patient importé !');renderPatients();KA_SECURE.showLockScreen(function(){refreshPatientSelect();});}
else{alert('Format invalide.');}
});
}
function exportDiagnosis(){
if(!currentPatient){alert('Sélectionnez un patient d'abord.');return}
var diag={diagnostic_principal:{maladie:'',score:0,symptomes_attendus:[],conduite:'',urgence:false,delai:''},diagnostics_différentiels:[]};
var results=document.getElementById('resultsArea');
if(results){
var first=results.querySelector('.result-item');
if(first){diag.diagnostic_principal.maladie=first.querySelector('strong')?.textContent?.replace('🚨','').trim()||''}
}
if(!diag.diagnostic_principal.maladie){alert('Lancez un diagnostic d'abord.');return}
var pkg=KA_BRIDGE.doctorToPatient(diag,{name:currentPatient.name,id:currentPatient.id});
var code=KA_BRIDGE.generateQRCode(pkg,'qrTransfer');
var modal=document.createElement('div');
modal.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.9);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px';
modal.innerHTML='<div style="background:#1a1a1a;border:1px solid #d4a853;border-radius:16px;padding:24px;max-width:400px;text-align:center"><h3 style="color:#d4a853;margin-bottom:12px">📤 Transfert au patient</h3><div id="qrTransfer" style="margin:12px 0"></div><p style="font-size:.7em;color:#9b8f7e">Le patient scanne ce code avec KA Patient</p><button onclick="this.parentElement.parentElement.remove()" style="background:#d4a853;color:#0d0d0d;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;margin-top:12px;font-weight:700;font-family:inherit">Fermer</button></div>';
document.body.appendChild(modal);
modal.onclick=function(e){if(e.target===modal)modal.remove()};
}

function setupPIN(){
var pin=prompt('Créez un code PIN à 4 chiffres pour protéger l'accès aux dossiers patients :');
if(!pin||pin.length!==4||!/^\d{4}$/.test(pin)){alert('PIN invalide (4 chiffres requis).');return}
if(KA_SECURE.setPIN(pin)){alert('✅ PIN configuré !');}
else{alert('Erreur.');}
}
</script>
<nav class="bottom-nav" id="bottomNav" style="display:none">
<div class="nav-item active" data-screen="resonance" onclick="showScreen('resonance')"><span class="nav-icon">〰️</span><span class="nav-label">Resonance</span></div>
<div class="nav-item" data-screen="history" onclick="showScreen('history')"><span class="nav-icon">📋</span><span class="nav-label">History</span></div>
<div class="nav-item" data-screen="vitals" onclick="showScreen('vitals')"><span class="nav-icon">💓</span><span class="nav-label">Vitals</span></div>
<div class="nav-item" data-screen="patients" onclick="showScreen('patients')"><span class="nav-icon">👥</span><span class="nav-label">Profile</span></div>
</nav>
<div class="screen" id="screen-history"><div id="historyList" style="padding:16px"></div></div>
<div class="screen" id="screen-vitals"><div id="vitalsContent" style="padding:16px"></div></div>
<div class="screen" id="screen-patients"><div id="patientsList" style="padding:16px"></div></div>

<div class="screen" id="screen-cardiac">
<div style="padding:16px">
<header style="text-align:center;padding:24px 0 16px"><h2 style="color:#d4a853">ANALYSE CARDIAQUE</h2></header>
<div class="card"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px"><h3 style="margin:0">ECG — Derivation II</h3><span class="harmonic-badge" id="harmonicStatus"><span class="dot"></span> Link Actif 94%</span></div>
<div class="ecg-grid"><div class="grid-overlay"></div>
<svg viewBox="0 0 600 200"><path d="M0,100 L50,100 L55,100 L60,30 L65,170 L70,100 L120,100 L125,100 L130,20 L135,180 L140,100 L200,100 L250,100 L300,100 L350,100 L400,100 L450,100 L500,100 L505,100 L510,40 L515,160 L520,100 L570,100 L600,100" stroke="#d4a853" stroke-width="2" fill="none" opacity="0.8"/></svg></div>
<div style="margin-top:12px"><input type="range" min="0" max="100" value="50" style="width:100%;accent-color:#d4a853"></div></div>
<div class="vital-grid" style="margin-top:12px">
<div class="stat-card"><div class="val">72</div><div class="lbl">BPM MOYEN</div></div>
<div class="stat-card"><div class="val">45 ms</div><div class="lbl">VARIABILITE</div></div>
<div class="stat-card"><div class="val">0</div><div class="lbl">ANOMALIES 24h</div></div>
<div class="stat-card"><div class="val">98%</div><div class="lbl">FIABILITE</div></div>
</div>
<div class="card" style="margin-top:12px"><h3>Evenements recents</h3>
<div class="event-row"><span class="dot"></span><span class="evt-time">14:30</span><span class="evt-text">Pic d'activite — 94 BPM</span></div>
<div class="event-row"><span class="dot" style="background:#666"></span><span class="evt-time">12:15</span><span class="evt-text">Phase de repos — 58 BPM</span></div>
<div class="event-row"><span class="dot" style="background:#666"></span><span class="evt-time">08:45</span><span class="evt-text">Variabilite matinale — 52 ms</span></div>
</div>
</div>
</div>

<div class="screen" id="screen-scanner">
<div style="padding:16px">
<header style="text-align:center;padding:24px 0 16px"><h2 style="color:#d4a853">SCANNER QR CODE</h2></header>
<div class="card" style="text-align:center">
<div class="scanner-view"><div class="corner tl"></div><div class="corner tr"></div><div class="corner bl"></div><div class="corner br"></div><div class="scan-line"></div></div>
<p style="color:#9b8f7e;margin:16px 0">Recherche de signal...</p>
<button class="btn btn-secondary" style="width:auto;padding:10px 24px;margin:0 auto">📷 Activer la camera</button>
<p style="font-size:.7em;color:#8b7355;margin-top:8px">Ou saisir le code manuellement</p>
<input placeholder="Code patient..." style="width:200px;padding:8px 12px;background:#141414;color:#d4c8a0;border:1px solid #2a2a2a;border-radius:8px;font-size:14px;font-family:inherit;text-align:center;margin-top:8px">
</div>
</div>
</div>

<div class="screen" id="screen-dossier">
<div style="padding:16px">
<header style="text-align:center;padding:24px 0 16px"><h2 style="color:#d4a853">DOSSIER MEDICAL</h2></header>
<div class="card" style="text-align:center"><div style="width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,#d4a853,#7b5804);display:flex;align-items:center;justify-content:center;font-size:1.6em;font-weight:700;margin:0 auto 8px" id="dossierAvatar">?</div><h3 id="dossierName">Patient anonyme</h3><p style="color:#9b8f7e;font-size:.8em" id="dossierId"></p></div>
<div class="vital-grid" style="margin-top:12px">
<div class="stat-card"><div class="val">72</div><div class="lbl">BPM</div></div>
<div class="stat-card"><div class="val">12/8</div><div class="lbl">cmHg</div></div>
<div class="stat-card"><div class="val">98%</div><div class="lbl">SpO2</div></div>
<div class="stat-card"><div class="val">36.7°</div><div class="lbl">Temp</div></div>
</div>
<div class="action-grid" style="margin-top:12px">
<div class="action-card" onclick="showScreen('resonance')"><div class="icon">🔍</div><div class="title">Nouveau Diagnostic</div><div class="sub">Lancer une analyse</div></div>
<div class="action-card" onclick="showScreen('cardiac')"><div class="icon">🫀</div><div class="title">Analyse Cardiaque</div><div class="sub">ECG detaille</div></div>
<div class="action-card" onclick="showScreen('history')"><div class="icon">📋</div><div class="title">Historique</div><div class="sub">Diagnostics passes</div></div>
<div class="action-card" onclick="showScreen('scanner')"><div class="icon">📷</div><div class="title">Scanner QR</div><div class="sub">Ouvrir un dossier</div></div>
</div>
</div>
</div>
</body>
</html>
