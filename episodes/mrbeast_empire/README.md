# Half a Billion Subscribers — and He Says He's Broke (MrBeast)

**Avsnitt • producerad 20 september 2026 • 4:19 (258,9 s) • 1280×720 / 30 fps**

Slutfil: **[mrbeast_empire.mp4](mrbeast_empire.mp4)**
Thumbnail: [thumbnail.jpg](thumbnail.jpg)
Manus: [script/script.txt](script/script.txt)
Undertexter: [captions.ass](captions.ass) (kinetic v2, Archivo Black + keyword-highlight)

## Ämnesval

Dokumentär om **MrBeast (Jimmy Donaldson)** — från "I Counted To 100,000!" (jan 2017) till
500M+-rekordet 12 juni 2026, med 2024 års kris (Ava Tyson-beskyllningarna, Beast
Games-grupptalan) som vändpunkt och 2026 års läge (Beast Games S2, Beast Industries
$5,2B, Beast Land) som payoff. Research gjord 20 september 2026; inga påståenden utan
källtäckning. Klassisk hook → karaktär → uppgång → vändpunkt → eskalering →
konsekvenser → payoff + CTA enligt STYLE_GUIDE.md.

## Faktakontroll per block

| Block | Påståenden | Källa |
|---|---|---|
| A1 | 500M+ prenumeranter 12 juni 2026, första individuella skaparen; "borrowing money"-citat | [1] everything-pr.com (Beast Industries-profil, 2026-09) |
| A2 | Greenville NC; började som 13-åring (2012); 5 års algoritmstudier; jan 2017 genombrott | [4] time.com TIME100 2026; allmänt dokumenterat |
| A3 | "I Counted To 100,000" (40 h); "50 Hours Buried Alive" (2021); giveaways som motor | [4] time.com; originalklipp C1 |
| A4 | $456,000 Squid Game IRL (nov 2021); Feastables; Beast Games ~$100M Amazon-deal (rapporterat); Beast City; $10M huvudpris S1 | [1]; originalklipp C2/C3 |
| A5 | Medvärd anklagad & klev undan 2024; extern advokatbyrå sade nyckelanklagelser vara ogrundade; grupptalan 16 sept 2024 (osäkra förhållanden, obetalda löner, trakasserier) — "alleging", inga skuldslutsatser | [5] allaboutlawyer.com; [8] reddit/Variety-rubrik |
| B1 | CEO Jeff Housenbold sedan sept 2024; Beast Land pop-up Riyadh ~$85M, vinst på 45 dagar; målet olöst feb 2026 | [1]; [4]; [5] |
| B2 | S2-premiär 7 jan 2026, 200 deltagare, Strong vs Smart, $5M pris; $5,2B värdering; ~750 anställda; 132-acre campus; $2,6B på papper | [1] everything-pr.com; [2] techbuzz.ai; [4] |
| A6 | 1,3B unika tittare/kvartal; "island"-giveaways; redaktionell syntes (ingen påhittad upplösning) | [1] |

## Källor

1. everything-pr.com — "Beast Industries 2026: Inside MrBeast's $5.2B Company" (13 sep 2026)
2. techbuzz.ai — "Beast Games Season 2 Hits Prime Video January 2026"
3. latimes.com — "Beast Games Season 2 episode 8" (11 feb 2026)
4. time.com — "Taming MrBeast: 2026 TIME100 Most Influential Companies"
5. allaboutlawyer.com — "MrBeast Lawsuit 2026, Beast Games Class Action Still Unresolved"
6. businessinsider.com — "MrBeast's new goal: turning 476M subscribers into paying members" (12 maj 2026) — återges som EXCERPT-kort i videon
7. Variety-rubrik om Beast Games-grupptalan (sept 2024) — återges som EXCERPT-kort
8. tts.fandom.com — prenumerant-milstolpar (korsreferens)
9. uniladtech.com — Beast Land $85M (nov 2025)

## Originalklipp (publiceringslicens krävs — demo/utbildning)

| # | Fönster i videon | Källa | Innehåll |
|---|---|---|---|
| C1 | 83,3–89,8 s | `vEoLQc2QZcQ` — re-upload av "I Counted To 100,000!" (reactor beskuren via crop) | räkneögonblick, sovrum |
| C2 | 118,0–124,0 s | `0e3GPea1Tyg` — MrBeast "$456,000 Squid Game In Real Life!" | RLGL-setet |
| C3 | 124,7–131,2 s | `RUaoJQ4ZfLY` — Prime Video "Beast Games Season 2 – Official Trailer" | Beast City-luftbild |
| C4 | 223,3–229,3 s | `JDad7XTfaIU` — Entertainment Tonight "Why BILLIONAIRE MrBeast Is Borrowing Money From His MOM!" | hans egna X-poster på skärm |

Klippen spelas i tysta svansar efter replik-pekarna ("Watch.", "Look at this.",
"He said it himself.") — VO och klipp-ljud överlappar aldrig. Enbart AI-genererade
visuella är bakgrunden (`bg_ai.png`) och thumbnail; alla personbilder/klipp är
verkligt källmaterial. EXCERPT-korten citerar verkliga rubriker med källa och datum,
märkta på kortet.

## Teknik enligt MANDATE.md

- **4 klipp med ljud** (krav ≥3), duckad beat-drone 0,10 under klipp, vol 1,30–1,50
- **Visual change 2–6 s**: 51 overlays, 43 ljudströmmar; aktivitets-median 1,221
- **Studiofonter**: Anton (glow-titlar/stat), Archivo Black (captions/LT), Bebas (sub-rader)
- **Lower thirds**: Jimmy Donaldson (A1 2,7 s), Jeff Housenbold (B1 2,0 s)
- **Social-UI-bevis**: EXCERPT-headlines Variety (A5) + Business Insider (B2), sweep-reveal + glitch
- **Data-viz**: 500M+ / $5.2B / $300M stat-slams (easeOutBack, beat-kvantiserade 90 BPM)
- **2.5D**: zoompan-bakgrund (förskjutet `on`-fönster per segment = sömlös zoom), drift-sinus på hero/parallax
- **Sound**: syntetiska impacts/whoosh/risers/glitch; riser 2,4 s före varje klipp
- **Look**: GRADE + bloom + GRAIN + letterbox + vinjett + HUD + lightleak + blixtar
- **Render-arkitektur**: 8 block-segment (RAM) → concat `-c copy` → separat ljud-pass → cinema-pass. Segment-cache: radera `.cache/render/` vid ändrad scenlayout.

## QA (körd 2026-09-20)

- `python3 scripts/verify_build.py episodes/mrbeast_empire/mrbeast_empire.mp4 258.9` → **PASS ✅**
  (duration 258,9 = target, activity 1,221 > 0,25, 35 ljud-höjdpunkter ≥ 3, ingen klippning)
- Ljud: **peak −3,41 dBFS**, **RMS −20,96 dBFS** (mål ≈ −3 / −18…−21)
- Klippfönster-RMS 0,105–0,158 mot duckad drone 0,043 (tydligt över, krav uppfyllt)
- QA-sheets `preview/qa_sheet1-3.jpg` granskade ruta för ruta; A1-krock (glow↔LT) fixad och omrenderad (`qa_fix_a1b.jpg`)
- Tre renderiterationer (OOM-fix → ljud-fix → layout-fix), se git-logg

## Kör om

```bash
pip install pillow numpy imageio-ffmpeg yt-dlp
ln -sf "$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" /usr/local/bin/ffmpeg
python3 scripts/make_captions.py   # timings.json + captions.ass (TRAIL-svansar för klipp)
python3 scripts/make_assets.py     # 37 GFX-assets
python3 scripts/build_video.py     # 3-pass-render
python3 ../../scripts/verify_build.py mrbeast_empire.mp4 258.9
```

TTS-rösten (voice-00) är sessionsbunden; `audio/*.wav` + `*_orig.wav` finns sparade för omrendering.

## Rättigheter

Klipp/porträtt/fotografier är tredjepartsmaterial för detta kommenterande
redigeringsutkast — ingen licens eller automatisk fair-use-rätt garanteras; kontrollera
tillstånd före publicering. Syntetiskt ljud och bakgrunder skapade för avsnittet.
Committa aldrig tokens; återkalla token från chatten direkt.
