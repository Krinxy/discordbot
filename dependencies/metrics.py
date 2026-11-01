import time
from collections import defaultdict, deque


class Metrics:
    def __init__(self, recent_window_seconds=1800, bucket_seconds=60):
        self.started_at = time.monotonic()
        self.recent_window_seconds = recent_window_seconds
        self.bucket_seconds = bucket_seconds
        self.calls = defaultdict(lambda: {
            "count": 0,
            "errors": 0,
            "total_duration": 0.0,
            "last_duration": 0.0,
            "last_called_at": None,
            "recent_calls": deque(),
        })

    def _prune(self, recent_calls, now):
        cutoff = now - self.recent_window_seconds
        while recent_calls and recent_calls[0][0] < cutoff:
            recent_calls.popleft()

    def _history(self, recent_calls, now):
        bucket_count = self.recent_window_seconds // self.bucket_seconds
        start = now - self.recent_window_seconds
        buckets = [{"t": int(start + i * self.bucket_seconds), "count": 0, "errors": 0} for i in range(bucket_count)]
        for called_at, success in recent_calls:
            index = int((called_at - start) // self.bucket_seconds)
            if 0 <= index < bucket_count:
                buckets[index]["count"] += 1
                if not success:
                    buckets[index]["errors"] += 1
        return buckets

    def record(self, name, duration, success):
        entry = self.calls[name]
        entry["count"] += 1
        if not success:
            entry["errors"] += 1
        entry["total_duration"] += duration
        entry["last_duration"] = duration
        now = time.time()
        entry["last_called_at"] = now
        entry["recent_calls"].append((now, success))
        self._prune(entry["recent_calls"], now)

    @property
    def uptime_seconds(self):
        return time.monotonic() - self.started_at

    @property
    def snapshot(self):
        now = time.time()
        calls = {}
        for name, entry in self.calls.items():
            self._prune(entry["recent_calls"], now)
            calls[name] = {
                "count": entry["count"],
                "errors": entry["errors"],
                "avg_duration_ms": round((entry["total_duration"] / entry["count"]) * 1000, 2) if entry["count"] else 0,
                "last_duration_ms": round(entry["last_duration"] * 1000, 2),
                "last_called_at": entry["last_called_at"],
                "recent_count": len(entry["recent_calls"]),
                "history": self._history(entry["recent_calls"], now),
            }
        return {
            "uptime_seconds": self.uptime_seconds,
            "recent_window_seconds": self.recent_window_seconds,
            "bucket_seconds": self.bucket_seconds,
            "calls": calls,
        }
