#!/usr/bin/env python3
"""make_video.py — GENERISK EPISODE-MASKIN ("bom klart"-kommandot).

Användning (nästa agent):
  1) Skapa EPISODES/episode_<topic>.json (kopiera episode_drake_poc.json som mall)
  2) Skapa TTS: add_voice -> generate_speech per block -> audio/<ID>.wav (se PIPELINE.md steg 5)
  3) Leta assets: image_search + yt-dlp-klipp (PIPELINE.md steg 3/6) -> assets/src/, assets/clips/
  4) Kör:  python3 scripts/make_video.py EPISODES/episode_<topic>.json
  5) Krav: python3 scripts/verify_build.py <utdata>   (MÅSTE PASS, se MANDATE.md)

Maskinen sköter själv: GFX-bygge (glow-titlar, lower thirds, tweets, stats),
timeline ur wav-längder, kinetic captions (keyword-highlight), beats med easing,
klipp med ljud + duckning, impacts/whooshes/risers, blixtar, cinematic-stack
(grade+grain+bloom+letterbox+HUD+vignette+particles), 90 BPM-beatmusik, verify.
"""
import os, sys, json, glob, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from cinema import (ease, ss, drift, GRAIN, letterbox, bloom_chain, MUSIC_BEAT,
                    SFX_IMPACT, SFX_WHOOSH, SFX_RISER, LOOKS)
import gfx_kit as GK
from make_captions import build_events, ts, HEADER, wav_dur, load_keywords
from sfx_bed import make_bed
from PIL import Image, ImageDraw

GFX = os.path.join(ROOT, "assets", "gfx")
CLIPDIR = os.path.join(ROOT, "assets", "clips")
FPS = 30
W, H = 1280, 720

# ---------------- helpers ----------------
def ensure_ffmpeg():
    if subprocess.run(["bash", "-c", "command -v ffmpeg"]).returncode != 0:
        subprocess.run(["pip", "install", "-q", "imageio-ffmpeg"])
        exe = subprocess.run(["python3", "-c",
            "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
            capture_output=True, text=True).stdout.strip()
        subprocess.run(["bash", "-c", f"ln -sf {exe} /usr/local/bin/ffmpeg"])

def big_card(out_name, main, sub="", accent=(232, 34, 46, 255), px=96, pad=70):
    """sunnyv2-textkort: stor vit text + accent-sub, svart kontur."""
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fm, fs = GK.F(px, "anton"), GK.F(max(px // 2, 28), "bebas")
    mw, mh = GK._tsize(d0, main, fm, 8)
    sw, sh = (GK._tsize(d0, sub, fs, 5) if sub else (0, 0))
    c = Image.new("RGBA", (max(mw, sw) + pad * 2, mh + (sh + 26 if sub else 0) + pad * 2), (0, 0, 0, 0))
    x = (c.width - mw) // 2
    d1 = ImageDraw.Draw(c)
    d1.text((x, pad), main, font=fm, fill=(255, 255, 255, 255), stroke_width=8,
            stroke_fill=(8, 8, 10, 255))
    if sub:
        d1.text(((c.width - sw) // 2, pad + mh + 20), sub, font=fs, fill=accent,
                stroke_width=5, stroke_fill=(8, 8, 10, 255))
    c.save(os.path.join(GFX, out_name)); return out_name

def g(n): return os.path.join(GFX, n)

def resolve_t(v, block_start, block_end):
    """'end-5' / float / 'mid+3' relativt block."""
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip()
    if s == "end": return block_end
    if s.startswith("end-"): return block_end - float(s[4:])
    if s.startswith("mid+"): return (block_start + block_end) / 2 + float(s[4:])
    return float(s)

ANIMS = ("slam", "slideR", "slideL", "rise", "pop", "drift")

# ---------------- main ----------------
def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "EPISODES/episode_drake_poc.json"
    cfg_path = cfg_path if os.path.isabs(cfg_path) else os.path.join(ROOT, cfg_path)
    C = json.load(open(cfg_path))
    ensure_ffmpeg()
    print("EPISODE:", C["topic"])

    # 1) manus + audio -> timeline
    audio_dir = os.path.join(ROOT, C.get("audio_dir", "audio"))
    blocks = C["blocks"]
    GAP = C.get("gap", 0.7)
    t, segs, missing = 0.0, [], []
    for b in blocks:
        p = os.path.join(audio_dir, f"{b['id']}.wav")
        if not os.path.exists(p):
            missing.append(b["id"]); continue
        d = wav_dur(p)
        segs.append({"id": b["id"], "text": b["text"], "start": round(t, 3), "dur": round(d, 3)})
        t += d + GAP
    if missing:
        print("SAKNAS TTS för:", missing, "\n-> kör add_voice + generate_speech först (PIPELINE.md steg 5)")
        sys.exit(2)
    TOTAL = t - GAP + C.get("tail", 2.5)
    BS = {s["id"]: (s["start"], s["start"] + s["dur"]) for s in segs}
    print("timeline:", {k: round(v[0], 1) for k, v in BS.items()}, "| total", round(TOTAL, 1), "s")

    # 2) GFX-bygge från config
    generated = []
    for gl in C.get("glows", []):
        n = f"cfg_glow_{len(generated)}.png"
        GK.glow_title(n, gl["text"], gl.get("px", 130), glow=tuple(gl.get("glow", [232, 34, 46, 150])))
        gl["_asset"] = n; generated.append(n)
    for lt in C.get("people", []):
        n = f"cfg_lt_{lt['key']}.png"
        GK.lower_third(n, lt["name"], lt.get("sub", ""), tuple(lt.get("accent", [232, 34, 46, 255])))
        lt["_asset"] = n; generated.append(n)
    tw = C.get("tweet")
    if tw:
        tw["_asset"] = "cfg_tweet.png"
        GK.tweet_ui("cfg_tweet.png", tw["name"], tw["handle"], tw["body"], tw["meta"],
                    tw["likes"], tw.get("avatar", ""))
    for si, st in enumerate(C.get("stats", [])):
        n = f"cfg_stat_{si}.png"
        GK.stat_card(n, st["big"], st["label"], tuple(st.get("accent", [232, 34, 46, 255])))
        st["_asset"] = n; generated.append(n)
    for cd in C.get("cards", []):
        n = f"cfg_card_{cd['id']}.png"
        big_card(n, cd["main"], cd.get("sub", ""), tuple(cd.get("accent", [232, 34, 46, 255])))
        cd["_asset"] = n; generated.append(n)
    for p in C.get("people", []):
        n = f"cfg_circle_{p['key']}.png"
        if p.get("img") and os.path.exists(os.path.join(ROOT, p["img"])):
            GK.circle_portrait(os.path.join(ROOT, p["img"]), n,
                               tuple(p.get("ring", [255, 255, 255, 255])))
            p["_circle"] = n; generated.append(n)

    # 3) captions (kinetic v2)
    kw = set(C.get("keywords", []))
    ev = build_events(segs, kw)
    cap_path = os.path.join(ROOT, "episode_captions.ass")
    open(cap_path, "w", encoding="utf-8").write(
        HEADER + "\n".join(f"Dialogue: 0,{ts(a)},{ts(b)},PopBig,,0,0,0,,{txt}" for a, b, txt in ev) + "\n")
    print("captions:", len(ev), "events")

    # ============================================================
    # 4) SEGMENTERAD RENDER (studiomode): liten graf per block = aldrig hanger
    #    base -> segment/block -> audio -> concat + cinematic final pass
    # ============================================================
    Wn, Hn = W, H
    CRFI = "18"          # intermediate-kvalitet
    TMP = os.path.join(ROOT, "seg"); os.makedirs(TMP, exist_ok=True)

    def run(cmd, tag):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            errlines = [l for l in r.stderr.splitlines() if any(k in l.lower() for k in ("error", "invalid", "no such", "cannot", "failed"))]
            print(f"RENDER-FEL ({tag}):")
            for l in errlines[-8:]: print("   ", l)
            print("    ...sista:", r.stderr[-300:])
            open(os.path.join(TMP, f"failed_{tag.replace(' ','_')}.cmd"), "w").write(" ".join(cmd))
            sys.exit(1)

    # --- normalisera beats/clips till globala events ---
    events = []   # overlays
    clipvs = []   # klipp-video events
    clipau = []   # klipp-ljud (global, till audiopass)
    flash_pts = []
    sfx_events = []
    for bt in C.get("beats", []):
        b0, b1 = BS[bt["block"]]
        at = bt.get("at", 0)
        T0 = (b0 + float(at)) if isinstance(at, (int, float)) else resolve_t(at, b0, b1)
        until = bt.get("until", None)
        if isinstance(until, str):      T1 = resolve_t(until, b0, b1)
        elif until is not None:         T1 = b0 + float(until)
        else:                           T1 = T0 + float(bt.get("dur", 5))
        events.append({"T0": T0, "T1": T1, "asset": g(bt["asset"]), "w": bt.get("w", 700),
                       "x": bt.get("x", (Wn - bt.get("w", 700)) // 2),
                       "y": bt.get("y", (Hn - 200) // 2), "anim": bt.get("anim", "pop"),
                       "impact": bt.get("impact", False), "reveal": bt.get("reveal", False)})
    for ci, cl in enumerate(C.get("clips", [])):
        b0, b1 = BS[cl["block"]]
        T0 = (b0 + float(cl["at"])) if isinstance(cl["at"], (int, float)) else resolve_t(cl["at"], b0, b1)
        T1 = T0 + float(cl["dur"])
        clipvs.append({"T0": T0, "T1": T1, "file": os.path.join(CLIPDIR, cl["file"]),
                       "cut": float(cl["cut"]), "w": cl.get("w", 920), "y": cl.get("y", 80)})
        clipau.append({"T0": T0, "dur": float(cl["dur"]), "vol": cl.get("vol", 1.0),
                       "file": os.path.join(CLIPDIR, cl["file"])})
    for e in events:
        if e["impact"]: flash_pts.append(e["T0"]); sfx_events.append(("impact", e["T0"], 0.55))
        if e["anim"] in ("slam", "slideL", "slideR"): sfx_events.append(("whoosh", e["T0"] - 0.45, 0.5))
        if e["reveal"]: sfx_events.append(("riser", e["T0"] - 2.4, 0.5))
    for cv in clipvs:
        flash_pts.append(cv["T0"]); sfx_events.append(("impact", cv["T0"], 0.5))
        sfx_events.append(("whoosh", cv["T0"] - 0.45, 0.5))

    # --- PASS 1: base (bg-zoompan + partiklar + vinjett + HUD + lightleak) ---
    base = os.path.join(TMP, "base.mp4")
    bg = os.path.join(ROOT, C.get("bg", "assets/src/bg_ai.png"))
    inputs = ["-i", bg]
    for asset, fin in [("particles.png", 0.05), ("vignette.png", 0.6), ("hud.png", 1.0), ("lightleak.png", 1.4)]:
        inputs += ["-loop", "1", "-t", f"{TOTAL:.2f}", "-i", g(asset)]
    fch = [f"[0:v]scale=2560:1440,zoompan=z='min(1+0.00030*on,1.22)':"
           f"x='iw/2-(iw/zoom)/2+34*sin(on/{FPS*7})':y='ih/2-(ih/zoom)/2':"
           f"d={int(TOTAL*FPS)}:s={Wn}x{Hn}:fps={FPS}[bg0]",
           "[1:v]format=rgba,setpts=PTS/TB[par]",
           "[2:v]format=rgba,setpts=PTS/TB[vig]",
           f"[3:v]format=rgba,fade=t=in:st=0.2:d=1.0:alpha=1,setpts=PTS/TB[hud]",
           f"[4:v]format=rgba,fade=t=in:st=0.3:d=1.4:alpha=1,setpts=PTS/TB[lk]"]
    fch.append("[bg0][par]overlay=x=0:y='mod(t*18,760)-60'[s1]")
    fch.append("[s1][vig]overlay=0:0[s2]")
    fch.append("[s2][hud]overlay=0:0[s3]")
    fch.append("[s3][lk]overlay=0:0,format=yuv420p[vout]")
    print("PASS 1/4: base", round(TOTAL), "s ...")
    run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fch), "-map", "[vout]",
         "-t", f"{TOTAL:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", CRFI,
         "-pix_fmt", "yuv420p", base], "base")

    # --- PASS 2: ett litet segment per block ---
    ids = [b["id"] for b in blocks if b["id"] in BS]
    wins = []
    for i, bid in enumerate(ids):
        b0, b1 = BS[bid]
        w0 = b0 if i == 0 else b0
        w1 = BS[ids[i + 1]][0] if i + 1 < len(ids) else TOTAL
        wins.append((bid, w0, w1))
    seg_files = []
    for si, (bid, w0, w1) in enumerate(wins):
        seg = os.path.join(TMP, f"seg_{si}.mp4")
        inputs = ["-ss", f"{w0:.3f}", "-t", f"{w1 - w0:.3f}", "-i", base]
        fch = ["[0:v]format=rgba[base]"]
        prev = "[base]"; n = 0
        def add_ov(inp_chain, T0g, T1g, xexpr, yexpr, wdt=None, tag=""):
            nonlocal prev, n, inputs
            n += 1
            hold = (min(T1g, w1) - T0g) + 2
            inputs += ["-loop", "1", "-t", f"{hold:.2f}", "-i", inp_chain]
            lab = f"ov{n}"
            ch = (f"[{ix_count[0]}:v]format=rgba" + (f",scale={wdt}:-1" if wdt else ""))
            shift = T0g - w0
            if shift > 0: ch += f",setpts=PTS+{shift:.3f}/TB"
            fin = 0.12 if tag == "pop" else 0.2
            ch += (f",fade=t=in:st={max(shift,0):.2f}:d={fin}:alpha=1"
                   f",fade=t=out:st={max(T1g - w0 - 0.22, shift):.2f}:d=0.22:alpha=1[{lab}]")
            fch.append(ch)
            fch.append(f"{prev}[{lab}]overlay=x='{xexpr}':y='{yexpr}':"
                       f"enable='between(t,{max(T0g - w0, 0):.2f},{T1g - w0:.2f})'[s{n}]")
            prev = f"[s{n}]"
        ix_count = [1]
        # (ix_count hanteras enklast: rak raecknad input-index)
        def next_idx():
            ix_count[0] += 1
            return ix_count[0] - 1
        # byggr om add_ov med korrekt indexhantering:
        for e in [e for e in events if e["T0"] < w1 - 0.05 and e["T1"] > w0 + 0.05]:
            idx = next_idx()
            hold = (min(e["T1"], w1) - e["T0"]) + 2
            inputs += ["-loop", "1", "-t", f"{hold:.2f}", "-i", e["asset"]]
            n += 1
            lab = f"ov{n}"; shift = e["T0"] - w0
            ch = f"[{idx}:v]format=rgba" + (f",scale={e['w']}:-1" if e["w"] else "")
            if shift > 0: ch += f",setpts=PTS+{shift:.3f}/TB"
            fin = 0.12 if e["anim"] == "pop" else 0.2
            ch += (f",fade=t=in:st={max(shift,0):.2f}:d={fin}:alpha=1"
                   f",fade=t=out:st={max(e['T1'] - w0 - 0.22, shift):.2f}:d=0.22:alpha=1[{lab}]")
            fch.append(ch)
            if e["anim"] == "slam" or e["anim"] == "slideL":
                xe = ease(shift, 0.8, -(e["w"] + 320), e["x"], back=True); ye = str(e["y"])
            elif e["anim"] == "slideR":
                xe = ease(shift, 0.8, Wn + 320, e["x"], back=True); ye = str(e["y"])
            elif e["anim"] == "rise":
                xe = str(e["x"]); ye = ease(shift, 0.9, 860, e["y"])
            elif e["anim"] == "drift":
                xe = f"{e['x']}+{drift(shift, 5, 16)}"; ye = f"{e['y']}+6*sin(2*PI*t/4.5)"
            else:
                xe, ye = str(e["x"]), str(e["y"])
            fch.append(f"{prev}[{lab}]overlay=x='{xe}':y='{ye}':"
                       f"enable='between(t,{max(shift, 0):.2f},{e['T1'] - w0:.2f})'[s{n}]")
            prev = f"[s{n}]"
        for cv in [cv for cv in clipvs if cv["T0"] < w1 - 0.05 and cv["T1"] > w0 + 0.05]:
            idx = next_idx()
            inputs += ["-ss", f"{cv['cut']:.2f}", "-t", f"{cv['T1'] - cv['T0']:.2f}", "-i", cv["file"]]
            n += 1
            lab = f"ov{n}"; shift = cv["T0"] - w0
            fch.append(f"[{idx}:v]scale={cv['w']}:-1,setsar=1,format=rgba,"
                       f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.35:width=3,"
                       f"setpts=PTS+{shift:.3f}/TB,"
                       f"fade=t=in:st={max(shift,0):.2f}:d=0.14:alpha=1,"
                       f"fade=t=out:st={max(cv['T1'] - w0 - 0.14, shift):.2f}:d=0.14:alpha=1[{lab}]")
            fch.append(f"{prev}[{lab}]overlay=x='(W-w)/2':y='{cv['y']}':"
                       f"enable='between(t,{max(shift,0):.2f},{cv['T1'] - w0:.2f})'[s{n}]")
            prev = f"[s{n}]"
        if C.get("endcard") and si == len(wins) - 1:
            ec = C["endcard"]; ecn = "cfg_endcard.png"
            GK.glow_title(ecn, ec["text"], 170, glow=tuple(ec.get("glow", [60, 220, 120, 140])))
            idx = next_idx()
            inputs += ["-loop", "1", "-t", "4", "-i", g(ecn)]
            n += 1; lab = f"ov{n}"; shift = TOTAL - 2.2 - w0
            fch.append(f"[{idx}:v]format=rgba,scale=620:-1,setpts=PTS+{shift:.3f}/TB,"
                       f"fade=t=in:st={max(shift,0):.2f}:d=0.3:alpha=1,"
                       f"fade=t=out:st={max(w1 - w0 - 0.7, shift):.2f}:d=0.6:alpha=1[{lab}]")
            fch.append(f"{prev}[{lab}]overlay=x='{(Wn-620)//2}':y='250':"
                       f"enable='between(t,{max(shift,0):.2f},{w1 - w0:.2f})'[s{n}]")
            prev = f"[s{n}]"
        fch[-1] = fch[-1][:fch[-1].rfind("[")] + ",format=yuv420p[vout]"   # label -> format+ut
        print(f"PASS 2/4: segment {si+1}/{len(wins)} ({bid}) ...")
        run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fch), "-map", "[vout]",
             "-t", f"{w1 - w0:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", CRFI,
             "-pix_fmt", "yuv420p", seg], f"seg {bid}")
        seg_files.append(seg)

    # --- PASS 3: ljud (VO + klipp + sfx-bed + musik) ---
    print("PASS 3/4: ljudmix ...")
    bed_path = os.path.join(ROOT, "episode_sfx.wav")
    make_bed([(k, tt, v) for k, tt, v in sfx_events], TOTAL, bed_path)
    inputs = []; fch = []; amix = []
    ai = 0
    for s_ in segs:
        inputs += ["-i", os.path.join(audio_dir, f"{s_['id']}.wav")]
        ms = int(s_["start"] * 1000)
        fch.append(f"[{ai}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"adelay={ms}|{ms}[v_{s_['id']}]"); amix.append(f"[v_{s_['id']}]"); ai += 1
    for ca in clipau:
        inputs += ["-i", ca["file"]]
        fch.append(f"[{ai}:a]atrim=0:{ca['dur']:.2f},aformat=sample_rates=44100:channel_layouts=stereo,"
                   f"volume={ca['vol']:.2f},adelay={int(ca['T0']*1000)}|{int(ca['T0']*1000)}[cc{len(amix)}]")
        amix.append(f"[cc{len(amix)}]"); ai += 1
    duck = "+".join(f"between(t,{cv['T0']-0.2:.2f},{cv['T1']+0.3:.2f})" for cv in clipvs) or "0"
    inputs += ["-i", bed_path]
    fch.append(f"[{ai}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.0[bed]")
    amix.append("[bed]"); ai += 1
    inputs += ["-f", "lavfi", "-t", f"{TOTAL:.2f}", "-i", MUSIC_BEAT + f":d={TOTAL:.2f}"]
    fch.append(f"[{ai}:a]lowpass=f=500,aformat=channel_layouts=stereo,"
               f"volume='if({duck},0.10,0.32)':eval=frame,"
               f"afade=t=in:st=0:d=1.5,afade=t=out:st={TOTAL-4:.2f}:d=3.5[mus]")
    amix.append("[mus]")
    audio_m4a = os.path.join(TMP, "audio.m4a")
    fch.append("".join(amix) + f"amix=inputs={len(amix)}:normalize=0,alimiter=limit=0.92[aout]")
    run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fch), "-map", "[aout]",
         "-t", f"{TOTAL:.2f}", "-c:a", "aac", "-b:a", "192k", audio_m4a], "audio")

    # --- PASS 4: concat + blixtar + cinematic + captions ---
    print("PASS 4/4: concat + cinematic + captions ...")
    lst = os.path.join(TMP, "list.txt")
    open(lst, "w").write("".join(f"file '{f}'\n" for f in seg_files))
    inputs = ["-f", "concat", "-safe", "0", "-i", lst, "-i", audio_m4a,
              "-f", "lavfi", "-t", f"{TOTAL:.2f}", "-i", f"color=c=white:s={Wn}x{Hn}:r={FPS}"]
    fch = [f"[2:v]format=rgba" + "".join(
        f",fade=t=in:st={p:.2f}:d=0.06:alpha=1,fade=t=out:st={p+0.10:.2f}:d=0.18:alpha=1"
        for p in flash_pts) + "[wfl]",
        "[0:v][wfl]overlay=0:0[fw]",
        "[fw]fade=t=in:st=0:d=0.5,format=rgba[preg]",
        "[preg]split=2[pl][pr];[pr]gblur=sigma=11[pg]",
        "[pl][pg]blend=all_mode=screen:all_opacity=0.22[pbl]",
        f"[pbl]{LOOKS[C.get('look','DEFAULT')]},{GRAIN},{letterbox()},"
        f"subtitles={cap_path}:fontsdir={os.path.join(ROOT,'assets','fonts')},format=yuv420p[vout]"]
    out = os.path.join(ROOT, C["out"])
    run(["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fch),
         "-map", "[vout]", "-map", "1:a", "-t", f"{TOTAL:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], "final")

    print("KLART:", out, os.path.getsize(out) // 1024, "KB")
    v = subprocess.run([sys.executable, os.path.join(HERE, "verify_build.py"), out, str(round(TOTAL))])
    sys.exit(v.returncode)

if __name__ == "__main__":
    main()
