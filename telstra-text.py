#!/bin/python3

import requests
import argparse
import re
import configparser

##### Get the only two required arguments ######################################

parser = argparse.ArgumentParser(description='Sends a text to a mobile number through Telstra\'s Messaging API.')
parser.add_argument('number', help='The mobile phone number to send the message to')
parser.add_argument('message', help='The message that will be sent')
args = parser.parse_args()

if len(args.message) > 1900:
    print('Message too long (>1900 chars)')
    exit(1)

if not re.match('(\+\d{1,3}[- ]?)?\d{10}', args.number):
    print('Not a valid mobile number')
    exit(1)

##### Read in our ID and secret from config ####################################

config = configparser.ConfigParser()
config_path = '/etc/telstra-text.conf'
config.read(config_path)

if not config.sections():
    print('No existing config was found')
    print('Copy the following blank template into ' + config_path + ' and fill in the blanks:')
    print('[Credentials]\n' + \
          'client_id = \n' + \
          'client_secret = ')
    exit(1)

if not 'Credentials' in config:
    print('Failed to read config: \'Credentials\' section missing')
    exit(1)

if not 'client_id' in config['Credentials']:
    print('Failed to read config: \'client_id\' missing')
    exit(1)

if not 'client_secret' in config['Credentials']:
    print('Failed to read config: \'client_secret\' missing')
    exit(1)

client_id = config['Credentials']['client_id']
client_secret = config['Credentials']['client_secret']

##### Get token ################################################################

headers = {'Content-Type': 'application/x-www-form-urlencoded'}
data = { \
    'client_id':client_id, \
    'client_secret':client_secret, \
    'grant_type':'client_credentials' \
}
response = requests.post('https://tapi.telstra.com/v2/oauth/token', headers=headers, data=data)

if not response.status_code == 200:
    print('Failed to get token')
    print(response.text)
    exit(1)

access_token = response.json()['access_token']
token_type = response.json()['token_type']

##### Get dedicated number #####################################################

headers = { \
    'Authorization':token_type + ' ' + access_token, \
    'Content-Type':'application/json' \
}
response = requests.post('https://tapi.telstra.com/v2/messages/provisioning/subscriptions', headers=headers, data='{}')

if not response.status_code in [201, 204]:
    print('Failed to get dedicated number')
    print(response.text)
    exit(1)

number = response.json()['destinationAddress']

##### Send a text to the number ################################################

headers = { \
    'Authorization':token_type + ' ' + access_token, \
    'Content-Type':'application/json' \
}
data = { \
    'to':args.number, \
    'body':args.message, \
    'from':number \
}
response = requests.post('https://tapi.telstra.com/v2/messages/sms', headers=headers, json=data)

if not response.status_code == 201:
    print('Failed to send SMS')
    print(response.text)
    exit(1)
