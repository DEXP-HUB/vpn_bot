# VPN Bot

Telegram-бот для автоматической выдачи VPN-конфигураций WireGuard. Бот помогает администратору управлять пользователями, создавать для них персональные конфиги, отправлять готовый `.conf` файл и QR-код прямо в Telegram.

## Что делает бот

Бот подключается к удалённому WireGuard-серверу по SSH, генерирует ключи для клиента, назначает свободный VPN-адрес, добавляет нового пира в работающий интерфейс `wg0` и сохраняет данные конфигурации в базе данных.

Пользователь получает готовый конфигурационный файл WireGuard и QR-код, который можно импортировать в приложение WireGuard на Windows, macOS, Android или iOS.

## Основные возможности

- Генерация персонального WireGuard-конфига для пользователя.
- Отправка `.conf` файла и QR-кода в Telegram.
- Добавление нового пира на сервер WireGuard без перезапуска интерфейса.
- Хранение пользователей, интерфейса WireGuard и выданных конфигураций в базе данных.
- Просмотр списка пользователей и созданных VPN-конфигураций.
- Удаление пользователей и VPN-конфигураций.
- Ограничение доступа к административным командам через middleware.
- Логирование входящих сообщений и ошибок.

## Команды бота

- `/start` — показать приветственное сообщение и инструкцию по получению VPN-конфига.
- `/generate_config` — создать новую WireGuard-конфигурацию и получить файл с QR-кодом.
- `/configs_list` — показать список всех созданных конфигураций.
- `/delete_config` — удалить конфигурацию по названию.
- `/add_user_by_id` — добавить пользователя по Telegram ID.
- `/delete_user_id` — удалить пользователя по Telegram ID.
- `/delete_user_name` — удалить пользователя по имени.
- `/users` — показать список пользователей.

## Технологии

Проект написан на Python и использует:

- Aiogram 3 для Telegram-бота.
- Paramiko для SSH-подключения к удалённому серверу.
- SQLAlchemy и SQLite для хранения данных.
- Poetry для управления зависимостями.
- qrcode для генерации QR-кодов WireGuard.


## .env
- TELEGRAM_BOT_TOKEN=bot_token
- SSH_HOST=test
- VPN_PORT=test
- SSH_PORT=test
- SSH_USERNAME=test
- SSH_PASSWORD=test
- ADMIN_ID=user_telegram_id
- ADMIN_NAME=test
- VPN_INTERFACE_NAME=wg0
- VPN_ADDRESS=10.0.0.1/24
- VPN_PRIVATE_KEY=test
- VPN_ALLOWED_IPS=0.0.0.0/0
- VPN_POST_UP=iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
- VPN_POST_DOWN=iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
- TEST=0


Как поднять:
1) git clone https://github.com/DEXP-HUB/vpn_bot.git
2) cd vpn_bot 
3) poetry install
4) poetry env activate
5) nano .env <- заполнить данными из раздела .env
6) poetry run python -m src.main
