import time
from urllib.parse import urlencode


class TwitchAuth:
    def __init__(self, http, client_id, client_secret):
        self.http = http
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = "https://id.twitch.tv/oauth2/token"
        self.streams_url = "https://api.twitch.tv/helix/streams"
        self.expiry_safety_margin_seconds = 60
        self.token = None
        self.token_expires_at = 0

    async def _refresh_token(self):
        params = urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        })
        data = await self.http.post_json(f"{self.token_url}?{params}")
        self.token = data["access_token"]
        self.token_expires_at = time.time() + data["expires_in"] - self.expiry_safety_margin_seconds

    async def _headers(self):
        if self.token is None or time.time() >= self.token_expires_at:
            await self._refresh_token()
        return {"Client-Id": self.client_id, "Authorization": f"Bearer {self.token}"}

    async def get_live_streams(self, logins):
        params = urlencode([("user_login", login) for login in logins])
        headers = await self._headers()
        data = await self.http.get_json(f"{self.streams_url}?{params}", headers=headers)
        return data.get("data", [])
