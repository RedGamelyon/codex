from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Vertical
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
                create_vault(path)
                self.dismiss()
                self.app.notify("Vault created")

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

            save_character("./my_first_vault", name, summary)
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
        width: 40;
        align: center middle;
    }

    #title {
        text-align: center;
        margin-bottom: 1;
    }

    .menu-button {
        width: 100%;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Welcome to Codex", id="title"),
            Button("Create Vault", id="create_vault", classes="menu-button"),
            Button("Create Character", id="create_character", classes="menu-button"),
            Button("Quit", id="quit", classes="menu-button"),
            id="menu",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.exit()

        elif event.button.id == "create_vault":
            self.push_screen(CreateVaultScreen())

        elif event.button.id == "create_character":
            self.push_screen(CreateCharacterScreen())
# =======================================================================================


if __name__ == "__main__":
    CodexApp().run()
