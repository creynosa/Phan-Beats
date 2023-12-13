from pathlib import Path

import toml

bot_name = "Phanbeats"
bot_pfp_url = r"https://raw.githubusercontent.com/creynosa/images/main/beats%20by%20phan.png"
last_song_id = 0
configPath = str(Path('musicbot') / 'config.toml')


def get_config() -> dict:
    """Reads and returns the general configs in the directory."""
    with open(configPath, 'r') as f:
        config = toml.load(f)
    return config


def write_to_config(updated_config: dict):
    """Writes an updated config to the config file."""
    with open(configPath, 'w') as f:
        toml.dump(updated_config, f)


initial_config = get_config()
