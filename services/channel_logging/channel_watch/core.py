from dependencies.logger import log
from orchestrator.registry import ServiceRegistry


@ServiceRegistry.instance().route("/watcher")
class Watcher:
    def __init__(self, db, settings):
        self.db = db
        self.channels = {
            int(entry["channel_id"]): entry["name"]
            for entry in settings.get("watch", "channels", default=[])
        }

    @log
    def handle_message(self, message):
        if (name := self.channels.get(message.channel.id)) is None:
            return False
        if message.author.bot or message.guild is None:
            return False
        self.db.add_watched_message(
            message.guild.id,
            message.channel.id,
            name,
            message.author.id,
            str(message.author),
            message.content[:2000],
            message.id,
        )
        return True
