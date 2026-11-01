# Mois D Zois — Admin frontend

A small Next.js dashboard for the bot: a grid of tiles (one per `services/*`), styled after the
iCloud web dashboard's app-grid pattern. Click a tile to see or manage that service. Everything on
this page is backed by the bot's real data via `services/admin_api/` (see the main `README.md`) —
there is no mock data.

## Running locally

1. Make sure the bot itself is running with `AdminApiKey` set in `config/config.ini` (see the repo
   root `README.md`'s "Admin API / web frontend" section).
2. Copy `.env.local.example` to `.env.local` and fill in the same key:
   ```
   ADMIN_API_BASE_URL=http://127.0.0.1:8787
   ADMIN_API_KEY=<same value as config/config.ini's AdminApiKey>
   ```
3. `npm install`
4. `npm run dev` and open http://localhost:3000

`ADMIN_API_KEY` is only ever read server-side (Server Components and Server Actions in
`src/app/actions.ts`) — it is never sent to the browser. `src/lib/admin-api.ts` is the single place
that talks to the bot's API; everything else goes through it.

## What's wired up vs. placeholder

`tickets`, `watcher`, `transfer`, and `log` (message log) have real detail views — the rest show a
"coming soon" placeholder until they get one. `rss` shows as "On Hold" automatically, because its
import is commented out in `orchestrator/bot.py`; uncommenting it there flips the tile back to
active without touching this frontend at all.

## Stack

Next.js (App Router) + TypeScript + Tailwind CSS v4 + shadcn/ui + lucide-react icons. No test
framework or extra state library — Server Components fetch data directly, and the two mutations
(export, set log channel) are plain Server Actions (`src/app/actions.ts`).
