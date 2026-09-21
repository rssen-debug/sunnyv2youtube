# sunny_auto.py — den automatiska dokumentärstudion

En enda post skapar en hel SunnyV2-stil dokumentär: research → manus →
fact-check → bilder/klipp → voiceover → timeline → grafik → captions →
render → QC → färdig MP4 (+ thumbnail, titel, metadata, risk-rapport).

```bash
# Ett ämne:
python3 sunny_auto.py --topic "MrBeast"

# Helt autonomt (hittar ämnet själv via trends/news/Youtube):
python3 sunny_auto.py --auto

# Med LLM som hjärna (creative director / researcher / editor-planner):
export GROQ_API_KEY="..."          # eller OPENAI_API_KEY
python3 sunny_auto.py --topic "MrBeast"

# Utan LLM (deterministiskt manussyntes ur research):
python3 sunny_auto.py --topic "MrBeast" --no-llm
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

**Exempel på full körning:**

```bash
export GROQ_API_KEY="..."
python3 sunny_auto.py --topic "MrBeast" --duration 8m --language en --style sunnyv2
```

## Vad som händer (pipelinen)

```
TOPIC → RESEARCH → STORY(hooks/vinklar) → LLM SCRIPT+PRODUKTIONSPLAN
   → FACT-CHECK(re-write vid behov) → VISUALS(bilder/bg) → VOICE(TTS per block)
   → TIMELINE(runt VERKLIG röst-längd) → CAPTIONS(kinetic v2) → GRAPHICS(gfx_kit)
   → FOOTAGE(yt-dlp sök→ladda→trimma m ljud) → LICENSLAGER
   → EPISODES/episode_<slug>.json → make_video.py → cinema/gfx/captions → ffmpeg
   → QC(verify_build) → (retry-loop) → thumbnail/titel/metadata → risk-scan
   → videos2026/<slug>_<style>_v1_<datum>.mp4
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
sunny_auto.py                      orchestrator (CLI + flöde + retries)
agents/
  research_agent.py                källor → claims (typ+tier+confidence)
  story_agent.py                   vinklar/hook (story.json)
  llm_client.py                    "hjärnan": production_plan (eller offline-syntes)
  script_agent.py                  script.json (block/scener)
  factcheck_agent.py               os­tödda siffror/namn → rewrite/flagga
  visual_agent.py                  porträtt/bg (Wikimedia tier1-2 → synth-fallback)
  footprint: audio_agent.py        TTS per block (edge-tts; mäter VERKLIG dur)
  footage_agent.py                 sök→ladda→RMS-ögonblick→trimma (MED ljud)
  graphics_agent.py                plan → PNG via gfx_kit + EPISODES-json
  thumbnail_agent.py               thumbnail + titel + metadata
  qc_agent.py                      verify_build + grundkontroller + LLM-kritik
  risk_agent.py                    copyright/defamation → GO|REVIEW|HOLD
  licensing.py                     asset → tier/status (allowed|review|reject)
engine/
  timeline.py                      audio-driven timeline (beat-synk, 90 BPM)
  media.py                         ffmpeg-inspect/heal, trim, RMS, grids
  audio.py                         TTS-motorer + musikintensitet + SFX-budget
  captions.py                      tunnt lager över make_captions.py v2
  retry.py                         diagnos → fix → retry (max N)
  knowledge.py                     channel_knowledge.json (learning-loop)
research/
  sources.py                       HTTP/Wikipedia/News/Wikimedia/yt-dlp + cache
  trends.py                        --auto: trends/news/autocomplete + scoring
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
