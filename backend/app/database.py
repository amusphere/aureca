from dotenv import load_dotenv
from sqlmodel import Session, create_engine

from app.config.database import DatabaseConfig

load_dotenv()

engine = create_engine(DatabaseConfig.URL, **DatabaseConfig.get_connection_args())


def get_session():
    with Session(engine) as session:
        yield session
