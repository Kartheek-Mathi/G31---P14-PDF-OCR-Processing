# IEEE report source

Open `main.tex` as the main document in Overleaf using the standard IEEEtran conference class. Keep `team.tex`, `metrics.tex`, `references.bib` and the `assets/` directory beside it. These files are sufficient to compile the delivered report; there are no font files to install or upload.

For the local automated build, edit the repository-root `PROJECT_METADATA.json`, then run `python CODE/tools/build_report.py` from the repository. This updates team metadata, copies the figures and runs LaTeX/BibTeX. The delivered report is eight pages. Follow the assignment-specific 5-10-page limit, not the older lecture-deck limit.

The source includes explicit missing-metadata notices. Do not simply erase them: first verify the full roster, actual contributions, course-policy requirements and published repository access. A known requester name alone is not a complete group authorship record.

The narrative and several result tables describe the recorded experiment. Changing models/data requires reviewing all prose and tables; the builder refreshes selected fields but does not author new scientific conclusions automatically.
