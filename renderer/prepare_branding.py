#!/usr/bin/env python3
"""Convert supplied checkerboard JPG call-to-action artwork into transparent PNG overlays."""
from collections import Counter
from pathlib import Path
from PIL import Image

ROOT = Path("branding")

def checker_colors(image):
    counts = Counter()
    pixels = image.convert("RGB")
    width, height = pixels.size
    for y in range(0, height, 3):
        for x in range(0, width, 3):
            red, green, blue = pixels.getpixel((x, y))
            saturation = max(red, green, blue) - min(red, green, blue)
            brightness = (red + green + blue) / 3
            if saturation <= 18 and 16 <= brightness <= 100:
                counts[round(brightness / 4) * 4] += 1
    values = [value for value, _ in counts.most_common(2)]
    if len(values) < 2:
        raise RuntimeError("Could not identify both checkerboard background shades.")
    return [(value, value, value) for value in values]

def remove_checkerboard(source, destination):
    image = Image.open(source).convert("RGBA")
    backgrounds = checker_colors(image)
    output = []
    for red, green, blue, _ in image.getdata():
        saturation = max(red, green, blue) - min(red, green, blue)
        brightness = (red + green + blue) / 3
        distance = min(max(abs(red - bg[0]), abs(green - bg[1]), abs(blue - bg[2])) for bg in backgrounds)
        alpha = 255
        if 16 <= brightness <= 100 and saturation <= 24:
            if distance <= 18:
                alpha = 0
            elif distance < 34:
                alpha = round((distance - 18) / 16 * 255)
        output.append((red, green, blue, alpha))
    image.putdata(output)
    image.save(destination, "PNG", optimize=True)
    return image.size, backgrounds

def main():
    assets = [
        (ROOT / "image_2d2a6dba.jpg", ROOT / "subscribe.png"),
        (ROOT / "image_c69a04ba.jpg", ROOT / "notification.png"),
    ]
    for source, destination in assets:
        if not source.is_file():
            raise SystemExit(f"Required channel artwork is missing: {source}")
        size, colors = remove_checkerboard(source, destination)
        print(f"BRANDING_READY {destination} size={size} removed_backgrounds={colors}")

if __name__ == "__main__":
    main()
