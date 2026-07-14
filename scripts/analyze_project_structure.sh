#!/usr/bin/env bash
# Engineering Documentation Framework Framework Advisor.
# Read-only analysis of structure, navigation, links, and governance.
# Compatible with the default macOS Bash 3.2 and newer Bash versions.
#
# Usage:
# ./scripts/analyze_project_structure.sh "/path/to/project root"

set -euo pipefail

STAGE1_RULESET_VERSION="2026-07-10-stage1"

if [[ $# -ne 1 ]]; then
  echo "Error: project root path is required." >&2
  echo "Usage: $(basename "$0") \"/path/to/project root\"" >&2
  exit 1
fi

PROJECT_ROOT="${1%/}"
if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo "Error: project root does not exist or is not a directory: $PROJECT_ROOT" >&2
  exit 1
fi

required_dirs=(
  docs docs/Architecture docs/Architecture/ADRs docs/AI docs/Developer_Handbook docs/Development
  docs/Governance docs/Specifications docs/API docs/Database docs/Deployment
  docs/User_Guides docs/Reference docs/Templates tasks archive scripts
)

recommended_root_files=(
  README.md PROJECT_INDEX.md PROJECT_CHARTER.md ARCHITECTURE_DECISIONS.md
  CHANGELOG.md
)

is_edf_repository=false
if [[ -f "$PROJECT_ROOT/docs/Governance/EDF_Governance.md" &&
      -f "$PROJECT_ROOT/docs/Architecture/Documentation_Information_Architecture.md" ]]; then
  is_edf_repository=true
else
  recommended_root_files+=(ENGINEERING_DOCUMENTATION_FRAMEWORK.md)
fi

ai_files=(
  docs/AI/README.md docs/AI/AI_Philosophy.md docs/AI/AI_Roles.md
  docs/AI/AI_Decision_Matrix.md docs/AI/Cost_Optimization.md
  docs/AI/Prompting_Guide.md docs/AI/Context_Checklist.md
  docs/AI/Verification.md docs/AI/Security.md docs/AI/Governance.md
)

governance_files=(
  docs/Governance/README.md docs/Governance/Governance_Overview.md
  docs/Governance/EDF_Governance.md
  docs/Governance/Document_Metadata_Standard.md
  docs/Governance/Document_Lifecycle.md
  docs/Governance/Ownership_and_Review.md
  docs/Governance/Change_Management.md
  docs/Governance/Analyzer_Compliance.md
  docs/Governance/Governance_Checklist.md
)

missing_dirs=()
missing_root_files=()
missing_ai_files=()
missing_governance_files=()
warnings=()
recommendations=()
markdown_outside=()
broken_links=()
orphan_docs=()
navigation_issues=()
metadata_issues=()
review_issues=()

for dir in "${required_dirs[@]}"; do
  [[ -d "$PROJECT_ROOT/$dir" ]] || missing_dirs+=("$dir")
done

for file in "${recommended_root_files[@]}"; do
  [[ -f "$PROJECT_ROOT/$file" ]] || missing_root_files+=("$file")
done

for file in "${ai_files[@]}"; do
  [[ -f "$PROJECT_ROOT/$file" ]] || missing_ai_files+=("$file")
done

for file in "${governance_files[@]}"; do
  [[ -f "$PROJECT_ROOT/$file" ]] || missing_governance_files+=("$file")
done

[[ ! -f "$PROJECT_ROOT/AI_WORKFLOW.md" ]] || warnings+=("Retired root document AI_WORKFLOW.md still exists.")
[[ ! -d "$PROJECT_ROOT/documents" ]] || warnings+=("Existing documents/ folder found; leave it untouched unless migration is intentional.")

all_md=()
while IFS= read -r -d '' file; do
  all_md+=("$file")
  rel="${file#"$PROJECT_ROOT"/}"
  case "$rel" in
    docs/*|archive/*|tasks/*|scripts/README.md|README.md|PROJECT_INDEX.md|PROJECT_CHARTER.md|ARCHITECTURE_DECISIONS.md|CHANGELOG.md|ENGINEERING_DOCUMENTATION_FRAMEWORK.md) ;;
    *) markdown_outside+=("$rel") ;;
  esac
done < <(find "$PROJECT_ROOT" -type f \( -iname '*.md' -o -iname '*.markdown' \) -print0)

inbound_file="$(mktemp "${TMPDIR:-/tmp}/edf-inbound.XXXXXX")"
trap 'rm -f "$inbound_file"' EXIT

for file in "${all_md[@]}"; do
  rel="${file#"$PROJECT_ROOT"/}"
  dir="$(dirname "$file")"
  content="$(cat "$file")"

  is_template_source=false
  case "$rel" in
    docs/Templates/*.md|docs/Templates/*.markdown)
      [[ "$rel" == "docs/Templates/README.md" ]] || is_template_source=true
      ;;
  esac

  while IFS= read -r target; do
    [[ -n "$target" ]] || continue
    case "$target" in
      http://*|https://*|mailto:*|\#*|url|URL|path|PATH|example|EXAMPLE|placeholder|PLACEHOLDER) continue ;;
    esac

    if [[ "$is_template_source" == true ]]; then
      continue
    fi
    path="${target%%#*}"
    [[ -n "$path" ]] || continue

    if [[ "$path" = /* ]]; then
      resolved="$path"
    else
      resolved="$dir/$path"
    fi

    normalized="$(python3 -c 'import os,sys; print(os.path.normpath(sys.argv[1]))' "$resolved" 2>/dev/null || true)"
    if [[ -z "$normalized" || ! -e "$normalized" ]]; then
      broken_links+=("$rel -> $target")
    elif [[ -f "$normalized" && "$normalized" =~ \.(md|markdown)$ ]]; then
      target_rel="${normalized#"$PROJECT_ROOT"/}"
      printf '%s\n' "$target_rel" >> "$inbound_file"
    fi
  done < <(grep -oE '\[[^]]+\]\([^)]+\)' "$file" | sed -E 's/^[^(]*\(([^)]+)\)$/\1/' || true)

  if [[ "$rel" == docs/* && "$is_template_source" == false ]]; then
    if ! grep -q '\[Home\](' "$file" || ! grep -q '\[Project Index\](' "$file"; then
      navigation_issues+=("$rel: missing breadcrumb navigation.")
    fi

    if [[ "$rel" != */README.md ]] && ! grep -q 'README\.md)' "$file"; then
      navigation_issues+=("$rel: missing parent domain README link.")
    fi
  fi

  if grep -q '^> \*\*Status:\*\*' "$file"; then
    status="$(sed -nE 's/^> \*\*Status:\*\*[[:space:]]*(.+)$/\1/p' "$file" | head -1)"
    owner="$(sed -nE 's/^> \*\*Owner:\*\*[[:space:]]*(.+)$/\1/p' "$file" | head -1)"
    applies="$(sed -nE 's/^> \*\*Applies To:\*\*[[:space:]]*(.+)$/\1/p' "$file" | head -1)"
    reviewed="$(sed -nE 's/^> \*\*Last Reviewed:\*\*[[:space:]]*([0-9]{4}-[0-9]{2}-[0-9]{2}).*$/\1/p' "$file" | head -1)"
    frequency="$(sed -nE 's/^> \*\*Review Frequency:\*\*[[:space:]]*(.+)$/\1/p' "$file" | head -1)"

    case "$status" in
      Draft|"In Review"|Approved|Maintained|Deprecated|Archived) ;;
      *) metadata_issues+=("$rel: missing or invalid Status.") ;;
    esac

    [[ -n "$owner" ]] || metadata_issues+=("$rel: missing Owner.")
    [[ -n "$applies" ]] || metadata_issues+=("$rel: missing Applies To.")

    if [[ "$status" == Approved || "$status" == Maintained ]]; then
      [[ -n "$reviewed" ]] || metadata_issues+=("$rel: approved or maintained document is missing Last Reviewed.")
      [[ -n "$frequency" ]] || metadata_issues+=("$rel: approved or maintained document is missing Review Frequency.")
    fi

    if grep -q '^> \*\*Authoritative:\*\*[[:space:]]*Yes' "$file" &&
       [[ "$status" == Draft || "$status" == Archived ]]; then
      metadata_issues+=("$rel: authoritative document cannot be Draft or Archived.")
    fi

    if [[ "$status" == Deprecated ]] &&
       ! grep -q '^> \*\*Superseded By:\*\*' "$file" &&
       ! grep -qi 'no replacement' "$file"; then
      metadata_issues+=("$rel: deprecated document lacks replacement information.")
    fi

    if [[ -n "$reviewed" && -n "$frequency" ]]; then
      days=""
      case "$frequency" in
        Monthly) days=31 ;;
        Quarterly) days=92 ;;
        Semiannual) days=183 ;;
        Annual) days=366 ;;
      esac
      if [[ -n "$days" ]]; then
        if python3 - "$reviewed" "$days" <<'PY'
from datetime import date, datetime, timedelta
import sys
reviewed = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
days = int(sys.argv[2])
sys.exit(0 if reviewed + timedelta(days=days) < date.today() else 1)
PY
        then
          review_issues+=("$rel: review is overdue ($frequency; last reviewed $reviewed).")
        fi
      fi
    fi
  fi
done

for file in "${all_md[@]}"; do
  rel="${file#"$PROJECT_ROOT"/}"
  case "$rel" in
    README.md|PROJECT_INDEX.md|CHANGELOG.md|ARCHITECTURE_DECISIONS.md|archive/*|scripts/README.md|docs/Templates/*.md|docs/Templates/*.markdown) continue ;;
  esac
  grep -Fqx "$rel" "$inbound_file" || orphan_docs+=("$rel")
done

[[ ${#markdown_outside[@]} -eq 0 ]] || recommendations+=("Audit Markdown outside canonical locations.")
[[ ${#missing_ai_files[@]} -eq 0 ]] || recommendations+=("Complete the modular AI Engineering Handbook.")
[[ ${#missing_governance_files[@]} -eq 0 ]] || recommendations+=("Complete the Governance documentation domain.")
[[ ${#broken_links[@]} -eq 0 ]] || recommendations+=("Repair broken relative Markdown links.")
[[ ${#orphan_docs[@]} -eq 0 ]] || recommendations+=("Link orphan documents from the project hierarchy.")
[[ ${#navigation_issues[@]} -eq 0 ]] || recommendations+=("Add required breadcrumb and parent navigation.")
[[ ${#metadata_issues[@]} -eq 0 ]] || recommendations+=("Correct governance metadata and lifecycle issues.")
[[ ${#review_issues[@]} -eq 0 ]] || recommendations+=("Review overdue governed documents.")

clamp() {
  local value="$1"
  (( value < 0 )) && value=0
  (( value > 100 )) && value=100
  echo "$value"
}

structure_score="$(clamp $((100 - ${#missing_dirs[@]} * 4 - ${#missing_root_files[@]} * 3)))"
ai_score=$(( (${#ai_files[@]} - ${#missing_ai_files[@]}) * 100 / ${#ai_files[@]} ))
governance_score="$(clamp $((100 - ${#missing_governance_files[@]} * 5 - ${#metadata_issues[@]} * 3 - ${#review_issues[@]} * 2)))"
navigation_score="$(clamp $((100 - ${#broken_links[@]} * 3 - ${#orphan_docs[@]} * 2 - ${#navigation_issues[@]} * 2)))"
overall_score=$(( (structure_score + ai_score + governance_score + navigation_score) / 4 ))

print_section() {
  local title="$1"
  echo
  echo "$title"
  printf '%*s\n' "${#title}" '' | tr ' ' '-'
}

print_items() {
  local array_name="$1"

  case "$array_name" in
    missing_dirs) [[ ${#missing_dirs[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${missing_dirs[@]}" ;;
    missing_root_files) [[ ${#missing_root_files[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${missing_root_files[@]}" ;;
    missing_ai_files) [[ ${#missing_ai_files[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${missing_ai_files[@]}" ;;
    missing_governance_files) [[ ${#missing_governance_files[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${missing_governance_files[@]}" ;;
    broken_links) [[ ${#broken_links[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${broken_links[@]}" ;;
    orphan_docs) [[ ${#orphan_docs[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${orphan_docs[@]}" ;;
    navigation_issues) [[ ${#navigation_issues[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${navigation_issues[@]}" ;;
    metadata_issues) [[ ${#metadata_issues[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${metadata_issues[@]}" ;;
    review_issues) [[ ${#review_issues[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${review_issues[@]}" ;;
    markdown_outside) [[ ${#markdown_outside[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${markdown_outside[@]}" ;;
    warnings) [[ ${#warnings[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${warnings[@]}" ;;
    recommendations) [[ ${#recommendations[@]} -eq 0 ]] && echo "None." || printf -- '- %s\n' "${recommendations[@]}" ;;
    *) echo "None." ;;
  esac
}

echo "Engineering Documentation Framework Advisor"
echo "Ruleset: $STAGE1_RULESET_VERSION"
echo "==========================================="
echo
echo "Project root: $PROJECT_ROOT"
echo "Project name: $(basename "$PROJECT_ROOT")"
if [[ "$is_edf_repository" == true ]]; then
  echo "Repository mode: EDF framework repository"
else
  echo "Repository mode: EDF adopting project"
fi
echo "Overall compliance: $overall_score%"
echo "Structure score: $structure_score%"
echo "AI score: $ai_score%"
echo "Navigation score: $navigation_score%"
echo "Governance score: $governance_score%"
echo
echo "This report is read-only."
echo "No files or folders were created, modified, moved, renamed, or deleted."

for pair in \
  "Missing required directories:missing_dirs" \
  "Missing recommended root files:missing_root_files" \
  "Missing AI handbook files:missing_ai_files" \
  "Missing Governance files:missing_governance_files" \
  "Broken links:broken_links" \
  "Orphan documents:orphan_docs" \
  "Navigation issues:navigation_issues" \
  "Governance metadata and lifecycle issues:metadata_issues" \
  "Overdue reviews:review_issues" \
  "Markdown outside canonical locations:markdown_outside" \
  "Warnings:warnings" \
  "Recommendations:recommendations"
do
  title="${pair%%:*}"
  array="${pair##*:}"
  print_section "$title"
  print_items "$array"
done
echo
