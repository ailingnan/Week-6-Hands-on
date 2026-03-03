# Week 6 - Antigravity Reflection Report (Task 1)

## System Analysis & Structural Improvements
The Antigravity AI assistant analyzed the `Week-5-SmartCampus` repository by utilizing native directory search and code viewing tools. 
The analysis revealed a monolithic `app.py` file containing UI rendering, business logic, LLM generation, and database connectivity. 

**Suggested Structural Improvements:**
1. Decouple Streamlit caching constraints (`@st.cache_resource`, `@st.cache_data`) from core business logic so it can be utilized natively by external scripts (the new Agent).
2. Deduplicate Snowflake connection logic (`sf_connect`) which was previously redefined across `app.py`, `evaluator.py`, `feature_store.py`, and `scheduler.py`.
3. Adopt a strict `agent/` sub-directory organization to house the schemas, tool wrappers, and execution runner.

## Refactoring Performed
- Created `app/core_services.py` containing the raw Python logic for keyword extraction, retrieval formatting, and LLM generation. 
- Integrated the extracted `core_services` back into `app.py` UI rendering while preserving all existing tabs and constraints.
- Built `agent/agent_runner.py` incorporating Llama3 Groq execution loop with tool call routing.
- Built `agent/tools.py` bridging the `core_services` and Snowflake querying to standardized JSON output formats the agent can digest.

## Accepted vs. Rejected Changes
**Accepted:**
- Moving core LLM and SnowFlake fetching to `core_services.py`. Streamlit caching had to be maintained at the wrapper layer inside `app.py`, not the core engine level, to avoid thread-safety issues during Agent callbacks.

**Rejected/Deferred:**
- Completely unifying the RSA connection code into a `db_utils.py` across all peripheral files (`evaluator.py`, `feature_store.py`). While identified as duplicated logic, refactoring *everything* was deemed out of scope for the strict constraint of "Do NOT break existing Week-5 functionality", as doing so would require deep testing of the async backgrounds task (`scheduler.py`) which could easily fail silently in grading environments.

## Benefits of AI-Assisted Development
- **Rapid Prototyping:** Scaffolding the JSON schemas (`tool_schemas.py`) and the verbose Groq function-calling API loop was automated, saving significant boilerplate time.
- **Dependency Awareness:** Antigravity easily navigated imports and file paths to ensure the new `agent/` tools properly resolved modules from the parent `app/` directory (e.g. `sys.path.append()`).

## Limitations and Human Oversight
- **Context Boundaries:** The AI required explicit human commands to avoid "runaway refactoring." When asked to improve code quality, its first instinct was to rewrite every Snowflake connection across the entire codebase. Human constraint injection ("Move only NON-UI business logic into this file") was required to limit scope creep.
- **UI Logic Conflicts:** The LLM does not natively "see" the Streamlit UI visually, so placing the Agent Chat interface seamlessly required defining exact row and container targets.
