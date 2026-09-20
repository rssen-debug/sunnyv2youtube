#!/usr/bin/env python3
"""POC v4 — "CINEMA KIT"-proof-of-concept (~39 s): ALLT i studiotoolkiten i EN video.

Demonstrerar: 2.5D-parallax, glow-titlar, lower thirds, tweet-UI (sweep-reveal),
stat-kort, kinetic captions (keyword-highlight), beat-pulsad musik (90 BPM),
impacts/whooshes/risers, kamerablixt, jump-cut, color grade + grain + bloom + letterbox + HUD.

Renderar: drake-video/POC_v4_cinema_kit.mp4 (kopieras till videos2026/)
"""
import os, sys, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cinema import ease, ss, drift, GRADE, GRAIN, letterbox, bloom_chain, MUSIC_BEAT, SFX_IMPACT, SFX_WHOOSH, SFX_RISER
from make_captions import build_events, ts, HEADER, parse_script, wav_dur, load_keywords

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GFX = os.path.join(ROOT, "assets", "gfx")
AUDIO = os.path.join(ROOT, "audio")
CLIPDIR = os.path.join(ROOT, "assets", "clips")
BG = os.path.join(ROOT, "assets", "src", "bg_ai.png")
OUT = os.path.join(ROOT, "POC_v4_cinema_kit.mp4")
FPS = 30

def g(n): return os.path.join(GFX, n)

# ---------------- timeline ----------------
full = json.load(open(os.path.join(ROOT, "timings.json")))
FSEG = {s["id"]: s for s in full["segments"]}
d1 = FSEG["A1"]["dur"]; d4 = FSEG["A4"]["dur"]
A4_T = 13.0                      # jump-cut: A4 startar vid 13 s
TOTAL = A4_T + d4 + 1.8          # luft + endcard
print(f"POC: A1 0..{d1:.1f}s | A4 {A4_T:.1f}..{A4_T + d4:.1f}s | total {TOTAL:.1f}s")

# ---------------- poc-captions (shiftade) ----------------
kw = load_keywords()
segs = []
b = {x["id"]: x for x in parse_script()}
segs.append({"id": "A1", "text": b["A1"]["text"], "start": 0.0, "dur": d1})
segs.append({"id": "A4", "text": b["A4"]["text"], "start": A4_T, "dur": d4})
ev = build_events(segs, kw)
lines = [f"Dialogue: 0,{ts(a)},{ts(bb)},PopBig,,0,0,0,,{txt}" for a, bb, txt in ev]
open(os.path.join(ROOT, "poc_captions.ass"), "w", encoding="utf-8").write(HEADER + "\n".join(lines) + "\n")

# ---------------- graf ----------------
inputs, fchains, overlays = [], [], []
ix = 0; ox = 0

def still(path, hold):
    global ix, inputs
    inputs += ["-loop", "1", "-t", f"{hold:.2f}", "-i", path]
    ix += 1
    return ix - 1

def overlay(idx, T0, T1, x, y, w=None, fin=0.25, fout=0.25, extra=""):
    global ox
    ox += 1
    fchains.append(
        f"[{idx}:v]format=rgba" + (f",scale={w}:-1" if w else "") + extra +
        f",setpts=PTS+{T0:.3f}/TB"
        f",fade=t=in:st={T0:.2f}:d={fin:.2f}:alpha=1"
        f",fade=t=out:st={T1 - fout:.2f}:d={fout:.2f}:alpha=1"
        f"[ov{ox}]")
    overlays.append((f"[ov{ox}]",
                     f"overlay=x='{x}':y='{y}':enable='between(t,{T0:.2f},{T1:.2f})'"))

def sfx_a(expr, dur, t, vol, tag, fade_in=0.01):
    global ix, inputs
    inputs += ["-f", "lavfi", "-t", str(dur), "-i", expr + f":d={dur}"]
    a = ix; ix += 1
    ch = f"[{a}:a]aformat=sample_rates=44100:channel_layouts=stereo"
    if fade_in > 0.2: ch += f",afade=t=in:st=0:d={fade_in}"
    ch += f",volume={vol},adelay={int(max(t,0)*1000)}|{int(max(t,0)*1000)}[{tag}]"
    fchains.append(ch)

# ---------- persistenta lager ----------
inputs += ["-i", BG]; ix += 1
fchains.append(f"[0:v]scale=2560:1440,zoompan=z='min(1+0.00030*on,1.22)':"
               f"x='iw/2-(iw/zoom)/2+34*sin(on/{FPS*7})':y='ih/2-(ih/zoom)/2':"
               f"d={int(TOTAL*FPS)}:s=1280x720:fps={FPS}[bg]")
p = still(g("particles.png"), TOTAL); overlay(p, 0, TOTAL, "0", "mod(t*18,760)-60", fin=0.05, fout=0.05)
v = still(g("vignette.png"), TOTAL); overlay(v, 0, TOTAL, "0", "0", fin=0.6, fout=0.05)
h = still(g("hud.png"), TOTAL); overlay(h, 0.2, TOTAL, "0", "0", fin=1.2, fout=0.4)
l = still(g("lightleak.png"), TOTAL); overlay(l, 0, TOTAL, "0", "0", fin=1.6, fout=0.6)

# ---------- SCEN 1 (A1): parallax-hero + glow-titel + lower third ----------
# hero: drake-cirkel med 2.5D-parallax (motriktad drift + andning)
hero = still(g("drake_circle.png"), d1 + 2)
ox += 1
fchains.append(f"[{hero}:v]format=rgba,scale=560:-1,setpts=PTS+0.300/TB,"
               f"rotate='(-1.6+1.6*min(max((t-0.3)/1.4,0),1))*PI/180':ow=iw:oh=ih:c=black@0"
               f",fade=t=in:st=0.30:d=0.30:alpha=1,fade=t=out:st={d1-0.45:.2f}:d=0.40:alpha=1[hero]")
overlays.append(("[hero]", f"overlay=x='{ease(0.3, 1.0, 1500, 690, back=True) + '+(' + str(26) + '*sin(2*PI*t/6.5))'}':"
                 f"y='150+7*sin(2*PI*t/4.3)':enable='between(t,0.30,{d1:.2f})'"))
# glow-titel slår in på beat (1.33 = 2*0.6667)
i = still(g("glow_drake.png"), d1 + 2)
overlay(i, 1.333, d1, ease(1.333, 0.5, "640", "120"), "250", w=560, fin=0.12)
sfx_a(SFX_IMPACT, 1.6, 1.333, 0.6, "im1")
# lower third glider in från vänster
i = still(g("lt_drake.png"), d1 + 2)
overlay(i, 2.6, d1 - 0.2, ease(2.6, 0.55, -1100, 46), "468", w=760, fin=0.18)
# stat-kort slam (beat 8.0)
i = still(g("stat_1m.png"), d1 + 2)
overlay(i, 8.0, 9.8, ease(8.0, 0.45, "640", "510", back=True), "300", w=260, fin=0.12)
sfx_a(SFX_IMPACT, 1.6, 8.0, 0.45, "im2")
# "vs THE GOTH GIRL"
i = still(g("title_vs.png"), d1 + 2)
overlay(i, 6.0, d1, ease(6.0, 0.7, -600, 120, back=True), "500", w=420)
# tweet-UI sweep-reveal (29..35 i A4-delen)
TW_T = A4_T + 16.0
tw = still(g("tweet_ryan.png"), TOTAL)
overlay(tw, TW_T, TW_T + 6.6, ease(TW_T, 0.5, "1320", "392"), ease(TW_T, 0.6, "820", "240"), w=500, fin=0.3)
# sweep-bar (scanlinje) under revealen
inputs += ["-f", "lavfi", "-t", "1.0", "-i", f"color=c=white:s=520x3:r={FPS}"]; ix += 1
ox += 1
fchains.append(f"[{ix-1}:v]format=rgba,fade=t=in:st=0:d=0.1:alpha=1,fade=t=out:st=0.75:d=0.25:alpha=1,"
               f"setpts=PTS+{TW_T:.3f}/TB[swp]")
overlays.append(("[swp]", f"overlay=x='392':y='{ease(TW_T, 0.85, 240, 610)}':"
                f"enable='between(t,{TW_T:.2f},{TW_T + 1:.2f})'"))
sfx_a(SFX_GLITCH if False else SFX_IMPACT, 1.6, TW_T, 0.35, "im3")

# ---------- JUMP-CUT (11.4 -> 13) ----------
sfx_a(SFX_WHOOSH, 1.0, A4_T - 0.45, 0.5, "wh1")
sfx_a(SFX_IMPACT, 1.6, A4_T, 0.55, "im4")
# glow bark-titel på beat 13.33
i = still(g("glow_bark.png"), TOTAL)
overlay(i, A4_T + 0.333, A4_T + 8.5, ease(A4_T + 0.333, 0.5, "90", "140"), "120", w=880, fin=0.12)
# pinkchyu-cirkel snurrar in
i = still(g("pink_circle.png"), TOTAL)
overlay(i, A4_T + 3.0, A4_T + 8.5, ease(A4_T + 3.0, 0.9, -560, 880, back=True), "330", w=330)
# ARF-kort
i = still(g("card_arf.png"), TOTAL)
overlay(i, A4_T + 9.0, A4_T + 15.0, "290", ease(A4_T + 9.0, 0.9, -340, 260, back=True), w=700)
# NOT LIKE US-kort
i = still(g("card_nlu.png"), TOTAL)
overlay(i, A4_T + 15.0, TW_T + 6.6, ease(A4_T + 15.0, 0.8, 1400, 200), "170", w=760)

# ---------- BARK-KLIPP MED LJUD (beat-lagda) ----------
CB = A4_T + 18.3
inputs += ["-ss", "5.50", "-t", "6.50", "-i", os.path.join(CLIPDIR, "bark.mp4")]
vidx = ix; ix += 1
ox += 1
fchains.append(f"[{vidx}:v]scale=940:-1,setsar=1,format=rgba,"
               f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.35:width=3,"
               f"setpts=PTS+{CB:.3f}/TB"
               f",fade=t=in:st={CB:.2f}:d=0.14:alpha=1,fade=t=out:st={CB + 6.36:.2f}:d=0.14:alpha=1[ov{ox}]")
overlays.append((f"[ov{ox}]", f"overlay=x='(W-w)/2':y='86':enable='between(t,{CB:.2f},{CB + 6.5:.2f})'"))
inputs += ["-i", os.path.join(CLIPDIR, "bark.mp4")]; aidx = ix; ix += 1
fchains.append(f"[{aidx}:a]atrim=0:6.5,aformat=sample_rates=44100:channel_layouts=stereo,"
               f"volume=1.40,adelay={int(CB*1000)}|{int(CB*1000)}[clp]")
sfx_a(SFX_IMPACT, 1.6, CB, 0.5, "im5")
sfx_a(SFX_RISER, 2.4, CB - 2.4, 0.5, "rs1", fade_in=2.2)

# ---------- ENDCARD ----------
i = still(g("glow_subscribe.png"), TOTAL)
overlay(i, TOTAL - 1.6, TOTAL, "330", "260", w=620, fin=0.3, fout=0.01)

# ---------- kamerablixt ----------
inputs += ["-f", "lavfi", "-t", f"{TOTAL:.2f}", "-i", f"color=c=white:s=1280x720:r={FPS}"]; ix += 1
ch = f"[{ix-1}:v]format=rgba"
for pnt in [1.333, A4_T, TW_T, CB]:
    ch += f",fade=t=in:st={pnt:.2f}:d=0.06:alpha=1,fade=t=out:st={pnt + 0.10:.2f}:d=0.18:alpha=1"
fchains.append(ch + "[wfl]")
overlays.append(("[wfl]", "overlay=0:0"))

# ---------- LJUD ----------
for lbl, at in [("A1", 0.0), ("A4", A4_T)]:
    inputs += ["-i", os.path.join(AUDIO, f"{lbl}.wav")]; a = ix; ix += 1
    fchains.append(f"[{a}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"adelay={int(at*1000)}|{int(at*1000)}[v_{lbl}]")
# beat-musik + duckning under klipp
inputs += ["-f", "lavfi", "-t", f"{TOTAL:.2f}", "-i", MUSIC_BEAT + f":d={TOTAL:.2f}"]; m = ix; ix += 1
fchains.append(f"[{m}:a]lowpass=f=500,aformat=channel_layouts=stereo,"
               f"volume='if(between(t,{CB - 0.2:.2f},{CB + 6.7:.2f}),0.10,0.34)':eval=frame,"
               f"afade=t=in:st=0:d=1.2,afade=t=out:st={TOTAL - 2.5:.2f}:d=2.2[mus]")

mix = "[v_A1][v_A4][clp][mus][im1][im2][im3][im4][im5][wh1][rs1]"
fchains.append(mix + "amix=inputs=11:normalize=0,alimiter=limit=0.92[aout]")

# ---------- klistra ihop ----------
graph = ";".join(fchains)
prev = "[bg]"
for n, (lbl, ovexpr) in enumerate(overlays):
    nxt = f"[v{n}]"
    graph += f";{prev}{lbl}{ovexpr}{nxt}"
    prev = nxt
graph += f";{prev}fade=t=in:st=0:d=0.5,{GRADE},{bloom_chain(prev, 'blo', uid='poc')}" \
         if False else ""
# bloom behöver egen kedja: bygg om snyggt:
graph = graph.rstrip(";")
graph += f";{prev}fade=t=in:st=0:d=0.5,fps={FPS},setpts=PTS/TB[pregrade]"
graph += ";" + GRADE.replace("eq=", "[pregrade]eq=", 1)
# efter GRADE-kedjan behöver vi label — bygg om rent istället:
graph = ";".join(fchains)
prev = "[bg]"
for n, (lbl, ovexpr) in enumerate(overlays):
    nxt = f"[v{n}]"
    graph += f";{prev}{lbl}{ovexpr}{nxt}"
    prev = nxt
graph += f";{prev}fade=t=in:st=0:d=0.5,format=rgba[preg]"
graph += f";[preg]split=2[pl][pr];[pr]gblur=sigma=11[pg];[pl][pg]blend=all_mode=screen:all_opacity=0.22[pbl]"
graph += f";[pbl]{GRADE},{GRAIN},{letterbox()},subtitles={os.path.join(ROOT, 'poc_captions.ass')},format=yuv420p[vout]"

open(os.path.join(ROOT, "scripts", "filtergraph_poc.txt"), "w").write(graph)
print("renderar POC", round(TOTAL, 1), "s ...")
r = subprocess.run(["ffmpeg", "-y"] + inputs +
                   ["-filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
                    "-t", f"{TOTAL:.2f}", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "21", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", OUT], capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-4500:]); raise SystemExit(1)
print("KLART:", OUT, os.path.getsize(OUT) // 1024, "KB")
