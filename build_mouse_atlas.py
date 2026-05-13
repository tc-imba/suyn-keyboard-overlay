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

# Component dimensions (px)
BODY_W,  BODY_H  = 180, 240
LMB_W,   LMB_H   = 78, 110
RMB_W,   RMB_H   = 78, 110
MMB_W,   MMB_H   = 30, 30
WHEEL_W, WHEEL_H = 22, 52
AREA_W,  AREA_H  = 110, 110
DOT_W,   DOT_H   = 16, 16

# Overlay-space (where each element sits inside the OBS overlay)
OVERLAY_W = BODY_W            # 180
GAP_BELOW_BODY = 20
OVERLAY_H = BODY_H + GAP_BELOW_BODY + AREA_H   # 380

# Position of components inside the body (overlay coords)
LMB_POS = (6, 8)
RMB_POS = (BODY_W - RMB_W - 6, 8)               # (96, 8)
WHEEL_POS = ((BODY_W - WHEEL_W) // 2, 28)       # (79, 28)
MMB_POS = ((BODY_W - MMB_W) // 2, 90)           # (75, 90)
AREA_POS = ((OVERLAY_W - AREA_W) // 2, BODY_H + GAP_BELOW_BODY)  # (35, 260)
# Dot's home (top-left) so its 16×16 sprite is centred in the area
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
    pad = 6
    inner = (pad, pad, BODY_W - pad, BODY_H - pad)
    # Drop shadow
    def _shape(d, fill):
        d.rounded_rectangle(inner, radius=72, fill=fill)
    out = _drop_shadow((BODY_W, BODY_H), _shape, blur=5, offset=(0, 4))
    # Body
    body = Image.new("RGBA", (BODY_W, BODY_H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle(inner, radius=72, fill=CARD_RGBA,
                         outline=CARD_OUTLINE, width=3)
    # Soft vertical divider between LMB & RMB along the top half
    div_x = BODY_W // 2
    bd.line([(div_x, 18), (div_x, 130)], fill=DIVIDER_RGBA, width=2)
    out.alpha_composite(body)
    return out


def _button_sprite(w: int, h: int, radius: int, pressed: bool) -> Image.Image:
    """Translucent rounded patch used to overlay LMB/RMB/MMB regions.
    Idle = nearly invisible (lets the body show through). Pressed = pink tint."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if pressed:
        d.rounded_rectangle((0, 0, w, h), radius=radius, fill=PRESS_TINT,
                            outline=(232, 130, 170, 220), width=2)
    else:
        # Subtle highlight so the user can see where the button is even at rest.
        d.rounded_rectangle((0, 0, w, h), radius=radius,
                            fill=(255, 255, 255, 25))
    return im


def draw_wheel_strip() -> Image.Image:
    """Four 22x52 sprites placed horizontally with 3px gutters:
       [default | middle-pressed | scroll-up | scroll-down]"""
    total_w = 4 * WHEEL_W + 3 * BORDER
    strip = Image.new("RGBA", (total_w, WHEEL_H), (0, 0, 0, 0))

    def _wheel(state: str) -> Image.Image:
        w = Image.new("RGBA", (WHEEL_W, WHEEL_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(w)
        body_fill = PRESS_TINT if state == "middle" else WHEEL_BODY
        d.rounded_rectangle((1, 1, WHEEL_W - 1, WHEEL_H - 1),
                            radius=WHEEL_W // 2, fill=body_fill,
                            outline=WHEEL_ACCENT, width=2)
        # Horizontal stripes (the wheel "treads")
        for ty in (14, 22, 30, 38):
            d.line([(5, ty), (WHEEL_W - 5, ty)], fill=WHEEL_ACCENT, width=1)
        if state == "up":
            d.polygon([(WHEEL_W // 2, 4), (5, 12), (WHEEL_W - 5, 12)],
                       fill=DOT_RGBA)
        elif state == "down":
            d.polygon([(WHEEL_W // 2, WHEEL_H - 4),
                       (5, WHEEL_H - 12),
                       (WHEEL_W - 5, WHEEL_H - 12)], fill=DOT_RGBA)
        return w

    for i, state in enumerate(["default", "middle", "up", "down"]):
        x = i * (WHEEL_W + BORDER)
        strip.alpha_composite(_wheel(state), (x, 0))
    return strip


def draw_area() -> Image.Image:
    """Cream rounded square for the mouse-movement dot."""
    def _shape(d, fill):
        d.rounded_rectangle((4, 4, AREA_W - 4, AREA_H - 4), radius=18, fill=fill)
    out = _drop_shadow((AREA_W, AREA_H), _shape, blur=4, offset=(0, 3))
    area = Image.new("RGBA", (AREA_W, AREA_H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(area)
    ad.rounded_rectangle((4, 4, AREA_W - 4, AREA_H - 4), radius=18,
                         fill=CARD_RGBA, outline=CARD_OUTLINE, width=3)
    # Crosshair guides
    cx, cy = AREA_W // 2, AREA_H // 2
    ad.line([(cx, 16), (cx, AREA_H - 16)], fill=(132, 200, 168, 80), width=1)
    ad.line([(16, cy), (AREA_W - 16, cy)], fill=(132, 200, 168, 80), width=1)
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

    atlas.alpha_composite(_button_sprite(LMB_W, LMB_H, 38, pressed=False),
                          LMB_IDLE_ATLAS)
    atlas.alpha_composite(_button_sprite(LMB_W, LMB_H, 38, pressed=True),
                          LMB_PRESS_ATLAS)
    atlas.alpha_composite(_button_sprite(RMB_W, RMB_H, 38, pressed=False),
                          RMB_IDLE_ATLAS)
    atlas.alpha_composite(_button_sprite(RMB_W, RMB_H, 38, pressed=True),
                          RMB_PRESS_ATLAS)
    atlas.alpha_composite(_button_sprite(MMB_W, MMB_H, 12, pressed=False),
                          MMB_IDLE_ATLAS)
    atlas.alpha_composite(_button_sprite(MMB_W, MMB_H, 12, pressed=True),
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
