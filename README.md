# Guilde Bot

Un bot Discord polyvalent pour gérer votre guilde Star Wars: The Old Republic (SWTOR).

## Fonctionnalités

### Gestion des Tâches
- Création et gestion de listes de tâches
- Ajout, modification et suppression de tâches
- Marquage des tâches comme complétées
- Interface interactive avec boutons et menus déroulants

### Streaming
- Annonce automatique des streams des membres
- Notification dans un canal dédié lorsqu'un membre commence à streamer
- Personnalisation du message d'annonce
- Support pour Twitch et autres plateformes de streaming

### Accueil des Nouveaux Membres
- Message de bienvenue automatique pour les nouveaux membres
- Configuration personnalisée du message d'accueil
- Assignation automatique des rôles
- Système de vérification des nouveaux membres

### Actualités SWTOR
- Agrégation des dernières nouvelles de SWTOR
- Notification automatique des mises à jour du jeu
- Partage des annonces officielles dans un canal dédié
- Suivi des maintenances et des événements du jeu

## Prérequis

- Python 3.8+
- PostgreSQL
- Un token Discord Bot
- Poetry (optionnel, pour la gestion des dépendances)
- Un compte développeur Twitch (pour les fonctionnalités de stream)

## Installation

1. Clonez le repository :
```bash
git clone https://github.com/StevenLignereux/guilde_bot.git
cd guilde_bot
```

2. Installez les dépendances :
```bash
# Avec pip
pip install -r requirements.txt

# Ou avec Poetry
poetry install
```

3. Créez un fichier `.env` à la racine du projet :
```env
# Configuration de la base de données
Database_URL=postgresql://username:password@localhost:5432/database_name

# Tokens Discord et Twitch
DISCORD_TOKEN=your_discord_bot_token
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret

# Configuration des canaux Discord (IDs)
WELCOME_CHANNEL_ID=your_welcome_channel_id
STREAM_CHANNEL_ID=your_stream_channel_id
NEWS_CHANNEL_ID=your_news_channel_id
```

4. Initialisez la base de données :
```bash
alembic upgrade head
```

## Utilisation

1. Démarrez le bot :
```bash
python main.py
```

2. Dans Discord, utilisez les commandes suivantes :
- `!tasks` : Affiche l'interface de gestion des tâches
- `!welcome` : Configure le message de bienvenue
- `!stream` : Configure les annonces de stream
- `!news` : Configure les notifications d'actualités SWTOR

Chaque commande dispose d'une interface interactive permettant une configuration facile et intuitive.

## Tests

Le projet utilise pytest pour les tests. Pour lancer les tests :

```bash
# Lancer tous les tests
pytest tests/

# Lancer les tests avec couverture
pytest tests/ -v --cov=src
```

## Architecture

Le projet suit une architecture hexagonale (ports & adapters) :

```
src/
├── application/        # Couche application (services)
│   └── services/      # Services métier
├── domain/            # Couche domaine
│   ├── entities/      # Entités métier
│   └── interfaces/    # Interfaces et ports
└── infrastructure/    # Couche infrastructure
    ├── config/        # Configuration
    └── repositories/  # Implémentation des repositories
```

## Contribution

1. Fork le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Committez vos changements (`git commit -m 'feat: ajout de ma fonctionnalité'`)
4. Push vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 