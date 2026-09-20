#!/usr/bin/env python3
"""sunnyv2-render v3 — DOKUMENTÄR-EDITION (klipp med ljud + sound design).
Bygger drake_goth_girl_sunnyv2.mp4 (1280x720, 30 fps).

Nytt i v3 (enligt dokumentär-reglerna):
  * Riktiga videoklipp MED original-ljud, synkade till repliker ("Here's the moment")
  * Sound design: impacts (boom), whooshes, risers, musik-duckning under klipp
  * Hårdare snitt (kortare fades) + allt annat från v2 (cards, hero, captions, blixtrar)

sunnyv2 => ffmpeg:
  Easy Ease (F9)      -> smoothstep   | Slam-in -> easeOutBack
  Velocity ramp       -> zoompan-exponentiell zoom
  Dip to white        -> vit flash-overlay
  Pre-compose/nesting -> märkta strömmar i filter_complex
"""
import os, json, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GFX = os.path.join(ROOT, "assets", "gfx")
AUDIO = os.path.join(ROOT, "audio")
CLIPDIR = os.path.join(ROOT, "assets", "clips")
BG = os.path.join(ROOT, "assets", "src", "bg_ai.png")
OUT = os.path.join(ROOT, "drake_goth_girl_sunnyv2.mp4")
FPS = 30
ORDER = ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "A6"]

T = json.load(open(os.path.join(ROOT, "timings.json")))
S = {s["id"]: s for s in T["segments"]}
TOTAL = T["total"] + 4.0
N_FR = int(TOTAL * FPS)

def g(n): return os.path.join(GFX, n)

def ss(T0, D):
    return f"min(max((t-{T0:.3f})/{D:.3f},0),1)"

def ease(T0, D, a, b, back=False):
    p = f"({ss(T0, D)})"
    if back:
        return f"{a}+({b}-{a})*(1+2.70158*pow({p}-1,3)+1.70158*pow({p}-1,2))"
    return f"{a}+({b}-{a})*{p}*{p}*(3-2*{p})"

inputs, fchains, overlays = [], [], []
ix = 0
ox = 0

def still(path, hold):
    global ix, inputs
    inputs += ["-loop", "1", "-t", f"{hold:.2f}", "-i", path]
    ix += 1
    return ix - 1

def overlay(idx, T0, T1, x, y, w=None, fin=0.25, fout=0.25):
    global ox
    ox += 1
    fchains.append(
        f"[{idx}:v]format=rgba" + (f",scale={w}:-1" if w else "") +
        f",setpts=PTS+{T0:.3f}/TB"
        f",fade=t=in:st={T0:.2f}:d={fin:.2f}:alpha=1"
        f",fade=t=out:st={T1 - fout:.2f}:d={fout:.2f}:alpha=1"
        f"[ov{ox}]")
    overlays.append((f"[ov{ox}]",
                     f"overlay=x='{x}':y='{y}':enable='between(t,{T0:.2f},{T1:.2f})'"))

# ---------------- bakgrund: langsam "infinite zoom" ----------------
inputs += ["-i", BG]
ix += 1
fchains.append(
    f"[0:v]scale=2560:1440,zoompan=z='min(1+0.00006*on,1.45)':"
    f"x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':d={N_FR}:s=1280x720:fps={FPS}[bg]")

p_idx = still(g("particles.png"), TOTAL)
overlay(p_idx, 0, TOTAL, "0", "mod(t*18,760)-60", fin=0.05, fout=0.05)
v_idx = still(g("vignette.png"), TOTAL)
overlay(v_idx, 0, TOTAL, "0", "0", fin=0.8, fout=0.05)

s1, d1 = S["A1"]["start"], S["A1"]["dur"]
s2, d2 = S["A2"]["start"], S["A2"]["dur"]
s3, d3 = S["A3"]["start"], S["A3"]["dur"]
s4, d4 = S["A4"]["start"], S["A4"]["dur"]
s5, d5 = S["A5"]["start"], S["A5"]["dur"]
b1 = S.get("B1"); b2 = S.get("B2")
s6, d6 = S["A6"]["start"], S["A6"]["dur"]
for k, v in S.items(): print(k, round(v["start"], 2), round(v["dur"], 2))

# ---------------- KLIPP MED LJUD (dokumentär-B-roll) ----------------
# {fil, cut=snapshot-tid i källan, dur, t=timeline-start, w, y, vol}
CLIPS = []
if b1 and b2:
    CLIPS = [
        {"f": "enews.mp4",   "cut": 26.0, "dur": 5.0, "t": s1 + d1 - 5.0,   "w": 860, "y": 80, "vol": 0.95},  # A1 "Listen to this."
        {"f": "bark.mp4",    "cut": 5.5,  "dur": 6.5, "t": s4 + 18.3,       "w": 920, "y": 60, "vol": 1.40},  # A4 "Here's the moment." (bark @ klipp 6.5-7s)
        {"f": "speed.mp4",   "cut": 21.5, "dur": 5.0, "t": s4 + d4 - 2.6,   "w": 820, "y": 85, "vol": 0.85},  # A4 "the clip was everywhere"
        {"f": "casaloma.mp4","cut": 0.5,  "dur": 7.0, "t": s5 + d5 - 7.0,   "w": 920, "y": 55, "vol": 0.75},  # A5 "Look at this place."
        {"f": "speed.mp4",   "cut": 27.0, "dur": 5.0, "t": b1["start"] + b1["dur"] - 5.0, "w": 820, "y": 85, "vol": 0.85},  # B1 "reacted how you'd expect"
        {"f": "tmz.mp4",     "cut": 3.5,  "dur": 6.5, "t": b2["start"] + 3.2, "w": 880, "y": 70, "vol": 1.35},  # B2 "Here she is, telling TMZ"
    ]
clip_audio = []      # (aidx, t, vol)
sfx_events = []      # (typ, t)  typ: impact/whoosh
risers = []          # t

for ci, c in enumerate(CLIPS):
    inputs += ["-ss", f"{c['cut']:.2f}", "-t", f"{c['dur']:.2f}", "-i", os.path.join(CLIPDIR, c["f"])]
    vidx = ix; ix += 1
    T0, T1 = c["t"], c["t"] + c["dur"]
    ox += 1
    fchains.append(
        f"[{vidx}:v]scale={c['w']}:-1,setsar=1,format=rgba,"
        f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.35:width=3,"
        f"setpts=PTS+{T0:.3f}/TB"
        f",fade=t=in:st={T0:.2f}:d=0.14:alpha=1"
        f",fade=t=out:st={T1 - 0.14:.2f}:d=0.14:alpha=1[ov{ox}]")
    overlays.append((f"[ov{ox}]",
                     f"overlay=x='(W-w)/2':y='{c['y']}':enable='between(t,{T0:.2f},{T1:.2f})'"))
    # klipp-ljud
    inputs += ["-i", os.path.join(CLIPDIR, c["f"])]  # ljud: hela filen, vi klipper med atrim
    aidx = ix; ix += 1
    fchains.append(f"[{aidx}:a]atrim=0:{c['dur']:.2f},aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"volume={c['vol']:.2f},adelay={int(T0 * 1000)}|{int(T0 * 1000)}[ca{ci}]")
    clip_audio.append(f"[ca{ci}]")
    sfx_events.append(("whoosh", T0 - 0.45))
    sfx_events.append(("impact", T0))

risers.append(s4 + 16.2)   # innan bark-reveal
risers.append(s6 + 2.0)    # innan endcard

# ---------------- GFX-scener (cards / hero / titlar) ----------------
# SCEN 1: hook
hero_n = int((d1 + 1.2) * FPS)
inputs += ["-i", g("drake_circle.png")]
ix += 1
fchains.append(
    f"[{ix-1}:v]scale=1600:-1,crop=1600:1600,zoompan=z='min(1+0.00035*on,1.30)':"
    f"x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':d={hero_n}:s=480x480:fps={FPS},format=rgba"
    f",setpts=PTS+{s1 + 0.3:.3f}/TB"
    f",fade=t=in:st={s1 + 0.3:.2f}:d=0.30:alpha=1"
    f",fade=t=out:st={s1 + d1 - 0.45:.2f}:d=0.40:alpha=1[hero]")
overlays.append(("[hero]", f"overlay=x='{ease(s1 + 0.3, 0.9, 1440, 700, back=True)}':y='170':"
                 f"enable='between(t,{s1:.2f},{s1 + d1 + 0.3:.2f})'"))
i = still(g("title_drake.png"), d1 + 1)
overlay(i, s1 + 1.6, s1 + d1, "90", ease(s1 + 1.6, 0.7, 480, 330), w=640)
sfx_events.append(("impact", s1 + 1.6))
i = still(g("title_vs.png"), d1 + 1)
overlay(i, s1 + 6.0, s1 + d1, ease(s1 + 6.0, 0.8, -600, 120, back=True), "500", w=420)

# SCEN 2: 20 women vs 1
i = still(g("card_20v1.png"), d2 + 1)
overlay(i, s2 + 0.4, s2 + d2, "90", ease(s2 + 0.4, 0.9, -320, 180, back=True), w=1000)
i = still(g("drake_circle.png"), d2 + 1)
overlay(i, s2 + 2.2, s2 + d2, ease(s2 + 2.2, 0.9, -520, 850, back=True), "390", w=320)

# SCEN 3: Pinkchyu
i = still(g("pink_circle.png"), d3 + 1)
overlay(i, s3 + 0.3, s3 + d3, ease(s3 + 0.3, 0.9, -560, 110, back=True), "140", w=470)
sfx_events.append(("impact", s3 + 0.3))
i = still(g("title_pink.png"), d3 + 1)
overlay(i, s3 + 2.0, s3 + d3, "640", ease(s3 + 2.0, 0.7, 460, 320), w=560)
i = still(g("card_mtg.png"), d3 + 1)
overlay(i, s3 + d3 - 6.5, s3 + d3, ease(s3 + d3 - 6.5, 0.8, 1400, 240), "540", w=780)

# SCEN 4: bark (cards bakom/kring klippet)
i = still(g("card_bark.png"), d4 + 1)
overlay(i, s4 + 0.6, s4 + 9.0, "140", ease(s4 + 0.6, 0.8, 150, 260, back=True), w=1000)
i = still(g("card_arf.png"), d4 + 1)
overlay(i, s4 + 9.0, s4 + 15.0, "290", ease(s4 + 9.0, 0.9, -340, 260, back=True), w=700)
i = still(g("card_nlu.png"), d4 + 1)
overlay(i, s4 + 15.0, s4 + d4, ease(s4 + 15.0, 0.8, 1400, 220), "300", w=860)

# SCEN 5: pris + Casa Loma
i = still(g("card_house.png"), d5 + 1)
overlay(i, s5 + 1.2, s5 + 11.0, ease(s5 + 1.2, 0.9, -620, 320, back=True), "240", w=640)
i = still(g("casa_card.png"), d5 + 1)
overlay(i, s5 + 10.5, s5 + d5, "350", ease(s5 + 10.5, 1.0, 900, 50), w=560)
i = still(g("card_casa.png"), d5 + 1)
overlay(i, s5 + 13.0, s5 + d5, ease(s5 + 13.0, 0.8, 1400, 620), "385", w=520)

# SCEN B1/B2
if b1:
    sb, db = b1["start"], b1["dur"]
    i = still(g("card_leash.png"), db + 1)
    overlay(i, sb + 0.5, sb + db * 0.55, ease(sb + 0.5, 0.8, -700, 200, back=True), "250", w=880)
    i = still(g("card_gothsplan.png"), db + 1)
    overlay(i, sb + db * 0.55, sb + db, ease(sb + db * 0.55, 0.9, 1400, 190), "240", w=820)
if b2:
    sc, dc = b2["start"], b2["dur"]
    i = still(g("card_dm.png"), dc + 1)
    overlay(i, sc + 0.5, sc + dc, ease(sc + 0.5, 0.8, 1400, 150), "280", w=940)
    i = still(g("pink_circle.png"), dc + 1)
    overlay(i, sc + 1.2, sc + dc, ease(sc + 1.2, 0.9, -520, 830, back=True), "400", w=330)

# SCEN 6: endcard
i = still(g("endcard.png"), d6 + 4.5)
overlay(i, s6 + 4.5, TOTAL - 0.6, "340", "230", w=600, fin=0.6, fout=1.5)

# ---------------- kamerablixtar ----------------
inputs += ["-f", "lavfi", "-t", f"{TOTAL:.2f}", "-i", f"color=c=white:s=1280x720:r={FPS}"]
ix += 1
flash_pts = [s2, s4, s5 + 10.5] + ([b1["start"]] if b1 else []) + [s6] + [c["t"] for c in CLIPS]
ch = f"[{ix-1}:v]format=rgba"
for p in flash_pts:
    ch += f",fade=t=in:st={p:.2f}:d=0.06:alpha=1,fade=t=out:st={p + 0.10:.2f}:d=0.18:alpha=1"
fchains.append(ch + "[wfl]")
overlays.append(("[wfl]", "overlay=0:0"))

# ================= LJUD =================
vo_idx = []
for lbl in ORDER:
    if lbl not in S: continue
    inputs += ["-i", os.path.join(AUDIO, f"{lbl}.wav")]
    vo_idx.append((lbl, ix)); ix += 1
for n, (lbl, aidx) in enumerate(vo_idx):
    ms = int(S[lbl]["start"] * 1000)
    fchains.append(f"[{aidx}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"adelay={ms}|{ms}[vn{n}]")

# drone med duckning under klipp (sankt musik => klipp-ljudet lyfter)
inputs += ["-f", "lavfi", "-t", f"{TOTAL:.2f}", "-i",
           "aevalsrc=exprs='0.10*sin(2*PI*49*t)+0.07*sin(2*PI*49.5*t)"
           "+0.05*sin(2*PI*98*t)+0.05*sin(2*PI*196.8*t)*(0.5+0.5*sin(2*PI*0.05*t))'"
           ":s=44100:d=" + f"{TOTAL:.2f}"]
mus = ix; ix += 1
duck = "+".join(f"between(t,{c['t'] - 0.2:.2f},{c['t'] + c['dur'] + 0.3:.2f})" for c in CLIPS)
fchains.append(f"[{mus}:a]lowpass=f=400,aformat=channel_layouts=stereo,"
               f"volume='if({duck},0.10,0.30)':eval=frame,"
               f"afade=t=in:st=0:d=3,afade=t=out:st={TOTAL - 6:.2f}:d=5.5[musv]")

# SFX: impacts + whooshes + risers (alla syntetiska, ingen copyright)
sfx_labels = []
for si, (typ, t) in enumerate(sfx_events):
    if t < 0.2: continue
    inputs += ["-f", "lavfi", "-t", "1.6", "-i",
               "aevalsrc=exprs='0.85*sin(2*PI*52*t)*exp(-5.5*t)+0.30*sin(2*PI*110*t)*exp(-8*t)':s=44100"]
    a = ix; ix += 1
    ms = int(max(t, 0) * 1000)
    fchains.append(f"[{a}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"volume=0.55,adelay={ms}|{ms}[sx{si}]")
    sfx_labels.append(f"[sx{si}]")
for si, t in enumerate(risers):
    inputs += ["-f", "lavfi", "-t", "2.4", "-i",
               "aevalsrc=exprs='0.16*sin(2*PI*(160+260*t)*t)+0.10*sin(2*PI*(90+40*t)*t)':s=44100"]
    a = ix; ix += 1
    ms = int(max(t - 2.4, 0) * 1000)
    fchains.append(f"[{a}:a]afade=t=in:st=0:d=2.2,aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"volume=0.5,adelay={ms}|{ms}[rs{si}]")
    sfx_labels.append(f"[rs{si}]")

mix_ins = "".join(f"[vn{n}]" for n in range(len(vo_idx))) + "".join(clip_audio) + \
          "[musv]" + "".join(sfx_labels)
n_in = len(vo_idx) + len(clip_audio) + 1 + len(sfx_labels)
fchains.append(f"{mix_ins}amix=inputs={n_in}:normalize=0,alimiter=limit=0.92[aout]")

# ---------------- klistra ihop ----------------
graph = ";".join(fchains)
prev = "[bg]"
for n, (lbl, ovexpr) in enumerate(overlays):
    nxt = f"[v{n}]"
    graph += f";{prev}{lbl}{ovexpr}{nxt}"
    prev = nxt
graph += (f";{prev}fade=t=in:st=0:d=0.8,fade=t=out:st={TOTAL - 1.4:.2f}:d=1.4,"
          f"subtitles={os.path.join(ROOT, 'captions.ass')},format=yuv420p[vout]")

open(os.path.join(ROOT, "scripts", "filtergraph.txt"), "w").write(graph)
print("renderar", round(TOTAL, 1), "s |", len(CLIPS), "klipp |", len(sfx_events), "SFX ...")
r = subprocess.run(["ffmpeg", "-y"] + inputs +
                   ["-filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
                    "-t", f"{TOTAL:.2f}", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "22", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", OUT], capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-4500:]); raise SystemExit(1)
print("KLART:", OUT, os.path.getsize(OUT) // 1024, "KB")
