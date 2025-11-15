# MDL (Model Definition Language) Usage Guide

## Overview

Wren AI uses **MDL (Model Definition Language)** as its semantic layer to dramatically improve SQL generation accuracy. MDL provides business context to the LLM, enabling it to understand relationships, metrics, and business logic.

**Key Benefits:**
- **Higher Accuracy**: MDL gives Claude context about your data model, reducing ambiguity
- **Business Semantics**: Define metrics, relationships, and calculated fields in business terms
- **dbt Integration**: Native support for dbt models and semantic layer
- **Consistent Logic**: Centralize business logic in one place

---

## What is MDL?

MDL is a declarative language that describes:

1. **Data Models**: Tables, views, and their columns
2. **Relationships**: How tables connect (foreign keys, joins)
3. **Metrics**: Pre-defined calculations (revenue, conversion rate, etc.)
4. **Semantic Properties**: Business names, descriptions, and metadata

### Example MDL

```yaml
models:
  - name: orders
    table_reference:
      schema: public
      table: orders
    columns:
      - name: order_id
        type: integer
        is_primary_key: true
      - name: customer_id
        type: integer
      - name: order_date
        type: date
      - name: total_amount
        type: decimal

  - name: customers
    table_reference:
      schema: public
      table: customers
    columns:
      - name: customer_id
        type: integer
        is_primary_key: true
      - name: name
        type: string
      - name: department
        type: string

relationships:
  - name: order_customer
    models:
      - name: orders
        column: customer_id
      - name: customers
        column: customer_id
    join_type: many_to_one

metrics:
  - name: total_revenue
    base_object: orders
    dimension:
      - name: order_date
    measure:
      - name: revenue
        expression: SUM(total_amount)
    description: "Total revenue from all orders"
```

---

## How MDL Improves Accuracy

### Without MDL:
**User Question**: "What's our revenue by department?"

**Problem**: Claude doesn't know:
- Which table contains revenue data
- How to join orders → customers → departments
- Whether "revenue" means gross, net, or something else

**Result**: Potentially incorrect SQL or error

### With MDL:
**User Question**: "What's our revenue by department?"

**MDL Context Provided**:
```yaml
- revenue metric is SUM(total_amount) from orders table
- orders join to customers via customer_id
- customers have department field
```

**Result**: Accurate SQL:
```sql
SELECT
  c.department,
  SUM(o.total_amount) as revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.department
```

---

## Using MDL with Wren AI Slack Bot

### 1. Set Up MDL in Wren AI

Wren AI manages MDL through its UI or config files. Ensure your MDL is deployed:

```bash
# Check Wren AI has your MDL loaded
curl http://wren-ai:8000/v1/models
```

### 2. Use `mdl_hash` Parameter

When Wren AI generates SQL, it uses the current MDL. To ensure consistency, use the `mdl_hash` parameter:

```python
# In wren_client.py - ask_question method
payload = {
    "query": question,
    "mdl_hash": self.current_mdl_hash  # Ensures consistent MDL version
}
```

**Current Implementation**: The Slack bot currently doesn't pass `mdl_hash`. This should be added for production use.

**Recommended Enhancement**:
```python
class WrenClient:
    def __init__(self, base_url, timeout, mdl_hash=None):
        self.mdl_hash = mdl_hash

    async def ask_question(self, question, user_context=None):
        payload = {"query": question}

        # Add MDL hash if available
        if self.mdl_hash:
            payload["mdl_hash"] = self.mdl_hash

        # ... rest of implementation
```

---

## Best Practices for MDL

### 1. Define Clear Relationships

```yaml
relationships:
  - name: order_to_customer
    models:
      - name: orders
        column: customer_id
      - name: customers
        column: customer_id
    join_type: many_to_one
    description: "Each order belongs to one customer"
```

**Impact**: Claude knows how to join tables without ambiguity.

### 2. Create Meaningful Metrics

```yaml
metrics:
  - name: monthly_recurring_revenue
    base_object: subscriptions
    dimension:
      - name: billing_month
    measure:
      - name: mrr
        expression: SUM(CASE WHEN status = 'active' THEN amount ELSE 0 END)
    description: "Monthly recurring revenue from active subscriptions"
```

**Impact**: Users can ask "What's our MRR?" and get accurate SQL.

### 3. Use Descriptive Names and Metadata

```yaml
columns:
  - name: created_at
    type: timestamp
    description: "Timestamp when the record was created"
    display_name: "Creation Date"
```

**Impact**: Claude understands intent even with ambiguous questions.

### 4. Define Calculated Fields

```yaml
calculated_fields:
  - name: days_since_order
    expression: DATEDIFF(day, order_date, CURRENT_DATE)
    description: "Number of days since order was placed"
```

**Impact**: Complex logic is centralized and reusable.

---

## dbt Integration

Wren AI has **native dbt integration**, allowing you to leverage existing dbt models as MDL.

### How It Works:

1. **dbt models** → Wren AI automatically discovers them
2. **dbt metrics** → Imported as Wren metrics
3. **dbt relationships** → Used for join logic
4. **dbt documentation** → Provides descriptions to Claude

### Setup (if using dbt):

```yaml
# wren-ai-service.yaml
dbt:
  enabled: true
  project_dir: /path/to/dbt/project
  profiles_dir: /path/to/dbt/profiles
  target: prod
```

### Benefits:

- **Single source of truth**: dbt already defines your data model
- **Governed analytics**: Wren AI uses approved dbt logic
- **Automatic updates**: MDL stays in sync with dbt changes

---

## Verifying MDL is Working

### 1. Check MDL is Loaded

```bash
# Query Wren AI for available models
curl http://wren-ai:8000/v1/models

# Response should show your models:
{
  "models": [
    {"name": "orders", "columns": [...], "metrics": [...]},
    {"name": "customers", "columns": [...]}
  ]
}
```

### 2. Test with Ambiguous Questions

**Good Test**: Ask questions that require MDL context:

```
/ask What's revenue by department?
/ask Show me top customers by lifetime value
/ask What's our conversion rate this month?
```

**Without MDL**: These would be ambiguous or incorrect.
**With MDL**: Claude generates accurate SQL using relationships and metrics.

### 3. Check Logs for MDL Usage

```bash
# In Wren AI logs, you should see:
"Using MDL hash: abc123..."
"Applied metric: total_revenue"
"Used relationship: order_to_customer"
```

---

## Common Issues

### Issue 1: "Table not found" errors

**Cause**: MDL schema doesn't match actual database schema.

**Fix**: Ensure MDL `table_reference` points to correct schema/table:
```yaml
table_reference:
  schema: public  # ← Must match actual schema
  table: orders   # ← Must match actual table name
```

### Issue 2: Inaccurate SQL despite MDL

**Cause**: MDL not being passed to LLM.

**Fix**: Verify `mdl_hash` is included in API calls (see implementation above).

### Issue 3: Metrics not recognized

**Cause**: Metric names don't match user language.

**Fix**: Add aliases and descriptions:
```yaml
metrics:
  - name: total_revenue
    aliases: ["revenue", "sales", "income"]
    description: "Total revenue including all sources"
```

---

## Recommended Enhancements for This Bot

Based on the research, here are recommended improvements:

### 1. **Add `mdl_hash` Parameter Support**

```python
# config.py
self.WREN_MDL_HASH = os.getenv("WREN_MDL_HASH")

# wren_client.py
async def ask_question(self, question, mdl_hash=None):
    payload = {"query": question}
    if mdl_hash:
        payload["mdl_hash"] = mdl_hash
```

### 2. **Fetch MDL Schema on Startup**

```python
# wren_client.py
async def load_mdl_schema(self):
    """Load MDL schema to cache entities."""
    try:
        response = await self.client.get(f"{self.base_url}/v1/models")
        self._schema_cache = response.json()

        # Extract all entities for fuzzy matching
        for model in self._schema_cache.get("models", []):
            self._entities_cache.append({
                "name": model["name"],
                "type": "model",
                "description": model.get("description", "")
            })

            # Add columns
            for col in model.get("columns", []):
                self._entities_cache.append({
                    "name": col["name"],
                    "type": "column",
                    "model": model["name"]
                })
```

### 3. **Display MDL Metrics in Help**

```python
# Add /metrics command to show available metrics
@app.command("/metrics")
async def show_metrics(ack, command, client):
    mdl_metrics = await wren.get_available_metrics()

    message = "📊 *Available Metrics:*\n\n"
    for metric in mdl_metrics:
        message += f"• *{metric['name']}*: {metric['description']}\n"

    await client.chat_postMessage(channel=command["channel_id"], text=message)
```

---

## Resources

- **Wren AI Documentation**: https://docs.getwren.ai/
- **MDL Specification**: Check Wren AI GitHub for MDL schema reference
- **dbt Integration**: https://docs.getwren.ai/integrations/dbt

---

## Summary

**MDL is critical for accuracy.** Without it, Claude is guessing at your data model. With it, Claude has precise context about:

- What tables exist and how they relate
- What metrics mean and how to calculate them
- What business terminology maps to which columns

**Recommendation**: Ensure Wren AI has a comprehensive MDL deployed before using the bot in production. This will dramatically reduce errors and improve user satisfaction.
