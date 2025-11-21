# 📊 Dashboard HubSpot - Raphaël Cheminaud

Dashboard automatique des activités HubSpot pour Raphaël Cheminaud chez 13 Years.

## 🌐 Accès en ligne

Le dashboard est accessible à l'adresse : **https://13yadmin.github.io/raphael-hubspot-dashboard/**

### 🔐 Authentification

Le dashboard est protégé par mot de passe. Lors de votre première visite, vous serez redirigé vers une page de connexion.

**Mot de passe** : `raphael2025`

La session reste active pendant 24 heures, puis expire automatiquement pour des raisons de sécurité.

## 🔄 Mise à jour automatique

Les données sont automatiquement rafraîchies **tous les jours à 16h45** via GitHub Actions.

Le dashboard affiche :
- 📧 Emails envoyés (hors séquences automatiques)
- 📞 Appels téléphoniques avec résultats détaillés (connecté, occupé, pas de réponse, etc.)
- ✅ Tâches
- 📝 Notes
- 🤝 Réunions
- ⏱️ Temps de travail effectif par jour
- 💰 Calcul de salaire basé sur les objectifs
- 📈 Statistiques et graphiques interactifs
- 🎯 Timeline détaillée jour par jour avec sessions de travail

## 💰 Système de rémunération

Le dashboard calcule automatiquement le salaire proratisé basé sur les objectifs :

### Objectifs quotidiens
- 30 appels par jour
- 30 emails par jour
- Salaire de base : 200€ par jour

### Calcul
Le salaire est proratisé selon le pourcentage d'accomplissement des objectifs mensuels :
```
Salaire proratisé = Salaire de base × (Actions réalisées / Objectifs mensuels)
```

**Exemple (Novembre 2025 - 14 jours actifs)** :
- Objectifs : 420 appels + 420 emails = 840 actions
- Réalisé : 167 appels + 106 emails = 273 actions
- Taux d'accomplissement : 32.5%
- Salaire : 910€ sur 2800€ de base

## 🛠️ Configuration technique

### Prérequis

- Token HubSpot API configuré dans les secrets GitHub (`HUBSPOT_TOKEN`)
- GitHub Pages activé sur la branche `main`
- Repository public pour accès GitHub Pages

### Structure du projet

```
.
├── index.html              # Dashboard principal
├── login.html             # Page d'authentification
├── data.json              # Données actualisées quotidiennement (gitignored)
├── fetch_data.py          # Script de récupération HubSpot
├── .github/
│   └── workflows/
│       └── update-dashboard.yml  # Automatisation quotidienne (16h45)
└── README.md
```

### Workflow automatique

1. **Tous les jours à 16h45** : GitHub Actions exécute `fetch_data.py`
2. Le script récupère les données HubSpot via API (engagements, appels, emails, etc.)
3. Génère `data.json` avec toutes les statistiques calculées
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

- **Seuil d'inactivité** : 30 minutes
- Si 2 actions sont espacées de plus de 30 minutes, elles appartiennent à des sessions différentes
- Le temps effectif = somme des durées de toutes les sessions
- Affichage graphique avec timeline par jour montrant les sessions de travail

### Statistiques d'appels

Le dashboard affiche des statistiques détaillées sur les appels :
- **Connecté** : Appels aboutis avec conversation
- **Pas de réponse** : Appels non décrochés
- **Occupé** : Ligne occupée
- **Message laissé** : Message vocal ou répondeur
- **Mauvais numéro** : Numéro incorrect ou invalide
- Durée moyenne des appels connectés
- Graphique de répartition des résultats d'appels

### Période couverte

Le dashboard peut afficher n'importe quelle période configurable. Actuellement configuré pour afficher les données depuis le **1er novembre 2025**.

## 🚀 Mise à jour manuelle

Pour forcer une mise à jour manuelle :

1. Aller dans l'onglet **Actions** du repository GitHub
2. Sélectionner le workflow "Update Dashboard"
3. Cliquer sur "Run workflow"

---

**Généré avec ❤️ par Claude Code**
