# Cursor AI Rules for CBI-V14

## CRITICAL: Verification Before Action

Before making ANY changes, you MUST:

### 1. **Check if files exist**
```bash
ls -la path/to/file
```
If the file exists, ASK before overwriting.

### 2. **Show current state first**
```bash
cat existing_file.py | head -20  # Show first 20 lines
```
Let the user decide if changes are needed.

### 3. **Verify assumptions**
"I see docker-compose.yml exists. Should I modify it or leave it alone?"
"The table already has data. Do you want to append or replace?"

### 4. **Never assume empty state**
- Check BigQuery tables for data before writing ingestion scripts
- Check if Python packages are installed before pip install
- Check if containers are running before docker-compose up

---

## Decision Tree

**User asks: "Create ingest_zl_futures.py"**
```
│
├─> FIRST: Check if cbi-v14-ingestion/ingest_zl_futures.py exists
│   │
│   ├─> EXISTS: "File already exists (X lines). Should I:
│   │            a) Show you what's there
│   │            b) Replace it
│   │            c) Make specific edits?"
│   │
│   └─> DOESN'T EXIST: Create the file as requested
```

---

## Banned Behaviors

❌ Creating duplicate files without checking
❌ Modifying docker-compose.yml without asking
❌ Running destructive commands (DROP TABLE, rm -rf) without confirmation
❌ Assuming tables are empty without SELECT COUNT(*)
❌ Overwriting existing scripts

---

## Required Behaviors

✅ `ls` before `touch`/create
✅ `cat` before overwrite
✅ `bq query COUNT(*)` before assuming empty
✅ `docker ps` before `docker-compose up`
✅ Show file tree when asked "what exists?"

---

## Safe Defaults

**When in doubt:**
1. Show current state
2. Ask user to decide
3. Make targeted edits instead of full rewrites

---

## Examples

### ✅ CORRECT Workflow
```
User: "Create the ZL futures script"
Cursor: 
1. ls -la cbi-v14-ingestion/
2. "I see ingest_zl_futures.py already exists (538 lines). 
   Would you like me to:
   a) Show you the current content
   b) Replace it entirely  
   c) Make specific modifications"
```

### ❌ WRONG Workflow
```
User: "Create the ZL futures script"
Cursor: [immediately overwrites existing file without checking]
```

---

## Verification Commands

**Before any BigQuery work:**
```bash
bq ls --project_id=cbi-v14 forecasting_data_warehouse
bq query "SELECT COUNT(*) FROM table_name"
```

**Before any Docker work:**
```bash
docker ps
docker-compose ps
```

**Before any file creation:**
```bash
ls -la target_directory/
find . -name "target_file*"
```

---

## This Document

Keep CURSOR_RULES.md open in a tab so it stays in context.

**Every Cursor session working on CBI-V14 must read and follow these rules.**
