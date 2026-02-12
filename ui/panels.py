"""
Codex UI Panels
Drawing functions for the main panel layout.
"""

from raylib import (
    DrawRectangle, DrawRectangleLines, DrawLine,
    BeginScissorMode, EndScissorMode,
    GetMouseWheelMove, GetMousePosition,
    IsMouseButtonPressed, MOUSE_BUTTON_LEFT
)

from .fonts import draw_text as DrawText, measure_text as MeasureText

from time import monotonic

from .colors import BG_PANEL, BG_DARK, BG_SELECTED, BORDER, BORDER_ACTIVE, TEXT, TEXT_DIM, ACCENT, TAG, RAYWHITE
from .components import draw_section_button, draw_button, draw_character_card, draw_scrollbar


# Layout constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
HEADER_HEIGHT = 80
SECTIONS_WIDTH = 150
ACTIONS_WIDTH = 150
MAIN_X = SECTIONS_WIDTH + ACTIONS_WIDTH
MAIN_WIDTH = WINDOW_WIDTH - MAIN_X
PANEL_HEIGHT = WINDOW_HEIGHT - HEADER_HEIGHT


def draw_header():
    """Draw the application header."""
    # Background
    DrawRectangle(0, 0, WINDOW_WIDTH, HEADER_HEIGHT, BG_DARK)

    # Title
    title = b"C O D E X"
    title_width = MeasureText(title, 32)
    DrawText(title, (WINDOW_WIDTH - title_width) // 2, 20, 32, RAYWHITE)

    # Subtitle
    subtitle = b"worldbuilding companion"
    subtitle_width = MeasureText(subtitle, 14)
    DrawText(subtitle, (WINDOW_WIDTH - subtitle_width) // 2, 55, 14, TEXT_DIM)

    # Divider line
    DrawLine(0, HEADER_HEIGHT, WINDOW_WIDTH, HEADER_HEIGHT, BORDER)


def draw_sections_panel(state) -> str | None:
    """Draw the sections panel. Returns clicked section name or None."""
    x = 0
    y = HEADER_HEIGHT
    width = SECTIONS_WIDTH

    DrawRectangle(x, y, width, PANEL_HEIGHT, BG_PANEL)
    border = BORDER_ACTIVE if state.focused_panel == "sections" else BORDER
    DrawRectangleLines(x, y, width, PANEL_HEIGHT, border)

    # Title
    DrawText(b"SECTIONS", x + 10, y + 10, 14, TEXT_DIM)
    DrawLine(x, y + 30, x + width, y + 30, BORDER)

    clicked = None
    focused = state.focused_panel == "sections"

    # Dashboard button
    btn_y = y + 40
    dash_selected = (state.view_mode == "dashboard") or (focused and state.selected_index == 0)
    if draw_section_button(x, btn_y, width - 1, 35, "Dashboard", selected=dash_selected):
        clicked = "dashboard"

    # Vault button
    btn_y += 40
    vault_disabled = state.active_vault is None
    vault_screen = state.view_mode in ("character_list", "character_view", "character_create", "character_edit", "stats")
    vault_selected = vault_screen or (focused and state.selected_index == 1)
    if draw_section_button(x, btn_y, width - 1, 35, "Vault", selected=vault_selected, disabled=vault_disabled):
        if not vault_disabled:
            clicked = "vault"

    return clicked


def draw_actions_panel(state) -> str | None:
    """Draw the actions panel. Returns clicked action name or None."""
    x = SECTIONS_WIDTH
    y = HEADER_HEIGHT
    width = ACTIONS_WIDTH

    DrawRectangle(x, y, width, PANEL_HEIGHT, BG_PANEL)
    border = BORDER_ACTIVE if state.focused_panel == "actions" else BORDER
    DrawRectangleLines(x, y, width, PANEL_HEIGHT, border)

    # Title
    DrawText(b"ACTIONS", x + 10, y + 10, 14, TEXT_DIM)
    DrawLine(x, y + 30, x + width, y + 30, BORDER)

    clicked = None
    btn_y = y + 45
    btn_width = width - 20
    btn_height = 32
    focused = state.focused_panel == "actions"
    btn_idx = 0

    if state.view_mode == "dashboard":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Create Vault", selected=focused and state.selected_index == btn_idx):
            clicked = "create_vault"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Open Vault", selected=focused and state.selected_index == btn_idx):
            clicked = "open_vault"

    elif state.view_mode == "character_list":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "New Character", selected=focused and state.selected_index == btn_idx):
            clicked = "create_character"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Search", selected=focused and state.selected_index == btn_idx):
            clicked = "search"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Templates", selected=focused and state.selected_index == btn_idx):
            clicked = "templates"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Stats", selected=focused and state.selected_index == btn_idx):
            clicked = "stats"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Open Folder", selected=focused and state.selected_index == btn_idx):
            clicked = "open_vault_folder"

    elif state.view_mode == "character_view":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Edit", selected=focused and state.selected_index == btn_idx):
            clicked = "edit"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Duplicate", selected=focused and state.selected_index == btn_idx):
            clicked = "duplicate"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Delete", selected=focused and state.selected_index == btn_idx):
            clicked = "delete"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Back", selected=focused and state.selected_index == btn_idx):
            clicked = "back"

    elif state.view_mode == "character_create":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Create", selected=focused and state.selected_index == btn_idx):
            clicked = "confirm_create"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Cancel", selected=focused and state.selected_index == btn_idx):
            clicked = "cancel_create"

    elif state.view_mode == "character_edit":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Save", selected=focused and state.selected_index == btn_idx):
            clicked = "save"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Cancel", selected=focused and state.selected_index == btn_idx):
            clicked = "cancel"

    elif state.view_mode == "stats":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Back", selected=focused and state.selected_index == btn_idx):
            clicked = "back_to_vault"

    elif state.view_mode == "template_editor":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Edit Field", selected=focused and state.selected_index == btn_idx):
            clicked = "edit_field"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Add Field", selected=focused and state.selected_index == btn_idx):
            clicked = "add_field"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Remove Field", selected=focused and state.selected_index == btn_idx):
            clicked = "remove_field"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Move Up", selected=focused and state.selected_index == btn_idx):
            clicked = "move_field_up"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Move Down", selected=focused and state.selected_index == btn_idx):
            clicked = "move_field_down"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Save", selected=focused and state.selected_index == btn_idx):
            clicked = "save_template"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Back", selected=focused and state.selected_index == btn_idx):
            clicked = "back_to_vault_from_templates"

    return clicked


def draw_main_panel_dashboard(state):
    """Draw the main panel for dashboard screen.

    Returns a Path if a recent vault was clicked, else None.
    """
    from pathlib import Path

    x = MAIN_X
    y = HEADER_HEIGHT
    width = MAIN_WIDTH
    height = PANEL_HEIGHT

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    # Welcome message
    center_x = x + width // 2
    draw_y = y + 60

    welcome = b"Welcome to Codex"
    welcome_width = MeasureText(welcome, 28)
    DrawText(welcome, center_x - welcome_width // 2, draw_y, 28, RAYWHITE)
    draw_y += 40

    subtitle = b"Create or open a vault to get started."
    subtitle_width = MeasureText(subtitle, 16)
    DrawText(subtitle, center_x - subtitle_width // 2, draw_y, 16, TEXT_DIM)
    draw_y += 30

    tip = b"Use the Actions panel to create or open a vault"
    tip_width = MeasureText(tip, 14)
    DrawText(tip, center_x - tip_width // 2, draw_y, 14, ACCENT)
    draw_y += 60

    # Recent vaults
    clicked_vault = None
    if state.recent_vaults:
        DrawLine(x + 40, draw_y, x + width - 40, draw_y, BORDER)
        draw_y += 20

        heading = b"Recent Vaults"
        heading_w = MeasureText(heading, 18)
        DrawText(heading, center_x - heading_w // 2, draw_y, 18, RAYWHITE)
        draw_y += 35

        btn_w = 400
        btn_x = center_x - btn_w // 2
        folder_btn_w = 36
        for vault_path in state.recent_vaults[:5]:
            vault_name = vault_path.name
            vault_dir = str(vault_path.parent)

            # Draw clickable vault entry
            DrawRectangle(btn_x, draw_y, btn_w, 50, BG_PANEL)
            DrawRectangleLines(btn_x, draw_y, btn_w, 50, BORDER)

            DrawText(vault_name.encode('utf-8'), btn_x + 15, draw_y + 8, 16, RAYWHITE)
            # Truncate path if too long
            path_text = vault_dir
            max_path_w = btn_w - folder_btn_w - 30
            if MeasureText(path_text.encode('utf-8'), 12) > max_path_w:
                path_text = "..." + path_text[-(max_path_w // 8):]
            DrawText(path_text.encode('utf-8'), btn_x + 15, draw_y + 28, 12, TEXT_DIM)

            # Folder icon button (right side)
            fb_x = btn_x + btn_w - folder_btn_w - 7
            fb_y = draw_y + 10
            fb_h = 30
            mouse = GetMousePosition()
            fb_hover = fb_x <= mouse.x <= fb_x + folder_btn_w and fb_y <= mouse.y <= fb_y + fb_h
            fb_color = BG_SELECTED if fb_hover else BG_PANEL
            DrawRectangle(fb_x, fb_y, folder_btn_w, fb_h, fb_color)
            DrawRectangleLines(fb_x, fb_y, folder_btn_w, fb_h, BORDER)
            dir_label = b"dir"
            dir_w = MeasureText(dir_label, 12)
            DrawText(dir_label, fb_x + (folder_btn_w - dir_w) // 2, fb_y + 9, 12, TEXT_DIM)

            if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and fb_hover and not state.modal_open):
                from helpers import open_in_file_manager
                open_in_file_manager(vault_path)
            # Click detection (open vault — exclude folder button area)
            elif (IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and
                    btn_x <= mouse.x <= btn_x + btn_w and
                    draw_y <= mouse.y <= draw_y + 50 and
                    not state.modal_open):
                clicked_vault = vault_path

            draw_y += 58

    return clicked_vault


def draw_main_panel_vault(state) -> int | None:
    """Draw the main panel for vault screen. Returns clicked character index or None."""
    x = MAIN_X
    y = HEADER_HEIGHT
    width = MAIN_WIDTH
    height = PANEL_HEIGHT

    DrawRectangle(x, y, width, height, BG_DARK)
    border = BORDER_ACTIVE if state.focused_panel == "main" else BORDER
    DrawRectangleLines(x, y, width, height, border)

    # Vault name header
    from helpers import get_vault_name, read_character, parse_character, sort_characters
    vault_name = get_vault_name(state.active_vault) if state.active_vault else "Unknown"
    DrawText(f"Vault: {vault_name}".encode('utf-8'), x + 15, y + 10, 18, RAYWHITE)
    DrawText(f"{len(state.characters)} character(s)".encode('utf-8'), x + 15, y + 32, 14, TEXT_DIM)

    # Sort button (right-aligned in header)
    sort_labels = {
        "name_asc": "Name A-Z",
        "name_desc": "Name Z-A",
        "date_desc": "Newest",
        "date_asc": "Oldest",
    }
    sort_label = f"Sort: {sort_labels.get(state.sort_mode, 'Name A-Z')}"
    sort_btn_w = 130
    sort_btn_x = x + width - sort_btn_w - 15
    sort_btn_y = y + 15
    if draw_button(sort_btn_x, sort_btn_y, sort_btn_w, 28, sort_label) and not state.modal_open:
        modes = ["name_asc", "name_desc", "date_desc", "date_asc"]
        current_idx = modes.index(state.sort_mode)
        state.sort_mode = modes[(current_idx + 1) % len(modes)]
        state.show_toast(f"Sort: {sort_labels[state.sort_mode]}", "info", 2.0)

    DrawLine(x, y + 55, x + width, y + 55, BORDER)

    # Search filter display
    if state.search_filter:
        DrawText(f"Filter: {state.search_filter}".encode('utf-8'), x + 15, y + 60, 14, ACCENT)
        filter_y_offset = 25
    else:
        filter_y_offset = 0

    # Character list
    list_x = x + 10
    list_y = y + 65 + filter_y_offset
    list_width = width - 30
    list_height = height - 75 - filter_y_offset
    card_height = 85

    # Filter characters
    filtered_chars = []
    for char_path in state.characters:
        if state.search_filter:
            content = read_character(char_path)
            parsed = parse_character(content)
            name_lower = parsed.get("name", "").lower()
            tags = parsed.get("tags", "").lower()
            if state.search_filter.lower() not in name_lower and state.search_filter.lower() not in tags:
                continue
        filtered_chars.append(char_path)

    # Sort characters
    filtered_chars = sort_characters(filtered_chars, state.sort_mode)

    # Store for keyboard navigation
    state.displayed_characters = filtered_chars

    content_height = len(filtered_chars) * card_height

    # Clamp selected_index to valid range
    if state.focused_panel == "main" and filtered_chars:
        if state.selected_index >= len(filtered_chars):
            state.selected_index = len(filtered_chars) - 1

    # Auto-scroll to keep keyboard selection visible
    if state.focused_panel == "main" and 0 <= state.selected_index < len(filtered_chars):
        sel_top = state.selected_index * card_height
        sel_bottom = sel_top + card_height
        view_top = state.scroll_offset
        view_bottom = state.scroll_offset + list_height
        if sel_top < view_top:
            state.scroll_offset = sel_top
        elif sel_bottom > view_bottom:
            state.scroll_offset = sel_bottom - list_height

    # Handle mouse scrolling
    mouse = GetMousePosition()
    if list_x <= mouse.x <= list_x + list_width and list_y <= mouse.y <= list_y + list_height:
        wheel = GetMouseWheelMove()
        state.scroll_offset -= int(wheel * 30)
        max_offset = max(0, content_height - list_height)
        state.scroll_offset = max(0, min(state.scroll_offset, max_offset))

    clicked_index = None

    # Draw characters with scissor mode for clipping
    BeginScissorMode(list_x, list_y, list_width, list_height)

    for i, char_path in enumerate(filtered_chars):
        card_y = list_y + i * card_height - state.scroll_offset

        # Skip if not visible
        if card_y + card_height < list_y or card_y > list_y + list_height:
            continue

        # Parse character data
        content = read_character(char_path)
        parsed = parse_character(content)
        name = parsed.get("name") or char_path.stem
        summary = parsed.get("summary") or ""
        tags_str = parsed.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        # Load thumbnail (priority: mimage → portrait → first image → None)
        from .portraits import get_character_thumbnail
        portrait_tex = get_character_thumbnail(state, name, parsed)

        is_kbd_selected = (state.focused_panel == "main" and state.selected_index == i)
        if draw_character_card(list_x, card_y, list_width - 15, name, summary, tags,
                               selected=is_kbd_selected, modal_open=bool(state.modal_open),
                               portrait_texture=portrait_tex):
            clicked_index = state.characters.index(char_path)

    EndScissorMode()

    # Draw scrollbar
    if content_height > list_height:
        draw_scrollbar(x + width - 18, list_y, list_height, state.scroll_offset, content_height, list_height)

    # Empty state
    if not filtered_chars:
        if state.search_filter:
            msg = b"No characters match your search"
        else:
            msg = b"No characters yet. Create one!"
        msg_width = MeasureText(msg, 16)
        DrawText(msg, x + (width - msg_width) // 2, y + height // 2, 16, TEXT_DIM)

    return clicked_index


def draw_main_panel_character_view(state):
    """Draw the main panel for character view screen."""
    from templates import IMAGE_FIELD_TYPES, FIELD_TYPE_MIMAGE, FIELD_TYPE_TAGS, template_has_image_fields
    from .portraits import (
        get_or_load_portrait, get_or_load_image, draw_portrait, draw_portrait_placeholder,
        draw_image, draw_image_placeholder,
    )

    x = MAIN_X
    y = HEADER_HEIGHT
    width = MAIN_WIDTH
    height = PANEL_HEIGHT

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    if not state.selected_character or not state.character_data:
        DrawText(b"No character selected", x + 20, y + 20, 16, TEXT_DIM)
        return

    data = state.character_data
    content_x = x + 20
    content_y = y + 20
    content_width = width - 50
    name = data.get("name", "Unknown")

    # Determine mode: new image fields vs legacy portrait
    template = state.active_template
    use_new_image_mode = template is not None and template_has_image_fields(template)

    # Handle scrolling
    mouse = GetMousePosition()
    if x <= mouse.x <= x + width and y <= mouse.y <= y + height:
        wheel = GetMouseWheelMove()
        state.view_scroll_offset -= int(wheel * 30)
        state.view_scroll_offset = max(0, state.view_scroll_offset)

    BeginScissorMode(x, y, width, height)

    draw_y = content_y - state.view_scroll_offset

    if use_new_image_mode:
        # --- New Image Mode: render all fields in template order ---
        for tf in template.fields:
            if tf.field_type == FIELD_TYPE_MIMAGE:
                # Centered main image + buttons
                iw = tf.effective_image_width
                ih = tf.effective_image_height
                img_x = content_x + (content_width - iw) // 2
                tex = get_or_load_image(state, name, tf.key)
                if tex is not None:
                    draw_image(tex, img_x, draw_y, iw, ih)
                    DrawRectangleLines(img_x, draw_y, iw, ih, BORDER)
                else:
                    draw_image_placeholder(img_x, draw_y, iw, ih, "No Main Image")

                btn_y = draw_y + ih + 6
                btn_h = 26
                if tex is not None:
                    half_w = (iw - 4) // 2
                    if draw_button(img_x, btn_y, half_w, btn_h, "Change") and not state.modal_open:
                        state.image_action = "change"
                        state.image_action_field_key = tf.key
                    if draw_button(img_x + half_w + 4, btn_y, half_w, btn_h, "Remove") and not state.modal_open:
                        state.image_action = "remove"
                        state.image_action_field_key = tf.key
                else:
                    if draw_button(img_x, btn_y, iw, btn_h, "Add Image") and not state.modal_open:
                        state.image_action = "add"
                        state.image_action_field_key = tf.key
                draw_y = btn_y + btn_h + 15

            elif tf.field_type in IMAGE_FIELD_TYPES:
                # Inline image field + buttons
                iw = tf.effective_image_width
                ih = tf.effective_image_height

                DrawText(tf.display_name.encode('utf-8'), content_x, draw_y, 18, ACCENT)
                draw_y += 25

                tex = get_or_load_image(state, name, tf.key)
                if tex is not None:
                    draw_image(tex, content_x, draw_y, iw, ih)
                    DrawRectangleLines(content_x, draw_y, iw, ih, BORDER)
                else:
                    draw_image_placeholder(content_x, draw_y, iw, ih)

                btn_y = draw_y + ih + 6
                btn_h = 26
                if tex is not None:
                    half_w = (iw - 4) // 2
                    if draw_button(content_x, btn_y, half_w, btn_h, "Change") and not state.modal_open:
                        state.image_action = "change"
                        state.image_action_field_key = tf.key
                    if draw_button(content_x + half_w + 4, btn_y, half_w, btn_h, "Remove") and not state.modal_open:
                        state.image_action = "remove"
                        state.image_action_field_key = tf.key
                else:
                    if draw_button(content_x, btn_y, min(iw, 120), btn_h, "Add Image") and not state.modal_open:
                        state.image_action = "add"
                        state.image_action_field_key = tf.key
                draw_y = btn_y + btn_h + 15

            elif tf.field_type == FIELD_TYPE_TAGS:
                # Tag chips
                tags_str = data.get(tf.key, "")
                if tags_str:
                    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                    if tags:
                        DrawText(tf.display_name.encode('utf-8'), content_x, draw_y, 18, ACCENT)
                        draw_y += 25
                        tag_x = content_x
                        for tag in tags:
                            tag_text = f"[{tag}]"
                            DrawText(tag_text.encode('utf-8'), tag_x, draw_y, 14, TAG)
                            tag_x += MeasureText(tag_text.encode('utf-8'), 14) + 10
                        draw_y += 25

            else:
                # Text section
                section_content = data.get(tf.key, "")
                if section_content:
                    DrawText(tf.display_name.encode('utf-8'), content_x, draw_y, 18, ACCENT)
                    draw_y += 25
                    lines = wrap_text(section_content, content_width, 14)
                    for line in lines:
                        DrawText(line.encode('utf-8'), content_x, draw_y, 14, TEXT)
                        draw_y += 18
                    draw_y += 15

    else:
        # --- Legacy Portrait Mode ---
        PORTRAIT_SIZE = 150
        PORTRAIT_MARGIN = 20
        portrait_right = x + width - 20
        portrait_left = portrait_right - PORTRAIT_SIZE
        portrait_top = content_y

        portrait_tex = get_or_load_portrait(state, name)

        # Portrait area (top-right)
        p_top = portrait_top - state.view_scroll_offset
        if portrait_tex is not None:
            draw_portrait(portrait_tex, portrait_left, p_top, PORTRAIT_SIZE)
            DrawRectangleLines(portrait_left, p_top, PORTRAIT_SIZE, PORTRAIT_SIZE, BORDER)
        else:
            draw_portrait_placeholder(portrait_left, p_top, PORTRAIT_SIZE)

        # Portrait buttons
        btn_y = p_top + PORTRAIT_SIZE + 8
        btn_w = PORTRAIT_SIZE
        btn_h = 26
        if portrait_tex is not None:
            half_w = (btn_w - 4) // 2
            if draw_button(portrait_left, btn_y, half_w, btn_h, "Change") and not state.modal_open:
                state.portrait_action = "change"
            if draw_button(portrait_left + half_w + 4, btn_y, half_w, btn_h, "Remove") and not state.modal_open:
                state.portrait_action = "remove"
        else:
            if draw_button(portrait_left, btn_y, btn_w, btn_h, "Add Portrait") and not state.modal_open:
                state.portrait_action = "add"

        portrait_zone_bottom = portrait_top + PORTRAIT_SIZE + btn_h + 50
        narrow_width = content_width - PORTRAIT_SIZE - PORTRAIT_MARGIN

        # Render fields in template order
        template_fields = state.active_template.fields if state.active_template else []
        if not template_fields:
            # Fallback for no template: default field order
            from templates import get_default_template
            template_fields = get_default_template().fields

        for tf in template_fields:
            if tf.field_type in IMAGE_FIELD_TYPES:
                continue  # Image fields not used in legacy mode

            value = data.get(tf.key, "")
            if not value:
                continue

            effective_width = narrow_width if (draw_y + state.view_scroll_offset < portrait_zone_bottom) else content_width

            if tf.field_type == FIELD_TYPE_TAGS:
                tags = [t.strip() for t in value.split(",") if t.strip()]
                if tags:
                    DrawText(tf.display_name.encode('utf-8'), content_x, draw_y, 18, ACCENT)
                    draw_y += 25
                    tag_x = content_x
                    for tag in tags:
                        tag_text = f"[{tag}]"
                        DrawText(tag_text.encode('utf-8'), tag_x, draw_y, 14, TAG)
                        tag_x += MeasureText(tag_text.encode('utf-8'), 14) + 10
                    draw_y += 25
            else:
                DrawText(tf.display_name.encode('utf-8'), content_x, draw_y, 18, ACCENT)
                draw_y += 25
                lines = wrap_text(value, effective_width, 14)
                for line in lines:
                    DrawText(line.encode('utf-8'), content_x, draw_y, 14, TEXT)
                    draw_y += 18
                draw_y += 15

    EndScissorMode()


def wrap_text(text: str, max_width: int, font_size: int) -> list[str]:
    """Wrap text to fit within max_width."""
    lines = []
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue

        words = paragraph.split()
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if MeasureText(test_line.encode('utf-8'), font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

    return lines


def _draw_image_field_in_form(state, tf, x, y, max_width, is_create=False):
    """Draw an image field in a create/edit form.

    Uses state.pending_images for create mode, vault images for edit mode.
    Buttons set state.image_action for between-frame handling.
    """
    from .portraits import get_or_load_image, load_portrait_texture, draw_image, draw_image_placeholder

    label = f"{tf.display_name}:"
    DrawText(label.encode('utf-8'), x, y, 14, TEXT_DIM)
    img_y = y + 20

    iw = min(tf.effective_image_width, max_width)
    ih = tf.effective_image_height

    texture = None

    if is_create:
        pending_path = state.pending_images.get(tf.key)
        if pending_path:
            cache_key = f"_pending:{tf.key}"
            if cache_key in state.portrait_cache:
                cached = state.portrait_cache[cache_key]
                texture = cached["texture"] if cached else None
            else:
                from pathlib import Path as P
                tex = load_portrait_texture(P(pending_path))
                if tex:
                    state.portrait_cache[cache_key] = {"texture": tex, "path": pending_path}
                    texture = tex
                else:
                    state.portrait_cache[cache_key] = None
    else:
        if state.character_data:
            char_name = state.character_data.get("name", "")
            if char_name:
                texture = get_or_load_image(state, char_name, tf.key)

    if texture:
        draw_image(texture, x, img_y, iw, ih)
        DrawRectangleLines(x, img_y, iw, ih, BORDER)
    else:
        draw_image_placeholder(x, img_y, iw, ih)

    # Buttons below image
    btn_y = img_y + ih + 5
    btn_h = 26

    if texture:
        half_w = (min(iw, 200) - 4) // 2
        if draw_button(x, btn_y, half_w, btn_h, "Change"):
            state.image_action = "change"
            state.image_action_field_key = tf.key
        if draw_button(x + half_w + 4, btn_y, half_w, btn_h, "Remove"):
            state.image_action = "remove"
            state.image_action_field_key = tf.key
    else:
        btn_w = min(iw, 140)
        if draw_button(x, btn_y, btn_w, btn_h, f"Add {tf.display_name}"):
            state.image_action = "add"
            state.image_action_field_key = tf.key


def draw_main_panel_character_form(state, is_create: bool = True):
    """Draw the character create/edit form as a main panel.

    This replaces the old modal-based create/edit character forms.
    Buttons (Create/Save, Cancel) come from the actions panel.
    """
    from .components import draw_text_input_stateful, calculate_text_input_height, TextInputState

    x = MAIN_X
    y = HEADER_HEIGHT
    width = MAIN_WIDTH
    height = PANEL_HEIGHT

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    mouse = GetMousePosition()

    # Title
    if is_create:
        title = "Create Character"
    else:
        name = state.form_data.get("name", "Unknown")
        title = f"Edit: {name}"
    DrawText(title.encode('utf-8'), x + 15, y + 10, 18, RAYWHITE)

    # "* Required" note
    req_label = b"* Required"
    req_w = MeasureText(req_label, 12)
    DrawText(req_label, x + width - req_w - 20, y + 14, 12, TEXT_DIM)

    # Get template and field configs
    from templates import template_fields_to_field_configs, get_default_template, IMAGE_FIELD_TYPES
    template = state.active_template or get_default_template()
    text_configs = template_fields_to_field_configs(template)
    text_config_map = {c.key: c for c in text_configs}

    # Template selector (only if multiple templates)
    header_h = 40
    if len(getattr(state, 'templates', [])) > 1:
        sel_y = y + 35
        DrawText(b"Template:", x + 15, sel_y + 4, 14, TEXT_DIM)
        sel_x = x + 95
        for tmpl in state.templates:
            is_sel = (state.active_template and
                      state.active_template.template_id == tmpl.template_id)
            btn_label = tmpl.name
            btn_w = MeasureText(btn_label.encode('utf-8'), 14) + 20
            if draw_button(sel_x, sel_y, btn_w, 26, btn_label, selected=is_sel):
                state.active_template = tmpl
                state.form_data = {tf2.key: "" for tf2 in tmpl.fields if tf2.field_type not in IMAGE_FIELD_TYPES}
                state._form_data_snapshot = dict(state.form_data)
                state.input_states = None
                state.pending_images = {}
                text_configs = template_fields_to_field_configs(tmpl)
                text_config_map = {c.key: c for c in text_configs}
                template = tmpl
            sel_x += btn_w + 5
        header_h = 70

    DrawLine(x, y + header_h, x + width, y + header_h, BORDER)

    # Form area
    form_x = x + 20
    form_y = y + header_h + 5
    form_w = width - 40
    form_h = height - header_h - 10

    input_w = form_w - 25
    scrollbar_x = x + width - 28

    # Initialize input states for text fields
    if state.input_states is None:
        state.input_states = {}
    for cfg in text_configs:
        if cfg.key not in state.input_states:
            initial_text = state.form_data.get(cfg.key, "")
            state.input_states[cfg.key] = TextInputState(text=initial_text, cursor_pos=len(initial_text))

    # Build render list in template field order (text + image fields)
    field_x = form_x + 5
    field_input_w = input_w - 5
    render_items = []
    total_form_height = 0

    for tf in template.fields:
        if tf.field_type in IMAGE_FIELD_TYPES:
            img_h = tf.effective_image_height
            item_h = 20 + img_h + 35 + 10  # label + image + buttons + spacing
            render_items.append(("image", tf, item_h))
            total_form_height += item_h
        elif tf.key in text_config_map:
            cfg = text_config_map[tf.key]
            input_state = state.input_states[cfg.key]
            dyn_h = calculate_text_input_height(input_state.text, field_input_w, cfg.min_height, cfg.multiline, cfg.expandable)
            item_h = 18 + dyn_h + 10
            render_items.append(("text", cfg, item_h, dyn_h))
            total_form_height += item_h

    # Handle scrolling when mouse is over form area
    if form_x <= mouse.x <= form_x + form_w and form_y <= mouse.y <= form_y + form_h:
        wheel = GetMouseWheelMove()
        max_scroll = max(0, total_form_height - form_h)
        state.form_scroll_offset -= int(wheel * 30)
        state.form_scroll_offset = max(0, min(state.form_scroll_offset, max_scroll))

    # Draw form with scissor clipping
    BeginScissorMode(form_x, form_y, form_w, form_h)

    draw_y = form_y - state.form_scroll_offset

    for item in render_items:
        if item[0] == "text":
            _, cfg, item_h, dyn_h = item

            if draw_y + item_h > form_y - 50 and draw_y < form_y + form_h + 50:
                DrawText(cfg.name.encode('utf-8'), field_x, draw_y, 14, TEXT_DIM)
                input_y = draw_y + 18

                if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
                    if field_x <= mouse.x <= field_x + field_input_w and input_y <= mouse.y <= input_y + dyn_h:
                        if form_y <= input_y <= form_y + form_h:
                            if state.active_field != cfg.key:
                                print(f"[DEBUG] Field focused: {cfg.key}")
                            state.active_field = cfg.key

                is_active = state.active_field == cfg.key
                input_state = state.input_states[cfg.key]
                expand_clicked = draw_text_input_stateful(
                    field_x, input_y, field_input_w, dyn_h, input_state, is_active,
                    multiline=cfg.multiline, expandable=cfg.expandable
                )

                if expand_clicked:
                    state.fullscreen_edit_field = cfg.key
                    state.fullscreen_edit_title = cfg.name.rstrip(':')
                    state.modal_open = "fullscreen_edit"

                state.form_data[cfg.key] = input_state.text

            draw_y += item_h

        elif item[0] == "image":
            _, tf, item_h = item

            if draw_y + item_h > form_y - 50 and draw_y < form_y + form_h + 50:
                _draw_image_field_in_form(state, tf, field_x, draw_y, field_input_w, is_create=is_create)

            draw_y += item_h

    EndScissorMode()

    # Draw scroll indicator if needed
    if total_form_height > form_h:
        scrollbar_h = max(20, int(form_h * form_h / total_form_height))
        max_scroll = total_form_height - form_h
        scrollbar_y = form_y + int((form_h - scrollbar_h) * state.form_scroll_offset / max_scroll) if max_scroll > 0 else form_y
        DrawRectangle(scrollbar_x, form_y, 8, form_h, (25, 25, 35, 255))
        DrawRectangle(scrollbar_x, scrollbar_y, 8, scrollbar_h, (70, 70, 100, 255))


def draw_main_panel_stats(state):
    """Draw the main panel for stats view."""
    x = MAIN_X
    y = HEADER_HEIGHT
    width = MAIN_WIDTH
    height = PANEL_HEIGHT

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    from helpers import get_vault_name, get_vault_stats

    if not state.active_vault:
        return

    vault_name = get_vault_name(state.active_vault)
    stats = get_vault_stats(state.active_vault)

    content_x = x + 30
    content_y = y + 30

    # Title
    DrawText(f"Vault Statistics: {vault_name}".encode('utf-8'), content_x, content_y, 24, RAYWHITE)
    content_y += 50

    # Stats
    DrawText(f"Total Characters: {stats['character_count']}".encode('utf-8'), content_x, content_y, 18, TEXT)
    content_y += 30

    DrawText(f"Unique Tags: {stats['tag_count']}".encode('utf-8'), content_x, content_y, 18, TEXT)
    content_y += 40

    # Tag list
    if stats['tags']:
        DrawText(b"Tags:", content_x, content_y, 16, ACCENT)
        content_y += 25
        tag_x = content_x
        for tag in stats['tags']:
            tag_text = f"[{tag}]"
            tag_width = MeasureText(tag_text.encode('utf-8'), 14)
            if tag_x + tag_width > x + width - 30:
                tag_x = content_x
                content_y += 22
            DrawText(tag_text.encode('utf-8'), tag_x, content_y, 14, TAG)
            tag_x += tag_width + 10


def draw_main_panel_template_editor(state) -> str | None:
    """Draw the main panel for template editor screen.

    Returns 'edit_field' on double-click, or None.
    """
    x = MAIN_X
    y = HEADER_HEIGHT
    width = MAIN_WIDTH
    height = PANEL_HEIGHT
    action = None

    DrawRectangle(x, y, width, height, BG_DARK)
    border = BORDER_ACTIVE if state.focused_panel == "main" else BORDER
    DrawRectangleLines(x, y, width, height, border)

    template = state.active_template
    if not template:
        DrawText(b"No template loaded", x + 20, y + 20, 16, TEXT_DIM)
        return None

    # Title
    DrawText(f"Template Editor: {template.name}".encode('utf-8'), x + 15, y + 10, 18, RAYWHITE)
    DrawText(f"{len(state.template_editor_fields)} field(s)".encode('utf-8'), x + 15, y + 32, 14, TEXT_DIM)

    # Template selector (if multiple templates)
    header_h = 55
    if len(state.templates) > 1:
        tmpl_x = x + 15
        tmpl_y = y + 55
        for tmpl in state.templates:
            btn_text = tmpl.name
            btn_w = MeasureText(btn_text.encode('utf-8'), 14) + 20
            is_sel = (template.template_id == tmpl.template_id)
            if draw_button(tmpl_x, tmpl_y, btn_w, 26, btn_text, selected=is_sel) and not state.modal_open:
                state.active_template = tmpl
                state.template_editor_fields = [
                    {"key": f.key, "display_name": f.display_name,
                     "field_type": f.field_type, "required": f.required,
                     "image_width": getattr(f, "image_width", 0),
                     "image_height": getattr(f, "image_height", 0)}
                    for f in tmpl.fields
                ]
                state.template_editor_selected = 0
            tmpl_x += btn_w + 8
        header_h = 90

    DrawLine(x, y + header_h, x + width, y + header_h, BORDER)

    # Column headers
    col_y = y + header_h + 8
    DrawText(b"KEY", x + 20, col_y, 12, TEXT_DIM)
    DrawText(b"LABEL", x + 180, col_y, 12, TEXT_DIM)
    DrawText(b"TYPE", x + 420, col_y, 12, TEXT_DIM)
    col_y += 18
    DrawLine(x + 15, col_y, x + width - 15, col_y, BORDER)
    col_y += 5

    # Field rows
    row_h = 35
    mouse = GetMousePosition()

    for i, fd in enumerate(state.template_editor_fields):
        row_y = col_y + i * row_h
        is_selected = (state.template_editor_selected == i)
        is_required = fd.get("required", False)

        # Row background
        if is_selected:
            DrawRectangle(x + 10, row_y, width - 20, row_h, BG_SELECTED)

        # Click to select, double-click to edit
        if (x + 10 <= mouse.x <= x + width - 10 and
                row_y <= mouse.y <= row_y + row_h):
            if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
                now = monotonic()
                if (state.template_editor_selected == i and
                        now - state.field_editor_last_click_time < 0.35):
                    action = "edit_field"
                    state.field_editor_last_click_time = 0.0
                else:
                    state.template_editor_selected = i
                    state.field_editor_last_click_time = now

        # Key column
        prefix = "[*] " if is_required else "    "
        key_color = TEXT_DIM if fd["key"] == "name" else TEXT
        DrawText((prefix + fd["key"]).encode('utf-8'), x + 20, row_y + 10, 14, key_color)

        # Display name column
        DrawText(fd["display_name"].encode('utf-8'), x + 180, row_y + 10, 14, RAYWHITE)

        # Type column
        DrawText(fd["field_type"].encode('utf-8'), x + 420, row_y + 10, 14, TAG)

        # Type cycle button (only on selected row)
        if is_selected:
            if draw_button(x + 520, row_y + 4, 60, 26, "Cycle") and not state.modal_open:
                types = ["text", "multiline", "tags", "number", "image", "mimage"]
                cur = types.index(fd["field_type"]) if fd["field_type"] in types else 0
                fd["field_type"] = types[(cur + 1) % len(types)]

    # Help text at bottom
    help_y = y + height - 30
    DrawText(b"[*] = required | j/k: select | Enter/dbl-click: edit | Actions: add/remove/reorder/save",
             x + 15, help_y, 12, TEXT_DIM)

    return action


def draw_shortcuts_overlay():
    """Draw keyboard shortcuts help overlay."""
    from raylib import DrawRectangle

    # Dim background
    DrawRectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, (0, 0, 0, 200))

    # Panel dimensions
    panel_w = 460
    panel_h = 440
    px = (WINDOW_WIDTH - panel_w) // 2
    py = (WINDOW_HEIGHT - panel_h) // 2

    # Panel background + border
    DrawRectangle(px, py, panel_w, panel_h, (30, 30, 45, 255))
    DrawRectangleLines(px, py, panel_w, panel_h, BORDER_ACTIVE)

    # Title
    title = b"KEYBOARD SHORTCUTS"
    tw = MeasureText(title, 20)
    DrawText(title, px + (panel_w - tw) // 2, py + 18, 20, RAYWHITE)

    DrawLine(px + 20, py + 48, px + panel_w - 20, py + 48, BORDER)

    # Shortcut entries: (section, key, description)
    entries = [
        ("NAVIGATION", None, None),
        (None, "j / Down", "Move down in list"),
        (None, "k / Up", "Move up in list"),
        (None, "h / l", "Switch panel focus"),
        (None, "Enter", "Select / Open"),
        (None, "Escape", "Go back / Close modal"),
        (None, "/", "Search characters"),
        ("", None, None),  # spacer
        ("TEXT EDITING", None, None),
        (None, "Ctrl+A", "Select all"),
        (None, "Ctrl+C", "Copy"),
        (None, "Ctrl+X", "Cut"),
        (None, "Ctrl+V", "Paste"),
        (None, "Shift+Left/Right", "Select text"),
        ("", None, None),  # spacer
        ("ACTIONS", None, None),
        (None, "?", "Show this help"),
    ]

    draw_y = py + 60
    key_x = px + 30
    desc_x = px + 210

    for section, key, desc in entries:
        if section is not None and key is None:
            if section == "":
                draw_y += 8
            else:
                DrawText(section.encode('utf-8'), key_x, draw_y, 14, ACCENT)
                draw_y += 20
        elif key is not None:
            DrawText(key.encode('utf-8'), key_x + 10, draw_y, 14, RAYWHITE)
            DrawText(desc.encode('utf-8'), desc_x, draw_y, 14, TEXT_DIM)
            draw_y += 20

    # Close hint at bottom
    hint = b"Press ? or Escape to close"
    hw = MeasureText(hint, 14)
    DrawText(hint, px + (panel_w - hw) // 2, py + panel_h - 30, 14, TEXT_DIM)
