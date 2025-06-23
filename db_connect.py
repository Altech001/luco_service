from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://lucosms_fr6s_user:XW8sLMPg8BPAKJmKbyymPokMLJZx2oia@dpg-d1c5d8euk2gs73acoa8g-a.oregon-postgres.render.com/lucosms_fr6s"

engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()