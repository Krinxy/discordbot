import re
from urllib.parse import urlparse


class ImdbLinkResolver:
    def __init__(self):
        self.imdb_hosts = {"imdb.com", "www.imdb.com"}
        self.title_id_pattern = re.compile(r"tt\d+")

    def resolve(self, text):
        parsed = urlparse(text.strip())
        if parsed.scheme not in ("http", "https") or parsed.hostname not in self.imdb_hosts:
            return None
        match = self.title_id_pattern.search(parsed.path)
        return match.group(0) if match else None
