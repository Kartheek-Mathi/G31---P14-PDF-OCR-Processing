# Demo runbook

## Before presenting

Complete `PROJECT_METADATA.json` with the real group number, full roster, verified contributions, assigned demo date and actual repository URL. Confirm the instructor can open the repository and the submission PDF. Review the course's AI-use policy. Rebuild and run `validate_submission.py`; its current metadata failures are intentional and must not be hidden.

Activate the environment, run `python CODE/run.py seed`, then `python CODE/run.py serve`. Open `http://127.0.0.1:8000` in an ordinary browser on the presenting machine. Leave the server running for the presentation. The recorded screenshots used an API bridge because the build browser restricted navigation; normal browser access is still a required local rehearsal check.

The deck's notes total 12 minutes. Rehearse transitions; do not spend the demo reading the architecture diagram. Screenshots are a permitted fallback according to the supplied announcement.

## Concrete demonstration

1. **Overview:** establish the seeded state: 48 fictional PDFs, 384 relationships and 432 nodes. These counts change if other documents are uploaded.
2. **Documents:** select `workflow-40.pdf`. Compare the original page with extracted text and inspect its eight affirmative relationships. Point out the two negative/tentative statements that were not stored as positive facts.
3. **Knowledge graph:** focus `Atlas40 Service`. Select the management edge and read its source quote. Drag a node; open the source page.
4. **Ask & retrieve:** enter `Which council supervises the team managing Atlas40 Service?`. The graph answer is `Assurance40 Council`. Trace `MANAGED_BY` to `Cedar40 Team`, then `REPORTS_TO` to the council. Show both source statements.
5. **Failure behavior:** ask `What is the annual budget of Atlas40 Service?`. Show explicit abstention. Explain that this narrow unknown-question family does not establish universal safety.
6. **Evaluation:** point out logistic regression's better unseen-phrase F1 and the tiny four-page OCR sample. Do not replace these measured findings with assumed improvements.

## Questions to be ready for

**Why a synthetic benchmark?** No real team corpus or authorization was supplied. The generated corpus provides transparent, reproducible integration tests without confidential content, but is not sufficient for estimating real-world accuracy.

**Why perfect graph scores?** The schema, query planner and fixture families are aligned by design. Entities are held out, but the language space remains narrow. New documents and independently authored questions are the next meaningful test.

**Is the neural model an LLM?** No. It is a task-trained BiLSTM with 21,705 parameters. A schema-validated local Ollama adapter exists but has not been live-evaluated.

**Does the graph prove the answer?** It shows the system's evidence chain. A wrongly labeled edge can have a real source quote, so semantic review is still needed.

**What did each member do?** Answer only with verified contributions. The generated package cannot establish prior personal work. Record actual review, implementation changes, experiments and presentation duties.
