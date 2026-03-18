from asyncio import QueueFull
from datetime import datetime
from socket import AF_INET
from typing import Any

from aiohttp import TCPConnector
from discord import Bot, Interaction, ApplicationContext, ApplicationCommandInvokeError, Activity, ActivityType
from discord.ext.tasks import loop

from config.settings import SETTINGS
# from lib.db.database import Database
from lib.logger import get_logger
# from lib.logging import log, save_traceback
# from lib.spotify.api import SpotifyAPI
from lib.utils import shortened

log = get_logger(__name__)


class TornadoBot(Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # connector hier NICHT erstellen
        self._uptime = None
        self._settings = SETTINGS

    async def setup_hook(self) -> None:
        connector = TCPConnector(family=AF_INET)
        self.http.connector = connector


    @property
    def uptime(self) -> datetime | None:
        """Returns the time the bot was started. Might be None if the bot has not yet logged in."""
        return self._uptime

    @property
    def settings(self) -> dict[str, Any]:
        """Returns the settings dictionary."""
        return self._settings

    # @property
    # def spotify(self) -> SpotifyAPI:
    #     """Returns the Spotify API instance."""
    #     return self._spotify

    # @property
    # def database(self) -> Database:
    #     """Returns the database instance."""
    #     return self._database

    @loop(minutes=5)
    async def presence_loop(self) -> None:
        """Updates the bot presence every 5 minutes."""
        await self.wait_until_ready()

        guilds, members = len(self.guilds), len(list(self.get_all_members()))
        message: str = f"{shortened(guilds)} servers | {shortened(members)} users"
        await self.change_presence(
            activity=Activity(type=ActivityType.playing, name=SETTINGS['Version'] + f" | {message}")
        )

    async def on_ready(self) -> None:
        # self._uptime = datetime.utcnow()
        #
        # try:
        #     await load_emojis(self.database, self.guilds)
        # except ValueError:
        #     log("No valid emoji guilds found. Creating new guild...")
        #     try:
        #         guild = await self.create_guild(name=random_hex(6))
        #     except (Forbidden, HTTPException):
        #         log("Failed to create new emoji guild", error=True)
        #     else:
        #         await self.database.add_emoji_guild(guild.id)
        #         log(f"Created new emoji guild {guild.name} ({guild.id})")
        #         await load_emojis(self.database, self.guilds)
        log.info(f"Logged in as {self.user.name} ({self.user.id})")

    # async def on_interaction(self, interaction: Interaction) -> None:
    #     log.info(f"Received interaction {interaction.id} from {interaction.user.name} ({interaction.user.id})")
    #     await self.process_application_commands(interaction, auto_sync=None)

        # if interaction.is_command():
        #     user_stats = await self.database.get_user_stats(interaction.user.id)
        #     user_stats.commands_used += 1
        #     await self.database.set_user_stats(user_stats)

    async def on_application_command_error(
            self,
            ctx: ApplicationContext,
            exception: ApplicationCommandInvokeError
    ) -> None:

        # emoji_cross: Emoji = await self.database.get_emoji("cross")
        if isinstance(exception.original, QueueFull):
            await ctx.respond("{emoji_cross} **Queue is full.**")
            return

        log.error(f"Error while processing interaction {ctx.interaction.id}: {exception.original}")
        await ctx.respond(
            "{emoji_cross} **Error** while **processing command**: `{exception.original.__class__.__name__}`"
        )
        raise exception.original
