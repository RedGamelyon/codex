"""
Codex Application Configuration
Manages persistent user settings at ~/.config/codex/config.json
"""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "codex"
CONFIG_FILE = CONFIG_DIR / "config.json"
MAX_RECENT_WORLDS = 10


def load_config() -> dict:
    """Load config from disk. Returns empty dict if not found."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(data: dict) -> None:
    """Save config to disk. Creates directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_recent_worlds() -> list[Path]:
    """Get list of recently opened world paths that still exist."""
    config = load_config()
    # Read new key, fall back to old "recent_vaults" for backward compat
    paths = config.get("recent_worlds", config.get("recent_vaults", []))
    return [Path(p) for p in paths if Path(p).exists()]


def add_recent_world(world_path: Path) -> None:
    """Add a world path to the recent worlds list (most recent first)."""
    config = load_config()
    paths = config.get("recent_worlds", config.get("recent_vaults", []))
    path_str = str(world_path.resolve())
    paths = [p for p in paths if p != path_str]
    paths.insert(0, path_str)
    paths = paths[:MAX_RECENT_WORLDS]
    config["recent_worlds"] = paths
    # Remove old key if present
    config.pop("recent_vaults", None)
    save_config(config)
