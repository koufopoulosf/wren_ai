# WREN AI PROJECT - REFACTORING ACTION PLAN

## Quick Reference: Code Smell Checklist

```
CRITICAL ISSUES (Fix Immediately):
[✓] Long functions (5+ functions >50 lines)
[✓] Code duplication (async pattern 3x, prompts 2x, DB connection 2x)
[✓] God object (WrenAssistant class - 4-5 responsibilities)
[✓] Missing error handling specificity (generic Exception catches)
[✓] No type contracts between modules (dict unpacking without validation)

HIGH PRIORITY (Fix within 1-2 weeks):
[✓] Tight coupling to Anthropic client (6+ locations)
[✓] Private attribute access (_db_conn)
[✓] Complex branching logic (3+ nested if/else)
[✓] Magic numbers scattered throughout
[✓] No test coverage (0% coverage)

MEDIUM PRIORITY (Fix within 2-4 weeks):
[✓] Missing abstractions (3 areas)
[✓] Inconsistent module organization
[✓] Large file (streamlit_app.py 965 lines)
[✓] Hard-coded configuration values
[✓] Inconsistent error handling patterns

LOW PRIORITY (Nice to have):
[✓] Logging improvements
[✓] Component documentation
[✓] Performance optimizations
```

---

## Concrete Examples With Before/After Code

### Example 1: Duplicate Async Pattern (CRITICAL)

**BEFORE** (3 locations, 40 lines of duplicate code):
```python
# sql_generator.py, lines 238-249
loop = asyncio.get_event_loop()
message = await loop.run_in_executor(
    None,
    lambda: self.anthropic.messages.create(
        model=self.model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
)
sql = message.content[0].text.strip()

# query_explainer.py, lines 73-85 (SAME PATTERN)
loop = asyncio.get_event_loop()
message = await loop.run_in_executor(
    None,
    lambda: self.client.messages.create(
        model=self.model,
        max_tokens=200,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )
)
explanation = message.content[0].text.strip()

# query_explainer.py, lines 143-155 (SAME PATTERN AGAIN)
loop = asyncio.get_event_loop()
message = await loop.run_in_executor(
    None,
    lambda: self.client.messages.create(
        model=self.model,
        max_tokens=250,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )
)
explanation = message.content[0].text.strip()
```

**AFTER** (Single utility, reusable everywhere):
```python
# src/llm_utils.py - NEW FILE
import asyncio
from anthropic import Anthropic
from typing import Optional

class LLMUtils:
    """Utilities for LLM API calls with proper async handling."""
    
    @staticmethod
    async def call_claude(
        client: Anthropic,
        model: str,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        timeout: Optional[int] = None
    ) -> str:
        """
        Call Claude API with proper async/await handling.
        
        Args:
            client: Anthropic client instance
            model: Model ID (e.g., 'claude-sonnet-4-20250514')
            prompt: User prompt
            max_tokens: Max tokens in response
            temperature: Response temperature (0.0-1.0)
            timeout: Optional timeout in seconds
            
        Returns:
            Response text from Claude
            
        Raises:
            LLMError: If API call fails
        """
        try:
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            return message.content[0].text.strip()
        except Exception as e:
            raise LLMError(f"Claude API call failed: {e}") from e

# Usage everywhere:
# ==================

# sql_generator.py
async def generate_sql(self, question: str, ...):
    schema_ddl = await self.get_schema_ddl()
    prompt = f"... {schema_ddl} ..."
    sql = await LLMUtils.call_claude(
        self.anthropic, 
        self.model, 
        prompt,
        max_tokens=2000
    )
    return sql

# query_explainer.py
async def explain(self, sql: str) -> str:
    prompt = f"Explain this SQL...\n{sql}"
    return await LLMUtils.call_claude(
        self.client,
        self.model,
        prompt,
        max_tokens=200,
        temperature=0.3
    )

# streamlit_app.py - classify_question method
classification_prompt = f"Classify: {question}"
response_text = await LLMUtils.call_claude(
    self.config.anthropic_client,
    self.config.ANTHROPIC_MODEL,
    classification_prompt,
    max_tokens=200
)
```

**Benefits**:
- Eliminates 40 lines of duplicate code
- Single place to fix async issues
- Better error handling
- Type hints for clarity
- Reusable across entire codebase

---

### Example 2: God Object Refactoring (CRITICAL)

**BEFORE** - WrenAssistant is doing too much:
```python
# streamlit_app.py, lines 234-557
class WrenAssistant:
    """Main application class - TOO MANY RESPONSIBILITIES!"""
    
    def __init__(self):
        self.config = Config()                    # 1. Config management
        self.sql_generator = None
        self.result_validator = None
        self.explainer = None
        self.schema_info = {"tables": []}
        self.initialized = False
    
    async def initialize(self):                   # 2. Initialization logic
        # ... initializes 3+ components
        
    async def classify_question(self, question):  # 3. Classification logic
        # ... complex classification with 2 prompts
        
    async def generate_conversational_response(...): # 4. Response generation
        # ... complex prompt engineering
        
    async def process_question(self, question):   # 5. Orchestration logic
        # ... coordinates entire pipeline
```

**AFTER** - Separated into focused classes:
```python
# src/classifiers.py - NEW FILE
class QuestionClassifier:
    """Classifies if question is about data or meta."""
    
    def __init__(self, client: Anthropic, model: str):
        self.client = client
        self.model = model
    
    async def classify(self, question: str) -> Classification:
        """Classify question type."""
        prompt = PromptTemplates.QUESTION_CLASSIFIER.format(
            question=question
        )
        response = await LLMUtils.call_claude(
            self.client, self.model, prompt
        )
        return Classification.from_json(response)
    
    async def handle_meta_question(self, question: str) -> str:
        """Generate response for meta questions."""
        prompt = PromptTemplates.META_RESPONSE.format(
            question=question
        )
        return await LLMUtils.call_claude(
            self.client, self.model, prompt, max_tokens=300
        )

# src/response_generators.py - NEW FILE
class ConversationalResponseGenerator:
    """Generates conversational responses for query results."""
    
    def __init__(self, client: Anthropic, model: str):
        self.client = client
        self.model = model
    
    async def generate(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        conversation_history: List[Dict] = None
    ) -> str:
        """Generate conversational response."""
        prompt = PromptTemplates.CONVERSATIONAL_RESPONSE.format(
            question=question,
            sql=sql,
            results=len(results),
            has_results=len(results) > 0
        )
        return await LLMUtils.call_claude(
            self.client, self.model, prompt, max_tokens=300
        )

# src/pipelines.py - NEW FILE
class QueryPipeline:
    """Orchestrates the query execution pipeline."""
    
    def __init__(
        self,
        classifier: QuestionClassifier,
        sql_gen: SQLGenerator,
        validator: ResultValidator,
        explainer: QueryExplainer,
        response_gen: ConversationalResponseGenerator
    ):
        self.classifier = classifier
        self.sql_gen = sql_gen
        self.validator = validator
        self.explainer = explainer
        self.response_gen = response_gen
    
    async def process(
        self,
        question: str,
        conversation_history: List[Dict] = None
    ) -> ProcessResult:
        """Execute full query pipeline."""
        
        # Step 1: Classify question
        classification = await self.classifier.classify(question)
        
        if not classification.is_data_query:
            response = await self.classifier.handle_meta_question(question)
            return ProcessResult.meta(response)
        
        # Step 2: Generate and execute SQL
        try:
            sql_result = await self.sql_gen.generate_sql(
                question,
                conversation_history=conversation_history
            )
            results = await self.sql_gen.execute_sql(sql_result.sql)
        except SQLGenerationError as e:
            return ProcessResult.error(str(e))
        
        # Step 3: Validate results
        is_valid, warnings = self.validator.validate_results(results, sql_result.sql)
        
        # Step 4: Generate explanation
        explanation = await self.response_gen.generate(
            question, sql_result.sql, results, conversation_history
        )
        
        return ProcessResult.success(
            sql=sql_result.sql,
            results=results,
            explanation=explanation,
            warnings=warnings if not is_valid else []
        )

# streamlit_app.py - MUCH SIMPLER NOW
class WrenAssistant:
    """Simplified assistant - orchestration only."""
    
    def __init__(self, pipeline: QueryPipeline):
        self.pipeline = pipeline
    
    async def process_question(
        self,
        question: str,
        conversation_history: list = None
    ) -> ProcessResult:
        """Process a user question."""
        return await self.pipeline.process(
            question, 
            conversation_history
        )
```

**Benefits**:
- Each class has ONE responsibility
- Easy to test independently
- Reusable components
- Better separation of concerns
- Easier to modify/extend individual pieces

---

### Example 3: Magic Numbers & Configuration (HIGH PRIORITY)

**BEFORE** (Scattered throughout codebase):
```python
# config.py, line 51
self._schema_cache_ttl = 300  # 5 minutes - where did this come from?

# streamlit_app.py, line 404
recent_history = conversation_history[-3:]  # Why 3?

# streamlit_app.py, line 409
if len(content) > 200:  # Why 200?
    content = content[:200] + "..."

# sql_generator.py, line 195
recent_history = conversation_history[-5:]  # Why 5? Different from above!

# result_validator.py, line 129
if negative_count > len(results) * 0.5:  # >50% - why 50%?
```

**AFTER** (Centralized configuration):
```python
# src/constants.py - NEW FILE
"""Application configuration constants."""

from typing import List

class CacheConfig:
    """Caching behavior configuration."""
    SCHEMA_TTL_SECONDS = 300          # 5 minutes
    SCHEMA_REFRESH_COOLDOWN = 60      # 1 minute minimum between refreshes
    RESULT_CACHE_TTL_SECONDS = 60     # 1 minute

class ConversationConfig:
    """Conversation context configuration."""
    RECENT_HISTORY_LIMIT = 5          # Number of recent messages to include
    HISTORY_TRUNCATION_LIMIT = 5      # Limit messages in history
    CONTENT_TRUNCATION_LIMIT = 300    # Characters before truncation
    CONTEXT_WINDOW_MESSAGES = 5       # Messages to include for context

class ValidationConfig:
    """Result validation thresholds."""
    NEGATIVE_VALUE_THRESHOLD = 0.5    # Alert if >50% of values are negative
    SUSPICIOUS_COLUMN_KEYWORDS: List[str] = [
        'revenue', 'price', 'cost', 'amount', 'total', 'value',
        'sales', 'income', 'profit', 'margin', 'balance'
    ]
    RESULT_ROW_LIMIT = 10000          # Warn if more rows returned
    RESULT_ROW_WARNING = 1000         # Threshold for warning

class LLMConfig:
    """LLM/Claude configuration."""
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    CLASSIFICATION_TEMPERATURE = 0.2
    EXPLANATION_TEMPERATURE = 0.3
    GENERATION_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 200
    CLASSIFICATION_MAX_TOKENS = 200
    EXPLANATION_MAX_TOKENS = 250
    GENERATION_MAX_TOKENS = 2000

class UIConfig:
    """UI/Streamlit configuration."""
    MAX_ROWS_DISPLAY = 100
    MAX_ROWS_EXPORT = 10000
    CHART_HEIGHT = 400
    MESSAGE_DISPLAY_LIMIT = 50       # Max messages to show in chat

class DatabaseConfig:
    """Database configuration."""
    DEFAULT_SCHEMA = 'public'
    CONNECTION_TIMEOUT = 10           # seconds
    QUERY_TIMEOUT = 30                # seconds

# Usage everywhere:
# ==================

# config.py
from constants import CacheConfig, LLMConfig

class Config:
    def __init__(self):
        self._schema_cache_ttl = CacheConfig.SCHEMA_TTL_SECONDS
        self.MAX_ROWS_DISPLAY = UIConfig.MAX_ROWS_DISPLAY

# sql_generator.py
from constants import ConversationConfig

async def generate_sql(self, question: str, ...):
    if conversation_history:
        recent = conversation_history[-ConversationConfig.RECENT_HISTORY_LIMIT:]

# streamlit_app.py
from constants import ConversationConfig

def generate_conversational_response(...):
    for msg in recent_history:
        if len(content) > ConversationConfig.CONTENT_TRUNCATION_LIMIT:
            content = content[:ConversationConfig.CONTENT_TRUNCATION_LIMIT] + "..."

# result_validator.py
from constants import ValidationConfig

def _check_suspicious_values(self, results):
    if negative_count > len(results) * ValidationConfig.NEGATIVE_VALUE_THRESHOLD:
        # warn
```

**Benefits**:
- Single source of truth for all configuration
- Easy to tune application behavior
- Self-documenting code
- Centralized dependency management
- Easy to compare settings across environments

---

## Refactoring Priority Matrix

```
           HIGH VALUE  │  LOW VALUE
        ────────────────────────────
HIGH     │ CRITICAL   │ NICE TO HAVE
EFFORT   │ FIX FIRST  │ SKIP UNLESS
         │            │ TIME PERMITS
        ────────────────────────────
LOW      │ QUICK WINS │ IGNORE
EFFORT   │ DO FIRST   │
         │            │
```

### CRITICAL (High Value, High Effort) - 2-3 weeks
1. Extract duplicate async pattern → LLMUtils
2. Refactor WrenAssistant → Separate classes
3. Create exception hierarchy
4. Add type contracts (dataclasses)

### QUICK WINS (High Value, Low Effort) - 1-2 days
1. Create constants.py file
2. Extract prompt templates
3. Remove duplicate imports
4. Add basic validation

### NICE TO HAVE (Low Value, High Effort) - 2-3 weeks
1. Refactor create_chart() with Strategy pattern
2. Add comprehensive logging
3. Performance optimizations
4. Add integration tests

### IGNORE (Low Value, Low Effort) - Skip
1. Minor code style improvements
2. Comment additions
3. Non-critical refactoring

---

## Dependency Diagram: BEFORE vs AFTER

### BEFORE (Tightly Coupled)
```
┌─────────────────────────┐
│   streamlit_app.py      │ ← Everything depends on this!
│  (965 lines)            │
├─────────────────────────┤
│ - WrenAssistant        │◄──┐
│ - init_session_state   │   │
│ - display_message      │   ├─ 5+ responsibilities
│ - create_chart         │   │
│ - classify_question    │   │
│ - generate_response    │◄──┘
│ - process_question     │
└─────────────────────────┘
         ▲
      ┌──┴──────────┬─────────────────┬──────────────┐
      │             │                 │              │
   config.py    SQLGenerator      QueryExplainer  ResultValidator
      │             │                 │              │
      └──────────────┴─────────────────┴──────────────┘
              ▼
         Anthropic Client (Direct coupling!)
```

### AFTER (Loosely Coupled)
```
┌──────────────────────────────────────────────────────┐
│          streamlit_app.py (200 lines)               │
│  - UI Orchestration Only                            │
│  - Delegates to AppContainer                        │
└──────────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────┐
│         AppContainer (Dependency Injection)         │
│  - Provides dependencies                            │
│  - Factory for object creation                      │
└──────────────────────────────────────────────────────┘
              │
    ┌─────────┴──────────┬──────────────┬──────────────┐
    │                    │              │              │
    ▼                    ▼              ▼              ▼
QueryPipeline      QuestionClassifier ResponseGen  Database
    │                    │              │              │
    ├─► SQLGenerator     │              │              │
    ├─► Validator        │              │              │
    └─► Explainer        │              │              │
                         │              │              │
                         └──────────────┴──────────────┘
                                    │
                                    ▼
                            LLMUtils (shared)
                                    │
                                    ▼
                            Anthropic Client
                         (Single abstraction point)
```

---

## Step-by-Step Refactoring Timeline

### Week 1: Foundation (CRITICAL FIRST)

**Day 1-2: Extract Duplicate Async Pattern**
- Create `src/llm_utils.py`
- Extract `LLMUtils.call_claude()` method
- Update 3 locations to use utility
- Test: All LLM calls still work

**Day 3-4: Exception Hierarchy**
- Create `src/exceptions.py`
- Define 5 custom exception types
- Update error handling (6+ locations)
- Add proper exception chaining

**Day 5: Extract Constants**
- Create `src/constants.py`
- Move 15+ magic numbers/strings
- Update imports in all files
- Verify no behavioral changes

### Week 2: Architecture (HIGH PRIORITY)

**Day 1-2: Create Data Classes**
- Create `src/models.py`
- Define SQLGenerationResult, QueryResult, ProcessResult, Classification
- Update method signatures
- Update type hints

**Day 3-4: Refactor WrenAssistant**
- Create `src/question_classifier.py` - Extract classification logic
- Create `src/response_generator.py` - Extract response generation
- Create `src/pipelines.py` - Add QueryPipeline class
- Update streamlit_app.py to use new classes

**Day 5: Dependency Injection**
- Create `src/container.py` - AppContainer for DI
- Update streamlit_app.py initialization
- Remove tight coupling

### Week 3: Polish (MEDIUM PRIORITY)

**Day 1-2: Extract Prompt Templates**
- Create `src/prompts.py`
- Move all prompt strings
- Add formatting helpers

**Day 3-4: Add Input Validation**
- Create `src/validators.py`
- Add APIResponseValidator
- Add SQL validation

**Day 5: Add Tests**
- Create `tests/unit/` directory
- Add 10+ unit tests
- Add 3-5 integration tests

---

## Measurement: Before → After Metrics

```
METRIC                      BEFORE      AFTER       IMPROVEMENT
────────────────────────────────────────────────────────────────
Largest File (lines)         965         200         79% reduction
Code Duplication             4 major     0           100% reduction
God Objects                  1           0           100% reduction
Long Functions (>80 lines)   5           0           100% reduction
Test Coverage                0%          60%+        60%+ gain
Cyclomatic Complexity Avg    8.5         3.2         62% reduction
Type Safety                  Partial     Complete    100% coverage
Module Cohesion              Low         High        Improved
```

---

## File Structure: After Refactoring

```
wren_ai/
├── src/
│   ├── __init__.py
│   ├── constants.py              # NEW - Configuration constants
│   ├── exceptions.py             # NEW - Custom exceptions
│   ├── models.py                 # NEW - Data classes
│   ├── prompts.py                # NEW - Prompt templates
│   ├── llm_utils.py              # NEW - Async LLM utilities
│   │
│   ├── config.py                 # REFACTORED - Config only
│   │
│   ├── database.py               # NEW - DB schema inspection
│   ├── sql_generator.py          # REFACTORED - Cleaner
│   ├── query_explainer.py        # REFACTORED - Use utils
│   ├── result_validator.py       # REFACTORED - Use constants
│   │
│   ├── classifiers.py            # NEW - Question classification
│   ├── response_generator.py     # NEW - Response generation
│   ├── pipelines.py              # NEW - Query pipeline
│   │
│   ├── ui_components.py          # NEW - UI rendering components
│   ├── chart_builders.py         # NEW - Chart strategy pattern
│   └── container.py              # NEW - Dependency injection
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # NEW - Fixtures
│   ├── unit/
│   │   ├── test_classifiers.py   # NEW
│   │   ├── test_sql_generator.py # NEW
│   │   └── test_validators.py    # NEW
│   └── integration/
│       ├── test_pipelines.py     # NEW
│       └── test_end_to_end.py    # NEW
│
├── streamlit_app.py              # SIMPLIFIED - UI only
├── requirements.txt
└── README.md
```

---

## Risk Mitigation

### Risk 1: Breaking Changes During Refactoring
**Mitigation**:
- Use feature flags for new code
- Keep old implementations alongside new
- Test thoroughly before switchover
- Have rollback plan ready

### Risk 2: Performance Degradation
**Mitigation**:
- Profile before/after refactoring
- Cache aggressively
- Monitor API call counts
- Add performance tests

### Risk 3: Integration Issues
**Mitigation**:
- Write integration tests FIRST
- Mock external dependencies
- Test with real database data
- Use staging environment

---

## Success Criteria

```
✓ All tests passing (>60% coverage)
✓ No code duplication
✓ All functions <50 lines (except special cases)
✓ All cyclomatic complexity <5
✓ All modules have single responsibility
✓ All dependencies explicitly passed (DI)
✓ All magic numbers extracted to constants
✓ Comprehensive error handling with custom exceptions
✓ Type hints on all functions
✓ Logging at all critical points
```

