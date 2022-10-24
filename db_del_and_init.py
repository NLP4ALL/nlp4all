"""
Set up database and user
"""

import json
from datetime import datetime
import time
import re
from nlp4all import db, bcrypt
from nlp4all.utils import add_project, clean_word
from nlp4all.models import User, Role, Organization, TweetTagCategory, Tweet

# app context part of update of flask -
# with app.app_context():
db.drop_all()

db.create_all()
db.session.commit()

admin_role = Role(name="Admin")
db.session.add(admin_role)
student_role = Role(name="Student")
db.session.add(admin_role)
teacher_role = Role(name="Teacher")
db.session.add(admin_role)
db.session.commit()

hp = bcrypt.generate_password_hash("1234")
user = User(
    username="arthurhjorth",
    email="arthur.hjorth@stx.oxon.org",
    password=hp,
    admin=True,
)
user.roles = [
    admin_role,
]
db.session.add(user)

org = Organization(name="UBI/CCTD")
db.session.add(org)
db.session.commit()
org = Organization(name="IMC Seminar Group")
db.session.add(org)
db.session.commit()

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
db.session.add(user)
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
db.session.add(user)
db.session.commit()

DATA_FILE = "tweet_data/all_parties.json"

existing_tag_names = []
with open(DATA_FILE, encoding="utf8") as inf:
    DATE_REP = "%Y-%m-%dT%H:%M:%S.%fZ"
    counter = 0  # pylint: disable=invalid-name
    for line in inf.readlines():  # choose how many tweets you want from each party file
        if counter % 1000 == 0:
            print(counter)
        indict = json.loads(line)
        # add cateogry if it does not already exist
        if indict["twitter_id"] not in existing_tag_names:
            category = TweetTagCategory.query.filter_by(
                name=indict["twitter_id"]
            ).first()
            if not category:
                category = TweetTagCategory(
                    name=indict["twitter_id"],
                    description="Tweet from " + indict["twitter_id"],
                )
                db.session.add(category)
                db.session.commit()
            existing_tag_names.append(indict["twitter_id"])
        category = TweetTagCategory.query.filter_by(name=indict["twitter_id"]).first()
        date_str = indict["created_at"]
        unix_time = time.mktime(datetime.strptime(date_str, DATE_REP).timetuple())
        timestamp = datetime.fromtimestamp(unix_time)
        t = indict["full_text"]
        t.replace(".", " ")
        t.replace("!", " ")
        t.replace("?", " ")
        t.replace(":", " ")
        t.replace("-", " ")
        t.replace("-", " ")
        t.replace(",", " ")
        t.replace("\\(", " ")
        t.replace("\\)", " ")
        a_tweet = Tweet(
            time_posted=timestamp,
            category=category.id,
            text=indict["full_text"],
            handle=indict["twitter_id"],
            full_text=" ".join([clean_word(word) for word in t.split()]),  # changed
            words=[
                re.sub(r"[^\w\s]", "", w)
                for w in t.lower().split()
                if "#" not in w and "http" not in w and "@" not in w
            ],
            links=[w for w in t.split() if "http" in w],
            hashtags=[w for w in t.split() if "#" in w],
            mentions=[w for w in t.split() if "@" in w],
            url="https://twitter.com/" + indict["twitter_id"] + "/" + str(indict["id"]),
        )
        db.session.add(a_tweet)
        counter = counter + 1  # pylint: disable=invalid-name


db.session.commit()
db.session.close()

org = Organization.query.filter_by(name="IMC Seminar Group").first()
biden = TweetTagCategory.query.filter_by(name="JoeBiden.json").first()
bernie = TweetTagCategory.query.filter_by(name="BernieSanders.json").first()

cats = [biden.id, bernie.id]

project = add_project(
    name="Bernie and JoeBiden",
    description="Can you tell the difference between Bernie and Joe Biden, Aug 2019-March 2020?",
    org=org.id,
    cat_ids=cats,
)

db.session.commit()
