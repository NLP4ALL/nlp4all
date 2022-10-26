"""
Set up database and user
"""

import json
from datetime import datetime
import time
import re
from flask_bcrypt import generate_password_hash
from nlp4all import app, db_session
# from nlp4all.utils import add_project, clean_word
from nlp4all.models import User, Role, Organization, TweetTagCategory, Tweet, database

# app context part of update of flask -
with app.app_context():
    database.drop_db()

    database.init_db()
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
    user.roles = [
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
    user.roles = [
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
    user.roles = [
        student_role,
    ]
    db_session.add(user)
    db_session.commit()
    db_session.close()

    # org = Organization.query.filter_by(name="IMC Seminar Group").first()
    # biden = TweetTagCategory.query.filter_by(name="JoeBiden.json").first()
    # bernie = TweetTagCategory.query.filter_by(name="BernieSanders.json").first()

    # cats = [biden.id, bernie.id]

    # project = add_project(
    #     name="Bernie and JoeBiden",
    #     description="Can you tell the difference between Bernie and Joe Biden, Aug 2019-March 2020?",
    #     org=org.id,
    #     cat_ids=cats,
    # )

    # db_session.commit()
