# Invix Solutions

## Что это

Каталог товаров для мини-приложения Telegram. Администратор отправляет боту фото с названием в подписи, товар появляется на сайте. Корзины и оплаты нет.

Бот: [@Invix_Solutions_bot](https://t.me/Invix_Solutions_bot)

## Стек

- Next.js 15, React 19, TypeScript, SCSS
- FastAPI, SQLAlchemy 2, Alembic
- aiogram 3, aiohttp
- PostgreSQL 16, MinIO
- Docker Compose

## Запуск через Docker

```bash
cp .env.example .env
make up
```

`make up` использует `docker-compose.yml` и `docker-compose.dev.yml`: первый описывает сервисы, второй публикует порты для локального запуска.

Если этот же бот уже работает на стенде через вебхук, для локального запуска нужен отдельный `BOT_TOKEN`.

Каталог: http://localhost:13000

API: http://localhost:18000

Консоль MinIO: http://localhost:19001

Демо-товары:

```bash
make seed
```

`make seed` берёт `SERVICE_TOKEN` из `.env` и обращается к API на хосте.

Образ MinIO берётся из `ghcr.io/coollabsio/minio`. Публикация MinIO в Docker Hub сейчас недоступна, это тот же MinIO в виде зеркала.

## Как добавить товар

1. Заполните `BOT_TOKEN` в `.env`.
2. Запустите бота: `make up`.
3. Отправьте боту `/id` или `/add`. Бот покажет ваш Telegram ID.
4. Добавьте ID в `ADMIN_TELEGRAM_IDS` или username в `ADMIN_TELEGRAM_USERNAMES` и перезапустите бота: `make up`.
5. Отправьте фото товара, название укажите в подписи.
6. Кнопка «Создать товар» или текст с этой фразой покажет инструкцию.

Для мини-приложения нужен публичный HTTPS адрес. Укажите его в `WEBAPP_URL`, а для режима вебхука заполните `BOT_WEBHOOK_BASE_URL` и `BOT_WEBHOOK_SECRET`. Если адрес без HTTPS, кнопка откроет каталог в браузере.

## Переменные окружения

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `POSTGRES_DB` | `invix` | Имя базы |
| `POSTGRES_USER` | `invix` | Пользователь базы |
| `POSTGRES_PASSWORD` | `invix` | Пароль базы |
| `DATABASE_URL` | `postgresql+asyncpg://invix:invix@postgres:5432/invix` | Подключение к базе |
| `S3_ENDPOINT_URL` | `http://minio:9000` | MinIO внутри сети |
| `PUBLIC_BASE_URL` | `http://localhost:18000` | Публичный адрес API для ссылок на фото |
| `S3_ACCESS_KEY` | `minioadmin` | Ключ MinIO |
| `S3_SECRET_KEY` | `minioadmin` | Секрет MinIO |
| `S3_BUCKET` | `media` | Бакет с фото |
| `S3_REGION` | `us-east-1` | Регион S3 |
| `SERVICE_TOKEN` | `change-me` | Токен внутреннего API |
| `CORS_ORIGINS` | `https://framemuse.github.io,http://localhost:13000` | Домены для запросов из браузера |
| `BOT_TOKEN` | пусто | Токен Telegram |
| `BOT_MODE` | `polling` | `polling` или `webhook` |
| `BOT_WEBHOOK_BASE_URL` | пусто | Публичный адрес бота |
| `BOT_WEBHOOK_SECRET` | `change-me` | Секрет вебхука |
| `ADMIN_TELEGRAM_IDS` | пусто | ID админов через запятую |
| `ADMIN_TELEGRAM_USERNAMES` | пусто | Username админов через запятую |
| `WEBAPP_URL` | `http://localhost:13000` | Адрес каталога в кнопке |
| `API_URL` | `http://api:8000` | API для сайта и бота |
| `IMAGE_TAG` | `local` | Тег образов |

## Архитектура

```mermaid
flowchart LR
  TG[Telegram] -->|вебхук| Bot[бот]
  TG -->|мини-приложение| Web[сайт]
  Bot -->|внутренний API| API[api]
  Web -->|GET /api/products| API
  API --> PG[(PostgreSQL)]
  API --> S3[(MinIO)]
```

Товар: фото загружается в MinIO, запись с ключом объекта сохраняется в PostgreSQL. Ключ объекта: SHA-256 содержимого. Одинаковые файлы хранятся в MinIO один раз. API отдаёт фото из MinIO по адресу `/api/images/{key}`.

## Обновления каталога

Сайт и мини-приложение получают новые товары по SSE: `GET /api/events`.

После создания товара API отправляет событие через PostgreSQL `NOTIFY`. Все инстансы API слушают канал `catalog` и отдают событие своим клиентам. Подписчики живут только на время соединения, поэтому состояние не накапливается. При переподключении клиент заново загружает список.

Nginx для `/api/events` отключает буферизацию.

## Почему SCSS

Это моя привычка. Стилей мало, но SCSS удобен для токенов и миксинов. На поведение проекта это не влияет.

## Без стейта и несколько инстансов

Состояния в памяти нет. Сайт не хранит данные. API создаёт сессию базы на запрос. Бот не использует машину состояний и локальные файлы.

Telegram может доставить одно обновление нескольким инстансам. `DedupeMiddleware` вставляет `update_id` в `processed_updates` через `ON CONFLICT DO NOTHING`. Вставился один раз - обработал один инстанс.

Для нескольких реплик:

```bash
make scale
```

Или вручную:

```bash
docker compose up -d --scale api=2 --scale bot=2 --scale web=2
```

Базовый `docker-compose.yml` не публикует порты `api`, `bot` и `web`. Локальные порты добавляет `docker-compose.dev.yml`, порты для сервера — `docker-compose.server.yml`. Перед репликами поставьте обратный прокси или балансировщик. Вебхук указывает на общий HTTPS адрес, поэтому липкие сессии не нужны.

Для локальной проверки реплик нужен отдельный `BOT_TOKEN`: один токен не может одновременно работать через вебхук на стенде и через опрос локально.

В режиме опроса бот берёт аренду в PostgreSQL. Опрашивает один инстанс, остальные ждут. Лидер продлевает аренду. Если лидер падает, аренда истекает и опрос продолжает другой инстанс. Аренда не даёт двум ботам одновременно вызвать `getUpdates`.

## Деплой через GitHub Actions

CI проверяет сайт, API и бота. При пуше в `main` собираются три образа и публикуются в GHCR:

```text
ghcr.io/framemuse/invix-api
ghcr.io/framemuse/invix-bot
ghcr.io/framemuse/invix-web
```

Теги: `latest` и SHA коммита.

Секреты репозитория:

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_PORT`

Переменные репозитория:

- `DEPLOY_ENABLED` - `true` включает деплой
- `DEPLOY_PATH` - каталог с репозиторием на сервере

На сервере нужны Docker, Compose, git и доступ к GHCR. Пользователь для деплоя должен иметь доступ к Docker. Репозиторий клонируется один раз, `.env` лежит на сервере. `IMAGE_TAG=latest` или SHA позволяет `docker compose pull`. Если пакеты в GHCR приватные, выполните на сервере `docker login ghcr.io`.

На сервере поднимаются только `api`, `bot`, PostgreSQL и MinIO. Сайт работает с GitHub Pages. Деплой использует `docker-compose.server.yml`: он публикует `api` и `bot` на localhost для nginx.

Для мини-приложения нужен HTTPS. Поставьте обратный прокси с сертификатом перед сайтом и ботом.

Для боевого стенда задайте `BOT_MODE=webhook`, `BOT_WEBHOOK_BASE_URL` и `WEBAPP_URL` с публичными HTTPS адресами.

## GitHub Pages

Сайт на GitHub Pages - статическая сборка каталога. Товары она берёт из публичного API, адрес задаётся переменной репозитория `PAGES_API_URL`. Сборка и публикация идут в `.github/workflows/pages.yml`.

Адрес: https://framemuse.github.io/Invix-Solutions/

Для статической сборки API должен быть доступен по HTTPS и разрешать запросы с `https://framemuse.github.io` через `CORS_ORIGINS`. Этот же адрес можно указать в `WEBAPP_URL`.

## Ограничения

- Telegram открывает мини-приложение только по HTTPS.
- Без публичного HTTPS ссылка в боте не откроется. Сам каталог в браузере продолжит работать.
- `PUBLIC_BASE_URL` должен быть доступен из браузера, иначе фото не загрузятся.
- Корзины, оплаты и авторизации нет по условию задачи.
