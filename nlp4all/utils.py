import tweepy
import re
import json
from nlp4all.models import TweetTagCategory, Tweet, Project, Role
from datetime import datetime
import time
import operator
from nlp4all import db


def generate_n_hsl_colors(no_colors, transparency=1, offset=0):
    hsl_span = int(255 / no_colors)
    return[(hsl_span * n + offset, 50, 100 * transparency) for n in range(no_colors)]

 
# takes a list of TweetTagCategory objects, returns
# a dict with the name of a category and its corresponding
# color
def assign_colors(list_of_categories):
    category_color_dict = {}
    no_colors = len(list_of_categories)
    hsl_span = int(255 / no_colors)
    for n in range(no_colors):
        category_color_dict[list_of_categories[n].name] = (n * hsl_span) + (hsl_span / 10)
    return(category_color_dict)

# because some tokens need to be split, we donøt know how many we will return per chunk, so we 
# make a generator. Additionally, this needs to return both the original version of the token and a 
# lowered and cleaned version that we can use to look up its current classification
# def clean_and_tokenize(astring):
    

# return a list of tuples with
# (word, tag, number, color) 
# for the tag and number that is highest
def create_css_info(classifications, text, list_of_categories):
    category_color_dict = assign_colors(list_of_categories)
    tups = []
    for word in text.split():
        clean_word = clean_non_transparencynum(word).lower()
        if clean_word in classifications:
            # @todo: special case 50/50 
            max_key = max(classifications[clean_word].items(), key=operator.itemgetter(1))[0]
            the_tup = (word, max_key, round( 100 * classifications[clean_word][max_key]), category_color_dict[max_key])
            tups.append(the_tup)
        else:
            tups.append((word, "none", 0))
    return(tups)
            
        
        # match = re.compile(word, re.IGNORECASE) # match.sub("")
#     words = clean_non_transparencynum(text).split()
#     print(classifications)
    
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


def remove_hash_links_mentions(t):
        t = [w for w in t.lower().split() if "#" not in w and "http" not in w and "@" not in w]
        t = " ".join([w for w in t])
        return(t)


def clean_non_transparencynum(t):
        t = t.replace(".", " ")
        t = t.replace("!", " ")
        t = t.replace("”", " ")
        t = t.replace("\"", " ")
        t = t.replace("\'", " ")
        t = t.replace("“", " ")
        t = t.replace("?", " ")
        t = t.replace(":", " ")
        t = t.replace("/", " ")
        # t = t.replace("-", " ")
        # t = t.replace("–", " ")
        t = t.replace(",", " ")
        t = t.replace("\(", " ")
        t = t.replace("\)", " ")
        return(t.strip())# changed this, might not work!

# We can get up to 3200 tweets per account at the time we do this. But we can get interrupted if twitter thinks we are being
# too greedy. I think the best way to ensure the transaction is to make sure that we download all 3200 tweets and add them to our 
# db, or we don't add any at all. Right? I think so...
def add_tweets_from_account(twitter_handle):
        consumer_key="***REMOVED***"
        consumer_secret="***REMOVED***"
        access_token="***REMOVED***"
        access_token_secret="***REMOVED***"
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        with open(twitter_handle+'_unicode.json', 'w') as outf:
                # we probably still want to save them in case we need to load them later, but 
                # no need to write for each file. Just append each dict to a big list, then save that.
                for status in tweepy.Cursor(api.user_timeline, screen_name=p, tweet_mode="extended").items():
                        # outf.write(json.dumps(status._json, ensure_ascii=False))
                        # outf.write("\n")
                        outdict = {}
                        indict = status
                        outdict['twitter_handle'] = handle
                        outdict['time'] = indict['created_at']
                        outdict['id'] = indict['id']
                        outdict['id_str'] = indict['id_str']
                        if 'retweeted_status' in  indict:
                            outdict['full_text'] = indict['retweeted_status']['full_text']
                        else:
                            outdict['full_text'] = indict['full_text']
                        outf.write(json.dumps(outdict, ensure_ascii=False))
                        outf.write("\n")
                        add_tweet_from_dict(outdict)

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
        t = clean_non_transparencynum(remove_hash_links_mentions(t))
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

# this takes a dictionary with n parties, and the estimate for each of them.
# the data from this function feeds into bar_chart.html (through analysis), and needs:
# 1. A list of party names (labels)
# 2. A list of estimates
# 3. A list of background colors (the actual color but with an transparency of .2)
# 4. a list of bar colors

def create_bar_chart_data(predictions, title=""):
        data = {}
        data['title'] = title
        colors = generate_n_hsl_colors(len(predictions))
        bg_colors = generate_n_hsl_colors(len(predictions), transparency = .5)
        data_points = []
        for tup in zip(list(predictions.keys()), list(predictions.values()), colors, bg_colors):
                d = {}
                d['label'] = tup[0] 
                d['estimate'] = tup[1] 
                d['color'] = hsl_color_to_string(tup[2])
                d['bg_color'] = hsl_color_to_string(tup[3])
                data_points.append(d)
        data['data_points'] = data_points
        print(data_points)
        return(data)

def hsl_color_to_string(hsltup):
        return(f"hsl({hsltup[0]}, {hsltup[1]}%, {hsltup[2]}%)")
         
