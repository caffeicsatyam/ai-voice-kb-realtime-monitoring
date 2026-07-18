# Limitations

This repository is an assessment prototype, not a production lending or insurance system.

- Gemini-backed agent replies require a valid Google API key and available quota. The deterministic KB and nudge portions work locally without it.
- Browser speech recognition and speech synthesis depend on the browser, selected voice, microphone permission, and network behavior. Accent quality is not formally benchmarked.
- The Q4 demo replays timestamped transcript chunks. It proves live-style incremental processing, but it does not include a streaming telephony provider or production diarization model.
- Nudge detection is intentionally transparent and deterministic, using rule patterns. It has known false-positive and false-negative risk, especially with colloquial language, poor ASR, negation, and multi-turn context.
- The local BM25 retriever is keyword-based. It does not provide semantic embeddings, access control, or managed index operations.
- Demo policies, customer examples, and CRM records are synthetic. They must not be used for financial decisions.
- Source document parsing targets the included Markdown inputs. PDF, DOCX, scanned images, and complex HTML need dedicated parsers and OCR.
- The supplied localized evidence consists of scripts, configurations, and automated localization checks. Final submission should add two real recorded test calls per market, with consent and no real PII.
- Qualification output is a preliminary assessment only. Final approval must be handled through regulated underwriting and document verification.
