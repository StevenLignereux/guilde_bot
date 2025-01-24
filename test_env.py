import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

def check_env():
    # Trouver le fichier .env
    env_path = find_dotenv()
    print(f"\nRecherche du fichier .env :")
    print(f"Chemin trouvé : {env_path}")
    
    # Vérifier si le fichier existe
    if not env_path:
        print("❌ Fichier .env non trouvé")
        return
    
    # Lire le contenu brut du fichier
    print("\nContenu du fichier .env :")
    with open(env_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'DATABASE' in line.upper() or 'DB' in line.upper():
                print(f"Trouvé : {line.strip()}")
    
    # Charger les variables
    load_dotenv(env_path)
    
    # Vérifier les variables chargées
    print("\nVariables d'environnement chargées :")
    database_url = os.getenv('Database_URL')
    print(f"Database_URL : {'[PRÉSENTE]' if database_url else '[MANQUANTE]'}")
    
    # Vérifier toutes les variables similaires
    print("\nAutres variables similaires trouvées :")
    for key in os.environ:
        if ('DATABASE' in key.upper() or 'DB' in key.upper()) and key != 'Database_URL':
            print(f"{key}: [PRÉSENTE]")

if __name__ == "__main__":
    check_env() 