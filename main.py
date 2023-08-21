import asyncio
import logging
from typing import Dict, List

import discord
import vrchatapi
from discord import Interaction, app_commands
from discord.ext import commands, tasks
from vrchatapi.api import authentication_api
from vrchatapi.exceptions import UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode

from configs.configs import ListenFriends, config
from utils.cookies import load_cookies, remove_cookies, save_cookies

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Enter a context with an instance of the API client
api_client: vrchatapi.ApiClient = vrchatapi.ApiClient()


class TwoFactorAuthException(Exception):
    pass


def login_vrc(username: str, password: str, code: str):
    """
    Auth to VRC API with username and password.
    It will try to login with cookies if cookies exist.
    """
    global api_client, friends
    configuration = vrchatapi.Configuration(
        username=username,
        password=password,
    )
    api_client = vrchatapi.ApiClient(configuration)
    api_client.user_agent = "VRC-Notify/0.1.0 woolensheep@qq.com"

    load_cookies(api_client)
    # Instantiate instances of API classes
    auth_api = authentication_api.AuthenticationApi(api_client)

    try:
        # Calling getCurrentUser on Authentication API logs you in if the user isn't already logged in.
        current_user = auth_api.get_current_user()
    except UnauthorizedException as e:
        if e.status == 200:
            if code == "":
                raise TwoFactorAuthException
            assert type(e.reason) == str
            if "Email 2 Factor Authentication" in e.reason:
                # Calling email verify2fa if the account has 2FA disabled
                auth_api.verify2_fa_email_code(
                    two_factor_email_code=TwoFactorEmailCode(code)
                )
            elif "2 Factor Authentication" in e.reason:
                # Calling verify2fa if the account has 2FA enabled
                auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(code))
            current_user = auth_api.get_current_user()
            assert isinstance(current_user, vrchatapi.CurrentUser)
            logging.info(f"Logged in as: {current_user.display_name}")
            save_cookies(api_client)
        else:
            remove_cookies()
            logging.info(f"Exception when calling API: {e}")
    except vrchatapi.ApiException as e:
        remove_cookies()
        logging.info(f"Exception when calling API: {e}")
    except Exception as e:
        remove_cookies()
        logging.info(f"Exception when login: {e}")


try:
    login_vrc(config.username, config.password, "")
except:
    pass
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents)
tree = bot.tree


@tree.command(
    name="ping",
    description="ping the bot to do health check",
)
@app_commands.describe()
async def ping(ctx):
    await ctx.response.send_message("pong")


@tree.command(
    name="login",
    description="login to your VRC website. DO NOT use this command in public channel.",
)
@app_commands.describe(
    username="Username of VRC",
    password="Password of VRC",
    code="(Optional) Email code or 2FA code",
)
async def login(ctx: Interaction, username: str, password: str, code: str = ""):
    global api_client
    await ctx.response.defer()
    try:
        login_vrc(username, password, code)
    except TwoFactorAuthException:
        await ctx.followup.send(
            "Resend `/login` command with verify code (or 2FA code)"
        )
        return
    except Exception as e:
        await ctx.followup.send(f"Login failed with error: {e}")
        return
    auth_api = authentication_api.AuthenticationApi(api_client)
    current_user = auth_api.get_current_user()
    name = current_user.display_name
    await ctx.followup.send(f"Logged in as {name}")


async def get_all_friends() -> Dict[str, vrchatapi.LimitedUser]:
    global api_client
    api_instance = vrchatapi.FriendsApi(api_client)
    friends: List[vrchatapi.LimitedUser] = []
    offset = 0
    while True:
        api_response: List[vrchatapi.LimitedUser] = api_instance.get_friends(
            offset=offset, n=100, offline="false"
        )
        if len(api_response) == 0:
            break
        friends.extend(api_response)
        offset += 100
    offset = 0
    while True:
        api_response = api_instance.get_friends(offset=offset, n=100, offline="true")
        if len(api_response) == 0:
            break
        friends.extend(api_response)
        offset += 100
        await asyncio.sleep(0.5)
    friend: vrchatapi.LimitedUser
    friends_map: Dict[str, vrchatapi.LimitedUser] = {}
    for friend in friends:
        friends_map[friend.display_name] = friend
    return friends_map


@tree.command(name="online_friends", description="get online friends list.")
async def get_online_friends(ctx: Interaction):
    """
    Get all online and active(on the website) friends list
    and send it via discord.
    """
    global api_client
    await ctx.response.defer()
    try:
        api_instance = vrchatapi.FriendsApi(api_client)
        offset = 0
        online_friends: List[vrchatapi.LimitedUser] = []
        while True:
            api_response = api_instance.get_friends(
                offset=offset, n=100, offline="false"
            )
            await asyncio.sleep(0.5)
            assert isinstance(api_response, List)
            if len(api_response) == 0:
                break
            online_friends.extend(api_response)
            offset += 100

        msg: str = ""
        for f in online_friends:
            emoji = get_status_emoji(f.status, f.location)
            msg += f"{emoji} {f.display_name}\n"
        await ctx.followup.send(discord.utils.escape_markdown(msg))
    except Exception as e:
        await ctx.followup.send(f"get_online_friends failed with error: {e}")


friends: Dict[str, vrchatapi.LimitedUser]


def get_status_emoji(status: str, location: str) -> str:
    """
    Get the emoji to represent the status.
    """
    if location == "offline":
        if status == "active":
            return "🌐"
        return "⚫"
    if status == "join me":
        return "🔵"
    if status == "active":
        return "🟢"
    if status == "ask me":
        return "🟠"
    if status == "do not disturb":
        return "🔴"
    return "❌"


@tasks.loop(minutes=config.update_interval_minutes)
async def update_friends_status():
    global friends, bot
    logging.info("Strat to update friend status")
    try:
        new_friends = await get_all_friends()
    except:
        logging.error("get all friends failed")
        return
    name: str
    conf: ListenFriends
    if len(friends) == 0:
        friends = new_friends
        return
    for name, conf in config.listen_friends.items():
        # find ambiguous dispaly name
        if name not in new_friends.keys():
            for n in new_friends.keys():
                if name in n:
                    name = n
        if name not in new_friends.keys() or name not in friends.keys():
            logging.info(f"{name} not found")
            continue
        online_just_now = False

        if (
            "online" in conf.on_events
            and friends[name].status == "offline"
            and not new_friends[name].status == "offline"
        ):
            online_just_now = True
            status_emoji = get_status_emoji(
                new_friends[name].status, new_friends[name].location
            )
            for ch_id in conf.to_channels:
                ch = bot.get_channel(config.channels[ch_id])
                if ch is None:
                    continue
                await ch.send(f"{status_emoji} {name} is online now!")

        if (
            "status_change" in conf.on_events
            and (
                friends[name].status != new_friends[name].status
                or (
                    friends[name].location != new_friends[name].location
                    and (
                        friends[name].location == "offline"
                        or new_friends[name].location == "offline"
                    )
                )
            )
            and not online_just_now
        ):
            old_status_emoji = get_status_emoji(
                friends[name].status, friends[name].location
            )
            status_emoji = get_status_emoji(
                new_friends[name].status, new_friends[name].location
            )
            for ch_id in conf.to_channels:
                ch = bot.get_channel(config.channels[ch_id])
                if ch is None:
                    continue
                await ch.send(
                    f"{name} status changed: {old_status_emoji} -> {status_emoji}"
                )
    friends = new_friends


@bot.event
async def on_ready():
    global friends
    try:
        friends = await get_all_friends()
    except:
        friends = {}
    update_friends_status.start()
    try:
        await tree.sync()
        logging.info("Commands sync finished")
    except Exception as e:
        logging.info(e)


bot.run(config.discord_bot_token)

api_client.close()
