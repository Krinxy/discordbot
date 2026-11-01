import hashlib


class ContentHasher:
    @staticmethod
    def hash(content):
        normalized = " ".join(content.strip().lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
