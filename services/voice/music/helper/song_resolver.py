import asyncio

import yt_dlp

from services.voice.music.util import MusicLinkResolver


class SongResolver:
    def __init__(self):
        self.link_resolver = MusicLinkResolver()
        self.ytdlp_options = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "default_search": "ytsearch",
        }

    async def resolve(self, link):
        target = self.link_resolver.resolve(link)
        if not self.link_resolver.is_safe(target):
            raise ValueError("unsafe link")
        loop = asyncio.get_running_loop()
        with yt_dlp.YoutubeDL(self.ytdlp_options) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(target, download=False))
        if "entries" in info:
            info = info["entries"][0]
        return info["url"], info.get("title", link)
