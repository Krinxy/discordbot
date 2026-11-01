class PlexParser:
    @staticmethod
    def parse(payload):
        event = payload.get("event", "unknown")
        metadata = payload.get("Metadata") or {}
        show_title = metadata.get("grandparentTitle")
        title = metadata.get("title", "Unknown item")
        full_title = f"{show_title} - {title}" if show_title else title
        account = (payload.get("Account") or {}).get("title")
        description = f"Triggered by {account}" if account else event
        return f"Plex: {event}", f"{full_title}\n{description}"
