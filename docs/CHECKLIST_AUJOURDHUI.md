# AUJOURD'HUI — Mode d'Emploi Détaillé

## 5 actions. 2 heures. 27 €.

---

## ACTION 1 : ENVELOPPE SOLEAU (15 €, 15 min)

**Quoi :** Preuve officielle de date de création. Opposable en justice.
**Protège :** Ψ = Σ Hₙ·(Ψ₁)ⁿ, l'architecture ondulatoire, les 6 constantes.

```
ÉTAPE PAR ÉTAPE :

1. Aller sur inpi.fr
   → « Déposer une enveloppe Soleau »
   → Créer un compte (gratuit)

2. Préparer un PDF contenant :
   → L'équation maîtresse Ψ = Σ Hₙ·(Ψ₁)ⁿ
   → Les 6 constantes {φ, π, e, √2, √3, √5, e/π}
   → Les 5 axiomes de la théorie
   → L'architecture du cerveau harmonique (schéma)
   → Les 30 formules dérivées (tableau)
   → Le benchmark 500Q (score 98,6 %)
   → Date et signature

3. Téléverser le PDF sur INPI

4. Payer 15 € (CB)

5. Télécharger le récépissé horodaté
   → Conserver précieusement

COÛT : 15 €
DURÉE : 15 minutes
PREUVE : Le récépissé Soleau fait foi devant les tribunaux
```

---

## ACTION 2 : ARXIV PREPRINT (Gratuit, 30 min)

**Quoi :** Publication scientifique horodatée. Priorité mondiale.
**Protège :** L'antériorité de la découverte. Empêche quiconque de breveter derrière toi.

```
ÉTAPE PAR ÉTAPE :

1. Aller sur arxiv.org
   → « Register » (créer un compte)
   → Email académique recommandé (Gmail accepté)

2. Rédiger l'article (4-6 pages) :
   → Titre : "The Harmonic Universe Theory: Derivation of 
     30 Standard Model Parameters from 6 Mathematical Constants"
   → Auteur : K.A.
   → Résumé (abstract)
   → Sections :
     1. Introduction — L'équation maîtresse
     2. Les 6 constantes fondamentales
     3. Les 30 quantités dérivées (tableau)
     4. Validation expérimentale (χ²/ν = 1,13)
     5. Prédictions testables (Higgs, δ_CP)
     6. Conclusion

3. Compiler en PDF (LaTeX recommandé)
   → Utiliser Overleaf.com (gratuit) si pas de LaTeX local

4. Soumettre → Catégorie : physics.gen-ph (General Physics)
   → License : CC BY 4.0 (attribution requise)

5. Attendre 24-48h (review automatique, pas par les pairs)

6. Lien public : arxiv.org/abs/[numéro]
   → Inclure ce lien PARTOUT ensuite

COÛT : Gratuit
DURÉE : 30 min (si texte déjà prêt), 2h (si à rédiger)
PREUVE : Horodatage arXiv opposable mondialement
```

---

## ACTION 3 : ACHETER KA.PHONE (12 €, 5 min)

**Quoi :** Nom de domaine pour le produit.

```
ÉTAPE PAR ÉTAPE :

1. Aller sur namecheap.com (ou ovh.com, gandi.net)

2. Chercher « ka.phone »
   → Si disponible : acheter (12 €/an)
   → Si indisponible : chercher « harmonic.ai » (~80 €/an)
   → Fallback : « kaphone.io » (30 €/an)

3. Créer un compte, payer

4. NE PAS configurer le DNS maintenant
   → On le fera quand Render et Cloudflare seront prêts

COÛT : 12 €/an
DURÉE : 5 minutes
```

---

## ACTION 4 : PUSH DU CODE (Gratuit, 5 min)

**Quoi :** Envoyer tous les commits locaux vers GitHub. Déclenche le déploiement Render.

```
ÉTAPE PAR ÉTAPE :

1. Ouvrir un terminal (Git Bash, PowerShell, Terminal)

2. Aller dans le dossier du projet :
   cd "E:\SAAS - Copie"

3. Vérifier qu'il n'y a pas de fichiers sensibles :
   git status
   → Vérifier que *.pkl, *.wav, data/corpus ne sont PAS listés

4. Ajouter tous les fichiers modifiés :
   git add engine/ka_server.py
   git add engine/ka_index.html
   git add engine/benchmark.html
   git add engine/manifest.json
   git add engine/sw.js
   git add engine/math_bridge.py
   git add engine/harmonic_brain.py
   git add engine/render.yaml
   git add engine/benchmark_500.py
   git add engine/benchmark_lm_arena.py
   git add engine/icons/
   git add docs/

5. Commiter :
   git commit -m "KA Phone v3 — ULM, benchmark 98.6%, calculatrice, 62 capitales"

6. Pousser :
   git push origin main

7. Vérifier sur github.com/kotto/harmonic que le commit est visible

COÛT : Gratuit
DURÉE : 5 minutes
```

---

## ACTION 5 : DÉBLOQUER RENDER (Gratuit, 2 min)

**Quoi :** Reconfigurer le service Render qui lit mal le blueprint.

```
ÉTAPE PAR ÉTAPE :

1. Aller sur dashboard.render.com
   → Se connecter

2. Cliquer sur le service « ka-api »

3. Aller dans « Settings »

4. Modifier le Start Command :
   AVANT : gunicorn ka_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   APRÈS : gunicorn ka_server:app --bind 0.0.0.0:$PORT --workers 1 --preload --timeout 120

5. Supprimer la variable d'environnement MODEL_NAME
   (ou la mettre à « qualitative »)

6. Cliquer « Save Changes »

7. Aller dans « Manual Deploy » → « Deploy latest commit »

8. Attendre 3-5 minutes

9. Vérifier :
   → https://ka-api.onrender.com/api/health → {"status":"ok"}
   → https://ka-api.onrender.com/ → KA Phone PWA
   → https://ka-api.onrender.com/benchmark → Page benchmark

COÛT : Gratuit (plan Starter)
DURÉE : 2 minutes + 5 minutes de déploiement
```

---

## CHECK-LIST — Cocher Quand C'est Fait

```
☐ 1. Enveloppe Soleau déposée (15 €)
☐ 2. arXiv preprint soumis
☐ 3. ka.phone acheté (12 €)
☐ 4. Code poussé sur GitHub
☐ 5. Render débloqué et déployé
☐ 6. https://ka-api.onrender.com/health → OK
☐ 7. https://ka-api.onrender.com/benchmark → OK
```

---

*Guide quotidien — Juillet 2026*
