#!/usr/bin/env python3
"""make_assets.py — mrbeast_empire-episodens GFX-fabrik (PIL).

Bygger allt visuellt bevismaterial till assets/gfx/ med STUDIOFONTER via gfx_kit.F()
(Anton / Archivo Black / Bebas — aldrig DejaVu som identitetsfont, MANDATE #3).

Kör: python3 scripts/make_assets.py   (stå i episodroten)
"""
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import os, sys, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx_kit import F, glow_title, lower_third, tweet_ui, stat_card, hud_frame, light_leak

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "src")
GFX = os.path.join(ROOT, "assets", "gfx")
os.makedirs(GFX, exist_ok=True)

WHITE = (255, 255, 255, 255)
RED = (232, 34, 46, 255)
GREY = (200, 200, 205, 255)
BLUE = (0, 160, 255, 255)

def _tsize(draw, text, font, stroke=0):
    bb = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    return bb[2] - bb[0], bb[3] - bb[1]

# ---------------- cirkelporträtt (studio-ring) ----------------
def circle_portrait(src_path, out_name, ring=(255, 255, 255, 255), size=1000):
    img = ImageOps.exif_transpose(Image.open(src_path).convert("RGB"))
    w, h = img.size
    s = min(w, h)
    left = int((w - s) * 0.62) if w > h else (w - s) // 2   # porträttet är högerförskjutet
    left = max(0, min(left, w - s))
    top = int((h - s) * 0.02) if h > w else 0
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

# ---------------- textkort med studiofonter ----------------
def text_card(out_name, lines, pad=60):
    """lines: [(text, px, färg, stroke, fontkey)] — fontkey: anton/archivo/bebas"""
    metrics, W, H = [], 0, 0
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    for text, px, color, stroke, fk in lines:
        w, h = _tsize(tmp, text, F(px, fk), stroke)
        metrics.append([text, px, color, stroke, fk, w, h])
        W = max(W, w); H += h + int(px * 0.34)
    canvas = Image.new("RGBA", (W + pad * 2, H + pad * 2), (0, 0, 0, 0))
    y = pad
    for text, px, color, stroke, fk, w, h in metrics:
        x = (canvas.width - w) // 2
        f = F(px, fk)
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y + 6), text, font=f, fill=(0, 0, 0, 220),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 220))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        canvas = Image.alpha_composite(canvas, sh)
        ImageDraw.Draw(canvas).text((x, y), text, font=f, fill=color,
                                    stroke_width=stroke, stroke_fill=(10, 10, 10, 255))
        y += h + int(px * 0.34)
    canvas.save(os.path.join(GFX, out_name))
    print("card:", out_name)

# ---------------- foto-kort (riktiga bilder, rundad ram) ----------------
def photo_card(src_path, out_name, w=1400, h=900, radius=28, border=RED, bw=10):
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
    ImageDraw.Draw(canvas).rounded_rectangle([pad, pad, pad + w, pad + h],
                                             radius, outline=border, width=bw)
    canvas.save(os.path.join(GFX, out_name))
    print("photo card:", out_name)

# ---------------- headline/press-kort (social-UI-bevis, EXCERPT-märkt) ----------------
def headline_card(out_name, outlet, datestr, body, W=980):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fon, fd, fb, fm = F(50, "archivo"), F(36, "bebas"), F(52, "anton"), F(34, "bebas")
    words, lines, cur = body.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if _tsize(d0, t, fb)[0] > W - 120:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    H = 46 + 58 + 20 + len(lines) * 66 + 26 + 40 + 46
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(card)
    dr.rounded_rectangle([0, 0, W - 1, H - 1], 24, fill=(16, 18, 22, 244),
                         outline=(232, 34, 46, 255), width=3)
    # outlet-tab + EXCERPT-markering (ärligt källmaterial, ingen fejkad screenshot)
    dr.rounded_rectangle([26, 26, 26 + _tsize(dr, outlet, fon)[0] + 36, 26 + 62], 10,
                         fill=(232, 34, 46, 255))
    dr.text((44, 34), outlet, font=fon, fill=(255, 255, 255, 255))
    ow = _tsize(dr, outlet, fon)[0]
    dr.text((44 + ow + 52, 42), "EXCERPT", font=fd, fill=(150, 154, 162, 235))
    dr.text((W - 60 - _tsize(dr, datestr, fd)[0], 42), datestr, font=fd,
            fill=(150, 154, 162, 235))
    y = 46 + 62 + 14
    for ln in lines:
        dr.text((44, y), ln, font=fb, fill=(240, 242, 245, 255))
        y += 66
    dr.text((44, y + 10), meta_label := "KÄLLA: SE EPISODENS KÄLLREGISTER", font=fm,
            fill=(110, 116, 126, 235))
    card.save(os.path.join(GFX, out_name))
    print("headline:", out_name, f"{W}x{H}")

# ---------------- partiklar + vinjett ----------------
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
    # porträtt + fotokort (riktiga bilder i assets/src/)
    mb = sorted(glob.glob(os.path.join(SRC, "mrbeast.jpg")))
    bl = sorted(glob.glob(os.path.join(SRC, "beastland.jpg")))
    fe = sorted(glob.glob(os.path.join(SRC, "feastables.jpg")))
    if mb: circle_portrait(mb[0], "beast_circle.png", WHITE)
    if bl: photo_card(bl[0], "pc_beastland.png", border=(150, 60, 255, 255))
    if fe: photo_card(fe[0], "pc_feast.png", border=(255, 196, 0, 255))

    # glow-titlar (Anton + neon)
    glow_title("glow_mrbeast.png", "MRBEAST", 210, glow=(232, 34, 46, 150))
    glow_title("glow_500m.png", "500,000,000", 170, glow=(120, 220, 255, 140))
    glow_title("glow_games.png", "BEAST GAMES", 130, glow=(150, 60, 255, 150))
    glow_title("glow_subscribe.png", "SUBSCRIBE", 165, glow=(60, 220, 120, 140))

    # lower thirds
    lower_third("lt_jimmy.png", "JIMMY DONALDSON",
                "AKA MRBEAST · GREENVILLE, NC · BIGGEST CHANNEL ON EARTH")
    lower_third("lt_housenbold.png", "JEFF HOUSENBOLD",
                "CEO · BEAST INDUSTRIES · SINCE 2024", accent=BLUE)

    # stat-kort (data-viz slams)
    stat_card("stat_500m.png", "500M+", "SUBSCRIBERS · FIRST PERSON EVER")
    stat_card("stat_52b.png", "$5.2B", "BEAST INDUSTRIES VALUATION")
    stat_card("stat_300m.png", "$300M", "EARNED 2026 · FORBES #1 CREATOR")

    # textkort per beat
    text_card("title_2017.png", [("JANUARY 2017", 120, WHITE, 10, "anton"),
                                 ("AFTER A THOUSAND FAILED UPLOADS", 44, GREY, 5, "bebas")])
    text_card("card_count.png", [("I COUNTED TO 100,000", 96, WHITE, 9, "anton"),
                                 ("40 HOURS · ONE WEBCAM · NO CUTS", 42, GREY, 5, "bebas")])
    text_card("card_buried.png", [("BURIED ALIVE · 50 HOURS", 84, RED, 9, "anton")])
    text_card("card_squid.png", [("$456,000 SQUID GAME", 92, WHITE, 9, "anton"),
                                 ("IN REAL LIFE · NOV 2021", 42, GREY, 5, "bebas")])
    text_card("card_feast.png", [("FEASTABLES", 120, WHITE, 10, "anton"),
                                 ("CHOCOLATE · IN STORES WORLDWIDE", 42, GREY, 5, "bebas")])
    text_card("card_games.png", [("BEAST CITY", 110, WHITE, 9, "anton"),
                                 ("PRIVATE COMPOUND · $10M GRAND PRIZE", 42, GREY, 5, "bebas")])
    text_card("card_lawsuit.png", [("CLASS ACTION", 116, RED, 10, "anton"),
                                   ("FILED · L.A. SUPERIOR COURT · SEPT 2024", 40, GREY, 5, "bebas")])
    text_card("card_ceo.png", [("NEW CEO", 116, WHITE, 10, "anton"),
                               ("FROM YOUTUBE CHANNEL TO COMPANY", 40, GREY, 5, "bebas")])
    text_card("card_s2.png", [("SEASON 2", 130, WHITE, 10, "anton"),
                              ("JAN 7 2026 · STRONG vs SMART · $5M PRIZE", 40, GREY, 5, "bebas")])
    text_card("card_campus.png", [("132-ACRE CAMPUS", 100, WHITE, 9, "anton"),
                                  ("GREENVILLE, NC · ~750 EMPLOYEES", 40, GREY, 5, "bebas")])
    text_card("card_end.png", [("STILL COUNTING.", 120, WHITE, 10, "anton"),
                               ("...AND NOWHERE NEAR DONE", 44, RED, 6, "bebas")])

    # extra beat-kort (scenplanen)
    text_card("card_oneguy.png", [("ONE GUY.", 130, WHITE, 10, "anton"),
                                  ("FROM A SMALL TOWN IN NORTH CAROLINA", 42, GREY, 5, "bebas")])
    text_card("card_broke.png", [('"I\'M BORROWING MONEY."', 84, RED, 9, "anton"),
                                 ("MRBEAST, ON HIS OWN BANK ACCOUNT", 40, GREY, 5, "bebas")])
    text_card("card_2012.png", [("2012", 150, WHITE, 10, "anton"),
                                ("THIRTEEN YEARS OLD · UPLOADS NOBODY WATCHED", 40, GREY, 5, "bebas")])
    text_card("card_algo.png", [("THE ALGORITHM", 110, WHITE, 9, "anton"),
                                ("STUDIED EVERY SINGLE DAY · 5 YEARS", 40, GREY, 5, "bebas")])
    text_card("card_money.png", [("HE HANDED STRANGERS MONEY", 80, WHITE, 9, "anton"),
                                 ("COST MORE → MADE MORE", 46, RED, 6, "bebas")])
    text_card("card_formula.png", [("THE FORMULA", 116, WHITE, 10, "anton"),
                                   ("ABSURD · COMMITMENT · BIGGER STAKES", 40, GREY, 5, "bebas")])
    text_card("card_turned.png", [("THE HEADLINES TURNED", 96, RED, 9, "anton")])
    text_card("card_survive.png", [("WOULD IT ALL SURVIVE?", 92, WHITE, 9, "anton")])

    # social-UI-bevis / headlines (EXCERPT-märkta, verkliga källor)
    headline_card("hl_variety.png", "VARIETY", "SEPT 2024",
                  "MrBeast, Amazon sued by Beast Games contestants, allegations include "
                  "chronic mistreatment and unpaid wages")
    headline_card("hl_bi.png", "BUSINESS INSIDER", "MAY 2026",
                  "MrBeast's new goal: turning his 476 million subscribers into paying members")

    particles(); vignette(); hud_frame("hud.png"); light_leak("lightleak.png")
    print("GFX-FABRIK KLAR ->", GFX)
