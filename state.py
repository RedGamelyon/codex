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

    # World
    active_world: Path | None = None
    characters: list[Path] = field(default_factory=list)

    # Navigation
    view_mode: str = "dashboard"  # dashboard, overview, character_list, character_view, character_create, character_edit, template_editor, stats, settings, timeline

    # Character selection
    selected_character: Path | None = None
    character_data: dict | None = None

    # Modal state
    modal_open: str | None = None  # create_world, open_world, delete_confirm, delete_world_confirm, search, edit_field, fullscreen_edit, unsaved_warning, link_picker

    # Input state
    text_input: str = ""
    input_active: bool = False
    active_field: str | None = None
    form_data: dict = field(default_factory=dict)
    _form_data_snapshot: dict = field(default_factory=dict)
    pending_navigation: str | None = None

    # Recent worlds
    recent_worlds: list[Path] = field(default_factory=list)

    # Section system
    current_section: str = "overview"
    enabled_sections: list[str] = field(default_factory=lambda: ["characters"])

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

    # World creation/open state
    discovered_worlds: list[Path] = field(default_factory=list)
    selected_world_index: int = -1
    default_locations: list[Path] = field(default_factory=list)
    selected_location_index: int = 0
    world_name_input: str = ""
    custom_location_input: str = ""
    show_custom_location: bool = False

    # Messages
    error_message: str = ""

    # Toast notifications
    toasts: list = field(default_factory=list)

    # Character sorting
    sort_mode: str = "name_asc"

    # Folder system
    folder_collapsed: dict = field(default_factory=dict)  # "section/folder_slug" -> bool
    folder_data: dict | None = None  # cached list_entities_with_folders result

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

    # Section popup (+ Section button)
    show_section_popup: bool = False

    # Timeline state
    timeline_events: list = field(default_factory=list)
    timeline_eras: list = field(default_factory=list)
    view_center_year: float = 500.0
    zoom_level: float = 1.0
    timeline_dragging: bool = False
    timeline_drag_start_x: float = 0.0
    timeline_drag_start_year: float = 0.0
    selected_event_index: int = -1
    hovered_event_index: int = -1
    selected_event_data: dict | None = None
    _timeline_last_click_time: float = 0.0

    # Event dragging (drag-to-reposition)
    event_dragging: bool = False
    event_drag_index: int = -1
    event_drag_start_x: float = 0.0
    event_drag_original_date: float = 0.0

    # Timeline bounds & display config (from calendar in world.yaml)
    timeline_start_year: float = -500.0
    timeline_end_year: float = 1500.0
    timeline_current_year: float | None = None
    timeline_time_format: str = "year_only"
    timeline_negative_label: str = "BC"
    timeline_positive_label: str = "AD"

    # Era editor state
    era_editor_eras: list = field(default_factory=list)
    era_editor_selected: int = -1

    # Link picker state
    link_picker_open: bool = False
    link_picker_field: str = ""              # which field key we're picking for
    link_picker_targets: list = field(default_factory=list)  # target sections
    link_picker_available: list = field(default_factory=list)  # [{section, slug, name}]
    link_picker_selected: list = field(default_factory=list)  # currently checked items
    link_picker_scroll: int = 0

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
        self.discovered_worlds = []
        self.selected_world_index = -1
        self.default_locations = []
        self.selected_location_index = 0
        self.world_name_input = ""
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
        # Clear era editor state
        self.era_editor_eras = []
        self.era_editor_selected = -1
        # Clear link picker state
        self.link_picker_open = False
        self.link_picker_field = ""
        self.link_picker_targets = []
        self.link_picker_available = []
        self.link_picker_selected = []
        self.link_picker_scroll = 0
        # Clear event drag state
        self.event_dragging = False
        self.event_drag_index = -1

    def reset_scroll(self):
        """Reset scroll offsets."""
        self.scroll_offset = 0
        self.view_scroll_offset = 0

    def load_characters(self):
        """Load character list from active world."""
        self.load_entities("characters")

    def load_entities(self, section: str = "characters"):
        """Load entity list for a section into characters list."""
        if self.active_world:
            from helpers import list_entities, list_entities_with_folders
            self.characters = list_entities(self.active_world, section)
            self.folder_data = list_entities_with_folders(self.active_world, section)
        else:
            self.characters = []
            self.folder_data = None
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

    def load_templates(self, section: str = "characters"):
        """Load templates for a section."""
        if self.active_world:
            from templates import ensure_section_templates, discover_templates
            ensure_section_templates(self.active_world, section)
            self.templates = discover_templates(self.active_world, section)
            if self.templates:
                self.active_template = self.templates[0]
        else:
            self.templates = []
            self.active_template = None

    def load_timeline_data(self):
        """Load timeline events, eras, and config from the active world."""
        if self.active_world:
            from helpers import load_timeline_events, get_calendar_config
            self.timeline_events = load_timeline_events(self.active_world)
            calendar = get_calendar_config(self.active_world)
            self.timeline_eras = calendar.get("eras", [])
            self.timeline_start_year = float(calendar.get("start_year", -500))
            self.timeline_end_year = float(calendar.get("end_year", 1500))
            cy = calendar.get("current_year")
            self.timeline_current_year = float(cy) if cy is not None else None
            self.timeline_time_format = calendar.get("time_format", "year_only")
            self.timeline_negative_label = calendar.get("negative_label", "BC")
            self.timeline_positive_label = calendar.get("positive_label", "AD")
        else:
            self.timeline_events = []
            self.timeline_eras = []
        # Clear selection when reloading
        self.selected_event_index = -1
        self.selected_event_data = None

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
