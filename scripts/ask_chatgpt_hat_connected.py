"""Attach NEW captures; SEATED only if face+hat are one connected person."""
from __future__ import annotations

import ctypes
import subprocess
import time
from pathlib import Path

import pyautogui
from PIL import ImageGrab

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

ROOT = Path(r"C:\Users\user\Documents\whack-a-name")
STORE = Path(
    r"C:\Users\user\AppData\Local\Cursor\AgentStores\cursor_agent_stores"
    r"\bc-f617877b-eaec-4432-8db1-768b13c985e8\files\media\whack-a-name"
)
user32 = ctypes.windll.user32


def find_hwnd(exact=None, substr=None):
    found = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def foreach(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if (exact and buf.value == exact) or (substr and substr in buf.value):
                    found.append((hwnd, buf.value))
        return True

    user32.EnumWindows(EnumWindowsProc(foreach), 0)
    return found


def focus(hwnd):
    for h, _ in find_hwnd(substr="Opera"):
        user32.ShowWindow(h, 6)
    time.sleep(0.2)
    fg = user32.GetForegroundWindow()
    user32.AttachThreadInput(
        user32.GetWindowThreadProcessId(fg, None),
        user32.GetWindowThreadProcessId(hwnd, None),
        True,
    )
    user32.ShowWindow(hwnd, 9)
    user32.ShowWindow(hwnd, 3)
    user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(
        user32.GetWindowThreadProcessId(fg, None),
        user32.GetWindowThreadProcessId(hwnd, None),
        False,
    )
    time.sleep(0.7)


def set_clip_text(text: str):
    ps = ROOT / "_clip.ps1"
    ps.write_text(f"Set-Clipboard -Value @'\n{text}\n'@", encoding="utf-8")
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps)],
        check=True,
    )


def set_clip_image(path: Path):
    ps = ROOT / "_clip_img.ps1"
    ps.write_text(
        "Add-Type -AssemblyName System.Windows.Forms\n"
        "Add-Type -AssemblyName System.Drawing\n"
        f"$img = [System.Drawing.Image]::FromFile('{path}')\n"
        "[System.Windows.Forms.Clipboard]::SetImage($img)\n"
        "$img.Dispose()\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps)],
        check=True,
    )


PROMPT = """These 3 NEW images are attached above this message (full board, hole close-up, baked face on dark void).

Ignore every prior BOARD:SEATED — those judged fake gray hair-domes.

Required: recognisable TopRock face fills the hole; party hat brim on HIS real hair; face+hat are ONE connected person. Reject gray/trapezoid dome, hat on fake mound, or face floating under a detached hat.

Reply with EXACTLY one first line:
BOARD: SEATED
or
BOARD: NOT_SEATED

Then 2 short bullets: (1) hat brim on real hair of same head? (2) any gray/fake dome between face and hat?

SEATED only if face and hat are one connected person. If NOT_SEATED, bake numbers only: RIM_INTO_HAIR, HAT_WIDTH_FRAC, facePx_front, visibleY_front.
"""


def main():
    hits = find_hwnd(exact="ChatGPT") or find_hwnd(substr="ChatGPT")
    if not hits:
        raise SystemExit("no ChatGPT")
    hwnd, title = hits[0]
    print("focus", title)
    focus(hwnd)

    # New chat so attachments are not lost in a long thread
    pyautogui.hotkey("ctrl", "n")
    time.sleep(1.5)
    # Click composer (bottom center-ish on maximized ChatGPT)
    pyautogui.click(960, 1180)
    time.sleep(0.4)

    imgs = [
        STORE / "play-aligned.png",
        STORE / "_proof_front.png",
        STORE / "_baked_face_05_void.png",
    ]
    for p in imgs:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        print("img", p.name)
        set_clip_image(p)
        time.sleep(0.4)
        pyautogui.click(960, 1180)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(3.0)

    set_clip_text(PROMPT)
    time.sleep(0.3)
    pyautogui.click(960, 1180)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    print("waiting")
    time.sleep(80)
    focus(hwnd)
    time.sleep(0.4)
    out = ROOT / "_chatgpt_hat_connected_reply.png"
    ImageGrab.grab().save(out)
    ImageGrab.grab().save(STORE / "_chatgpt_hat_connected_reply.png")
    print("saved", out)


if __name__ == "__main__":
    main()
