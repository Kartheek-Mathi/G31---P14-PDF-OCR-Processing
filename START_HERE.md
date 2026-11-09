# Start here

1. Read `README.md` and run the local app with `python CODE/run.py seed` then `python CODE/run.py serve` after installing `requirements.txt`.
2. Review the PDF report and 10-slide demo in `SUBMISSION/`. Their numbers are measured on the included synthetic benchmark, not an existing team dataset.
3. Fill `PROJECT_METADATA.json`: actual group number, complete roster, true detailed contributions, presentation date and published GitHub URL. Check the course AI-use policy. No contribution history has been invented.
4. Publish using `CODE/tools/publish_github.sh` from your authenticated GitHub CLI, grant instructor access, and rebuild with `build_report.py` / `build_demo.py`.
5. Run `validate_submission.py`. It deliberately fails while required identity, repository and policy checks remain unresolved. Submit only after reviewing the actual implementation and clearing those checks.

The final report follows the 5-10-page requirement in the supplied announcement, not the older 15-20-page slide. The demo is 10 slides with a 12-minute script. One person submits each group deliverable.
