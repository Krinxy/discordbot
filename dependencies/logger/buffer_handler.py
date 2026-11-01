import logging
from collections import deque
from datetime import datetime, timezone


class BufferHandler(logging.Handler):
    def __init__(self, capacity=500):
        super().__init__()
        self.capacity = capacity
        self.records = deque(maxlen=capacity)

    def emit(self, record):
        self.records.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })

    def snapshot(self, limit=200):
        return list(self.records)[-limit:]
