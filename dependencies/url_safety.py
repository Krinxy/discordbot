import ipaddress
import socket
from urllib.parse import urlparse


class UrlSafety:
    @staticmethod
    def is_safe(url):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        try:
            infos = socket.getaddrinfo(hostname, None)
        except OSError:
            return False
        return all(ipaddress.ip_address(info[4][0]).is_global for info in infos)
