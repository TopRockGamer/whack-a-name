"""Attach pose proof to ChatGPT Desktop and ask for concrete hat/hole offsets."""
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
POSE = ROOT / "_fix_pose.png"
PROMPT = """These are live screenshots of Whack-a-TopRock at http://localhost:5188/?pose=1 (Phaser 3, 1280x720).

PROBLEM: party hats don't sit cleanly on the circular TopRock faces in the wooden holes.

Current layout constants:
- HOLES (centers): back (521,410), (822,410), (1125,410); front (475,493), (821,493), (1161,493)
- facePx: back 108, front 128; faces masked to hole ellipses back 96x66, front 112x78
- hat: party_hat.png 174x214, origin (0.5, 0.9), scale = facePx*0.72/174, angle -8
- brim world Y = (hole.y - 2 - maskH/2) - brimLift, with brimLift = -14

Please inspect the attached image(s) and reply with a CONCRETE fix only:
1) exact HAT originX/originY
2) exact scale formula or scaleMul
3) exact brimLift (or offsetY)
4) any face visibleY / facePx changes
5) whether to regen/crop the hat art

No essays — numbers I can paste into config.ts."""

user32 = ctypes.windll.user32


def find_hwnd(substr: str):
    found = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def foreach(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if substr in buf.value:
                    found.append((hwnd, buf.value))
        return True

    user32.EnumWindows(EnumWindowsProc(foreach), 0)
    return found


def focus(hwnd):
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
    time.sleep(0.5)


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


def main():
    hits = find_hwnd("ChatGPT")
    if not hits:
        # launch
        candidates = list(Path(r"C:\Users\user\AppData\Local\Programs").glob("ChatGPT*/ChatGPT.exe"))
        if not candidates:
            raise SystemExit("ChatGPT Desktop not found")
        subprocess.Popen([str(candidates[0])])
        time.sleep(5)
        hits = find_hwnd("ChatGPT")
    hwnd, title = hits[0]
    print("focus", title)
    focus(hwnd)
    time.sleep(0.8)

    # New chat if possible (ctrl+n common)
    pyautogui.hotkey("ctrl", "n")
    time.sleep(1.2)

    # Paste image
    set_clip_image(POSE)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(2.0)

    # Also try attaching crop proofs
    for name in ["_comp_1.png", "_comp_4.png"]:
        p = ROOT / name
        if p.exists():
            set_clip_image(p)
            time.sleep(0.2)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(1.5)

    set_clip_text(PROMPT)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.4)
    pyautogui.press("enter")
    print("prompt sent — waiting for reply")
    time.sleep(45)
    ImageGrab.grab().save(ROOT / "_chatgpt_reply.png")
    print("saved _chatgpt_reply.png")


if __name__ == "__main__":
    main()
