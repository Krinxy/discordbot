import asyncio

import aiohttp


class Http:
    def __init__(self, limit=5, timeout_seconds=20):
        self.limit = asyncio.Semaphore(limit)
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.session = None

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session

    async def close(self):
        if self.session is not None and not self.session.closed:
            await self.session.close()

    async def get_text(self, url, headers=None):
        session = await self._ensure_session()
        async with self.limit, session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

    async def get_json(self, url, headers=None):
        session = await self._ensure_session()
        async with self.limit, session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json(content_type=None)

    async def post_json(self, url, json_body=None, headers=None):
        session = await self._ensure_session()
        async with self.limit, session.post(url, json=json_body, headers=headers) as response:
            response.raise_for_status()
            return await response.json(content_type=None)
