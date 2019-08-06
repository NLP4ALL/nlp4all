from nlp4all import db, bcrypt
from nlp4all.models import User, Role, Organization, Project
from nlp4all.models import TweetTagCategory, Tweet, User, Organization, Project, BayesianAnalysis
from nlp4all import db, bcrypt
import json, os
from datetime import datetime
import time
import json
import nlp4all.utils
from sqlalchemy.orm.attributes import flag_modified
from random import shuffle


db.drop_all()
print("HEP")

db.create_all()
db.session.commit()

nlp4all.utils.add_role('Admin')
admin_role = nlp4all.utils.get_role('Admin')

nlp4all.utils.add_role('Student')
student_role = nlp4all.utils.get_role('Student')

nlp4all.utils.add_role('Teacher')
teacher_role = nlp4all.utils.get_role('Teacher')


print("he")

hp = bcrypt.generate_password_hash("Hermes_2014")
user = User(username="arthurhjorth", email="arthur.hjorth@stx.oxon.org", password=hp)
user.roles = [admin_role,]
db.session.add(user)

org = Organization(name="UBI/CCTD")
db.session.add(org)
db.session.commit()

user = User(username="arthurhjorth_teacher", email="arthur.hjorth@u.northwestern.edu", password=hp, organizations=[org,])
user.roles = [teacher_role,]
db.session.add(user)
user = User(username="arthurhjorth_student", email="hermeshjorth2011@u.northwestern.edu", password=hp, organizations=[org,])
user.roles = [student_role,]
db.session.add(user)
db.session.commit()


data_dir = 'tweet_data/'
files = [f for f in os.listdir(data_dir) if '_out.json' in f]
print("reading in data")
existing_tag_names = []
for f in files:
    print(f)
    with open(data_dir+f) as inf:
        lines = [line for line in inf.readlines()]
        for line in lines[:200]:
        # for line in inf.readlines():
            indict = json.loads(line)
            category = TweetTagCategory.query.filter_by(name = indict['twitter_handle']).first()
            if not category:
                nlp4all.utils.add_category(indict['twitter_handle'], "Tweet from " + indict['twitter_handle'])
            existing_tag_names.append(indict['twitter_handle'])
            category = TweetTagCategory.query.filter_by(name = indict['twitter_handle']).first()
            nlp4all.utils.add_tweet_from_dict(indict, category)

print("creating orgs")


org = Organization.query.first()
all_cats = TweetTagCategory.query.all()
cat_ids = [5, 6]
nlp4all.utils.add_project(name="DF og EL", description="Kan du kende forskel på DF og Enhedslisten?", org = org.id, cat_ids = cat_ids)

analysis = BayesianAnalysis(user = 2, name="Test Analysis", project=1, data = {"counts" : 0, "words" : {}})
db.session.add(analysis)
db.session.commit()

# get 800 DF tweets and 800 EHl tweets and add them

# list to store tags in
tags = []
print("DF")
df_tweets = Tweet.query.filter_by(category = 1).all()
df_cat = all_cats[0]

shuffle(df_tweets)
for t in df_tweets[:300]:
    # tag = TweetTag (category = 1, analysis = analysis.id, tweet=t.id)
    # tags.append(tag)
    analysis.data = analysis.updated_data(t, df_cat)
print("EHL")
ehl_cat = all_cats[2]
ehl_tweets = Tweet.query.filter_by(category = 3).all()
shuffle(ehl_tweets)
for t in ehl_tweets[:300]:
    # tag = TweetTag (category = 2, analysis = analysis.id, tweet=t.id)
    # tags.append(tag)
    analysis.data = analysis.updated_data(t, ehl_cat)



flag_modified(analysis, "data")
db.session.add(analysis)
db.session.merge(analysis)
db.session.flush()
db.session.commit()




# for t in tags:
#     db.session.add(t)
# db.session.commit()

for c in TweetTagCategory.query.all():
    print(c.id, c.name) 