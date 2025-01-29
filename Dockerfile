FROM python:3.12-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# S'assurer que les dossiers de ressources existent
RUN mkdir -p src/resources/images src/resources/fonts

# Copier les ressources d'abord
COPY src/resources/images/welcome.png src/resources/images/
COPY src/resources/fonts/default.ttf src/resources/fonts/

# Copier le reste du code source
COPY . .

# Vérifier que les ressources sont présentes
RUN test -f src/resources/images/welcome.png || (echo "ERREUR: welcome.png manquant" && exit 1)
RUN test -f src/resources/fonts/default.ttf || (echo "ERREUR: default.ttf manquant" && exit 1)

CMD ["python", "main.py"] 