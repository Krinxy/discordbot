class GenericParser:
    @staticmethod
    def parse(payload):
        title = payload.get("title")
        if not title:
            return None
        return title, payload.get("description", "")
