from nlp4all import db, bcrypt
from nlp4all.models import User, Role, Organization, Project
from nlp4all.models import TweetTagCategory, Tweet, User, Organization, Project, BayesianAnalysis
from nlp4all import db, bcrypt
import json, os
from datetime import datetime
import time
import json




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



data_dir = 'tweet_data/'
files = [f for f in os.listdir(data_dir) if '_out.json' in f]

existing_tag_names = []
for f in files:
    with open(data_dir+f) as inf:
        counter = 0
        for line in inf.readlines()[:25]:
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
            a_tweet = Tweet(
                time_posted = timestamp,
                category = category.id,
                handle = indict['twitter_handle'],
                text= indict['full_text'],
                words = [w for w in indict['full_text'].lower().split() if "#" not in w and "http" not in w],
                links = [w for w in indict['full_text'].split() if "http" in w],
                hashtags = [w for w in indict['full_text'].split() if "#" in w],
                url = "https://twitter.com/"+indict['twitter_handle']+"/"+str(indict['id'])
                )
            
            db.session.add(a_tweet)


db.session.commit()
db.session.close()


project = Project(name="DF og Ehl", organization=org.id)
db.session.add(project)
db.session.commit()

print(Tweet.query.all())

for t in Tweet.query.all():
    print(t)