import asyncio
import asyncpg
from dotenv import load_dotenv
import os

async def create_tables():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer l'URL de la base de données
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("Erreur: DATABASE_URL n'est pas définie")
        return
    
    print(f"Tentative de connexion à : {db_url}")
    
    try:
        # Créer une connexion
        conn = await asyncpg.connect(db_url)
        
        # Créer la table task_lists
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS task_lists (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                user_discord_id VARCHAR NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Créer la table tasks
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                description VARCHAR NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                task_list_id INTEGER NOT NULL REFERENCES task_lists(id) ON DELETE CASCADE
            )
        ''')
        
        print("Tables créées avec succès!")
        
        # Fermer la connexion
        await conn.close()
        
    except Exception as e:
        print(f"Erreur lors de la création des tables: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_tables())