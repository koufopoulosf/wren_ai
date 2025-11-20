# Scripts Directory

## Database Scripts

### `generate_crypto_data.py`
**Purpose:** This was used to GENERATE the historical crypto data SQL file.

**You don't need to run this!** The generated SQL data is already in `database/data/02_insert_data.sql` and will be automatically loaded by PostgreSQL when you run `docker-compose up` for the first time.

This script is kept for reference in case you want to regenerate or modify the historical data pattern.

### `postgres-init.sh`
**Purpose:** Manual initialization script (not currently used).

The PostgreSQL Docker image automatically runs any `.sql` files in `/docker-entrypoint-initdb.d/` on first startup, so this script is not needed. The SQL files are mounted directly in `docker-compose.yml`.

### `ollama-entrypoint.sh`
**Purpose:** Automatically pulls the embedding model when Ollama container starts.

This runs automatically when you start the containers.

## How Data Loading Works

When you run `docker-compose up`:

1. PostgreSQL container starts
2. Checks if database is already initialized
3. If NOT initialized (first run):
   - Automatically runs `01_create_schema.sql` (creates tables)
   - Automatically runs `02_insert_data.sql` (inserts ~19,000 records of crypto data)
4. Your database is ready with 2 years of historical data!

**Note:** The data is only loaded on FIRST run. To reload data, you need to delete the volume:
```bash
docker-compose down -v  # Removes volumes
docker-compose up       # Fresh start with data reload
```
