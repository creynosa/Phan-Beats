import os
import subprocess
from pathlib import Path

from pytube import YouTube, Playlist


def download(link: str):
    print('Downloading your videos and converting them to mp3 files...')

    destinationPath = Path(r'C:\Users\creyn\Documents\Programming\Discord\phan-beats\temp')
    destination = str(destinationPath)
    download_errors = []

    if 'playlist' in link:
        p = Playlist(link)
        for video in p.videos:
            invalid = r'<>:"/\|?*'
            try:
                video_title = ''.join([letter for letter in video.title if letter not in invalid])
            except:
                print('Invalid characters for song (i think).')
                continue

            file_name = f"{video_title}.mp4"
            filepath = destinationPath / file_name

            new_file_name = f"{video_title}.mp3"
            new_filepath = destinationPath / new_file_name

            if os.path.exists(filepath):
                download_errors.append(video.title)
                continue

            audio = video.streams.filter(only_audio=True)[1]
            audio.download(output_path=destination, filename=file_name)

            subprocess.run(['ffmpeg', '-i', filepath, new_filepath])
            os.remove(filepath)

        if not download_errors:
            text = f"Downloaded the playlist successfully!"
        else:
            errors = '\n'.join(download_errors)
            text = f'Some songs were not processed: \n\n{errors}'

        print(text)
        return

    else:
        yt = YouTube(link)
        invalid = r'<>:"/\|?*'
        video_title = ''.join([letter for letter in yt.title if letter not in invalid])

        file_name = f"{video_title}.mp4"
        filepath = destinationPath / file_name

        new_file_name = f"{video_title}.mp3"
        new_filepath = destinationPath / new_file_name

        if os.path.exists(filepath):
            download_errors.append(yt.title)
        else:
            audio = yt.streams.filter(only_audio=True)[1]
            print(f"{audio=}")
            audio.download(output_path=destination, filename=file_name)

            subprocess.run(['ffmpeg', '-i', filepath, new_filepath])
            os.remove(filepath)

    if not download_errors:
        text = f"Downloaded the song successfully! Please wait for Phan to add it to the library."
    else:
        errors = '\n'.join(download_errors)
        text = f'The song was not processed because it has already been downloaded: \n\n{errors}'

    print(text)
    return
