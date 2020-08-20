import requests
import hashlib
from dotenv import load_dotenv
import os
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json


class Key(BaseModel):
    type_: str
    code: int


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


def get_messages_for_company(url_template, jwt_token, fedresurs_password, participant_type, participant_code):
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


def load_tasks(filepath):
    with open(filepath, 'rt') as src:
        try:
            tasks = json.load(src)
        except json.decoder.JSONDecodeError:
            tasks = []
    return tasks


Path('files').mkdir(exist_ok=True)
filepath = Path('files') / Path('tasks.json')
filepath.touch(exist_ok=True)

load_dotenv()

fedresurs_login = os.getenv('FEDRESURS_LOGIN')
fedresurs_password = hashlib.sha512(str.encode(os.getenv('FEDRESURS_PASSWORD'))).hexdigest().upper()
jwt_token = os.getenv('JWT_TOKEN')

if fedresurs_login == 'demo':
    url_template = 'https://services.fedresurs.ru/SignificantEvents/MessagesServiceDemo2/{}/'
else:
    url_template = 'https://services.fedresurs.ru/SignificantEvents/MessagesService2/{}/'



app = FastAPI()


@app.get('/')
def root():
    return {'hello' : 'world'}


@app.post('/task/', status_code=201)
def create_task(key:Key):
    tasks = load_tasks(filepath)
    task = key.dict()
    if tasks:
        task['guid'] = tasks[-1]['guid'] + 1
    else:
        task['guid'] = 0
    tasks.append(task)
    with open(filepath, 'wt') as trg:
        json.dump(tasks, trg)
    return {'task_guid': task['guid']}


# @app.post('/messages/')
# def get_messages(task_guid: int):
    # tasks = load_tasks
    # task = list(filter(lambda task: tasks['guid'] == task_guid, tasks))
    # participant_type = task['type_']
    # participant_code = task['code']
    # messages = get_messages_for_company(url_template, jwt_token, fedresurs_password, participant_type, participant_code)
    # return messages
