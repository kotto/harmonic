#!/usr/bin/env python3
"""
INGESTION AUTO — Batch continu sans intervention
=================================================
Continue l'ingestion massive automatiquement jusqu'à l'objectif.
Reprend au checkpoint, sauvegarde périodiquement, objectifs progressifs.

Objectifs : 1M → 5M → 10M → 50M → 100M tokens

Usage :
  python ingestion_auto.py                    # Continue jusqu'à l'objectif défini
  python ingestion_auto.py --target 5000000   # Objectif personnalisé (5M)
  python ingestion_auto.py --status           # Voir progression
  python ingestion_auto.py --forever          # Tourne indéfiniment
"""

import os, sys, time, signal, json, argparse
import numpy as np
from datetime import datetime

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)
from ka_reasoning_engine import KAReasoningEngine

BASE_DIR = os.path.join(_project_root, "ka_knowledge_base")
HOLOGRAMME_FILE = os.path.join(BASE_DIR, "hologramme.npy")
PROGRESS_FILE = os.path.join(BASE_DIR, "auto_progress.json")

# =========================================================================
# GÉNÉRATEUR INFINI DE CONNAISSANCES
# =========================================================================

BATCHS = [
    # Médecine spécialisée
    [
        "L endocrinologie etudie les hormones et les glandes endocrines. La thyroide produit la thyroxine T4 et la triiodothyronine T3 regulant le metabolisme. Le pancreas endocrine produit l insuline et le glucagon regulant la glycemie. Les surrenales produisent le cortisol et l adrenaline.",
        "La nephrologie traite les maladies du rein. La dialyse supplee la fonction renale defaillante. La transplantation renale est le traitement de l insuffisance renale terminale. La creatinine serique est un marqueur de la fonction renale.",
        "L hematologie etudie le sang et ses maladies. Les globules rouges transportent l oxygene via l hemoglobine. Les globules blancs defendent l organisme. Les plaquettes assurent la coagulation.",
        "La pneumologie traite les maladies pulmonaires. La BPCO est liee au tabagisme. L embolie pulmonaire est une urgence vitale. La fibrose pulmonaire idiopathique est une maladie rare et grave.",
        "La gastroenterologie traite le tube digestif. L ulcere gastroduodenal est souvent lie a Helicobacter pylori. La maladie de Crohn et la rectocolite hemorragique sont des maladies inflammatoires chroniques intestinales.",
        "L hepatologie etudie le foie. La cirrhose est une fibrose hepatique avancee. Les hepatites virales A B C D et E sont des causes majeures de maladie hepatique. Le carcinome hepatocellulaire est le cancer primitif du foie.",
    ],
    # Ingénierie et sciences appliquées
    [
        "L ingenierie civile concoit et construit les infrastructures. Le beton arme associe beton et acier pour la resistance. Les ponts suspendus franchissent de grandes portees. Les barrages regulent les cours d eau et produisent de l electricite.",
        "L ingenierie mecanique etudie les machines et les systemes mecaniques. La thermodynamique appliquee optimise les moteurs thermiques. La mecanique des fluides analyse les ecoulements. La resistance des materiaux predit les deformations.",
        "L ingenierie electrique traite de l electricite et de l electromagnetisme. Les transformateurs modifient la tension electrique. Les moteurs electriques convertissent l electricite en mouvement. Les generateurs produisent l electricite.",
        "L ingenierie aeronautique concoit les avions et les helicopteres. L aerodynamique etudie les ecoulements d air autour des profils. La portance est generee par la difference de pression entre l extrados et l intrados de l aile.",
        "L ingenierie chimique transforme la matiere a l echelle industrielle. La distillation separe les constituants d un melange liquide. La catalyse accelere les reactions chimiques. Les reacteurs chimiques optimisent la production.",
        "L ingenierie nucleaire exploite l energie du noyau atomique. Les reacteurs a eau pressurisee REP sont les plus repandus. Le combustible nucleaire est enrichi en uranium 235. La surete nucleaire est fondee sur le concept de defense en profondeur.",
    ],
    # Sciences humaines et sociales
    [
        "L anthropologie etudie l homme dans toutes ses dimensions. L anthropologie culturelle analyse les croyances les rites et les coutumes. L anthropologie physique etudie l evolution biologique de l homme. L ethnographie decrit les societes humaines.",
        "La demographie etudie les populations humaines. La natalite mesure le nombre de naissances. La mortalite mesure le nombre de deces. Le solde migratoire est la difference entre les entrees et les sorties d un territoire.",
        "La criminologie etudie le phenomene criminel. La criminologie classique met l accent sur le libre arbitre. La criminologie positiviste recherche les causes biologiques et sociales. La prevention situationnelle reduit les opportunites criminelles.",
        "Les sciences de l education etudient les processus d enseignement et d apprentissage. La pedagogie differenciee adapte l enseignement aux besoins de chaque eleve. L evaluation formative accompagne l apprentissage sans le sanctionner.",
        "La science politique analyse les phenomenes politiques. Les regimes politiques sont classes selon la separation des pouvoirs. Les partis politiques structurent la competition electorale. Les lobbies influencent les decisions publiques.",
        "Les relations internationales etudient les interactions entre Etats. Le realisme met l accent sur la puissance et les interets nationaux. Le liberalisme privilegie la cooperation et les institutions internationales. Le constructivisme souligne le role des idees et des normes.",
    ],
    # Culture et civilisation
    [
        "La mythologie grecque raconte les aventures des dieux et des heros. Zeus regne sur l Olympe. Hercule accomplit douze travaux legendaires. L Odyssee d Homere narre le retour d Ulysse apres la guerre de Troie.",
        "La philosophie chinoise est marquee par Confucius et Lao Tseu. Le confucianisme met l accent sur l ethique et l harmonie sociale. Le taoisme prone le non agir wu wei et l harmonie avec la nature. Le legalisme privilegie la loi et l ordre.",
        "L art medieval europeen est essentiellement religieux. Les enluminures decorent les manuscrits. Les fresques ornent les eglises romanes. Les vitraux des cathedrales gothiques racontent la Bible aux fideles illettres.",
        "Le baroque aux XVIIe et XVIIIe siecles se caracterise par l exces et le mouvement. Le Bernin sculpta l Extase de sainte Therese. Le chateau de Versailles incarne le baroque francais. La musique baroque atteint son apogee avec Bach et Haendel.",
        "Le romantisme au XIXe siecle exalta les sentiments et la nature. Delacroix peignit La Liberte guidant le peuple. Victor Hugo ecrivit Les Miserables et Notre Dame de Paris. Beethoven ouvrit la voie du romantisme musical.",
        "L art moderne au XXe siecle rompt avec la figuration. Le cubisme de Picasso decomposa les formes. Le surrealisme de Dali explora l inconscient. L abstraction de Kandinsky supprima toute reference au reel.",
    ],
    # Écologie et environnement
    [
        "La biodiversite designe la variete du vivant a tous les niveaux. La diversite genetique est la variabilite au sein d une espece. La diversite specifique est le nombre d especes dans un ecosysteme. La diversite ecosystemique est la variete des habitats.",
        "Les energies renouvelables sont issues de sources inepuisables. L energie solaire photovoltaique convertit la lumiere en electricite. L energie eolienne exploite la force du vent. La biomasse valorise les dechets organiques.",
        "La gestion des dechets vise a reduire leur impact environnemental. Le recyclage revalorise les materiaux. Le compostage transforme les dechets organiques en amendement. L incineration produit de l energie a partir des dechets.",
        "La preservation des oceans est un enjeu mondial. Les aires marines protegees limitent les activites humaines. La surpeche epuise les stocks de poissons. La pollution plastique contamine les ecosystemes marins.",
        "L agriculture durable concilie production et environnement. L agroecologie s inspire du fonctionnement des ecosystemes. La permaculture concoit des systemes agricoles resilients. L agriculture de conservation preserve les sols.",
        "La foret joue un role crucial dans la regulation du climat. Les forets tropicales abritent la majorite de la biodiversite terrestre. La deforestation libere du CO2 dans l atmosphere. Le reboisement restaure les ecosystemes forestiers.",
    ],
    # Mathématiques et logique avancées
    [
        "L algebre lineaire etudie les espaces vectoriels et les applications lineaires. Une matrice est un tableau de nombres. Le determinant mesure l amplification du volume par une transformation lineaire. Les valeurs propres caracterisent une matrice.",
        "La theorie des probabilites modelise les phenomenes aleatoires. La loi normale ou gaussienne est omnipresente dans la nature. Le theoreme central limite justifie son importance. La loi de Poisson modelise les evenements rares.",
        "La topologie etudie les proprietes invariantes par deformation continue. Un espace topologique est defini par une collection d ouverts. La connexite signifie qu un espace est d un seul tenant. La compacite generalise la notion de ferme borne.",
        "L analyse fonctionnelle etudie les espaces de fonctions. Les espaces de Banach sont des espaces vectoriels normes complets. Les espaces de Hilbert sont munis d un produit scalaire. Les operateurs lineaires generalisent les matrices.",
        "La theorie des graphes modelise des reseaux de relations. Un graphe est un ensemble de sommets relies par des aretes. Le probleme du voyageur de commerce cherche le plus court chemin visitant toutes les villes. Les graphes sont utilises en informatique et en logistique.",
        "La cryptographie securise les communications. Le chiffrement symetrique utilise une cle unique pour chiffrer et dechiffrer. Le chiffrement asymetrique utilise une paire de cles publique et privee. Le protocole Diffie Hellman permet l echange securise de cles.",
    ],
    # Sport, santé et bien-être
    [
        "La nutrition etudie les besoins alimentaires de l organisme. Les macronutriments sont les glucides les lipides et les proteines. Les micronutriments sont les vitamines et les mineraux. L equilibre alimentaire est essentiel a la sante.",
        "La physiologie de l exercice etudie les adaptations de l organisme a l effort. Le VO2 max mesure la capacite aerobie maximale. La filiere anaerobie lactique produit de l energie sans oxygene. L entrainement ameliore les performances.",
        "Le sommeil est essentiel a la recuperation et a la memoire. Le sommeil paradoxal est celui des reves. Le sommeil lent profond est reparateur. L insomnie affecte la qualite de vie et la sante.",
        "La gestion du stress est un enjeu de sante publique. Le stress chronique augmente le risque de maladies cardiovasculaires. La meditation de pleine conscience reduit l anxiete. L activite physique est un antistress naturel.",
        "La sante publique vise a ameliorer la sante des populations. La vaccination a eradique la variole et reduit la polio. La prevention reduit l incidence des maladies chroniques. L education a la sante responsabilise les citoyens.",
    ],
]

# =========================================================================
# GESTIONNAIRE D'INGESTION AUTOMATIQUE
# =========================================================================

class IngestionAuto:
    def __init__(self, target: int = 5_000_000):
        self.target = target
        self.hologramme_file = HOLOGRAMME_FILE
        self.progress_file = PROGRESS_FILE
        self.interrompu = False
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)
    
    def _stop(self, *args):
        self.interrompu = True
        print("\n⏸️  Arrêt demandé. Sauvegarde en cours...")
    
    def run(self):
        engine = KAReasoningEngine(mode="harmonic")
        if os.path.exists(self.hologramme_file):
            engine.bridge.monde.H = np.load(self.hologramme_file)
        
        total_tokens = engine.bridge.monde.n_experiences
        t0 = time.time()
        batch_idx = 0
        
        print(f"Démarrage | Objectif: {self.target:,} | Départ: {total_tokens:,} tokens")
        print("=" * 60)
        
        while total_tokens < self.target and not self.interrompu:
            batch = BATCHS[batch_idx % len(BATCHS)]
            self._show_status(total_tokens, t0)
            
            for texte in batch:
                if self.interrompu: break
                for _ in range(200):
                    engine.bridge.apprendre(texte, amplitude=0.5)
                    total_tokens += len(texte.split())
                    if total_tokens >= self.target: break
                if self.interrompu or total_tokens >= self.target: break
            
            batch_idx += 1
            
            if batch_idx % 5 == 0:
                np.save(self.hologramme_file, engine.bridge.monde.H)
                self._autosave(total_tokens)
        
        np.save(self.hologramme_file, engine.bridge.monde.H)
        dt = time.time() - t0
        print(f"\n{'='*60}")
        print(f"{'Terminé' if not self.interrompu else 'Interrompu'} | {total_tokens:,} tokens | {dt/60:.0f}min | E={engine.bridge.monde.energie():.0f}")
    
    def _show_status(self, tokens, t0):
        pct = min(tokens / self.target * 100, 100)
        b = '#' * int(pct / 2) + '-' * (50 - int(pct / 2))
        eta = (time.time() - t0) / max(tokens - 1_000_000, 1) * (self.target - tokens) / 60
        print(f"[{b}] {tokens:,}/{self.target:,} ({pct:.0f}%) | ETA:{eta:.0f}min")
    
    def _autosave(self, tokens):
        with open(self.progress_file, 'w') as f:
            json.dump({"tokens": tokens, "timestamp": datetime.now().isoformat()}, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=5_000_000, help="Objectif en tokens (defaut: 5M)")
    parser.add_argument("--status", action="store_true", help="Afficher progression")
    parser.add_argument("--forever", action="store_true", help="Tourner indefiniment")
    args = parser.parse_args()
    
    if args.status:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE) as f:
                d = json.load(f)
            print(f"Progression: {d.get('tokens',0):,} tokens ({d.get('timestamp','?')})")
        return
    
    target = 999_999_999 if args.forever else args.target
    IngestionAuto(target=target).run()


if __name__ == "__main__":
    main()