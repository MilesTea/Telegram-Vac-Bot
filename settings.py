import json
import os

default_settings = {
    'notifications': {
        'state': False,
        'hour_from': '12',
        'hour_to': '18',
    }
}

texts = {
    '/start': 'Приветствие',
    'cancel': 'Отмена',
    'unknown_command': 'Команда не распознана',
    'main_menu': 'Возврат в главное меню',
    'events': {  # Готово
        'all': 'Все события',
        'new': 'Новое событие',
        'empty': 'Нет активных событий',
        'new_datetime': 'Введите дату и время в формате дд.мм.гг чч:мм',
        'new_datetime_error': 'Введите корректную дату согласно образцу',
        'new_text': 'Введите текст события. Также вы можете прикрепить картинку',
        'new_complete': 'Событие запланировано на {datetime}',
        'delete_button': 'Удалить',
    },
    'questions': {
        'all': 'Вопросы',
        'empty': 'Нет активных вопросов',
        'answer_button': 'Ответить',
        'delete_button': 'Удалить',
        'not_found': 'На этот вопрос уже дали ответ',
        'answer': 'Введите ваш ответ на вопрос от {username}',
        'answer_complete': 'Ваш ответ отправлен пользователю',
        'answer_error': 'Ошибка при отправке ответа пользователю',
        'answer_first_line': 'Ответ врача на ваш вопрос:\n',
        'admin_notification': 'Новый вопрос от пользователя {username}',

        'ask_button': 'Задать вопрос врачу профилактики',
        'ask': 'Введите свой вопрос в одном сообщении.',
        'ask_complete': 'Ваш вопрос был отправлен.',
        'ask_limit': 'Ваш вопрос уже находится в обработке',
        'ask_text_only': 'Вы можете отправить только текст',
        'ask_too_long': 'Слишком длинное сообщение',
    },
    'certificates': {
        'all': 'Заявки на справки',
        'empty': 'Нет активных заявок',
        'answer_button': 'Ответить',
        'delete_button': 'Удалить',
        'not_found': 'На эту заявку уже дали ответ',
        'answer': 'Введите ваш ответ на заявку от {username}',
        'answer_complete': 'Ваш ответ отправлен пользователю',
        'answer_error': 'Ошибка при отправке ответа пользователю',
        'answer_first_line': 'Врач прислал ответ на вашу заявку:\n',
        'admin_notification': 'Новая заявка на справку от пользователя {username}',

        'ask_button': 'Заказать справку',
        'ask': 'Введите ФИО, класс ребёнка, и название необходимой справки.',
        'ask_complete': 'Ваше заявление на справку было отправлено.',
        'ask_limit': 'Вы можете запросить только 2 справки за раз',
        'ask_text_only': 'Вы можете отправить только текст',
        'ask_too_long': 'Слишком длинное сообщение',
    },
}


class Settings:
    def __init__(self):
        if 'settings.json' in os.listdir(os.getcwd()):
            with open('settings.json', 'r', encoding='utf-8') as file:
                self.settings = json.load(file)
        else:
            with open('settings.json', 'w', encoding='utf-8') as file:
                json.dump(default_settings, file, sort_keys=True, indent=2)
                self.settings = default_settings

    def __str__(self):
        text = f'Уведомления: {"Включены" if self.notifications_state else "Выключены"}\nВремя отправки уведомлений: ' \
               f'с {self.settings["notifications"]["hour_from"]} до {self.settings["notifications"]["hour_to"]}'
        return text

    def update(self):
        with open('settings.json', 'w', encoding='utf-8') as file:
            json.dump(self.settings, file, sort_keys=True, indent=2)

    @property
    def notifications_state(self):
        return self.settings['notifications']['state']

    @notifications_state.setter
    def notifications_state(self, state: bool):
        if type(state) is bool:
            self.settings['notifications']['state'] = state
        self.update()

    @property
    def notifications_hours(self):
        return [self.settings['notifications']['hour_from'], self.settings['notifications']['hour_to']]

    @notifications_hours.setter
    def notifications_hours(self, hours: list or tuple):
        if len(hours) != 2:
            raise 'list or tuple with length of 2 required'
        hour_from, hour_to = hours[0], hours[1]
        if type(hour_from) is int or type(hour_to) is str:
            self.settings['notifications']['hour_from'] = str(hour_from)
        if type(hour_to) is int or type(hour_to) is str:
            self.settings['notifications']['hour_to'] = str(hour_to)
        self.update()


def get_texts():
    if 'texts.json' in os.listdir(os.getcwd()):
        with open('texts.json', 'r', encoding='utf-8') as file:
            _texts = json.load(file)
    else:
        with open('texts.json', 'w', encoding='utf-8') as file:
            json.dump(texts, file, sort_keys=True, indent=2)
            _texts = texts
    return _texts
