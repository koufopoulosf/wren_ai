"""
Wren AI API Client - Enhanced Version

Improvements:
- Actual entity discovery and search
- Fuzzy matching for suggestions
- Direct database fallback for simple queries (Redshift or Postgres)
- Better error handling with context
"""

import logging
import asyncio
import time
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import httpx
from fuzzywuzzy import fuzz, process
from anthropic import Anthropic
from schema_formatter import SchemaFormatter
from cell_retriever import CellRetriever

# Database connectors (import as needed)
try:
    import redshift_connector
    REDSHIFT_AVAILABLE = True
except ImportError:
    REDSHIFT_AVAILABLE = False

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)


class WrenClient:
    """
    Enhanced async client for Wren AI with entity discovery.
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        db_type: str = "redshift",
        db_config: Optional[Dict] = None,
        redshift_config: Optional[Dict] = None,  # Deprecated, use db_config
        mdl_hash: Optional[str] = None,
        anthropic_client: Optional[Anthropic] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Wren AI client with optional database fallback.

        Args:
            base_url: Wren AI service URL
            timeout: Request timeout
            db_type: Database type ("redshift" or "postgres")
            db_config: Optional database connection config for fallback
            redshift_config: Deprecated - use db_config instead
            mdl_hash: Optional MDL hash for version control (auto-fetched if not provided)
            anthropic_client: Optional Anthropic client for NLP understanding
            model: Claude model name for NLP tasks
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.anthropic_client = anthropic_client
        self.model = model

        # Simple rate limiting (10 req/sec)
        self._last_request_time = None
        self._min_request_interval = 0.1  # 100ms = 10 req/sec

        # Cache for schema (avoid repeated fetches)
        self._schema_cache = None
        self._entities_cache = []  # List of all entities (tables, columns, metrics)

        # MDL (Model Definition Language) for semantic layer
        self._mdl = None  # Full MDL structure
        self.mdl_hash = mdl_hash  # Version hash for MDL
        self._mdl_models = []  # Extracted models for quick access
        self._mdl_metrics = []  # Extracted metrics for quick access
        self._schema_formatter = None  # Schema formatter for dual formats
        self._cell_retriever = None  # Cell value retriever

        # Database fallback (optional) - supports Redshift or Postgres
        self.db_type = db_type.lower()
        self.db_config = db_config or redshift_config  # Support legacy redshift_config
        self._db_conn = None

        logger.info(f"✅ Enhanced Wren client initialized: {base_url}")
        if self.db_config:
            logger.info(f"✅ Database fallback enabled: {self.db_type.upper()}")

            # Validate connector availability
            if self.db_type == "redshift" and not REDSHIFT_AVAILABLE:
                logger.warning("⚠️ redshift-connector not installed, fallback disabled")
                self.db_config = None
            elif self.db_type == "postgres" and not POSTGRES_AVAILABLE:
                logger.warning("⚠️ psycopg2 not installed, fallback disabled")
                self.db_config = None

    async def _rate_limit(self):
        """Simple rate limiting for Wren AI calls."""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)

        self._last_request_time = datetime.now()
    
    async def validate_question_entities(self, question: str) -> Tuple[bool, str, List[str]]:
        """
        Pre-validate entities in question before calling Wren AI.

        Args:
            question: Natural language question

        Returns:
            (is_valid, error_message, suggestions)
        """
        # Extract entities from question
        mentioned_entities = await self._extract_entities_from_question(question)

        if not mentioned_entities:
            # No specific entities detected - ask for clarification
            return await self._generate_clarification(question)

        # Validate entities
        found, missing = await self._validate_entities(mentioned_entities)

        if missing:
            # Some entities don't exist - provide helpful guidance
            return await self._generate_entity_not_found_response(question, missing, found)

        logger.info(f"✅ Pre-validation passed - all entities exist")
        return True, "", []

    async def _generate_clarification(self, question: str) -> Tuple[bool, str, List[str]]:
        """
        Generate helpful clarification when we can't understand the question.

        Returns:
            (is_valid=True, clarification_message, suggestions)
        """
        # If we have no schema loaded, ask user to wait
        if not self._entities_cache:
            msg = "⏳ **Loading your data schema...**\n\nPlease wait a moment while I discover what data is available."
            return False, msg, []

        # Generate helpful guidance using Claude
        if self.anthropic_client:
            try:
                return await self._generate_ai_clarification(question)
            except Exception as e:
                logger.warning(f"AI clarification failed: {e}")

        # Fallback: Show available data
        available = [e['name'] for e in self._entities_cache[:15]]
        msg = f"💡 **I'm not sure what data you're looking for.**\n\n"
        msg += f"Available data includes: {', '.join(f'`{a}`' for a in available)}\n\n"
        msg += "Can you rephrase your question using one of these entities?"

        return False, msg, available

    async def _generate_ai_clarification(self, question: str) -> Tuple[bool, str, List[str]]:
        """Use Claude to generate helpful clarifying questions."""
        available_entities = [e['name'] for e in self._entities_cache[:30]]
        entity_list = ', '.join(available_entities)

        prompt = f"""The user asked: "{question}"

Available data entities: {entity_list}

The question doesn't clearly match any specific entity. Generate 2-3 helpful clarifying questions to understand what the user wants, OR suggest which entities might be relevant.

Format your response as:
💡 **Let me help clarify:**
- [Question 1]
- [Question 2]
- [Suggestion if applicable]

Be conversational and helpful."""

        # Call Claude API (async using executor)
        import asyncio
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
        )

        clarification = message.content[0].text.strip()
        return False, clarification, available_entities[:5]

    async def _generate_entity_not_found_response(
        self,
        question: str,
        missing: List[str],
        found: List[str]
    ) -> Tuple[bool, str, List[str]]:
        """
        Generate helpful response when entities are not found.

        Returns:
            (is_valid, error_message, suggestions)
        """
        # Find suggestions using fuzzy matching
        suggestions = []
        for entity in missing:
            best_match = self._fuzzy_find_entity(entity)
            if best_match and best_match['score'] > 50:
                suggestions.append(best_match['entity']['name'])

        # Use Claude to generate a helpful response
        if self.anthropic_client and suggestions:
            try:
                return await self._generate_ai_entity_suggestion(question, missing, suggestions)
            except Exception as e:
                logger.warning(f"AI suggestion generation failed: {e}")

        # Fallback to basic error message
        error_msg = f"⚠️ **Entity Not Found**\n\n"
        error_msg += f"Could not find: {', '.join(f'`{e}`' for e in missing)}\n\n"

        if suggestions:
            error_msg += f"💡 **Did you mean:** {', '.join(f'`{s}`' for s in suggestions)}?\n\n"
            error_msg += "Try asking your question with one of these entities instead."
        else:
            # Show available entities
            available = [e['name'] for e in self._entities_cache[:10]]
            if available:
                error_msg += f"**Available data:** {', '.join(f'`{a}`' for a in available)}"

        return False, error_msg, suggestions

    async def _generate_ai_entity_suggestion(
        self,
        question: str,
        missing: List[str],
        suggestions: List[str]
    ) -> Tuple[bool, str, List[str]]:
        """Use Claude to generate a helpful suggestion for entity not found."""
        prompt = f"""The user asked: "{question}"

They mentioned: {', '.join(missing)}
But these entities don't exist in the schema.

Similar entities that DO exist: {', '.join(suggestions)}

Generate a helpful, conversational response that:
1. Acknowledges what they're looking for
2. Suggests the similar entities
3. Asks if they want to use one of those instead

Keep it friendly and concise (2-3 sentences max).

Response:"""

        # Call Claude API (async using executor)
        import asyncio
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
        )

        response_text = message.content[0].text.strip()
        return False, response_text, suggestions

    async def ask_question(
        self,
        question: str,
        max_wait: int = 30
    ) -> Dict:
        """
        Convert natural language to SQL using async polling API.

        Args:
            question: Natural language question
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

        # Add MDL hash for semantic layer version control
        if self.mdl_hash:
            payload["mdl_hash"] = self.mdl_hash
            logger.debug(f"Using MDL hash: {self.mdl_hash[:8]}...")

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
        Extract potential entity names from question using Claude NLP.

        Returns:
            List of potential entity names mentioned
        """
        # If no Claude client, fall back to basic pattern matching
        if not self.anthropic_client:
            return await self._extract_entities_basic(question)

        # Use Claude to understand what the user is asking about
        try:
            available_entities = [e['name'] for e in self._entities_cache[:50]]
            entity_list = ', '.join(available_entities[:20]) if available_entities else "No entities loaded yet"

            prompt = f"""You are analyzing a data question to identify which data entities (tables, columns, or metrics) the user is asking about.

Question: "{question}"

Available entities in the schema: {entity_list}

Task: Extract the key entities the user is asking about. Consider:
- Direct mentions (e.g., "revenue" → revenue)
- Synonyms (e.g., "income" → revenue, "clients" → customers)
- Implied entities (e.g., "how much did we make" → revenue/sales)

Return ONLY a JSON array of entity names mentioned or implied, or an empty array if none.
Example: ["revenue", "customers"]

Response:"""

            # Call Claude API (async using executor)
            import asyncio
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=150,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            import re
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
                logger.info(f"Claude extracted entities: {entities}")
                return entities

            return []

        except Exception as e:
            logger.warning(f"Claude entity extraction failed: {e}, falling back to basic patterns")
            return await self._extract_entities_basic(question)

    async def _extract_entities_basic(self, question: str) -> List[str]:
        """Fallback: Basic pattern matching for entity extraction."""
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
        Find best matching entity using fuzzy matching (including aliases).

        Returns:
            {'entity': dict, 'type': str, 'score': int} or None
        """
        if not self._entities_cache:
            return None

        search_lower = search_term.lower()
        best_match = None
        best_score = 0

        for entity in self._entities_cache:
            # Check exact match on name first
            if entity['name'].lower() == search_lower:
                return {
                    'entity': entity,
                    'type': entity['type'],
                    'score': 100
                }

            # Check exact match on aliases
            aliases = entity.get('aliases', [])
            if search_lower in aliases:
                return {
                    'entity': entity,
                    'type': entity['type'],
                    'score': 95  # Slightly lower than exact name match
                }

            # Fuzzy match on name
            name_score = fuzz.token_sort_ratio(search_lower, entity['name'].lower())

            # Fuzzy match on aliases
            alias_scores = [fuzz.token_sort_ratio(search_lower, alias) for alias in aliases]
            max_alias_score = max(alias_scores) if alias_scores else 0

            # Take the best score
            score = max(name_score, max_alias_score)

            if score > best_score:
                best_score = score
                best_match = entity

        if best_match and best_score > 50:  # Minimum threshold
            return {
                'entity': best_match,
                'type': best_match['type'],
                'score': best_score
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

            # Try database fallback
            if self.db_config:
                logger.info(f"Trying direct {self.db_type.upper()} fallback...")
                return await self._execute_via_database(sql)
            else:
                raise Exception(f"Query failed: {str(e)}")
    
    async def _execute_via_database(self, sql: str) -> List[Dict]:
        """
        Execute SQL directly on database (fallback).

        Supports both Redshift and Postgres.
        """
        try:
            # Create connection if needed
            if not self._db_conn:
                if self.db_type == "redshift":
                    self._db_conn = redshift_connector.connect(
                        host=self.db_config['host'],
                        port=self.db_config.get('port', 5439),
                        database=self.db_config['database'],
                        user=self.db_config['user'],
                        password=self.db_config['password'],
                        ssl=self.db_config.get('ssl', True)
                    )
                elif self.db_type == "postgres":
                    self._db_conn = psycopg2.connect(
                        host=self.db_config['host'],
                        port=self.db_config.get('port', 5432),
                        database=self.db_config['database'],
                        user=self.db_config['user'],
                        password=self.db_config['password'],
                        sslmode='require' if self.db_config.get('ssl', True) else 'prefer'
                    )
                else:
                    raise Exception(f"Unsupported database type: {self.db_type}")

            cursor = self._db_conn.cursor()
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

            logger.info(f"✅ {self.db_type.upper()} fallback success: {len(results)} rows")
            return results

        except Exception as e:
            logger.error(f"❌ {self.db_type.upper()} fallback failed: {e}")
            raise Exception(f"Query execution failed: {str(e)}")

    async def _execute_via_redshift(self, sql: str) -> List[Dict]:
        """
        DEPRECATED: Use _execute_via_database instead.
        Kept for backward compatibility.
        """
        return await self._execute_via_database(sql)
    
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

        if self._db_conn:
            self._db_conn.close()
            logger.info(f"{self.db_type.upper()} connection closed")

        logger.info("Wren AI client closed")

    async def load_mdl(self):
        """
        Load MDL (Model Definition Language) from Wren AI.

        Fetches the deployed semantic layer and extracts models, metrics,
        and entities for improved accuracy and entity discovery.
        """
        try:
            logger.info("Loading MDL from Wren AI...")

            response = await self.client.get(
                f"{self.base_url}/v1/models",
                timeout=10
            )

            if response.status_code == 200:
                self._mdl = response.json()

                # Calculate MDL hash for version control
                if not self.mdl_hash:
                    self.mdl_hash = self._calculate_hash(self._mdl)

                # Extract models
                self._mdl_models = self._mdl.get("models", [])

                # Extract metrics
                self._mdl_metrics = self._mdl.get("metrics", [])

                # Update entities cache for fuzzy matching
                self._entities_cache = []

                # Add models to entities
                for model in self._mdl_models:
                    entity = {
                        "name": model.get("name", ""),
                        "type": "model",
                        "description": model.get("description", ""),
                        "columns": len(model.get("columns", [])),
                        "aliases": self._generate_aliases(model.get("name", ""), model.get("description", ""))
                    }
                    self._entities_cache.append(entity)

                    # Add columns as entities
                    for col in model.get("columns", []):
                        entity = {
                            "name": col.get("name", ""),
                            "type": "column",
                            "model": model.get("name", ""),
                            "description": col.get("description", ""),
                            "aliases": self._generate_aliases(col.get("name", ""), col.get("description", ""))
                        }
                        self._entities_cache.append(entity)

                # Add metrics to entities
                for metric in self._mdl_metrics:
                    entity = {
                        "name": metric.get("name", ""),
                        "type": "metric",
                        "description": metric.get("description", ""),
                        "baseObject": metric.get("baseObject", ""),
                        "aliases": self._generate_aliases(metric.get("name", ""), metric.get("description", ""))
                    }
                    self._entities_cache.append(entity)

                # Initialize schema formatter with loaded MDL
                if self._mdl_models:
                    self._schema_formatter = SchemaFormatter(
                        mdl_models=self._mdl_models,
                        mdl_metrics=self._mdl_metrics
                    )
                    logger.info("✅ Schema formatter initialized")

                    # Initialize cell retriever
                    self._cell_retriever = CellRetriever(
                        wren_client=self,
                        max_cells_per_column=10
                    )

                    # Load cell cache in background (non-blocking)
                    asyncio.create_task(self._cell_retriever.load_cell_cache())
                    logger.info("✅ Cell retriever initialized (loading cache in background)")

                logger.info(f"✅ MDL loaded successfully")
                logger.info(f"   - MDL hash: {self.mdl_hash[:8] if self.mdl_hash else 'N/A'}...")
                logger.info(f"   - Models: {len(self._mdl_models)}")
                logger.info(f"   - Metrics: {len(self._mdl_metrics)}")
                logger.info(f"   - Entities cached: {len(self._entities_cache)}")

                return True

            elif response.status_code == 404:
                logger.warning("⚠️ No MDL deployed")
                logger.warning("   Attempting to introspect database schema directly...")

                # Fallback: introspect database schema
                if self.db_config:
                    try:
                        success = await self._introspect_database_schema()
                        if success:
                            logger.info("✅ Successfully introspected database schema")
                            logger.info("   For better accuracy, deploy MDL via Wren UI")
                            return True
                    except Exception as db_error:
                        logger.error(f"❌ Database introspection failed: {db_error}")

                logger.warning("   Bot will work but with limited schema knowledge")
                logger.warning("   See docs/MDL_USAGE.md for MDL setup instructions")
                return False

            else:
                logger.warning(f"⚠️ Failed to load MDL: HTTP {response.status_code}")
                logger.warning("   Attempting to introspect database schema directly...")

                # Fallback: introspect database schema
                if self.db_config:
                    try:
                        success = await self._introspect_database_schema()
                        if success:
                            logger.info("✅ Successfully introspected database schema")
                            return True
                    except Exception as db_error:
                        logger.error(f"❌ Database introspection failed: {db_error}")

                return False

        except Exception as e:
            logger.warning(f"⚠️ Could not load MDL: {e}")
            logger.warning("   Attempting to introspect database schema directly...")

            # Fallback: introspect database schema
            if self.db_config:
                try:
                    success = await self._introspect_database_schema()
                    if success:
                        logger.info("✅ Successfully introspected database schema")
                        return True
                except Exception as db_error:
                    logger.error(f"❌ Database introspection failed: {db_error}")

            logger.warning("   Bot will work but with limited schema knowledge")
            logger.warning("   See docs/MDL_USAGE.md for MDL setup instructions")
            return False

    async def _introspect_database_schema(self) -> bool:
        """
        Fallback: Introspect database schema directly when MDL unavailable.

        Discovers tables and columns from database information_schema.

        Returns:
            True if successful, False otherwise
        """
        logger.info("🔍 Introspecting database schema...")
        logger.info(f"   Database type: {self.db_type}")
        logger.info(f"   Database host: {self.db_config.get('host', 'N/A')}")
        logger.info(f"   Database name: {self.db_config.get('database', 'N/A')}")

        try:
            # Connect to database
            if self.db_type == "postgres":
                if not POSTGRES_AVAILABLE:
                    logger.error("❌ psycopg2 not installed - install with: pip install psycopg2-binary")
                    return False

                logger.info("   Connecting to PostgreSQL...")
                import psycopg2.extras
                conn = psycopg2.connect(**self.db_config)
                logger.info("   ✅ Connected successfully!")

            elif self.db_type == "redshift":
                if not REDSHIFT_AVAILABLE:
                    logger.error("❌ redshift-connector not installed - install with: pip install redshift-connector")
                    return False

                logger.info("   Connecting to Redshift...")
                conn = redshift_connector.connect(**self.db_config)
                logger.info("   ✅ Connected successfully!")

            else:
                logger.error(f"❌ Unsupported database type: {self.db_type}")
                logger.error(f"   Supported types: postgres, redshift")
                return False

            cursor = conn.cursor()

            # Query to get tables and columns
            # Works for both PostgreSQL and Redshift
            query = """
                SELECT
                    t.table_schema,
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.ordinal_position
                FROM information_schema.tables t
                JOIN information_schema.columns c
                    ON t.table_schema = c.table_schema
                    AND t.table_name = c.table_name
                WHERE t.table_schema NOT IN ('information_schema', 'pg_catalog')
                    AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_schema, t.table_name, c.ordinal_position
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            # Group by table
            tables = {}
            for row in rows:
                schema, table, column, data_type, position = row
                table_key = f"{schema}.{table}"

                if table_key not in tables:
                    tables[table_key] = {
                        'name': table,
                        'schema': schema,
                        'columns': []
                    }

                tables[table_key]['columns'].append({
                    'name': column,
                    'type': data_type,
                    'position': position
                })

            cursor.close()
            conn.close()

            # Convert to MDL format
            self._mdl_models = []
            self._mdl_metrics = []
            self._entities_cache = []

            for table_key, table_info in tables.items():
                # Create model
                model = {
                    'name': table_info['name'],
                    'table_reference': {
                        'schema': table_info['schema'],
                        'table': table_info['name']
                    },
                    'columns': table_info['columns'],
                    'description': f"Table {table_key}"
                }
                self._mdl_models.append(model)

                # Add to entities cache
                entity = {
                    'name': table_info['name'],
                    'type': 'model',
                    'description': f"Table {table_key}",
                    'columns': len(table_info['columns']),
                    'aliases': self._generate_aliases(table_info['name'])
                }
                self._entities_cache.append(entity)

                # Add columns to entities cache
                for col in table_info['columns']:
                    col_entity = {
                        'name': col['name'],
                        'type': 'column',
                        'model': table_info['name'],
                        'description': f"{col['type']} column in {table_info['name']}",
                        'aliases': self._generate_aliases(col['name'])
                    }
                    self._entities_cache.append(col_entity)

            if len(self._mdl_models) == 0:
                logger.warning("⚠️ No tables found in database")
                logger.warning("   Check that:")
                logger.warning("   - Database has tables (not empty)")
                logger.warning("   - User has permissions to view information_schema")
                logger.warning("   - Schema filters are correct")
                return False

            logger.info(f"✅ Introspected {len(self._mdl_models)} tables")
            logger.info(f"   - Total entities: {len(self._entities_cache)}")

            return True

        except ImportError as e:
            logger.error(f"❌ Missing database driver: {e}")
            logger.error(f"   Install with: pip install psycopg2-binary  # for PostgreSQL")
            logger.error(f"             or: pip install redshift-connector  # for Redshift")
            return False
        except ConnectionError as e:
            logger.error(f"❌ Could not connect to database: {e}")
            logger.error(f"   Check that:")
            logger.error(f"   - Database host is reachable: {self.db_config.get('host')}")
            logger.error(f"   - Port is correct: {self.db_config.get('port')}")
            logger.error(f"   - Database exists: {self.db_config.get('database')}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to introspect database")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error message: {str(e)}")
            logger.error(f"   Database config:")
            logger.error(f"   - Type: {self.db_type}")
            logger.error(f"   - Host: {self.db_config.get('host', 'N/A')}")
            logger.error(f"   - Port: {self.db_config.get('port', 'N/A')}")
            logger.error(f"   - Database: {self.db_config.get('database', 'N/A')}")
            logger.error(f"   - User: {self.db_config.get('user', 'N/A')}")

            # Check for common error patterns
            error_str = str(e).lower()
            if 'authentication' in error_str or 'password' in error_str:
                logger.error("   → Looks like an authentication error - check DB_USER and DB_PASSWORD")
            elif 'timeout' in error_str or 'timed out' in error_str:
                logger.error("   → Connection timed out - check DB_HOST and network connectivity")
            elif 'refused' in error_str:
                logger.error("   → Connection refused - check DB_PORT and firewall rules")
            elif 'does not exist' in error_str:
                logger.error("   → Database or table not found - check DB_DATABASE")

            return False

    def _generate_aliases(self, name: str, description: str = "") -> List[str]:
        """
        Enhanced alias generation with comprehensive synonym matching.

        Creates variations like:
        - total_revenue -> revenue, total revenue, rev, sales, income, turnover, earnings
        - order_count -> orders, order count, num orders, number of orders, purchase count
        - customer_name -> customer, cust, client, buyer, user, account

        Args:
            name: Entity name
            description: Optional description to extract keywords from

        Returns:
            List of aliases (up to 15)
        """
        if not name:
            return []

        aliases = []
        name_lower = name.lower()

        # Remove common prefixes and add as alias
        for prefix in ['total_', 'num_', 'count_', 'avg_', 'sum_', 'max_', 'min_', 'total', 'num', 'count']:
            if name_lower.startswith(prefix):
                aliases.append(name_lower.replace(prefix, ''))
            if name_lower.startswith(prefix + '_'):
                aliases.append(name_lower.replace(prefix + '_', ''))

        # Replace underscores with spaces
        if '_' in name_lower:
            aliases.append(name_lower.replace('_', ' '))
            aliases.append(name_lower.replace('_', ''))  # Remove entirely

        # Enhanced business term mappings
        abbreviations = {
            'revenue': ['rev', 'sales', 'income', 'turnover', 'earnings'],
            'customer': ['cust', 'client', 'buyer', 'user', 'account'],
            'order': ['orders', 'purchase', 'purchases', 'transaction', 'transactions'],
            'product': ['products', 'item', 'items', 'sku', 'skus'],
            'user': ['users', 'member', 'members', 'customer', 'customers'],
            'count': ['num', 'number', 'total', 'qty', 'quantity'],
            'average': ['avg', 'mean'],
            'quantity': ['qty', 'amount', 'volume'],
            'price': ['cost', 'value', 'rate'],
            'date': ['time', 'timestamp', 'when'],
            'amount': ['value', 'total', 'sum'],
            'status': ['state', 'condition'],
            'type': ['kind', 'category', 'class'],
            'name': ['title', 'label'],
            'id': ['identifier', 'key'],
            'description': ['desc', 'details'],
            'address': ['location', 'addr'],
            'phone': ['telephone', 'tel'],
            'email': ['mail', 'e-mail'],
            'category': ['cat', 'group', 'type'],
        }

        # Add abbreviations if name contains these words
        for word, abbrevs in abbreviations.items():
            if word in name_lower:
                aliases.extend(abbrevs)
                # Also add variants with the word replaced
                for abbrev in abbrevs:
                    aliases.append(name_lower.replace(word, abbrev))

        # Extract keywords from description
        if description:
            desc_lower = description.lower()
            for word, abbrevs in abbreviations.items():
                if word in desc_lower and word not in name_lower:
                    aliases.extend(abbrevs)

        # Remove duplicates and the original name
        aliases = list(set(aliases))
        if name_lower in aliases:
            aliases.remove(name_lower)

        return aliases[:15]  # Limit to 15 aliases per entity

    def _calculate_hash(self, mdl: Dict) -> str:
        """
        Calculate SHA1 hash of MDL for version control.

        Args:
            mdl: MDL dictionary

        Returns:
            SHA1 hash string
        """
        mdl_str = json.dumps(mdl, sort_keys=True)
        return hashlib.sha1(mdl_str.encode()).hexdigest()

    def get_available_models(self) -> List[Dict]:
        """
        Get list of available data models from MDL.

        Returns:
            List of model dictionaries with name, description, columns
        """
        return [
            {
                "name": model.get("name", ""),
                "description": model.get("description", "No description"),
                "columns": len(model.get("columns", [])),
                "primaryKey": model.get("primaryKey", "")
            }
            for model in self._mdl_models
        ]

    def get_available_metrics(self) -> List[Dict]:
        """
        Get list of available metrics from MDL.

        Returns:
            List of metric dictionaries with name, description, baseObject
        """
        return [
            {
                "name": metric.get("name", ""),
                "description": metric.get("description", "No description"),
                "baseObject": metric.get("baseObject", ""),
                "timeGrain": metric.get("timeGrain", "")
            }
            for metric in self._mdl_metrics
        ]

    def get_schema_ddl(self) -> str:
        """
        Get schema in DDL format (for SQL generation).

        Returns:
            DDL-formatted schema string
        """
        if not self._schema_formatter:
            return ""
        return self._schema_formatter.to_ddl(
            include_comments=True,
            include_examples=True
        )

    def get_schema_markdown(self) -> str:
        """
        Get schema in Markdown format (for LLM reasoning).

        Returns:
            Markdown-formatted schema string
        """
        if not self._schema_formatter:
            return ""
        return self._schema_formatter.to_markdown(include_metrics=True)

    def get_schema_compact(self) -> str:
        """
        Get compact schema (for token efficiency).

        Returns:
            Compact schema string
        """
        if not self._schema_formatter:
            return ""
        return self._schema_formatter.to_compact()