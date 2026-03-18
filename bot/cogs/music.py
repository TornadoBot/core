from asyncio import TimeoutError

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
    async def join(self, ctx: CustomApplicationContext) -> None:
        """Joins a voice channel."""

        if ctx.author.voice is None:
            await ctx.respond(
                ":cross: **_Error_**\n"
                "You are not in a **voice channel**\n"
                "→ Join one and run `/join` again"
            )
            return

        await ctx.defer()

        destination = ctx.author.voice.channel
        try:
            voice = await destination.connect()
        except TimeoutError:
            await ctx.respond(
                ":cross: **Connection failed_**\n"
                f"Could not join {destination.mention}"
            )
            return
        except ClientException:
            channel = ctx.guild.voice_client.channel

            if channel == destination:
                await ctx.respond(
                    ":check2: **_Already here_**\n"
                    f"Connected to {channel.mention}"
                )
                return

            await ctx.respond(
                ":attention: **_Already connected_**\n"
                f"Currently in {channel.mention}"
            )
            return

        player: Player = Player(ctx)
        player.voice = voice
        self.set_player(ctx.guild.id, player)

        await ctx.respond(
            f":check2: **_Connected_** to {destination.mention}\n"
            f"**Ready to play music.** Use `/play`"
        )

    @slash_command()
    async def play(self, ctx: CustomApplicationContext, search: str):
        """Play a song."""

        # TODO: Add detailed feedback
        # TODO: Add support for other search types
        # TODO: Improve parameter documentation
        # TODO: Add automatic join

        player: Player = self._audio_players.get(ctx.guild.id)
        player.put(Song(search, ctx.author))
        await ctx.respond(
            ":check: **_URL added_**\n"
            f"{search}"
        )

def setup(bot: TornadoBot) -> None:
    bot.add_cog(Music(bot))
