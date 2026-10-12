"""Convert a photograph into the persistent character grid used by the header."""

import argparse
from pathlib import Path

from PIL import Image, ImageOps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo", type=Path)
    parser.add_argument("--crop", nargs=4, type=int, default=None,
                        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    args = parser.parse_args()
    image = ImageOps.exif_transpose(Image.open(args.photo))
    if args.crop:
        image = image.crop(tuple(args.crop))
    columns = 96
    rows = round(columns * 3.9 / 6.7 * image.height / image.width)
    gray = ImageOps.autocontrast(ImageOps.grayscale(image), cutoff=1)
    gray = gray.resize((columns, rows), Image.Resampling.LANCZOS)
    ramp = " .,:;irsXA253hMHGS#9B&@"
    lines = []
    for y in range(rows):
        line = ""
        for x in range(columns):
            darkness = (1 - gray.getpixel((x, y)) / 255) ** 1.25
            line += ramp[round(darkness * (len(ramp) - 1))]
        lines.append(line)
    destination = Path(__file__).resolve().parents[1] / "assets" / "portrait.txt"
    destination.write_text("\n".join(lines) + "\n")
    print(f"Created {columns} x {rows} character portrait.")


if __name__ == "__main__":
    main()
