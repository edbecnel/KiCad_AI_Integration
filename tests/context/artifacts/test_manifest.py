"""Tests for per-project manifest."""

from pathlib import Path

from context.artifacts.manifest import Manifest, ManifestComponentLink, ManifestLink


def test_manifest_round_trip(tmp_path: Path) -> None:
    pro = tmp_path / "flyback.kicad_pro"
    pro.touch()
    manifest = Manifest(
        project_path=str(pro),
        project_name="flyback",
        links=[
            ManifestLink(
                artifact_id="ds-F0D3180-abc",
                part="F0D3180",
                components=[
                    ManifestComponentLink(reference="U3", sheet_path="flyback.kicad_sch")
                ],
            )
        ],
    )
    saved = manifest.save()
    assert saved.is_file()
    loaded = Manifest.load(pro)
    assert loaded.project_name == "flyback"
    assert len(loaded.links) == 1
    assert loaded.links[0].components[0].reference == "U3"
