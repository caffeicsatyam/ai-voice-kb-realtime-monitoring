# AI Engineer Assessment Execution Plan - Google ADK + Free Stack

## Goal

Submit a working 48-hour prototype that proves four things:

- A knowledge-grounded voice agent can qualify or support a real customer conversation.
- A traceable knowledge base can be built from messy business material and connected to the agent.
- Localized voice bots can handle Philippines and Indonesia financial conversations naturally.
- Live call audio can produce useful real-time nudges with measured latency and false-positive controls.

The winning strategy is to keep the scope narrow, integrated, measurable, and easy to explain.

Use **Google ADK as the agent orchestration layer**. ADK should coordinate the loan qualification agent, KB retrieval tool, multilingual market agents, and real-time nudge agent. Keep the rest of the stack free/local-first so the project can run without paid telephony or managed infrastructure.

## Recommended Scope

Use one core business domain across Questions 1, 2, and 4:

**Business-loan qualification for small businesses**

Why this scope works:

- Qualification rules are easy to model: business age, monthly revenue, location, requested amount, collateral, documents, and repayment capacity.
- Objections are realistic: interest rate, eligibility uncertainty, documents, callback timing, and trust.
- The same calls can be reused for real-time nudges: missed document collection, missing disclosure, customer frustration, callback request, and eligibility signal.
- It avoids heavier medical or regulated insurance complexity while still showing production judgment.

For Question 3, keep separate localized prototypes:

- Philippines: bancassurance or life-insurance renewal reminder in English, Filipino, and Taglish.
- Indonesia: consumer-finance installment reminder in formal and colloquial Bahasa Indonesia, with one non-Jakarta accent test.

## Target Architecture

```text
source_docs/
  web_pages/
  policy_docs/
  faq_docs/
  forms/
       |
       v
kb_builder/
  extraction -> cleaning -> dedupe -> normalization -> PII scan
       |
       v
knowledge_base/
  records.jsonl
  chunks.jsonl
  local_index
  retrieval_tests.json
       |
       v
adk_app/
  root_agent.py
  agents/
    loan_qualification_agent.py
    philippines_voice_agent.py
    indonesia_voice_agent.py
    realtime_nudge_agent.py
  tools/
    retrieve_kb.py
    qualify_lead.py
    crm_mock.py
    escalate.py
    detect_signals.py
    emit_nudge.py
  callbacks/
    citation_guard.py
    latency_logger.py
    safety_fallback.py
       |
       v
web_app/
  FastAPI adapter
  browser microphone UI
  browser/Windows TTS
  transcript and evidence logger
       |
       +--> Q1 local web voice agent
       |
       +--> Q3 localized voice prototypes
       |
       +--> Q4 real-time replay + nudge dashboard/CLI
```

## Implementation Choices

Use **Google ADK + a free/local-first stack**:

- Agent framework: Google ADK for orchestration, tools, callbacks, agent separation, and evaluation-friendly traces.
- App/API layer: Python FastAPI to expose ADK agents to the local web UI and test scripts.
- Main Q1 agent: ADK `loan_qualification_agent` with tools for KB retrieval, lead qualification, mock CRM, callback scheduling, and escalation.
- Q3 agents: separate ADK agents for Philippines and Indonesia so localization choices are explicit and testable.
- Q4 agent: ADK `realtime_nudge_agent` that receives transcript chunks/signals and returns short actionable nudges.
- Knowledge base: JSONL records plus a local SQLite, BM25, TF-IDF, or FAISS index.
- Retrieval: local hybrid keyword plus optional local embedding similarity, with citations and metadata.
- Model strategy: keep the LLM provider configurable. Prefer local Ollama via LiteLLM if available; otherwise use the lowest-cost/free Gemini option only if the user has available quota. Keep deterministic/rule-based fallbacks for scoring and nudges.
- Embeddings: start with TF-IDF/BM25 for zero-cost reliability; optionally use local `sentence-transformers` if already available.
- Voice interface: local browser-based web calling using microphone input and browser or Windows TTS.
- ASR: local `faster-whisper`, `whisper.cpp`, or another installed local Whisper option; use manual transcripts only as a fallback if local ASR setup is blocked.
- TTS: browser SpeechSynthesis, Windows built-in voices, or free Edge TTS voices where available.
- Real-time demo: replay recorded audio in real-time chunks and process chunks as they arrive.
- Dashboard: simple local HTML/JS page, CLI, FastAPI polling endpoint, or Streamlit if already installed.
- Storage: local files for assessment evidence; mock CRM action as JSON output or webhook log.

Avoid paid telephony or hosted voice platforms unless free credits are already available. A local web calling interface is enough if it demonstrates audio input, transcription, retrieval-grounded responses, TTS/playback, transcripts, and logs.

## 48-Hour Timeline

### Hours 0-2: Setup and Scope Lock

- Choose the main use case: business-loan qualification.
- Confirm the ADK + free/local stack: Google ADK, FastAPI, local retrieval, browser microphone, local/browser TTS, and real-time replay.
- Create repository structure, README skeleton, `.env.example`, and test evidence folders.
- Define the exact business rules and qualification fields.

Deliverables by hour 2:

- Repo structure.
- Chosen ADK agent structure and free/local tools.
- Use-case script outline.
- Business rules draft.

### Hours 2-8: Question 2 Knowledge Base

Build the KB first because Question 1 depends on it.

Tasks:

- Collect or create representative source material:
  - product overview
  - loan eligibility rules
  - required documents
  - pricing or fee disclaimers
  - FAQs
  - objection-handling notes
  - mock forms with PII examples
- Implement ingestion and cleaning:
  - remove navigation/header/footer noise
  - deduplicate repeated sections
  - normalize terms such as "loan amount", "requested funding", and "principal"
  - flag PII such as phone numbers, email addresses, names, IDs, and addresses
- Create record and chunk schema.
- Add source tracking, version, category, product, jurisdiction, and PII flags.
- Build retrieval interface.
- Run at least five retrieval tests.

Minimum KB schema:

```json
{
  "record_id": "kb_loan_001",
  "title": "Business Loan Eligibility",
  "content": "Applicants must have at least 12 months of business operation...",
  "category": "qualification",
  "product": "small_business_loan",
  "source_type": "policy_doc",
  "source_ref": "source_docs/policy_docs/eligibility.md#business-age",
  "version": "1.0",
  "contains_pii": false,
  "effective_date": "2026-07-18"
}
```

Required retrieval tests:

- Product question: "What loan products are available?"
- Policy question: "Can a business operating for 8 months qualify?"
- Qualification question: "What documents do I need?"
- FAQ question: "How long does approval take?"
- Objection question: "Why do you need my bank statements?"

Deliverables by hour 8:

- `records.jsonl`
- `chunks.jsonl`
- retrieval interface
- retrieval test report with verdicts
- citations visible in answers

### Hours 8-16: Question 1 Knowledge-Grounded Voice Agent

Tasks:

- Build the ADK `loan_qualification_agent` and local web voice interface.
- Add the business-loan qualification script.
- Connect the ADK agent to the KB retrieval tool; do not bypass retrieval for FAQs, objections, or policy answers.
- Implement qualification logic:
  - business age
  - monthly revenue
  - requested amount
  - location
  - documents available
  - preferred callback time
- Add unsupported-question fallback:
  - "I do not have that information in the current knowledge base."
  - offer human escalation.
- Add objection handling through retrieval, not hardcoded FAQ dumping.
- Add one optional business action:
  - mock CRM lead creation
  - callback scheduling
  - escalation webhook

Required test calls:

- Cooperative customer.
- Customer with objection.
- Incomplete or conflicting details.
- Out-of-scope question.
- Human-assistance request.

Deliverables by hour 16:

- Local web calling link, for example `http://localhost:8000`.
- ADK agent config, tool definitions, prompt/instructions, and local conversation-flow config.
- API endpoint logs.
- 3 or more recordings.
- transcripts and qualification results.

### Hours 16-24: Question 3 Native-Language Voice Bots

Build small but convincing prototypes instead of large generic agents.

Philippines bot:

- Sector: bancassurance or life-insurance renewal reminder.
- Languages: English, Filipino/Tagalog, and Taglish.
- Must naturally use: premium, policy, beneficiary, rider, lapse, coverage, bank referral.
- Test code-switching and fallback in the same language/register.

Indonesia bot:

- Sector: consumer finance installment reminder.
- Languages: formal Bahasa Indonesia, colloquial Bahasa Indonesia, English finance loanwords.
- Include one regional-accent test outside standard Jakarta speech.
- Must naturally use: cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan.

Tasks:

- Configure separate ADK market agents plus local/browser ASR and TTS settings per market, or document any free-tool compromise.
- Write localized scripts, FAQs, objections, and fallback messages.
- Run two recorded calls per market.
- Document provider/model, languages tested, code-switching quality, ASR errors, TTS compromises, and accent observations.

Deliverables by hour 24:

- Philippines bot config and two recordings.
- Indonesia bot config and two recordings.
- transcripts.
- localization examples, at least three per market.
- native-speaker/compliance gap notes.

### Hours 24-34: Question 4 Real-Time Insights and Nudges

Use recorded calls from Question 1 or 3 and replay them in real-time chunks. This qualifies if the system processes audio as it arrives and emits nudges before playback ends.

Tasks:

- Build streaming simulation:
  - split audio into 2-5 second chunks
  - send each chunk at real-time speed
  - transcribe continuously
- Track latency:
  - audio chunk received
  - ASR completed
  - signal extraction completed
  - nudge generated
  - nudge displayed
- Implement signals:
  - missed cross-sell or missed follow-up
  - skipped disclosure or risky statement
  - rising frustration
  - payment difficulty or callback need
  - noisy/ambiguous segment suppression
- Implement nudge control:
  - confidence threshold
  - duplicate suppression
  - cooldown
  - expiry
  - priority level

Nudge examples:

```json
{
  "timestamp": "00:01:18",
  "signal": "missing_disclosure",
  "priority": "high",
  "confidence": 0.86,
  "nudge": "Mention that final approval depends on document verification.",
  "expires_after_seconds": 30
}
```

Required tests:

- Missed opportunity.
- Skipped disclosure or risky statement.
- Rising frustration.
- Noisy or ambiguous call with no unnecessary nudge.

Deliverables by hour 34:

- streaming/simulation script connected to the ADK nudge agent
- dashboard, CLI, webhook, WebSocket, or polling output
- latency report with P50/P95
- false-positive notes
- recorded live demo

### Hours 34-42: Evidence, Tests, and Hardening

Tasks:

- Run all test scenarios end to end.
- Save recordings, transcripts, logs, and screenshots.
- Create a clear test-results table.
- Verify the bot says "unknown" when the KB lacks an answer.
- Verify the KB is actually called during voice conversations.
- Verify nudges appear within seconds and do not repeat excessively.
- Add known limitations and production-improvement plan.

Deliverables by hour 42:

- test matrix
- transcripts
- call recordings
- retrieval report
- latency report
- known limitations

### Hours 42-48: README and Walkthrough Video

Tasks:

- Finalize README:
  - setup
  - env vars
  - architecture
  - how to run each question
  - sample inputs
  - test results
  - limitations
- Record video walkthrough:
  - system overview
  - live demo
  - KB and retrieval design
  - voice flow
  - multilingual handling
  - live nudges
  - fallback/error cases
  - production improvements
- Remove secrets and customer data.
- Make final submission package.

Deliverables by hour 48:

- repository link
- README
- `.env.example`
- architecture diagram
- recordings
- transcripts
- video walkthrough
- test reports

## Repository Structure

```text
ai-voice-adk-assessment/
  README.md
  .env.example
  agent.md
  docs/
    architecture.md
    adk_stack.md
    assessment_notes.md
    limitations.md
    production_improvements.md
  source_docs/
    web_pages/
    policy_docs/
    forms/
    multilingual/
  kb_builder/
    ingest.py
    clean.py
    dedupe.py
    pii.py
    build_index.py
  knowledge_base/
    records.jsonl
    chunks.jsonl
    retrieval_tests.json
    retrieval_report.md
  adk_app/
    root_agent.py
    agents/
      loan_qualification_agent.py
      philippines_voice_agent.py
      indonesia_voice_agent.py
      realtime_nudge_agent.py
    tools/
      retrieve_kb.py
      qualify_lead.py
      crm_mock.py
      escalate.py
      detect_signals.py
      emit_nudge.py
    callbacks/
      citation_guard.py
      latency_logger.py
      safety_fallback.py
  web_app/
    main.py
    static/
    templates/
  voice_configs/
    q1_business_loan_agent.md
    q3_philippines_agent.md
    q3_indonesia_agent.md
  realtime_nudges/
    stream_replay.py
    transcribe.py
    signals.py
    dashboard.py
    latency_report.py
  evidence/
    recordings/
    transcripts/
    screenshots/
    logs/
    test_results.md
```

## Test Matrix

| Area | Scenario | Expected Result | Evidence |
| --- | --- | --- | --- |
| Q1 voice agent | cooperative customer | qualifies lead, creates mock CRM summary | recording, transcript, result JSON |
| Q1 voice agent | objection | answers using KB citation | recording, transcript, retrieval log |
| Q1 voice agent | incomplete/conflicting details | asks clarifying question | transcript |
| Q1 voice agent | out-of-scope question | says information is unavailable | transcript |
| Q1 voice agent | human request | escalates or schedules callback | transcript, webhook log |
| Q2 KB | product query | retrieves correct product chunk | retrieval report |
| Q2 KB | policy query | cites qualification policy | retrieval report |
| Q2 KB | objection query | retrieves objection-handling guidance | retrieval report |
| Q3 Philippines | Taglish customer | stays natural and local | recording, transcript |
| Q3 Philippines | human escalation | remains in Filipino/Taglish | transcript |
| Q3 Indonesia | colloquial speech | handles local phrasing | recording, transcript |
| Q3 Indonesia | regional accent | documents ASR quality/errors | transcript, notes |
| Q4 nudges | missed opportunity | emits useful nudge before call ends | dashboard/video |
| Q4 nudges | skipped disclosure | emits compliance nudge | dashboard/video |
| Q4 nudges | frustration | suggests empathy/slowdown | dashboard/video |
| Q4 nudges | noisy ambiguous audio | suppresses low-confidence nudge | logs |

## Scoring Priorities

Focus effort according to the evaluation weights:

- Output quality: clear transcripts, reports, citations, and demo evidence.
- End-to-end completeness: make every question run, even if each is compact.
- Functional implementation: prioritize working calls, retrieval, and live nudges.
- Business understanding: explain why the rules and flows match the selected domain.
- Technical depth: include latency, fallbacks, ranking, PII handling, and scale limitations.

## Production Improvement Plan

Mention these clearly in the final walkthrough:

- Replace local JSON/vector index with a managed retrieval service.
- Replace local web calling with production telephony only after the free prototype is proven.
- Add automated source refresh and KB version approvals.
- Add role-based access controls and audit logging.
- Add stronger PII redaction and consent handling.
- Improve streaming diarization for agent/customer separation.
- Add human review workflows for compliance-sensitive nudges.
- Add multilingual native-speaker QA and country-specific compliance review.
- Load test 10x concurrency and measure ASR, LLM, and delivery bottlenecks.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Browser voice setup takes too long | Use typed-chat plus recorded audio/TTS demo, and document it as a local web voice fallback |
| Real-time audio integration is hard | Replay recordings in chunks at real-time speed |
| Multilingual ASR quality is inconsistent | Document observed errors and fallback behavior honestly |
| Local model downloads are too large | Use TF-IDF/BM25 retrieval and browser/Windows TTS; keep ASR optional or use prepared transcripts for non-core demos |
| KB content is too thin | Create varied source docs with policies, FAQs, forms, objections, and PII examples |
| Nudges are noisy | Use confidence threshold, cooldown, topic grouping, and duplicate suppression |
| Evaluation expects proof, not claims | Save recordings, transcripts, logs, screenshots, and latency metrics |

## Final Submission Checklist

- [ ] Working repository.
- [ ] README with setup and run instructions.
- [ ] `.env.example` with no secrets.
- [ ] Architecture diagram.
- [ ] Q1 ADK-powered local web voice agent.
- [ ] Q1 recordings, transcripts, and results.
- [ ] Q2 KB records, chunks, schema, ADK retrieval tool, retrieval tests, and citations.
- [ ] Q3 Philippines ADK bot recordings, transcripts, config, and localization examples.
- [ ] Q3 Indonesia ADK bot recordings, transcripts, config, and accent observations.
- [ ] Q4 real-time streaming/simulation method.
- [ ] Q4 dashboard/API/CLI nudges.
- [ ] Q4 latency report with P50/P95.
- [ ] False-positive and suppression-control analysis.
- [ ] Video walkthrough.
- [ ] Known limitations and production-improvement plan.
- [ ] No secrets, API keys, or real customer information committed.






