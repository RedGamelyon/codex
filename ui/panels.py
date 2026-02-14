"""
Codex UI Panels
Drawing functions for the main panel layout.
"""

import math
from raylib import (
    DrawRectangle, DrawRectangleLines, DrawLine, DrawCircle,
    BeginScissorMode, EndScissorMode,
    GetMouseWheelMove, GetMousePosition,
    IsMouseButtonPressed, IsMouseButtonDown, MOUSE_BUTTON_LEFT,
    GetScreenWidth, GetScreenHeight,
)

from .fonts import draw_text as DrawText, measure_text as MeasureText

from time import monotonic

from .colors import BG_PANEL, BG_DARK, BG_SELECTED, BORDER, BORDER_ACTIVE, TEXT, TEXT_DIM, ACCENT, TAG, DANGER, RAYWHITE
from .components import draw_section_button, draw_button, draw_character_card, draw_scrollbar


HEADER_HEIGHT = 80


def _layout():
    """Compute layout dimensions from current window size."""
    sw = GetScreenWidth()
    sh = GetScreenHeight()
    sections_w = max(120, min(180, int(sw * 0.12)))
    actions_w = max(120, min(180, int(sw * 0.12)))
    main_x = sections_w + actions_w
    return sw, sh, sections_w, actions_w, main_x, sw - main_x, sh - HEADER_HEIGHT


def draw_header():
    """Draw the application header."""
    sw = GetScreenWidth()

    # Background
    DrawRectangle(0, 0, sw, HEADER_HEIGHT, BG_DARK)

    # Title
    title = b"C O D E X"
    title_width = MeasureText(title, 32)
    DrawText(title, (sw - title_width) // 2, 20, 32, RAYWHITE)

    # Subtitle
    subtitle = b"worldbuilding companion"
    subtitle_width = MeasureText(subtitle, 14)
    DrawText(subtitle, (sw - subtitle_width) // 2, 55, 14, TEXT_DIM)

    # Divider line
    DrawLine(0, HEADER_HEIGHT, sw, HEADER_HEIGHT, BORDER)


def draw_sections_panel(state) -> str | None:
    """Draw the sections panel. Returns clicked section name or None."""
    from helpers import SECTIONS

    _, _, sections_w, _, _, _, panel_h = _layout()
    x = 0
    y = HEADER_HEIGHT
    width = sections_w

    DrawRectangle(x, y, width, panel_h, BG_PANEL)
    border = BORDER_ACTIVE if state.focused_panel == "sections" else BORDER
    DrawRectangleLines(x, y, width, panel_h, border)

    # Title
    title = b"WORLD" if state.active_world else b"SECTIONS"
    DrawText(title, x + 10, y + 10, 14, TEXT_DIM)
    DrawLine(x, y + 30, x + width, y + 30, BORDER)

    clicked = None
    focused = state.focused_panel == "sections"
    btn_h = 30
    btn_idx = 0

    if not state.active_world:
        # No world open — just show Dashboard
        btn_y = y + 40
        dash_selected = (state.view_mode == "dashboard") or (focused and state.selected_index == 0)
        if draw_section_button(x, btn_y, width - 1, btn_h, "Dashboard", selected=dash_selected):
            clicked = "dashboard"
        return clicked

    # --- World is open ---
    btn_y = y + 40

    # Overview
    overview_selected = state.current_section == "overview" or (focused and state.selected_index == btn_idx)
    if draw_section_button(x, btn_y, width - 1, btn_h, "Overview", selected=overview_selected):
        clicked = "overview"
    btn_y += btn_h + 2
    btn_idx += 1

    # Enabled sections (full color)
    section_order = ["characters", "locations", "timeline", "codex"]
    enabled = state.enabled_sections

    for section_key in section_order:
        meta = SECTIONS.get(section_key)
        if not meta:
            continue
        is_enabled = section_key in enabled
        is_current = state.current_section == section_key
        is_selected = is_current or (focused and state.selected_index == btn_idx)

        if is_enabled:
            if draw_section_button(x, btn_y, width - 1, btn_h, meta["name"], selected=is_selected):
                clicked = section_key
        else:
            # Greyed out disabled section
            DrawText(meta["name"].encode('utf-8'), x + 15, btn_y + 8, 14, TEXT_DIM)
            # Click to enable
            mouse = GetMousePosition()
            if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and
                    x <= mouse.x <= x + width and btn_y <= mouse.y <= btn_y + btn_h):
                clicked = f"enable_{section_key}"

        btn_y += btn_h + 2
        btn_idx += 1

    # Divider
    btn_y += 5
    DrawLine(x + 10, btn_y, x + width - 10, btn_y, BORDER)
    btn_y += 8

    # + Section button (only if there are disabled sections)
    disabled_sections = [s for s in section_order if s not in enabled]
    if disabled_sections:
        plus_selected = focused and state.selected_index == btn_idx
        if draw_button(x + 10, btn_y, width - 21, 26, "+ Section", selected=plus_selected):
            state.show_section_popup = not state.show_section_popup
        btn_idx += 1

        # Section popup
        if state.show_section_popup:
            popup_x = x + 10
            popup_y = btn_y + 30
            popup_w = width - 20
            popup_item_h = 28
            popup_h = len(disabled_sections) * popup_item_h + 30

            DrawRectangle(popup_x, popup_y, popup_w, popup_h, (40, 40, 60, 255))
            DrawRectangleLines(popup_x, popup_y, popup_w, popup_h, BORDER_ACTIVE)
            DrawText(b"Enable Section", popup_x + 8, popup_y + 6, 12, TEXT_DIM)

            for i, sec_key in enumerate(disabled_sections):
                item_y = popup_y + 24 + i * popup_item_h
                sec_name = SECTIONS[sec_key]["name"]
                mouse = GetMousePosition()
                hovering = (popup_x <= mouse.x <= popup_x + popup_w and
                            item_y <= mouse.y <= item_y + popup_item_h)
                if hovering:
                    DrawRectangle(popup_x + 2, item_y, popup_w - 4, popup_item_h, BG_SELECTED)
                DrawText(sec_name.encode('utf-8'), popup_x + 15, item_y + 7, 14, RAYWHITE)
                if hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
                    clicked = f"enable_{sec_key}"
                    state.show_section_popup = False

        btn_y += 32

    # Divider before Settings
    btn_y += 5
    DrawLine(x + 10, btn_y, x + width - 10, btn_y, BORDER)
    btn_y += 8

    # Settings (always at bottom area)
    settings_y = max(btn_y, y + panel_h - btn_h - 10)
    settings_selected = state.current_section == "settings" or (focused and state.selected_index == btn_idx)
    if draw_section_button(x, settings_y, width - 1, btn_h, "Settings", selected=settings_selected):
        clicked = "settings"

    return clicked


def draw_actions_panel(state) -> str | None:
    """Draw the actions panel. Returns clicked action name or None."""
    _, _, sections_w, actions_w, _, _, panel_h = _layout()
    x = sections_w
    y = HEADER_HEIGHT
    width = actions_w

    DrawRectangle(x, y, width, panel_h, BG_PANEL)
    border = BORDER_ACTIVE if state.focused_panel == "actions" else BORDER
    DrawRectangleLines(x, y, width, panel_h, border)

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
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Create World", selected=focused and state.selected_index == btn_idx):
            clicked = "create_world"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Open World", selected=focused and state.selected_index == btn_idx):
            clicked = "open_world"

    elif state.view_mode == "overview":
        pass  # Overview has no actions

    elif state.view_mode == "settings":
        pass  # Settings handles its own actions

    elif state.view_mode == "timeline":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Add Event", selected=focused and state.selected_index == btn_idx):
            clicked = "timeline_add_event"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Manage Eras", selected=focused and state.selected_index == btn_idx):
            clicked = "timeline_manage_eras"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Go to Year", selected=focused and state.selected_index == btn_idx):
            clicked = "timeline_goto_year"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Fit All", selected=focused and state.selected_index == btn_idx):
            clicked = "timeline_fit_all"

    elif state.view_mode == "character_list":
        from helpers import SECTIONS as _S
        _sec = getattr(state, 'current_section', 'characters')
        _sing = _S.get(_sec, _S["characters"]).get("singular", "Entry")
        if draw_button(x + 10, btn_y, btn_width, btn_height, f"New {_sing}", selected=focused and state.selected_index == btn_idx):
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
        if draw_button(x + 10, btn_y, btn_width, btn_height, "New Folder", selected=focused and state.selected_index == btn_idx):
            clicked = "new_folder"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Open Dir", selected=focused and state.selected_index == btn_idx):
            clicked = "open_world_folder"

    elif state.view_mode == "character_view":
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Edit", selected=focused and state.selected_index == btn_idx):
            clicked = "edit"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Duplicate", selected=focused and state.selected_index == btn_idx):
            clicked = "duplicate"
        btn_y += 40
        btn_idx += 1
        if draw_button(x + 10, btn_y, btn_width, btn_height, "Move", selected=focused and state.selected_index == btn_idx):
            clicked = "move_to_folder"
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
            clicked = "back_to_world"

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
            clicked = "back_to_world_from_templates"

    return clicked


def draw_main_panel_dashboard(state):
    """Draw the main panel for dashboard screen.

    Returns a Path if a recent world was clicked, else None.
    """
    from pathlib import Path

    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    # Welcome message
    center_x = x + width // 2
    draw_y = y + 60

    welcome = b"Welcome to Codex"
    welcome_width = MeasureText(welcome, 28)
    DrawText(welcome, center_x - welcome_width // 2, draw_y, 28, RAYWHITE)
    draw_y += 40

    subtitle = b"Create or open a world to get started."
    subtitle_width = MeasureText(subtitle, 16)
    DrawText(subtitle, center_x - subtitle_width // 2, draw_y, 16, TEXT_DIM)
    draw_y += 30

    tip = b"Use the Actions panel to create or open a world"
    tip_width = MeasureText(tip, 14)
    DrawText(tip, center_x - tip_width // 2, draw_y, 14, ACCENT)
    draw_y += 60

    # Recent worlds
    clicked_world = None
    if state.recent_worlds:
        DrawLine(x + 40, draw_y, x + width - 40, draw_y, BORDER)
        draw_y += 20

        heading = b"Recent Worlds"
        heading_w = MeasureText(heading, 18)
        DrawText(heading, center_x - heading_w // 2, draw_y, 18, RAYWHITE)
        draw_y += 35

        btn_w = min(400, width - 80)
        btn_x = center_x - btn_w // 2
        folder_btn_w = 36
        for world_path in state.recent_worlds[:5]:
            world_name = world_path.name
            world_dir = str(world_path.parent)

            # Draw clickable world entry
            DrawRectangle(btn_x, draw_y, btn_w, 50, BG_PANEL)
            DrawRectangleLines(btn_x, draw_y, btn_w, 50, BORDER)

            DrawText(world_name.encode('utf-8'), btn_x + 15, draw_y + 8, 16, RAYWHITE)
            # Truncate path if too long
            path_text = world_dir
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
                open_in_file_manager(world_path)
            # Click detection (open world — exclude folder button area)
            elif (IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and
                    btn_x <= mouse.x <= btn_x + btn_w and
                    draw_y <= mouse.y <= draw_y + 50 and
                    not state.modal_open):
                clicked_world = world_path

            draw_y += 58

    return clicked_world


def draw_main_panel_overview(state):
    """Draw the overview page for an open world."""
    from helpers import (
        get_world_name, get_world_description, SECTIONS,
        get_section_count, get_tag_counts, get_recent_activity,
        get_most_connected, load_timeline_events,
    )
    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    if not state.active_world:
        return

    # Handle scrolling
    mouse = GetMousePosition()
    if x <= mouse.x <= x + width and y <= mouse.y <= y + height:
        wheel = GetMouseWheelMove()
        state.view_scroll_offset -= int(wheel * 30)
        state.view_scroll_offset = max(0, state.view_scroll_offset)

    BeginScissorMode(x, y, width, height)

    content_x = x + 30
    content_w = width - 60
    draw_y = y + 30 - state.view_scroll_offset

    # World name
    world_name = get_world_name(state.active_world)
    DrawText(world_name.upper().encode('utf-8'), content_x, draw_y, 24, RAYWHITE)
    draw_y += 35

    # World description
    desc = get_world_description(state.active_world)
    if desc:
        desc_lines = wrap_text(desc, content_w, 14)
        for line in desc_lines:
            DrawText(line.encode('utf-8'), content_x, draw_y, 14, TEXT_DIM)
            draw_y += 18
    draw_y += 15

    # Divider
    DrawLine(content_x, draw_y, content_x + content_w, draw_y, BORDER)
    draw_y += 20

    # --- Section cards ---
    DrawText(b"SECTIONS", content_x, draw_y, 14, TEXT_DIM)
    draw_y += 25

    section_order = ["characters", "locations", "timeline", "codex"]
    enabled = state.enabled_sections
    card_w = min(160, (content_w - 30) // 3)
    card_h = 100
    cards_per_row = max(1, (content_w + 10) // (card_w + 10))

    for i, sec_key in enumerate(section_order):
        meta = SECTIONS.get(sec_key)
        if not meta:
            continue

        col = i % cards_per_row
        row = i // cards_per_row
        cx = content_x + col * (card_w + 10)
        cy = draw_y + row * (card_h + 10)

        is_enabled = sec_key in enabled

        # Card background
        card_bg = BG_PANEL if is_enabled else (25, 25, 35, 255)
        DrawRectangle(cx, cy, card_w, card_h, card_bg)
        DrawRectangleLines(cx, cy, card_w, card_h, BORDER)

        # Section name
        name_text = meta["name"].upper().encode('utf-8')
        name_w = MeasureText(name_text, 14)
        DrawText(name_text, cx + (card_w - name_w) // 2, cy + 12, 14, RAYWHITE if is_enabled else TEXT_DIM)

        if is_enabled:
            count = get_section_count(state.active_world, sec_key)
            count_text = str(count).encode('utf-8')
            count_w = MeasureText(count_text, 24)
            DrawText(count_text, cx + (card_w - count_w) // 2, cy + 35, 24, ACCENT)

            # Description
            desc_text = meta.get("description", "")
            if desc_text:
                dw = MeasureText(desc_text.encode('utf-8'), 10)
                DrawText(desc_text.encode('utf-8'), cx + (card_w - dw) // 2, cy + 62, 10, TEXT_DIM)

            # View All button
            btn_label = "View All"
            btn_w = MeasureText(btn_label.encode('utf-8'), 12) + 16
            btn_x = cx + (card_w - btn_w) // 2
            btn_y = cy + card_h - 30
            if draw_button(btn_x, btn_y, btn_w, 22, btn_label) and not state.modal_open:
                state.current_section = sec_key
                if sec_key == "timeline":
                    state.view_mode = "timeline"
                    state.load_timeline_data()
                else:
                    state.load_entities(sec_key)
                    state.load_templates(sec_key)
                    state.view_mode = "character_list"
                    state.selected_character = None
                    state.character_data = None
                    state.reset_scroll()
        else:
            dis_text = b"(disabled)"
            dis_w = MeasureText(dis_text, 12)
            DrawText(dis_text, cx + (card_w - dis_w) // 2, cy + 40, 12, TEXT_DIM)

            # Enable button
            btn_label = "Enable"
            btn_w = MeasureText(btn_label.encode('utf-8'), 12) + 16
            btn_x = cx + (card_w - btn_w) // 2
            btn_y = cy + card_h - 30
            if draw_button(btn_x, btn_y, btn_w, 22, btn_label) and not state.modal_open:
                from helpers import enable_section
                enable_section(state.active_world, sec_key)
                if sec_key not in state.enabled_sections:
                    state.enabled_sections.append(sec_key)
                state.show_toast(f"{meta['name']} enabled", "success")

    # Advance draw_y past cards
    total_rows = (len(section_order) + cards_per_row - 1) // cards_per_row
    draw_y += total_rows * (card_h + 10) + 15

    # --- Timeline Preview (mini horizontal bar) ---
    if "timeline" in enabled:
        events = load_timeline_events(state.active_world)
        if events:
            DrawLine(content_x, draw_y, content_x + content_w, draw_y, BORDER)
            draw_y += 15
            DrawText(b"TIMELINE PREVIEW", content_x, draw_y, 14, TEXT_DIM)
            draw_y += 22

            # Simple horizontal timeline bar
            bar_x = content_x
            bar_w = content_w
            bar_h = 50
            bar_y = draw_y

            DrawRectangle(bar_x, bar_y, bar_w, bar_h, (30, 30, 45, 255))
            DrawRectangleLines(bar_x, bar_y, bar_w, bar_h, BORDER)

            # Compute year range
            min_year = min(e["date"] for e in events)
            max_year = max(e["date"] for e in events)
            year_span = max(1, max_year - min_year)
            padding = year_span * 0.1
            view_min = min_year - padding
            view_max = max_year + padding
            view_span = max(1, view_max - view_min)

            # Draw axis line
            line_y = bar_y + bar_h // 2
            DrawLine(bar_x + 10, line_y, bar_x + bar_w - 10, line_y, BORDER)

            # Draw events as dots
            for ev in events:
                frac = (ev["date"] - view_min) / view_span
                ex = bar_x + 10 + int(frac * (bar_w - 20))
                DrawCircle(ex, line_y, 4.0, ACCENT)

            # Year labels at ends
            min_label = _format_year(min_year, state)
            max_label = _format_year(max_year, state)
            DrawText(min_label.encode('utf-8'), bar_x + 5, bar_y + bar_h - 15, 10, TEXT_DIM)
            max_lw = MeasureText(max_label.encode('utf-8'), 10)
            DrawText(max_label.encode('utf-8'), bar_x + bar_w - max_lw - 5, bar_y + bar_h - 15, 10, TEXT_DIM)

            # Event count
            ev_count_text = f"{len(events)} event{'s' if len(events) != 1 else ''}"
            DrawText(ev_count_text.encode('utf-8'), bar_x + bar_w - MeasureText(ev_count_text.encode('utf-8'), 11) - 5, bar_y + 3, 11, TEXT_DIM)

            draw_y += bar_h + 15

    # --- Most Connected Entries ---
    connected = get_most_connected(state.active_world, limit=5)
    if connected:
        DrawLine(content_x, draw_y, content_x + content_w, draw_y, BORDER)
        draw_y += 15
        DrawText(b"MOST CONNECTED", content_x, draw_y, 14, TEXT_DIM)
        draw_y += 22

        section_icons = {"characters": "[C]", "locations": "[L]", "timeline": "[T]", "codex": "[X]"}
        for entry in connected:
            icon = section_icons.get(entry["section"], "")
            text = f"{icon} {entry['name']}"
            DrawText(text.encode('utf-8'), content_x + 10, draw_y, 14, TEXT)
            # Reference count badge
            ref_text = f"{entry['count']} ref{'s' if entry['count'] != 1 else ''}"
            rw = MeasureText(ref_text.encode('utf-8'), 12)
            DrawText(ref_text.encode('utf-8'), content_x + content_w - rw, draw_y + 1, 12, ACCENT)
            draw_y += 22

        draw_y += 10

    # --- Tag Breakdown (across all sections) ---
    tag_counts = get_tag_counts(state.active_world)
    if tag_counts:
        DrawLine(content_x, draw_y, content_x + content_w, draw_y, BORDER)
        draw_y += 15
        DrawText(b"TAGS", content_x, draw_y, 14, TEXT_DIM)
        draw_y += 22

        tag_x = content_x
        sorted_tags = sorted(tag_counts.items(), key=lambda t: t[1], reverse=True)
        for tag_name, count in sorted_tags[:20]:
            tag_text = f"{tag_name} ({count})"
            tw = MeasureText(tag_text.encode('utf-8'), 14)
            if tag_x + tw + 15 > content_x + content_w:
                tag_x = content_x
                draw_y += 22
            DrawText(tag_text.encode('utf-8'), tag_x, draw_y, 14, TAG)
            tag_x += tw + 15
        draw_y += 30

    # --- Recent Activity ---
    activity = get_recent_activity(state.active_world, limit=8)
    if activity:
        DrawLine(content_x, draw_y, content_x + content_w, draw_y, BORDER)
        draw_y += 15
        DrawText(b"RECENT ACTIVITY", content_x, draw_y, 14, TEXT_DIM)
        draw_y += 22

        import time as _time_mod
        now = _time_mod.time()
        section_icons = {"characters": "[C]", "locations": "[L]", "timeline": "[T]", "codex": "[X]"}

        for entry in activity:
            age = now - entry["modified"]
            if age < 60:
                age_str = "just now"
            elif age < 3600:
                age_str = f"{int(age / 60)}m ago"
            elif age < 86400:
                age_str = f"{int(age / 3600)}h ago"
            elif age < 604800:
                age_str = f"{int(age / 86400)}d ago"
            else:
                age_str = _time_mod.strftime("%b %d", _time_mod.localtime(entry["modified"]))

            icon = section_icons.get(entry["section"], "")
            entry_text = f"{icon} {entry['name']}"
            DrawText(entry_text.encode('utf-8'), content_x + 10, draw_y, 14, TEXT)

            # Right-aligned timestamp
            age_w = MeasureText(age_str.encode('utf-8'), 12)
            DrawText(age_str.encode('utf-8'), content_x + content_w - age_w, draw_y + 1, 12, TEXT_DIM)
            draw_y += 22

        draw_y += 10

    EndScissorMode()


def _parse_hex_color(hex_str: str) -> tuple:
    """Parse a hex color string like '#4A90D9' to (r, g, b)."""
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 6:
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return (r, g, b)
        except ValueError:
            pass
    return (100, 100, 150)


def _format_year(year: float, state) -> str:
    """Format a year value using the configured time system."""
    yr = int(year)
    neg_label = getattr(state, "timeline_negative_label", "BC")
    if yr < 0:
        return f"{abs(yr)} {neg_label}"
    return str(yr)


def _format_year_with_era(year: float, state) -> str:
    """Format a year with its era name if available."""
    yr_str = _format_year(year, state)
    fmt = getattr(state, "timeline_time_format", "year_only")
    if fmt == "year_only":
        return yr_str
    # Find era for this year
    for era in state.timeline_eras:
        if era.get("start", 0) <= year <= era.get("end", 0):
            era_name = era.get("name", "")
            if era_name:
                if fmt == "era_year":
                    return f"{era_name}, Year {yr_str}"
                else:  # age_year
                    return f"Year {yr_str} — {era_name}"
    return yr_str


def draw_main_panel_timeline(state) -> str | None:
    """Draw the visual timeline panel with event detail card.

    Returns action string or None.
    """
    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h
    action = None

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    # --- Header ---
    DrawText(b"TIMELINE", x + 15, y + 10, 18, RAYWHITE)
    event_count = len(state.timeline_events)
    count_text = f"{event_count} event{'s' if event_count != 1 else ''}"
    DrawText(count_text.encode('utf-8'), x + 15, y + 32, 14, TEXT_DIM)
    DrawLine(x, y + 55, x + width, y + 55, BORDER)

    # --- Layout positions ---
    header_h = 55
    tl_x = x + 20
    tl_w = width - 40
    tl_right = tl_x + tl_w

    era_y = y + header_h + 10
    era_h = 25
    line_y = era_y + era_h + 25
    stem_len = 22
    node_bottom = line_y + stem_len + 38
    zoom_y = node_bottom + 5
    zoom_h = 25
    card_divider_y = zoom_y + zoom_h + 5

    # --- Coordinate conversion ---
    base_ppy = tl_w / 1000.0
    ppy = base_ppy * state.zoom_level
    center_screen_x = tl_x + tl_w / 2

    def year_to_x(yr):
        return center_screen_x + (yr - state.view_center_year) * ppy

    def x_to_year(sx):
        return state.view_center_year + (sx - center_screen_x) / ppy if ppy > 0 else state.view_center_year

    mouse = GetMousePosition()
    in_timeline_area = (tl_x <= mouse.x <= tl_right and
                        y + header_h <= mouse.y <= card_divider_y)

    # --- Scissor for timeline visual area ---
    BeginScissorMode(x + 1, y + header_h + 1, width - 2, card_divider_y - y - header_h)

    # --- Era bands ---
    for era in state.timeline_eras:
        e_start = era.get("start", 0)
        e_end = era.get("end", 0)
        e_color = _parse_hex_color(era.get("color", "#4A90D9"))
        ex1 = max(tl_x, int(year_to_x(e_start)))
        ex2 = min(tl_right, int(year_to_x(e_end)))
        if ex2 > ex1:
            DrawRectangle(ex1, era_y, ex2 - ex1, era_h, (e_color[0], e_color[1], e_color[2], 50))
            DrawRectangleLines(ex1, era_y, ex2 - ex1, era_h, (e_color[0], e_color[1], e_color[2], 80))
            era_name = era.get("name", "")
            nw = MeasureText(era_name.encode('utf-8'), 11)
            label_cx = ex1 + (ex2 - ex1 - nw) // 2
            if label_cx >= tl_x and label_cx + nw <= tl_right:
                DrawText(era_name.encode('utf-8'), label_cx, era_y + 7, 11,
                         (e_color[0], e_color[1], e_color[2], 220))

    # --- Year markers ---
    intervals = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
    target_px = 80
    best_interval = intervals[-1]
    for iv in intervals:
        if iv * ppy >= target_px:
            best_interval = iv
            break

    min_vis = x_to_year(tl_x)
    max_vis = x_to_year(tl_right)

    DrawLine(tl_x, line_y, tl_right, line_y, BORDER)

    first_mark = int(min_vis / best_interval) * best_interval
    mark_year = first_mark
    while mark_year <= max_vis:
        mx = int(year_to_x(mark_year))
        if tl_x <= mx <= tl_right:
            DrawLine(mx, line_y - 4, mx, line_y + 4, TEXT_DIM)
            yr_text = _format_year(mark_year, state)
            tw = MeasureText(yr_text.encode('utf-8'), 10)
            DrawText(yr_text.encode('utf-8'), mx - tw // 2, line_y + 7, 10, TEXT_DIM)
        mark_year += best_interval

    # --- Current year marker ---
    current_yr = getattr(state, "timeline_current_year", None)
    if current_yr is not None:
        cx = year_to_x(current_yr)
        if tl_x <= cx <= tl_right:
            DrawLine(int(cx), era_y, int(cx), line_y + 20, (212, 175, 55, 180))
            now_label = b"Now"
            nw = MeasureText(now_label, 10)
            DrawText(now_label, int(cx) - nw // 2, era_y - 12, 10, (212, 175, 55, 220))

    # --- Event nodes ---
    new_hovered = -1
    drag_idx = state.event_drag_index

    for i, event in enumerate(state.timeline_events):
        # If this event is being dragged, show at mouse position
        if state.event_dragging and i == drag_idx:
            ex = mouse.x
        else:
            ex = year_to_x(event["date"])
        if ex < tl_x - 50 or ex > tl_right + 50:
            continue

        is_selected = (i == state.selected_event_index)
        is_being_dragged = (state.event_dragging and i == drag_idx)
        radius = 8 if is_being_dragged else (7 if is_selected else 5)

        # Check hover (not while dragging another event)
        if not state.event_dragging:
            if abs(mouse.x - ex) < radius + 5 and abs(mouse.y - line_y) < radius + 5:
                new_hovered = i

        is_hovered = (new_hovered == i)

        # Stem
        stem_bottom_y = line_y + stem_len
        DrawLine(int(ex), line_y + radius, int(ex), stem_bottom_y, (150, 150, 170, 120))

        # Node
        if is_being_dragged:
            DrawCircle(int(ex), line_y, 9.0, (255, 200, 80, 255))
        elif is_selected:
            DrawCircle(int(ex), line_y, 8.0, ACCENT)
        elif is_hovered:
            DrawCircle(int(ex), line_y, 7.0, (150, 180, 255, 255))
        else:
            DrawCircle(int(ex), line_y, 5.0, TEXT_DIM)

        # Event name below stem
        name_text = event["name"]
        nw = MeasureText(name_text.encode('utf-8'), 12)
        name_draw_x = int(ex) - nw // 2
        DrawText(name_text.encode('utf-8'), name_draw_x, stem_bottom_y + 3, 12,
                 RAYWHITE if (is_selected or is_being_dragged) else TEXT)

        # Date below name
        if is_being_dragged:
            drag_year = x_to_year(mouse.x)
            date_text = _format_year(drag_year, state)
        else:
            date_text = _format_year(event["date"], state)
        dw = MeasureText(date_text.encode('utf-8'), 10)
        DrawText(date_text.encode('utf-8'), int(ex) - dw // 2, stem_bottom_y + 17, 10,
                 (255, 200, 80, 255) if is_being_dragged else TEXT_DIM)

    state.hovered_event_index = new_hovered

    EndScissorMode()

    # --- Event drag handling ---
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and in_timeline_area and new_hovered >= 0 and not state.event_dragging:
        state.event_drag_index = new_hovered
        state.event_drag_start_x = mouse.x
        state.event_drag_original_date = state.timeline_events[new_hovered]["date"]

    if state.event_drag_index >= 0 and not state.event_dragging:
        if IsMouseButtonDown(MOUSE_BUTTON_LEFT):
            if abs(mouse.x - state.event_drag_start_x) > 5:
                state.event_dragging = True
        else:
            # Mouse released without dragging — it's a click
            clicked_idx = state.event_drag_index
            now = monotonic()
            if (state.selected_event_index == clicked_idx and
                    now - state._timeline_last_click_time < 0.35):
                action = "timeline_edit_event"
                state._timeline_last_click_time = 0.0
            else:
                state.selected_event_index = clicked_idx
                # Load event data for detail card
                if 0 <= clicked_idx < len(state.timeline_events):
                    state.selected_event_data = dict(state.timeline_events[clicked_idx])
                state._timeline_last_click_time = now
            state.event_drag_index = -1

    if state.event_dragging:
        if IsMouseButtonDown(MOUSE_BUTTON_LEFT):
            pass  # Visual feedback handled above in node drawing
        else:
            # Released — finalize drag
            new_year = x_to_year(mouse.x)
            drag_i = state.event_drag_index
            if 0 <= drag_i < len(state.timeline_events):
                state.timeline_events[drag_i]["date"] = new_year
                action = "timeline_drag_complete"
            state.event_dragging = False
            state.event_drag_index = -1

    # --- Panning (only when not interacting with an event) ---
    if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and in_timeline_area
            and new_hovered < 0 and state.event_drag_index < 0):
        # Click on empty area deselects event
        state.selected_event_index = -1
        state.selected_event_data = None
        state.timeline_dragging = True
        state.timeline_drag_start_x = mouse.x
        state.timeline_drag_start_year = state.view_center_year

    if state.timeline_dragging:
        if IsMouseButtonDown(MOUSE_BUTTON_LEFT):
            dx = mouse.x - state.timeline_drag_start_x
            if ppy > 0:
                state.view_center_year = state.timeline_drag_start_year - dx / ppy
        else:
            state.timeline_dragging = False

    # --- Zooming (mouse wheel) ---
    if in_timeline_area:
        wheel = GetMouseWheelMove()
        if wheel != 0:
            mouse_year = x_to_year(mouse.x)
            if wheel > 0:
                state.zoom_level *= 1.15
            else:
                state.zoom_level /= 1.15
            state.zoom_level = max(0.01, min(100.0, state.zoom_level))
            new_ppy = base_ppy * state.zoom_level
            if new_ppy > 0:
                state.view_center_year = mouse_year - (mouse.x - center_screen_x) / new_ppy

    # --- Zoom controls ---
    DrawLine(x, zoom_y - 5, x + width, zoom_y - 5, BORDER)
    zoom_label = f"Zoom: {state.zoom_level:.1f}x"
    DrawText(zoom_label.encode('utf-8'), tl_x, zoom_y + 4, 12, TEXT_DIM)

    zoom_ctrl_x = tl_x + 100
    if draw_button(zoom_ctrl_x, zoom_y, 28, 22, "-"):
        state.zoom_level = max(0.01, state.zoom_level / 1.3)
    zoom_ctrl_x += 33

    slider_x = zoom_ctrl_x
    slider_w = min(200, tl_w - 200)
    if slider_w > 30:
        slider_cy = zoom_y + 11
        DrawLine(slider_x, slider_cy, slider_x + slider_w, slider_cy, BORDER)
        min_z, max_z = 0.01, 100.0
        zoom_frac = (math.log(state.zoom_level) - math.log(min_z)) / (math.log(max_z) - math.log(min_z))
        zoom_frac = max(0.0, min(1.0, zoom_frac))
        knob_x = slider_x + int(zoom_frac * slider_w)
        DrawRectangle(knob_x - 4, slider_cy - 4, 8, 8, ACCENT)
        if IsMouseButtonDown(MOUSE_BUTTON_LEFT):
            if slider_x <= mouse.x <= slider_x + slider_w and slider_cy - 10 <= mouse.y <= slider_cy + 10:
                new_frac = (mouse.x - slider_x) / slider_w
                new_frac = max(0.0, min(1.0, new_frac))
                state.zoom_level = math.exp(math.log(min_z) + new_frac * (math.log(max_z) - math.log(min_z)))
        zoom_ctrl_x = slider_x + slider_w + 8

    if draw_button(zoom_ctrl_x, zoom_y, 28, 22, "+"):
        state.zoom_level = min(100.0, state.zoom_level * 1.3)

    # --- Card divider ---
    DrawLine(x, card_divider_y, x + width, card_divider_y, BORDER)

    # --- Event detail card or empty message ---
    card_y = card_divider_y + 1
    card_h = max(0, y + height - card_y)

    if state.selected_event_data and 0 <= state.selected_event_index < len(state.timeline_events):
        event = state.selected_event_data
        card_action = _draw_event_detail_card(
            state, event, x, card_y, width, card_h, tl_x, tl_w)
        if card_action:
            action = card_action
    elif not state.timeline_events:
        empty_msg = b"No events yet. Use 'Add Event' to create one."
        ew = MeasureText(empty_msg, 14)
        DrawText(empty_msg, x + (width - ew) // 2, card_y + card_h // 2 - 7, 14, TEXT_DIM)
    else:
        hint_msg = b"Click an event to view details"
        hw = MeasureText(hint_msg, 14)
        DrawText(hint_msg, x + (width - hw) // 2, card_y + card_h // 2 - 7, 14, TEXT_DIM)

    return action


def _draw_event_detail_card(state, event: dict, x: int, card_y: int,
                             width: int, card_h: int, tl_x: int, tl_w: int) -> str | None:
    """Draw the event detail card in the lower portion of the timeline panel."""
    from .portraits import get_or_load_image, draw_image

    mouse = GetMousePosition()
    action = None

    # Scrolling
    if x <= mouse.x <= x + width and card_y <= mouse.y <= card_y + card_h:
        wheel = GetMouseWheelMove()
        state.view_scroll_offset -= int(wheel * 30)
        state.view_scroll_offset = max(0, state.view_scroll_offset)

    BeginScissorMode(x + 1, card_y, width - 2, card_h)

    content_x = tl_x
    content_w = tl_w
    draw_y = card_y + 10 - state.view_scroll_offset

    # --- Top row: image (left) + info (right) ---
    img_w = 160
    img_h = 110
    event_name = event.get("name", "Unknown")
    tex = get_or_load_image(state, event_name, "image")

    info_x = content_x
    if tex is not None:
        draw_image(tex, content_x, draw_y, img_w, img_h)
        DrawRectangleLines(content_x, draw_y, img_w, img_h, BORDER)
        info_x = content_x + img_w + 15

    # Name
    DrawText(event_name.upper().encode('utf-8'), info_x, draw_y, 20, RAYWHITE)
    # Date + Era
    date_era = _format_year_with_era(event.get("date", 0), state)
    DrawText(date_era.encode('utf-8'), info_x, draw_y + 26, 14, ACCENT)

    # Tags
    tags_str = event.get("tags", "")
    if tags_str:
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        if tags:
            tag_x = info_x
            tag_y = draw_y + 46
            for tag in tags:
                tag_text = f"[{tag}]"
                DrawText(tag_text.encode('utf-8'), tag_x, tag_y, 12, TAG)
                tag_x += MeasureText(tag_text.encode('utf-8'), 12) + 8

    # Short description preview next to image
    desc = event.get("description", "")
    if desc and tex is not None:
        preview_w = content_w - img_w - 15
        preview = desc[:200]
        lines = wrap_text(preview, preview_w, 13)
        dy = draw_y + 65
        for line in lines[:3]:
            DrawText(line.encode('utf-8'), info_x, dy, 13, TEXT)
            dy += 17

    top_h = max(img_h if tex else 50, 70)
    draw_y += top_h + 10

    # Divider
    DrawLine(content_x, draw_y, content_x + content_w, draw_y, BORDER)
    draw_y += 10

    # --- Full description ---
    if desc:
        DrawText(b"Description:", content_x, draw_y, 14, ACCENT)
        draw_y += 20
        desc_lines = wrap_text(desc, content_w, 13)
        for line in desc_lines:
            DrawText(line.encode('utf-8'), content_x, draw_y, 13, TEXT)
            draw_y += 17
        draw_y += 10

    # --- Characters Involved ---
    chars = event.get("characters_involved", "")
    if chars:
        DrawText(b"Characters Involved:", content_x, draw_y, 14, ACCENT)
        draw_y += 20
        for line in wrap_text(chars, content_w, 13):
            DrawText(line.encode('utf-8'), content_x, draw_y, 13, TEXT)
            draw_y += 17
        draw_y += 10

    # --- Locations ---
    locs = event.get("locations", "")
    if locs:
        DrawText(b"Locations:", content_x, draw_y, 14, ACCENT)
        draw_y += 20
        for line in wrap_text(locs, content_w, 13):
            DrawText(line.encode('utf-8'), content_x, draw_y, 13, TEXT)
            draw_y += 17
        draw_y += 10

    # --- Consequences ---
    consequences = event.get("consequences", "")
    if consequences:
        DrawText(b"Consequences:", content_x, draw_y, 14, ACCENT)
        draw_y += 20
        for cline in consequences.split("\n"):
            cline = cline.strip()
            if not cline:
                continue
            bullet = cline
            if not bullet.startswith("- ") and not bullet.startswith("* "):
                bullet = f"- {bullet}"
            for wl in wrap_text(bullet, content_w - 10, 13):
                DrawText(wl.encode('utf-8'), content_x + 10, draw_y, 13, TEXT)
                draw_y += 17
        draw_y += 10

    EndScissorMode()

    # --- Action buttons (fixed at bottom of card) ---
    btn_y = card_y + card_h - 38
    DrawRectangle(x + 1, btn_y - 5, width - 2, 43, BG_DARK)
    DrawLine(x, btn_y - 5, x + width, btn_y - 5, BORDER)

    btn_right = tl_x + tl_w
    btn_w = 70
    btn_h = 28
    gap = 8

    if draw_button(btn_right - btn_w, btn_y, btn_w, btn_h, "Close"):
        action = "timeline_close_card"
    if draw_button(btn_right - btn_w * 2 - gap, btn_y, btn_w, btn_h, "Delete"):
        action = "timeline_delete_event"
    if draw_button(btn_right - btn_w * 3 - gap * 2, btn_y, btn_w, btn_h, "Edit"):
        action = "timeline_edit_event"

    return action


def draw_main_panel_world(state) -> str | None:
    """Draw the main panel for world screen (entity list with folders).

    Returns an action string or None:
        "select:<index>"          - entity card clicked (index into state.characters)
        "folder_create"           - New Folder button clicked
        "folder_move:<path>"      - Move to Folder requested for an entity
    """
    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h

    DrawRectangle(x, y, width, height, BG_DARK)
    border = BORDER_ACTIVE if state.focused_panel == "main" else BORDER
    DrawRectangleLines(x, y, width, height, border)

    # Section header
    from helpers import read_character, parse_character, sort_characters, SECTIONS
    section = getattr(state, 'current_section', 'characters')
    section_meta = SECTIONS.get(section, SECTIONS["characters"])
    section_name = section_meta["name"]
    singular = section_meta.get("singular", "Entry")
    DrawText(section_name.upper().encode('utf-8'), x + 15, y + 10, 18, RAYWHITE)
    count = len(state.characters)
    count_label = f"{count} {singular.lower()}{'s' if count != 1 else ''}" if count != 1 else f"1 {singular.lower()}"
    DrawText(count_label.encode('utf-8'), x + 15, y + 32, 14, TEXT_DIM)

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

    # Entity list area
    list_x = x + 10
    list_y = y + 65 + filter_y_offset
    list_width = width - 30
    list_height = height - 75 - filter_y_offset
    card_height = 85
    folder_header_h = 36
    action = None

    # Build display list: interleave folder headers and entity cards
    # Each item is ("folder", slug, display_name, entry_count, is_collapsed)
    #           or ("entry", char_path, flat_index)
    display_items = []
    flat_chars = []  # for keyboard navigation (entries only)
    folder_data = state.folder_data

    if state.search_filter and folder_data:
        # When searching, flatten all entries and filter
        all_entries = []
        for fd in folder_data["folders"].values():
            all_entries.extend(fd["entries"])
        all_entries.extend(folder_data["root_entries"])

        for char_path in all_entries:
            content = read_character(char_path)
            parsed = parse_character(content)
            name_lower = parsed.get("name", "").lower()
            tags = parsed.get("tags", "").lower()
            if (state.search_filter.lower() not in name_lower and
                    state.search_filter.lower() not in tags):
                continue
            flat_chars.append(char_path)

        flat_chars = sort_characters(flat_chars, state.sort_mode)
        for i, cp in enumerate(flat_chars):
            display_items.append(("entry", cp, i))

    elif folder_data and (folder_data["folders"] or folder_data["root_entries"]):
        # Folder-aware display
        flat_idx = 0

        # Folders first (sorted by name)
        for slug in sorted(folder_data["folders"], key=lambda s: s.lower()):
            fd = folder_data["folders"][slug]
            collapse_key = f"{section}/{slug}"
            is_collapsed = state.folder_collapsed.get(collapse_key, False)
            entries = sort_characters(fd["entries"], state.sort_mode)
            display_items.append(("folder", slug, fd["name"], len(entries), is_collapsed))

            if not is_collapsed:
                for cp in entries:
                    flat_chars.append(cp)
                    display_items.append(("entry", cp, flat_idx))
                    flat_idx += 1
            else:
                # Still add to flat_chars for indexing but skip display
                for cp in entries:
                    flat_chars.append(cp)
                    flat_idx += 1

        # Root entries (unsorted section)
        root_entries = sort_characters(folder_data["root_entries"], state.sort_mode)
        if root_entries and folder_data["folders"]:
            display_items.append(("divider", "Unsorted"))

        for cp in root_entries:
            flat_chars.append(cp)
            display_items.append(("entry", cp, flat_idx))
            flat_idx += 1

        # New Folder button at end
        display_items.append(("new_folder",))

    else:
        # Fallback: flat list from state.characters (no folder data)
        filtered_chars = list(state.characters)
        if state.search_filter:
            filtered_chars = []
            for char_path in state.characters:
                content = read_character(char_path)
                parsed = parse_character(content)
                name_lower = parsed.get("name", "").lower()
                tags = parsed.get("tags", "").lower()
                if (state.search_filter.lower() not in name_lower and
                        state.search_filter.lower() not in tags):
                    continue
                filtered_chars.append(char_path)

        filtered_chars = sort_characters(filtered_chars, state.sort_mode)
        for i, cp in enumerate(filtered_chars):
            flat_chars.append(cp)
            display_items.append(("entry", cp, i))

    # Store for keyboard navigation
    state.displayed_characters = flat_chars

    # Compute total content height
    content_height = 0
    for item in display_items:
        if item[0] == "folder":
            content_height += folder_header_h
        elif item[0] == "entry":
            # Check if inside a collapsed folder
            content_height += card_height
        elif item[0] == "divider":
            content_height += 30
        elif item[0] == "new_folder":
            content_height += 40

    # Clamp selected_index
    if state.focused_panel == "main" and flat_chars:
        if state.selected_index >= len(flat_chars):
            state.selected_index = len(flat_chars) - 1

    # Handle mouse scrolling
    mouse = GetMousePosition()
    if list_x <= mouse.x <= list_x + list_width and list_y <= mouse.y <= list_y + list_height:
        wheel = GetMouseWheelMove()
        state.scroll_offset -= int(wheel * 30)
        max_offset = max(0, content_height - list_height)
        state.scroll_offset = max(0, min(state.scroll_offset, max_offset))

    # Draw items with scissor clipping
    BeginScissorMode(list_x, list_y, list_width, list_height)

    # Pre-compute which entries are in folders (for indentation)
    folder_entry_set = set()
    if folder_data and not state.search_filter:
        for fd in folder_data["folders"].values():
            for ep in fd["entries"]:
                folder_entry_set.add(ep)

    draw_y = list_y - state.scroll_offset
    for item in display_items:
        if item[0] == "folder":
            _, slug, display_name, entry_count, is_collapsed = item
            fh = folder_header_h

            if draw_y + fh >= list_y and draw_y <= list_y + list_height:
                # Folder header background
                hover = (list_x <= mouse.x <= list_x + list_width and
                         draw_y <= mouse.y <= draw_y + fh)
                bg = BG_SELECTED if hover else (35, 35, 50, 255)
                DrawRectangle(list_x, draw_y, list_width - 15, fh, bg)
                DrawRectangleLines(list_x, draw_y, list_width - 15, fh, BORDER)

                # Collapse indicator
                arrow = ">" if is_collapsed else "v"
                DrawText(arrow.encode('utf-8'), list_x + 10, draw_y + 11, 14, TEXT_DIM)

                # Folder icon + name
                folder_label = f"[F] {display_name}"
                DrawText(folder_label.encode('utf-8'), list_x + 28, draw_y + 11, 14, RAYWHITE)

                # Entry count
                count_text = f"({entry_count})"
                cw = MeasureText(count_text.encode('utf-8'), 12)
                DrawText(count_text.encode('utf-8'), list_x + list_width - 15 - cw - 10, draw_y + 12, 12, TEXT_DIM)

                # Click to toggle collapse
                if (hover and IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and not state.modal_open):
                    collapse_key = f"{section}/{slug}"
                    state.folder_collapsed[collapse_key] = not is_collapsed

            draw_y += fh

        elif item[0] == "entry":
            _, char_path, flat_idx = item

            if draw_y + card_height >= list_y and draw_y <= list_y + list_height:
                content = read_character(char_path)
                parsed = parse_character(content)
                name = parsed.get("name") or char_path.stem
                summary = parsed.get("summary") or ""
                tags_str = parsed.get("tags", "")
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]

                from .portraits import get_character_thumbnail
                portrait_tex = get_character_thumbnail(state, name, parsed)

                is_kbd_selected = (state.focused_panel == "main" and state.selected_index == flat_idx)

                # Indent entries that are inside a folder
                indent = 20 if char_path in folder_entry_set else 0

                if draw_character_card(list_x + indent, draw_y, list_width - 15 - indent, name, summary, tags,
                                       selected=is_kbd_selected, modal_open=bool(state.modal_open),
                                       portrait_texture=portrait_tex):
                    action = f"select:{state.characters.index(char_path)}"

            draw_y += card_height

        elif item[0] == "divider":
            label = item[1]
            dh = 30
            if draw_y + dh >= list_y and draw_y <= list_y + list_height:
                DrawLine(list_x + 5, draw_y + 12, list_x + 60, draw_y + 12, BORDER)
                DrawText(label.encode('utf-8'), list_x + 65, draw_y + 6, 12, TEXT_DIM)
                label_w = MeasureText(label.encode('utf-8'), 12)
                DrawLine(list_x + 70 + label_w, draw_y + 12, list_x + list_width - 20, draw_y + 12, BORDER)
            draw_y += dh

        elif item[0] == "new_folder":
            nh = 40
            if draw_y + nh >= list_y and draw_y <= list_y + list_height:
                btn_w = 120
                btn_x = list_x + (list_width - btn_w) // 2
                if draw_button(btn_x, draw_y + 8, btn_w, 26, "+ New Folder") and not state.modal_open:
                    action = "folder_create"
            draw_y += nh

    EndScissorMode()

    # Draw scrollbar
    if content_height > list_height:
        draw_scrollbar(x + width - 18, list_y, list_height, state.scroll_offset, content_height, list_height)

    # Empty state
    if not flat_chars and not display_items:
        if state.search_filter:
            msg = f"No {section_name.lower()} match your search".encode('utf-8')
        else:
            msg = f"No {section_name.lower()} yet. Create one!".encode('utf-8')
        msg_width = MeasureText(msg, 16)
        DrawText(msg, x + (width - msg_width) // 2, y + height // 2, 16, TEXT_DIM)

    return action


def draw_main_panel_character_view(state) -> str | None:
    """Draw the main panel for character view screen.

    Returns an action string if a link/backlink chip was clicked, else None.
    """
    from templates import IMAGE_FIELD_TYPES, FIELD_TYPE_MIMAGE, FIELD_TYPE_TAGS, FIELD_TYPE_LINK, template_has_image_fields
    from helpers import parse_link_field, resolve_link_name
    from .portraits import (
        get_or_load_image, draw_image, draw_image_placeholder,
    )

    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h

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
    nav_action = None  # Track link chip clicks

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

            elif tf.field_type == FIELD_TYPE_LINK:
                # Link chips (clickable)
                link_value = data.get(tf.key, "")
                if link_value:
                    links = parse_link_field(link_value)
                    if links:
                        # Resolve display names
                        if state.active_world:
                            for lnk in links:
                                lnk["name"] = resolve_link_name(
                                    state.active_world, lnk["section"], lnk["slug"])
                        DrawText(tf.display_name.encode('utf-8'), content_x, draw_y, 18, ACCENT)
                        draw_y += 25
                        draw_y, chip_action = _draw_link_chips_view(
                            state, links, content_x, draw_y, content_width)
                        if chip_action:
                            nav_action = chip_action

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

        # Backlinks section
        draw_y, bl_action = _draw_backlinks_section(state, content_x, draw_y, content_width)
        if bl_action:
            nav_action = bl_action

    else:
        # --- Text-only mode (no image fields in template) ---
        template_fields = state.active_template.fields if state.active_template else []
        if not template_fields:
            from templates import get_default_template
            template_fields = get_default_template().fields

        for tf in template_fields:
            value = data.get(tf.key, "")
            if not value:
                continue

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
            elif tf.field_type == FIELD_TYPE_LINK:
                links = parse_link_field(value)
                if links:
                    if state.active_world:
                        for lnk in links:
                            lnk["name"] = resolve_link_name(
                                state.active_world, lnk["section"], lnk["slug"])
                    DrawText(tf.display_name.encode('utf-8'), content_x, draw_y, 18, ACCENT)
                    draw_y += 25
                    draw_y, chip_action = _draw_link_chips_view(
                        state, links, content_x, draw_y, content_width)
                    if chip_action:
                        nav_action = chip_action
            else:
                DrawText(tf.display_name.encode('utf-8'), content_x, draw_y, 18, ACCENT)
                draw_y += 25
                lines = wrap_text(value, content_width, 14)
                for line in lines:
                    DrawText(line.encode('utf-8'), content_x, draw_y, 14, TEXT)
                    draw_y += 18
                draw_y += 15

        # Backlinks section
        draw_y, bl_action = _draw_backlinks_section(state, content_x, draw_y, content_width)
        if bl_action:
            nav_action = bl_action

    EndScissorMode()
    return nav_action


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


def _get_section_icon(section: str) -> str:
    """Get a text icon for a section."""
    icons = {"characters": "[C]", "locations": "[L]", "timeline": "[T]", "codex": "[X]"}
    return icons.get(section, "")


def _draw_link_chips_view(state, links: list[dict], content_x: int, draw_y: int,
                           content_width: int) -> tuple[int, str | None]:
    """Draw linked entries as clickable chips in view mode.

    Returns (new_draw_y, action_string_or_None).
    Action is "navigate:section:slug" if a chip is clicked.
    """
    if not links:
        return draw_y, None

    action = None
    chip_x = content_x
    chip_h = 26
    chip_gap = 8
    chip_pad = 8
    mouse = GetMousePosition()

    for link in links:
        section = link.get("section", "")
        slug = link.get("slug", "")
        name = link.get("name", slug.replace("_", " ").title())
        icon = _get_section_icon(section)
        chip_text = f"{icon} {name}" if icon else name
        chip_w = MeasureText(chip_text.encode('utf-8'), 13) + chip_pad * 2

        # Wrap to next line if needed
        if chip_x + chip_w > content_x + content_width and chip_x > content_x:
            chip_x = content_x
            draw_y += chip_h + 4

        # Hover detection
        hovering = (chip_x <= mouse.x <= chip_x + chip_w and
                    draw_y <= mouse.y <= draw_y + chip_h)

        # Draw chip
        bg = (70, 90, 120, 255) if hovering else (50, 70, 100, 255)
        DrawRectangle(chip_x, draw_y, chip_w, chip_h, bg)
        DrawRectangleLines(chip_x, draw_y, chip_w, chip_h, (80, 100, 130, 255))
        DrawText(chip_text.encode('utf-8'), chip_x + chip_pad, draw_y + 6, 13, RAYWHITE)

        if hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            action = f"navigate:{section}:{slug}"

        chip_x += chip_w + chip_gap

    draw_y += chip_h + 10
    return draw_y, action


def _draw_link_field_edit(state, tf, links: list[dict], content_x: int, draw_y: int,
                           content_width: int) -> tuple[int, str | None]:
    """Draw a link field in edit mode with chips (removable) and Add button.

    Returns (new_draw_y, action_string_or_None).
    Actions: "link_add:field_key", "link_remove:field_key:section:slug"
    """
    action = None
    chip_x = content_x
    chip_h = 26
    chip_gap = 8
    chip_pad = 8
    mouse = GetMousePosition()

    for link in links:
        section = link.get("section", "")
        slug = link.get("slug", "")
        name = link.get("name", slug.replace("_", " ").title())
        icon = _get_section_icon(section)
        chip_text = f"{icon} {name}" if icon else name
        remove_w = 18
        chip_w = MeasureText(chip_text.encode('utf-8'), 13) + chip_pad * 2 + remove_w

        # Wrap
        if chip_x + chip_w > content_x + content_width - 80 and chip_x > content_x:
            chip_x = content_x
            draw_y += chip_h + 4

        # Draw chip
        DrawRectangle(chip_x, draw_y, chip_w, chip_h, (50, 70, 100, 255))
        DrawRectangleLines(chip_x, draw_y, chip_w, chip_h, (80, 100, 130, 255))
        DrawText(chip_text.encode('utf-8'), chip_x + chip_pad, draw_y + 6, 13, RAYWHITE)

        # Remove button (x)
        rx = chip_x + chip_w - remove_w - 2
        r_hovering = (rx <= mouse.x <= rx + remove_w and
                      draw_y + 2 <= mouse.y <= draw_y + chip_h - 2)
        r_color = DANGER if r_hovering else TEXT_DIM
        DrawText(b"x", rx + 4, draw_y + 6, 13, r_color)

        if r_hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            action = f"link_remove:{tf.key}:{section}:{slug}"

        chip_x += chip_w + chip_gap

    # Add button
    add_x = chip_x if chip_x < content_x + content_width - 70 else content_x
    add_y = draw_y if chip_x < content_x + content_width - 70 else draw_y + chip_h + 4
    if draw_button(add_x, add_y, 65, chip_h, "+ Add"):
        action = f"link_add:{tf.key}"

    draw_y = add_y + chip_h + 10
    return draw_y, action


def _draw_backlinks_section(state, content_x: int, draw_y: int,
                             content_width: int) -> tuple[int, str | None]:
    """Draw the 'Referenced By' backlinks section at the bottom of character view.

    Returns (new_draw_y, action_string_or_None).
    """
    if not state.active_world or not state.selected_character:
        return draw_y, None

    slug = state.selected_character.stem
    section = getattr(state, 'current_section', 'characters')

    from helpers import find_backlinks
    backlinks = find_backlinks(state.active_world, section, slug)
    if not backlinks:
        return draw_y, None

    action = None
    mouse = GetMousePosition()

    # Divider
    DrawLine(content_x, draw_y, content_x + content_width, draw_y, BORDER)
    draw_y += 15

    DrawText(b"REFERENCED BY", content_x, draw_y, 14, TEXT_DIM)
    draw_y += 22

    for bl in backlinks:
        icon = _get_section_icon(bl["section"])
        text = f"{icon} {bl['name']}"
        if bl.get("field"):
            text += f" -- {bl['field']}"

        tw = MeasureText(text.encode('utf-8'), 13)
        hovering = (content_x <= mouse.x <= content_x + tw and
                    draw_y <= mouse.y <= draw_y + 20)

        color = (180, 180, 220, 255) if hovering else (140, 140, 170, 255)
        DrawText(text.encode('utf-8'), content_x, draw_y, 13, color)

        if hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            action = f"navigate:{bl['section']}:{bl['slug']}"

        draw_y += 22

    draw_y += 10
    return draw_y, action


def _draw_image_field_in_form(state, tf, x, y, max_width, is_create=False):
    """Draw an image field in a create/edit form.

    Uses state.pending_images for create mode, world images for edit mode.
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


def draw_main_panel_character_form(state, is_create: bool = True) -> str | None:
    """Draw the character create/edit form as a main panel.

    This replaces the old modal-based create/edit character forms.
    Buttons (Create/Save, Cancel) come from the actions panel.
    Returns an action string if a link field button is clicked, else None.
    """
    from .components import draw_text_input_stateful, calculate_text_input_height, TextInputState
    from templates import FIELD_TYPE_LINK
    from helpers import parse_link_field, resolve_link_name

    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    mouse = GetMousePosition()
    form_action = None

    # Title
    from helpers import SECTIONS as _SECTIONS
    _section = getattr(state, 'current_section', 'characters')
    _singular = _SECTIONS.get(_section, _SECTIONS["characters"]).get("singular", "Entry")
    if is_create:
        title = f"Create {_singular}"
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
        elif tf.field_type == FIELD_TYPE_LINK:
            # Estimate height: label + chips + add button
            raw = state.form_data.get(tf.key, "")
            links = parse_link_field(raw) if raw else []
            # Rough estimate: one row of chips + add button
            rows = max(1, (len(links) + 3) // 4) if links else 1
            item_h = 18 + rows * 30 + 10
            render_items.append(("link", tf, item_h, links))
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

        elif item[0] == "link":
            _, tf, item_h, links = item

            if draw_y + item_h > form_y - 50 and draw_y < form_y + form_h + 50:
                # Label
                label = tf.display_name
                DrawText(label.encode('utf-8'), field_x, draw_y, 14, TEXT_DIM)
                chip_y = draw_y + 18

                # Resolve display names for links
                if state.active_world:
                    for lnk in links:
                        if "name" not in lnk:
                            lnk["name"] = resolve_link_name(
                                state.active_world, lnk["section"], lnk["slug"])

                _, link_action = _draw_link_field_edit(
                    state, tf, links, field_x, chip_y, field_input_w)
                if link_action and form_action is None:
                    form_action = link_action

            draw_y += item_h

    EndScissorMode()

    # Draw scroll indicator if needed
    if total_form_height > form_h:
        scrollbar_h = max(20, int(form_h * form_h / total_form_height))
        max_scroll = total_form_height - form_h
        scrollbar_y = form_y + int((form_h - scrollbar_h) * state.form_scroll_offset / max_scroll) if max_scroll > 0 else form_y
        DrawRectangle(scrollbar_x, form_y, 8, form_h, (25, 25, 35, 255))
        DrawRectangle(scrollbar_x, scrollbar_y, 8, scrollbar_h, (70, 70, 100, 255))

    return form_action


def draw_main_panel_stats(state):
    """Draw the main panel for stats view."""
    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    from helpers import get_world_name, get_world_stats

    if not state.active_world:
        return

    world_name = get_world_name(state.active_world)
    stats = get_world_stats(state.active_world)

    content_x = x + 30
    content_y = y + 30

    # Title
    DrawText(f"World Statistics: {world_name}".encode('utf-8'), content_x, content_y, 24, RAYWHITE)
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
    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h
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


def draw_main_panel_settings(state) -> str | None:
    """Draw the settings page. Returns action string or None."""
    from helpers import SECTIONS, get_world_name, get_world_description, open_in_file_manager
    from .components import draw_text_input_stateful, TextInputState

    _, _, _, _, main_x, main_w, panel_h = _layout()
    x = main_x
    y = HEADER_HEIGHT
    width = main_w
    height = panel_h
    action = None

    DrawRectangle(x, y, width, height, BG_DARK)
    DrawRectangleLines(x, y, width, height, BORDER)

    if not state.active_world:
        return None

    # Handle scrolling
    mouse = GetMousePosition()
    if x <= mouse.x <= x + width and y <= mouse.y <= y + height:
        wheel = GetMouseWheelMove()
        state.view_scroll_offset -= int(wheel * 30)
        state.view_scroll_offset = max(0, state.view_scroll_offset)

    BeginScissorMode(x, y, width, height)

    content_x = x + 30
    content_w = width - 60
    input_w = min(400, content_w - 20)
    draw_y = y + 20 - state.view_scroll_offset

    # Title
    DrawText(b"WORLD SETTINGS", content_x, draw_y, 20, RAYWHITE)
    draw_y += 35

    # --- GENERAL ---
    DrawText(b"GENERAL", content_x, draw_y, 14, TEXT_DIM)
    draw_y += 5
    DrawLine(content_x, draw_y + 14, content_x + content_w, draw_y + 14, BORDER)
    draw_y += 25

    # Initialize settings input states
    if state.input_states is None:
        state.input_states = {}

    # World Name
    DrawText(b"World Name:", content_x, draw_y, 14, TEXT_DIM)
    draw_y += 20

    if "_settings_name" not in state.input_states:
        name = get_world_name(state.active_world)
        state.input_states["_settings_name"] = TextInputState(text=name, cursor_pos=len(name))

    name_active = state.active_field == "_settings_name"
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if content_x <= mouse.x <= content_x + input_w and draw_y <= mouse.y <= draw_y + 32:
            state.active_field = "_settings_name"
    draw_text_input_stateful(content_x, draw_y, input_w, 32, state.input_states["_settings_name"], name_active)
    draw_y += 45

    # Description
    DrawText(b"Description:", content_x, draw_y, 14, TEXT_DIM)
    draw_y += 20

    if "_settings_desc" not in state.input_states:
        desc = get_world_description(state.active_world)
        state.input_states["_settings_desc"] = TextInputState(text=desc, cursor_pos=len(desc))

    desc_active = state.active_field == "_settings_desc"
    if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
        if content_x <= mouse.x <= content_x + input_w and draw_y <= mouse.y <= draw_y + 60:
            state.active_field = "_settings_desc"
    draw_text_input_stateful(content_x, draw_y, input_w, 60, state.input_states["_settings_desc"], desc_active, multiline=True)
    draw_y += 75

    # Save button for general settings
    if draw_button(content_x, draw_y, 120, 28, "Save Changes") and not state.modal_open:
        action = "save_world_meta"
    draw_y += 45

    # --- SECTIONS ---
    DrawText(b"SECTIONS", content_x, draw_y, 14, TEXT_DIM)
    draw_y += 5
    DrawLine(content_x, draw_y + 14, content_x + content_w, draw_y + 14, BORDER)
    draw_y += 25

    section_order = ["characters", "locations", "timeline", "codex"]
    enabled = state.enabled_sections

    for sec_key in section_order:
        meta = SECTIONS.get(sec_key)
        if not meta:
            continue

        is_enabled = sec_key in enabled
        is_characters = sec_key == "characters"

        # Checkbox
        cb_size = 18
        cb_x = content_x
        cb_y = draw_y + 2

        if is_characters:
            # Always checked, greyed out
            DrawRectangle(cb_x, cb_y, cb_size, cb_size, (50, 50, 70, 255))
            DrawRectangleLines(cb_x, cb_y, cb_size, cb_size, BORDER)
            DrawText(b"x", cb_x + 4, cb_y + 1, 16, TEXT_DIM)
        elif is_enabled:
            DrawRectangle(cb_x, cb_y, cb_size, cb_size, (60, 120, 60, 255))
            DrawRectangleLines(cb_x, cb_y, cb_size, cb_size, BORDER)
            DrawText(b"x", cb_x + 4, cb_y + 1, 16, RAYWHITE)
        else:
            DrawRectangle(cb_x, cb_y, cb_size, cb_size, (35, 35, 50, 255))
            DrawRectangleLines(cb_x, cb_y, cb_size, cb_size, BORDER)

        # Label
        label_color = TEXT_DIM if is_characters else RAYWHITE
        DrawText(meta["name"].encode('utf-8'), cb_x + cb_size + 10, draw_y + 3, 16, label_color)

        # Description / status
        if is_characters:
            DrawText(b"(always enabled)", cb_x + cb_size + 120, draw_y + 5, 12, TEXT_DIM)
        elif not is_enabled:
            DrawText(b"Click to enable", cb_x + cb_size + 120, draw_y + 5, 12, TEXT_DIM)

        # Click handler (not for characters)
        if not is_characters:
            if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and
                    cb_x <= mouse.x <= cb_x + cb_size + 110 and
                    cb_y <= mouse.y <= cb_y + cb_size + 4):
                if is_enabled:
                    action = f"disable_{sec_key}"
                else:
                    action = f"enable_{sec_key}"

        draw_y += 30

    draw_y += 10
    DrawText(b"Enabling a section creates its folder.", content_x, draw_y, 12, TEXT_DIM)
    draw_y += 30

    # --- TIMELINE SETTINGS ---
    if "timeline" in enabled:
        DrawText(b"TIMELINE", content_x, draw_y, 14, TEXT_DIM)
        draw_y += 5
        DrawLine(content_x, draw_y + 14, content_x + content_w, draw_y + 14, BORDER)
        draw_y += 25

        half_w = min(140, (input_w - 20) // 2)

        # Start Year / End Year
        DrawText(b"Start Year:", content_x, draw_y, 14, TEXT_DIM)
        DrawText(b"End Year:", content_x + half_w + 20, draw_y, 14, TEXT_DIM)
        draw_y += 20

        if "_tl_start_year" not in state.input_states:
            sv = str(int(getattr(state, "timeline_start_year", -500)))
            state.input_states["_tl_start_year"] = TextInputState(text=sv, cursor_pos=len(sv))
        if "_tl_end_year" not in state.input_states:
            ev = str(int(getattr(state, "timeline_end_year", 1500)))
            state.input_states["_tl_end_year"] = TextInputState(text=ev, cursor_pos=len(ev))

        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if content_x <= mouse.x <= content_x + half_w and draw_y <= mouse.y <= draw_y + 32:
                state.active_field = "_tl_start_year"
            elif content_x + half_w + 20 <= mouse.x <= content_x + half_w + 20 + half_w and draw_y <= mouse.y <= draw_y + 32:
                state.active_field = "_tl_end_year"
        draw_text_input_stateful(content_x, draw_y, half_w, 32, state.input_states["_tl_start_year"], state.active_field == "_tl_start_year")
        draw_text_input_stateful(content_x + half_w + 20, draw_y, half_w, 32, state.input_states["_tl_end_year"], state.active_field == "_tl_end_year")
        draw_y += 45

        # Current Year
        DrawText(b"Current Year (optional):", content_x, draw_y, 14, TEXT_DIM)
        draw_y += 20
        if "_tl_current_year" not in state.input_states:
            cy = getattr(state, "timeline_current_year", None)
            cv = str(int(cy)) if cy is not None else ""
            state.input_states["_tl_current_year"] = TextInputState(text=cv, cursor_pos=len(cv))
        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if content_x <= mouse.x <= content_x + half_w and draw_y <= mouse.y <= draw_y + 32:
                state.active_field = "_tl_current_year"
        draw_text_input_stateful(content_x, draw_y, half_w, 32, state.input_states["_tl_current_year"], state.active_field == "_tl_current_year")
        draw_y += 45

        # Display Format
        DrawText(b"Display Format:", content_x, draw_y, 14, TEXT_DIM)
        draw_y += 20
        fmt = getattr(state, "timeline_time_format", "year_only")
        formats = [("year_only", "Year Only"), ("age_year", "Age/Year"), ("era_year", "Era Year")]
        fmt_x = content_x
        for fkey, flabel in formats:
            fw = MeasureText(flabel.encode('utf-8'), 13) + 20
            is_sel = (fmt == fkey)
            if draw_button(fmt_x, draw_y, fw, 26, flabel, selected=is_sel) and not state.modal_open:
                state.timeline_time_format = fkey
            fmt_x += fw + 6
        draw_y += 38

        # Labels
        DrawText(b"Negative Years Label:", content_x, draw_y, 14, TEXT_DIM)
        DrawText(b"Positive Years Label:", content_x + half_w + 20, draw_y, 14, TEXT_DIM)
        draw_y += 20
        if "_tl_neg_label" not in state.input_states:
            nl = getattr(state, "timeline_negative_label", "BC")
            state.input_states["_tl_neg_label"] = TextInputState(text=nl, cursor_pos=len(nl))
        if "_tl_pos_label" not in state.input_states:
            pl = getattr(state, "timeline_positive_label", "AD")
            state.input_states["_tl_pos_label"] = TextInputState(text=pl, cursor_pos=len(pl))
        if IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            if content_x <= mouse.x <= content_x + half_w and draw_y <= mouse.y <= draw_y + 32:
                state.active_field = "_tl_neg_label"
            elif content_x + half_w + 20 <= mouse.x <= content_x + half_w + 20 + half_w and draw_y <= mouse.y <= draw_y + 32:
                state.active_field = "_tl_pos_label"
        draw_text_input_stateful(content_x, draw_y, half_w, 32, state.input_states["_tl_neg_label"], state.active_field == "_tl_neg_label")
        draw_text_input_stateful(content_x + half_w + 20, draw_y, half_w, 32, state.input_states["_tl_pos_label"], state.active_field == "_tl_pos_label")
        draw_y += 45

        # Save button
        if draw_button(content_x, draw_y, 180, 28, "Save Timeline Settings") and not state.modal_open:
            action = "save_timeline_settings"
        draw_y += 45

    # --- DATA ---
    DrawText(b"DATA", content_x, draw_y, 14, TEXT_DIM)
    draw_y += 5
    DrawLine(content_x, draw_y + 14, content_x + content_w, draw_y + 14, BORDER)
    draw_y += 25

    if draw_button(content_x, draw_y, 140, 30, "Open Folder") and not state.modal_open:
        open_in_file_manager(state.active_world)
    DrawText(b"Show world in file manager", content_x + 150, draw_y + 8, 12, TEXT_DIM)
    draw_y += 40

    # Export (future)
    DrawRectangle(content_x, draw_y, 140, 30, (35, 35, 50, 255))
    DrawRectangleLines(content_x, draw_y, 140, 30, BORDER)
    export_label = b"Export World"
    ew = MeasureText(export_label, 14)
    DrawText(export_label, content_x + (140 - ew) // 2, draw_y + 8, 14, TEXT_DIM)
    DrawText(b"(coming soon)", content_x + 150, draw_y + 8, 12, TEXT_DIM)
    draw_y += 55

    # --- DANGER ZONE ---
    DrawText(b"DANGER ZONE", content_x, draw_y, 14, DANGER)
    draw_y += 5
    DrawLine(content_x, draw_y + 14, content_x + content_w, draw_y + 14, DANGER)
    draw_y += 25

    # Delete World button
    del_w = 160
    del_h = 32
    del_hover = (content_x <= mouse.x <= content_x + del_w and draw_y <= mouse.y <= draw_y + del_h)
    del_bg = (180, 50, 50, 255) if del_hover else (120, 40, 40, 255)
    DrawRectangle(content_x, draw_y, del_w, del_h, del_bg)
    DrawRectangleLines(content_x, draw_y, del_w, del_h, DANGER)
    del_label = b"Delete World"
    dw = MeasureText(del_label, 14)
    DrawText(del_label, content_x + (del_w - dw) // 2, draw_y + 9, 14, RAYWHITE)
    if del_hover and IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and not state.modal_open:
        action = "delete_world"

    DrawText(b"This cannot be undone", content_x + del_w + 15, draw_y + 9, 12, TEXT_DIM)

    EndScissorMode()
    return action


def draw_shortcuts_overlay():
    """Draw keyboard shortcuts help overlay."""
    sw = GetScreenWidth()
    sh = GetScreenHeight()

    # Dim background
    DrawRectangle(0, 0, sw, sh, (0, 0, 0, 200))

    # Panel dimensions
    panel_w = min(460, sw - 40)
    panel_h = min(440, sh - 40)
    px = (sw - panel_w) // 2
    py = (sh - panel_h) // 2

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
