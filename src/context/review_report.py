"""Structured engineering review reports (Phase 3)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from providers.types import TokenUsage

FindingSeverity = Literal["critical", "warning", "info"]


@dataclass
class ReviewFinding:
    id: str
    severity: FindingSeverity
    category: str
    summary: str
    recommendation: str
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "references": list(self.references),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewFinding:
        refs = data.get("references")
        return cls(
            id=str(data.get("id", "")),
            severity=str(data.get("severity", "info")),  # type: ignore[arg-type]
            category=str(data.get("category", "general")),
            summary=str(data.get("summary", "")),
            recommendation=str(data.get("recommendation", "")),
            references=[str(r) for r in refs] if isinstance(refs, list) else [],
        )


@dataclass
class ReviewReport:
    audit_type: str
    project_path: str
    model: str
    findings: list[ReviewFinding] = field(default_factory=list)
    narrative: str = ""
    usage: TokenUsage = field(default_factory=TokenUsage)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_type": self.audit_type,
            "project_path": self.project_path,
            "model": self.model,
            "findings": [f.to_dict() for f in self.findings],
            "narrative": self.narrative,
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
            },
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewReport:
        findings_raw = data.get("findings")
        findings = (
            [ReviewFinding.from_dict(item) for item in findings_raw if isinstance(item, dict)]
            if isinstance(findings_raw, list)
            else []
        )
        usage_raw = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        usage = TokenUsage(
            input_tokens=int(usage_raw.get("input_tokens", 0)),
            output_tokens=int(usage_raw.get("output_tokens", 0)),
        )
        return cls(
            audit_type=str(data.get("audit_type", "")),
            project_path=str(data.get("project_path", "")),
            model=str(data.get("model", "")),
            findings=findings,
            narrative=str(data.get("narrative", "")),
            usage=usage,
            created_at=str(data.get("created_at", "")),
        )


def reviews_dir(project_path: Path | str) -> Path:
    pro = Path(project_path).expanduser().resolve()
    return pro.parent / "kicad_ai" / "reviews"


def save_review_report(report: ReviewReport) -> Path:
    directory = reviews_dir(report.project_path)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{stamp}_{report.audit_type}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def parse_findings_from_response(text: str) -> list[ReviewFinding]:
    """Extract a JSON findings array from provider narrative text."""
    block = _extract_json_block(text)
    if block is None:
        return []
    try:
        data = json.loads(block)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and isinstance(data.get("findings"), list):
        items = data["findings"]
    elif isinstance(data, list):
        items = data
    else:
        return []
    findings: list[ReviewFinding] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        if not item.get("id"):
            item["id"] = f"F{idx + 1}"
        try:
            findings.append(ReviewFinding.from_dict(item))
        except (TypeError, ValueError):
            continue
    return findings


def _extract_json_block(text: str) -> str | None:
    fenced = re.search(r"```json\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    for start in ("{", "["):
        idx = text.find(start)
        if idx >= 0:
            snippet = text[idx:]
            for end in ("}", "]"):
                last = snippet.rfind(end)
                if last > 0:
                    return snippet[: last + 1]
    return None


STRUCTURED_FINDINGS_SUFFIX = (
    "\n\nAfter your narrative, include a fenced JSON block named findings with this shape:\n"
    "```json\n"
    '{"findings": [{"id":"F1","severity":"warning","category":"netlist",'
    '"summary":"...","recommendation":"...","references":["R1"]}]}\n'
    "```"
)
