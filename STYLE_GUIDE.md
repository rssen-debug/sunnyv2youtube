# STYLE_GUIDE.md — Stilreglerna (1:1, använd som prompt för VARJE ny video)

> Detta är huvudprompten som alla videor i repot ska följa. Kopiera texten nedan rakt av
> när du (agenten) får uppdraget: *"Repot sunnyv2youtube, läs PIPELINE.md + STYLE_GUIDE.md,
> skapa nu en video om [TREND HÄR]"*. Byggmanualen (hur reglerna implementerats i ffmpeg)
> ligger i **PIPELINE.md**.

---

Create a highly engaging modern YouTube documentary video about an internet personality, creator, streamer, celebrity, company, controversy, or internet phenomenon.

## STYLE:

- Fast-paced internet documentary / video essay
- Strong storytelling rather than a traditional news-documentary format
- Dark, cinematic, slightly mysterious atmosphere
- Constant visual movement so the screen never feels static
- Mix real photographs, video clips, screenshots, social-media posts, headlines, tweets/posts, websites, memes, charts and AI-generated cinematic visuals
- Use subtle zooms, pans, parallax, camera movement and motion graphics on still images
- Frequently change visuals to match what is being said
- Use occasional dramatic visual emphasis for important moments
- Keep the editing clean and intentional rather than chaotic

## STORY STRUCTURE:

1. OPEN WITH A STRONG HOOK
   Start with the most interesting or surprising part of the story.
   Immediately create a question the viewer wants answered.
2. SET UP THE CHARACTER
   Quickly explain who the person is and why they matter.
   Avoid unnecessary background information.
3. THE RISE
   Show how their career, channel, business or reputation grew.
   Use a chronological progression with increasingly interesting events.
4. THE TURNING POINT
   Introduce the event, decision, controversy or mistake that changed everything.
5. ESCALATION
   Increase the stakes.
   Reveal new information gradually rather than explaining everything at once.
6. CONSEQUENCES
   Show what happened afterward and how the audience, career, business or public image changed.
7. END WITH A STRONG PAYOFF
   Bring the story back to the opening hook.
   Leave the viewer with a memorable final fact, development or unanswered question.

## EDITING:

- Change visuals frequently, approximately every 2–6 seconds depending on narration.
- Synchronize visuals tightly with the narration.
- Use screenshots when discussing online events.
- Highlight relevant text with animated crops, zooms or callouts.
- Use newspaper headlines, social-media posts, comments and website screenshots as visual evidence.
- Use B-roll to illustrate what the narrator is discussing.
- Use AI-generated cinematic shots only when real footage or photographs are unavailable or when visualization improves the storytelling.
- Use occasional memes or humorous visual interruptions when appropriate.
- Avoid excessive transitions; prefer hard cuts, zooms, fades and motivated camera movement.
- Build intensity as the story progresses.

## SOUND DESIGN:

- Professional documentary narration.
- Background music should continuously support the emotional tone without overpowering narration.
- Use subtle risers, impacts, glitches, clicks, whooshes and environmental sounds.
- Increase sound intensity during major reveals.
- Briefly reduce or remove music before important statements to create tension.

## VOICE:

- Calm, confident narrator.
- Conversational rather than formal news-anchor delivery.
- Speak clearly and relatively quickly.
- Use pauses before important revelations.
- The narration should feel like someone telling the viewer an unbelievable story rather than reading an encyclopedia.

## VISUAL PHILOSOPHY:

Every sentence should have a visual reason to exist.

Do not simply put one image on screen while the narrator talks.
Instead, continuously construct the story visually using:
photographs → clips → screenshots → social posts → headlines → graphics → maps → AI visuals → animated stills → close-ups → reaction images.

The final result should feel like a professionally edited internet documentary designed to maximize viewer retention while still being coherent, factual and visually interesting.

---

## Hur reglerna är implementerade i repot (snabbkopia från PIPELINE.md)

| Regel | Implementation |
|---|---|
| Hook → karaktär → rise → turning point → escalation → consequences → payoff | Manus-mall `script/script.txt` (A1 hook, A2–A3 karaktär/rise, A4 turning point, A5 eskalering, B1–B2 konsekvenser, A6 payoff + CTA) |
| Visual change var 2–6 s | Scen-systemet i `build_video.py`: 3–5 beats per block (cards, circles, klipp, titlar) |
| Klipp med ljud, synkat till replik | `CLIPS`-listan + repliker som pekar ("Here's the moment." → klipp 0,3 s senare) |
| Screenshots/headlines/tweets som bevis | `text_card()`-kort med citat + image_search-screenshots i `assets/src/` |
| AI-visuals endast vid behov | `bg_ai.png` + recreations (`clip_recreation.png`) — bara när riktigt material saknas |
| Dark cinematic + konstant rörelse | `bg_ai.png` + infinite-zoom (`zoompan`) + partiklar + vinjett |
| Kamerablixt/dramatisk emphasis | Vit flash-overlay (dip to white) vid reveals |
| Risers/impacts/whooshes | Syntetiska `aevalsrc`-formler (§8 i PIPELINE.md), risers 2,4 s före reveal |
| Musik aldrig över VO; duckning | Drone 0,30 vol; `volume='if(between(...),0.10,0.30)':eval=frame` under klipp |
| Paus inför reveals | "..." i manuset → TTS-paus + tystnad före impact |
| Calm confident narrator | add_voice: masculin, en-GB, narration |
