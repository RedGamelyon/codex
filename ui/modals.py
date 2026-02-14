"""
Codex Modal Dialogs
"""

from pathlib import Path

from raylib import (
    DrawRectangle, DrawRectangleLines, DrawLine,
    GetMousePosition, IsMouseButtonPressed,
    MOUSE_BUTTON_LEFT, BeginScissorMode, EndScissorMode,
    GetMouseWheelMove, GetScreenWidth, GetScreenHeight,
)

from .fonts import draw_text as DrawText, measure_text as MeasureText

from .colors import BORDER, TEXT_DIM, DANGER, RAYWHITE, ACCENT, BG_HOVER, BG_SELECTED, TAG
from .components import (
    draw_button, draw_text_input_stateful,
    TextInputState, calculate_text_input_height
)


def draw_modal_background():
    """Draw the dimmed background overlay."""
    DrawRectangle(0, 0, GetScreenWidth(), GetScreenHeight(), (0, 0, 0, 180))


def draw_modal_box(title: str, width: int = 400, height: int = 200) -> tuple[int, int, int, int]:
    """Draw modal box and return content area (x, y, width, height)."""
    x = (GetScreenWidth() - width) // 2
    y = (GetScreenHeight() - height) // 2

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


def draw_create_world_modal(state) -> str | None:
    """Draw create world modal with name and location picker."""
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Create New World", 500, 380)

    mouse = GetMousePosition()
    action = None

    # Initialize locations if needed
    if not state.default_locations:
        from helpers import get_default_locations
        state.default_locations = get_default_locations()

    # World Name input
    DrawText(b"World Name:", content_x + 20, content_y + 10, 14, TEXT_DIM)
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

    # Stateful text input for world name
    if state.input_states is None:
        state.input_states = {}
    if "_world_name" not in state.input_states:
        state.input_states["_world_name"] = TextInputState(
            text=state.world_name_input, cursor_pos=len(state.world_name_input))
    draw_text_input_stateful(
        name_input_x, name_input_y, name_input_w, name_input_h,
        state.input_states["_world_name"],
        state.input_active and not state.show_custom_location
    )
    state.world_name_input = state.input_states["_world_name"].text

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

        if "_world_custom_path" not in state.input_states:
            state.input_states["_world_custom_path"] = TextInputState(
                text=state.custom_location_input, cursor_pos=len(state.custom_location_input))
        draw_text_input_stateful(
            content_x + 20, custom_input_y, list_w, 35,
            state.input_states["_world_custom_path"],
            state.input_active and state.show_custom_location
        )
        state.custom_location_input = state.input_states["_world_custom_path"].text
        y_offset = custom_input_y + 45

    # Preview
    if state.world_name_input:
        if state.show_custom_location and state.custom_location_input:
            base = state.custom_location_input
            if base.startswith("~"):
                base = str(Path.home()) + base[1:]
            preview = f"{base}/{state.world_name_input}"
        elif state.default_locations and not state.show_custom_location:
            loc = state.default_locations[state.selected_location_index]
            preview = str(loc / state.world_name_input).replace(str(Path.home()), "~")
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


def draw_open_world_modal(state) -> str | None:
    """Draw open world modal with discovered worlds list."""
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Open World", 500, 400)

    mouse = GetMousePosition()
    action = None

    # Discover worlds if not already done
    if not state.discovered_worlds:
        from helpers import discover_worlds
        state.discovered_worlds = discover_worlds()

    # Found worlds section
    DrawText(b"Found Worlds:", content_x + 20, content_y + 10, 14, TEXT_DIM)

    list_x = content_x + 20
    list_y = content_y + 28
    list_w = content_w - 40
    item_h = 32
    list_h = min(item_h * 6, content_h - 180)  # Max 6 items visible

    DrawRectangle(list_x, list_y, list_w, list_h, (30, 30, 45, 255))
    DrawRectangleLines(list_x, list_y, list_w, list_h, BORDER)

    if state.discovered_worlds:
        # Handle scrolling within list
        if list_x <= mouse.x <= list_x + list_w and list_y <= mouse.y <= list_y + list_h:
            wheel = GetMouseWheelMove()
            total_height = len(state.discovered_worlds) * item_h
            max_scroll = max(0, total_height - list_h)
            state.form_scroll_offset -= int(wheel * 30)
            state.form_scroll_offset = max(0, min(state.form_scroll_offset, max_scroll))

        BeginScissorMode(list_x, list_y, list_w, list_h)

        for i, world_path in enumerate(state.discovered_worlds):
            item_y = list_y + i * item_h - state.form_scroll_offset

            if item_y + item_h < list_y or item_y > list_y + list_h:
                continue

            world_name = world_path.name
            world_loc = str(world_path.parent).replace(str(Path.home()), "~")
            display_text = f"{world_name}  ({world_loc})"

            if draw_list_item(list_x + 1, item_y, list_w - 2, item_h, display_text, selected=(i == state.selected_world_index)):
                state.selected_world_index = i

        EndScissorMode()
    else:
        DrawText(b"No worlds found in common locations", list_x + 10, list_y + list_h // 2 - 7, 14, TEXT_DIM)

    # Manual path input section
    manual_y = list_y + list_h + 15
    DrawText(b"Or enter path manually:", content_x + 20, manual_y, 14, TEXT_DIM)

    input_y = manual_y + 18
    input_h = 35

    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if list_x <= mouse.x <= list_x + list_w and input_y <= mouse.y <= input_y + input_h:
            state.input_active = True
            state.selected_world_index = -1
        elif not (list_x <= mouse.x <= list_x + list_w and list_y <= mouse.y <= list_y + list_h):
            state.input_active = False

    if state.input_states is None:
        state.input_states = {}
    if "_world_open_path" not in state.input_states:
        state.input_states["_world_open_path"] = TextInputState(
            text=state.text_input, cursor_pos=len(state.text_input))
    draw_text_input_stateful(
        list_x, input_y, list_w, input_h,
        state.input_states["_world_open_path"], state.input_active
    )
    state.text_input = state.input_states["_world_open_path"].text

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


def draw_delete_world_confirm_modal(state, world_name: str) -> str | None:
    """Draw delete world confirmation modal. Returns action: 'delete_world', 'cancel', or None."""
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Delete World", 450, 220)

    # Warning
    DrawText(f"Delete '{world_name}'?".encode('utf-8'), content_x + 20, content_y + 15, 16, RAYWHITE)
    DrawText(b"This will permanently delete the entire", content_x + 20, content_y + 42, 14, DANGER)
    DrawText(b"world folder and all its contents.", content_x + 20, content_y + 60, 14, DANGER)
    DrawText(b"Characters, templates, and images will be lost.", content_x + 20, content_y + 85, 14, TEXT_DIM)

    # Buttons
    btn_y = content_y + content_h - 55
    action = None

    if draw_button(content_x + 20, btn_y, 140, 35, "Delete World"):
        action = "delete_world"

    if draw_button(content_x + 170, btn_y, 100, 35, "Cancel"):
        action = "cancel"

    return action


def draw_fullscreen_editor_modal(state, field_key: str, title: str) -> str | None:
    """Draw fullscreen text editor for a field. Returns 'close' when done, None otherwise."""
    from raylib import IsKeyPressed, KEY_ESCAPE

    sw = GetScreenWidth()
    sh = GetScreenHeight()

    # Full screen overlay
    DrawRectangle(0, 0, sw, sh, (25, 25, 35, 255))

    # Title bar
    DrawRectangle(0, 0, sw, 50, (35, 35, 50, 255))
    DrawText(f"Edit: {title}".encode('utf-8'), 20, 15, 20, RAYWHITE)
    DrawLine(0, 50, sw, 50, BORDER)

    # Close button
    close_btn_x = sw - 100
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
    editor_w = sw - margin * 2
    editor_h = sh - 90

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
    types = ["text", "multiline", "tags", "number", "link", "image", "mimage"]
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


# --- Timeline Modals ---

ERA_PRESET_COLORS = [
    "#4A90D9",  # Blue
    "#D4AF37",  # Gold
    "#7B68EE",  # Purple
    "#2ECC71",  # Green
    "#E74C3C",  # Red
    "#F39C12",  # Orange
    "#1ABC9C",  # Teal
    "#9B59B6",  # Violet
]


def _parse_hex_color(hex_str: str) -> tuple:
    """Parse hex color string to (r, g, b)."""
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 6:
        try:
            return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
        except ValueError:
            pass
    return (100, 100, 150)


def draw_era_editor_modal(state) -> str | None:
    """Draw era editor modal. Returns 'done' or 'cancel' or None."""
    from raylib import DrawRectangle as _DR, DrawRectangleLines as _DRL

    draw_modal_background()

    modal_w = 520
    modal_h = 480
    content_x, content_y, content_w, content_h = draw_modal_box("Manage Eras", modal_w, modal_h)

    mouse = GetMousePosition()
    action = None

    eras = state.era_editor_eras
    sel = state.era_editor_selected

    # --- Era list ---
    list_x = content_x + 15
    list_y = content_y + 5
    list_w = content_w - 30
    item_h = 30
    list_h = min(item_h * 5, 150)

    _DR(list_x, list_y, list_w, list_h, (30, 30, 45, 255))
    _DRL(list_x, list_y, list_w, list_h, BORDER)

    BeginScissorMode(list_x, list_y, list_w, list_h)
    for i, era in enumerate(eras):
        iy = list_y + i * item_h
        if iy + item_h < list_y or iy > list_y + list_h:
            continue
        is_sel = (i == sel)
        if is_sel:
            _DR(list_x + 1, iy, list_w - 2, item_h, BG_SELECTED)
        hovering = (list_x <= mouse.x <= list_x + list_w and iy <= mouse.y <= iy + item_h)
        if hovering and not is_sel:
            _DR(list_x + 1, iy, list_w - 2, item_h, BG_HOVER)
        if hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            state.era_editor_selected = i
            sel = i
            # Populate input states for editing
            _sync_era_editor_inputs(state, eras[i])

        # Color swatch
        c = _parse_hex_color(era.get("color", "#4A90D9"))
        _DR(list_x + 8, iy + 6, 18, 18, (c[0], c[1], c[2], 255))
        _DRL(list_x + 8, iy + 6, 18, 18, BORDER)

        # Era info
        info = f"{era.get('name', '?')}  ({era.get('start', 0)} - {era.get('end', 0)})"
        DrawText(info.encode('utf-8'), list_x + 32, iy + 8, 13, RAYWHITE if is_sel else TEXT_DIM)
    EndScissorMode()

    if not eras:
        DrawText(b"No eras defined", list_x + 10, list_y + list_h // 2 - 7, 14, TEXT_DIM)

    # --- List buttons ---
    btn_row_y = list_y + list_h + 8
    if draw_button(list_x, btn_row_y, 80, 26, "Add"):
        new_era = {"name": "New Era", "start": 0, "end": 500, "color": ERA_PRESET_COLORS[len(eras) % len(ERA_PRESET_COLORS)]}
        eras.append(new_era)
        state.era_editor_selected = len(eras) - 1
        _sync_era_editor_inputs(state, new_era)

    if sel >= 0 and sel < len(eras):
        if draw_button(list_x + 90, btn_row_y, 80, 26, "Remove"):
            eras.pop(sel)
            if sel >= len(eras):
                state.era_editor_selected = len(eras) - 1
            sel = state.era_editor_selected
            if sel >= 0 and sel < len(eras):
                _sync_era_editor_inputs(state, eras[sel])
            else:
                state.input_states = None

    # --- Edit selected era ---
    edit_y = btn_row_y + 38
    if 0 <= sel < len(eras):
        era = eras[sel]
        DrawText(b"EDIT ERA", list_x, edit_y, 12, TEXT_DIM)
        DrawLine(list_x, edit_y + 15, list_x + list_w, edit_y + 15, BORDER)
        edit_y += 22

        # Initialize input states
        if state.input_states is None:
            state.input_states = {}
            _sync_era_editor_inputs(state, era)

        input_w = list_w - 10

        # Name
        DrawText(b"Name:", list_x, edit_y, 13, TEXT_DIM)
        edit_y += 16
        if "_era_name" not in state.input_states:
            _sync_era_editor_inputs(state, era)
        name_active = state.active_field == "_era_name"
        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if list_x <= mouse.x <= list_x + input_w and edit_y <= mouse.y <= edit_y + 30:
                state.active_field = "_era_name"
        draw_text_input_stateful(list_x, edit_y, input_w, 30, state.input_states["_era_name"], name_active)
        era["name"] = state.input_states["_era_name"].text
        edit_y += 38

        # Start / End on same row
        half_w = (input_w - 20) // 2
        DrawText(b"Start Year:", list_x, edit_y, 13, TEXT_DIM)
        DrawText(b"End Year:", list_x + half_w + 20, edit_y, 13, TEXT_DIM)
        edit_y += 16

        start_active = state.active_field == "_era_start"
        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if list_x <= mouse.x <= list_x + half_w and edit_y <= mouse.y <= edit_y + 30:
                state.active_field = "_era_start"
        draw_text_input_stateful(list_x, edit_y, half_w, 30, state.input_states["_era_start"], start_active)
        try:
            era["start"] = int(state.input_states["_era_start"].text.strip() or "0")
        except ValueError:
            pass

        end_active = state.active_field == "_era_end"
        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if list_x + half_w + 20 <= mouse.x <= list_x + input_w and edit_y <= mouse.y <= edit_y + 30:
                state.active_field = "_era_end"
        draw_text_input_stateful(list_x + half_w + 20, edit_y, half_w, 30, state.input_states["_era_end"], end_active)
        try:
            era["end"] = int(state.input_states["_era_end"].text.strip() or "0")
        except ValueError:
            pass
        edit_y += 38

        # Color presets
        DrawText(b"Color:", list_x, edit_y, 13, TEXT_DIM)
        edit_y += 18
        swatch_size = 24
        swatch_gap = 6
        for ci, preset in enumerate(ERA_PRESET_COLORS):
            sx = list_x + ci * (swatch_size + swatch_gap)
            if sx + swatch_size > list_x + list_w:
                break
            pc = _parse_hex_color(preset)
            is_current = era.get("color", "").upper() == preset.upper()
            _DR(sx, edit_y, swatch_size, swatch_size, (pc[0], pc[1], pc[2], 255))
            border_c = ACCENT if is_current else BORDER
            _DRL(sx, edit_y, swatch_size, swatch_size, border_c)
            if is_current:
                _DRL(sx - 1, edit_y - 1, swatch_size + 2, swatch_size + 2, ACCENT)
            if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and
                    sx <= mouse.x <= sx + swatch_size and edit_y <= mouse.y <= edit_y + swatch_size):
                era["color"] = preset

    # --- Done / Cancel buttons ---
    btn_y = content_y + content_h - 45

    if draw_button(content_x + 20, btn_y, 80, 35, "Done"):
        action = "done"

    if draw_button(content_x + 110, btn_y, 80, 35, "Cancel"):
        action = "cancel"

    return action


def _sync_era_editor_inputs(state, era: dict):
    """Sync text input states to match the given era's values."""
    if state.input_states is None:
        state.input_states = {}
    name = era.get("name", "")
    start = str(era.get("start", 0))
    end = str(era.get("end", 0))
    state.input_states["_era_name"] = TextInputState(text=name, cursor_pos=len(name))
    state.input_states["_era_start"] = TextInputState(text=start, cursor_pos=len(start))
    state.input_states["_era_end"] = TextInputState(text=end, cursor_pos=len(end))


def draw_goto_year_modal(state) -> str | None:
    """Draw 'Go to Year' modal. Returns 'goto', 'cancel', or None."""
    draw_modal_background()

    content_x, content_y, content_w, content_h = draw_modal_box("Go to Year", 350, 180)

    mouse = GetMousePosition()
    action = None

    DrawText(b"Enter year to jump to:", content_x + 20, content_y + 15, 14, TEXT_DIM)

    input_x = content_x + 20
    input_y = content_y + 38
    input_w = content_w - 40
    input_h = 35

    if state.input_states is None:
        state.input_states = {}
    if "_goto_year" not in state.input_states:
        yr = str(int(state.view_center_year))
        state.input_states["_goto_year"] = TextInputState(text=yr, cursor_pos=len(yr))

    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if input_x <= mouse.x <= input_x + input_w and input_y <= mouse.y <= input_y + input_h:
            state.active_field = "_goto_year"

    draw_text_input_stateful(
        input_x, input_y, input_w, input_h,
        state.input_states["_goto_year"],
        state.active_field == "_goto_year"
    )

    # Buttons
    btn_y = content_y + content_h - 50

    if draw_button(content_x + 20, btn_y, 100, 35, "Go"):
        action = "goto"

    if draw_button(content_x + 130, btn_y, 100, 35, "Cancel"):
        action = "cancel"

    return action


# --- Link Picker Modal ---

def draw_link_picker_modal(state) -> str | None:
    """Draw the link picker modal for selecting entities to link.

    Returns 'add', 'cancel', or None.
    """
    draw_modal_background()

    modal_w = 450
    modal_h = 500
    content_x, content_y, content_w, content_h = draw_modal_box(
        f"Select {state.link_picker_field.replace('_', ' ').title()}", modal_w, modal_h)

    mouse = GetMousePosition()
    action = None

    # --- Search input ---
    if state.input_states is None:
        state.input_states = {}
    if "_link_search" not in state.input_states:
        state.input_states["_link_search"] = TextInputState(text="", cursor_pos=0)

    DrawText(b"Search:", content_x + 15, content_y + 10, 14, TEXT_DIM)
    search_x = content_x + 75
    search_w = content_w - 90
    search_y = content_y + 5

    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if search_x <= mouse.x <= search_x + search_w and search_y <= mouse.y <= search_y + 30:
            state.active_field = "_link_search"

    draw_text_input_stateful(
        search_x, search_y, search_w, 30,
        state.input_states["_link_search"],
        state.active_field == "_link_search"
    )

    search_query = state.input_states["_link_search"].text.lower()

    # --- Section tabs (if multiple target sections) ---
    list_y_start = content_y + 45
    targets = state.link_picker_targets
    if len(targets) > 1:
        from helpers import SECTIONS
        tab_x = content_x + 15
        for target in targets:
            meta = SECTIONS.get(target, {})
            tab_label = meta.get("name", target.title()) or target.title()
            tw = MeasureText(tab_label.encode('utf-8'), 13) + 16
            DrawText(tab_label.encode('utf-8'), tab_x, list_y_start + 2, 13, ACCENT)
            tab_x += tw + 5
        list_y_start += 24

    # --- Filter entries ---
    available = state.link_picker_available
    filtered = [e for e in available if search_query in e.get("name", "").lower()]

    # --- Entity list ---
    list_x = content_x + 10
    list_w = content_w - 20
    list_h = content_h - (list_y_start - content_y) - 55
    item_h = 30

    DrawRectangle(list_x, list_y_start, list_w, list_h, (30, 30, 45, 255))
    DrawRectangleLines(list_x, list_y_start, list_w, list_h, BORDER)

    # Scrolling
    if list_x <= mouse.x <= list_x + list_w and list_y_start <= mouse.y <= list_y_start + list_h:
        wheel = GetMouseWheelMove()
        total_height = len(filtered) * item_h
        max_scroll = max(0, total_height - list_h)
        state.link_picker_scroll -= int(wheel * 30)
        state.link_picker_scroll = max(0, min(state.link_picker_scroll, max_scroll))

    BeginScissorMode(list_x, list_y_start, list_w, list_h)

    section_icons = {"characters": "[C]", "locations": "[L]", "timeline": "[T]", "codex": "[X]"}

    for i, entry in enumerate(filtered):
        iy = list_y_start + i * item_h - state.link_picker_scroll
        if iy + item_h < list_y_start or iy > list_y_start + list_h:
            continue

        # Check if already selected
        is_selected = any(
            s.get("section") == entry.get("section") and s.get("slug") == entry.get("slug")
            for s in state.link_picker_selected
        )

        hovering = (list_x <= mouse.x <= list_x + list_w and iy <= mouse.y <= iy + item_h)

        # Row background
        if is_selected:
            DrawRectangle(list_x + 1, iy, list_w - 2, item_h, BG_SELECTED)
        elif hovering:
            DrawRectangle(list_x + 1, iy, list_w - 2, item_h, BG_HOVER)

        # Checkbox
        chk_x = list_x + 10
        chk_size = 16
        chk_y = iy + (item_h - chk_size) // 2
        DrawRectangleLines(chk_x, chk_y, chk_size, chk_size, BORDER)
        if is_selected:
            DrawText(b"X", chk_x + 3, chk_y + 1, 13, ACCENT)

        # Icon + name
        icon = section_icons.get(entry.get("section", ""), "")
        name = entry.get("name", "?")
        label = f"{icon} {name}" if icon else name
        DrawText(label.encode('utf-8'), chk_x + chk_size + 10, iy + 8, 14, RAYWHITE)

        # Toggle on click
        if hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if is_selected:
                state.link_picker_selected = [
                    s for s in state.link_picker_selected
                    if not (s.get("section") == entry.get("section") and s.get("slug") == entry.get("slug"))
                ]
            else:
                state.link_picker_selected.append({
                    "section": entry["section"],
                    "slug": entry["slug"],
                    "name": entry["name"],
                })

    EndScissorMode()

    if not filtered:
        msg = b"No entries found"
        mw = MeasureText(msg, 14)
        DrawText(msg, list_x + (list_w - mw) // 2, list_y_start + list_h // 2 - 7, 14, TEXT_DIM)

    # --- Selected count ---
    sel_count = len(state.link_picker_selected)
    if sel_count > 0:
        sel_text = f"{sel_count} selected"
        DrawText(sel_text.encode('utf-8'), content_x + 15, content_y + content_h - 48, 13, ACCENT)

    # --- Buttons ---
    btn_y = content_y + content_h - 48
    if draw_button(content_x + content_w - 220, btn_y, 100, 35, "Cancel"):
        action = "cancel"
    if draw_button(content_x + content_w - 110, btn_y, 100, 35, "Add"):
        action = "add"

    return action


def draw_create_folder_modal(state) -> str | None:
    """Draw the create folder modal.

    Returns 'create', 'cancel', or None.
    """
    draw_modal_background()

    modal_w = 400
    modal_h = 180
    content_x, content_y, content_w, content_h = draw_modal_box(
        "Create Folder", modal_w, modal_h)

    action = None

    # Input field
    DrawText(b"Folder Name:", content_x + 15, content_y + 15, 14, TEXT_DIM)

    if state.input_states is None:
        state.input_states = {}
    if "_folder_name" not in state.input_states:
        state.input_states["_folder_name"] = TextInputState(text="", cursor_pos=0)

    inp_x = content_x + 15
    inp_y = content_y + 35
    inp_w = content_w - 30
    inp_h = 32

    mouse = GetMousePosition()
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if inp_x <= mouse.x <= inp_x + inp_w and inp_y <= mouse.y <= inp_y + inp_h:
            state.active_field = "_folder_name"

    # Auto-focus on open
    if state.active_field is None:
        state.active_field = "_folder_name"

    draw_text_input_stateful(
        inp_x, inp_y, inp_w, inp_h,
        state.input_states["_folder_name"],
        state.active_field == "_folder_name"
    )

    # Buttons
    btn_y = content_y + content_h - 48
    if draw_button(content_x + content_w - 220, btn_y, 100, 35, "Cancel"):
        action = "cancel"
    if draw_button(content_x + content_w - 110, btn_y, 100, 35, "Create"):
        action = "create"

    return action


def draw_move_to_folder_modal(state) -> str | None:
    """Draw the move-to-folder picker modal.

    Returns 'move:<folder_slug>' or 'move:_root' or 'cancel', or None.
    """
    draw_modal_background()

    modal_w = 400
    # Height based on number of folders
    folder_data = state.folder_data or {"folders": {}, "root_entries": []}
    folder_count = len(folder_data["folders"]) + 1  # +1 for root option
    modal_h = min(400, 120 + folder_count * 32)
    content_x, content_y, content_w, content_h = draw_modal_box(
        "Move to Folder", modal_w, modal_h)

    action = None
    mouse = GetMousePosition()
    item_h = 32
    draw_y = content_y + 10

    # Root option
    label = "(Root / Unsorted)"
    hovering = (content_x + 10 <= mouse.x <= content_x + content_w - 10 and
                draw_y <= mouse.y <= draw_y + item_h)
    if hovering:
        DrawRectangle(content_x + 10, draw_y, content_w - 20, item_h, BG_HOVER)
    DrawText(label.encode('utf-8'), content_x + 25, draw_y + 9, 14, RAYWHITE)
    if hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        action = "move:_root"
    draw_y += item_h

    # Folder options
    for slug in sorted(folder_data["folders"], key=lambda s: s.lower()):
        fd = folder_data["folders"][slug]
        label = f"[F] {fd['name']}"
        hovering = (content_x + 10 <= mouse.x <= content_x + content_w - 10 and
                    draw_y <= mouse.y <= draw_y + item_h)
        if hovering:
            DrawRectangle(content_x + 10, draw_y, content_w - 20, item_h, BG_HOVER)
        DrawText(label.encode('utf-8'), content_x + 25, draw_y + 9, 14, RAYWHITE)
        if hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            action = f"move:{slug}"
        draw_y += item_h

    # Cancel button
    btn_y = content_y + content_h - 45
    if draw_button(content_x + content_w - 120, btn_y, 100, 35, "Cancel"):
        action = "cancel"

    return action
