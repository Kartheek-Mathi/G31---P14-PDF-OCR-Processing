#!/usr/bin/env bash
# Reproduction deliberately refreshes synthetic fixtures, trained models and metrics.
# It does not remove user uploads or reseed the interactive application database.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
command -v tesseract >/dev/null || { echo 'Install Tesseract English OCR first.' >&2; exit 1; }
python CODE/tools/generate_dataset.py
python CODE/tools/train_models.py
python CODE/tools/evaluate.py
python -m pytest -q --junitxml=EVALUATIONS/results/tests.xml | tee EVALUATIONS/results/tests.log
python CODE/tools/build_figures.py
printf '\nExperiments refreshed. Review result changes before rebuilding the report and demo.\n'
