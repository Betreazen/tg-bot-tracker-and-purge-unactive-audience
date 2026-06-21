# 🚀 Быстрый запуск

Бот запускается в Docker одной командой. Все настройки — в одном файле `.env`.

## Требования
- Установленные **Docker** и **Docker Compose** ([инструкция по установке](https://docs.docker.com/engine/install/)).
- Токен бота от [@BotFather](https://t.me/BotFather).
- Бот добавлен **администратором** в ваш канал.

## Запуск за 3 шага

```bash
# 1. Создать файл настроек из шаблона
cp .env.example .env

# 2. Заполнить .env (см. ниже какие поля обязательны)
nano .env

# 3. Запустить
docker compose up -d --build
```

Готово. Проверить, что бот поднялся:

```bash
docker compose logs -f bot
# Ждём строку: "Bot started successfully"
```

## Что заполнить в `.env`

Обязательны только 4 поля (всё остальное имеет рабочие значения по умолчанию):

| Поле | Где взять |
|------|-----------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `CHANNEL_ID` | переслать пост канала в [@userinfobot](https://t.me/userinfobot) (начинается с `-100`) |
| `CHANNEL_USERNAME` | username канала без `@` |
| `ADMIN_IDS` | `/start` у [@userinfobot](https://t.me/userinfobot); несколько — через запятую |

Рекомендуется также сменить `POSTGRES_PASSWORD` на свой.
Строки подключения к БД и Redis собираются автоматически — задавать их не нужно.

## Несколько ботов на одном сервере

Каждый бот — отдельная папка со своим `.env`. Конфликтов портов нет
(порты БД/Redis на хост не публикуются). Для каждого бота важно задать **уникальное**
`COMPOSE_PROJECT_NAME`:

```bash
cp -r tg-bot-tracker bot_beta && cd bot_beta
cp .env.example .env
# в .env: COMPOSE_PROJECT_NAME=bot_beta, свой BOT_TOKEN, CHANNEL_ID, ADMIN_IDS
docker compose up -d --build
```

## Частые команды

```bash
docker compose logs -f bot          # логи бота
docker compose ps                   # статус контейнеров
docker compose restart bot          # перезапустить бота
docker compose down                 # остановить всё
docker compose up -d --build        # пересобрать и запустить (после git pull)
```

## Обновление кода

```bash
git pull
docker compose up -d --build
```

## Если что-то не так

```bash
docker compose ps                   # все ли контейнеры "Up"/"healthy"?
docker compose logs bot | grep -Ei "error|critical"
```

- **`Bot token is invalid`** → проверьте `BOT_TOKEN` в `.env`, затем `docker compose up -d`.
- **Бот не видит подписку** → бот должен быть админом канала, `CHANNEL_ID` начинается с `-100`.
- **Посты не публикуются** → у бота должно быть право публикации в канале.

## Бэкап базы данных

```bash
# имена контейнеров зависят от COMPOSE_PROJECT_NAME, поэтому работаем через сервис
docker compose exec -T postgres pg_dump -U tg_bot_user tg_bot_db > backup.sql

# восстановление
docker compose exec -T postgres psql -U tg_bot_user tg_bot_db < backup.sql
```

---

Подробнее о возможностях и архитектуре — в [README.md](README.md).
