"""
Set up database and user
"""

from flask_bcrypt import generate_password_hash
from nlp4all import create_app

# from nlp4all.utils import add_project, clean_word
from nlp4all.models import User, Role, Organization
from nlp4all.helpers import database

print("WARNING: This file only works for 'localdev' environment.")

app = create_app("localdev")
with app.app_context():
    database.drop_db()

    database.init_db()

    db_session = app.extensions["sqlalchemy"].session
    db_session.commit()

    admin_role = Role(name="Admin")
    db_session.add(admin_role)
    student_role = Role(name="Student")
    db_session.add(admin_role)
    teacher_role = Role(name="Teacher")
    db_session.add(admin_role)
    db_session.commit()

    hp = generate_password_hash("1234")
    user = User(
        username="arthurhjorth",
        email="arthur.hjorth@stx.oxon.org",
        password=hp,
        admin=True,
    )
    user.roles = [  # type: ignore
        admin_role,
    ]
    db_session.add(user)

    org = Organization(name="UBI/CCTD")
    db_session.add(org)
    db_session.commit()
    org = Organization(name="IMC Seminar Group")
    db_session.add(org)
    db_session.commit()

    user = User(
        username="arthurhjorth_teacher",
        email="arthur.hjorth@u.northwestern.edu",
        password=hp,
        organizations=[
            org,
        ],
    )
    user.roles = [  # type: ignore
        teacher_role,
    ]
    db_session.add(user)
    user = User(
        username="arthur_student",
        email="arthur@mgmt.au.dk",
        password=hp,
        organizations=[
            org,
        ],
    )
    user.roles = [  # type: ignore
        student_role,
    ]
    db_session.add(user)
    db_session.commit()
    db_session.close()
