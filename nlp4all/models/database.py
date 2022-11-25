"""SQLAlchemy ORM setup"""

import os

# from greenlet import getcurrent
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///FIX_UR_ENV_REPLACE.db"
)

engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False})

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
# bind=engine,
# scopefunc=getcurrent))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db(): # pylint: disable=too-many-locals
    """Initializes the database."""
    # pylint: disable=import-outside-toplevel, unused-import
    from . import BayesianAnalysis
    from . import BayesianRobot
    from . import ConfusionMatrix
    from . import DataSource
    from . import DataTagCategory
    from . import MatrixCategories
    from . import Organization
    from . import Project
    from . import ProjectCategories
    from . import Role
    from . import Tweet
    from . import TweetAnnotation
    from . import TweetMatrix
    from . import TweetProject
    from . import TweetTag
    from . import User
    from . import UserOrgs
    from . import UserRoles
    # pylint: enable=wrong-import-position, unused-import

    Base.metadata.create_all(bind=engine)


def drop_db(): # pylint: disable=too-many-locals
    """Drops all tables in the database."""
    # pylint: disable=import-outside-toplevel, unused-import
    from . import BayesianAnalysis
    from . import BayesianRobot
    from . import ConfusionMatrix
    from . import DataSource
    from . import DataTagCategory
    from . import MatrixCategories
    from . import Organization
    from . import Project
    from . import ProjectCategories
    from . import Role
    from . import Tweet
    from . import TweetAnnotation
    from . import TweetMatrix
    from . import TweetProject
    from . import TweetTag
    from . import User
    from . import UserOrgs
    from . import UserRoles
    # pylint: enable=wrong-import-position, unused-import

    Base.metadata.drop_all(bind=engine)
