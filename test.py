import json


class TestError(Exception):
    pass


def questions_number(data):
    """ Хватает ли вопросов в каждой категории"""
    questions = data["questions"]
    categories = data["periods"]
    for category in categories:
        category_questions = list(
            filter(lambda question: question["period"] == category["name"],
                   data["questions"]))
        if len(category_questions) < category["length"]:
            raise TestError(f"В категории  {category['name']} нехватает "
                            f"вопросов: {len(category_questions)} вместо "
                            f"{category['length']}")
    return "Все категории имеют достаточно вопросов"


def questions_category(data):
    """Есть ли вопросы к несуществующим категориям"""
    categories = list(map(lambda category: category["name"],
                          data["periods"]))
    for question in data["questions"]:
        period = question["period"]
        if period not in categories:
            raise TestError(f"Вопрос {question['text'][:30]}... относится к"
                            f"несуществующей категории {period}")
    return "Все вопросы относятся к существующим категориям"


def is_period_jumps(data):
    """ Есть ли переходы между всеми периодами """
    categories = list(map(lambda category: category["name"],
                          data["periods"]))
    category_jumps = categories
    jumps = list(data["jumps"].keys())
    if category_jumps != jumps:
        raise TestError(f"Переходы различаются \n Нужны:   {category_jumps} \n "
                        f"Имеются: {jumps}")
    return "Имеются все необходимые переходы"


def is_null_question_variants(data):
    """ Есть ли вопросы без вариантов ответа """
    for question in data["questions"]:
        if len(question["answers"]) == 0:
            raise TestError(f"У вопроса {question['text'][:30]}... нет "
                            f"вариантов ответа")
    return "Все вопросы имеют варианты ответа"


def is_none_variant_causes(data):
    """  Есть ли вопросы без указания последствий """
    effects = ["government", "economy", "military", "control",
               "communism"]
    for question in data['questions']:
        for answer in question["answers"]:
            if answer.get("effects", None) is None:
                raise TestError(
                    f"Ответ {answer['text'][:30]} вопроса "
                    f"{question['text'][:30]}"
                    f"Не имеет последствий")
            for effect in effects:
                if answer["effects"].get(effect) is None:
                    raise TestError(
                        f"Ответ {answer['text'][:30]} вопроса "
                        f"{question['text']}"
                        f"Не имеет поля {effect}")

    return "Все ответы имеют последствия"


def is_null_variant_causes(data):
    """ Есть ли вопросы с нудевыми последствиями """
    for question in data['questions']:
        for answer in question["answers"]:
            effects = answer["effects"].values()
            if all(list(map(lambda effect: effect == 0, effects))):
                raise TestError(
                    f"Ответ {answer['text'][:30]} вопроса "
                    f"{question['text'][:30]}... "
                    f"имеет нулевые последствия")
    return "Все ответы имеют ненулевые последствия"


if __name__ == '__main__':
    with open("quest.json", "r", encoding="utf8") as file:
        quest = json.loads(file.read())
    try:
        print(questions_number(quest))
        print(questions_category(quest))
        print(is_period_jumps(quest))
        print(is_null_question_variants(quest))
        print(is_none_variant_causes(quest))
        print(is_null_variant_causes(quest))
        print("Все тесты пройдены успешно")
    except TestError as error:
        print(error)
