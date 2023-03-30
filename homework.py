from dotenv import load_dotenv
import telegram
import os
import time
import requests
from pprint import pprint



load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
PAYLOAD = {'from_date': 7}
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """
    Проверяет доступность переменных окружения,
    которые необходимы для работы программы. 
    Если отсутствует хотя бы одна переменная окружения — 
    продолжать работу бота нет смысла.
    """


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram чат,
    определяемый переменной окружения TELEGRAM_CHAT_ID. 
    Принимает на вход два параметра: экземпляр класса Bot и строку с текстом сообщения.
    """


def get_api_answer(timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса. 
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=PAYLOAD)
    # pprint(homework_statuses.json())

    return dict(homework_statuses.json())



def check_response(response):
    """
    проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    homeworks = response.get('homeworks')
    homework_1 = homeworks[0] 
    status = homework_1.get('status')
    current_date = response.get('current_date')
    

    statuses = {
        'reviewing': 'работа взята в ревью',
        'approved': 'ревью успешно пройдено',
        'rejected': 'в работе есть ошибки, нужно поправить'
    }

    if status in statuses:
        print('работа в стадии:',status)
    else:
        print('error')

    # print(status)

    # # pprint(response.get('homeworks')[0].get('status'))




def parse_status(homework):
    """
    извлекает из информации о конкретной домашней 
    работе статус этой работы. В качестве параметра функция 
    получает только один элемент из списка домашних работ. 
    В случае успеха, функция возвращает подготовленную 
    для отправки в Telegram строку, содержащую один из 
    вердиктов словаря HOMEWORK_VERDICTS.
    """
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    # 1 Сделать запрос к API.
    response = get_api_answer(timestamp)

    # 2 Проверить ответ.
    check_response(response)

    # 3 Если есть обновления — получить статус работы из обновления и отправить сообщение в Telegram.
    # 4 Подождать некоторое время и вернуться в пункт 1.
    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
