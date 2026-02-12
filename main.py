"""
Codex - Worldbuilding Companion
A Raylib-based character and worldbuilding management tool.
"""

from pathlib import Path

from raylib import (
    InitWindow, CloseWindow, WindowShouldClose,
    BeginDrawing, EndDrawing, ClearBackground,
    SetTargetFPS, SetExitKey, SetConfigFlags,
    SetWindowTitle, IsKeyPressed, IsKeyDown,
    FLAG_WINDOW_RESIZABLE,
    KEY_ESCAPE, KEY_ENTER,
    KEY_J, KEY_K, KEY_H, KEY_L, KEY_SLASH,
    KEY_LEFT_SHIFT, KEY_RIGHT_SHIFT,
)

from state import AppState
from helpers import (
    create_vault, is_valid_vault,
    save_character, delete_character, save_character_from_template,
    get_character_slug, pick_image_file,
    save_portrait, remove_portrait, rename_portrait_dir
)
from templates import ensure_default_template, get_default_template
from ui.colors import BG_DARK
from ui.panels import (
    draw_header, draw_sections_panel, draw_actions_panel,
    draw_main_panel_dashboard, draw_main_panel_vault,
    draw_main_panel_character_view, draw_main_panel_stats,
    draw_main_panel_template_editor, draw_main_panel_character_form,
    draw_shortcuts_overlay
)
from ui.components import draw_toasts, draw_context_menu
from ui.modals import (
    draw_create_vault_modal, draw_open_vault_modal,
    draw_delete_confirm_modal, draw_search_modal,
    draw_fullscreen_editor_modal,
    draw_field_editor_modal,
    draw_unsaved_warning_modal
)


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720


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
    in_text_field = state.view_mode in ("character_create", "character_edit") or state.modal_open
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
            navigate_away_from_form(state, "character_list")
        elif state.view_mode == "character_edit":
            navigate_away_from_form(state, "character_view")
        elif state.view_mode == "character_view":
            state.view_mode = "character_list"
            state.selected_character = None
            state.character_data = None
        elif state.view_mode == "stats":
            state.view_mode = "character_list"
        elif state.view_mode == "template_editor":
            state.view_mode = "character_list"
        elif state.selected_index >= 0:
            state.selected_index = -1

    # Enter key in modals
    if IsKeyPressed(KEY_ENTER) and state.modal_open:
        if state.modal_open == "create_vault":
            handle_create_vault(state)
        elif state.modal_open == "open_vault":
            handle_open_vault(state)
        elif state.modal_open == "search":
            state.search_filter = state.text_input
            state.modal_open = None
            state.reset_input()

    # Vim navigation (only when no modal and not in form view)
    if not state.modal_open and state.view_mode not in ("character_create", "character_edit"):
        _handle_vim_keys(state)

    # Update toasts
    state.update_toasts()


def _handle_vim_keys(state: AppState):
    """Handle vim-style keyboard navigation."""
    # / opens search (character_list screen only)
    if IsKeyPressed(KEY_SLASH):
        if state.view_mode == "character_list" and state.active_vault:
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


def _get_item_count(state: AppState) -> int:
    """Get navigable item count for the focused panel."""
    if state.focused_panel == "sections":
        return 2
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
        return [("Create Vault", "create_vault"), ("Open Vault", "open_vault")]
    elif state.view_mode == "character_list":
        return [("New Character", "create_character"), ("Search", "search"), ("Templates", "templates"), ("Stats", "stats")]
    elif state.view_mode == "character_view":
        return [("Edit", "edit"), ("Duplicate", "duplicate"), ("Delete", "delete"), ("Back", "back")]
    elif state.view_mode == "character_create":
        return [("Create", "confirm_create"), ("Cancel", "cancel_create")]
    elif state.view_mode == "character_edit":
        return [("Save", "save"), ("Cancel", "cancel")]
    elif state.view_mode == "stats":
        return [("Back", "back_to_vault")]
    elif state.view_mode == "template_editor":
        return [("Edit Field", "edit_field"), ("Add Field", "add_field"), ("Remove Field", "remove_field"),
                ("Move Up", "move_field_up"), ("Move Down", "move_field_down"),
                ("Save", "save_template"), ("Back", "back_to_vault_from_templates")]
    return []


def _handle_vim_enter(state: AppState):
    """Handle Enter key for vim navigation."""
    if state.focused_panel == "sections":
        sections = ["dashboard", "vault"]
        if 0 <= state.selected_index < len(sections):
            section = sections[state.selected_index]
            if section == "dashboard":
                state.view_mode = "dashboard"
                state.selected_character = None
                state.character_data = None
            elif section == "vault" and state.active_vault:
                state.view_mode = "character_list"
                state.selected_character = None
                state.character_data = None
                state.reset_scroll()

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


def handle_create_vault(state: AppState):
    """Handle vault creation."""
    vault_name = state.vault_name_input.strip()
    if not vault_name:
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

    # Create vault path
    vault_path = Path(base_path) / vault_name

    create_vault(str(vault_path))
    state.active_vault = vault_path
    state.load_characters()
    state.load_templates()
    state.view_mode = "character_list"
    state.modal_open = None
    state.reset_input()
    state.show_toast("Vault created!", "success")

    from config import add_recent_vault, get_recent_vaults
    add_recent_vault(vault_path)
    state.recent_vaults = get_recent_vaults()


def handle_open_vault(state: AppState):
    """Handle vault opening."""
    vault_path = None

    # Check if a vault was selected from the list
    if state.selected_vault_index >= 0 and state.discovered_vaults:
        vault_path = state.discovered_vaults[state.selected_vault_index]
    elif state.text_input.strip():
        # Use manual path input
        path = state.text_input.strip()
        if path.startswith("~"):
            path = str(Path.home()) + path[1:]
        vault_path = Path(path)

    if vault_path:
        if is_valid_vault(vault_path):
            state.active_vault = vault_path
            ensure_default_template(vault_path)
            state.load_characters()
            state.load_templates()
            state.view_mode = "character_list"
            state.modal_open = None
            state.reset_input()
            state.error_message = ""
            state.show_toast(f"Opened: {vault_path.name}", "success")

            from config import add_recent_vault, get_recent_vaults
            add_recent_vault(vault_path)
            state.recent_vaults = get_recent_vaults()
        else:
            state.error_message = "Not a valid vault (missing vault.yaml or characters/)"
            state.show_toast("Invalid vault path", "error")


def _open_vault_direct(state: AppState, vault_path: Path):
    """Open a vault directly (from dashboard recent vaults)."""
    if is_valid_vault(vault_path):
        state.active_vault = vault_path
        ensure_default_template(vault_path)
        state.load_characters()
        state.load_templates()
        state.view_mode = "character_list"
        state.show_toast(f"Opened: {vault_path.name}", "success")

        from config import add_recent_vault, get_recent_vaults
        add_recent_vault(vault_path)
        state.recent_vaults = get_recent_vaults()
    else:
        state.show_toast("Vault no longer valid", "error")


def handle_create_character(state: AppState):
    """Handle character creation."""
    if not state.active_vault:
        return

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
    save_character_from_template(state.active_vault, template, state.form_data)

    # Copy any pending images to the character's image directory
    if state.pending_images:
        slug = get_character_slug(name)
        for field_key, img_path in state.pending_images.items():
            from pathlib import Path as P
            if P(img_path).exists():
                save_portrait(state.active_vault, name, img_path, field_key=field_key)

    state.load_characters()
    state.view_mode = "character_list"
    state.reset_input()
    state.show_toast("Character created!", "success")


def handle_save_character(state: AppState):
    """Handle saving edited character."""
    if not state.selected_character or not state.active_vault:
        return

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
        # Rename portrait dir if name changed
        old_name = state.character_data.get("name", "") if state.character_data else ""
        if old_name and old_name != name:
            rename_portrait_dir(state.active_vault, old_name, name)

        # Delete old file
        old_path = state.selected_character
        delete_character(old_path)

        # Save with template
        template = state.active_template or get_default_template()
        new_path = save_character_from_template(state.active_vault, template, state.form_data)

        # Reload
        state.load_characters()
        state.selected_character = new_path
        state.select_character(new_path)
        state.view_mode = "character_view"
        state.reset_input()
        state.show_toast("Changes saved", "success")


def handle_delete_character(state: AppState):
    """Handle character deletion."""
    if state.selected_character:
        # Remove all image files (portrait + custom image fields)
        if state.active_vault and state.character_data:
            char_name = state.character_data.get("name", "")
            if char_name:
                remove_portrait(state.active_vault, char_name, field_key=None)

        delete_character(state.selected_character)
        state.load_characters()
        state.selected_character = None
        state.character_data = None
        state.view_mode = "character_list"
        state.modal_open = None
        state.show_toast("Character deleted", "info")


def handle_duplicate_character(state: AppState):
    """Duplicate the currently viewed character."""
    if not state.active_vault or not state.character_data or not state.selected_character:
        return

    from helpers import get_characters_dir, get_character_slug, get_portrait_dir
    from templates import IMAGE_FIELD_TYPES
    import shutil

    template = state.active_template or get_default_template()
    original_name = state.character_data.get("name", "Unnamed")

    # Generate a unique copy name
    characters_dir = get_characters_dir(state.active_vault)
    copy_name = f"{original_name} (Copy)"
    slug = get_character_slug(copy_name)
    counter = 2
    while (characters_dir / f"{slug}.md").exists():
        copy_name = f"{original_name} (Copy {counter})"
        slug = get_character_slug(copy_name)
        counter += 1

    # Build form data from original character, replacing name
    form_data = {}
    for tf in template.fields:
        if tf.field_type in IMAGE_FIELD_TYPES:
            continue
        if tf.key == "name":
            form_data[tf.key] = copy_name
        else:
            form_data[tf.key] = state.character_data.get(tf.key, "")

    # Save the new character file
    new_path = save_character_from_template(state.active_vault, template, form_data)

    # Copy all images from original character's image directory
    original_slug = get_character_slug(original_name)
    new_slug = get_character_slug(copy_name)
    original_img_dir = get_portrait_dir(state.active_vault, original_slug)
    if original_img_dir.exists():
        new_img_dir = get_portrait_dir(state.active_vault, new_slug)
        new_img_dir.mkdir(parents=True, exist_ok=True)
        for img_file in original_img_dir.iterdir():
            if img_file.is_file():
                shutil.copy2(str(img_file), str(new_img_dir / img_file.name))

    # Reload and open the new character in edit mode
    state.load_characters()
    state.select_character(new_path)
    state.resolve_template_for_character()
    state.prepare_edit_form()
    state._form_data_snapshot = dict(state.form_data)
    state.view_mode = "character_edit"
    state.input_states = None
    state.form_scroll_offset = 0
    state.show_toast("Character duplicated!", "success")


def handle_portrait_action(state: AppState):
    """Handle portrait add/change/remove actions (runs between frames)."""
    action = state.portrait_action
    state.portrait_action = None
    print(f"[DEBUG] handle_portrait_action: action={action!r}")

    if not state.active_vault or not state.character_data:
        print(f"[DEBUG] handle_portrait_action: no vault or character data, aborting")
        return

    name = state.character_data.get("name", "")
    if not name:
        print(f"[DEBUG] handle_portrait_action: empty character name, aborting")
        return

    slug = get_character_slug(name)
    print(f"[DEBUG] handle_portrait_action: name={name!r}, slug={slug!r}")

    if action in ("add", "change"):
        path = pick_image_file()
        if path is None:
            print("[DEBUG] handle_portrait_action: no file selected (cancelled)")
            return

        from pathlib import Path as P
        if not P(path).exists():
            print(f"[ERROR] handle_portrait_action: selected file doesn't exist: {path}")
            state.show_toast("Error: file not found", "error")
            return

        result = save_portrait(state.active_vault, name, path, field_key="portrait")
        if result:
            state.invalidate_portrait(slug, "portrait")
            state.show_toast("Portrait updated", "success")
            print(f"[DEBUG] handle_portrait_action: portrait saved to {result}")
        else:
            state.show_toast("Failed to save portrait — check console", "error")
            print(f"[ERROR] handle_portrait_action: save_portrait returned None")
    elif action == "remove":
        if remove_portrait(state.active_vault, name, field_key="portrait"):
            state.invalidate_portrait(slug, "portrait")
            state.show_toast("Portrait removed", "info")
            print(f"[DEBUG] handle_portrait_action: portrait removed for {name!r}")


def handle_image_action(state: AppState):
    """Handle image field add/change/remove actions (runs between frames).

    Supports two modes:
    - Create mode (view_mode == "character_create"): stores paths in pending_images
    - Normal mode: saves/removes images in the vault immediately
    """
    action = state.image_action
    field_key = state.image_action_field_key
    state.image_action = None
    state.image_action_field_key = None

    if not action or not field_key:
        return

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
            # Store temp path for later (will be copied on character save)
            state.invalidate_portrait("_pending", field_key)
            state.pending_images[field_key] = path
            state.show_toast("Image selected", "success")
        else:
            if not state.active_vault or not state.character_data:
                return
            name = state.character_data.get("name", "")
            if not name:
                return
            slug = get_character_slug(name)
            result = save_portrait(state.active_vault, name, path, field_key=field_key)
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
            if not state.active_vault or not state.character_data:
                return
            name = state.character_data.get("name", "")
            if not name:
                return
            slug = get_character_slug(name)
            if remove_portrait(state.active_vault, name, field_key=field_key):
                state.invalidate_portrait(slug, field_key)
                state.show_toast("Image removed", "info")


def draw_ui(state: AppState):
    """Draw the entire UI."""
    # Draw panels
    draw_header()

    # Sections panel
    section_clicked = draw_sections_panel(state)
    if section_clicked and not state.modal_open:
        if section_clicked == "dashboard":
            if state.view_mode in ("character_create", "character_edit"):
                navigate_away_from_form(state, "dashboard")
            else:
                state.view_mode = "dashboard"
                state.selected_character = None
                state.character_data = None
        elif section_clicked == "vault":
            if state.view_mode in ("character_create", "character_edit"):
                navigate_away_from_form(state, "character_list")
            else:
                state.view_mode = "character_list"
                state.selected_character = None
                state.character_data = None
                state.reset_scroll()

    # Actions panel
    action_clicked = draw_actions_panel(state)
    if action_clicked and not state.modal_open:
        handle_action(state, action_clicked)

    # Main panel
    if state.view_mode == "dashboard":
        clicked_vault = draw_main_panel_dashboard(state)
        if clicked_vault and not state.modal_open:
            _open_vault_direct(state, clicked_vault)
    elif state.view_mode == "character_list":
        char_clicked = draw_main_panel_vault(state)
        if char_clicked is not None and not state.modal_open:
            state.select_character(state.characters[char_clicked])
            state.view_mode = "character_view"
    elif state.view_mode == "character_view":
        draw_main_panel_character_view(state)
    elif state.view_mode == "character_create":
        draw_main_panel_character_form(state, is_create=True)
    elif state.view_mode == "character_edit":
        draw_main_panel_character_form(state, is_create=False)
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


def handle_action(state: AppState, action: str):
    """Handle action button clicks."""
    if action == "create_vault":
        state.modal_open = "create_vault"
        state.input_active = True
    elif action == "open_vault":
        state.modal_open = "open_vault"
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
    elif action == "open_vault_folder":
        if state.active_vault:
            from helpers import open_in_file_manager
            open_in_file_manager(state.active_vault)
    elif action == "edit":
        state.resolve_template_for_character()
        state.prepare_edit_form()
        state._form_data_snapshot = dict(state.form_data)
        state.view_mode = "character_edit"
        state.input_states = None
        state.form_scroll_offset = 0
    elif action == "duplicate":
        handle_duplicate_character(state)
    elif action == "delete":
        state.modal_open = "delete_confirm"
    elif action == "back":
        if state.view_mode in ("character_create", "character_edit"):
            target = "character_view" if state.selected_character else "character_list"
            navigate_away_from_form(state, target)
        else:
            state.view_mode = "character_list"
            state.selected_character = None
            state.character_data = None
    elif action == "back_to_vault":
        state.view_mode = "character_list"
    elif action == "confirm_create":
        handle_create_character(state)
    elif action == "save":
        handle_save_character(state)
    elif action == "cancel":
        navigate_away_from_form(state, "character_view" if state.selected_character else "character_list")
    elif action == "cancel_create":
        navigate_away_from_form(state, "character_list")
    elif action == "templates":
        state.view_mode = "template_editor"
        state.template_editor_selected = 0
        if state.active_template:
            state.template_editor_fields = [
                {"key": f.key, "display_name": f.display_name,
                 "field_type": f.field_type, "required": f.required,
                 "image_width": getattr(f, "image_width", 0),
                 "image_height": getattr(f, "image_height", 0)}
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
    elif action == "back_to_vault_from_templates":
        state.view_mode = "character_list"


def _handle_save_template(state: AppState):
    """Save the currently edited template."""
    from templates import TemplateField, Template, save_template
    if not state.active_template or not state.active_vault:
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
        ))
    state.active_template.fields = fields
    save_template(state.active_vault, state.active_template)
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
    if state.modal_open == "create_vault":
        action = draw_create_vault_modal(state)
        if action == "create":
            handle_create_vault(state)
        elif action == "cancel":
            state.modal_open = None
            state.reset_input()

    elif state.modal_open == "open_vault":
        action = draw_open_vault_modal(state)
        if action == "open":
            handle_open_vault(state)
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
    InitWindow(WINDOW_WIDTH, WINDOW_HEIGHT, b"codex")
    SetWindowTitle(b"Codex - Worldbuilding Companion")
    _tile_on_hyprland()
    SetExitKey(0)  # Disable Raylib's default ESC = quit behavior
    SetTargetFPS(60)

    from ui.fonts import init_font
    init_font()

    state = AppState()

    from config import get_recent_vaults
    state.recent_vaults = get_recent_vaults()

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
