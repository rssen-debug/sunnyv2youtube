#!/usr/bin/env python3
"""
sunny_auto.py — AUTOMATISK DOKUMENTÄRSTUDIO (orchestrator).

Ett ämne:
    python sunny_auto.py --topic "MrBeast"

Helt autonomt:
    python sunny_auto.py --auto

Pipeline:
    TOPIC(discovery+scoring) → RESEARCH → STORY/HOOK → LLM MANUS+PLAN →
    FACT-CHECK → VISUALS → VOICE → TIMELINE(audio-driven) → PACING →
    CAPTIONS → GRAPHICS → FOOTAGE → LICENS → RENDER → QC → THUMBNAIL →
    TITLE → RISK → METADATA → (upload, optional)

LLM = hjärnan (creative director / researcher / editor-planner / QC-kritiker).
Python + gfx_kit + cinema + make_captions + make_video + verify_build = händerna.

Val:
  --topic "X"        ämne (text)
  --auto             hitta ämne själv (ranking med story-potential)
  --duration 8m      mål-längd (hint; voiceover styr)
  --language en      språk (en/sv/no/da/de/fr ...)
  --style sunnyv2    stilprofil (look i cinema.py)
  --voice auto       TTS-röst (auto = en-GB-RyanNeural); --list visar röster
  --no-llm           kör utan LLM-nyckel (deterministiskt manussyntes)
  --retries 3        max självläkningsförsök
  --max-clips 6      max nedladdade klipp
  --dry-run          research+plan+voice+grafik men INGEN render
  --list             lista edge-tts-röster/voiceprofiler
  --upload           ladda upp till YouTube (kräver YT_CLIENT_SECRETS, PRIVAT)
  --auto-publish     (med --upload) publicera direkt
  --ingest-analytics <json>   matning av CTR/AVD/retention för en slug
  --allow-qc-fail    fortsätt trots QC-fail (för demo)

Nycklar (valfritt): OPENAI_API_KEY / GROQ_API_KEY (eller SUNNY_LLM_URL+KEY).
Utan nyckel fungerar hela kedjan med built-in fallback-logik.
"""
import os, sys, json, re, datetime, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

# ---------------------------------------------------------------- imports
from research import sources as RSRC
from engine import timeline as TLE
from engine import knowledge as KB
from engine import retry as RETRY
from engine import pacing as PACING
from agents import research_agent, story_agent, llm_client, script_agent
from agents import factcheck_agent, visual_agent, audio_agent, footage_agent
from agents import graphics_agent, qc_agent, thumbnail_agent, risk_agent
from agents import licensing, llm, topic_agent, title_agent, upload_agent

ROOT = HERE
STYLES = {"sunnyv2": "DEFAULT"}

# ---------------------------------------------------------------- helpers
def log(n, msg, ok=None):
    mark = "" if ok is None else (" ✓" if ok else " ✗")
    print(f"[{n:02d}] {msg}{mark}", flush=True)

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
        vs = asyncio.run(edge_tts.list_voices())
        for v in vs:
            if v["Locale"].startswith(("en", "sv", "no", "da")):
                print(f"{v['ShortName']:34s} {v['Locale']:8s} {v['Gender']}")
    except Exception as e:
        print("kunde inte lista röster:", e)

# ---------------------------------------------------------------- main
def main(argv):
    args = _parse(argv)

    if args["list"]:
        _list_voices()
        return 0

    if args["ingest_analytics"]:
        return _do_ingest(args["ingest_analytics"])

    force_no_llm = args["no_llm"]
    _saved_keys = {}
    if force_no_llm:  # stäng av ev. nycklar -> offline-vägen
        for k in ("OPENAI_API_KEY", "GROQ_API_KEY", "SUNNY_LLM_KEY"):
            if os.environ.get(k):
                _saved_keys[k] = os.environ[k]; del os.environ[k]

    # 0) ämne (eller ämnesupptäckt + ranking)
    topic = args["topic"]
    if not topic and args["auto"]:
        log(0, "ämnesupptäckt + ranking (story-potential) ...")
        try:
            ranked = topic_agent.run(limit=20, use_llm=(not force_no_llm))
            print(f"     toppkandidater: " +
                  ", ".join(f"{r['topic']}({r['score']})" for r in ranked[:5]))
            topic, score = topic_agent.pick(ranked)
            print(f"     valt: “{topic}” (score {score:.2f})")
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

    print("=" * 48)
    print("SUNNY AUTO — topic:", topic, "| stil:", style,
          f"| mål: {goal_dur}s | LLM:",
          "av" if force_no_llm else ("på" if llm.is_available() else "av (ingen nyckel)"))
    print("=" * 48, flush=True)

    memory = KB.load()  # LLM-minne: do-not-repeat + formatmönster

    # 1) research
    log(1, "research (källor/claims/typologi) ...")
    research = research_agent.run(topic, proj)

    # 2) story + hook-motor
    log(2, "story-arkitekt + hook-motor (vinklar/hooks/gaps) ...")
    story = story_agent.run(topic, research, proj,
                            use_llm=(not force_no_llm))

    # 3) brain: production plan
    log(3, "LLM skriver manus + produktionsplan (med kanal-minne) ...")
    plan = llm_client.plan(topic, research, goal_dur, no_llm=force_no_llm,
                           memory=None if force_no_llm else memory)

    # 4) script.json + fact-check (→ rewrite vid behov)
    log(4, "script.json + fact-check ...")
    script_agent.run(plan, proj)
    check_report, plan = factcheck_agent.run(
        plan, research, proj, rewrite_with_llm=(not force_no_llm))
    if not check_report.get("safe", False):
        print("     varning: fact-check flaggade block — se factcheck.json")

    # 5) visuals (bilder + bg)
    log(5, "visuell regissör (porträtt/bg, Wikimedia tier1-2 → synth) ...")
    vis = visual_agent.run(topic, research, proj, slug)

    # 6) script.txt (make_captions.py läser den)
    _write_script_txt(plan)

    # 7) voice
    voice = args["voice"] or "auto"
    if voice == "auto":
        voice = LANG_VOICE.get((args["language"] or "en").lower(),
                               "en-GB-RyanNeural")
    log(7, f"voiceover (TTS {voice}) ...")
    audio_agent.run(plan, proj, voice=voice)

    # 8) timeline (audio-driven)
    log(8, "timeline byggs runt verklig röst-duration ...")
    timeline = TLE.build_timeline(plan)
    print(f"     total: {timeline['total']:.1f}s, {len(timeline['segments'])} block")

    # 9) pacing-gate (visual rhythm + SFX-budget) → fix om glapp
    log(9, "pacing-gate (2-6s-rytm, SFX-budget) ...")
    pacing_report = PACING.analyze(timeline, plan)
    if pacing_report["issues"]:
        print("     pacing-issues:", [(i["type"], i.get("block", ""))
                                      for i in pacing_report["issues"][:6]])
        fixes, plan = PACING.fix(pacing_report, timeline, plan)
        if fixes:
            print("     auto-fix:", [f["fix"] for f in fixes])
            timeline = TLE.build_timeline(plan)
    json.dump(pacing_report, open(os.path.join(proj, "pacing.json"), "w"),
              ensure_ascii=False, indent=1)

    # 10) production_plan.json (editorn)
    from agents import edit_agent
    edit_agent.run(plan, timeline, check_report, proj)

    # 11) captions (kinetic)
    log(11, "captions (kinetic v2 + topic-keywords) ...")
    from engine import captions as CAPS
    CAPS.run(keywords=plan.get("keywords"))

    # 12) graphics (plan -> PNG via gfx_kit)
    log(12, "grafik (gfx_kit: glow/lower thirds/stat/tweet/timeline/chart) ...")
    beats, gfx_assets = graphics_agent.build_graphics(plan, slug, vis["people"])

    # 13) footage (sök → ladda → RMS-ögonblick → trim, MED ljud)
    log(13, "footage (yt-dlp + RMS-ögonblick + trim) ...")
    clip_files = {"0": ""}
    try:
        clip_files = footage_agent.run(plan, slug, proj,
                                       max_clips=args["max_clips"])
    except Exception as e:
        print("     footage-fel:", str(e)[:200])

    # 14) licens/risk-lager
    log(14, "licens-/upphovsrättslager ...")
    all_assets = list(vis["assets"]) + list(gfx_assets)
    for fname in clip_files.values():
        if fname:
            all_assets.append({"type": "clip",
                               "file": os.path.join("assets", "clips", fname),
                               "source": "youtube", "license": "youtube"})
    manifest = licensing.manifest(proj, all_assets)

    # 15) kompilera EPISODES/*.json för make_video.py
    log(15, "kompilerar EPISODES/episode_*.json ...")
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

    # 16) render + retry-lag
    log(16, "render (make_video.py → gfx/cinema/captions → ffmpeg) ...")
    rlog = []

    def do_render():
        nonlocal cfg
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts",
                          "make_video.py"), os.path.relpath(ep_path, ROOT)],
                           capture_output=True, text=True, cwd=ROOT)
        if r.returncode != 0:
            raise RuntimeError((r.stdout + r.stderr)[-1500:])
        return r.stdout + r.stderr

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

    # 17) QC
    log(17, "QC (verify_build + svart/frys + tystnad + LLM-kritik) ...")
    qc = qc_agent.run(out_abs, target_dur=timeline["total"],
                      timeline=timeline, project_dir=proj,
                      script_text=" ".join(b["voiceover"] for b in plan["blocks"]))
    if not qc["pass"]:
        print("     QC-fail:", "; ".join(qc["issues"])[:600])

    # 18) thumbnail + titel-motor + metadata
    log(18, "thumbnail-paket + titel-motor (verifiering mot löfte) ...")
    tm = thumbnail_agent.run(plan, topic, proj, out_abs)
    ttl = title_agent.run(plan, topic, proj, memory=memory,
                          use_llm=(not force_no_llm))
    tm["title"] = ttl["title"]
    tm["title_candidates"] = ttl["candidates"]
    thumbnail_agent.write_metadata(tm, proj)

    # 19) risk
    log(19, "risk-scan (copyright/fair-use/defamation) ...")
    risk = risk_agent.run(check_report, manifest, proj)

    # 20) kunskapsbas (learning-loop)
    log(20, "kunskapsbas ...")
    KB.record_run(slug, topic, {"title": tm["title"], "video": tm["video"],
                                "thumbnail": tm["thumbnail"],
                                "duration": timeline["total"], "qc": str(qc["pass"]),
                                "risk": risk["status"]})

    # 21) upload (optional)
    yt_id = ""
    if args["upload"]:
        log(21, "upload (YouTube API, resumable) ...")
        if not qc["pass"] and not args["allow_qc_fail"]:
            print("     BLOCKERAD: QC fail — ingen upload.")
        elif risk["status"] == "HOLD":
            print("     BLOCKERAD: risk HOLD — ingen auto-upload.")
        else:
            try:
                yt_id = upload_agent.upload(
                    out_abs, tm, privacy="private",
                    auto_publish=args["auto_publish"])
                print(f"     uppladdad: https://youtu.be/{yt_id}")
                KB.record_run(slug, topic, {"title": tm["title"],
                                            "video": tm["video"],
                                            "youtube_id": yt_id,
                                            "risk": risk["status"]})
            except Exception as e:
                print("     upload misslyckades:", str(e)[:300])

    _finalize(proj, topic, timeline, plan, check_report, manifest, qc,
              out_rel, date_s, ok=True, risk=risk, meta=tm, yt_id=yt_id)
    return 0 if (qc["pass"] or args["allow_qc_fail"]) else 3

# ---------------------------------------------------------------- helpers 2
def _do_ingest(path):
    """--ingest-analytics: mata in CTR/AVD/retention för en slug."""
    if not os.path.exists(path):
        print("fil saknas:", path); return 2
    data = json.load(open(path, encoding="utf-8"))
    slug = data.pop("slug", None)
    if not slug:
        print("json måste ha 'slug'-nyckel"); return 2
    got = KB.ingest_analytics(slug, data)
    print(f"✓ analytics inmatade för {slug}:", got)
    return 0

def _parse(argv):
    d = {"topic": None, "auto": False, "duration": "8m", "language": "en",
         "style": "sunnyv2", "voice": "auto", "no_llm": False, "retries": 3,
         "max_clips": 6, "dry_run": False, "list": False, "allow_qc_fail": False,
         "upload": False, "auto_publish": False, "ingest_analytics": None}
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
        elif a == "--retries": d["retries"] = int(val() or 3)
        elif a == "--max-clips": d["max_clips"] = int(val() or 6)
        elif a == "--dry-run": d["dry_run"] = True
        elif a == "--list": d["list"] = True
        elif a == "--allow-qc-fail": d["allow_qc_fail"] = True
        elif a == "--upload": d["upload"] = True
        elif a == "--auto-publish": d["auto_publish"] = True
        elif a == "--ingest-analytics": d["ingest_analytics"] = val()
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
              date_s, ok=True, risk=None, meta=None, yt_id=""):
    print("\n" + "=" * 48)
    print("SUNNY AUTO COMPLETE" if ok else "SUNNY AUTO — INTE GODKÄND")
    print("=" * 48)
    research_path = os.path.join(proj, "research.json")
    rf = 0
    if os.path.exists(research_path):
        try:
            rf = len(json.load(open(research_path, encoding="utf-8")).get("facts", []))
        except Exception:
            pass
    print(f"Topic:       {topic}")
    print(f"Research:    {'✓' if rf else '✗'} ({rf} claims)")
    print(f"Script:      ✓ ({len(plan.get('blocks', []))} block)")
    print(f"Fact check:  {'✓' if check_report.get('safe', False) else '✗ (se factcheck.json)'}")
    print(f"Voiceover:   ✓")
    print(f"Footage:     ✓ ({len([a for a in manifest if a.get('type') == 'clip'])} klipp)")
    print(f"Graphics:    ✓ ({len([a for a in manifest if a.get('type') == 'graphic'])} st)")
    print(f"Captions:    ✓")
    print(f"Timeline:    ✓ ({timeline['total']:.1f}s)")
    print(f"Render:      {'✓' if os.path.exists(os.path.join(ROOT, out_rel)) else '✗'}")
    print(f"QC:          {'✓ PASS' if qc.get('pass') else '✗ ' + '; '.join(qc.get('issues', []))[:120]}")
    if risk:
        print(f"Risk:        {risk['status']} ({risk['severity']})")
    print(f"VIDEO:       {out_rel}")
    if meta and meta.get("thumbnail"):
        print(f"THUMBNAIL:   {meta['thumbnail']}")
        print(f"TITLE:       {meta['title']}")
    if yt_id:
        print(f"YOUTUBE:     https://youtu.be/{yt_id}")
    if risk and risk["status"] == "HOLD":
        print("\n→ HÅLL INNE: risk-scan kräver mänsklig granskning före publicering.")
    if not qc.get("pass"):
        print("\n→ QC misslyckades efter retries. Åtgärda enligt qc.json och kör om.")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
