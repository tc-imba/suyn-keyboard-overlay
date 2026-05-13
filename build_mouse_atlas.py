"""Build the suyn mouse-overlay atlas + layout JSON.

Top-down stylized mouse silhouette with LMB / RMB / MMB / scroll / dot.
Visually consistent with the keyboard preset (cream cards, mint accents,
pink-tint pressed state).

Outputs:
  output/mouse-suyn.png
  output/mouse-suyn.json
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "output")

# Colour palette — matched to keyboard build_atlas.py (shadow + white outline)
CARD_RGBA       = (255, 246, 229, 235)  # cream body (same alpha as keyboard)
CARD_OUTLINE    = (255, 255, 255, 220)  # white outline (keyboard style)
PRESS_TINT      = (255, 180, 200, 130)  # pink wash on pressed state
DIVIDER_RGBA    = (132, 200, 168, 140)  # mint divider between LMB/RMB
WHEEL_BODY      = (200, 220, 210, 255)  # mint-tinted wheel body
WHEEL_ACCENT    = (132, 200, 168, 255)  # mint stripes
DOT_RGBA        = ( 70, 140, 110, 255)  # mint dot
SHADOW_RGBA     = (180, 140, 170, 90)   # match keyboard shadow

# The plugin auto-locates the pressed sprite at idle + cy + 3px (and the wheel
# auto-derives middle/up/down to the right at cx + 3px). Honour that gutter.
BORDER = 3

# Component dimensions (px).
# Keyboard reference (OBS-rendered): tile = 192, CARD_INSET = 22, pitch = 170.
# Tiles overlap by 22; CARD_INSET creates 22 px transparent inset on every side.
# Keyboard overlay height = 2 * pitch + tile = 340 + 192 = 532.
# Mouse mimics the same tile-stacking: body tile + trackpad tile overlap by 22,
# body tile uses pad=22 (= CARD_INSET) so its silhouette has matching insets.
TILE = 192            # keyboard tile size
PITCH = 170           # uniform pitch in OBS render (== keyboard pitch_x/y)
CARD_INSET = 22       # transparent inset around each tile (== keyboard CARD_INSET)
BODY_W,  BODY_H  = 280, 362     # 362 = PITCH + TILE (mouse "spans 2 rows")
LMB_W,   LMB_H   = 120, 170
RMB_W,   RMB_H   = 120, 170
MMB_W,   MMB_H   = 46, 46
WHEEL_W, WHEEL_H = 34, 80
SIDE_W,  SIDE_H  = 14, 44       # side buttons — half-pill (left half only)
AREA_W,  AREA_H  = TILE, TILE   # 192×192 — same as a key card
DOT_W,   DOT_H   = 22, 22

# Overlay-space (where each element sits inside the OBS overlay).
# Shift everything right by BODY_X_OFF to make room for side buttons on the left.
BODY_X_OFF = 10                  # extra left margin for side buttons
GAP_BELOW_BODY = -CARD_INSET    # -22 — tiles overlap like keyboard rows
OVERLAY_W = BODY_X_OFF + max(BODY_W, AREA_W)   # 10 + 280 = 290
OVERLAY_H = BODY_H + GAP_BELOW_BODY + AREA_H   # 362 - 22 + 192 = 532

# Position of components inside the overlay (all shifted right by BODY_X_OFF).
LMB_POS = (BODY_X_OFF + 30, 32)
RMB_POS = (BODY_X_OFF + BODY_W - RMB_W - 30, 32)
WHEEL_POS = (BODY_X_OFF + (BODY_W - WHEEL_W) // 2, 56)
MMB_POS = (BODY_X_OFF + (BODY_W - MMB_W) // 2, 160)
SIDE_BACK_POS = (BODY_X_OFF + CARD_INSET - SIDE_W + 2, 170)  # mouse5 — right edge aligns with body edge
SIDE_FWD_POS  = (BODY_X_OFF + CARD_INSET - SIDE_W + 2, 220) # mouse4
AREA_POS = (BODY_X_OFF + (BODY_W - AREA_W) // 2, BODY_H + GAP_BELOW_BODY)
AREA_CENTRE = (AREA_POS[0] + AREA_W // 2, AREA_POS[1] + AREA_H // 2)
DOT_POS = (AREA_CENTRE[0] - DOT_W // 2, AREA_CENTRE[1] - DOT_H // 2)


# ---------- atlas region layout ──────────────────────────────────────────
# Left: Body | Middle: Area top + small items below | Right: LMB/RMB pairs
# LMB/RMB: idle (transparent) on top, pressed (chibi) below (v+h+3 convention)
G = BORDER

# Left: Body
BODY_ATLAS         = (0, 0)

# Middle: Area on top, small items below
_MX                = BODY_W + G
AREA_ATLAS         = (_MX, 0)
_SY                = AREA_H + G
_sx                = _MX
SIDE_IDLE_ATLAS    = (_sx, _SY)
SIDE_PRESS_ATLAS   = (_sx, _SY + SIDE_H + G)
DOT_ATLAS          = (_sx, _SY + 2 * (SIDE_H + G) + 14)
_sx               += max(SIDE_W, DOT_W) + G
WHEEL_STRIP_ATLAS  = (_sx, _SY)
MMB_IDLE_ATLAS     = (_sx, _SY + WHEEL_H + G)
MMB_PRESS_ATLAS    = (_sx, _SY + WHEEL_H + G + MMB_H + G)

# Right: LMB and RMB side by side (idle top=transparent, pressed bottom=chibi)
_RX                = _MX + AREA_W + G
LMB_IDLE_ATLAS     = (_RX, 0)
LMB_PRESS_ATLAS    = (_RX, LMB_H + G)
RMB_IDLE_ATLAS     = (_RX + LMB_W + G, 0)
RMB_PRESS_ATLAS    = (RMB_IDLE_ATLAS[0], RMB_H + G)

ATLAS_W = RMB_IDLE_ATLAS[0] + RMB_W
ATLAS_H = max(BODY_H,
              LMB_PRESS_ATLAS[1] + LMB_H,
              MMB_PRESS_ATLAS[1] + MMB_H)


# ---------- drawing helpers ----------
def _drop_shadow(size, draw_fn, blur=4, offset=(0, 3)):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_fn(d, SHADOW_RGBA)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(layer, offset, layer)
    return out


def draw_body() -> Image.Image:
    """Cream body — keyboard-identical shadow (blur in place, no paste offset)."""
    pad = CARD_INSET
    radius = 90
    # Shadow: drawn 4px lower, blurred in place (same as keyboard make_card_rect)
    shadow = Image.new("RGBA", (BODY_W, BODY_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((pad, pad + 4, BODY_W - pad, BODY_H - pad),
                         radius=radius, fill=SHADOW_RGBA)
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    # Card: 4px shorter at bottom (same as keyboard)
    card = Image.new("RGBA", (BODY_W, BODY_H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((pad, pad, BODY_W - pad, BODY_H - pad - 4),
                         radius=radius, fill=CARD_RGBA,
                         outline=CARD_OUTLINE, width=2)
    # Soft vertical divider between LMB & RMB along the top half
    div_x = BODY_W // 2
    cd.line([(div_x, 24), (div_x, BODY_H // 2 + 10)],
            fill=DIVIDER_RGBA, width=2)
    out = Image.new("RGBA", (BODY_W, BODY_H), (0, 0, 0, 0))
    out = Image.alpha_composite(out, shadow)
    out = Image.alpha_composite(out, card)
    return out


def _button_sprite(w: int, h: int, radius: int, pressed: bool,
                    no_press_state: bool = False) -> Image.Image:
    """Translucent rounded patch used to overlay LMB/RMB/MMB regions.
    Idle = nearly invisible (lets the body show through). Pressed = pink tint.
    `no_press_state=True` makes idle == pressed (used for MMB)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    show_press = pressed and not no_press_state
    if show_press:
        d.rounded_rectangle((0, 0, w, h), radius=radius, fill=PRESS_TINT,
                            outline=(232, 130, 170, 220), width=2)
    else:
        pass  # Idle state: fully transparent
    return im


def _strip_white_bg(im: Image.Image, threshold: int = 240) -> Image.Image:
    """Knock out near-white pixels (white background removal)."""
    im = im.copy()
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r >= threshold and g >= threshold and b >= threshold:
                px[x, y] = (r, g, b, 0)
    return im


def _peek_button_sprite(w: int, h: int, radius: int, peek_img: Image.Image,
                         mirror: bool = False, x_offset: int = 0) -> Image.Image:
    """Pressed button sprite with a peeking chibi (white bg removed + cropped).
    x_offset: shift chibi left (negative) or right (positive)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Strip white background, then crop transparent border
    chibi = _strip_white_bg(peek_img)
    bbox = chibi.getbbox()
    if bbox:
        chibi = chibi.crop(bbox)
    if mirror:
        chibi = chibi.transpose(Image.FLIP_LEFT_RIGHT)
    # Scale chibi to 85% of button height (smaller after crop)
    target_h = int(h * 0.85)
    chibi = chibi.resize((int(chibi.width * target_h / chibi.height), target_h), Image.LANCZOS)
    # Centre vertically, shift horizontally
    cx = (w - chibi.width) // 2 + x_offset
    cy = (h - chibi.height) // 2
    im.alpha_composite(chibi, (cx, cy))
    return im


def draw_wheel_strip() -> Image.Image:
    """Four sprites placed horizontally with 3px gutters:
       [default | middle-pressed | scroll-up | scroll-down]"""
    total_w = 4 * WHEEL_W + 3 * BORDER
    strip = Image.new("RGBA", (total_w, WHEEL_H), (0, 0, 0, 0))
    # Tread stripes spread across most of the wheel height
    stripe_top, stripe_bot = 14, WHEEL_H - 14
    n_stripes = 5
    stripe_ys = [stripe_top + i * (stripe_bot - stripe_top) // (n_stripes - 1)
                 for i in range(n_stripes)]

    def _wheel(state: str) -> Image.Image:
        w = Image.new("RGBA", (WHEEL_W, WHEEL_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(w)
        body_fill = PRESS_TINT if state == "middle" else WHEEL_BODY
        d.rounded_rectangle((1, 1, WHEEL_W - 1, WHEEL_H - 1),
                            radius=WHEEL_W // 2, fill=body_fill,
                            outline=WHEEL_ACCENT, width=2)
        for ty in stripe_ys:
            d.line([(6, ty), (WHEEL_W - 6, ty)], fill=WHEEL_ACCENT, width=1)
        if state == "up":
            d.polygon([(WHEEL_W // 2, 5), (6, 16), (WHEEL_W - 6, 16)],
                       fill=DOT_RGBA)
        elif state == "down":
            d.polygon([(WHEEL_W // 2, WHEEL_H - 5),
                       (6, WHEEL_H - 16),
                       (WHEEL_W - 6, WHEEL_H - 16)], fill=DOT_RGBA)
        return w

    for i, state in enumerate(["default", "middle", "up", "down"]):
        x = i * (WHEEL_W + BORDER)
        strip.alpha_composite(_wheel(state), (x, 0))
    return strip


def draw_side_button(pressed: bool) -> Image.Image:
    """Half-pill side button — rounded on left, flat on right.
    Mint idle, pink pressed (like the wheel)."""
    # Draw a full pill twice the width, then crop the left half
    full_w = SIDE_W * 2
    full = Image.new("RGBA", (full_w, SIDE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(full)
    r = SIDE_H // 2
    if pressed:
        d.rounded_rectangle((1, 1, full_w - 1, SIDE_H - 1), radius=r,
                            fill=PRESS_TINT, outline=(232, 130, 170, 220), width=2)
    else:
        d.rounded_rectangle((1, 1, full_w - 1, SIDE_H - 1), radius=r,
                            fill=WHEEL_BODY, outline=WHEEL_ACCENT, width=2)
    return full.crop((0, 0, SIDE_W, SIDE_H))


def draw_area() -> Image.Image:
    """Cream rounded square (trackpad) — keyboard-identical shadow."""
    _INSET = 22
    _RADIUS = 22
    shadow = Image.new("RGBA", (AREA_W, AREA_H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((_INSET, _INSET + 4, AREA_W - _INSET, AREA_H - _INSET),
                         radius=_RADIUS, fill=SHADOW_RGBA)
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    card = Image.new("RGBA", (AREA_W, AREA_H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(card)
    ad.rounded_rectangle((_INSET, _INSET, AREA_W - _INSET, AREA_H - _INSET - 4),
                         radius=_RADIUS, fill=CARD_RGBA,
                         outline=CARD_OUTLINE, width=2)
    cx, cy = AREA_W // 2, AREA_H // 2
    ad.line([(cx, _INSET + 14), (cx, AREA_H - _INSET - 14)],
            fill=(132, 200, 168, 160), width=1)
    ad.line([(_INSET + 14, cy), (AREA_W - _INSET - 14, cy)],
            fill=(132, 200, 168, 160), width=1)
    out = Image.new("RGBA", (AREA_W, AREA_H), (0, 0, 0, 0))
    out = Image.alpha_composite(out, shadow)
    out = Image.alpha_composite(out, card)
    return out


def draw_dot() -> Image.Image:
    d_im = Image.new("RGBA", (DOT_W, DOT_H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(d_im)
    dd.ellipse((0, 0, DOT_W, DOT_H), fill=DOT_RGBA,
               outline=(255, 255, 255, 220), width=2)
    return d_im


# ---------- main build ----------
def build():
    os.makedirs(OUTPUT, exist_ok=True)
    atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (0, 0, 0, 0))

    atlas.alpha_composite(draw_body(), BODY_ATLAS)

    # Load peeking chibi for LMB/RMB pressed states
    peek = Image.open(os.path.join(HERE, "assets", "mouse", "peek.png")).convert("RGBA")

    # LMB/RMB: idle is transparent (not composited), pressed has chibi
    atlas.alpha_composite(_peek_button_sprite(LMB_W, LMB_H, 58, peek, mirror=False, x_offset=-10),
                          LMB_PRESS_ATLAS)
    atlas.alpha_composite(_peek_button_sprite(RMB_W, RMB_H, 58, peek, mirror=True, x_offset=10),
                          RMB_PRESS_ATLAS)
    # MMB has no visual pressed state (user spec): idle == pressed.
    atlas.alpha_composite(
        _button_sprite(MMB_W, MMB_H, 18, pressed=False, no_press_state=True),
        MMB_IDLE_ATLAS)
    atlas.alpha_composite(
        _button_sprite(MMB_W, MMB_H, 18, pressed=True, no_press_state=True),
        MMB_PRESS_ATLAS)

    atlas.alpha_composite(draw_wheel_strip(), WHEEL_STRIP_ATLAS)
    atlas.alpha_composite(draw_side_button(pressed=False), SIDE_IDLE_ATLAS)
    atlas.alpha_composite(draw_side_button(pressed=True),  SIDE_PRESS_ATLAS)
    atlas.alpha_composite(draw_area(), AREA_ATLAS)
    atlas.alpha_composite(draw_dot(), DOT_ATLAS)

    # Watermark in unused atlas area
    wm_layer = Image.new("RGBA", atlas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(wm_layer)
    wm_font = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "Chalkboard.ttc"), 16, index=1)
    wm_text = "made by tc-imba"
    bbox = wm_font.getbbox(wm_text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Below RMB pressed sprite (safe unused area)
    wx = RMB_PRESS_ATLAS[0] + RMB_W - tw - bbox[0]
    wy = RMB_PRESS_ATLAS[1] + RMB_H + 4 - bbox[1]
    d.text((wx, wy), wm_text, font=wm_font, fill=(120, 120, 120, 220))
    atlas.alpha_composite(wm_layer)

    out_png = os.path.join(OUTPUT, "mouse-suyn.png")
    atlas.save(out_png, "PNG", optimize=True)
    print(f"Wrote {out_png}  {atlas.size}  {os.path.getsize(out_png):,} bytes")

    # ----- JSON layout -----
    elements = [
        # Body silhouette
        {"id": "body", "type": 0, "z_level": 0,
         "mapping": [BODY_ATLAS[0], BODY_ATLAS[1], BODY_W, BODY_H],
         "pos": [BODY_X_OFF, 0]},
        # Left mouse button (LMB) — idle transparent, pressed chibi
        {"code": 1, "id": "lmb", "type": 3, "z_level": 1,
         "mapping": [LMB_IDLE_ATLAS[0], LMB_IDLE_ATLAS[1], LMB_W, LMB_H],
         "pos": list(LMB_POS)},
        # Right mouse button (RMB) — idle transparent, pressed chibi (mirrored)
        {"code": 2, "id": "rmb", "type": 3, "z_level": 1,
         "mapping": [RMB_IDLE_ATLAS[0], RMB_IDLE_ATLAS[1], RMB_W, RMB_H],
         "pos": list(RMB_POS)},
        # Middle mouse button (MMB) — code 3 — game action: noop
        {"code": 3, "id": "mmb", "type": 3, "z_level": 2,
         "mapping": [MMB_IDLE_ATLAS[0], MMB_IDLE_ATLAS[1], MMB_W, MMB_H],
         "pos": list(MMB_POS)},
        # Scroll wheel — game action: camera zoom
        {"id": "wheel", "type": 4, "z_level": 2,
         "mapping": [WHEEL_STRIP_ATLAS[0], WHEEL_STRIP_ATLAS[1],
                     WHEEL_W, WHEEL_H],
         "pos": list(WHEEL_POS)},
        # Side button forward (mouse5) — top
        {"code": 5, "id": "side_fwd", "type": 3, "z_level": 1,
         "mapping": [SIDE_IDLE_ATLAS[0], SIDE_IDLE_ATLAS[1], SIDE_W, SIDE_H],
         "pos": list(SIDE_BACK_POS)},
        # Side button back (mouse4) — bottom
        {"code": 4, "id": "side_back", "type": 3, "z_level": 1,
         "mapping": [SIDE_IDLE_ATLAS[0], SIDE_IDLE_ATLAS[1], SIDE_W, SIDE_H],
         "pos": list(SIDE_FWD_POS)},
        # Mouse-movement area background
        {"id": "area", "type": 0, "z_level": 0,
         "mapping": [AREA_ATLAS[0], AREA_ATLAS[1], AREA_W, AREA_H],
         "pos": list(AREA_POS)},
        # Mouse-movement dot — game action: look direction
        {"id": "dot", "type": 9, "z_level": 1,
         "mapping": [DOT_ATLAS[0], DOT_ATLAS[1], DOT_W, DOT_H],
         "mouse_radius": 45,
         "mouse_type": 0,
         "pos": list(DOT_POS)},
    ]
    layout = {
        "default_height": 0,
        "default_width": 0,
        "elements": elements,
        "flags": 8,                # mouse movement enabled
        "overlay_height": OVERLAY_H,
        "overlay_width": OVERLAY_W,
        "space_h": 0,
        "space_v": 0,
    }
    out_json = os.path.join(OUTPUT, "mouse-suyn.json")
    with open(out_json, "w") as f:
        json.dump(layout, f, indent=4, ensure_ascii=False)
    print(f"Wrote {out_json}")

    # JS wrappers for browser renderers (avoids CORS issues with file://)
    out_js = os.path.join(OUTPUT, "mouse-suyn.js")
    with open(out_js, "w") as f:
        f.write(f"var MOUSE_PRESET = {json.dumps(layout)};\n")
    print(f"Wrote {out_js}")

    # Also generate keyboard JS wrapper from existing JSON
    kb_json_path = os.path.join(OUTPUT, "wasd-suyn.json")
    if os.path.exists(kb_json_path):
        with open(kb_json_path) as f:
            kb_layout = json.load(f)
        kb_js = os.path.join(OUTPUT, "wasd-suyn.js")
        with open(kb_js, "w") as f:
            f.write(f"var KEYBOARD_PRESET = {json.dumps(kb_layout)};\n")
        print(f"Wrote {kb_js}")


if __name__ == "__main__":
    build()
