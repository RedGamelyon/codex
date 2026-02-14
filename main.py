"""
Codex - Worldbuilding Companion
A Raylib-based character and worldbuilding management tool.
"""

from pathlib import Path

from raylib import (
    InitWindow, CloseWindow, WindowShouldClose,
    BeginDrawing, EndDrawing, ClearBackground,
    SetTargetFPS, SetExitKey, SetConfigFlags,
    SetWindowTitle, SetWindowMinSize,
    IsKeyPressed, IsKeyDown,
    FLAG_WINDOW_RESIZABLE,
    KEY_ESCAPE, KEY_ENTER,
    KEY_J, KEY_K, KEY_H, KEY_L, KEY_SLASH,
    KEY_LEFT_SHIFT, KEY_RIGHT_SHIFT,
    KEY_LEFT, KEY_RIGHT, KEY_EQUAL, KEY_MINUS,
    KEY_KP_ADD, KEY_KP_SUBTRACT,
)

from state import AppState
from helpers import (
    create_world, is_valid_world,
    delete_character,
    get_character_slug, pick_image_file,
    save_entity_from_template, remove_entity_image,
    rename_entity_image_dir, get_entity_dir, get_entity_image_dir,
    SECTIONS,
)
from templates import ensure_default_template, get_default_template
from ui.colors import BG_DARK
from ui.panels import (
    draw_header, draw_sections_panel, draw_actions_panel,
    draw_main_panel_dashboard, draw_main_panel_overview,
    draw_main_panel_world, draw_main_panel_timeline,
    draw_main_panel_character_view, draw_main_panel_stats,
    draw_main_panel_template_editor, draw_main_panel_character_form,
    draw_main_panel_settings, draw_shortcuts_overlay
)
from ui.components import draw_toasts, draw_context_menu
from ui.modals import (
    draw_create_world_modal, draw_open_world_modal,
    draw_delete_confirm_modal, draw_delete_world_confirm_modal,
    draw_search_modal,
    draw_fullscreen_editor_modal,
    draw_field_editor_modal,
    draw_unsaved_warning_modal,
    draw_era_editor_modal,
    draw_goto_year_modal,
    draw_link_picker_modal,
    draw_create_folder_modal,
    draw_move_to_folder_modal,
)


INITIAL_WIDTH = 1280
INITIAL_HEIGHT = 720


def _section_list_view(state: AppState) -> str:
    """Return the 'list/home' view for the current section."""
    return "timeline" if state.current_section == "timeline" else "character_list"


def navigate_away_from_form(state: AppState, target_view: str):
    """Navigate away from create/edit form, checking for unsaved changes."""
    if state.has_unsaved_changes():
        state.pending_navigation = target_view
        state.modal_open = "unsaved_warning"
    else:
        state.view_mode = target_view
        state.reset_input()


def handle_input(state: AppState):
    """Handle global input."""
    # Shortcuts help overlay toggle (? = Shift + /)
    in_text_field = state.view_mode in ("character_create", "character_edit", "settings") or state.modal_open
    if IsKeyPressed(KEY_SLASH) and (IsKeyDown(KEY_LEFT_SHIFT) or IsKeyDown(KEY_RIGHT_SHIFT)):
        if state.show_shortcuts_help:
            state.show_shortcuts_help = False
            return
        elif not in_text_field:
            state.show_shortcuts_help = True
            return

    # Block all other input while shortcuts overlay is shown
    if state.show_shortcuts_help:
        if IsKeyPressed(KEY_ESCAPE):
            state.show_shortcuts_help = False
        state.update_toasts()
        return

    # Close section popup on escape
    if state.show_section_popup and IsKeyPressed(KEY_ESCAPE):
        state.show_section_popup = False
        return

    # Timeline keyboard controls (pan/zoom)
    if state.view_mode == "timeline" and not state.modal_open:
        if IsKeyDown(KEY_LEFT):
            state.view_center_year -= 5.0 / max(state.zoom_level, 0.01)
        if IsKeyDown(KEY_RIGHT):
            state.view_center_year += 5.0 / max(state.zoom_level, 0.01)
        if IsKeyPressed(KEY_EQUAL) or IsKeyPressed(KEY_KP_ADD):
            state.zoom_level = min(100.0, state.zoom_level * 1.3)
        if IsKeyPressed(KEY_MINUS) or IsKeyPressed(KEY_KP_SUBTRACT):
            state.zoom_level = max(0.01, state.zoom_level / 1.3)

    # Escape key handling
    if IsKeyPressed(KEY_ESCAPE):
        if state.modal_open == "fullscreen_edit":
            pass  # Let the fullscreen editor handle its own ESC
        elif state.modal_open:
            if state.modal_open == "unsaved_warning":
                # Dismiss unsaved warning → stay in form
                state.modal_open = None
                state.pending_navigation = None
            else:
                state.modal_open = None
                state.reset_input()
        elif state.view_mode == "character_create":
            navigate_away_from_form(state, _section_list_view(state))
        elif state.view_mode == "character_edit":
            navigate_away_from_form(state, "character_view")
        elif state.view_mode == "character_view":
            target = _section_list_view(state)
            state.view_mode = target
            state.selected_character = None
            state.character_data = None
            if target == "timeline":
                state.load_timeline_data()
        elif state.view_mode == "character_list":
            state.view_mode = "overview"
            state.current_section = "overview"
            state.view_scroll_offset = 0
        elif state.view_mode == "overview":
            pass  # Overview is the home screen when world is open
        elif state.view_mode == "timeline":
            if state.selected_event_index >= 0:
                state.selected_event_index = -1
                state.selected_event_data = None
                state.view_scroll_offset = 0
            else:
                state.view_mode = "overview"
                state.current_section = "overview"
                state.view_scroll_offset = 0
        elif state.view_mode == "settings":
            state.view_mode = "overview"
            state.current_section = "overview"
            state.view_scroll_offset = 0
            state.input_states = None
        elif state.view_mode == "stats":
            state.view_mode = "character_list"
        elif state.view_mode == "template_editor":
            state.view_mode = "character_list"
        elif state.selected_index >= 0:
            state.selected_index = -1

    # Enter key in modals
    if IsKeyPressed(KEY_ENTER) and state.modal_open:
        if state.modal_open == "create_world":
            handle_create_world(state)
        elif state.modal_open == "open_world":
            handle_open_world(state)
        elif state.modal_open == "search":
            state.search_filter = state.text_input
            state.modal_open = None
            state.reset_input()
        elif state.modal_open == "goto_year":
            # Trigger goto action via Enter key
            if state.input_states and "_goto_year" in state.input_states:
                year_text = state.input_states["_goto_year"].text.strip()
                try:
                    state.view_center_year = float(year_text)
                    state.show_toast(f"Jumped to year {year_text}", "info", 1.5)
                except ValueError:
                    state.show_toast("Invalid year", "warning")
            state.modal_open = None
            state.reset_input()

    # Vim navigation (only when no modal and not in form view)
    if not state.modal_open and state.view_mode not in ("character_create", "character_edit", "settings"):
        _handle_vim_keys(state)

    # Update toasts
    state.update_toasts()


def _handle_vim_keys(state: AppState):
    """Handle vim-style keyboard navigation."""
    # / opens search (character_list screen only)
    if IsKeyPressed(KEY_SLASH):
        if state.view_mode == "character_list" and state.active_world:
            state.modal_open = "search"
            state.text_input = state.search_filter
            state.input_active = True
            return

    # h/l — switch panel focus
    panels = ["sections", "actions", "main"]
    if IsKeyPressed(KEY_H):
        idx = panels.index(state.focused_panel)
        if idx > 0:
            state.focused_panel = panels[idx - 1]
            state.selected_index = 0
    if IsKeyPressed(KEY_L):
        idx = panels.index(state.focused_panel)
        if idx < len(panels) - 1:
            state.focused_panel = panels[idx + 1]
            state.selected_index = 0

    # j/k — navigate items in focused panel
    count = _get_item_count(state)
    if count > 0:
        if IsKeyPressed(KEY_J):
            if state.selected_index < 0:
                state.selected_index = 0
            elif state.selected_index < count - 1:
                state.selected_index += 1
        if IsKeyPressed(KEY_K):
            if state.selected_index < 0:
                state.selected_index = 0
            elif state.selected_index > 0:
                state.selected_index -= 1

    # Enter — activate selected item
    if IsKeyPressed(KEY_ENTER) and state.selected_index >= 0:
        _handle_vim_enter(state)


def _get_section_count(state: AppState) -> int:
    """Get number of items in the sections panel for vim navigation."""
    if not state.active_world:
        return 1  # Just dashboard
    # overview + sections + settings
    return 2 + len(SECTIONS)


def _get_item_count(state: AppState) -> int:
    """Get navigable item count for the focused panel."""
    if state.focused_panel == "sections":
        return _get_section_count(state)
    elif state.focused_panel == "actions":
        return len(_get_actions(state))
    elif state.focused_panel == "main":
        if state.view_mode == "character_list":
            return len(state.displayed_characters)
        elif state.view_mode == "template_editor":
            return len(state.template_editor_fields)
    return 0


def _get_actions(state: AppState) -> list[tuple[str, str]]:
    """Get available actions for current screen."""
    if state.view_mode == "dashboard":
        return [("Create World", "create_world"), ("Open World", "open_world")]
    elif state.view_mode in ("overview", "settings"):
        return []
    elif state.view_mode == "timeline":
        return [("Add Event", "timeline_add_event"), ("Manage Eras", "timeline_manage_eras"),
                ("Go to Year", "timeline_goto_year"), ("Fit All", "timeline_fit_all")]
    elif state.view_mode == "character_list":
        singular = SECTIONS.get(state.current_section, SECTIONS["characters"]).get("singular", "Entry")
        return [(f"New {singular}", "create_character"), ("Search", "search"), ("Templates", "templates")]
    elif state.view_mode == "character_view":
        return [("Edit", "edit"), ("Duplicate", "duplicate"), ("Delete", "delete"), ("Back", "back")]
    elif state.view_mode == "character_create":
        return [("Create", "confirm_create"), ("Cancel", "cancel_create")]
    elif state.view_mode == "character_edit":
        return [("Save", "save"), ("Cancel", "cancel")]
    elif state.view_mode == "stats":
        return [("Back", "back_to_world")]
    elif state.view_mode == "template_editor":
        return [("Edit Field", "edit_field"), ("Add Field", "add_field"), ("Remove Field", "remove_field"),
                ("Move Up", "move_field_up"), ("Move Down", "move_field_down"),
                ("Save", "save_template"), ("Back", "back_to_world_from_templates")]
    return []


def _handle_vim_enter(state: AppState):
    """Handle Enter key for vim navigation."""
    if state.focused_panel == "sections":
        if not state.active_world:
            if state.selected_index == 0:
                state.view_mode = "dashboard"
        else:
            # Build section list matching panel layout: overview, characters, locations, timeline, codex, settings
            section_order = ["characters", "locations", "timeline", "codex"]
            items = ["overview"] + section_order + ["settings"]
            if 0 <= state.selected_index < len(items):
                _handle_section_click(state, items[state.selected_index])

    elif state.focused_panel == "actions":
        actions = _get_actions(state)
        if 0 <= state.selected_index < len(actions):
            _, action_key = actions[state.selected_index]
            handle_action(state, action_key)

    elif state.focused_panel == "main":
        if state.view_mode == "character_list":
            if 0 <= state.selected_index < len(state.displayed_characters):
                char_path = state.displayed_characters[state.selected_index]
                state.select_character(char_path)
                state.view_mode = "character_view"
        elif state.view_mode == "template_editor":
            if 0 <= state.selected_index < len(state.template_editor_fields):
                state.template_editor_selected = state.selected_index
                handle_action(state, "edit_field")


def _fit_all_timeline_events(state: AppState):
    """Zoom and center to show all timeline events."""
    if not state.timeline_events:
        # If no events but eras exist, fit to eras
        if state.timeline_eras:
            starts = [e.get("start", 0) for e in state.timeline_eras]
            ends = [e.get("end", 0) for e in state.timeline_eras]
            min_val = min(starts)
            max_val = max(ends)
            range_val = max(max_val - min_val, 1)
            state.view_center_year = (min_val + max_val) / 2
            state.zoom_level = max(0.01, min(100.0, 1000.0 / (range_val * 1.2)))
        return
    dates = [e["date"] for e in state.timeline_events]
    min_date = min(dates)
    max_date = max(dates)
    range_years = max(max_date - min_date, 1)
    state.view_center_year = (min_date + max_date) / 2
    state.zoom_level = max(0.01, min(100.0, 1000.0 / (range_years * 1.2)))
    state.show_toast("Fit to all events", "info", 1.5)


def _open_timeline_event(state: AppState):
    """Open the selected timeline event for editing."""
    idx = state.selected_event_index
    if idx < 0 or idx >= len(state.timeline_events):
        return
    event = state.timeline_events[idx]
    event_path = event.get("path")
    if not event_path:
        return
    state.load_entities("timeline")
    state.load_templates("timeline")
    state.select_character(event_path)
    state.resolve_template_for_character()
    state.prepare_edit_form()
    state._form_data_snapshot = dict(state.form_data)
    state.view_mode = "character_edit"
    state.input_states = None
    state.form_scroll_offset = 0


def _handle_timeline_drag_complete(state: AppState):
    """Save the new date after dragging an event on the timeline."""
    idx = state.event_drag_index if state.event_drag_index >= 0 else state.selected_event_index
    if idx < 0 or idx >= len(state.timeline_events):
        return
    event = state.timeline_events[idx]
    event_path = event.get("path")
    new_date = event["date"]
    if not event_path:
        return
    from helpers import update_event_date
    update_event_date(event_path, new_date)
    state.load_timeline_data()
    # Re-select the event after reload
    for i, e in enumerate(state.timeline_events):
        if e.get("path") == event_path:
            state.selected_event_index = i
            state.selected_event_data = dict(e)
            break
    state.show_toast(f"Moved to year {int(new_date)}", "info", 1.5)


def handle_create_world(state: AppState):
    """Handle world creation."""
    world_name = state.world_name_input.strip()
    if not world_name:
        return

    # Determine the base location
    if state.show_custom_location:
        base_path = state.custom_location_input.strip()
        if not base_path:
            return
        if base_path.startswith("~"):
            base_path = str(Path.home()) + base_path[1:]
    elif state.default_locations:
        base_path = str(state.default_locations[state.selected_location_index])
    else:
        return

    # Create world path
    world_path = Path(base_path) / world_name

    create_world(str(world_path))
    state.active_world = world_path
    state.load_characters()
    state.load_templates()
    from helpers import get_enabled_sections
    state.enabled_sections = get_enabled_sections(world_path)
    state.current_section = "overview"
    state.view_mode = "overview"
    state.view_scroll_offset = 0
    state.modal_open = None
    state.reset_input()
    state.show_toast("World created!", "success")

    from config import add_recent_world, get_recent_worlds
    add_recent_world(world_path)
    state.recent_worlds = get_recent_worlds()


def handle_open_world(state: AppState):
    """Handle world opening."""
    world_path = None

    # Check if a world was selected from the list
    if state.selected_world_index >= 0 and state.discovered_worlds:
        world_path = state.discovered_worlds[state.selected_world_index]
    elif state.text_input.strip():
        # Use manual path input
        path = state.text_input.strip()
        if path.startswith("~"):
            path = str(Path.home()) + path[1:]
        world_path = Path(path)

    if world_path:
        if is_valid_world(world_path):
            state.active_world = world_path
            ensure_default_template(world_path)
            state.load_characters()
            state.load_templates()
            from helpers import get_enabled_sections
            state.enabled_sections = get_enabled_sections(world_path)
            state.current_section = "overview"
            state.view_mode = "overview"
            state.view_scroll_offset = 0
            state.modal_open = None
            state.reset_input()
            state.error_message = ""
            state.show_toast(f"Opened: {world_path.name}", "success")

            from config import add_recent_world, get_recent_worlds
            add_recent_world(world_path)
            state.recent_worlds = get_recent_worlds()
        else:
            state.error_message = "Not a valid world (missing world.yaml or characters/)"
            state.show_toast("Invalid world path", "error")


def _open_world_direct(state: AppState, world_path: Path):
    """Open a world directly (from dashboard recent worlds)."""
    if is_valid_world(world_path):
        state.active_world = world_path
        ensure_default_template(world_path)
        state.load_characters()
        state.load_templates()
        from helpers import get_enabled_sections
        state.enabled_sections = get_enabled_sections(world_path)
        state.current_section = "overview"
        state.view_mode = "overview"
        state.view_scroll_offset = 0
        state.show_toast(f"Opened: {world_path.name}", "success")

        from config import add_recent_world, get_recent_worlds
        add_recent_world(world_path)
        state.recent_worlds = get_recent_worlds()
    else:
        state.show_toast("World no longer valid", "error")


def handle_create_character(state: AppState):
    """Handle entity creation for the current section."""
    if not state.active_world:
        return

    section = state.current_section
    singular = SECTIONS.get(section, SECTIONS["characters"]).get("singular", "Entry")
    template = state.active_template or get_default_template()

    # Validate all required fields
    from templates import IMAGE_FIELD_TYPES
    for tf in template.fields:
        if tf.required and tf.field_type not in IMAGE_FIELD_TYPES:
            value = state.form_data.get(tf.key, "").strip()
            if not value:
                state.show_toast(f"{tf.display_name} is required", "error")
                return

    name = state.form_data.get("name", "").strip()
    if not name:
        return  # Already caught above if name is required
    save_entity_from_template(state.active_world, section, template, state.form_data)

    # Copy any pending images to the entity's image directory
    if state.pending_images:
        from helpers import save_entity_image
        for field_key, img_path in state.pending_images.items():
            from pathlib import Path as P
            if P(img_path).exists():
                save_entity_image(state.active_world, section, name, img_path, field_key=field_key)

    state.load_entities(section)
    if section == "timeline":
        state.view_mode = "timeline"
        state.load_timeline_data()
    else:
        state.view_mode = "character_list"
    state.reset_input()
    state.show_toast(f"{singular} created!", "success")


def handle_save_character(state: AppState):
    """Handle saving edited entity."""
    if not state.selected_character or not state.active_world:
        return

    section = state.current_section

    # Validate all required fields
    template = state.active_template or get_default_template()
    from templates import IMAGE_FIELD_TYPES
    for tf in template.fields:
        if tf.required and tf.field_type not in IMAGE_FIELD_TYPES:
            value = state.form_data.get(tf.key, "").strip()
            if not value:
                state.show_toast(f"{tf.display_name} is required", "error")
                return

    name = state.form_data.get("name", "").strip()
    if name:
        # Rename image dir if name changed
        old_name = state.character_data.get("name", "") if state.character_data else ""
        if old_name and old_name != name:
            rename_entity_image_dir(state.active_world, section, old_name, name)

        # Delete old file
        old_path = state.selected_character
        delete_character(old_path)

        # Save with template
        template = state.active_template or get_default_template()
        new_path = save_entity_from_template(state.active_world, section, template, state.form_data)

        # Reload
        state.load_entities(section)
        if section == "timeline":
            state.view_mode = "timeline"
            state.load_timeline_data()
            state.selected_character = None
            state.character_data = None
            state.reset_input()
        else:
            state.selected_character = new_path
            state.select_character(new_path)
            state.view_mode = "character_view"
            state.reset_input()
        state.show_toast("Changes saved", "success")


def handle_delete_character(state: AppState):
    """Handle entity deletion."""
    if state.selected_character:
        section = state.current_section
        singular = SECTIONS.get(section, SECTIONS["characters"]).get("singular", "Entry")

        # Remove all image files
        if state.active_world and state.character_data:
            char_name = state.character_data.get("name", "")
            if char_name:
                remove_entity_image(state.active_world, section, char_name, field_key=None)

        delete_character(state.selected_character)
        state.load_entities(section)
        state.selected_character = None
        state.character_data = None
        if section == "timeline":
            state.view_mode = "timeline"
            state.load_timeline_data()
        else:
            state.view_mode = "character_list"
        state.modal_open = None
        state.show_toast(f"{singular} deleted", "info")


def handle_duplicate_character(state: AppState):
    """Duplicate the currently viewed entity."""
    if not state.active_world or not state.character_data or not state.selected_character:
        return

    section = state.current_section
    singular = SECTIONS.get(section, SECTIONS["characters"]).get("singular", "Entry")

    from templates import IMAGE_FIELD_TYPES
    import shutil

    template = state.active_template or get_default_template()
    original_name = state.character_data.get("name", "Unnamed")

    # Generate a unique copy name
    entity_dir = get_entity_dir(state.active_world, section)
    copy_name = f"{original_name} (Copy)"
    slug = get_character_slug(copy_name)
    counter = 2
    while (entity_dir / f"{slug}.md").exists():
        copy_name = f"{original_name} (Copy {counter})"
        slug = get_character_slug(copy_name)
        counter += 1

    # Build form data from original, replacing name
    form_data = {}
    for tf in template.fields:
        if tf.field_type in IMAGE_FIELD_TYPES:
            continue
        if tf.key == "name":
            form_data[tf.key] = copy_name
        else:
            form_data[tf.key] = state.character_data.get(tf.key, "")

    # Save the new entity file
    new_path = save_entity_from_template(state.active_world, section, template, form_data)

    # Copy all images from original entity's image directory
    original_slug = get_character_slug(original_name)
    new_slug = get_character_slug(copy_name)
    original_img_dir = get_entity_image_dir(state.active_world, section, original_slug)
    if original_img_dir.exists():
        new_img_dir = get_entity_image_dir(state.active_world, section, new_slug)
        new_img_dir.mkdir(parents=True, exist_ok=True)
        for img_file in original_img_dir.iterdir():
            if img_file.is_file():
                shutil.copy2(str(img_file), str(new_img_dir / img_file.name))

    # Reload and open in edit mode
    state.load_entities(section)
    state.select_character(new_path)
    state.resolve_template_for_character()
    state.prepare_edit_form()
    state._form_data_snapshot = dict(state.form_data)
    state.view_mode = "character_edit"
    state.input_states = None
    state.form_scroll_offset = 0
    state.show_toast(f"{singular} duplicated!", "success")


def handle_portrait_action(state: AppState):
    """Handle portrait add/change/remove actions (runs between frames)."""
    action = state.portrait_action
    state.portrait_action = None

    if not state.active_world or not state.character_data:
        return

    section = state.current_section
    name = state.character_data.get("name", "")
    if not name:
        return

    slug = get_character_slug(name)

    if action in ("add", "change"):
        path = pick_image_file()
        if path is None:
            return

        from pathlib import Path as P
        if not P(path).exists():
            state.show_toast("Error: file not found", "error")
            return

        from helpers import save_entity_image
        result = save_entity_image(state.active_world, section, name, path, field_key="portrait")
        if result:
            state.invalidate_portrait(slug, "portrait")
            state.show_toast("Portrait updated", "success")
        else:
            state.show_toast("Failed to save portrait", "error")
    elif action == "remove":
        if remove_entity_image(state.active_world, section, name, field_key="portrait"):
            state.invalidate_portrait(slug, "portrait")
            state.show_toast("Portrait removed", "info")


def handle_image_action(state: AppState):
    """Handle image field add/change/remove actions (runs between frames).

    Supports two modes:
    - Create mode (view_mode == "character_create"): stores paths in pending_images
    - Normal mode: saves/removes images in the world immediately
    """
    action = state.image_action
    field_key = state.image_action_field_key
    state.image_action = None
    state.image_action_field_key = None

    if not action or not field_key:
        return

    section = state.current_section
    is_create_mode = state.view_mode == "character_create"

    if action in ("add", "change"):
        path = pick_image_file()
        if path is None:
            return

        from pathlib import Path as P
        if not P(path).exists():
            state.show_toast("Error: file not found", "error")
            return

        if is_create_mode:
            # Store temp path for later (will be copied on entity save)
            state.invalidate_portrait("_pending", field_key)
            state.pending_images[field_key] = path
            state.show_toast("Image selected", "success")
        else:
            if not state.active_world or not state.character_data:
                return
            name = state.character_data.get("name", "")
            if not name:
                return
            slug = get_character_slug(name)
            from helpers import save_entity_image
            result = save_entity_image(state.active_world, section, name, path, field_key=field_key)
            if result:
                state.invalidate_portrait(slug, field_key)
                state.show_toast("Image updated", "success")
            else:
                state.show_toast("Failed to save image", "error")

    elif action == "remove":
        if is_create_mode:
            if field_key in state.pending_images:
                del state.pending_images[field_key]
            state.invalidate_portrait("_pending", field_key)
            state.show_toast("Image removed", "info")
        else:
            if not state.active_world or not state.character_data:
                return
            name = state.character_data.get("name", "")
            if not name:
                return
            slug = get_character_slug(name)
            if remove_entity_image(state.active_world, section, name, field_key=field_key):
                state.invalidate_portrait(slug, field_key)
                state.show_toast("Image removed", "info")


def _handle_link_action(state: AppState, action: str):
    """Handle link-related actions from view/form panels."""
    if action.startswith("navigate:"):
        # Navigate to a linked entity: navigate:section:slug
        parts = action.split(":", 2)
        if len(parts) == 3:
            _, target_section, target_slug = parts
            if not state.active_world:
                return
            # Switch to target section
            state.current_section = target_section
            state.load_entities(target_section)
            state.load_templates(target_section)
            # Find and open the entity
            entity_dir = get_entity_dir(state.active_world, target_section)
            entity_path = entity_dir / f"{target_slug}.md"
            if entity_path.exists():
                state.select_character(entity_path)
                state.resolve_template_for_character()
                state.view_mode = "character_view"
                state.view_scroll_offset = 0
            else:
                state.show_toast(f"Entity not found: {target_slug}", "warning")

    elif action.startswith("link_add:"):
        # Open link picker for a field: link_add:field_key
        field_key = action.split(":", 1)[1]
        template = state.active_template
        if template:
            # Find the template field to get targets
            for tf in template.fields:
                if tf.key == field_key:
                    state.link_picker_field = field_key
                    state.link_picker_targets = list(tf.link_targets)
                    # Build available entities list
                    available = []
                    if state.active_world:
                        from helpers import list_entities, read_character, parse_character
                        for target_section in tf.link_targets:
                            entities = list_entities(state.active_world, target_section)
                            for ep in entities:
                                content = read_character(ep)
                                parsed = parse_character(content)
                                available.append({
                                    "section": target_section,
                                    "slug": ep.stem,
                                    "name": parsed.get("name", ep.stem.replace("_", " ").title()),
                                })
                    state.link_picker_available = available
                    # Pre-select currently linked items
                    from helpers import parse_link_field
                    current_links = parse_link_field(state.form_data.get(field_key, ""))
                    current_set = {f"{l['section']}:{l['slug']}" for l in current_links}
                    state.link_picker_selected = [
                        item for item in available
                        if f"{item['section']}:{item['slug']}" in current_set
                    ]
                    state.link_picker_scroll = 0
                    state.link_picker_open = True
                    state.modal_open = "link_picker"
                    break

    elif action.startswith("link_remove:"):
        # Remove a link: link_remove:field_key:section:slug
        parts = action.split(":", 3)
        if len(parts) == 4:
            _, field_key, section, slug = parts
            from helpers import parse_link_field, format_link_field
            current = parse_link_field(state.form_data.get(field_key, ""))
            current = [l for l in current if not (l["section"] == section and l["slug"] == slug)]
            state.form_data[field_key] = format_link_field(current)


def draw_ui(state: AppState):
    """Draw the entire UI."""
    # Draw panels
    draw_header()

    # Sections panel
    section_clicked = draw_sections_panel(state)
    if section_clicked and not state.modal_open:
        _handle_section_click(state, section_clicked)

    # Actions panel
    action_clicked = draw_actions_panel(state)
    if action_clicked and not state.modal_open:
        handle_action(state, action_clicked)

    # Main panel
    if state.view_mode == "dashboard":
        clicked_world = draw_main_panel_dashboard(state)
        if clicked_world and not state.modal_open:
            _open_world_direct(state, clicked_world)
    elif state.view_mode == "overview":
        draw_main_panel_overview(state)
    elif state.view_mode == "timeline":
        timeline_action = draw_main_panel_timeline(state)
        if timeline_action and not state.modal_open:
            handle_action(state, timeline_action)
    elif state.view_mode == "settings":
        settings_action = draw_main_panel_settings(state)
        if settings_action and not state.modal_open:
            _handle_settings_action(state, settings_action)
    elif state.view_mode == "character_list":
        list_action = draw_main_panel_world(state)
        if list_action and not state.modal_open:
            if list_action.startswith("select:"):
                idx = int(list_action[7:])
                state.select_character(state.characters[idx])
                state.view_mode = "character_view"
            elif list_action == "folder_create":
                state.modal_open = "create_folder"
                state.text_input = ""
                state.input_active = True
    elif state.view_mode == "character_view":
        view_action = draw_main_panel_character_view(state)
        if view_action and not state.modal_open:
            _handle_link_action(state, view_action)
    elif state.view_mode == "character_create":
        form_action = draw_main_panel_character_form(state, is_create=True)
        if form_action and not state.modal_open:
            _handle_link_action(state, form_action)
    elif state.view_mode == "character_edit":
        form_action = draw_main_panel_character_form(state, is_create=False)
        if form_action and not state.modal_open:
            _handle_link_action(state, form_action)
    elif state.view_mode == "stats":
        draw_main_panel_stats(state)
    elif state.view_mode == "template_editor":
        te_action = draw_main_panel_template_editor(state)
        if te_action and not state.modal_open:
            handle_action(state, te_action)

    # Draw modals on top
    if state.modal_open:
        draw_modal(state)

    # Draw context menu on top of modals
    draw_context_menu()

    # Draw shortcuts overlay on top of everything
    if state.show_shortcuts_help:
        draw_shortcuts_overlay()

    # Draw toasts on top of everything
    if state.toasts:
        draw_toasts(state.toasts)


def _handle_section_click(state: AppState, section: str):
    """Handle clicking a section in the sections panel."""
    from helpers import enable_section

    if section == "dashboard":
        if state.view_mode in ("character_create", "character_edit"):
            navigate_away_from_form(state, "dashboard")
        else:
            state.view_mode = "dashboard"
            state.current_section = "overview"
            state.selected_character = None
            state.character_data = None

    elif section == "overview":
        if state.view_mode in ("character_create", "character_edit"):
            navigate_away_from_form(state, "overview")
        else:
            state.view_mode = "overview"
            state.current_section = "overview"
            state.view_scroll_offset = 0

    elif section == "settings":
        if state.view_mode in ("character_create", "character_edit"):
            navigate_away_from_form(state, "settings")
        else:
            state.view_mode = "settings"
            state.current_section = "settings"
            state.view_scroll_offset = 0
            state.input_states = None
            state.active_field = None

    elif section == "characters":
        if state.view_mode in ("character_create", "character_edit"):
            navigate_away_from_form(state, "character_list")
        else:
            state.current_section = "characters"
            state.load_entities("characters")
            state.load_templates("characters")
            state.view_mode = "character_list"
            state.selected_character = None
            state.character_data = None
            state.reset_scroll()

    elif section.startswith("enable_"):
        sec_key = section[7:]
        if state.active_world:
            enable_section(state.active_world, sec_key)
            if sec_key not in state.enabled_sections:
                state.enabled_sections.append(sec_key)
            meta = SECTIONS.get(sec_key, {})
            state.show_toast(f"{meta.get('name', sec_key)} enabled", "success")

    elif section == "timeline":
        if state.view_mode in ("character_create", "character_edit"):
            navigate_away_from_form(state, "timeline")
        else:
            state.view_mode = "timeline"
            state.current_section = "timeline"
            state.view_scroll_offset = 0
            state.load_timeline_data()

    elif section in ("locations", "codex"):
        if state.view_mode in ("character_create", "character_edit"):
            navigate_away_from_form(state, "character_list")
        else:
            state.current_section = section
            state.load_entities(section)
            state.load_templates(section)
            state.view_mode = "character_list"
            state.selected_character = None
            state.character_data = None
            state.reset_scroll()


def _handle_settings_action(state: AppState, action: str):
    """Handle actions from the settings page."""
    from helpers import enable_section, disable_section, update_world_meta

    if action == "save_world_meta":
        if state.input_states and state.active_world:
            name = state.input_states.get("_settings_name")
            desc = state.input_states.get("_settings_desc")
            new_name = name.text.strip() if name else None
            new_desc = desc.text if desc else None
            if new_name:
                update_world_meta(state.active_world, name=new_name, description=new_desc)
                state.show_toast("World settings saved", "success")
            else:
                state.show_toast("World name cannot be empty", "warning")

    elif action == "delete_world":
        state.modal_open = "delete_world_confirm"

    elif action.startswith("enable_"):
        sec_key = action[7:]
        if state.active_world:
            enable_section(state.active_world, sec_key)
            if sec_key not in state.enabled_sections:
                state.enabled_sections.append(sec_key)
            meta = SECTIONS.get(sec_key, {})
            state.show_toast(f"{meta.get('name', sec_key)} enabled", "success")

    elif action.startswith("disable_"):
        sec_key = action[8:]
        if state.active_world and sec_key != "characters":
            disable_section(state.active_world, sec_key)
            if sec_key in state.enabled_sections:
                state.enabled_sections.remove(sec_key)
            meta = SECTIONS.get(sec_key, {})
            state.show_toast(f"{meta.get('name', sec_key)} disabled", "info")

    elif action == "save_timeline_settings":
        if state.input_states and state.active_world:
            from helpers import get_calendar_config, save_calendar_config
            calendar = get_calendar_config(state.active_world)
            try:
                start_text = state.input_states.get("_tl_start_year")
                calendar["start_year"] = int(start_text.text.strip()) if start_text and start_text.text.strip() else -500
            except ValueError:
                pass
            try:
                end_text = state.input_states.get("_tl_end_year")
                calendar["end_year"] = int(end_text.text.strip()) if end_text and end_text.text.strip() else 1500
            except ValueError:
                pass
            cy_state = state.input_states.get("_tl_current_year")
            if cy_state and cy_state.text.strip():
                try:
                    calendar["current_year"] = int(cy_state.text.strip())
                except ValueError:
                    pass
            else:
                calendar.pop("current_year", None)
            calendar["time_format"] = state.timeline_time_format
            neg_state = state.input_states.get("_tl_neg_label")
            pos_state = state.input_states.get("_tl_pos_label")
            calendar["negative_label"] = neg_state.text.strip() if neg_state and neg_state.text.strip() else "BC"
            calendar["positive_label"] = pos_state.text.strip() if pos_state and pos_state.text.strip() else "AD"
            save_calendar_config(state.active_world, calendar)
            state.load_timeline_data()
            state.show_toast("Timeline settings saved", "success")


def _handle_delete_world(state: AppState):
    """Delete the current world and return to dashboard."""
    from helpers import delete_world
    if state.active_world:
        world_name = state.active_world.name
        if delete_world(state.active_world):
            # Remove from recent worlds
            from config import load_config, save_config
            config = load_config()
            paths = config.get("recent_worlds", [])
            path_str = str(state.active_world.resolve())
            paths = [p for p in paths if p != path_str]
            config["recent_worlds"] = paths
            save_config(config)

            state.active_world = None
            state.characters = []
            state.selected_character = None
            state.character_data = None
            state.templates = []
            state.active_template = None
            state.enabled_sections = ["characters"]
            state.current_section = "overview"
            state.view_mode = "dashboard"
            state.modal_open = None
            state.reset_input()
            state.clear_portrait_cache()

            # Refresh recent worlds
            from config import get_recent_worlds
            state.recent_worlds = get_recent_worlds()

            state.show_toast(f"World '{world_name}' deleted", "info")
        else:
            state.show_toast("Failed to delete world", "error")
            state.modal_open = None


def handle_action(state: AppState, action: str):
    """Handle action button clicks."""
    if action == "create_world":
        state.modal_open = "create_world"
        state.input_active = True
    elif action == "open_world":
        state.modal_open = "open_world"
        state.input_active = True
    elif action == "create_character":
        from templates import get_default_template, IMAGE_FIELD_TYPES
        state.view_mode = "character_create"
        template = state.active_template or get_default_template()
        state.form_data = {tf.key: "" for tf in template.fields if tf.field_type not in IMAGE_FIELD_TYPES}
        state._form_data_snapshot = dict(state.form_data)
        first_text = next((tf.key for tf in template.fields if tf.field_type not in IMAGE_FIELD_TYPES), "name")
        state.active_field = first_text
        state.input_states = None
        state.form_scroll_offset = 0
        state.pending_images = {}
    elif action == "search":
        state.modal_open = "search"
        state.text_input = state.search_filter
        state.input_active = True
    elif action == "stats":
        state.view_mode = "stats"
    elif action == "new_folder":
        state.modal_open = "create_folder"
        state.text_input = ""
        state.input_active = True
    elif action == "open_world_folder":
        if state.active_world:
            from helpers import open_in_file_manager
            open_in_file_manager(state.active_world)
    elif action == "edit":
        state.resolve_template_for_character()
        state.prepare_edit_form()
        state._form_data_snapshot = dict(state.form_data)
        state.view_mode = "character_edit"
        state.input_states = None
        state.form_scroll_offset = 0
    elif action == "duplicate":
        handle_duplicate_character(state)
    elif action == "move_to_folder":
        if state.selected_character and state.folder_data:
            state.modal_open = "move_to_folder"
    elif action == "delete":
        state.modal_open = "delete_confirm"
    elif action == "back":
        if state.view_mode in ("character_create", "character_edit"):
            target = "character_view" if state.selected_character else _section_list_view(state)
            navigate_away_from_form(state, target)
        else:
            target = _section_list_view(state)
            state.view_mode = target
            state.selected_character = None
            state.character_data = None
            if target == "timeline":
                state.load_timeline_data()
    elif action == "back_to_world":
        target = _section_list_view(state)
        state.view_mode = target
        if target == "timeline":
            state.load_timeline_data()
    elif action == "confirm_create":
        handle_create_character(state)
    elif action == "save":
        handle_save_character(state)
    elif action == "cancel":
        navigate_away_from_form(state, "character_view" if state.selected_character else _section_list_view(state))
    elif action == "cancel_create":
        navigate_away_from_form(state, _section_list_view(state))
    elif action == "templates":
        state.view_mode = "template_editor"
        state.template_editor_selected = 0
        if state.active_template:
            state.template_editor_fields = [
                {"key": f.key, "display_name": f.display_name,
                 "field_type": f.field_type, "required": f.required,
                 "image_width": getattr(f, "image_width", 0),
                 "image_height": getattr(f, "image_height", 0),
                 "link_targets": getattr(f, "link_targets", [])}
                for f in state.active_template.fields
            ]
    elif action == "edit_field":
        idx = state.template_editor_selected
        if 0 <= idx < len(state.template_editor_fields):
            state.field_editor_index = idx
            fd = state.template_editor_fields[idx]
            state.field_editor_type = fd["field_type"]
            state._field_editor_width = fd.get("image_width", 0)
            state._field_editor_height = fd.get("image_height", 0)
            state._field_editor_required = fd.get("required", False)
            state.modal_open = "edit_field"
            state.active_field = "field_editor_label"
            state.input_states = None  # Force re-init in modal draw
    elif action == "add_field":
        _handle_add_template_field(state)
    elif action == "remove_field":
        _handle_remove_template_field(state)
    elif action == "move_field_up":
        _handle_move_template_field(state, -1)
    elif action == "move_field_down":
        _handle_move_template_field(state, 1)
    elif action == "save_template":
        _handle_save_template(state)
    elif action == "back_to_world_from_templates":
        state.view_mode = "character_list"

    # --- Timeline actions ---
    elif action == "timeline_add_event":
        state.load_entities("timeline")
        state.load_templates("timeline")
        # Pre-fill date with center of current view
        from templates import get_default_template, IMAGE_FIELD_TYPES
        state.view_mode = "character_create"
        template = state.active_template or get_default_template()
        state.form_data = {tf.key: "" for tf in template.fields if tf.field_type not in IMAGE_FIELD_TYPES}
        state.form_data["date"] = str(int(state.view_center_year))
        state._form_data_snapshot = dict(state.form_data)
        first_text = next((tf.key for tf in template.fields if tf.field_type not in IMAGE_FIELD_TYPES), "name")
        state.active_field = first_text
        state.input_states = None
        state.form_scroll_offset = 0
        state.pending_images = {}
    elif action == "timeline_manage_eras":
        import copy
        state.era_editor_eras = copy.deepcopy(state.timeline_eras)
        state.era_editor_selected = 0 if state.era_editor_eras else -1
        state.modal_open = "era_editor"
        state.input_states = None
        state.active_field = None
    elif action == "timeline_goto_year":
        state.modal_open = "goto_year"
        state.input_states = None
        state.active_field = "_goto_year"
    elif action == "timeline_fit_all":
        _fit_all_timeline_events(state)
    elif action == "timeline_view_event":
        _open_timeline_event(state)
    elif action == "timeline_edit_event":
        _open_timeline_event(state)
    elif action == "timeline_delete_event":
        idx = state.selected_event_index
        if 0 <= idx < len(state.timeline_events):
            event = state.timeline_events[idx]
            event_path = event.get("path")
            if event_path:
                delete_character(event_path)
                state.load_timeline_data()
                state.show_toast("Event deleted", "info")
    elif action == "timeline_close_card":
        state.selected_event_index = -1
        state.selected_event_data = None
        state.view_scroll_offset = 0
    elif action == "timeline_drag_complete":
        _handle_timeline_drag_complete(state)


def _handle_save_template(state: AppState):
    """Save the currently edited template."""
    from templates import TemplateField, Template, save_template
    if not state.active_template or not state.active_world:
        return
    fields = []
    for fd in state.template_editor_fields:
        fields.append(TemplateField(
            key=fd["key"],
            display_name=fd["display_name"],
            field_type=fd["field_type"],
            required=fd.get("required", False),
            image_width=fd.get("image_width", 0),
            image_height=fd.get("image_height", 0),
            link_targets=fd.get("link_targets", []),
        ))
    state.active_template.fields = fields
    save_template(state.active_world, state.active_template)
    state.load_templates()
    state.show_toast("Template saved", "success")


def _handle_add_template_field(state: AppState):
    """Add a new field to the template being edited."""
    idx = len(state.template_editor_fields)
    key = f"custom_{idx}"
    state.template_editor_fields.append({
        "key": key,
        "display_name": f"Custom Field {idx}",
        "field_type": "multiline",
        "required": False,
        "image_width": 0,
        "image_height": 0,
    })
    state.template_editor_selected = len(state.template_editor_fields) - 1
    state.show_toast("Field added", "info")


def _handle_remove_template_field(state: AppState):
    """Remove selected field from the template (cannot remove name)."""
    idx = state.template_editor_selected
    if 0 <= idx < len(state.template_editor_fields):
        if state.template_editor_fields[idx]["key"] == "name":
            state.show_toast("Cannot remove Name field", "warning")
            return
        state.template_editor_fields.pop(idx)
        if state.template_editor_selected >= len(state.template_editor_fields):
            state.template_editor_selected = max(0, len(state.template_editor_fields) - 1)
        state.show_toast("Field removed", "info")


def _handle_move_template_field(state: AppState, direction: int):
    """Move selected field up (-1) or down (+1)."""
    idx = state.template_editor_selected
    fields = state.template_editor_fields
    new_idx = idx + direction
    if idx < 0 or idx >= len(fields) or new_idx < 0 or new_idx >= len(fields):
        return
    fields[idx], fields[new_idx] = fields[new_idx], fields[idx]
    state.template_editor_selected = new_idx


def _handle_save_field_edit(state: AppState):
    """Apply field editor modal changes to the in-memory field list."""
    idx = state.field_editor_index
    if idx < 0 or idx >= len(state.template_editor_fields):
        state.modal_open = None
        state.reset_input()
        return

    new_label = state.input_states["field_editor_label"].text.strip()
    new_key = state.input_states["field_editor_key"].text.strip()
    new_type = state.field_editor_type

    if not new_label:
        state.show_toast("Label cannot be empty", "warning")
        return
    if not new_key:
        state.show_toast("Field ID cannot be empty", "warning")
        return

    # Sanitize key
    new_key = new_key.lower().replace(" ", "_")
    new_key = "".join(c for c in new_key if c.isalnum() or c == "_")
    if not new_key:
        state.show_toast("Invalid field ID", "warning")
        return

    # Check for duplicate keys
    for i, other in enumerate(state.template_editor_fields):
        if i != idx and other["key"] == new_key:
            state.show_toast(f"Key '{new_key}' already used", "warning")
            return

    # Single mimage validation
    if new_type == "mimage":
        for i, other in enumerate(state.template_editor_fields):
            if i != idx and other["field_type"] == "mimage":
                state.show_toast("Only one Main Image (mimage) allowed", "warning")
                return

    # Apply changes
    fd = state.template_editor_fields[idx]
    fd["display_name"] = new_label
    fd["key"] = new_key
    fd["field_type"] = new_type

    # Store image dimensions from editor state
    fd["image_width"] = getattr(state, '_field_editor_width', 0) or 0
    fd["image_height"] = getattr(state, '_field_editor_height', 0) or 0
    fd["required"] = state._field_editor_required

    # Default link_targets for link fields
    if new_type == "link" and not fd.get("link_targets"):
        fd["link_targets"] = [state.current_section]
    elif new_type != "link":
        fd["link_targets"] = []

    state.modal_open = None
    state.reset_input()
    state.show_toast("Field updated", "success")


def _handle_delete_field_from_modal(state: AppState):
    """Delete the field being edited from the template field list."""
    idx = state.field_editor_index
    if 0 <= idx < len(state.template_editor_fields):
        fd = state.template_editor_fields[idx]
        if fd["key"] == "name":
            state.show_toast("Cannot delete Name field", "warning")
            state.modal_open = None
            state.reset_input()
            return
        state.template_editor_fields.pop(idx)
        if state.template_editor_selected >= len(state.template_editor_fields):
            state.template_editor_selected = max(0, len(state.template_editor_fields) - 1)
        state.show_toast("Field removed", "info")

    state.modal_open = None
    state.reset_input()


def draw_modal(state: AppState):
    """Draw active modal."""
    if state.modal_open == "create_world":
        action = draw_create_world_modal(state)
        if action == "create":
            handle_create_world(state)
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()

    elif state.modal_open == "open_world":
        action = draw_open_world_modal(state)
        if action == "open":
            handle_open_world(state)
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()

    elif state.modal_open == "fullscreen_edit":
        field_key = state.fullscreen_edit_field
        title = state.fullscreen_edit_title or "Field"
        if field_key:
            action = draw_fullscreen_editor_modal(state, field_key, title)
            if action == "close":
                # Panel-based form persists — just close the modal
                state.modal_open = None
                state.fullscreen_edit_field = None
                state.fullscreen_scroll_offset = 0

    elif state.modal_open == "delete_confirm":
        char_name = state.character_data.get("name", "Unknown") if state.character_data else "Unknown"
        action = draw_delete_confirm_modal(state, char_name)
        if action == "delete":
            handle_delete_character(state)
        elif action == "cancel":
            state.modal_open = None

    elif state.modal_open == "search":
        action = draw_search_modal(state)
        if action == "search":
            state.search_filter = state.text_input
            state.modal_open = None
            state.reset_input()
        elif action == "clear":
            state.search_filter = ""
            state.text_input = ""
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()

    elif state.modal_open == "edit_field":
        action = draw_field_editor_modal(state)
        if action == "save":
            _handle_save_field_edit(state)
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()
        elif action == "delete":
            _handle_delete_field_from_modal(state)

    elif state.modal_open == "delete_world_confirm":
        world_name = ""
        if state.active_world:
            from helpers import get_world_name
            world_name = get_world_name(state.active_world)
        action = draw_delete_world_confirm_modal(state, world_name)
        if action == "delete_world":
            _handle_delete_world(state)
        elif action == "cancel":
            state.modal_open = None

    elif state.modal_open == "era_editor":
        action = draw_era_editor_modal(state)
        if action == "done":
            # Save eras to world.yaml
            from helpers import get_calendar_config, save_calendar_config
            calendar = get_calendar_config(state.active_world) if state.active_world else {}
            calendar["eras"] = state.era_editor_eras
            if state.active_world:
                save_calendar_config(state.active_world, calendar)
            state.timeline_eras = list(state.era_editor_eras)
            state.modal_open = None
            state.reset_input()
            state.show_toast("Eras saved", "success")
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()

    elif state.modal_open == "goto_year":
        action = draw_goto_year_modal(state)
        if action == "goto":
            if state.input_states and "_goto_year" in state.input_states:
                year_text = state.input_states["_goto_year"].text.strip()
                try:
                    state.view_center_year = float(year_text)
                    state.show_toast(f"Jumped to year {year_text}", "info", 1.5)
                except ValueError:
                    state.show_toast("Invalid year", "warning")
            state.modal_open = None
            state.reset_input()
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()

    elif state.modal_open == "link_picker":
        action = draw_link_picker_modal(state)
        if action == "add":
            # Apply selected links to form data
            from helpers import format_link_field
            field_key = state.link_picker_field
            links = [{"section": s["section"], "slug": s["slug"]}
                     for s in state.link_picker_selected]
            state.form_data[field_key] = format_link_field(links)
            state.modal_open = None
            state.link_picker_open = False
        elif action == "cancel":
            state.modal_open = None
            state.link_picker_open = False

    elif state.modal_open == "create_folder":
        action = draw_create_folder_modal(state)
        if action == "create":
            if state.input_states and "_folder_name" in state.input_states:
                folder_name = state.input_states["_folder_name"].text.strip()
                if folder_name and state.active_world:
                    from helpers import create_folder
                    section = getattr(state, 'current_section', 'characters')
                    create_folder(state.active_world, section, folder_name)
                    state.load_entities(section)
                    state.show_toast(f"Folder '{folder_name}' created", "success")
            state.modal_open = None
            state.reset_input()
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()

    elif state.modal_open == "move_to_folder":
        action = draw_move_to_folder_modal(state)
        if action and action.startswith("move:"):
            target_folder = action[5:]
            if target_folder == "_root":
                target_folder = None
            if state.active_world and state.selected_character:
                from helpers import move_entity_to_folder
                section = getattr(state, 'current_section', 'characters')
                new_path = move_entity_to_folder(
                    state.active_world, section,
                    state.selected_character, target_folder)
                state.selected_character = new_path
                state.load_entities(section)
                state.show_toast("Moved to folder", "success")
            state.modal_open = None
            state.reset_input()
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()

    elif state.modal_open == "unsaved_warning":
        action = draw_unsaved_warning_modal(state)
        if action == "discard":
            target = state.pending_navigation or "character_list"
            state.pending_navigation = None
            state.modal_open = None
            state.reset_input()
            state.view_mode = target
        elif action == "keep_editing":
            state.modal_open = None
            state.pending_navigation = None


def _tile_on_hyprland():
    """Ask Hyprland to tile our window (XWayland windows default to floating)."""
    import shutil
    import subprocess
    if shutil.which("hyprctl"):
        subprocess.Popen(
            ["hyprctl", "dispatch", "settiled", "class:codex"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


def main():
    """Main entry point."""
    SetConfigFlags(FLAG_WINDOW_RESIZABLE)
    # Use short lowercase title — raylib sets it as X11 WM_CLASS for window matching
    InitWindow(INITIAL_WIDTH, INITIAL_HEIGHT, b"codex")
    SetWindowTitle(b"Codex - Worldbuilding Companion")
    SetWindowMinSize(800, 600)
    _tile_on_hyprland()
    SetExitKey(0)  # Disable Raylib's default ESC = quit behavior
    SetTargetFPS(60)

    from ui.fonts import init_font
    init_font()

    state = AppState()

    from config import get_recent_worlds
    state.recent_worlds = get_recent_worlds()

    while not WindowShouldClose():
        # Update
        handle_input(state)

        # Handle portrait file picker (blocks between frames)
        if state.portrait_action:
            handle_portrait_action(state)
        if state.image_action:
            handle_image_action(state)

        # Draw
        BeginDrawing()
        ClearBackground(BG_DARK)
        draw_ui(state)
        EndDrawing()

    state.clear_portrait_cache()
    CloseWindow()


if __name__ == "__main__":
    main()
