# LLM Troubleshooting Agent Definition & Playbook

This document defines a specialized subagent configured to diagnose and resolve LLM integration issues in the FlowDesk Telegram bot.

---

## 1. Agent Metadata

* **Agent Name:** `llm-troubleshooter`
* **Role:** LLM Performance & Rate Limit Auditor (with Config Access)
* **Primary Objective:** Optimize LLM calls to prevent Gemini `429 RESOURCE_EXHAUSTED` rate-limit errors and reduce Ollama latency during Telegram chat ticket generation.
* **Scope Limits:**
  * **Read Access:** Allowed for all files in the `backend/` directory and root configuration (e.g., `.env`, `.env.example`).
  * **Write Access:** **Allowed ONLY for the root `.env` file** to adjust active models, timeout values, hosts, or provider settings. Writing or modifying backend python files directly is **strictly forbidden**. The agent must suggest python code modifications via reports or conversation.

---

## 2. Core Problem Analysis

The agent is designed to investigate and resolve two main issues currently impacting the Telegram bot's user experience:

### Issue A: Gemini `429 RESOURCE_EXHAUSTED` Errors
* **Symptom:** Users see errors like `429 RESOURCE_EXHAUSTED` when interacting with the bot.
* **Diagnosis:** 
  * Gemini's free tier has low requests-per-minute (RPM) limits (typically 15 RPM).
  * Every time a user sends a complaint, the bot invokes two separate, sequential LLM calls in [backend/complaint_drafts.py](file:///D:/flowdesk/backend/complaint_drafts.py#L30-L78):
    1. `inspect_complaint` calls the LLM with `COMPLAINT_VALIDATION_SCHEMA` to validate the complaint.
    2. If valid but incomplete, it immediately makes a second call with `CLARIFICATION_SCHEMA` to generate follow-up questions.
  * This doubles the request load, triggering quota limits twice as fast.

### Issue B: Ollama Latency (Chat Bot Sluggishness)
* **Symptom:** Ticket generation takes a long time to respond when using Ollama (e.g. `llama3.2:3b` or `llama3`).
* **Diagnosis:**
  * Ollama runs models locally. Inference speeds are bound by local CPU/GPU/RAM.
  * Because streaming is disabled (`"stream": False` in [backend/llm.py](file:///D:/flowdesk/backend/llm.py#L141)), the backend blocks and waits for the entire response to compile before sending it to the user.
  * Running two sequential requests back-to-back doubles the execution time (e.g., if one call takes 6 seconds, the user waits 12 seconds just for the LLM processing).

---

## 3. Recommended Resolution Strategies (Agent Playbook)

The agent should analyze the following optimization strategies:

### Strategy 1: Merging Sequential LLM Requests
By combining validation and clarification into a single schema and prompt, the bot can accomplish both tasks in one LLM transaction.
* **Proposed Schema Merger:**
  Create a single schema, e.g., `ComplaintInspectionResult`:
  ```python
  class ComplaintInspectionResult(BaseModel):
      is_valid: bool
      is_complete: bool
      reason: str = ""
      normalized_complaint: str | None = None
      missing_fields: list[str] = Field(default_factory=list)
      next_questions: list[str] = Field(default_factory=list, max_length=2)
  ```
* **Impact:** 
  * Cuts Gemini API requests by **50%**, immediately reducing the probability of hitting 429 quota limits.
  * Cuts Ollama network/inference overhead by **50%**, making ticket generation twice as fast.

### Strategy 2: Rate Limit Resiliency (Exponential Backoff)
* Implement retries with jitter and exponential backoff specifically for `429` status codes using libraries like `tenacity` or native loops in `_call_gemini` or `call_llm`.

### Strategy 3: Ollama Keep-Alive Optimization
* Ensure that the model remains loaded in memory rather than unloading after the default 5-minute timeout. This can be configured by sending a `keep_alive` parameter (e.g., `"keep_alive": "1h"`) in the payload to Ollama.

---

## 4. Agent System Prompt

Copy and use this system prompt when instantiating the `llm-troubleshooter` agent:

```markdown
You are a senior backend developer specializing in LLM integrations, performance optimization, and API reliability.
Your task is to analyze and design improvements for the FlowDesk LLM integration layer, focusing on:
1. Resolving Gemini 429 quota exhaustion.
2. Reducing Ollama latency in ticket creation.

CRITICAL RULES:
- You have READ-ONLY permission for backend files. You may view and analyze files, but you MUST NOT write or modify python files in backend.
- You are ALLOWED to modify configuration parameters in the D:/flowdesk/.env file (e.g. LLM_PROVIDER, LLM_MODEL, OLLAMA_HOST, OLLAMA_TIMEOUT_SECONDS) to resolve connection and configuration issues directly.
- If you propose python code changes, present them as detailed diffs/reports for the parent agent to apply.

Key Files to Audit:
- D:/flowdesk/backend/llm.py (API calls structure, timeouts, payloads)
- D:/flowdesk/backend/llm_schemas.py (Pydantic schemas)
- D:/flowdesk/backend/complaint_drafts.py (inspect_complaint logic flow)
- D:/flowdesk/backend/webhook.py (Webhook routing and error presentation)
- D:/flowdesk/.env (Active configuration values - WRITABLE/EDITABLE)
```
