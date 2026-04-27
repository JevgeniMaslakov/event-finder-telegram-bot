from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..config import TICKETMASTER_API_KEY, SYNC_CITY, SYNC_COUNTRY_CODE
from ..models import Category, Event, Source

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

CATEGORY_MAP = {
    "music": ("Концерты", "concerts"),
    "sports": ("Спортивные мероприятия", "sports"),
    "arts & theatre": ("Лекции и выставки", "lectures-exhibitions"),
    "arts": ("Лекции и выставки", "lectures-exhibitions"),
    "film": ("Кино", "film"),
    "miscellaneous": ("Другое", "other"),
    "family": ("Другое", "other"),
}


def _normalize_category(classification: dict[str, Any]) -> tuple[str, str]:
    segment = classification.get("segment", {}) if classification else {}
    name = (segment.get("name") or "").strip().lower()
    return CATEGORY_MAP.get(name, ("Другое", "other"))


def _get_or_create_source(db: Session) -> Source:
    source = db.query(Source).filter(Source.name == "Ticketmaster").first()
    if source:
        return source

    source = Source(
        name="Ticketmaster",
        type="api",
        base_url="https://developer.ticketmaster.com/",
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


async def sync_ticketmaster_events(db: Session) -> dict:
    if not TICKETMASTER_API_KEY:
        return {
            "ok": False,
            "source": "Ticketmaster",
            "error": "TICKETMASTER_API_KEY is not set",
            "created": 0,
            "updated": 0,
            "total_received": 0,
        }

    params = {
        "apikey": TICKETMASTER_API_KEY,
        "city": SYNC_CITY,
        "countryCode": SYNC_COUNTRY_CODE,
        "size": 50,
        "sort": "date,asc",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(TICKETMASTER_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return {
            "ok": False,
            "source": "Ticketmaster",
            "error": str(e),
            "created": 0,
            "updated": 0,
            "total_received": 0,
        }

    embedded = data.get("_embedded", {})
    events = embedded.get("events", [])
    source = _get_or_create_source(db)

    created = 0
    updated = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for item in events:
        external_id = item.get("id")
        if not external_id:
            continue

        title = item.get("name") or "Без названия"
        description = item.get("info") or item.get("pleaseNote") or ""

        dates = item.get("dates", {}).get("start", {})
        local_date = dates.get("localDate")
        local_time = dates.get("localTime", "19:00:00")

        if local_date:
            try:
                event_date = datetime.fromisoformat(f"{local_date}T{local_time}")
            except ValueError:
                event_date = now
        else:
            event_date = now

        venue = ((item.get("_embedded", {}) or {}).get("venues", [{}]) or [{}])[0]
        venue_name = venue.get("name")
        city = (venue.get("city") or {}).get("name")
        country = (venue.get("country") or {}).get("countryCode")
        address = (venue.get("address") or {}).get("line1")

        location = venue.get("location") or {}
        lat = float(location["latitude"]) if location.get("latitude") else None
        lon = float(location["longitude"]) if location.get("longitude") else None

        url = item.get("url")

        classifications = item.get("classifications", [])
        cat_name, cat_slug = _normalize_category(classifications[0] if classifications else {})
        category = _get_or_create_category(db, cat_name, cat_slug)

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
            existing.latitude = lat
            existing.longitude = lon
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
                    latitude=lat,
                    longitude=lon,
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
        "source": "Ticketmaster",
        "error": None,
        "created": created,
        "updated": updated,
        "total_received": len(events),
    }