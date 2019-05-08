<<<<<<< HEAD
import re
import json
from nlp4all.models import TweetTagCategory, Tweet, Project, Role
from datetime import datetime
import time
from nlp4all import db

# this function takes a dictionary containing 
def add_css_class(classifications, text):
    words = clean_non_alphanum(text).split()
    print(words)
#     categories = list(words.keys())
#     all_words = list(words[categories[0]].keys())
#     text_words = text.split()


def clean_word(aword):
    if "@" in  aword:
        return "@twitter_ID"
    if "#" in aword:
        return "#hashtag"
    if "http" in aword:
        return "http://link"
    return aword


def clean_non_alphanum(t):
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
        t = t.replace("–", " ")
        t = t.replace(",", " ")
        t = t.replace("\(", " ")
        t = t.replace("\)", " ")
        return(t)

def add_category(name, description):
        category = TweetTagCategory(name = name, description = description)
        db.session.add(category)
        db.session.commit()

def add_project(name, org, cats):
        project = Project(name = name, organization = org, categories = cats)
        db.session.add(project)
        db.session.commit()

def twitter_date_to_unix(date_str):
        date_rep = '%a %b %d %H:%M:%S %z %Y'
        unix_time = time.mktime(datetime.strptime(date_str, date_rep).timetuple())
        return(datetime.fromtimestamp(unix_time))

def add_tweet_from_dict(indict, category):
        timestamp = twitter_date_to_unix(indict['time'])
        full_text = indict['full_text']
        links = [w for w in full_text.split() if "http" in w],
        hashtags = [w for w in full_text.split() if "#" in w],
        mentions = [w for w in full_text.split() if "@" in w],
        tweet_parts = [clean_word(w) for w in full_text.split()]
        full_text=" ".join([w for w in tweet_parts])
        t = indict['full_text']
        t = clean_non_alphanum(t)
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

def add_role(role_name):
        role = Role(name=role_name)
        db.session.add(role)
        db.session.commit()

def get_role(role_name):
        return(Role.query.filter_by(name=role_name).first())
=======

# this function takes a dictionary containing 
def add_css_class(words, text):
    categories = list(words.keys())
    all_words = list(words[categories[0]].keys())
    text_words = text.lower().split()
    for w in text_words:
        print(w)
        # css_class = (category, )
        # print(t, )
>>>>>>> b07ee2241f7c02d6180008eac330234c55a18768

