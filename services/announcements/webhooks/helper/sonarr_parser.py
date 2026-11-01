class SonarrParser:
    @staticmethod
    def parse(payload):
        event_type = payload.get("eventType")
        series = payload.get("series") or {}
        series_title = series.get("title", "Unknown series")
        if event_type == "Download":
            episodes = payload.get("episodes") or []
            names = ", ".join(f"S{e.get('seasonNumber')}E{e.get('episodeNumber')}" for e in episodes)
            return f"New episode: {series_title}", names or "A new episode is available."
        if event_type == "Test":
            return "Sonarr test event", "The webhook connection to Sonarr is working."
        return f"Sonarr: {event_type}", series_title
