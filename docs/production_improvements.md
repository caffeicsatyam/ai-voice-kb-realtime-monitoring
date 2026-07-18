# Production Improvements

## Reliability and Safety

- Replace the in-memory session, transcript, CRM, and nudge state with authenticated durable services.
- Add consent capture, audit trails, data retention/deletion controls, encryption, tenant isolation, role-based access, and secrets management.
- Add policy version approval, retrieval evaluation gates, factuality checks, and a human review workflow for high-risk conversations.
- Build formal compliance rules with jurisdiction-specific disclosures and escalation playbooks.

## Voice and Localization

- Use a tested streaming ASR provider or local streaming ASR, speaker diarization, voice-activity detection, and confidence calibration.
- Measure word error rate and intent accuracy for Tagalog, Taglish, formal/colloquial Bahasa Indonesia, English loanwords, and non-Jakarta regional accents.
- Use licensed neural TTS voices and run native-speaker reviews for terminology, politeness, register, and code switching.

## Retrieval and Intelligence

- Add hybrid semantic plus lexical retrieval, reranking, document-level ACLs, freshness monitoring, automated document ingestion, and source change alerts.
- Replace simple regex nudges with evaluated classifiers/LLM reasoning that use conversation state, guardrails, and a labeled false-positive dataset.
- Track online quality metrics: grounding rate, escalation rate, nudge acceptance, false-positive rate, containment, latency, and customer satisfaction.

## Operations

- Add structured telemetry, tracing, dashboards, load tests, CI, dependency scanning, and versioned reproducible demo fixtures.
- Integrate an approved telephony provider, CRM, scheduler, and webhook consumer behind authenticated adapters.
- Set SLOs for end-to-end voice latency and test degradation behavior when ASR, model, CRM, or retrieval is unavailable.
