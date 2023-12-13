import math

import discord
from discord import app_commands
from discord.ext import commands

from logs import loggers
from musicbot.audioplayer import VoiceState
from musicbot.general import bot_name, bot_pfp_url
from musicbot.library import main_library
from musicbot.playlists import main_playlists
from musicbot.songs import Song, parse_id_from_raw_name

logger = loggers.createLogger('main.music_commands')


class MusicCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.embed_color = 0xFFFFFF
        self.voice_states = {}

    def get_voice_state(self, ctx: discord.ext.commands.Context):
        """Creates a voice-state for the music bot."""
        state = VoiceState(self.bot, ctx)
        self.voice_states[ctx.guild.id] = state

        return state

    def interaction_check(self, interaction: discord.Interaction):
        """Prevents the bot from being used in DMs."""
        if not interaction.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels."
            )
        return True

    async def ensure_voice_state(self, interaction: discord.Interaction):
        """Ensures there's an active voice state before any music is played."""
        if not interaction.user or not interaction.user.voice:
            raise commands.CommandError

        ctx = await self.bot.get_context(interaction)
        guild_id = interaction.guild_id

        if not self.voice_states[guild_id]:
            self.voice_states[guild_id] = self.get_voice_state(ctx)

    @app_commands.command(name="join")
    async def _join(self, interaction: discord.Interaction):
        """Connects the music bot to the user's voice channel."""
        await self.ensure_voice_state(interaction)

        guild_id = interaction.guild_id
        voice_state = self.voice_states[guild_id]

        # If there's no voice client yet, create one. Then, move.
        # Bot movement always happens.
        destination = interaction.user.voice.channel
        if not voice_state.voice:
            voice_state.voice = await destination.connect()
            await voice_state.voice.move_to(destination)

            text = f'The music bot has joined {destination.mention}!'
            embed = discord.Embed(title='Music Bot Initialized', description=text, color=0xFFFFFF)
        else:
            if interaction.user != interaction.guild.owner:
                text = f"The music bot is already in {voice_state.voice.channel.mention}."
                embed = discord.Embed(title='Oops!', description=text, color=0xFFFFFF)
            else:
                voice_state.voice = await destination.connect()
                await voice_state.voice.move_to(destination)

                text = f'The music bot was moved to {destination.mention}!'
                embed = discord.Embed(title='Music Bot Initialized', description=text, color=0xFFFFFF)

        embed.set_author(name=bot_name, icon_url=bot_pfp_url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='leave')
    async def _leave(self, interaction: discord.Interaction):
        """Disconnect the music bot from its voice channel."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        if not voice_state.voice:
            text = 'The music bot is not connected to any voice channel.'
            title = 'Oops'
        else:
            await voice_state.stop()
            del voice_state
            self.voice_states[interaction.guild_id] = None

            text = 'The music bot has been disconnected.'
            title = 'Music Bot Disconnected'

        embed = discord.Embed(title=title, description=text, color=0xFFFFFF)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        await interaction.response.send_message(embed=embed)

    play_group = app_commands.Group(name='play', description="Use this to play music")

    @play_group.command(name='song')
    @app_commands.describe(selection='Select a song or search for one by its name, artist, or ID. Or play all')
    @app_commands.autocomplete(selection=main_library.song_raw_names_autocomplete)
    async def _play(self, interaction: discord.Interaction, selection: str):
        """Plays a single song from the library."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        # Connect to a voice channel if the bot has not joined a channel yet.
        # Bot movement sometimes happens.
        if not voice_state.voice:
            destination = interaction.user.voice.channel
            voice_state.voice = await destination.connect()
            await voice_state.voice.move_to(destination)

        song_id = parse_id_from_raw_name(selection)
        song = Song(song_id)
        await voice_state.songs.put(song)

        embed_text = f"Added `{song.title}` to the queue."
        embed = discord.Embed(description=embed_text, color=self.embed_color)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        await interaction.response.send_message(embed=embed)

    @play_group.command(name='all')
    async def _play_all(self, interaction: discord.Interaction) -> None:
        """Plays the entire music library."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        # Connect to a voice channel if the bot has not joined a channel yet.
        # Bot movement sometimes happens.
        if not voice_state.voice:
            destination = interaction.user.voice.channel
            voice_state.voice = await destination.connect()
            await voice_state.voice.move_to(destination)

        all_song_ids = main_library.get_all_song_ids()
        all_songs = []
        for song_id in all_song_ids:
            all_songs.append(Song(song_id))

        for song in all_songs:
            await voice_state.songs.put(song)

        embed_text = f"Added all songs to the queue!"
        embed = discord.Embed(description=embed_text, color=self.embed_color)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        await interaction.response.send_message(embed=embed)

    @play_group.command(name='playlist')
    @app_commands.describe(selection='The playlist to play')
    @app_commands.autocomplete(selection=main_playlists.playlist_choices_autocomplete)
    async def _play_playlist(self, interaction: discord.Interaction, selection: int) -> None:
        """Plays a single playlist from the library."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        # Connect to a voice channel if the bot has not joined a channel yet.
        # Bot movement sometimes happens.
        if not voice_state.voice:
            destination = interaction.user.voice.channel
            voice_state.voice = await destination.connect()
            await voice_state.voice.move_to(destination)

        playlist = main_playlists.playlists_dict[selection]
        for song in playlist.songs:
            await voice_state.songs.put(song)

        embed_text = f"Added `{playlist.name}` to the queue!"
        embed = discord.Embed(description=embed_text, color=self.embed_color)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        await interaction.response.send_message(embed=embed)

    # @play_group.command(name='youtube')
    # @app_commands.describe(selection='The YouTube link to a video or playlist')
    # async def _youtube(self, interaction: discord.Interaction, link: str) -> None:
    #     """Temporarily downloads and plays a temporary YouTube video or playlist"""
    #     await self.ensure_voice_state(interaction)
    #     voice_state = self.voice_states[interaction.guild_id]
    #
    #     if not voice_state.voice:
    #         destination = interaction.user.voice.channel
    #         voice_state.voice = await destination.connect()
    #         await voice_state.voice.move_to(destination)
    #
    #     if 'playlist' in link:
    #         embed_text = f"The bot cannot currently play playlists."
    #         embed = discord.Embed(description=embed_text, color=self.embed_color)
    #         embed.set_author(name=bot_name, icon_url=bot_pfp_url)
    #         return await interaction.response.send_message(embed=embed)

    @app_commands.command(name='volume')
    async def _volume(self, interaction: discord.Interaction, volume: app_commands.Range[int, 0, 100]):
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        """Change the volume of the music bot from 0% to 100%."""
        if volume < 0 or volume > 100:
            error = 'Volume must be a number between 0 and 100. Please try again.'
            embed = discord.Embed(title='Oops!', description=error, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)

            return await interaction.response.send_message(embed=embed)

        voice_state.volume = volume / 100

        text = f"Volume set to {volume}%"
        embed = discord.Embed(description=text, color=0xFFFFFF)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause")
    async def _pause(self, interaction: discord.Interaction):
        """Pause the music bot."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        if voice_state.voice.is_playing():
            voice_state.voice.pause()

            text = "The music bot has been paused."
            embed = discord.Embed(description=text, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)

            await interaction.response.send_message(embed=embed)
        else:
            if voice_state.voice.is_paused():
                error = 'The music bot is already paused.'
            else:
                error = 'No music is being played right now.'

            embed = discord.Embed(title='Oops!', description=error, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resume")
    async def _resume(self, interaction: discord.Interaction):
        """Resume the music bot if paused."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        if voice_state.voice.is_paused():
            voice_state.voice.resume()

            text = "The music bot has now resumed."
            embed = discord.Embed(description=text, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)

            await interaction.response.send_message(embed=embed)
        else:
            if voice_state.voice.is_playing():
                error = 'The music bot is already playing.'
            else:
                error = 'No music is being played right now.'

            embed = discord.Embed(title='Oops!', description=error, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)
            return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stop")
    async def _stop(self, interaction: discord.Interaction):
        """Stops the music bot."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        # Stop any looping
        if voice_state.loop:
            voice_state.loop = False

        voice_state.songs.clear()

        if voice_state.is_playing:
            voice_state.voice.stop()

            text = "The music bot has been stopped and looping has been turned off."
            embed = discord.Embed(description=text, color=0xFFFFFF)

        else:
            error = 'No music is being played right now.'
            embed = discord.Embed(title='Oops!', description=error, color=0xFFFFFF)

        embed.set_author(name=bot_name, icon_url=bot_pfp_url)
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name="skip")
    async def _skip(self, interaction: discord.Interaction):
        """Skips the current song playing."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        if not voice_state.is_playing:
            error = 'No music is being played right now.'
            embed = discord.Embed(title='Oops!', description=error, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)

            return await interaction.response.send_message(embed=embed)

        text = f'Skipped over song.'
        embed = discord.Embed(description=text, color=0xFFFFFF)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        await interaction.response.send_message(embed=embed)

        voice_state.skip()

    @app_commands.command(name="queue")
    @app_commands.describe(page='Enter page')
    async def _queue(self, interaction: discord.Interaction, page: int):
        """Shows the current song queue."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        if len(voice_state.songs) == 0:
            error = 'Looks like the queue is empty.'
            embed = discord.Embed(title='Oops!', description=error, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)

            return await interaction.response.send_message(embed=embed)

        items_per_page = 10
        pages = math.ceil(len(voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        song_names = ""
        artist_names = ""
        for i, song in enumerate(voice_state.songs[start:end], start=start):
            queue_num = i + 1
            song_names += f"`{queue_num}.`  {song.title}\n"
            artist_names += f"`{song.artist}`\n"

        embed = discord.Embed(title=f"Songs in Queue", color=0xFFFFFF)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        embed.add_field(name='Song', value=song_names)
        embed.add_field(name='Artist', value=artist_names)
        embed.set_footer(text=f"Viewing page {page}/{pages}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='loop')
    async def _loop(self, interaction: discord.Interaction):
        """Toggles looping for the current song playing."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        if not voice_state.is_playing:
            error = 'No music is being played right now.'
            embed = discord.Embed(title='Oops!', description=error, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)

            return await interaction.response.send_message(embed=embed)

        voice_state.loop = not voice_state.loop

        if voice_state.loop:
            text = 'The current song will now loop.'
        else:
            text = 'Looping has been turned off for the current song.'

        embed = discord.Embed(description=text, color=0xFFFFFF)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name='shuffle')
    async def _shuffle(self, interaction: discord.Interaction):
        """Shuffles the queue."""
        await self.ensure_voice_state(interaction)
        voice_state = self.voice_states[interaction.guild_id]

        if len(voice_state.songs) == 0:
            error = 'Looks like the queue is empty.'
            embed = discord.Embed(title='Oops!', description=error, color=0xFFFFFF)
            embed.set_author(name=bot_name, icon_url=bot_pfp_url)

            return await interaction.response.send_message(embed=embed)

        voice_state.songs.shuffle()
        text = 'The queue has been shuffled.'
        embed = discord.Embed(description=text, color=0xFFFFFF)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        return await interaction.response.send_message(embed=embed)

    @app_commands.command(name='playlist')
    async def _playlist(self, interaction: discord.Interaction):
        """Shares a link to create a playlist."""
        url_text = "https://docs.google.com/spreadsheets/d/1rbUAug8W87L8kLWXYb44r8JaXIqY6IvhQouidXJEDIQ/edit?usp=sharing"

        text = f"Go to the following google sheet and select your songs. Afterwards, DM Phan with your playlist name and the playlist copypasta." \
               f"\n\n{url_text}"

        embed = discord.Embed(description=text, color=0xFFFFFF)
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        return await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.voice_states[guild.id] = None
        print('=====Bot is online and ready!=====')


async def setup(bot):
    await bot.add_cog(MusicCommands(bot))
