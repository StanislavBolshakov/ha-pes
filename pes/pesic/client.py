import requests
import json
import ssl
from urllib3 import poolmanager
from .custom_exceptions import MissingArgumentError, TokenError


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


class RestClient:
    def __init__(self, base_url: str = None, token: str = None) -> None:
        self.token = token
        if base_url is None:
            # Mobile App uses https://ikus.pesc.ru/ikus4 endpoint
            self.base_url = 'https://ikus.pesc.ru/api'

        if token is None:
            raise MissingArgumentError('The authentication token must be supplied')
        
        self.session = requests.session()
        self.session.mount('https://', TLSAdapter())

    def get(self, url):
        header = {'Authorization': 'Bearer ' + self.token, 'rs': 'ma'}
        response = self.session.get(self.base_url + url, headers=header)

        if type(response.json()) == dict and response.json().get('code') == '5':
            raise TokenError('The authentication token seems to be out of date or malformed')
        return response.json()

        
    def post(self, url, data):
        header = {
            'accept-encoding': 'gzip',
            'Authorization': 'Bearer ' + self.token,
            'content-type': 'application/json',
            'rs': 'ma'
        }
        response = self.session.post(self.base_url + url, headers=header, data=json.dumps(data))
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            return response.text
