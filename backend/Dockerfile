# Dockerfile pour le déploiement de Datavera Backend sur Hugging Face Spaces
# - SDK Hugging Face Spaces: Docker
# - Port d'écoute obligatoire HF Spaces: 7860

FROM python:3.12-slim

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Installation des dépendances système légères nécessaires pour pandas/duckdb si nécessaire
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie du fichier de dépendances
COPY requirements.txt /app/requirements.txt

# Installation des dépendances Python (strictement basées sur requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code applicatif backend (dossier app/)
COPY app /app/app

# Exposition du port 7860 (port d'écoute imposé par Hugging Face Spaces)
EXPOSE 7860

# Définition de la variable d'environnement PYTHONPATH pour localiser le sous-module app
ENV PYTHONPATH=/app

# Commande de démarrage avec Uvicorn sur le port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
