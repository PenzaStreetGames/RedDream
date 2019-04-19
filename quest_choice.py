from json import loads
from random import randrange

with open('quest.json', 'r', encoding='utf-8') as file:
    quest = loads(file.read())


# возвращает заданное количество вопросов
# (не текста вопросов, а всю структуру вопроса из json файла)
def make_questions_list(questions_count):
    questions_list = []

    while questions_count:
        for period in quest['periods']:
            if questions_count:

                period_questions = []
                for question in quest["questions"]:

                    if question['period'] == period['name'] and questions_count:
                        period_questions.append(question)

                for i in range(period['length']):
                    if questions_count:
                        try:
                            questions_list.append(period_questions.pop(randrange(len(period_questions))))
                        except ValueError:
                            # если все пошло по этому пути, значит вопросов из этой эпохи
                            # нет в json файле
                            questions_list.append('Вопрос для этой эпохи ({}) не найден'.format(period['name']))
                        questions_count -= 1

    return questions_list


li = make_questions_list(13)
print(li)
print(len(li))
