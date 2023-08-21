"""
Config module including all settings of notification and discord bot.
"""
from typing import Dict, List

import yaml
from pydantic import BaseModel


class ListenFriends(BaseModel):
    """
    Config of friends to listen.
    """

    on_events: List[str]
    to_channels: List[str]


class Config(BaseModel):
    """
    Top level config class.
    """

    discord_bot_token: str
    username: str
    password: str
    update_interval_minutes: int
    listen_friends: Dict[str, ListenFriends]
    channels: Dict[str, int]


config: Config

with open("config.yaml", "r", encoding="utf-8") as yaml_file:
    data = yaml.safe_load(yaml_file)

config = Config(**data)
