from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Handle postgres:// schema for cloud providers
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
elif db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
elif db_url.startswith("mariadb://"):
    db_url = db_url.replace("mariadb://", "mysql+pymysql://", 1)

# Handle database-specific connection args
if db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
elif "mysql" in db_url or "mariadb" in db_url:
    # MariaDB / MySQL on cPanel: pool_recycle prevents timeout drops
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=280,
        echo=settings.DEBUG
    )
else:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
