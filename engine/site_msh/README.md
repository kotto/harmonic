# 🌊 MSH — Modèle Standard Harmonique

Site web présentant le Modèle Standard Harmonique (MSH-5.0).

## Déploiement sur Render

1. Connecter ce dépôt à Render
2. Configurer :
   - **Runtime** : Node
   - **Build Command** : `npm install`
   - **Start Command** : `node server.js`
   - **Port** : 3000

## Déploiement sur Oracle Cloud

```bash
scp -r site_msh/* ubuntu@<IP_ORACLE>:/var/www/msh/
ssh ubuntu@<IP_ORACLE> "sudo apt-get install -y nginx && sudo cp /var/www/msh/nginx.conf /etc/nginx/sites-available/msh && sudo ln -sf /etc/nginx/sites-available/msh /etc/nginx/sites-enabled/ && sudo systemctl restart nginx"
```

## Contenu

- Fichier unique `index.html` (CSS + JS embarqués)
- 10 livres + conclusion
- Thème sombre, navigation sidebar, responsive