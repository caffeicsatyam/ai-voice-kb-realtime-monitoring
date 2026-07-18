# Google ADK Stack Decision

Use Google ADK as the assessment's agent orchestration layer, while keeping infrastructure free/local-first.

## Why ADK

- It makes the project look like a real agent system instead of a single prompt wrapper.
- It cleanly separates agents for loan qualification, Philippines localization, Indonesia localization, and real-time nudges.
- It exposes KB retrieval, qualification, escalation, CRM logging, signal detection, and nudge emission as tools.
- It supports callbacks for citation guards, latency logging, and safe fallback behavior.
- It gives a strong walkthrough story: agents, tools, callbacks, tests, evidence, and production path.

## Free/Local Boundary

ADK should not force paid infrastructure. Keep these local:

- KB storage and search: JSONL plus SQLite/BM25/TF-IDF/local FAISS.
- Voice demo: local browser microphone interface.
- TTS: browser SpeechSynthesis, Windows voices, or free Edge TTS voices.
- ASR: local Whisper option when available; prepared transcripts as a documented fallback for non-core demos.
- Real-time nudges: recording replayed in real-time chunks.
- Evidence: local recordings, transcripts, logs, screenshots, and latency reports.

## Proposed ADK Agents

- `loan_qualification_agent`: handles Q1 conversation flow and calls retrieval/qualification/escalation tools.
- `philippines_voice_agent`: handles English, Filipino/Tagalog, and Taglish bancassurance or life-insurance flow.
- `indonesia_voice_agent`: handles formal/colloquial Bahasa Indonesia, finance loanwords, and regional-accent observations.
- `realtime_nudge_agent`: receives transcript chunks and signal context, then emits short prioritized nudges.

## Proposed ADK Tools

- `retrieve_kb(query, filters)`: returns cited KB chunks with record IDs and source references.
- `qualify_lead(profile)`: returns preliminary eligibility and missing fields.
- `create_mock_crm_lead(summary)`: writes a local JSON lead record.
- `schedule_callback(request)`: writes a local callback record.
- `escalate_to_human(reason, context)`: writes an escalation log.
- `detect_signals(transcript_chunk, state)`: detects compliance gaps, frustration, missed opportunities, and callback needs.
- `emit_nudge(signal)`: applies confidence thresholds, cooldown, dedupe, priority, and expiry.

## Quality Bar

The final demo should show ADK tool calls in logs. At minimum, evidence must prove:

- Q1 called `retrieve_kb` during a voice conversation.
- Q1 safely refused or escalated an unsupported question.
- Q2 retrieval tests include citations and verdicts.
- Q3 uses separate localized agents, not literal translations.
- Q4 emits nudges while chunks are still being processed, with measured latency.
