# Architecture and code map

`run.py` is the entrypoint. `Pipeline.ingest` validates and extracts the PDF, creates sentence/line chunks, invokes an extractor, writes the original under a SHA-256 filename, and commits document/chunk/triple rows in one SQLite transaction. Re-ingesting identical bytes is idempotent at the document level.

| Component | Source file | Responsibility |
|---|---|---|
| PDF validation/native text/OCR/rendering | `CODE/docweave/pdf_io.py` | Bound file/page/image sizes, native text first, batch Tesseract fallback, 1-based page provenance |
| Ontology/entities/evidence records | `CODE/docweave/schema.py` | Eight predicates, typed endpoints, exact normalization, deterministic IDs |
| Baseline and learned extractors | `CODE/docweave/extractors.py` | Rules, JSON/NPZ logistic classifier, BiLSTM classifier and conservative guards |
| Neural network | `CODE/docweave/neural.py` | Task-trained 32-d embedding, bidirectional LSTM with 32 units per direction, max pooling, 32-unit hidden layer, nine labels |
| Database and graph | `CODE/docweave/store.py` | Foreign keys, atomic replacement, document lookups and two-hop neighborhood display |
| Retrieval and answers | `CODE/docweave/retrieval.py` | TF-IDF cosine, exact entity matching, typed path planning, +1 complete-path chunk boost, explicit abstention |
| Local HTTP interface | `CODE/docweave/server.py` | Upload, previews, document detail, graph, query, metrics, and exports |
| Browser UI | `CODE/docweave/web/` | Original-page/text comparison, draggable SVG graph, source inspection, trace answers, evaluation tables |
| Optional integrations | `CODE/docweave/adapters.py` | Ollama JSON-schema extraction, Neo4j export, standalone Docling conversion |

## Data contract

A chunk stores `id`, `document_id`, `page`, `text`, and `method`. A triple stores `id`, `subject`, `predicate`, `object`, `chunk_id`, `quote`, `confidence`, and `method`. Document hashes are SHA-256 of the original bytes. Chunk/triple keys use truncated SHA-256 for deterministic local identifiers, not a cryptographic access-control guarantee. A foreign-key chain resolves each triple to its original PDF and page.

## Concrete flow

`workflow-40.pdf` contains `Atlas40 Service is managed by Cedar40 Team.` and `Cedar40 Team is accountable to Assurance40 Council.` Native extraction returns both as text chunks. The classifier sees masked entity types rather than identities; the endpoint validator constructs `MANAGED_BY` and `REPORTS_TO` triples. SQLite stores both with source chunk IDs. The question `Which council supervises the team managing Atlas40 Service?` matches the exact seed entity and the two-relation path. Traversal returns `Assurance40 Council`; both supporting chunks receive the graph ranking boost. The UI shows the result, two predicates and source links. An annual-budget question has no supported path and produces no answer.

## Complexity and scale

Native parsing depends on PDF structure. For N chunks and vocabulary V, TF-IDF uses sparse document-term storage. A query scores every indexed chunk, then sorts N scores: approximately sparse dot-product work plus O(N log N). The current path tracer scans all E triples per hop and matches entity names across the query, favoring clarity over scale. Its short configured paths cost O(hE). Two-hop graph display also scans edges. Replace these scans with indexed adjacency lists and use approximate/vector indexes before scaling to large corpora. No million-document throughput claim is made.
