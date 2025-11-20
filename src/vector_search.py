"""
Vector-based semantic search using Qdrant and Ollama embeddings.

This module provides semantic search capabilities by:
1. Embedding text using Ollama /api/embeddings endpoint (nomic-embed-text model)
2. Storing/retrieving vectors in Qdrant
3. Finding semantically similar items (tables, columns, etc.)

Note: Uses the legacy /api/embeddings endpoint for broader Ollama version compatibility
"""

import logging
from typing import List, Dict, Optional, Any
import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class VectorSearch:
    """Semantic search using Qdrant vector database and Ollama embeddings."""

    def __init__(
        self,
        qdrant_host: str = "qdrant",
        qdrant_port: int = 6333,
        ollama_url: str = "http://ollama:11434",
        embedding_model: str = "nomic-embed-text",
        collection_name: str = "schema_entities"
    ):
        """
        Initialize vector search.

        Args:
            qdrant_host: Qdrant server hostname
            qdrant_port: Qdrant server port
            ollama_url: Ollama API URL
            embedding_model: Ollama embedding model to use
            collection_name: Qdrant collection name
        """
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.ollama_url = ollama_url
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.embedding_dim = 768  # nomic-embed-text dimension

        # Initialize collection
        self._ensure_collection_exists()

        logger.info(
            f"VectorSearch initialized: {qdrant_host}:{qdrant_port}, "
            f"model={embedding_model}, collection={collection_name}"
        )

    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection created: {self.collection_name}")
            else:
                logger.debug(f"Collection already exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Ollama.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/embed",
                    json={
                        "model": self.embedding_model,
                        "input": text
                    }
                )
                response.raise_for_status()
                result = response.json()
                # The /api/embed endpoint returns "embeddings" (plural) as an array of arrays
                # We take the first embedding since we're sending a single input
                return result["embeddings"][0]
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def index_entity(
        self,
        entity_id: str,
        text: str,
        entity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Index a single entity (table, column, metric, etc.).

        Args:
            entity_id: Unique identifier
            text: Text to embed (e.g., "customers table: Customer master data...")
            entity_type: Type of entity ("table", "column", "metric")
            metadata: Additional metadata to store
        """
        try:
            # Generate embedding
            embedding = await self.generate_embedding(text)

            # Prepare payload
            payload = {
                "text": text,
                "entity_type": entity_type,
                **(metadata or {})
            }

            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=hash(entity_id) % (2**63),  # Convert string ID to int
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            logger.debug(f"Indexed entity: {entity_id} ({entity_type})")
        except Exception as e:
            logger.error(f"Error indexing entity {entity_id}: {e}")
            raise

    async def index_entities_batch(self, entities: List[Dict[str, Any]]):
        """
        Index multiple entities in batch.

        Args:
            entities: List of dicts with keys: entity_id, text, entity_type, metadata
        """
        try:
            # Skip if no entities to index
            if not entities:
                logger.info("No entities to index (empty list)")
                return

            points = []

            for entity in entities:
                text = entity["text"]
                embedding = await self.generate_embedding(text)

                payload = {
                    "text": text,
                    "entity_type": entity["entity_type"],
                    **(entity.get("metadata", {}))
                }

                points.append(
                    PointStruct(
                        id=hash(entity["entity_id"]) % (2**63),
                        vector=embedding,
                        payload=payload
                    )
                )

            # Batch upsert
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Batch indexed {len(entities)} entities")
        except Exception as e:
            logger.error(f"Error in batch indexing: {e}")
            raise

    async def search(
        self,
        query: str,
        limit: int = 5,
        entity_type: Optional[str] = None,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar entities.

        Args:
            query: Search query text
            limit: Maximum number of results
            entity_type: Filter by entity type (optional)
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of matches with keys: entity_id, text, entity_type, score, metadata
        """
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)

            # Build filter
            search_filter = None
            if entity_type:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="entity_type",
                            match=MatchValue(value=entity_type)
                        )
                    ]
                )

            # Search
            results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                query_filter=search_filter,
                score_threshold=score_threshold
            ).points

            # Format results
            matches = []
            for result in results:
                matches.append({
                    "score": result.score,
                    "text": result.payload.get("text"),
                    "entity_type": result.payload.get("entity_type"),
                    "metadata": {
                        k: v for k, v in result.payload.items()
                        if k not in ["text", "entity_type"]
                    }
                })

            logger.debug(f"Search for '{query}' returned {len(matches)} results")
            return matches

        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise

    def clear_collection(self):
        """Clear all vectors from the collection."""
        try:
            self.qdrant_client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection_exists()
            logger.info(f"Collection cleared: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            info = self.qdrant_client.get_collection(collection_name=self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
