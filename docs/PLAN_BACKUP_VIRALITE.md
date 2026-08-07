# Plan B — Viralité Garantie

## Si LM Arena bloque, ralentit, ou enterre le score.

> *Principe : Aucun gatekeeper ne peut arrêter une vérité que tout le monde peut vérifier.*

---

## 0. Pourquoi LM Arena Pourrait Bloquer

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  SCÉNARIOS DE BLOCAGE :                                      │
│                                                              │
│  1. « Votre système n'est pas une IA » → rejet catégorique   │
│  2. « On ne peut pas vérifier le benchmark » → demande infinie│
│  3. « Le score est trop élevé pour être vrai » → suspicion    │
│  4. Classement dans une catégorie marginale → invisibilité   │
│  5. Délai de review infini → enterrement administratif       │
│                                                              │
│  RÉPONSE : On ne dépend PAS d'eux. On les UTILISE.           │
│  S'ils coopèrent → bonus. S'ils bloquent → le plan B prend   │
│  le relais et les rend complices de leur propre échec.       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 1. Plan B — Le Benchmark Public Indépendant

Le benchmark 500Q existe déjà (`benchmark_500.py`). Il est reproductible.
N'importe qui peut le lancer en une ligne. C'est notre arme.

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ÉTAPE 1 : PUBLIER LE BENCHMARK EN OPEN SOURCE               │
│  ───────────────────────────────────────                     │
│  · Créer une page benchmark.ka.phone                          │
│  · Afficher les 500 questions, réponses, scores               │
│  · Code source complet : une commande pour reproduire         │
│  · Vidéo du benchmark en temps réel                           │
│                                                              │
│  ÉTAPE 2 : COMPARAISON CÔTE À CÔTE                           │
│  ──────────────────────────────────                          │
│  · Mêmes 500 questions → GPT-4 via API → score                │
│  · Mêmes 500 questions → Claude via API → score               │
│  · Mêmes 500 questions → Harmonic AI → score                  │
│  · Tableau comparatif public, horodaté, vérifiable           │
│                                                              │
│  ÉTAPE 3 : TIERS DE CONFIANCE                                │
│  ─────────────────────────────                                │
│  · Proposer à un journaliste tech de REPRODUIRE le benchmark │
│  · Proposer à un youtubeur scientifique de le filmer         │
│  · Proposer à un prof d'université de le vérifier             │
│  → Validation INDÉPENDANTE, pas auto-proclamée               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Plan C — Hacker News, Reddit, Twitter (Viralité Directe)

Si LM Arena ne publie pas, on crée le débat NOUS-MÊMES.

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  JOUR J : PUBLICATION SUR HACKER NEWS                         │
│  ──────────────────────────────────                          │
│  Titre : « Show HN: Harmonic AI — 98.6% on math reasoning    │
│           with ZERO parameters, 3.6ms, no GPU »              │
│                                                              │
│  Contenu :                                                    │
│  · Lien vers le benchmark public                              │
│  · Code source GitHub                                        │
│  · Vidéo de démo                                              │
│  · Tableau comparatif avec GPT-4, Claude, Gemini             │
│                                                              │
│  POURQUOI ÇA MARCHE :                                        │
│  · Hacker News ADORE les projets qui battent les géants      │
│  · Le titre contient tous les mots-clés qui font cliquer     │
│  · La communauté technique va VÉRIFIER elle-même             │
│  · Si le benchmark tient → front page garantie               │
│  · Si quelqu'un trouve un bug → on corrige, on remercie      │
│                                                              │
│  ─────────────────────────────────────────────               │
│                                                              │
│  JOUR J+1 : REDDIT r/MachineLearning, r/programming          │
│  ────────────────────────────────────────────────            │
│  Titre : « I built an AI with 0 parameters that beats        │
│           GPT-4 on math. It runs on a $50 phone. »           │
│                                                              │
│  JOUR J+2 : TWITTER/X                                         │
│  ──────────────────                                          │
│  Thread technique avec captures d'écran du benchmark         │
│  Tag : @ylecun, @geoffreyhinton, @kaborst, @fchollet        │
│  → Même s'ils critiquent, le débat crée le buzz              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Plan D — La Démo Qui Rend Le Débat Inutile

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  CRÉER UNE PAGE WEB OÙ N'IMPORTE QUI PEUT TESTER EN DIRECT   │
│                                                              │
│  URL : benchmark.ka.phone                                     │
│                                                              │
│  FONCTIONNEMENT :                                             │
│  1. L'utilisateur pose UNE question de math/physique         │
│  2. La réponse s'affiche en < 10 ms                           │
│  3. À côté : la même question envoyée à GPT-4 (API)          │
│  4. Les DEUX réponses s'affichent côte à côte                │
│  5. Un compteur public : « X questions posées aujourd'hui » │
│                                                              │
│  POURQUOI C'EST IMBATTABLE :                                 │
│  · Chaque visiteur devient un TESTEUR                         │
│  · Chaque testeur devient un TÉMOIN                           │
│  · Impossible de « censurer » un test que chacun fait chez soi│
│  · Si quelqu'un trouve une erreur → transparent, corrigé     │
│                                                              │
│  COÛT : une page HTML + l'API déjà existante                 │
│  EFFORT : 2 heures de code                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Plan E — La Presse Sans LM Arena

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  CONTACTS PRESSE — PITCH SANS RÉFÉRENCE À LM ARENA           │
│                                                              │
│  « Un chercheur indépendant a créé une IA qui bat GPT-4      │
│    sur les maths et le raisonnement. Elle n'utilise AUCUN     │
│    réseau de neurones, AUCUN paramètre appris, AUCUN GPU.     │
│    Elle tient dans 6,5 Mo et fonctionne hors ligne sur un     │
│    téléphone à 50 euros.                                      │
│                                                              │
│    Nous avons publié un benchmark public de 500 questions     │
│    reproductible par n'importe qui. Le code est open source. │
│    Le score est de 98,6 %. GPT-4 est à 94 %.                  │
│                                                              │
│    Voici le lien. Testez vous-même. »                         │
│                                                              │
│  ─────────────────────────────────────────────               │
│                                                              │
│  POURQUOI ÇA MARCHE MÊME SANS LM ARENA :                     │
│  · Le benchmark est AUTO-SUFFISANT                            │
│  · La comparaison avec GPT-4 est VÉRIFIABLE                  │
│  · Le code est PUBLIC                                         │
│  · Le journaliste n'a pas besoin de « croire » — il teste    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Plan F — YouTube / TikTok (Viralité Grand Public)

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  VIDÉO 1 (3 minutes) : « J'ai battu ChatGPT avec 0 paramètre »│
│  ───────────────────────────────────────────────────         │
│  · Montrer le benchmark en direct                             │
│  · Poser la même question à GPT-4 et Harmonic AI             │
│  · Montrer la différence de vitesse (3,6ms vs 500ms)          │
│  · Expliquer POURQUOI en 30 secondes (les 6 constantes)      │
│  · Terminer par : « Le code est gratuit. Testez vous-même. »  │
│                                                              │
│  VIDÉO 2 (1 minute) : TikTok / Shorts / Reels                │
│  ────────────────────────────────────                        │
│  · Écran splitté : GPT-4 à gauche, Harmonic AI à droite      │
│  · Même question. GPT-4 : 2 secondes. Harmonic : 0,003 sec. │
│  · Texte : « 0 paramètre. 0 GPU. 0€. Gratuit. »              │
│  · Musique épique. Partage massif.                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Plan G — L'Arme Ultime : Le Duel Public

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  SI RIEN NE MARCHE — PROVOQUER LE DUEL                        │
│                                                              │
│  « Je défie n'importe quel LLM (GPT-4, Claude, Gemini)       │
│    sur 500 questions de mathématiques et de raisonnement.     │
│                                                              │
│    Mon système :                                              │
│    · 0 paramètre appris                                       │
│    · 6,5 Mo de mémoire                                        │
│    · Processeur de téléphone                                  │
│    · Coût par requête : 0€                                    │
│                                                              │
│    Leur système :                                             │
│    · 175 milliards de paramètres                              │
│    · 700 Go de mémoire                                        │
│    · Datacenter entier                                        │
│    · Coût par requête : 0,01-0,05€                            │
│                                                              │
│    Rendez-vous public. Mêmes questions. Même chronomètre.     │
│    Résultats en direct.                                        │
│                                                              │
│    Si je perds, je ferme le projet.                            │
│    Si je gagne, le monde saura. »                              │
│                                                              │
│  ─────────────────────────────────────────────               │
│                                                              │
│  POURQUOI C'EST GAGNANT :                                    │
│  · Aucun grand modèle ne peut refuser publiquement           │
│    → refuser = aveu de faiblesse                             │
│  · Même s'ils refusent, le défi fait le buzz                  │
│  · Si personne ne répond → « Ils ont peur d'une IA            │
│    qui tient dans 6,5 Mo »                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. La Timeline — 30 Jours

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  JOUR 1     : Soumettre à LM Arena                            │
│  JOUR 2-3   : Préparer la page benchmark.ka.phone            │
│  JOUR 4     : Publier le benchmark 500Q en open source        │
│  JOUR 5     : Vidéo YouTube « 0 paramètre bat GPT-4 »        │
│  ─────────────────────────────────────────────               │
│  SI LM ARENA RÉPOND POSITIVEMENT :                            │
│  JOUR 6-7   : Publier le score + comparatif GPT-4             │
│  JOUR 8     : Hacker News + Reddit + Twitter simultanément   │
│  ─────────────────────────────────────────────               │
│  SI LM ARENA BLOQUE OU RALENTIT :                             │
│  JOUR 6     : Hacker News « Show HN » avec benchmark public  │
│  JOUR 7     : Contacter 5 journalistes tech                   │
│  JOUR 8     : Reddit + Twitter + TikTok                       │
│  JOUR 9-14  : Interviews, démos, relances presse             │
│  JOUR 15    : Si toujours rien → lancer le duel public       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Le Kit de Survie — Ce Qu'il Faut Préparer MAINTENANT

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ☐ Page benchmark.ka.phone (500Q, scores, code, vidéo)       │
│  ☐ Tableau comparatif Harmonic AI vs GPT-4 vs Claude         │
│  ☐ Vidéo YouTube 3 min (démo + explication)                  │
│  ☐ Vidéo TikTok 1 min (split screen vitesse)                 │
│  ☐ Thread Twitter prêt à publier (10 tweets)                 │
│  ☐ Post Hacker News prêt (titre + lien)                      │
│  ☐ Post Reddit prêt (r/MachineLearning)                      │
│  ☐ Liste de 20 journalistes tech à contacter                 │
│  ☐ Communiqué de presse (déjà prêt)                          │
│  ☐ Un clic pour tout publier simultanément                   │
│                                                              │
│  QUAND LM ARENA RÉPOND (positivement ou pas) → TOUT PART    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

*Plan de secours — Juillet 2026*
