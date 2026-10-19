# Copy-ready scene prompts

Use with [the production kit](google-vids-production.md). Total planned duration: **3:12**, with **24 × 8-second scenes**, **10 avatar scenes** and **14 actual recordings**.

The avatar is the one you already selected. Each avatar prompt below is self-contained: attach the same avatar and approved background references, then paste the complete block into AI video mode. If you use dedicated AI avatar mode, paste **only the quoted dialogue** into its script field and keep the remaining text as visual/edit direction. Dedicated avatar mode may not expose lens and movement settings.

Evidence scenes have capture/edit specifications instead of generative-video prompts. They are real software recordings with the same avatar voice as narration. Lens: not applicable to screen capture. Use these specifications in the editor, not as instructions to fabricate a UI.

Every scene is planned for eight seconds. Start speech around 0.35 seconds and finish naturally by about 7.5 seconds. Actual timing can differ. If a line overruns in the chosen voice, use its shorter version or shorten its introductory pause. Do not accelerate speech until it sounds unnatural.


## 01 · The hook · 0:00–0:08

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-01.txt](prompts/scene-01.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 50 mm full-frame equivalent, f/2.8 intent; chest-up medium shot, eye-level camera. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: One almost imperceptible straight push-in, no more than three percent over eight seconds; no lateral movement.
PERFORMANCE: Begin with relaxed shoulders and an attentive expression; make one small open-palm gesture, then settle.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "A support bot should know when it has an answer, and when it needs to ask."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “A useful support bot knows when to answer, and when to ask.”

## 02 · What this project is · 0:08–0:16

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-02.txt](prompts/scene-02.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 35 mm full-frame equivalent, f/4 intent; waist-up medium shot at the same eye level and axis. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: Locked tripod; no zoom, pan, tilt or focus change.
PERFORMANCE: Stay comfortably centered; use a small inclusive hand gesture on the list, without counting on fingers.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "This project brings policy answers, document checks, conversation context, and support tickets into one service desk."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “Policy answers, document checks, context, and tickets come together in one service desk.”

## 03 · The real service desk · 0:16–0:24

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Run the actual FastAPI application and record its customer page at localhost:8000. Use synthetic data and a masked customer role key.
FRAMING: Full-screen browser capture at 1920×1080, with text large enough to read. Start on the page title and chat/upload panels; use one slow downward scroll to reveal the tickets panel.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Hold the top for two seconds, scroll smoothly during seconds two to five, then hold. No orbit, simulated handheld motion or perspective warp.
NARRATION, exactly: "Here’s the actual interface: ask a question, share a document, or pick up an existing support ticket."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Actual local UI · synthetic data"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 04 · Policy evidence · 0:24–0:32

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-04.txt](prompts/scene-04.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 50 mm full-frame equivalent, f/2.8 intent; chest-up medium shot, eye-level. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: Locked tripod; match scene 01's camera axis.
PERFORMANCE: A small nod on the first sentence; keep the second sentence clear and matter-of-fact.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "Before searching policies, it checks access, dates, and versions. Then the answer has to cite its evidence."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “Access, dates, and versions come first. Then the answer must cite its evidence.”

## 05 · A cited fixture answer · 0:32–0:40

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Run python scripts/demo_t4.py and record the real first supported answer and its citation. This uses FakeClock/FakeLLM; keep that fact visible.
FRAMING: Terminal capture with a neutral dark theme and at least 24-pixel text. Crop to the query, Answer and Citations rows from the actual output.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Static for five seconds, then a small editor crop toward the citation, maximum 110 percent. Do not retype or replace the answer.
NARRATION, exactly: "Here’s an offline demo answer. Its citation shows the document, version, and section behind the response."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Offline fixture demo · FakeClock / FakeLLM"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 06 · Refusing without evidence · 0:40–0:48

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: In the real scripts/demo_t4.py output, record the no-evidence scenario and its actual refusal status.
FRAMING: Same terminal theme and font as scene 05. Show the question, refusal answer and empty citations together.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Locked crop; one editor-added underline or outline can draw attention to Refusal=True. Preserve the original text.
NARRATION, exactly: "And when there’s no supporting policy, this fixture run refuses instead of filling the gap with a guess."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Offline fixture demo · no supporting evidence"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 07 · The retrieval path · 0:48–0:56

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Record the rendered architecture diagram in the actual README, or the corresponding filter code with identifiers visible. This is an architecture explanation, not a live request trace.
FRAMING: Show authorization, applicable dates, latest version and hybrid retrieval in one readable crop.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: One slow editor crop from the filter node toward retrieval, 100 to 108 percent. Keep edges straight.
NARRATION, exactly: "Those filters happen before scoring. Restricted or inactive documents aren’t supposed to become evidence for the current question."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Architecture · filtering before similarity"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 08 · Controlled updates · 0:56–1:04

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-08.txt](prompts/scene-08.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 35 mm full-frame equivalent, f/4 intent; waist-up medium shot, same eye level. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: Locked tripod; no movement.
PERFORMANCE: Rest one hand lightly near the desk; deliver the list naturally, without a formal presentation pose.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "Updating the bot’s knowledge has a checklist too: validate it, check quality, approve it, then wait."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “New knowledge passes validation, quality checks, approval, and a maintenance window.”

## 09 · Maintenance activation · 1:04–1:12

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Run python scripts/demo_t1.py. Record actual lines showing activation blocked at 01:30 and approved activation at 02:00, if the current real output contains them.
FRAMING: Readable terminal crop containing both lines and the script's offline FakeClock/FakeLLM identification.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Hold the blocked line for three seconds; use a single editor emphasis on the activated line for the rest. No altered timestamps.
NARRATION, exactly: "In this simulated day, activation waits outside the window, then proceeds after approval when the configured window opens."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Offline maintenance simulation · FakeClock / FakeLLM"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 10 · Health rollback · 1:12–1:20

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Record the actual health-failure and auto-rollback lines from scripts/demo_t1.py. Do not claim a real provider outage was induced.
FRAMING: Same terminal appearance as scene 09, with the previous and restored ACTIVE version readable.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Static; highlight the restored version using a simple editor outline. Keep the frame steady.
NARRATION, exactly: "A scripted health failure follows, and the active snapshot rolls back. That behavior uses a fake clock."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Offline simulation · scripted health failure"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 11 · From upload to fields · 1:20–1:28

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-11.txt](prompts/scene-11.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 50 mm full-frame equivalent, f/2.8 intent; chest-up medium shot, same eye level. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: Gentle straight push-in, no more than two percent over the whole shot.
PERFORMANCE: Brief glance toward the lower desk area, then maintain eye contact; one small explanatory gesture.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "Documents follow a different path: validate the upload, extract visible fields, and compare them with the customer’s message."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “Validate the upload, extract visible fields, then compare them with the customer's message.”

## 12 · Actual invoice extraction · 1:28–1:36

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Upload tests/fixtures/task2/clean.png through the real UI. For the customer message, use the order/date/amount actually visible in that fixture. Record actual extraction results.
FRAMING: Show the upload filename and returned fields; use a tight crop of the document panel, with text remaining readable.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Hold the input for two seconds and the actual extraction result for six; trim a long processing wait with a clearly ordinary cut.
NARRATION, exactly: "Here, the clean invoice fixture exposes its order, date, and amount. Missing fields should stay empty, never invented."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Actual OCR · synthetic invoice fixture"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 13 · Conflicting information · 1:36–1:44

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Submit the mismatched invoice fixture with a deliberately conflicting synthetic customer message. Record the actual response; retain the original file and message for verification.
FRAMING: Same upload-panel crop as scene 12, showing the compared values and clarification text.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Static result crop with an editor outline around the conflicting pair. Do not generate replacement field values.
NARRATION, exactly: "If the message and invoice disagree, the next step is clarification, with conflicting values shown to the customer."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Actual upload check · conflicting synthetic values"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 14 · Language and context · 1:44–1:52

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-14.txt](prompts/scene-14.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 50 mm full-frame equivalent, f/2.8 intent; chest-up medium shot. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: Locked tripod. Match the approved reference framing precisely.
PERFORMANCE: Use an easy conversational tone and a slight pause after language; keep gestures restrained.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "Conversations can switch language, keep recent context, and protect recognized names and order details while responses are translated."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “Conversations keep context across language changes, while recognized names and order details stay protected.”

## 15 · Corrections win · 1:52–2:00

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Run python -m pytest -v tests/test_task6.py::test_correction_overrides_earlier_value. Record the actual test name and outcome. Show its source assertions if extra context is needed.
FRAMING: Terminal and, optionally, a side-by-side crop of the actual test source. Use readable type, not a generated chat reenactment.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: One cut from the selected test name to its real result. Keep eight seconds total.
NARRATION, exactly: "This test checks an order correction: keep the latest value, and mark the older one as superseded."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Offline automated test · correction handling"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 16 · Entity bytes and isolation · 2:00–2:08

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Run python -m pytest -v tests/test_task6.py::test_entities_preserved_across_languages tests/test_task6.py::test_concurrent_sessions_isolated. Record the real named results.
FRAMING: Show both exact test names and their terminal outcomes at readable scale.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Static capture; no scroll while the names are being read. An editor outline can move once between the two rows.
NARRATION, exactly: "Other tests check order details stay intact, and different customers keep separate conversations, even with simultaneous requests."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Offline tests · entity bytes / concurrent isolation"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 17 · Risk is separate · 2:08–2:16

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-17.txt](prompts/scene-17.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 50 mm full-frame equivalent, f/2.8 intent; chest-up medium shot. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: A restrained straight push-in of two percent, with no angle change.
PERFORMANCE: Become attentive without looking alarmed; keep the sentence calm and direct, with no dramatic expression.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "A calm message can still describe a serious problem. High-risk detection stays separate from the sentiment classifier’s prediction."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “Calm wording can describe serious trouble. Risk detection stays separate from sentiment.”

## 18 · Calm high-risk scenarios · 2:16–2:24

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Run python -m pytest -v tests/test_task5.py::test_calm_account_compromise_escalates tests/test_task5.py::test_calm_duplicate_payment_escalates tests/test_task5.py::test_calm_legal_threat_escalates tests/test_assisted_sentiment.py::test_high_risk_independent_of_provider_positive_label. Record the actual named outcomes.
FRAMING: Record the exact named results; keep high-risk vocabulary and PASS status readable. This is offline contract verification.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Static terminal crop with a single gentle crop shift if needed; no generated alert animation.
NARRATION, exactly: "Calm compromise, duplicate-payment, and legal-threat scenarios have named tests. The escalation decision does not depend on provider sentiment."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Offline tests · separate rule-based high-risk detector"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 19 · A complete handoff · 2:24–2:32

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-19.txt](prompts/scene-19.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 35 mm full-frame equivalent, f/4 intent; waist-up medium shot. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: Locked tripod, on the same side of the axis as earlier wide shots.
PERFORMANCE: Open one palm briefly on questions, then return to a relaxed neutral pose.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "When support needs a ticket, missing details stay as questions. The system shouldn’t invent a customer or order."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “Missing ticket details stay as questions; the system should not invent them.”

## 20 · Ticket draft · 2:32–2:40

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: In the real customer UI, ask for a ticket without supplying all mandatory fields. Record the actual questions and draft; enter synthetic details only.
FRAMING: A readable crop of Your tickets and its missing-field questions. Keep any access key masked or outside the capture.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Hold the missing-field message, then show the completed synthetic form with a hard cut. No fake success overlay.
NARRATION, exactly: "The draft asks for mandatory information first. Supplied details move into the final structured ticket and its handoff."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Actual local UI · synthetic ticket draft"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 21 · Queue and routing · 2:40–2:48

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Submit the completed synthetic ticket in the real UI and record the actual QUEUED state. Use scripts/demo_t3.py for a separately labelled offline SLA explanation if desired.
FRAMING: Ticket ID, issue and actual status in one clear crop. No external email or paging UI.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Static hold. Add one small editor label for local queue, without altering the actual result.
NARRATION, exactly: "With no eligible agent configured, the ticket queues. Routing and service deadlines use configured skills and business hours."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Actual local queue · external delivery not configured"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 22 · Evidence before claims · 2:48–2:56

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-22.txt](prompts/scene-22.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 50 mm full-frame equivalent, f/2.8 intent; chest-up medium shot. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: Locked camera; no dramatic push or rack focus.
PERFORMANCE: Direct, candid delivery; a small pause between sentences, with a neutral expression.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "Tests check how the system behaves. Model quality is a separate question, especially when quotas interrupt evaluation."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “Passing tests do not make a quota-limited model evaluation valid.”

## 23 · Results and limitations · 2:56–3:04

**Mode:** actual screen recording plus matching-avatar voiceover. This block is a capture specification, not a Veo prompt.

```text
DURATION AND FORMAT: Eight seconds, 16:9. Use an actual 1920×1080 screen recording; keep the recording's native frame rate, and let the editor handle the common timeline. One shared avatar voice for narration.
SOURCE / ACTION: Record the current REPORT measured-results table and the actual successful CI workflow. Show T4 12/20 plus INVALID and 10/72 provider failures, T5 fallback 20/48, and translation HTTP 429.
FRAMING: Use two four-second evidence crops: report status, then actual CI/test evidence. Add an editor label with the recorded source commit and date.
LENS / LIGHT: No physical lens or studio lighting applies. Capture the screen directly, with no glare, external camera, artificial depth of field or perspective distortion. Keep the browser/terminal theme consistent within each sequence.
MOVEMENT / EDIT: Two hard cuts only; no rapid scrolling or tiny full-page capture. Keep the invalid-run label beside the 12/20 count.
NARRATION, exactly: "The report keeps the invalid policy run, the fallback score, and translation failures visible, alongside actual test evidence."
AUDIO: Match the selected avatar's saved English voice and accent, conversational, around 140–150 words per minute. Start around 0.35 seconds and finish naturally by about 7.5 seconds. No typing sounds under speech; same low room tone or shared quiet music bed as the full edit.
EDITOR-ADDED LABEL: "Measured evidence · invalid run / fallback / quota limits"
CONTINUITY: Match the previous evidence shot's font and theme. Keep captions inside 5% safe margins, use cream/forest/sage labels, and end on a stable frame for the next hard cut.
EVIDENCE RULE: Preserve actual values, citations, failures and statuses. Label offline tests/demos. Do not generate a fictional success screen or imply live translation succeeded. Hide credentials and local filesystem usernames.
```

## 24 · Close with the repository · 3:04–3:12

**Mode:** existing avatar / generated presenter. **Standalone file:** [scene-24.txt](prompts/scene-24.txt).

```text
Generate one eight-second, 16:9 presenter shot, 24 fps where supported, 1080p if available. No cuts inside the shot. The exact lens numbers below describe visual intent, not guaranteed camera metadata.

Use the exact avatar already selected in this Google Vids document as the identity and voice reference. Preserve its face, body, hair, clothing and accessories; one presenter only. Reuse the approved background reference: a sage wall, pale oak desk at the lower edge, matte closed laptop image-left, terracotta mug image-right, small plant far image-left, warm table lamp far image-right. Keep all prop positions unchanged.

Lighting is identical to the approved reference: large soft 5000 K key from camera-left at 45 degrees and slightly above eye level, broad camera-right fill one stop lower, faint neutral edge light behind image-right, dim 2700 K background practical. Natural skin texture, subtle catchlights, controlled highlights, fixed exposure and white balance. Background slightly darker than the face.

English speech, using the selected avatar's saved voice and existing accent, around 140–150 words per minute. Relaxed and specific, like explaining a useful project to one friend. Dry close voice, quiet room tone, no music, no additional voices. Small natural gestures and blinking. No sales-pitch intonation or formal newsreader posture.

CAMERA AND OPTICS: 50 mm full-frame equivalent, f/2.8 intent; chest-up medium shot. Focus on the avatar's eyes. Natural perspective, mild background blur, level horizon, no autofocus hunting.
CAMERA MOVEMENT: Locked camera; hold a stable composition for the closing card.
PERFORMANCE: Small relaxed smile after speaking; keep the pose steady for the final editor-added repository card.

TIMING: 0.0–0.35 seconds: settle into the shot. Around 0.35–7.5 seconds: speak the following English line once, naturally, with synchronized mouth movement. Keep a small pause where punctuation suggests it; finish the whole sentence. Remaining time: a quiet natural hold.
DIALOGUE, exactly: "The code, setup steps, and evidence are in the repository. It’s a local demo, with its limits documented."

CONTINUITY: Same selected avatar, saved voice, outfit, room, prop positions and light direction as the approved reference and every other presenter shot. Do not invent a different person, accent or location. Keep hands anatomically natural.
PICTURE EXCLUSIONS: No subtitles, logos, readable screens, generated UI, animated statistics, extra people, watermarks added by the prompt, transitions or music. Platform-applied labels remain untouched. Titles/captions are added later in the editor.
```

**Shorter dialogue if needed:** “Explore the code and evidence in the repository. Current status: local demo.”

## Captions and final card

Build captions from the exact narration. Use a clean sans-serif face, 48–56 px on a 1080p canvas, two lines maximum, with a dark translucent backing and 5% margins. These are edit recommendations, not Google controls. Keep captions out of the way of evidence fields.

For scene 24, add this editor-created card after the spoken line, or keep a small static repository label visible throughout that last scene:

Real-Time Gen AI Customer Service Bot  
github.com/rxp017/Real_Time_Gen_AI_Customer_Service_Bot  
Code · Setup · Report · Test evidence  
Current deployment: local demo

Keep mentor attribution in the video description or final credits: extends aslin72/GEN---AI-course, customer_service_chatbot_LLM. The avatar narrates the project; it should not claim to be the original author or a real customer.
