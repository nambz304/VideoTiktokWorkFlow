"""
Crop 10 Milo poses from single sprite sheet → individual PNGs
Grid: 2 rows x 5 cols
"""
from PIL import Image
import os

SRC = "/Users/catcomputer/.claude/image-cache/bc5a2cda-e041-4036-811a-e9e16461bb50/1.png"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Map position (row, col) → filename
POSES = {
    (0, 0): "milo_wave.png",
    (0, 1): "milo_think.png",
    (0, 2): "milo_point.png",
    (0, 3): "milo_happy.png",
    (0, 4): "milo_sleep.png",
    (1, 0): "milo_eat.png",
    (1, 1): "milo_exercise.png",
    (1, 2): "milo_hold_product.png",
    (1, 3): "milo_cta.png",
    (1, 4): "milo_surprise.png",
}

img = Image.open(SRC).convert("RGBA")
W, H = img.size  # 1402 x 1122
cols, rows = 5, 2
cell_w = W // cols  # 280
cell_h = H // rows  # 561

for (row, col), filename in POSES.items():
    x0 = col * cell_w
    y0 = row * cell_h
    x1 = x0 + cell_w
    y1 = y0 + cell_h
    cropped = img.crop((x0, y0, x1, y1))
    out_path = os.path.join(OUT_DIR, filename)
    cropped.save(out_path, "PNG")
    print(f"✓ {filename}  ({x0},{y0}) → ({x1},{y1})")

print(f"\nDone. {len(POSES)} files saved to {OUT_DIR}")
