import re
from urllib.parse import parse_qs, urlparse

from dependencies.url_safety import UrlSafety


class MusicLinkResolver:
    def __init__(self):
        self.youtube_hosts = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
        self.youtube_short_host = "youtu.be"
        self.bare_youtube_pattern = re.compile(r"^(www\.|m\.|music\.)?youtube\.com/|^youtu\.be/", re.IGNORECASE)
        self.video_id_pattern = re.compile(r"^[A-Za-z0-9_-]{11}$")

    @staticmethod
    def is_safe(link):
        parsed = urlparse(link)
        if not parsed.scheme:
            return True
        return UrlSafety.is_safe(link)

    @staticmethod
    def _video_id_from_query(parsed):
        values = parse_qs(parsed.query).get("v", [])
        return values[0] if len(values) == 1 else None

    @staticmethod
    def _video_id_from_path(parsed, prefix):
        remainder = parsed.path[len(prefix):]
        segment = remainder.split("/")[0]
        return segment or None

    def resolve(self, text):
        stripped = text.strip()
        parsed = urlparse(stripped)
        if not parsed.scheme:
            if self.bare_youtube_pattern.match(stripped):
                raise ValueError("youtube links need an explicit https:// prefix")
            return stripped
        hostname = parsed.hostname or ""
        if hostname in self.youtube_hosts and parsed.path == "/watch":
            video_id = self._video_id_from_query(parsed)
        elif hostname in self.youtube_hosts and parsed.path.startswith("/shorts/"):
            video_id = self._video_id_from_path(parsed, "/shorts/")
        elif hostname == self.youtube_short_host:
            video_id = self._video_id_from_path(parsed, "/")
        else:
            video_id = None
        if video_id is None or not self.video_id_pattern.match(video_id):
            raise ValueError("only youtube links are allowed")
        return f"https://www.youtube.com/watch?v={video_id}"
