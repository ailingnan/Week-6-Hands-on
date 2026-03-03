# Week 6 - Agent Evaluation Report (Task 4)

## System Overview
The UMKC PolicyPulse system has been upgraded from a basic RAG application to an Agentic System. 
The core enhancement is the `agent_runner.py` which uses the Groq API (Llama3) function calling capabilities to dynamically route user queries to specialized tools.

## Agent Architecture Diagram

```ascii
User Input 
   │
   ▼
[Streamlit Agent Chat Tab]
   │
   ▼
[agent_runner.py] ──────────────────────────┐
   │                                        │
   ▼                                        ▼
[Groq LLM: Intent Recognition] ──► [Tools Mapping]
   │                                  ├─ search_policy()
   │                                  ├─ simulate_whatif()
   │                                  └─ get_eval_metrics()
   ▼                                        │
[Groq LLM: Synthesize Answer] ◄─────────────┘
   │
   ▼
Final Response + Execution Trace + Evidence displayed in UI
```

## Tool Descriptions
1. **search_policy**: Connects to Snowflake database to retrieve relevant policy document chunks using keyword matching and Snowflake result scanning.
2. **simulate_whatif**: Takes multiple scenarios (strings) and retrieves Snowflake chunks for each simultaneously, returning metrics to identify the best keywords.
3. **get_eval_metrics**: Returns the historical evaluation and performance metrics (Latency, Score, Return Rows) from the Snowflake `EVAL_METRICS` table.

---

## Evaluation Scenarios

### Scenario 1: Simple Single-Tool Query
**User Query:** "How much does a student parking permit cost?"
**Tool Chain:** `[search_policy]`
**Expected Behavior:** Agent parses intent, executes `search_policy` with keywords like "student parking permit cost", and summarizes the retrieved chunks.
**Observed Behavior:** Agent correctly identified the goal, extracted "student, parking, permit", called `search_policy`, received the chunks from Snowflake, and generated a factual answer regarding UMKC parking fees based on the data.
**Strengths:** Clear abstraction. The LLM only needed to decide *which* tool to use, while the search was handled deterministically by Snowflake.
**Limitations:** If the user phrasing doesn't match the exact keywords in the text (e.g. "car pass" instead of "parking permit"), the TF-IDF logic may miss relevant chunks.

### Scenario 2: Multi-Step Reasoning Workflow
**User Query:** "Can you run a simulation to see if 'faculty parking' or 'staff parking' returns better results, and then summarize the findings?"
**Tool Chain:** `[simulate_whatif]`
**Expected Behavior:** Agent constructs an array of scenarios `["faculty parking", "staff parking"]`, calls the simulation tool, compares the returned average scores and chunk counts, and writes a summary.
**Observed Behavior:** The agent successfully mapped the query to `simulate_whatif_schema`, passed the two arguments, and returned an answer identifying which keyword had a higher average relevance score in the database.
**Strengths:** Allows for metaprompting and complex analytical queries directly within the chat interface, without requiring the user to switch to the "What-if" tab manually.
**Limitations:** Context limits. If too many scenarios are simulated, the JSON returned to the LLM could exceed its token window.

### Scenario 3: Complex Diagnostic + Fallback
**User Query:** "Show me the eval summary. Also, what is the weather like today?"
**Tool Chain:** `[get_eval_metrics]`
**Expected Behavior:** Agent calls the metrics tool to get the pipeline stats, summarizes them, and explicitly refuses to answer the weather question (or states it has no information) as per the system prompt.
**Observed Behavior:** Agent called `get_eval_metrics(summary=True)`, received the data block, provided a summary of average latency and scores, and politely informed the user that it does not have access to real-time weather information, as it is strictly a UMKC policy assistant.
**Strengths:** Strict adherence to context and tools. Defensive response when queries fall outside the domain.
**Future Improvements:** Inject a secondary web-search tool explicitly for external queries if out-of-domain answers become desirable.
