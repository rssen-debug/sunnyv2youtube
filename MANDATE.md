# MANDATE.md — TVÅNGSREGLER (läs innan DU renderar något)

Detta dokument är **bindande**. En video som bryter mot något av nedan är en **MISSLYCKAD**
leverans, oavsett hur snygg den är på andra sätt. `verify_build.py` körs alltid efter render
och **REJECTAR** videor som bryter mot de mätbara reglerna.

## BAKGRUND (varför detta finns)
En agent levererade en "textspels-video" (stills + textkort, inga klipp, inget ljud i bild,
ingen motion) och kallade den sunnyv2-stil. Det är INTE acceptabelt. Därför finns:
1. **GFX KIT v2** (`scripts/gfx_kit.py`) — studio-assets: glow-titlar (Anton), lower thirds,
   tweet/social-UI-mockups, stat-kort, HUD-ram, light leaks
2. **CINEMA KIT** (`scripts/cinema.py`) — easing/overshoot, parallax-motor, color grade
   (teal/orange), film grain, bloom, letterbox, beat-musik (90 BPM), SFX-formler
3. **Captions v2** — kinetic typography, Archivo Black, keyword-highlight (röda nyckelord),
   rotations-jitter
4. **verify_build.py** — maskinell QA som blockerar "basic"-leveranser

## DE 12 TVÅNGSKRAVEN

| # | Krav | Hur (konkret) |
|---|---|---|
| 1 | **Minst 3 äkta klipp MED ljud** per 3 min | yt-dlp → `CLIPS`-listan i buildern; repliker pekar ut dem ("Here's the moment.") |
| 2 | **Visual change var 2–6 s** | 3–5 beats per manus-block (cards/circles/klipp/titlar/stat) |
| 3 | **Riktiga display-fonts** | Anton/Archivo Black/Bebas via `gfx_kit.F()` — ALDRIG DejaVu som huvudfont |
| 4 | **Lower third** vid varje ny person-intro | `gfx_kit.lower_third()` — glider in, ligger ÖVER captions-zonen (y ≤ 470) |
| 5 | **Social-UI-bevis** minst 1 | `tweet_ui()` / screenshot med sweep-reveal + glitch-SFX |
| 6 | **Data-viz** minst 1 | `stat_card()` — mitt-i-skärm pop 1–2 s (pattern interrupt) |
| 7 | **Kinetic captions** | `make_captions.py` v2 + `keywords.txt` uppdaterad för topicn |
| 8 | **2.5D-rörelse på stills** | `cinema.parallax_bg/parallax_fg` eller drift-ease — aldrig statiska stills >4 s |
| 9 | **Sound design** | impacts på slams, riser 2,4 s före stora reveals, whoosh på snitt, musik-duckning under klipp (0.10) |
| 10 | **Cinematic look** | GRADE + GRAIN + bloom + letterbox + vignette + HUD (CINEMA-lagret) |
| 11 | **Beat-sync (90 BPM)** | stora infall på `k*0.6667 s` (1.333, 2.0, 8.0, 13.333 ...) |
| 12 | **Censurvarv**: `python3 scripts/verify_build.py <fil>` MÅSTE PASSA | kör efter VARJE render; fixa och rendera om tills PASS |

## RÖD LISTA (momentant NEJ)
- Textspels-video: stills + text utan klipp/ljud/motion
- DejaVu Sans som identitetsfont
- Statiska full-frame stills i >6 s utan parallax/zoom
- Musik som överröstar VO eller klipp-ljud
- Grafik i captions-zonen (y 560–650) när captions är aktiva
- "Kreativ" egen standardstil som avviker från STYLE_GUIDE.md
- Att hoppa över QA-sheet-granskning eller verify_build

## MINIMI-CHECKLISTA FÖRE LEVERANS
- [ ] verify_build.py PASS
- [ ] QA-sheet granskad ruta-för-ruta (inga krockar)
- [ ] RMS: klipp-ljud tydligt över drone; peak ≈ −3 dBFS
- [ ] Duration ≈ target (±5 %)
- [ ] Kopia till `videos2026/` med namnmönster `ämne_stil_version_datum.mp4`
- [ ] README + git-commit uppdaterade
