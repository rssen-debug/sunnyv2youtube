# sunny_auto.py — den automatiska dokumentärstudion

En enda post skapar en hel SunnyV2-stil dokumentär: research → manus →
fact-check → bilder/klipp → voiceover → timeline → grafik → captions →
render → QC → färdig MP4 (+ thumbnail, titel, metadata, risk-rapport).

```bash
# Ett ämne:
python3 sunny_auto.py --topic "MrBeast"

# Helt autonomt (ranking med story-potential + full pipeline):
python3 sunny_auto.py --auto

# Med LLM som hjärna (creative director / researcher / editor-planner):
export GROQ_API_KEY="..."          # eller OPENAI_API_KEY
python3 sunny_auto.py --topic "MrBeast"

# Utan LLM (deterministiskt manussyntes ur research):
python3 sunny_auto.py --topic "MrBeast" --no-llm

# Uppladdning till YouTube (kräver OAuth2-uppgifter, PRIVAT som default):
export YT_CLIENT_SECRETS=/path/client_secrets.json
python3 sunny_auto.py --topic "MrBeast" --upload            # om QC+risk tillåter
python3 sunny_auto.py --topic "MrBeast" --upload --auto-publish

# Learning-loop: mata in analytics efter publicering:
python3 sunny_auto.py --ingest-analytics meta.json
# meta.json = {"slug":"mrbeast","ctr":7.2,"avd":"3:41","retention":"3:41",
#              "likes":12000,"comments":340,"views":410000,
#              "sections_lost_viewers":["2:10-2:40"]}
```

## Flaggor

| Flagga | Betydelse | Default |
|---|---|---|
| `--topic "X"` | ämne | — |
| `--auto` | hitta ämne själv | — |
| `--duration 8m` | mål-längd (hint; voiceovern styr) | `8m` |
| `--language en` | språk (en/en-gb/en-us/sv/no/da/de/fr) | `en` |
| `--style sunnyv2` | stilprofil (look i cinema.py) | `sunnyv2` |
| `--voice auto` | TTS-röst (`auto` = en-GB-RyanNeural); `--list` visar röster | `auto` |
| `--no-llm` | offline-läge utan LLM-nyckel | av |
| `--retries 3` | max självläkningsförsök vid fel | `3` |
| `--max-clips 6` | max nedladdade klipp | `6` |
| `--dry-run` | research+manus+voice+grafik men INGEN render | av |
| `--list` | lista edge-tts-röster | — |
| `--upload` | ladda upp till YouTube (OAuth2; `YT_CLIENT_SECRETS`; privat) | av |
| `--auto-publish` | tillsammans med `--upload`: publicera direkt | av |
| `--ingest-analytics <f>` | mata in CTR/AVD/retention m.m. för slug | — |

**Exempel på full körning:**

```bash
export GROQ_API_KEY="..."
python3 sunny_auto.py --topic "MrBeast" --duration 8m --language en --style sunnyv2
```

## Vad som händer (pipelinen)

```
TOPIC(discovery+scoring) → RESEARCH(claims+tier+typologi) → STORY/HOOK-MOTOR
   → LLM MANUS+PLAN → FACT-CHECK(rewrite) → VISUALS → VOICE → TIMELINE(audio-driven)
   → PACING-GATE(2-6s-rytm, SFX-budget) → CAPTIONS → GRAPHICS(gfx_kit)
   → FOOTAGE(yt-dlp, med ljud) → LICENS → RENDER(make_video+cinema) → QC
   → THUMBNAIL → TITEL-MOTOR(verifiering) → RISK → METADATA → (UPLOAD)
```

Varje steg loggas `[01]..[20]` i terminalen och avslutas med:

```
================================
SUNNY AUTO COMPLETE
================================
Topic:       MrBeast
Research:    ✓
...
QC:          ✓ PASS
VIDEO:       videos2026/mrbeast_sunnyv2_v1_2026-09-21.mp4
```

## Arkitektur — LLM bestämmer, Python utför

```
sunny_auto.py                      orchestrator (CLI + flöde + retries + upload)
agents/
  topic_agent.py                   ämnesupptäckt + ranking (story-potential)
  research_agent.py                källor → claims (typ+tier+confidence)
  story_agent.py                   vinklar + driver hook-motorn (story.json)
  hook_agent.py                    HOOK-MOTORN: hooks/openings/gaps/cold opens
  llm_client.py                    "hjärnan": production_plan (eller offline-syntes)
  script_agent.py                  script.json (block/scener)
  factcheck_agent.py               os­tödda siffror/namn → rewrite/flagga
  visual_agent.py                  porträtt/bg (Wikimedia tier1-2 → synth-fallback)
  audio_agent.py                   TTS per block (edge-tts; mäter VERKLIG dur)
  footage_agent.py                 sök→ladda→RMS-ögonblick→trimma (MED ljud)
  graphics_agent.py                plan → PNG via gfx_kit + EPISODES-json
  edit_agent.py                    production_plan.json (hela planen i en fil)
  title_agent.py                   TITEL-MOTORN: typer + verifiering (löfte, inga
                                   upprepningar, max 100 tecken, ej clickbait)
  thumbnail_agent.py               thumbnail-paket + titel + metadata
  qc_agent.py                      verify_build + svart/frys/tystnad + LLM-kritik
  risk_agent.py                    copyright/fair-use/reused-content/defamation
                                   → GO|REVIEW|HOLD
  upload_agent.py                  YouTube Data API v3 (resumable, OAuth2 device)
  licensing.py                     asset → tier/status (allowed|review|reject)
engine/
  timeline.py                      audio-driven timeline (beat-synk, 90 BPM)
  pacing.py                        PACING-MOTORN: 2-6s-rytm, SFX-budget, musik-
                                   kollision → deterministiska fixar
  media.py                         ffmpeg-inspect/heal, trim, RMS, frys/svart
  audio.py                         TTS-motorer + musikintensitet
  captions.py                      tunnt lager över make_captions.py v2
  retry.py                         diagnos → fix → retry (max N)
  knowledge.py                     channel_knowledge.json + analytics-ingest
                                   (CTR/AVD/retention → learning-loop)
research/
  sources.py                       HTTP/Wikipedia/News/Wikimedia/yt-dlp + cache
  trends.py                        trends/news/autocomplete-kandidater
  claims.py                        claim-typologi + källhierarki + research.json
```

Studiotoolkiten **återanvänds, byggs inte om**: `gfx_kit.py` (glow-titlar,
lower thirds, tweet/stat/timeline/chart), `cinema.py` (easing/looks/SFX/musik),
`make_captions.py` (kinetic captions), `make_video.py` (JSON → full render),
`verify_build.py` (MANDATE-QA).

## Projektstruktur per episod

```
projects/<slug>/
  research.json          claims med kind/tier/confidence
  story.json             vinklar + hook
  script.json            manus (blocks/visuals)
  factcheck.json         os­tödda påståenden + åtgärder
  production_plan.json   hela videoplanen (block/visual/clip/music/caption)
  asset.json             licensstatus per asset
  timeline.json          audio-driven timelines (segments/beats/clips/grafik)
  qc.json                QC-resultat + mätvärden
  risk.json              GO/REVIEW/HOLD
  thumbnail.jpg + metadata.json (titel/desc/tags)
```

## Viktiga principer

1. **Timeline byggs runt rösten** — varje blocks wav-längd mäts (`wave`-modulen),
   sedan placeras klipp/grafik/SFX relativt blocket. Inga gissade durations.
2. **LLM hittar inte på fakta** — siffror/namn måste matcha research-claims,
   annars ändras eller tas de bort (fact-check → rewrite).
3. **Klipp kopplas till narration** — clip_plan har query + block + at/until;
   footage-motorn letar ögonblicket via RMS-topp och behåller ljudet.
4. **Licenslager** — varje asset får tier + status; risk-agenten sätter
   `GO|REVIEW|HOLD` före leverans.
5. **Självläkning** — render/Q C-fel diagnostiseras och repareras (max
   `--retries`), exempelvis plockas trasiga klipp bort och renderas om.

## Beroenden

```bash
pip install -r requirements.txt
```

(ffmpeg installeras automatiskt via `imageio-ffmpeg` om det saknas;
yt-dlp används bara för footage.)

## Notera

- TTS: edge-tts (Microsoft Edge-röster). `voice_id` från andra sessioner gäller
  inte här — kör med `--voice <namn>` eller `auto`.
- Footage/bilder hämtas från publika källor och taggas med licens. Repot är
  demo/utbildning; **publicering kräver egen fair-use/licens-bedömning**
  (se `projects/<slug>/risk.json`).
