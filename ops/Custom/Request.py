import json
from django.conf import settings
import requests
class Request(object):
    def __init__(self):
    	# cursor = conn.cursor()
    	# cursor.execute("SELECT * FROM uf1_users")
    	# records = cursor.fetchall()
    	# pprint.pprint(records)
    	self.data = []

    def post(self, params, method, token=None):
        url = settings.API['base_url']+'v1/'+method+'/'
        payload = params
        headers = {
            'content-type': 'application/json',
            'Authorization':settings.API['key']
        }
        if token is not None:
            headers['Authorization'] += '.'+token

        return requests.post(url, data=payload, headers=headers)

    def get(self, params, method, token=None):
        url = settings.API['base_url']+'v1/'+method+'/'
        payload = params
        headers = {
            'content-type': 'application/json',
            'Authorization':settings.API['key']
        }
        if token is not None:
            headers['Authorization'] += '.'+token

        return requests.get(url, data=payload, headers=headers)




