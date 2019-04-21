"""

-> medal.pythonanywhere.com <-

"""

# medal red dream
# импортируем библиотеки
from flask import Flask, request
import logging
import requests
import math

import json


class GameData:

    def __init__(self):
        self.quest_data = {}


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
sessionStorage = {}


@app.route('/red_dream', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    with open("/home/medal/mysite/quest.json", "r", encoding="utf8") as file:
        GameData.quest_data = json.loads(file.read())

    # Начинаем формировать ответ, согласно документации
    # мы собираем словарь, который потом при помощи библиотеки json преобразуем в JSON и отдадим Алисе
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    start(request.json, response)

    logging.info('Response: %r', request.json)

    return json.dumps(response)


def start(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,  # здесь будет храниться имя
            'game_started': False  # здесь информация о том, что пользователь начал игру. По умолчанию False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Сыграешь в игру?'
            init_buttons(req, res, ["Да", "Нет"])

    else:
        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                sessionStorage[user_id]['game_started'] = True
                handle_dialog(req, res)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'
                init_buttons(req, res, ["Да", "Нет"])
        else:
            handle_dialog(req, res)


def handle_dialog(req, res):
    res['response']['text'] = GameData.quest_data["questions"][0]["text"]
    return


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


def change_period(req, res, count_answers, users_answers):
    """ Проверка смены периода """
    if count_answers == users_answers:
        res['response']['text'] = ""
        # Здесь переход в новую эпоху
    return


def is_liveable(req, res, params):
    """ Проверка жизнеспособности страны """
    # params - словарь показателей страны
    #   (name: показатель, value: значение, max: максимум, min: минимум,
    #       warn_min: предупреждение, warn_max: предупреждение
    #       end_max: концовка 1, end_min: концовка 2)
    for param in params:
        if param["value"] == param["max"]:
            res['response']['text'] = param["end_max"]
            return
        elif param["value"] == param["min"]:
            res['response']['text'] = param["end_min"]
            return
        elif round(param["value"]) == param["min"]:
            res['response']['text'] = param["warn_min"]
            return
        elif round(param["value"]) == param["max"]:
            res['response']['text'] = param["warn_max"]
            return
    return


def question(req, res, text, variants, results):
    """ Показ вопроса, вариантов ответа и вывод последствий. """
    # results - список ответов в том же порядке вопросов
    res['response']['text'] = text
    init_buttons(req, res, variants)
    answer = req['request']['original_utterance']
    for i, result in enumerate(variants):
        if answer == result:
            res['response']['text'] = results[i]


def init_buttons(req, res, buttons):
    res['response']['buttons'] = [
        {
            'title': button,
            'hide': True
        } for button in buttons

    ]


if __name__ == '__main__':

    app.run()
