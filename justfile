migrate:
    cd backend && .venv/bin/alembic upgrade head

dev:
    ./run.sh

backup:
    mkdir -p backups
    sqlite3 backend/runway.db ".backup 'backups/runway-$(date +%Y%m%d-%H%M%S).db'"
    @echo "Backup saved."
