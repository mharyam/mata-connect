## MataConnect Community Enricher Data Pipeline

This project is a **data pipeline and AI-powered community enricher**. It takes community URLs, enriches them using an LLM, stores the results in SQLite, and then loads the cleaned community documents into MongoDB for use in MataConnect.

### What it does

- **Input**: A CSV of community URLs (see `data/mata_connect.csv`).
- **Enrich**: Uses `enricher/openai_enricher.py` and the OpenAI Agents stack to visit each URL and extract structured community data (name, description, tags, location, contact, social links, focus areas, etc.).
- **Store (SQLite)**: Persists the enriched JSON per URL into `communities.db` via `enricher/process_communities.py` and `enricher/database.py`, skipping URLs that were already processed.
- **Load (MongoDB)**: Transforms the SQLite JSON into the MataConnect community schema and bulk-inserts into MongoDB using `enricher/load_to_mongodb.py`.

### Setup

1. **Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment**

Create a `.env` file in the project root with at least:

```bash
OPENAI_API_KEY=your_openai_key
MONGODB_PASSWORD=your_mongodb_password
# Optionally override:
# MONGODB_URI=your_full_mongodb_uri
# MONGODB_DATABASE=mataconnect
# MONGODB_COLLECTION=communities
```

### Running the pipeline

1. **Enrich communities from URLs into SQLite**

```bash
python enricher/process_communities.py  # uses data/mata_connect.csv by default
```

This will:
- Read URLs from `data/mata_connect.csv`
- Enrich each site via `OpenAIEnricher.enrich_community`
- Store JSON results in `communities.db`, skipping URLs already in the DB

2. **Load enriched data from SQLite into MongoDB**

```bash
python enricher/load_to_mongodb.py
```

This will:
- Read all rows from `communities.db`
- Transform them to the target MongoDB community document shape
- Bulk-insert into the `mataconnect` database / `communities` collection (configurable in `config.py`)

### Key files

- `enricher/openai_enricher.py` – defines the `CommunityInfo` schema and the OpenAI-based enrichment agent.
- `enricher/process_communities.py` – reads the CSV, calls the enricher, writes to SQLite.
- `enricher/database.py` – SQLite helpers (init, save, lookup).
- `enricher/load_to_mongodb.py` – transforms SQLite JSON into the MataConnect MongoDB schema and bulk-loads it.
- `config.py` – MongoDB configuration and env var validation.

### Notes

- The pipeline is **idempotent** per-URL at the SQLite layer: if a URL is already present, it is not re-enriched.
- MongoDB loading is designed for **batch/bulk inserts**, suitable for refreshing the MataConnect communities index from enriched data.


