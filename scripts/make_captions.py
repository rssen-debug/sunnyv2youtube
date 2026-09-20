#!/usr/bin/env python3
"""Läser script.txt (###A1-block) + audio/*.wav -> räknar timeline (timings.json)
och genererar word-by-word pop-captions (captions.ass, sunnyv2-stil).

Timing-modell: per block fördelas tal-durationen proportionellt mot ordlängd
(2+tecken). Skarp exakt syncing kräver Whisper; se README.
"""
import os, json, wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "script", "script.txt")
AUDIO = os.path.join(ROOT, "audio")
GAP = 0.7           # tystnad mellan VO-block (sek)
TAIL = 0.5          # extra luft efter sista blocket
LEAD = 0.10         # captions startar så här långt in i blocket

def wav_dur(p):
    with wave.open(p, "rb") as w:
        return w.getnframes() / w.getframerate()

def main():
    blocks, cur = [], None
    for line in open(SCRIPT, encoding="utf-8"):
        line = line.strip()
        if line.startswith("###"):
            cur = {"id": line[3:].strip(), "text": ""}
            blocks.append(cur)
        elif line and cur is not None:
            cur["text"] += (" " if cur["text"] else "") + line

    t = 0.0
    segs = []
    for b in blocks:
        p = os.path.join(AUDIO, f"{b['id']}.wav")
        d = wav_dur(p)
        segs.append({"id": b["id"], "text": b["text"], "start": round(t, 3), "dur": round(d, 3)})
        t += d + GAP
    total = t - GAP + TAIL
    json.dump({"segments": segs, "total": round(total, 3), "fps": 30},
              open(os.path.join(ROOT, "timings.json"), "w"), indent=1)
    print("total video:", round(total, 2), "s")

    # ---- ASS captions ----
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,DejaVu Sans,58,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,92,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def ts(x):
        h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    ev = []
    for s in segs:
        words = s["text"].split()
        weights = [len(w) + 2 for w in words]
        t0 = s["start"] + LEAD
        span = s["dur"] - LEAD - 0.15
        # ord-tider
        wt, acc = [], t0
        for w, ww in zip(words, weights):
            d = span * ww / sum(weights)
            wt.append((w, acc, acc + d)); acc += d
        # grupper om <=3 ord / <=16 tecken
        group, glen = [], 0
        for item in wt:
            group.append(item); glen += len(item[0]) + 1
            if len(group) >= 3 or glen >= 16 or item is wt[-1]:
                ev.append((group[0][1], group[-1][2], " ".join(g[0] for g in group)))
                group, glen = [], 0

    lines = []
    for a, b, txt in ev:
        fx = r"{\fscx62\fscy62\t(0,70,\fscx100\fscy100)\fad(35,45)}"
        lines.append(f"Dialogue: 0,{ts(a)},{ts(b)},Pop,,0,0,0,,{fx}{txt}")
    open(os.path.join(ROOT, "captions.ass"), "w", encoding="utf-8").write(header + "\n".join(lines) + "\n")
    print("captions.ass:", len(ev), "events")

if __name__ == "__main__":
    main()
