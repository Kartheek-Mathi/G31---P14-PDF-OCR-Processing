# Source provenance

## Course-provided sources

Hasan Davulcu, *CSE 573 Semantic Web Mining: Group Projects*, Fall 2026, uploaded lecture deck. P14 describes PDF/OCR-to-graph workflows, relationship-aware retrieval, subject-predicate-object extraction, entity/link mapping and interactive graph views. The proposal guidance also requests classical baselines alongside AI/deep-learning methods. The software-use slide asks teams to identify their own work and reused components. The private course deck is not redistributed.

The user's pasted **Final Project Report** announcement supplies the 5-10-page limit, required sections and point weights, December 9, 2026 deadline, and `Group#-Project#-F26-Final Project Report.PDF` pattern. The pasted **Group Project DEMO** announcement supplies 10-slide/12-minute guidance, topic weights, GitHub layout, the last-slide repository link and the `FA26` demo filename. These assignment-specific announcements take precedence in this package over the earlier slide's conflicting length/time guidance. The actual group number and team roster were not supplied.

## Public primary technical sources checked during preparation

- IEEE official conference template: https://www.overleaf.com/latex/templates/ieee-conference-template-example/nsncsyjfmpxy
- Auer et al., *Docling Technical Report*, arXiv:2408.09869, 2024: https://arxiv.org/abs/2408.09869
- Reimers and Gurevych, *Sentence-BERT*, EMNLP 2019: https://arxiv.org/abs/1908.10084
- Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*, arXiv:2404.16130, v2, 2025: https://arxiv.org/abs/2404.16130
- scikit-learn TF-IDF API: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
- scikit-learn logistic regression API: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- pypdf extraction documentation: https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md
- Tesseract CLI: https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html
- PyTorch LSTM API: https://docs.pytorch.org/docs/stable/generated/torch.nn.LSTM.html
- Ollama structured outputs: https://docs.ollama.com/capabilities/structured-outputs
- Neo4j parameterized queries: https://neo4j.com/docs/python-manual/current/query-simple/
- Docling converter API: https://docling-project.github.io/docling/reference/document_converter/

Public sources establish tool behavior and related-work context, not this project's empirical results. All empirical numbers come from locally executed scripts in `EVALUATIONS/results/`. No numbers from external papers are copied into this project's comparison tables.

## Repository publication and CI

GitHub CLI `gh repo create` documentation: https://cli.github.com/manual/gh_repo_create . The helper uses the documented local-source, visibility, remote and push flags. Actions implementation references: https://github.com/actions/checkout and https://github.com/actions/setup-python . The included CI workflow has not been run on a remote runner.
