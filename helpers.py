"""
Codex Helper Functions
Data operations for vaults and characters.
"""

from pathlib import Path
import shutil
import subprocess
import yaml


PORTRAIT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


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


def create_vault(path: str) -> None:
    """Create a new vault at the given path."""
    vault_path = Path(path)
    vault_path.mkdir(parents=True, exist_ok=True)

    characters_dir = vault_path / "characters"
    characters_dir.mkdir(exist_ok=True)

    vault_config = vault_path / "vault.yaml"
    config_data = {
        "name": vault_path.name,
        "version": "1.0",
        "description": f"Vault: {vault_path.name}"
    }
    with open(vault_config, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False)

    from templates import ensure_default_template
    ensure_default_template(vault_path)


def get_character_slug(name: str) -> str:
    """Generate a filesystem-safe slug from a character name."""
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in name)
    return safe_name.strip().replace(" ", "_").lower()


def save_character(
    vault_path: Path,
    name: str,
    summary: str,
    description: str,
    traits: str,
    history: str,
    relationships: str,
    tags: list[str]
) -> Path:
    """Save a character to the vault as a markdown file."""
    characters_dir = get_characters_dir(vault_path)
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


def save_character_from_template(vault_path: Path, template, form_data: dict) -> Path:
    """Save a character using template-based rendering."""
    from templates import render_character_from_template

    name = form_data.get("name", "Unnamed")
    characters_dir = get_characters_dir(vault_path)
    slug = get_character_slug(name)
    filepath = characters_dir / f"{slug}.md"

    content = render_character_from_template(template, form_data)

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def is_valid_vault(path: Path) -> bool:
    """Check if a path is a valid vault (has vault.yaml and characters/)."""
    if not path.exists() or not path.is_dir():
        return False

    vault_config = path / "vault.yaml"
    characters_dir = path / "characters"

    return vault_config.exists() and characters_dir.exists()


def get_characters_dir(vault_path: Path) -> Path:
    """Get the characters directory for a vault."""
    return vault_path / "characters"


def read_character(path: Path) -> str:
    """Read a character markdown file."""
    with open(path, "r") as f:
        return f.read()


def list_characters(vault_path: Path) -> list[Path]:
    """List all character files in a vault."""
    characters_dir = get_characters_dir(vault_path)
    if not characters_dir.exists():
        return []
    return sorted(characters_dir.glob("*.md"))


def make_title_box(title: str, padding: int = 2) -> str:
    """Create an ASCII box around a title."""
    inner_width = len(title) + padding * 2
    top = "┌" + "─" * inner_width + "┐"
    middle = "│" + " " * padding + title + " " * padding + "│"
    bottom = "└" + "─" * inner_width + "┘"
    return f"{top}\n{middle}\n{bottom}"


def make_section_header(section: str) -> str:
    """Create a section header with decorative lines."""
    return f"━━━ {section} ━━━"


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


def get_vault_name(vault_path: Path) -> str:
    """Get the name of a vault from its config."""
    vault_config = vault_path / "vault.yaml"
    if vault_config.exists():
        with open(vault_config, "r") as f:
            config = yaml.safe_load(f)
            return config.get("name", vault_path.name)
    return vault_path.name


def get_vault_stats(vault_path: Path) -> dict:
    """Get statistics about a vault."""
    characters = list_characters(vault_path)

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


def delete_character(path: Path) -> bool:
    """Delete a character file."""
    try:
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def discover_vaults(search_paths: list[Path] | None = None) -> list[Path]:
    """Find all valid vaults in common locations."""
    if search_paths is None:
        search_paths = [
            Path.home() / "Documents",
            Path.home() / "projects",
            Path.home() / "codex",
            Path.home(),
            Path.cwd(),
        ]

    vaults = []
    seen = set()

    for base_path in search_paths:
        if not base_path.exists():
            continue

        # Check if base_path itself is a vault
        if is_valid_vault(base_path) and base_path not in seen:
            vaults.append(base_path)
            seen.add(base_path)

        # Check immediate subdirectories for vault.yaml
        try:
            for item in base_path.iterdir():
                if item.is_dir() and item not in seen and is_valid_vault(item):
                    vaults.append(item)
                    seen.add(item)
        except PermissionError:
            continue

    return sorted(vaults, key=lambda p: p.name.lower())


def get_default_locations() -> list[Path]:
    """Get default locations for creating vaults."""
    locations = [
        Path.home() / "Documents",
        Path.home() / "projects",
        Path.home() / "codex",
    ]
    return [loc for loc in locations if loc.exists() or loc.parent.exists()]


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

def get_portrait_dir(vault_path: Path, slug: str) -> Path:
    """Get the portrait directory for a character slug."""
    return get_characters_dir(vault_path) / "images" / slug


def find_portrait(vault_path: Path, character_name: str, field_key: str = "portrait") -> Path | None:
    """Find an image file for a character field. Returns path or None."""
    slug = get_character_slug(character_name)
    portrait_dir = get_portrait_dir(vault_path, slug)
    if not portrait_dir.exists():
        return None
    for ext in PORTRAIT_EXTENSIONS:
        candidate = portrait_dir / f"{field_key}{ext}"
        if candidate.exists():
            return candidate
    return None


def save_portrait(vault_path: Path, character_name: str, source_path: str, field_key: str = "portrait") -> Path | None:
    """Copy an image into the character's image directory.

    Removes existing file for this field_key first. Returns new path or None on failure.
    """
    slug = get_character_slug(character_name)
    portrait_dir = get_portrait_dir(vault_path, slug)
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
    remove_portrait(vault_path, character_name, field_key=field_key)

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


def remove_portrait(vault_path: Path, character_name: str, field_key: str | None = None) -> bool:
    """Remove image files for a character.

    If field_key is None, removes ALL images in the slug directory (for character deletion).
    If field_key is given, removes only that field_key's files.
    Only rmdir's the directory if it's empty afterward.
    """
    slug = get_character_slug(character_name)
    portrait_dir = get_portrait_dir(vault_path, slug)
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


def rename_portrait_dir(vault_path: Path, old_name: str, new_name: str) -> bool:
    """Move portrait directory when a character is renamed."""
    old_slug = get_character_slug(old_name)
    new_slug = get_character_slug(new_name)
    if old_slug == new_slug:
        return True

    old_dir = get_portrait_dir(vault_path, old_slug)
    new_dir = get_portrait_dir(vault_path, new_slug)

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
