import hmac 
import hashlib
import base64
import json
import time
import requests
import logging

import Common.not_secret_info as secrets

class Utils:
	@staticmethod
	def get_timestamp():
		return int(round(time.time() * 1000))

	@staticmethod
	def generate_signature(body):
		secret_bytes = bytes(secrets.secret_key, encoding='utf-8')
		json_body = json.dumps(body, separators = (',', ':'))
		signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

		headers = {
    				'Content-Type': 'application/json',
    				'X-AUTH-APIKEY': secrets.public_key,
    				'X-AUTH-SIGNATURE': signature
				}

		return json_body, headers

	@staticmethod
	def process_requests(url, query={}):
		response = requests.get(url, params=query).json()
		if "code" in response:
			print(f"Code : {response['code']} | Status : {response['status']} | Message : {response['message']}")
			return None

		return response

	@staticmethod
	def post_request(url, body, header):
		response = requests.post(url, data = body, headers = header).json()
		if "code" in response:
			print(f"Code : {response['code']} | Status : {response['status']} | Message : {response['message']}")
			return None
		if response == None:
			print(f"Unknown error occured")

		return response

	@staticmethod
	def setup_logger(log_path):
		logging.basicConfig(filename=log_path, 
							format='%(asctime)s :: %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
		
		return logging.getLogger(__name__)
