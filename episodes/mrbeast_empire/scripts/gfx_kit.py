#!/usr/bin/env python3
"""GFX KIT v2 — "million dollar studio"-assets (Pillow).
Bygger: glow-titlar, lower thirds, tweet/UI-mockups, stat-kort, HUD, light leak.
FONTER: Anton / Archivo Black / Bebas Neue (assets/fonts) med DejaVu-fallback.

Användning: importera funktioner i din builder ELLER kör för Drake-POC-standardassets.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GFX = os.path.join(ROOT, "assets", "gfx")
FDIR = os.path.join(ROOT, "assets", "fonts")
os.makedirs(GFX, exist_ok=True)
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def F(px, which="anton"):
    p = {"anton": os.path.join(FDIR, "Anton-Regular.ttf"),
         "archivo": os.path.join(FDIR, "ArchivoBlack-Regular.ttf"),
         "bebas": os.path.join(FDIR, "BebasNeue-Regular.ttf"),
         "dejavu": DEJAVU}.get(which, DEJAVU)
    try:
        return ImageFont.truetype(p, px)
    except Exception:
        return ImageFont.truetype(DEJAVU, px)

def _tsize(draw, text, font, stroke=0):
    bb = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    return bb[2] - bb[0], bb[3] - bb[1]

# ---------------- GLOW TITEL (neon-dokumentär-look) ----------------
def glow_title(out, text, px=170, fill=(255, 255, 255, 255),
               glow=(232, 34, 46, 160), stroke=10, pad=140):
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    f = F(px, "anton")
    w, h = _tsize(tmp, text, f, stroke)
    W, H = w + pad * 2, h + px + pad
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = (W - w) // 2, pad // 2 + int(px * 0.18)
    # glow-lager: bred mjuk + tät
    for radius, alpha in [(34, glow[3]), (12, min(255, glow[3] + 60))]:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((x, y), text, font=f, fill=glow[:3] + (alpha,),
                                   stroke_width=stroke, stroke_fill=glow[:3] + (alpha,))
        layer = layer.filter(ImageFilter.GaussianBlur(radius))
        canvas = Image.alpha_composite(canvas, layer)
    d = ImageDraw.Draw(canvas)
    d.text((x, y), text, font=f, fill=fill, stroke_width=stroke,
           stroke_fill=(8, 8, 10, 255))
    canvas.save(os.path.join(GFX, out))
    print("glow_title:", out)

# ---------------- LOWER THIRD (namn/reveal-bar) ----------------
def lower_third(out, main, sub="", accent=(232, 34, 46, 255), W=1080):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fm, fs = F(72, "archivo"), F(40, "bebas")
    mw, mh = _tsize(d0, main, fm)
    sw, sh = (_tsize(d0, sub, fs) if sub else (0, 0))
    H = 36 + mh + (14 + sh if sub else 0) + 34
    card = Image.new("RGBA", (W, H + 20), (0, 0, 0, 0))
    dr = ImageDraw.Draw(card)
    dr.rounded_rectangle([26, 10, W - 6, H + 6], 14, fill=(12, 12, 14, 208))
    dr.rounded_rectangle([26, 10, 40, H + 6], 7, fill=accent)
    ox = 64
    dr.text((ox, 24), main, font=fm, fill=(255, 255, 255, 255))
    if sub:
        dr.text((ox, 24 + mh + 12), sub, font=fs, fill=(190, 190, 196, 235))
    card.save(os.path.join(GFX, out))
    print("lower_third:", out)

# ---------------- TWEET / SOCIAL UI MOCKUP ----------------
def _heart(dr, cx, cy, r, fill):
    dr.ellipse([cx - r, cy - r, cx, cy], fill=fill)
    dr.ellipse([cx, cy - r, cx + r, cy], fill=fill)
    dr.polygon([(cx - r, cy - r * 0.35), (cx + r, cy - r * 0.35), (cx, cy + r)], fill=fill)

def tweet_ui(out, name, handle, body, meta, likes, avatar_path, W=940):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fn, fh, fb, fm = F(44, "archivo"), F(36, "bebas"), F(46, "archivo"), F(34, "bebas")
    # radbryt body
    words, lines, cur = body.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if _tsize(d0, t, fb)[0] > W - 120:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    av = 92
    H = 40 + av + 26 + len(lines) * (58 + 8) + 30 + 46 + 34
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(card)
    dr.rounded_rectangle([0, 0, W - 1, H - 1], 26, fill=(21, 24, 28, 242),
                         outline=(70, 76, 84, 255), width=2)
    # avatar (cirkelbeskuren)
    if os.path.exists(avatar_path):
        a = ImageOps.fit(Image.open(avatar_path).convert("RGB"), (av, av), Image.LANCZOS)
        m = Image.new("L", (av, av), 0)
        ImageDraw.Draw(m).ellipse([0, 0, av, av], fill=255)
        card.paste(a, (40, 40), m)
    nx = 40 + av + 26
    dr.text((nx, 44), name, font=fn, fill=(255, 255, 255, 255))
    nw = _tsize(dr, name, fn)[0]
    dr.text((nx + nw + 16, 52), handle, font=fh, fill=(120, 128, 138, 255))
    y = 40 + av + 26
    for ln in lines:
        dr.text((40, y), ln, font=fb, fill=(232, 234, 238, 255))
        y += 58 + 8
    y += 12
    dr.text((40, y), meta, font=fm, fill=(110, 118, 128, 255))
    # hjärta + likes
    hy = y + 66
    _heart(dr, 56, hy, 16, (249, 24, 128, 255))
    dr.text((84, hy - 18), likes, font=fh, fill=(249, 24, 128, 255))
    card.save(os.path.join(GFX, out))
    print("tweet_ui:", out, f"{W}x{H}")

# ---------------- STAT-KORT (data-viz slam) ----------------
def stat_card(out, big, label, accent=(232, 34, 46, 255)):
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fb, fl = F(200, "anton"), F(46, "bebas")
    bw, bh = _tsize(d0, big, fb)
    lw, lh = _tsize(d0, label, fl)
    W = max(bw, lw) + 160
    H = 30 + bh + 18 + lh + 40
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(c)
    dr.rectangle([(W - min(bw, 420)) // 2, 18, (W + min(bw, 420)) // 2, 24], fill=accent)
    dr.text(((W - bw) // 2, 40), big, font=fb, fill=(255, 255, 255, 255),
            stroke_width=8, stroke_fill=(8, 8, 10, 255))
    dr.text(((W - lw) // 2, 40 + bh + 18), label, font=fl, fill=(205, 205, 212, 245))
    c.save(os.path.join(GFX, out))
    print("stat_card:", out)

# ---------------- HUD-ram (hörn + ticks, subtil) ----------------
def hud_frame(out, W=1280, H=720, alpha=70):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(c)
    L, m, col = 46, 26, (255, 255, 255, alpha)
    for (x, y, dx, dy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        dr.line([(x, y), (x + dx * L, y)], fill=col, width=3)
        dr.line([(x, y), (x, y + dy * L)], fill=col, width=3)
    for cx in (W // 2,):
        dr.line([(cx - 14, 24), (cx + 14, 24)], fill=col, width=2)
        dr.line([(cx - 14, H - 24), (cx + 14, H - 24)], fill=col, width=2)
    c.save(os.path.join(GFX, out))
    print("hud:", out)

# ---------------- LIGHT LEAK (varm ljusläcka, lägg överst) ----------------
def light_leak(out, W=1280, H=720):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    blob = Image.new("L", (W, H), 0)
    db = ImageDraw.Draw(blob)
    db.ellipse([-W * 0.25, H * 0.55, W * 0.45, H * 1.35], fill=46)
    db.ellipse([W * 0.72, -H * 0.25, W * 1.25, H * 0.35], fill=26)
    blob = blob.filter(ImageFilter.GaussianBlur(90))
    warm = Image.new("RGBA", (W, H), (255, 128, 60, 0))
    warm.putalpha(blob)
    c = Image.alpha_composite(c, warm)
    c.save(os.path.join(GFX, out))
    print("light_leak:", out)

if __name__ == "__main__":
    import glob
    SRC = os.path.join(ROOT, "assets", "src")
    # Drake-POC + fullvideo-assets
    glow_title("glow_drake.png", "DRAKE", 200, glow=(232, 34, 46, 150))
    glow_title("glow_bark.png", '"WOULD YOU BARK?"', 110, glow=(120, 220, 255, 140))
    glow_title("glow_subscribe.png", "SUBSCRIBE", 170, glow=(60, 220, 120, 140))
    glow_title("glow_gothsplan.png", "GOTH'S PLAN", 130, glow=(232, 34, 46, 160))
    lower_third("lt_drake.png", "DRAKE", "THE BIGGEST RAPPER ALIVE · 9TH STAKE ANNIVERSARY")
    lower_third("lt_pink.png", "PINKCHYU", "LIN LAMAR · 23 · GOTH CREATOR · 2M+ FOLLOWERS",
                accent=(200, 60, 220, 255))
    lower_third("lt_tmz.png", "TMZ INTERVIEW", "A SECOND CELEB BARKED IN HER DMS",
                accent=(0, 160, 255, 255))
    avatars = glob.glob(os.path.join(SRC, "pinkchyu.jpg"))
    tweet_ui("tweet_ryan.png",
             "ryan", "@scubaryan_",
             "Drake instantly folded and started barking after this goth baddie told him to",
             "9:12 PM · Aug 8, 2026", "4.1M", avatars[0] if avatars else "")
    stat_card("stat_1m.png", "1M+", "VIEWS IN HOURS")
    stat_card("stat_98.png", "98", "ROOMS · CASA LOMA")
    hud_frame("hud.png")
    light_leak("lightleak.png")
    print("GFX KIT v2 KLART ->", GFX)
