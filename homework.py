import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def check_tokens():
    """Проверяет доступность переменных окружения.
    Они необходимы для работы программы.
    Если отсутствует хотя бы одна переменная окружения —
    продолжать работу бота нет смысла.
    """
    tokens = all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])
    return tokens


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат.
    Чат определяется переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса
    Bot и строку с текстом сообщения.
    """
    logger.info(f"Начало отправки сообщения: {message}")
    try:
        bot_message = bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        if not bot_message:
            logger.debug(f"Сообщение отправлено: {message}")
    except telegram.TelegramError as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        # обработка ошибки, например, повторная отправка сообщения
        # или просто игнорирование


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={"from_date": timestamp}
    )
    try:
        homework_statuses = requests.get(**params)
    except Exception as error:
        logger.error(f"Ошибка при запросе к API: {error}")
    else:
        if homework_statuses.status_code != HTTPStatus.OK:
            error_message = "Статус страницы не равен 200"
            raise requests.HTTPError(error_message)
        return homework_statuses.json()


def check_response(response):
    """проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    logger.info("Ответ от сервера получен")
    if not isinstance(response, dict):
        raise TypeError("Неверный тип входящих данных: ожидается словарь")
    if 'homeworks' not in response:
        raise KeyError('Ключ "homeworks" отсутствует в словаре')
    if 'current_date' not in response:
        raise KeyError('Ключ "current_date" отсутствует в словаре')
    homeworks_response = response['homeworks']
    if not isinstance(homeworks_response, list):
        raise TypeError("Неверный тип значения по ключу 'homeworks': "
                        "ожидается список")
    logger.info("Список домашних работ получен")
    return homeworks_response


def parse_status(homework):
    """Извлекает статус домашней работы.
    В качестве параметра функция
    получает только один элемент из списка домашних работ.
    В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку, содержащую один из
    вердиктов словаря HOMEWORK_VERDICTS.
    """
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    if "homework_name" not in homework:
        message_homework_name = "Такого имени не существует"
        raise KeyError(message_homework_name)
    if homework_status not in HOMEWORK_VERDICTS:
        message_homework_status = "Такого статуса не существует"
        raise KeyError(message_homework_status)
    verdict = HOMEWORK_VERDICTS[homework_status]
    if not verdict:
        message_verdict = "Такого статуса нет в словаре"
        raise ValueError(message_verdict)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        logger.critical('Ошибка в получении токенов!')
        sys.exit()
    current_report = {}
    prev_report = {}
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            if homework:
                message = parse_status(homework)
                homework_name = response.get("homework_name")
                status = response.get("status")
                current_report[homework_name] = status
                if current_report != prev_report:
                    send_message(bot, message)
                    prev_report = current_report.copy()
                    homework_name = response.get("homework_name")
                    status = response.get("status")
                    current_report[homework_name] = status
            current_timestamp = response.get("current_date")

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
        else:
            logger.error("Сбой, ошибка не найдена")
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    logging.basicConfig(
        format=('%(asctime)s'
                '%(name)s'
                '%(levelname)s'
                '%(message)s'
                '%(funcName)s'
                '%(lineno)d'),
        level=logging.INFO,
        filename="program.log",
        filemode="w",
    )
    main()
