"""Tests for datasheets folder catalog scan."""

from pathlib import Path

from context.artifacts.store import ArtifactStore


def test_scan_datasheets_folder_registers_new_pdf(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "library")
    store.bootstrap()
    ds = store.library_path / "datasheets"
    (ds / "LM7805.pdf").write_bytes(b"%PDF-1.4 lm7805")

    added = store.scan_datasheets_folder()
    assert added == 1
    entries = store.get_by_part("LM7805", "datasheet")
    assert len(entries) == 1

    added_again = store.scan_datasheets_folder()
    assert added_again == 0
