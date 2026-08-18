from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ScrapedItemDB(Base):
    """SQLAlchemy model for persisted scraped items.

    Columns:
    - id: primary key integer
    - title: text, not null
    - url: text, not null
    - scraped_at: timestamp with timezone, defaults to now()
    """
    __tablename__ = "scraped_items"
    __table_args__ = (UniqueConstraint('url', name='uq_scraped_items_url'),)

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
