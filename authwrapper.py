# import httplib
from auth0.v2.management import Auth0
import os
import json

import requests

# from dotenv import Dotenv
# env = Dotenv('./.env')
env = os.environ


class auth0Wrapper:
    def get_token(self):
        json_header = {'content-type': 'application/json'}
        token_url = 'https://guestmealme.auth0.com/oauth/token'

        token_payload = {
            'client_id' : env['AUTH0_CLIENT_ID'],
            'client_secret' : env['AUTH0_CLIENT_SECRET'],
            'audience'      : "https://guestmealme.auth0.com/api/v2/",
            'grant_type'    : "client_credentials"
        }

        token_info = requests.post(token_url, data=json.dumps(token_payload),
                                   headers=json_header)
        # print(token_info)

        token_info = token_info.json()
        # print(token_info)

        self.token = token_info['access_token']

    def get_users(self):
        self.get_token()
        auth0 = Auth0(env['AUTH0_DOMAIN'], self.token)
        return auth0.users.list()['users']

    def get_email_from_user_id(self, user_id):
        users = self.get_users()
        for x in users:
            if x['user_id'] == user_id:
                return x['email']

    def get_first_name_from_user_id(self, user_id):
        users = self.get_users()
        for x in users:
            if x['user_id'] == user_id:
                return x['user_metadata']['first_name']
