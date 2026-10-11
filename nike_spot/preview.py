"""Hoja de contactos de fotogramas concretos (revisión rápida)."""
import sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw
import render


def one(args):
    fi, s = args
    return fi, render.render_frame(fi, samples=s)


if __name__ == "__main__":
    out = sys.argv[1]
    frames = [int(x) for x in sys.argv[2].split(",")]
    samples = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    cols = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    tw, th = 270, 480
    with Pool(4) as p:
        res = dict(p.map(one, [(f, samples) for f in frames]))
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 20)), (60, 60, 60))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(frames):
        im = Image.fromarray(res[f]).resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + 20)
        sheet.paste(im, (x, y + 20))
        d.text((x + 4, y + 4), f"f{f}  {f/60:.2f}s", fill=(255, 255, 0))
    sheet.save(out)
