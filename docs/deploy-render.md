# Deploy with Render Docker

Use the repository's Dockerfile as a Render web service. Keep the single Uvicorn worker. Set secret environment values in Render's dashboard: `GOOGLE_API_KEY`, `GOOGLE_MODEL=gemini-2.5-flash`, and distinct random role keys from `.env.example`. Leave `GOOGLE_FALLBACK_MODELS` empty until another model has successful generation evidence. Never place these values in Git or frontend assets. Customer keys are entered only into the page's password field; the browser does not persist them.

Set the health-check path to `/health`. `healthy` currently means configured provider credentials/model, not a live provider/quota probe. A new configured empty store imports the preserved training FAQs with metadata. Existing ACTIVE snapshots are not silently overwritten. Ingest domain policies through the existing authenticated knowledge-update workflow; the customer UI has no administrative controls.

Render supplies `PORT` and `RENDER_EXTERNAL_URL`. The Docker command uses that port, and the exact external URL is accepted as an origin. The app also permits same-origin browser requests; other origins are rejected before processing. Use HTTPS. Rate limits are per source IP and hashed credential, Clock-driven and bounded in memory; changing a key does not bypass the IP budget. Upload type/size/decompression/security gates remain enforced server-side. Provider calls remain server-side.

## Free-tier limits

Render Free web services stop after 15 minutes without inbound traffic. While stopped, the in-process scheduler, SLA/escalation timers and upload purge cannot execute. On wake, persisted jobs can catch up only if storage survived. Free service filesystems are ephemeral, and free services cannot attach persistent disks. SQLite tickets, sessions, ACTIVE pointers, uploads and quarantine can be lost across restarts/redeploys. Therefore this deployment is a demonstration, not a durable support service. See [Render Free documentation](https://render.com/docs/free) and [persistent disks](https://render.com/docs/disks).

For durable operation, select an appropriate paid service with a persistent disk at `/app/data`, writable by UID 1000. Default database, upload, quarantine and inbox paths are under that directory. Run one instance and one worker; distributed scheduling and rate-limit coordination are not implemented. Verify write access and retention deletion on the deployed disk before using customer files. External alert delivery remains unconfigured.

## Verification after deployment

1. Open the assigned `https://<service>.onrender.com/` URL signed out. Verify the customer UI and `/health`.
2. With a customer key, send a supported FAQ and inspect its source citation, upload a synthetic invoice, then complete and refresh a ticket. Check ownership using another customer key.
3. Try an unsupported question and malformed file; verify refusal/rejection. Verify an unknown Origin is rejected and burst requests return 429.
4. On durable hosting, restart and confirm state survives. Exercise a maintenance-window activation and FakeClock tests separately; a UI demo alone does not prove the scheduler.

No live deployment URL is recorded until these checks actually run. The GitHub repository and CI run URLs are source/verification links, not a deployed chatbot.
