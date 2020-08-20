import requests
import hashlib
from dotenv import load_dotenv
import os


def get_jwt_token(url_template, fedresurs_password):
    url = url_template.format('v1/auth')
    payload = {
        'login': 'demo',
        'passwordHash': fedresurs_password
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    jwt_token = response.json()['jwt']
    with open('.env', 'at', encoding='utf-8') as trg:
        print(f'\nJWT_TOKEN={jwt_token}', file=trg)
    return jwt_token


def get_messages(url_template, jwt_token, fedresurs_password, participant_type, participant_code):
    jwt_token = get_jwt_token(url_template, fedresurs_password)  # пока будем авторизовываться заново каждый раз, потом можно оптимизировать
    url = url_template.format('v1/messages')
    headers = {'Authorization': f'Bearer {jwt_token}'}
    offset = 0
    i = 0
    all_messages = []
    while True:
        payload = {
            'messageTypes': 'StopFinancialLeaseContract',  # заменить на нужные типы
            'participant.type': participant_type,
            'participant.code': participant_code,
            'limit': 20,
            'offset': offset
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        messages = response.json()
        if messages['total'] == 0:
            break
        for message in messages['messages']:
            d = {
                'guid': message['guid'],
                'description': message['messageType']['description'],
                'date': message['datePublish'],
            }
            all_messages.append(d)
        offset += 20
        return all_messages


load_dotenv()

fedresurs_login = os.getenv('FEDRESURS_LOGIN')
fedresurs_password = hashlib.sha512(str.encode(os.getenv('FEDRESURS_PASSWORD'))).hexdigest().upper()
jwt_token = os.getenv('JWT_TOKEN')

if fedresurs_login == 'demo':
    url_template = 'https://services.fedresurs.ru/SignificantEvents/MessagesServiceDemo2/{}/'
else:
    url_template = 'https://services.fedresurs.ru/SignificantEvents/MessagesService2/{}/'

participant_type = 'Company'
participant_code = 1027700109271  # пример

messages = get_messages(url_template, jwt_token, fedresurs_password, participant_type, participant_code)
print(messages)
