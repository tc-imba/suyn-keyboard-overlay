# suyn keyboard overlay

Cute chibi keyboard + mouse preset for the [input-overlay](https://github.com/univrsal/input-overlay) OBS plugin.

## Keyboard

Two PNG variants share **one** layout JSON (`output/wasd-suyn.json`) — pick whichever PNG you prefer in OBS, the layout file stays the same:

| PNG | Series |
| --- | --- |
| `output/wasd-suyn.png`  | Series 1 — refined 表情包1 chibis |
| `output/wasd-suyn2.png` | Series 2 — 表情包2 chibis + 哇哦 / 伸懒腰 / Q版小人 specials |

## Mouse

Separate companion overlay at `output/mouse-suyn.png` + `output/mouse-suyn.json`.
Stylized top-down silhouette: LMB / RMB / MMB (with pink pressed-state),
scroll wheel (rotates on scroll), and a movement-dot area showing where the
cursor is drifting.

## Layout

```
Row 1:  Tab  Q  W  E  R
Row 2:  Shift  A  S  D  T
Row 3:  Ctrl  Z  [ ─── Space ─── ]
```

- Idle: cream rounded card with the key letter (Chalkboard SE Bold, mint-green outline).
- Pressed: cream card with the chibi sticker.
- Spacebar idle: avatar circle (left) + Suyn logo (right), symmetric margins.
- Spacebar pressed: bottom strip of 便利贴 ("劳资蜀道山" with flower icon).

## Build

```sh
python3 build_atlas.py        # keyboard atlases (wasd-suyn.png, wasd-suyn2.png)
python3 build_mouse_atlas.py  # mouse atlas + JSON (mouse-suyn.png, mouse-suyn.json)
```

Requires Pillow (`pip install Pillow`) and Chalkboard SE installed at the macOS default path.

## Install in OBS

### Native source (recommended)

1. Copy the generated PNG + matching JSON anywhere.
2. In OBS, add an `Input Overlay` source per overlay (one for keyboard, one for
   mouse if you want both — they can be positioned independently).
3. Set **Image file** to the `.png` and **Layout file** to the `.json`.
4. Enable **Monitor input**.

### Browser source (for OBS forks like livehime)

Requires the input-overlay plugin's WebSocket server enabled on port 16899
(OBS → Tools → Input Overlay Settings).

Add a **Browser Source** with local file and set the size accordingly:

| Renderer | File | Size |
|----------|------|------|
| Keyboard only | `output/keyboard-renderer.html` | 872 × 532 |
| Mouse only | `output/mouse-renderer.html` | 290 × 532 |
| Full (keyboard + mouse) | `output/full-renderer.html` | 1140 × 532 |

URL parameters (append to the local file path, e.g. `?debug=1&sens=80`):

| Param | Default | Description |
|-------|---------|-------------|
| `debug` | off | `1` to show debug overlay |
| `sens` | 50 | Mouse dot sensitivity (mouse/full only) |
| `decay` | 0.6 | Dot return-to-center speed (0–0.99) |
| `attack` | 0.1 | Dot smoothing for direction changes (0–1) |
| `idle` | 50 | Ms of no movement before decay starts |
| `wheel_dur` | 250 | Ms the scroll arrow shows |
| `gap` | -22 | Pixel gap between keyboard and mouse (full only) |

## Assets

- `assets/series1/` — 12 chibis from 表情包1 (ASCII-renamed).
- `assets/series2/` — 9 chibis from 表情包2 (chibi01–chibi09) + `wow.png`, `stretch.jpg`, `chibi_hips.png`.
- `assets/space/` — `avatar.jpg` (head-shot star), `suyn-logo.webp`, `sticky-note.jpg` (便利贴).

## Credits

All chibi artwork, the avatar, the Suyn logo, and the 便利贴 sticker are by
**[苏烟Suyn](https://space.bilibili.com/33004908)** on Bilibili. All credit for
the art goes to her — this repo just packages the assets into an input-overlay
preset. Please support the original artist.

## License

Code and layout in this repository are released under the [MIT License](LICENSE).
The license covers only the build script and layout JSON; the artwork assets
remain the property of their creator (see Credits above).
