"""Render the square OracleGuard Portal logo to a 1024 px PNG.

The matching vector source is web/public/oracleguard-logo.svg.
Requires Pillow only when regenerating this optional submission asset.
"""

from pathlib import Path
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "public" / "oracleguard-logo.png"
SCALE = 4


def point(x: float, y: float) -> tuple[int, int]:
    return round(x * SCALE), round(y * SCALE)


def bezier(start, control_a, control_b, end, steps=36):
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        yield (
            u**3 * start[0] + 3 * u**2 * t * control_a[0] + 3 * u * t**2 * control_b[0] + t**3 * end[0],
            u**3 * start[1] + 3 * u**2 * t * control_a[1] + 3 * u * t**2 * control_b[1] + t**3 * end[1],
        )


def main() -> None:
    canvas = Image.new("RGBA", (1024 * SCALE, 1024 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((point(0, 0), point(1024, 1024)), radius=176 * SCALE, fill="#101611")
    draw.rounded_rectangle((point(168, 168), point(856, 856)), radius=152 * SCALE, fill="#d4ef79")

    shield = [(512, 294), (688, 360), (688, 512)]
    shield.extend(bezier((688, 512), (688, 636), (611, 718), (512, 764)))
    shield.extend(bezier((512, 764), (413, 718), (336, 636), (336, 512)))
    shield.extend([(336, 360), (512, 294)])
    draw.line([point(*xy) for xy in shield], fill="#172015", width=44 * SCALE, joint="curve")
    for x, y in ((512, 294), (512, 764)):
        radius = 22 * SCALE
        px, py = point(x, y)
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill="#172015")

    pulse = [(398, 521), (460, 521), (494, 458), (538, 585), (575, 521), (625, 521)]
    draw.line([point(*xy) for xy in pulse], fill="#172015", width=34 * SCALE, joint="curve")
    for x, y in (pulse[0], pulse[-1]):
        radius = 17 * SCALE
        px, py = point(x, y)
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill="#172015")

    canvas.resize((1024, 1024), Image.Resampling.LANCZOS).save(OUTPUT, optimize=True)
    print(f"{OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
