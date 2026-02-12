"""
Codex Font Management
Loads a custom font at each needed size for crisp rendering.
Provides drop-in replacements for DrawText / MeasureText.
"""

from pathlib import Path
import subprocess

from raylib import (
    ffi, LoadFontEx, DrawTextEx, MeasureTextEx,
    DrawText as _DrawTextDefault, MeasureText as _MeasureTextDefault,
    SetTextureFilter, IsFontValid, TEXTURE_FILTER_POINT,
)


# Font loaded at each pixel size for crisp rendering (no scaling)
_fonts: dict[int, object] = {}
_font_path: str | None = None

# Sizes actually used in the UI
_PRELOAD_SIZES = (12, 14, 16, 18, 20, 24, 28, 32)

# Preferred fonts in order (nerd font variants first)
_PREFERRED_FONTS = [
    "JetBrainsMono Nerd Font:style=Regular",
    "JetBrainsMono Nerd Font Mono:style=Regular",
    "JetBrains Mono:style=Regular",
    "Fira Code:style=Regular",
    "Source Code Pro:style=Regular",
    "Ubuntu Mono:style=Regular",
    "Hack:style=Regular",
]

# Spacing ratio relative to font size (0 = default kerning)
_SPACING_RATIO = 0.0


def _find_font_path() -> str | None:
    """Find the best available font using fc-match."""
    for font_spec in _PREFERRED_FONTS:
        try:
            result = subprocess.run(
                ["fc-match", font_spec, "--format=%{file}"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                if path and Path(path).exists():
                    # fc-match always returns something — verify it's actually the font we asked
                    name_part = font_spec.split(":")[0].lower().replace(" ", "")
                    file_lower = Path(path).stem.lower().replace("-", "").replace("_", "")
                    if name_part.replace(" ", "") in file_lower:
                        return path
        except Exception:
            continue
    return None


def _build_codepoints() -> list[int]:
    """Build a list of Unicode codepoints to load."""
    cps = []
    # Basic ASCII + Latin-1 Supplement + Latin Extended-A
    cps.extend(range(0x0020, 0x0180))
    # General Punctuation (em dash, bullets, ellipsis, etc.)
    cps.extend(range(0x2000, 0x2070))
    # Arrows
    cps.extend(range(0x2190, 0x21FF))
    # Misc Symbols (checkmark, star, etc.)
    cps.extend(range(0x2600, 0x2700))
    return cps


def _load_font_at_size(size: int) -> object | None:
    """Load the font at an exact pixel size with point filtering."""
    if not _font_path:
        return None
    codepoints = _build_codepoints()
    cp_array = ffi.new("int[]", codepoints)
    font = LoadFontEx(_font_path.encode("utf-8"), size, cp_array, len(codepoints))
    if IsFontValid(font):
        SetTextureFilter(font.texture, TEXTURE_FILTER_POINT)
        return font
    return None


def _get_font(size: int):
    """Get the font for a given size, loading on demand if needed."""
    font = _fonts.get(size)
    if font is not None:
        return font
    if _font_path:
        font = _load_font_at_size(size)
        if font is not None:
            _fonts[size] = font
            return font
    return None


def init_font() -> None:
    """Load the preferred font at all needed sizes. Call once after InitWindow."""
    global _font_path

    _font_path = _find_font_path()
    if not _font_path:
        return

    for size in _PRELOAD_SIZES:
        font = _load_font_at_size(size)
        if font is not None:
            _fonts[size] = font


def draw_text(text, x: int, y: int, font_size: int, color) -> None:
    """Drop-in replacement for DrawText using the loaded font."""
    font = _get_font(font_size)
    if font is not None:
        spacing = font_size * _SPACING_RATIO
        DrawTextEx(font, text, (int(x), int(y)), font_size, spacing, color)
    else:
        _DrawTextDefault(text, int(x), int(y), font_size, color)


def measure_text(text, font_size: int) -> int:
    """Drop-in replacement for MeasureText using the loaded font."""
    font = _get_font(font_size)
    if font is not None:
        spacing = font_size * _SPACING_RATIO
        vec = MeasureTextEx(font, text, font_size, spacing)
        return int(vec.x)
    else:
        return _MeasureTextDefault(text, font_size)
