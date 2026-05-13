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

# Colour palette — match build_atlas.py
CARD_RGBA       = (255, 246, 229, 255)  # cream body
CARD_OUTLINE    = (132, 200, 168, 255)  # mint outline
PRESS_TINT      = (255, 180, 200, 130)  # pink wash on pressed state
DIVIDER_RGBA    = (132, 200, 168, 140)  # soft mint divider between LMB/RMB
WHEEL_BODY      = (200, 220, 210, 255)
WHEEL_ACCENT    = (132, 200, 168, 255)
DOT_RGBA        = ( 70, 140, 110, 255)
SHADOW_RGBA     = (180, 140, 170, 80)

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
AREA_W,  AREA_H  = TILE, TILE   # 192×192 — same as a key card
DOT_W,   DOT_H   = 22, 22

# Overlay-space (where each element sits inside the OBS overlay).
# Body tile and trackpad tile overlap by CARD_INSET (22), matching the keyboard
# row stacking. The visible silhouette + cream card edges leave a 22 px gap.
GAP_BELOW_BODY = -CARD_INSET    # -22 — tiles overlap like keyboard rows
OVERLAY_W = max(BODY_W, AREA_W)
OVERLAY_H = BODY_H + GAP_BELOW_BODY + AREA_H   # 362 - 22 + 192 = 532

# Position of components inside the body (overlay coords).
# Silhouette is inset by CARD_INSET=22; put buttons a few px inside that.
LMB_POS = (30, 32)
RMB_POS = (BODY_W - RMB_W - 30, 32)
WHEEL_POS = ((BODY_W - WHEEL_W) // 2, 56)
MMB_POS = ((BODY_W - MMB_W) // 2, 160)
AREA_POS = ((OVERLAY_W - AREA_W) // 2, BODY_H + GAP_BELOW_BODY)
# Dot's home (top-left) so its sprite is centred in the trackpad
AREA_CENTRE = (AREA_POS[0] + AREA_W // 2, AREA_POS[1] + AREA_H // 2)
DOT_POS = (AREA_CENTRE[0] - DOT_W // 2, AREA_CENTRE[1] - DOT_H // 2)


# ---------- atlas region layout (where each sprite lives in the PNG) ----------
# Stack everything in a tight grid. Idle/pressed pairs are stacked vertically
# with BORDER (3px) gutter so the plugin's auto-press derivation works.
BODY_ATLAS         = (0, 0)
LMB_IDLE_ATLAS     = (BODY_W + 10, 0)
LMB_PRESS_ATLAS    = (LMB_IDLE_ATLAS[0], LMB_IDLE_ATLAS[1] + LMB_H + BORDER)
RMB_IDLE_ATLAS     = (LMB_IDLE_ATLAS[0] + LMB_W + 10, 0)
RMB_PRESS_ATLAS    = (RMB_IDLE_ATLAS[0], RMB_IDLE_ATLAS[1] + RMB_H + BORDER)
MMB_IDLE_ATLAS     = (RMB_IDLE_ATLAS[0] + RMB_W + 10, 0)
MMB_PRESS_ATLAS    = (MMB_IDLE_ATLAS[0], MMB_IDLE_ATLAS[1] + MMB_H + BORDER)
# Wheel: 4 horizontal sprites with 3px gutters (default + middle + up + down)
WHEEL_STRIP_ATLAS  = (BODY_W + 10, RMB_PRESS_ATLAS[1] + RMB_H + 10)
AREA_ATLAS         = (0, BODY_H + 10)
DOT_ATLAS          = (AREA_W + 10, BODY_H + 10)

ATLAS_W = max(MMB_IDLE_ATLAS[0] + MMB_W,
              WHEEL_STRIP_ATLAS[0] + 4 * WHEEL_W + 3 * BORDER)
ATLAS_H = max(LMB_PRESS_ATLAS[1] + LMB_H,
              WHEEL_STRIP_ATLAS[1] + WHEEL_H,
              AREA_ATLAS[1] + AREA_H)


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
    """Cream teardrop silhouette: rounded rect with a more rounded top."""
    pad = CARD_INSET   # 22 — match keyboard's CARD_INSET so silhouette has
                       # the same 22 px transparent border as a key tile.
    inner = (pad, pad, BODY_W - pad, BODY_H - pad)
    radius = 105   # generous radius matching the silhouette
    def _shape(d, fill):
        d.rounded_rectangle(inner, radius=radius, fill=fill)
    out = _drop_shadow((BODY_W, BODY_H), _shape, blur=6, offset=(0, 5))
    body = Image.new("RGBA", (BODY_W, BODY_H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle(inner, radius=radius, fill=CARD_RGBA,
                         outline=CARD_OUTLINE, width=3)
    # Soft vertical divider between LMB & RMB along the top half
    div_x = BODY_W // 2
    bd.line([(div_x, 24), (div_x, BODY_H // 2 + 10)],
            fill=DIVIDER_RGBA, width=2)
    out.alpha_composite(body)
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
        # Subtle highlight so the user can see where the button is even at rest.
        d.rounded_rectangle((0, 0, w, h), radius=radius,
                            fill=(255, 255, 255, 25))
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
        # macOS / libuiohook doesn't reliably deliver MMB release events, so a
        # press-tinted "middle" sprite would get stuck pink. Use the neutral
        # body fill for the middle state — visually identical to default.
        body_fill = WHEEL_BODY
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


def draw_area() -> Image.Image:
    """Cream rounded square (trackpad) styled like a keyboard key card —
    same CARD_INSET=22, same radius=22, same drop shadow as a key tile."""
    CARD_INSET = 22
    RADIUS = 22
    inner = (CARD_INSET, CARD_INSET, AREA_W - CARD_INSET, AREA_H - CARD_INSET)
    def _shape(d, fill):
        d.rounded_rectangle(inner, radius=RADIUS, fill=fill)
    out = _drop_shadow((AREA_W, AREA_H), _shape, blur=6, offset=(0, 4))
    area = Image.new("RGBA", (AREA_W, AREA_H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(area)
    ad.rounded_rectangle(inner, radius=RADIUS, fill=CARD_RGBA,
                         outline=(255, 255, 255, 220), width=2)
    ad.rounded_rectangle(inner, radius=RADIUS, outline=CARD_OUTLINE, width=3)
    # Soft crosshair guides centred in the card
    cx, cy = AREA_W // 2, AREA_H // 2
    ad.line([(cx, CARD_INSET + 14), (cx, AREA_H - CARD_INSET - 14)],
            fill=(132, 200, 168, 80), width=1)
    ad.line([(CARD_INSET + 14, cy), (AREA_W - CARD_INSET - 14, cy)],
            fill=(132, 200, 168, 80), width=1)
    out.alpha_composite(area)
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

    atlas.alpha_composite(_button_sprite(LMB_W, LMB_H, 58, pressed=False),
                          LMB_IDLE_ATLAS)
    atlas.alpha_composite(_button_sprite(LMB_W, LMB_H, 58, pressed=True),
                          LMB_PRESS_ATLAS)
    atlas.alpha_composite(_button_sprite(RMB_W, RMB_H, 58, pressed=False),
                          RMB_IDLE_ATLAS)
    atlas.alpha_composite(_button_sprite(RMB_W, RMB_H, 58, pressed=True),
                          RMB_PRESS_ATLAS)
    # MMB has no visual pressed state (user spec): idle == pressed.
    atlas.alpha_composite(
        _button_sprite(MMB_W, MMB_H, 18, pressed=False, no_press_state=True),
        MMB_IDLE_ATLAS)
    atlas.alpha_composite(
        _button_sprite(MMB_W, MMB_H, 18, pressed=True, no_press_state=True),
        MMB_PRESS_ATLAS)

    atlas.alpha_composite(draw_wheel_strip(), WHEEL_STRIP_ATLAS)
    atlas.alpha_composite(draw_area(), AREA_ATLAS)
    atlas.alpha_composite(draw_dot(), DOT_ATLAS)

    out_png = os.path.join(OUTPUT, "mouse-suyn.png")
    atlas.save(out_png, "PNG", optimize=True)
    print(f"Wrote {out_png}  {atlas.size}  {os.path.getsize(out_png):,} bytes")

    # ----- JSON layout -----
    elements = [
        # Body silhouette
        {"id": "body", "type": 0, "z_level": 0,
         "mapping": [BODY_ATLAS[0], BODY_ATLAS[1], BODY_W, BODY_H],
         "pos": [0, 0]},
        # Left mouse button (LMB)  — uiohook code 1 — game action: attack
        {"code": 1, "id": "lmb", "type": 3, "z_level": 1,
         "mapping": [LMB_IDLE_ATLAS[0], LMB_IDLE_ATLAS[1], LMB_W, LMB_H],
         "pos": list(LMB_POS)},
        # Right mouse button (RMB) — code 2 — game action: dodge (same as Shift)
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


if __name__ == "__main__":
    build()
