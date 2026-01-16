import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, DateTime, UniqueConstraint, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db_path():
    env_path = os.getenv('BASE_PATH')
    if env_path:
        try:
            p = Path(env_path)
            if p.parent.exists(): return p / 'tap.db'
        except: pass
    return Path(__file__).resolve().parent.parent / 'tap.db'

DB_FILE_PATH = get_db_path()
DB_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_FILE_PATH}")
Session = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

class ImageLog(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    phash = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PlaceLog(Base):
    __tablename__ = "places"
    id = Column(Integer, primary_key=True)
    title_norm = Column(String, index=True)
    source = Column(String)
    region = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('title_norm', 'source', name='_place_source_uc'),)

class PostLog(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    embedding = Column(JSON) # 문맥 벡터 저장
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)

init_db()
