import configparser
import functools
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from dependencies.auth.policy import AuthPolicy
from dependencies.logger import Logging


class Auth:
    _instance = None

    def __init__(self, base_dir=None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent
        self.config_dir = self.base_dir / "config"
        self.config_path = self.config_dir / "config.ini"
        self.policy_path = self.config_dir / "auth.json"
        self.log = Logging.get_logger("auth")
        self.pepper = self._load_pepper()
        self.policy = self._load_policy()
        self.enabled = self.pepper is not None and self.policy is not None
        self.cooldown_seconds = self.policy.cooldown_seconds if self.policy else 0
        self.last_call_at = {}
        if not self.enabled:
            self.log.critical("auth disabled: pepper=%s policy=%s", self.pepper is not None, self.policy is not None)

    def _load_pepper(self):
        ini = configparser.ConfigParser()
        ini.read(self.config_path, encoding="utf-8")
        pepper = ini.get("BotConfig", "AuthPepper", fallback=None) or os.environ.get("ZOIS_AUTH_PEPPER")
        return pepper.encode("utf-8") if pepper else None

    def _load_policy(self):
        try:
            with open(self.policy_path, encoding="utf-8") as file:
                return AuthPolicy.model_validate(json.load(file))
        except (OSError, ValueError) as error:
            self.log.critical("failed to load auth policy: %s", type(error).__name__)
            return None

    def hash_id(self, discord_id):
        return hmac.new(self.pepper, str(discord_id).encode("utf-8"), hashlib.sha256).hexdigest()

    def is_authorized(self, user_id, role_ids):
        if not self.enabled:
            return False
        if self.hash_id(user_id) in self.policy.users:
            return True
        return bool(set(role_ids) & set(self.policy.roles))

    def _rate_limited(self, hashed_id):
        if not self.cooldown_seconds:
            return False
        now = time.perf_counter()
        last = self.last_call_at.get(hashed_id)
        self.last_call_at[hashed_id] = now
        return last is not None and (now - last) < self.cooldown_seconds

    @staticmethod
    def _extract_identity(args):
        for arg in args[1:]:
            if hasattr(arg, "user_id"):
                member = getattr(arg, "member", None)
                roles = [role.id for role in member.roles] if member else []
                return arg.user_id, roles
            candidate = getattr(arg, "user", None)
            if candidate is not None:
                roles = [role.id for role in getattr(candidate, "roles", [])]
                return candidate.id, roles
        return None, []

    @staticmethod
    async def _deny(args, text):
        response = next(
            (r for arg in args if (r := getattr(arg, "response", None)) and not r.is_done()),
            None,
        )
        if response is not None:
            await response.send_message(text, ephemeral=True)

    def _requires_auth(self, name):
        entry = self.policy.functions.get(name) if self.policy else None
        return entry.auth_required if entry is not None else True

    def _authorize(self, args):
        user_id, role_ids = self._extract_identity(args)
        authorized = user_id is not None and self.is_authorized(user_id, role_ids)
        limited = authorized and self._rate_limited(self.hash_id(user_id))
        return authorized and not limited, limited

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def user(self, func):
        name = func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not self._requires_auth(name):
                return await func(*args, **kwargs)
            start = time.perf_counter()
            allowed, limited = self._authorize(args)
            self.log.info(
                "auth check for %s: %s (%.3fs)",
                name, "granted" if allowed else ("limited" if limited else "denied"), time.perf_counter() - start,
            )
            if not allowed:
                text = "Please wait a moment before trying again." if limited else "No permission."
                await self._deny(args, text)
                return None
            return await func(*args, **kwargs)

        return wrapper
