from orchestrator.registry import ServiceRegistry


class ServiceManifest:
    def __init__(self):
        self.entries = {
            "/tickets": {
                "slug": "tickets", "title": "Tickets",
                "description": "Reaction-driven support ticket queue.", "icon": "Ticket",
            },
            "/watcher": {
                "slug": "watcher", "title": "Channel Watch",
                "description": "Logged messages from watched channels.", "icon": "Eye",
            },
            "/transfer": {
                "slug": "transfer", "title": "Transfer",
                "description": "Export queued requests to JSON.", "icon": "Upload",
            },
            "/message_log": {
                "slug": "log", "title": "Message Log",
                "description": "Per-guild deleted/edited message log channel.", "icon": "FileText",
            },
            "/music": {
                "slug": "music", "title": "Music",
                "description": "Voice channel playback via yt-dlp.", "icon": "Music",
            },
            "/voice_channels": {
                "slug": "voice_channels", "title": "Voice Channels",
                "description": "Auto-managed overflow voice channels.", "icon": "Users",
            },
            "/backfill": {
                "slug": "backfill", "title": "Backfill",
                "description": "Catches up missed messages and tickets on a timer.", "icon": "History",
            },
            "/imdb": {
                "slug": "imdb", "title": "IMDb Matching",
                "description": "Matches ticket content to IMDb titles.", "icon": "Film",
            },
            "/rss": {
                "slug": "rss", "title": "RSS Feeds",
                "description": "Polls RSS/Atom feeds and posts new items.", "icon": "Rss",
            },
            "/free_games": {
                "slug": "free_games", "title": "Free Games",
                "description": "Watches Epic Games Store and Steam for free games.", "icon": "Gift",
            },
            "/twitch_watch": {
                "slug": "twitch_watch", "title": "Twitch Watch",
                "description": "Announces when configured Twitch channels go live.", "icon": "Radio",
            },
            "/birthdays": {
                "slug": "birthdays", "title": "Birthdays",
                "description": "Self-service birthday tracking with daily announcements.", "icon": "Cake",
            },
            "/webhooks": {
                "slug": "webhooks", "title": "Webhook Relay",
                "description": "Relays Sonarr/Radarr/Lidarr/Plex/Uptime Kuma events to Discord.",
                "icon": "Webhook",
            },
            "/watchlist_export": {
                "slug": "watchlist_export", "title": "Watchlist Export",
                "description": "Pushes matched IMDb tickets to an external API.", "icon": "Send",
            },
            "/logging": {
                "slug": "system_logs", "title": "System Logs",
                "description": "Recent application log lines from every service in this process.",
                "icon": "Terminal",
            },
        }

    def tiles(self):
        active_routes = ServiceRegistry.instance().routes
        return [
            {**meta, "on_hold": path not in active_routes}
            for path, meta in self.entries.items()
        ]

    def tile_by_slug(self, slug):
        return next((tile for tile in self.tiles() if tile["slug"] == slug), None)
