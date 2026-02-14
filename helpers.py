"""
Codex Helper Functions
Data operations for worlds and characters.
"""

from datetime import date
from pathlib import Path
import shutil
import subprocess
import yaml


PORTRAIT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")

# Section metadata
SECTIONS = {
    "characters": {
        "name": "Characters",
        "folder": "characters",
        "description": "People, creatures, NPCs",
        "singular": "Character",
    },
    "locations": {
        "name": "Locations",
        "folder": "locations",
        "description": "Places, regions, dungeons",
        "singular": "Location",
    },
    "timeline": {
        "name": "Timeline",
        "folder": "timeline",
        "description": "Events and history",
        "singular": "Event",
    },
    "codex": {
        "name": "Codex",
        "folder": "codex",
        "description": "Items, factions, races, lore",
        "singular": "Entry",
    },
}


def open_in_file_manager(path: Path) -> None:
    """Open a folder in the system file manager."""
    import platform
    p = str(path)
    try:
        system = platform.system()
        if system == "Linux":
            if shutil.which("gio"):
                subprocess.Popen(["gio", "open", p])
            elif shutil.which("nautilus"):
                subprocess.Popen(["nautilus", p])
            elif shutil.which("dolphin"):
                subprocess.Popen(["dolphin", p])
            elif shutil.which("thunar"):
                subprocess.Popen(["thunar", p])
            elif shutil.which("nemo"):
                subprocess.Popen(["nemo", p])
            elif shutil.which("pcmanfm"):
                subprocess.Popen(["pcmanfm", p])
            else:
                subprocess.Popen(["xdg-open", p])
        elif system == "Darwin":
            subprocess.Popen(["open", p])
        elif system == "Windows":
            subprocess.Popen(["explorer", p])
    except Exception:
        pass


# --- World Management ---

def _migrate_vault_yaml(world_path: Path) -> None:
    """Rename vault.yaml to world.yaml if needed (backward compat)."""
    old = world_path / "vault.yaml"
    new = world_path / "world.yaml"
    if old.exists() and not new.exists():
        old.rename(new)


def create_world(path: str) -> None:
    """Create a new world at the given path."""
    world_path = Path(path)
    world_path.mkdir(parents=True, exist_ok=True)

    characters_dir = world_path / "characters"
    characters_dir.mkdir(exist_ok=True)

    world_config = world_path / "world.yaml"
    config_data = {
        "name": world_path.name,
        "description": "",
        "created": str(date.today()),
        "enabled_sections": ["characters"],
    }
    with open(world_config, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False)

    from templates import ensure_default_template
    ensure_default_template(world_path)


def is_valid_world(path: Path) -> bool:
    """Check if a path is a valid world (has world.yaml or vault.yaml, and characters/)."""
    if not path.exists() or not path.is_dir():
        return False

    characters_dir = path / "characters"
    if not characters_dir.exists():
        return False

    # Accept both world.yaml (new) and vault.yaml (legacy)
    return (path / "world.yaml").exists() or (path / "vault.yaml").exists()


def get_world_name(world_path: Path) -> str:
    """Get the name of a world from its config."""
    _migrate_vault_yaml(world_path)
    world_config = world_path / "world.yaml"
    if world_config.exists():
        with open(world_config, "r") as f:
            config = yaml.safe_load(f)
            return config.get("name", world_path.name)
    return world_path.name


def get_world_stats(world_path: Path) -> dict:
    """Get statistics about a world."""
    characters = list_characters(world_path)

    total_tags = set()
    for char_path in characters:
        content = read_character(char_path)
        parsed = parse_character(content)
        tags_str = parsed.get("tags", "")
        if tags_str:
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    total_tags.add(tag)

    return {
        "character_count": len(characters),
        "tag_count": len(total_tags),
        "tags": sorted(total_tags)
    }


def discover_worlds(search_paths: list[Path] | None = None) -> list[Path]:
    """Find all valid worlds in common locations."""
    if search_paths is None:
        search_paths = [
            Path.home() / "Documents",
            Path.home() / "projects",
            Path.home() / "codex",
            Path.home(),
            Path.cwd(),
        ]

    worlds = []
    seen = set()

    for base_path in search_paths:
        if not base_path.exists():
            continue

        if is_valid_world(base_path) and base_path not in seen:
            worlds.append(base_path)
            seen.add(base_path)

        try:
            for item in base_path.iterdir():
                if item.is_dir() and item not in seen and is_valid_world(item):
                    worlds.append(item)
                    seen.add(item)
        except PermissionError:
            continue

    return sorted(worlds, key=lambda p: p.name.lower())


def get_default_locations() -> list[Path]:
    """Get default locations for creating worlds."""
    locations = [
        Path.home() / "Documents",
        Path.home() / "projects",
        Path.home() / "codex",
    ]
    return [loc for loc in locations if loc.exists() or loc.parent.exists()]


# --- Section System ---

def get_enabled_sections(world_path: Path) -> list[str]:
    """Return list of enabled section names."""
    _migrate_vault_yaml(world_path)
    config_file = world_path / "world.yaml"
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
        return config.get("enabled_sections", ["characters"])
    return ["characters"]


def enable_section(world_path: Path, section: str) -> None:
    """Add section to enabled_sections in world.yaml and create its folder."""
    _migrate_vault_yaml(world_path)
    config_file = world_path / "world.yaml"
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    sections = config.get("enabled_sections", ["characters"])
    if section not in sections:
        sections.append(section)
    config["enabled_sections"] = sections

    # Create folder if section is known
    if section in SECTIONS:
        folder = world_path / SECTIONS[section]["folder"]
        folder.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Create default templates for the section
    from templates import ensure_section_templates
    ensure_section_templates(world_path, section)


def disable_section(world_path: Path, section: str) -> None:
    """Remove section from enabled_sections in world.yaml."""
    _migrate_vault_yaml(world_path)
    config_file = world_path / "world.yaml"
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    sections = config.get("enabled_sections", ["characters"])
    if section in sections:
        sections.remove(section)
    config["enabled_sections"] = sections
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def is_section_enabled(world_path: Path, section: str) -> bool:
    """Check if a section is enabled."""
    return section in get_enabled_sections(world_path)


def update_world_meta(world_path: Path, name: str | None = None, description: str | None = None) -> None:
    """Update world name and/or description in world.yaml."""
    _migrate_vault_yaml(world_path)
    config_file = world_path / "world.yaml"
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    if name is not None:
        config["name"] = name
    if description is not None:
        config["description"] = description
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_world_description(world_path: Path) -> str:
    """Get the description of a world from its config."""
    _migrate_vault_yaml(world_path)
    config_file = world_path / "world.yaml"
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
        return config.get("description", "")
    return ""


def delete_world(world_path: Path) -> bool:
    """Delete an entire world folder. Returns True on success."""
    try:
        if world_path.exists() and world_path.is_dir():
            shutil.rmtree(str(world_path))
            return True
        return False
    except Exception:
        return False


def get_section_count(world_path: Path, section: str) -> int:
    """Count entries in a section (including subfolders)."""
    return len(list_entities(world_path, section))


def get_recent_activity(world_path: Path, limit: int = 5) -> list[dict]:
    """Get recently modified entries across all enabled sections."""
    entries = []

    for section in get_enabled_sections(world_path):
        if section not in SECTIONS:
            continue
        for entity_path in list_entities(world_path, section):
            try:
                mtime = entity_path.stat().st_mtime
            except OSError:
                continue
            content = read_character(entity_path)
            parsed = parse_character(content)
            entries.append({
                "name": parsed.get("name", entity_path.stem.replace("_", " ").title()),
                "section": section,
                "path": entity_path,
                "modified": mtime,
            })

    entries.sort(key=lambda x: x["modified"], reverse=True)
    return entries[:limit]


def get_tag_counts(world_path: Path) -> dict[str, int]:
    """Get tag usage counts across all enabled sections."""
    tag_counts: dict[str, int] = {}
    for section in get_enabled_sections(world_path):
        if section not in SECTIONS:
            continue
        for entity_path in list_entities(world_path, section):
            try:
                content = read_character(entity_path)
                parsed = parse_character(content)
                tags_str = parsed.get("tags", "")
                if tags_str:
                    for tag in tags_str.split(","):
                        tag = tag.strip()
                        if tag:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            except Exception:
                continue
    return tag_counts


# --- Character Management ---

def get_character_slug(name: str) -> str:
    """Generate a filesystem-safe slug from a character name."""
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in name)
    return safe_name.strip().replace(" ", "_").lower()


def get_most_connected(world_path: Path, limit: int = 5) -> list[dict]:
    """Find entries that are referenced most often via link fields."""
    ref_counts: dict[str, int] = {}
    ref_names: dict[str, str] = {}

    for section in get_enabled_sections(world_path):
        if section not in SECTIONS:
            continue
        for entity_path in list_entities(world_path, section):
            try:
                content = entity_path.read_text(encoding="utf-8")
            except Exception:
                continue
            # Count section:slug references
            for line in content.split("\n"):
                line = line.strip()
                if ":" in line and not line.startswith("---") and not line.startswith("#"):
                    parts = line.split(":")
                    if len(parts) == 2:
                        sec, slug = parts[0].strip(), parts[1].strip()
                        if sec in SECTIONS and slug and " " not in slug:
                            key = f"{sec}:{slug}"
                            ref_counts[key] = ref_counts.get(key, 0) + 1

    # Resolve names for top entries
    results = []
    for key, count in sorted(ref_counts.items(), key=lambda x: -x[1])[:limit]:
        sec, slug = key.split(":", 1)
        name = ref_names.get(key)
        if not name:
            entity_dir = get_entity_dir(world_path, sec)
            # Search root and subfolders
            for candidate in entity_dir.rglob(f"{slug}.md"):
                if "images" not in candidate.parts:
                    try:
                        content = read_character(candidate)
                        parsed = parse_character(content)
                        name = parsed.get("name", slug.replace("_", " ").title())
                    except Exception:
                        name = slug.replace("_", " ").title()
                    break
            if not name:
                name = slug.replace("_", " ").title()
        results.append({"section": sec, "slug": slug, "name": name, "count": count})

    return results


def save_character(
    world_path: Path,
    name: str,
    summary: str,
    description: str,
    traits: str,
    history: str,
    relationships: str,
    tags: list[str]
) -> Path:
    """Save a character to the world as a markdown file."""
    characters_dir = get_characters_dir(world_path)
    slug = get_character_slug(name)
    filepath = characters_dir / f"{slug}.md"

    # Build markdown content
    tags_str = ", ".join(tags) if tags else ""
    content = f"""# {name}

## Summary
{summary}

## Description
{description}

## Traits
{traits}

## History
{history}

## Relationships
{relationships}

## Tags
{tags_str}
"""

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def save_character_from_template(world_path: Path, template, form_data: dict) -> Path:
    """Save a character using template-based rendering."""
    from templates import render_character_from_template

    name = form_data.get("name", "Unnamed")
    characters_dir = get_characters_dir(world_path)
    slug = get_character_slug(name)
    filepath = characters_dir / f"{slug}.md"

    content = render_character_from_template(template, form_data)

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def get_characters_dir(world_path: Path) -> Path:
    """Get the characters directory for a world."""
    return world_path / "characters"


def read_character(path: Path) -> str:
    """Read a character markdown file."""
    with open(path, "r") as f:
        return f.read()


def list_characters(world_path: Path) -> list[Path]:
    """List all character files in a world."""
    characters_dir = get_characters_dir(world_path)
    if not characters_dir.exists():
        return []
    return sorted(characters_dir.glob("*.md"))


def make_title_box(title: str, padding: int = 2) -> str:
    """Create an ASCII box around a title."""
    inner_width = len(title) + padding * 2
    top = "\u250c" + "\u2500" * inner_width + "\u2510"
    middle = "\u2502" + " " * padding + title + " " * padding + "\u2502"
    bottom = "\u2514" + "\u2500" * inner_width + "\u2518"
    return f"{top}\n{middle}\n{bottom}"


def make_section_header(section: str) -> str:
    """Create a section header with decorative lines."""
    return f"\u2501\u2501\u2501 {section} \u2501\u2501\u2501"


def render_character(markdown: str) -> str:
    """Render character markdown for display."""
    return markdown


def parse_character(markdown: str) -> dict[str, str]:
    """Parse character markdown into a dictionary.

    Handles optional YAML frontmatter (--- ... ---). Frontmatter is stored
    under the '_meta' key. Characters without frontmatter get _meta={}.
    Section headers are normalized to lowercase with spaces replaced by
    underscores so they match template field keys (e.g. "Combat Style" ->
    "combat_style").
    """
    from templates import _strip_frontmatter

    meta, body = _strip_frontmatter(markdown)

    result: dict[str, str] = {"name": "", "_meta": meta}

    lines = body.split("\n")
    current_section = None
    current_content = []

    for line in lines:
        stripped = line.strip()
        # Skip portrait marker
        if stripped.startswith("![portrait]"):
            continue
        if line.startswith("# "):
            result["name"] = line[2:].strip()
        elif line.startswith("## "):
            # Save previous section
            if current_section:
                result[current_section] = "\n".join(current_content).strip()

            # Normalize: lowercase + spaces to underscores to match template keys
            section_name = line[3:].strip().lower().replace(" ", "_")
            current_section = section_name
            current_content = []
        elif current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        result[current_section] = "\n".join(current_content).strip()

    return result


def delete_character(path: Path) -> bool:
    """Delete a character file."""
    try:
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def sort_characters(characters: list[Path], sort_mode: str) -> list[Path]:
    """Sort character paths by the given mode."""
    if sort_mode == "name_asc":
        return sorted(characters, key=lambda p: p.stem.lower())
    elif sort_mode == "name_desc":
        return sorted(characters, key=lambda p: p.stem.lower(), reverse=True)
    elif sort_mode == "date_desc":
        return sorted(characters, key=lambda p: p.stat().st_mtime, reverse=True)
    elif sort_mode == "date_asc":
        return sorted(characters, key=lambda p: p.stat().st_mtime)
    return characters


# --- Portrait Management ---

def get_portrait_dir(world_path: Path, slug: str) -> Path:
    """Get the portrait directory for a character slug."""
    return get_characters_dir(world_path) / "images" / slug


def find_portrait(world_path: Path, character_name: str, field_key: str = "portrait") -> Path | None:
    """Find an image file for a character field. Returns path or None."""
    slug = get_character_slug(character_name)
    portrait_dir = get_portrait_dir(world_path, slug)
    if not portrait_dir.exists():
        return None
    for ext in PORTRAIT_EXTENSIONS:
        candidate = portrait_dir / f"{field_key}{ext}"
        if candidate.exists():
            return candidate
    return None


def save_portrait(world_path: Path, character_name: str, source_path: str, field_key: str = "portrait") -> Path | None:
    """Copy an image into the character's image directory.

    Removes existing file for this field_key first. Returns new path or None on failure.
    """
    slug = get_character_slug(character_name)
    portrait_dir = get_portrait_dir(world_path, slug)
    print(f"[DEBUG] save_portrait: slug={slug!r} field_key={field_key!r}")
    print(f"[DEBUG] save_portrait: source={source_path!r}")
    print(f"[DEBUG] save_portrait: target_dir={portrait_dir}")

    source = Path(source_path).resolve()
    print(f"[DEBUG] save_portrait: resolved source={source}")
    ext = source.suffix.lower()
    print(f"[DEBUG] save_portrait: source exists={source.exists()}, is_file={source.is_file()}, suffix={ext!r}")

    if not source.exists():
        print(f"[ERROR] save_portrait: source file does not exist: {source}")
        return None
    if not source.is_file():
        print(f"[ERROR] save_portrait: source is not a file: {source}")
        return None
    if ext not in PORTRAIT_EXTENSIONS:
        print(f"[ERROR] save_portrait: unsupported extension {ext!r}, allowed: {PORTRAIT_EXTENSIONS}")
        return None

    # Remove existing file for this field_key only
    remove_portrait(world_path, character_name, field_key=field_key)

    # Create directory (remove_portrait only rmdir's when empty)
    try:
        portrait_dir.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] save_portrait: directory created/exists: {portrait_dir.exists()}")
    except PermissionError as e:
        print(f"[ERROR] save_portrait: permission denied creating dir: {e}")
        return None
    except OSError as e:
        print(f"[ERROR] save_portrait: OS error creating dir: {e}")
        return None

    dest = portrait_dir / f"{field_key}{ext}"
    print(f"[DEBUG] save_portrait: copying {source} -> {dest}")
    try:
        shutil.copy2(str(source), str(dest))
        print(f"[DEBUG] save_portrait: copy successful, dest exists={dest.exists()}, size={dest.stat().st_size}")
        return dest
    except Exception as copy_err:
        print(f"[DEBUG] save_portrait: shutil.copy2 failed: {type(copy_err).__name__}: {copy_err}")
        try:
            with open(source, 'rb') as src_f:
                data = src_f.read()
            with open(dest, 'wb') as dst_f:
                dst_f.write(data)
            print(f"[DEBUG] save_portrait: manual copy done, dest exists={dest.exists()}")
            return dest
        except Exception as e:
            print(f"[ERROR] save_portrait: manual copy also failed: {type(e).__name__}: {e}")
            return None


def remove_portrait(world_path: Path, character_name: str, field_key: str | None = None) -> bool:
    """Remove image files for a character.

    If field_key is None, removes ALL images in the slug directory (for character deletion).
    If field_key is given, removes only that field_key's files.
    Only rmdir's the directory if it's empty afterward.
    """
    slug = get_character_slug(character_name)
    portrait_dir = get_portrait_dir(world_path, slug)
    removed = False
    if portrait_dir.exists():
        if field_key is None:
            # Remove everything in the directory
            for child in list(portrait_dir.iterdir()):
                try:
                    child.unlink()
                    removed = True
                except OSError:
                    pass
        else:
            # Remove only files for this field_key
            for ext in PORTRAIT_EXTENSIONS:
                candidate = portrait_dir / f"{field_key}{ext}"
                if candidate.exists():
                    candidate.unlink()
                    removed = True
        # Only rmdir if empty
        try:
            portrait_dir.rmdir()
        except OSError:
            pass
    return removed


def rename_portrait_dir(world_path: Path, old_name: str, new_name: str) -> bool:
    """Move portrait directory when a character is renamed."""
    old_slug = get_character_slug(old_name)
    new_slug = get_character_slug(new_name)
    if old_slug == new_slug:
        return True

    old_dir = get_portrait_dir(world_path, old_slug)
    new_dir = get_portrait_dir(world_path, new_slug)

    if old_dir.exists():
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            old_dir.rename(new_dir)
            return True
        except Exception:
            return False
    return True


def pick_image_file() -> str | None:
    """Open a zenity file picker for image selection. Returns path or None."""
    print("[DEBUG] Opening zenity file picker...")
    try:
        result = subprocess.run(
            [
                "zenity", "--file-selection",
                "--title=Select Portrait Image",
                "--file-filter=Images | *.png *.jpg *.jpeg *.gif *.webp",
                "--file-filter=All files | *",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        print(f"[DEBUG] zenity returncode: {result.returncode}")
        print(f"[DEBUG] Raw zenity stdout repr: {result.stdout!r}")
        if result.stderr.strip():
            print(f"[DEBUG] zenity stderr: {result.stderr.strip()}")
        if result.returncode == 0:
            path = result.stdout.strip().strip("'").strip('"').strip()
            path = path.replace('\n', '').replace('\r', '')
            print(f"[DEBUG] Cleaned file path repr: {path!r}")
            if path:
                p = Path(path)
                print(f"[DEBUG] Selected file: {path}")
                print(f"[DEBUG] File exists: {p.exists()}")
                print(f"[DEBUG] File is_file: {p.is_file()}")
                print(f"[DEBUG] File suffix: {p.suffix}")
                return path
        print("[DEBUG] No file selected (cancelled or empty)")
        return None
    except subprocess.TimeoutExpired:
        print("[ERROR] zenity timed out after 120s")
        return None
    except FileNotFoundError:
        print("[ERROR] zenity not found on this system")
        return None
    except Exception as e:
        print(f"[ERROR] File picker error: {type(e).__name__}: {e}")
        return None


# --- Entity System (generic, section-aware) ---

def get_entity_dir(world_path: Path, section: str) -> Path:
    """Get the entity directory for a section."""
    if section in SECTIONS:
        return world_path / SECTIONS[section]["folder"]
    return world_path / section


def list_entities(world_path: Path, section: str) -> list[Path]:
    """List all entity files in a section, including subfolders."""
    entity_dir = get_entity_dir(world_path, section)
    if not entity_dir.exists():
        return []
    results = []
    for item in entity_dir.rglob("*.md"):
        # Skip files inside 'images' directories
        if "images" in item.parts:
            continue
        results.append(item)
    return sorted(results)


def list_entities_with_folders(world_path: Path, section: str) -> dict:
    """List entities organized by folder.

    Returns:
        {
            "folders": {
                "folder_slug": {
                    "name": "Display Name",
                    "path": Path,
                    "entries": [Path, ...],
                },
                ...
            },
            "root_entries": [Path, ...],
        }
    """
    entity_dir = get_entity_dir(world_path, section)
    result: dict = {"folders": {}, "root_entries": []}
    if not entity_dir.exists():
        return result

    for item in sorted(entity_dir.iterdir()):
        if item.is_dir() and item.name != "images":
            folder_entries = sorted(item.glob("*.md"), key=lambda p: p.stem.lower())
            result["folders"][item.name] = {
                "name": item.name.replace("_", " ").title(),
                "path": item,
                "entries": folder_entries,
            }
        elif item.is_file() and item.suffix == ".md":
            result["root_entries"].append(item)

    result["root_entries"].sort(key=lambda p: p.stem.lower())
    return result


def create_folder(world_path: Path, section: str, folder_name: str) -> Path:
    """Create a new subfolder in a section."""
    entity_dir = get_entity_dir(world_path, section)
    slug = folder_name.strip().lower().replace(" ", "_")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    folder_path = entity_dir / slug
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def rename_folder(world_path: Path, section: str, old_slug: str, new_name: str) -> Path | None:
    """Rename a subfolder. Returns new path or None on failure."""
    entity_dir = get_entity_dir(world_path, section)
    old_path = entity_dir / old_slug
    if not old_path.exists() or not old_path.is_dir():
        return None
    new_slug = new_name.strip().lower().replace(" ", "_")
    new_slug = "".join(c for c in new_slug if c.isalnum() or c == "_")
    new_path = entity_dir / new_slug
    if new_path.exists():
        return None
    old_path.rename(new_path)
    return new_path


def delete_folder(world_path: Path, section: str, folder_slug: str) -> bool:
    """Delete an empty subfolder. Returns True if deleted."""
    entity_dir = get_entity_dir(world_path, section)
    folder_path = entity_dir / folder_slug
    if not folder_path.exists() or not folder_path.is_dir():
        return False
    # Only delete if no .md files remain
    if list(folder_path.glob("*.md")):
        return False
    try:
        shutil.rmtree(str(folder_path))
        return True
    except Exception:
        return False


def move_entity_to_folder(world_path: Path, section: str, entity_path: Path,
                          target_folder: str | None) -> Path:
    """Move an entity to a subfolder, or to root if target_folder is None.

    Also moves the entity's images directory.
    Returns the new entity path.
    """
    entity_dir = get_entity_dir(world_path, section)
    slug = entity_path.stem

    if target_folder:
        dest_dir = entity_dir / target_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
    else:
        dest_dir = entity_dir

    new_path = dest_dir / entity_path.name
    if new_path == entity_path:
        return entity_path

    shutil.move(str(entity_path), str(new_path))

    # Move images: always stored in entity_dir/images/slug
    # Images stay in the central images dir, no need to move
    return new_path


def save_entity_from_template(world_path: Path, section: str, template, form_data: dict) -> Path:
    """Save an entity using template-based rendering."""
    from templates import render_character_from_template

    name = form_data.get("name", "Unnamed")
    entity_dir = get_entity_dir(world_path, section)
    entity_dir.mkdir(parents=True, exist_ok=True)
    slug = get_character_slug(name)
    filepath = entity_dir / f"{slug}.md"

    content = render_character_from_template(template, form_data)

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def get_entity_image_dir(world_path: Path, section: str, slug: str) -> Path:
    """Get the image directory for an entity in a section."""
    return get_entity_dir(world_path, section) / "images" / slug


def find_entity_image(world_path: Path, section: str, entity_name: str, field_key: str = "portrait") -> Path | None:
    """Find an image file for an entity field. Returns path or None."""
    slug = get_character_slug(entity_name)
    img_dir = get_entity_image_dir(world_path, section, slug)
    if not img_dir.exists():
        return None
    for ext in PORTRAIT_EXTENSIONS:
        candidate = img_dir / f"{field_key}{ext}"
        if candidate.exists():
            return candidate
    return None


def save_entity_image(world_path: Path, section: str, entity_name: str, source_path: str, field_key: str = "portrait") -> Path | None:
    """Save an image for an entity. Returns new path or None."""
    slug = get_character_slug(entity_name)
    img_dir = get_entity_image_dir(world_path, section, slug)

    source = Path(source_path).resolve()
    ext = source.suffix.lower()

    if not source.exists() or not source.is_file() or ext not in PORTRAIT_EXTENSIONS:
        return None

    # Remove existing file for this field_key
    remove_entity_image(world_path, section, entity_name, field_key=field_key)

    try:
        img_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None

    dest = img_dir / f"{field_key}{ext}"
    try:
        shutil.copy2(str(source), str(dest))
        return dest
    except Exception:
        return None


def remove_entity_image(world_path: Path, section: str, entity_name: str, field_key: str | None = None) -> bool:
    """Remove image files for an entity."""
    slug = get_character_slug(entity_name)
    img_dir = get_entity_image_dir(world_path, section, slug)
    removed = False
    if img_dir.exists():
        if field_key is None:
            for child in list(img_dir.iterdir()):
                try:
                    child.unlink()
                    removed = True
                except OSError:
                    pass
        else:
            for ext in PORTRAIT_EXTENSIONS:
                candidate = img_dir / f"{field_key}{ext}"
                if candidate.exists():
                    candidate.unlink()
                    removed = True
        try:
            img_dir.rmdir()
        except OSError:
            pass
    return removed


def load_timeline_events(world_path: Path) -> list[dict]:
    """Load all timeline events from .md files, sorted by date."""
    events = []
    timeline_dir = get_entity_dir(world_path, "timeline")
    if not timeline_dir.exists():
        return events

    for md_file in sorted(list_entities(world_path, "timeline")):
        try:
            content = read_character(md_file)
            parsed = parse_character(content)

            date_str = parsed.get("date", "").strip()
            try:
                date_val = float(date_str) if date_str else 0
            except ValueError:
                date_val = 0

            events.append({
                "name": parsed.get("name", md_file.stem.replace("_", " ").title()),
                "date": date_val,
                "era": parsed.get("era", ""),
                "tags": parsed.get("tags", ""),
                "description": parsed.get("description", ""),
                "characters_involved": parsed.get("characters_involved", ""),
                "locations": parsed.get("locations", ""),
                "consequences": parsed.get("consequences", ""),
                "path": md_file,
            })
        except Exception:
            continue

    events.sort(key=lambda e: e["date"])
    return events


def update_event_date(event_path: Path, new_date: float) -> None:
    """Update the date field in a timeline event .md file."""
    content = event_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    result = []
    in_date_section = False
    date_replaced = False

    for line in lines:
        if line.strip() == "## Date":
            in_date_section = True
            result.append(line)
            continue
        if in_date_section and not date_replaced:
            date_val = int(new_date) if new_date == int(new_date) else round(new_date, 1)
            result.append(str(date_val))
            in_date_section = False
            date_replaced = True
            continue
        if line.startswith("## "):
            in_date_section = False
        result.append(line)

    event_path.write_text("\n".join(result), encoding="utf-8")


def get_calendar_config(world_path: Path) -> dict:
    """Get calendar configuration from world.yaml."""
    _migrate_vault_yaml(world_path)
    config_file = world_path / "world.yaml"
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
        return config.get("calendar", {})
    return {}


def save_calendar_config(world_path: Path, calendar: dict) -> None:
    """Save calendar configuration to world.yaml."""
    _migrate_vault_yaml(world_path)
    config_file = world_path / "world.yaml"
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    config["calendar"] = calendar
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


# --- Link System ---

def parse_link_field(value: str) -> list[dict]:
    """Parse a link field value into list of {section, slug} dicts.

    Supports 'section:slug' format (one per line).
    """
    links = []
    for line in value.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            section, slug = line.split(":", 1)
            section = section.strip()
            slug = slug.strip()
            if section and slug:
                links.append({"section": section, "slug": slug})
    return links


def format_link_field(links: list[dict]) -> str:
    """Format links for storage in markdown."""
    lines = []
    for link in links:
        lines.append(f"{link['section']}:{link['slug']}")
    return "\n".join(lines)


def resolve_link_name(world_path: Path, section: str, slug: str) -> str:
    """Resolve a link's display name from its entity file."""
    entity_dir = get_entity_dir(world_path, section)
    entity_path = entity_dir / f"{slug}.md"
    if entity_path.exists():
        try:
            content = read_character(entity_path)
            parsed = parse_character(content)
            return parsed.get("name", slug.replace("_", " ").title())
        except Exception:
            pass
    return slug.replace("_", " ").title()


def find_backlinks(world_path: Path, target_section: str, target_slug: str) -> list[dict]:
    """Find all entries that link to the target entry.

    Searches all section folders for link references in 'section:slug' format.
    """
    backlinks = []
    target_ref = f"{target_section}:{target_slug}"

    for section_key in SECTIONS:
        section_dir = get_entity_dir(world_path, section_key)
        if not section_dir.exists():
            continue

        for entity_file in section_dir.glob("*.md"):
            try:
                content = entity_file.read_text(encoding="utf-8")
            except Exception:
                continue

            if target_ref not in content:
                continue

            # Find which field(s) contain the link
            parsed = parse_character(content)
            linking_field = None
            for field_name, field_value in parsed.items():
                if field_name.startswith("_"):
                    continue
                if target_ref in str(field_value):
                    linking_field = field_name.replace("_", " ").title()
                    break

            backlinks.append({
                "section": section_key,
                "slug": entity_file.stem,
                "name": parsed.get("name", entity_file.stem.replace("_", " ").title()),
                "field": linking_field,
                "path": entity_file,
            })

    return backlinks


def rename_entity_image_dir(world_path: Path, section: str, old_name: str, new_name: str) -> bool:
    """Move image directory when an entity is renamed."""
    old_slug = get_character_slug(old_name)
    new_slug = get_character_slug(new_name)
    if old_slug == new_slug:
        return True

    old_dir = get_entity_image_dir(world_path, section, old_slug)
    new_dir = get_entity_image_dir(world_path, section, new_slug)

    if old_dir.exists():
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            old_dir.rename(new_dir)
            return True
        except Exception:
            return False
    return True
