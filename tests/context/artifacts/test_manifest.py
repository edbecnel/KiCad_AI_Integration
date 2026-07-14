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


def test_upsert_link_same_artifact_different_parts() -> None:
    manifest = Manifest(project_path="/p/flyback.kicad_pro", project_name="flyback")
    comp_a = ManifestComponentLink(reference="U1", sheet_path="flyback.kicad_sch")
    comp_b = ManifestComponentLink(reference="U14", sheet_path="flyback.kicad_sch")
    manifest.upsert_link("ds-FOD3180-abc", "FOD3180", comp_a)
    manifest.upsert_link("ds-FOD3180-abc", "FOD3180-TEST", comp_b)
    assert len(manifest.links) == 2
    assert manifest.get_links_for_part("FOD3180")[0].artifact_id == "ds-FOD3180-abc"
    assert manifest.get_links_for_part("FOD3180-TEST")[0].components[0].reference == "U14"
