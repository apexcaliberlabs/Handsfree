import os
from pathlib import Path
from PIL import Image, ImageDraw


def generate_handsfree_icon(save_dir: str) -> str:
    """Generates a high-tech glowing cyan hand & orb icon for Handsfree."""
    os.makedirs(save_dir, exist_ok=True)
    ico_path = os.path.join(save_dir, "handsfree.ico")
    png_path = os.path.join(save_dir, "handsfree.png")

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Dark circular backing with subtle gradient
    draw.ellipse([8, 8, size - 8, size - 8], fill=(16, 20, 32, 255), outline=(0, 229, 255, 200), width=4)

    # 2. Outer glowing cyan ring
    draw.ellipse([20, 20, size - 20, size - 20], outline=(0, 229, 255, 120), width=3)

    # 3. Glowing central energy dot / virtual cursor orb
    cx, cy = size // 2, size // 2 - 10
    for r in range(40, 10, -5):
        alpha = int(120 - r * 2.5)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 229, 255, max(10, alpha)), width=3)

    draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(0, 255, 200, 255), outline=(255, 255, 255, 255), width=2)
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(255, 255, 255, 255))

    # 4. Stylized hand silhouette lines beneath the orb
    wrist_y = size - 42
    # Palm arch
    draw.arc([cx - 48, cy + 15, cx + 48, wrist_y], start=0, end=180, fill=(0, 229, 255, 230), width=5)
    # Pointing index finger ray towards orb
    draw.line([cx, cy + 18, cx, cy + 55], fill=(0, 229, 255, 255), width=6)
    # Thumb arc
    draw.line([cx - 24, cy + 32, cx - 42, cy + 45], fill=(0, 229, 255, 220), width=5)
    # Middle finger ray
    draw.line([cx + 18, cy + 24, cx + 22, cy + 55], fill=(0, 229, 255, 200), width=5)

    img.save(png_path, format="PNG")
    img.save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    )
    return ico_path


if __name__ == "__main__":
    out_dir = str(Path(__file__).resolve().parent)
    generate_handsfree_icon(out_dir)
    print("Icons generated successfully!")
