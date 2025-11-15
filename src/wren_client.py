"""
Wren AI API Client

Async wrapper for Wren AI's REST API with:
- Retry logic with exponential backoff
- Comprehensive error handling
- Health checks
- Schema discovery
"""

import logging
import asyncio
from typing import Dict, List, Optional
import httpx
from asyncio_throttle import Throttle

logger = logging.getLogger(__name__)


class WrenClient:
    """
    Async client for Wren AI REST API.
    
    Handles:
    - Natural language to SQL conversion
    - SQL execution
    - Schema discovery
    - Health checks
    - Rate limiting and retries
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize Wren AI client.
        
        Args:
            base_url: Wren AI service URL (e.g., http://wren-ai:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Rate limiting: 10 requests per second
        self.throttle = Throttle(rate_limit=10, period=1.0)
        
        logger.info(f"✅ Wren client initialized: {base_url}")
    
    async def ask_question(
        self,
        question: str,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Convert natural language question to SQL.
        
        Args:
            question: Natural language query
            user_context: Optional context (department, role, etc.)
        
        Returns:
            {
                'sql': str,              # Generated SQL
                'confidence': float,     # Confidence score 0-1
                'suggestions': list,     # Alternative interpretations
                'metadata': dict         # Additional info
            }
        
        Raises:
            Exception: If Wren AI fails after retries
        """
        payload = {
            "query": question,
            "context": user_context or {}
        }
        
        # Retry with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.throttle:
                    logger.info(
                        f"Asking Wren AI: '{question[:100]}...' "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    
                    response = await self.client.post(
                        f"{self.base_url}/api/v1/asks",
                        json=payload
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # Extract SQL and confidence
                    sql = result.get("sql", "")
                    confidence = result.get("confidence", 0.0)
                    suggestions = result.get("suggestions", [])
                    
                    logger.info(
                        f"✅ Wren AI response: SQL length={len(sql)}, "
                        f"confidence={confidence:.2f}"
                    )
                    
                    return {
                        "sql": sql,
                        "confidence": confidence,
                        "suggestions": suggestions,
                        "metadata": result.get("metadata", {})
                    }
            
            except httpx.HTTPStatusError as e:
                error_text = e.response.text[:200]
                logger.error(
                    f"❌ HTTP {e.response.status_code} from Wren AI: {error_text}"
                )
                
                if attempt == max_retries - 1:
                    raise Exception(
                        f"Wren AI returned error {e.response.status_code}. "
                        "Please check Wren AI logs or try rephrasing your question."
                    )
            
            except httpx.TimeoutException:
                logger.error(f"⏱️  Wren AI timeout (attempt {attempt + 1})")
                
                if attempt == max_retries - 1:
                    raise Exception(
                        "Wren AI is taking too long to respond. "
                        "Please try again or simplify your question."
                    )
            
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}", exc_info=True)
                
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to connect to Wren AI: {str(e)}")
            
            # Exponential backoff: 1s, 2s, 4s
            wait_time = 2 ** attempt
            logger.info(f"⏳ Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
        
        raise Exception("Failed to get response from Wren AI after all retries")
    
    async def execute_sql(self, sql: str) -> List[Dict]:
        """
        Execute SQL query via Wren AI.
        
        Args:
            sql: SQL query to execute
        
        Returns:
            List of result rows as dictionaries
        
        Raises:
            Exception: If execution fails
        """
        try:
            async with self.throttle:
                logger.info(f"Executing SQL via Wren AI (length: {len(sql)})")
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/execute",
                    json={"sql": sql}
                )
                response.raise_for_status()
                
                result = response.json()
                data = result.get("data", [])
                
                logger.info(f"✅ Query executed successfully: {len(data)} rows")
                return data
        
        except httpx.HTTPStatusError as e:
            error_msg = e.response.text[:300]
            logger.error(f"❌ SQL execution failed: {error_msg}")
            
            # Try to extract meaningful error message
            if "syntax error" in error_msg.lower():
                raise Exception(
                    "SQL syntax error. Please try rephrasing your question."
                )
            elif "timeout" in error_msg.lower():
                raise Exception(
                    "Query timed out. Try adding more filters or a shorter time period."
                )
            elif "permission" in error_msg.lower():
                raise Exception(
                    "Permission denied. You may not have access to this data."
                )
            else:
                raise Exception(f"Query failed: {error_msg}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error executing SQL: {e}", exc_info=True)
            raise Exception(f"Failed to execute query: {str(e)}")
    
    async def get_schema(self) -> Dict:
        """
        Get database schema information from Wren AI.
        
        Returns:
            Schema information including tables, columns, relationships
        """
        try:
            async with self.throttle:
                logger.info("Fetching schema from Wren AI")
                
                response = await self.client.get(
                    f"{self.base_url}/api/v1/schema"
                )
                response.raise_for_status()
                
                schema = response.json()
                
                table_count = len(schema.get("tables", []))
                logger.info(f"✅ Retrieved schema: {table_count} tables")
                
                return schema
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch schema: {e}")
            return {"tables": [], "relationships": []}
    
    async def search_entities(
        self, 
        search_term: str,
        entity_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for entities (tables, columns, metrics) in schema.
        
        Args:
            search_term: Term to search for
            entity_type: Optional filter ('table', 'column', 'metric')
        
        Returns:
            List of matching entities
        """
        try:
            async with self.throttle:
                params = {"q": search_term}
                if entity_type:
                    params["type"] = entity_type
                
                response = await self.client.get(
                    f"{self.base_url}/api/v1/search",
                    params=params
                )
                response.raise_for_status()
                
                results = response.json().get("results", [])
                logger.info(f"Found {len(results)} entities matching '{search_term}'")
                
                return results
        
        except Exception as e:
            logger.error(f"❌ Entity search failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """
        Check if Wren AI service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=5
            )
            
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.info("✅ Wren AI health check passed")
            else:
                logger.warning(
                    f"⚠️  Wren AI health check failed: HTTP {response.status_code}"
                )
            
            return is_healthy
        
        except Exception as e:
            logger.error(f"❌ Wren AI health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client gracefully."""
        await self.client.aclose()
        logger.info("Wren AI client closed")