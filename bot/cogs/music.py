from asyncio import TimeoutError, QueueFull

from discord import slash_command, ClientException
from discord.ext.commands import Cog

from bot import TornadoBot
from lib.contexts import CustomApplicationContext
from lib.logger import get_logger
from lib.music.player import Player
from lib.music.song import Song

log = get_logger(__name__)

class Music(Cog):
    def __init__(self, bot: TornadoBot) -> None:
        self.bot = bot
        self._audio_players: dict[int, Player] = {}

    def get_player(self, guild_id: int) -> Player:
        return self._audio_players.get(guild_id)

    def set_player(self, guild_id: int, player: Player) -> None:
        if self._audio_players.get(guild_id) is not None:
            self._audio_players[guild_id].cleanup()
        self._audio_players[guild_id] = player

    @slash_command()
    async def join(self, ctx: CustomApplicationContext) -> bool:
        """Joins a voice channel."""

        if ctx.author.voice is None:
            await ctx.respond(
                ":cross: **_Error_**\n"
                "You are not in a **voice channel**\n"
                "→ Join one and run `/join` again"
            )
            return False

        await ctx.defer()

        destination = ctx.author.voice.channel
        try:
            voice = await destination.connect()
        except TimeoutError:
            await ctx.respond(
                ":cross: **Connection failed_**\n"
                f"Could not join {destination.mention}"
            )
            return False
        except ClientException:
            channel = ctx.guild.voice_client.channel

            if channel == destination:
                await ctx.respond(
                    ":check2: **_Already here_**\n"
                    f"Connected to {channel.mention}"
                )
                return True

            await ctx.respond(
                ":attention: **_Already connected_**\n"
                f"Currently in {channel.mention}"
            )
            return False

        player: Player = Player(ctx)
        player.voice = voice
        self.set_player(ctx.guild.id, player)

        await ctx.respond(
            f":check2: **_Connected_** to {destination.mention}\n"
            f"**Ready to play music.** Use `/play`"
        )
        return True

    @slash_command()
    async def play(self, ctx: CustomApplicationContext, search: str):
        """Play a song."""

        if not await self.join(ctx):
            return

        # TODO: Add detailed feedback
        # TODO: Add support for other search types
        # TODO: Improve parameter documentation

        player: Player = self._audio_players.get(ctx.guild.id)

        try:
            player.put(Song(search, ctx.author))
        except QueueFull:
            await ctx.respond(
                ":cross: **_Error_**\n"
                "The queue is full. Please try again later."
            )
            return
        await ctx.respond(
            ":check: **_URL added_**\n"
            f"{search}"
        )

def setup(bot: TornadoBot) -> None:
    bot.add_cog(Music(bot))
