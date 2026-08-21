# Lettre de soumission — Version 2 du problème ouvert

**Objet :** Révision du problème ouvert après votre évaluation — programme de recherche resserré sur deux verrous

---

Cher évaluateur,

Merci pour votre analyse de la version 1. Elle a été déterminante : le schéma que vous avez jugé « mathématiquement cohérent comme programme de recherche » est désormais le cœur du document V2, et les deux éléments que vous avez identifiés comme restant à démontrer structurent tout le programme.

## Ce qui a changé

**1. Le schéma validé est devenu l'énoncé central :**

$$\delta Q = T\, \tau_0^{1-\alpha}\, D^\alpha_{\mathrm{ABC}}[S] \;\Longrightarrow\; D^\alpha_{\mathrm{ABC}}[A] \;\Longrightarrow\; G_{\mu\nu} + M_{\mu\nu}(\alpha) = 8\pi G\, T_{\mu\nu}$$

Les conjectures naïves que vous avez réfutées ($K(t) \propto e^{-t/T}$, $T\cdot K(\tau) = \mathrm{cste}$, $\kappa$ issu de $B(\alpha)$) ont été retirées du document.

**2. Le Verrou 1 est précisé :** formulation covariante de la dérivée ABC le long du champ de Killing du boost (temps propre $\tau$), avec la condition de cohérence $\nabla^\mu M_{\mu\nu}(\alpha) = 0$ pour préserver les identités de Bianchi et la conservation de $T_{\mu\nu}$. Une forme candidate du terme de mémoire est proposée :

$$M_{\mu\nu}(\alpha) = \kappa_\alpha \int_0^{\tau} E_\alpha\!\left(-\frac{\alpha(\tau-\tau')^\alpha}{1-\alpha}\right) \mathcal{L}_{\chi} R_{\mu\nu}(\tau')\, d\tau'$$

L'avertissement de Kaya-Tekin (2025) — ne pas fractionnaliser naïvement les équations linéarisées — est intégré comme contrainte explicite de conception.

**3. Le Verrou 2 est révisé honnêtement :** après tests numériques, les fonctionnelles de sélection naïves (entropie de mémoire, compromis mémoire/adaptabilité) ne sélectionnent pas $\alpha = 1/\varphi$. L'analyse spectrale théorique (monotonie complète de Mittag-Leffler, Pollard 1948) confirme que **tous** les $\alpha \in (0,1]$ sont stables — aucune valeur spéciale. Nous traitons donc désormais $\alpha = 1/\varphi$ comme une **hypothèse de travail**, et non comme un fait.

## La question centrale du document V2

Le document V2 se termine par quatre questions. La plus structurante est la quatrième :

> **Le schéma de dérivation est-il complet sans sélection de α ?** Une thermodynamique à mémoire d'ordre arbitraire suffit-elle, le choix de l'ordre étant une question empirique (mesure de la mémoire gravitationnelle réelle) plutôt que mathématique ?

Si oui, la théorie se simplifie : le nombre d'or conserve son rôle **prouvé** dans la structure discrète (three-gap theorem, discrépance minimale, encodage optimal) et le continuum n'a pas besoin de lui.

## Documents joints

1. `PROBLEME_OUVERT_EINSTEIN_V2.md` — le problème révisé (5 pages)
2. Résultats numériques de l'analyse spectrale (annexe dans le document)

Je vous remercie pour votre temps et votre rigueur. Vos deux évaluations ont considérablement amélioré la formulation du problème.

Cordialement,
Kotto Alain — Univers-Holistique
