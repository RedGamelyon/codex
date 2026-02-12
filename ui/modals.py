"""
Codex Modal Dialogs
"""

from pathlib import Path

from raylib import (
    DrawRectangle, DrawRectangleLines, DrawLine,
    GetMousePosition, IsMouseButtonPressed,
    MOUSE_BUTTON_LEFT, BeginScissorMode, EndScissorMode,
    GetMouseWheelMove
)

from .fonts import draw_text as DrawText, measure_text as MeasureText

from .colors import BORDER, TEXT_DIM, DANGER, RAYWHITE, ACCENT, BG_HOVER, BG_SELECTED, TAG
from .components import (
    draw_button, draw_text_input_stateful,
    TextInputState, calculate_text_input_height
)


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720


def draw_modal_background():
    """Draw the dimmed background overlay."""
    DrawRectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, (0, 0, 0, 180))


def draw_modal_box(title: str, width: int = 400, height: int = 200) -> tuple[int, int, int, int]:
    """Draw modal box and return content area (x, y, width, height)."""
    x = (WINDOW_WIDTH - width) // 2
    y = (WINDOW_HEIGHT - height) // 2

    # Box
    DrawRectangle(x, y, width, height, (40, 40, 60, 255))
    DrawRectangleLines(x, y, width, height, (100, 100, 140, 255))

    # Title
    DrawText(title.encode('utf-8'), x + 20, y + 15, 20, RAYWHITE)
    DrawLine(x, y + 45, x + width, y + 45, BORDER)

    return (x, y + 50, width, height - 50)


def draw_list_item(x: int, y: int, width: int, height: int, text: str, selected: bool = False) -> bool:
    """Draw a selectable list item. Returns True if clicked."""
    mouse = GetMousePosition()
    hovering = (x <= mouse.x <= x + width) and (y <= mouse.y <= y + height)
    clicked = hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT)

    # Background
    if selected:
        bg_color = BG_SELECTED
    elif hovering:
        bg_color = BG_HOVER
    else:
        bg_color = (35, 35, 50, 255)

    DrawRectangle(x, y, width, height, bg_color)

    # Selection indicator
    if selected:
        DrawRectangle(x, y, 3, height, ACCENT)

    # Text
    prefix = "> " if selected else "  "
    DrawText((prefix + text).encode('utf-8'), x + 8, y + (height - 14) // 2, 14, RAYWHITE)

    return clicked


def draw_create_vault_modal(state) -> str | None:
    """Draw create vault modal with name and location picker."""
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Create New Vault", 500, 380)

    mouse = GetMousePosition()
    action = None

    # Initialize locations if needed
    if not state.default_locations:
        from helpers import get_default_locations
        state.default_locations = get_default_locations()

    # Vault Name input
    DrawText(b"Vault Name:", content_x + 20, content_y + 10, 14, TEXT_DIM)
    name_input_x = content_x + 20
    name_input_y = content_y + 28
    name_input_w = content_w - 40
    name_input_h = 35

    # Handle click to activate name input
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if name_input_x <= mouse.x <= name_input_x + name_input_w and name_input_y <= mouse.y <= name_input_y + name_input_h:
            state.input_active = True
            state.show_custom_location = False
        elif not state.show_custom_location:
            state.input_active = False

    # Stateful text input for vault name
    if state.input_states is None:
        state.input_states = {}
    if "_vault_name" not in state.input_states:
        state.input_states["_vault_name"] = TextInputState(
            text=state.vault_name_input, cursor_pos=len(state.vault_name_input))
    draw_text_input_stateful(
        name_input_x, name_input_y, name_input_w, name_input_h,
        state.input_states["_vault_name"],
        state.input_active and not state.show_custom_location
    )
    state.vault_name_input = state.input_states["_vault_name"].text

    # Location selector
    DrawText(b"Location:", content_x + 20, content_y + 75, 14, TEXT_DIM)

    list_x = content_x + 20
    list_y = content_y + 93
    list_w = content_w - 40
    item_h = 28
    list_h = item_h * 4  # Show 4 items

    DrawRectangle(list_x, list_y, list_w, list_h, (30, 30, 45, 255))
    DrawRectangleLines(list_x, list_y, list_w, list_h, BORDER)

    BeginScissorMode(list_x, list_y, list_w, list_h)

    for i, loc in enumerate(state.default_locations):
        item_y = list_y + i * item_h
        display_text = str(loc).replace(str(Path.home()), "~")
        if draw_list_item(list_x + 1, item_y, list_w - 2, item_h, display_text, selected=(i == state.selected_location_index and not state.show_custom_location)):
            state.selected_location_index = i
            state.show_custom_location = False
            state.input_active = False

    # Custom location option
    custom_y = list_y + len(state.default_locations) * item_h
    if draw_list_item(list_x + 1, custom_y, list_w - 2, item_h, "Custom...", selected=state.show_custom_location):
        state.show_custom_location = True
        state.input_active = False

    EndScissorMode()

    # Custom location input (if selected)
    y_offset = list_y + list_h + 10
    if state.show_custom_location:
        DrawText(b"Custom Path:", content_x + 20, y_offset, 14, TEXT_DIM)
        custom_input_y = y_offset + 18

        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            custom_input_x = content_x + 20
            if custom_input_x <= mouse.x <= custom_input_x + list_w and custom_input_y <= mouse.y <= custom_input_y + 35:
                state.input_active = True

        if "_vault_custom_path" not in state.input_states:
            state.input_states["_vault_custom_path"] = TextInputState(
                text=state.custom_location_input, cursor_pos=len(state.custom_location_input))
        draw_text_input_stateful(
            content_x + 20, custom_input_y, list_w, 35,
            state.input_states["_vault_custom_path"],
            state.input_active and state.show_custom_location
        )
        state.custom_location_input = state.input_states["_vault_custom_path"].text
        y_offset = custom_input_y + 45

    # Preview
    if state.vault_name_input:
        if state.show_custom_location and state.custom_location_input:
            base = state.custom_location_input
            if base.startswith("~"):
                base = str(Path.home()) + base[1:]
            preview = f"{base}/{state.vault_name_input}"
        elif state.default_locations and not state.show_custom_location:
            loc = state.default_locations[state.selected_location_index]
            preview = str(loc / state.vault_name_input).replace(str(Path.home()), "~")
        else:
            preview = ""

        if preview:
            DrawText(b"Will create:", content_x + 20, y_offset, 12, TEXT_DIM)
            DrawText(preview.encode('utf-8'), content_x + 20, y_offset + 14, 12, TAG)

    # Buttons
    btn_y = content_y + content_h - 50
    if draw_button(content_x + 20, btn_y, 100, 35, "Create"):
        action = "create"

    if draw_button(content_x + 130, btn_y, 100, 35, "Cancel"):
        action = "cancel"

    return action


def draw_open_vault_modal(state) -> str | None:
    """Draw open vault modal with discovered vaults list."""
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Open Vault", 500, 400)

    mouse = GetMousePosition()
    action = None

    # Discover vaults if not already done
    if not state.discovered_vaults:
        from helpers import discover_vaults
        state.discovered_vaults = discover_vaults()

    # Found vaults section
    DrawText(b"Found Vaults:", content_x + 20, content_y + 10, 14, TEXT_DIM)

    list_x = content_x + 20
    list_y = content_y + 28
    list_w = content_w - 40
    item_h = 32
    list_h = min(item_h * 6, content_h - 180)  # Max 6 items visible

    DrawRectangle(list_x, list_y, list_w, list_h, (30, 30, 45, 255))
    DrawRectangleLines(list_x, list_y, list_w, list_h, BORDER)

    if state.discovered_vaults:
        # Handle scrolling within list
        if list_x <= mouse.x <= list_x + list_w and list_y <= mouse.y <= list_y + list_h:
            wheel = GetMouseWheelMove()
            total_height = len(state.discovered_vaults) * item_h
            max_scroll = max(0, total_height - list_h)
            state.form_scroll_offset -= int(wheel * 30)
            state.form_scroll_offset = max(0, min(state.form_scroll_offset, max_scroll))

        BeginScissorMode(list_x, list_y, list_w, list_h)

        for i, vault_path in enumerate(state.discovered_vaults):
            item_y = list_y + i * item_h - state.form_scroll_offset

            if item_y + item_h < list_y or item_y > list_y + list_h:
                continue

            vault_name = vault_path.name
            vault_loc = str(vault_path.parent).replace(str(Path.home()), "~")
            display_text = f"{vault_name}  ({vault_loc})"

            if draw_list_item(list_x + 1, item_y, list_w - 2, item_h, display_text, selected=(i == state.selected_vault_index)):
                state.selected_vault_index = i

        EndScissorMode()
    else:
        DrawText(b"No vaults found in common locations", list_x + 10, list_y + list_h // 2 - 7, 14, TEXT_DIM)

    # Manual path input section
    manual_y = list_y + list_h + 15
    DrawText(b"Or enter path manually:", content_x + 20, manual_y, 14, TEXT_DIM)

    input_y = manual_y + 18
    input_h = 35

    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if list_x <= mouse.x <= list_x + list_w and input_y <= mouse.y <= input_y + input_h:
            state.input_active = True
            state.selected_vault_index = -1
        elif not (list_x <= mouse.x <= list_x + list_w and list_y <= mouse.y <= list_y + list_h):
            state.input_active = False

    if state.input_states is None:
        state.input_states = {}
    if "_vault_open_path" not in state.input_states:
        state.input_states["_vault_open_path"] = TextInputState(
            text=state.text_input, cursor_pos=len(state.text_input))
    draw_text_input_stateful(
        list_x, input_y, list_w, input_h,
        state.input_states["_vault_open_path"], state.input_active
    )
    state.text_input = state.input_states["_vault_open_path"].text

    # Error message
    if state.error_message:
        DrawText(state.error_message.encode('utf-8'), content_x + 20, input_y + 40, 14, DANGER)

    # Buttons
    btn_y = content_y + content_h - 50
    if draw_button(content_x + 20, btn_y, 100, 35, "Open"):
        action = "open"

    if draw_button(content_x + 130, btn_y, 100, 35, "Cancel"):
        action = "cancel"

    return action


def draw_unsaved_warning_modal(state) -> str | None:
    """Draw unsaved changes warning modal.

    Returns 'discard', 'keep_editing', or None.
    """
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Unsaved Changes", 400, 180)

    DrawText(b"You have unsaved changes.", content_x + 20, content_y + 20, 16, RAYWHITE)
    DrawText(b"Discard changes and leave?", content_x + 20, content_y + 45, 14, TEXT_DIM)

    btn_y = content_y + content_h - 50
    action = None

    if draw_button(content_x + 20, btn_y, 100, 35, "Discard"):
        action = "discard"

    if draw_button(content_x + 130, btn_y, 120, 35, "Keep Editing"):
        action = "keep_editing"

    return action


def draw_delete_confirm_modal(state, character_name: str) -> str | None:
    """Draw delete confirmation modal. Returns action: 'delete', 'cancel', or None."""
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Confirm Delete", 400, 180)

    # Warning message
    DrawText(f"Delete '{character_name}'?".encode('utf-8'), content_x + 20, content_y + 20, 16, RAYWHITE)
    DrawText(b"This action cannot be undone.", content_x + 20, content_y + 45, 14, TEXT_DIM)

    # Buttons
    btn_y = content_y + content_h - 50
    action = None

    if draw_button(content_x + 20, btn_y, 100, 35, "Delete"):
        action = "delete"

    if draw_button(content_x + 130, btn_y, 100, 35, "Cancel"):
        action = "cancel"

    return action


def draw_fullscreen_editor_modal(state, field_key: str, title: str) -> str | None:
    """Draw fullscreen text editor for a field. Returns 'close' when done, None otherwise."""
    from raylib import IsKeyPressed, KEY_ESCAPE

    # Full screen overlay
    DrawRectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, (25, 25, 35, 255))

    # Title bar
    DrawRectangle(0, 0, WINDOW_WIDTH, 50, (35, 35, 50, 255))
    DrawText(f"Edit: {title}".encode('utf-8'), 20, 15, 20, RAYWHITE)
    DrawLine(0, 50, WINDOW_WIDTH, 50, BORDER)

    # Close button
    close_btn_x = WINDOW_WIDTH - 100
    close_btn_y = 8
    if draw_button(close_btn_x, close_btn_y, 80, 34, "Close"):
        return "close"

    # ESC to close
    if IsKeyPressed(KEY_ESCAPE):
        return "close"

    # Editor area with margins
    margin = 40
    editor_x = margin
    editor_y = 70
    editor_w = WINDOW_WIDTH - margin * 2
    editor_h = WINDOW_HEIGHT - 90

    # Ensure input state exists
    if not hasattr(state, 'input_states') or state.input_states is None:
        state.input_states = {}
    if field_key not in state.input_states:
        initial_text = state.form_data.get(field_key, "")
        state.input_states[field_key] = TextInputState(text=initial_text, cursor_pos=len(initial_text))

    input_state = state.input_states[field_key]

    # Calculate dynamic height for the content
    dynamic_height = calculate_text_input_height(input_state.text, editor_w, editor_h, True)

    # Handle form scrolling if content exceeds editor area
    mouse = GetMousePosition()
    if editor_x <= mouse.x <= editor_x + editor_w and editor_y <= mouse.y <= editor_y + editor_h:
        wheel = GetMouseWheelMove()
        max_scroll = max(0, dynamic_height - editor_h)
        if not hasattr(state, 'fullscreen_scroll_offset'):
            state.fullscreen_scroll_offset = 0
        state.fullscreen_scroll_offset -= int(wheel * 30)
        state.fullscreen_scroll_offset = max(0, min(state.fullscreen_scroll_offset, max_scroll))

    scroll_offset = getattr(state, 'fullscreen_scroll_offset', 0)

    # Draw editor with scissor clipping
    BeginScissorMode(editor_x, editor_y, editor_w, editor_h)

    # Draw the text input at scrolled position
    draw_text_input_stateful(
        editor_x, editor_y - scroll_offset, editor_w, dynamic_height,
        input_state, active=True, multiline=True, expandable=False
    )

    EndScissorMode()

    # Draw scroll indicator if needed
    if dynamic_height > editor_h:
        scrollbar_x = editor_x + editor_w - 10
        scrollbar_h = max(30, int(editor_h * editor_h / dynamic_height))
        max_scroll = dynamic_height - editor_h
        scrollbar_y = editor_y + int((editor_h - scrollbar_h) * scroll_offset / max_scroll) if max_scroll > 0 else editor_y
        DrawRectangle(scrollbar_x, editor_y, 8, editor_h, (35, 35, 50, 255))
        DrawRectangle(scrollbar_x, scrollbar_y, 8, scrollbar_h, (80, 80, 120, 255))

    # Sync back to form_data
    state.form_data[field_key] = input_state.text

    return None


def draw_search_modal(state) -> str | None:
    """Draw search modal. Returns action: 'search', 'clear', 'cancel', or None."""
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Search Characters", 450, 180)

    # Search input
    DrawText(b"Search by name or tag:", content_x + 20, content_y + 15, 14, TEXT_DIM)

    input_x = content_x + 20
    input_y = content_y + 35
    input_w = content_w - 40
    input_h = 35

    # Handle click to activate
    mouse = GetMousePosition()
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if input_x <= mouse.x <= input_x + input_w and input_y <= mouse.y <= input_y + input_h:
            state.input_active = True
        else:
            state.input_active = False

    if state.input_states is None:
        state.input_states = {}
    if "_search_input" not in state.input_states:
        state.input_states["_search_input"] = TextInputState(
            text=state.text_input, cursor_pos=len(state.text_input))
    draw_text_input_stateful(
        input_x, input_y, input_w, input_h,
        state.input_states["_search_input"], state.input_active
    )
    state.text_input = state.input_states["_search_input"].text

    # Buttons
    btn_y = content_y + content_h - 50
    action = None

    if draw_button(content_x + 20, btn_y, 100, 35, "Search"):
        action = "search"

    if draw_button(content_x + 130, btn_y, 100, 35, "Clear"):
        action = "clear"

    if draw_button(content_x + 240, btn_y, 100, 35, "Cancel"):
        action = "cancel"

    return action


def _sanitize_key(label: str) -> str:
    """Convert a display label to a valid field key."""
    key = label.lower().strip().replace(" ", "_")
    return "".join(c for c in key if c.isalnum() or c == "_") or "field"


def draw_field_editor_modal(state) -> str | None:
    """Draw field editor modal for editing a template field's properties.

    Returns 'save', 'cancel', 'delete', or None.
    """
    draw_modal_background()

    # Taller modal when image type is selected (need room for dimension inputs)
    is_image_type = state.field_editor_type in ("image", "mimage")
    modal_h = 430 if is_image_type else 340
    content_x, content_y, content_w, content_h = draw_modal_box("Edit Field", 440, modal_h)

    idx = state.field_editor_index
    if idx < 0 or idx >= len(state.template_editor_fields):
        return "cancel"

    fd = state.template_editor_fields[idx]
    is_name_field = fd["key"] == "name"

    # Initialize input states on first frame
    if state.input_states is None:
        state.input_states = {}
    if "field_editor_label" not in state.input_states:
        label_text = fd["display_name"]
        key_text = fd["key"]
        state.input_states["field_editor_label"] = TextInputState(
            text=label_text, cursor_pos=len(label_text)
        )
        state.input_states["field_editor_key"] = TextInputState(
            text=key_text, cursor_pos=len(key_text)
        )
    if "field_editor_width" not in state.input_states:
        w_val = str(getattr(state, '_field_editor_width', 0) or 0)
        h_val = str(getattr(state, '_field_editor_height', 0) or 0)
        # Show empty string for 0 (means "use default")
        state.input_states["field_editor_width"] = TextInputState(
            text=w_val if w_val != "0" else "", cursor_pos=len(w_val if w_val != "0" else "")
        )
        state.input_states["field_editor_height"] = TextInputState(
            text=h_val if h_val != "0" else "", cursor_pos=len(h_val if h_val != "0" else "")
        )

    mouse = GetMousePosition()
    action = None

    # --- Label input ---
    label_x = content_x + 20
    label_y = content_y + 10
    input_w = content_w - 40
    DrawText(b"Label:", label_x, label_y, 14, TEXT_DIM)

    input_y = label_y + 20
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if label_x <= mouse.x <= label_x + input_w and input_y <= mouse.y <= input_y + 35:
            state.active_field = "field_editor_label"

    draw_text_input_stateful(
        label_x, input_y, input_w, 35,
        state.input_states["field_editor_label"],
        state.active_field == "field_editor_label"
    )

    # --- Field ID input (auto-generated from label unless focused) ---
    key_label_y = input_y + 45
    DrawText(b"Field ID:", label_x, key_label_y, 14, TEXT_DIM)

    key_input_y = key_label_y + 20
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if label_x <= mouse.x <= label_x + input_w and key_input_y <= mouse.y <= key_input_y + 35:
            state.active_field = "field_editor_key"

    # Auto-generate key from label when key field is not active
    if state.active_field != "field_editor_key":
        auto_key = _sanitize_key(state.input_states["field_editor_label"].text)
        key_state = state.input_states["field_editor_key"]
        key_state.text = auto_key
        key_state.cursor_pos = len(auto_key)

    draw_text_input_stateful(
        label_x, key_input_y, input_w, 35,
        state.input_states["field_editor_key"],
        state.active_field == "field_editor_key"
    )
    DrawText(b"(auto-generated from label)", label_x, key_input_y + 38, 12, TEXT_DIM)

    # --- Type selector (two rows for all types) ---
    type_label_y = key_input_y + 58
    DrawText(b"Type:", label_x, type_label_y, 14, TEXT_DIM)

    type_btn_y = type_label_y + 20
    types = ["text", "multiline", "tags", "number", "image", "mimage"]
    btn_x = label_x
    for t in types:
        btn_w = MeasureText(t.encode('utf-8'), 14) + 24
        # Wrap to next row if exceeding width
        if btn_x + btn_w > content_x + content_w - 20:
            btn_x = label_x
            type_btn_y += 34
        is_sel = (state.field_editor_type == t)
        if draw_button(btn_x, type_btn_y, btn_w, 28, t, selected=is_sel):
            state.field_editor_type = t
        btn_x += btn_w + 8

    next_y = type_btn_y + 38

    # --- Required checkbox ---
    req_y = next_y
    DrawText(b"Required:", label_x, req_y + 4, 14, TEXT_DIM)
    chk_x = label_x + 80
    chk_size = 22
    DrawRectangle(chk_x, req_y, chk_size, chk_size, (30, 30, 45, 255))
    DrawRectangleLines(chk_x, req_y, chk_size, chk_size, BORDER)
    if state._field_editor_required:
        DrawText(b"X", chk_x + 5, req_y + 3, 16, ACCENT)
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if chk_x <= mouse.x <= chk_x + chk_size and req_y <= mouse.y <= req_y + chk_size:
            state._field_editor_required = not state._field_editor_required
    next_y = req_y + 30

    # --- Dimension inputs (only for image types) ---
    if is_image_type:
        DrawText(b"Dimensions (0 = default):", label_x, next_y, 14, TEXT_DIM)
        dim_y = next_y + 20
        dim_input_w = 80

        # Width input
        DrawText(b"W:", label_x, dim_y + 8, 14, TEXT_DIM)
        w_input_x = label_x + 25
        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if w_input_x <= mouse.x <= w_input_x + dim_input_w and dim_y <= mouse.y <= dim_y + 35:
                state.active_field = "field_editor_width"
        draw_text_input_stateful(
            w_input_x, dim_y, dim_input_w, 35,
            state.input_states["field_editor_width"],
            state.active_field == "field_editor_width"
        )

        # Height input
        h_label_x = w_input_x + dim_input_w + 20
        DrawText(b"H:", h_label_x, dim_y + 8, 14, TEXT_DIM)
        h_input_x = h_label_x + 25
        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if h_input_x <= mouse.x <= h_input_x + dim_input_w and dim_y <= mouse.y <= dim_y + 35:
                state.active_field = "field_editor_height"
        draw_text_input_stateful(
            h_input_x, dim_y, dim_input_w, 35,
            state.input_states["field_editor_height"],
            state.active_field == "field_editor_height"
        )

        # Parse and store dimensions on state for save handler
        try:
            w_text = state.input_states["field_editor_width"].text.strip()
            state._field_editor_width = int(w_text) if w_text else 0
        except ValueError:
            state._field_editor_width = 0
        try:
            h_text = state.input_states["field_editor_height"].text.strip()
            state._field_editor_height = int(h_text) if h_text else 0
        except ValueError:
            state._field_editor_height = 0

        # Show effective defaults
        from templates import DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_HEIGHT, DEFAULT_MIMAGE_WIDTH, DEFAULT_MIMAGE_HEIGHT
        if state.field_editor_type == "mimage":
            dw, dh = DEFAULT_MIMAGE_WIDTH, DEFAULT_MIMAGE_HEIGHT
        else:
            dw, dh = DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_HEIGHT
        DrawText(f"Default: {dw}x{dh}".encode('utf-8'), h_input_x + dim_input_w + 15, dim_y + 8, 12, TEXT_DIM)
    else:
        # Clear dimension state for non-image types
        state._field_editor_width = 0
        state._field_editor_height = 0

    # --- Bottom buttons ---
    btn_y = content_y + content_h - 45

    if draw_button(content_x + 20, btn_y, 80, 35, "Save"):
        action = "save"

    if draw_button(content_x + 110, btn_y, 80, 35, "Cancel"):
        action = "cancel"

    if not is_name_field:
        if draw_button(content_x + content_w - 120, btn_y, 100, 35, "Delete"):
            action = "delete"

    return action
