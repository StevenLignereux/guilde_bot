FROM python:3.12-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source et les ressources
COPY . .

# S'assurer que les dossiers de ressources existent
RUN mkdir -p src/resources/images src/resources/fonts

# Vérifier que les ressources sont présentes
RUN test -f src/resources/images/welcome.png || echo "WARNING: welcome.png manquant"
RUN test -f src/resources/fonts/default.ttf || echo "WARNING: default.ttf manquant"

CMD ["python", "main.py"] 