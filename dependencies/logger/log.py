import functools
import inspect
import time

from dependencies.logger.core import Logging


class log:
    def __init__(self, func):
        self.func = func
        self.is_async = inspect.iscoroutinefunction(func)
        functools.update_wrapper(self, func)

    @staticmethod
    def _logger_for(instance):
        return Logging.get_logger(instance.__class__.__module__)

    async def _call_async(self, instance, *args, **kwargs):
        logger = self._logger_for(instance)
        start = time.perf_counter()
        try:
            return await self.func(instance, *args, **kwargs)
        except Exception:
            logger.exception("%s failed", self.func.__qualname__)
            raise
        finally:
            logger.info("%s took %.3fs", self.func.__qualname__, time.perf_counter() - start)

    def _call_sync(self, instance, *args, **kwargs):
        logger = self._logger_for(instance)
        start = time.perf_counter()
        try:
            return self.func(instance, *args, **kwargs)
        except Exception:
            logger.exception("%s failed", self.func.__qualname__)
            raise
        finally:
            logger.info("%s took %.3fs", self.func.__qualname__, time.perf_counter() - start)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.is_async:
            return functools.partial(self._call_async, instance)
        return functools.partial(self._call_sync, instance)
