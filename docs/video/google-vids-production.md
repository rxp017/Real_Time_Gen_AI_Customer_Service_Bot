# Google Vids production kit

Project: Real-Time Gen AI Customer Service Bot. Prepared 19 October 2026.

**Your choices:** Google Vids, the avatar you already selected, English, landscape, approximately three minutes. Keep the selected avatar; this kit does not ask you to create a replacement.

**Delivery plan:** 3 minutes 12 seconds, built from 24 eight-second scenes. Ten presenter scenes use your existing avatar; fourteen scenes show actual software, documents, diagrams or test evidence. The 80 seconds of presenter footage can use generated clips or Vids' dedicated avatar mode. The other 112 seconds are screen recordings.

## 1. What one prompt can produce

Checked against Google's documentation on 19 October 2026:

| Tool / mode | Documented length | How this plan uses it |
| --- | --- | --- |
| Google Vids: Generate video | Current help lists selectable 3–10 second clips. That help page now also refers to Omni. | Select eight seconds when available. Check the model label in your account before calling a clip Veo-generated. |
| Veo 3.1 through Gemini API | Four, six or eight seconds; reference-image generation requires eight seconds. This is an API specification, not a promise about the Vids interface. | Eight seconds is the shared planning unit; this kit does not require the API. |
| Google Vids: dedicated AI avatar | Up to 60 seconds per generated avatar segment, separate from the short video-clip mode. | Enter dialogue in the avatar script field. Generate adjacent short scenes together if preferred, then trim in the editor. |

Sources: [Vids video generation](https://support.google.com/docs/answer/16143507?hl=en), [Veo 3.1 specification](https://ai.google.dev/gemini-api/docs/veo?hl=en), [Vids avatars](https://support.google.com/docs/answer/16334946?hl=en).

Google's Vids article contains both the newer 3–10 second selector description and an older eight-second animation paragraph. Use the duration/model controls actually present in your account. This plan selects eight seconds to avoid depending on the ten-second option. Available models, avatar ingredients and credits vary by account; the kit does not assume a subscription allowance or spend credits.

**Do not paste the whole three-minute script into the short-clip prompt.** Generate one planned scene at a time. Assemble the complete video in the Vids timeline.

## 2. Use the right Vids mode

**Talking avatar scenes:** start with the avatar you already selected and keep its saved voice. Put only the spoken line in the avatar script field; camera, room and lighting notes belong in visual/refinement fields where available. Dedicated avatar mode may not expose lens or camera-motion controls. For that mode, the locked medium shot is the valid fallback.

**Camera-directed generated scenes:** open AI video / Create, select the existing avatar as an ingredient if your account exposes that option, add the approved room reference, select landscape and eight seconds, then paste the complete prompt from [scene-prompts.md](scene-prompts.md).

**Software scenes:** record the real application or repository and upload the recording to Vids. Add narration using the voice matching your selected avatar. Keep text, citations, field values and measured results legible; do not use generative edits on evidence footage.

If the avatar cannot be a video ingredient, use dedicated avatar mode plus actual screen recordings. A written face description cannot guarantee identity across independent generations. Lens, aperture and Kelvin values below are creative direction, not verified capture metadata or guaranteed controls.

## 3. Continuity card

These are production labels, not special model commands.

| Item | Locked choice |
| --- | --- |
| Avatar | The exact selected Vids avatar; unchanged face, hair, body, outfit and accessories |
| Voice | That avatar's saved English voice and accent, also used for screen narration |
| Performance | Casual, direct, interested; talking to one friend, relaxed shoulders, small natural gestures |
| Set | R1: small creative workspace, sage wall, pale oak desk, one plant, matte laptop, warm lamp |
| Light | L1: soft camera-left key, gentle camera-right fill, faint edge light, warm background practical |
| Palette | Deep forest #163c32, sage #dce6d6, cream #f4f4eb, restrained lime #d5ee9b |
| Default camera | Eye-level tripod, 50 mm full-frame equivalent, medium chest-up, f/2.8 intent |
| Alternate camera | 35 mm, medium waist-up, f/4 intent; same side of the camera axis |
| Frame / edit | 16:9, 1920×1080 canvas if available; eight-second scenes and hard cuts |
| Audio | Same voice throughout, around 140–150 words/minute, dry and close; no generated music |
| Text | Add captions, labels and metrics in the editor after generation, inside 5% safe margins |

Reuse the same saved avatar asset. Keep all scenes inside one Vids document and insert keeper clips into the timeline before closing the session. Save the first approved presenter shot as the visual reference for later shots. Repeated direction helps continuity but does not guarantee it.

## 4. Avatar direction — for your existing avatar

Use in an appearance/refinement field only if needed. Keep the selected avatar and voice.

```text
Use the avatar already selected in this Google Vids document. Preserve the exact face, facial proportions, skin tone, hairstyle, body proportions, clothing, accessories and saved voice from that asset. Maintain the same identity across every scene. One presenter only.

The performance feels like a relaxed creator explaining a useful project to a friend: natural posture, comfortable eye contact, small hand movements below shoulder level, a brief smile at the opening and closing. Use ordinary conversational English and the selected voice's existing accent. Avoid a sales-pitch delivery, theatrical surprise, exaggerated nodding and rigid newsreader posture. Keep breathing and blinking subtle.

Frame at eye level in a chest-up medium shot, with hands occasionally visible at the lower edge. Use a natural 50 mm full-frame-equivalent perspective and soft background separation. Preserve the chosen outfit; make the scene casual through delivery, framing and the room.
```

## 5. Background reference prompt — R1

Make or choose this room once. Reuse the approved reference.

```text
Create a photorealistic 16:9 background reference for a casual software-project walkthrough. A small, comfortable creative workspace. Muted sage painted wall; pale oak desk across the lower quarter; matte dark closed laptop at image-left; one terracotta mug at image-right; one small green plant on a low shelf in the far image-left background; a compact warm table lamp in the far image-right background. Keep these positions fixed.

Leave the center clear for the already-selected avatar, with comfortable headroom and a clean area behind the face. No people in this background reference. No readable screens, code, charts, writing, logos, posters or invented interfaces. Lightly lived-in, tidy and believable natural textures. Avoid a boardroom, neon gaming setup and luxury office.

Camera at the future presenter's eye level, 50 mm full-frame-equivalent perspective, f/2.8 depth-of-field intent, level horizon, no fisheye distortion. Soft daylight-style key from camera-left outside the frame, gentle camera-right bounce fill, subtle separation. A dim 2700 K lamp adds a warm patch at far image-right. Natural forest, sage and cream palette. No dramatic haze or glossy highlights. Still reference: no camera movement.
```

## 6. Lighting and camera refinement prompt — L1

Use once on the approved avatar/set reference, or as video direction.

```text
Preserve the selected avatar's identity and approved R1 room. Use a large soft 5000 K key at camera-left, roughly 45 degrees off-axis and slightly above eye level. Use broad camera-right fill about one stop dimmer. Add a very subtle neutral edge light from behind image-right; the small background practical stays warm at 2700 K. The background is slightly darker than the face.

Natural skin texture, visible catchlights, soft shadow edges and controlled highlights. No beauty-filter skin, colored face lighting, hard underlighting, pulsing exposure or changing white balance. Maintain the same lighting direction and perceived exposure across shots.

Eye-level camera, straight verticals, 50 mm full-frame-equivalent lens, f/2.8 intent, focus on the eyes, mild background blur. No autofocus hunting or focus breathing. Static camera unless the individual scene requests a very small push-in.
```

## 7. Exact edit plan — 3:12

Each row is eight seconds. [Scene prompts](scene-prompts.md) contain the complete prompt/capture specification and exact narration for every row.

| Scene | Timeline | Picture | Purpose |
| --- | --- | --- | --- |
| 01 | 0:00–0:08 | Avatar | Hook: answering versus asking for help |
| 02 | 0:08–0:16 | Avatar | What the project brings together |
| 03 | 0:16–0:24 | Real UI | Chat, upload and tickets on one page |
| 04 | 0:24–0:32 | Avatar | Evidence-based policy answers |
| 05 | 0:32–0:40 | Offline demo capture | Fixture answer and citation |
| 06 | 0:40–0:48 | Offline demo capture | Actual refusal without evidence |
| 07 | 0:48–0:56 | Real architecture diagram | Access, date and version filters |
| 08 | 0:56–1:04 | Avatar | Controlled knowledge updates |
| 09 | 1:04–1:12 | Offline maintenance demo | Activation inside the window |
| 10 | 1:12–1:20 | Offline maintenance demo | Scripted health failure and rollback |
| 11 | 1:20–1:28 | Avatar | Document upload and extraction |
| 12 | 1:28–1:36 | Real upload capture | Visible fields from a clean invoice |
| 13 | 1:36–1:44 | Real upload capture | Conflicts ask for clarification |
| 14 | 1:44–1:52 | Avatar | Language and protected context |
| 15 | 1:52–2:00 | Actual offline test capture | Latest corrected order wins |
| 16 | 2:00–2:08 | Actual offline test capture | Entity bytes and session isolation |
| 17 | 2:08–2:16 | Avatar | Calm high-risk messages still matter |
| 18 | 2:16–2:24 | Actual offline test capture | Risk rules independent of sentiment |
| 19 | 2:24–2:32 | Avatar | Handoff without inventing details |
| 20 | 2:32–2:40 | Real ticket capture | Missing fields keep an incomplete draft |
| 21 | 2:40–2:48 | Real ticket capture | Actual queue and local handoff |
| 22 | 2:48–2:56 | Avatar | Tested behavior versus model quality |
| 23 | 2:56–3:04 | Real report and CI | Invalid run, measured results and quota |
| 24 | 3:04–3:12 | Avatar + editor end card | Repository, report and deployment status |

## 8. Generation and assembly order

1. Keep your avatar selected; note its saved English voice. Create one 16:9 Vids document for the full film.
2. Approve the R1 background once. Use L1 to establish the soft, casual look.
3. Generate scene 01 as a pilot. Check identity, outfit, pronunciation, room and voice before making the remaining nine presenter clips.
4. In AI video mode, select eight seconds and attach the same approved references. In dedicated avatar mode, paste only the spoken line and trim the result into its slot. If speech overruns, use the shorter alternate; do not rush the voice.
5. Record actual software with [the capture checklist](../demo-script.md). Retain raw recordings and original outputs; edit for timing and legibility.
6. Add fourteen evidence shots and the matching avatar voice as narration. Screen captures do not use physical lenses; each capture spec states that.
7. Keep eight seconds per scene, including brief breathing handles. Use hard cuts; overlapping dissolves would alter the 3:12 timing.
8. Add captions, labels and repository end card in Vids. Correct any recognition errors against the supplied dialogue.
9. Optional: one quiet instrumental bed in the editor, without vocals and well below speech. Presenter generations contain no separate music.
10. Watch once muted for visual continuity and once with eyes closed for voice continuity. Export and confirm the actual final duration; generation timing can vary.

**Budget target:** ten successful eight-second presenter clips = 80 generated seconds, plus actual recordings. Rerolls and dedicated-avatar generations may count differently. Read the quota shown in Vids; do not infer it from the chatbot API key.

## 9. Final checks

- Same selected avatar, outfit, voice, room props and lighting direction in every presenter shot.
- One short line per shot; no clipped words, unrequested speakers or changing accent.
- Real UI text and results. Offline fixture demonstrations have an editor-added label.
- Show 12/20 policy answers beside **INVALID: 10/72 infrastructure failures**, never as validated accuracy. Sentiment fallback is 20/48. Live translation remains unverified after HTTP 429.
- Identify recorded commit/date for test and CI counts. Current public deployment status: not deployed.
- Keep credentials out of recordings. Use synthetic customers and a masked customer key.
- Captions fit the frame. Spell the project name, repository owner and mentor attribution correctly.

This is a production plan and prompt kit. No video generation, paid credit use, avatar creation or upload to Google has been performed here.
