# Evaluation evidence

The checked-in outputs are from actual execution of the included implementation, not illustrative or expected scores. The corpus and queries are synthetic and share a deliberately narrow workflow schema. Read `DATA/README.md` and the report's limitations before interpreting any perfect scores.

## Result files

`results/metrics.json` is the main metric record. `classification_predictions.jsonl` contains per-statement class predictions; `triple_predictions.jsonl` contains graph-extraction outcomes; `retrieval_per_query.csv` and `answer_predictions.jsonl` preserve query-level evidence; `ocr_predictions.jsonl` retains reference and recognized text. Inspect the directory for exact emitted filenames. Training history, confusion matrices, environment information, build logs and automated-test XML are retained alongside these outputs.

`figures/` contains generated charts, a vector architecture diagram and crops of actual screenshots. `screenshots/` contains six full running-interface screenshots. `results/browser_smoke.json` records seven actual smoke checks, including its local API bridge transport limitation. Browser screenshots are not a participant usability study. `results/submission_validation.json` is expected to fail while group metadata remains unverified; that is an administrative gate, not a code-test failure.

## Protocol

The ordinary relation test uses 90 statements (72 affirmative facts and 18 negative/tentative statements) from nine held-out entity sets. The independent phrasing slice contains 72 positive statements; it uses one unseen template per predicate, not 72 independent linguistic patterns. The three extraction systems share the same entity grammar. The classifier vocabulary is fitted only on training data; the neural checkpoint is selected on development macro F1, not on test performance.

Retrieval uses all 48 documents as the search corpus and 54 answerable test queries, grouped into literal, paraphrase and two-hop families. There are nine additional annual-budget queries for abstention. Both retrieval modes use the same neural graph. Lexical mode ranks by TF-IDF; graph mode adds a complete-path evidence bonus. Both modes calculate a diagnostic trace, so latency is not a clean isolation of graph traversal cost. Recall measures all required support chunks, not just whether any source was retrieved. A document-level bootstrap with 2,000 resamples accounts partially for correlated queries; it cannot establish real-domain external validity.

Four image-only PDFs are derived from held-out native documents. Two are clean renders and two have mild synthetic degradation. All four OCR calls were submitted in one Tesseract subprocess batch. CER and WER are micro-averaged against full page references. This is a small extraction smoke test, not an OCR robustness benchmark.

## Re-run

Install `requirements-dev.txt` and system Tesseract, then run `bash CODE/tools/reproduce.sh` from the repository. This regenerates fixture data and result artifacts, not user uploads. Times vary by machine. Native Python/PyTorch package versions and hardware affect exact timing and potentially training reproducibility. Only the recorded environment and one random seed were exercised here.

The authored report narrative and selected demo statements describe the delivered run. Build tools refresh charts and selected numeric fields but do not automatically rewrite scientific interpretation. Compare every claim to the new metrics before submitting after any model/data change.
