# AI Engineer Assessment Agent Guide

## Mission

Build a working, defensible AI Engineer assessment submission within 48 hours using Google ADK as the agent orchestration layer. The final result must demonstrate functional prototypes, grounded AI behavior, measurable results, reliable fallbacks, and clear technical judgment.

Do not produce only architecture notes or a generic PRD. Every major requirement must have working evidence: code, configs, logs, recordings, transcripts, retrieval tests, latency measurements, and a walkthrough.

## Assessment Strategy

Use one tightly connected core domain for Questions 1, 2, and 4:

**Small-business loan qualification**

This keeps the knowledge base, ADK voice agent, and real-time nudge system aligned. It also creates clear qualification logic, realistic objections, and useful compliance or missed-opportunity nudges.

Use separate localized prototypes for Question 3:

- Philippines: bancassurance or life-insurance renewal reminder.
- Indonesia: consumer-finance installment reminder.

Prioritize a reliable core workflow over extra features or visual polish.

## Google ADK + Free-First Stack Rule

Use Google ADK as the orchestration layer, but keep the implementation free/local-first. ADK should own agent definitions, tool calls, callbacks, and workflow separation. Local services should own retrieval, web voice simulation, ASR/TTS, evidence logging, and the real-time replay demo.

Default to free, local, and repository-contained tools. Do not depend on paid telephony, hosted voice-agent platforms, managed vector databases, or paid ASR/TTS unless the user explicitly chooses them or already has free credits.

Preferred stack:

- Agent framework: Google ADK.
- Backend/API: Python FastAPI adapter around ADK agents.
- Model provider: configurable; prefer local Ollama through LiteLLM if available, with Gemini/free quota as an optional fallback.
- Knowledge base: JSONL plus SQLite, BM25, TF-IDF, or local FAISS.
- Retrieval: ADK `retrieve_kb` tool backed by local hybrid keyword search plus optional local embeddings.
- Embeddings: TF-IDF/BM25 first; local `sentence-transformers` only if available.
- Voice interface: local browser microphone interface.
- ASR: local `faster-whisper`, `whisper.cpp`, or installed Whisper option.
- TTS: browser SpeechSynthesis, Windows built-in voices, or free Edge TTS voices.
- Real-time nudges: real-time replay script calls an ADK nudge agent on transcript chunks/signals.
- Dashboard: local HTML/JS, CLI, FastAPI polling, or Streamlit if already installed.

Paid services such as Vapi, Retell, Twilio, hosted ASR/TTS, or managed vector databases are optional production upgrades, not required for the assessment plan.

## Non-Negotiable Outcomes

The submission must include:

- A working voice agent connected to the knowledge base.
- A production-style knowledge base with traceable records, chunks, metadata, citations, and retrieval tests.
- Philippines and Indonesia localized voice bot prototypes with recordings, transcripts, ASR/TTS notes, and localization examples.
- A real-time or real-time-simulated audio pipeline that emits nudges before the call ends.
- Latency report with P50/P95 and component timings.
- Test recordings, transcripts, logs, and clear verdicts.
- README, `.env.example`, architecture diagram, setup instructions, limitations, and production-improvement plan.
- Video walkthrough covering the live demo, architecture, retrieval, voice flow, multilingual handling, nudges, fallbacks, and limitations.

## Core Technical Principles

- Ground answers in retrieved knowledge base records. Do not hardcode all FAQs, policies, objections, or eligibility rules into the prompt.
- Cite sources for retrieval-backed answers.
- If the KB does not contain the answer, say the information is unavailable and offer escalation.
- Keep the system auditable: save source references, record IDs, retrieval logs, transcripts, and decision outputs.
- Use mock actions where full integrations are unnecessary, but make them realistic and logged.
- Measure behavior instead of merely describing it.
- Avoid committing secrets, credentials, real customer information, or raw PII.

## Recommended Repository Structure

```text
README.md
.env.example
agent.md
docs/
  architecture.md
  adk_stack.md
  limitations.md
  production_improvements.md
  test_results.md
source_docs/
  web_pages/
  policy_docs/
  faq_docs/
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
```

## Question 1: Knowledge-Grounded Voice Agent

### Objective

Build a local web-callable Google ADK agent for small-business loan qualification.

### Required Behavior

The agent must:

- Introduce itself clearly and ask for consent to continue.
- Qualify the customer using structured fields:
  - business name
  - business age
  - location
  - monthly revenue
  - requested loan amount
  - loan purpose
  - available documents
  - preferred callback time
- Use the Question 2 knowledge base through an ADK `retrieve_kb` tool for product, policy, FAQ, and objection answers.
- Ask clarifying questions for incomplete or conflicting details.
- Avoid hallucination. If unsupported, say the current KB does not contain that information.
- Escalate to a human when requested or when the conversation becomes risky.
- Create one mock business action:
  - lead summary
  - callback schedule
  - preliminary eligibility result
  - escalation webhook log

### Required Test Scenarios

- Cooperative customer.
- Customer with an objection.
- Incomplete or conflicting details.
- Out-of-scope question.
- Human-assistance request.

### Evidence to Save

- ADK agent instructions, tool definitions, and local voice interface config.
- Local web calling link, for example `http://localhost:8000`.
- At least three recordings.
- Transcripts.
- Qualification result JSON.
- ADK tool-call logs proving the KB was used.
- Mock CRM or escalation logs.

### Quality Gate

Do not mark Q1 complete until at least one transcript and ADK tool log show a retrieved KB answer, one transcript shows an unsupported-question fallback, and one transcript shows escalation or callback handling.

## Question 2: Production-Ready Knowledge Base

### Objective

Convert mixed business content into a structured, searchable, traceable knowledge base usable by the Q1 voice bot.

### Source Material

Create or collect representative source content:

- product overview
- eligibility rules
- required documents
- pricing or fee disclaimers
- FAQ content
- objection-handling guide
- intake form examples
- duplicate material
- inconsistent terminology
- sample PII that must be redacted or flagged

### Processing Requirements

Implement or document:

- website extraction approach
- document parsing approach
- removal of navigation, headers, footers, repeated sections, and irrelevant text
- extraction failure handling
- duplicate and near-duplicate removal
- heading, date, terminology, category, and field normalization
- PII identification and protection
- source error flagging

### Record Schema

Use a schema like:

```json
{
  "record_id": "kb_loan_001",
  "title": "Business Loan Eligibility",
  "content": "Applicants must have at least 12 months of business operation.",
  "category": "qualification",
  "product": "small_business_loan",
  "source_type": "policy_doc",
  "source_ref": "source_docs/policy_docs/eligibility.md#business-age",
  "version": "1.0",
  "contains_pii": false,
  "effective_date": "2026-07-18"
}
```

### Retrieval Requirements

Retrieval must include:

- chunking strategy
- metadata structure
- taxonomy
- versioning
- local embedding, BM25, TF-IDF, or indexing approach
- ranking logic
- citations
- verdicts for test queries

### Required Retrieval Tests

At minimum, test:

- product question
- policy question
- qualification question
- FAQ question
- objection question

Each retrieval test must include:

- user question
- retrieved chunk or record
- source reference
- relevance explanation
- verdict: correct, partially correct, or incorrect

### Quality Gate

Do not mark Q2 complete until the ADK voice agent can call the retrieval tool and answer with citations or safe fallback.

## Question 3: Native-Language Voice Bots

### Objective

Build separate Google ADK localized prototypes for real financial conversations in the Philippines and Indonesia. The goal is natural localization, not literal translation.

### Philippines Bot

Sector:

- life insurance or bancassurance

Language support:

- English
- Filipino/Tagalog
- natural Taglish

Required terms to use naturally:

- premium
- policy
- beneficiary
- rider
- lapse
- coverage
- bank referral

Possible flow:

- renewal reminder
- premium reminder
- lead qualification
- bancassurance cross-sell

### Indonesia Bot

Sector:

- multifinance or consumer finance

Language support:

- formal Bahasa Indonesia
- colloquial Bahasa Indonesia
- finance-related English loanwords
- at least one regional accent outside standard Jakarta speech

Required terms to use naturally:

- cicilan
- tenor
- denda
- DP
- jatuh tempo
- angsuran
- pembiayaan

Possible flow:

- installment reminder
- qualification
- loan follow-up
- collections support

### Required Evidence

For each market, save:

- two recorded calls
- transcripts
- ASR provider/model
- TTS provider/voice
- languages tested
- code-switching observations
- approximate quality
- observed ASR errors
- fallback behavior
- native-speaker or compliance gaps

Also provide at least three localization examples per market showing adaptation rather than direct translation.

### Quality Gate

Do not mark Q3 complete unless fallback and escalation remain in the customer's language/register without sudden unnecessary English switching.

## Question 4: Live Insights and Nudges From Call Audio

### Objective

Analyze call audio while it is happening and produce short, useful recommendations before the call ends.

A completed recording analyzed only after upload does not qualify. If live call streaming is difficult, replay a recording at real-time speed in chunks and process each chunk as it arrives.

### Pipeline Requirements

Implement:

- streaming input from live audio or real-time chunk replay
- continuous transcription
- agent/customer separation where possible
- signal extraction through deterministic rules and/or an ADK nudge agent
- nudge generation through ADK `realtime_nudge_agent`
- dashboard, WebSocket, webhook, polling API, or CLI display
- latency measurement
- nudge suppression controls

### Signals to Track

Track at least:

- missed cross-sell or missed next-step opportunity
- compliance gap or risky statement
- rising frustration
- payment difficulty
- callback need
- noisy or ambiguous audio where nudges should be suppressed

### Nudge Controls

Implement:

- confidence thresholds
- duplicate suppression
- cooldowns
- topic grouping
- priority levels
- expiry rules

### Latency Metrics

Measure:

- audio received to transcription
- transcription to signal extraction
- signal extraction to nudge-decision output
- ADK `realtime_nudge_agent` output to display
- end-to-end latency

Report:

- P50
- P95
- component latency
- approximate false positives

### Required Test Scenarios

- Missed cross-sell or missed opportunity.
- Skipped disclosure or risky statement.
- Rising frustration.
- Noisy or ambiguous call where unnecessary nudges are avoided.

### Quality Gate

Do not mark Q4 complete unless nudges appear within seconds during live playback and repetitive or low-confidence alerts are suppressed.

## Final README Requirements

The README must include:

- project overview
- architecture diagram
- setup instructions
- environment variables
- how to run the KB builder
- how to run retrieval tests
- how to run the ADK app and local voice agent web app/API
- how to run multilingual prototypes
- how to run real-time nudges
- sample inputs
- test results summary
- links or paths to recordings and transcripts
- latency report summary
- known limitations
- production-improvement plan

## Video Walkthrough Script

Cover these points in order:

1. State the business use case and why it was selected.
2. Show the architecture and repository structure.
3. Demonstrate the knowledge base records, metadata, citations, and retrieval tests.
4. Show the Q1 ADK voice agent using the KB retrieval tool during a call.
5. Show fallback behavior for unsupported questions.
6. Show mock CRM, callback, or escalation output.
7. Demonstrate the Philippines and Indonesia localized bot behavior.
8. Explain ASR/TTS choices, code-switching, and localization examples.
9. Demonstrate real-time audio replay or live audio producing nudges.
10. Show latency metrics and suppression controls.
11. Explain known limitations and production improvements.

## Rejection Conditions to Avoid

Never submit:

- only design notes with no working prototype
- a disconnected knowledge base and voice bot
- hallucinated answers without retrieval grounding
- multilingual bots that are only literal translations
- nudges generated only after full call upload
- unmeasured latency
- excessive low-value nudges
- secrets, API keys, or customer information
- polished UI without functional depth
- copied work that cannot be explained

## Definition of Done

The assessment is ready to submit when:

- All four questions have working outcomes.
- Q1 and Q2 are connected through an ADK retrieval tool.
- Q3 has separate Philippines and Indonesia evidence.
- Q4 processes audio during live playback, not only after upload.
- Test coverage maps directly to the assessment requirements.
- Every major claim has evidence.
- Limitations are honest and production-aware.
- The final walkthrough can be confidently explained and defended.






