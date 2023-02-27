"""Database helpers."""

from __future__ import annotations

import typing as t
import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from sqlalchemy import select
from ..database import Base
from ..config import get_env_variable

if t.TYPE_CHECKING:
    from ..models import OrganizationModel


def create_default_org() -> 'OrganizationModel':
    """Creates the default organization."""
    from ..models import OrganizationModel
    from .. import db

    org_name = get_env_variable("NLP4ALL_ORG_NAME")
    # if the matching org already exists, don't create it
    stmt = select(OrganizationModel).where(OrganizationModel.name == org_name)
    org: OrganizationModel = db.session.scalars(stmt).first()  # type: ignore

    if org is not None:
        current_app.logger.warning(f"Default org already exists (id: {org.id}, name: {org.name}), not creating it.")
        return org

    org = OrganizationModel(name=org_name)
    db.session.add(org)
    db.session.commit()
    current_app.logger.info(f"Created default org: {org_name} (id: {org.id})", )
    return org


def create_default_user(org: 'OrganizationModel') -> None:
    """Creates the default user."""
    from ..models import UserModel
    from ..models import OrganizationModel
    from ..controllers import UserController
    from .. import db

    # First, we check if there are any admins for this org
    # if there are, we don't create a default user
    stmt = select(UserModel).where(  # type: ignore
        UserModel.admin
    ).where(  # type: ignore
        UserModel.organizations.any(OrganizationModel.id == org.id)
    )
    admin: UserModel = db.session.scalars(stmt).first()  # type: ignore
    if admin is not None:
        current_app.logger.warning(
            f"Default admin user (id: {admin.id}) for org {org.name} (id: {org.id}) already exists, not creating it.")
        return

    user_name = get_env_variable("NLP4ALL_ADMIN_EMAIL")
    user_password = get_env_variable("NLP4ALL_ADMIN_PASSWORD")

    user = UserModel(
        username=user_name,
        email=user_name,
        password=UserController.bcrypt.generate_password_hash(user_password).decode("utf-8"),
        admin=True
    )
    user.organizations.append(org)
    db.session.add(user)
    db.session.commit()
    current_app.logger.info(f"Created default admin user {user_name} (id: {user.id}) for org {org.name} (id: {org.id})")


def init_db() -> None:  # pylint: disable=too-many-locals
    """Initializes the database."""
    engine = current_app.extensions["sqlalchemy"].engine
    Base.metadata.create_all(bind=engine)
    org = create_default_org()
    create_default_user(org)


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    """Initializes the database."""
    init_db()
    current_app.logger.info("Initialized database.")


def drop_db() -> None:  # pylint: disable=too-many-locals
    """Drops all tables in the database."""
    engine = current_app.extensions["sqlalchemy"].get_engine()
    Base.metadata.drop_all(bind=engine)


@click.command("drop-db")
@with_appcontext
def drop_db_command() -> None:
    """Drops the database."""
    drop_db()
    current_app.logger.info("Dropped database.")


def init_app(app: Flask) -> None:
    """Initializes the database for the Flask app.

    Args:
        app (Flask): The Flask app.
    """
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_db_command)


def model_cols_jsonb_to_json(app: Flask, cls: t.Type[Base]) -> None:  # pylint: disable=too-many-locals
    """Converts a Postgres JSONB column to a SQLite JSON column.
    Within the model itself, the column is defined as a JSONB column,
    we only need to change this to JSON when we are using SQLite.

    Currently only Data and DataSource use JSONB, and we only need to
    change these when we're testing, or local dev (which both use sqlite).
    """
    # pylint: disable=import-outside-toplevel, unused-import
    from sqlalchemy.dialects.sqlite import JSON
    from sqlalchemy_json import mutable_json_type, NestedMutable
    from sqlalchemy.ext.mutable import MutableDict
    from ..database import N4AFlatJSON, N4ANestedJSON, N4AFlatJSONB, N4ANestedJSONB

    SQLiteNestedMutableJSON = mutable_json_type(dbtype=JSON, nested=True)  # pylint: disable=invalid-name
    SQLiteMutableJSON = mutable_json_type(dbtype=JSON, nested=False)  # pylint: disable=invalid-name

    tables = cls.__subclasses__()
    for tbl in tables:
        type_changed = False
        app.logger.warning(">>> Converting table [%s] to SQLite JSON ===", tbl.__tablename__)
        for col in tbl.__table__.columns:
            if isinstance(col.type, (N4ANestedJSON, N4ANestedJSONB)):
                app.logger.warning("      Converting column [%s] from %s to %s (DBTYPE: %s)",
                                   col.name,
                                   type(col.type),
                                   NestedMutable,
                                   JSON)
                col.type = SQLiteNestedMutableJSON
                type_changed = True
                continue
            if isinstance(col.type, (N4AFlatJSON, N4AFlatJSONB)):
                app.logger.warning("      Converting column [%s] from %s to %s (DBTYPE: %s)",
                                   col.name,
                                   type(col.type),
                                   MutableDict,
                                   JSON)
                col.type = SQLiteMutableJSON
                type_changed = True
                continue
        if type_changed:
            app.logger.warning(
                "+++ Done converting table [%s] to SQLite JSON +++\n",
                tbl.__tablename__)
        else:
            app.logger.warning(
                "--- No changes to table [%s] ---\n",
                tbl.__tablename__)
    # pylint: enable=import-outside-toplevel, unused-import
