#!/usr/bin/env python3
"""build_video.py — mrbeast_empire-renderaren v2 (SHOT-BASERAD för 2GB-RAM-sandboxen).

Arkitektur (samma lösning som kick_rank_drama-episoden):
  PASS A — 8 block-segment (video only, endast det blockets overlays) -> .cache/render/seg_*.mp4
  PASS B — ljud HELA videon i ett pass (VO + 4 klipp + beat-drone + SFX, duckad) -> episode_audio.m4a
  PASS C — concat (-c copy) + CINEMA-LAGRET (blixtar, fades, GRADE, bloom, GRAIN,
           letterbox, kinetic captions) + mux -> mrbeast_empire.mp4

MANDATE-matning: 4 klipp m ljud / beats 2-6s / Anton+Archivo+Bebas / LT vid intros /
EXCERPT-headline sweep+glitch / 3 stat-slams / kinetic captions / parallax+drift /
impacts+risers+whoosh+duck / grade+grain+bloom+letterbox+vignette+HUD / 90 BPM-sync.
"""
import os, sys, json, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cinema import (ease, ss, drift, GRADE, GRAIN, letterbox,
                    MUSIC_BEAT, SFX_IMPACT, SFX_WHOOSH, SFX_RISER, SFX_GLITCH, beat)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GFX = os.path.join(ROOT, "assets", "gfx")
AUDIO = os.path.join(ROOT, "audio")
CLIPDIR = os.path.join(ROOT, "assets", "clips")
FDIR = os.path.join(ROOT, "assets", "fonts")
BG = os.path.join(ROOT, "assets", "src", "bg_ai.png")
SEGDIR = os.path.join(ROOT, ".cache", "render")
OUT = os.path.join(ROOT, "mrbeast_empire.mp4")
AOUT = os.path.join(ROOT, "episode_audio.m4a")
FPS = 30
ORDER = ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "A6"]
os.makedirs(SEGDIR, exist_ok=True)

T = json.load(open(os.path.join(ROOT, "timings.json")))
S = {s["id"]: s for s in T["segments"]}
TOTAL = T["total"] + 2.0

def g(n): return os.path.join(GFX, n)
def B(x): return beat(x)
def sh(args, label):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"!!! {label} MISSLYCKADES:\n", r.stderr[-3500:]); raise SystemExit(1)
    return r

# ---------- förskalning av PNG (RAM) ----------
_SMCACHE = {}
def prescale(fname, w):
    key = (fname, w)
    if key in _SMCACHE:
        return _SMCACHE[key]
    from PIL import Image
    src = g(fname)
    img = Image.open(src).convert("RGBA")
    if img.width <= w:
        dst = src
    else:
        h = max(1, int(img.height * w / img.width))
        dst = os.path.join(GFX, "sm_" + fname.replace(".png", f"_{w}.png"))
        img.resize((w, h), Image.LANCZOS).save(dst)
    _SMCACHE[key] = dst
    return dst

# ---------- scenplan: absoluta tider ----------
SCENE = []      # {path,T0,T1,x,y,fin,fout}
FLASH = []      # blixtpunkter (absoluta)
SFX = []        # (typ, t, vol)
def card(name, T0, T1, x, y, w=0, fin=0.25, fout=0.25):
    SCENE.append({"path": prescale(name, w) if w else g(name),
                  "T0": T0, "T1": T1, "x": str(x), "y": str(y), "fin": fin, "fout": fout})
def impact(t, vol=0.55): SFX.append(("impact", t, vol))
def whoosh(t, vol=0.5):  SFX.append(("whoosh", t, vol))
def riser(t, vol=0.5):   SFX.append(("riser", t, vol))
def glitch(t, vol=0.4):  SFX.append(("glitch", t, vol))

s1 = S["A1"]["start"]
s2 = S["A2"]["start"]
s3 = S["A3"]["start"]; sp3 = S["A3"]["speech"]
s4 = S["A4"]["start"]; sp4 = S["A4"]["speech"]
s5 = S["A5"]["start"]
sb = S["B1"]["start"]
sc = S["B2"]["start"]; spc = S["B2"]["speech"]
s6 = S["A6"]["start"]
d1 = S["A1"]["dur"]
d6 = S["A6"]["dur"]
for k in ORDER:
    print(k, "start", round(S[k]["start"], 2), "dur", round(S[k]["dur"], 2))
print("TOTAL:", round(TOTAL, 1))

# ---------------- KLIPP (C1-C4) ----------------
C1 = B(s3 + sp3 + 0.25)
C2 = B(s4 + sp4 + 0.35)
C3 = B(C2 + 6.9)
C4 = B(sc + spc + 0.30)
CLIPS = [
    {"f": "count.mp4",      "dur": 6.5, "t": C1, "w": 880, "y": 64, "vol": 1.30, "crop": "crop=iw*0.70:ih:iw*0.30:0,"},
    {"f": "squid.mp4",      "dur": 6.0, "t": C2, "w": 900, "y": 60, "vol": 1.30, "crop": ""},
    {"f": "beastgames.mp4", "dur": 6.5, "t": C3, "w": 920, "y": 55, "vol": 1.35, "crop": ""},
    {"f": "et.mp4",         "dur": 6.0, "t": C4, "w": 880, "y": 66, "vol": 1.50, "crop": ""},
]
for c in CLIPS:
    riser(c["t"] - 2.4); whoosh(c["t"] - 0.45); impact(c["t"]); FLASH.append(c["t"])
    print(f"klipp {c['f']} @ {c['t']:.2f}s")

# ---------------- A1 HOOK ----------------
card("beast_circle.png", s1 + 0.3, s1 + 8.4,
     ease(s1 + 0.3, 1.0, 1500, 690, back=True) + "+(18*sin(2*PI*t/6.5))",
     "150+7*sin(2*PI*t/4.3)", 560, fin=0.30, fout=0.35)
card("glow_mrbeast.png", B(s1 + 1.33), s1 + 8.2, ease(s1 + 1.33, 0.5, "640", "110"), "185", 580, fin=0.12)
impact(B(s1 + 1.33), 0.6)
card("lt_jimmy.png", s1 + 2.67, s1 + 9.2, ease(s1 + 2.67, 0.55, -780, 46), "450", 700, fin=0.18)
card("stat_500m.png", B(s1 + 8.0), s1 + 10.4, ease(s1 + 8.0, 0.45, "640", "860", back=True), "185", 300, fin=0.12)
impact(B(s1 + 8.0))
card("card_oneguy.png", s1 + 10.8, s1 + 16.4, "150", ease(s1 + 10.8, 0.7, -320, 170, back=True), 980)
card("card_broke.png", s1 + 16.8, s1 + 22.2, ease(s1 + 16.8, 0.7, 1400, 210), "180", 860)
card("glow_500m.png", B(s1 + 22.67), s1 + d1 - 0.3, ease(s1 + 22.67, 0.8, "640", "250"), "190", 780)

# ---------------- A2 KARAKTÄR ----------------
FLASH.append(s2)
card("card_2012.png", s2 + 0.4, s2 + 7.2, "190", ease(s2 + 0.4, 0.7, -320, 165, back=True), 900)
card("beast_circle.png", s2 + 3.0, s2 + 7.0, ease(s2 + 3.0, 0.9, -560, 900, back=True), "185", 310)
card("card_algo.png", B(s2 + 9.33), s2 + 15.6, "200", "160", 880)
impact(B(s2 + 9.33), 0.45)
card("title_2017.png", B(s2 + 16.0), s2 + 23.4, "160", ease(s2 + 16.0, 0.6, -340, 150), 960, fin=0.14)
impact(B(s2 + 16.0), 0.5)
card("beast_circle.png", s2 + 20.0, s2 + 25.8, ease(s2 + 20.0, 0.9, 1400, 880, back=True), "190", 300)

# ---------------- A3 GENOMBROTT ----------------
card("card_count.png", s3 + 0.4, s3 + 7.8, "150", "160", 980)
card("card_buried.png", B(s3 + 8.0), s3 + 13.0, "210", "180", 860)
impact(B(s3 + 8.0), 0.5)
card("card_money.png", s3 + 13.3, s3 + 18.6, "190", "170", 900)
card("card_formula.png", B(s3 + 19.33), s3 + 24.9, "210", "170", 860)
impact(B(s3 + 19.33), 0.45)

# ---------------- A4 IMPERIET ----------------
FLASH.append(s4)
card("card_squid.png", s4 + 0.4, s4 + 7.6, "160", ease(s4 + 0.4, 0.7, -320, 160), 960)
card("pc_feast.png", s4 + 7.8, s4 + 13.2, "270", ease(s4 + 7.8, 0.8, -900, 35), 740)
card("card_feast.png", s4 + 13.6, s4 + 16.0, "240", "90", 760)
card("card_games.png", B(s4 + 16.67), s4 + 21.4, "150", "160", 980)
impact(B(s4 + 16.67), 0.5)
card("glow_games.png", B(s4 + 21.33), s4 + sp4 - 0.3, ease(s4 + 21.33, 0.7, "640", "240"), "185", 780)
impact(B(s4 + 21.33), 0.5)

# ---------------- A5 KRISEN ----------------
FLASH.append(s5)
card("card_lawsuit.png", B(s5 + 0.67), s5 + 7.0, "170", "160", 940)
impact(B(s5 + 0.67), 0.55)
HLV = B(s5 + 8.0)
card("hl_variety.png", HLV, s5 + 14.4, ease(HLV, 0.5, "1320", "330"), ease(HLV, 0.6, "760", "150"), 620, fin=0.3)
SWEEP = {"path": "SWEEP", "T0": HLV, "T1": HLV + 1.0, "x": "330",
         "y": ease(HLV, 0.85, 150, 545), "fin": 0.1, "fout": 0.25}
SCENE.append(SWEEP)
glitch(HLV); FLASH.append(HLV)
card("card_turned.png", B(s5 + 14.67), s5 + 20.6, "190", ease(s5 + 14.67, 0.7, -320, 170), 900)
impact(B(s5 + 14.67), 0.45)
card("card_survive.png", B(s5 + 21.33), s5 + 26.8, "200", "170", 880)
card("beast_circle.png", s5 + 26.4, s5 + 31.4, ease(s5 + 26.4, 0.9, 1400, 880, back=True), "185", 300)

# ---------------- B1 SVARET ----------------
FLASH.append(sb)
card("card_ceo.png", sb + 0.4, sb + 6.0, "170", "165", 940)
card("lt_housenbold.png", sb + 2.0, sb + 6.9, ease(sb + 2.0, 0.55, -780, 46), "420", 700, fin=0.18)
card("pc_beastland.png", sb + 7.2, sb + 14.2, "280", ease(sb + 7.2, 0.8, -900, 30), 720)
card("card_lawsuit.png", sb + 14.6, sb + 20.0, "360", "90", 560)

# ---------------- B2 JUST NU ----------------
FLASH.append(sc)
card("card_s2.png", sc + 0.4, sc + 6.4, "160", "155", 960)
card("glow_games.png", B(sc + 6.67), sc + 12.0, ease(sc + 6.67, 0.7, "640", "290"), "250", 700, fin=0.14)
card("stat_52b.png", B(sc + 12.0), sc + 14.4, ease(sc + 12.0, 0.45, "640", "865", back=True), "185", 300, fin=0.12)
impact(B(sc + 12.0))
card("card_campus.png", B(sc + 14.67), sc + 19.6, "190", "160", 900)
card("glow_500m.png", B(sc + 20.0), sc + 24.0, "250", "190", 780)
impact(B(sc + 20.0), 0.5)
card("stat_300m.png", B(sc + 24.0), sc + 26.4, ease(sc + 24.0, 0.45, "640", "865", back=True), "190", 290, fin=0.12)
HLB = B(sc + 26.67)
card("hl_bi.png", HLB, sc + 32.6, ease(HLB, 0.5, "1320", "330"), ease(HLB, 0.6, "760", "150"), 620, fin=0.3)
glitch(HLB)

# ---------------- A6 PAYOFF ----------------
FLASH.append(s6)
card("card_buried.png", s6 + 0.4, s6 + 4.6, "260", "165", 760)
card("glow_mrbeast.png", B(s6 + 4.67), s6 + 11.0, ease(s6 + 4.67, 0.7, "640", "235"), "175", 790)
impact(B(s6 + 4.67), 0.55)
card("card_end.png", B(s6 + 11.33), s6 + 17.5, "150", "165", 980)
riser(s6 + 15.7)
SUB = B(s6 + 18.67)
card("glow_subscribe.png", SUB, TOTAL - 0.6, "330", "230", 620, fin=0.5, fout=0.3)
impact(SUB, 0.5); whoosh(SUB - 0.45)

# ============================================================
# PASS A — block-segment (video only)
# ============================================================
SEGS = [("A1", 0.0, s2), ("A2", s2, s3), ("A3", s3, s4), ("A4", s4, s5),
        ("A5", s5, sb), ("B1", sb, sc), ("B2", sc, s6), ("A6", s6, TOTAL)]

# för-skala bakgrund en gång
from PIL import Image as _PILImage
_BG1920 = BG.replace(".png", "_1920.png")
if not os.path.exists(_BG1920):
    _im = _PILImage.open(BG).convert("RGB")
    _im = _im.resize((1920, int(_im.height * 1920 / _im.width)), _PILImage.LANCZOS)
    _im.save(_BG1920)

def render_segment(sid, T0, T1):
    out = os.path.join(SEGDIR, f"seg_{sid}.mp4")
    dur = T1 - T0
    inputs, fchains, overlays = [], [], []
    ix = 0; ox = 0

    def still(path, hold):
        nonlocal ix, inputs
        inputs += ["-loop", "1", "-t", f"{hold:.2f}", "-i", path]
        ix += 1
        return ix - 1

    def add_overlay(idx, L0, L1, x, y, fin=0.25, fout=0.25, extra=""):
        nonlocal ox
        ox += 1
        fchains.append(
            f"[{idx}:v]format=rgba" + extra +
            f",setpts=PTS+{max(L0,0):.3f}/TB"
            f",fade=t=in:st={max(L0,0):.2f}:d={max(fin,0.04):.2f}:alpha=1"
            f",fade=t=out:st={max(L1 - fout, 0.1):.2f}:d={max(fout,0.04):.2f}:alpha=1[ov{ox}]")
        overlays.append((f"[ov{ox}]",
                         f"overlay=x='{x}':y='{y}':enable='between(t,{max(L0,0):.2f},{L1:.2f})'"))

    # bakgrund: zoompan med FÖRSKJUTET fönster (on+ON0) => sömlös zoom över snitten
    ON0 = int(T0 * FPS)
    inputs += ["-i", _BG1920]; ix += 1
    fchains.append(
        f"[0:v]scale=1920:1080,zoompan=z='min(1+0.00006*(on+{ON0}),1.45)':"
        f"x='iw/2-(iw/zoom)/2+34*sin((on+{ON0})/{FPS*7.0})':y='ih/2-(ih/zoom)/2':"
        f"d={int(dur*FPS)+2}:s=1280x720:fps={FPS}[bg]")
    # persistenter (particles med fas-offset, vinjett, HUD, lightleak)
    poff = (18.0 * T0) % 760
    add_overlay(still(g("particles.png"), dur + 1), 0, dur, "0", f"mod(t*18+{poff:.2f},760)-60", 0.08, 0.08)
    add_overlay(still(g("vignette.png"), dur + 1), 0, dur, "0", "0", 0.08, 0.08)
    add_overlay(still(g("hud.png"), dur + 1), 0, dur, "0", "0", 1.2 if T0 == 0 else 0.08, 0.4)
    add_overlay(still(g("lightleak.png"), dur + 1), 0, dur, "0", "0", 1.6 if T0 == 0 else 0.08, 0.6)

    # uttryck i globala tider -> segment-lokala tider (två säkra ankare, inga svep-regexer)
    def loc(expr):
        return (expr
                .replace("PI*t", f"PI*(t+{T0:.3f})")
                .replace("(t-", f"(t+{T0:.3f}-"))

    # scenkort i fönstret
    for e in SCENE:
        if e["T1"] <= T0 or e["T0"] >= T1:
            continue
        L0, L1 = max(e["T0"] - T0, 0.0), min(e["T1"] - T0, dur)
        if e["path"] == "SWEEP":
            inputs += ["-f", "lavfi", "-t", f"{L1:.2f}", "-i", f"color=c=white:s=640x3:r={FPS}"]
            ix += 1
            add_overlay(ix - 1, L0, L1, loc(e["x"]), loc(e["y"]), 0.1, 0.25)
        else:
            add_overlay(still(e["path"], dur + 1), L0, L1,
                        loc(e["x"]), loc(e["y"]), e["fin"], e["fout"])

    # klipp-video i fönstret
    n_clip = 0
    for c in CLIPS:
        if c["t"] + c["dur"] <= T0 or c["t"] >= T1:
            continue
        L0, L1 = max(c["t"] - T0, 0.0), min(c["t"] + c["dur"] - T0, dur)
        inputs += ["-ss", f"{max(T0 - c['t'], 0):.2f}", "-t", f"{L1 - L0:.2f}",
                   "-i", os.path.join(CLIPDIR, c["f"])]
        v = ix; ix += 1
        fin = 0.14 if c["t"] >= T0 else 0.04
        n_clip += 1
        fchains.append(
            f"[{v}:v]{c['crop']}scale={c['w']}:-1,setsar=1,format=rgba,"
            f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.35:width=3,"
            f"setpts=PTS+{L0:.3f}/TB"
            f",fade=t=in:st={L0:.2f}:d={fin:.2f}:alpha=1"
            f",fade=t=out:st={L1 - 0.14:.2f}:d=0.14:alpha=1[vc{n_clip}]")
        overlays.append((f"[vc{n_clip}]",
                         f"overlay=x='(W-w)/2':y='{c['y']}':enable='between(t,{L0:.2f},{L1:.2f})'"))

    graph = ";".join(fchains)
    prev = "[bg]"
    for n, (lbl, ovexpr) in enumerate(overlays):
        nxt = f"[x{n}]"
        graph += f";{prev}{lbl}{ovexpr}{nxt}"
        prev = nxt
    graph += f";{prev}fps={FPS},format=yuv420p[vout]"
    open(os.path.join(SEGDIR, f"graph_{sid}.txt"), "w").write(graph)
    r = sh(["ffmpeg", "-y"] + inputs + ["-filter_complex", graph,
            "-map", "[vout]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-profile:v", "high", "-level", "4.0", "-an",
            "-video_track_timescale", "15360", out], f"seg {sid}")
    print("segment klart:", sid, round(dur, 2), "s | overlays:", len(overlays))

for sid, T0, T1 in SEGS:
    # segment-cache: rendera bara om filen saknas (ändrad SCENE/CLIPS => radera .cache/render)
    if not os.path.exists(os.path.join(SEGDIR, f"seg_{sid}.mp4")):
        render_segment(sid, T0, T1)
    else:
        print("segment-cache:", sid)

# concat (samma codec-inställningar => -c copy)
lst = os.path.join(SEGDIR, "list.txt")
open(lst, "w").write("\n".join(f"file 'seg_{sid}.mp4'" for sid, _, _ in SEGS))
segs_all = os.path.join(SEGDIR, "segs_all.mp4")
sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", segs_all], "concat")
print("concat ok")

# ============================================================
# PASS B — ljud, hela videon
# ============================================================
inputs, fchains = [], []
ix = 0
vo_labels, clip_audio, sfx_labels = [], [], []
for lbl in ORDER:
    inputs += ["-i", os.path.join(AUDIO, f"{lbl}.wav")]
    a = ix; ix += 1
    ms = int(S[lbl]["start"] * 1000)
    fchains.append(f"[{a}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"adelay={ms}|{ms}[v_{lbl}]")
    vo_labels.append(f"[v_{lbl}]")
for ci, c in enumerate(CLIPS):
    inputs += ["-ss", f"{0:.2f}", "-t", f"{c['dur']:.2f}", "-i", os.path.join(CLIPDIR, c["f"])]
    a = ix; ix += 1
    T0 = c["t"]
    fchains.append(f"[{a}:a]atrim=0:{c['dur']:.2f},aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"volume={c['vol']:.2f},adelay={int(T0 * 1000)}|{int(T0 * 1000)}[ca{ci}]")
    clip_audio.append(f"[ca{ci}]")
EXPR = {"impact": (SFX_IMPACT, 1.6, 0.0), "whoosh": (SFX_WHOOSH, 1.0, 0.0),
        "riser": (SFX_RISER, 2.4, 2.2), "glitch": (SFX_GLITCH, 1.0, 0.0)}
for si, (typ, t, vol) in enumerate(SFX):
    if t < 0.15: continue
    expr, dur, fi = EXPR[typ]
    inputs += ["-f", "lavfi", "-t", str(dur), "-i", expr + f":d={dur}"]
    a = ix; ix += 1
    ch = f"[{a}:a]aformat=sample_rates=44100:channel_layouts=stereo"
    if fi > 0.2: ch += f",afade=t=in:st=0:d={fi}"
    ch += f",volume={vol},adelay={int(max(t, 0) * 1000)}|{int(max(t, 0) * 1000)}[sx{si}]"
    fchains.append(ch)
    sfx_labels.append(f"[sx{si}]")
duck = "+".join(f"between(t,{c['t'] - 0.2:.2f},{c['t'] + c['dur'] + 0.3:.2f})" for c in CLIPS)
inputs += ["-f", "lavfi", "-t", f"{TOTAL:.2f}", "-i", MUSIC_BEAT + f":d={TOTAL:.2f}"]
m = ix; ix += 1
fchains.append(f"[{m}:a]lowpass=f=500,aformat=channel_layouts=stereo,"
               f"volume='if({duck},0.10,0.34)':eval=frame,"
               f"afade=t=in:st=0:d=1.6,afade=t=out:st={TOTAL - 2.6:.2f}:d=2.3[mus]")
mix = "".join(vo_labels) + "".join(clip_audio) + "[mus]" + "".join(sfx_labels)
n_in = len(vo_labels) + len(clip_audio) + 1 + len(sfx_labels)
fchains.append(mix + f"amix=inputs={n_in}:normalize=0,alimiter=limit=0.63:level=0[aout]")
print("ljud-mixar", n_in, "strömmar ...")
sh(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fchains),
    "-map", "[aout]", "-t", f"{TOTAL:.2f}", "-c:a", "aac", "-b:a", "160k", AOUT], "ljud-pass")
print("ljud klart")

# ============================================================
# PASS C — CINEMA-LAGRET + mux
# ============================================================
inputs = ["-i", segs_all]
fchains = []
# blixt-lager (vit overlay med fade-par)
inputs += ["-f", "lavfi", "-t", f"{TOTAL:.2f}", "-i", f"color=c=white:s=1280x720:r={FPS}"]
ch = "[1:v]format=rgba"
for p in FLASH:
    ch += f",fade=t=in:st={p:.2f}:d=0.06:alpha=1,fade=t=out:st={p + 0.10:.2f}:d=0.18:alpha=1"
fchains.append(ch + "[wfl]")
fchains.append(f"[0:v][wfl]overlay=0:0[base]")
graph = ";".join(fchains)
graph += (f";[base]fade=t=in:st=0:d=0.6,fade=t=out:st={TOTAL - 1.4:.2f}:d=1.4,format=rgba[preg]"
          f";[preg]split=2[pl][pr];[pr]gblur=sigma=11[pg];[pl][pg]blend=all_mode=screen:all_opacity=0.22[pbl]"
          f";[pbl]{GRADE},{GRAIN},{letterbox()},"
          f"subtitles=filename={os.path.join(ROOT, 'captions.ass')}:fontsdir={FDIR},"
          f"fps={FPS},format=yuv420p[vout]")
inputs += ["-i", AOUT]
sh(["ffmpeg", "-y"] + inputs + ["-filter_complex", graph,
    "-map", "[vout]", "-map", "2:a", "-t", f"{TOTAL:.2f}",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy",
    "-movflags", "+faststart", OUT], "cinema-pass")
print("KLART:", OUT, os.path.getsize(OUT) // 1024, "KB")
