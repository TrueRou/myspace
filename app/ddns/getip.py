import json
import os
from time import sleep

import urllib3.exceptions
from godaddypy import Client, Account

import requests

from app.ddns import ipconfig


def get_ip(forced=False):
    try:
        client = Client(Account(api_key=ipconfig.api_key, api_secret=ipconfig.api_secret))
        response = requests.request("GET", ipconfig.getip_url)
        data = json.loads(response.text)
        if data['isp'] == "电信":
            ipconfig.do_task(client, data['ip'])
            print('IP is updated at ' + data['ip'])
        elif forced:
            sleep(5)  # Fuck you windows why not give options to network card
            get_ip(True)
    except (requests.exceptions.ConnectionError, urllib3.exceptions.ProtocolError):
        print('Failed to access the Internet, Try rasdial')
        os.system(f'rasdial {ipconfig.adsl_name} {ipconfig.adsl_account} {ipconfig.adsl_password}')


