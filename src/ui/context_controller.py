"""Centralized project context collection for the Assistant shell (ADP-011)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from context.collector import collect_stretch_context
from context.context_cache import save_context_cache
from context.fingerprint import compute_fingerprint, save_fingerprint
from context.incremental import refresh_context_layers
from context.model import ProjectContext
from ui.project_path import format_launcher_context_summary
from utils.config import AppConfig, load_config

ContextListener = Callable[[ProjectContext, str], None]


class ContextController:
    """Owns ProjectContext refresh and notifies Assistant tab panels."""

    def __init__(self, *, config: AppConfig | None = None) -> None:
        self.project_path: Path | None = None
        self.context: ProjectContext | None = None
        self.summary_text: str = ""
        self.last_error: str | None = None
        self._config = config
        self._listeners: list[ContextListener] = []

    def bind_listener(self, callback: ContextListener) -> None:
        """Register a callback invoked after each successful refresh."""
        self._listeners.append(callback)

    def refresh(self, project_path: Path) -> None:
        """Collect context once and notify listeners."""
        self.last_error = None
        pro = Path(project_path).expanduser().resolve()
        cfg = self._config or load_config()
        try:
            ctx = collect_stretch_context(pro, config=cfg, verbose=False)
            summary = format_launcher_context_summary(pro, ctx, cfg=cfg)
            save_fingerprint(compute_fingerprint(pro))
        except OSError as exc:
            self.last_error = str(exc)
            self.project_path = None
            self.context = None
            self.summary_text = ""
            return

        self.project_path = pro
        self.context = ctx
        self.summary_text = summary
        for listener in self._listeners:
            listener(ctx, summary)

    def refresh_layers(self, layers: set[str], *, include_image: bool = False) -> bool:
        """Partially refresh dirty layers on the current context."""
        if self.context is None or self.project_path is None or not layers:
            return False
        cfg = self._config or load_config()
        try:
            ctx = refresh_context_layers(
                self.context,
                self.project_path,
                layers,
                config=cfg,
                include_image=include_image,
            )
            summary = format_launcher_context_summary(self.project_path, ctx, cfg=cfg)
        except OSError as exc:
            self.last_error = str(exc)
            return False

        self.context = ctx
        self.summary_text = summary
        for listener in self._listeners:
            listener(ctx, summary)
        return True

    def save_context_cache(self, *, prompt_excerpt: str | None = None) -> None:
        """Persist static context snapshot after a successful chat turn."""
        if self.context is None or self.project_path is None:
            return
        save_context_cache(self.project_path, self.context, prompt_excerpt=prompt_excerpt)
