from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from ..config import PREDICTHQ_API_TOKEN, SYNC_COUNTRY_CODE
from ..models import Category, Event, Source

PREDICTHQ_URL = "https://api.predicthq.com/v1/events/"

CATEGORY_MAP = {
    "concerts": ("Концерты", "concerts"),
    "sports": ("Спортивные мероприятия", "sports"),
    "performing-arts": ("Лекции и выставки", "lectures-exhibitions"),
    "conferences": ("Лекции и выставки", "lectures-exhibitions"),
    "expos": ("Лекции и выставки", "lectures-exhibitions"),
    "festivals": ("Другое", "other"),
    "community": ("Другое", "other"),
}


def _get_or_create_source(db: Session) -> Source:
    source = db.query(Source).filter(Source.name == "PredictHQ").first()
    if source:
        return source

    source = Source(
        name="PredictHQ",
        type="api",
        base_url="https://api.predicthq.com/",
        last_sync_at=None,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def _get_or_create_category(db: Session, name: str, slug: str) -> Category:
    category = db.query(Category).filter(Category.slug == slug).first()
    if category:
        return category

    category = Category(name=name, slug=slug)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def _normalize_category(category_value: str | None) -> tuple[str, str]:
    if not category_value:
        return ("Другое", "other")
    return CATEGORY_MAP.get(category_value.strip().lower(), ("Другое", "other"))


async def sync_predicthq_events(db: Session) -> dict:
    if not PREDICTHQ_API_TOKEN:
        return {
            "ok": False,
            "source": "PredictHQ",
            "error": "PREDICTHQ_API_TOKEN is not set",
            "created": 0,
            "updated": 0,
            "total_received": 0,
        }

    headers = {
        "Authorization": f"Bearer {PREDICTHQ_API_TOKEN}",
        "Accept": "application/json",
    }

    # Tallinn center with radius
    params = {
        "country": SYNC_COUNTRY_CODE,
        "active.gte": datetime.now(timezone.utc).date().isoformat(),
        "within": "25km@59.4370,24.7536",
        "category": "concerts,sports,performing-arts,conferences,expos,festivals,community",
        "limit": 100,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(PREDICTHQ_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return {
            "ok": False,
            "source": "PredictHQ",
            "error": str(e),
            "created": 0,
            "updated": 0,
            "total_received": 0,
        }

    results = data.get("results", []) or []
    source = _get_or_create_source(db)

    created = 0
    updated = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for item in results:
        external_id = item.get("id")
        if not external_id:
            continue

        title = item.get("title") or "Без названия"
        description = item.get("description") or ""

        start_value = item.get("start")
        if start_value:
            try:
                event_date = datetime.fromisoformat(start_value.replace("Z", "+00:00"))
                if event_date.tzinfo is not None:
                    event_date = event_date.replace(tzinfo=None)
            except ValueError:
                event_date = now
        else:
            event_date = now

        location = item.get("location") or []
        latitude = float(location[1]) if len(location) == 2 else None
        longitude = float(location[0]) if len(location) == 2 else None

        entities = item.get("entities") or []
        venue_name = None
        address = None
        city = "Tallinn"
        country = SYNC_COUNTRY_CODE

        for entity in entities:
            if entity.get("type") == "venue":
                venue_name = entity.get("name")
                formatted = entity.get("formatted_address")
                if formatted:
                    address = formatted
                break

        category_name, category_slug = _normalize_category(item.get("category"))
        category = _get_or_create_category(db, category_name, category_slug)

        url = item.get("url")
        if not url and item.get("phq_attendance") is not None:
            url = "https://www.predicthq.com/"

        existing = (
            db.query(Event)
            .filter(Event.external_id == external_id, Event.source_id == source.id)
            .first()
        )

        if existing:
            existing.title = title
            existing.description = description
            existing.event_date = event_date
            existing.venue_name = venue_name
            existing.address = address
            existing.city = city
            existing.country = country
            existing.latitude = latitude
            existing.longitude = longitude
            existing.url = url
            existing.category_id = category.id
            existing.updated_at = now
            updated += 1
        else:
            db.add(
                Event(
                    external_id=external_id,
                    title=title,
                    description=description,
                    event_date=event_date,
                    venue_name=venue_name,
                    address=address,
                    city=city,
                    country=country,
                    latitude=latitude,
                    longitude=longitude,
                    url=url,
                    category_id=category.id,
                    source_id=source.id,
                    created_at=now,
                    updated_at=now,
                )
            )
            created += 1

    source.last_sync_at = now
    db.commit()

    return {
        "ok": True,
        "source": "PredictHQ",
        "error": None,
        "created": created,
        "updated": updated,
        "total_received": len(results),
    }