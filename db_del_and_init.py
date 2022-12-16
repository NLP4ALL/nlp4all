"""
Set up database and user
"""

from flask_bcrypt import generate_password_hash
from nlp4all import create_app

# from nlp4all.utils import add_project, clean_word
from nlp4all.models import UserModel, RoleModel, OrganizationModel
from nlp4all.helpers import database

print("WARNING: This file only works for 'localdev' environment.")

app = create_app("localdev")
with app.app_context():
    database.drop_db()

    database.init_db()

    db_session = app.extensions["sqlalchemy"].session
    db_session.commit()

    admin_role = RoleModel(name="Admin")
    db_session.add(admin_role)
    student_role = RoleModel(name="Student")
    db_session.add(admin_role)
    teacher_role = RoleModel(name="Teacher")
    db_session.add(admin_role)
    db_session.commit()

    hp = generate_password_hash("1234")
    user = UserModel(
        username="arthurhjorth",
        email="arthur.hjorth@stx.oxon.org",
        password=hp,
        admin=True,
    )
    user.roles = [  # type: ignore
        admin_role,
    ]
    db_session.add(user)

    org = OrganizationModel(name="UBI/CCTD")
    db_session.add(org)
    db_session.commit()
    org = OrganizationModel(name="IMC Seminar Group")
    db_session.add(org)
    db_session.commit()

    user = UserModel(
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
    user = UserModel(
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
