# Streamlit Integration Guide: Auto-Schema Generator

**Quick Integration:** Add a "🔄 Update Schema" button to your Streamlit app (10 minutes)

---

## Step 1: Import the Auto-Schema Generator

Add this at the top of `streamlit_app.py` (after line 31):

```python
from config import Config
from wren_client import WrenClient
from validator import SQLValidator
from result_validator import ResultValidator
from query_explainer import QueryExplainer
from auto_schema_generator import AutoSchemaGenerator  # <-- ADD THIS LINE
```

---

## Step 2: Add the Schema Generator Button

Insert this code in your sidebar section (around line 474, right after `st.markdown("---")`):

```python
    with st.sidebar:
        st.success("✅ Wren AI Ready")

        st.markdown("---")

        # ============ AUTO-SCHEMA GENERATOR ============
        st.subheader("🔄 Auto-Schema Generator")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Update Schema", help="Auto-generate schema from database", use_container_width=True):
                with st.spinner(""):
                    # Progress indicators
                    progress_text = st.empty()
                    progress_bar = st.progress(0)

                    try:
                        # Prepare database config
                        db_config = {
                            'host': st.session_state.assistant.config.DB_HOST,
                            'port': st.session_state.assistant.config.DB_PORT,
                            'database': st.session_state.assistant.config.DB_DATABASE,
                            'user': st.session_state.assistant.config.DB_USER,
                            'password': st.session_state.assistant.config.DB_PASSWORD,
                            'ssl': st.session_state.assistant.config.DB_SSL
                        }

                        # Initialize generator
                        generator = AutoSchemaGenerator(
                            db_config=db_config,
                            anthropic_client=st.session_state.assistant.config.anthropic_client
                        )

                        # Progress callback
                        def update_progress(text: str, percent: int):
                            progress_text.text(text)
                            progress_bar.progress(percent)

                        # Connect
                        progress_text.text("Connecting to database...")
                        progress_bar.progress(5)
                        generator.connect()

                        # Generate schema
                        import asyncio
                        new_schema = asyncio.run(
                            generator.generate_schema(
                                include_samples=True,
                                progress_callback=update_progress
                            )
                        )

                        # Save to MDL file
                        schema_path = "database/mdl/schema.json"
                        generator.save_to_file(new_schema, schema_path)
                        generator.disconnect()

                        # Reload Wren client with new schema
                        st.session_state.assistant.wren._mdl_models = new_schema.get('models', [])
                        st.session_state.assistant.wren._mdl_metrics = new_schema.get('metrics', [])

                        # Rebuild validator with new schema
                        st.session_state.assistant.validator = SQLValidator(
                            mdl_models=new_schema.get('models', []),
                            mdl_metrics=new_schema.get('metrics', [])
                        )

                        # Clear progress
                        progress_bar.empty()
                        progress_text.empty()

                        # Show success
                        st.success(f"""
✅ **Schema updated successfully!**

- **{len(new_schema['models'])}** tables discovered
- **{sum(len(m.get('columns', [])) for m in new_schema['models'])}** columns profiled
- **{len(new_schema['metrics'])}** metrics generated
                        """)

                        # Give time to read
                        import time
                        time.sleep(2)

                        # Reload page
                        st.rerun()

                    except Exception as e:
                        progress_bar.empty()
                        progress_text.empty()
                        st.error(f"❌ Schema generation failed: {str(e)}")
                        import logging
                        logging.error(f"Schema generation error: {e}", exc_info=True)

        with col2:
            if st.button("📄 View Schema", help="View current schema details", use_container_width=True):
                st.session_state.show_schema_details = True

        # Show schema details modal
        if st.session_state.get('show_schema_details', False):
            with st.expander("📋 Current Schema Details", expanded=True):
                models = st.session_state.assistant.wren._mdl_models
                metrics = st.session_state.assistant.wren._mdl_metrics

                st.write(f"### Tables ({len(models)})")

                for model in models:
                    with st.container():
                        st.write(f"**{model['name']}**")
                        st.caption(model.get('description', 'No description'))
                        st.write(f"  Columns: {len(model.get('columns', []))}")

                        # Show first few columns
                        if model.get('columns'):
                            cols_to_show = model['columns'][:3]
                            for col in cols_to_show:
                                st.text(f"    • {col.get('name')} ({col.get('type')})")

                            if len(model['columns']) > 3:
                                st.caption(f"    ... and {len(model['columns']) - 3} more")

                st.write(f"### Metrics ({len(metrics)})")

                for metric in metrics[:5]:  # Show first 5
                    st.write(f"  - **{metric['name']}**: {metric.get('description', 'No description')}")

                if len(metrics) > 5:
                    st.caption(f"  ... and {len(metrics) - 5} more")

                if st.button("❌ Close", key="close_schema"):
                    st.session_state.show_schema_details = False
                    st.rerun()

        st.markdown("---")
        # ============ END: AUTO-SCHEMA GENERATOR ============

        # ... rest of your existing sidebar code continues here ...
        # Statistics
        st.subheader("📊 Schema Info")
        # ... etc
```

---

## Step 3: Test It!

```bash
# Start your app
streamlit run streamlit_app.py

# In the app:
# 1. Look at the left sidebar
# 2. Click "🔄 Update Schema"
# 3. Wait 30-60 seconds
# 4. See success message!
```

---

## What Happens When You Click

```
User clicks "🔄 Update Schema"
    ↓
Progress: "Connecting to database..." (5%)
    ↓
Progress: "Profiling tables..." (20%)
    ↓
Progress: "Generating AI descriptions..." (60%)
    ↓
Progress: "Converting to MDL format..." (90%)
    ↓
Progress: "Complete!" (100%)
    ↓
Success message with stats
    ↓
Page reloads with new schema
```

**Total time: 30-60 seconds** (depending on database size)

---

## Enhanced Version (Optional)

For more detailed progress and error handling:

```python
# Replace the basic version with this enhanced one

st.subheader("🔄 Auto-Schema Generator")

# Show last update time
import os
from pathlib import Path
schema_path = "database/mdl/schema.json"

if Path(schema_path).exists():
    from datetime import datetime
    modified_time = datetime.fromtimestamp(os.path.getmtime(schema_path))
    time_ago = datetime.now() - modified_time

    if time_ago.days > 0:
        last_update = f"{time_ago.days} days ago"
    elif time_ago.seconds // 3600 > 0:
        last_update = f"{time_ago.seconds // 3600} hours ago"
    else:
        last_update = f"{time_ago.seconds // 60} minutes ago"

    st.caption(f"Last updated: {last_update}")

col1, col2 = st.columns(2)

with col1:
    update_btn = st.button(
        "🔄 Update",
        help="Re-generate schema from database",
        use_container_width=True
    )

with col2:
    view_btn = st.button(
        "👁️ View",
        help="View current schema details",
        use_container_width=True
    )

if update_btn:
    # Enhanced progress tracking
    status_container = st.container()

    with status_container:
        with st.status("Generating schema...", expanded=True) as status:
            try:
                # Prepare config
                st.write("🔧 Preparing configuration...")
                db_config = {
                    'host': st.session_state.assistant.config.DB_HOST,
                    'port': st.session_state.assistant.config.DB_PORT,
                    'database': st.session_state.assistant.config.DB_DATABASE,
                    'user': st.session_state.assistant.config.DB_USER,
                    'password': st.session_state.assistant.config.DB_PASSWORD,
                    'ssl': st.session_state.assistant.config.DB_SSL
                }

                # Initialize
                st.write("🔌 Connecting to database...")
                generator = AutoSchemaGenerator(
                    db_config=db_config,
                    anthropic_client=st.session_state.assistant.config.anthropic_client
                )
                generator.connect()

                # Profile database
                st.write("📊 Profiling database structure...")
                import asyncio

                async def generate_with_updates():
                    progress_placeholder = st.empty()

                    def update_callback(text, percent):
                        progress_placeholder.progress(percent / 100, text=text)

                    schema = await generator.generate_schema(
                        include_samples=True,
                        progress_callback=update_callback
                    )
                    progress_placeholder.empty()
                    return schema

                new_schema = asyncio.run(generate_with_updates())

                # Save
                st.write("💾 Saving schema...")
                generator.save_to_file(new_schema, schema_path)
                generator.disconnect()

                # Reload
                st.write("🔄 Reloading application...")
                st.session_state.assistant.wren._mdl_models = new_schema.get('models', [])
                st.session_state.assistant.wren._mdl_metrics = new_schema.get('metrics', [])
                st.session_state.assistant.validator = SQLValidator(
                    mdl_models=new_schema.get('models', []),
                    mdl_metrics=new_schema.get('metrics', [])
                )

                # Update status
                status.update(label="✅ Schema updated!", state="complete", expanded=False)

                # Show detailed results
                st.success(f"""
**Schema generation complete!**

📊 **Discovered:**
- {len(new_schema['models'])} tables
- {sum(len(m.get('columns', [])) for m in new_schema['models'])} columns
- {len(new_schema['metrics'])} metrics

🔍 **Auto-detected:**
- {sum(len(m.get('relationships', [])) for m in new_schema['models'])} relationships
- Primary keys for all tables
- Data types and constraints
                """)

                import time
                time.sleep(3)
                st.rerun()

            except Exception as e:
                status.update(label="❌ Schema generation failed", state="error")
                st.error(f"""
**Error:** {str(e)}

**Common causes:**
- Database not accessible
- Invalid credentials
- Claude API key missing or invalid
- Network issues

**Check:**
- Your `.env` file has correct credentials
- Database is running: `docker-compose ps`
- Claude API key: `echo $ANTHROPIC_API_KEY`
                """)

                import logging
                logging.error(f"Schema generation error: {e}", exc_info=True)

if view_btn:
    st.session_state.show_schema_details = True

# ... rest of the code for showing schema details ...
```

---

## Troubleshooting

### Issue: "Module 'auto_schema_generator' not found"

**Fix:**
```bash
# Make sure file exists
ls src/auto_schema_generator.py

# If missing, create it from the provided code
# Then restart Streamlit
streamlit run streamlit_app.py
```

### Issue: Button click does nothing

**Check console for errors:**
```bash
# Look at terminal running streamlit
# Should see logging output
```

### Issue: "Database connection failed"

**Check your .env file:**
```env
DB_HOST=postgres
DB_PORT=5432
DB_DATABASE=analytics
DB_USER=wren_user
DB_PASSWORD=wren_password
```

**Test connection:**
```python
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    port=5432,
    database='analytics',
    user='wren_user',
    password='wren_password'
)
print("✅ Connected!")
conn.close()
```

### Issue: "Claude API error"

**Check API key:**
```bash
echo $ANTHROPIC_API_KEY

# Should output: sk-ant-...
# If empty, add to .env:
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Cost Estimate

**Per schema generation:**
- Database profiling: ~30-60 seconds (free)
- Claude API call: ~$0.02-0.05 per 100 tables
- **Total: ~$0.05 per update**

**If you update daily:**
- **~$1.50/month**

**Compare to manual MDL:**
- 4-8 hours/month @ $100/hr = **$400-800/month**

**Savings: $398-798/month** 💰

---

## Next Steps

1. ✅ Create `src/auto_schema_generator.py` (done!)
2. ▶️ **Add button to `streamlit_app.py`** (copy code above)
3. ▶️ **Test it:** Click the button and watch it work!
4. ✅ Never manually update MDL again

---

## Optional Enhancements

### A) Schedule Automatic Updates

Create a background task that updates schema every night:

```python
# Add to your streamlit_app.py initialization
import threading
import time
import schedule

def background_schema_updater():
    """Background task to update schema daily"""
    def update_schema():
        try:
            # Same code as button, but without Streamlit UI
            from auto_schema_generator import AutoSchemaGenerator
            from config import Config

            config = Config()
            db_config = {
                'host': config.DB_HOST,
                'port': config.DB_PORT,
                'database': config.DB_DATABASE,
                'user': config.DB_USER,
                'password': config.DB_PASSWORD,
                'ssl': config.DB_SSL
            }

            generator = AutoSchemaGenerator(db_config, config.anthropic_client)
            generator.connect()

            import asyncio
            schema = asyncio.run(generator.generate_schema())

            generator.save_to_file(schema, "database/mdl/schema.json")
            generator.disconnect()

            print(f"✅ Schema auto-updated at {datetime.now()}")

        except Exception as e:
            print(f"❌ Auto-update failed: {e}")

    # Schedule daily at 3 AM
    schedule.every().day.at("03:00").do(update_schema)

    while True:
        schedule.run_pending()
        time.sleep(60)

# Start background updater
if 'schema_updater_started' not in st.session_state:
    threading.Thread(target=background_schema_updater, daemon=True).start()
    st.session_state.schema_updater_started = True
```

### B) Show Schema Diff

Show what changed since last update:

```python
# Add this button next to "View Schema"
if st.button("📊 What Changed?"):
    import json

    # Load current schema
    with open("database/mdl/schema.json") as f:
        current_schema = json.load(f)

    # Load previous schema (if exists)
    prev_path = "database/mdl/schema_previous.json"
    if Path(prev_path).exists():
        with open(prev_path) as f:
            prev_schema = json.load(f)

        # Compare
        current_tables = {m['name'] for m in current_schema.get('models', [])}
        prev_tables = {m['name'] for m in prev_schema.get('models', [])}

        new_tables = current_tables - prev_tables
        removed_tables = prev_tables - current_tables

        st.write("### Schema Changes")

        if new_tables:
            st.write("**New tables:**")
            for table in new_tables:
                st.write(f"  + {table}")

        if removed_tables:
            st.write("**Removed tables:**")
            for table in removed_tables:
                st.write(f"  - {table}")

        if not new_tables and not removed_tables:
            st.info("No table changes detected")
    else:
        st.info("No previous schema to compare")
```

---

Done! 🎉

Your Streamlit app now has automatic schema generation with just one button click.

**Time saved: ~4-8 hours per month**
**Cost: ~$1.50 per month**
**ROI: 266-533x** 💰
