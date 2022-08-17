# Телеграм бот для уведомления пациентов и связи с врачом
## Возможности
### Для пользователей
* Пользователи могут отправлять администраторам(врачам) вопросы и заявления на справки (при этом аккаунт врача остается скрытым для пользователя).
* Пользователи будут получать уведомления, созданные врачами.
### Для врачей
* Врачи могут создавать объявления для пользователей на определенное время.
* Врачи могут анонимно отвечать на вопросы и заявки пользователей.
### Технические
* Подключение к базе данных SQLite3 / PostgreSQL.
* Админ панель.
* Возможность развертывания через Docker.
## Установка и запуск
### Получение токена
Для получения токена воспользуйтесь официальным ботом Telegram по [ссылке](https://t.me/BotFather)
### Запуск без развертывания
#### Для запуска вам потребуется

1) Установить Python интерпретатор.
2) Установить зависимости проекта <code>pip install -r requirements.txt</code>

Для первого запуска из консоли используйте команду: 
<br>
<code>python main.py [токен] [СУБД] [адрес]</code> <br>
Последующий запуск можно осуществлять без аргументов(бот их запомнит): 
<code>python main.py</code>
<br>
#### Пример:
<code>python main.py postgresql "login:password@postgres:5432/database"</code>
<br>
Без указания адреса/СУБД при первом запуске будет использоваться SQLite3 с адресом ./database.db

### Развертывание с помощью Docker
#### Для развертывания бота с помощью Docker вам потребуется:
1) Установить Docker.
2) Собрать образ контейнера <code>docker build -t telebot .</code>

Для первого запуска контейнера используйте 
<code>docker run telebot [токен] [СУБД] [адрес]</code> <br>
Последующий запуск можно осуществлять без аргументов(бот их запомнит): 
<code>python main.py</code> <br>
Без указания адреса/СУБД при первом запуске будет использоваться SQLite3 с адресом ./database.db

## Дополнительные возможности
### Доступ к базе данных
Для доступа к базе данных используйте команду <code>python debug.py</code> (только после первого запуска)
* Для добавление нового администратора введите команду <code>admins.add(id)</code>
* Для того, чтобы узнать id пользователя используйте команду <code>users.get_by_username('@ник_пользователя').user_id</code>

Изменения текста
* Изменить тексты бота можно внутри файла texts.json (генерируется после первого запуска)
* Для применения изменений перезапустите бота

Для изменения настроек уведомлений отправьте боту сообщение "Настройки"