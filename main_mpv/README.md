# Event Finder MVP

Минимально жизнеспособная версия сервиса поиска локальных мероприятий на базе Telegram-бота.

## Стек
- FastAPI
- PostgreSQL
- SQLAlchemy
- python-telegram-bot
- Ticketmaster Discovery API

## Что уже реализовано
- хранение мероприятий, категорий, источников и пользователей в PostgreSQL;
- backend API для категорий, поиска по категории, поиска рядом и карточки мероприятия;
- импорт мероприятий из внешнего источника через Ticketmaster API;
- Telegram-бот с командами `/start`, поиском по категориям, поиском рядом и просмотром деталей события.

## Структура проекта
- `app/main.py` — FastAPI backend
- `app/models.py` — модели базы данных
- `app/db.py` — подключение к PostgreSQL
- `app/services/ticketmaster.py` — загрузка мероприятий из Ticketmaster
- `bot/bot.py` — Telegram-бот

## Как запустить

### 1. Установить зависимости
```bash
pip install -r requirements.txt
```

### 2. Создать `.env`
Скопируй `.env.example` в `.env` и заполни переменные.

### 3. Поднять PostgreSQL
Можно локально или через Docker:
```bash
docker run --name event-finder-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=event_finder \
  -p 5432:5432 -d postgres:16
```

### 4. Запустить backend
```bash
uvicorn app.main:app --reload
```

### 5. Выполнить первичную синхронизацию событий
Открой:
- `POST http://127.0.0.1:8000/sync/ticketmaster`

### 6. Запустить Telegram-бота
```bash
python bot/bot.py
```

## Основные backend endpoint'ы
- `GET /health`
- `GET /categories`
- `GET /events/category/{slug}`
- `GET /events/nearby?lat=59.437&lon=24.7536&radius_km=10`
- `GET /events/{event_id}`
- `POST /sync/ticketmaster`

## Что можно добавить дальше
- PostGIS для геопоиска на стороне базы данных;
- историю запросов пользователя;
- автоматический cron sync;
- дополнительные источники мероприятий.
