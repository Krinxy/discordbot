import time


class Router:
    def __init__(self, metrics):
        self.metrics = metrics
        self.handlers = {}

    def add(self, name, func):
        if name in self.handlers:
            raise ValueError(f"Route already registered: {name}")
        self.handlers[name] = func

    def get(self, name):
        return self.handlers[name]

    async def dispatch(self, name, interaction, **params):
        start = time.perf_counter()
        success = True
        try:
            await self.handlers[name](interaction, **params)
        except Exception:
            success = False
            raise
        finally:
            self.metrics.record(name, time.perf_counter() - start, success)
