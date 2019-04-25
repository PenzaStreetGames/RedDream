"""
-> medal.pythonanywhere.com <-
"""
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
        self.government = quest["start_values"]["government"]
        self.economy = quest["start_values"]["economy"]
        self.military = quest["start_values"]["military"]
        self.control = quest["start_values"]["control"]
        self.communism = quest["start_values"]["communism"]
        self.questions = []
        self.jumps_questions = []

    def get_params(self):
        return {
            "government": self.government,
            "economy": self.economy,
            "military": self.military,
            "control": self.control,
            "communism": self.communism,
        }

    def change_params(self, params):
        self.government += params["government"]
        self.economy += params["military"]
        self.military += params["military"]
        self.control += params["control"]
        self.communism += params["communism"]
        step = 0.3
        delta = params.copy()
        delta["communism"] = (sum([self.government, self.economy,
                                    self.military, self.control])
                              / 4 - 50) * step
        self.communism += delta["communism"]
        logging.error((sum([self.government, self.economy, self.military,
                            self.control]) / 4 - 50))
        return delta

    def __str__(self):
        return f"Политическая мощь: {round(self.government, 2)}\n" + \
               f"Экономика: {round(self.economy, 2)}\n" + \
               f"Военная мощь: {round(self.military, 2)}\n" + \
               f"Котроль над народом: {round(self.control, 2)}\n" + \
               f"Коммунизм: {round(self.communism, 2)}\n"


class Question:

    def __init__(self, obj):
        self.text = obj["text"]
        self.date = obj["date"]
        self.period = obj["period"]
        self.answers = obj["answers"]

    def get_answers_titles(self):
        return [el["text"] for el in self.answers]

    def get_effects_on_answer(self, data):
        k = quest["k"]
        for answer in self.answers:
            if answer["text"] == data:
                for effect in answer["effects"]:
                    answer["effects"][effect] *= k
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
with open("/home/PenzaStreetNetworks/mysite/quest.json", "r",
          encoding="utf8") as file:
    quest = json.loads(file.read())


@app.route('/red_dream', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    User.quest_data = quest

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
        user.questions, user.jumps_questions = make_questions_list(User.quest_data)
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False,
            'user': user,
            "current_question": 0,
            "echo_effect": False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'Приятно познакомиться, ' \
                f'{first_name.title()}. Я Алиса. Сыграешь в игру ' \
                f'"Красная Мечта"? В ней нужно отвечать на вопросы по ' \
                f'управлению страной и победить, построив коммунизм. Сыграем?'
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
    user_id = req['session']['user_id']
    user = sessionStorage[user_id]["user"]
    if req['request']['original_utterance'] == "Статистика":
        res['response']['text'] = str(user)
        init_buttons(req, res)
        return
    if req['request']['original_utterance'] == "Помощь":
        res['response']['text'] = quest["help"]
        init_buttons(req, res)
        return
    try:
        if not is_liveable(req, res, user.get_params()):
            res['end_session'] = True
            return
        current = sessionStorage[user_id]['current_question']

        echo_effect = sessionStorage[user_id]['echo_effect']
        next_question = Question(user.questions[current])
        if current and echo_effect:
            past_question = Question(user.questions[current - 1])
            analyze_answer(req, res, past_question.get_cause_effect(
                req['request']['original_utterance']),
                           past_question.get_effects_on_answer(
                               req['request']['original_utterance']))

            init_buttons(req, res, ["Дальше", "Статистика", "Помощь"])
            sessionStorage[user_id]['echo_effect'] = False
            return
        if current in list(user.jumps_questions):
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = user.jumps_questions[
                current].title() + "." + quest["jumps"][
                user.jumps_questions[current]]["text"]
            res['response']['card']['image_id'] = quest["jumps"][
                user.jumps_questions[current]]["image"]
            res['response']['text'] = user.jumps_questions[current].title()

            init_buttons(req, res, ["Приступаем!"])
            del user.jumps_questions[current]
            return
        res['response']['text'] = str(next_question)
        init_buttons(req, res, next_question.get_answers_titles())
        sessionStorage[user_id]['current_question'] += 1
        sessionStorage[user_id]['echo_effect'] = True

        return
    except IndexError:
        records = {sessionStorage[user_id]['first_name']: user.get_params()}

        with open("/home/PenzaStreetNetworks/mysite/records.json", "w",
                  encoding="utf8") as file:
            file.write(json.dumps(records))


def analyze_answer(req, res, effect, params):
    user_id = req['session']['user_id']
    user = sessionStorage[user_id]['user']
    delta = user.change_params(params)
    res['response']['text'] = effect + string_effects(delta, delta=True)
    if not is_liveable(req, res, user.get_params()):
        res['response']['text'] += '\nИгра закончена!'
        return
    return


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


def change_period(req, res, count_answers, users_answers):
    """ Проверка смены периода """
    if count_answers == users_answers:
        res['response']['text'] = ""
        # Здесь переход в новую эпоху
    return


def is_liveable(req, res, params):
    """ Проверка жизнеспособности страны """
    echo = res['response'].get('text', '')
    for param in params:
        if params[param] >= quest["value_max"]:
            echo += "\n\n" + User.quest_data["endings"][f"{param} max"]
            res['response']["text"] = echo
            return False
        elif params[param] <= quest["value_min"]:
            echo += "\n\n" + User.quest_data["endings"][f"{param} min"]
            res['response']["text"] = echo
            return False
        elif params[param] >= quest["value_lot"]:
            echo += "\n\n" + User.quest_data["warnings"][f"{param} high"]
            res['response']["text"] = echo
            return True
        elif params[param] <= quest["value_few"]:
            echo += "\n\n" + User.quest_data["warnings"][f"{param} low"]
            res['response']["text"] = echo
            return True
    return True


def question(req, res, text, variants, results):
    """ Показ вопроса, вариантов ответа и вывод последствий. """
    # results - список ответов в том же порядке вопросов
    res['response']['text'] = text
    init_buttons(req, res, variants)
    answer = req['request']['original_utterance']
    for i, result in enumerate(variants):
        if answer == result:
            res['response']['text'] = results[i]


def init_buttons(req, res, buttons=None):
    user_id = req['session']['user_id']
    if not buttons:
        buttons = sessionStorage[user_id]["buttons"].copy()
    res['response']['buttons'] = [
        {
            'title': button,
            'hide': True
        } for button in buttons

    ]
    sessionStorage[user_id]["buttons"] = buttons.copy()


def make_questions_list(data):
    questions_list = []
    counts = {}
    for question in sorted(data["questions"], key=lambda key: random.random()):
        counts[question["period"]] = counts.get(question["period"], 0) + 1
        this_period = list(filter(lambda period: period["name"] == question[
            "period"], quest["periods"]))[0]
        if counts[question["period"]] <= this_period["length"]:
            questions_list.append(question)

    questions_list.sort(key=lambda el: el["date"])
    jumps_questions = {0: questions_list[0]["period"]}

    for item, question in enumerate(questions_list):
        if item and question["period"] != questions_list[item - 1]["period"]:
            jumps_questions[item] = question["period"]
    logging.error(jumps_questions)

    return questions_list, jumps_questions


def string_effects(effects, delta=False):
    government = effects["government"]
    economy = effects["economy"]
    military = effects["military"]
    control = effects["control"]
    communism = effects["communism"]
    if not delta:
        return f"п {government} э {economy} в {military} н {control} к " \
            f"{round(communism, 2)}"
    else:
        signs = [
            "+" if government >= 0 else "-",
            "+" if economy >= 0 else "-",
            "+" if military >= 0 else "-",
            "+" if control >= 0 else "-",
            "+" if communism >= 0 else "-"
        ]
        return f"\n Политическа мощь: {signs[0]}{government}\n" \
            f"Эконмическая мощь: {signs[1]}{economy}\n" \
            f"Военная мощь{signs[2]}{military}\n" \
            f"Контроль над народом: {signs[3]}{control}\n" \
            f"Коммунизм: {signs[4]}{round(communism, 2)}"


def string_effects(effects, delta=False):
    government = round(effects["government"], 2)
    economy = round(effects["economy"], 2)
    military = round(effects["military"], 2)
    control = round(effects["control"], 2)
    communism = round(effects["communism"], 2)
    if not delta:
        return f"п {government} э {economy} в {military} н {control} к " \
               f"{communism}"
    else:
        signs = [
            "+" if government >= 0 else "-",
            "+" if economy >= 0 else "-",
            "+" if military >= 0 else "-",
            "+" if control >= 0 else "-",
            "+" if communism >= 0 else "-"
        ]
        return f"\n Политическа мощь: {signs[0]}{government}\n" \
               f"Эконмическая мощь: {signs[1]}{economy}\n" \
               f"Военная мощь: {signs[2]}{military}\n" \
               f"Контроль над народом: {signs[3]}{control}\n" \
               f"Коммунизм: {signs[4]}{round(communism, 2)}"


if __name__ == '__main__':
    app.run()
