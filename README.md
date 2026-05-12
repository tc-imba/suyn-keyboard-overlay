# suyn keyboard overlay

Cute chibi keyboard preset for the [input-overlay](https://github.com/univrsal/input-overlay) OBS plugin.

Two PNG variants share **one** layout JSON (`output/wasd-suyn.json`) — pick whichever PNG you prefer in OBS, the layout file stays the same:

| PNG | Series |
| --- | --- |
| `output/wasd-suyn.png`  | Series 1 — refined 表情包1 chibis |
| `output/wasd-suyn2.png` | Series 2 — 表情包2 chibis + 哇哦 / 伸懒腰 / Q版小人 specials |

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
python3 build_atlas.py
```

Requires Pillow (`pip install Pillow`) and Chalkboard SE installed at the macOS default path.

## Install in OBS

1. Copy the generated PNG + matching JSON anywhere.
2. In OBS, add an `Input Overlay` source.
3. Set **Image file** to the `.png` and **Layout file** to the `.json`.
4. Enable **Monitor input**.

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
