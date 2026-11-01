import configparser
from pathlib import Path

import yaml


class Settings:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.config_dir = self.base_dir / "config"
        self.config_path = self.config_dir / "config.ini"
        self.yaml_path = self.config_dir / "config.yaml"
        self.ini = configparser.ConfigParser()
        self.ini.read(self.config_path, encoding="utf-8")
        self.yaml = self._load_yaml(self.yaml_path)

    @staticmethod
    def _load_yaml(path):
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    @property
    def token(self):
        return self.ini.get("BotConfig", "Token")

    @property
    def reminder_user_ids(self):
        raw = self.ini.get("BotConfig", "ReminderUserIds", fallback="")
        return [int(value) for value in raw.split(",") if value.strip()]

    @property
    def admin_api_key(self):
        return self.ini.get("BotConfig", "AdminApiKey", fallback=None)

    @property
    def blacklisted_ticket_user_ids(self):
        raw = self.ini.get("Tickets", "BlacklistedUserIds", fallback="")
        return {int(value) for value in raw.split(",") if value.strip()}

    @property
    def twitch_client_id(self):
        return self.ini.get("Twitch", "ClientId", fallback=None)

    @property
    def twitch_client_secret(self):
        return self.ini.get("Twitch", "ClientSecret", fallback=None)

    @property
    def watchlist_export_token(self):
        return self.ini.get("BotConfig", "WatchlistExportToken", fallback=None)

    def get(self, *path, default=None):
        value = self.yaml
        try:
            for key in path:
                value = value[key]
        except (KeyError, TypeError):
            return default
        return value
