DB = backend/runway.db
BACKUP_DIR = backups
TIMESTAMP = $(shell date +%Y%m%d-%H%M%S)

backup:
	mkdir -p $(BACKUP_DIR)
	sqlite3 $(DB) ".backup '$(BACKUP_DIR)/runway-$(TIMESTAMP).db'"
	@echo "Backup saved to $(BACKUP_DIR)/runway-$(TIMESTAMP).db"
