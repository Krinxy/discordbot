class RadarrParser:
    @staticmethod
    def parse(payload):
        event_type = payload.get("eventType")
        movie = payload.get("movie") or {}
        title = movie.get("title", "Unknown movie")
        year = movie.get("year")
        movie_label = f"{title} ({year})" if year else title
        if event_type == "Download":
            return f"New movie: {movie_label}", "The movie has been downloaded and is available."
        if event_type == "Test":
            return "Radarr test event", "The webhook connection to Radarr is working."
        return f"Radarr: {event_type}", movie_label
