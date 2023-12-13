import asyncio
import itertools
import random

import discord
from async_timeout import timeout
from discord.ext import commands

from logs import loggers
from musicbot.general import initial_config
from musicbot.sources import SongSource

logger = loggers.createLogger('main.audioplayer')


class VoiceError(Exception):
    pass


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: discord.ext.commands.Context) -> None:
        self.bot = bot
        self.channel_id = initial_config['channels'][str(ctx.guild.id)]
        self.ctx = ctx
        self.channel = bot.get_channel(self.channel_id)

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        logger.debug(f"audio_player_task started")
        while True:
            self.next.clear()
            try:
                async with timeout(180):
                    # If the music player is not looping, get the next song. Otherwise, it keeps the old song.
                    if self.current and self.loop:
                        logger.debug(f"The current song is now looping. Keeping the same 'self.current' value.")
                        self.current = self.current
                    else:
                        logger.debug(f"Waiting for a new song in queue...")
                        self.current = await self.songs.get()
                        logger.debug(f"New song found in queue!")
            except asyncio.TimeoutError:
                # Clears the music player if it times out.
                logger.debug(f"No song found. Timed out.")
                self.bot.loop.create_task(self.stop())
                self.current = None
                logger.debug(f"Assuming audio_player_task ended here")
                continue

            logger.debug(f"Exited try loop.")
            source = await SongSource.create_source(self.current.raw_name)
            self.current.source = source
            self.current.source.volume = self._volume

            self.voice.play(self.current.source, after=self.play_next_song)

            await self.channel.send(embed=self.current.embed)

            logger.debug(f"Waiting for song to finish...")
            await self.next.wait()
            logger.debug(f"Song finished!")

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            self.voice.stop()
            await self.voice.disconnect()
            self.voice = None

        return
