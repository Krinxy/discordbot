class UptimeKumaParser:
    @staticmethod
    def parse(payload):
        heartbeat = payload.get("heartbeat") or {}
        monitor = payload.get("monitor") or {}
        monitor_name = monitor.get("name", "Unknown monitor")
        status = "up" if heartbeat.get("status") == 1 else "down"
        message = payload.get("msg", "")
        return f"{monitor_name} is {status}", message
