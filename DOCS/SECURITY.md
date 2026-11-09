# Security and privacy scope

This is a single-user, loopback-only research prototype, not a hardened enterprise deployment.

Implemented controls include a 20 MiB PDF content check; a 50-page limit; encrypted/invalid-file rejection; bounded rendered image allocation; a per-OCR batch subprocess timeout; content-hash storage filenames; parameterized SQL; foreign-key transactions; escaped text in the frontend; spreadsheet formula neutralization in CSV exports; same-origin checks for browser writes; a restricted Host header; and local-only Ollama endpoints. The default pipeline does not send document text to an external service. Neo4j export is an explicit user command and uses parameters.

Remaining risks include PDF-parser vulnerabilities, resource exhaustion before application-level upload checks, no authentication, no per-user authorization, no encryption-at-rest layer, no antivirus sandbox, and no audited retention/deletion workflow. OCR and classification are fallible. PDF text and LLM output are untrusted data, not instructions. Quote and endpoint membership checks do not prove semantic entailment. Optional LLM results are labeled `ollama_unreviewed` and must be reviewed.

Do not bind this app to a public interface, expose it through a tunnel, or upload confidential documents without a separate security design. Keep `.env`, credentials, local SQLite files and user uploads out of Git. Only the original fictional fixtures belong in the supplied `DATA/raw/` directory. A new private repository is the publishing helper's default.
