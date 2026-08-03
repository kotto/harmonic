# 🚀 PLAN DE DIFFUSION — Le lancement en 3 vagues

## Prérequis (avant tout envoi)

1. **VPS public avec la démo** : `http://VOTRE_VPS:8765/defi-calcul` en
   ligne et stable (le lien du communiqué).
2. **La collecte LLM faite** : les réponses de GPT-4o / Claude sur les
   33 calculs (`benchmark_compare_llm.py --llm-api …`) — le comparatif
   avec les vrais chiffres LLM est plus fort que le tableau sans eux.
3. **Le site avec les liens de téléchargement** : Vital KA (gratuit),
   KA Mobile, KA Enterprise — le funnel du communiqué.
4. **Une adresse presse** : presse@ka-enterprise.fr (réponse < 24 h).

## Vague 1 — Les blogueurs tech (semaine 1)

Le test viral, zéro risque : ils créent l'élan, ils testent la démo.

- **Contenu** : le lien `/defi-calcul` + le post « L'IA qui ne se trompe
  jamais en calcul » (généré par `benchmark_compare_llm.py`).
- **Cibles** : blogueurs français tech et IA (YouTube, X, LinkedIn),
  les comptes « tech FR » ; puis Hacker News (titre : « An IA that
  refuses to hallucinate: 33/33 exact, 0 GPU, 0 trained parameters »).
- **Message** : le défi interactif, pas la théorie.

## Vague 2 — La presse économique et généraliste (semaines 2-3)

L'angle souveraineté + coût : la presse économique ne couvre pas les
benchmarks, elle couvre les histoires.

- **Dossier envoyé** : COMMUNIQUE_PRESSE.md + NARRATIF.md +
  COMPARATIF_CERTITUDE.md + FAQ_OBJECTIONS.md + PREUVES.md.
- **Cibles** : Les Échos (IA souveraine), Usine Digitale, Le Monde
  Informatique, Journal du Net, La Tribune, French Tech.
- **Angle** : « Une IA française à 20 €/mois qui défie le modèle des
  géants du GPU — données souveraines, zéro hallucination, déterministe ».
- **Offre** : une démo de 15 minutes avec leurs données ou le défi en
  direct.

## Vague 3 — La presse technique internationale (semaines 3-6)

Après les preuves et les premiers relais.

- **Cibles** : Ars Technica, The Register, TechCrunch, Hacker News
  (deuxième passage), la presse IA spécialisée.
- **Angle** : la thèse — « la génération est de la récupération
  vérifiée ; notre mémoire est lisible, nos réponses sont prouvées par
  exécution » + HumanEval 100 % par récupération + le langage chaîne
  GSM8K 99,2 %.
- **Préparation obligatoire** : la FAQ est leur premier réflexe — la
  transparence (GSM8K 1,6 % assumé) est notre bouclier.

## Le calendrier type

| Jour | Action |
|---|---|
| J0 | VPS de démo en ligne + collecte LLM + site à jour |
| J1-J7 | Blogueurs FR + Hacker News (vague 1) |
| J8-J21 | Dossier presse économique FR (vague 2) |
| J22-J45 | Presse technique internationale (vague 3) |
| Continu | Suivi des téléchargements (Vital KA = lead magnet) → essais Enterprise |

## Indicateurs de succès

- **Vague 1** : 10+ tests publics de la démo, 2-5 articles blogueurs.
- **Vague 2** : 2-3 articles presse FR (économie/tech).
- **Vague 3** : 1 article international (ou Hacker News front page).
- **Funnel** : 1 000+ visites sur le défi → 100+ téléchargements Vital KA
  → 5+ essais Enterprise.

## Les pièges

- Ne JAMAIS envoyer un communiqué sans la FAQ jointe — les journalistes
  appellent avec GSM8K en tête.
- Ne pas promettre de date pour la « généralisation GSM8K » — le
  chantier est ouvert, annoncé comme tel.
- Répondre à toute critique technique publiquement et avec les mesures —
  c'est la réputation qui se construit ici.
