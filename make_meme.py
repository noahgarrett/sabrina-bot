
from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
from pathlib import Path

def load_font(size: int):
    """Try a couple of common bold fonts, fall back to PIL's default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            print("Warning: could not load font at", p)
            continue
    return ImageFont.load_default(size=size)

def fit_image(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Letterbox-fit `img` into (box_w, box_h) without distortion."""
    img_ratio = img.width / img.height
    box_ratio = box_w / box_h
    if img_ratio > box_ratio:
        # too wide -> fit by width
        new_w = box_w
        new_h = int(box_w / img_ratio)
    else:
        new_h = box_h
        new_w = int(box_h * img_ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (box_w, box_h), (240, 240, 240))
    x = (box_w - new_w) // 2
    y = (box_h - new_h) // 2
    canvas.paste(resized, (x, y))
    return canvas

def draw_justified_text(draw: ImageDraw.ImageDraw, box, text, font, fill=(255,255,255), line_spacing=6):
    """Draw multi-line centered text inside `box` with word wrap."""
    x0, y0, x1, y1 = box
    max_width = x1 - x0
    # heuristic to find a decent wrap width based on font metrics
    avg_char_w = sum(font.getlength(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ ") / 27
    est_chars_per_line = max(1, int(max_width / max(1, avg_char_w)))
    lines = []
    for para in text.splitlines():
        lines.extend(textwrap.wrap(para, width=est_chars_per_line))
        if para.strip() == "":
            lines.append("")

    # Compute total height
    lh = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    total_h = len(lines) * lh + (len(lines)-1) * line_spacing
    y = y0 + (y1 - y0 - total_h)//2
    for line in lines:
        w = font.getlength(line)
        draw.text((x0 + (max_width - w)//2, y), line, font=font, fill=fill)
        y += lh + line_spacing

def make_meme(user_png_bytes: bytes, meme_text: str, out_path: str,
              canvas_w: int = 750, canvas_h: int = 923, font_size: int = 36):
    """
    Build a meme that mimics the layout:
    - Fixed Sabrina image on top-left
    - User-provided PNG on top-right
    - Bold white text in a dark panel at the bottom
    
    Parameters
    ----------
    user_png_path : str
        Path to the PNG to place in the top-right.
    meme_text : str
        The text shown in the bottom panel. Use any case; it will be uppercased.
    out_path : str
        Output PNG path.
    canvas_w, canvas_h : int
        Final image size. Defaults mirror the sample proportions.
    """
    # Layout constants (tuned by eye to resemble the reference)
    margin = 12
    gutter = 8
    top_h = int(canvas_h * 0.56)  # height of the top split row
    panel_h = canvas_h - top_h     # text panel height
    col_w = (canvas_w - (2*margin) - gutter) // 2

    # Background (light gray like the borders in the example)
    bg = Image.new("RGB", (canvas_w, canvas_h), (220, 220, 220))

    # Load images
    sabrina_path = "sabrina.png"
    sabrina = Image.open(sabrina_path).convert("RGB")
    right = Image.open(user_png_bytes).convert("RGBA")

    # Prepare top-left (fit/letterbox)
    left_box = (margin, margin, margin + col_w, margin + top_h)
    left_fit = fit_image(sabrina, col_w, top_h)
    bg.paste(left_fit, (left_box[0], left_box[1]))

    # Prepare top-right (fit with light outline sticker effect if PNG has alpha)
    right_box = (margin + col_w + gutter, margin, margin + col_w + gutter + col_w, margin + top_h)
    right_fit = fit_image(right.convert("RGB"), col_w, top_h)

    # Optional: if the provided image has transparency, create a white stroke
    if right.mode == "RGBA" and right.getchannel("A").getextrema()[1] < 255:
        # Sticker effect: put a white rounded border shadow around the resized image
        # For simplicity, create a 1px white frame.
        right_fit = ImageOps.expand(right_fit, border=2, fill="white")
        # Trim back to the box size if needed
        right_fit = right_fit.crop((0, 0, col_w, top_h))
    bg.paste(right_fit, (right_box[0], right_box[1]))

    # Bottom dark panel
    panel = Image.new("RGB", (canvas_w, panel_h), (29, 29, 31))
    bg.paste(panel, (0, top_h))

    # Text
    draw = ImageDraw.Draw(bg)
    text_pad = 20
    # Bigger font for compact canvases; adjust to width
    font = load_font(font_size)
    text_box = (text_pad, top_h + text_pad, canvas_w - text_pad, canvas_h - text_pad)
    draw_justified_text(draw, text_box, meme_text.upper(), font, fill=(255,255,255))

    # Save
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    bg.save(out_path, "PNG")

    return bg

if __name__ == "__main__":
    # Example usage:
    # Change these values or import the function elsewhere.
    user_png = "user_image.png"
    text = "SABRINA CARPENTER DOES NOT KNOW HOW TO PRESS E"
    out = "generated_meme.png"
    try:
        make_meme(user_png, text, out, font_size=48)
        print(f"Saved meme to: {out}")
    except FileNotFoundError as e:
        print("Example failed because the example_user_image.png was not found. "
              "Call make_meme() with your image path and text.")
