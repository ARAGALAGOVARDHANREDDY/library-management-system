import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Load .env from the project folder
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)


# Local MySQL configuration
DB_HOST = os.getenv("DB_HOST", "127.0.0.1").strip()
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root").strip()
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "library_db").strip()


# Validate configuration
if not DB_HOST:
    raise ValueError("DB_HOST is missing in .env")

if not DB_USER:
    raise ValueError("DB_USER is missing in .env")

if not DB_NAME:
    raise ValueError("DB_NAME is missing in .env")


# Create MySQL connection URL
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    query={
        "charset": "utf8mb4"
    }
)


# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False
)


# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# SQLAlchemy Base
Base = declarative_base()


# Database dependency for FastAPI
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
