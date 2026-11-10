from sqlalchemy import create_engine  # the tool that opens a connection to the database
from sqlalchemy.orm import sessionmaker, declarative_base  # tools to talk to the database and describe tables
from dotenv import load_dotenv  # the tool that reads the secret settings in the .env file
import os  # gives access to the computer's settings (environment variables)

load_dotenv()  # read the .env file, so its settings become available below

DATABASE_URL = os.getenv("DATABASE_URL")  # the address of the database (user, password, server, name), taken from .env

engine = create_engine(DATABASE_URL)  # the "phone line" between Python and PostgreSQL
SessionLocal = sessionmaker(  # a factory that makes "sessions" (one conversation with the database)
    autocommit=False,  # never save automatically: we decide when to save with db.commit()
    autoflush=False,  # do not send changes to the database before we ask
    bind=engine  # use the phone line created above
)

Base = declarative_base()  # the parent of every table class: models/*.py inherit from it

def get_db():  # gives each API route its own database session
    db = SessionLocal()  # open a new conversation with the database
    try:
        yield db  # lend the session to the route while it works
    finally:
        db.close()  # when the route is finished (even after an error), hang up
