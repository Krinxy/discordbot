class LidarrParser:
    @staticmethod
    def parse(payload):
        event_type = payload.get("eventType")
        artist = payload.get("artist") or {}
        artist_name = artist.get("name", "Unknown artist")
        albums = payload.get("albums") or []
        album_names = ", ".join(album.get("title", "") for album in albums) or "a new release"
        if event_type == "Download":
            return f"New music: {artist_name}", f"{album_names} is now available."
        if event_type == "Test":
            return "Lidarr test event", "The webhook connection to Lidarr is working."
        return f"Lidarr: {event_type}", artist_name
