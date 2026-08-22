"""Confidence-gated promotion of AERF stage outputs to user library circuit families."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from platform_core.contracts import DesignSnapshot
from reasoning.family_registry import DEFAULT_LEARNING_LIBRARY_SUBDIR, load_families
from reasoning.stages import get_stage
from reasoning.stage_schemas import validate_stage_envelope
from utils.config import AppConfig, LearningMinConfidence, load_config

ConfidenceLevel = Literal["high", "medium", "low"]
_CONFIDENCE_RANK: dict[str, int] = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class PromotionResult:
    promoted: bool
    family_id: str | None
    message: str
    library_path: Path | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _family_directory_name(family_id: str) -> str:
    return "_".join(part.capitalize() for part in family_id.split("_"))


def _stage_hash(envelope: dict[str, Any]) -> str:
    payload = json.dumps(envelope, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def check_promotion_gates(
    stage_outputs: list[dict[str, Any]],
    *,
    min_confidence: LearningMinConfidence = "high",
    max_open_questions: int = 50,
) -> tuple[bool, str]:
    if len(stage_outputs) < 8:
        return False, "incomplete_stages"

    min_rank = _CONFIDENCE_RANK[min_confidence]
    family_ids: set[str] = set()
    total_open = 0

    for envelope in stage_outputs:
        stage_id = envelope.get("stage_id")
        if not isinstance(stage_id, int):
            return False, "invalid_stage_id"

        confidence = envelope.get("confidence", "low")
        if not isinstance(confidence, str):
            confidence = "low"
        if _CONFIDENCE_RANK.get(confidence, 0) < min_rank:
            return False, f"stage_{stage_id}_confidence_{confidence}"

        _, err = validate_stage_envelope(envelope, expected_stage_id=stage_id)
        if err:
            return False, f"stage_{stage_id}_validation_{err}"

        if stage_id == 0:
            determinations = envelope.get("determinations")
            if isinstance(determinations, dict):
                family_id = determinations.get("family_id")
                if isinstance(family_id, str) and family_id.strip():
                    family_ids.add(family_id.strip())

        open_questions = envelope.get("open_questions") or []
        if isinstance(open_questions, list):
            total_open += len(open_questions)

    if len(family_ids) != 1:
        return False, "inconsistent_family_id"
    family_id = family_ids.pop()
    if family_id == "generic":
        return False, "generic_family_not_promoted"
    if total_open > max_open_questions:
        return False, "too_many_open_questions"

    return True, "ok"


def distill_stage_markdown(envelope: dict[str, Any]) -> str:
    stage_id = int(envelope["stage_id"])
    stage = get_stage(stage_id)
    determinations = envelope.get("determinations", {})
    lines = [
        f"# {stage.stage_id:02d} - {stage.file_title}",
        "",
        "Auto-promoted from AERF stage output (user library).",
        "",
        "## Determinations",
        "",
        json.dumps(determinations, indent=2, ensure_ascii=False),
    ]
    open_questions = envelope.get("open_questions") or []
    if open_questions:
        lines.extend(["", "## Open questions"])
        for item in open_questions:
            lines.append(f"- {item}")
    unknowns = envelope.get("unknowns") or []
    if unknowns:
        lines.extend(["", "## Unknowns"])
        for item in unknowns:
            lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def derive_recognition_from_snapshot(snapshot: DesignSnapshot) -> dict[str, Any]:
    data = snapshot.to_dict(include_image_bytes=False)
    patterns: set[str] = set()
    for sym in data.get("symbols") or []:
        if not isinstance(sym, dict):
            continue
        lib_id = str(sym.get("lib_id") or "")
        if ":" in lib_id:
            prefix = lib_id.split(":")[0] + ":"
            if len(prefix) > 2:
                patterns.add(prefix)
    net_names = []
    connectivity = data.get("schematic_connectivity")
    if isinstance(connectivity, dict):
        net_names.extend(str(n) for n in connectivity.get("unique_net_names") or [])
    keywords: set[str] = set()
    blob = " ".join(net_names).lower()
    for token in re.findall(r"[a-z][a-z0-9_]{2,}", blob):
        if token in ("net", "pad", "gnd", "vcc"):
            continue
        keywords.add(token)
    return {
        "symbol_lib_patterns": sorted(patterns)[:8],
        "net_keywords": sorted(keywords)[:12],
        "min_score": 1,
    }


def _load_provenance(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("promotions"), list):
        return data["promotions"]
    return []


def promote_family_to_library(
    stage_outputs: list[dict[str, Any]],
    snapshot: DesignSnapshot,
    project_path: Path | str,
    *,
    config: AppConfig | None = None,
    min_confidence: LearningMinConfidence | None = None,
) -> PromotionResult:
    cfg = config or load_config()
    min_conf = min_confidence or cfg.learning_min_confidence
    ok, reason = check_promotion_gates(stage_outputs, min_confidence=min_conf)
    if not ok:
        return PromotionResult(promoted=False, family_id=None, message=reason)

    stage0 = next(s for s in stage_outputs if s.get("stage_id") == 0)
    determinations = stage0.get("determinations", {})
    family_id = str(determinations.get("family_id", "")).strip()
    family_label = str(determinations.get("family_label") or family_id).strip()

    lib_root = Path(cfg.artifact_library_path).expanduser() / cfg.learning_library_subdir
    lib_root.mkdir(parents=True, exist_ok=True)
    manifest_path = lib_root / "families.json"
    families_data: dict[str, Any] = {"families": []}
    if manifest_path.is_file():
        families_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    directory = _family_directory_name(family_id)
    family_dir = lib_root / directory
    family_dir.mkdir(parents=True, exist_ok=True)

    for envelope in sorted(stage_outputs, key=lambda s: s.get("stage_id", 0)):
        stage_id = envelope.get("stage_id")
        if not isinstance(stage_id, int):
            continue
        stage = get_stage(stage_id)
        (family_dir / stage.filename).write_text(
            distill_stage_markdown(envelope),
            encoding="utf-8",
        )

    recognition = derive_recognition_from_snapshot(snapshot)
    families = families_data.get("families") or []
    updated = False
    for entry in families:
        if entry.get("family_id") == family_id:
            entry["directory"] = directory
            entry["label"] = family_label
            entry["status"] = "learned"
            entry["recognition"] = recognition
            updated = True
            break
    if not updated:
        families.append(
            {
                "family_id": family_id,
                "directory": directory,
                "label": family_label,
                "status": "learned",
                "recognition": recognition,
            }
        )
    families_data["families"] = families
    manifest_path.write_text(json.dumps(families_data, indent=2) + "\n", encoding="utf-8")

    provenance_path = family_dir / "provenance.json"
    promotions = _load_provenance(provenance_path)
    promotions.append(
        {
            "promoted_at": _utc_now_iso(),
            "project_path": str(Path(project_path).expanduser().resolve()),
            "family_id": family_id,
            "stage_hashes": [_stage_hash(s) for s in stage_outputs],
            "gate_result": reason,
            "min_confidence": min_conf,
        }
    )
    provenance_path.write_text(
        json.dumps({"promotions": promotions}, indent=2) + "\n",
        encoding="utf-8",
    )

    return PromotionResult(
        promoted=True,
        family_id=family_id,
        message=f"promoted_to_library:{family_id}",
        library_path=lib_root,
    )


def try_auto_promote(
    stage_outputs: list[dict[str, Any]],
    snapshot: DesignSnapshot,
    project_path: Path | str,
    *,
    config: AppConfig | None = None,
) -> PromotionResult:
    cfg = config or load_config()
    if not cfg.learning_auto_promote:
        return PromotionResult(promoted=False, family_id=None, message="auto_promote_disabled")
    if not stage_outputs:
        return PromotionResult(promoted=False, family_id=None, message="no_stages")
    return promote_family_to_library(
        stage_outputs,
        snapshot,
        project_path,
        config=cfg,
    )
