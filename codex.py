from re import escape
from textual import content
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Vertical, VerticalScroll
from pathlib import Path
import json
from textual.widgets import Input
from textual.screen import ModalScreen

# Bindings
BINDINGS = [("escape", "cancel", "Cancel")]

def action_cancel(self) -> None:
    self.app.pop_screen()

# =======================================================================================
#
#                           Vault + Character Creation v0.1
#
# =======================================================================================

def create_vault(path: str) -> None:
    vault_path = Path(path).expanduser().resolve()
    vault_path.mkdir(parents=True, exist_ok=True)

    (vault_path / "characters").mkdir(exist_ok=True)
    (vault_path / "templates").mkdir(exist_ok=True)
    (vault_path / "metadata").mkdir(exist_ok=True)

    vault_yaml = vault_path / "vault.yaml"
    if not vault_yaml.exists():
        vault_yaml.write_text("name: My Codex Vault\nversion: 1\n", encoding="utf-8")

    relationships_json = vault_path / "metadata" / "relationships.json"
    if not relationships_json.exists():
        relationships_json.write_text(
            json.dumps({"relationships": []}, indent=2),
            encoding="utf-8",
        )

def save_character(
    vault_path: str,
    name: str,
    summary: str = "",
    description: str = "",
    traits: str = "",
    history: str = "",
    relationships: str = "",
) -> Path:
    vault = Path(vault_path).expanduser().resolve()
    characters_dir = vault / "characters"
    characters_dir.mkdir(exist_ok=True)
    slug = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")
    file_path = characters_dir / f"{slug}.md"
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
    """
    file_path.write_text(content, encoding="utf-8")
    return file_path

def is_valid_vault(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False

    if not (path / "vault.yaml").exists():
        return False
    if not (path / "characters").exists():
        return False

    return True

def get_characters_dir(vault_path: Path) -> Path:
    return vault_path / "characters"

def read_character(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "Character file not found."
    return path.read_text(encoding="utf-8")

def list_characters(vault_path: Path) -> list[Path]:
    characters_dir = get_characters_dir(vault_path)

    if not characters_dir.exists() or not characters_dir.is_dir():
        return []

    return sorted(
        file for file in characters_dir.iterdir()
        if file.is_file() and file.suffix.lower() == ".md"
    )

def make_title_box(title: str, padding: int = 2) -> str:
    """
    Create an ASCII box around the title.
    
    ╔══════════════════╗
    ║   Character Name ║
    ╚══════════════════╝
    """
    inner_width = len(title) + (padding *2)

    top = "╔" + "═" * inner_width + "╗"
    middle = "║" + " " * padding + title + " " * padding + "║"
    bottom = "╚" + "═" * inner_width + "╝"

    return "\n".join([top, middle, bottom])

def make_section_header(section: str) -> str:
    """
    Create a simple underlined section header.

    ─── Summary ───
    """
    decoration = "─" * 3
    return f"{decoration} {section} {decoration}"

def render_character(markdown: str) -> str:
    """
    Transform character markdown into ASCII-formatted display text.

    Handles;
    - # Title -> boxed title block
    - ## Section -> underlined section header
    - Regular text -> preserved with clean spacing
    """
    lines = markdown.strip().split("\n")
    output = []

    for line in lines:
        stripped = line.strip()


        # Main Title: # Name
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            output.append(make_title_box(title))
            output.append("") # blank line after title

        # Section header: ## Section
        elif stripped.startswith("## "):
            section = stripped[3:].strip()
            output.append("") # blank line before section
            output.append(make_section_header(section))

        # Regular content
        else:
            output.append(line)

    return "\n".join(output)

def parse_character(markdown: str) -> dict[str, str]:
    """
    Parse character markdown into a dictionary of sections.

    Returns dict with keys: name, summary, description, traits, history, relationships
    """

    sections = {
        "name": "",
        "summary": "",
        "description": "",
        "traits": "",
        "history": "",
        "relationships": "",
    }

    current_section = None
    content_lines = []

    for line in markdown.split("\n"):
        stripped = line.strip()

        # Main title
        if stripped.startswith("# ") and not stripped.startswith("## "):
            # Save previous section if any
            if current_section and content_lines:
                sections[current_section] = "\n".join(content_lines).strip()
            sections["name"] = stripped[2:].strip()
            current_section = None
            content_lines = []

        # Section header
        elif stripped.startswith("## "):
            # Save previous section
            if current_section and content_lines:
                sections[current_section] = "\n".join(content_lines).strip()

            section_name = stripped[3:].strip().lower()
            if section_name in sections:
                current_section =  section_name
                content_lines = []
            else:
                current_section = None
                content_lines = []

        # Content line
        elif current_section:
            content_lines.append(line)

    if current_section and content_lines:
        sections[current_section] = "\n".join(content_lines).strip()

    return sections

def get_vault_name(vault_path: Path) -> str:
    """Read vault name from vault.yaml"""
    yaml_path = vault_path / "vault.yaml"
    if not yaml_path.exists():
        return "Unknown Vault"

    content = yaml_path.read_text(encoding="utf-8")
    for line in content.split("\n"):
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()

    return "Unknown Vault"

def get_vault_stats(vault_path: Path) -> dict:
    """Gather stats about the vault"""
    characters = list_characters(vault_path)

    stats = {
        "name": get_vault_name(vault_path),
        "character_count": len(characters),
        "recent": None,
        "empty_sections": 0,
    }

    if not characters:
        return stats

    # Find most recently modified
    most_recent = max(characters, key=lambda p: p.stat().st_mtime)
    stats["recent"] = most_recent.stem.replace("_", " ").title()

    # Count characters with empty sections
    for char_path in characters:
        raw = read_character(char_path)
        data = parse_character(raw)
        # Check if any section (other than name) is empty
        for key in ["summary", "description", "traits", "history", "relationships"]:
            if not data[key]:
                stats["empty_sections"] += 1
                break # Count each character only once

    return stats
# =======================================================================================
#
#                                    Vault Screen
#
# =======================================================================================

class CreateVaultScreen(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Static("Create Vault")
        yield Input(
            placeholder="Vault path (e.g. ./my_vault)",
            id="vault_path",
        )
        yield Button("Create", id="confirm")
        yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()

        elif event.button.id == "confirm":
            path = self.query_one("#vault_path", Input).value.strip()
            if path:
                vault_path = Path(path).expanduser().resolve()
                create_vault(vault_path)

                self.app.active_vault = vault_path
                self.app.update_vault_status()

                self.dismiss()
                self.app.notify("Vault created and set as active")

    def action_cancel(self) -> None:
        self.dismiss()

class OpenVaultScreen(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Static("Open Existing Vault")

        yield Input(
            placeholder="Path to existing vault",
            id="vault_path",
        )

        yield Button("Open", id="confirm")
        yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()

        elif event.button.id == "confirm":
            raw_path = self.query_one("#vault_path", Input).value.strip()

            if not raw_path:
                self.app.notify("Path is required", severity="error")
                return

            vault_path = Path(raw_path).expanduser().resolve()

            if not is_valid_vault(vault_path):
                self.app.notify(
                    "Invalid vault (missing vault.yaml or characters/)", severity="error",
                )
                return


        self.app.active_vault = vault_path

        # Update UI only if widget exists
        try:
            self.app.update_vault_status()
        except Exception as e:
            self.app.notify(f"Vault opened (UI warning: {e})", severity="warning")

        self.dismiss()
        self.app.notify("Vault opened")

# =======================================================================================
#
#                                 Character Screen
#
# =======================================================================================

class ListCharactersScreen(ModalScreen):
    BINDINGS = [("escape", "cancel", "Close")]

    def compose(self) -> ComposeResult:
        yield Static("Characters in Active Vault", id="title")
        yield Static("", id="list")
        yield Button("Close", id="close")

    def on_mount(self) -> None:
        list_widget = self.query_one("#list", Static)

        vault = self.app.active_vault
        if not vault:
            list_widget.update("No active vault selected.")
            return

        characters = list_characters(vault)
        if not characters:
            list_widget.update("No characters found.")
            return

        # Clear placeholder text
        list_widget.update("")

        self.character_map: dict[str, Path] = {}

        for idx, path in enumerate(characters):
            name = path.stem.replace("_", " ").title()
            button_id = f"char_{idx}"

            self.character_map[button_id] = path

            self.mount(
                Button(name, id=button_id),
                after=list_widget,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()
            return

        if event.button.id in self.character_map:
            character_path = self.character_map[event.button.id]
            self.app.push_screen(ViewCharacterScreen(character_path))

    def action_cancel(self) -> None:
        self.dismiss()

class ViewCharacterScreen(ModalScreen):
    BINDINGS = [("escape", "cancel", "Close")]

    def __init__(self, character_path: Path):
        super().__init__()
        self.character_path = character_path

    def compose(self) -> ComposeResult:
        yield Static("View Character", id="title")
        yield VerticalScroll(
            Static("", id="content"),
            id="scroll",
        )
        yield Button("Edit", id="edit")
        yield Button("Close", id="close")

    def on_mount(self) -> None:
        content = self.query_one("#content", Static)
        raw_text = read_character(self.character_path)
        rendered = render_character(raw_text)
        content.update(rendered)

    def _on_screen_resume(self) -> None:
        # Re-render content when returning from edit screen
        content = self.query_one("#content", Static)
        raw_text = read_character(self.character_path)
        rendered = render_character(raw_text)
        content.update(rendered)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()
        elif event.button.id == "edit":
            self.app.push_screen(EditCharacterScreen(self.character_path))

    def action_cancel(self) -> None:
        self.dismiss()

class EditCharacterScreen(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, character_path: Path):
        super().__init__()
        self.character_path = character_path

    def compose(self) -> ComposeResult:
        yield Static("Edit Character", id="title")
        yield VerticalScroll(
            Static("Name *", classes="field-label"),
            Input(placeholder="Character name", id="name"),
            Static("Summary", classes="field-label"),
            Input(placeholder="A brief one-liner", id="summary"),
            Static("Description", classes="field-label"),
            Input(placeholder="Physical appearance, personality...", id="description"),
            Static("Traits", classes="field-label"),
            Input(placeholder="Key traits, quirks, abilities...", id="traits"),
            Static("History", classes="field-label"),
            Input(placeholder="Backstory, origin, major events...", id="history"),
            Static("Relationships", classes="field-label"),
            Input(placeholder="Connections to other characters...", id="relationships"),
            id="form-scroll",
        )
        yield Button("Save", id="save")
        yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        # Load existing data and fill the fields
        raw_text = read_character(self.character_path)
        data = parse_character(raw_text)

        self.query_one("#name", Input).value = data["name"]
        self.query_one("#summary", Input).value = data["summary"]
        self.query_one("#description", Input).value = data["description"]
        self.query_one("#traits", Input).value = data["traits"]
        self.query_one("#history", Input).value = data["history"]
        self.query_one("#relationships", Input).value = data["relationships"]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()
        elif event.button.id == "save":
            name = self.query_one("#name", Input).value.strip()
            if not name:
                self.app.notify("Name is required", severity="error")
                return
            summary = self.query_one("#summary", Input).value.strip()
            description = self.query_one("#description", Input).value.strip()
            traits = self.query_one("#traits", Input).value.strip()
            history = self.query_one("#history", Input).value.strip()
            relationships = self.query_one("#relationships", Input).value.strip()

            # Write directly to the existing file
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
            """
            self.character_path.write_text(content, encoding="utf-8")
            self.dismiss()
            self.app.notify(f"Character '{name}' saved")

    def action_cancel(self) -> None:
        self.dismiss()

class DashboardScreen(ModalScreen):
    BINDINGS = [("escape", "cancel", "Close")]

    def compose(self) -> ComposeResult:
        yield Static("", id="dashboard-content")
        yield Button("Close", id="close")

    def on_mount(self) -> None:
        content = self.query_one("#dashboard-content", Static)

        if not self.app.active_vault:
            content.update("No active_vault.")
            return
        
        stats = get_vault_stats(self.app.active_vault)

        # Build the dashboard display
        name_box = make_title_box(stats["name"])
        
        recent = stats["recent"] or "None yet"
        incomplete = stats["empty_sections"]
        
        display = f"""{name_box}

─── Stats ───

  Characters:  {stats["character_count"]}
  Recently Modified:  {recent}
  Incomplete Profiles:  {incomplete}

"""
        content.update(display)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()

    def action_cancel(self) -> None:
        self.dismiss()

class CreateCharacterScreen(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Static("Create Character", id="title")
        yield VerticalScroll(
            Static("Name *", classes="field-label"),
            Input(placeholder="Character name", id="name"),
            Static("Summary", classes="field-label"),
            Input(placeholder="A brief one-liner", id="summary"),
            Static("Description", classes="field-label"),
            Input(placeholder="Physical appearance, personality...", id="description"),
            Static("Traits", classes="field-label"),
            Input(placeholder="Key traits, quirks, abilities...", id="traits"),
            Static("History", classes="field-label"),
            Input(placeholder="Backstory, origin, major events...", id="history"),
            Static("Relationships", classes="field-label"),
            Input(placeholder="Connections to other characters...", id="relationships"),
            id="form-scroll",
        )
        yield Button("Create", id="confirm")
        yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()
        elif event.button.id == "confirm":
            name = self.query_one("#name", Input).value.strip()
            if not name:
                self.app.notify("Name is required", severity="error")
                return
            if not self.app.active_vault:
                self.app.notify("No active vault selected", severity="error")
                return

            # Gather all fields
            summary = self.query_one("#summary", Input).value.strip()
            description = self.query_one("#description", Input).value.strip()
            traits = self.query_one("#traits", Input).value.strip()
            history = self.query_one("#history", Input).value.strip()
            relationships = self.query_one("#relationships", Input).value.strip()
            
            save_character(
                self.app.active_vault,
                name,
                summary,
                description,
                traits,
                history,
                relationships,
            )
            self.dismiss()
            self.app.notify(f"Character '{name}' created")
    
    def action_cancel(self) -> None:
        self.dismiss()

# =======================================================================================
#
#                             Codex Application + UI v0.1
#
# =======================================================================================

class CodexApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #menu {
        width: 50;
    }

    Button {
       width: 100%;
    }
    #form-scroll {
        height: 20;
        border: solid green;
        padding: 1;
    }
    .field-label {
        margin-top: 1;
        color: $text-muted;
    }
    """

    def update_vault_status(self) -> None:
        status = "None"
        if self.active_vault:
            status = str(self.active_vault)
        self.query_one("#vault_status", Static).update(f"Active Vault: {status}")

    def on_mount(self) -> None:
        self.active_vault: Path | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Welcome to Codex", id="title"),
            Static("Active Vault: None", id="vault_status"),
            Button("Open Existing Vault", id="open_vault"),
            Button("Create Vault", id="create_vault", classes="menu-button"),
            Button("Dashboard", id="dashboard"),
            Button("Create Character", id="create_character", classes="menu-button"),
            Button("List Characters", id="list_characters"),
            Button("Quit", id="quit", classes="menu-button"),
            id="menu",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.exit()

        elif event.button.id == "create_vault":
            self.push_screen(CreateVaultScreen())

        elif event.button.id == "open_vault":
            self.push_screen(OpenVaultScreen())

        elif event.button.id == "create_character":
            if not self.active_vault:
                self.notify("Create or open a vault first", severity="warning")
                return
            self.push_screen(CreateCharacterScreen())

        elif event.button.id == "list_characters":
            if not self.active_vault:
                self.notify("No active vault selected", severity="warning")
                return
            self.push_screen(ListCharactersScreen())

        elif event.button.id == "dashboard":
            if not self.active_vault:
                self.notify("No active vault selected", severity="warning")
                return
            self.push_screen(DashboardScreen())

# =======================================================================================


if __name__ == "__main__":
    CodexApp().run()
