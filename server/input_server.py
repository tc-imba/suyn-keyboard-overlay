"""Standalone WebSocket server that captures global keyboard/mouse input
and broadcasts events in the same JSON format as the input-overlay OBS plugin.

Usage:
    pip install pynput websockets
    python input_server.py [--port 16899]

Browser sources (keyboard-renderer.html, mouse-renderer.html) connect to
ws://localhost:16899/ and receive JSON events identical to those the native
input-overlay plugin would send.
"""

import argparse
import asyncio
import ctypes
import json
import sys
import threading
import time
from collections import deque

try:
    from pynput import keyboard, mouse
except ImportError:
    sys.exit("pynput is required.  Install it with:  pip install pynput")

try:
    import websockets
except ImportError:
    sys.exit("websockets is required.  Install it with:  pip install websockets")

# ── Windows scan-code conversion ─────────────────────────────────────────
user32 = ctypes.windll.user32
MAPVK_VK_TO_VSC_EX = 4  # returns extended scan code when applicable


def _vk_to_scancode(vk: int) -> int:
    """Convert a Windows virtual-key code to a uiohook-compatible scan code."""
    sc = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC_EX)
    if sc == 0:
        return 0
    # Windows returns extended keys as 0xE0XX.
    # uiohook encodes most of these as 0x0EXX.
    if sc > 0xFF:
        high = (sc >> 8) & 0xFF
        low = sc & 0xFF
        if high == 0xE0:
            sc = 0x0E00 | low
        elif high == 0xE1:
            sc = 0x0100 | low
    return sc


def _key_vk(key) -> int:
    """Extract the Windows VK code from a pynput key object."""
    # Character keys: KeyCode with .vk
    vk = getattr(key, "vk", None)
    if vk is not None:
        return vk
    # Special keys: Key enum whose .value is a KeyCode
    val = getattr(key, "value", None)
    if val is not None:
        return getattr(val, "vk", 0)
    return 0


# ── Thread-safe message queue ────────────────────────────────────────────
_queue: deque = deque(maxlen=4096)


def _enqueue(event_type: str, **fields):
    msg = json.dumps({
        "time": time.time() * 1000,
        "event_source": "local",
        "event_type": event_type,
        **fields,
    })
    _queue.append(msg)


# ── Keyboard hooks ───────────────────────────────────────────────────────
def _on_key_press(key):
    sc = _vk_to_scancode(_key_vk(key))
    if sc:
        _enqueue("key_pressed", mask=0, keycode=sc, rawcode=sc)


def _on_key_release(key):
    sc = _vk_to_scancode(_key_vk(key))
    if sc:
        _enqueue("key_released", mask=0, keycode=sc, rawcode=sc)


# ── Mouse hooks ──────────────────────────────────────────────────────────
_BUTTON_MAP = {
    mouse.Button.left: 1,
    mouse.Button.right: 2,
    mouse.Button.middle: 3,
}

# Throttle mouse-move events (send at most every 5 ms)
_last_move_time = 0.0
_MOVE_INTERVAL = 0.005


def _on_click(x, y, button, pressed):
    btn = _BUTTON_MAP.get(button, 0)
    if btn == 0:
        return
    evt = "mouse_pressed" if pressed else "mouse_released"
    _enqueue(evt, mask=0, button=btn, clicks=1, x=int(x), y=int(y))


def _on_move(x, y):
    global _last_move_time
    now = time.monotonic()
    if now - _last_move_time < _MOVE_INTERVAL:
        return
    _last_move_time = now
    _enqueue("mouse_moved", mask=0, button=0, clicks=0, x=int(x), y=int(y))


def _on_scroll(x, y, dx, dy):
    _enqueue("mouse_wheel", mask=0, type=1,
             delta=abs(dy), rotation=int(dy),
             direction=3, x=int(x), y=int(y))


# ── WebSocket server ─────────────────────────────────────────────────────
_clients: set = set()


async def _ws_handler(websocket):
    _clients.add(websocket)
    addr = websocket.remote_address
    print(f"  + client connected  ({addr[0]}:{addr[1]})  [{len(_clients)} total]")
    try:
        async for _ in websocket:
            pass  # we only broadcast, never consume client data
    finally:
        _clients.discard(websocket)
        print(f"  - client disconnected ({addr[0]}:{addr[1]})  [{len(_clients)} total]")


async def _broadcaster():
    """Drain the message queue and fan out to every connected client."""
    while True:
        while _queue:
            msg = _queue.popleft()
            if _clients:
                coros = [c.send(msg) for c in list(_clients)]
                await asyncio.gather(*coros, return_exceptions=True)
        await asyncio.sleep(0.002)  # 2 ms poll


async def _serve(port: int):
    # Start pynput listeners (they run their own daemon threads)
    kb = keyboard.Listener(on_press=_on_key_press, on_release=_on_key_release)
    ms = mouse.Listener(on_click=_on_click, on_move=_on_move, on_scroll=_on_scroll)
    kb.start()
    ms.start()
    print(f"Input hooks active  (keyboard + mouse)")
    print(f"WebSocket server listening on  ws://localhost:{port}/")
    print(f"Press Ctrl+C to stop.\n")

    async with websockets.serve(_ws_handler, "localhost", port):
        await _broadcaster()


# ── Entry point ──────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="input-overlay WebSocket relay server")
    ap.add_argument("--port", type=int, default=16899,
                    help="WebSocket server port (default: 16899)")
    args = ap.parse_args()
    try:
        asyncio.run(_serve(args.port))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
