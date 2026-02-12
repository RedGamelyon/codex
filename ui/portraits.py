"""
Codex Portrait Rendering
Texture loading, caching, and drawing for character portraits.
"""

from pathlib import Path
from raylib import (
    LoadTexture, DrawTexturePro,
    DrawRectangle, DrawRectangleLines,
    ffi
)

from .fonts import draw_text as DrawText, measure_text as MeasureText

from .colors import BORDER, TEXT_DIM


def load_portrait_texture(portrait_path: Path):
    """Load a portrait image as a Raylib Texture2D. Returns texture or None."""
    print(f"[DEBUG] load_portrait_texture: path={portrait_path}")
    print(f"[DEBUG] load_portrait_texture: exists={portrait_path.exists()}")
    try:
        texture = LoadTexture(str(portrait_path).encode('utf-8'))
        print(f"[DEBUG] load_portrait_texture: loaded {texture.width}x{texture.height}")
        if texture.width > 0:
            return texture
        print(f"[ERROR] load_portrait_texture: texture has zero dimensions")
    except Exception as e:
        print(f"[ERROR] load_portrait_texture: {type(e).__name__}: {e}")
    return None


def get_or_load_image(state, character_name: str, field_key: str = "portrait"):
    """Get a cached image texture for a field, loading if needed. Returns texture or None."""
    from helpers import get_character_slug, find_portrait

    if not state.active_vault:
        return None

    slug = get_character_slug(character_name)
    cache_key = f"{slug}:{field_key}"

    # Check cache (None entry = known miss)
    if cache_key in state.portrait_cache:
        cached = state.portrait_cache[cache_key]
        if cached is None:
            return None
        return cached["texture"]

    # Try to find and load
    img_path = find_portrait(state.active_vault, character_name, field_key=field_key)
    if img_path is None:
        state.portrait_cache[cache_key] = None
        return None

    texture = load_portrait_texture(img_path)
    if texture is not None:
        state.portrait_cache[cache_key] = {"texture": texture, "path": str(img_path)}
        return texture

    state.portrait_cache[cache_key] = None
    return None


def get_character_thumbnail(state, character_name: str, parsed_data: dict | None = None):
    """Get the best thumbnail texture for a character card.

    Priority: mimage field → legacy portrait → first image field → None.
    Uses parsed_data's _meta.template to resolve the character's template.
    """
    from templates import IMAGE_FIELD_TYPES, FIELD_TYPE_MIMAGE

    # Resolve template for this character
    template = None
    if parsed_data and state.templates:
        meta = parsed_data.get("_meta", {})
        if isinstance(meta, dict):
            template_id = meta.get("template", "default")
            for t in state.templates:
                if t.template_id == template_id:
                    template = t
                    break
        if template is None and state.templates:
            template = state.templates[0]

    if template is not None:
        # Collect image fields by priority: mimage first, then image fields
        mimage_keys = []
        image_keys = []
        for tf in template.fields:
            if tf.field_type == FIELD_TYPE_MIMAGE:
                mimage_keys.append(tf.key)
            elif tf.field_type in IMAGE_FIELD_TYPES:
                image_keys.append(tf.key)

        # Try mimage fields first
        for key in mimage_keys:
            tex = get_or_load_image(state, character_name, field_key=key)
            if tex is not None:
                return tex

        # Try legacy portrait
        tex = get_or_load_portrait(state, character_name)
        if tex is not None:
            return tex

        # Try regular image fields
        for key in image_keys:
            tex = get_or_load_image(state, character_name, field_key=key)
            if tex is not None:
                return tex

        return None

    # No template — fall back to legacy portrait
    return get_or_load_portrait(state, character_name)


def get_or_load_portrait(state, character_name: str):
    """Get a cached portrait texture, loading it if needed. Returns texture or None.

    Legacy wrapper around get_or_load_image for backward compatibility.
    """
    from helpers import get_character_slug, find_portrait

    if not state.active_vault:
        return None

    slug = get_character_slug(character_name)

    # Check legacy cache key first (for existing callers)
    if slug in state.portrait_cache:
        cached = state.portrait_cache[slug]
        if cached is None:
            return None
        return cached["texture"]

    # Try to find and load
    portrait_path = find_portrait(state.active_vault, character_name)
    if portrait_path is None:
        state.portrait_cache[slug] = None
        return None

    texture = load_portrait_texture(portrait_path)
    if texture is not None:
        state.portrait_cache[slug] = {"texture": texture, "path": str(portrait_path)}
        return texture

    state.portrait_cache[slug] = None
    return None


def draw_portrait(texture, x: int, y: int, size: int):
    """Draw a portrait texture scaled to fit a square, maintaining aspect ratio."""
    src_w = float(texture.width)
    src_h = float(texture.height)

    scale = min(size / src_w, size / src_h)
    dst_w = src_w * scale
    dst_h = src_h * scale
    dst_x = x + (size - dst_w) / 2
    dst_y = y + (size - dst_h) / 2

    source = ffi.new("Rectangle *", [0, 0, src_w, src_h])
    dest = ffi.new("Rectangle *", [dst_x, dst_y, dst_w, dst_h])
    origin = ffi.new("Vector2 *", [0, 0])

    DrawTexturePro(texture, source[0], dest[0], origin[0], 0.0, (255, 255, 255, 255))


def draw_image(texture, x: int, y: int, width: int, height: int):
    """Draw an image texture scaled to fit a rectangle, maintaining aspect ratio."""
    src_w = float(texture.width)
    src_h = float(texture.height)

    scale = min(width / src_w, height / src_h)
    dst_w = src_w * scale
    dst_h = src_h * scale
    dst_x = x + (width - dst_w) / 2
    dst_y = y + (height - dst_h) / 2

    source = ffi.new("Rectangle *", [0, 0, src_w, src_h])
    dest = ffi.new("Rectangle *", [dst_x, dst_y, dst_w, dst_h])
    origin = ffi.new("Vector2 *", [0, 0])

    DrawTexturePro(texture, source[0], dest[0], origin[0], 0.0, (255, 255, 255, 255))


def draw_portrait_placeholder(x: int, y: int, size: int):
    """Draw a placeholder box where a portrait would go."""
    DrawRectangle(x, y, size, size, (35, 35, 50, 255))
    DrawRectangleLines(x, y, size, size, BORDER)
    label = b"No Image"
    tw = MeasureText(label, 12)
    DrawText(label, x + (size - tw) // 2, y + size // 2 - 6, 12, TEXT_DIM)


def draw_image_placeholder(x: int, y: int, width: int, height: int, label: str = "No Image"):
    """Draw a placeholder box for an image field."""
    DrawRectangle(x, y, width, height, (35, 35, 50, 255))
    DrawRectangleLines(x, y, width, height, BORDER)
    label_b = label.encode('utf-8')
    tw = MeasureText(label_b, 12)
    DrawText(label_b, x + (width - tw) // 2, y + height // 2 - 6, 12, TEXT_DIM)
