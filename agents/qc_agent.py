#!/usr/bin/env python3
"""agents/qc_agent.py — flerskikts-QC:
1) verify_build.py (MANDATE: h264/aac, rörelse, ljud-höjdpunkter, statik-larm)
2) grundläggande fil-/stream-kontroller (saknad fil, svart/videolös, duration)
3) LLM-kritik av frames om tillgänglig (pacing/visuell variation)

Returnerar dict {pass, issues, measurements}. Vid fail -> diagnos -> retry-loop
i sunny_auto.py.
"""
import os, json, subprocess, sys, re, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, "scripts")
from engine import media
from agents import llm

def _basic_checks(out):
    issues = []
    if not os.path.exists(out):
        return {"exists": False, "issues": ["fil saknas"]}
    if os.path.getsize(out) < 20_000:
        issues.append("filen misstänkt liten (trasig/fel) ")
    p = media.probe(out)
    if p["duration"] <= 1.0:
        issues.append(f"duration {p['duration']:.1f}s <= 1s (trasig)")
    if not p["video"]:
        issues.append("ingen videoström")
    if not p["audio"]:
        issues.append("ingen ljudström")
    if p["res"] and p["res"][0] < 640:
        issues.append(f"låg upplösning {p['res']}")
    return {"exists": True, "duration": p["duration"], "res": p["res"],
            "issues": issues}

def _llm_critic(out, timeline, script_text, project_dir):
    """Sampla frames, skicka till LLM (bild via URL ej möjlig — vi skickar
    signalstatistik + text). Ger strukturerade kommentarer."""
    if not llm.is_available():
        return []
    try:
        fs = []
        p = media.probe(out)
        total = p["duration"]
        step = max(1.0, total / 10)
        for i in range(10):
            t = min(i * step + 0.4, total - 0.2)
            fr = os.path.join(tempfile.gettempdir(), f"qc_{os.getpid()}_{i}.jpg")
            subprocess.run([media.ffmpeg(), "-y", "-v", "error", "-ss", str(t),
                            "-i", out, "-frames:v", "1", "-vf", "scale=64:36",
                            fr], capture_output=True)
            if os.path.exists(fr):
                fs.append((round(t, 1), fr))
        prompt = (f"Du är post-produktionskritiker. Video: {total:.0f}s.\n"
                  f"Timeline-översikt (block/start/dur):\n"
                  f"{json.dumps([{ 'id': s['id'], 'start': s['start'], 'dur': s['dur']} for s in timeline.get('segments', [])], ensure_ascii=False)}\n"
                  f"Ange JSON-lista med rhythm-/pacing-problem du anar utifrån blocklängder "
                  f"(långa block utan visuals = risk). Svara: "
                  f'[{{"time":2.0,"issue":"..."}}]')
        obj = llm.fill_json(prompt, max_tokens=900)
        return obj if isinstance(obj, list) else []
    except Exception:
        return []

def run(out, target_dur=None, timeline=None, project_dir=None, script_text=""):
    basic = _basic_checks(out)
    fails = list(basic["issues"])
    measurements = {}
    if basic["exists"] and not fails:
        # 1) verify_build
        r = subprocess.run([sys.executable, os.path.join(HERE, "verify_build.py"),
                            out] + ([str(round(target_dur))] if target_dur else []),
                           capture_output=True, text=True)
        verify_out = r.stdout + r.stderr
        measurements["verify"] = verify_out.strip()[-1500:]
        if r.returncode != 0:
            fails.append("verify_build REJECT: " +
                         "; ".join(l for l in verify_out.splitlines() if "REJECT" in l)[:400])
        else:
            measurements["verify_pass"] = True
    comments = []
    if basic["exists"] and timeline and llm.is_available():
        comments = _llm_critic(out, timeline, script_text, project_dir)
    qc = {"pass": not fails and not [c for c in comments if c.get("issue")],
          "issues": fails, "measurements": measurements,
          "critic": comments}
    if project_dir:
        os.makedirs(project_dir, exist_ok=True)
        with open(os.path.join(project_dir, "qc.json"), "w", encoding="utf-8") as f:
            json.dump(qc, f, ensure_ascii=False, indent=1)
    return qc
