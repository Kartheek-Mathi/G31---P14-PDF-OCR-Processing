#!/usr/bin/env bash
# Create a new repository; never overwrite a remote or embed credentials.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
TARGET="${1:-}"
VISIBILITY="${2:---private}"
if [[ ! "$TARGET" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo "Usage: bash CODE/tools/publish_github.sh ACCOUNT/NEW_REPOSITORY [--private|--public]" >&2
  exit 2
fi
if [[ "$VISIBILITY" != "--private" && "$VISIBILITY" != "--public" ]]; then
  echo "Visibility must be --private or --public; private is the default." >&2; exit 2
fi
command -v git >/dev/null || { echo 'Install Git first.' >&2; exit 1; }
command -v gh >/dev/null || { echo 'Install GitHub CLI, then run gh auth login.' >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'Authenticate locally with gh auth login. Do not put tokens in project files.' >&2; exit 1; }
git config user.name >/dev/null || { echo 'Configure your real Git author name first.' >&2; exit 1; }
git config user.email >/dev/null || { echo 'Configure your Git author email first.' >&2; exit 1; }
if gh repo view "$TARGET" >/dev/null 2>&1; then
  echo 'Target repository already exists. Refusing to overwrite it. Use an unused repository name.' >&2; exit 1
fi
if [[ -d .git ]]; then
  if git remote get-url origin >/dev/null 2>&1; then
    echo 'This directory already has an origin remote. Refusing to replace it.' >&2; exit 1
  fi
  if [[ -n "$(git diff --cached --name-only)" ]]; then
    echo 'Existing staged changes found. Review and unstage them before using this publishing helper.' >&2; exit 1
  fi
else
  git init --initial-branch=main
fi
# Only the intended project deliverables are staged. Runtime uploads are ignored.
git add .gitignore .env.example .github README.md START_HERE.md LICENSE \
  THIRD_PARTY_NOTICES.md PROJECT_METADATA.json FILE_MANIFEST.json requirements.txt requirements-dev.txt \
  requirements-optional.txt compose.yaml pytest.ini CODE DATA EVALUATIONS SUBMISSION DOCS
if git diff --cached --name-only | grep -E '(^|/)(\.env|id_rsa|id_ed25519)$|^DATA/runtime/' >/dev/null; then
  echo 'Potential secret/runtime content detected in the staged set. Review before publishing.' >&2; exit 1
fi
if ! git diff --cached --quiet; then
  git commit -m 'Add AI-assisted DocWeave prototype, synthetic benchmark and submission artifacts'
fi
gh repo create "$TARGET" "$VISIBILITY" --source . --remote origin --push
URL="https://github.com/$TARGET"
printf '\nPublished: %s\n' "$URL"
printf '%s\n' 'Now set repository_url in PROJECT_METADATA.json, verify instructor access, complete team metadata, rebuild both deliverables, validate them, then commit and push the updated files.'
