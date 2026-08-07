# 🤝 KA Enterprise — Fiche partenaires hébergeurs (1 page)

## Ce que KA Enterprise vous apporte

1. **De la demande pour VOS VPS.** KA Enterprise tourne **uniquement sur le
   VPS du client** (votre infrastructure). Chaque installation = un VPS
   vendu, renouvelé, et de la bande passante consommée. Notre onboarding
   propose même « choisissez votre hébergeur ».
2. **Un argument de différenciation pour vos PME.** L'IA d'entreprise qui
   répond uniquement sur les données privées, sans hallucination, sans
   GPU, à partir de 49 €/mois : une raison concrète pour vos clients de
   prendre l'IA — là où les offres LLM leur font peur (coût, données chez
   un tiers).
3. **Un produit clé en main.** Installation automatisée en 1 clic
   (`deploy_provider.py` : API Hetzner, Scaleway — ou installation sur IP
   existante pour OVH et les autres), onboarding en 5 minutes, zéro
   maintenance de votre côté.
4. **Un usage intensif mais léger.** CPU seul, 2 vCPU / 4 Go suffisent —
   aucune charge GPU, aucun pic de facturation.

## Ce que nous demandons

| | |
|---|---|
| **Référencement** | KA Enterprise dans votre catalogue partenaires / marketplace de services |
| **Co-marketing** | 1 cas d'usage commun par trimestre (webinaire, article, démo) |
| **Aucune exclusivité** | le client garde le choix de son hébergeur |
| **Commission** | 10 % récurrent sur les licences des clients que vous apportez (tracking par code partenaire) |
| **Vos données** | jamais : les données clients restent sur vos serveurs, nous n'y avons pas accès |

## Ce que nous ne demandons PAS

- Pas d'investissement de votre part
- Pas d'intégration marketplace lourde (notre install est autonome)
- Pas d'accès à nos clients (nous vous amenons les vôtres)

## Déploiement — 3 minutes

```bash
# Hetzner (création automatique du VPS + installation)
python partners/deploy_provider.py --provider hetzner --token <VOTRE_TOKEN> \
    --ssh-key ~/.ssh/id_ed25519

# Scaleway (création automatique + installation)
python partners/deploy_provider.py --provider scaleway \
    --secret-key <SK> --project-id <ID> --ssh-key ~/.ssh/id_ed25519

# OVHcloud / autres (VPS existant → installation)
python partners/deploy_provider.py --ip <IP> --ssh-key ~/.ssh/id_ed25519
```

Résultat : `http://VOTRE_VPS:8767/onboard` — l'entreprise décrit son
environnement et son IA naît en 5 minutes.

## En 3 phrases

> Nous vendons de l'IA d'entreprise qui tourne sur VOTRE infrastructure.
> Vous vendez des VPS ; nous vendons la raison de les prendre. Zéro risque,
> zéro investissement, 10 % récurrent pour vous.

---

*Contact : partenaires@ka-enterprise.fr · Dossier sécurité : DOSSIER_SECURITE.md · Tarifs : demo_kit/FICHE_TARIFAIRE.md*
