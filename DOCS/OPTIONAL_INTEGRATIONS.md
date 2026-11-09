# Optional integrations: implemented adapters, not measured services

These are opt-in extensions. The recorded metrics do **not** come from them.

## Local Ollama LLM triplet extraction

Install Ollama separately and select a model your machine can run. The example model name is a configurable default, not a claim that it was downloaded or benchmarked here.

```bash
ollama pull qwen2.5:3b
# With Ollama running locally:
export OLLAMA_MODEL=qwen2.5:3b
python CODE/run.py serve --extractor ollama
```

Only newly uploaded/re-seeded documents use the selected extractor. Starting the server does not silently reprocess existing graph rows. Re-seeding with Ollama can take substantial work and replaces extraction records for the identical synthetic PDFs; export prior results first when comparing methods.

The adapter calls `/api/chat` with `stream=false`, temperature 0, and an explicit JSON schema. Returned quotes and endpoints must occur in the source chunk; unknown predicates, explicit negations and duplicate triples are rejected. This is grounding validation, not a full semantic-fidelity test. The optional LLM supports more entity surface forms than the deterministic typed recognizer, but that behavior has not been measured.

## Neo4j

Install the driver from `requirements-optional.txt`, start an authorized local Neo4j instance, and set credentials in the process environment. A `compose.yaml` is supplied for a local container, but Docker startup and the driver/server integration were not exercised during this artifact build.

```bash
export NEO4J_PASSWORD='set-a-real-local-password'
docker compose up -d
python CODE/run.py export-neo4j
```

The exporter uses `DocWeaveEntity` nodes and `DOCWEAVE_RELATION` relationships with a `predicate` property. It does not interpolate relation types or other document strings into Cypher. `MERGE` uses project-scoped keys. This is an export adapter; the interactive application's canonical store remains SQLite.

## Docling

```bash
python -m pip install 'docling>=2,<3'
python CODE/run.py convert-docling DATA/raw/workflow-40.pdf DATA/processed/workflow-40-docling.md
```

This produces a standalone Markdown conversion. It is **not** silently substituted for the page-preserving native parser. Layout models may require a download. The package's report discusses Docling as related work and an extension path, not as an evaluated method.

LlamaCloud integration and pretrained dense semantic retrieval are not implemented in this package. Do not claim the classroom's suggested tool list was fully used.
