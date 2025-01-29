FROM python:3.12-slim

WORKDIR /app

# Créer la structure des dossiers
RUN mkdir -p src/resources/images src/resources/fonts

# Copier d'abord les fichiers de ressources
COPY src/resources/images/welcome.png src/resources/images/
COPY src/resources/fonts/default.ttf src/resources/fonts/

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Vérifier que les ressources sont présentes et afficher leur taille
RUN ls -l src/resources/images/welcome.png && \
    ls -l src/resources/fonts/default.ttf

# Définir les permissions
RUN chmod -R 755 src/resources

# Commande de démarrage avec vérification
CMD echo "=== Vérification des chemins ===" && \
    echo "WELCOME_IMAGE_PATH=$WELCOME_IMAGE_PATH" && \
    echo "FONT_PATH=$FONT_PATH" && \
    echo "WELCOME_CHANNEL_ID=$WELCOME_CHANNEL_ID" && \
    echo "=== Contenu des dossiers ===" && \
    ls -la src/resources/images && \
    ls -la src/resources/fonts && \
    echo "=== Démarrage du bot ===" && \
    python main.py 