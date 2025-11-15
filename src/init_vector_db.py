"""
Initialize vector database with schema embeddings.

This script should be run:
1. On first application startup
2. Whenever the database schema changes

It will:
- Connect to PostgreSQL and introspect the schema
- Generate embeddings for all tables and columns
- Store embeddings in Qdrant for semantic search
"""

import asyncio
import logging
from src.config import Config
from src.vector_search import VectorSearch
from src.schema_embedder import SchemaEmbedder

logger = logging.getLogger(__name__)


async def initialize_vector_db():
    """Initialize vector database with current schema."""
    try:
        # Load config
        config = Config()

        logger.info("="*70)
        logger.info("INITIALIZING VECTOR DATABASE")
        logger.info("="*70)

        # Initialize vector search
        vector_search = VectorSearch(
            qdrant_host=config.QDRANT_HOST,
            qdrant_port=config.QDRANT_PORT,
            ollama_url=config.OLLAMA_URL,
            embedding_model=config.EMBEDDING_MODEL,
            collection_name=config.VECTOR_COLLECTION
        )

        logger.info(f"✅ Vector search initialized")

        # Initialize schema embedder
        db_config = {
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "database": config.DB_DATABASE,
            "user": config.DB_USER,
            "password": config.DB_PASSWORD,
            "ssl": "require" if config.DB_SSL else "disable"
        }

        schema_embedder = SchemaEmbedder(
            db_config=db_config,
            vector_search=vector_search
        )

        logger.info(f"✅ Schema embedder initialized")

        # Embed schema
        logger.info("🔄 Embedding schema into vector database...")
        await schema_embedder.refresh_schema_embeddings()

        logger.info("="*70)
        logger.info("✅ VECTOR DATABASE INITIALIZATION COMPLETE")
        logger.info("="*70)

        # Show stats
        stats = vector_search.get_collection_info()
        logger.info(f"Collection: {stats.get('name')}")
        logger.info(f"Total vectors: {stats.get('points_count', 0)}")
        logger.info(f"Status: {stats.get('status')}")

    except Exception as e:
        logger.error(f"❌ Error initializing vector database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(initialize_vector_db())
