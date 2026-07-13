#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/check_frontend_only_redesign.sh [--working-tree | --staged | --last-commit | --range <revset>]

Modes:
  --working-tree  Check tracked and untracked local changes. Default.
  --staged        Check staged changes only.
  --last-commit   Check files changed in HEAD.
  --range REVSET  Check files changed in a git diff range.

Exit codes:
  0 = only frontend-safe files detected
  1 = backend/risky files detected
  2 = invalid usage
EOF
}

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

mode="${1:---working-tree}"
range_arg=""

case "$mode" in
  --working-tree)
    ;;
  --staged)
    ;;
  --last-commit)
    ;;
  --range)
    if [[ $# -lt 2 ]]; then
      usage
      exit 2
    fi
    range_arg="$2"
    ;;
  --help|-h)
    usage
    exit 0
    ;;
  *)
    usage
    exit 2
    ;;
esac

read_changes_working_tree() {
  {
    git diff --name-only --diff-filter=ACMRD HEAD
    git ls-files --others --exclude-standard
  } | sort -u
}

read_changes_staged() {
  git diff --cached --name-only --diff-filter=ACMR
}

read_changes_last_commit() {
  git diff-tree --no-commit-id --name-only -r HEAD
}

read_changes_range() {
  git diff --name-only "$range_arg"
}

load_changed_files() {
  local line
  changed_files=()
  while IFS= read -r line; do
    changed_files+=("$line")
  done
}

case "$mode" in
  --working-tree)
    load_changed_files < <(read_changes_working_tree)
    ;;
  --staged)
    load_changed_files < <(read_changes_staged)
    ;;
  --last-commit)
    load_changed_files < <(read_changes_last_commit)
    ;;
  --range)
    load_changed_files < <(read_changes_range)
    ;;
esac

if [[ ${#changed_files[@]} -eq 0 ]]; then
  echo "No files to check."
  exit 0
fi

is_allowed_path() {
  local path="$1"
  case "$path" in
    nexalix_app/templates/*|\
    nexalix_app/static/css/*|\
    nexalix_app/static/js/*|\
    nexalix_app/static/images/*|\
    nexalix_app/static/fonts/*|\
    FRONTEND_ONLY_REDESIGN_POLICY.md|\
    scripts/check_frontend_only_redesign.sh)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

safe_files=()
risky_files=()

for file in "${changed_files[@]}"; do
  [[ -z "$file" ]] && continue
  if is_allowed_path "$file"; then
    safe_files+=("$file")
  else
    risky_files+=("$file")
  fi
done

echo "Frontend-only redesign audit"
echo "Repository: $repo_root"
echo "Mode: $mode"
echo

if [[ ${#safe_files[@]} -gt 0 ]]; then
  echo "Safe frontend paths:"
  printf '  - %s\n' "${safe_files[@]}"
  echo
fi

if [[ ${#risky_files[@]} -gt 0 ]]; then
  echo "Risky backend or deployment paths detected:"
  printf '  - %s\n' "${risky_files[@]}"
  echo
  echo "This change set is not frontend-only."
  echo "Review the files above before pushing or split frontend work into a separate commit."
  exit 1
fi

echo "Only frontend-safe redesign files were detected."
