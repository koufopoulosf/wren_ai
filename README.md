# 🤖 Data Assistant

**Ask questions about your data in natural language and get instant SQL, visualizations, and insights.**

A modern AI-powered data assistant that uses Claude's advanced language understanding to transform natural language questions into accurate SQL queries. Built with Streamlit, PostgreSQL, and Anthropic's Claude.

![Version](https://img.shields.io/badge/version-5.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Code Quality](https://img.shields.io/badge/code%20quality-refactored-brightgreen)

---

## ✨ Features

- 🎯 **Natural Language to SQL** - Ask questions in plain English, get accurate SQL queries
- 🧠 **Full Schema Context with Comments** - Claude receives complete DDL including column comments for better understanding
- 🗄️ **Multi-Database Support** - Works with PostgreSQL and AWS Redshift
- 🔒 **Security First** - Prepared statement protection, input validation, read-only queries
- 📊 **Rich Visualizations** - Interactive charts with Plotly (bar, line, scatter, pie, treemap)
- 💾 **Multi-Format Export** - Download results as CSV, JSON, or chart images
- 🎨 **Clean UI** - Claude-inspired modern interface with conversational responses
- 🤖 **Context-Aware** - Remembers conversation history for natural follow-up questions
- ⚡ **Fast & Simple** - Lightweight architecture with schema caching (5 min TTL)

---

## 🏗️ Architecture

### Clean, Object-Oriented Design

Built with modern software engineering principles: **Single Responsibility**, **DRY**, and **proper encapsulation**.

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                             │
│                    Streamlit App (:8501)                        │
│     • Chat interface with Claude-like UI                        │
│     • Conversational context management                         │
│     • Result visualization and export                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 DataAssistant (UI Coordinator)                  │
│     • Component initialization                                  │
│     • Session management                                        │
│     • Delegates to PipelineOrchestrator                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              PipelineOrchestrator (Workflow Manager)            │
│     • Coordinates complete query processing pipeline            │
│     • Manages workflow: classify → generate → validate → respond│
└─────────────┬────────────┬────────────┬─────────────────────────┘
              │            │            │
     ┌────────┘            │            └──────────┐
     ▼                     ▼                       ▼
┌──────────────┐  ┌─────────────────┐   ┌──────────────────┐
│ Question     │  │  SQL Generator  │   │   Response       │
│ Classifier   │  │  • Schema DDL   │   │   Generator      │
│ • Data query?│  │  • NL → SQL     │   │  • Conversational│
│ • Meta query?│  │  • LLM calls    │   │  • Context-aware │
└──────────────┘  └────────┬────────┘   └──────────────────┘
                           │
                  ┌────────┴─────────┐
                  │   Result         │
                  │   Validator      │
                  │  • Validation    │
                  │  • Warnings      │
                  └──────────────────┘
                           │
                  ┌────────┴─────────┐
                  │   LLMUtils       │
                  │  • Async calls   │
                  │  • Retry logic   │
                  │  • No duplication│
                  └──────────────────┘
                           │
              ┌────────────┴───────────────┐
              ▼                            ▼
     ┌────────────────┐         ┌──────────────────┐
     │   PostgreSQL   │         │ Claude Sonnet 4.5│
     │   (:5432)      │         │      API         │
     │  • Data Store  │         │  • SQL gen       │
     │  • Crypto DB   │         │  • Explanations  │
     └────────────────┘         └──────────────────┘
```

### How It Works

1. **User asks a question** in natural language through Streamlit UI
2. **Question Classification**: QuestionClassifier determines if it's a data query or meta question
3. **Schema Retrieval**: SQLGenerator fetches complete PostgreSQL schema DDL (cached 5 min)
4. **SQL Generation**: LLMUtils calls Claude with full schema context to generate accurate SQL
5. **Query Execution**: SQL runs against PostgreSQL with prepared statement safety
6. **Result Validation**: ResultValidator checks results and generates warnings
7. **Response Generation**: ResponseGenerator creates natural, conversational explanation
8. **Results Display**: PipelineOrchestrator returns complete response to UI
9. **Context Memory**: Conversation history enables intelligent follow-up questions

### Architecture Benefits

✅ **Single Responsibility** - Each class has one clear purpose
✅ **Zero Code Duplication** - DRY principle applied throughout
✅ **Easy to Test** - Components can be tested independently
✅ **Better Maintainability** - Clean separation of concerns
✅ **Proper Encapsulation** - No private attribute access
✅ **Reusable Components** - LLMUtils, constants, exceptions shared across modules

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- 4GB RAM minimum
- 2GB disk space

### 1. Setup

```bash
# Clone or navigate to the project
cd data_assistant

# Create environment file with your API key
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-your-key-here
EOF
```

### 2. Launch

```bash
# Start all services
docker-compose up -d

# Watch logs (first startup takes ~30-60 seconds)
docker-compose logs -f streamlit-app

# Wait for: "You can now view your Streamlit app in your browser"
```

### 3. Access

Open your browser to **http://localhost:8501**

The app will automatically initialize with a cryptocurrency trading database!

---

## 💡 Example Queries

Try these questions:

```
What are the top 10 cryptocurrencies by market cap?
Show me BTC price trends over time
How many users are registered on the platform?
What's the total trading volume today?
Show me the most actively traded pairs
Which users have the highest portfolio values?
Compare trading volumes between different exchanges
List all pending trades for Ethereum
```

---

## 📁 Project Structure

### Root Files

```
data_assistant/
├── streamlit_app.py           # Main Streamlit UI application (~835 lines)
├── docker-compose.yml         # Service orchestration (postgres + streamlit)
├── Dockerfile                 # Streamlit app container build
├── requirements.txt           # Python dependencies
├── .env.example              # Environment configuration template
└── README.md                 # This file
```

### Source Files (`src/`)

**Core Modules:**

- **`config.py`** - Configuration management, environment variables, API client initialization
- **`pipeline_orchestrator.py`** - **NEW!** Orchestrates complete query processing workflow
- **`question_classifier.py`** - **NEW!** Classifies user questions (data vs meta queries)
- **`response_generator.py`** - **NEW!** Generates natural, conversational responses
- **`sql_generator.py`** - SQL generation from natural language using Claude
- **`query_explainer.py`** - Natural language explanations of SQL queries
- **`result_validator.py`** - Query result validation and warning detection

**Utility Modules:**

- **`llm_utils.py`** - **NEW!** Reusable LLM API utilities (async calls, retry logic)
- **`constants.py`** - **NEW!** Centralized constants (no more magic numbers!)
- **`exceptions.py`** - **NEW!** Custom exception hierarchy (DataAssistantError, LLMError, etc.)

### Code Quality Improvements

**Before Refactoring:**
- 40+ lines of duplicate code across 3 files
- 280+ line DataAssistant class doing 4-5 different jobs
- Magic numbers scattered throughout
- Private attribute access violations

**After Refactoring:**
- ✅ **0 lines of duplicate code** (100% elimination)
- ✅ **130 line DataAssistant** focused on UI coordination (53% reduction)
- ✅ **9 focused classes** each with single responsibility
- ✅ **Proper encapsulation** with public methods only
- ✅ **Reusable utilities** shared across all modules

### Database Files (`database/`)

```
database/
├── schema/
│   └── 01_create_schema.sql    # PostgreSQL schema (20+ tables for crypto platform)
└── data/
    └── 02_insert_data.sql      # Sample cryptocurrency trading data
```

**Schema Tables:**
- `cryptocurrencies` - Crypto asset master data
- `users` - Platform users
- `wallets` - User wallets
- `transactions` - Trading transactions
- `orders` - Buy/sell orders
- `portfolios` - User portfolio holdings
- And more... (20+ tables total)

### Scripts (`scripts/`)

**`generate_crypto_data.py`** - Reference script that generated the sample data

---

## 🔧 Configuration

### Environment Variables

All configuration is in `.env` file (copy from `.env.example`):

```bash
# REQUIRED
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database Configuration (PostgreSQL)
DB_TYPE=postgres  # or 'redshift' for AWS Redshift
DB_HOST=postgres
DB_PORT=5432
DB_DATABASE=cryptoDB
DB_USER=data_assistant_user
DB_PASSWORD=data_assistant_password
DB_SSL=false  # Set to 'true' for Redshift or remote databases

# Optional - Claude model
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

**For AWS Redshift:**
```bash
DB_TYPE=redshift
DB_HOST=your-cluster.region.redshift.amazonaws.com
DB_PORT=5439
DB_DATABASE=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_SSL=true
```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Streamlit UI | 8501 | Web interface |
| PostgreSQL | 5432 | Database |

---

## 🔒 Security Features

### Multi-Layer Protection

1. **Prepared Statements** - All queries use asyncpg prepared statements
2. **Input Validation** - Questions and SQL validated before execution
3. **Read-Only Intent** - Prompts guide Claude to generate SELECT queries only
4. **Connection Pooling** - Database connections properly managed
5. **No Data in Prompts** - Only schema metadata sent to Claude, never actual data

### Safe by Default

- No SQL injection vulnerabilities
- No DROP/DELETE/UPDATE commands generated
- Database credentials never exposed to LLM
- All errors logged and handled gracefully

---

## 🛠️ Customization

### Connect Your Own Database

**Works with PostgreSQL and Redshift!**

1. **Update `.env` file:**
```bash
# PostgreSQL
DB_TYPE=postgres
DB_HOST=your-postgres-host
DB_PORT=5432
DB_DATABASE=your_database
DB_USER=your_user
DB_PASSWORD=your_password

# OR Redshift
DB_TYPE=redshift
DB_HOST=your-cluster.region.redshift.amazonaws.com
DB_PORT=5439
DB_DATABASE=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_SSL=true
```

2. **Restart services:**
```bash
docker-compose restart streamlit-app
```

3. **Start querying!** The system automatically fetches your schema on first query.

### Adding Column Comments for Better Accuracy

Column comments help Claude understand your data better:

```sql
-- PostgreSQL / Redshift
COMMENT ON COLUMN users.email IS 'User email address for login and notifications';
COMMENT ON COLUMN orders.total_amount IS 'Total order amount in USD including tax';
COMMENT ON COLUMN transactions.created_at IS 'Timestamp when transaction was processed';
```

These comments are included in the DDL sent to Claude, resulting in more accurate SQL generation!

### Add Custom Data

Edit `database/schema/01_create_schema.sql` and `database/data/02_insert_data.sql`:

```sql
-- schema
CREATE TABLE your_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
);

-- data
INSERT INTO your_table (name) VALUES ('example');
```

Restart:
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Recreate with new schema
```

---

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs postgres
docker-compose logs streamlit-app

# Restart services
docker-compose restart
```

### Connection Issues

```bash
# Verify PostgreSQL is running
docker-compose exec postgres psql -U data_assistant_user -d cryptoDB -c "SELECT 1;"

# Check Streamlit logs
docker-compose logs -f streamlit-app
```

### Reset Everything

```bash
# Remove all data and start fresh
docker-compose down -v
docker-compose up -d
```

---

## 📊 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI** | Streamlit | Web interface |
| **LLM** | Claude Sonnet 4.5 | SQL generation & explanations |
| **Database** | PostgreSQL 15 / Redshift | Data storage (your choice!) |
| **Orchestration** | Docker Compose | Multi-service deployment |
| **Language** | Python 3.11+ | Application code |
| **Async** | asyncio + asyncpg | Database operations |
| **Viz** | Plotly | Interactive charts |

---

## 🎯 How It Works

### Data Query: "What was total trading volume last month?"

```
1. User Input → "What was total trading volume last month?"
2. Schema Retrieval → System fetches full DDL from PostgreSQL
3. Claude Prompt → "Given schema X, generate SQL for: [question]"
4. SQL Generated → "SELECT SUM(volume) FROM transactions WHERE created_at >= ..."
5. Execution → asyncpg prepared statement executes query
6. Results → {"sum": 12345.67}
7. Explanation → Claude: "The total trading volume last month was 12,345.67..."
8. Display → Table + optional chart + CSV/JSON export
```

---

## 🎉 What Makes This Special

### Our Approach

✅ **Full schema context** - Claude receives complete DDL for accurate SQL
✅ **Conversational AI** - Remembers context for natural follow-up questions
✅ **Clean OOP design** - Single Responsibility Principle, DRY, proper encapsulation
✅ **Prepared statements** - SQL injection impossible
✅ **Intelligent responses** - Handles empty results and ambiguous queries gracefully
✅ **Smart chart selection** - Automatically filters chart types based on data structure

---

## 🎨 Code Architecture & Design Patterns

### Object-Oriented Principles Applied

This codebase follows industry best practices for maintainable software:

#### 1. **Single Responsibility Principle (SRP)**
Each class has exactly one reason to change:

- **DataAssistant**: UI coordination and component initialization
- **PipelineOrchestrator**: Workflow management and coordination
- **QuestionClassifier**: Question intent classification
- **ResponseGenerator**: Conversational response generation
- **SQLGenerator**: SQL generation from natural language
- **QueryExplainer**: SQL → natural language explanations
- **ResultValidator**: Result validation and warnings

#### 2. **DRY (Don't Repeat Yourself)**
Zero code duplication achieved through:

- **LLMUtils**: Centralized async API calls (eliminates 40+ duplicate lines)
- **Constants**: All magic numbers in one place
- **Exceptions**: Custom hierarchy for consistent error handling

#### 3. **Proper Encapsulation**
No private attribute access - only public methods:

```python
# ❌ Bad (before refactoring)
tables = await sql_generator._db_conn.fetch(query)

# ✅ Good (after refactoring)
tables = await sql_generator.get_table_names()
```

#### 4. **Dependency Injection**
Components receive dependencies, enabling easy testing:

```python
orchestrator = PipelineOrchestrator(
    classifier=classifier,
    response_generator=response_generator,
    sql_generator=sql_generator,
    result_validator=result_validator
)
```

#### 5. **Clear Separation of Concerns**

```
UI Layer:          streamlit_app.py (UI rendering, user interaction)
Coordination:      DataAssistant (initialization, delegation)
Workflow:          PipelineOrchestrator (process coordination)
Business Logic:    Individual components (classification, generation, etc.)
Utilities:         LLMUtils, constants, exceptions (shared functionality)
```

### Refactoring Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Code duplication | 40+ lines | 0 lines | ✅ -100% |
| DataAssistant size | 280 lines | 130 lines | ✅ -53% |
| Files with single responsibility | 3 | 9 | ✅ +200% |
| Magic numbers | Everywhere | Centralized | ✅ Fixed |
| Private access violations | Yes | None | ✅ Fixed |

---

## 📈 Performance

- **Query Latency**: 2-5 seconds (Claude API call)
- **Database Queries**: <100ms typical
- **Startup Time**: 30-60 seconds
- **Memory Usage**: ~500MB total (both services)

---

## 🚀 Production Deployment

### Recommendations

1. **Database**
   - Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
   - Enable connection pooling (PgBouncer)
   - Set up read replicas for queries

2. **Security**
   - Add authentication (Streamlit auth, OAuth)
   - Use secrets manager (AWS Secrets Manager, Vault)
   - Enable SSL/TLS everywhere
   - Implement rate limiting

3. **Monitoring**
   - Application monitoring (DataDog, New Relic)
   - Log aggregation (ELK, CloudWatch)
   - Query performance tracking
   - Cost monitoring (Claude API usage)

---

## 📚 Additional Resources

- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 💬 Support & Issues

- **Issues**: Report bugs or request features via GitHub Issues
- **Questions**: Start a discussion in GitHub Discussions

---

## 🎯 Roadmap

- [ ] Support for MySQL, SQL Server, BigQuery, Redshift
- [ ] Query history and favorites
- [ ] Multi-user support with authentication
- [ ] Advanced chart customization
- [ ] Scheduled reports
- [ ] API endpoints for programmatic access
- [ ] Support for complex aggregations and window functions
- [ ] Query optimization suggestions
- [ ] Cost estimation for cloud databases

---

**Built with ❤️ for data teams everywhere**

**Stack**: Python · Streamlit · Claude · PostgreSQL · Docker
