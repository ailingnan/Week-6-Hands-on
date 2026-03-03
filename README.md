# Week-6-Hands-on
# HappyGroup: Smart Campus Digital Twin
# Video link :# https://drive.google.com/file/d/1A1RJ85WTymJMVNDYLD-HBNPqZzY9y8pI/view?usp=sharing

------------------------------------------------------------------------

## 1. System Workflow

The **HappyGroup** Smart Campus system is a production-grade data science pipeline designed to transform authoritative campus documents into a trust-aware digital twin for decision support.

- **Data Ingestion & Cleaning:** Raw PDFs (e.g., UMKC Jeanne Clery Act Reports) are processed via `01_extract_chunk.py`. The script cleans null bytes (`\x00`) and generates 1,200-character segments with 200-character overlaps to maintain semantic flow.
- **Cloud Warehousing:** Data is migrated to **Snowflake** using a staging-to-production pattern (Database: `TRAINING_DB`, Schema: `UMKC_RAG`).
- **Feature Engineering:** SQL-based and Python-based transformations automatically categorize text and calculate metadata — including keyword density and chunk length — to prepare high-quality grounding data.
- **LLM Generation:** Retrieved document chunks are passed to **Groq LLaMA** as grounding context, enabling natural language answers rooted in official UMKC policy.
- **Evaluation & Retrieval:** An optimized SQL layer performs ranked searches, while a dedicated Python evaluation module (`evaluator.py`) logs retrieval quality and latency back to Snowflake.
- **Agentic Extension (Week 6):** An automated intelligent agent runs on top of these pipelines, capable of intent recognition, function calling (`search_policy`, `simulate_whatif`), and synthesizing multi-document answers.

---

## 2. Architecture & Evaluation Layer

Our system follows a 4-tier modular architecture designed for high reliability and trust calibration.

**Tier 1 — Source Layer:** All raw data originates from a local `/data` directory containing authoritative UMKC artifacts, including PDFs such as the Jeanne Clery Act Report and supplementary CSV datasets.

**Tier 2 — Processing Layer (Python ETL):** Raw documents are ingested and cleaned by `01_extract_chunk.py`, which segments text into 1,200-character chunks with 200-character overlaps and outputs a structured `chunks.csv`. Ongoing ingestion is handled by `scheduler.py`, which automatically detects and uploads new files, while `feature_store.py` extracts and versions keyword-level features from every user query.

**Tier 3 — Storage Layer (Snowflake):** All processed data is persisted in Snowflake under the `UMKC_RAG` schema via RSA key authentication. The storage layer consists of five purpose-built tables: `DOC_CHUNKS_RAW` for initial staging, `DOC_CHUNKS_FEATURED` for production-ready text with engineered features, `FEATURE_STORE` for versioned keyword records, `EVAL_METRICS` for automated retrieval performance logging, and `INGEST_LOG` for file-level lineage and deduplication tracking.

**Tier 4 — Application Layer (Streamlit & Agent):** The `app.py` PolicyPulse dashboard serves as the user-facing interface. In Week 6, we introduced the **Agent Chat** tab, powered by `agent_runner.py` and Groq tool calling, allowing users to interact with the database using natural language instructions instead of manual dashboard clicks.

**Monitoring:** Throughout all tiers, `pipeline_logs.csv` maintains a continuous audit trail of every ingestion and LLM generation run, recording high-resolution timestamps, success/failure status, row counts, and end-to-end latency.

| Table | Purpose |
|-------|---------|
| `DOC_CHUNKS_RAW` | Initial staging of extracted text |
| `DOC_CHUNKS_FEATURED` | Production table with engineered text features |
| `FEATURE_STORE` | Versioned keyword feature store per query run |
| `EVAL_METRICS` | Automated retrieval performance logging |
| `INGEST_LOG` | File-level ingestion lineage and deduplication |

**Monitoring:** `pipeline_logs.csv` tracks every ingestion and LLM generation run with high-resolution timestamps, success/failure status, row counts, and latency.

---

## 3. Implemented Extensions (Team of 3)

As a three-member team, we implemented **six technical extensions** beyond the core requirements, each owned by a team member.

### Extension 1 — Automated Feature-Engineering Pipeline *(Ailing Nan)*
- **Category:** Data / Feature Extension
- **Implementation:** `feature_store.py` + `04_feature_engineering.sql`
- **Description:** Automatically extracts keyword features from every user query, filters stopwords, and writes versioned feature records (keyword list, keyword count, TopK setting) to the Snowflake `FEATURE_STORE` table. Supports version labels (v1/v2/v3) for longitudinal comparison of feature distributions.

### Extension 2 — System Performance & Evaluation Logging *(Lyza Iamrache)*
- **Category:** System / Application Extension
- **Implementation:** `evaluator.py` + `pipeline_logs.csv`
- **Description:** A dedicated logging layer records the semantic score, latency, and row count of every retrieval and LLM generation run into Snowflake (`EVAL_METRICS`) and local CSV. Enables real-time monitoring and post-hoc performance auditing.

### Extension 3 — Query Performance Optimization *(Gia Huynh)*
- **Category:** System / Application Extension
- **Implementation:** `05_retrieval_queries.sql` + `@st.cache_data` in `app.py`
- **Description:** Retrieval is optimized through ranked keyword-density scoring in SQL, combined with a 120-second Streamlit result cache that eliminates redundant Snowflake round-trips. Prioritizes high-density sections to reduce AI hallucinations.

### Extension 4 — Evaluation Metrics Comparison Dashboard *(Gia Huynh)*
- **Category:** Model / Decision Extension
- **Implementation:** Tab 3 in `app.py` + `evaluator.py`
- **Description:** An interactive dashboard aggregates `EVAL_METRICS` by version, surfacing average score, mean latency, and total runs as bar charts. Automatically highlights the best-performing version.

### Extension 5 — What-if Scenario Simulation Module *(Ailing Nan)*
- **Category:** Model / Decision Extension
- **Implementation:** Tab 4 in `app.py` (`run_whatif()`)
- **Description:** Users enter multiple query phrasings and the system runs all scenarios in parallel, returning a side-by-side comparison of chunks returned, average score, and latency. Automatically identifies the optimal query formulation.

### Extension 6 — Automated Scheduled Data Ingestion Workflow *(Lyza Iamrache)*
- **Category:** System / Application Extension
- **Implementation:** `scheduler.py`
- **Description:** A background polling worker scans the `ingest_inbox/` directory, hashes each file to prevent duplicate ingestion, and appends new CSV datasets to `DOC_CHUNKS_FEATURED`. Can be run continuously with a configurable interval (`SCHEDULER_INTERVAL_SEC`).

---

## 4. Week 6 Agent Enhancement Overview

In CS 5588 Week 6, the system was refactored by the Antigravity IDE into a standalone Agentic architecture while maintaining 100% of the Week 5 Streamlit functionality.

- **Non-UI Logic Extraction:** Snowflake connectivity, LLM calling, and keyword formulation were extracted into `app/core_services.py` to prevent redundant Streamlit caching loops when the Agent runs.
- **Tool Schemas:** Defined standard JSON schemas (`agent/tool_schemas.py`) for deterministic LLM function calling.
- **Tool Mapping:** Encapsulated Snowflake retrievals inside specialized Python wrapper functions (`agent/tools.py`).
- **Agent Runner:** The core reasoning loop (`agent/agent_runner.py`) uses LLaMA3 via Groq to parse user intents, execute the necessary tools sequentially, return the evidence, and synthesize the final answer.
- **Agent Chat Interface:** Hosted inside the main Streamlit application, providing users a seamless chat log alongside expandable "Reasoning Trace" and "Evidence" elements.

---

## 5. Repository Structure

```
Week-6-SmartCampus/
├── README.md
├── CONTRIBUTIONS.md
├── pipeline_logs.csv
├── requirements.txt
│
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_create_tables.sql
│   ├── 03_create_staging_tables.sql
│   ├── 04_feature_engineering.sql
│   └── 05_retrieval_queries.sql
│
├── ingestion/
│   └── scheduler.py
│
├── feature_engineering/
│   └── feature_store.py
│
├── modeling/
│   └── evaluator.py
│
├── agent/
│   ├── agent_runner.py
│   ├── tool_schemas.py
│   └── tools.py
│
├── app/
│   ├── app.py
│   └── core_services.py
│
└── architecture/
    └── architecture_diagram.png
```

---

## 6. Team Contributions

| Member | Primary Role | Technical Ownership (Week 5 & 6) |
| :--- | :--- | :--- |
| **Ailing Nan** | Project Lead & AI Architect | **Core System & AI Engine (Most Important Contribution):** Led the Week 6 Antigravity IDE setup, designed the agent tools (`tools.py`, `tool_schemas.py`), built the `agent_runner.py` reasoning loop, and integrated the complete Agent Chat interface. Also owns the foundational Python ETL pipeline, RSA Security, Database Governance, and Extensions 1 & 5. |
| **Lyza Iamrache** | Systems Lead | Snowflake Architecture, Automated Scheduled Ingestion (Ext. 6), Pipeline Logging & Monitoring (Ext. 2) |
| **Gia Huynh** | Evaluation & UI Lead | Streamlit Application UI, SQL Query Optimization (Ext. 3), Evaluation Metrics Dashboard (Ext. 4) |

---

## 7. Setup & Reproducibility

### Prerequisites
- Python 3.10+
- Snowflake Account with RSA Key Authentication configured
- Groq API Key (free at [console.groq.com](https://console.groq.com))

```bash
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=TRAINING_DB
SNOWFLAKE_SCHEMA=UMKC_RAG
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
SCHEDULER_INTERVAL_SEC=60
```

### Execution Steps

1. **Prepare Data:** Place PDF reports into the `/data` folder.

2. **Run Ingestion:**
```bash
python ingestion/01_extract_chunk.py
```

3. **Deploy Snowflake Schema:** Run SQL scripts in order:
```
sql/01_create_schema.sql
sql/02_create_tables.sql
sql/03_create_staging_tables.sql
sql/04_feature_engineering.sql
sql/05_retrieval_queries.sql
```

4. **Launch Application:**
```bash
streamlit run app/app.py
```

5. **Run Evaluation Module:**
```bash
python modeling/evaluator.py
```

6. **(Optional) Start Scheduled Ingestion:**
```bash
python ingestion/scheduler.py
```

---

## 8. Demo Instructions

Follow these step-by-step instructions to test the Week 6 Agent integration locally:

1. Launch the application: `streamlit run app/app.py`
2. Open your web browser (usually defaults to `http://localhost:8501`).
3. Click on the very first tab labeled **"🤖 Agent Chat"**.
4. Type an inquiry in the chat input box at the bottom.

**Example Demo Queries:**
- *"How much is a student parking permit?"* (Tests `search_policy` tool)
- *"Run a simulation for 'faculty parking' and 'student parking'. Which one has a better score?"* (Tests `simulate_whatif` tool)
- *"Can you summarize our evaluation metric trends?"* (Tests `get_eval_metrics` tool)

**Expected Outputs:**
You should see a message stating "Agent is thinking...", followed by the agent responding directly in the chat. Below the response, two expandable sections (`🛠️ Agent Reasoning Trace` and `📄 Retrieved Evidence`) will appear containing the JSON execution log and the raw text chunks retrieved.

*Known Limitations:* If the JSON trace returned by a complex command is exceptionally long, Groq may occasionally hit max token limits. Wait 60 seconds and try again securely.

---

*HappyGroup · UMKC Data Science · 2026*
