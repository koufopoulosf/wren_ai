#!/bin/bash
# Postgres initialization script
# This script ensures the database schema and data are loaded
# even if the postgres volume already exists

set -e

echo "🔍 Checking if database schema needs initialization..."

# Wait for postgres to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; do
  echo "⏳ Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "✅ PostgreSQL is ready"

# Check if tables exist
TABLE_COUNT=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")

if [ "$TABLE_COUNT" -eq "0" ]; then
    echo "📊 No tables found. Initializing database schema..."

    # Run schema creation
    if [ -f /docker-entrypoint-initdb.d/01_create_schema.sql ]; then
        echo "📝 Creating schema..."
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/01_create_schema.sql
        echo "✅ Schema created"
    else
        echo "❌ Schema file not found: /docker-entrypoint-initdb.d/01_create_schema.sql"
        exit 1
    fi

    # Run data insertion
    if [ -f /docker-entrypoint-initdb.d/02_insert_data.sql ]; then
        echo "📝 Inserting data..."
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/02_insert_data.sql
        echo "✅ Data inserted"
    else
        echo "❌ Data file not found: /docker-entrypoint-initdb.d/02_insert_data.sql"
        exit 1
    fi

    echo "🎉 Database initialization complete!"
else
    echo "✅ Database already initialized (found $TABLE_COUNT tables)"
fi

echo "📊 Database summary:"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
