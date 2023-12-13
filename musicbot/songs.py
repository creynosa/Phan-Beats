import re

import discord

from musicbot.general import bot_name, bot_pfp_url
from musicbot.library import main_library


class Song:
    def __init__(self, song_id, yt_filepath=None):
        self.song_id = int(song_id) if song_id else None

        if self.song_id:
            self.metadata = main_library.library[song_id]
            self.filepath = self.metadata['filepath']
            self.artist = self.metadata['artist']
            self.title = self.metadata['title']
            self.duration = self.metadata['duration']
            self.duration_str = self.metadata['duration_str']
            self.raw_name = self.metadata['raw_name']
        # else:
        #     self.filepath = yt_filepath
        #     self.artist = "Unknown"
        #     self.title = ""
        #     self.duration = ""
        #     self.duration_str = ""
        #     self.raw_name = ""

        self.embed = self.create_embed()

        # TODO: figure out how to add album_art automatically

        # Set when song is called by the music player
        self.source = None
        self.requester = None

    def create_embed(self):
        """Creates and returns an embed detailing a song's information."""
        embed = discord.Embed(
            title="Now Playing",
            color=0xff0000,  # red
        )
        embed.add_field(name='Artist', value=f"```{self.artist}```")
        embed.add_field(name='Title', value=f"```{self.title}```")
        embed.add_field(name='Duration', value=f"```{self.duration_str}```")
        embed.set_author(name=bot_name, icon_url=bot_pfp_url)

        return embed


def parse_id_from_raw_name(raw_name: str) -> int:
    """Returns the song ID from a search string using the song's raw filename."""
    song_id_regex = re.compile(r"\[(\d*)] (.*)")
    match = re.search(song_id_regex, raw_name)
    song_id = int(match.group(1))

    return song_id
