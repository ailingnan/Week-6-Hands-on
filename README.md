# Week-6-Hands-on
# HappyGroup: Smart Campus Digital Twin
# Video link :# https://drive.google.com/file/d/1A1RJ85WTymJMVNDYLD-HBNPqZzY9y8pI/view?usp=sharing

------------------------------------------------------------------------

# 1. Project Overview

HappyGroup's Smart Campus system is a Snowflake-backed
Retrieval-Augmented Generation (RAG) pipeline extended in Week 6 with a
fully integrated AI Agent layer.

The system transforms authoritative UMKC policy documents into an
intelligent decision-support platform capable of:

-   Snowflake-based document retrieval\
-   Feature-engineered query tracking\
-   Version-based evaluation comparison\
-   Scenario simulation\
-   AI agent reasoning with structured tool calling\
-   Evidence-grounded natural language responses

By Week 6, the project includes:

✔ Snowflake-backed data pipeline\
✔ Automated ingestion workflow\
✔ Evaluation & logging framework\
✔ Tool-based AI Agent\
✔ Interactive chat interface\
✔ Version comparison dashboard

Target milestone: \~60% completion of final capstone system.

------------------------------------------------------------------------

# 2. System Architecture

## Tier 1 --- Source Layer

Authoritative UMKC artifacts (PDFs, CSV files) stored locally under
`/data`.

## Tier 2 --- Processing Layer (Python ETL)

-   `01_extract_chunk.py` --- Cleans null bytes and splits documents
    into 1,200-character chunks with overlap.
-   `scheduler.py` --- Automated ingestion with deduplication.
-   `feature_store.py` --- Extracts version-controlled keyword metadata.

## Tier 3 --- Storage Layer (Snowflake)

Database: `TRAINING_DB`\
Schema: `UMKC_RAG`

Core tables: - DOC_CHUNKS_RAW\
- DOC_CHUNKS_FEATURED\
- FEATURE_STORE\
- EVAL_METRICS\
- INGEST_LOG

## Tier 4 --- Application & Agent Layer

Streamlit Dashboard + Tool-Based AI Agent\
Agent components: - `agent_runner.py`\
- `tools.py`\
- `tool_schemas.py`

Agent workflow: 1. Interpret user request\
2. Route intent\
3. Call tool(s)\
4. Execute workflow\
5. Return evidence-grounded explanation

------------------------------------------------------------------------

# 3. Implemented Extensions

1.  Automated Feature Engineering\
2.  Evaluation Logging\
3.  SQL Retrieval Optimization\
4.  Evaluation Comparison Dashboard\
5.  What-if Simulation\
6.  Scheduled Auto Ingestion

------------------------------------------------------------------------

# 4. Week 6 Required Deliverables

This repository includes:

-   task1_antigravity_report.md\
-   task4_evaluation_report.md\
-   agent/tools.py\
-   agent/tool_schemas.py\
-   agent/agent_runner.py\
-   Updated Streamlit application\
-   Demo video link

------------------------------------------------------------------------

# 5. Setup Instructions

## Install Dependencies

``` bash
pip install -r requirements.txt
```

## Environment Variables (.env)

    SNOWFLAKE_ACCOUNT=your_account
    SNOWFLAKE_USER=your_user
    SNOWFLAKE_ROLE=your_role
    SNOWFLAKE_WAREHOUSE=your_warehouse
    SNOWFLAKE_DATABASE=TRAINING_DB
    SNOWFLAKE_SCHEMA=UMKC_RAG
    GROQ_API_KEY=your_groq_key
    SCHEDULER_INTERVAL_SEC=60

## Run Application

``` bash
streamlit run app/app.py
```

Open: http://localhost:8501

------------------------------------------------------------------------

# 6. Security Notice

RSA private keys are NOT stored in this repository.\
Users must generate and store their own `rsa_key.p8` locally and add it
to `.gitignore`.

------------------------------------------------------------------------

# Final Statement

By Week 6, the HappyGroup Smart Campus system has evolved into a
structured, tool-aware AI agent platform capable of intelligent,
evidence-grounded decision support.

HappyGroup · UMKC Data Science · 2026
