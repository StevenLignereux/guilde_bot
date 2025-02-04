#!/bin/bash

# Configuration
BACKUP_DIR="/opt/backups"
DB_NAME="guild_bot"
DB_USER="guildbot"
DATE=$(date +%Y%m%d_%H%M%S)

# Créer le dossier de backup s'il n'existe pas
mkdir -p $BACKUP_DIR

# Backup de la base de données
pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compression
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Nettoyage des vieux backups (garde les 7 derniers jours)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete 