# Codex

**Worldbuilding Companion**

A focused, aesthetic tool for creating and managing characters — built for writers, roleplayers, and worldbuilders.

Codex gives you a dedicated space to build characters with customizable templates, image support, and markdown-based storage that plays nicely with tools like Obsidian. No electron, no web browser — just a fast native window.

[Screenshots coming soon]

---

## Features

- **Customizable templates** — Define your own character sheets with any combination of fields
- **Dynamic field types** — Text, multiline, number, tags, portrait images, and full-size main images
- **Template editor** — Create and modify templates directly in the app
- **Image support** — Attach portraits and images to characters with configurable dimensions
- **World system** — Organize characters into separate worlds (campaigns, projects, settings)
- **Markdown storage** — Characters are saved as `.md` files with YAML frontmatter (Obsidian-compatible)
- **Search and sort** — Filter characters by name or tag, sort by name or date
- **Duplicate characters** — One-click duplication with all fields and images copied
- **Vim-style navigation** — `j`/`k`/`h`/`l` for keyboard-driven workflows
- **Keyboard shortcuts** — Full clipboard support, text selection, and a `?` help overlay
- **Recent worlds** — Quick access to your last-opened worlds
- **Open in file manager** — Jump to your world folder from the app
- **JetBrains Mono** — Clean monospace font loaded at native sizes for crisp rendering

---

## Installation

```bash
# Clone the repo
git clone https://github.com/username/codex.git
cd codex

# Create virtual environment
python -m venv codex
source codex/bin/activate

# Install dependencies
pip install raylib PyYAML

# Run
python main.py
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python  | 3.10+   | Runtime |
| raylib  | 5.5+    | GUI rendering |
| PyYAML  | 6.0+    | Template and world config parsing |

**Optional:** JetBrains Mono or JetBrainsMono Nerd Font installed on your system for the best text rendering. Falls back to Fira Code, Source Code Pro, Ubuntu Mono, Hack, or raylib's default font.

---

## Usage

### Creating a World

A world is a folder that holds your characters, templates, and images. When you first launch Codex, click **Create World** and choose a name and location. The world structure is created automatically.

### Creating Characters

With a world open, click **New Character**. Fill in the fields defined by your active template and click **Create**. Characters are saved as markdown files in the `characters/` directory.

### Using Templates

Templates define what fields appear on a character sheet. The default template includes Name, Summary, Description, Traits, History, Relationships, and Tags — but you can create your own.

Open the **Templates** editor from the world actions panel to add, remove, reorder fields, and change field types. Templates are saved as markdown files in `templates/`.

### Adding Images

In the character view, click the image placeholder to attach a portrait or image. Images are stored in `characters/images/{character}/` alongside your character files.

---

## Keyboard Shortcuts

### Navigation

| Key | Action |
|-----|--------|
| `j` / `Down` | Move down in list |
| `k` / `Up` | Move up in list |
| `h` / `l` | Switch panel focus |
| `Enter` | Select / Open |
| `Escape` | Go back / Close modal |
| `/` | Search characters |

### Text Editing

| Key | Action |
|-----|--------|
| `Ctrl+A` | Select all |
| `Ctrl+C` | Copy |
| `Ctrl+X` | Cut |
| `Ctrl+V` | Paste |
| `Shift+Left/Right` | Select text |

### Other

| Key | Action |
|-----|--------|
| `?` | Show keyboard shortcuts help |

---

## Templates

Templates are markdown files with YAML frontmatter and field placeholders.

### Example Template

```markdown
---
name: Fantasy Character
author: Your Name
version: 1.0
description: Template for fantasy RPG characters
---
## Name
{name|required}
![portrait]
## Class
{class|text}
## Summary
{summary|multiline}
## Combat Style
{combat_style|multiline}
## Inventory
{inventory|tags}
```

### Field Types

| Type | Syntax | Description |
|------|--------|-------------|
| `text` | `{key}` or `{key\|text}` | Single-line text input |
| `multiline` | `{key\|multiline}` | Multi-line text area |
| `tags` | `{key\|tags}` | Comma-separated tag list |
| `number` | `{key\|number}` | Numeric input |
| `image` | `{key\|image}` | Inline image field |
| `mimage` | `{key\|mimage}` | Large main image (one per template) |

### Modifiers

- `required` — Field must be filled before saving: `{name|required}`, `{bio|multiline|required}`
- `w=N`, `h=N` — Custom image dimensions: `{avatar|image|w=200|h=200}`
- `![portrait]` — Legacy portrait marker, placed between fields to control portrait position

---

## World Structure

```
my-world/
├── world.yaml              # World name and metadata
├── templates/
│   ├── default.md           # Default character template
│   └── custom_template.md   # Your custom templates
└── characters/
    ├── elena_blackwood.md   # Character file (markdown)
    ├── ryn_ashford.md
    ├── images/
    │   ├── elena_blackwood/
    │   │   └── portrait.png
    │   └── ryn_ashford/
    │       ├── portrait.jpg
    │       └── reference.png
    └── ...
```

Characters are plain markdown files. You can edit them in any text editor, and they'll sync with tools like Obsidian, Git, or Syncthing.

---

## Configuration

Codex stores user settings at `~/.config/codex/config.json`. Currently this tracks your recently opened worlds. No telemetry, no accounts, no cloud — your data stays on your machine.

---

## Roadmap

Planned for future versions:

- **Sections** — Locations, timelines, and codex sections beyond characters
- **Map view** — Visual map with pinned locations
- **Relationship graph** — Visual connections between characters
- **Export** — PDF, HTML, and other export formats

---

## Contributing

Contributions are welcome. If you find a bug or have a feature idea, open an issue on the [issues page](https://github.com/username/codex/issues).

---

## License

[License TBD]

---

## Credits

- Built with [Raylib](https://www.raylib.com/) via [raylib-python-cffi](https://github.com/electronstudio/raylib-python-cffi)
- Font: [JetBrains Mono](https://www.jetbrains.com/lp/mono/)
- Character data stored as Markdown + YAML
