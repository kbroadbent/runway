migrate:
    cd backend && .venv/bin/alembic upgrade head

dev:
    ./run.sh

backup:
    mkdir -p backups
    sqlite3 data/runway.db ".backup 'backups/runway-$(date +%Y%m%d-%H%M%S).db'"
    @echo "Backup saved."

docker:
    docker compose up

docker-build:
    docker compose up --build

docker-bg:
    docker compose up -d

docker-down:
    docker compose down
