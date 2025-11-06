# 📊 Dashboard HubSpot - Raphaël Cheminaud

Dashboard automatique des activités HubSpot pour Raphaël Cheminaud chez 13 Years.

## 🌐 Accès en ligne

Le dashboard est accessible à l'adresse : **https://13yadmin.github.io/raphael-hubspot-dashboard/**

## 🔄 Mise à jour automatique

Les données sont automatiquement rafraîchies **tous les jours à 17h30** via GitHub Actions.

Le dashboard affiche :
- 📧 Emails envoyés (hors séquences automatiques)
- 📞 Appels téléphoniques
- ✅ Tâches
- ⏱️ Temps de travail effectif
- 📈 Statistiques et graphiques interactifs
- 🎯 Timeline détaillée jour par jour

## 🛠️ Configuration technique

### Prérequis

- Token HubSpot API configuré dans les secrets GitHub (`HUBSPOT_TOKEN`)
- GitHub Pages activé sur la branche `main`

### Structure du projet

```
.
├── index.html              # Dashboard (template)
├── data.json              # Données actualisées quotidiennement
├── fetch_data.py          # Script de récupération HubSpot
├── .github/
│   └── workflows/
│       └── update-dashboard.yml  # Automatisation quotidienne
└── README.md
```

### Workflow

1. **Tous les jours à 17h30** : GitHub Actions exécute `fetch_data.py`
2. Le script récupère les données HubSpot via API
3. Génère `data.json` avec toutes les statistiques
4. Commit et push automatique si changements détectés
5. GitHub Pages redéploie automatiquement le site

## 🔧 Développement local

Pour tester en local :

```bash
# 1. Cloner le repo
git clone [URL_DU_REPO]
cd raphael-dashboard

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Définir le token HubSpot
export HUBSPOT_TOKEN="votre-token"

# 4. Exécuter le script
python fetch_data.py

# 5. Ouvrir index.html dans un navigateur
# Note: Il faut un serveur HTTP local pour éviter les erreurs CORS
python -m http.server 8000
# Puis ouvrir http://localhost:8000
```

## 📝 Détails techniques

### Exclusions

- Les emails de **séquences automatiques** sont exclus du rapport
- Seules les activités manuelles sont comptabilisées

### Calcul du temps de travail

- **Seuil d'inactivité** : 65 minutes
- Si 2 actions sont espacées de plus de 65 minutes, elles appartiennent à des sessions différentes
- Le temps effectif = somme des durées de toutes les sessions

### Période couverte

Le dashboard affiche les données depuis le **lundi dernier** jusqu'à aujourd'hui.

## 🚀 Mise à jour manuelle

Pour forcer une mise à jour manuelle :

1. Aller dans l'onglet **Actions** du repository GitHub
2. Sélectionner le workflow "Update Dashboard"
3. Cliquer sur "Run workflow"

---

**Généré avec ❤️ par Claude Code**
