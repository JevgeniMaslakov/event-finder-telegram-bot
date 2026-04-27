import re
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Category, Event, User, SearchHistory
from .services.ticketmaster import sync_ticketmaster_events
from .services.predicthq import sync_predicthq_events
from .utils import haversine_km

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Finder MVP")

DEFAULT_CATEGORIES = [
    {"name": "Концерты", "slug": "concerts"},
    {"name": "Спортивные мероприятия", "slug": "sports"},
    {"name": "Лекции и выставки", "slug": "lectures-exhibitions"},
    {"name": "Кино", "slug": "film"},
    {"name": "Другое", "slug": "other"},
]


class UserUpsertPayload(BaseModel):
    telegram_id: str
    username: str | None = None
    language: str = "ru"


class SearchLogPayload(BaseModel):
    telegram_id: str
    username: str | None = None
    language: str = "ru"
    action: str
    value: str | None = None


def serialize_event_short(event: Event) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "event_date": event.event_date.isoformat() if event.event_date else None,
        "venue_name": event.venue_name,
        "address": event.address,
        "city": event.city,
        "url": event.url,
        "source": event.source.name if event.source else None,
    }


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w\sа-яёõäöü-]", "", value, flags=re.IGNORECASE)
    return value


def normalize_event_dt(value: str | None) -> str:
    if not value:
        return ""
    return value[:16]


def dedupe_event_dicts(items: list[dict]) -> list[dict]:
    seen = set()
    result = []

    for item in items:
        title = normalize_text(item.get("title"))
        date = normalize_event_dt(item.get("event_date"))
        venue = normalize_text(item.get("venue_name"))
        key = f"{title}|{date}|{venue}"

        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


def _period_range(period: str):
    now = datetime.now()
    start = now

    if period == "today":
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    if period == "week":
        end = now + timedelta(days=7)
        return start, end

    if period == "weekend":
        days_until_saturday = (5 - now.weekday()) % 7
        saturday = (now + timedelta(days=days_until_saturday)).replace(hour=0, minute=0, second=0, microsecond=0)
        sunday_end = (saturday + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

        if now.weekday() == 5:
            return now, sunday_end
        if now.weekday() == 6:
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return now, end
        return saturday, sunday_end

    raise HTTPException(status_code=400, detail="Unsupported period")


async def ensure_seed_data(db: Session):
    has_events = db.query(Event).filter(Event.event_date >= datetime.now()).first()
    if has_events:
        return

    tm_result = await sync_ticketmaster_events(db)
    phq_result = await sync_predicthq_events(db)

    print("Seed sync results:")
    print("Ticketmaster:", tm_result)
    print("PredictHQ:", phq_result)


def upsert_user(db: Session, telegram_id: str, username: str | None = None, language: str = "ru") -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if user:
        if username is not None:
            user.username = username
        user.language = language or user.language
    else:
        user = User(
            telegram_id=telegram_id,
            username=username,
            language=language or "ru",
            created_at=datetime.utcnow(),
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user


def save_search_log(
    db: Session,
    telegram_id: str,
    username: str | None,
    language: str,
    action: str,
    value: str | None = None,
):
    user = upsert_user(
        db=db,
        telegram_id=telegram_id,
        username=username,
        language=language,
    )

    entry = SearchHistory(
        user_id=user.id,
        action=action,
        value=value,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "event-finder-backend",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "event-finder-backend"}


@app.post("/users/upsert")
def create_or_update_user(payload: UserUpsertPayload, db: Session = Depends(get_db)):
    user = upsert_user(
        db=db,
        telegram_id=payload.telegram_id,
        username=payload.username,
        language=payload.language,
    )
    return {
        "status": "ok",
        "user": {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "language": user.language,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


@app.get("/users/{telegram_id}")
def get_user(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "language": user.language,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@app.post("/history/search")
def log_search(payload: SearchLogPayload, db: Session = Depends(get_db)):
    entry = save_search_log(
        db=db,
        telegram_id=payload.telegram_id,
        username=payload.username,
        language=payload.language,
        action=payload.action,
        value=payload.value,
    )
    return {
        "status": "ok",
        "log_id": entry.id,
        "action": entry.action,
        "value": entry.value,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@app.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    await ensure_seed_data(db)

    categories = db.query(Category).order_by(Category.name.asc()).all()
    db_categories = [{"id": c.id, "name": c.name, "slug": c.slug} for c in categories]

    existing_slugs = {c["slug"] for c in db_categories}
    result = db_categories[:]

    for item in DEFAULT_CATEGORIES:
        if item["slug"] not in existing_slugs:
            result.append(item)

    order = {item["slug"]: i for i, item in enumerate(DEFAULT_CATEGORIES)}
    result.sort(key=lambda x: order.get(x["slug"], 999))
    return result


@app.get("/events/category/{slug}")
async def get_events_by_category(
    slug: str,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    await ensure_seed_data(db)

    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        fallback = next((c for c in DEFAULT_CATEGORIES if c["slug"] == slug), None)
        if not fallback:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"category": {"name": fallback["name"], "slug": fallback["slug"]}, "events": []}

    events = (
        db.query(Event)
        .filter(Event.category_id == category.id)
        .filter(Event.event_date >= datetime.now())
        .order_by(Event.event_date.asc())
        .limit(limit * 4)
        .all()
    )

    payload = [serialize_event_short(e) for e in events]
    payload = dedupe_event_dicts(payload)[:limit]

    return {"category": {"name": category.name, "slug": category.slug}, "events": payload}


@app.get("/events/nearby")
async def get_nearby_events(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(10.0, gt=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    await ensure_seed_data(db)

    events_with_coords = (
        db.query(Event)
        .filter(Event.latitude.isnot(None), Event.longitude.isnot(None))
        .filter(Event.event_date >= datetime.now())
        .all()
    )

    result = []
    for e in events_with_coords:
        distance = haversine_km(lat, lon, e.latitude, e.longitude)
        if distance <= radius_km:
            row = serialize_event_short(e)
            row["distance_km"] = round(distance, 2)
            result.append(row)

    result.sort(key=lambda x: (x["distance_km"], x.get("event_date") or "9999-99-99"))
    result = dedupe_event_dicts(result)

    filtered = []
    venue_counter = {}
    for item in result:
        venue = normalize_text(item.get("venue_name") or "unknown")
        venue_counter[venue] = venue_counter.get(venue, 0) + 1
        if venue_counter[venue] <= 2:
            filtered.append(item)
        if len(filtered) >= limit:
            break

    if filtered:
        return {"events": filtered}

    fallback_events = (
        db.query(Event)
        .filter(Event.event_date >= datetime.now())
        .order_by(Event.event_date.asc())
        .limit(limit * 4)
        .all()
    )

    fallback = []
    for e in fallback_events:
        row = serialize_event_short(e)
        row["distance_km"] = None
        fallback.append(row)

    fallback = dedupe_event_dicts(fallback)[:limit]
    return {"events": fallback}


@app.get("/events/period/{period}")
async def get_events_by_period(
    period: str,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    await ensure_seed_data(db)
    start_dt, end_dt = _period_range(period)

    events = (
        db.query(Event)
        .filter(Event.event_date >= start_dt)
        .filter(Event.event_date <= end_dt)
        .order_by(Event.event_date.asc())
        .limit(limit * 4)
        .all()
    )

    payload = [serialize_event_short(e) for e in events]
    payload = dedupe_event_dicts(payload)[:limit]
    return {"period": period, "events": payload}


@app.get("/events/{event_id}")
def get_event_details(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_date": event.event_date.isoformat() if event.event_date else None,
        "venue_name": event.venue_name,
        "address": event.address,
        "city": event.city,
        "country": event.country,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "url": event.url,
        "category": event.category.name if event.category else None,
        "source": event.source.name if event.source else None,
    }


@app.post("/sync/ticketmaster")
async def sync_ticketmaster(db: Session = Depends(get_db)):
    result = await sync_ticketmaster_events(db)
    return {"status": "ok", **result}


@app.post("/sync/predicthq")
async def sync_predicthq(db: Session = Depends(get_db)):
    result = await sync_predicthq_events(db)
    return {"status": "ok", **result}


@app.post("/sync/all")
async def sync_all(db: Session = Depends(get_db)):
    tm_result = await sync_ticketmaster_events(db)
    phq_result = await sync_predicthq_events(db)
    return {"status": "ok", "ticketmaster": tm_result, "predicthq": phq_result}