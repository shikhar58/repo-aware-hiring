import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ.get("DATABASE_URL", "postgresql+psycopg://app@db/app"))
Session = sessionmaker(engine)
