"""

-> medal.pythonanywhere.com <-

"""

# medal red dream
# импортируем библиотеки
from flask import Flask, request
import logging
import requests
import math
import random
import json


class User:
    quest_data = {}

    def __init__(self, id):
        self.move = 0
        self.id = id
        self.period = ""
        self.government = 0
        self.economy = 0
        self.military = 0
        self.control = 0
        self.communism = 0
        self.questions = None

    def change_params(self, params):
        self.government *= params["government"]
        self.economy *= params["military"]
        self.military *= params["military"]
        self.control *= params["control"]
        self.communism *= params["communism"]


class Question:

    def __init__(self, obj):
        self.text = obj["text"]
        self.date = obj["date"]
        self.period = obj["period"]
        self.answers = obj["answers"]

    def get_answers_titles(self):
        return [el["text"] for el in self.answers]

    def get_effects_on_answer(self, data):
        for answer in self.answers:
            if answer["text"] == data:
                return answer["effects"]

    def get_cause_effect(self, data):
        for answer in self.answers:
            if answer["text"] == data:
                return answer["cause"]

    def __str__(self):
        return self.text


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
sessionStorage = {}


@app.route('/red_dream', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    with open("quest.json", "r", encoding="utf8") as file:
        User.quest_data = json.loads(file.read())

    # Начинаем формировать ответ, согласно документации
    # мы собираем словарь, который потом при помощи библиотеки json преобразуем в JSON и отдадим Алисе
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    user_id = request.json['session']['user_id']

    start(request.json, response)

    logging.info('Response: %r', request.json)

    return json.dumps(response)


def start(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        user = User(user_id)
        user.questions = make_questions_list(User.quest_data)
        sessionStorage[user_id] = {
            'first_name': None,  # здесь будет храниться имя
            'game_started': False,  # здесь информация о том, что пользователь начал игру. По умолчанию False
            'user': user,
            "current_question": 0
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
    try:
        user_id = req['session']['user_id']
        current = sessionStorage[user_id]['current_question']
        next_question = Question(sessionStorage[user_id]["user"].questions[current])
        if current:
            past_question = Question(sessionStorage[user_id]["user"].questions[current - 1])
            analyze_answer(req, res, past_question.get_cause_effect(req['request']['original_utterance']),
                           past_question.get_effects_on_answer(req['request']['original_utterance']))

            res['response']['text'] += "\n" + str(next_question)
        else:
            res['response']['text'] = str(next_question)
        init_buttons(req, res, next_question.get_answers_titles())
        sessionStorage[user_id]['current_question'] += 1
        return
    except IndexError:
        res['response']['text'] = 'Игра закончена'


def analyze_answer(req, res, effect, params):
    user_id = req['session']['user_id']
    user = sessionStorage[user_id]['user']
    user.change_params(params)
    res['response']['text'] = effect
    # if not is_liveable(req, res, user.get_params()):
    #   res['response']['text'] = 'Игра закончена'
    #    return
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


def make_questions_list(data):
    questions_list = []
    counts = {}
    for question in sorted(data["questions"], key=lambda key: random.random()):
        counts[question["period"]] = counts.get(question["period"], 0) + 1
        if counts[question["period"]] <= 2:
            questions_list.append(question)

    questions_list.sort(key=lambda el: el["date"])

    return questions_list


if __name__ == '__main__':
    app.run()
