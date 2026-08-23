"""Load User Guide markdown and manifest for the in-app Help viewer."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GuideTopic:
    """One entry in the user guide table of contents."""

    topic_id: str
    title: str
    rel_path: str


@dataclass(frozen=True)
class GuideSection:
    """Grouped sidebar section in the Help viewer."""

    title: str
    topic_ids: tuple[str, ...]


@dataclass(frozen=True)
class GuideManifest:
    """Parsed ``guide_manifest.json``."""

    default_topic: str
    topics: tuple[GuideTopic, ...]
    sections: tuple[GuideSection, ...]
    tab_topics: dict[str, str]

    @property
    def topic_by_id(self) -> dict[str, GuideTopic]:
        return {topic.topic_id: topic for topic in self.topics}

    def path_for_tab(self, tab_id: str) -> str:
        return self.tab_topics.get(tab_id, self.default_topic)

    def path_for_topic(self, topic: str | None) -> str:
        if not topic:
            return self.default_topic
        if topic.endswith(".md"):
            return topic
        by_id = self.topic_by_id
        if topic in by_id:
            return by_id[topic].rel_path
        for entry in self.topics:
            if entry.rel_path == topic:
                return entry.rel_path
        if topic in self.tab_topics:
            return self.tab_topics[topic]
        return self.default_topic


def user_guides_dir() -> Path:
    """Resolve ``docs/User_Guides`` relative to the repository."""
    src_env = os.environ.get("KICAD_AI_SRC")
    if src_env:
        return Path(src_env).expanduser().resolve().parent / "docs" / "User_Guides"
    return Path(__file__).resolve().parents[2] / "docs" / "User_Guides"


def load_manifest(guides_dir: Path | None = None) -> GuideManifest:
    root = guides_dir or user_guides_dir()
    manifest_path = root / "guide_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    topics = tuple(
        GuideTopic(topic_id=str(item["id"]), title=str(item["title"]), rel_path=str(item["path"]))
        for item in data.get("topics", [])
    )
    by_id = {topic.topic_id: topic for topic in topics}
    sections: list[GuideSection] = []
    for section in data.get("sections", []):
        topic_ids = tuple(str(topic_id) for topic_id in section.get("topic_ids", []))
        if not topic_ids:
            continue
        if any(topic_id not in by_id for topic_id in topic_ids):
            continue
        sections.append(GuideSection(title=str(section["title"]), topic_ids=topic_ids))
    if not sections:
        sections = [GuideSection(title="Guides", topic_ids=tuple(topic.topic_id for topic in topics))]
    return GuideManifest(
        default_topic=str(data.get("default_topic", "README.md")),
        topics=topics,
        sections=tuple(sections),
        tab_topics={str(k): str(v) for k, v in (data.get("tab_topics") or {}).items()},
    )


def read_guide_markdown(rel_path: str, guides_dir: Path | None = None) -> str:
    root = (guides_dir or user_guides_dir()).resolve()
    target = (root / rel_path).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError(f"Guide path escapes docs root: {rel_path!r}")
    if not target.is_file():
        raise FileNotFoundError(f"User guide not found: {rel_path}")
    return target.read_text(encoding="utf-8")


def resolve_guide_href(href: str, current_rel_path: str, guides_dir: Path | None = None) -> str | None:
    """Resolve a relative markdown href to a guide path under ``User_Guides``."""
    href = href.strip()
    if not href or href.startswith("#"):
        return None
    lowered = href.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "userguide:")):
        return None
    root = (guides_dir or user_guides_dir()).resolve()
    base = (root / current_rel_path).parent
    target = (base / href).resolve()
    if not str(target).startswith(str(root)):
        return None
    if target.suffix.lower() != ".md":
        return None
    return str(target.relative_to(root))
