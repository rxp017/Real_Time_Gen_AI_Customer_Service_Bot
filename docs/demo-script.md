# Capture checklist for the 3:12 walkthrough

Use [the Google Vids production kit](video/google-vids-production.md) and [all 24 scene specifications](video/scene-prompts.md). The user selected English, landscape and an existing avatar. The plan contains ten eight-second presenter scenes and fourteen eight-second actual recordings.

## Record real material first

Use synthetic customer data. Enter any customer role key before recording and keep the field masked. Keep provider keys, environment files, browser autofill and local filesystem usernames out of frame. In a temporary PowerShell recording session, a simple prompt can remove the full working-directory path:

```powershell
function prompt { 'bot-demo> ' }
```

Record which commit and date each terminal/CI clip shows. Do not change actual output, timestamps, field values or statuses in the editor.

## Capture sources

| Scenes | Source | Keep visible |
| --- | --- | --- |
| 03 | Actual customer UI at localhost:8000 | Chat, document upload and tickets; local provider status |
| 05–06 | python scripts/demo_t4.py | Supported fixture answer/citation, then actual no-evidence refusal |
| 07 | Actual rendered README architecture | Access/date/version filters before scoring |
| 09–10 | python scripts/demo_t1.py | Blocked activation, approved maintenance activation and scripted rollback |
| 12–13 | Real UI with tests/fixtures/task2/clean.png and mismatched.png | Actual extracted fields and conflicting values |
| 15 | Actual correction test below | Test name and real outcome |
| 16 | Actual entity/isolation tests below | Named outcomes, labelled offline |
| 18 | Actual risk tests below | Calm-risk cases and provider independence |
| 20–21 | Real customer ticket draft and submission | Missing mandatory fields, then actual status; queue is a local record |
| 23 | REPORT measured-result section and real CI run | Invalid evaluation label, fallback score, quota limits and source commit |

The demo scripts are offline fixture simulations with FakeClock/FakeLLM and actual local storage. Keep that label visible. Actual OCR uses installed Tesseract. UI/provider refusal or quota failure must remain a refusal/failure; do not substitute a generated success.

## Named offline test captures

Use the project's Python 3.11 environment. On Windows, replace python with .\.runtime\python311\python.exe.

```sh
python -m pytest -v tests/test_task6.py::test_correction_overrides_earlier_value
python -m pytest -v tests/test_task6.py::test_entities_preserved_across_languages tests/test_task6.py::test_concurrent_sessions_isolated
python -m pytest -v tests/test_task5.py::test_calm_account_compromise_escalates tests/test_task5.py::test_calm_duplicate_payment_escalates tests/test_task5.py::test_calm_legal_threat_escalates tests/test_assisted_sentiment.py::test_high_risk_independent_of_provider_positive_label
```

Capture what actually runs. Passing offline contracts do not establish general language accuracy, broad risk coverage or live-provider translation quality.

## Evidence frame for scene 23

Use the current report, with enough type size to read:

- Pre-fix exposed sets: T4 3/20 correct-cited; T5 pipeline 22/48.
- Post-fix T4: 12/20 correct-cited and 0/52 false answers, but **INVALID**, with 10/72 infrastructure failures (13.89%) above the registered 10% limit.
- T5 post-fix fallback-only: 20/48. Live post-fix classification was skipped under quota.
- Live translation remains unverified after HTTP 429.
- Verified implementation snapshot ea7a845: 355 passing tests, Ruff clean, Ubuntu/Windows/Docker CI successful. If recording a later successful commit, show its actual identifier and results.

Do not present the invalid run as a validated improvement. Keep the report's development replay numbers separate from live generation.

## Edit and export

Create 24 contiguous eight-second slots in a 16:9 timeline. Generate the ten presenter shots with the already-selected avatar and saved voice, then insert the fourteen recordings with matching-voice narration. Follow each scene's lens intent, framing and movement; actual screen captures use no physical lens.

Use readable captions, restrained forest/sage/cream labels and hard cuts. Current end-card status is **local demo**, with repository and report links. No public live deployment or external helpdesk delivery is claimed. The recording remains planned until the actual export exists and has been checked.
