# 🎯 Wren AI Slack Bot for AWS Redshift

Production-ready Slack bot that enables teams to query AWS Redshift data warehouse using natural language powered by Wren AI and Claude Sonnet 4.5.

## ✨ Features

- **🗣️ Natural Language Queries**: Ask questions in plain English
- **🤖 Claude Sonnet 4.5**: Latest AI model for accurate SQL explanations
- **🔒 Row-Level Security**: Department-based data filtering
- **📥 Multiple Export Formats**: CSV, JSON, and charts
- **💬 Smart Clarifications**: Progressive questioning when uncertain
- **🔍 Entity Discovery**: Suggests alternatives when data is missing
- **📊 Auto Chart Generation**: Visualizations with one click
- **📝 Comprehensive Logging**: Full audit trail of all queries
- **✅ SQL Validation**: Safety checks to prevent dangerous operations
- **⚡ AWS Redshift Optimized**: Direct integration with Redshift

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Slack workspace (admin access)
- Anthropic API key ([get one](https://console.anthropic.com/))
- AWS Redshift cluster with read-only user

### Installation

```bash
# 1. Clone repository
git clone <your-repo>
cd wren-ai-slack-bot

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your credentials
nano .env

# 4. Start services
docker-compose up -d

# 5. Check logs
docker-compose logs -f bot
```

You should see:
```
✅ WREN AI SLACK BOT STARTED SUCCESSFULLY
📊 Wren AI: http://wren-ai:8000
🤖 Claude Model: claude-sonnet-4-20250514
💬 Listening for /ask commands in Slack...
```

## ⚙️ Configuration

### 1. Environment Variables (.env)

```bash
# Anthropic API (Claude Sonnet 4.5)
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# AWS Redshift
REDSHIFT_HOST=your-cluster.us-east-1.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DATABASE=analytics
REDSHIFT_USER=readonly_user
REDSHIFT_PASSWORD=your-password
DB_SSL=true

# User Roles (Format: SLACK_USER_ID:ROLE:DEPARTMENT)
USER_ROLES=U01ABC:admin:all,U02DEF:analyst:sales,U03GHI:analyst:marketing

# Department Access Rules
DEPT_ACCESS_SALES=public.orders,public.customers
DEPT_ACCESS_MARKETING=public.campaigns,public.leads
DEPT_ACCESS_FINANCE=public.*
```

### 2. Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Enable **Socket Mode**
4. Add **Bot Token Scopes**:
   - `chat:write`
   - `commands`
   - `users:read`
   - `files:write`
5. Create **Slash Command**: `/ask`
6. Install app to workspace

### 3. Get Slack User IDs

```
Right-click user in Slack → View profile → ⋯ More → Copy member ID
```

### 4. Configure User Roles

```bash
# Format: SLACK_USER_ID:ROLE:DEPARTMENT

# Admin - sees all data
USER_ROLES=U01ABC123:admin:all

# Analyst - sees only their department
USER_ROLES=U02DEF456:analyst:sales

# Multiple users
USER_ROLES=U01ABC:admin:all,U02DEF:analyst:sales,U03GHI:analyst:marketing
```

## 📖 Usage

### Basic Query

```
/ask What was revenue last month?
```

Bot responds with:
1. **SQL Query** (for transparency)
2. **Plain English Explanation** (via Claude)
3. **Security Filter Info** (what data you can see)
4. **[✅ Run Query]** button

### With Exports

```
User: /ask Show top 10 customers by revenue

Bot: ✅ Results (1.2s | 10 rows)
     [Shows data]
     
     [📥 Download CSV] [📄 Download JSON] [📊 Show Chart]
     
     👍 Helpful  |  👎 Not helpful
```

### Progressive Clarification

```
User: /ask show revenue

Bot: 🤔 I need some clarification (confidence: 45%)
     
     Did you mean one of these?
     1. Total revenue last month
     2. Revenue by region this quarter
     3. Daily revenue trend
     
     [Select option or rephrase]
```

### Entity Discovery

```
User: /ask What's our NPS score?

Bot: 😕 I couldn't find "NPS" in the data.
     
     I found these related items:
     • metric: customer_satisfaction
     • metric: retention_rate
     • table: customer_feedback
     
     Did you mean one of these?
```

## 🔒 Security

### Row-Level Security (RLS)

Automatic department filtering ensures users only see their data:

```sql
-- Sales user asks: "SELECT * FROM orders"
-- Bot executes: "SELECT * FROM orders WHERE department = 'sales'"

-- Admin asks: "SELECT * FROM orders"
-- Bot executes: "SELECT * FROM orders" (no filter)
```

### SQL Validation

Blocks dangerous operations:
- ❌ DROP, DELETE, INSERT, UPDATE
- ❌ SQL injection patterns
- ❌ Multiple statements
- ✅ Only SELECT queries allowed

### Best Practices

1. **Read-only Redshift user**: Grant SELECT-only permissions
2. **Network security**: Use VPC and security groups
3. **Audit logs**: Review `logs/wren-bot.log` regularly
4. **SSL/TLS**: Enable `DB_SSL=true` for encrypted connections

## 📊 Logging

Every query is logged with full context:

```log
2024-11-15 10:30:45 | QUERY_START | User=U01ABC (John Doe) | Dept=sales | Question="revenue last month"
2024-11-15 10:30:48 | QUERY_SUCCESS | User=U01ABC | Duration=2.5s | Rows=150 | SQLLength=245
2024-11-15 10:30:50 | EXPORT | User=U01ABC | Type=CSV | Rows=150
2024-11-15 10:30:55 | FEEDBACK | User=U01ABC | Type=positive
```

### Access Logs

```bash
# View live logs
docker-compose logs -f bot

# View log file
cat logs/wren-bot.log

# Search for successful queries
grep QUERY_SUCCESS logs/wren-bot.log

# Find errors
grep ERROR logs/wren-bot.log

# User activity
grep "User=U01ABC" logs/wren-bot.log
```

### Analytics

```bash
# Total queries today
grep "$(date +%Y-%m-%d)" logs/wren-bot.log | grep QUERY_SUCCESS | wc -l

# Average query time
grep QUERY_SUCCESS logs/wren-bot.log | grep -oP 'Duration=\K[0-9.]+' | awk '{sum+=$1; count++} END {print sum/count "s"}'

# Most active users
grep QUERY_START logs/wren-bot.log | grep -oP 'User=\K[^ ]+' | sort | uniq -c | sort -rn
```

## 🔧 Troubleshooting

### Bot Not Responding

```bash
# Check bot status
docker-compose ps

# View logs
docker-compose logs bot | tail -50

# Restart bot
docker-compose restart bot
```

### "User Not Authorized"

1. Get Slack user ID: Right-click user → Copy member ID
2. Add to `.env`:
   ```bash
   USER_ROLES=U01ABC:analyst:sales,U02DEF:admin:all
   ```
3. Restart: `docker-compose restart bot`

### Wren AI Connection Failed

```bash
# Check Wren AI logs
docker-compose logs wren-ai

# Test connection
curl http://localhost:8000/health

# Verify Redshift credentials
docker-compose exec wren-ai env | grep REDSHIFT
```

### Queries Timing Out

1. Add filters to reduce data volume
2. Increase timeout in `.env`:
   ```bash
   MAX_QUERY_TIMEOUT_SECONDS=60
   ```
3. Optimize Redshift tables (indexes, distribution keys)

## 📈 Performance

| Metric | Target | Typical |
|--------|--------|---------|
| Simple queries | <2s | 1-2s |
| Complex queries | <5s | 3-5s |
| Cache hit rate | >50% | 60-70% |
| Uptime | >99% | 99.5% |

### Optimization Tips

1. **Redshift Performance**:
   - Use distribution keys
   - Create indexes on filter columns
   - Vacuum tables regularly

2. **Query Patterns**:
   - Encourage specific time periods
   - Use aggregations vs raw data
   - Limit result sets

3. **Wren AI**:
   - Define clear semantic models
   - Add entity descriptions
   - Configure relationships

## 🚢 Production Deployment

### AWS ECS/Fargate

```bash
# 1. Build and push image
docker build -t your-registry/wren-bot:latest .
docker push your-registry/wren-bot:latest

# 2. Create ECS task definition
# 3. Configure secrets in AWS Secrets Manager
# 4. Deploy service
```

### Environment Variables in AWS

Use AWS Secrets Manager for sensitive data:
- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_APP_TOKEN`
- `REDSHIFT_PASSWORD`

### Monitoring

Set up CloudWatch alarms for:
- Container health
- Query error rate
- Response time (p95, p99)
- Memory/CPU usage

## 📝 Example Queries

```
# Revenue queries
/ask What was total revenue last month?
/ask Show revenue by region for Q4
/ask Compare revenue vs last year

# Customer queries
/ask Top 10 customers by lifetime value
/ask How many new customers this week?
/ask Customer retention rate by cohort

# Product queries
/ask Best selling products last month
/ask Product categories by revenue
/ask Products with declining sales

# Operational queries
/ask Daily active users last 30 days
/ask Average order value by channel
/ask Conversion rate by traffic source
```

## 🛣️ Roadmap

- [ ] S3 export for large datasets
- [ ] Scheduled queries (daily/weekly reports)
- [ ] Query templates
- [ ] Natural language follow-ups
- [ ] Multi-database support
- [ ] Custom chart types
- [ ] Query history per user
- [ ] Advanced analytics dashboard

## 📞 Support

- 📖 **Documentation**: See this README
- 🐛 **Issues**: Open a GitHub issue
- 💬 **Questions**: Check logs first, then ask team
- 🔒 **Security**: Email security@yourcompany.com

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- [Wren AI](https://github.com/Canner/WrenAI) - Open-source semantic layer
- [Anthropic](https://www.anthropic.com/) - Claude Sonnet 4.5
- [Slack Bolt](https://slack.dev/bolt-python/) - Slack SDK

---

**Built for data teams who want natural language access to their Redshift data** 🚀