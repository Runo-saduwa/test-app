from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL (update your .env file with the correct values)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://runo:1234@localhost:5432/cowabunga")

# SQLAlchemy Synchronous Engine
engine = create_engine(DATABASE_URL, echo=True)

# Synchronous Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get the session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()