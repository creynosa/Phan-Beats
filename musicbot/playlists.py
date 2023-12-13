from pathlib import Path
from typing import Optional, List

import discord
import toml
from discord import app_commands

from logs import loggers
from musicbot.songs import Song

logger = loggers.createLogger('main.playlists')


class Playlist:
    def __init__(self, playlist_id: int, playlist_data: dict):
        self.id = playlist_id
        self.data = playlist_data

        self.name = self.data['name']
        self.choice_display_name = f"[{self.id}] {self.name}"
        self.song_ids = self.data['song_ids']
        self.has_songs = False if self.song_ids == [] else True

        self.songs = self.get_playlist_songs()

    def get_playlist_songs(self) -> Optional[list[Song]]:
        """Creates and returns a list of Song objects for the playlist."""
        if self.has_songs:
            songs = []
            for song_id in self.song_ids:
                songs.append(Song(song_id))
            return songs
        else:
            return None


class Playlists:
    def __init__(self):
        self.config_path = Path("musicbot") / "playlists.toml"
        self.config = self.get_config(self.config_path)

        self.playlists_list = self.get_playlists_list()
        self.playlists_dict = self.get_playlists_dict()

    @staticmethod
    def get_config(filepath: Path) -> dict:
        """Returns a dictionary of all music playlist configurations stored in the project."""
        with open(str(filepath), 'r') as f:
            config = toml.load(f)

        return config

    @staticmethod
    def update_config(filepath: Path, updated_config: dict) -> None:
        """Updates the config file with an updated config."""
        with open(str(filepath), 'w') as f:
            toml.dump(updated_config, f)

    def get_playlists_dict(self) -> dict[int, Playlist]:
        """Returns a Playlist object using its playlist ID."""
        config = self.config

        playlists_dict = {}
        for playlist_id, playlist_data in config.items():
            playlist = Playlist(int(playlist_id), playlist_data)
            playlists_dict[int(playlist_id)] = playlist

        return playlists_dict

    def get_playlists_list(self) -> list[Playlist]:
        """Creates and returns a list of all stored playlists as Playlist objects."""
        config = self.config

        playlists_list = []
        for playlist_id, playlist_data in config.items():
            playlist = Playlist(int(playlist_id), playlist_data)
            playlists_list.append(playlist)

        return playlists_list

    async def playlist_choices_autocomplete(self, interaction: discord.Interaction, current: str) -> List[
        app_commands.Choice]:
        """Used as a callback to generate choices for the "/play playlist" command in music_commands.py."""

        choices = [(playlist.choice_display_name, playlist.id) for playlist in self.playlists_list]

        # choice[0] = playlist choice display name
        # choice[1] = playlist id
        choice_list = [app_commands.Choice(name=choice[0], value=choice[1]) for choice in choices if
                       current.lower() in choice[0].lower()]

        logger.debug(f"Playlist choices: {choice_list=}")

        return choice_list[:25]


main_playlists = Playlists()
