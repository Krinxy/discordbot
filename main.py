from dependencies.logger import Logging
from dependencies.settings import Settings
from orchestrator.bot import MoisBot
from orchestrator.registry import ServiceRegistry


def main():
    Logging.setup()
    Logging.get_logger("main").info("Registered services: %s", ServiceRegistry.instance().summary)
    settings = Settings()
    MoisBot(settings).run(settings.token)


if __name__ == "__main__":
    main()
