FROM python:3.12-slim

WORKDIR /app

# Copier tout le code source d'abord
COPY . .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Vérifier la structure des dossiers
RUN ls -la src/resources/images || true
RUN ls -la src/resources/fonts || true

# Afficher les variables d'environnement au démarrage
CMD echo "=== Vérification des chemins ===" && \
    echo "WELCOME_IMAGE_PATH=$WELCOME_IMAGE_PATH" && \
    echo "FONT_PATH=$FONT_PATH" && \
    echo "WELCOME_CHANNEL_ID=$WELCOME_CHANNEL_ID" && \
    ls -la src/resources/images && \
    ls -la src/resources/fonts && \
    python main.py 