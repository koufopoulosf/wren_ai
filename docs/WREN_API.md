# Wren AI OSS API Documentation

> **Research Date:** November 15, 2024
> **Wren AI Version:** v0.25.0+
> **API Version:** v1

## Overview

Wren AI OSS provides a **REST API** for Text-to-SQL conversion and query execution. The API is **asynchronous** and uses a **polling pattern** where you submit a request, receive a `query_id`, then poll for results.

---

## Base URL

For self-hosted deployments:
```
http://wren-ai:8000/v1
```

For production, replace with your Wren AI service URL.

---

## Authentication

Self-hosted Wren AI OSS does **not require authentication** by default. For production, implement authentication at the reverse proxy level (nginx, Traefik, etc.).

---

## API Endpoints

### 1. Text-to-SQL (Ask API)

Convert natural language questions to SQL queries.

#### **POST /v1/asks**

Submit a question for SQL generation.

**Request:**
```json
{
  "query": "What was revenue last month?",
  "mdl_hash": "optional-model-hash",
  "histories": [
    {
      "question": "What was revenue last week?",
      "sql": "SELECT SUM(amount) FROM orders WHERE ..."
    }
  ],
  "ignore_sql_generation_reasoning": false,
  "enable_column_pruning": false,
  "use_dry_plan": false,
  "allow_dry_plan_fallback": true,
  "custom_instruction": "Only use tables in the sales schema"
}
```

**Response:**
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes:**
- `200 OK` - Request accepted
- `400 Bad Request` - Invalid request body
- `500 Internal Server Error` - Server error

---

#### **GET /v1/asks/{query_id}/result**

Poll for the Text-to-SQL result.

**Parameters:**
- `query_id` (path) - UUID returned from POST /v1/asks

**Response:**
```json
{
  "status": "finished",
  "type": "TEXT_TO_SQL",
  "rephrased_question": "What was the total revenue for last month?",
  "intent_reasoning": "User wants to see total revenue for the previous month",
  "sql_generation_reasoning": "Generated SQL to sum revenue from orders table with date filter",
  "retrieved_tables": ["orders", "customers"],
  "response": [
    {
      "sql": "SELECT SUM(amount) FROM orders WHERE date >= '2024-10-01' AND date < '2024-11-01'",
      "type": "llm"
    }
  ],
  "error": null,
  "trace_id": "trace-123"
}
```

**Status Values:**
- `"understanding"` - Analyzing the question
- `"searching"` - Finding relevant tables
- `"planning"` - Creating query plan
- `"generating"` - Generating SQL
- `"correcting"` - Fixing SQL errors
- `"finished"` - ✅ SQL ready
- `"failed"` - ❌ Error occurred
- `"stopped"` - User cancelled

**Polling Strategy:**
```python
import time
import httpx

async def ask_and_wait(question: str, max_wait: int = 30):
    client = httpx.AsyncClient()

    # 1. Submit question
    response = await client.post(
        "http://wren-ai:8000/v1/asks",
        json={"query": question}
    )
    query_id = response.json()["query_id"]

    # 2. Poll for result
    start = time.time()
    while time.time() - start < max_wait:
        result = await client.get(
            f"http://wren-ai:8000/v1/asks/{query_id}/result"
        )
        data = result.json()

        if data["status"] in ["finished", "failed", "stopped"]:
            return data

        await asyncio.sleep(1)  # Poll every 1 second

    raise TimeoutError("Query timed out")
```

---

#### **GET /v1/asks/{query_id}/streaming-result**

Stream results in real-time via Server-Sent Events (SSE).

**Response:** `text/event-stream`

**Example:**
```python
async for line in client.stream(
    "GET",
    f"http://wren-ai:8000/v1/asks/{query_id}/streaming-result"
):
    # Process SSE events
    print(line)
```

---

#### **PATCH /v1/asks/{query_id}**

Stop an in-progress ask operation.

**Request:**
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 2. SQL Execution API

Execute SQL queries and get results.

#### **POST /v1/sql-answers**

Submit SQL for execution.

**Request:**
```json
{
  "sql": "SELECT SUM(amount) FROM orders WHERE date >= '2024-10-01'",
  "mdl_hash": "optional-model-hash"
}
```

**Response:**
```json
{
  "query_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

---

#### **GET /v1/sql-answers/{query_id}**

Get SQL execution results.

**Response:**
```json
{
  "status": "finished",
  "results": [
    {
      "column1": "value1",
      "column2": "value2"
    }
  ],
  "error": null
}
```

**Status Values:**
- `"preprocessing"` - Preparing query
- `"executing"` - Running SQL
- `"finished"` - ✅ Results ready
- `"failed"` - ❌ Execution error

---

#### **GET /v1/sql-answers/{query_id}/streaming**

Stream SQL results via SSE.

**Response:** `text/event-stream`

---

### 3. Schema & Models

> **Note:** Schema/model access is typically via the **Wren UI GraphQL API** or database query. The REST API v1 doesn't directly expose schema endpoints.

**Alternative:** Query models via Wren UI's GraphQL:
```graphql
query GetModels {
  models {
    name
    displayName
    description
    columns {
      name
      type
    }
  }
}
```

---

### 4. Additional Endpoints

#### **GET /v1/question-recommendation**

Get suggested questions based on schema.

#### **POST /v1/chart**

Generate chart configuration from SQL results.

#### **GET /v1/semantics-description**

Get semantic descriptions of data entities.

---

## Health Check

```bash
curl http://wren-ai:8000/health
```

**Response:**
```json
{
  "status": "ok"
}
```

---

## Error Handling

**Standard Error Response:**
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error in SQL query"
  }
}
```

**Common Error Codes:**
- `INVALID_SQL` - SQL syntax error
- `TIMEOUT` - Query took too long
- `CONNECTION_ERROR` - Database connection failed
- `NOT_FOUND` - Query ID not found
- `INTERNAL_ERROR` - Server error

---

## Rate Limiting

Self-hosted Wren AI has **no built-in rate limiting**. Implement at application level or reverse proxy.

**Recommended limits:**
- 10 requests/second per user
- 100 active queries per user

---

## Best Practices

### 1. Always Use Polling with Timeout

```python
async def poll_with_timeout(query_id, max_wait=30, poll_interval=1):
    start = time.time()
    while time.time() - start < max_wait:
        result = await get_result(query_id)
        if is_finished(result):
            return result
        await asyncio.sleep(poll_interval)
    raise TimeoutError()
```

### 2. Handle All Status States

```python
def handle_result(data):
    status = data["status"]

    if status == "finished":
        return data["response"]
    elif status == "failed":
        raise Exception(data["error"]["message"])
    elif status == "stopped":
        raise Exception("Query was cancelled")
    else:
        # Still processing
        return None
```

### 3. Include Context for Better Results

```python
# Bad
{"query": "show revenue"}

# Good
{
    "query": "show revenue",
    "histories": [
        {"question": "What tables do we have?", "sql": "SHOW TABLES"}
    ],
    "custom_instruction": "Only use public schema"
}
```

### 4. Cache Model Hash

The `mdl_hash` parameter helps Wren AI cache models. Reuse the same hash for the same schema.

---

## Migration from Current Code

### Current (Incorrect) Assumptions:

```python
# ❌ Current code assumes synchronous API
response = await client.post(
    f"{base_url}/api/v1/ask",  # Wrong endpoint
    json={"query": question}
)
sql = response.json()["sql"]  # Wrong - no immediate SQL
```

### Correct Implementation:

```python
# ✅ Correct async/polling approach
# 1. Submit question
response = await client.post(
    f"{base_url}/v1/asks",  # Correct endpoint
    json={"query": question}
)
query_id = response.json()["query_id"]

# 2. Poll for result
while True:
    result = await client.get(
        f"{base_url}/v1/asks/{query_id}/result"
    )
    data = result.json()

    if data["status"] == "finished":
        sql = data["response"][0]["sql"]
        break
    elif data["status"] == "failed":
        raise Exception(data["error"]["message"])

    await asyncio.sleep(1)
```

---

## Example: Complete Workflow

```python
import httpx
import asyncio
import time

class WrenAIClient:
    def __init__(self, base_url="http://wren-ai:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60)

    async def ask_question(self, question: str, max_wait: int = 30):
        """
        Ask question and wait for SQL.

        Returns:
            {
                "sql": "SELECT ...",
                "confidence": 0.95,
                "tables_used": ["orders"]
            }
        """
        # 1. Submit question
        response = await self.client.post(
            f"{self.base_url}/v1/asks",
            json={"query": question}
        )
        query_id = response.json()["query_id"]

        # 2. Poll for result
        start = time.time()
        while time.time() - start < max_wait:
            result = await self.client.get(
                f"{self.base_url}/v1/asks/{query_id}/result"
            )
            data = result.json()

            if data["status"] == "finished":
                return {
                    "sql": data["response"][0]["sql"],
                    "tables_used": data["retrieved_tables"],
                    "reasoning": data.get("sql_generation_reasoning")
                }
            elif data["status"] == "failed":
                raise Exception(data["error"]["message"])

            await asyncio.sleep(1)

        raise TimeoutError(f"Query timed out after {max_wait}s")

    async def execute_sql(self, sql: str, max_wait: int = 30):
        """
        Execute SQL and wait for results.

        Returns:
            List of result rows
        """
        # 1. Submit SQL
        response = await self.client.post(
            f"{self.base_url}/v1/sql-answers",
            json={"sql": sql}
        )
        query_id = response.json()["query_id"]

        # 2. Poll for result
        start = time.time()
        while time.time() - start < max_wait:
            result = await self.client.get(
                f"{self.base_url}/v1/sql-answers/{query_id}"
            )
            data = result.json()

            if data["status"] == "finished":
                return data["results"]
            elif data["status"] == "failed":
                raise Exception(data["error"]["message"])

            await asyncio.sleep(1)

        raise TimeoutError(f"Execution timed out after {max_wait}s")

# Usage
async def main():
    client = WrenAIClient()

    # Ask question
    result = await client.ask_question("What was revenue last month?")
    print(f"Generated SQL: {result['sql']}")

    # Execute SQL
    rows = await client.execute_sql(result['sql'])
    print(f"Results: {rows}")

asyncio.run(main())
```

---

## Additional Resources

- **GitHub:** https://github.com/Canner/WrenAI
- **Documentation:** https://docs.getwren.ai/
- **API Reference:** https://wrenai.readme.io/reference/

---

## Changelog

- **v0.25.0** - Added comprehensive REST API with `/v1/asks` and `/v1/sql-answers`
- **Earlier versions** - GraphQL-only API

---

**Last Updated:** November 15, 2024
