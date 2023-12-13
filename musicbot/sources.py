import discord

from musicbot.library import main_library
from musicbot.songs import parse_id_from_raw_name


class SourceError(Exception):
    pass


class SongSource(discord.PCMVolumeTransformer):
    def __init__(self, source: discord.FFmpegPCMAudio, volume: float = 0.5):
        super().__init__(source, volume)

    @classmethod
    async def create_source(cls, search: str):
        """Creates a source of a song to be played."""
        song_id = parse_id_from_raw_name(search)
        song_filepath = main_library.library[song_id]['filepath']

        return cls(discord.FFmpegPCMAudio(str(song_filepath)))

    @classmethod
    async def create_yt_source(cls, temp_filepath: str):
        """Creates a source for a temporarily downloaded YouTube video"""
        return cls(discord.FFmpegPCMAudio(str(temp_filepath)))
