"""
KA Care — Pipeline de diagnostic médical harmonique.
=====================================================
Encode les symptômes en ψ, mesure la résonance avec la base de maladies,
retourne un diagnostic classé par probabilité.

Usage :
    from ka_care import KACare
    care = KACare()
    resultat = care.diagnostiquer("fièvre, toux sèche, fatigue")
    print(resultat["diagnostic_principal"])
"""

import os, sys, json
import numpy as np

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE_DIR)

# ═══════════════════════════════════════════════════════════════════
# ENCODEUR MÉDICAL — par features (préserve la similarité sémantique)
# ═══════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * np.pi
DIM = 512

# Features médicales (16 dimensions) → chaque feature a un vecteur de base
MEDICAL_FEATURES = [
    "douleur", "fievre", "respiratoire", "digestif", "neurologique",
    "cardiaque", "cutane", "musculaire", "articulaire", "ORL",
    "urinaire", "psychologique", "general", "tete", "thorax", "abdomen",
    "renale", "hematologique", "urgence_hemorragique", "urgence_hydrique",
    "dengue_specifique", "chikungunya_specifique", "zika_specifique",
    "fievre_jaune_specifique", "cholera_specifique", "bilharziose_specifique",
    "trypano_specifique", "leishmaniose_specifique", "onchocercose_specifique",
    "filariose_specifique", "leptospirose_specifique"
]

# Vecteurs de base pour chaque feature (générés une fois)
_BASES = None

def fnv1a_64(text: str) -> int:
    """FNV-1a 64-bit — déterministe, portable."""
    h = 0xCBF29CE484222325
    for ch in text:
        h ^= ord(ch)
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h

def _init_bases():
    global _BASES
    if _BASES is not None:
        return
    _BASES = []
    for i, feat in enumerate(MEDICAL_FEATURES):
        seed = fnv1a_64(f"med_feat_{feat}")
        base = np.zeros(DIM, dtype=np.complex128)
        for d in range(DIM):
            phase = ((seed >> (d % 32)) ^ (d * 2654435761)) % 2147483647
            phase = (phase * PHI) % TAU
            base[d] = np.cos(phase) + 1j * np.sin(phase)
        base /= np.sqrt(np.sum(np.abs(base) ** 2))
        _BASES.append(base)


# Mapping symptôme → features activées (poids 0..1)
SYMPTOM_FEATURES = {
    # Douleurs
    "douleur_thoracique":   {"douleur": 1.0, "thorax": 1.0, "cardiaque": 0.8},
    "douleur_bras_gauche":  {"douleur": 1.0, "cardiaque": 0.7, "musculaire": 0.5},
    "douleur_abdominale":   {"douleur": 1.0, "abdomen": 1.0, "digestif": 0.8},
    "douleur_lombaire":     {"douleur": 1.0, "musculaire": 0.8, "articulaire": 0.5},
    "maux_de_tête":         {"douleur": 0.8, "tete": 1.0, "neurologique": 0.5},
    "maux_de_tête_violents":{"douleur": 1.0, "tete": 1.0, "neurologique": 0.8},
    "maux_de_tête_intenses":{"douleur": 1.0, "tete": 1.0, "neurologique": 0.7},
    "mal_de_gorge":         {"douleur": 0.6, "ORL": 1.0},
    "mal_de_gorge_léger":   {"douleur": 0.3, "ORL": 0.8},
    "mal_de_gorge_intense": {"douleur": 0.8, "ORL": 1.0},
    "douleur_mollet":       {"douleur": 0.8, "musculaire": 0.8},
    "douleur_pied":         {"douleur": 0.7, "articulaire": 0.6},
    "douleurs_articulaires":{"douleur": 0.8, "articulaire": 1.0},
    "douleurs_musculaires": {"douleur": 0.8, "musculaire": 1.0},
    "douleurs_abdominales": {"douleur": 0.8, "abdomen": 1.0, "digestif": 0.8},
    "douleur_bas_ventre":   {"douleur": 0.8, "abdomen": 0.8, "digestif": 0.6, "urinaire": 0.5},
    "courbatures":          {"douleur": 0.5, "musculaire": 1.0, "general": 0.5},
    
    # Fièvre
    "fièvre":               {"fievre": 0.7, "general": 0.5},
    "fièvre_modérée":       {"fievre": 0.5, "general": 0.3},
    "fièvre_élevée":        {"fievre": 1.0, "general": 0.7},
    "fièvre_cyclique":      {"fievre": 0.8, "general": 0.5},
    "frissons":             {"fievre": 0.6, "general": 0.5},
    "frissons_intenses":    {"fievre": 0.9, "general": 0.7},
    "sueurs":               {"fievre": 0.3, "general": 0.5},
    "sueurs_froides":       {"fievre": 0.2, "general": 0.7, "cardiaque": 0.5},
    
    # Respiratoire
    "toux_sèche":           {"respiratoire": 1.0, "ORL": 0.5},
    "toux_grasse":          {"respiratoire": 1.0, "ORL": 0.7},
    "toux_légère":          {"respiratoire": 0.5, "ORL": 0.3},
    "toux_sang":            {"respiratoire": 1.0, "cardiaque": 0.8},
    "essoufflement":        {"respiratoire": 1.0, "cardiaque": 0.5},
    "essoufflement_léger":  {"respiratoire": 0.6},
    "essoufflement_brutal": {"respiratoire": 1.0, "cardiaque": 0.9},
    "respiration_rapide":   {"respiratoire": 1.0, "general": 0.5},
    "sifflement_respiratoire":{"respiratoire": 1.0},
    "oppression_thoracique":{"respiratoire": 0.8, "thorax": 0.8},
    "expectorations":       {"respiratoire": 1.0},
    "expectorations_colorées":{"respiratoire": 1.0},
    
    # Digestif
    "nausées":              {"digestif": 0.8, "general": 0.4},
    "vomissements":         {"digestif": 1.0, "general": 0.5},
    "diarrhée":             {"digestif": 1.0},
    "perte_appétit":        {"digestif": 0.5, "general": 0.5},
    "douleur_rebond":       {"digestif": 0.8, "douleur": 0.8, "abdomen": 0.8},
    
    # Neurologique
    "confusion":            {"neurologique": 1.0, "general": 0.5},
    "paralysie_visage":     {"neurologique": 1.0, "tete": 0.8},
    "faiblesse_bras":       {"neurologique": 0.8, "musculaire": 0.5},
    "trouble_parole":       {"neurologique": 1.0, "tete": 0.5},
    "trouble_vision":       {"neurologique": 0.8, "tete": 0.5},
    "perte_équilibre":      {"neurologique": 0.8},
    "vertiges":             {"neurologique": 0.5, "general": 0.3},
    "photophobie":          {"neurologique": 0.6, "tete": 0.5},
    "phonophobie":          {"neurologique": 0.6, "tete": 0.5},
    
    # Cardiaque
    "palpitations":         {"cardiaque": 1.0},
    "tachycardie":          {"cardiaque": 1.0},
    "angoisse":             {"cardiaque": 0.5, "psychologique": 0.8},
    "chute_tension":        {"cardiaque": 0.8, "general": 0.5},
    
    # Autres
    "fatigue":              {"general": 0.8},
    "fatigue_légère":       {"general": 0.4},
    "fatigue_intense":      {"general": 1.0},
    "fatigue_extrême":      {"general": 1.0},
    "anosmie":              {"ORL": 0.8, "neurologique": 0.5},
    "agueusie":             {"ORL": 0.7, "neurologique": 0.5},
    "nez_bouché":           {"ORL": 1.0, "respiratoire": 0.5},
    "éternuements":         {"ORL": 1.0},
    "écoulement_nasal":     {"ORL": 1.0},
    "ganglions":            {"ORL": 0.8, "general": 0.3},
    "urticaire":            {"cutane": 1.0},
    "démangeaisons":        {"cutane": 0.8},
    "éruption_cutanée":     {"cutane": 1.0},
    "gonflement_visage":    {"cutane": 0.8, "tete": 0.5},
    "peau_marbree":         {"cutane": 0.8, "cardiaque": 0.3},
    "rougeur":              {"cutane": 0.5},
    "taches_rouges":        {"cutane": 0.8},
    "brûlures_urinaires":   {"urinaire": 1.0, "douleur": 0.5},
    "envies_fréquentes":    {"urinaire": 1.0},
    "urines_troubles":      {"urinaire": 0.8},
    "tristesse_persistante":{"psychologique": 1.0},
    "perte_intérêt":        {"psychologique": 0.8},
    "idées_noires":         {"psychologique": 1.0},
    "isolement":            {"psychologique": 0.7},
    "peur_mourir":          {"psychologique": 0.8, "cardiaque": 0.3},
    "tremblements":         {"neurologique": 0.5, "general": 0.3},
    "vision_floue":         {"neurologique": 0.5, "tete": 0.3},
    "perte_poids":          {"general": 0.5, "digestif": 0.3},
    "soif_intense":         {"general": 0.7, "digestif": 0.3},
    "haleine_fruitée":      {"general": 0.5, "digestif": 0.3},
    "raideur_nuque":        {"neurologique": 0.8, "musculaire": 0.5, "tete": 0.5},
    "raideur_dos":          {"musculaire": 0.8, "articulaire": 0.5},
    "difficulté_mouvement": {"musculaire": 0.5, "articulaire": 0.5, "general": 0.3},
    "douleur_jambe":        {"douleur": 0.7, "musculaire": 0.5},
    "spasme_musculaire":    {"musculaire": 1.0, "douleur": 0.5},
    "difficulté_avaler":    {"ORL": 0.8},
    "amygdales_rouges":     {"ORL": 1.0},
    "absence_de_toux":      {"ORL": 0.3},
    "difficulté_respirer":  {"respiratoire": 1.0, "cardiaque": 0.5},
    "difficulté_parler":    {"neurologique": 0.5, "ORL": 0.3, "respiratoire": 0.3},
    "sensation_étouffement":{"respiratoire": 0.8, "psychologique": 0.5},
    "troubles_sommeil":     {"psychologique": 0.5, "general": 0.5},
    "chaleur_locale":       {"cutane": 0.3, "general": 0.2},
    "gonflement_jambe":     {"cutane": 0.5, "musculaire": 0.3},
    "malaise":              {"general": 0.7, "cardiaque": 0.3},
    "aura_visuelle":        {"neurologique": 0.5, "tete": 0.3},
    
    # ── Spécifiques maladies tropicales ──────────────────────────
    "ictère":               {"digestif": 0.8, "general": 0.5, "fievre_jaune_specifique": 1.0},
    "hémorragies":          {"cutane": 0.8, "general": 0.7, "urgence_hemorragique": 1.0},
    "oligurie":             {"urinaire": 1.0, "general": 0.5, "renale": 1.0},
    "anurie":               {"urinaire": 1.0, "general": 0.5, "renale": 1.0},
    "pâleur":               {"cutane": 0.5, "general": 0.5, "hematologique": 0.8},
    "anémie":               {"general": 0.7, "hematologique": 1.0},
    "anémie_sévère":        {"general": 0.9, "hematologique": 1.0},
    "splénomégalie":        {"general": 0.7, "leishmaniose_specifique": 1.0},
    "splénomégalie_massive":{"general": 0.8, "leishmaniose_specifique": 1.0},
    "hépatomégalie":        {"digestif": 0.7, "general": 0.5},
    "amaigrissement":       {"general": 0.7, "digestif": 0.5},
    "pancytopénie":         {"general": 0.7, "hematologique": 1.0},
    "ictère":               {"digestif": 0.8, "general": 0.5},
    "bradycardie":          {"cardiaque": 1.0, "general": 0.3},
    "bradycardie_relative": {"cardiaque": 0.8, "general": 0.3},
    "taches_roses":         {"cutane": 1.0, "general": 0.3},
    "abattement":           {"general": 0.7, "psychologique": 0.5},
    "douleurs_rétro_orbitaires": {"tete": 1.0, "douleur": 0.8, "neurologique": 0.5},
    "polyarthralgie":       {"articulaire": 1.0, "douleur": 0.8},
    "myalgies_mollets":     {"musculaire": 1.0, "douleur": 0.7},
    "hématurie":            {"urinaire": 1.0, "general": 0.5},
    "diarrhée_sanglante":   {"digestif": 1.0, "general": 0.5},
    "diarrhée_aqueuse_profuse": {"digestif": 1.0, "general": 0.7},
    "déshydratation_sévère":{"general": 1.0, "digestif": 0.5},
    "crampes_musculaires":  {"musculaire": 1.0, "douleur": 0.5, "general": 0.3},
    "yeux_enfoncés":        {"general": 1.0, "tete": 0.5},
    "pli_cutané":           {"cutane": 0.8, "general": 0.5},
    "choc_hypovolémique":   {"cardiaque": 1.0, "general": 0.8},
    "chancre_inoculation":  {"cutane": 1.0, "general": 0.3},
    "prurit_intense":       {"cutane": 1.0, "general": 0.3},
    "nodules_sous_cutanés": {"cutane": 1.0, "general": 0.3},
    "cécité_progressive":   {"neurologique": 1.0, "tete": 0.8},
    "dépigmentation":       {"cutane": 0.8, "general": 0.3},
    "lymphœdème":           {"cutane": 1.0, "general": 0.5},
    "éléphantiasis":        {"cutane": 1.0, "general": 0.5},
    "hydrocèle":            {"urinaire": 0.8, "general": 0.3},
    "lymphangite":          {"cutane": 0.8, "general": 0.3},
    "saignements_muqueuses":{"cutane": 0.8, "general": 0.5, "urgence_hemorragique": 0.8},
    "léthargie":            {"neurologique": 0.8, "psychologique": 0.5, "general": 0.5},
    "insuffisance_rénale":  {"urinaire": 1.0, "general": 0.7, "renale": 1.0},
    "ataxie":               {"neurologique": 1.0, "general": 0.3},
    "prurit":               {"cutane": 0.8, "general": 0.2},
    "conjonctivite":        {"ORL": 0.5, "cutane": 0.5},
    "hépatomégalie":        {"digestif": 0.7, "general": 0.5},
    "bradycardie_relative": {"cardiaque": 0.8, "general": 0.3},
}


def _symptom_to_features(symptom: str) -> dict:
    """Convertit un symptôme en dictionnaire de features activées."""
    key = symptom.lower().strip().replace(" ", "_")
    
    # Chercher le symptôme exact
    if key in SYMPTOM_FEATURES:
        return SYMPTOM_FEATURES[key]
    
    # Chercher partiellement
    for sk in SYMPTOM_FEATURES:
        if sk in key or key in sk:
            return SYMPTOM_FEATURES[sk]
    
    # Fallback : extraire les mots et attribuer des features basiques
    features = {}
    words = key.split("_")
    for w in words:
        for feat in MEDICAL_FEATURES:
            if feat in w or w in feat:
                features[feat] = 0.5
    if not features:
        features["general"] = 0.5
    return features


def encode(text: str) -> np.ndarray:
    """Encode un texte (symptômes) en ψ via features médicales.
    
    Contrairement à FNV1a pur, cette méthode préserve la similarité
    sémantique : deux symptômes partageant des features médicales
    auront des ψ proches.
    """
    _init_bases()
    
    symptoms = text.lower().replace(",", " ").replace(";", " ").split("_")
    # Regrouper en bigrammes pour capturer "douleur_thoracique", etc.
    words = text.lower().replace(",", " ").replace(";", " ").split()
    
    psi = np.zeros(DIM, dtype=np.complex128)
    
    # Essayer chaque mot individuellement + paires
    for i, word in enumerate(words):
        features = _symptom_to_features(word)
        for feat_name, weight in features.items():
            if feat_name in MEDICAL_FEATURES:
                idx = MEDICAL_FEATURES.index(feat_name)
                psi += weight * _BASES[idx]
    
    # Essayer les bigrammes
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i+1]}"
        features = _symptom_to_features(bigram)
        for feat_name, weight in features.items():
            if feat_name in MEDICAL_FEATURES:
                idx = MEDICAL_FEATURES.index(feat_name)
                psi += weight * _BASES[idx] * 0.5  # poids réduit pour bigrammes
    
    norm = np.sqrt(np.sum(np.abs(psi) ** 2))
    if norm > 1e-10:
        psi /= norm
    return psi


def resonance(psi_a: np.ndarray, psi_b: np.ndarray) -> float:
    """Résonance cosinus entre deux ψ (0 = orthogonal, 1 = identique)."""
    return float(np.real(np.dot(np.conj(psi_a), psi_b)))


# ═══════════════════════════════════════════════════════════════════
# BASE DE MALADIES
# ═══════════════════════════════════════════════════════════════════

class KACare:
    """Moteur de diagnostic médical par résonance harmonique."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 
                                   "data", "ka_care_diseases.json")
        
        with open(db_path, "r", encoding="utf-8") as f:
            self.db = json.load(f)
        
        # Pré-encoder toutes les maladies
        self._maladies = {}
        for nom, data in self.db["maladies"].items():
            symptomes_texte = " ".join(data["symptomes"])
            self._maladies[nom] = {
                "psi": encode(symptomes_texte),
                "symptomes": data["symptomes"],
                "gravite": data["gravite"],
                "urgence": data["urgence"],
                "conduite": data["conduite"],
                "delai_consultation": data["delai_consultation"],
            }
    
    def diagnostiquer(self, symptomes: str) -> dict:
        """Diagnostic complet à partir d'une description de symptômes.
        
        Args:
            symptomes: texte libre décrivant les symptômes
        
        Returns:
            dict avec diagnostic principal, différentiels, confiance, alerte
        """
        # Encoder les symptômes du patient
        psi_patient = encode(symptomes)
        
        # Calculer la résonance avec chaque maladie
        scores = []
        for nom, data in self._maladies.items():
            score = resonance(psi_patient, data["psi"])
            scores.append({
                "maladie": nom.replace("_", " "),
                "score": round(score, 4),
                "confiance": self._score_to_confiance(score),
                "gravite": data["gravite"],
                "urgence": data["urgence"],
                "conduite": data["conduite"],
                "delai": data["delai_consultation"],
                "symptomes_attendus": data["symptomes"],
            })
        
        # Trier par score décroissant
        scores.sort(key=lambda x: -x["score"])
        
        # Détails de résonance par symptôme attendu
        details = []
        if scores:
            top = scores[0]
            for s in top["symptomes_attendus"][:5]:
                psi_s = encode(s)
                r = resonance(psi_patient, psi_s)
                details.append({"symptome": s, "resonance": round(r, 4)})
        
        return {
            "diagnostic_principal": scores[0] if scores else None,
            "diagnostics_différentiels": scores[1:5] if len(scores) > 1 else [],
            "tous_les_scores": scores,
            "details_resonance": details,
            "alerte": scores[0]["urgence"] if scores else False,
            "nb_maladies_testees": len(scores),
        }
    
    def _score_to_confiance(self, score: float) -> str:
        if score > 0.8:
            return "TRÈS ÉLEVÉE"
        elif score > 0.6:
            return "ÉLEVÉE"
        elif score > 0.4:
            return "MODÉRÉE"
        elif score > 0.2:
            return "FAIBLE"
        else:
            return "TRÈS FAIBLE"
    
    @property
    def nb_maladies(self) -> int:
        return len(self._maladies)
    
    def liste_maladies(self) -> list:
        return sorted(self._maladies.keys())


# ═══════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    care = KACare()
    print(f"🏥 KA Care — {care.nb_maladies} pathologies chargées\n")
    
    tests = [
        "fièvre, toux sèche, fatigue, perte d odorat",
        "douleur thoracique, essoufflement, sueurs froides, nausées",
        "nez bouché, éternuements, mal de gorge léger",
        "paralysie du visage, difficulté à parler, perte d équilibre",
        "diarrhée, vomissements, douleurs abdominales",
    ]
    
    for symptomes in tests:
        r = care.diagnostiquer(symptomes)
        d = r["diagnostic_principal"]
        print(f"Patient : \"{symptomes}\"")
        print(f"  → {d['maladie']} (score: {d['score']:.3f}, confiance: {d['confiance']})")
        if d["urgence"]:
            print(f"  🚨 URGENCE : {d['conduite']}")
        else:
            print(f"  ✓ {d['conduite'][:60]}...")
        print()
