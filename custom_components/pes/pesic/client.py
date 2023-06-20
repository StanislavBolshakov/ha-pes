import requests
import json
import ssl
import time
from urllib3 import poolmanager
from .custom_exceptions import MissingArgumentError, TokenError, CredentialsError


class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        self.poolmanager = poolmanager.PoolManager(num_pools=connections,
                                                   maxsize=maxsize,
                                                   block=block,
                                                   ssl_version=ssl.PROTOCOL_TLS,
                                                   ssl_context=ctx)


class RestClient():
    def __init__(self, base_url: str = None, username: str = None, password: str = None) -> None:
        self.retry_count = 0
        self.retry_threshold = 3
        if username is None or password is None:
            raise MissingArgumentError('Username and Password must be supplied')
        self.username = username
        self.password = password
        if base_url is None:
            # Mobile App uses https://ikus.pesc.ru/ikus4 endpoint
            self.base_url = 'https://ikus.pesc.ru/api'

        self.session = requests.session()
        self.session.mount('https://', TLSAdapter())

        self.token = self._fetch_token()

    def _fetch_token(self) -> str:
        header = {'Accept': 'application/json, text/plain, */*', 'Captcha': 'none','Content-Type': 'application/json',}
        data = {'type': 'PHONE', 'login': self.username, 'password': self.password,}
        response = self.session.post('https://ikus.pesc.ru/api/v6/users/auth', headers=header, json=data)
        if type(response.json()) == dict and response.json().get('code') == '3':
            raise CredentialsError("Wrong username or password")
        else:
            return response.json().get('auth')

    def get(self, url):
        while (self.retry_count <= self.retry_threshold):
            header = {'Authorization': 'Bearer ' + self.token}
            response = self.session.get(self.base_url + url, headers=header)
            if type(response.json()) == dict and response.json().get('code') == '5':
                if self.retry_count == self.retry_threshold:
                    raise TokenError('Token regeneration process failed. Aborting')
                else:
                    time.sleep(5)
                    self.retry_count = self.retry_count + 1
                    self.token = self._fetch_token()
                    continue
            else:
                self.retry_count = 0
                return response.json()

        
    def post(self, url, data):
        while (self.retry_count <= self.retry_threshold):
            header = {
                'accept-encoding': 'gzip',
                'Authorization': 'Bearer ' + self.token,
                'content-type': 'application/json'
            }
            response = self.session.post(self.base_url + url, headers=header, data=json.dumps(data))
            print (response.json())
            if type(response.json()) == dict and response.json().get('code') == '5':
                if self.retry_count == self.retry_threshold:
                    raise TokenError('Token regeneration process failed. Aborting')
                else:
                    time.sleep(5)
                    self.retry_count = self.retry_count + 1
                    self.token = self._fetch_token()
                    continue
            else:
                self.retry_count = 0
                try:
                    return response.json()
                except json.decoder.JSONDecodeError:
                    return response.text
