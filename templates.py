"""
Codex Template System
Template parsing, rendering, discovery, and conversion for dynamic character forms.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re
import yaml


# Field type constants
FIELD_TYPE_TEXT = "text"
FIELD_TYPE_MULTILINE = "multiline"
FIELD_TYPE_TAGS = "tags"
FIELD_TYPE_NUMBER = "number"
FIELD_TYPE_IMAGE = "image"
FIELD_TYPE_MIMAGE = "mimage"
FIELD_TYPE_LINK = "link"

IMAGE_FIELD_TYPES = {FIELD_TYPE_IMAGE, FIELD_TYPE_MIMAGE}
VALID_FIELD_TYPES = {
    FIELD_TYPE_TEXT, FIELD_TYPE_MULTILINE, FIELD_TYPE_TAGS, FIELD_TYPE_NUMBER,
    FIELD_TYPE_IMAGE, FIELD_TYPE_MIMAGE, FIELD_TYPE_LINK,
}

# Default image dimensions
DEFAULT_IMAGE_WIDTH = 150
DEFAULT_IMAGE_HEIGHT = 150
DEFAULT_MIMAGE_WIDTH = 300
DEFAULT_MIMAGE_HEIGHT = 300

# Regex to match {key}, {key|type}, {key|type|w=N|h=N}, {key|type|required}, etc.
_FIELD_PLACEHOLDER = re.compile(r'\{(\w[\w|=,]*)\}')


def _parse_field_placeholder(raw: str) -> dict | None:
    """Parse a field placeholder like 'name|text|required' or 'portrait|image|w=150|h=150|required'.

    Returns dict with key, field_type, image_width, image_height, required, link_targets.
    """
    parts = raw.split("|")
    if not parts:
        return None

    key = parts[0]
    field_type = FIELD_TYPE_TEXT
    img_w = 0
    img_h = 0
    required = False
    link_targets: list[str] = []

    for part in parts[1:]:
        if part in VALID_FIELD_TYPES:
            field_type = part
        elif part.startswith("w="):
            try:
                img_w = int(part[2:])
            except ValueError:
                pass
        elif part.startswith("h="):
            try:
                img_h = int(part[2:])
            except ValueError:
                pass
        elif part.startswith("target="):
            link_targets = [t.strip() for t in part[7:].split(",") if t.strip()]
        elif part == "required":
            required = True

    return {"key": key, "field_type": field_type, "image_width": img_w, "image_height": img_h,
            "required": required, "link_targets": link_targets}


@dataclass
class TemplateField:
    """A single field defined in a template."""
    key: str              # Internal key, e.g. "summary", "combat_style"
    display_name: str     # Label shown in UI, e.g. "Summary", "Combat Style"
    field_type: str       # One of VALID_FIELD_TYPES
    required: bool = False
    image_width: int = 0   # 0 = use default for type
    image_height: int = 0
    link_targets: list = field(default_factory=list)  # ["characters", "locations", etc.]

    @property
    def effective_image_width(self) -> int:
        if self.image_width > 0:
            return self.image_width
        if self.field_type == FIELD_TYPE_MIMAGE:
            return DEFAULT_MIMAGE_WIDTH
        return DEFAULT_IMAGE_WIDTH

    @property
    def effective_image_height(self) -> int:
        if self.image_height > 0:
            return self.image_height
        if self.field_type == FIELD_TYPE_MIMAGE:
            return DEFAULT_MIMAGE_HEIGHT
        return DEFAULT_IMAGE_HEIGHT


@dataclass
class Template:
    """A parsed character template."""
    name: str
    author: str = "Codex"
    version: str = "1.0"
    description: str = ""
    filename: str = ""
    fields: list[TemplateField] = field(default_factory=list)
    portrait_position: int = 0  # Insert portrait before this many non-name fields (0=after title, -1=none)

    @property
    def template_id(self) -> str:
        """Template identifier derived from filename stem."""
        return Path(self.filename).stem if self.filename else self.name.lower().replace(" ", "_")


# --- Default template ---

DEFAULT_TEMPLATE_MARKDOWN = """\
---
name: Default Character
author: Codex
version: 1.0
description: Standard character template
---

## Main Image
{showcase|mimage|w=350|h=250}

## Name
{name|required}

## Portrait
{portrait|image|w=150|h=150}

## Tags
{tags|tags}

## Summary
{summary}

## Description
{description|multiline}

## Traits
{traits|multiline}

## History
{history|multiline}
"""


def get_default_template() -> Template:
    """Return the built-in default template matching current hardcoded fields."""
    return Template(
        name="Default Character",
        author="Codex",
        version="1.0",
        description="Standard character template",
        filename="default.md",
        fields=[
            TemplateField("showcase", "Main Image", FIELD_TYPE_MIMAGE, image_width=350, image_height=250),
            TemplateField("name", "Name", FIELD_TYPE_TEXT, required=True),
            TemplateField("portrait", "Portrait", FIELD_TYPE_IMAGE, image_width=150, image_height=150),
            TemplateField("tags", "Tags", FIELD_TYPE_TAGS),
            TemplateField("summary", "Summary", FIELD_TYPE_TEXT),
            TemplateField("description", "Description", FIELD_TYPE_MULTILINE),
            TemplateField("traits", "Traits", FIELD_TYPE_MULTILINE),
            TemplateField("history", "History", FIELD_TYPE_MULTILINE),
        ],
    )


def get_default_template_markdown() -> str:
    """Return the raw markdown content for the default template file."""
    return DEFAULT_TEMPLATE_MARKDOWN


def template_has_image_fields(template: Template) -> bool:
    """Check if a template has any image or mimage fields."""
    return any(tf.field_type in IMAGE_FIELD_TYPES for tf in template.fields)


# --- Parsing ---

def _strip_frontmatter(markdown: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown.

    Returns (frontmatter_dict, body_without_frontmatter).
    If no frontmatter, returns ({}, original_markdown).
    """
    if not markdown.startswith("---"):
        return {}, markdown

    # Find closing ---
    end_idx = markdown.find("\n---", 3)
    if end_idx < 0:
        return {}, markdown

    frontmatter_str = markdown[3:end_idx].strip()
    body = markdown[end_idx + 4:].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        return {}, markdown

    return frontmatter, body


def parse_template(markdown: str, filename: str = "") -> Template:
    """Parse a template markdown file into a Template object.

    Template format:
    ---
    name: Template Name
    author: ...
    ---
    ## Name
    {name|required}
    ![portrait]
    ## Section Name
    {field_key|type}
    """
    frontmatter, body = _strip_frontmatter(markdown)

    fields = []
    current_section = None
    portrait_position = -1  # -1 = no portrait marker found
    field_count = 0  # count of all fields parsed so far

    for line in body.split("\n"):
        stripped = line.strip()

        # Track portrait marker position
        if stripped == "![portrait]":
            portrait_position = field_count
            continue

        # Section header → potential field label
        if stripped.startswith("## "):
            current_section = stripped[3:].strip()
            continue

        # Legacy: Title line with {name} placeholder (backward compat)
        if stripped.startswith("# ") and "{name}" in stripped:
            fields.append(TemplateField(
                key="name",
                display_name="Name",
                field_type=FIELD_TYPE_TEXT,
                required=True,
            ))
            field_count += 1
            current_section = None
            continue

        # Field placeholder
        match = _FIELD_PLACEHOLDER.search(stripped)
        if match:
            parsed = _parse_field_placeholder(match.group(1))
            if parsed is None:
                continue
            key = parsed["key"]
            field_type = parsed["field_type"]
            img_w = parsed["image_width"]
            img_h = parsed["image_height"]
            is_required = parsed["required"]
            targets = parsed.get("link_targets", [])

            # Image fields don't require a section header; derive display name from key
            if field_type in IMAGE_FIELD_TYPES:
                display = current_section or key.replace("_", " ").title()
                fields.append(TemplateField(
                    key=key,
                    display_name=display,
                    field_type=field_type,
                    required=is_required,
                    image_width=img_w,
                    image_height=img_h,
                ))
                field_count += 1
                current_section = None
            elif current_section:
                fields.append(TemplateField(
                    key=key,
                    display_name=current_section,
                    field_type=field_type,
                    required=is_required,
                    image_width=img_w,
                    image_height=img_h,
                    link_targets=targets,
                ))
                field_count += 1
                current_section = None

    # Ensure name field exists somewhere (don't force position)
    if not any(f.key == "name" for f in fields):
        fields.append(TemplateField("name", "Name", FIELD_TYPE_TEXT, required=True))

    return Template(
        name=frontmatter.get("name", Path(filename).stem if filename else "Unnamed"),
        author=frontmatter.get("author", "Unknown"),
        version=str(frontmatter.get("version", "1.0")),
        description=frontmatter.get("description", ""),
        filename=filename,
        fields=fields,
        portrait_position=portrait_position,
    )


# --- Conversion to FieldConfig ---

def template_fields_to_field_configs(template: Template) -> list:
    """Convert Template.fields to list of FieldConfig objects for modal rendering."""
    from ui.components import FieldConfig

    configs = []
    for tf in template.fields:
        # Image fields are managed in character view, not in create/edit modals
        if tf.field_type in IMAGE_FIELD_TYPES:
            continue
        # Link fields have their own rendering in the form
        if tf.field_type == FIELD_TYPE_LINK:
            continue
        req = "* " if tf.required else ""
        if tf.field_type == FIELD_TYPE_MULTILINE:
            label = f"{req}{tf.display_name}:"
            cfg = FieldConfig(
                name=label, key=tf.key,
                min_height=80, multiline=True, expandable=True,
                field_type=tf.field_type,
            )
        elif tf.field_type == FIELD_TYPE_TAGS:
            label = f"{req}{tf.display_name} (comma-separated):"
            cfg = FieldConfig(
                name=label, key=tf.key,
                min_height=40, multiline=True, expandable=True,
                field_type=tf.field_type,
            )
        elif tf.field_type == FIELD_TYPE_NUMBER:
            label = f"{req}{tf.display_name}:"
            cfg = FieldConfig(
                name=label, key=tf.key,
                min_height=40, multiline=False, expandable=False,
                field_type=tf.field_type,
            )
        else:  # text
            label = f"{req}{tf.display_name}:"
            cfg = FieldConfig(
                name=label, key=tf.key,
                min_height=40, multiline=True, expandable=True,
                field_type=tf.field_type,
            )
        configs.append(cfg)

    return configs


# --- Rendering ---

def render_character_from_template(template: Template, form_data: dict) -> str:
    """Render a character markdown file from template + form data.

    Produces markdown with YAML frontmatter containing template reference.
    Portrait marker is placed according to template.portrait_position.
    """
    lines = [
        "---",
        f"template: {template.template_id}",
        "---",
        "",
    ]

    # Only use legacy portrait marker when template has no image fields
    has_images = template_has_image_fields(template)
    portrait_pos = template.portrait_position
    portrait_added = False
    field_idx = 0

    for tf in template.fields:
        # Skip image fields — they don't produce markdown sections
        if tf.field_type in IMAGE_FIELD_TYPES:
            continue

        # Insert legacy portrait before this field if position matches
        if not has_images and not portrait_added and portrait_pos >= 0 and field_idx == portrait_pos:
            lines.append("![portrait]")
            lines.append("")
            portrait_added = True

        value = form_data.get(tf.key, "")
        lines.append(f"## {tf.display_name}")
        lines.append(value)
        lines.append("")
        field_idx += 1

    # Portrait at end if not yet placed (legacy mode only)
    if not has_images and not portrait_added and portrait_pos >= 0:
        lines.append("![portrait]")
        lines.append("")

    return "\n".join(lines)


# --- Discovery & persistence ---

def discover_templates(world_path: Path, section: str = "characters") -> list[Template]:
    """Find and parse all template .md files for a section."""
    templates = []
    default_found = False
    seen_files: set[str] = set()

    # Look in section-specific directory first
    section_dir = world_path / "templates" / section
    if section_dir.exists():
        for template_file in sorted(section_dir.glob("*.md")):
            try:
                content = template_file.read_text(encoding="utf-8")
                parsed = parse_template(content, template_file.name)
                templates.append(parsed)
                seen_files.add(template_file.name)
                if template_file.stem == "default":
                    default_found = True
            except Exception as e:
                print(f"[ERROR] Failed to parse template {template_file}: {e}")

    # For characters, also check legacy templates/ root (backward compat)
    if section == "characters":
        legacy_dir = world_path / "templates"
        if legacy_dir.exists():
            for template_file in sorted(legacy_dir.glob("*.md")):
                if template_file.name in seen_files:
                    continue
                try:
                    content = template_file.read_text(encoding="utf-8")
                    parsed = parse_template(content, template_file.name)
                    templates.append(parsed)
                    if template_file.stem == "default":
                        default_found = True
                except Exception as e:
                    print(f"[ERROR] Failed to parse template {template_file}: {e}")

    default_template = get_section_default_template(section)

    if not default_found:
        templates.insert(0, default_template)

    # Sort: default first, then alphabetical
    templates.sort(key=lambda t: ("" if t.template_id == "default" else t.name.lower()))

    return templates if templates else [default_template]


def save_template(world_path: Path, template: Template) -> Path:
    """Write a template to world/templates/{template_id}.md."""
    templates_dir = world_path / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Build markdown
    lines = [
        "---",
        f"name: {template.name}",
        f"author: {template.author}",
        f"version: {template.version}",
        f"description: {template.description}",
        "---",
        "",
    ]

    has_images = template_has_image_fields(template)
    portrait_pos = template.portrait_position
    portrait_added = False
    field_idx = 0

    for tf in template.fields:
        # Insert legacy portrait at correct position (only when no image fields)
        if not has_images and not portrait_added and portrait_pos >= 0 and field_idx == portrait_pos:
            lines.append("![portrait]")
            lines.append("")
            portrait_added = True

        req_suffix = "|required" if tf.required else ""

        # Image fields: write placeholder with dimensions
        if tf.field_type in IMAGE_FIELD_TYPES:
            dim_parts = f"{{{tf.key}|{tf.field_type}"
            if tf.image_width > 0:
                dim_parts += f"|w={tf.image_width}"
            if tf.image_height > 0:
                dim_parts += f"|h={tf.image_height}"
            dim_parts += f"{req_suffix}}}"
            lines.append(f"## {tf.display_name}")
            lines.append(dim_parts)
            lines.append("")
            field_idx += 1
            continue

        # Link fields: write placeholder with target
        if tf.field_type == FIELD_TYPE_LINK:
            target_str = ",".join(tf.link_targets) if tf.link_targets else ""
            placeholder = f"{{{tf.key}|link"
            if target_str:
                placeholder += f"|target={target_str}"
            placeholder += f"{req_suffix}}}"
            lines.append(f"## {tf.display_name}")
            lines.append(placeholder)
            lines.append("")
            field_idx += 1
            continue

        lines.append(f"## {tf.display_name}")
        if tf.field_type == FIELD_TYPE_TEXT and not req_suffix:
            lines.append(f"{{{tf.key}}}")
        elif tf.field_type == FIELD_TYPE_TEXT:
            lines.append(f"{{{tf.key}{req_suffix}}}")
        else:
            lines.append(f"{{{tf.key}|{tf.field_type}{req_suffix}}}")
        lines.append("")
        field_idx += 1

    # Legacy portrait at end if not yet placed
    if not has_images and not portrait_added and portrait_pos >= 0:
        lines.append("![portrait]")
        lines.append("")

    content = "\n".join(lines)
    filepath = templates_dir / f"{template.template_id}.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


def _migrate_template_links(existing_path: Path, reference_markdown: str) -> bool:
    """Upgrade multiline fields to link fields based on reference template.

    Scans the existing template for fields that the reference defines as 'link',
    and rewrites them in-place. Also adds any missing link fields from the
    reference. Preserves all other user customizations (extra fields, image
    fields, ordering). Only touches Codex-authored templates with a lower
    version.

    Returns True if the file was modified.
    """
    import re
    try:
        content = existing_path.read_text(encoding="utf-8")
    except Exception:
        return False
    old_meta, _ = _strip_frontmatter(content)
    new_meta, _ = _strip_frontmatter(reference_markdown)
    if old_meta.get("author", "") != "Codex":
        return False
    old_ver = str(old_meta.get("version", "0"))
    new_ver = str(new_meta.get("version", "0"))
    if old_ver >= new_ver:
        return False

    # Build map of link fields from reference: key -> "key|link|target=..."
    ref_template = parse_template(reference_markdown, "ref")
    link_fields: dict[str, TemplateField] = {}
    for tf in ref_template.fields:
        if tf.field_type == FIELD_TYPE_LINK:
            link_fields[tf.key] = tf

    if not link_fields:
        # Just bump version
        content = re.sub(r'(?m)^version:\s*\S+', f'version: {new_ver}', content)
        existing_path.write_text(content, encoding="utf-8")
        return True

    modified = content
    existing_keys = set()

    # Upgrade existing fields: {key|multiline} -> {key|link|target=...}
    for key, tf in link_fields.items():
        targets_str = ",".join(tf.link_targets)
        # Match {key}, {key|text}, {key|multiline}, etc.
        pattern = re.compile(r'\{' + re.escape(key) + r'(\|[^}]*)?\}')
        replacement = '{' + key + '|link|target=' + targets_str + '}'
        new_modified = pattern.sub(replacement, modified)
        if new_modified != modified:
            existing_keys.add(key)
            modified = new_modified

    # Add missing link fields before ## Tags (or at end)
    for key, tf in link_fields.items():
        if key not in existing_keys:
            targets_str = ",".join(tf.link_targets)
            new_section = f"## {tf.display_name}\n{{{key}|link|target={targets_str}}}"
            # Insert before ## Tags if it exists, otherwise append
            if "## Tags" in modified:
                modified = modified.replace("## Tags", new_section + "\n## Tags")
            else:
                modified = modified.rstrip() + "\n" + new_section + "\n"

    # Bump version
    modified = re.sub(r'(?m)^version:\s*\S+', f'version: {new_ver}', modified)

    existing_path.write_text(modified, encoding="utf-8")
    return True


def ensure_default_template(world_path: Path) -> None:
    """Create or update world/templates/default.md."""
    templates_dir = world_path / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    default_path = templates_dir / "default.md"
    new_md = get_default_template_markdown()
    if not default_path.exists():
        default_path.write_text(new_md, encoding="utf-8")
    else:
        _migrate_template_links(default_path, new_md)


# --- Section-specific default templates ---

LOCATION_DEFAULT_TEMPLATE = """\
---
name: Default Location
author: Codex
version: 1.1
description: Standard location template
---
## Name
{name|required}
![portrait]
## Summary
{summary|multiline}
## Description
{description|multiline}
## Geography
{geography|multiline}
## Notable Features
{notable_features|multiline}
## Notable Characters
{notable_characters|link|target=characters}
## Connected Locations
{connected_locations|link|target=locations}
## Historical Events
{historical_events|link|target=timeline}
## Related
{location_related|link|target=codex}
## Tags
{tags|tags}
"""

TIMELINE_DEFAULT_TEMPLATE = """\
---
name: Default Event
author: Codex
version: 1.1
description: Timeline event template
---
## Image
{image|image|w=300|h=200}
## Name
{name|required}
## Date
{date|number|required}
## Era
{era}
## Tags
{tags|tags}
## Description
{description|multiline}
## Characters Involved
{characters_involved|link|target=characters}
## Locations
{locations|link|target=locations}
## Related
{related|link|target=codex,timeline}
## Consequences
{consequences|multiline}
"""

CODEX_DEFAULT_TEMPLATE = """\
---
name: Default Entry
author: Codex
version: 1.1
description: General-purpose codex entry
---
## Name
{name|required}
![portrait]
## Summary
{summary|multiline}
## Description
{description|multiline}
## Notable Members
{notable_members|link|target=characters}
## Locations
{codex_locations|link|target=locations}
## Key Events
{codex_events|link|target=timeline}
## Related
{codex_related|link|target=codex}
## Tags
{tags|tags}
"""

CODEX_TEMPLATES = {
    "item": """\
---
name: Item
author: Codex
version: 1.1
description: Items, weapons, and artifacts
---
## Name
{name|required}
## Type
{type}
## Summary
{summary|multiline}
## Description
{description|multiline}
## Properties
{properties|multiline}
## History
{history|multiline}
## Tags
{tags|tags}
""",
    "faction": """\
---
name: Faction
author: Codex
version: 1.1
description: Organizations, guilds, and groups
---
## Name
{name|required}
## Summary
{summary|multiline}
## Goals
{goals|multiline}
## Structure
{structure|multiline}
## Notable Members
{notable_members|link|target=characters}
## Headquarters
{headquarters|link|target=locations}
## Key Events
{faction_events|link|target=timeline}
## History
{history|multiline}
## Related
{faction_related|link|target=codex}
## Tags
{tags|tags}
""",
    "race": """\
---
name: Race
author: Codex
version: 1.1
description: Species and races
---
## Name
{name|required}
## Summary
{summary|multiline}
## Physical Traits
{physical_traits|multiline}
## Culture
{culture|multiline}
## Abilities
{abilities|multiline}
## History
{history|multiline}
## Tags
{tags|tags}
""",
    "power_system": """\
---
name: Power System
author: Codex
version: 1.1
description: Magic systems, technology, and powers
---
## Name
{name|required}
## Summary
{summary|multiline}
## Rules
{rules|multiline}
## Limitations
{limitations|multiline}
## Practitioners
{practitioners|multiline}
## History
{history|multiline}
## Tags
{tags|tags}
""",
    "creature": """\
---
name: Creature
author: Codex
version: 1.1
description: Creatures, beasts, and monsters
---
## Name
{name|required}
## Summary
{summary|multiline}
## Appearance
{appearance|multiline}
## Behavior
{behavior|multiline}
## Habitat
{habitat|multiline}
## Abilities
{abilities|multiline}
## Tags
{tags|tags}
""",
    "culture": """\
---
name: Culture
author: Codex
version: 1.1
description: Cultures, traditions, and customs
---
## Name
{name|required}
## Summary
{summary|multiline}
## Values
{values|multiline}
## Traditions
{traditions|multiline}
## Social Structure
{social_structure|multiline}
## History
{history|multiline}
## Tags
{tags|tags}
""",
    "language": """\
---
name: Language
author: Codex
version: 1.1
description: Languages and writing systems
---
## Name
{name|required}
## Summary
{summary|multiline}
## Grammar
{grammar|multiline}
## Vocabulary
{vocabulary|multiline}
## Writing System
{writing_system|multiline}
## Speakers
{speakers|multiline}
## Tags
{tags|tags}
""",
}

# Map section -> default template markdown
SECTION_DEFAULT_TEMPLATES = {
    "characters": DEFAULT_TEMPLATE_MARKDOWN,
    "locations": LOCATION_DEFAULT_TEMPLATE,
    "timeline": TIMELINE_DEFAULT_TEMPLATE,
    "codex": CODEX_DEFAULT_TEMPLATE,
}


def get_section_default_template(section: str = "characters") -> Template:
    """Return the built-in default template for a section."""
    if section == "characters":
        return get_default_template()
    md = SECTION_DEFAULT_TEMPLATES.get(section, CODEX_DEFAULT_TEMPLATE)
    return parse_template(md, "default.md")


def ensure_section_templates(world_path: Path, section: str) -> None:
    """Create or update default template files for a section."""
    # Characters use the legacy root templates/default.md via ensure_default_template
    if section == "characters":
        ensure_default_template(world_path)
        return

    templates_dir = world_path / "templates" / section
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Default template
    default_path = templates_dir / "default.md"
    md = SECTION_DEFAULT_TEMPLATES.get(section)
    if md:
        if not default_path.exists():
            default_path.write_text(md, encoding="utf-8")
        else:
            _migrate_template_links(default_path, md)

    # Codex section has additional templates
    if section == "codex":
        for template_id, tmpl_md in CODEX_TEMPLATES.items():
            path = templates_dir / f"{template_id}.md"
            if not path.exists():
                path.write_text(tmpl_md, encoding="utf-8")
            else:
                _migrate_template_links(path, tmpl_md)
