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

IMAGE_FIELD_TYPES = {FIELD_TYPE_IMAGE, FIELD_TYPE_MIMAGE}
VALID_FIELD_TYPES = {
    FIELD_TYPE_TEXT, FIELD_TYPE_MULTILINE, FIELD_TYPE_TAGS, FIELD_TYPE_NUMBER,
    FIELD_TYPE_IMAGE, FIELD_TYPE_MIMAGE,
}

# Default image dimensions
DEFAULT_IMAGE_WIDTH = 150
DEFAULT_IMAGE_HEIGHT = 150
DEFAULT_MIMAGE_WIDTH = 300
DEFAULT_MIMAGE_HEIGHT = 300

# Regex to match {key}, {key|type}, {key|type|w=N|h=N}, {key|type|required}, etc.
_FIELD_PLACEHOLDER = re.compile(r'\{(\w[\w|=]*)\}')


def _parse_field_placeholder(raw: str) -> dict | None:
    """Parse a field placeholder like 'name|text|required' or 'portrait|image|w=150|h=150|required'.

    Returns dict with key, field_type, image_width, image_height, required.
    """
    parts = raw.split("|")
    if not parts:
        return None

    key = parts[0]
    field_type = FIELD_TYPE_TEXT
    img_w = 0
    img_h = 0
    required = False

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
        elif part == "required":
            required = True

    return {"key": key, "field_type": field_type, "image_width": img_w, "image_height": img_h, "required": required}


@dataclass
class TemplateField:
    """A single field defined in a template."""
    key: str              # Internal key, e.g. "summary", "combat_style"
    display_name: str     # Label shown in UI, e.g. "Summary", "Combat Style"
    field_type: str       # One of VALID_FIELD_TYPES
    required: bool = False
    image_width: int = 0   # 0 = use default for type
    image_height: int = 0

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
description: Standard character template with all default fields
---
## Name
{name|required}
![portrait]
## Summary
{summary|multiline}
## Description
{description|multiline}
## Traits
{traits|multiline}
## History
{history|multiline}
## Relationships
{relationships|multiline}
## Tags
{tags|tags}
"""


def get_default_template() -> Template:
    """Return the built-in default template matching current hardcoded fields."""
    return Template(
        name="Default Character",
        author="Codex",
        version="1.0",
        description="Standard character template with all default fields",
        filename="default.md",
        fields=[
            TemplateField("name", "Name", FIELD_TYPE_TEXT, required=True),
            TemplateField("summary", "Summary", FIELD_TYPE_MULTILINE),
            TemplateField("description", "Description", FIELD_TYPE_MULTILINE),
            TemplateField("traits", "Traits", FIELD_TYPE_MULTILINE),
            TemplateField("history", "History", FIELD_TYPE_MULTILINE),
            TemplateField("relationships", "Relationships", FIELD_TYPE_MULTILINE),
            TemplateField("tags", "Tags", FIELD_TYPE_TAGS),
        ],
        portrait_position=1,
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

def discover_templates(vault_path: Path) -> list[Template]:
    """Find and parse all template .md files in vault/templates/."""
    templates_dir = vault_path / "templates"
    if not templates_dir.exists():
        return [get_default_template()]

    templates = []
    default_found = False

    for template_file in sorted(templates_dir.glob("*.md")):
        try:
            content = template_file.read_text(encoding="utf-8")
            parsed = parse_template(content, template_file.name)
            templates.append(parsed)
            if template_file.stem == "default":
                default_found = True
        except Exception as e:
            print(f"[ERROR] Failed to parse template {template_file}: {e}")

    if not default_found:
        templates.insert(0, get_default_template())

    # Sort: default first, then alphabetical
    templates.sort(key=lambda t: ("" if t.template_id == "default" else t.name.lower()))

    return templates if templates else [get_default_template()]


def save_template(vault_path: Path, template: Template) -> Path:
    """Write a template to vault/templates/{template_id}.md."""
    templates_dir = vault_path / "templates"
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


def ensure_default_template(vault_path: Path) -> None:
    """Create vault/templates/default.md if it doesn't exist."""
    templates_dir = vault_path / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    default_path = templates_dir / "default.md"
    if not default_path.exists():
        default_path.write_text(get_default_template_markdown(), encoding="utf-8")
