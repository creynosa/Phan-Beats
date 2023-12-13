import math
import os
import re
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from mutagen.mp3 import MP3

from logs import loggers
from musicbot.general import get_config, write_to_config

logger = loggers.createLogger('main.library')


class Library:
    def __init__(self):
        self.library = get_library()
        self.song_raw_names = self.get_all_song_raw_names()
        self.song_raw_names_with_artist = self.get_all_song_raw_names_with_artist()
        # self.generate_data_for_sheets()

    def get_all_song_ids(self) -> list[int]:
        """Gets a list of all the song ids in the music library."""
        song_ids = []
        for song_id, _ in self.library.items():
            song_ids.append(song_id)

        song_ids.sort()

        return song_ids

    def get_all_song_raw_names(self) -> list[str]:
        """Gets a list of all the song filenames of the music library."""

        song_raw_names = []
        for song_id, song_metadata in self.library.items():
            title = song_metadata['title']
            filename = f"[{song_id}] {title}"
            song_raw_names.append(filename)
        song_raw_names.sort()

        return song_raw_names

    def get_all_song_raw_names_with_artist(self) -> list[tuple]:
        """Gets a list of all the song filenames of the music library with their respective artist."""

        song_raw_names = []
        for song_id, song_metadata in self.library.items():
            title = song_metadata['title']
            artist = song_metadata['artist']
            filename = f"[{song_id}] {title}"
            song_raw_names.append((filename, artist))

        return song_raw_names

    async def song_raw_names_autocomplete(self, interaction: discord.Interaction, current: str) -> list[
        app_commands.Choice]:
        """Converts the list of song names to a list of Choices."""

        choices = self.song_raw_names_with_artist

        # choice[0] is song title w/ id. (ex. [1] Bring Me To Life)
        # choice[1] is artist name (ex. Evanescence)
        choice_list = [app_commands.Choice(name=f"{choice[0]} by {choice[1]}", value=f"{choice[0]}") for choice in
                       choices if
                       current.lower() in choice[0].lower() or current.lower() in choice[1].lower()]

        return choice_list[:25]

    # def generate_data_for_sheets(self):
    #     song_ids = []
    #     song_names = []
    #     artists = []
    #
    #     for song_id, song_data in list(self.library.items()):
    #         song_ids.append(str(song_id))
    #         song_names.append(song_data['title'])
    #         artists.append(song_data['artist'])
    #
    #     song_id_string = '|'.join(song_ids)
    #     song_names_string = '|'.join(song_names)
    #     artists_string = '|'.join(artists)
    #
    #     full_text = f"{song_id_string}\n\n{song_names_string}\n\n{artists_string}"
    #
    #     logger.debug('Writing to file')
    #     with open('test.txt', 'w') as f:
    #         f.write(full_text)
    #     logger.debug(("Wrote to file"))


def get_song_metadata(filepath: str) -> dict:
    """Parses a song's filepath and returns a tuple containing the song's ID and metadata."""

    song_id_regex = re.compile(r"((.*)\\(.*)\\)\[(\d*)] (.*).mp3")
    match = re.search(song_id_regex, filepath)

    artist = match.group(3)
    song_id = int(match.group(4))
    title = match.group(5)
    raw_name = f"[{song_id}] {title}"

    mutagen_source = MP3(str(filepath))
    duration = parse_duration(mutagen_source)
    duration_str = get_duration_string(duration)

    metadata = {
        'artist': artist,
        'title': title,
        'duration': duration,
        'duration_str': duration_str,
        'filepath': filepath,
        'raw_name': raw_name,
    }

    return metadata


def get_song_album_art(filepath: str) -> Optional[str]:
    """Reads the album art text file in specified file."""
    try:
        with open(filepath, 'r') as f:
            url = f.read()
    except FileNotFoundError:
        return None

    return url


def parse_duration(mp3_file: MP3) -> tuple[int, int, int]:
    """Returns a song's duration in a tuple (hours, minutes, seconds)."""
    length_in_seconds = math.trunc(mp3_file.info.length)

    hours, seconds = divmod(length_in_seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    return hours, minutes, seconds


def get_duration_string(song_duration: tuple[int, int, int]) -> str:
    """Returns a song's duration in a formatted string."""
    hours, minutes, seconds = song_duration

    if hours < 10:
        hours = f"0{hours}"
    if minutes < 10:
        minutes = f"0{minutes}"
    if seconds < 10:
        seconds = f"0{seconds}"

    return f"{hours}h:{minutes}m:{seconds}s"


def get_song_id(filename: str) -> Optional[int]:
    """Returns the song_id of a given filename."""
    song_id_regex = re.compile(r"\[(\d*)] (.*).mp3")
    match = re.search(song_id_regex, filename)

    return int(match.group(1)) if match else None


def get_library() -> dict:
    """Returns a dictionary of all available songs in a given directory. \
    The dictionary will be formatted as follows: {song_id: {song_metadata}}"""

    musicFolder = Path('music')

    library = {}
    config = get_config()
    last_song_id_used = config['library']['last_song_id_used']
    config_needs_updating = False

    for root, dirs, files in os.walk(musicFolder, topdown=True):
        for name in files:
            if name.endswith('.mp3'):
                song_path = str(os.path.join(root, name))

                song_id = get_song_id(song_path)
                if not song_id:
                    new_song_id = last_song_id_used + 1

                    new_filename = f"[{new_song_id}] {name}"
                    new_filepath = str(os.path.join(root, new_filename))
                    os.rename(song_path, new_filepath)

                    song_path = new_filepath
                    last_song_id_used = new_song_id
                    config['library']['last_song_id_used'] = last_song_id_used
                    config_needs_updating = True

                song_metadata = get_song_metadata(song_path)
                library[song_id] = song_metadata

    if config_needs_updating:
        write_to_config(config)

    return library


main_library = Library()
