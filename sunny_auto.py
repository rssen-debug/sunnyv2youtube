#!/usr/bin/env python3
"""
sunny_auto.py — AUTOMATISK DOKUMENTÄRSTUDIO (orchestrator).

Ett ämne:
    python sunny_auto.py --topic "MrBeast"

Helt autonomt:
    python sunny_auto.py --auto

Flowchart:
    TOPIC → RESEARCH → LLM(script+plan) → FACT-CHECK → FOOTAGE → VOICE →
    GRAPHICS → CAPTIONS → TIMELINE → RENDER(cinema/gfx/ffmpeg) → QC → FINAL MP4

LLM = hjärnan (creative director / researcher / editor-planner).
Python + gfx_kit + cinema + make_captions + make_video + verify_build = händerna.

Val:
  --topic "X"        ämne (text)
  --auto             hitta ämne själv (trends/news/Youtube)
  --duration 8m      mål-längd (hint till manus; voiceover styr)
  --language en      språk (en/sv/.. påverkar TTS-röst)
  --style sunnyv2    stilprofil (skrivs in i output-namn + look)
  --voice auto       TTS-röst (auto = en-GB-RyanNeural etc.)
  --no-llm           kör helt utan LLM-nyckel (deterministiskt manussyntes)
  --retries 3        max självläkningsförsök
  --max-clips 6      max nedladdade klipp
  --dry-run          research+plan+voice+grafik men INGEN dyr render
  --list             lista tillgängliga edge-tts-röster

Nycklar (valfritt): OPENAI_API_KEY / GROQ_API_KEY (eller SUNNY_LLM_URL+KEY).
Utan nyckel fungerar hela kedjan med built-in fallback-logik.
"""
import os, sys, json, re, datetime, subprocess, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

# ---------------------------------------------------------------- imports
from research import sources as RSRC
from research import trends as TRENDS
from engine import timeline as TLE
from engine import knowledge as KB
from engine import retry as RETRY
from agents import research_agent, story_agent, llm_client, script_agent
from agents import factcheck_agent, visual_agent, audio_agent, footage_agent
from agents import graphics_agent, qc_agent, thumbnail_agent, risk_agent
from agents import licensing, llm

ROOT = HERE
STYLES = {"sunnyv2": "DEFAULT"}

# ---------------------------------------------------------------- helpers
def log(n, msg, ok=None):
    mark = "" if ok is None else (" ✓" if ok else " ✗")
    print(f"[{n:02d}] {msg}{mark}", flush=True)
    sys.stdout.flush()

def slugify(s):
    s = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    return re.sub(r"\s+", "_", s)[:40] or "episode"

def parse_duration(v):
    v = (v or "8m").strip().lower()
    m = re.match(r"(\d+)\s*([sm])?", v)
    if not m:
        return 480
    n = int(m.group(1)); unit = m.group(2) or "m"
    return n * 60 if unit == "m" else n

LANG_VOICE = {
    "en": "en-GB-RyanNeural", "eng": "en-GB-RyanNeural",
    "en-gb": "en-GB-RyanNeural", "en-us": "en-US-AndrewNeural",
    "sv": "sv-SE-MattiasNeural", "swe": "sv-SE-MattiasNeural",
    "no": "nb-NO-FinnNeural", "da": "da-DK-JeppeNeural",
    "de": "de-DE-ConradNeural", "fr": "fr-FR-HenriNeural",
}

def _list_voices():
    try:
        import asyncio, edge_tts
        async def go():
            return await edge_tts.list_voices()
        vs = asyncio.run(go())
        for v in vs:
            if v["Locale"].startswith(("en", "sv", "no", "da")):
                print(f"{v['ShortName']:32s} {v['Locale']:10s} {v['Gender']}")
    except Exception as e:
        print("kunde inte lista röster:", e)

# ---------------------------------------------------------------- main
def main(argv):
    args = _parse(argv)

    if args["list"]:
        _list_voices()
        return 0

    force_no_llm = args["no_llm"]
    _saved_keys = {}
    if force_no_llm:  # stäng av ev. nycklar så hela kedjan går offline-vägen
        for k in ("OPENAI_API_KEY", "GROQ_API_KEY", "SUNNY_LLM_KEY"):
            if os.environ.get(k):
                _saved_keys[k] = os.environ[k]; del os.environ[k]

    # 0) ämne
    topic = args["topic"]
    if not topic and args["auto"]:
        log(0, "hittar ämnen ...")
        try:
            cands = TRENDS.discover_candidates(n=20)
            topic, score = TRENDS.pick_best(cands)
            print(f"     valt: “{topic}”  (story-score {score:.2f})")
        except Exception as e:
            print("     ämnesupptäckt misslyckades:", e)
            topic = None
    if not topic:
        print(__doc__); return 2

    slug = slugify(topic)
    style = args["style"] or "sunnyv2"
    look = STYLES.get(style, "DEFAULT")
    goal_dur = parse_duration(args["duration"])
    date_s = datetime.date.today().isoformat()
    out_rel = f"videos2026/{slug}_{style}_v1_{date_s}.mp4"
    proj = os.path.join(ROOT, "projects", slug)
    os.makedirs(proj, exist_ok=True)
    today = date_s

    print("=" * 48)
    print("SUNNY AUTO — topic:", topic, "| stil:", style,
          f"| mål: {goal_dur}s | LLM:", "av" if force_no_llm else ("på" if llm.is_available() else "av (ingen nyckel)"))
    print("=" * 48, flush=True)

    # 1) research
    log(1, "research (källor/claims) ...")
    research = research_agent.run(topic, proj)

    # 2) story
    log(2, "story-arkitekt (vinklar/hook) ...")
    story = story_agent.run(topic, research, proj)

    # 3) brain: production plan
    log(3, "LLM skriver manus + produktionsplan ...")
    plan = llm_client.plan(topic, research, goal_dur, no_llm=force_no_llm)

    # 4) script.json + fact-check (→ rewrite vid behov)
    log(4, "script.json + fact-check (krav: inga os­tödda påståenden) ...")
    script_agent.run(plan, proj)
    check_report, plan = factcheck_agent.run(
        plan, research, proj, rewrite_with_llm=(not force_no_llm))
    if not check_report.get("safe", False):
        print("     varning: fact-check flaggade block — se factcheck.json")

    # 5) visuals (bilder + bg)
    log(5, "visuell regissör (porträtt/bg via Wikimedia, fallback synth) ...")
    vis = visual_agent.run(topic, research, proj, slug)

    # 6) skriv script/script.txt (make_captions.py läser denna)
    _write_script_txt(plan)

    # 7) voice
    voice = args["voice"] or "auto"
    if voice == "auto":
        voice = LANG_VOICE.get((args["language"] or "en").lower(),
                               "en-GB-RyanNeural")
    log(7, f"voiceover (TTS {voice}) ...")
    audio_agent.run(plan, proj, voice=voice)

    # 8) timeline (audio-driven — runt VERKLIG röst-duration)
    log(8, "timeline byggs runt rösten ...")
    timeline = TLE.build_timeline(plan)
    print(f"     total: {timeline['total']:.1f}s, {len(timeline['segments'])} block")

    # 8b) production_plan.json (editorn: hela planen i en fil)
    from agents import edit_agent
    edit_agent.run(plan, timeline, check_report, proj)

    # 9) captions (kinetic v2 + topic-keywords)
    log(9, "captions (kinetic) ...")
    from engine import captions as CAPS
    CAPS.run(keywords=plan.get("keywords"))

    # 10) graphics (plan -> PNG via gfx_kit)
    log(10, "grafik (gfx_kit: glow/lower thirds/stat/tweet/timeline/chart) ...")
    beats, gfx_assets = graphics_agent.build_graphics(
        plan, slug, vis["people"])

    # 12) footage (sök -> ladda -> trimma -> normalisera)
    log(12, "footage (yt-dlp + RMS-ögonblick + trim) ...")
    # (nummer-gap medvetet: 11 = licenslagret, körs efter footage)
    clip_files = {"0": ""}
    try:
        clip_files = footage_agent.run(plan, slug, proj,
                                       max_clips=args["max_clips"])
    except Exception as e:
        print("     footage-fel:", str(e)[:200])

    # 11) licens/risk-lager
    log(11, "licens-/upphovsrättslager (asset-> tier/status) ...")
    all_assets = []
    all_assets += vis["assets"]
    all_assets += gfx_assets
    for fname in clip_files.values():
        if fname:
            all_assets.append({"type": "clip",
                               "file": os.path.join("assets", "clips", fname),
                               "source": "youtube", "license": "youtube"})
    manifest = licensing.manifest(proj, all_assets)

    # 13) kompilera EPISODES/*.json för make_video.py
    log(13, "kompilerar EPISODES/episode_*.json (make_video-maskineriet) ...")
    ep_path, cfg = graphics_agent.compile_episode(
        plan, timeline, slug, topic, beats, clip_files, out_rel,
        people_lookup=vis["people"], bg_rel=vis["bg"],
        keywords=plan.get("keywords"), style_look=look)

    out_abs = os.path.join(ROOT, out_rel)
    if args["dry_run"]:
        print("\n=== DRY-RUN KLART (ingen render) ===")
        print("episode-config:", os.path.relpath(ep_path, ROOT))
        print("planerat output:", out_rel, "| total", timeline["total"], "s")
        _write_proj_meta(proj, topic, timeline, plan, check_report, manifest, dry=True)
        return 0

    # 14) render (make_video.py) + retry-lag
    log(16, "render (make_video.py → gfx/cinema/captions → ffmpeg) ...")
    rlog = []

    def do_render():
        nonlocal cfg
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts",
                          "make_video.py"), os.path.relpath(ep_path, ROOT)],
                           capture_output=True, text=True, cwd=ROOT)
        if r.returncode != 0:
            raise RuntimeError((r.stdout + r.stderr)[-1500:])
        return (r.stdout + r.stderr)

    def diagnose_render(exc, attempt):
        msg = str(exc)
        m = re.findall(r"(assets/clips/[^\s']+)", msg)
        if m and attempt == 0:
            bad = {os.path.basename(x) for x in m}
            cfg["clips"] = [c for c in cfg.get("clips", [])
                            if c.get("file") not in bad]
            json.dump(cfg, open(ep_path, "w", encoding="utf-8"), indent=1)
            return "tog bort trasiga klipp: " + ", ".join(bad)
        return None

    try:
        RETRY.run_with_retry("render", do_render, max_retries=args["retries"],
                             diagnose_fix=diagnose_render, log=rlog)
    except Exception as e:
        print("     RENDER MISSLYCKADES efter retries:", str(e)[-800:])
        qc = {"pass": False, "issues": ["render misslyckades"],
              "measurements": {}, "critic": []}
        _finalize(proj, topic, timeline, plan, check_report, manifest, qc,
                  out_rel, date_s, ok=False)
        return 1

    # 15) QC (verify_build + grundkontroller + ev. LLM-kritik)
    log(18, "QC (verify_build.py + grundkontroller) ...")
    qc = qc_agent.run(out_abs, target_dur=timeline["total"],
                      timeline=timeline, project_dir=proj,
                      script_text=" ".join(b["voiceover"] for b in plan["blocks"]))
    if not qc["pass"]:
        print("     QC-fail:", "; ".join(qc["issues"])[:600])

    # 16) thumbnail + titel + metadata
    log(17, "thumbnail + titel + metadata ...")
    tm = thumbnail_agent.run(plan, topic, proj, out_abs)
    thumbnail_agent.write_metadata(tm, proj)

    # 17) risk
    log(19, "risk-scan (upphovsrätt/defamation/copycat) ...")
    risk = risk_agent.run(check_report, manifest, proj)

    # 18) kunskapsbas
    log(20, "kunskapsbas (learning-loop) ...")
    KB.record_run(slug, topic, {"title": tm["title"], "video": tm["video"],
                                "thumbnail": tm["thumbnail"],
                                "duration": timeline["total"], "qc": str(qc["pass"]),
                                "risk": risk["status"]})

    _finalize(proj, topic, timeline, plan, check_report, manifest, qc,
              out_rel, date_s, ok=True, risk=risk, meta=tm)
    return 0 if (qc["pass"] or args["allow_qc_fail"]) else 3

# ---------------------------------------------------------------- helpers 2
def _parse(argv):
    d = {"topic": None, "auto": False, "duration": "8m", "language": "en",
         "style": "sunnyv2", "voice": "auto", "no_llm": False, "retries": 3,
         "max_clips": 6, "dry_run": False, "list": False, "allow_qc_fail": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        def val():
            nonlocal i
            i += 1
            return argv[i] if i < len(argv) else None
        if a == "--topic": d["topic"] = val()
        elif a == "--auto": d["auto"] = True
        elif a == "--duration": d["duration"] = val() or "8m"
        elif a == "--language": d["language"] = val() or "en"
        elif a == "--style": d["style"] = val() or "sunnyv2"
        elif a == "--voice": d["voice"] = val() or "auto"
        elif a == "--no-llm": d["no_llm"] = True
        elif a == "--retries":
            d["retries"] = int(val() or 3)
        elif a == "--max-clips":
            d["max_clips"] = int(val() or 6)
        elif a == "--dry-run": d["dry_run"] = True
        elif a == "--list": d["list"] = True
        elif a == "--allow-qc-fail": d["allow_qc_fail"] = True
        elif a in ("-h", "--help"):
            print(__doc__); sys.exit(0)
        else:
            print("okänt argument:", a); print(__doc__); sys.exit(2)
        i += 1
    return d

def _write_script_txt(plan):
    with open(os.path.join(ROOT, "script", "script.txt"), "w",
              encoding="utf-8") as f:
        for b in plan.get("blocks", []):
            f.write(f"###{b['id']}\n")
            f.write((b.get("voiceover", "") or "").strip() + "\n\n")

def _write_proj_meta(proj, topic, timeline, plan, check_report, manifest, dry=False):
    with open(os.path.join(proj, "status.json"), "w", encoding="utf-8") as f:
        json.dump({"topic": topic, "dry": dry, "total": timeline["total"],
                   "factcheck_safe": check_report.get("safe", False),
                   "assets": len(manifest)}, f, ensure_ascii=False, indent=1)

def _finalize(proj, topic, timeline, plan, check_report, manifest, qc, out_rel,
              date_s, ok=True, risk=None, meta=None):
    print("\n" + "=" * 48)
    print("SUNNY AUTO COMPLETE" if ok else "SUNNY AUTO — INTE GODKÄND")
    print("=" * 48)
    print(f"Topic:       {topic}")
    print(f"Research:    {'✓' if len(json.load(open(os.path.join(proj,'research.json'))).get('facts',[])) else '✗'}")
    print(f"Script:      ✓ ({len(plan.get('blocks',[]))} block)")
    print(f"Fact check:  {'✓' if check_report.get('safe', False) else '✗ (se factcheck.json)'}")
    print(f"Voiceover:   ✓")
    print(f"Footage:     ✓ ({len([a for a in manifest if a.get('type')=='clip'])})")
    print(f"Graphics:    ✓ ({len([a for a in manifest if a.get('type')=='graphic'])})")
    print(f"Captions:    ✓")
    print(f"Timeline:    ✓ ({timeline['total']:.1f}s)")
    print(f"Render:      {'✓' if os.path.exists(os.path.join(ROOT, out_rel)) else '✗'}")
    print(f"QC:          {'✓ PASS' if qc.get('pass') else '✗ ' + '; '.join(qc.get('issues',[]))[:120]}")
    if risk:
        print(f"Risk:        {risk['status']} ({risk['severity']})")
    print(f"VIDEO:       {out_rel}")
    if meta and meta.get("thumbnail"):
        print(f"THUMBNAIL:   {meta['thumbnail']}")
        print(f"TITLE:       {meta['title']}")
    if risk and risk["status"] == "HOLD":
        print("\n→ HÅLL INNE: risk-scan kräver mänsklig granskning före publicering.")
    if not qc.get("pass"):
        print("\n→ QC misslyckades efter retries. Åtgärda enligt qc.json och kör om.")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
