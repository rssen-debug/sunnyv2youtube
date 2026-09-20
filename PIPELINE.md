# PIPELINE.md — EXAKT 1:1 hur den här videon byggs (och hur du bygger nästa)

Detta repo (`sunnyv2youtube`) är en **komplett, körbar pipeline** för sunnyv2-/urlörelse-dokumentärer:
manus → TTS → timing → captions → GFX → klipp med ljud → sound design → ffmpeg-render → QA → push.

**Nästa agent behöver bara veta detta:**
> "Repot heter **sunnyv2youtube**. Läs `PIPELINE.md` och kör pipelinen. Skapa en video om *INSERT TREND HERE*."

---

## INNEHÅLL
1. [Promptmall för nästa video](#1-promptmall)
2. [Arkitektur: vad varje fil gör](#2-arkitektur)
3. [Stegen 0–10, exakt som vi gjorde](#3-stegen)
4. [Verktygs-verkligheter (sandbox-fällor)](#4-verktygsverkligheter)
5. [Timing- & caption-systemet](#5-timing--captions)
6. [Scen- & grafiksystemet](#6-scen--grafik)
7. [Klipp: hitta, ladda, klipp ut, ljud](#7-klipp)
8. [Sound design-formler](#8-sound-design)
9. [Alla buggar viSprang på + fixar (LÄR DIG DETTA)](#9-buggar--fixar)
10. [QA-protokoll](#10-qa-protokoll)
11. [GitHub-push ( detta repo)](#11-github)

---

<a name="1-promptmall"></a>
## 1. PROMPTMALL (kopiera, byt topic)

```
Repot sunnyv2youtube innehåller en komplett pipeline. Läs PIPELINE.md och kör:

Topic: [TREND/PERSON HÄR]
1. Webbsök fakta (3-5 källor) → skriv script/script.txt i 8-10 block (###A1...): hook → vem → uppgång → vändpunkt → eskalering → konsekvens → payoff + CTA. Varje block 300-600 tecken. Skriv repliker som PEEKAR ut klipp ("Here's the moment.", "Look at this.", "Listen to this.")
2. Leta bilder: image_search på 3-4 frågor (porträtt, platser, screenshots) → assets/src/
3. AI-generera: mörk bakgrund (bg_ai.png) + ev. recreation-skärm (clip_recreation.png)
4. TTS: add_voice (maskulin, en-GB, narration) → generate_speech PER BLOCK -> audio/<ID>.wav
5. Klipp: yt-dlp sök ("ytsearch6:..."), ladda ≤480p, mux, analysera RMS för att hitta ögonblick, fyll CLIPS-listan i build_video.py med {fil, cut, dur, t, w, y, vol}
6. GFX: anpassa text_card-raderna i make_assets.py till topicn → kör den
7. Kör: make_captions.py → build_video.py → QA-sheet + RMS-kontroller → fixa → rendera igen
8. Uppdatera README.md (scenario/fakta/källor) + pusha
```

**Reglerna för stilen** står ORDLAGRANT i **STYLE_GUIDE.md**. **TVÅNGSKRAVEN** står i **MANDATE.md** — minst 3 klipp med ljud, GFX-kit (lower thirds/tweets/stat-kort/glow-titlar), kinetic captions, 2.5D-parallax, sound design, cinematic grade — och `scripts/verify_build.py` REJECTAR videor som bryter mot dem. Studio-verktygen: `gfx_kit.py`, `cinema.py`, `make_captions.py` (v2), `build_poc_v4.py` (full demo i `POC_v4_cinema_kit.mp4`). ARBETSFLÖDE: manus → GFX-kit → CLIPS → render → **verify_build PASS** → QA-sheet → leverera + kopia till `videos2026/`.

---

<a name="2-arkitektur"></a>
## 2. ARKITEKTUR

```
drake-video/  (= repo-roten sunnyv2youtube)
├── drake_goth_girl_sunnyv2.mp4   SLUTPRODUKTEN (3:06, 1280x720/30fps)
├── thumbnail.jpg                 YouTube-thumbnail (AI-genererad)
├── PIPELINE.md                   DENNA FIL — ge till nästa agent
├── README.md                     Översikt + fakta/källor + stilregler
├── script/script.txt             MANUSET: ###ID-block. ÄNDRA HÄR FÖRST.
├── audio/A1.wav ... B2.wav       TTS per block (måste matcha script-IDs)
├── timings.json                  AUTO: per block start/dur + total (READ AV ALLT)
├── captions.ass                  AUTO: word-by-word pop-captions
├── assets/src/                   RÅFOTON (drake.jpg, pinkchyu.jpg, casa.jpg,
│                                 stream_screenshot.png) + bg_ai.png + clip_recreation.png
├── assets/gfx/                   AUTO-FABRIKAT: *_circle.png, card_*.png,
│                                 title_*.png, particles.png, vignette.png
├── assets/clips/                 yt-dlp-klipp (bark/tmz/enews/casaloma/speed.mp4)
│                                 + grid_*.jpg (kontaktblad per klipp)
├── scripts/
│   ├── make_assets.py            Pillow-fabrik: cirkelporträtt, kort, partiklar
│   ├── make_captions.py          läs wavs → timings.json + captions.ass
│   ├── build_video.py            ★ ffmpeg-ORCHESTRATORN: allt grafik+ljud+klipp
│   └── filtergraph.txt           senaste filtergraphen (debug — läs vid fel!)
└── preview/sheet*.jpg            QA-rutnät (genereras per render)
```

**Flöde:** `script.txt` + `audio/*.wav` → `make_captions.py` → `timings.json` → `build_video.py` läser timings + bygger EN enda ffmpeg `filter_complex` (30+ inputs, 20+ overlays, 20+ audiostreams) → mp4.

---

<a name="3-stegen"></a>
## 3. STEGEN 0–10 (exakt vad vi gjorde, i ordning)

**0) Verktyg (VARJE ny session — se §4):**
```bash
command -v ffmpeg >/dev/null || { pip install -q imageio-ffmpeg; \
  ln -sf $(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())") /usr/local/bin/ffmpeg; }
pip install -q yt-dlp pillow numpy
```
(Ingen apt i miljön → imageio-ffmpegs statiska binär. Ingen ffprobe → `ffmpeg -i` + regex.)

**1) FAKTA:** `web_search` 3–5 frågor om topicn. Samla: namn, datum, siffror, citat, källor. Skriv ner dem i README.

**2) MANUS:** `script/script.txt`:
```
###A1
Hook: mest chockerande grejen. Ställ frågan tittaren MÅSTE få svar på. Sluta med cliffhanger.

###A2
Vem är personen + varför spelar det roll. INGA onödiga bakgrundsfakta.

###A3 ... uppgången ...
###A4 ... vändpunkten (skriv "Here's the moment." exakt där klippet ska in!)
###A5 ... eskalering ("Look at this place." för plats-b-roll)
###B1/B2 ... konsekvenser, nya twistrar (B = bonus-block)
###A6 (eller sista) Payoff + bind tillbaka till hooken + CTA: "Subscribe..."
```
Regler: 300–600 tecken/block, "..."/pauser inför reveals, vardaglig men självsäker ton, ALDRIG mer än ~600 tecken (TTS-gräns 1500, men kort = bättre rytma). Visual-change var 2–6 s styrs av scenerna i build_video.py — planera manuset så varje block har 2–4 visuella beats.

**3) BILDER:** `image_search` (2–3 st per huvudperson + plats + screenshots). `read_file` VARJE träff innan använd (flera är fel/stock). Kopiera till `assets/src/` med STABILA namn (drake.jpg...). Licens-varning: sökbilder = endast demo; för publicering: egna/licensierade.

**4) AI-VISUALS:** `generate_image`: (a) `bg_ai.png` — mörk dokumentärbakgrund med röd glow + partiklar, (b) ev. recreation-skärmar för det som saknar footage. AI-bilder = fallback när riktigt material saknas (regeln i stilguiden).

**5) TTS:**
- `add_voice(text=hook-exempel, language="en-GB", voice_identity={gender: masculine, use_case: narration})` → användaren väljer → du får `voice_id`. OBS: voice_id lever bara i DIN session — kör alltid eget add_voice.
- `generate_speech` per block → `audio/A1.wav` osv. (max 10 clips/turn — 8 block = OK; behövs fler: kör resten nästa tur).
- Läs upp repliker med citat/paus-tecken: "..." ger dramatisk paus.

**6) KLIPP (det som gör dokumentären "riktig"):** se §7. Sök med `yt-dlp --flat-playlist --print` på `ytsearch6:`-frågor → välj korta klipp (30–90 s) från nyhetskanaler/streams → ladda ≤480p → muxa → RMS-analys för att hitta exakt ögonblick → fyll `CLIPS`-listan i build_video.py.

**7) GFX:** Redigera `text_card(...)`-raderna i `make_assets.py` (rubriker med topicns ord), porträttglobs motsvarar src-namnen → `python3 scripts/make_assets.py`.

**8) TIMING + CAPTIONS:** `python3 scripts/make_captions.py` → läser wav-längderna, skriver `timings.json` + `captions.ass` (word-by-word, grupper ≤3 ord/≤16 tecken, pop `\fscx62\fscy62\t(0,70,...)`).

**9) RENDER:** `python3 scripts/build_video.py` (≈4–5 min för 3 min video, veryfast/crf22). Bygg fel → LÄS `scripts/filtergraph.txt` och matcha mot §9.

**10) QA + ITERERA (OBSLIIGT):** gör QA-sheet (9–12 tidsstämplade stills i rutnät) + RMS-fönster-kontroller (klipp-ljud > drone-RMS på klipppunkterna) + kolla Duration. Titta på VARJE sheet. Typiska fixar: kort som krockar captions (flytta y upp), klipp-timing (justera t/cut), knappar fade. Rendera om tills rent. Sedan README + push (§11).

---

<a name="4-verktygsverkligheter"></a>
## 4. VERKTYGS-VERKLIGHETER (sandbox-fällor — TA DETTA PÅ ALLVAR)

1. **Installerade paket dör mellan svagna.** ffmpeg/yt-dlp försvinner → kör install-blocket i steg 0 i VARKOMMANDO du behöver dem. Lita aldrig på att "det fanns förra svaret".
2. **Arbetsfiler kan också försvinna (sällsynt men hänt med klipp).** Om filer är borta: ladda ner igen. Sätt ALDRIG flera svagna på mellansteget utan att ha koll på att filerna finnes (`ls`).
3. **Ingen ffprobe** → duration/stream-info via `ffmpeg -i f 2>&1 | grep -E "Duration|Stream"` + regex `(\d+):(\d+):([\d.]+)`.
4. **TTS:** `voice_id` är sessionsbundet; max 10 generate_speech per tur; wav-längd läses med Pythons `wave`-modul.
5. **2 CPU-kärnor / ~2 GB RAM** → veryfast + crf 22 + 720p. 1080p funkar men dubblerar tiden.
6. **Snapshot tar inte node_modules/.cache osv.** — håll dig till workspace-filer.

---

<a name="5-timing--captions"></a>
## 5. TIMING- & CAPTION-SYSTEMET

`make_captions.py`:
- `start(N) = start(N-1) + dur(N-1) + GAP`, `dur` = exakt wav-längd (wave-modulen). `GAP=0.7`, `TAIL=0.5`.
- Captions: varje blockets ord fördelas proportionellt mot ordlängd (`len+2`), start-offset `LEAD=0.10`.
- Gruppering: ≤3 ord eller ≤16 tecken per event → pop-stil `{\fscx62\fscy62\t(0,70,\fscx100\fscy100)\fad(35,45)}`, stil "Pop" DejaVu Sans 58, outline 4, MarginV 92 (→ caption-band y≈572–650 på 720p).
- **Uppgradering till frames-exakt:** kör `whisper audio/A1.wav --word_timestamps True --output_format json` och byt proportionell fördelning motverkliga stämplar. (Vi körde proportionellt — bra, inte perfekt.)

**Caption-zon-regeln: grafik under y≈540 krockar captions. ALDRIG placera kort/text där efter blockstart+0.5s.** (Casa Loma-buggen: label på y=545 satt PÅ "weeks later, he". Fix: y=385.)

---

<a name="6-scen--grafik"></a>
## 6. SCEN- & GRAFIKSYSTEMET

`make_assets.py` bygger:
- **Cirkelporträtt** (`circle_portrait`): beskär kvadrat → cirkelmask → skugga + ring (vit/lila). = sunnyv2:s Photoshop-cirklar.
- **Textkort** (`text_card`): stor vit text med svart kontur + skugga, ev. röd accent + grå subrad. = name reveals / memes / bevis.
- **Fotokort** (`photo_card`): rundade hörn + röd ram + skugga. = plats/beweis-foton.
- **particles.png** (två lager, små + bokeh) och **vignette.png**.

`build_video.py`-helpers:
- `still(path, hold)` → input-index (ALLTID via denna — manuell index-hållning saboterade grafen en gång).
- `overlay(idx, T0, T1, x, y, w, fin, fout)` → fade+setpts+enable och lägger i overlays-listan.
- `ease(T0,D,a,b)` = smoothstep (F9/Easy Ease), `back=True` = easeOutBack (slam/bounce, k=1.70158).
- Klipp fås egen kedja: `scale→setsar→format=rgba→drawbox(ram)→setpts→fade` + `overlay=(W-w)/2`.
- Bakgrund: `zoompan z=min(1+0.00006*on,1.45)` på 2560×1440-upscale = sunnyv2:s "infinite zoom"-light.
- Blixtar: vit color-input med fade-in 0.06/out 0.18 per punkt = "Dip to white"/kamerablixt.
- Endast EN overlay klistras på i taget: `[bg][ov1]overlay[v0];[v0][ov2]overlay[v1]...` — kedjan byggs i loop.

**Ny scen för ny topic = 3 rader:** `i = still(g("card_x.png"), d+1); overlay(i, s+dt, s+slut, ease(...), "y", w=...)`. Kopiera mönster från existerande.

---

<a name="7-klipp"></a>
## 7. KLIPP

**Sök:**
```bash
yt-dlp --no-warnings --flat-playlist --print "%(id)s | %(duration)s | %(title)s" "ytsearch6:DRAKE BARKING KICK"
```
Välj: korta (30–90 s), nyhetskanaler (TMZ, E! News), reactions (iShowSpeed), original-stream.

**Ladda + mux (utan ffprobe fallback yt-dlps merge — därför separata streams + egen mux):**
```bash
yt-dlp --no-warnings -f "bv*[height<=480][ext=mp4]+ba[ext=m4a]/b[height<=480]" -o "%(id)s.%(ext)s" URL
ffmpeg -y -v error -i ID.f397.mp4 -i ID.f140.m4a -c copy -movflags +faststart name.mp4
```

**Hitta ögonblicken:** (a) grep kontaktblad `grid_*.jpg` var 2 s; (b) **RMS-analys** för ljudhöjdpunkter (skället låg på 6.5–7.0 s i bark.mp4):
```python
out = subprocess.run(["ffmpeg","-i","bark.mp4","-map","0:a","-ac","1","-ar","8000","-f","s16le","-"], capture_output=True).stdout
x = np.frombuffer(out, dtype=np.int16).astype(np.float32)/32768
rms per 0.5 s -> topp = ögonblicket
```

**I build_video.py — CLIPS-listan:**
```python
{"f":"bark.mp4","cut":5.5,"dur":6.5,"t":s4+18.3,"w":920,"y":60,"vol":1.40}
# fil, cut=var i källan, dur, t=timeline-start (KOPPLA TILL REPLIKEN!), w, y, vol (klipp-ljud >1 = höj)
```
Repliken ska PEEKA: "Here's the moment." → klippet startar ~0.3 s efter. Klipp-ljud sänk ALDRIG under 0.75 — ducka dronen istället.

**Licens:** klipp/bilder från sök = endast demo/utbildning. För publicering: fair-use-bedömning själv / licensierat (Epidemic Sound för musik).

---

<a name="8-sound-design"></a>
## 8. SOUND DESIGN (alla syntetiska = noll copyright)

```python
# IMPACT/BOOM (vid slam-ins, klipp-start): 52 Hz sinus med exp-decay + 110 Hz-slag
"aevalsrc=exprs='0.85*sin(2*PI*52*t)*exp(-5.5*t)+0.30*sin(2*PI*110*t)*exp(-8*t)':s=44100"  # 1.6s, vol 0.55, adelay

# WHOOSH: risers kort variant / klipp-ankomst: samma som riser men 0.6s + vol 0.35

# RISER (2.4 s FÖRE stor reveal — start = reveal_tid - 2.4):
"aevalsrc=exprs='0.16*sin(2*PI*(160+260*t)*t)+0.10*sin(2*PI*(90+40*t)*t)':s=44100"  # afade in 2.2

# MUSIK/DRONE: 49 Hz + 49.5 Hz (bult) + 98 + 196.8 (svällning via 0.05 Hz-LFO), lowpass 400
# DUCKNING under klipp (frame-eval):
volume='if(between(t,{t0},{t1})+between(t,...),0.10,0.30)':eval=frame
# MIX: alla inputs -> amix=inputs=N:normalize=0 -> alimiter=limit=0.92
```
Nivåer (kontrolleras med astats): peak ≈ −3 dBFS, RMS ≈ −18…−21 dBFS; klipp-RMS ska vara tydligt över drone-RMS (vår mätning: 0.13–0.16 vs 0.097).

---

<a name="9-buggar--fixar"></a>
## 9. ALLA BUGGAR VI SPRANG PÅ + FIXAR (lär dig — undvik samma)

| # | Bugg/symptom | Orsak | FIX |
|---|---|---|---|
| 1 | `Invalid argument` / två kedjor läser samma input | bg-inputen ökade aldrig `ix` → alla index försköts | ALLA `-i` MÅSTE öka räknaren; använd `still()`-helpern överallt |
| 2 | `Numerical result out of range` vid parse | `tremolo=f=0.07` (min 0.1) | ta bort tremolo; lägg svällning i aevalsrc-uttrycket |
| 3 | `TypeError: expected str ... not list` | variabelkollision `CLIPS` (katalog vs lista) | döp om katalogen till `CLIPDIR` |
| 4 | `UnboundLocalError: inputs` | `still()` saknade `global inputs, ix` | lägg till globals i helpern |
| 5 | Dubbla/ogiltiga overlay-taggar | `[ov{ix}]`-räknare delad med input-index | egen `ox`-räknare för overlay-taggar |
| 6 | ffmpeg saknas efter ny session | installerade paket persists inte | install-blocket i steg 0, varje gång |
| 7 | yt-dlp "merge"-fel / inga muxade filer | ingen ffprobe i miljön | ladda separata streams + `ffmpeg -c copy`-mux själv |
| 8 | Nedladdade klipp försvann | snapshot-flakiness mellan svagna | ner+mux+probe i ETT bash-anrop; `ls`-verifiera |
| 9 | Kort ovanpå captions (Casa Loma) | y=545 hamnade i caption-bandet | håll grafik över y≈540 när captions syns; label flyttad till 385 |
| 10 | Parallella edit-filer mot samma fil | senaste skrivningen vann, den andra tappades | redigera SEKVENTIELT, en edit per fil per tur |
| 11 | Regex-rensning åt funktioner | girig multi-line regex i py-patch | ändra via edit_file/tydliga ankare, aldrig breda regex-svep |
| 12 | Image-search träffar var fel/stock | autotillit | `read_file` VARJE bild innan använd |
| 13 | Klipp-ljud "saknades" | glömt separat audio-input per klipp | klipp läggs in TVÅ gånger: video (filterad) + audio (atrim+adelay) |
| 14 | `generate_speech`-tak nås | >10 clips per tur | planera ≤8 block; ev. rest nästa tur |

---

<a name="10-qa-protokoll"></a>
## 10. QA-PROTOKOLL (gör detta EFTER VARJE render)

1. **Duration/streams:** `ffmpeg -i ut.mp4 2>&1 | grep -E "Duration|Stream"` — förväntat: ~3:00+, h264 1280x720 + aac 44100 stereo.
2. **QA-sheet:** 9–12 stills rutnät med tidsstämplar (script finns i git-historiken/preview) — titta på VARJE ruta: krockar? tomma ytor? läsbarhet?
3. **Ljud-RMS på fönster:** drone-only-vs-klipp (skript i §7-modellen) + `astats` peak/RMS helhet.
4. **Fackligt-öga-checklista:** förändras bilden var 2–6 s? stämmer klipp mot replik? cards i caption-zon? fade out sista sekunderna?
5. Fixa → rendera om (endast ~4–5 min) → upprepa. Vi körde 3 iterationer på 3-minutaren.

---

<a name="11-github"></a>
## 11. GITHUB

Repo: `sunnyv2youtube` (privat). Push-mönster (token ALDRIG i filer — bara transient i push-URL, och rotera den!):
```bash
cd /home/user/drake-video && git init -b main && git add -A && git commit -m "v3"
git remote add origin https://<TOKEN>@github.com/<USER>/sunnyv2youtube.git
git push -u origin main && git remote set-url origin https://github.com/<USER>/sunnyv2youtube.git
```

*Byggd av agent-pipeline v3 — sunnyv2-metoden: keyframes + easing är allt; klipp med ljud är vad som gör det till en dokumentär.*
