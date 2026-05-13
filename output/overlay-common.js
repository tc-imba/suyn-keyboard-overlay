/*
    Shared overlay renderer for suyn keyboard/mouse input overlay.
    Loaded by keyboard-renderer.html, mouse-renderer.html, full-renderer.html.
*/

const TEXTURE_SPACE = 3;
const WS_URL = "ws://localhost:16899/";
const ET = { TEXTURE: 0, KEYBOARD_KEY: 1, MOUSE_BUTTON: 3, WHEEL: 4, MOUSE_MOVEMENT: 9 };

// ── URL params ──────────────────────────────────────────────────────────
const params = new URLSearchParams(location.search);
const DEBUG      = params.get("debug") === "1";
const MOUSE_SENS = parseFloat(params.get("sens"))   || 50;
const DECAY      = parseFloat(params.get("decay"))   || 0.6;
const ATTACK     = parseFloat(params.get("attack"))  || 0.1;
const IDLE_MS    = parseInt(params.get("idle"))       || 50;
const WHEEL_DUR  = parseInt(params.get("wheel_dur")) || 250;
const IS_MAC     = /Mac|iPhone|iPad/.test(navigator.platform);

// ── Debug ───────────────────────────────────────────────────────────────
let _debugLines = [];
function dbg(msg) {
    if (!DEBUG) return;
    const el = document.getElementById("debug");
    if (!el) return;
    _debugLines.unshift(msg);
    if (_debugLines.length > 6) _debugLines.pop();
    el.textContent = _debugLines.join("\n");
    console.log(msg);
}

// ── VK → scan code mapping ──────────────────────────────────────────────
const VK_TO_SC = {
    0x57:0x11, 0x41:0x1E, 0x53:0x1F, 0x44:0x20,
    0x51:0x10, 0x45:0x12, 0x52:0x13, 0x54:0x14,
    0x5A:0x2C, 0x09:0x0F, 0x20:0x39,
    0x10:0x2A, 0xA0:0x2A, 0xA1:0x36,
    0x11:0x1D, 0xA2:0x1D, 0xA3:0x0E1D,
    40976:0x2A, 40977:0x1D, 40978:0x38, 41232:0x36, 41233:0x0E1D,
};
function resolveKeycode(kc) { return VK_TO_SC[kc] !== undefined ? VK_TO_SC[kc] : kc; }

// ── Element helpers ─────────────────────────────────────────────────────
function parseElements(preset, xOff = 0) {
    return preset.elements
        .map(d => ({
            ...d, pressed: false,
            u: d.mapping[0], v: d.mapping[1], w: d.mapping[2], h: d.mapping[3],
            x: d.pos[0] + xOff, y: d.pos[1],
            baseX: d.pos[0] + xOff, baseY: d.pos[1],
            wheelDir: 0, lastWheelTime: 0,
            offsetX: d.pos[0] + xOff, offsetY: d.pos[1],
        }))
        .sort((a, b) => a.z_level - b.z_level);
}

// ── Keyboard input ──────────────────────────────────────────────────────
const _typedTimers = {};
function setKey(elements, kc, pressed) {
    const sc = resolveKeycode(kc);
    for (const el of elements) if (el.code === sc) el.pressed = pressed;
}
function flashKey(elements, kc) {
    const sc = resolveKeycode(kc);
    setKey(elements, sc, true);
    clearTimeout(_typedTimers[sc]);
    _typedTimers[sc] = setTimeout(() => setKey(elements, sc, false), 150);
}

// ── Mouse input ─────────────────────────────────────────────────────────
function setButton(elements, code, pressed) {
    if (IS_MAC && code === 3) return;
    for (const el of elements) {
        if (el.type === ET.MOUSE_BUTTON && el.code === code) el.pressed = pressed;
        if (el.type === ET.WHEEL && code === 3) el.pressed = pressed;
    }
}
function setWheel(elements, dir) {
    for (const el of elements)
        if (el.type === ET.WHEEL) { el.wheelDir = dir; el.lastWheelTime = Date.now(); }
}

// ── Mouse movement tracking ─────────────────────────────────────────────
let _curMX = -1, _curMY = -1, _frMX = -1, _frMY = -1;
let _dotFX = 0, _dotFY = 0, _lastMoveT = performance.now();

function updateMousePos(x, y) { _curMX = x; _curMY = y; }

function tickMouseDot(elements) {
    const now = performance.now();
    if (_curMX >= 0) {
        if (_frMX < 0) { _frMX = _curMX; _frMY = _curMY; _lastMoveT = now; }
        let dx = _curMX - _frMX, dy = _curMY - _frMY;
        _frMX = _curMX; _frMY = _curMY;
        if (Math.abs(dx) > 0 || Math.abs(dy) > 0) {
            const tFX = Math.max(-1, Math.min(1, dx / MOUSE_SENS));
            const tFY = Math.max(-1, Math.min(1, dy / MOUSE_SENS));
            _dotFX += (tFX - _dotFX) * (Math.abs(tFX) > Math.abs(_dotFX) ? 1.0 : ATTACK);
            _dotFY += (tFY - _dotFY) * (Math.abs(tFY) > Math.abs(_dotFY) ? 1.0 : ATTACK);
            _lastMoveT = now;
        } else if (now - _lastMoveT > IDLE_MS) {
            _dotFX *= DECAY; _dotFY *= DECAY;
            if (Math.abs(_dotFX) < 0.005) _dotFX = 0;
            if (Math.abs(_dotFY) < 0.005) _dotFY = 0;
        }
    }
    for (const el of elements) {
        if (el.type === ET.MOUSE_MOVEMENT) {
            const r = el.mouse_radius || 45;
            el.offsetX = el.baseX + r * _dotFX;
            el.offsetY = el.baseY + r * _dotFY;
        }
    }
}

function tickWheel(elements) {
    const now = Date.now();
    for (const el of elements)
        if (el.type === ET.WHEEL && el.wheelDir !== 0 && now - el.lastWheelTime > WHEEL_DUR)
            el.wheelDir = 0;
}

// ── Drawing ─────────────────────────────────────────────────────────────
function drawKeyboardElements(ctx, atlas, elements) {
    if (!atlas.complete || atlas.naturalWidth === 0) return;
    for (const el of elements) {
        if (el.pressed)
            ctx.drawImage(atlas, el.u, el.v + el.h + TEXTURE_SPACE, el.w, el.h, el.x, el.y, el.w, el.h);
        else
            ctx.drawImage(atlas, el.u, el.v, el.w, el.h, el.x, el.y, el.w, el.h);
    }
}

function drawMouseElements(ctx, atlas, elements) {
    if (!atlas.complete || atlas.naturalWidth === 0) return;
    for (const el of elements) {
        switch (el.type) {
            case ET.TEXTURE:
                ctx.drawImage(atlas, el.u, el.v, el.w, el.h, el.x, el.y, el.w, el.h); break;
            case ET.MOUSE_BUTTON:
                if (el.pressed)
                    ctx.drawImage(atlas, el.u, el.v + el.h + TEXTURE_SPACE, el.w, el.h, el.x, el.y, el.w, el.h);
                else
                    ctx.drawImage(atlas, el.u, el.v, el.w, el.h, el.x, el.y, el.w, el.h);
                break;
            case ET.WHEEL: {
                ctx.drawImage(atlas, el.u, el.v, el.w, el.h, el.x, el.y, el.w, el.h);
                if (el.pressed) {
                    const su = el.u + el.w + TEXTURE_SPACE;
                    ctx.drawImage(atlas, su, el.v, el.w, el.h, el.x, el.y, el.w, el.h);
                }
                if (el.wheelDir === 1) {
                    const su = el.u + (el.w + TEXTURE_SPACE) * 2;
                    ctx.drawImage(atlas, su, el.v, el.w, el.h, el.x, el.y, el.w, el.h);
                } else if (el.wheelDir === -1) {
                    const su = el.u + (el.w + TEXTURE_SPACE) * 3;
                    ctx.drawImage(atlas, su, el.v, el.w, el.h, el.x, el.y, el.w, el.h);
                }
                break;
            }
            case ET.MOUSE_MOVEMENT:
                ctx.drawImage(atlas, el.u, el.v, el.w, el.h, el.offsetX, el.offsetY, el.w, el.h); break;
        }
    }
}

// ── WebSocket ───────────────────────────────────────────────────────────
function connectWS(kbElements, msElements) {
    let ws;
    try { ws = new WebSocket(WS_URL); } catch { setTimeout(() => connectWS(kbElements, msElements), 3000); return; }
    ws.onmessage = (e) => {
        let data;
        try { data = JSON.parse(e.data); } catch { return; }
        const t = data.event_type;

        if (kbElements && kbElements.length) {
            if (t === "key_pressed") setKey(kbElements, data.keycode, true);
            else if (t === "key_released") setKey(kbElements, data.keycode, false);
            else if (t === "key_typed") flashKey(kbElements, data.keycode);
        }

        if (msElements && msElements.length) {
            if (t === "mouse_pressed") setButton(msElements, data.button, true);
            else if (t === "mouse_released") setButton(msElements, data.button, false);
            else if (t === "mouse_moved" || t === "mouse_dragged") updateMousePos(data.x, data.y);
            else if (t === "mouse_wheel") setWheel(msElements, data.rotation > 0 ? 1 : -1);
        }

        if (t.startsWith("key"))
            dbg(`${t} kc=${data.keycode} sc=${resolveKeycode(data.keycode)}`);
        else if (t.startsWith("mouse") && t !== "mouse_moved" && t !== "mouse_dragged")
            dbg(`${t} btn=${data.button||""} rot=${data.rotation||""}`);
    };
    ws.onclose = () => setTimeout(() => connectWS(kbElements, msElements), 2000);
    ws.onerror = () => {};
}
