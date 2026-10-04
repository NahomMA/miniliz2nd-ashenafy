"""Generate the app icon, Android adaptive icon layers, splash image and the mascot.

Usage (from front-end/):  uv run --with pillow python scripts/make-assets.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

IMAGES = Path(__file__).resolve().parents[1] / "assets" / "images"
MAROON, MAROON_DARK, GOLD, WHITE = "#7A1F3D", "#5C1630", "#C8963E", "#FFFFFF"
ROSE, FACE = "#E3B4C2", "#3B1020"
SIZE, SCALE = 1024, 4  # drawn at 4x and reduced, for smooth edges


def mark(scale: float, ring_base: str, ring: str, heart: str) -> Image.Image:
    """The LifeSize mark: a progress ring (the goal) around a heart (the family), on a transparent canvas."""
    side = SIZE * SCALE
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    centre, radius, width = side / 2, 330 * SCALE * scale, 84 * SCALE * scale
    box = [centre - radius, centre - radius, centre + radius, centre + radius]
    draw.arc(box, 0, 360, fill=ring_base, width=round(width))
    draw.arc(box, -90, 180, fill=ring, width=round(width))
    for angle_point in ((centre, centre - radius + width / 2), (centre - radius + width / 2, centre)):
        x, y = angle_point
        draw.ellipse([x - width / 2, y - width / 2, x + width / 2, y + width / 2], fill=ring)

    lobe = 78 * SCALE * scale
    top = centre - lobe * 0.55
    for x in (centre - lobe * 0.92, centre + lobe * 0.92):
        draw.ellipse([x - lobe, top - lobe, x + lobe, top + lobe], fill=heart)
    draw.polygon(
        [(centre - lobe * 1.80, top + lobe * 0.30), (centre, top - lobe * 0.2), (centre + lobe * 1.80, top + lobe * 0.30), (centre, top + lobe * 2.5)],
        fill=heart,
    )
    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def on_background(layer: Image.Image, colour: str) -> Image.Image:
    background = Image.new("RGBA", layer.size, colour)
    background.alpha_composite(layer)
    return background.convert("RGB")


def mascot() -> Image.Image:
    """Liv, the guide: an original robot drawn in the app's palette (no third-party artwork)."""
    side, unit = 512 * SCALE, 512 * SCALE / 100
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    box = lambda x0, y0, x1, y1: [x0 * unit, y0 * unit, x1 * unit, y1 * unit]

    draw.line([50 * unit, 20 * unit, 50 * unit, 9 * unit], fill=MAROON_DARK, width=round(2.4 * unit))
    draw.ellipse(box(45, 4, 55, 14), fill=GOLD)
    draw.rounded_rectangle(box(12, 36, 22, 54), radius=4 * unit, fill=ROSE)
    draw.rounded_rectangle(box(78, 36, 88, 54), radius=4 * unit, fill=ROSE)
    draw.rounded_rectangle(box(19, 19, 81, 68), radius=17 * unit, fill=MAROON)
    draw.rounded_rectangle(box(27, 28, 73, 60), radius=11 * unit, fill=FACE)
    draw.ellipse(box(35, 36, 44, 47), fill=GOLD)
    draw.ellipse(box(56, 36, 65, 47), fill=GOLD)
    draw.arc(box(42, 43, 58, 55), 20, 160, fill=GOLD, width=round(1.8 * unit))
    draw.rounded_rectangle(box(31, 72, 69, 97), radius=10 * unit, fill=MAROON)
    for x in (45.4, 54.6):
        draw.ellipse(box(x - 5, 78, x + 5, 88), fill=WHITE)
    draw.polygon([(41 * unit, 84.5 * unit), (50 * unit, 82 * unit), (59 * unit, 84.5 * unit), (50 * unit, 94 * unit)], fill=WHITE)
    return canvas.resize((512, 512), Image.LANCZOS)


def main() -> None:
    on_background(mark(1.0, MAROON_DARK, GOLD, WHITE), MAROON).save(IMAGES / "icon.png")
    mark(0.62, MAROON_DARK, GOLD, WHITE).save(IMAGES / "android-icon-foreground.png")
    mark(0.62, WHITE, WHITE, WHITE).save(IMAGES / "android-icon-monochrome.png")
    mark(0.8, MAROON_DARK, GOLD, WHITE).save(IMAGES / "splash-icon.png")
    on_background(mark(1.0, MAROON_DARK, GOLD, WHITE), MAROON).resize((48, 48), Image.LANCZOS).save(IMAGES / "favicon.png")
    mascot().save(IMAGES / "liv.png")
    print("assets written to", IMAGES)


if __name__ == "__main__":
    main()
