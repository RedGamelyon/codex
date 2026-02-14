"""
Codex UI Components
Reusable drawing functions for buttons, inputs, cards, etc.
"""

from dataclasses import dataclass, field
from raylib import (
    GetMousePosition, IsMouseButtonPressed, MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT,
    DrawRectangle, DrawRectangleLines,
    DrawLine, GetCharPressed, IsKeyDown,
    GetClipboardText, SetClipboardText, GetFrameTime,
    KEY_BACKSPACE, KEY_DELETE, KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN,
    KEY_HOME, KEY_END, KEY_ENTER, KEY_A, KEY_C, KEY_V, KEY_X,
    KEY_LEFT_CONTROL, KEY_RIGHT_CONTROL, KEY_LEFT_SHIFT, KEY_RIGHT_SHIFT,
    ffi, GetScreenWidth, GetScreenHeight,
)

from .fonts import draw_text as DrawText, measure_text as MeasureText

from .colors import (
    BG_BUTTON, BG_HOVER, BG_SELECTED, BG_PANEL,
    BORDER, BORDER_ACTIVE, TEXT, TEXT_DIM, TAG, RAYWHITE
)


@dataclass
class FieldConfig:
    """Configuration for a form field - supports template system."""
    name: str  # Display label
    key: str   # Key for saving to data dict
    min_height: int = 40
    multiline: bool = False
    expandable: bool = False  # Shows [+] button for fullscreen edit
    field_type: str = "text"  # "text", "multiline", "tags", "number"


@dataclass
class TextInputState:
    """State for a text input field with cursor and selection support."""
    text: str = ""
    cursor_pos: int = 0
    selection_start: int | None = None  # None if no selection
    scroll_offset_y: int = 0  # For multiline vertical scroll (unused in expanding mode)
    blink_timer: float = 0.0
    cursor_visible: bool = True

    # Key repeat frame counters
    _key_frames: dict[int, int] = field(default_factory=dict)

    def get_selected_text(self) -> str:
        """Return currently selected text, or empty string."""
        if self.selection_start is None:
            return ""
        start = min(self.selection_start, self.cursor_pos)
        end = max(self.selection_start, self.cursor_pos)
        return self.text[start:end]

    def delete_selection(self) -> bool:
        """Delete selected text. Returns True if there was a selection."""
        if self.selection_start is None:
            return False
        start = min(self.selection_start, self.cursor_pos)
        end = max(self.selection_start, self.cursor_pos)
        self.text = self.text[:start] + self.text[end:]
        self.cursor_pos = start
        self.selection_start = None
        return True

    def insert_text(self, new_text: str):
        """Insert text at cursor, replacing any selection."""
        self.delete_selection()
        self.text = self.text[:self.cursor_pos] + new_text + self.text[self.cursor_pos:]
        self.cursor_pos += len(new_text)
        self.reset_blink()

    def reset_blink(self):
        """Reset cursor blink to visible state."""
        self.blink_timer = 0.0
        self.cursor_visible = True


@dataclass
class ContextMenuState:
    """State for the right-click context menu."""
    visible: bool = False
    x: int = 0
    y: int = 0
    target_input: TextInputState | None = None

_context_menu = ContextMenuState()


# Constants for text rendering
TEXT_FONT_SIZE = 16
TEXT_LINE_HEIGHT = 18
TEXT_PADDING = 8


def calculate_text_input_height(text: str, width: int, min_height: int, multiline: bool, expandable: bool = False) -> int:
    """Calculate the height a text input needs based on its content.

    Must match the width calculation in draw_text_input_stateful exactly.
    """
    if not multiline:
        return min_height

    # Match the exact width calculation from draw_text_input_stateful
    EXPAND_BTN_SIZE = 20
    max_text_width = width - TEXT_PADDING * 2 - (EXPAND_BTN_SIZE + 8 if expandable else 0)

    wrapped_lines, _ = _wrap_text_with_positions(text if text else " ", max_text_width, TEXT_FONT_SIZE)
    content_height = len(wrapped_lines) * TEXT_LINE_HEIGHT + TEXT_PADDING * 2
    return max(min_height, content_height)


def _is_ctrl_down() -> bool:
    """Check if either Ctrl key is pressed."""
    return IsKeyDown(KEY_LEFT_CONTROL) or IsKeyDown(KEY_RIGHT_CONTROL)


def _is_shift_down() -> bool:
    """Check if either Shift key is pressed."""
    return IsKeyDown(KEY_LEFT_SHIFT) or IsKeyDown(KEY_RIGHT_SHIFT)


def _handle_key_repeat(state: TextInputState, key: int) -> bool:
    """Handle key with repeat. Returns True if key should trigger action."""
    if IsKeyDown(key):
        frames = state._key_frames.get(key, 0)
        state._key_frames[key] = frames + 1
        # Trigger on first frame, then after 25 frames delay, every 2 frames
        if frames == 0 or (frames > 25 and frames % 2 == 0):
            return True
        return False
    else:
        state._key_frames[key] = 0
        return False


def _find_word_boundary_left(text: str, pos: int) -> int:
    """Find the start of the word to the left of pos."""
    if pos <= 0:
        return 0
    # Skip any spaces immediately to the left
    pos -= 1
    while pos > 0 and text[pos] == ' ':
        pos -= 1
    # Find start of word
    while pos > 0 and text[pos - 1] not in ' \n':
        pos -= 1
    return pos


def _find_word_boundary_right(text: str, pos: int) -> int:
    """Find the end of the word to the right of pos."""
    length = len(text)
    if pos >= length:
        return length
    # Skip current word
    while pos < length and text[pos] not in ' \n':
        pos += 1
    # Skip spaces
    while pos < length and text[pos] == ' ':
        pos += 1
    return pos


def _click_to_cursor_pos(
    text: str, click_x: float, click_y: float,
    max_width: int, font_size: int, line_height: int,
    multiline: bool, scroll_offset_y: int
) -> int:
    """Convert a click position to cursor position in text."""
    if not text:
        return 0

    if multiline:
        wrapped_lines, line_starts = _wrap_text_with_positions(text, max_width, font_size)
        # Determine which line was clicked
        clicked_line = int(click_y / line_height) + scroll_offset_y
        clicked_line = max(0, min(clicked_line, len(wrapped_lines) - 1))

        # Find position within the line
        line_text = wrapped_lines[clicked_line]
        line_start = line_starts[clicked_line]
        col = _x_to_char_pos(line_text, click_x, font_size)
        return line_start + col
    else:
        # Single line - find character position
        return _x_to_char_pos(text, click_x, font_size)


def _x_to_char_pos(text: str, click_x: float, font_size: int) -> int:
    """Convert x coordinate to character position in a line of text."""
    if click_x <= 0:
        return 0
    # Binary search would be faster, but linear is fine for typical text lengths
    for i in range(len(text) + 1):
        char_x = MeasureText(text[:i].encode('utf-8'), font_size)
        if i < len(text):
            next_char_x = MeasureText(text[:i + 1].encode('utf-8'), font_size)
            # Click is closer to current position or next position?
            if click_x < (char_x + next_char_x) / 2:
                return i
        else:
            return i
    return len(text)


def draw_button(
    x: int, y: int, width: int, height: int, text: str,
    selected: bool = False, disabled: bool = False
) -> bool:
    """Draw a button, return True if clicked."""
    mouse = GetMousePosition()
    hovering = (x <= mouse.x <= x + width) and (y <= mouse.y <= y + height)
    clicked = hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and not disabled

    # Draw background
    if disabled:
        color = (30, 30, 40, 255)
    elif selected:
        color = BG_SELECTED
    elif hovering:
        color = BG_HOVER
    else:
        color = BG_BUTTON

    DrawRectangle(x, y, width, height, color)

    # Draw border
    border_color = BORDER_ACTIVE if selected else BORDER
    if disabled:
        border_color = (50, 50, 60, 255)
    DrawRectangleLines(x, y, width, height, border_color)

    # Draw text centered
    font_size = 16
    text_bytes = text.encode('utf-8')
    text_width = MeasureText(text_bytes, font_size)
    text_color = TEXT if not disabled else (80, 80, 100, 255)
    DrawText(text_bytes, x + (width - text_width) // 2, y + (height - font_size) // 2, font_size, text_color)

    return clicked


def draw_text_input_stateful(
    x: int, y: int, width: int, height: int,
    state: TextInputState, active: bool, label: str = "",
    multiline: bool = False, expandable: bool = False
) -> bool:
    """Draw a text input field with full cursor/selection support.

    Modifies state in place. Returns True if expand button was clicked.
    Height is used as-is - caller should use calculate_text_input_height() for dynamic sizing.
    """
    expand_clicked = False
    EXPAND_BTN_SIZE = 20

    # Draw box
    border_color = BORDER_ACTIVE if active else BORDER
    DrawRectangle(x, y, width, height, (30, 30, 45, 255))
    DrawRectangleLines(x, y, width, height, border_color)

    # Draw expand button if enabled
    if expandable:
        btn_x = x + width - EXPAND_BTN_SIZE - 4
        btn_y = y + 4
        mouse = GetMousePosition()
        btn_hover = (btn_x <= mouse.x <= btn_x + EXPAND_BTN_SIZE and
                     btn_y <= mouse.y <= btn_y + EXPAND_BTN_SIZE)
        btn_color = (80, 80, 100, 255) if btn_hover else (60, 60, 80, 255)
        DrawRectangle(btn_x, btn_y, EXPAND_BTN_SIZE, EXPAND_BTN_SIZE, btn_color)
        # Draw expand icon
        DrawText(b"[+]", btn_x + 2, btn_y + 3, 12, RAYWHITE)
        if btn_hover and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            expand_clicked = True

    text_x = x + TEXT_PADDING
    text_y = y + TEXT_PADDING
    # Leave room for expand button
    max_text_width = width - TEXT_PADDING * 2 - (EXPAND_BTN_SIZE + 8 if expandable else 0)
    text = state.text
    cursor_pos = state.cursor_pos

    # Ensure cursor_pos is valid
    cursor_pos = max(0, min(cursor_pos, len(text)))
    state.cursor_pos = cursor_pos

    # Handle click to position cursor (not on expand button)
    mouse = GetMousePosition()
    if active and IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and not expand_clicked:
        if x <= mouse.x <= x + width and y <= mouse.y <= y + height:
            click_x = mouse.x - text_x
            click_y = mouse.y - text_y
            new_cursor_pos = _click_to_cursor_pos(
                text, click_x, click_y, max_text_width, TEXT_FONT_SIZE, TEXT_LINE_HEIGHT,
                multiline, 0  # No internal scroll offset
            )
            # Shift+click extends selection
            if _is_shift_down():
                if state.selection_start is None:
                    state.selection_start = state.cursor_pos
            else:
                state.selection_start = None
            state.cursor_pos = new_cursor_pos
            state.reset_blink()

    # Right-click opens context menu
    if active and IsMouseButtonPressed(MOUSE_BUTTON_RIGHT):
        if x <= mouse.x <= x + width and y <= mouse.y <= y + height:
            _context_menu.visible = True
            _context_menu.x = int(mouse.x)
            _context_menu.y = int(mouse.y)
            _context_menu.target_input = state

    if multiline:
        # === MULTILINE MODE (no internal scrolling - box expands) ===
        wrapped_lines, line_starts = _wrap_text_with_positions(text if text else " ", max_text_width, TEXT_FONT_SIZE)
        cursor_line, cursor_col = _pos_to_line_col(cursor_pos, line_starts, wrapped_lines)

        # Draw ALL lines (form handles scrolling, not this field)
        for line_idx, line in enumerate(wrapped_lines):
            line_y = text_y + line_idx * TEXT_LINE_HEIGHT
            line_start_pos = line_starts[line_idx]

            # Draw selection highlight for this line if applicable
            if state.selection_start is not None and active:
                sel_start = min(state.selection_start, cursor_pos)
                sel_end = max(state.selection_start, cursor_pos)
                line_end_pos = line_start_pos + len(line)

                if sel_start < line_end_pos and sel_end > line_start_pos:
                    highlight_start = max(0, sel_start - line_start_pos)
                    highlight_end = min(len(line), sel_end - line_start_pos)
                    pre_text = line[:highlight_start]
                    sel_text = line[highlight_start:highlight_end]
                    highlight_x = text_x + MeasureText(pre_text.encode('utf-8'), TEXT_FONT_SIZE)
                    highlight_w = MeasureText(sel_text.encode('utf-8'), TEXT_FONT_SIZE)
                    DrawRectangle(highlight_x, line_y, highlight_w, TEXT_LINE_HEIGHT, (70, 100, 150, 255))

            DrawText(line.encode('utf-8'), text_x, line_y, TEXT_FONT_SIZE, RAYWHITE)

        # Draw cursor if active and visible
        if active and state.cursor_visible:
            cursor_line_text = wrapped_lines[cursor_line][:cursor_col] if cursor_line < len(wrapped_lines) else ""
            cx = text_x + MeasureText(cursor_line_text.encode('utf-8'), TEXT_FONT_SIZE)
            cy = text_y + cursor_line * TEXT_LINE_HEIGHT
            DrawLine(cx, cy, cx, cy + TEXT_LINE_HEIGHT, RAYWHITE)

    else:
        # === SINGLE LINE MODE ===
        # For single line, we still need horizontal scrolling since box doesn't expand horizontally
        text_before_cursor = text[:cursor_pos]
        cursor_pixel_pos = MeasureText(text_before_cursor.encode('utf-8'), TEXT_FONT_SIZE)

        scroll_offset = 0
        if cursor_pixel_pos > max_text_width:
            scroll_offset = cursor_pixel_pos - max_text_width + 20

        visible_start_char = 0
        accumulated_width = 0
        for i, char in enumerate(text):
            char_width = MeasureText(char.encode('utf-8'), TEXT_FONT_SIZE)
            if accumulated_width + char_width >= scroll_offset:
                visible_start_char = i
                break
            accumulated_width += char_width

        # Draw selection highlight
        if state.selection_start is not None and active:
            sel_start = min(state.selection_start, cursor_pos)
            sel_end = max(state.selection_start, cursor_pos)
            sel_start_px = MeasureText(text[:sel_start].encode('utf-8'), TEXT_FONT_SIZE) - scroll_offset
            sel_end_px = MeasureText(text[:sel_end].encode('utf-8'), TEXT_FONT_SIZE) - scroll_offset
            sel_start_px = max(0, sel_start_px)
            sel_end_px = min(max_text_width, sel_end_px)
            if sel_end_px > sel_start_px:
                DrawRectangle(text_x + sel_start_px, text_y, sel_end_px - sel_start_px, height - TEXT_PADDING * 2, (70, 100, 150, 255))

        # Draw text
        display_text = text[visible_start_char:]
        while MeasureText(display_text.encode('utf-8'), TEXT_FONT_SIZE) > max_text_width and len(display_text) > 0:
            display_text = display_text[:-1]
        DrawText(display_text.encode('utf-8'), text_x, y + (height - TEXT_FONT_SIZE) // 2, TEXT_FONT_SIZE, RAYWHITE)

        # Draw cursor if active
        if active and state.cursor_visible:
            cx = text_x + cursor_pixel_pos - scroll_offset
            cx = max(text_x, min(cx, x + width - TEXT_PADDING))
            DrawLine(cx, y + TEXT_PADDING, cx, y + height - TEXT_PADDING, RAYWHITE)

    # Handle input if active
    if active:
        _handle_text_input(state, multiline, max_text_width, TEXT_FONT_SIZE)

        # Update cursor blink
        state.blink_timer += GetFrameTime()
        if state.blink_timer >= 0.5:
            state.blink_timer = 0.0
            state.cursor_visible = not state.cursor_visible

    return expand_clicked


def _handle_text_input(state: TextInputState, multiline: bool, max_width: int, font_size: int) -> None:
    """Process keyboard input for text field."""
    ctrl = _is_ctrl_down()
    shift = _is_shift_down()

    # Start selection if shift is held and no selection exists
    def maybe_start_selection():
        if shift and state.selection_start is None:
            state.selection_start = state.cursor_pos
        elif not shift:
            state.selection_start = None

    # --- Ctrl key combinations FIRST (before character input) ---
    if ctrl:
        # Ctrl+A - Select all
        if _handle_key_repeat(state, KEY_A):
            state.selection_start = 0
            state.cursor_pos = len(state.text)
            print(f"[DEBUG] Ctrl+A: select all, len={len(state.text)}")

        # Ctrl+C - Copy
        if _handle_key_repeat(state, KEY_C):
            selected = state.get_selected_text()
            print(f"[DEBUG] Ctrl+C pressed, selection={state.selection_start}->{state.cursor_pos}, selected={repr(selected)}")
            if selected:
                SetClipboardText(selected.encode('utf-8'))
                print(f"[DEBUG] SetClipboardText called with {repr(selected)}")

        # Ctrl+X - Cut
        if _handle_key_repeat(state, KEY_X):
            selected = state.get_selected_text()
            print(f"[DEBUG] Ctrl+X pressed, cutting: {repr(selected)}")
            if selected:
                SetClipboardText(selected.encode('utf-8'))
                state.delete_selection()

        # Ctrl+V - Paste
        if _handle_key_repeat(state, KEY_V):
            raw = GetClipboardText()
            clipboard = ""
            if raw != ffi.NULL:
                try:
                    clipboard = ffi.string(raw).decode('utf-8', errors='replace')
                except Exception:
                    pass
            print(f"[DEBUG] Ctrl+V pressed, clipboard={repr(clipboard[:100]) if clipboard else 'empty'}")
            if clipboard:
                if not multiline:
                    clipboard = clipboard.replace('\n', ' ').replace('\r', '')
                state.insert_text(clipboard)
            else:
                print("[DEBUG] Ctrl+V: clipboard empty")

        # Drain character queue so ctrl combos don't insert text
        key = GetCharPressed()
        while key > 0:
            key = GetCharPressed()
    else:
        # --- Regular character input (only when ctrl NOT held) ---
        key = GetCharPressed()
        while key > 0:
            if key >= 32:  # Printable characters
                state.insert_text(chr(key))
            key = GetCharPressed()

    # Enter key (multiline only)
    if multiline and _handle_key_repeat(state, KEY_ENTER):
        state.insert_text('\n')

    # Backspace
    if _handle_key_repeat(state, KEY_BACKSPACE):
        if not state.delete_selection():
            if ctrl:
                # Delete word
                new_pos = _find_word_boundary_left(state.text, state.cursor_pos)
                state.text = state.text[:new_pos] + state.text[state.cursor_pos:]
                state.cursor_pos = new_pos
            elif state.cursor_pos > 0:
                state.text = state.text[:state.cursor_pos - 1] + state.text[state.cursor_pos:]
                state.cursor_pos -= 1
        state.reset_blink()

    # Delete
    if _handle_key_repeat(state, KEY_DELETE):
        if not state.delete_selection():
            if ctrl:
                # Delete word forward
                new_pos = _find_word_boundary_right(state.text, state.cursor_pos)
                state.text = state.text[:state.cursor_pos] + state.text[new_pos:]
            elif state.cursor_pos < len(state.text):
                state.text = state.text[:state.cursor_pos] + state.text[state.cursor_pos + 1:]
        state.reset_blink()

    # Left arrow
    if _handle_key_repeat(state, KEY_LEFT):
        maybe_start_selection()
        if ctrl:
            state.cursor_pos = _find_word_boundary_left(state.text, state.cursor_pos)
        elif state.cursor_pos > 0:
            state.cursor_pos -= 1
        if not shift:
            state.selection_start = None
        state.reset_blink()

    # Right arrow
    if _handle_key_repeat(state, KEY_RIGHT):
        maybe_start_selection()
        if ctrl:
            state.cursor_pos = _find_word_boundary_right(state.text, state.cursor_pos)
        elif state.cursor_pos < len(state.text):
            state.cursor_pos += 1
        if not shift:
            state.selection_start = None
        state.reset_blink()

    # Home
    if _handle_key_repeat(state, KEY_HOME):
        maybe_start_selection()
        if multiline:
            line_start = state.text.rfind('\n', 0, state.cursor_pos)
            state.cursor_pos = line_start + 1 if line_start >= 0 else 0
        else:
            state.cursor_pos = 0
        if not shift:
            state.selection_start = None
        state.reset_blink()

    # End
    if _handle_key_repeat(state, KEY_END):
        maybe_start_selection()
        if multiline:
            line_end = state.text.find('\n', state.cursor_pos)
            state.cursor_pos = line_end if line_end >= 0 else len(state.text)
        else:
            state.cursor_pos = len(state.text)
        if not shift:
            state.selection_start = None
        state.reset_blink()

    # Up/Down arrows (multiline only)
    if multiline:
        wrapped_lines, line_starts = _wrap_text_with_positions(state.text, max_width, font_size)
        cursor_line, cursor_col = _pos_to_line_col(state.cursor_pos, line_starts, wrapped_lines)

        if _handle_key_repeat(state, KEY_UP) and cursor_line > 0:
            maybe_start_selection()
            target_line = cursor_line - 1
            target_col = min(cursor_col, len(wrapped_lines[target_line]))
            state.cursor_pos = line_starts[target_line] + target_col
            if not shift:
                state.selection_start = None
            state.reset_blink()

        if _handle_key_repeat(state, KEY_DOWN) and cursor_line < len(wrapped_lines) - 1:
            maybe_start_selection()
            target_line = cursor_line + 1
            target_col = min(cursor_col, len(wrapped_lines[target_line]))
            state.cursor_pos = line_starts[target_line] + target_col
            if not shift:
                state.selection_start = None
            state.reset_blink()


def _wrap_text_with_positions(text: str, max_width: int, font_size: int) -> tuple[list[str], list[int]]:
    """Wrap text and return (lines, start_positions) for cursor mapping.

    Handles word wrapping and character-level wrapping for long words.
    """
    if not text:
        return [''], [0]

    lines = []
    line_starts = []

    # Process each paragraph (split by explicit newlines)
    paragraphs = text.split('\n')
    char_pos = 0

    for para_idx, paragraph in enumerate(paragraphs):
        if not paragraph:
            lines.append('')
            line_starts.append(char_pos)
            char_pos += 1  # Account for newline character
            continue

        # Process this paragraph character by character for accurate wrapping
        current_line = ''
        line_start = char_pos

        for char in paragraph:
            test_line = current_line + char
            test_width = MeasureText(test_line.encode('utf-8'), font_size)

            if test_width <= max_width:
                current_line = test_line
            else:
                # Line would be too long - need to wrap
                if current_line:
                    # Try to break at last space for cleaner wrapping
                    last_space = current_line.rfind(' ')
                    if last_space > 0 and len(current_line) > 1:
                        # Break at word boundary
                        lines.append(current_line[:last_space])
                        line_starts.append(line_start)
                        # Start new line with remainder + new char
                        remainder = current_line[last_space + 1:]
                        line_start = line_start + last_space + 1
                        current_line = remainder + char
                    else:
                        # No space or single char - force break at character
                        lines.append(current_line)
                        line_starts.append(line_start)
                        line_start = char_pos
                        current_line = char
                else:
                    # Empty line but char still too wide (shouldn't happen normally)
                    current_line = char

            char_pos += 1

        # Add remaining content of paragraph
        if current_line:
            lines.append(current_line)
            line_starts.append(line_start)

        char_pos += 1  # Account for newline at end of paragraph

    if not lines:
        return [''], [0]
    return lines, line_starts


def _pos_to_line_col(pos: int, line_starts: list[int], lines: list[str]) -> tuple[int, int]:
    """Convert flat cursor position to (line_index, column)."""
    for i in range(len(line_starts) - 1, -1, -1):
        if pos >= line_starts[i]:
            col = pos - line_starts[i]
            col = min(col, len(lines[i]))  # Clamp to line length
            return (i, col)
    return (0, 0)


# Legacy wrapper for backwards compatibility
def draw_text_input(
    x: int, y: int, width: int, height: int,
    text: str, active: bool, label: str = "",
    multiline: bool = False
) -> str:
    """Legacy text input - creates temporary state. Prefer draw_text_input_stateful."""
    state = TextInputState(text=text, cursor_pos=len(text))
    draw_text_input_stateful(x, y, width, height, state, active, label, multiline)
    return state.text


def draw_character_card(
    x: int, y: int, width: int,
    name: str, summary: str, tags: list[str],
    selected: bool = False, modal_open: bool = False,
    portrait_texture=None
) -> bool:
    """Draw a character card, return True if clicked."""
    height = 80
    mouse = GetMousePosition()
    # Don't process hover/click when a modal is open
    hovering = not modal_open and (x <= mouse.x <= x + width) and (y <= mouse.y <= y + height)
    clicked = hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT)

    # Background
    if selected:
        bg_color = BG_SELECTED
    elif hovering:
        bg_color = BG_HOVER
    else:
        bg_color = (35, 35, 50, 255)

    DrawRectangle(x, y, width, height, bg_color)
    DrawRectangleLines(x, y, width, height, BORDER)

    # Portrait thumbnail
    THUMB_SIZE = 50
    thumb_x = x + 10
    thumb_y = y + (height - THUMB_SIZE) // 2
    text_indent = 0

    if portrait_texture is not None:
        from .portraits import draw_portrait
        draw_portrait(portrait_texture, thumb_x, thumb_y, THUMB_SIZE)
        DrawRectangleLines(thumb_x, thumb_y, THUMB_SIZE, THUMB_SIZE, BORDER)
        text_indent = THUMB_SIZE + 10

    # Name
    DrawText(name.encode('utf-8'), x + 10 + text_indent, y + 12, 18, RAYWHITE)

    # Tags (right-aligned)
    tag_x = x + width - 10
    for tag in reversed(tags[:3]):
        tag_text = f"[{tag}]"
        tag_width = MeasureText(tag_text.encode('utf-8'), 12)
        tag_x -= tag_width + 5
        DrawText(tag_text.encode('utf-8'), tag_x, y + 14, 12, TAG)

    # Summary (truncated)
    display_summary = summary
    if len(display_summary) > 60:
        display_summary = display_summary[:57] + "..."
    DrawText(display_summary.encode('utf-8'), x + 10 + text_indent, y + 42, 14, TEXT_DIM)

    return clicked


def draw_panel_border(x: int, y: int, width: int, height: int, title: str = ""):
    """Draw a panel with border and optional title."""
    DrawRectangle(x, y, width, height, BG_PANEL)
    DrawRectangleLines(x, y, width, height, BORDER)

    if title:
        # Draw title bar
        DrawLine(x, y + 25, x + width, y + 25, BORDER)
        DrawText(title.encode('utf-8'), x + 10, y + 5, 16, TEXT_DIM)


def draw_section_button(
    x: int, y: int, width: int, height: int,
    text: str, selected: bool = False, disabled: bool = False
) -> bool:
    """Draw a section navigation button."""
    mouse = GetMousePosition()
    hovering = (x <= mouse.x <= x + width) and (y <= mouse.y <= y + height)
    clicked = hovering and IsMouseButtonPressed(MOUSE_BUTTON_LEFT) and not disabled

    # Draw background
    if disabled:
        color = (25, 25, 35, 255)
    elif selected:
        color = BG_SELECTED
    elif hovering:
        color = BG_HOVER
    else:
        color = BG_PANEL

    DrawRectangle(x, y, width, height, color)

    # Selection indicator
    if selected:
        DrawRectangle(x, y, 3, height, BORDER_ACTIVE)

    # Draw text
    prefix = "> " if selected else "  "
    text_color = TEXT if not disabled else (70, 70, 90, 255)
    DrawText((prefix + text).encode('utf-8'), x + 10, y + (height - 16) // 2, 16, text_color)

    return clicked


def draw_scrollbar(x: int, y: int, height: int, offset: int, content_height: int, visible_height: int):
    """Draw a vertical scrollbar."""
    if content_height <= visible_height:
        return

    # Calculate scrollbar dimensions
    scrollbar_height = max(30, int(visible_height * visible_height / content_height))
    max_offset = content_height - visible_height
    scrollbar_y = y + int((height - scrollbar_height) * offset / max_offset) if max_offset > 0 else y

    # Draw track
    DrawRectangle(x, y, 8, height, (25, 25, 35, 255))

    # Draw thumb
    DrawRectangle(x, scrollbar_y, 8, scrollbar_height, (70, 70, 100, 255))


def draw_toasts(toasts):
    """Draw toast notifications in the bottom-right corner."""
    from time import monotonic

    if not toasts:
        return

    sw = GetScreenWidth()
    sh = GetScreenHeight()
    toast_width = min(300, sw - 40)
    toast_height = 40
    padding = 8
    start_x = sw - toast_width - 20
    start_y = sh - 20
    now = monotonic()

    for i, toast in enumerate(list(reversed(toasts))[:5]):
        y = start_y - (i + 1) * (toast_height + padding)

        colors = {
            "success": (40, 120, 60),
            "info": (40, 80, 140),
            "warning": (180, 140, 40),
            "error": (160, 50, 50),
        }
        r, g, b = colors.get(toast.toast_type, (40, 80, 140))

        time_left = toast.duration - (now - toast.created_at)
        alpha = 230
        if time_left < 0.5:
            alpha = int(230 * max(0, time_left / 0.5))

        DrawRectangle(start_x, y, toast_width, toast_height, (r, g, b, alpha))

        icons = {"success": "+", "info": "i", "warning": "!", "error": "x"}
        icon = icons.get(toast.toast_type, "")
        text_alpha = min(255, alpha + 25)
        DrawText(icon.encode('utf-8'), start_x + 12, y + 12, 16, (255, 255, 255, text_alpha))
        DrawText(toast.message.encode('utf-8'), start_x + 35, y + 12, 16, (255, 255, 255, text_alpha))


def draw_context_menu():
    """Draw and handle the right-click context menu for text inputs.

    Call once per frame after all other drawing, before toasts.
    """
    menu = _context_menu
    if not menu.visible or menu.target_input is None:
        return

    mouse = GetMousePosition()
    mx, my = int(mouse.x), int(mouse.y)

    # Menu dimensions
    item_h = 28
    menu_w = 120
    items = ["Cut", "Copy", "Paste", "Select All"]
    menu_h = item_h * len(items)

    # Clamp menu position to window
    menu_x = min(menu.x, GetScreenWidth() - menu_w - 5)
    menu_y = min(menu.y, GetScreenHeight() - menu_h - 5)

    # Check if user has a selection
    has_selection = menu.target_input.selection_start is not None
    clipboard_text = ""
    try:
        raw = GetClipboardText()
        if raw != ffi.NULL:
            clipboard_text = ffi.string(raw).decode('utf-8', errors='replace')
    except Exception:
        pass
    has_clipboard = bool(clipboard_text)

    # Close on any click outside menu
    clicking = IsMouseButtonPressed(MOUSE_BUTTON_LEFT) or IsMouseButtonPressed(MOUSE_BUTTON_RIGHT)
    if clicking and not (menu_x <= mx <= menu_x + menu_w and menu_y <= my <= menu_y + menu_h):
        menu.visible = False
        return

    # Draw menu background
    DrawRectangle(menu_x, menu_y, menu_w, menu_h, (45, 45, 65, 255))
    DrawRectangleLines(menu_x, menu_y, menu_w, menu_h, BORDER)

    for i, label in enumerate(items):
        iy = menu_y + i * item_h
        hovering = menu_x <= mx <= menu_x + menu_w and iy <= my <= iy + item_h

        # Determine if item is enabled
        if label in ("Cut", "Copy"):
            enabled = has_selection
        elif label == "Paste":
            enabled = has_clipboard
        else:  # Select All
            enabled = bool(menu.target_input.text)

        # Hover highlight
        if hovering and enabled:
            DrawRectangle(menu_x + 1, iy, menu_w - 2, item_h, BG_HOVER)

        text_color = RAYWHITE if enabled else TEXT_DIM
        DrawText(label.encode('utf-8'), menu_x + 12, iy + 7, 14, text_color)

        # Handle click on enabled item
        if hovering and enabled and IsMouseButtonPressed(MOUSE_BUTTON_LEFT):
            inp = menu.target_input

            if label == "Cut":
                selected = inp.get_selected_text()
                if selected:
                    SetClipboardText(selected.encode('utf-8'))
                    inp.delete_selection()

            elif label == "Copy":
                selected = inp.get_selected_text()
                if selected:
                    SetClipboardText(selected.encode('utf-8'))

            elif label == "Paste":
                if clipboard_text:
                    inp.insert_text(clipboard_text)

            elif label == "Select All":
                inp.selection_start = 0
                inp.cursor_pos = len(inp.text)

            menu.visible = False
            return

        # Draw separator after Copy
        if label == "Copy":
            sep_y = iy + item_h - 1
            DrawLine(menu_x + 8, sep_y, menu_x + menu_w - 8, sep_y, BORDER)
