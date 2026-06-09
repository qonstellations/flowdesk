# BACKEND REVIEW NOTES: FlowDesk

## Purpose

These notes capture the backend review after reading the current implementation. They are not implementation instructions for immediate work. Use this as a roadmap for redesigning the MVP backend before adding tests.

## User Feedback

### 1. Student identity and verification

The current `users` model relies mostly on `telegram_id`, which only identifies a Telegram account. It does not prove the sender is a real student.

Potential direction:

* Add student verification.
* Consider Google OAuth and require an approved `.edu` or institution-owned domain.
* Decide whether Telegram should remain the primary intake channel after verification or whether the web app should handle account linking.

### 2. Remove student department

Student users do not need a department field. Department should apply to staff/admin routing and assignment, not students.

### 3. Remove hardcoded seeding and make departments configurable

Departments should not be seeded as fixed defaults. Admins should be able to create and manage departments, contacts, and routing metadata.

Open question:

* How should admin identity be verified?
* Is strong admin authentication required for the MVP, or is a simpler admin key acceptable temporarily?

### 4. Make Telegram ID required

`telegram_id` should not be optional in `run_workflow()` or the ticket creation flow for this version.

Reason:

* Tickets need a definite owner.
* Telegram replies and status tracking depend on it.

### 5. Intake should clarify unclear complaints

The intake prompt currently says not to reject unclear complaints and proceeds anyway. This should change.

Desired behavior:

* If the complaint is unclear, the bot should have a back-and-forth conversation with the Telegram user.
* The system should only continue once the issue is definite enough.
* The intake agent should check for required signals, such as:
  * real campus issue
  * affected service/facility
  * location, if needed
  * urgency/severity
  * enough context for staff to act

### 6. Replace `call_gemini()` with provider-agnostic `call_llm()`

Rewrite the LLM layer so it checks environment variables and calls the configured provider.

Potential environment variables:

* `LLM_PROVIDER=gemini|openai|ollama`
* `LLM_API_KEY=...`
* `LLM_MODEL=...`
* `OLLAMA_HOST=...`

### 7. Do not create tickets for unverified problems

A ticket should only be created when the system has a definite, verified complaint.

Unclear, spam, casual chat, or incomplete messages should not create tickets.

### 8. Remove fixed categories and route against admin-created departments

`constants.CATEGORIES` should eventually be removed or replaced with database-backed configuration.

Departments should be created by the admin, and routing should use the current department records instead of hardcoded category mappings.

### 9. Replace SLA wording with more user-friendly language

The current SLA concept may feel too formal or inaccurate for the user-facing product.

Potential alternatives:

* estimated completion time
* expected resolution time
* target resolution time
* response window

### 10. Rewrite `router.py`

The current router only maps fixed categories to seeded departments. It should be rewritten around admin-created departments and their descriptions/contact metadata.

### 11. Improve resolution-time calculation

The current deadline calculation is a simple priority-to-hours map. The LLM should help decide urgency based on severity and problem details.

Potential direction:

* LLM estimates urgency and target window.
* Backend still validates the result against bounded allowed values.
* Admin-configured department rules can override or constrain the LLM.

### 12. Rewrite `llm.py` and remove mock fallback

The current mock fallback should be removed. If the AI cannot classify/validate the complaint, the system should fail clearly or ask the user for clarification instead of fabricating a result.

Prompting should include domain-specific hints and key terms to help the LLM classify campus issues better.

### 13. Improve Telegram typing indicators

`send_typing_action()` is not used consistently. The bot should show typing indicators whenever the user is waiting for LLM validation, clarification, classification, routing, or ticket creation.

### 14. Understand `delete_webhook()`

`delete_webhook()` removes the Telegram webhook registered for the bot. This is useful when:

* switching from webhook mode to local polling
* changing tunnel/domain URLs
* disabling the bot integration temporarily
* debugging webhook registration problems

### 15. Complaint validation

The deterministic validation idea is useful, but the LLM should likely perform deeper validation.

Potential direction:

* Keep deterministic validation for cheap obvious rejection.
* Use LLM validation for nuanced judgment.
* Do not create a ticket until both the system and the user-provided details are sufficient.

## Suggested Design Improvements

### Authentication and identity

Separate identity concerns:

* Telegram account identity: `telegram_id`
* Verified institutional identity: email/domain/OAuth subject
* App role: student, staff, admin

Recommended MVP path:

1. Keep Telegram as intake.
2. Add a `verified_email` and `is_verified` field to users.
3. Add a simple account-linking flow later: student opens web portal, signs in with Google, then links Telegram ID.
4. For the first proper MVP, admin can use an environment-based admin key, but the code should be structured so proper auth can replace it.

### Departments and routing

Replace category-first routing with department-first configuration.

Possible department fields:

* `name`
* `description`
* `responsibilities`
* `contact`
* `active`
* `default_target_hours`
* `escalation_contact`

Routing prompt should receive current active departments and choose one by ID/name with a confidence score and reason.

### Clarification flow

Clarification should not live only inside LangGraph as a single pass. Telegram is asynchronous, so the backend likely needs conversation state.

Possible state fields:

* `telegram_id`
* `draft_complaint`
* `missing_fields`
* `asked_questions`
* `answers`
* `created_at`
* `expires_at`

Flow:

```text
/ticket raw issue
→ validate/inspect completeness
→ if incomplete, save draft and ask one or two questions
→ next Telegram message answers questions
→ merge answer into draft
→ repeat only if still incomplete
→ create ticket
```

### LLM provider layer

`call_llm()` should have a stable internal contract:

* accepts prompt/messages
* accepts optional schema
* returns parsed structured data
* raises a clear exception on provider failure

Do not silently fall back from provider failure to fake classification.

### Resolution time

Use user-facing wording in Telegram and UI:

* "Target resolution"
* "Expected completion"

Internally, the database can still store a timestamp field such as `target_resolution_at`. The name can be changed later through migration if desired.

### Testing later

When the core layers settle, add tests around:

* complaint validation and clarification decisions
* LLM response parsing and provider errors
* routing against custom departments
* ticket creation only after verified completeness
* admin-created department configuration
* Telegram webhook conversation state

Avoid adding test-only branches to runtime code.

## Suggested Implementation Order

1. Redesign data model for users, verification, departments, and complaint drafts.
2. Rewrite LLM provider layer as `call_llm()`.
3. Define structured schemas for complaint validation, clarification, routing, and target resolution.
4. Implement Telegram clarification state before ticket creation.
5. Replace hardcoded categories/departments with admin-configured departments.
6. Rename SLA-facing language to target/expected resolution.
7. Add real admin configuration screens.
8. Add authentication/verification flow.
9. Add tests only after these interfaces stabilize.
