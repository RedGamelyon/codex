"""
Codex Application State
"""

from pathlib import Path
from dataclasses import dataclass, field
from time import monotonic


@dataclass
class Toast:
    """A toast notification message."""
    message: str
    toast_type: str = "info"
    created_at: float = field(default_factory=monotonic)
    duration: float = 3.0


@dataclass
class AppState:
    """Main application state."""

    # Vault
    active_vault: Path | None = None
    characters: list[Path] = field(default_factory=list)

    # Navigation
    view_mode: str = "dashboard"  # dashboard, character_list, character_view, character_create, character_edit, template_editor, stats

    # Character selection
    selected_character: Path | None = None
    character_data: dict | None = None

    # Modal state
    modal_open: str | None = None  # create_vault, open_vault, delete_confirm, search, edit_field, fullscreen_edit, unsaved_warning

    # Input state
    text_input: str = ""
    input_active: bool = False
    active_field: str | None = None
    form_data: dict = field(default_factory=dict)
    _form_data_snapshot: dict = field(default_factory=dict)
    pending_navigation: str | None = None

    # Recent vaults
    recent_vaults: list[Path] = field(default_factory=list)

    # Search/filter
    search_filter: str = ""

    # Scroll offsets
    scroll_offset: int = 0
    view_scroll_offset: int = 0
    form_scroll_offset: int = 0

    # Fullscreen editor state
    fullscreen_edit_field: str | None = None
    fullscreen_edit_title: str = ""
    fullscreen_return_modal: str | None = None
    fullscreen_scroll_offset: int = 0

    # Text input states (for stateful text input components)
    input_states: dict | None = None

    # Vault creation/open state
    discovered_vaults: list[Path] = field(default_factory=list)
    selected_vault_index: int = -1
    default_locations: list[Path] = field(default_factory=list)
    selected_location_index: int = 0
    vault_name_input: str = ""
    custom_location_input: str = ""
    show_custom_location: bool = False

    # Messages
    error_message: str = ""

    # Toast notifications
    toasts: list = field(default_factory=list)

    # Character sorting
    sort_mode: str = "name_asc"

    # Vim navigation
    focused_panel: str = "main"
    selected_index: int = -1
    displayed_characters: list = field(default_factory=list)

    # Portrait support
    portrait_cache: dict = field(default_factory=dict)
    portrait_action: str | None = None

    # Template system
    templates: list = field(default_factory=list)
    active_template: object | None = None
    template_editor_fields: list = field(default_factory=list)
    template_editor_selected: int = -1

    # Field editor modal
    field_editor_index: int = -1
    field_editor_type: str = "text"
    _field_editor_required: bool = False
    field_editor_last_click_time: float = 0.0

    # Image field actions (for new image mode)
    image_action: str | None = None           # "add", "change", "remove"
    image_action_field_key: str | None = None  # which image field

    # Temporary image storage for new character creation
    pending_images: dict = field(default_factory=dict)  # field_key -> file path string

    # Shortcuts help overlay
    show_shortcuts_help: bool = False

    def has_unsaved_changes(self) -> bool:
        """Check if form data differs from snapshot."""
        if self.view_mode not in ("character_create", "character_edit"):
            return False
        return self.form_data != self._form_data_snapshot

    def reset_input(self):
        """Reset input state."""
        self.text_input = ""
        self.input_active = False
        self.active_field = None
        self.form_data = {}
        self._form_data_snapshot = {}
        self.pending_navigation = None
        self.error_message = ""
        self.form_scroll_offset = 0
        self.discovered_vaults = []
        self.selected_vault_index = -1
        self.default_locations = []
        self.selected_location_index = 0
        self.vault_name_input = ""
        self.custom_location_input = ""
        self.show_custom_location = False
        self.fullscreen_edit_field = None
        self.fullscreen_edit_title = ""
        self.fullscreen_return_modal = None
        self.fullscreen_scroll_offset = 0
        self.input_states = None
        self.portrait_action = None
        self.template_editor_selected = -1
        self.field_editor_index = -1
        self.field_editor_type = "text"
        self._field_editor_required = False
        self.field_editor_last_click_time = 0.0
        self.image_action = None
        self.image_action_field_key = None
        # Clear pending images and their cached textures
        if self.pending_images:
            self.invalidate_portrait("_pending")
            self.pending_images = {}

    def reset_scroll(self):
        """Reset scroll offsets."""
        self.scroll_offset = 0
        self.view_scroll_offset = 0

    def load_characters(self):
        """Load character list from active vault."""
        if self.active_vault:
            from helpers import list_characters
            self.characters = list_characters(self.active_vault)
        else:
            self.characters = []
        self.clear_portrait_cache()

    def select_character(self, char_path: Path):
        """Select a character and load its data."""
        from helpers import read_character, parse_character

        self.selected_character = char_path
        content = read_character(char_path)
        self.character_data = parse_character(content)
        self.view_scroll_offset = 0

    def prepare_edit_form(self):
        """Populate form data from current character for editing."""
        if self.character_data:
            if self.active_template:
                self.form_data = {}
                for tf in self.active_template.fields:
                    self.form_data[tf.key] = self.character_data.get(tf.key, "")
            else:
                self.form_data = {
                    "name": self.character_data.get("name", ""),
                    "summary": self.character_data.get("summary", ""),
                    "description": self.character_data.get("description", ""),
                    "traits": self.character_data.get("traits", ""),
                    "history": self.character_data.get("history", ""),
                    "relationships": self.character_data.get("relationships", ""),
                    "tags": self.character_data.get("tags", ""),
                }
            self.active_field = "name"

    def load_templates(self):
        """Load templates from active vault."""
        if self.active_vault:
            from templates import discover_templates
            self.templates = discover_templates(self.active_vault)
            if self.templates:
                self.active_template = self.templates[0]
        else:
            self.templates = []
            self.active_template = None

    def resolve_template_for_character(self):
        """Set active_template based on current character's _meta.template field."""
        if self.character_data:
            meta = self.character_data.get("_meta", {})
            template_id = meta.get("template", "default")
            for t in self.templates:
                if t.template_id == template_id:
                    self.active_template = t
                    return
        # Fallback to first (default) template
        if self.templates:
            self.active_template = self.templates[0]

    def show_toast(self, message: str, toast_type: str = "info", duration: float = 3.0):
        """Add a toast notification."""
        self.toasts.append(Toast(message=message, toast_type=toast_type, duration=duration))

    def update_toasts(self):
        """Remove expired toasts."""
        now = monotonic()
        self.toasts = [t for t in self.toasts if now - t.created_at < t.duration]

    def clear_portrait_cache(self):
        """Unload all cached portrait textures."""
        from raylib import UnloadTexture
        for entry in self.portrait_cache.values():
            if entry is not None:
                try:
                    UnloadTexture(entry["texture"])
                except Exception:
                    pass
        self.portrait_cache.clear()

    def invalidate_portrait(self, slug: str, field_key: str | None = None):
        """Remove portrait(s) from the cache.

        If field_key is given, invalidate only "{slug}:{field_key}".
        If field_key is None, invalidate legacy key (slug) and all "{slug}:*" keys.
        """
        from raylib import UnloadTexture

        def _unload(key):
            if key in self.portrait_cache:
                entry = self.portrait_cache[key]
                if entry is not None:
                    try:
                        UnloadTexture(entry["texture"])
                    except Exception:
                        pass
                del self.portrait_cache[key]

        if field_key is not None:
            _unload(f"{slug}:{field_key}")
        else:
            # Invalidate legacy key
            _unload(slug)
            # Invalidate all field-keyed entries for this slug
            prefix = f"{slug}:"
            keys_to_remove = [k for k in self.portrait_cache if k.startswith(prefix)]
            for k in keys_to_remove:
                _unload(k)
