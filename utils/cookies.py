"""
Uitl functions to manage cookies of VRChat API.
"""

import os
from http.cookiejar import LWPCookieJar
from re import L


def save_cookies(client, filename: str = "cookies"):
    """Save current session cookies

    Args:
        filename (str): Path to save cookies to
    """

    cookie_jar = LWPCookieJar(filename=filename)

    for cookie in client.rest_client.cookie_jar:
        cookie_jar.set_cookie(cookie)

    cookie_jar.save()


def load_cookies(client, filename: str = "cookies"):
    """Load cached session cookies from file

    Args:
        filename (str): Path to load cookies from
    """
    if not os.path.exists(filename):
        return
    cookie_jar = LWPCookieJar(filename=filename)
    try:
        cookie_jar.load()
    except FileNotFoundError:
        cookie_jar.save()
        return

    for cookie in cookie_jar:
        client.rest_client.cookie_jar.set_cookie(cookie)


def remove_cookies(filename: str = "cookies"):
    """
    remove cookies file
    """
    if os.path.exists(filename):
        os.remove(filename)
