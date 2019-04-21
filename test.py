import json


def is_dict(data):
    return type(data) == dict


def cat_questions(data):
    """ Хватает ли вопросов в каждой категории / Есть ли вопросы к несуществующим категориям"""
    counts = {}
    real = {}
    for el in data["periods"]:
        if is_dict(el):
            counts[el["name"]] = el["length"]
    for el in data["questions"]:
        real[el["period"]] = real.get(el["period"], 0) + 1
    return counts == real


def is_period_jumps(data):
    """ Есть ли переходы между всеми периодами """
    pass


def is_null_question_variants(data):
    """ Есть ли вопросы без вариантов ответа """
    counts = {}
    real = {}
    for el in data["questions"]:
        if not len(el["answers"]):
            return False
    return True


def is_null_variant_causes(data):
    """  Есть ли вопросы без указания последствий """
    counts = {}
    real = {}
    for question in data["questions"]:
        for el in question["answers"]:
            if not el["cause"]:
                return False
    return True



with open("quest.json", "r", encoding="utf8") as file:
    quest = json.loads(file.read())


def make_questions_list(data):
    questions_list = []
    for question in data["questions"]:
        questions_list.append(question)

    questions_list.sort(key=lambda el: el["date"])

    return questions_list

print(make_questions_list(quest))