"""Heuristic circuit family classifier (host-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from platform_core.contracts import DesignSnapshot
from reasoning.family_registry import CircuitFamily, load_families
from utils.config import AppConfig, load_config

ConfidenceLevel = Literal["high", "medium", "low"]
CLASSIFIABLE_STATUSES = frozenset({"complete", "learned"})


@dataclass(frozen=True)
class FamilyAlternative:
    family_id: str
    confidence: ConfidenceLevel


@dataclass(frozen=True)
class FamilyClassification:
    family_id: str
    family_label: str
    confidence: ConfidenceLevel
    alternatives: list[FamilyAlternative] = field(default_factory=list)
    recognition_basis: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "family_label": self.family_label,
            "confidence": self.confidence,
            "alternatives": [
                {"family_id": alt.family_id, "confidence": alt.confidence}
                for alt in self.alternatives
            ],
            "recognition_basis": list(self.recognition_basis),
        }


def _collect_net_names(snapshot_data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    connectivity = snapshot_data.get("schematic_connectivity")
    if isinstance(connectivity, dict):
        unique = connectivity.get("unique_net_names") or []
        names.extend(str(n) for n in unique)
        for net in connectivity.get("nets") or []:
            if isinstance(net, dict) and net.get("name"):
                names.append(str(net["name"]))
    netlist = snapshot_data.get("netlist_summary")
    if isinstance(netlist, dict):
        for net in netlist.get("nets") or []:
            if isinstance(net, dict) and net.get("name"):
                names.append(str(net["name"]))
    return names


def _score_family(
    family: CircuitFamily,
    snapshot_data: dict[str, Any],
) -> tuple[int, list[str]]:
    rules = family.recognition
    if rules is None:
        return 0, []

    score = 0
    basis: list[str] = []
    symbols = snapshot_data.get("symbols") or []
    for sym in symbols:
        if not isinstance(sym, dict):
            continue
        lib_id = str(sym.get("lib_id") or "")
        for pattern in rules.symbol_lib_patterns:
            if lib_id.startswith(pattern):
                score += 1
                tag = f"symbol:{pattern.rstrip('_')}"
                if tag not in basis:
                    basis.append(tag)

    net_names = _collect_net_names(snapshot_data)
    net_blob = " ".join(net_names).lower()
    for keyword in rules.net_keywords:
        if keyword.lower() in net_blob:
            score += 1
            tag = f"net:{keyword}"
            if tag not in basis:
                basis.append(tag)

    return score, basis


def _confidence_for_score(score: int, min_score: int) -> ConfidenceLevel:
    if score >= min_score + 2:
        return "high"
    if score >= min_score:
        return "medium"
    return "low"


def _hint_matches_family(user_hint: str, family: CircuitFamily) -> bool:
    hint = user_hint.strip().lower()
    if not hint:
        return False
    candidates = {
        family.family_id.lower(),
        family.label.lower(),
        family.directory.lower().replace("_", " "),
    }
    return any(hint in c or c in hint for c in candidates)


def _classifiable_families(config: AppConfig | None = None) -> list[CircuitFamily]:
    cfg = config or load_config()
    return [
        family
        for family in load_families(library_path=cfg.artifact_library_path, config=cfg)
        if family.status in CLASSIFIABLE_STATUSES
    ]


def _generic_family(config: AppConfig | None = None) -> CircuitFamily | None:
    cfg = config or load_config()
    try:
        from reasoning.family_registry import get_family

        return get_family(
            "generic",
            library_path=cfg.artifact_library_path,
            config=cfg,
        )
    except KeyError:
        return None


def classify_circuit_family(
    snapshot: DesignSnapshot,
    *,
    user_hint: str | None = None,
    ekm_family_id: str | None = None,
    library_path: Path | None = None,
    config: AppConfig | None = None,
) -> FamilyClassification:
    """Classify circuit family from a design snapshot using manifest heuristics."""
    cfg = config or load_config()
    lib = library_path or cfg.artifact_library_path
    snapshot_data = snapshot.to_dict(include_image_bytes=False)
    classifiable = _classifiable_families(cfg)

    if not classifiable:
        generic = _generic_family(cfg)
        if generic is None:
            raise ValueError("No classifiable circuit families in manifest")
        return FamilyClassification(
            family_id=generic.family_id,
            family_label=generic.label,
            confidence="low",
            recognition_basis=["fallback_generic"],
        )

    scored: list[tuple[CircuitFamily, int, list[str]]] = []
    for family in classifiable:
        if family.family_id == "generic":
            continue
        score, basis = _score_family(family, snapshot_data)
        scored.append((family, score, basis))

    scored.sort(key=lambda item: item[1], reverse=True)
    best_family, best_score, best_basis = scored[0] if scored else (classifiable[0], 0, [])
    min_score = (best_family.recognition.min_score if best_family.recognition else 1)

    if user_hint:
        for family in classifiable:
            if _hint_matches_family(user_hint, family):
                hint_basis = list(best_basis)
                if "user_hint" not in hint_basis:
                    hint_basis.append("user_hint")
                return FamilyClassification(
                    family_id=family.family_id,
                    family_label=family.label,
                    confidence="high",
                    alternatives=_alternatives(scored, family.family_id),
                    recognition_basis=hint_basis,
                )

    if ekm_family_id:
        for family in classifiable:
            if family.family_id == ekm_family_id:
                ekm_basis = list(best_basis)
                if "ekm_prior" not in ekm_basis:
                    ekm_basis.append("ekm_prior")
                confidence: ConfidenceLevel = "medium"
                if best_family.family_id == family.family_id and best_score >= min_score:
                    confidence = _confidence_for_score(best_score, min_score)
                return FamilyClassification(
                    family_id=family.family_id,
                    family_label=family.label,
                    confidence=confidence,
                    alternatives=_alternatives(scored, family.family_id),
                    recognition_basis=ekm_basis,
                )

    if best_score < min_score:
        generic = _generic_family(cfg)
        if generic is not None:
            return FamilyClassification(
                family_id=generic.family_id,
                family_label=generic.label,
                confidence="low",
                alternatives=_alternatives(scored, generic.family_id),
                recognition_basis=["low_recognition_score", *best_basis],
            )

    confidence = _confidence_for_score(best_score, min_score)
    return FamilyClassification(
        family_id=best_family.family_id,
        family_label=best_family.label,
        confidence=confidence,
        alternatives=_alternatives(scored, best_family.family_id),
        recognition_basis=best_basis,
    )


def _alternatives(
    scored: list[tuple[CircuitFamily, int, list[str]]],
    selected_id: str,
) -> list[FamilyAlternative]:
    alts: list[FamilyAlternative] = []
    for family, score, _basis in scored:
        if family.family_id == selected_id or score <= 0:
            continue
        min_score = family.recognition.min_score if family.recognition else 1
        alts.append(
            FamilyAlternative(
                family_id=family.family_id,
                confidence=_confidence_for_score(score, min_score),
            )
        )
    return alts
