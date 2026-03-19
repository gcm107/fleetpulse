from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Integer, String, Text

from backend.database import Base


class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module = Column(String, nullable=False)
    source = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    records_processed = Column(Integer)
    records_inserted = Column(Integer)
    records_updated = Column(Integer)
    records_errored = Column(Integer)
    status = Column(String)
    error_message = Column(Text)
    source_file = Column(String)
    source_date = Column(Date)
