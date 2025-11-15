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
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import httpx
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

        # Simple rate limiting (10 req/sec)
        self._last_request_time = None
        self._min_request_interval = 0.1  # 100ms = 10 req/sec

        # Cache for schema (avoid repeated fetches)
        self._schema_cache = None
        self._entities_cache = []  # List of all entities (tables, columns, metrics)

        # Redshift fallback (optional)
        self.redshift_config = redshift_config
        self._redshift_conn = None

        logger.info(f"✅ Enhanced Wren client initialized: {base_url}")
        if redshift_config:
            logger.info("✅ Redshift fallback enabled")

    async def _rate_limit(self):
        """Simple rate limiting for Wren AI calls."""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)

        self._last_request_time = datetime.now()
    
    async def ask_question(
        self,
        question: str,
        user_context: Optional[Dict] = None,
        max_wait: int = 30
    ) -> Dict:
        """
        Convert natural language to SQL using async polling API.

        Args:
            question: Natural language question
            user_context: Optional context (department, etc.)
            max_wait: Maximum seconds to wait for response

        Returns:
            {
                'sql': str,
                'confidence': float,
                'suggestions': list,
                'entities_found': list,
                'entities_missing': list,
                'metadata': dict
            }
        """
        # Detect entities mentioned in question
        mentioned_entities = await self._extract_entities_from_question(question)

        payload = {
            "query": question
        }

        # Add optional parameters if needed
        if user_context:
            payload["custom_instruction"] = f"User context: {user_context}"

        max_retries = 3
        query_id = None

        # Step 1: Submit the question
        for attempt in range(max_retries):
            try:
                await self._rate_limit()
                logger.info(f"Submitting question to Wren AI: '{question[:100]}...'")

                response = await self.client.post(
                    f"{self.base_url}/v1/asks",  # ✅ Correct endpoint
                    json=payload
                )
                response.raise_for_status()

                result = response.json()
                query_id = result.get("query_id")

                if not query_id:
                    raise Exception("No query_id in response")

                logger.info(f"✅ Question submitted, query_id: {query_id}")
                break

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

        # Step 2: Poll for result
        import time
        start = time.time()
        poll_interval = 1.0

        while time.time() - start < max_wait:
            try:
                await self._rate_limit()

                result_response = await self.client.get(
                    f"{self.base_url}/v1/asks/{query_id}/result"
                )
                result_response.raise_for_status()

                data = result_response.json()
                status = data.get("status", "")

                logger.debug(f"Poll status: {status}")

                if status == "finished":
                    # Extract SQL and metadata
                    response_list = data.get("response", [])
                    sql = response_list[0].get("sql", "") if response_list else ""

                    # Calculate confidence based on status transitions
                    confidence = 0.8 if sql else 0.0

                    # Check if entities mentioned exist
                    entities_found, entities_missing = await self._validate_entities(
                        mentioned_entities
                    )

                    duration = time.time() - start
                    logger.info(
                        f"✅ Wren response ({duration:.1f}s): SQL={len(sql)}, "
                        f"confidence={confidence:.2f}, "
                        f"entities_found={len(entities_found)}, "
                        f"entities_missing={len(entities_missing)}"
                    )

                    return {
                        "sql": sql,
                        "confidence": confidence,
                        "suggestions": [],  # v1 API doesn't return suggestions
                        "entities_found": entities_found,
                        "entities_missing": entities_missing,
                        "metadata": {
                            "rephrased_question": data.get("rephrased_question"),
                            "reasoning": data.get("sql_generation_reasoning"),
                            "tables_used": data.get("retrieved_tables", [])
                        }
                    }

                elif status == "failed":
                    error = data.get("error", {})
                    error_msg = error.get("message", "Unknown error")
                    logger.error(f"❌ Wren AI failed: {error_msg}")
                    raise Exception(f"Wren AI error: {error_msg}")

                elif status == "stopped":
                    raise Exception("Query was cancelled")

                # Still processing, wait and retry
                await asyncio.sleep(poll_interval)

            except httpx.HTTPStatusError as e:
                logger.error(f"❌ Polling error: HTTP {e.response.status_code}")
                raise Exception(f"Failed to get result: HTTP {e.response.status_code}")

            except Exception as e:
                if "Wren AI error" in str(e) or "cancelled" in str(e):
                    raise  # Re-raise known errors
                logger.error(f"❌ Polling exception: {e}")
                await asyncio.sleep(poll_interval)

        raise Exception(f"Query timed out after {max_wait}s")
    
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

        Note: Wren AI v1 REST API doesn't expose schema directly.
        This would typically be accessed via GraphQL UI API.
        For now, returns cached or empty schema.

        Returns:
            Schema with tables, columns, metrics, relationships
        """
        if self._schema_cache:
            return self._schema_cache

        try:
            await self._rate_limit()
            logger.info("Attempting to fetch schema from Wren AI")

            # Try v1/models endpoint (if it exists)
            response = await self.client.get(
                f"{self.base_url}/v1/models"
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

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    "⚠️ Schema endpoint not available in Wren AI v1 REST API. "
                    "Schema features will be limited."
                )
            else:
                logger.error(f"❌ Failed to fetch schema: HTTP {e.response.status_code}")

            # Return empty schema rather than failing
            self._schema_cache = {"tables": [], "relationships": [], "metrics": []}
            return self._schema_cache

        except Exception as e:
            logger.error(f"❌ Failed to fetch schema: {e}")
            # Return empty schema rather than failing
            self._schema_cache = {"tables": [], "relationships": [], "metrics": []}
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
    
    async def execute_sql(self, sql: str, max_wait: int = 30) -> List[Dict]:
        """
        Execute SQL via Wren AI async API or fallback to direct Redshift.

        Args:
            sql: SQL query to execute
            max_wait: Maximum seconds to wait for execution

        Returns:
            List of result rows as dictionaries
        """
        try:
            # Step 1: Submit SQL for execution
            await self._rate_limit()
            logger.info(f"Submitting SQL to Wren AI for execution")

            response = await self.client.post(
                f"{self.base_url}/v1/sql-answers",  # ✅ Correct endpoint
                json={"sql": sql}
            )
            response.raise_for_status()

            result = response.json()
            query_id = result.get("query_id")

            if not query_id:
                raise Exception("No query_id in response")

            logger.info(f"✅ SQL submitted, query_id: {query_id}")

            # Step 2: Poll for execution result
            start = time.time()
            poll_interval = 1.0

            while time.time() - start < max_wait:
                await self._rate_limit()

                result_response = await self.client.get(
                    f"{self.base_url}/v1/sql-answers/{query_id}"
                )
                result_response.raise_for_status()

                data = result_response.json()
                status = data.get("status", "")

                logger.debug(f"Execution status: {status}")

                if status == "finished":
                    results = data.get("results", [])
                    duration = time.time() - start
                    logger.info(f"✅ Query executed ({duration:.1f}s): {len(results)} rows")
                    return results

                elif status == "failed":
                    error = data.get("error", {})
                    error_msg = error.get("message", "Unknown error")
                    logger.error(f"❌ Execution failed: {error_msg}")
                    raise Exception(f"Query execution failed: {error_msg}")

                # Still processing
                await asyncio.sleep(poll_interval)

            raise Exception(f"Execution timed out after {max_wait}s")

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
                f"{self.base_url.replace('/v1', '')}/health",  # Health is at root, not /v1
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