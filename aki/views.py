# -*- coding: utf-8 -*-

from django.shortcuts import HttpResponse
from .models import akin, profiles, flood_control, daily_bonus
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .secret_key import service_key

from stem import Signal
from stem.control import Controller
from torrequest import TorRequest
import socks
import socket
import os

import requests
import time
import datetime
import json
import re
from bs4 import BeautifulSoup
import numpy as np
from random import randint

from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlparse, parse_qsl, urlencode

token = "cfc1ac2bfe0c13307ed1250665c0e6837411829ce009b1643e9f03c5d9b0819a8d5b4dbde2be7fb3add09"


def get_current_ip():
    session = requests.session()

    # TO Request URL with SOCKS over TOR
    session.proxies = {}
    session.proxies['http'] = 'socks5h://localhost:9050'
    session.proxies['https'] = 'socks5h://localhost:9050'

    try:
        r = session.get('http://httpbin.org/ip')
    except Exception as e:
        print(str(e))
    else:
        return r.text


def renew_tor_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password="nanana")
        controller.signal(Signal.NEWNYM)


def ip(request):
    proxies = {
        'http': 'http://139.196.218.83:8080',
        'https': 'https://1.70.65.84:9999'
    }
    r = requests.get('http://httpbin.org/ip', proxies=proxies).text

    return HttpResponse(json.dumps({'a': r}, ensure_ascii=False))


class InvalidAnswerError(ValueError):
    """Raised when the user inputs an invalid answer"""
    pass


class InvalidLanguageError(ValueError):
    """Raised when the user inputs an invalid language"""
    pass


class AkiConnectionFailure(Exception):
    """Raised if the Akinator API fails to connect for some reason. Base class for AkiTimedOut, AkiNoQuestions, AkiServerDown, and AkiTechnicalError"""
    pass


class AkiTimedOut(AkiConnectionFailure):
    """Raised if the Akinator session times out. Derived from AkiConnectionFailure"""
    pass


class AkiNoQuestions(AkiConnectionFailure):
    """Raised if the Akinator API runs out of questions to ask. This will happen if "Akinator.step" is at 79 and the "answer" function is called again. Derived from AkiConnectionFailure"""
    pass


class AkiServerDown(AkiConnectionFailure):
    """Raised if Akinator's servers are down for the region you're running on. If this happens, try again later or use a different language. Derived from AkiConnectionFailure"""
    pass


class AkiTechnicalError(AkiConnectionFailure):
    """Raised if Aki's servers had a technical error. If this happens, try again later or use a different language. Derived from AkiConnectionFailure"""
    pass


class CantGoBackAnyFurther(Exception):
    """Raised when the user is on the first question and tries to go back further"""
    pass


# * URLs for the API requests
NEW_SESSION_URL1 = "https://{}/new_session?callback=jQuery331023608747682107778_{}&urlApiWs={}&partner=1&childMod={}&player=website-desktop&uid_ext_session={}&frontaddr={}&constraint=ETAT<>'AV'&soft_constraint={}&question_filter={}"
NEW_SESSION_URL = "https://{}/new_session?callback=jQuery331023608747682107778_{}&urlApiWs={}&partner=1&childMod={}&player=website-desktop&uid_ext_session={}&frontaddr={}&constraint=ETAT<>'AV'&soft_constraint={}&question_filter={}"
ANSWER_URL = "https://{}/answer_api?callback=jQuery331023608747682107778_{}&urlApiWs={}&childMod={}&session={}&signature={}&step={}&answer={}&frontaddr={}&question_filter={}"
BACK_URL = "{}/cancel_answer?callback=jQuery331023608747682107778_{}&childMod={}&session={}&signature={}&step={}&answer=-1&question_filter={}"
WIN_URL = "{}/list?callback=jQuery331023608747682107778_{}&childMod={}&session={}&signature={}&step={}"

# * HTTP headers to use for the requests
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/81.0.4044.92 Chrome/81.0.4044.92 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}


def _update(resp, start=False):
    """Update class variables"""
    resp = resp
    if start:
        session = int(resp["parameters"]["identification"]["session"])
        signature = int(resp["parameters"]["identification"]["signature"])
        question = str(resp["parameters"]["step_information"]["question"])
        progression = float(resp["parameters"]["step_information"]["progression"])
        step = int(resp["parameters"]["step_information"]["step"])
    else:
        question = str(resp["parameters"]["question"])
        progression = float(resp["parameters"]["progression"])
        step = int(resp["parameters"]["step"])


def get_lang_and_theme(lang=None):
    """Returns the language code and theme based on what is input"""

    if lang is None or lang == "en" or lang == "english":
        return {"lang": "en", "theme": "c"}
    elif lang == "en_animals" or lang == "english_animals":
        return {"lang": "en", "theme": "a"}
    elif lang == "en_objects" or lang == "english_objects":
        return {"lang": "en", "theme": "o"}
    elif lang == "ar" or lang == "arabic":
        return {"lang": "ar", "theme": "c"}
    elif lang == "cn" or lang == "chinese":
        return {"lang": "cn", "theme": "c"}
    elif lang == "de" or lang == "german":
        return {"lang": "de", "theme": "c"}
    elif lang == "de_animals" or lang == "german_animals":
        return {"lang": "de", "theme": "a"}
    elif lang == "es" or lang == "spanish":
        return {"lang": "es", "theme": "c"}
    elif lang == "es_animals" or lang == "spanish_animals":
        return {"lang": "es", "theme": "a"}
    elif lang == "fr" or lang == "french":
        return {"lang": "fr", "theme": "c"}
    elif lang == "fr_animals" or lang == "french_animals":
        return {"lang": "fr", "theme": "a"}
    elif lang == "fr_objects" or lang == "french_objects":
        return {"lang": "fr", "theme": "o"}
    elif lang == "il" or lang == "hebrew":
        return {"lang": "il", "theme": "c"}
    elif lang == "it" or lang == "italian":
        return {"lang": "it", "theme": "c"}
    elif lang == "it_animals" or lang == "italian_animals":
        return {"lang": "it", "theme": "a"}
    elif lang == "jp" or lang == "japanese":
        return {"lang": "jp", "theme": "c"}
    elif lang == "jp_animals" or lang == "japanese_animals":
        return {"lang": "jp", "theme": "a"}
    elif lang == "kr" or lang == "korean":
        return {"lang": "kr", "theme": "c"}
    elif lang == "nl" or lang == "dutch":
        return {"lang": "nl", "theme": "c"}
    elif lang == "pl" or lang == "polish":
        return {"lang": "pl", "theme": "c"}
    elif lang == "pt" or lang == "portuguese":
        return {"lang": "pt", "theme": "c"}
    elif lang == "ru" or lang == "russian":
        return {"lang": "ru", "theme": "c"}
    elif lang == "tr" or lang == "turkish":
        return {"lang": "tr", "theme": "c"}
    else:
        raise InvalidLanguageError("You put \"{}\", which is an invalid language.".format(lang))


def _auto_get_region(lang, theme):
    """Automatically get the uri and server from akinator.com for the specified language and theme"""

    server_regex = re.compile(
        "[{\"translated_theme_name\":\"[\s\S]*\",\"urlWs\":\"https:\\\/\\\/srv[0-9]+\.akinator\.com:[0-9]+\\\/ws\",\"subject_id\":\"[0-9]+\"}]")
    uri = lang + ".akinator.com"
    r = requests.get("https://" + uri)

    match = server_regex.search(r.text)
    parsed = json.loads(match.group().split("'arrUrlThemesToPlay', ")[-1])

    if theme == "c":
        return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "1"), None)["urlWs"]}
    elif theme == "a":
        return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "14"), None)["urlWs"]}
    elif theme == "o":
        return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "2"), None)["urlWs"]}


def _get_session_info():
    """Get uid and frontaddr from akinator.com/game"""

    info_regex = re.compile("var uid_ext_session = '(.*)'\\;\\n.*var frontaddr = '(.*)'\\;")
    r = requests.get("https://en.akinator.com/game")

    match = info_regex.search(r.text)
    uid, frontaddr = match.groups()[0], match.groups()[1]


def _parse_response(response):
    """Parse the JSON response and turn it into a Python object"""

    return json.loads(",".join(response.split("(")[1::])[:-1])


def raise_connection_error(response):
    """Raise the proper error if the API failed to connect"""

    if response == "KO - SERVER DOWN":
        raise AkiServerDown("Akinator's servers are down in this region. Try again later or use a different language")
    elif response == "KO - TECHNICAL ERROR":
        raise AkiTechnicalError(
            "Akinator's servers have had a technical error. Try again later or use a different language")
    elif response == "KO - TIMEOUT":
        raise AkiTimedOut("Your Akinator session has timed out")
    elif response == "KO - ELEM LIST IS EMPTY" or response == "WARN - NO QUESTION":
        raise AkiNoQuestions("\"Akinator.step\" reached 80. No more questions")
    else:
        raise AkiConnectionFailure("An unknown error has occured. Server response: {}".format(response))


def ans_to_id(ans):
    """Convert an input answer string into an Answer ID for Akinator"""

    ans = str(ans).lower()
    if ans == "yes" or ans == "y" or ans == "0":
        return "0"
    elif ans == "no" or ans == "n" or ans == "1":
        return "1"
    elif ans == "i" or ans == "idk" or ans == "i dont know" or ans == "i don't know" or ans == "2":
        return "2"
    elif ans == "probably" or ans == "p" or ans == "3":
        return "3"
    elif ans == "probably not" or ans == "pn" or ans == "4":
        return "4"
    else:
        raise InvalidAnswerError("""
        You put "{}", which is an invalid answer.
        The answer must be one of these:
            - "yes" OR "y" OR "0" for YES
            - "no" OR "n" OR "1" for NO
            - "i" OR "idk" OR "i dont know" OR "i don't know" OR "2" for I DON'T KNOW
            - "probably" OR "p" OR "3" for PROBABLY
            - "probably not" OR "pn" OR "4" for PROBABLY NOT
        """.format(ans))


class Akinator():

    def __init__(self):

        self.resp = None

        self.uri = None
        self.server = None
        self.session = None
        self.signature = None
        self.uid = None
        self.frontaddr = None
        self.child_mode = None
        self.question_filter = None
        self.timestamp = None

        self.question = None
        self.progression = None
        self.step = None

        self.first_guess = None
        self.guesses = None

    def _update(self, resp, start=False):
        """Update class variables"""
        self.resp = resp
        if start:
            self.session = int(resp["parameters"]["identification"]["session"])
            self.signature = int(resp["parameters"]["identification"]["signature"])
            self.question = str(resp["parameters"]["step_information"]["question"])
            self.progression = float(resp["parameters"]["step_information"]["progression"])
            self.step = int(resp["parameters"]["step_information"]["step"])
        else:
            self.question = str(resp["parameters"]["question"])
            self.progression = float(resp["parameters"]["progression"])
            self.step = int(resp["parameters"]["step"])

    def _parse_response(self, response):
        """Parse the JSON response and turn it into a Python object"""

        return json.loads(",".join(response.split("(")[1::])[:-1])

    def _get_session_info(self):
        """Get uid and frontaddr from akinator.com/game"""

        info_regex = re.compile("var uid_ext_session = '(.*)'\\;\\n.*var frontaddr = '(.*)'\\;")
        r = requests.get("https://en.akinator.com/game")

        match = info_regex.search(r.text)
        self.uid, self.frontaddr = match.groups()[0], match.groups()[1]

    def _auto_get_region(self, lang, theme):
        """Automatically get the uri and server from akinator.com for the specified language and theme"""

        server_regex = re.compile(
            "[{\"translated_theme_name\":\"[\s\S]*\",\"urlWs\":\"https:\\\/\\\/srv[0-9]+\.akinator\.com:[0-9]+\\\/ws\",\"subject_id\":\"[0-9]+\"}]")
        uri = lang + ".akinator.com"
        r = requests.get("https://" + uri)

        match = server_regex.search(r.text)
        parsed = json.loads(match.group().split("'arrUrlThemesToPlay', ")[-1])

        if theme == "c":
            return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "1"), None)["urlWs"]}
        elif theme == "a":
            return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "14"), None)["urlWs"]}
        elif theme == "o":
            return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "2"), None)["urlWs"]}

    def start_game(self, language=None, child_mode=False):
        ###
        ###
        ###
        ###
        self.timestamp = time.time()
        self.ftimestamp = self.timestamp
        region_info = self._auto_get_region(get_lang_and_theme(language)["lang"], get_lang_and_theme(language)["theme"])
        self.uri, self.server = region_info["uri"], region_info["server"]

        self.child_mode = child_mode
        soft_constraint = "ETAT%3D%27EN%27" if self.child_mode else ""
        self.question_filter = "cat%3D1" if self.child_mode else ""

        self._get_session_info()

        r = requests.get(
            NEW_SESSION_URL.format(self.uri, self.timestamp, self.server, str(self.child_mode).lower(), self.uid,
                                   self.frontaddr, soft_constraint, self.question_filter), headers=HEADERS)

        resp = self._parse_response(r.text)

        if resp["completion"] == "OK":
            self._update(resp, True)
            return resp, self.timestamp
        else:
            return None, None
        ###
        ###
        ###
        ###

    def answer(self, ans):
        """Answer the current question, which you can find with "Akinator.question". Returns a string containing the next question

        The "ans" parameter must be one of these:
            - "yes" OR "y" OR "0" for YES
            - "no" OR "n" OR "1" for NO
            - "i" OR "idk" OR "i dont know" OR "i don't know" OR "2" for I DON'T KNOW
            - "probably" OR "p" OR "3" for PROBABLY
            - "probably not" OR "pn" OR "4" for PROBABLY NOT
        """
        ans = ans_to_id(ans)
        r = requests.get(
            ANSWER_URL.format(self.uri, self.timestamp, self.server, str(self.child_mode).lower(), self.session,
                              self.signature, self.step, ans, self.frontaddr, self.question_filter), headers=HEADERS)
        resp = self._parse_response(r.text)

        if resp["completion"] == "OK":
            self._update(resp)
            return self.question
        else:
            return raise_connection_error(resp["completion"])

    def back(self):
        """Goes back to the previous question. Returns a string containing that question

        If you're on the first question and you try to go back again, the CantGoBackAnyFurther exception will be raised
        """
        if self.step == 0:
            raise CantGoBackAnyFurther("You were on the first question and couldn't go back any further")

        r = requests.get(
            BACK_URL.format(self.server, self.timestamp, str(self.child_mode).lower(), self.session, self.signature,
                            self.step, self.question_filter), headers=HEADERS)
        resp = self._parse_response(r.text)

        if resp["completion"] == "OK":
            self._update(resp)
            return self.question
        else:
            return raise_connection_error(resp["completion"])

    def win(self):
        """Get Aki's guesses for who the person you're thinking of is based on your answers to the questions so far

        Defines and returns the variable "Akinator.first_guess", a dictionary describing his first choice for who you're thinking about. The three most important values in the dict are "name" (character's name), "description" (description of character), and "absolute_picture_path" (direct link to image of character)

        This function also defines "Akinator.guesses", which is a list of dictionaries containing his choices in order from most likely to least likely

        It's recommended that you call this function when Aki's progression is above 85%, which is when he will have most likely narrowed it down to just one choice. You can get his current progression via "Akinator.progression"
        """
        r = requests.get(
            WIN_URL.format(self.server, self.timestamp, str(self.child_mode).lower(), self.session, self.signature,
                           self.step), headers=HEADERS)
        resp = self._parse_response(r.text)

        if resp["completion"] == "OK":
            self.first_guess = resp["parameters"]["elements"][0]["element"]
            self.guesses = [g["element"] for g in resp["parameters"]["elements"]]
            return self.first_guess
        else:
            return raise_connection_error(resp["completion"])

    def resps(self):

        return self.resp

    def front(self):

        return self.frontaddr


def get_session_info():
    """Get uid and frontaddr from akinator.com/game"""

    info_regex = re.compile("var uid_ext_session = '(.*)'\\;\\n.*var frontaddr = '(.*)'\\;")
    r = requests.get("https://en.akinator.com/game")

    match = info_regex.search(r.text)
    uid, frontaddr = match.groups()[0], match.groups()[1]


def auto_get_region(lang, theme):
    """Automatically get the uri and server from akinator.com for the specified language and theme"""

    server_regex = re.compile(
        "[{\"translated_theme_name\":\"[\s\S]*\",\"urlWs\":\"https:\\\/\\\/srv[0-9]+\.akinator\.com:[0-9]+\\\/ws\",\"subject_id\":\"[0-9]+\"}]")
    uri = lang + ".akinator.com"
    r = requests.get("https://" + uri)

    match = server_regex.search(r.text)
    parsed = json.loads(match.group().split("'arrUrlThemesToPlay', ")[-1])

    if theme == "c":
        return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "1"), None)["urlWs"]}
    elif theme == "a":
        return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "14"), None)["urlWs"]}
    elif theme == "o":
        return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "2"), None)["urlWs"]}


def win(server=None, timestamp=None, session=None, signature=None, step=None):
    """Get Aki's guesses for who the person you're thinking of is based on your answers to the questions so far

        Defines and returns the variable "Akinator.first_guess", a dictionary describing his first choice for who you're thinking about. The three most important values in the dict are "name" (character's name), "description" (description of character), and "absolute_picture_path" (direct link to image of character)

        This function also defines "Akinator.guesses", which is a list of dictionaries containing his choices in order from most likely to least likely

        It's recommended that you call this function when Aki's progression is above 85%, which is when he will have most likely narrowed it down to just one choice. You can get his current progression via "Akinator.progression"
        """
    r = requests.get(
        WIN_URL.format(server, timestamp, str('false').lower(), session, signature,
                       step), headers=HEADERS)
    resp = _parse_response(r.text)

    if resp["completion"] == "OK":
        first_guess = resp["parameters"]["elements"][0]["element"]
        guesses = [g["element"] for g in resp["parameters"]["elements"]]
        # resp['parameters']
        return resp
    else:
        return raise_connection_error(resp["completion"])


def is_valid(*, query: dict, secret: str) -> bool:
    """Check VK Apps signature"""
    vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
    hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256).digest())
    decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')
    return query["sign"] == decoded_hash_code


def gg(r, user_id=None) -> bool:
    if r is None:
        return False
    try:
        url = 'https://example.com/?' + r.headers.get('xvk')
    except Exception:
        return False
    client_secret = "coS0TotdX3pOMVBFJ4kF"
    # url = 'https://example.com/?vk_access_token_settings=&vk_app_id=7669770&vk_are_notifications_enabled=0&vk_is_app_user=1&vk_is_favorite=1&vk_language=ru&vk_platform=mobile_android&vk_ref=widget&vk_ts=1610377339&vk_user_id=274487787&sign=k1VwXxByCZkkVwwLRc0G9ULUHkH_yLWaH3vSHAOvHWM'
    # client_secret = "wvl68m4dR1UpLrVRli"
    query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    if user_id is not None:
        try:
            int(user_id)
        except ValueError:
            return False
    if user_id is not None:
        if (str(user_id) == str(query_params['vk_user_id'])):
            try:
                flood_user = flood_control.objects.get(user_id=user_id)
                if flood_user.timestamp == int(str(datetime.datetime.now()).split(':')[1]):
                    if flood_user.count > 39:
                        return False
                    flood_user.count += 1
                    flood_user.save()
                else:
                    flood_user.timestamp = int(str(datetime.datetime.now()).split(':')[1])
                    flood_user.count = 1
                    flood_user.save()
            except Exception:
                timestamp = int(str(datetime.datetime.now()).split(':')[1])
                a = flood_control(user_id=user_id, timestamp=timestamp, count=1)
                a.save()
        else:
            return False
    else:
        try:
            user_id = int(query_params['vk_user_id'])
        except ValueError:
            return False

        try:
            flood_user = flood_control.objects.get(user_id=user_id)
            if flood_user.timestamp == int(str(datetime.datetime.now()).split(':')[1]):
                if flood_user.count > 39:
                    return False
                print(6)
                flood_user.count += 1
                flood_user.save()
            else:
                flood_user.timestamp = int(str(datetime.datetime.now()).split(':')[1])
                flood_user.count = 1
                flood_user.save()
        except Exception:
            timestamp = int(str(datetime.datetime.now()).split(':')[1])
            a = flood_control(user_id=user_id, timestamp=timestamp, count=1)
            a.save()
    status = is_valid(query=query_params, secret=client_secret)
    if status:
        return True
    else:
        return False


class Akinator_dynamic_ip():

    def __init__(self):

        self.resp = None

        self.uri = None
        self.server = None
        self.session = None
        self.signature = None
        self.uid = None
        self.frontaddr = None
        self.child_mode = None
        self.question_filter = None
        self.timestamp = None

        self.question = None
        self.progression = None
        self.step = None

        self.first_guess = None
        self.guesses = None

    def _update(self, resp, start=False):
        """Update class variables"""
        self.resp = resp
        if start:
            self.session = int(resp["parameters"]["identification"]["session"])
            self.signature = int(resp["parameters"]["identification"]["signature"])
            self.question = str(resp["parameters"]["step_information"]["question"])
            self.progression = float(resp["parameters"]["step_information"]["progression"])
            self.step = int(resp["parameters"]["step_information"]["step"])
        else:
            self.question = str(resp["parameters"]["question"])
            self.progression = float(resp["parameters"]["progression"])
            self.step = int(resp["parameters"]["step"])

    def _parse_response(self, response):
        """Parse the JSON response and turn it into a Python object"""

        return json.loads(",".join(response.split("(")[1::])[:-1])

    def _get_session_info(self):
        """Get uid and frontaddr from akinator.com/game"""

        info_regex = re.compile("var uid_ext_session = '(.*)'\\;\\n.*var frontaddr = '(.*)'\\;")
        r = requests.get("https://en.akinator.com/game")

        match = info_regex.search(r.text)
        self.uid, self.frontaddr = match.groups()[0], match.groups()[1]

    def _auto_get_region(self, lang, theme):
        """Automatically get the uri and server from akinator.com for the specified language and theme"""

        server_regex = re.compile(
            "[{\"translated_theme_name\":\"[\s\S]*\",\"urlWs\":\"https:\\\/\\\/srv[0-9]+\.akinator\.com:[0-9]+\\\/ws\",\"subject_id\":\"[0-9]+\"}]")
        uri = lang + ".akinator.com"
        r = requests.get("https://" + uri)

        match = server_regex.search(r.text)
        parsed = json.loads(match.group().split("'arrUrlThemesToPlay', ")[-1])

        if theme == "c":
            return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "1"), None)["urlWs"]}
        elif theme == "a":
            return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "14"), None)["urlWs"]}
        elif theme == "o":
            return {"uri": uri, "server": next((i for i in parsed if i["subject_id"] == "2"), None)["urlWs"]}

    def start_game(self, language=None, child_mode=False):

        ###
        ###
        ###
        ###
        self.timestamp = time.time()
        self.ftimestamp = self.timestamp
        region_info = self._auto_get_region(get_lang_and_theme(language)["lang"], get_lang_and_theme(language)["theme"])
        self.uri, self.server = region_info["uri"], region_info["server"]

        self.child_mode = child_mode
        soft_constraint = "ETAT%3D%27EN%27" if self.child_mode else ""
        self.question_filter = "cat%3D1" if self.child_mode else ""

        self._get_session_info()

        r = requests.get(
            NEW_SESSION_URL.format(self.uri, self.timestamp, self.server, str(self.child_mode).lower(), self.uid,
                                   self.frontaddr, soft_constraint, self.question_filter), headers=HEADERS)
        resp = self._parse_response(r.text)

        if resp["completion"] == "OK":
            self._update(resp, True)
            return resp, self.timestamp
        else:
            return None, None
        ###
        ###
        ###
        ###

    def resps(self):

        return self.resp

    def front(self):

        return self.frontaddr

    def change_ip(self):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="1234")
            controller.signal(Signal.NEWNYM)


def start_game_ip(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    if gg(request, request.GET.get('id')):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    user_id = query_params['vk_user_id']

    if user_id is None:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    try:
        user_id = int(user_id)
    except Exception:
        pass

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps({'error': 'profile not found'}, ensure_ascii=False))

    language = request.GET.get('language')
    if language is None:
        language = 'ru'

    aki = Akinator_dynamic_ip()

    with open('time_ip.txt', 'r') as f:
        file = f.read()
    if str(datetime.datetime.today()).split(' ')[1].split(':')[0] != str(file):
        with open('time_ip.txt', 'w') as f:
            f.write(str(str(datetime.datetime.today()).split(' ')[1].split(':')[0]))
        aki.change_ip()

    # timestamp = time.time()

    pars, timestamp = aki.start_game(language=language)
    frontaddr = aki.front()

    if pars is None:
        return HttpResponse(None)

    parse = pars['parameters']['step_information']

    session = int(pars['parameters']['identification']['session'])
    signature = int(pars['parameters']['identification']['signature'])
    challenge_auth = str(pars['parameters']['identification']['challenge_auth'])

    uri = "ru.akinator.com"
    question_filter = ""
    server = 'https://srv12.akinator.com:9398/ws'

    upd_step = requests.get(
        ANSWER_URL.format(uri, timestamp, server, str('false').lower(), session,
                          signature, 0, 2, frontaddr, question_filter), headers=HEADERS)

    upd_step = json.loads(",".join(upd_step.text.split("(")[1::])[:-1])
    if upd_step['completion'] == 'KO - TIMEOUT':
        n = True
        while n:
            aki = Akinator()
            pars, timestamp = aki.start_game(language=language)
            frontaddr = aki.front()

            if pars is None:
                return HttpResponse(None)

            parse = pars['parameters']['step_information']
            session = int(pars['parameters']['identification']['session'])
            signature = int(pars['parameters']['identification']['signature'])
            challenge_auth = str(pars['parameters']['identification']['challenge_auth'])

            uri = "ru.akinator.com"
            question_filter = ""
            server = 'https://srv12.akinator.com:9398/ws'
            upd_step = requests.get(
                ANSWER_URL.format(uri, timestamp, server, str('false').lower(), session,
                                  signature, 0, 2, frontaddr, question_filter), headers=HEADERS)

            upd_step = json.loads(",".join(upd_step.text.split("(")[1::])[:-1])
            if upd_step['completion'] == 'KO - TIMEOUT':
                pass
            else:
                r = requests.get(
                    BACK_URL.format(server, timestamp, 'false', session, signature, parse['step'], question_filter),
                    headers=HEADERS)
                resp = json.loads(",".join(r.text.split("(")[1::])[:-1])
                n = False

    aks = akin(session=session, signature=signature, challenge_auth=challenge_auth,
               answers='{}|{}|{}|{}|{}'.format(parse['question'], parse['step'],
                                               parse['progression'], parse['questionid'], parse['infogain']),
               timestamp=timestamp, frontaddr=frontaddr, user_id=user_id)
    aks.save()

    answer = pars
    # answer['parameters'] = answer['parameters']['step_information']

    answer = json.dumps(answer, ensure_ascii=False)
    return HttpResponse(answer)


def start_game_without_KO_TIMEOUT(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    if gg(request, request.GET.get('id')):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    user_id = request.GET.get('id')
    if user_id is None:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    try:
        user_id = int(user_id)
    except Exception:
        pass

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps({'error': 'profile not found'}, ensure_ascii=False))

    language = request.GET.get('language')
    if language is None:
        language = 'ru'

    aki = Akinator()

    # timestamp = time.time()

    pars, timestamp = aki.start_game(language=language)
    frontaddr = aki.front()

    if pars is None:
        return HttpResponse(None)

    parse = pars['parameters']['step_information']

    session = int(pars['parameters']['identification']['session'])
    signature = int(pars['parameters']['identification']['signature'])
    challenge_auth = str(pars['parameters']['identification']['challenge_auth'])

    uri = "ru.akinator.com"
    question_filter = ""
    server = 'https://srv12.akinator.com:9398/ws'

    upd_step = requests.get(
        ANSWER_URL.format(uri, timestamp, server, str('false').lower(), session,
                          signature, 0, 2, frontaddr, question_filter), headers=HEADERS)

    upd_step = json.loads(",".join(upd_step.text.split("(")[1::])[:-1])
    if upd_step['completion'] == 'KO - TIMEOUT':
        n = True
        while n:
            aki = Akinator()
            pars, timestamp = aki.start_game(language=language)
            frontaddr = aki.front()

            if pars is None:
                return HttpResponse(None)

            parse = pars['parameters']['step_information']
            session = int(pars['parameters']['identification']['session'])
            signature = int(pars['parameters']['identification']['signature'])
            challenge_auth = str(pars['parameters']['identification']['challenge_auth'])

            uri = "ru.akinator.com"
            question_filter = ""
            server = 'https://srv12.akinator.com:9398/ws'
            upd_step = requests.get(
                ANSWER_URL.format(uri, timestamp, server, str('false').lower(), session,
                                  signature, 0, 2, frontaddr, question_filter), headers=HEADERS)

            upd_step = json.loads(",".join(upd_step.text.split("(")[1::])[:-1])
            if upd_step['completion'] == 'KO - TIMEOUT':
                pass
            else:
                r = requests.get(
                    BACK_URL.format(server, timestamp, 'false', session, signature, parse['step'], question_filter),
                    headers=HEADERS)
                resp = json.loads(",".join(r.text.split("(")[1::])[:-1])
                n = False

    aks = akin(session=session, signature=signature, challenge_auth=challenge_auth,
               answers='{}|{}|{}|{}|{}'.format(parse['question'], parse['step'],
                                               parse['progression'], parse['questionid'], parse['infogain']),
               timestamp=timestamp, frontaddr=frontaddr, user_id=user_id)
    aks.save()

    answer = pars
    # answer['parameters'] = answer['parameters']['step_information']

    answer = json.dumps(answer, ensure_ascii=False)
    return HttpResponse(answer)


def update(request, child_mode=False):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    if gg(request):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    """
    Args:
        session:
        signature:
        challenge_auth:
        step:
        ans:

        request:
                https://domain/aki/update/?session=&signature=&challenge_auth=&step=&ans=
    Returns:
    """
    try:
        session = int(request.GET.get('session'))
        signature = int(request.GET.get('signature'))
        step = int(request.GET.get('step'))
        ans = int(request.GET.get('ans'))
    except ValueError:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    if session > 100000 or signature > 179858659200:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    challenge_auth = request.GET.get('challenge_auth')

    if 4 < ans < 0:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    if (session or signature or challenge_auth or step or ans) is None:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    # session = 233
    # signature = 344771339
    # challenge_auth = "b8e896a0-0423-4cdf-a7e4-7d9a24e2bab7"
    try:
        aks = akin.objects.get(session=session, signature=signature, challenge_auth=challenge_auth)
    except ObjectDoesNotExist:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    if aks.game_end:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    timestamp = aks.timestamp
    frontaddr = aks.frontaddr
    user_id = aks.user_id
    uri = "ru.akinator.com"
    question_filter = ""
    server = 'https://srv12.akinator.com:9398/ws'

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps({'error': 'profile not found'}, ensure_ascii=False))

    # return HttpResponse('{}'.format(ANSWER_URL.format(uri, timestamp, server, str(child_mode).lower(), session, signature, step, ans, frontaddr, question_filter)))

    r = requests.get(
        ANSWER_URL.format(uri, timestamp, server, str(child_mode).lower(), session,
                          signature, step, ans, frontaddr, question_filter), headers=HEADERS)

    ahahaha = r.text

    if r.text[19:36] == "KO - UNAUTHORIZED":
        return HttpResponse(json.dumps(r.text, ensure_ascii=False))  # проверка на не правильный ответ

    r = json.loads(",".join(r.text.split("(")[1::])[:-1])

    if r['completion'] == 'OK':
        step = int(r["parameters"]["step"])
    else:
        return HttpResponse(json.dumps(ahahaha, ensure_ascii=False))

    if float(r['parameters']['progression']) > 80.0:
        resp = win(server=server, timestamp=timestamp, session=session, signature=signature, step=step)
        a = {"element": {"id": "48560", "name": "кот-флейтист", "id_base": "2240792", "proba": "0.871314",
                         "description": "кот-флейтист", "valide_contrainte": "1", "ranking": "9", "pseudo": "X",
                         "picture_path": "partenaire/p/2240792__1164578741.jpg", "corrupt": "1", "relative": "0",
                         "award_id": "-1", "flag_photo": 0,
                         "absolute_picture_path": "https://photos.clarinea.fr/BL_6_ru/600/partenaire/p/2240792__1164578741.jpg"}}

        if resp['completion'] == 'OK':
            el = resp['parameters']['elements'][0]['element']  # el problema ппххпхп

            resp['parameters']['elements'] = el
            resp['type'] = "win"

            id = el['id']
            name = el['name']
            id_base = el['id_base']
            proba = el['proba']
            description = el['description']
            letters = ["порн", "порно", "секс", "взрослое", "взрослого кино", "эроти", "эскорт"]
            isNotChild = False
            for i in letters:
                if str(description).find(i) != -1:
                    aks.isNotChild = True
                    isNotChild = True
                    break

            resp['isLimitation'] = isNotChild

            absolute_picture_path = el['absolute_picture_path']

            aks.character = '{}|{}|{}|{}|{}|{}'.format(id, name, id_base, proba, description, absolute_picture_path)
            aks.game_end = True
            aks.save()
            if profile.how_left <= 0:
                pass
            else:
                profile.how_left -= 1

            profile.how_start += 1
            profile.save()

        return HttpResponse(json.dumps(resp, ensure_ascii=False))

    parse = r['parameters']
    answers = ';{}|{}|{}|{}|{}'.format(parse['question'], parse['step'],
                                       parse['progression'], parse['questionid'], parse['infogain'])
    aks.answers += answers
    aks.save()

    var = {"parameters": {"step_information": {
        "answers": [{"answer": "Да"}, {"answer": "Нет"}, {"answer": "Я не знаю"}, {"answer": "Возможно Частично"},
                    {"answer": "Скорее нет Не совсем"}], "step": "0", "questionid": "800", "progression": "0.00000",
        "infogain": "0.00000", "question": "Ваш персонаж существовал в реальности?"}}, "completion": "OK"}

    answer_how_start_game = {"parameters":
        {"step_information": {
            "answers": r['parameters']['answers'], "step": r['parameters']['step'],
            "progression": r['parameters']['progression'], "question": r['parameters']['question']
        }}, "completion": r['completion'], }

    return HttpResponse(json.dumps(answer_how_start_game, ensure_ascii=False))


def last_games(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    if gg(request):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    answer = {1: []}
    html = requests.get('https://ru.akinator.com/').text
    soup = BeautifulSoup(html, 'html.parser')
    soup = soup.find("div", {"class": "content session-text"})
    soup = soup.find_all('li')
    for i in soup:
        answer[1].append(i.text)
    return HttpResponse(json.dumps(answer, ensure_ascii=False))


def how_games(request):
    timeRecieved = ''
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    user_id = query_params['vk_user_id']
    if gg(request, user_id=user_id):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    '''    
    place_in_top = 1
    while True:

        delitel = len(most_games_players) // 2
        if most_games_players[delitel].how_start < user_games:
            most_games_players = most_games_players[delitel:-1]
            place_in_top += delitel
        elif most_games_players[delitel].how_start > user_games:
            most_games_players = most_games_players[0:delitel]
            place_in_top -= delitel
        elif most_games_players[delitel].how_start == user_games:
            place_in_top += delitel
            break
    place_in_top = 1    
    '''

    most_games_players = np.array(profiles.objects.order_by('-how_start'))
    place_in_top = 0
    count = 0
    for i in most_games_players:
        count += 1
        if i == profile:
            place_in_top = count
            break

    if profile.how_left <= 0:
        profile.how_left = 0

    if int(time.time()) > profile.timestamp_bonus + 86400:
        isAvailable = True
        timeRecieved = f'Тебе дается 2 бесплатные попытки, нажми чтобы собрать их.'
        profile.how_left += 2
        #profile.timestamp_bonus = int(time.time())
    else:
        isAvailable = False
        if (int(time.time()) - profile.timestamp_bonus + 86400) > 3599:
            hours = (profile.timestamp_bonus + 86400 - int(time.time())) // 3600
            if hours == 11:
                timeRecieved = f'Заходи через {hours} часов и получишь бесплатные игры'
            elif 21 > hours % 10 > 4:
                timeRecieved = f'Заходи через {hours} часов и получишь бесплатные игры'
            elif hours % 10 == 2 or hours % 10 == 3 or hours % 10 == 4:
                timeRecieved = f'Заходи через {hours} часа и получишь бесплатные игры'
            elif hours % 10 == 1:
                timeRecieved = f'Заходи через {hours} час и получишь бесплатные игры'
        else:
            timeRecieved = 'Бонус ждет тебя совсем скоро, заходи через час и получишь его!'
    answer = {'games_start': profile.how_start, 'games_left': profile.how_left, 'place_in_top': place_in_top,
              'isAvailable': isAvailable, 'timeReceived': timeRecieved}
    profile.save()
    return HttpResponse(json.dumps(answer, ensure_ascii=False))


@csrf_exempt
@ensure_csrf_cookie
def post_new_user(request):
    if str(request.method) != 'POST':
        response = HttpResponse("Данил. Хватит. Умоляю. Этот хост стоит 150 руб, не надо с ним так.</br> Спасибо!")
        return response

    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    query_params = dict(parse_qsl(urlparse(url=url).query, keep_blank_values=True))
    id_vk = query_params['vk_user_id']
    if gg(request):
        pass
    else:
        return HttpResponse(json.dumps(False, ensure_ascii=False))

    '''
    try:
        profile = profiles.objects.get(user_id=id_vk)
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    except Exception:
        pass
    '''
    user_id = id_vk
    user_vk = requests.get(
        f"https://api.vk.com/method/users.get?user_ids={user_id}&access_token={token}&fields=photo_200_orig,photo_max_orig&v=5.126").json()
    user_vk = user_vk['response'][0]
    snf = f"{user_vk['first_name']} {user_vk['last_name']}"
    img = user_vk['photo_max_orig']

    p = profiles(user_id=id_vk, snf=snf, img=img, how_start=0, how_left=5, how_referals=0,
                 timestamp_register=int(time.time()), timestamp_bonus=int(time.time()))  # Это на прод
    try:
        p.save()
    except Exception as e:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    response = HttpResponse(json.dumps(user_vk, ensure_ascii=False))
    return response


def last_10_games(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    if gg(request):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    all_akin = akin.objects.filter(character__isnull=False)
    answer = {}

    try:
        last = all_akin[len(all_akin) - 10:len(all_akin)]
    except AssertionError:
        last = all_akin

    count = 0
    for i in last:
        spi = str(i.character).split('|')
        isNotChild = i.isNotChild
        answer[count] = {'name': spi[1], 'opisanie': spi[4], 'img': spi[5], 'isLimitation': isNotChild}
        count += 1

    a = answer

    keys, value = list(a.keys()), list(reversed(list(a.values())))
    answer = {}
    count = 0

    for i in keys:
        answer[i] = value[count]
        count += 1

    return HttpResponse(json.dumps(answer, ensure_ascii=False))


def add_try(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    user_id = query_params['vk_user_id']
    if gg(request, user_id=user_id):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    # aks = akin.objects.get(session=session, signature=signature, challenge_auth=challenge_auth)

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    points = request.GET.get('points')
    profile = profiles.objects.get(user_id=user_id)
    profile.how_left += int(points)
    profile.save()

    return HttpResponse(json.dumps(True, ensure_ascii=False))


def rating(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    if gg(request):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    # user_id = request.GET.get('id')

    answer = {}
    most_games_player = profiles.objects.order_by('-how_start')

    most_games_player = most_games_player[:10]

    rating_players_id = ""
    for i in most_games_player:
        rating_players_id += str(i.user_id) + ","

    if rating_players_id[-1] == ",":
        rating_players_id = rating_players_id[0:-1]

    user_vk = requests.get(
        f"https://api.vk.com/method/users.get?user_ids={rating_players_id}&access_token={token}&fields=photo_200_orig,photo_max_orig"
        f"&v=5.126").json()

    answer = {}
    count = 0
    for i in range(len(user_vk['response'])):
        profile = profiles.objects.get(user_id=user_vk['response'][i]['id'])
        user_vk['response'][i]['name'] = user_vk['response'][i]['first_name'] + ' ' + user_vk['response'][i][
            'last_name']
        user_vk['response'][i]['img'] = user_vk['response'][i]['photo_max_orig']
        user_vk['response'][i]['isDonut'] = profile.isDonate
        user_vk['response'][i]['how_start'] = profile.how_start
        answer[count] = user_vk['response'][i]
        count += 1

    return HttpResponse(json.dumps(answer, ensure_ascii=False))


def get_last_games_id(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    user_id = query_params['vk_user_id']
    try:
        user_id = int(user_id)
    except ValueError:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    if gg(request, user_id=user_id):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    answer = {}
    try:
        games = akin.objects.filter(user_id=user_id).filter(character__isnull=False)
        characters = np.array(games)
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    character = {}
    character_description = {}
    for i in characters:
        try:
            character[str(i.character).split('|')[1]] += 1
        except:
            character[str(i.character).split('|')[1]] = 1

    for i in characters:
        character_description[str(i.character).split('|')[1]] = {
            'name': str(i.character).split('|')[1],
            'img': str(i.character).split('|')[-1],
            'opisanie': str(i.character).split('|')[4],
            'isLimitation': i.isNotChild,
            'count': character[str(i.character).split('|')[1]]
        }
    answer = {}
    for i in reversed(character_description.keys()):
        answer[i] = character_description[i]

    return HttpResponse(json.dumps(answer, ensure_ascii=False))


def _rating(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    user_id = request.GET.get('id')
    if gg(request, user_id=user_id):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    answer = {}
    most_games_player = profiles.objects.order_by('-how_start')

    if user_id == None:
        return HttpResponse(json.dumps(answer, ensure_ascii=False))

    else:
        t1 = time.time()
        a = list(most_games_player)
        answer['player'] = a.index(most_games_player.get(user_id=user_id)) + 1
        return HttpResponse(json.dumps(answer, ensure_ascii=False))


def referals(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")
    '''
    if gg(request.headers.get('xvk')):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    '''
    from_id = request.GET.get('from')
    to = request.GET.get('to')
    if int(from_id) == int(to):
        return HttpResponse(
            json.dumps({'error': 'from_id==to'}, ensure_ascii=False))  # Проверка на то, не один ли это пользователь
    try:
        profile = profiles.objects.get(user_id=from_id)
    except Exception:
        return HttpResponse(json.dumps({'error': 'profile_not_found'}, ensure_ascii=False))
    ref = profile.referals  #
    if ref is None:
        pass
    else:
        ref = ref.split(',')
        if len(ref) >= 100:
            return HttpResponse(json.dumps({'error': 'profile_ref>100'}, ensure_ascii=False))
        if to in ref:
            return HttpResponse(json.dumps({'error': 'already_in_referal'}, ensure_ascii=False))
    if profile.referals == "":
        profile.referals = to
        profile.how_referals = 1
    else:
        profile.referals += ',{}'.format(to)
        profile.how_referals += 1
    profile.how_left += int(3)

    try:
        profile_to = profiles.objects.get(user_id=int(to))
    except Exception:
        return HttpResponse(json.dumps({'error': 'profile_not_register'}, ensure_ascii=False))

    if profile_to.timestamp_register + 4 < int(time.time()):
        return HttpResponse(json.dumps({'error': 'profile_already_register'}, ensure_ascii=False))

    if profile_to.who_referal is not None:
        return HttpResponse(json.dumps({'error': 'profile_already_register'}, ensure_ascii=False))
    else:
        profile_to.who_referal = int(from_id)
        profile_to.how_left += 3
        profile_to.isInvite = True

    profile.save()
    profile_to.save()

    return HttpResponse(json.dumps({'a': profile.snf}, ensure_ascii=False))


def get_referals(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    user_id = query_params['vk_user_id']

    if gg(request, user_id=user_id):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    if profile.how_referals == 0:
        answer = {'referals': [], 'how_referals': 0}
    else:
        user_vk = requests.get(
            f"https://api.vk.com/method/users.get?user_ids={profile.referals}&access_token={token}&fields=photo_max_orig,photo_200_orig&v=5.126").json()

        for i in user_vk['response']:
            i['name'] = i['first_name'] + " " + i['last_name']
            i['img'] = i['photo_max_orig']

        answer = {'referals': user_vk['response'], 'how_referals': profile.how_referals}

    return HttpResponse(json.dumps(answer, ensure_ascii=False))


def daily_rating(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    if gg(request):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    def value_counts(list, x):
        count = 0
        for i in list:
            if i == x:
                count += 1

        return count

    date = datetime.date.today()
    today_unix = time.mktime(datetime.datetime.strptime(str(date), "%Y-%m-%d").timetuple())

    aki = akin.objects.filter(timestamp__gte=today_unix).filter(character__isnull=False)

    character = []
    akis = {}
    for persons in aki:
        character.append(persons.character.split('|')[1])
        akis[persons.character.split('|')[1]] = [persons.character.split('|')[5], persons.isNotChild]

    personCount = {}
    for i in character:
        count = value_counts(character, i)
        personCount[i] = count

    answer = []
    for i in personCount:
        answer.append({'name': i, 'count': personCount[i], 'img': akis[i][0], 'isLimitation': akis[i][1]})

    return HttpResponse(json.dumps(answer, ensure_ascii=False))


def add_donate(request):
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")
    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    user_id = query_params['vk_user_id']
    if gg(request, user_id=user_id):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    if profile is None:
        HttpResponse(json.dumps(False, ensure_ascii=False))
    else:
        profile.isDonate = True
        return HttpResponse(json.dumps(True, ensure_ascii=False))


def remove_donate(request):
    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    user_id = query_params['vk_user_id']
    if request.method == 'GET':
        pass
    else:
        return HttpResponse("Сделай ты GET запрос!")

    if gg(request, user_id=user_id):
        pass
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    user_id = request.GET.get('id')
    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    if profile is None:
        return HttpResponse(json.dumps(False, ensure_ascii=False))
    else:
        profile.isDonate = False
        return HttpResponse(json.dumps(True, ensure_ascii=False))


def test(request):
    games = akin.objects.get(user_id=380320460)
    answer = np.array(games)
    return HttpResponse(answer)


def test_headers(request):
    user_id = request.GET.get('id')
    if gg(request, user_id=user_id):
        return HttpResponse(json.dumps(True, ensure_ascii=False))  # а эт надо будет убрать в проде
    else:
        return HttpResponse(json.dumps(None, ensure_ascii=False))  # а эт надо будет убрать в проде


def ip(request):
    var = {
        0: {
            'name': 'name',
            'img': 'img',
            'opisanie': 'opisanie',
            'isLimitation': 'isLimitation',
            'count': 'count',
        },
        1: {
            'name': 'name',
            'img': 'img',
            'opisanie': 'opisanie',
            'isLimitation': 'isLimitation',
            'count': 'count',
        },
    }

    games = akin.objects.filter(user_id=380320460).filter(character__isnull=False)
    characters = np.array(games)

    character = {}
    for i in characters:
        try:
            character[str(i.character).split('|')[1]] += 1
        except:
            character[str(i.character).split('|')[1]] = 1

    return HttpResponse(json.dumps(character, ensure_ascii=False))


@csrf_exempt
@ensure_csrf_cookie
def rating_beetween_friends(r):
    if str(r.method) != 'POST':
        response = HttpResponse("Данил. Хватит. Умоляю. Этот хост стоит 150 руб, не надо с ним так.</br> Спасибо!")
        return response

    if gg(r):
        pass
    else:
        return HttpResponse(json.dumps(False, ensure_ascii=False))

    answer = []
    try:
        url = 'https://example.com/?' + r.headers.get('xvk')
        query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
        user_id = int(query_params['vk_user_id'])
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))
    profiles_player = profiles.objects.order_by('-how_start')
    req = requests.get(
        f"https://api.vk.com/method/friends.get?user_id={user_id}&access_token={service_key}&order=random&fields"
        f"=nickname,photo_200_orig&v=5.126").json()
    friend_user = []
    try:
        for i in req['response']['items']:
            friend_user.append(i['id'])
    except KeyError:
        return HttpResponse(json.dumps({'error': 'profile_private'}, ensure_ascii=False))

    pre_answer = []
    for friend in friend_user:
        try:
            profile_friend = profiles_player.get(user_id=int(friend))
            ans = {
                "name": profile_friend.snf,
                "img": profile_friend.img,
                "how_start": profile_friend.how_start,
                'id': profile_friend.user_id
            }
            pre_answer.append(ans)
        except Exception:
            pass

    for i in range(len(pre_answer)):
        for j in range(i, len(pre_answer)):
            if pre_answer[i]['how_start'] < pre_answer[j]['how_start']:
                pre_answer[i], pre_answer[j] = pre_answer[j], pre_answer[i]

    return HttpResponse(json.dumps(pre_answer, ensure_ascii=False))

def get_attemp(request):
    if str(request.method) != 'GET':
        response = HttpResponse("Данил. Хватит. Умоляю. Этот хост стоит 150 руб, не надо с ним так.</br> Спасибо!")
        return response

    if gg(request):
        pass
    else:
        return HttpResponse(json.dumps(False, ensure_ascii=False))

    try:
        url = 'https://example.com/?' + request.headers.get('xvk')
    except Exception:
        return HttpResponse(json.dumps(None, ensure_ascii=False))

    query_params = dict(parse_qsl(urlparse(url=url).query, keep_blank_values=True))
    user_id = query_params['vk_user_id']

    try:
        profile = profiles.objects.get(user_id=user_id)
    except Exception:
        return HttpResponse("Ты пытаешься сломать что-то? Ага, ага, пытайся")

    if int(time.time()) > profile.timestamp_bonus + 86400:
        profile.how_left += 2
        profile.timestamp_bonus = int(time.time())
        profile.save()
    else:
        return HttpResponse(json.dumps({'error' : 'Сутки не прошли'}, ensure_ascii=False))

    return HttpResponse(json.dumps({}, ensure_ascii=False))