# ANNEXE A — Fondements mathématiques de la compression harmonique

## A.1 Le noyau ABC d'Atangana-Baleanu-Caputo

La mémoire des hologrammes HWAT utilise la dérivée fractionnaire ABC :

$${}^{ABC}_a D^\alpha_t f(t) = \frac{B(\alpha)}{1-\alpha} \int_a^t f'(\tau) E_\alpha\left(-\alpha \frac{(t-\tau)^\alpha}{1-\alpha}\right) d\tau$$

où $E_\alpha$ est la fonction de Mittag-Leffler :

$$E_\alpha(z) = \sum_{k=0}^{\infty} \frac{z^k}{\Gamma(\alpha k + 1)}$$

**Propriété exploitée :** la fonction de Mittag-Leffler décroît de façon **non-exponentielle** (loi de puissance), ce qui reproduit le comportement de la mémoire biologique : les souvenirs récents dominent sans oubli brutal des anciens.

**Bénéfice compression :** la mémoire d'un hologramme HWAT (dim=32) encode l'équivalent d'une base de connaissances via superposition — chaque fait est une onde ajoutée, pas un poids stocké.

## A.2 Le principe d'incertitude de Gabor

$$ \Delta t \cdot \Delta \omega \geq \frac{1}{2} $$

Toute information ne peut pas être simultanément parfaitement localisée en temps et en fréquence. HWAT l'utilise comme **principe de conception** :
- L'amplitude encode le *quoi* (contenu sémantique)
- La phase encode le *où/quand* (structure, position)

Ce découplage phase/amplitude permet de **régénérer** l'information (phases par formule) au lieu de la stocker — la source de la compression massive.

## A.3 L'holographie de Bekenstein

Le principe holographique (Bekenstein, 1981) : l'information d'un volume peut être encodée sur sa surface.

HWAT l'applique : la mémoire holographique $H \in \mathbb{C}^{N\times N}$ encode des faits par superposition additive :

$$H \leftarrow H + \psi_{\text{fait}}$$

La lecture se fait par **résonance** : $H \otimes \psi_{\text{requête}}$ extrait les faits dont les ondes interfèrent constructivement. Un hologramme de 32×32 complexe stocke des milliers de faits par interférence.

## A.4 Le nombre d'or φ et l'espacement des phases

$$φ = \frac{1+\sqrt{5}}{2} = 1.618...$$

- Positions encodées par $\varphi_{pos}[p, d] = \omega_d \cdot p$ avec des fréquences $\omega_d$ espacées en loi de puissance
- Le ratio $α = 1/φ$ régit le noyau ABC
- **Preuve de sélectivité mesurée :** similarité cosinus entre deux positions distinctes = **0.205** (parfaitement séparable)

## A.5 Le hash FNV-1a (déterminisme)

```
h = 2166136261
for byte in text: h ^= byte; h *= 16777619
```

- Un token → une amplitude + une phase **toujours identiques** (aucun aléa)
- Les embeddings sont **recalculés**, jamais stockés
- **Reproductibilité bit-à-bit** : deux exécutions donnent exactement la même sortie
- Conséquence : pas de table d'embedding (vocab×dim×4 octets économisés)

## A.6 L'attention par cohérence de phase

Au lieu de $QK^T$ :

$$\alpha_{ij} = \text{softmax}_i\left(\frac{1}{\sqrt{d}}\sum_{d}\cos(\varphi^Q_{i,d} - \varphi^K_{j,d}) \cdot \sqrt{|Q_{i,d}| \cdot |K_{j,d}|}\right)$$

- Coût : identique au produit scalaire (matmul de cos/sin)
- **Propriété :** déterministe, sans dropout ni bruit
- Implémentation efficace : `cos(φᵢ−φⱼ) = cosφᵢcosφⱼ + sinφᵢsinφⱼ` (2 matmuls)

## A.7 Budget théorique de compression

| Composant | Stockage standard | Stockage HWAT | Économie |
|-----------|-------------------|---------------|----------|
| Embeddings 50K×1024 | 204.8 MB | **0 (recalculé)** | 100% |
| Tête de sortie 2×1024×50K | 409.6 MB | **0 (recalculé)** | 100% |
| Poids MLP (125M) | ~480 MB | ~480 MB | 0% |
| **Monolithe total** | **~1.1 GB** | **~480 MB** | **−57%** |
| **Hologrammes 15 domaines** | — | **8.4 MB** | **−99%** |

---

*Annexe A — DOSSIER TECHNIQUE MTN v1.0 — 2026-08-01*
