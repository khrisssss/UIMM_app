from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os 

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL") #reads the database connection from .env

engine = create_engine(DATABASE_URL) #connection between Python and PostgreSQL
SessionLocal = sessionmaker(    #creates database sessions
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

Base = declarative_base() #parent class for database tables

def get_db():            #gives a database session to API routes
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()