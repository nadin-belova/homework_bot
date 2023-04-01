from logging import StreamHandler
from dotenv import load_dotenv
from json.decoder import JSONDecodeError

import logging
import os
import requests
import sys
import telegram
import time


load_dotenv()


class APIUnavailableException(Exception):
    """Ошибка, возникающая в случае недоступности API."""

    pass


class HomeworkDataError(Exception):
    """Ошибка, возникающая в случае некорректных данных о домашнем задании."""

    pass


class HomeworkStatusError(Exception):
    """Ошибка, возникающая в случае некорректного статуса домашнего задания."""

    pass


class TokensValidationError(Exception):
    """Ошибка, возникающая в случае некорректной валидации токенов."""

    pass


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TOKENS = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
          'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
          'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID}

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
HEADERS = {'Authorization': f"OAuth {PRACTICUM_TOKEN}"}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

handler = StreamHandler(stream=sys.stdout)
logging.getLogger('').addHandler(handler)


def check_tokens():
    """Проверяет доступность переменных окружения.
    Они необходимы для работы программы.
    Если отсутствует хотя бы одна переменная окружения —
    продолжать работу бота нет смысла.
    """
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        raise ValueError('Неверно заданы переменные окружения')


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат.
    Чат определяется переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса
    Bot и строку с текстом сообщения.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('удачная отправка сообщения в Telegram')
    except Exception as error:
        logging.error(f'Cбой при отправке сообщения в Telegram {error}')


def get_api_answer(current_timestamp=None):
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        logging.info('Запрос к API отправлен')
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        response.raise_for_status()  # raises HTTPError for non-200 responses
        return response.json()
    except JSONDecodeError as e:
        logging.error('Получен не формат json')
        raise e
    except requests.exceptions.RequestException as e:
        logging.error(f'API недоступен. {e}')
        raise APIUnavailableException('API недоступен') from e


def check_response(response):
    """проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    if not isinstance(response, dict):
        logging.error('Полученная информация не является словарем')
        raise TypeError('Полученная информация не является словарем')

    if 'homeworks' not in response:
        logging.error('Новый статус не получен')
        raise KeyError('Новый статус не получен')
    homeworks = response.get('homeworks')
    try:
        homework = homeworks[0]
        return homework
    except IndexError:
        logging.error('Получен пустой список')


def parse_status(homework):
    """Извлекает статус домашней работы.
    В качестве параметра функция
    получает только один элемент из списка домашних работ.
    В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку, содержащую один из
    вердиктов словаря HOMEWORK_VERDICTS.
    """
    if 'homework_name' not in homework:
        logging.error('Нет информации о домашнем задании')
        raise KeyError('Нет информации о домашнем задании')
    if not isinstance(homework, dict):
        logging.error('Полученная информация не является словарем')
        raise TypeError('Полученная информация не является словарем')
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        if homework_status is None or homework_status not in HOMEWORK_STATUSES:
            logging.error('Неизвестный статус')
            raise HomeworkStatusError('Неизвестный статус')
    except Exception as error:
        HomeworkDataError(
            f'Полученные данные не могут'
            f'быть проанализированы{error}')
        logging.error(
            f'Полученные данные не могут'
            f'быть проанализированы {error}')
    else:
        verdict = HOMEWORK_STATUSES.get(homework_status)
        logging.info('удачная отправка сообщения в Telegram')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.error('Токены не могут быть проверены')
        raise TokensValidationError('Токены не могут быть проверены')
    logging.info('Проверка токенов прошла успешно')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    response1 = get_api_answer(current_timestamp)
    while True:
        try:
            response2 = get_api_answer(current_timestamp)
            if response2 != response1:
                homework = check_response(response2)
                message = parse_status(homework)
                response1 = response2
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            break
        else:
            send_message(bot, message)
            logging.info('Сообщение успешно отправлено')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
