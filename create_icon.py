"""
Generate syscleaner.ico — Tech Bytes Design brand icon for SysCleaner.
Run: python create_icon.py
Requires: pip install pillow
"""
from __future__ import annotations
import math
from pathlib import Path


def _draw_icon(size: int):
    from PIL import Image, ImageDraw

    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background: rounded square ────────────────────────────────────────────
    pad = max(1, size // 12)
    r   = max(2, size // 6)
    draw.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=r,
        fill=(13, 17, 23, 255),      # #0D1117 — deep dark
    )

    # ── Outer cyan ring ────────────────────────────────────────────────────────
    cx = cy = size / 2
    ring_r  = size * 0.36
    lw      = max(2, size // 20)
    draw.ellipse(
        [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
        outline=(0, 180, 216, 255),  # #00B4D8 — cyan
        width=lw,
    )

    # ── Shield body ────────────────────────────────────────────────────────────
    sw = size * 0.22   # half-width
    sh = size * 0.28   # half-height
    # Shield polygon: top-left, top-right, mid-right, bottom-tip, mid-left
    shield = [
        (cx - sw,      cy - sh),
        (cx + sw,      cy - sh),
        (cx + sw,      cy + sh * 0.3),
        (cx,           cy + sh),
        (cx - sw,      cy + sh * 0.3),
    ]
    draw.polygon(shield, fill=(0, 180, 216, 255))

    # ── Check-mark ─────────────────────────────────────────────────────────────
    cs = size * 0.11
    ck_pts = [
        (cx - cs,        cy + cs * 0.1),
        (cx - cs * 0.2,  cy + cs * 0.85),
        (cx + cs,        cy - cs * 0.55),
    ]
    ck_w = max(2, size // 16)
    draw.line(ck_pts, fill=(13, 17, 23, 255), width=ck_w)

    # ── Small cyan dot (bottom-right accent) ─────────────────────────────────
    dot_r = max(2, size // 14)
    dot_x = cx + ring_r * 0.68
    dot_y = cy + ring_r * 0.68
    draw.ellipse(
        [dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r],
        fill=(0, 180, 216, 220),
    )

    return img


def main() -> None:
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "pillow", "-q"], check=True)

    sizes  = [256, 128, 64, 48, 32, 16]
    frames = [_draw_icon(s) for s in sizes]

    out = Path(__file__).parent / "syscleaner.ico"
    frames[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"Icon saved -> {out}")


if __name__ == "__main__":
    main()
