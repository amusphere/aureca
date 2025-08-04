from os import getenv

from dotenv import load_dotenv
from sqlmodel import Session, create_engine

load_dotenv()

DATABASE_URL = getenv("DATABASE_URL", "sqlite:///./test_database.db")

engine = create_engine(DATABASE_URL, future=True)


def get_session():
    with Session(engine) as session:
        yield session
