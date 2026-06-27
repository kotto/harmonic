#!/usr/bin/env python3
"""
GENERATEUR VOCABULAIRE_ETENDU — Version autonome.
Copie VOCABULAIRE_BASE + filtre les mots extraits → écrit le fichier complet.
"""
import os, re, json

# ==== VOCABULAIRE_BASE (copié depuis harmonic_resonance_generator.py) ====
VOCABULAIRE_BASE = [
    '<PAD>','<UNK>','<BOS>','<EOS>',
    'le','la','les','de','des','du','un','une','et','est','a',
    'dans','que','qui','pas','ne','sur','pour','avec',
    'je','tu','il','elle','on','nous','vous','ils','elles',
    'ce','cet','cette','ces','mon','ton','son','ma','ta','sa',
    'au','aux','en','par','plus','moins','tres','aussi',
    'comme','si','mais','ou','donc','car','ni','or',
    'faire','dire','avoir','etre','aller','pouvoir','vouloir','savoir',
    'voir','venir','prendre','donner','parler','temps','chose','monde',
    'vie','homme','femme','enfant','jour','nuit','mois','annee','heure',
    'question','reponse','probleme','solution','idee','raison',
    'travail','maison','ville','pays','grand','petit','beau','bon',
    'mauvais','vrai','faux','nouveau','vieux','jeune',
    'long','court','haut','bas','fort','faible','rapide','clair',
    'important','necessaire','possible','impossible','premier','dernier',
    'tout','tous','toute','chaque','quelque','plusieurs',
    'rien','personne','jamais','toujours','souvent','parfois',
    'beaucoup','peu','trop','assez','encore','enfin',
    'alors','apres','avant','depuis','pendant','vers','chez',
    'sans','sous','contre','selon','loin','pres',
    'ici','la','ailleurs','maintenant','aujourd','hier','demain',
    'bonjour','merci','pardon','oui','non','peut-etre',
    'comment','pourquoi','combien',
    'harmonie','resonance','frequence','onde',
    'phi','nombre','or','proportion','doree',
    'univers','nature','physique','conscience','esprit','ame',
    'pensee','intelligence','connaissance','sagesse','verite',
    'amour','paix','joie','lumiere','energie','force',
    'sens','infini','eternel','absolu','systeme','modele',
    'theorie','principe','loi','information',
    'algorithme','programme','fonction','reseau',
    'apprentissage','inference','signature','dimension','espace',
    'generation','creation','analyse','synthese','logique',
    'raisonnement','intuition','imagination','sentiment','emotion',
    'realite','possible','necessaire','cause','effet',
    'zero','un','deux','trois','quatre','cinq',
    'six','sept','huit','neuf','dix','cent','mille',
    'quand','ou','pourquoi','comment','quel','quelle',
    'se','ce','sa','son','tes','ta','ton','mes','ma','mon',
    'ses','leurs','leur','nos','notre','vos','votre',
    'donc','or','ni','car','mais','ou','et',
    'pourtant','cependant','neanmoins','toutefois','quoique',
    'parce','puisque','ainsi','notamment',
    'precisement','effectivement','certes','sansdoute',
    'philosophie','science','art','musique','poesie',
    'mathematique','physique','chimie','biologie',
    'histoire','geographie','politique','economie',
    'droit','justice','liberte','egalite','fraternite',
    'reve','imagination','creation','invention',
    'beaute','harmonie','equilibre','perfection',
    'complexite','simplicite','profondeur','surface',
    'evolution','revolution','transformation','changement',
    'diversite','unite','totalite','partie',
    'abstrait','concret','theorique','pratique',
    'operationnel',
]

# Stopwords supplémentaires à exclure
STOPWORDS = {
    'environ','sont','ont','ans','etait','avait','etaient','ete',
    'peut','entre','tres','dont','taux','toutes','tous',
    'permet','egal','egalement','egalement',
}

def extraire_mots_depuis_fichier(filepath: str) -> list:
    """Extrait les mots uniques depuis vocabulaire_extrait.py"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher le MOTS_PAR_FREQUENCE list
    match = re.search(r'MOTS_PAR_FREQUENCE\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if not match:
        print("ERREUR: Impossible de trouver MOTS_PAR_FREQUENCE dans", filepath)
        return []
    
    # Extraire les tuples (mot, freq)
    tuples = re.findall(r"\(\s*'([^']*)'\s*,\s*(\d+)\s*\)", match.group(1))
    
    mots = []
    vus = set()
    base_set = set(VOCABULAIRE_BASE)
    
    for mot, freq_str in tuples:
        freq = int(freq_str)
        mot_lower = mot.lower().strip()
        
        # Normalize: remove accents for comparison with base
        mot_norm = mot_lower.replace("'", "")
        
        if mot_norm in base_set:
            continue
        if mot_norm in STOPWORDS:
            continue
        if len(mot_norm) <= 2 and not mot_norm.isalpha():
            continue
        if mot_norm in vus:
            continue
        
        vus.add(mot_norm)
        mots.append((mot, freq))
    
    # Trier par fréquence desc puis alpha
    mots.sort(key=lambda x: (-x[1], x[0]))
    return mots

def classifier_par_domaine(mots):
    """Classe les mots par domaine heuristique."""
    histoire = set([
        'afrique','africain','africaine','africaines','africains',
        'royaume','koush','meroe','ghana','mali','zimbabwe',
        'kongo','nzinga','ndongo','matamba','angola',
        'dahomey','samory','toure','menelik','ranavalona',
        'madagascar','chaka','zoulou','bismarck','berlin',
        'nkrumah','kwame','garvey','marcus','equiano','olaudah',
        'panafricanisme','panafricain','panafricaniste',
        'colonisation','colonial','coloniaux','negriere','deporte',
        'transatlantique','abolitionniste',
        'tirailleurs','senegalais','soldats',
        'siecle','xixe','xxe','xviie','xive','xiie','xiiie','xiiie-xve',
        'civilisation','ecriture','hieroglyphes','meroitique',
        'langues','langue','swahilie','transsaharienne','transsahariennes',
        'mansa','kankan','moussa',
        'capitale','empereur','reine',
        'bataille','guerre','guerres','resistance','resistances',
        'resiste','revoltes','combattu',
        'independant','independances','independante',
        'partage','conference','chancelier',
        'exploitation','economique','brutale',
        'mondiales','determinante','massive','participation',
        'portugais','britanniques','francais','francaise',
        'etaient','directement','attribuables',
        'determinees','heroiques','ancetres','afrocentree',
        'statues','culturelles','culturelle','civilisations',
        'empire','empires','rois','reines','egypte','nubie',
        'songhai','askia','mohammed','tombouctou',
        'universite','sankore','manuscrits','savants',
        'or','sel','commerciales','routes','caravanes',
        'berberes','nomades','peuples','ethnies',
        'esclavage','traite','négriere','plantation',
        'resistant','resister','resistance',
        'independance','decolonisation','liberation',
        'nationalisme','nationaliste','négritude',
        'senghor','cesaire','diop','cheikh','anta',
        'lumumba','kasa-vubu','mobutu','kenyatta','nyerere',
        'kaunda','nkomo','mugabe','mandela','tambo',
        'apartheid','segregation','discrimination',
        'race','raciale','racisme','raciste',
        'ethiopie','liberia','egyptien','egyptienne',
        'maghreb','tunisie','algerie','maroc',
        'mozambique','angola','guinee','cote','ivoire',
        'senegal','mali','burkina','faso','niger',
        'tchad','cameroun','gabon','congo','rwanda','burundi',
        'ouganda','kenya','tanzanie','zambie','malawi',
        'botswana','namibie','afrique','sud',
    ])
    
    medecine = set([
        'cancer','cancers','traitement','traitements','maladie','maladies',
        'patients','patient','diagnostic','depistage',
        'chronique','chroniques','ague','symptomes',
        'infection','infectieuse','bacterienne','bacteries','virale','virus',
        'tuberculose','tuberculosis','paludisme','vih','sida',
        'pneumonie','bronchopneumopathie','bpco',
        'bronchiolite','coqueluche','rougeole','oreillons','rubeole',
        'tetanos','diphterie','poliomyelite',
        'diabete','hypertension','cardiaque','cardiovasculaire',
        'infarctus','fibrillation','atriale','arythmie',
        'accident','vasculaire','cerebral','avc',
        'parkinson','alzheimer','sclerose','plaques',
        'depression','anxiete','schizophrenie','bipolaire',
        'psychiatrique','psychiatriques','troubles','anxieux',
        'asthme','bronchite','pneumocoque','meningocoque',
        'hepatite','hepatites','cirrhose',
        'renal','renale','renaux','nephropathie','nephrotique',
        'antibiotiques','antipsychotiques','immunosuppresseurs',
        'vaccination','vaccins','vaccinal','vaccin',
        'chirurgie','radiotherapie','chimiotherapie',
        'transplantation','greffe',
        'medicament','medicaments',
        'epidemiologie','prevalence','incidence','mortalite',
        'soins','sante','publique','hopital','clinique',
        'urgences','reanimation',
        'pediatrie','neonatologie','geriatrie',
        'respiratoire','neurologique',
        'inflammatoire','auto-immune','dégenerative',
        'genetique','mutation','moleculaire','cellulaire','cellules',
        'staphylococcus','streptococcus','pseudomonas','aeruginosa',
        'escherichia','enterobacteries',
        'meticilline','carbapenemes','rifampicine','isoniazide',
        'statines','atorvastatine','rosuvastatine',
        'insuffisance','cardiaque','renale','hepatique',
        'obesite','surpoids','metabolique','syndrome',
        'thyroide','dysthyroidies','cushing',
        'prostate','colorectal','poumon','melanome','sein',
        'psoriasis','eczema','dermatite','dermatose',
        'polyarthrite','rhumatoide','goutte','arthropathie',
        'osteoporose','fracture',
        'grossesse','pre-eclampsie','mammographie',
        'cataracte','glaucome','degenerescence','maculaire',
        'prevention','reeducation','kinésitherapie','rehabilitation',
        'palliatif','accompagnement',
        'diabetique','diabetiques','obese','obeses',
        'cardiaques','cardio','vasculaires',
        'cerebrovasculaire','myocarde','infarctus',
        'arythmie','bradycardie','tachycardie',
        'valvulaire','valvulopathie','endocardite',
        'pericarde','myocardite','cardiomyopathie',
        'anevrisme','thrombose','embolie','pulmonaire',
        'phlebite','hemorragie','hemorragique',
        'leucemie','lymphome','myelome','tumeur','tumeurs',
        'benin','benigne','malin','maligne','metastase',
        'biopsie','scanner','irm','echographie','radiographie',
        'analyse','sanguin','sanguine','biologique',
        'cholesterol','triglycerides','glycemie','hemoglobine',
        'creatinine','uree','kaliemie','natremie',
        'virologie','bacteriologie','parasitologie',
        'mycose','champignon','levure','candida',
        'aspergillose','cryptococcose','toxoplasmose',
        'pneumocystose','strongyloidose',
        'nosocomiale','communautaire','opportuniste',
        'prophylaxie','chimioprophylaxie','serotherapie',
        'antiviral','antiviraux','antiretroviraux',
        'antipaludique','antileishmanien','anthelminthique',
        'allergie','allergique','allergene','anaphylaxie',
        'urticaire','angiœdeme','dermatite','atopique',
        'intolerance','intolerant','gluten','lactose',
        'endocrinienne','endocrinien','hormone','hormonal',
        'thyroide','thyroïdien','parathyroide','surrenale',
        'hypophyse','hypothalamus','pineale',
        'diabetologue','endocrinologue','nutritionniste',
        'dieteticien','dietetique','nutrition',
        'psychiatre','psychologue','psychotherapeute',
        'neurologue','neurochirurgien','neuropediatre',
        'cardiologue','chirurgien','cardiochirurgien',
        'pneumologue','gastroenterologue','hepatologue',
        'nephrologue','urologue','gynecologue','obstetricien',
        'pediatre','geriatre','gerontologue',
        'radiologue','anatomopathologiste','biologiste',
        'pharmacien','pharmacologie','pharmacovigilance',
        'infirmier','infirmiere','aide-soignant','aide-soignante',
        'ambulancier','sage-femme','puéricultrice',
        'methylprednisolone','dexamethasone','hydrocortisone',
        'prednisone','prednisolone','betamethasone',
        'cortisone','corticoides','corticotherapie',
        'furosemide','spironolactone','hydrochlorothiazide',
        'indapamide','bumetanide','diuretiques',
        'amlodipine','nifedipine','lercanidipine',
        'inhibiteurs','calcium','icb',
        'beta-bloquants','beta-bloquant','atenolol','bisoprolol',
        'propranolol','metoprolol','nebivolol','carvedilol',
        'iec','sartan','valsartan','losartan','irbesartan',
        'candesartan','telmisartan','olmesartan',
        'ramipril','perindopril','enalapril','lisinopril',
        'captopril','trandolapril','quinapril','fosinopril',
        'clopidogrel','ticagrelor','prasugrel','antiagregant',
        'aspirine','warfarin','acenocoumarol','avk',
        'rivaroxaban','apixaban','edoxaban','dabigatran',
        'aod',' anticoagulant','anticoagulants',
        'heparine','heparine','enoxaparine','tinzaparine',
        'fondaparinux','bivalirudine',
        'metformine','glibenclamide','gliclazide','glimepiride',
        'sitagliptine','vildagliptine','saxagliptine','linagliptine',
        'dpp-4','inhibiteurs',
        'dulaglutide','liraglutide','semaglutide','exenatide',
        'glp-1','agoniste',
        'empagliflozine','dapagliflozine','canagliflozine',
        'sglt2','inhibiteur',
        'insuline','glargine','detemir','degludec','aspart',
        'lispro','glulisine','regular','nph',
        'antidepresseur','antidepresseurs','isrs','isrsn',
        'fluoxetine','sertraline','escitalopram','citalopram',
        'paroxetine','fluvoxamine','vortioxetine',
        'venlafaxine','duloxetine','milnacipran','levomilnacipran',
        'amitriptyline','clomipramine','imipramine','nortriptyline',
        'mirtazapine','trazodone','agomelatine','bupropion',
        'benzodiazepines','benzodiazepine','diazepam','lorazepam',
        'alprazolam','bromazepam','clonazepam','oxazepam',
        'temazepam','nitrazepam','flunitrazepam',
        'zolpidem','zopiclone','eszopiclone',
        'hypnotiques','sedatifs','anxiolytiques','anxiolytique',
        'lithium','thymoregulateur','thymoregulateurs',
        'lamotrigine','valproate','acide','valproique',
        'carbamazepine','oxcarbazepine',
        'olanzapine','quetiapine','risperidone','aripiprazole',
        'clozapine','paliperidone','amisulpride','lurasidone',
        'ziprasidone','haloperidol','chlorpromazine',
        'neuroleptiques','neuroleptique','antipsychotique',
        'morphine','fentanyl','oxycodone','hydromorphone',
        'codeine','tramadol','naloxone','buprenorphine',
        'methadone','analgesiques','antalgiques','antalgique',
        'anti-inflammatoire','anti-inflammatoires','aINS',
        'ibuprofene','kétoprofene','diclofenac','naproxene',
        'piroxicam','meloxicam','celecoxib','etoricoxib',
        'paracetamol','acetaminophene','nefopam','floctafenine',
        'colchicine','allopurinol','febuxostat','hypouricemiants',
        'methotrexate','leflunomide','sulfasalazine','hydroxychloroquine',
        'corticoide','corticoides','bolus',
        'anti-tnf','infliximab','adalimumab','etanercept',
        'certolizumab','golimumab','tocilizumab','rituximab',
        'belimumab','secukinumab','ustekinumab','vedolizumab',
        'biothérapies','biothérapie','biologique',
        'immunoglobulines','plasmapherese','echange','plasmatique',
        'mycophenolate','cyclophosphamide','azathioprine',
        'ciclosporine','tacrolimus','sirolimus','everolimus',
        'viagra','cialis','leV','traitement','dysfonction','erectile',
        'corticotherapie','inhalée','inhalateur','aérosol',
        'nébulisation','bronchodilatateur','bronchodilatateurs',
        'beta-2','mimétiques','salmeterol','formoterol',
        'indacaterol','olodaterol','vilanterol','umeclidinium',
        'glycopyrronium','tiotropium','aclidinium','ipratropium',
        'anticholinergiques','anticholinergique',
        'corticoide','inhalé','béclometasone','budésonide',
        'fluticasone','mométasone','ciclesonide',
        'montelukast','zafirlukast','antileucotriène',
        'omalizumab','mepolizumab','reslizumab','benralizumab',
        'anti-ige','anti-il5','anti-il4','anti-il13',
        'duplilumab','tralokinumab','lebrikizumab',
        'antihistaminique','antihistaminiques',
        'cétirizine','loratadine','desloratadine','fexofenadine',
        'levocétirizine','bilastine','ebastine','mizolastine',
        'hydroxyzine','dexchlorphéniramine','prométhazine',
        'anti-H1','anti-H2',
        'cromoglycate','nedocromil','kétotifène',
        'vaccin','vaccins','dTP','hexavalent','pentavalent',
        'BCG','vaccination','rougeole','oreillons','rubéole','ROR',
        'hépatite','B','vaccin','HPV','papillomavirus',
        'méningocoque','pneumocoque','haemophilus','influenzae',
        'coqueluche','tétanos','diphtérie','poliomyélite',
        'grippe','grippal','saisonnier','vaccin','antigrippal',
        'COVID-19','SARS-CoV-2','coronavirus','pandémie',
        'confinement','distanciation','gestes','barrière',
        'masque','protection','dépistage','test','PCR','antigénique',
        'vaccin','ARN','messager','ARNm','vecteur','viral',
        'Comirnaty','Spikevax','Vaxzevria','Janssen','Nuvaxovid',
        'variole','variole','simienne','monkeypox','mpox',
        'fièvre','jaune','dengue','zika','chikungunya','Ébola',
        'Marburg','Lassa','fièvre','hémorragique',
        'rage','peste','charbon','anthrax',
        'bioterrorisme','biologique','guerre',
        'trypanosomiase','maladie','sommeil',
        'leishmaniose','bilharziose','filariose','onchocercose',
        'lèpre','Buruli','ulcère','plan','yaws',
        'pian','béjel','endémique','tréponématose',
        'bactérienne','résistance','antimicrobienne','RAM',
        'antibiorésistance','bactéries','multirésistantes',
        'BMR','BHRe','clostridium','difficile',
        'infection','nosocomiale','IAS','prévention',
        'hygiène','mains','solution','hydroalcoolique',
        'précautions','standard','contact','gouttelettes',
        'air','isolement','protection',
        'stérilisation','désinfection','antisepsie',
        'aiguille','blessure','exposition','sang',
        'accident','exposition','sang','AES',
        'risque','biologique','prévention',
        'infectiologue','hygiéniste','épidémiologiste',
        'microbiologiste','bactériologiste','virologiste',
        'parasitologue','mycologue',
    ])
    
    sciences = set([
        'gene','proteine','cellule','neurones',
        'molecule','molecules','atome','particule',
        'quantique','mecanique','ondulatoire',
        'thermodynamique','entropie','energie',
        'mathematique','algebre','geometrie','calcul',
        'statistique','probabilite','correlation',
        'donnees','algorithme','reseau','neuronal',
        'classification','regression','optimisation',
        'fractale','chaos','bifurcation','attracteur',
        'topologie','differentielle','integrale',
        'complexite','emergence','auto-organisation',
        'systeme','dynamique','non-lineaire',
        'feedback','boucle','retroaction','causalite',
        'entropie','information','theorie',
        'bit','qubit','quantique','intrication',
        'superposition','decoherence','teleportation',
        'crypto','cryptographie','chiffrement',
        'holographique','hologramme','holographie',
        'fourier','ondelette','transformee',
        'harmonique','frequence','amplitude','phase',
        'resonance','cavite','mode','propre',
        'signal','traitement','filtre','convolution',
        'gradient','descente','stochastique',
        'tenseur','matrice','vecteur','espace',
        'latent','plongement','embedding',
        'attention','transformer','autoregressif',
        'diffusion','flow','normalisation',
        'batch','layer','dropout','regularisation',
        'fonction','perte','loss','entropie','croisee',
        'apprentissage','supervise','non-supervise',
        'renforcement','RLHF','fine-tuning',
        'transfert','apprentissage','few-shot',
        'zero-shot','prompt','ingenierie',
        'distillation','modele','compresser',
        'token','tokenization','vocabulaire',
        'corpus','dataset','entrainement',
        'inference','inférence','generation',
        'raisonnement','cognition','conscience',
        'emergence','intelligence','artificielle',
        'alignement','securite','ethique','IA',
    ])
    
    h, m, s, d = [], [], [], []
    for mot, freq in mots:
        ml = mot.lower()
        if ml in histoire:
            h.append((mot, freq))
        elif ml in medecine:
            m.append((mot, freq))
        elif ml in sciences:
            s.append((mot, freq))
        else:
            d.append((mot, freq))
    return h, m, s, d

def ecrire_fichier_complet(mots_histoire, mots_medecine, mots_sciences, mots_divers, outpath):
    """Écrire le fichier vocabulaire_etendu.py complet."""
    lines = []
    lines.append('#!/usr/bin/env python3')
    lines.append('"""')
    lines.append('VOCABULAIRE ETENDU POUR L\'HOLOGRAMME HARMONIQUE (autonome).')
    lines.append('')
    lines.append('Combine VOCABULAIRE_BASE (323 tokens generiques) avec les mots')
    lines.append('specifiques extraits des injections de connaissance (histoire,')
    lines.append('medecine, sciences).')
    lines.append('')
    lines.append('Usage :')
    lines.append('    from vocabulaire_etendu import VOCABULAIRE_ETENDU, VOCAB_SIZE_ETENDU')
    lines.append('"""')
    
    # VOCABULAIRE_BASE
    lines.append('VOCABULAIRE_BASE = [')
    for mot in VOCABULAIRE_BASE:
        lines.append(f"    '{mot}',")
    lines.append(']')
    lines.append('VOCAB_BASE_SET = set(VOCABULAIRE_BASE)')
    lines.append('')
    
    # MOTS_NOUVEAUX
    total_nouveaux = len(mots_histoire) + len(mots_medecine) + len(mots_sciences) + len(mots_divers)
    lines.append(f'# MOTS_NOUVEAUX — {total_nouveaux} mots specifiques extraits des injections')
    lines.append('# Organises par domaine heuristique.')
    lines.append('MOTS_NOUVEAUX = [')
    
    lines.append('')
    lines.append('    # ===== HISTOIRE AFRICAINE (UNESCO) =====')
    for mot, freq in mots_histoire:
        lines.append(f"    '{mot}',")
    
    lines.append('')
    lines.append('    # ===== MEDECINE (PubMed) =====')
    for mot, freq in mots_medecine:
        lines.append(f"    '{mot}',")
    
    lines.append('')
    lines.append('    # ===== SCIENCES =====')
    for mot, freq in mots_sciences:
        lines.append(f"    '{mot}',")
    
    lines.append('')
    lines.append('    # ===== DIVERS =====')
    for mot, freq in mots_divers:
        lines.append(f"    '{mot}',")
    
    lines.append(']')
    lines.append('')
    
    # Code final
    lines.append("")
    lines.append("# Filtrer les doublons avec VOCABULAIRE_BASE")
    lines.append("MOTS_NOUVEAUX_FILTRES = []")
    lines.append("for mot in MOTS_NOUVEAUX:")
    lines.append("    if mot not in VOCAB_BASE_SET and mot not in MOTS_NOUVEAUX_FILTRES:")
    lines.append("        MOTS_NOUVEAUX_FILTRES.append(mot)")
    lines.append("")
    lines.append("# Vocabulaire etendu final")
    lines.append("VOCABULAIRE_ETENDU = VOCABULAIRE_BASE + MOTS_NOUVEAUX_FILTRES")
    lines.append("VOCAB_SIZE_ETENDU = len(VOCABULAIRE_ETENDU)")
    lines.append("")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append("    print(f'VOCABULAIRE_BASE: {len(VOCABULAIRE_BASE)} tokens')")
    lines.append("    print(f'MOTS_NOUVEAUX: {len(MOTS_NOUVEAUX)} tokens (bruts)')")
    lines.append("    print(f'MOTS_NOUVEAUX_FILTRES: {len(MOTS_NOUVEAUX_FILTRES)} tokens (apres dedup)')")
    lines.append("    print(f'VOCABULAIRE_ETENDU: {VOCAB_SIZE_ETENDU} tokens')")
    lines.append("    # Verification : mots cibles doivent etre presents")
    lines.append("    cibles = [")
    lines.append("        'ghana','infarctus','fibrillation','paludisme','parkinson',")
    lines.append("        'tuberculose','hypertension','alzheimer','cancer','diabete',")
    lines.append("        'schizophrenie','hologramme','connaissance','resonance',")
    lines.append("        'cardiaque','traitement','colonisation','vaccination',")
    lines.append("    ]")
    lines.append("    print('\\n--- Verification mots cibles ---')")
    lines.append("    VOCAB_SET = set(VOCABULAIRE_ETENDU)")
    lines.append("    manquants = []")
    lines.append("    for c in cibles:")
    lines.append("        present = c in VOCAB_SET")
    lines.append("        if present:")
    lines.append("            print(f'  [OK] {c}')")
    lines.append("        else:")
    lines.append("            print(f'  [MANQUE] {c}')")
    lines.append("            manquants.append(c)")
    lines.append("    if manquants:")
    lines.append("        print(f'\\n⚠ {len(manquants)} mots cibles manquants !')")
    lines.append("    else:")
    lines.append("        print(f'\\n✓ Tous les {len(cibles)} mots cibles sont presents !')")
    
    content = '\n'.join(lines)
    
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return content

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extrait_path = os.path.join(base_dir, 'harmonic_training', 'model', 'vocabulaire_extrait.py')
    outpath = os.path.join(base_dir, 'harmonic_training', 'model', 'vocabulaire_etendu.py')
    
    if not os.path.exists(extrait_path):
        print(f"ERREUR: {extrait_path} introuvable")
        return
    
    mots = extraire_mots_depuis_fichier(extrait_path)
    print(f"Mots extraits (apres filtre): {len(mots)}")
    
    h, m, s, d = classifier_par_domaine(mots)
    print(f"  Histoire: {len(h)}")
    print(f"  Medecine: {len(m)}")
    print(f"  Sciences: {len(s)}")
    print(f"  Divers:   {len(d)}")
    print(f"  Total:    {len(h)+len(m)+len(s)+len(d)}")
    
    content = ecrire_fichier_complet(h, m, s, d, outpath)
    print(f"\nFichier ecrit: {outpath}")
    print(f"Taille: {len(content)} caracteres")
    
    # Vérification rapide
    vocab_etendu = VOCABULAIRE_BASE + [mot for mot, _ in h + m + s + d]
    total = len(vocab_etendu)
    uniques = len(set(vocab_etendu))
    print(f"\nVerification:")
    print(f"  VOCAB_BASE: {len(VOCABULAIRE_BASE)}")
    print(f"  NOUVEAUX bruts: {len(mots)}")
    print(f"  VOCAB_ETENDU (avec dedup): {total}")
    print(f"  Uniques reels: {uniques}")
    print(f"  Ratio expansion: {uniques/len(VOCABULAIRE_BASE):.1f}x")
    
    # Vérifier mots cibles
    cibles = ['ghana','infarctus','fibrillation','paludisme','parkinson',
              'tuberculose','hypertension','alzheimer','cancer','diabete',
              'schizophrenie','hologramme','connaissance','resonance',
              'cardiaque','traitement','colonisation','vaccination']
    vocab_set = set(vocab_etendu)
    print(f"\n  Mots cibles presents: {sum(1 for c in cibles if c in vocab_set)}/{len(cibles)}")
    for c in cibles:
        if c not in vocab_set:
            print(f"    MANQUE: {c}")

if __name__ == '__main__':
    main()
