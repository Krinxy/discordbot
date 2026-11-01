# discordbot

"Mois D Zois" — a Discord bot for channel watching, RSS feeds (YouTube uploads, news), music playback (YouTube via yt-dlp + FFmpeg), and a reaction-driven ticket workflow.

## What's essential to run it

1. `pip install -e .` (editable install from `pyproject.toml` — no separate `requirements.txt`)
2. FFmpeg installed on the host (music playback shells out to it — not a pip package).
3. Discord Developer Portal: enable the **Message Content** and **Server Members** privileged intents on your application.
4. `config/config.ini` (gitignored, create it yourself):
   ```ini
   [BotConfig]
   Token = your-bot-token
   AuthPepper = a-long-random-secret
   ReminderUserIds = optional-comma-separated-discord-user-ids
   AdminApiKey = optional-long-random-secret
   WatchlistExportToken = optional-long-random-secret

   [Twitch]
   ClientId = optional-twitch-app-client-id
   ClientSecret = optional-twitch-app-client-secret
   ```
   `Token` and `AuthPepper` are required — without a pepper, `/mois` and all admin/ticket actions deny everyone (see "Auth" below). `ReminderUserIds` is optional; see "Ticket reminders" below. `AdminApiKey` is optional; see "Admin API / web frontend" below — without it, the admin API still starts but denies every request. `WatchlistExportToken` and `[Twitch]` are both optional; see "Watchlist export" and "Twitch live announcements" below — either feature just stays disabled (one `CRITICAL` log line at startup, nothing crashes) until its values are filled in.
5. `config/config.yaml` — copy `config/config.example.yaml` to this path first (the real file is gitignored). Watched channels, ticket emojis/timers, RSS poll interval. Comes with one example watched channel — edit it to match your server. RSS feeds themselves are managed at runtime (see "RSS feeds" below), not in this file.
6. `config/auth.json` — copy `config/auth.example.json` to this path first (the real file is gitignored). It starts with empty `users`/`roles`, meaning **nobody** is authorized, including you. You must add yourself before any `/mois` command works (see "Adding an authorized user" below).
7. `python main.py`

## Auth

`/mois` commands, ticket status changes, and a couple of admin actions are gated by `@Auth.instance().user` (`dependencies/auth/core.py`), not a plaintext ID list. Discord user IDs are never stored or logged as-is — only `HMAC-SHA256(AuthPepper, user_id)`, so the list in `config/auth.json` is meaningless to anyone without the pepper, even with full repo + database access.

Consequences of that design, worth knowing before you touch it:

- `config/auth.json`, `config/config.yaml` and `config/config.ini` are all gitignored; only the `*.example.*` templates are committed.
- If `AuthPepper` is missing, or `config/auth.json` is missing/invalid, the bot still starts — auth just denies everyone. Check the logs for a `CRITICAL` line from the `auth` logger if `/mois` stops responding.
- `config/auth.json` starting with empty `users`/`roles` means **nobody** is authorized, including you. You have to add yourself.
- Already-authorized users additionally get a per-user cooldown (`auth.json`'s `cooldown_seconds`, default 2s) — rapid repeat calls get "please wait a moment" instead of going through.

Role-based access (`config/auth.json`'s `roles` list) stays a plain list of role IDs — role membership is already visible to anyone in the server, so hashing it wouldn't hide anything. This is deliberately not exposed as a Discord slash command (e.g. no `/mois adduser`) — managing who is privileged happens out-of-band, on the machine running the bot, never from inside Discord itself, so a compromised or coerced Discord session can't grant itself access.

### Adding an authorized user

1. Get their Discord user ID (right-click their name in Discord with Developer Mode on → "Copy User ID").
2. Hash it with your own pepper:
   ```
   python -c "from dependencies.auth import Auth; print(Auth.instance().hash_id(THEIR_DISCORD_ID))"
   ```
3. Add the printed hash to `config/auth.json`'s `users` list.
4. Restart the bot (`python main.py`, or your process manager / container restart) — the policy file is only read at startup, there is no live reload.
5. Clear your shell history afterwards — step 2 puts the raw ID and its hash side by side in plaintext, which together with a leaked pepper is the whole secret.

### Removing an authorized user

1. Compute the same hash again (step 2 above) for the person you're removing.
2. Delete that hash from `config/auth.json`'s `users` list.
3. Restart the bot.

If they were also listed in `ReminderUserIds`, remove their ID from that comma-separated value in `config/config.ini` too — otherwise the next startup's cross-check just drops them from reminders silently (see below) rather than DM someone no longer authorized.

## Ticket reminders

Ticket channels (`config/config.yaml`'s `watch.channels` entries with `tickets: true`) run a small status workflow via emoji reactions: open → operation → closed → archive, plus a side status `currently_not_possible`. When a ticket is set to `currently_not_possible`, the bot doesn't just leave it — every `reminder_interval_days` (default 2) it DMs **every designated recipient** to check whether it's still not possible, each with their own button to snooze it another `reminder_interval_days` if the answer is still no. Snoozing (or resolving the ticket's status directly in the channel) is per-**ticket**, not per-recipient — the first person to act clears the reminder for everyone else too, nobody has to duplicate the check.

Those recipients are `ReminderUserIds` in `config/config.ini`, a comma-separated list of real, unhashed Discord user IDs — but each one must **also** appear in `config/auth.json`'s `users` list (hashed, same as any other authorized user). `Tickets` checks this once at startup, per ID: any ID that doesn't hash to an entry in `auth.json` (or if auth itself is disabled) is silently dropped from the list and one `CRITICAL` line is logged — the bot never DMs an ID that isn't independently confirmed authorized. The rest of the list still gets reminders even if one entry fails this check. So: to receive reminders, a person's hash needs to be in `auth.json` too (follow "Adding an authorized user" above for them, then add their real ID to `ReminderUserIds`).

## RSS feeds

Feeds live in `config/bot.db`'s `rss_feeds` table (via `RssRepository`), not in `config.yaml` — add, disable, or re-enable them through the admin frontend's RSS panel (`/services/rss`), which takes effect on the next poll, no restart needed. `config/config.yaml`'s `rss.poll_seconds` (default 900) is still the only feed-related YAML setting.

For a YouTube channel's upload feed, the feed `url` is always `https://www.youtube.com/feeds/videos.xml?channel_id=<their channel ID>` (not their @handle — the channel ID, found in their channel's "About" page or a channel-ID lookup tool). The feed's `channel_id` field is the **Discord** channel the bot posts new items into.

A feed URL is rejected (400) if it isn't `http(s)` or resolves to a non-public IP — the same SSRF check `/mois music play` already applies to links, shared via `dependencies/url_safety.py::UrlSafety`, since a feed URL is admin-API-supplied input the bot fetches unattended on a timer.

`rss_seen` (the dedup log of already-posted items) is pruned on every poll — rows older than `rss.retention_days` (default 90) are deleted, so this table doesn't grow forever on a small SD card.

## Free games

`services/announcements/free_games/` polls the Epic Games Store's and Steam's public storefront endpoints (no API key needed) every `free_games.poll_seconds` (default 3600) and posts anything currently free to `free_games.channel_id` in `config/config.yaml`. Stays silent (logs one `CRITICAL` line at startup) until `channel_id` is set to a real Discord channel ID. Same retention pruning as RSS: `free_games.retention_days` (default 90).

## Twitch live announcements

`services/announcements/twitch_watch/` polls the Twitch Helix API for the channels listed in `config/config.yaml`'s `twitch.channels` (each entry: `login`, the channel's lowercase URL name, and `channel_id`, where to post) and announces an offline→live transition. Requires a Twitch application's `ClientId`/`ClientSecret` in `config/config.ini`'s `[Twitch]` section (create one at [dev.twitch.tv/console](https://dev.twitch.tv/console) — a "Server-Server" app, no redirect URL needed since this uses the client-credentials flow) — without both plus at least one configured channel, the service logs one `CRITICAL` line at startup and never starts polling.

## Birthdays

Self-service: anyone can run `/mois birthday <month> <day>` — this is the one `/mois` command that needs neither the admin hash nor a role, since it only ever touches the caller's own data. Once a day, `services/announcements/birthdays/` checks for matches against `birthdays.channel_id` (`config/config.yaml`) and posts a congratulation embed. Stays silent until `channel_id` is set.

## Webhook relay

`services/announcements/webhooks/` runs its own small `aiohttp.web` server (separate from the admin API, `webhooks.host`/`webhooks.port` in `config/config.yaml`, default `127.0.0.1:8788`) that accepts webhooks from Sonarr, Radarr, Lidarr, Plex, and Uptime Kuma, plus a `generic` type (`{"title": ..., "description": ...}`) for anything else. Each source is a row in `config/bot.db`'s `webhook_sources` table, managed through the admin API rather than by hand:

```
POST /services/webhooks   {"source_type": "sonarr", "name": "my sonarr", "channel_id": 123456789012345678}
```
returns the row plus a one-time `secret` and the full webhook URL (`/webhook/sonarr/<secret>`) — paste that URL into the source app's own webhook/notification settings (Sonarr/Radarr/Lidarr: Settings → Connect; Plex: Settings → Webhooks, Plex Pass required; Uptime Kuma: a Notification of type "Webhook"). The secret is per-source and never shown again after creation — deleting and re-adding a source issues a new one. `POST /services/webhooks/{id}/enabled` toggles a source without deleting it.

## IMDb blacklist

`services/media_requests/imdb/` matches ticket content against IMDb before a title is confirmed (see "Watchlist export" below for what happens after). Two independent blacklist dimensions in `config/config.yaml`'s `tickets.blacklist`, both empty (no blocking) by default:

```yaml
tickets:
  blacklist:
    person_names: []   # substring-matched against the candidate's cast/stars string, case-insensitive
    tags: []            # qid values to reject outright: movie, tvSeries, tvMovie, tvMiniSeries, video
```

`person_names` blocks a specific already-matched title (e.g. it stars someone you never want recommended) — the requester gets a distinct "blacklisted" message, not a generic "not found". `tags` blocks by content **type** before a candidate is even built (e.g. `tags: ["tvSeries", "tvMiniSeries"]` to only ever allow movies) — a tag-blocked candidate never reaches the candidate list at all, so from the requester's side it looks identical to "nothing found" rather than getting its own message. This is deliberate: IMDb's free suggestion endpoint (which this uses, no API key) doesn't return a genre field, only a coarse content-type (`qid`) — genre-level blocking would need a second, heavier API call per lookup, which isn't worth it for this bot's scale.

## Watchlist export

The movie recommendation platform lives entirely inside Discord (tickets, IMDb matching). This export is a generic adapter that hands the matched films over to any server of yours that exposes a small HTTP endpoint, so whatever consumes the collection stays outside this repo.

`/mois export_movies` (admin-gated, like `/mois export`) pushes every ticket's IMDb match that's been fully resolved (`status = 'matched'` in `config/bot.db`'s `imdb_matches`, see `services/media_requests/imdb/`) and not yet exported to an external URL you configure, as `POST {"films": [...]}` with `Authorization: Bearer <WatchlistExportToken>`. Set the target in `config/config.yaml`:

```yaml
watchlist_export:
  target_url: "https://your-other-service/api/films"
```
Leaving `target_url` empty (the default) or `WatchlistExportToken` unset in `config/config.ini` keeps the feature disabled — the command then just replies "Nothing new to export." without attempting a request.

## Admin API / web frontend

`services/admin_api/` runs a small `aiohttp.web` server (no extra dependency — `aiohttp` is already required for RSS) alongside the bot, so the app under `frontend/` (Next.js) has real data to show instead of mocks. It binds to `config/config.yaml`'s `admin_api.host`/`admin_api.port` (default `127.0.0.1:8787` — localhost-only unless you deliberately change the host):

```yaml
admin_api:
  host: "127.0.0.1"
  port: 8787
```

Every request needs `Authorization: Bearer <AdminApiKey>` (see `config/config.ini` above) or it gets a `401`; if `AdminApiKey` is unset, the server still starts but denies everyone, same fail-closed pattern as `Auth`. There's no session/login system — this is a single shared secret for a single-admin tool, not a multi-user auth system.

`GET /services` returns a tile for every service, with `on_hold: true` for any service whose import is currently commented out of `orchestrator/bot.py` (this is how RSS shows up as "on hold" today — no separate flag to maintain, toggling it back on in `bot.py` is the only thing that changes the tile). `tickets`, `watcher`, `transfer`, and `log` (the message log) have real detail endpoints under `/services/<slug>`; the rest return a placeholder until they get one.

Running behind Docker: the container needs `-p 8787:8787` published and `admin_api.host` set to `"0.0.0.0"` in the mounted `config.yaml`, since `127.0.0.1` inside a container isn't reachable from the host otherwise.

See `frontend/README.md` for running the web dashboard itself.

## System logs

Not to be confused with "Message Log" above (that's Discord message delete/edit logging) — **System Logs** is the bot's own application/operational log, viewable at the frontend's `/services/system_logs` (`/logs` redirects there) so you can see what's actually running/erroring without needing a shell on the host. `dependencies/logger/buffer_handler.py::BufferHandler` is a bounded in-memory ring buffer (`deque(maxlen=500)`, no file, no new dependency) attached to the root logger in `Logging.setup()` — it captures every `zois.*` logger (every service) plus `discord`/`aiohttp` at their configured levels. Served via `GET /services/logs` on the admin API, same auth as every other admin endpoint.

Deliberately **not** a file or a database table: it resets on every restart, and 500 entries is small enough to stay effectively free on a Raspberry Pi's RAM — this is a live "what's happening right now" view, not a durable audit log (see `config/deploy/docker-compose.yml`'s recommendation to check `docker compose logs` for anything you need to keep across restarts).

## Music playback (`/mois music play`)

Only YouTube links are accepted (`services/voice/music/util.py::resolve_music_target`) — a link to any other host is rejected outright, and the video ID is extracted and used to rebuild a clean YouTube URL ourselves rather than forwarding whatever the user pasted, which closes off domain-confusion tricks (`youtube.com.evil.com`, `evil.com/youtube.com/...`) that a naive "contains youtube.com" check would miss. Paste a link with `https://` in front — a bare `youtube.com/...` without a scheme is rejected with a hint to add it, rather than being silently searched for as text. Anything that isn't URL-shaped at all (no recognizable link) is instead searched on YouTube directly, same as typing a song name into YouTube's search bar.

## Dynamic voice channels

Off by default (`config/config.yaml`'s `voice_channels.categories` starts empty). When configured, the bot keeps exactly one empty "overflow" voice channel available in a category, on top of whatever fixed channels are already there:

```yaml
voice_channels:
  check_interval_seconds: 300
  categories:
    - category_id: 123456789012345678
      max_generic_channels: 10
      name_pool: ["Mois", "Anis", "Sun Diego", "Eduard"]
      max_creations_per_user: 2
```

`category_id` is the category the fixed channels already live in. `name_pool` is used in order (`Mois`, `Anis`, `Sun Diego`, `Eduard`), then cycled with a number once exhausted (`Mois 2`, `Anis 2`, ...) up to `max_generic_channels`. The bot only ever touches a channel whose **current name** exactly matches something from this pool — never your fixed channels, never the AFK channel, and never a bot-created channel you've since renamed (renaming one removes it from the bot's bookkeeping permanently, on purpose). Deleting one of these from a live server is a one-way action, so double-check `category_id` before enabling this.

`max_creations_per_user` (default 2) is spam protection: it caps how many channel creations one person can trigger within one `check_interval_seconds` window by rapidly joining/leaving — the overall `max_generic_channels` cap alone only limits the total count, not how fast one user can churn through create/delete cycles. Hitting the limit just means that user doesn't get a new spare channel for the rest of the window; nothing breaks, no message is sent (there's no natural reply channel for a voice join anyway).

## Message/data growth

The ticket and watched-channel data lives in SQLite (`config/bot.db`) and doesn't grow unbounded on Discord's side: once a closed ticket passes `archive_after_days`, its Discord message is deleted from the channel (so the live channel never accumulates old tickets) — only a database row survives, marked `status = 'archive'`. A ticket row is a few hundred bytes; even tens of thousands of archived tickets stay in the single-digit megabytes. At the scale this bot is built for (not a 10k-member server), this isn't something you need to actively manage.

## Deployment

Non-Docker: `python main.py` on the host, with `config/` populated as above. Restart the process to pick up config changes.

Docker: `config/deploy/build_image.sh` (bash) or `config/deploy/build_image.ps1` (PowerShell) build the image — always run one of these rather than a manual `docker build`, so the build command can't drift between machines. `config/` is never baked into the image (see `.dockerignore`); it's declared a `VOLUME` and must be supplied at `docker run` time:

```
docker run -v /path/to/your/config:/app/config mois-d-zois
```

That host `config/` directory needs the same contents as the non-Docker setup above (`config.ini`, `config.yaml`, `auth.json`). Restart the container to pick up config changes — there's still no live reload, Docker or not.

Not built yet: automated CI-triggered image builds/pushes, and a real HTTP health-check layer (`orchestrator/registry.py`'s service registry exists as the seam for that later, see `CLAUDE.md`'s "Service registry" section).

## Docker Compose (Raspberry Pi / multi-service host)

The single-container setup above still works standalone, but the intended way to run everything together (bot, admin frontend, and monitoring) — especially on a Raspberry Pi that's meant to host several unrelated projects over time — is `config/deploy/docker-compose.yml`, orchestrated through `pnpm` from the repo root. It lives under `config/deploy/` alongside the existing `Dockerfile`/`build_image.*` (deploy tooling, not config data — see `CLAUDE.md`'s "Docker" section), same as how `config/.env` (the one piece of compose-related *data*, a secret) sits directly under `config/` next to `config.ini`/`auth.json` rather than in `deploy/`.

1. **One-time**: create the shared Docker network any compose stack on the host can join — this one and any future, unrelated project:
   ```
   docker network create edge
   ```
2. Copy `config/.env.example` to `config/.env` and fill in `ADMIN_API_KEY` — it must be the exact same value as `config/config.ini`'s `AdminApiKey`. Both `.env` and `.env.example` are covered by the repo's `.gitignore`/documented as config data, same tier as `config.ini`.
3. In `config/config.yaml`, set `admin_api.host` and `webhooks.host` to `"0.0.0.0"` — required in Docker, since Traefik/other containers can't reach a loopback-only bind (see the comments next to both in `config.yaml`).
4. `pnpm install` once at the repo root (this is a pnpm workspace — `frontend/` is its one member; `node_modules/` at every level stays pnpm-managed on the host and is never bind-mounted into a container, so a container's own internally-installed `node_modules` can never clash with the host's), then:
   ```
   pnpm dc:up       # docker compose up -d --build
   pnpm dc:logs     # docker compose logs -f
   pnpm dc:ps       # docker compose ps
   pnpm dc:restart  # docker compose restart
   pnpm dc:down     # docker compose down --remove-orphans
   ```
   Each script already points at `config/deploy/docker-compose.yml` and `config/.env` — run them from the repo root, no extra flags needed. `dc:down` also drops any leftover/renamed containers (`--remove-orphans`) but deliberately never touches the named `kuma-data` volume, so Uptime Kuma's monitor history and settings survive a `dc:down`/`dc:up` cycle.

What's in the stack:

- **`traefik`** — reverse proxy on port 80, the single entry point for everything below. Only containers with `traefik.enable=true` are ever routed (`--providers.docker.exposedbydefault=false`), so future, unrelated services sharing the `edge` network don't get accidentally exposed just by existing.
- **`bot`** — same image as the standalone Dockerfile above, reachable through Traefik at `http://<pi-ip>/admin/...` (the admin API — `/admin` is stripped before reaching the container, so it still sees `/services/...`, `/metrics`) and `http://<pi-ip>/webhook/<source>/<secret>` (the webhook relay — no prefix stripping, since `services/announcements/webhooks/core.py`'s own routes already start with `/webhook/`; this is the exact URL you paste into Sonarr/Radarr/etc., see "Webhook relay" above).
- **`frontend`** — the admin dashboard, at `http://<pi-ip>/` (catch-all route, lowest Traefik priority so it never shadows `/admin` or `/webhook`). Talks to `bot` directly over the internal Docker network (`http://bot:8787`), never through Traefik, via `ADMIN_API_BASE_URL`/`ADMIN_API_KEY` env vars set in `docker-compose.yml`.
- **`uptime-kuma`** — monitoring, published directly on its own port (`http://<pi-ip>:3001`), deliberately **not** routed through Traefik: Kuma's own docs don't reliably support being served from a subpath behind a reverse proxy, so it gets a dedicated port instead of fighting that. Add HTTP monitors for `http://bot:8787/metrics` and `http://frontend:3000` (Kuma reaches both by their Docker service name, same network) and point Kuma's built-in **Webhook** notification type at your webhook relay URL (`http://bot:8788/webhook/uptime_kuma/<secret>`, created the same way as any other source — see "Webhook relay" above) to get down/up alerts posted straight into Discord via `UptimeKumaParser`.

Not included on purpose: TLS/HTTPS. Traefik only listens on port 80 for now — encrypting these endpoints is a deliberate, separate piece of future work, not something bolted on ad hoc here.

## Resource footprint (Raspberry Pi)

This stack is built to run on a Raspberry Pi (assume a Pi 4/5, 4-8GB RAM) as one of several services on the box, so every piece here was checked against "does this grow without bound" and "how much RAM/disk does it actually need" — not just "does it work."

**In-memory state** — everything the bot keeps in RAM is bounded by design: `Metrics` prunes each call's history to a rolling 30-minute window, `Auth`'s per-user cooldown tracking is bounded by the tiny number of authorized admins in `auth.json`, `Birthdays`' daily dedup set clears itself every day, and `VoiceChannels`' per-user creation-throttle tracking now deletes its own entry once a user's rate-limit window expires (instead of leaving a permanent empty entry behind — a real, if small, per-user leak that's now fixed). discord.py's gateway intents (`orchestrator/bot.py::_build_intents`) are already the minimum this bot actually needs, nothing extra.

**Container memory limits** — `config/deploy/docker-compose.yml` sets `mem_limit`/`cpus` on every one of the 4 services (`traefik` 128m/0.5, `bot` 384m/1.0, `frontend` 256m/0.5, `uptime-kuma` 256m/0.5 — about 1GB reserved total), so one misbehaving container (most likely `bot`, if an `ffmpeg`/`yt-dlp` subprocess spikes) can't starve the others on a memory-constrained box.

**Image size** — `frontend/Dockerfile` builds on `node:20-alpine` (all three stages, with `libc6-compat` for `sharp`'s native bindings — the same pattern Next.js's own official Docker example uses) instead of `node:20-slim`, roughly 180MB → 50MB of base image. `config/deploy/Dockerfile` (the bot) **deliberately stays on `python:3.11-slim`, not alpine** — `pyproject.toml`'s `PyNaCl` dependency needs libsodium and has a history of being unreliable to build against musl libc (Alpine) without a prebuilt wheel; the image-size win isn't worth risking a failing/slow build on the Pi's own CPU.

**Disk growth** — `rss_seen`/`free_games_seen` (pure insert-only dedup logs) are now pruned on every poll via `rss.retention_days`/`free_games.retention_days` (both default 90 days, see "RSS feeds"/"Free games" above) instead of growing forever. `twitch_stream_state`/`webhook_sources` don't need this — they upsert in place. Ticket rows are kept forever by design even after archival (already documented in "Message/data growth" above — stays small at this bot's scale). Uptime Kuma keeps its own heartbeat history inside the `kuma-data` volume; set a conservative retention under its own **Settings → Monitor History** (not something this repo controls) so that doesn't grow unbounded either.

**Build/deploy hygiene**: prefer **not** building images on the Pi itself — `pnpm dc:up --build` compiles pip/pnpm/Next.js on the Pi's own limited CPU and SD card every time. For anything beyond quick local iteration, cross-build on a real machine (`docker buildx build --platform linux/arm64 ...`) and load or push the finished image to the Pi instead. Repeated `--build` runs also leave dangling intermediate layers/images behind — run `docker image prune -f` occasionally to reclaim that space (deliberately **not** `docker system prune --volumes`, which would also delete the named `kuma-data` volume and wipe Uptime Kuma's history).
