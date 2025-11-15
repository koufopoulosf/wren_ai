# Troubleshooting: wren-ai-service unhealthy

## Error Message
```
✘ Container wren-ai-service  Error
dependency failed to start: container wren-ai-service is unhealthy
```

## Common Causes & Solutions

### 1. Check Service Logs

**Run this to see what's failing:**
```bash
docker compose logs wren-ai
# or
docker logs wren-ai-service
```

**Look for errors like:**
- `ModuleNotFoundError`
- `Connection refused`
- `Configuration error`
- `Model not found`

---

### 2. Most Common Issue: Ollama Model Not Downloaded

The wren-ai-service starts **before** Ollama finishes downloading the embedding model.

**Solution A: Manual Pull (Recommended)**
```bash
# Stop everything
docker compose down

# Start only Ollama first
docker compose up -d ollama

# Wait for Ollama to be ready
docker compose logs -f ollama
# Wait for: "Listening on [::]:11434"

# Pull the embedding model manually
docker exec -it wren-ollama ollama pull nomic-embed-text

# Verify model is downloaded
docker exec -it wren-ollama ollama list
# Should show: nomic-embed-text

# Now start everything
docker compose up -d
```

**Solution B: Increase Startup Wait Time**

Edit `docker-compose.yml`:
```yaml
wren-ai:
  healthcheck:
    start_period: 180s  # Increase from 120s to 180s
```

---

### 3. Configuration File Issues

**Check if config is mounted correctly:**
```bash
docker exec -it wren-ai-service cat /app/config.yaml
```

If it shows "No such file or directory", the volume mount is wrong.

**Fix:** Ensure `wren-ai-config.yaml` exists in project root:
```bash
ls -la wren-ai-config.yaml
```

---

### 4. Port Conflicts

**Check if port 5555 is already in use:**
```bash
lsof -i :5555
# or
netstat -tuln | grep 5555
```

**Solution:** Stop the conflicting process or change the port:
```yaml
wren-ai:
  ports:
    - "5556:5555"  # Use different external port
```

---

### 5. Dependencies Not Ready

Wren AI depends on:
- Qdrant (vector DB)
- Ollama (embeddings)
- Wren Engine (SQL execution)

**Check all services are healthy:**
```bash
docker compose ps
```

All should show "healthy" or "Up":
```
postgres         Up (healthy)
qdrant          Up
ollama          Up (healthy)
wren-engine     Up
wren-ai         Up (healthy)  ← Should be this
```

If Qdrant or Ollama are down:
```bash
docker compose restart qdrant ollama
docker compose logs qdrant ollama
```

---

### 6. API Key Issues

**Check if ANTHROPIC_API_KEY is set:**
```bash
docker exec -it wren-ai-service printenv | grep ANTHROPIC
```

Should show:
```
ANTHROPIC_API_KEY=sk-ant-...
```

If empty:
1. Check your `.env` file exists: `cat .env`
2. Verify API key is set: `grep ANTHROPIC_API_KEY .env`
3. Restart: `docker compose restart wren-ai`

---

### 7. Memory Issues

Wren AI service needs ~1GB RAM to start.

**Check available memory:**
```bash
free -h
docker stats --no-stream
```

**Solution:** Increase Docker memory limit:
- Docker Desktop: Settings → Resources → Memory → 4GB minimum

---

### 8. Config.yaml Format Issues

The current `wren-ai-config.yaml` might have incorrect structure.

**Test the configuration:**
```bash
# Check if YAML is valid
docker run --rm -v $(pwd)/wren-ai-config.yaml:/config.yaml python:3.11 \
  python -c "import yaml; yaml.safe_load(open('/config.yaml'))"
```

**Common mistakes:**
- Wrong provider names
- Incorrect indentation
- Missing required fields

---

## Step-by-Step Diagnosis

Run these commands **in order**:

### Step 1: Check Docker is running
```bash
docker ps
```

### Step 2: Stop everything
```bash
docker compose down
```

### Step 3: Check .env file
```bash
cat .env | grep -v "^#" | grep -v "^$"
```

Should show at least:
```
ANTHROPIC_API_KEY=sk-ant-...
TELEMETRY_ENABLED=false
```

### Step 4: Start services one by one
```bash
# Start infrastructure first
docker compose up -d postgres qdrant ollama

# Wait for all to be healthy
docker compose ps

# Pull Ollama model
docker exec -it wren-ollama ollama pull nomic-embed-text

# Verify
docker exec -it wren-ollama ollama list

# Start wren-engine
docker compose up -d wren-engine

# Finally start wren-ai
docker compose up -d wren-ai

# Watch logs
docker compose logs -f wren-ai
```

### Step 5: Check health endpoint
```bash
curl http://localhost:5555/health
```

Should return:
```json
{"status":"ok"}
```

---

## Quick Fix: Restart Everything

Sometimes a simple restart works:

```bash
# Nuclear option - removes all containers and volumes
docker compose down -v

# Fresh start
docker compose up -d

# Watch all logs
docker compose logs -f
```

**Warning:** This deletes all vector embeddings. Wren AI will re-index your schema on first query.

---

## Still Not Working?

### Enable Debug Logging

Edit `wren-ai-config.yaml`:
```yaml
settings:
  log_level: DEBUG  # Change from INFO
```

Restart:
```bash
docker compose restart wren-ai
docker compose logs -f wren-ai
```

### Check Wren AI Version Compatibility

Our setup uses `wren-ai-service:0.29.0`. Check if there's an issue:

```bash
# Try a different version
docker compose down
```

Edit `docker-compose.yml`:
```yaml
wren-ai:
  image: ghcr.io/canner/wren-ai-service:latest  # Try latest
```

```bash
docker compose up -d
```

---

## Expected Startup Sequence

When everything works correctly:

```
1. [postgres] Database ready (10 seconds)
2. [qdrant] Vector DB ready (5 seconds)
3. [ollama] Server ready (5 seconds)
   → Downloading nomic-embed-text (60 seconds on first run)
4. [wren-engine] SQL engine ready (15 seconds)
5. [wren-ai] Connecting to dependencies (30 seconds)
   → Loading configuration
   → Connecting to Qdrant
   → Connecting to Ollama
   → Testing Anthropic API
   → Service ready! (120 seconds total)
```

**Timeline:** 2-3 minutes for first startup

---

## Health Check Details

The health check runs:
```bash
curl -f http://localhost:5555/health
```

**Failure reasons:**
- Service not started yet
- Configuration error preventing startup
- Dependency (Qdrant/Ollama) not reachable
- API key invalid

---

## Getting More Help

If still stuck, provide these details:

```bash
# 1. Service status
docker compose ps

# 2. Wren AI logs (last 100 lines)
docker compose logs wren-ai --tail=100

# 3. Ollama status
docker exec -it wren-ollama ollama list

# 4. Qdrant status
curl http://localhost:6333/collections

# 5. Docker version
docker --version
docker compose version

# 6. System resources
free -h
df -h
```

Then open an issue on the Wren AI GitHub or check their Discord.

---

**Created:** 2025-11-15
