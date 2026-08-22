"""Discover Freerouting executable or JAR path."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from routing.errors import RoutingToolNotFoundError


class FreeroutingResolution:
    """Resolved Freerouting invocation."""

    def __init__(self, *, jar_path: Path | None = None, cli_path: Path | None = None) -> None:
        self.jar_path = jar_path
        self.cli_path = cli_path

    @property
    def installed(self) -> bool:
        return bool(self.jar_path or self.cli_path)

    def build_command(
        self,
        *,
        dsn_path: Path,
        ses_path: Path,
        excluded_net_classes: list[str] | None = None,
    ) -> list[str]:
        inc_args: list[str] = []
        for net_class in excluded_net_classes or []:
            inc_args.extend(["-inc", net_class])

        if self.cli_path:
            return [
                str(self.cli_path),
                "-de",
                str(dsn_path),
                "-do",
                str(ses_path),
                *inc_args,
            ]

        if self.jar_path:
            java = shutil.which("java") or "java"
            return [
                java,
                "-jar",
                str(self.jar_path),
                "-de",
                str(dsn_path),
                "-do",
                str(ses_path),
                *inc_args,
            ]

        raise RoutingToolNotFoundError("Freerouting is not installed.")


def resolve_freerouting(
    *,
    jar: str | None = None,
    cli: str | None = None,
) -> FreeroutingResolution:
    """
    Resolve Freerouting JAR or native executable.

    Order: explicit jar/cli → FREEROUTING_JAR / FREEROUTING_CLI env → PATH.
    """
    jar_candidates: list[Path | str] = []
    cli_candidates: list[Path | str] = []

    if jar:
        jar_candidates.append(jar)
    if cli:
        cli_candidates.append(cli)

    env_jar = os.environ.get("FREEROUTING_JAR")
    if env_jar:
        jar_candidates.append(env_jar)
    env_cli = os.environ.get("FREEROUTING_CLI")
    if env_cli:
        cli_candidates.append(env_cli)

    which_cli = shutil.which("freerouting")
    if which_cli:
        cli_candidates.append(which_cli)

    for candidate in cli_candidates:
        path = Path(candidate).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return FreeroutingResolution(cli_path=path.resolve())

    for candidate in jar_candidates:
        path = Path(candidate).expanduser()
        if path.is_file():
            return FreeroutingResolution(jar_path=path.resolve())

    if sys.platform == "darwin":
        mac_jar = Path.home() / "Applications" / "freerouting.jar"
        if mac_jar.is_file():
            return FreeroutingResolution(jar_path=mac_jar.resolve())

    raise RoutingToolNotFoundError(
        "Freerouting not found. Install Freerouting and set FREEROUTING_JAR or FREEROUTING_CLI."
    )


def try_resolve_freerouting(
    *,
    jar: str | None = None,
    cli: str | None = None,
) -> FreeroutingResolution | None:
    try:
        return resolve_freerouting(jar=jar, cli=cli)
    except RoutingToolNotFoundError:
        return None
