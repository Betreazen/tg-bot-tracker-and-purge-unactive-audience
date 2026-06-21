# Telegram Bot for Channel Audience Collection and Export

A Telegram bot designed to verify active real users of a Telegram channel and generate a list of live audience.

## Features

- ✅ User subscription verification
- ✅ Activity tracking with timestamp
- ✅ Admin panel with inline keyboard
- ✅ Post creation and scheduling
- ✅ Statistics dashboard
- ✅ User export to .txt file
- ✅ Support for text, photo, video, and GIF posts
- ✅ Automatic scheduled post publishing
- ✅ Anti-flood protection for user messages

## Technology Stack

- **Python 3.11+**
- **aiogram 3.x** - Telegram Bot Framework
- **PostgreSQL** - Database
- **SQLAlchemy 2.0** - Async ORM
- **Redis** - Cache and FSM storage
- **Docker & docker-compose** - Containerization

## Project Structure

```
.
├── app/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # Database models
│   │   └── connection.py       # Database connection
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── user_handlers.py    # User interaction handlers
│   │   ├── admin_handlers.py   # Admin menu handlers
│   │   └── post_handlers.py    # Post creation handlers
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── admin_middleware.py # Admin authorization
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py     # User business logic
│   │   └── scheduler_service.py # Post scheduling
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # Configuration loader
│       ├── logger.py            # Logging setup
│       ├── texts.py             # Text manager
│       └── redis_storage.py    # Redis utilities
├── bot.py                       # Main entry point
├── texts.json                   # Russian texts
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Docker services
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+
- Redis 7+
- Docker & docker-compose (optional)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tg-bot-tracker-and-purge-unactive-audience
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

### Docker Setup

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

2. **Update docker-compose.yml**
   
   Update the database connection in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://tg_bot_user:tg_bot_password@postgres:5432/tg_bot_db
   REDIS_URL=redis://redis:6379/0
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f bot
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

### Running Multiple Bots on One Server

Каждый бот запускается как **отдельный Compose-проект** с собственными
контейнерами Postgres и Redis. Изоляция обеспечивается так:

- В базовом `docker-compose.yml` **порты Postgres/Redis не публикуются** на хост,
  поэтому конфликта портов между ботами не возникает в принципе.
- Имена контейнеров, томов и сети автоматически берут префикс из
  `COMPOSE_PROJECT_NAME`.

Чтобы добавить второго бота:

```bash
# 1. Отдельная папка-копия проекта
cp -r tg-bot-tracker bot_beta && cd bot_beta

# 2. Свой .env c уникальными значениями
cp .env.example .env
#   COMPOSE_PROJECT_NAME=bot_beta      <- уникальное имя!
#   BOT_TOKEN=...                      <- токен второго бота
#   CHANNEL_ID=...                     <- его канал
#   (POSTGRES_PASSWORD задайте свой)

# 3. Запуск — не конфликтует с первым ботом
docker-compose up -d
```

Если для отладки нужен прямой доступ к БД/Redis с хоста — скопируйте
`docker-compose.override.yml.example` в `docker-compose.override.yml`
и задайте **уникальные** порты для каждого бота.

## Configuration

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `CHANNEL_ID` | Channel ID (with -100 prefix) | `-1001234567890` |
| `CHANNEL_USERNAME` | Channel username (without @) | `my_channel` |
| `ADMIN_IDS` | Comma-separated admin user IDs | `123456789,987654321` |
| `TIMEZONE` | Timezone for timestamps | `Europe/Moscow` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `LOG_PATH` | Path to log file | `logs/bot.log` |

### Getting Configuration Values

1. **BOT_TOKEN**: Create a bot via [@BotFather](https://t.me/BotFather)
2. **CHANNEL_ID**: Forward a message from your channel to [@userinfobot](https://t.me/userinfobot)
3. **ADMIN_IDS**: Send `/start` to [@userinfobot](https://t.me/userinfobot) to get your user ID

### Bot Setup

1. Make your bot an **administrator** of your channel
2. Ensure your channel is **public**
3. Give the bot permission to **post messages**

## Usage

### For Users

1. Open the bot and press `/start`
2. Bot checks if you're subscribed to the channel
3. If subscribed, your activity is recorded
4. If not subscribed, you'll receive a notification

### For Administrators

1. Send `/admin` to open the admin panel
2. Available actions:
   - **📝 Create Post**: Create and schedule posts
   - **📊 Statistics**: View user statistics
   - **📥 Export Users**: Export usernames to .txt file
   - **❌ Close**: Close admin menu

### Creating Posts

1. Click "Create Post" in admin menu
2. Send your content (text, photo, video, or GIF)
3. Review the preview
4. Choose action:
   - **Send Now**: Publish immediately
   - **Schedule**: Select date and time
   - **Cancel**: Discard the post

### Scheduling Posts

1. Select year → month → day → hour
2. All times are in GMT+3 (Europe/Moscow)
3. Bot will automatically publish at scheduled time
4. You'll receive a notification when published

### Exporting Users

1. Click "Export Users" in admin menu
2. Bot generates a .txt file with usernames
3. File format: one `@username` per line
4. Only includes users with usernames who are subscribed

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | BIGINT | Telegram user ID (primary key) |
| `username` | TEXT | Username without @ |
| `first_name` | TEXT | User's first name |
| `last_name` | TEXT | User's last name |
| `first_seen_at` | TIMESTAMP | First interaction time |
| `last_seen_at` | TIMESTAMP | Latest interaction time |

### Scheduled Posts Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGINT | Post ID (primary key) |
| `admin_id` | BIGINT | Admin who created the post |
| `content_type` | STRING | Type: text, photo, video, animation |
| `text` | TEXT | Post text or caption |
| `file_id` | TEXT | Telegram file ID |
| `scheduled_time` | TIMESTAMP | When to publish |
| `created_at` | TIMESTAMP | When post was created |
| `published` | BOOLEAN | Publication status |

## Logging

Logs are stored in the file specified by `LOG_PATH` environment variable.

**Log Format:**
```
2024-01-15 14:30:45 - app.handlers.user_handlers - INFO - User 123456789 started bot
```

**Logged Events:**
- User interactions
- Subscription checks
- Admin actions
- Post publications
- Errors with stack traces

## Important Notes

### What the Bot Does

✅ Tracks user activity  
✅ Verifies channel subscription  
✅ Exports active users  
✅ Creates and schedules posts  

### What the Bot Does NOT Do

❌ Automatically remove users  
❌ Ban users  
❌ Clean the channel  
❌ Analyze fake accounts  

### Data Management

- Users without username are **stored** but **not exported**
- Users without username are **not counted** in statistics
- Subscription is checked on **every interaction** (re-verification)
- Usernames are **updated** on each interaction
- Scheduled posts **persist** through bot restarts

## Troubleshooting

### Bot doesn't respond

1. Check bot is running: `docker-compose ps` or check logs
2. Verify `BOT_TOKEN` is correct
3. Ensure network connectivity

### Subscription check fails

1. Verify bot is admin in the channel
2. Check `CHANNEL_ID` is correct (must start with -100)
3. Ensure channel is public

### Database connection errors

1. Check PostgreSQL is running
2. Verify `DATABASE_URL` is correct
3. Ensure database exists and user has permissions

### Redis connection errors

1. Check Redis is running
2. Verify `REDIS_URL` is correct
3. Test connection: `redis-cli ping`

### Scheduled posts not publishing

1. Check bot is running continuously
2. Verify timezone settings
3. Check scheduler service logs

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests (if implemented)
pytest
```

### Code Style

The project follows:
- PEP 8 style guide
- Type hints for all functions
- Async/await for all I/O operations
- Comprehensive docstrings

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for educational and practical purposes.

## Support

For issues or questions:
1. Check this README
2. Review logs in `LOG_PATH`
3. Check database and Redis connectivity
4. Verify all environment variables are set correctly

## Maintenance

### Backup Database

```bash
# Using docker compose (имена контейнеров теперь зависят от COMPOSE_PROJECT_NAME,
# поэтому обращаемся к сервису, а не к фиксированному имени)
docker compose exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup.sql

# Restore
docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB" < backup.sql
```

### View Logs

```bash
# Docker
docker-compose logs -f bot

# Local
tail -f logs/bot.log
```

### Restart Bot

```bash
# Docker
docker-compose restart bot

# Local
# Stop with Ctrl+C and run: python bot.py
```

## Architecture

- **Handlers**: Process user and admin interactions
- **Services**: Business logic (user management, scheduling)
- **Database**: Persistent storage with async PostgreSQL
- **Redis**: FSM state storage and caching
- **Scheduler**: Background task for scheduled posts
- **Middleware**: Authorization and request processing

## Security

- Admin access controlled via `ADMIN_IDS` only
- No public API endpoints
- Database credentials in environment variables
- Bot token secured in `.env` file
- Admin actions restricted by `ADMIN_IDS` whitelist via middleware

---

**Created with ❤️ for managing Telegram channel audiences**
