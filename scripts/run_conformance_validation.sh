#!/usr/bin/env bash
# Required shell compatibility: Bash 3.2 or newer.
# Keep this script compatible with the default Bash shipped by macOS.
#
# Runs Framework Advisor conformance analysis against an adopting project and
# writes a timestamped report under <project-root>/reports/conformance/.
#
# Usage:
#   ./scripts/run_conformance_validation.sh "/path/to/adopting project root"

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
analyzer="$script_dir/analyze_project_structure.sh"

usage() {
    echo "Usage: $(basename "$0") \"/path/to/adopting project root\"" >&2
    exit 1
}

require_file() {
    required_file="$1"
    description="$2"

    if [[ ! -f "$required_file" ]]; then
        echo "Required $description not found: $required_file" >&2
        exit 1
    fi
}

extract_score() {
    label="$1"
    report="$2"

    sed -n "s/^${label}: \\([0-9][0-9]*%\\)$/\\1/p" "$report" | tail -n 1
}

print_recommendations() {
    report="$1"
    recommendations="$(
        awk '
            /^Recommendations$/ {
                in_recommendations = 1
                next
            }
            in_recommendations && /^- / {
                print
                found = 1
                next
            }
            in_recommendations && found && $0 !~ /^- / {
                exit
            }
        ' "$report"
    )"

    if [[ -n "$recommendations" ]]; then
        printf '%s\n' "$recommendations"
    else
        echo "- No recommendations reported."
    fi
}

print_summary() {
    report="$1"
    target_root="$2"
    overall="$(extract_score "Overall compliance" "$report")"
    structure="$(extract_score "Structure score" "$report")"
    ai="$(extract_score "AI score" "$report")"
    navigation="$(extract_score "Navigation score" "$report")"
    governance="$(extract_score "Governance score" "$report")"

    echo
    echo "============================================================"
    echo "Conformance validation completed successfully."
    echo
    echo "Report:"
    echo "${report#$target_root/}"
    echo
    echo "Compliance scores:"
    echo "- Overall: ${overall:-Not reported}"
    echo "- Structure: ${structure:-Not reported}"
    echo "- AI: ${ai:-Not reported}"
    echo "- Navigation: ${navigation:-Not reported}"
    echo "- Governance: ${governance:-Not reported}"
    echo
    echo "Next recommended actions:"
    print_recommendations "$report"
    echo "============================================================"
}

if [[ $# -ne 1 ]]; then
    echo "Error: exactly one project root path is required." >&2
    usage
fi

target_root="${1%/}"
if [[ ! -d "$target_root" ]]; then
    echo "Error: project root does not exist or is not a directory: $target_root" >&2
    exit 1
fi

target_root="$(cd "$target_root" && pwd)"

require_file "$analyzer" "Framework Advisor"

report_dir="$target_root/reports/conformance"
mkdir -p "$report_dir"

timestamp="$(date '+%Y%m%d-%H%M%S')"
report_path="$report_dir/framework-advisor-$timestamp.txt"

run_conformance_validation() {
    echo "Engineering Documentation Framework Adoption Conformance Validation"
    echo "==================================================================="
    echo
    echo "Project root: $target_root"
    echo "Started: $(date '+%Y-%m-%d %H:%M:%S %z')"

    echo
    echo "Framework Advisor conformance analysis"
    echo "--------------------------------------"
    /bin/bash "$analyzer" "$target_root"

    echo
    echo "Validation completed: $(date '+%Y-%m-%d %H:%M:%S %z')"
}

if run_conformance_validation 2>&1 | tee "$report_path"; then
    print_summary "$report_path" "$target_root" | tee -a "$report_path"
else
    validation_status=$?
    echo
    echo "Conformance validation failed." | tee -a "$report_path" >&2
    echo "Review the captured report:" | tee -a "$report_path" >&2
    echo "${report_path#$target_root/}" | tee -a "$report_path" >&2
    exit "$validation_status"
fi
