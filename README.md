<div align="center" id="top">
    <img width="400" src="images/logo.svg" alt="VRC Notify Bot Logo" />
</div>


<h1 align="center">VRC Notify Bot</h1>

<p align="center">
    <a href="https://github.com/woolen-sheep/vrc-notify-bot/actions">
        <img alt="GitHub Workflow Status" src="https://img.shields.io/github/actions/workflow/status/woolen-sheep/vrc-notify-bot/docker-build-push.yml?style=flat-square">
    </a>
    <a href="https://github.com/woolen-sheep/vrc-notify-bot/stargazers">
        <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/woolen-sheep/vrc-notify-bot?style=flat-square">
    </a>
    <a href="https://hub.docker.com/r/woolensheep/vrc-notify-bot">
        <img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/woolensheep/vrc-notify-bot?style=flat-square">
    </a>
    <a href="/LICENSE">
        <img alt="LICENSE" src="https://img.shields.io/github/license/woolen-sheep/vrc-notify-bot?style=flat-square">
    </a>
</p>

## Introduction

This script is a discord bot to notify the status changes of your friends in VRChat.

Note: If you only want notifications on your windows desktop, [VRCX](https://github.com/vrcx-team/VRCX) is better. You probably need this repo when:

- You have a cloud server or a local host up 7*24.
- You want notifications when your desktop or VRCX is not up, or want notifications on your mobile devices.

## Quick Start

- [Apply for a discord bot](https://discordpy.readthedocs.io/en/stable/discord.html) and invite it to your server.

- Copy the content of [`config.example.yaml`](/config.example.yaml), fill in needed fields, and save it as `config.yaml`:

```yaml
discord_bot_token: your_discord_bot_token
username: username
password: password
update_interval_minutes: 1
# channels name and id
channels:
  notify_channel: 10000000000000000
# friends to listen
listen_friends:
  # display name of your friend.
  # can use substring of display name
  # such as `woolen` for `woolensheep`
  # but make sure this will not conflict
  # with outher friends
  woolensheep:
    on_events:
      - online
      - status_change
    to_channels:
      # channel names defined above
      - notify_channel
```

- run docker container:

```bash
docker run -itd \
    -v /absolute/path/to/config.yaml:/app/config.yaml \
    --name vrc-notify woolensheep/vrc-notify-bot:latest
```

- If it's the first time you run it, you need to send `/login` command to it with a 2FA code (mostly a e-mail code).
    - Warning: To avoid leaking your password, DO NOT use this command in a public server.

- Send `/online_friends` command to check if the bot is working fine.

## License 

Released under [GPL-3.0](/LICENSE) by [@woolen-sheep](https://github.com/woolen-sheep).
