# DocWeave demo speaker notes

Suggested speaking time: 720 seconds (12 minutes), including the live/screenshot demonstration. Adjust pacing after rehearsal.

## Slide 1 - 35 seconds

Introduce DocWeave and the actual team. This package is an AI-assisted generated reference implementation. The displayed results were measured on fictional, reproducible workflow PDFs. Replace Group TBD and verify the entire team roster before presenting. The project demonstrates evidence-linked processing rather than unrestricted document understanding.

## Slide 2 - 60 seconds

Use the actual fixture rather than an abstract example. The service sentence identifies Cedar40 Team; a second sentence says that Cedar40 Team reports to Assurance40 Council. Define success as recovering both supporting chunks and retaining their document/page links. Explain the closed schema: arbitrary invoices or legal narratives may yield text but no recognized relationships. Tables, coreference and general legal interpretation are not evaluated.

## Slide 3 - 70 seconds

Trace PDF bytes through the implemented modules: pdf_io.py, extractors.py, store.py and retrieval.py. Native pages avoid OCR; image-only pages use one bounded Tesseract batch. Re-ingestion is transactional and idempotent for identical bytes. Every edge retains its quote and page. Optional adapters are implemented code, not tested integrations; do not present LlamaCloud, dense pretrained retrieval or a live LLM run as completed work.

## Slide 4 - 65 seconds

The neural model is trained from scratch, not an LLM or pretrained transformer. Explain masking of entity identities and the nine labels, including NO_RELATION. Use the training split only for learning and the development split for checkpoint choice. The earliest best development checkpoint is epoch 5. The handcrafted question planner is an important limitation: the graph ranking bonus is evidence-path membership, not a learned reranker or general reasoning engine.

## Slide 5 - 60 seconds

State the exact counts and synthetic origin. Each native PDF has eight positive relations and two non-assertive statements. Splits are 300/90/90 statements with disjoint entities. Gold labels are written independently of parsing, but both labels and documents share the same fixture design, so annotation independence is limited. Four scan pages derive from test documents and are correlated smoke tests, not a real-world OCR benchmark.

## Slide 6 - 90 seconds

Explain the ablation: same chunks and graph, different ranking score; both modes calculate a diagnostic graph trace, so this is not a graph-free latency comparison. Emphasize complete evidence coverage for two-hop questions rather than first-relevant-hit metrics alone. Bootstrap confidence intervals resample documents, not individual correlated question variants. Unanswerable examples are all annual-budget questions; their perfect abstention score does not establish general out-of-domain safety. OCR evaluates four actual scans in one batch.

## Slide 7 - 85 seconds

Report the measured advantage without hiding the artificial setting. Standard test macro F1 is 1.000 for both learned classifiers, but stress-test macro F1 is 0.833 for logistic and 0.708 for BiLSTM. The neural model mislabels oversees as alerts and secures communications as management in repeated templates. Graph Recall@5 is 1.000 versus 0.741, with lexical document-bootstrap interval approximately 0.667 to 0.806. Two-hop complete@5 is zero for lexical mode and one for graph mode on eighteen narrow-schema questions. This is a designed proof of integration, not state-of-the-art performance.

## Slide 8 - 85 seconds

Switch to the live local application or use this screenshot as the allowed fallback. Open workflow-40.pdf. Show the original page and extracted text side by side, then the eight relationship records. Change the page selector on a multi-page upload if available. Explain the distinction between a PDF/OCR error and a relation-classifier error. The system can extract text from unsupported documents without inventing relationships. The screenshot was captured from the real app through a local API bridge because direct browser networking was restricted in the build environment.

## Slide 9 - 100 seconds

Focus the graph on Atlas40 Service and click MANAGED_BY. Show the source quote and the note that its model score is not calibrated. Ask the council question and trace Service to Team to Council. Click both citations. Then ask the annual-budget question to demonstrate abstention. Explain that graph visualizations and exact quotes do not guarantee predicate correctness; a mislabeled relation can still point to a real sentence. The current question parser is handcrafted and its behavior on unfamiliar query language remains a limitation.

## Slide 10 - 70 seconds

State actual ownership only after the team has verified it. The provided package is not evidence that any member previously implemented its modules. Assign real presenters and responsibilities, record completed contributions with files or commits, and review the course AI-use policy. A GitHub remote was not available during the artifact build. Publish the repository, verify instructor access, insert its real URL in PROJECT_METADATA.json and regenerate this slide. The final report is due December 9, 2026 at the time shown in Canvas; one person submits for the group.
