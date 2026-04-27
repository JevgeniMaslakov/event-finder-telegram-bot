from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(64), unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    language = Column(String(16), default="ru", nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    searches = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    value = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="searches")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)

    events = relationship("Event", back_populates="category")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=True)
    last_sync_at = Column(DateTime, nullable=True)

    events = relationship("Event", back_populates="source")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), index=True, nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=False)
    venue_name = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    country = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    url = Column(String(1000), nullable=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    category = relationship("Category", back_populates="events")
    source = relationship("Source", back_populates="events")