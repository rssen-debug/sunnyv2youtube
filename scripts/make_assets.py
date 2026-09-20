#!/usr/bin/env python3
"""sunnyv2-style asset factory (PIL).
Bygger: cirkelporträtt, titelkort, partiklar, vinjett -> drake-video/assets/gfx/
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "src")
GFX = os.path.join(ROOT, "assets", "gfx")
os.makedirs(GFX, exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(px): return ImageFont.truetype(FONT, px)

def circle_portrait(src_path, out_name, ring=(255, 255, 255, 255), size=1000):
    img = ImageOps.exif_transpose(Image.open(src_path).convert("RGB"))
    w, h = img.size
    s = min(w, h)
    left = (w - s) // 2
    top = int((h - s) * 0.05) if h > w else 0
    img = img.crop((left, top, left + s, top + s)).resize((size, size), Image.LANCZOS)
    pad = 60
    canvas = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([pad + 10, pad + 26, pad + size + 10, pad + size + 26],
                               fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    canvas = Image.alpha_composite(canvas, sh)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    canvas.paste(img, (pad, pad), mask)
    d = ImageDraw.Draw(canvas)
    bw = 22
    d.ellipse([pad - bw // 2, pad - bw // 2, pad + size + bw // 2, pad + size + bw // 2],
              outline=ring, width=bw)
    canvas.save(os.path.join(GFX, out_name))
    print("portrait:", out_name)

def text_card(out_name, lines, pad=60):
    metrics = []
    W = H = 0
    for text, px, color, stroke in lines:
        bb = ImageDraw.Draw(Image.new("RGBA", (10, 10))).textbbox(
            (0, 0), text, font=font(px), stroke_width=stroke)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        metrics.append([text, px, color, stroke, w, h])
        W = max(W, w); H += h + int(px * 0.28)
    canvas = Image.new("RGBA", (W + pad * 2, H + pad * 2), (0, 0, 0, 0))
    y = pad
    for text, px, color, stroke, w, h in metrics:
        x = (canvas.width - w) // 2
        f = font(px)
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y + 6), text, font=f, fill=(0, 0, 0, 220),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 220))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        canvas = Image.alpha_composite(canvas, sh)
        ImageDraw.Draw(canvas).text((x, y), text, font=f, fill=color,
                                    stroke_width=stroke, stroke_fill=(10, 10, 10, 255))
        y += h + int(px * 0.28)
    canvas.save(os.path.join(GFX, out_name))
    print("card:", out_name)

def photo_card(src_path, out_name, w=1400, h=900, radius=28,
               border=(230, 30, 40, 255), bw=10):
    img = ImageOps.exif_transpose(Image.open(src_path).convert("RGB"))
    img = ImageOps.fit(img, (w, h), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=3, percent=90, threshold=2))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius, fill=255)
    pad = 60
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad + 8, pad + 24, pad + w + 8, pad + h + 24],
                                         radius, fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    canvas = Image.alpha_composite(canvas, sh)
    canvas.paste(img, (pad, pad), mask)
    ImageDraw.Draw(canvas).rounded_rectangle(
        [pad, pad, pad + w, pad + h], radius, outline=border, width=bw)
    canvas.save(os.path.join(GFX, out_name))
    print("photo card:", out_name)

def particles(out_name="particles.png", W=1280, H=760, n=120):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rnd = __import__("random").Random(42)
    lay1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(lay1)
    for _ in range(n):
        r = rnd.uniform(1.2, 4.5); a = rnd.randint(45, 160)
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        d1.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
    lay1 = lay1.filter(ImageFilter.GaussianBlur(1.2))
    lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(lay2)
    for _ in range(14):
        r = rnd.uniform(12, 34); a = rnd.randint(18, 40)
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        d2.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 235, a))
    lay2 = lay2.filter(ImageFilter.GaussianBlur(6))
    canvas = Image.alpha_composite(canvas, lay1)
    canvas = Image.alpha_composite(canvas, lay2)
    canvas.save(os.path.join(GFX, out_name))
    print("particles ok")

def vignette(out_name="vignette.png", W=1280, H=720):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(120))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    black.putalpha(ImageOps.invert(m))
    black.save(os.path.join(GFX, out_name))
    print("vignette ok")

if __name__ == "__main__":
    WHITE = (255, 255, 255, 255); RED = (232, 34, 46, 255); GREY = (200, 200, 205, 255)

    drake = sorted(glob.glob(os.path.join(SRC, "drake.jpg")))
    pink = sorted(glob.glob(os.path.join(SRC, "pinkchyu.jpg")))
    casa = sorted(glob.glob(os.path.join(SRC, "casa.jpg")))
    if drake: circle_portrait(drake[0], "drake_circle.png", WHITE)
    if pink:  circle_portrait(pink[0], "pink_circle.png", (200, 60, 220, 255))
    if casa:  photo_card(casa[0], "casa_card.png")

    text_card("title_drake.png", [("DRAKE", 150, WHITE, 10),
                                  ("ONE OF THE BIGGEST RAPPERS ALIVE", 44, GREY, 5)])
    text_card("title_vs.png", [("vs THE GOTH GIRL", 84, RED, 9)])
    text_card("title_pink.png", [("PINKCHYU", 150, WHITE, 10),
                                 ("AKA LIN LAMAR · THE GOTH BADDIE", 46, GREY, 5)])
    text_card("card_20v1.png", [("20 WOMEN vs DRAKE", 104, WHITE, 9),
                                ("KICK LIVESTREAM · AUG 8 2026 · BY NELK", 42, GREY, 5)])
    text_card("card_mtg.png", [("SHE PULLED OUT MAGIC: THE GATHERING CARDS", 54, WHITE, 7)])
    text_card("card_bark.png", [('"WOULD YOU BARK FOR ME?"', 92, WHITE, 9)])
    text_card("card_arf.png", [("ARF.  ARF.  ARF.", 130, RED, 10),
                               ("...AND A LITTLE WHIMPER", 44, GREY, 5)])
    text_card("card_nlu.png", [('THE INTERNET SYNCED IT TO "NOT LIKE US"', 56, WHITE, 7)])
    text_card("card_house.png", [("HER PRIZE? A HOUSE.", 92, WHITE, 9),
                                 ("...FOR HER MOM", 60, RED, 7)])
    text_card("card_casa.png", [("CASA LOMA · TORONTO", 68, WHITE, 8),
                                ("98-ROOM GOTHIC CASTLE · PRIVATE SUSHI DINNER", 38, GREY, 5)])
    text_card("card_leash.png", [("THE LEASH PHOTO", 96, WHITE, 9),
                                 ("1,000,000+ VIEWS IN DAYS · ALMOST CERTAINLY AI", 40, GREY, 5)])
    text_card("card_gothsplan.png", [('"GOTH\'S PLAN"', 110, RED, 10),
                                     ("THE MEME THAT EXPLAINED EVERYTHING", 42, GREY, 5)])
    text_card("card_dm.png", [("NOW CELEBS BARK IN HER DMS", 72, WHITE, 8),
                              ("A 'MASSIVE MUSICIAN' · SHE NEVER REPLIED · PER TMZ", 38, GREY, 5)])
    text_card("endcard.png", [("SUBSCRIBE", 150, WHITE, 10),
                              ("NEXT WEEK'S STORY IS EVEN STRANGER", 46, RED, 6)])
    particles(); vignette()
    print("KLART ->", GFX)
