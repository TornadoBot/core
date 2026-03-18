from os import environ, listdir

from bot import TornadoBot
from config.settings import SETTINGS
from lib.logger import get_logger

log = get_logger(__name__)


def main() -> None:
    """
    Entry point for the TornadoBot application.
    Validates environment variables, loads cogs, and starts the bot.

    :return: None
    """
    if not "DISCORD_TOKEN" in environ.keys():
        log.error("Environment variable DISCORD_TOKEN is not set.")
        return
    bot: TornadoBot = TornadoBot(
        owner_ids=SETTINGS["OwnerIDs"],
        description=SETTINGS["Description"],
        intents=SETTINGS["Intents"],
    )

    for cog in listdir('cogs'):
        if cog.endswith('.py') and not cog.startswith('_'):
            bot.load_extension(f'cogs.{cog[:-3]}')
    bot.run(environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
