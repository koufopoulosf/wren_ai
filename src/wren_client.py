"""
Wren AI API Client - Enhanced Version

Improvements:
- Actual entity discovery and search
- Fuzzy matching for suggestions
- Direct Redshift fallback for simple queries
- Better error handling with context
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
import httpx
from asyncio_throttle import Throttle
from fuzzywuzzy import fuzz, process
import redshift_connector

logger = logging.getLogger(__name__)


class WrenClient:
    """
    Enhanced async client for Wren AI with entity discovery.
    """
    
    def __init__(
        self, 
        base_url: str, 
        timeout: int = 30,
        redshift_config: Optional[Dict] = None
    ):
        """
        Initialize Wren AI client with optional Redshift fallback.
        
        Args:
            base_url: Wren AI service URL
            timeout: Request timeout
            redshift_config: Optional Redshift connection config for fallback
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.throttle = Throttle(rate_limit=10, period=1.0)
        
        # Cache for schema (avoid repeated fetches)
        self._schema_cache = None
        self._entities_cache = []  # List of all entities (tables, columns, metrics)
        
        # Redshift fallback (optional)
        self.redshift_config = redshift_config
        self._redshift_conn = None
        
        logger.info(f"✅ Enhanced Wren client initialized: {base_url}")
        if redshift_config:
            logger.info("✅ Redshift fallback enabled")
    
    async def ask_question(
        self,
        question: str,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Convert natural language to SQL with enhanced entity discovery.
        
        Returns:
            {
                'sql': str,
                'confidence': float,
                'suggestions': list,
                'entities_found': list,  # NEW: Entities detected in question
                'entities_missing': list,  # NEW: Entities user mentioned but don't exist
                'metadata': dict
            }
        """
        # Detect entities mentioned in question
        mentioned_entities = await self._extract_entities_from_question(question)
        
        payload = {
            "query": question,
            "context": user_context or {}
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.throttle:
                    logger.info(f"Asking Wren AI: '{question[:100]}...'")
                    
                    response = await self.client.post(
                        f"{self.base_url}/api/v1/ask",  # Fixed endpoint
                        json=payload
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # Extract response
                    sql = result.get("sql", "")
                    confidence = result.get("confidence", 0.0)
                    suggestions = result.get("suggestions", [])
                    
                    # Check if entities mentioned exist
                    entities_found, entities_missing = await self._validate_entities(
                        mentioned_entities
                    )
                    
                    logger.info(
                        f"✅ Wren response: SQL={len(sql)}, "
                        f"confidence={confidence:.2f}, "
                        f"entities_found={len(entities_found)}, "
                        f"entities_missing={len(entities_missing)}"
                    )
                    
                    return {
                        "sql": sql,
                        "confidence": confidence,
                        "suggestions": suggestions,
                        "entities_found": entities_found,
                        "entities_missing": entities_missing,
                        "metadata": result.get("metadata", {})
                    }
            
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ HTTP {e.response.status_code}")
                if attempt == max_retries - 1:
                    raise Exception(
                        f"Wren AI error {e.response.status_code}. "
                        "Please try rephrasing your question."
                    )
            
            except httpx.TimeoutException:
                logger.error(f"⏱️ Timeout (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    raise Exception("Wren AI timeout. Try simplifying your question.")
            
            except Exception as e:
                logger.error(f"❌ Error: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to connect to Wren AI: {str(e)}")
            
            await asyncio.sleep(2 ** attempt)
        
        raise Exception("Failed after all retries")
    
    async def _extract_entities_from_question(self, question: str) -> List[str]:
        """
        Extract potential entity names from question.
        
        Returns:
            List of potential entity names mentioned
        """
        # Common metric/entity patterns
        patterns = [
            'nps', 'revenue', 'orders', 'customers', 'users', 'sales',
            'churn', 'retention', 'conversion', 'traffic', 'signups',
            'arr', 'mrr', 'ltv', 'cac', 'roi', 'margin'
        ]
        
        question_lower = question.lower()
        mentioned = []
        
        for pattern in patterns:
            if pattern in question_lower:
                mentioned.append(pattern)
        
        return mentioned
    
    async def _validate_entities(
        self, 
        entities: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Check which entities exist in schema and which don't.
        
        Returns:
            (entities_found, entities_missing)
        """
        if not entities:
            return [], []
        
        # Ensure schema is loaded
        await self._ensure_schema_loaded()
        
        found = []
        missing = []
        
        for entity in entities:
            # Fuzzy match against cached entities
            best_match = self._fuzzy_find_entity(entity)
            
            if best_match and best_match['score'] > 70:
                found.append(best_match['entity'])
            else:
                missing.append(entity)
        
        return found, missing
    
    def _fuzzy_find_entity(self, search_term: str) -> Optional[Dict]:
        """
        Find best matching entity using fuzzy matching.
        
        Returns:
            {'entity': str, 'type': str, 'score': int} or None
        """
        if not self._entities_cache:
            return None
        
        # Get all entity names
        entity_names = [e['name'] for e in self._entities_cache]
        
        # Fuzzy match
        result = process.extractOne(
            search_term.lower(),
            entity_names,
            scorer=fuzz.token_sort_ratio
        )
        
        if result:
            best_match, score = result[0], result[1]
            # Find full entity info
            for entity in self._entities_cache:
                if entity['name'] == best_match:
                    return {
                        'entity': best_match,
                        'type': entity['type'],
                        'score': score
                    }
        
        return None
    
    async def search_similar_entities(
        self,
        search_term: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for entities similar to search term.
        
        Returns:
            List of similar entities with scores
        """
        await self._ensure_schema_loaded()
        
        if not self._entities_cache:
            return []
        
        entity_names = [e['name'] for e in self._entities_cache]
        
        # Get top matches
        matches = process.extract(
            search_term.lower(),
            entity_names,
            scorer=fuzz.token_sort_ratio,
            limit=limit
        )
        
        results = []
        for match_name, score in matches:
            if score > 50:  # Only reasonable matches
                # Find full entity info
                for entity in self._entities_cache:
                    if entity['name'] == match_name:
                        results.append({
                            'name': match_name,
                            'type': entity['type'],
                            'description': entity.get('description', ''),
                            'score': score
                        })
                        break
        
        return results
    
    async def _ensure_schema_loaded(self):
        """Load schema if not already cached."""
        if self._schema_cache is None:
            try:
                await self.get_schema()
            except Exception as e:
                logger.warning(f"Failed to load schema: {e}")
                self._schema_cache = {"tables": [], "relationships": []}
    
    async def get_schema(self) -> Dict:
        """
        Get database schema from Wren AI.
        
        Returns:
            Schema with tables, columns, metrics, relationships
        """
        if self._schema_cache:
            return self._schema_cache
        
        try:
            async with self.throttle:
                logger.info("Fetching schema from Wren AI")
                
                response = await self.client.get(
                    f"{self.base_url}/api/v1/schema"
                )
                response.raise_for_status()
                
                schema = response.json()
                self._schema_cache = schema
                
                # Build entities cache
                self._build_entities_cache(schema)
                
                logger.info(
                    f"✅ Schema loaded: {len(self._entities_cache)} entities"
                )
                
                return schema
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch schema: {e}")
            # Return empty schema rather than failing
            self._schema_cache = {"tables": [], "relationships": []}
            return self._schema_cache
    
    def _build_entities_cache(self, schema: Dict):
        """Build flat list of all entities from schema."""
        self._entities_cache = []
        
        # Extract tables
        for table in schema.get("tables", []):
            self._entities_cache.append({
                'name': table.get('name', '').lower(),
                'type': 'table',
                'description': table.get('description', '')
            })
            
            # Extract columns
            for column in table.get('columns', []):
                self._entities_cache.append({
                    'name': column.get('name', '').lower(),
                    'type': 'column',
                    'table': table.get('name', ''),
                    'description': column.get('description', '')
                })
        
        # Extract metrics
        for metric in schema.get("metrics", []):
            self._entities_cache.append({
                'name': metric.get('name', '').lower(),
                'type': 'metric',
                'description': metric.get('description', '')
            })
    
    async def execute_sql(self, sql: str) -> List[Dict]:
        """
        Execute SQL via Wren AI or fallback to direct Redshift.
        """
        try:
            # Try Wren AI first
            async with self.throttle:
                logger.info(f"Executing SQL via Wren AI")
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/query",  # More standard endpoint
                    json={"sql": sql}
                )
                response.raise_for_status()
                
                result = response.json()
                data = result.get("data", result.get("results", []))
                
                logger.info(f"✅ Query executed: {len(data)} rows")
                return data
        
        except Exception as e:
            logger.warning(f"Wren AI execution failed: {e}")
            
            # Try Redshift fallback
            if self.redshift_config:
                logger.info("Trying direct Redshift fallback...")
                return await self._execute_via_redshift(sql)
            else:
                raise Exception(f"Query failed: {str(e)}")
    
    async def _execute_via_redshift(self, sql: str) -> List[Dict]:
        """
        Execute SQL directly on Redshift (fallback).
        """
        try:
            # Create connection if needed
            if not self._redshift_conn:
                self._redshift_conn = redshift_connector.connect(
                    host=self.redshift_config['host'],
                    port=self.redshift_config.get('port', 5439),
                    database=self.redshift_config['database'],
                    user=self.redshift_config['user'],
                    password=self.redshift_config['password'],
                    ssl=self.redshift_config.get('ssl', True)
                )
            
            cursor = self._redshift_conn.cursor()
            cursor.execute(sql)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            
            logger.info(f"✅ Redshift fallback success: {len(results)} rows")
            return results
        
        except Exception as e:
            logger.error(f"❌ Redshift fallback failed: {e}")
            raise Exception(f"Query execution failed: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check Wren AI health."""
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=5
            )
            
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.info("✅ Wren AI healthy")
            else:
                logger.warning(f"⚠️ Wren AI unhealthy: {response.status_code}")
            
            return is_healthy
        
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    async def close(self):
        """Cleanup connections."""
        await self.client.aclose()
        
        if self._redshift_conn:
            self._redshift_conn.close()
        
        logger.info("Wren AI client closed")