# Submission checklist

## Administrative blockers in this package

The group number, assigned demo date, complete team roster, verified individual contributions and actual GitHub URL were not supplied. They are explicitly marked, not guessed. `GroupTBD` files are review copies, not cleared final uploads. The last demo slide cannot contain a valid remote link until a repository is actually published.

Complete `PROJECT_METADATA.json`. Each member's contribution should describe work they actually performed and evidence such as files, commits, experiment logs or reviewed sections. Check the course's AI-use policy and disclose assistance as required. A generated implementation must not be described as prior original team work.

## Deliverable checks

| Requirement from the supplied announcement | Delivered evidence / action |
|---|---|
| Report PDF, 5-10 pages | Eight-page IEEE-format report; rebuild after metadata changes |
| All required report sections | Present, including results, UI and contribution section |
| Detailed individual contributions | Section exists; truthful team records still required |
| Demo approximately 10 slides / 12 minutes | 10-slide editable PPTX, PDF and 720-second speaker notes |
| Live demo or screenshots | Runnable local app and six actual screenshots |
| Repository README + CODE / DATA / EVALUATIONS | Included |
| GitHub URL on final demo slide | Placeholder until real remote is published and metadata rebuilt |
| One uploader per group | Team must choose the actual uploader |
| Final report deadline | December 9, 2026 at midnight in the announcement; confirm exact Canvas time |
| Demo deadline | Before/on the assigned group presentation date; fill metadata |

## Rebuild and validate

```bash
python CODE/tools/build_report.py
python CODE/tools/build_demo.py
python CODE/tools/validate_submission.py
```

A successful metadata validator does not independently verify contributions, policy compliance or instructor access. Those flags are truthful manual attestations. Inspect the rebuilt PDFs visually and read all result claims against the current experiment outputs. File generation does not submit anything to Canvas.

Required final names after replacing the group number:

```text
Group<NUMBER>-Project14-F26-Final Project Report.PDF
Group<NUMBER>-Project14-FA26-Group-DEMO-Presentation.PDF
```

The report naming pattern uses **F26**; the demo uses **FA26**. Do not confuse Project 14 with Group 14. Use the filenames for the actual group, not leftover GroupTBD copies.

## Repository publication

The included `publish_github.sh` creates a new private repository by default, without embedded credentials. Give the instructor access; a private repository is not automatically accessible to them. Public publication requires a separate review of permission to share all material.

After inserting the real URL and rebuilding:

```bash
git add PROJECT_METADATA.json SUBMISSION EVALUATIONS/results
# Review the staged diff before committing.
git diff --cached --stat
git commit -m "Finalize verified team metadata and submission artifacts"
git push
```

Then open the repository and download/view the files as the instructor would. Do not assume that a local build updated the remote.
