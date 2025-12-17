from re import escape
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

def save_character(vault_path: str, name: str, summary: str) -> Path:
    vault = Path(vault_path).expanduser().resolve()
    characters_dir = vault / "characters"
    characters_dir.mkdir(exist_ok=True)

    slug = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")
    file_path = characters_dir / f"{slug}.md"

    content = f"""# {name}

## Summary
{summary}

## Description

## Traits

## History

## Relationships
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
        yield Button("Close", id="close")

    def on_mount(self) -> None:
        content = self.query_one("#content", Static)
        text = read_character(self.character_path)
        content.update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss()

    def action_cancel(self) -> None:
        self.dismiss()

# =======================================================================================
#
#                                 Character Screen
#
# =======================================================================================

class CreateCharacterScreen(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Static("Create Character")

        yield Input(
                placeholder="Character Name",
                id="name",
        )
        yield Input(
                placeholder="Short Summary",
                id="summary",
        )

        yield Button("Create", id="confirm")
        yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()

        elif event.button.id == "confirm":
            name = self.query_one("#name", Input).value.strip()
            summary = self.query_one("#summary", Input).value.strip()

            if not name:
                self.app.notify("Name is required", severity="error")
                return

            if not self.app.active_vault:
                self.app.notify("No active vault selected", severity="error")
                return

            save_character(self.app.active_vault, name, summary)

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

# =======================================================================================


if __name__ == "__main__":
    CodexApp().run()
