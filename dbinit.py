from nlp4all import db, bcrypt
from nlp4all.models import User, Role, Organization, Project
from nlp4all.models import TweetTagCategory, Tweet, User, Organization, Project, BayesianAnalysis
from nlp4all import db, bcrypt
import json, os
from datetime import datetime
import time
import json
from sqlalchemy.orm.attributes import flag_modified

db.drop_all()


db.create_all()
db.session.commit()

admin_role = Role(name='Admin')
db.session.add(admin_role)
student_role = Role(name='Student')
db.session.add(admin_role)
teacher_role = Role(name='Teacher')
db.session.add(admin_role)
db.session.commit()

hp = bcrypt.generate_password_hash("***REMOVED***")
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


def clean_word(aword):
    if "@" in  aword:
        return "@twitter_ID"
    if "#" in aword:
        return "#hashtag"
    if "http" in aword:
        return "http://link"
    return aword

data_dir = 'tweet_data/'
files = [f for f in os.listdir(data_dir) if '_out.json' in f]

existing_tag_names = []
for f in files:
    with open(data_dir+f) as inf:
        counter = 0
        for line in inf.readlines()[:800]:
            indict = json.loads(line)
#             add cateogyr if it does not already exist
            if indict['twitter_handle'] not in existing_tag_names:
                category = TweetTagCategory.query.filter_by(name = indict['twitter_handle']).first()
                if not category:
                    category = TweetTagCategory(name = indict['twitter_handle'], description = "Tweet from " + indict['twitter_handle'])
                    db.session.add(category)
                    db.session.commit()
                existing_tag_names.append(indict['twitter_handle'])
            category = TweetTagCategory.query.filter_by(name = indict['twitter_handle']).first()
            date_str = indict['time']
            date_rep = '%a %b %d %H:%M:%S %z %Y'
            unix_time = time.mktime(datetime.strptime(date_str, date_rep).timetuple())
            timestamp = datetime.fromtimestamp(unix_time)
            full_text = indict['full_text']
            links = [w for w in full_text.split() if "http" in w],
            hashtags = [w for w in full_text.split() if "#" in w],
            mentions = [w for w in full_text.split() if "@" in w],
            tweet_parts = [clean_word(w) for w in full_text.split()]
            full_text=" ".join([w for w in tweet_parts])
            t = indict['full_text']
            t = [w for w in t.lower().split() if "#" not in w and "http" not in w and "@" not in w]
            t = " ".join([w for w in t])
            t = t.replace(".", " ")
            t = t.replace("!", " ")
            t = t.replace("”", " ")
            t = t.replace("\"", " ")
            t = t.replace("\'", " ")
            t = t.replace("“", " ")
            t = t.replace("?", " ")
            t = t.replace(":", " ")
            t = t.replace("/", " ")
            t = t.replace("-", " ")
            t = t.replace("-", " ")
            t = t.replace(",", " ")
            t = t.replace("\(", " ")
            t = t.replace("\)", " ")
            t = t.lower()
            words = t.split()
            a_tweet = Tweet(
                time_posted = timestamp,
                category = category.id,
                handle = indict['twitter_handle'],
                full_text= full_text,
                words = words,
                links = links,
                hashtags = hashtags,
                mentions = mentions,
                url = "https://twitter.com/"+indict['twitter_handle']+"/"+str(indict['id']),
                text = " ".join([clean_word(word) for word in t.split()])
                )
            
            db.session.add(a_tweet)


db.session.commit()
db.session.close()

org = Organization.query.first()
all_cats = TweetTagCategory.query.all()
cats = [all_cats[4], all_cats[5]]
project = Project(name="DF og Ehl", organization=org.id, categories=cats)
db.session.add(project)
db.session.commit()
analysis = BayesianAnalysis(user = 2, name="Test Analysis", filters=json.dumps([]), features=json.dumps([]),project=1, data = {"counts" : 0, "words" : {}})

db.session.add(analysis)
db.session.commit()

# get 800 DF tweets and 800 EHl tweets and add them
df_tweets = Tweet.query.filter_by(category = 5).all()
df_cat = all_cats[4]
for t in df_tweets[:500]:
    analysis.data = analysis.updated_data(t, df_cat)

ehl_cat = all_cats[5]
ehl_tweets = Tweet.query.filter_by(category = 6).all()
for t in ehl_tweets[:500]:
    analysis.data = analysis.updated_data(t, ehl_cat)

flag_modified(analysis, "data")
db.session.add(analysis)
db.session.merge(analysis)
db.session.flush()
db.session.commit()

for c in TweetTagCategory.query.all():
    print(c.id, c.name) 