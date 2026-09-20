# Senaste avsnittet

**[Half a Billion Subscribers — and He Says He's Broke (MrBeast)](episodes/mrbeast_empire/README.md)** — 20 september 2026, **4:19**, 720p/30 fps, engelsk brittisk berättarröst, fyra originalklipp med ljud, kinetic captions, 3-pass-renderaren, verify_build **PASS**.

[Öppna videon](episodes/mrbeast_empire/mrbeast_empire.mp4) · [Thumbnail](episodes/mrbeast_empire/thumbnail.jpg) · [Manus](episodes/mrbeast_empire/script/script.txt)

Tidigare avsnitt: [The Kick Streamer Rank Dispute](episodes/kick_rank_drama/README.md) (20 sep 2026, 3:41).
Äldre demo nedan är bevarad oförändrad; dess fakta har inte verifierats i den nya produktionen.

---

# sunnyv2youtube — AI-dokumentär-pipeline

**Demo-video:** `drake_goth_girl_sunnyv2.mp4` — "Drake × The Goth Girl (Pinkchyu)" — **3:06**, 1280×720/30fps, engelsk TTS-berättarröst, word-by-word-popcaptions, **riktiga videoklipp med ljud** (bark-ögonblicket, TMZ-interview, E! News, Casa Loma-drone, iShowSpeed-reaction), sound design (impacts, risers, whooshes, musik-duckning), kamerablixtar, cirkelporträtt, name reveals, infinite-zoom-bakgrund.

> **Nästa agent:** läs **[MANDATE.md](MANDATE.md)** (tvångsregler), **[STYLE_GUIDE.md](STYLE_GUIDE.md)** (stil 1:1) och **[PIPELINE.md](PIPELINE.md)** (byggmanual). Säj bara: *"Repot sunnyv2youtube, skapa en video om X."* leveransen MÅSTE passera `python3 scripts/verify_build.py`.

**Studio-Kit v2 (i `scripts/`):**
- `gfx_kit.py` — glow-titlar (Anton), lower thirds, tweet/social-UI-mockups, stat-kort, HUD, light leaks
- `cinema.py` — easing/overshoot, 2.5D-parallax, teal/orange-grade, grain, bloom, letterbox, 90 BPM beat-musik, SFX-formler
- `make_captions.py` — kinetic captions v2 med keyword-highlight (`keywords.txt`)
- `build_poc_v4.py` — POC som demonstrerar HELA kitet (`POC_v4_cinema_kit.mp4`)
- `verify_build.py` — maskinell QA enligt MANDATE.md (REJECTAR bildspels-videor)

## Stilprofil (sunnyv2 / modern internet-dokumentär)
- **Struktur:** hook → karaktär → uppgång → vändpunkt → eskalering → konsekvenser → payoff (bind ihop med hooken) + CTA
- **Tempo:** bildbyte var 2–6 s; varje mening har visuell grund; hård snitt > pratiga övergångar
- **Bevis:** foton, klipp, screenshots, headlines, tweets, kort — med zoom/pan/callout
- **AI-visuals** endast när riktigt material saknas
- **Ljud:** dokumentär-VO (lugn, självsäker, paus inför reveals), musik som stödjer men aldrig överröstar, duckning under klipp, risers/impacts på reveals
- **Filosofi:** varje sekund rör sig. Keyframes + easing är allt.

## Kör om videon från scratch
```bash
# steg 0 i PIPELINE.md §3 först (ffmpeg/yt-dlp install)
python3 scripts/make_assets.py      # GFX-fabrik
python3 scripts/make_captions.py    # timings.json + captions.ass
python3 scripts/build_video.py      # full render (~5 min)
```

## Faktapidrog (källor)
Drake höll "20 women vs 1"-datingstream (NELK/Kick, 8 aug 2026, Stake 9-årsjubileum). **Pinkchyu (Lin Lamar, 23, Texas, 2M+ följare)** plockade fram Magic: The Gathering-kort och frågade **"Would you bark for me?"** — Drake: *"You can look me dead in my eyes, and if you say do anything, I would"* — och skällde (arf arf arf + whimper). Klippet viraliserades (synkat till "Not Like Us"). Hon vann; pris = **hus till mamman**; två veckor senare **Casa Loma** (98-rumsslott, Toronto) för privat sushi. AI-leash-foto → **"Goth's Plan"**-memes. **TMZ:** ännu en "massive musician" skällde i hennes DMs.
Källor: consequence.net, tmz.com, yahoo.com, cassiuslife.com, indiatimes.com, thetab.com, ladbible.com.

## ⚠️ Licens & säkerhet
- Sökbilder/klipp = **endast demo/utbildning**; granska rättigheter före publicering. Musik: byt dronen mot Epidemic Sound/YouTube Audio Library vid publicering.
- **Committa ALDRIG tokens.** Token som skapade repot ska roteras omedelbart efter push.
