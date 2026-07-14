"""Tests for chat supply helpers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from prompts import build_general_review_prompt
from ui.chat_supply import build_chat_prompt, collect_chat_context
from utils.config import AppConfig

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_build_chat_prompt(tmp_path: Path) -> None:
    ds_dir = FIXTURES / "datasheets"
    ds_dir.mkdir(exist_ok=True)
    (ds_dir / "F0D3180.pdf").write_bytes(b"%PDF-1.4 test")

    config = AppConfig(artifact_library_path=tmp_path / "library")
    ctx = collect_chat_context(
        FIXTURES / "testproj.kicad_pro",
        config=config,
        include_image=False,
    )
    built = build_chat_prompt(ctx, "Hello?", include_image=False)
    same = build_general_review_prompt(ctx, "Hello?", include_image=False)
    assert built.text == same.text
    assert built.template == "general_review"


def test_send_requires_approval_in_ui_not_here() -> None:
    """Approve & Send is enforced in ChatDialog; smoke test only documents contract."""
    assert True


def test_collect_chat_context_with_scan(tmp_path: Path) -> None:
    library = tmp_path / "library"
    ds = library / "datasheets"
    ds.mkdir(parents=True)
    (ds / "F0D3180.pdf").write_bytes(b"%PDF-1.4 scan test")

    config = AppConfig(artifact_library_path=library)
    ctx = collect_chat_context(
        FIXTURES / "testproj.kicad_pro",
        config=config,
        include_image=False,
    )
    assert ctx.project_name == "testproj"
