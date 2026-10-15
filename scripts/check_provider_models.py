"""Read Google's model inventory using the local key; output metadata only."""

import json
from pathlib import Path

import httpx
from dotenv import dotenv_values


def discover() -> dict[str, object]:
    key = dotenv_values(Path(__file__).resolve().parents[1] / ".env").get("GOOGLE_API_KEY")
    if not key:
        return {"status": "missing_key"}
    models = []
    token = None
    while True:
        params = {"pageSize": 100}
        if token:
            params["pageToken"] = token
        try:
            response = httpx.get("https://generativelanguage.googleapis.com/v1beta/models",
                                 headers={"x-goog-api-key": key}, params=params, timeout=15.0)
        except httpx.RequestError as exc:
            return {"status": "network_error", "error_type": type(exc).__name__}
        if response.status_code != 200:
            return {"status": "api_error", "http_status": response.status_code}
        payload = response.json()
        models.extend(m["name"].removeprefix("models/") for m in payload.get("models", [])
                      if "generateContent" in m.get("supportedGenerationMethods", []))
        token = payload.get("nextPageToken")
        if not token:
            break
    report = {"status": "ok", "generate_content_models": sorted(models),
              "note": "Listing does not establish project billing tier or model quota."}
    path = Path(__file__).resolve().parents[1] / "docs/verification/provider-models.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2))
