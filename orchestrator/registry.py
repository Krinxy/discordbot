class ServiceRegistry:
    _instance = None

    def __init__(self):
        self.routes = {}

    @property
    def summary(self):
        return ", ".join(sorted(self.routes))

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def route(self, path):
        def decorator(cls):
            self.routes[path] = cls
            return cls

        return decorator
