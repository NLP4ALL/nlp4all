"""Analyses helper functions"""

import re
import time
import operator
from datetime import datetime

from flask import g

from .datasets import create_n_split_tnt_sets, create_n_train_and_test_sets
from .colors import (
    assign_colors,
    generate_n_hsl_colors,
    hsl_color_to_string,
    ann_assign_colors,
)
from .nlp import clean_non_transparencynum, clean_word, remove_hash_links_mentions
from ..models import (
    DataTagCategoryModel,
    DataModel,
    ProjectModel,
    RoleModel,
    ConfusionMatrixModel,
    DataAnnotationModel
)

# @TODO: this file needs to be broken out
# some of these functions belong on the **models** not the **helpers**

# return a list of tuples with
# (word, tag, number, color)
# for the tag and number that is highest


def create_css_info(classifications, text, list_of_categories):
    """create a list of tuples for the tag and number that is highest"""
    category_color_dict = assign_colors(list_of_categories)
    tups = []
    split_list = text.split()
    word_counter = 0
    for word in split_list:
        cleaned_word = clean_non_transparencynum(word).lower()
        if cleaned_word in classifications:
            # @todo: special case 50/50
            max_key = max(classifications[cleaned_word].items(), key=operator.itemgetter(1))[0]
            the_tup = (
                word,
                max_key,
                round(100 * classifications[cleaned_word][max_key]),
                category_color_dict[max_key],
                word_counter,
            )
            tups.append(the_tup)
            word_counter += 1
        else:
            tups.append((word, "none", 0, "", word_counter))
            word_counter += 1
    return tups

    # match = re.compile(word, re.IGNORECASE) # match.sub("")


#     words = clean_non_transparencynum(text).split()
#     print(classifications)

#     categories = list(words.keys())
#     all_words = list(words[categories[0]].keys())
#     text_words = text.split()


# We can get up to 3200 tweets per account at the time we do this.
# But we can get interrupted if twitter thinks we are being
# too greedy. I think the best way to ensure the transaction
# is to make sure that we download all 3200 tweets and add them to our
# db, or we don't add any at all. Right? I think so...


# def add_tweets_from_account(twitter_handle):
#     """add tweets from a twitter account to the database"""
#     # @TODO: I broke this now, but we need to either
#     # use env or a stored key from a database etc.
#     consumer_key = "NONE"
#     consumer_secret = "NONE"
#     access_token = "NONE"
#     access_token_secret = "NONE"
#     auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
#     auth.set_access_token(access_token, access_token_secret)
#     api = tweepy.API(auth)
#     with open(twitter_handle + "_unicode.json", "w", encoding="utf8") as outf:
#         # we probably still want to save them in case we need to load them later, but
#         # no need to write for each file. Just append each dict to a big list,
#         # then save that.
#         for status in tweepy.Cursor(
#             api.user_timeline, screen_name=twitter_handle, data_mode="extended"
#         ).items():
#             # outf.write(json.dumps(status._json, ensure_ascii=False))
#             # outf.write("\n")
#             outdict = {}
#             indict = status
#             outdict["twitter_handle"] = twitter_handle
#             outdict["time"] = indict["created_at"]
#             outdict["id"] = indict["id"]
#             outdict["id_str"] = indict["id_str"]
#             if "retweeted_status" in indict:
#                 outdict["full_text"] = indict["retweeted_status"]["full_text"]
#             else:
#                 outdict["full_text"] = indict["full_text"]
#             outf.write(json.dumps(outdict, ensure_ascii=False))
#             outf.write("\n")
#             add_data_from_dict(outdict)


def add_category(name, description):
    """add a category to the database"""
    category = DataTagCategoryModel(name=name, description=description)
    g.db.add(category)
    g.db.commit()


def get_user_projects(a_user):
    """get a list of projects for a user"""
    # people have access to projects iif they are part of the organizatioin of those
    # projects, or  because the user is an admiin
    my_projects = []
    if a_user.admin:
        my_projects = ProjectModel.query.all()
    else:
        user_orgs = [org.id for org in a_user.organizations]
        my_projects = ProjectModel.query.filter(
            ProjectModel.organization.in_(user_orgs)
        ).all()  # pylint: disable=no-member
    return my_projects


def add_project(name, description, org, cat_ids):
    """add a project to the database"""
    print(description)
    cats_objs = DataTagCategoryModel.query.filter(
        DataTagCategoryModel.id.in_(cat_ids)
    ).all()  # pylint: disable=no-member
    data_objs = [t for cat in cats_objs for t in cat.data]
    tf_idf = tf_idf_from_tweets_and_cats_objs(data_objs, cats_objs)
    data_id_and_cat = {t.id: t.category for t in data_objs}
    training_and_test_sets = create_n_train_and_test_sets(30, data_id_and_cat)
    project = ProjectModel(
        name=name,
        description=description,
        organization=org,
        categories=cats_objs,
        tweets=data_objs,
        tf_idf=tf_idf,
        training_and_test_sets=training_and_test_sets,
    )
    g.db.add(project)
    g.db.commit()
    return project


def add_matrix(cat_ids, ratio, userid):
    """add a matrix to the database"""
    ratio = round(ratio, 3)
    cats_objs = DataTagCategoryModel.query.filter(
        DataTagCategoryModel.id.in_(cat_ids)
    ).all()  # pylint: disable=no-member
    data_objs = [t for cat in cats_objs for t in cat.data]
    tf_idf = tf_idf_from_tweets_and_cats_objs(data_objs, cats_objs)
    data_id_and_cat = {t.id: t.category for t in data_objs}
    training_and_test_sets = create_n_split_tnt_sets(30, ratio, data_id_and_cat)
    matrix_data = {"matrix_classes": {}, "accuracy": 0}
    matrix = ConfusionMatrixModel(
        categories=cats_objs,
        tweets=data_objs,
        tf_idf=tf_idf,
        training_and_test_sets=training_and_test_sets,
        train_data={"counts": 0, "words": {}},
        matrix_data=matrix_data,
        threshold=0,
        ratio=ratio,
        user=userid,
    )
    g.db.add(matrix)
    g.db.commit()
    return matrix


# new split to training and testing - with changing the relative sizes


def tf_idf_from_tweets_and_cats_objs(tweets, cats):
    """create a tf_idf dict from a list of tweets and a list of categories"""
    tf_idf = {}
    tf_idf["cat_counts"] = {cat.id: 0 for cat in cats}
    tf_idf["words"] = {}
    for tweet in tweets:
        tf_idf["cat_counts"][tweet.category] = tf_idf["cat_counts"][tweet.category] + 1
        for word in tweet.words:
            the_list = tf_idf["words"].get(word, [])
            the_list.append((tweet.id, tweet.category))
            tf_idf["words"][word] = the_list
    return tf_idf


def twitter_date_to_unix(date_str):
    """convert a twitter date string to a unix timestamp"""
    date_rep = "%a %b %d %H:%M:%S %z %Y"
    unix_time = time.mktime(datetime.strptime(date_str, date_rep).timetuple())
    return datetime.fromtimestamp(unix_time)


def add_data_from_dict(indict, category=None):
    """add a tweet to the database from a dict"""
    timestamp = twitter_date_to_unix(indict["time"])
    full_text = indict["full_text"]
    links = ([w for w in full_text.split() if "http" in w],)
    hashtags = ([w for w in full_text.split() if "#" in w],)
    mentions = ([w for w in full_text.split() if "@" in w],)
    data_parts = [clean_word(w) for w in full_text.split()]
    full_text = " ".join(data_parts)
    text = indict["full_text"]
    text = clean_non_transparencynum(remove_hash_links_mentions(text))
    words = text.split()
    a_tweet = DataModel(
        time_posted=timestamp,
        category=category.id if category else None,
        handle=indict["twitter_handle"],
        full_text=full_text,
        words=words,
        links=links,
        hashtags=hashtags,
        mentions=mentions,
        url="https://twitter.com/" + indict["twitter_handle"] + "/" + str(indict["id"]),
        text=" ".join([clean_word(word) for word in text.split()]),
    )
    g.db.add(a_tweet)
    g.db.commit()


def add_role(role_name):
    """add a role to the database"""
    role = RoleModel(name=role_name)
    g.db.add(role)
    g.db.commit()


def get_role(role_name):
    """get a role from the database"""
    return RoleModel.query.filter_by(name=role_name).first()


def create_bar_chart_data(predictions, title=""):
    """create a dictionary of data for a bar chart"""
    data = {}
    data["title"] = title
    colors = generate_n_hsl_colors(len(predictions))
    bg_colors = generate_n_hsl_colors(len(predictions), transparency=0.5)
    data_points = []
    for tup in zip(list(predictions.keys()), list(predictions.values()), colors, bg_colors):
        data_point = {}
        data_point["label"] = tup[0]
        data_point["estimate"] = tup[1]
        data_point["color"] = hsl_color_to_string(tup[2])
        data_point["bg_color"] = hsl_color_to_string(tup[3])
        data_points.append(data_point)
    data["data_points"] = data_points
    return data


def create_pie_chart_data(cat_names, title=""):
    """create a dictionary of data for a pie chart"""
    data = {}
    data["title"] = title
    colors = generate_n_hsl_colors(len(cat_names))
    bg_colors = generate_n_hsl_colors(len(cat_names), transparency=0.5)
    data_points = []
    for tup in zip(list(cat_names), colors, bg_colors):
        data_point = {}
        data_point["label"] = tup[0]
        data_point["color"] = hsl_color_to_string(tup[1])
        data_point["bg_color"] = hsl_color_to_string(tup[2])
        data_point["pie_data"] = 100 / len(cat_names)
        data_points.append(data_point)
    data["data_points"] = data_points
    return data


def ann_create_css_info(
    classifications, text, list_of_categories, ann
):  # pylint: disable=too-many-locals, unused-argument
    """create a dictionary of data for the css info"""
    category_color_dict = ann_assign_colors(list_of_categories)
    word_list = [(v, k) for k, v in ann[0].coordinates["word_locs"].items()]
    # print( category_color_dict)
    tups = [(word_list[w][0], w, "none", 0) for w in range(len(word_list))]
    for i in range(  # pylint: disable=consider-using-enumerate, too-many-nested-blocks
        len(word_list)
    ):
        word = word_list[i]
        cleaned_word = re.sub(r"[^\w\s]", "", word[0].lower())
        if cleaned_word in classifications and sum(classifications[cleaned_word].values()) > 0:
            relevants = []
            for j in ann:
                # print(str(w))
                if (
                    str(i) in j.coordinates["txt_coords"].keys()
                ):  # if the position is in the tagged area
                    if j.coordinates["txt_coords"][str(i)] not in relevants:
                        relevants.append((j.coordinates["txt_coords"][str(i)][0], i))
                    taglist = [
                        m.annotation_tag
                        for m in ann
                        if str(i) in m.coordinates["txt_coords"].keys()
                    ]
                    # print(taglist)
                    key_list = []
                    value_list = []
                    for tag in taglist:
                        if tag not in key_list:
                            key_list.append(tag)
                            value_list.append(taglist.count(tag))
                    # print(classifications[clean_word][max_key], category_color_dict[max_key])
                    the_tup = (
                        word[0],
                        i,
                        j.annotation_tag,
                        classifications[cleaned_word][j.annotation_tag],
                        category_color_dict[j.annotation_tag],
                        value_list,
                        key_list,
                    )  # @TODO: show all tags
                    if tups[i][2] == "none":
                        tups[i] = the_tup  # type: ignore
    return tups


def get_tags(analysis, words, a_tweet):  # set of tweet words
    """get tags for a tweet"""
    # take each word  and  calculate a proportion for each tag
    ann_tags = [c.name for c in ProjectModel.query.get(analysis.project).categories]
    for tag in list(analysis.annotation_tags.keys()):
        if tag not in ann_tags:
            ann_tags.append(tag)
    mydict = {word.lower(): {a.lower(): 0 for a in ann_tags} for word in words}
    annotations = DataAnnotationModel.query.filter(
        DataAnnotationModel.tweet == a_tweet.id, DataAnnotationModel.analysis == analysis.id
    ).all()
    for ann in annotations:
        if ann.text in a_tweet.full_text:
            for word in list(ann.coordinates["txt_coords"].keys()):
                w_to_tag = ann.coordinates["txt_coords"][word][1]
                if w_to_tag not in ["hashtag", "httplink", "twitter_id"]:
                    mydict[w_to_tag][ann.annotation_tag] += 1
    return mydict


# assign cell colors (red/green) for matrices
def matrix_css_info(index_list):
    """create a dictionary of data for the css info for a matrix"""
    matrix_colors = [[0, 100, 50], [120, 100, 25], [0, 100, 100]]  # cell colors
    tups = []
    x = 0  # pylint: disable=invalid-name
    alpha = 0.9
    green_list = []  # these are correct prediction cells
    for i in range(len(index_list)):
        green_list.append((x, x + 1))
        x += 1  # pylint: disable=invalid-name
    for i in index_list:
        row_sum = sum(i[h][0] for h in range(1, len(i)))
        for j in i:
            if j[-1] in green_list:
                j.append(matrix_colors[1])  # green
                j.append(round(((j[0] / row_sum) * alpha), 2))
            elif j[-1][1] == 0:
                j.append(matrix_colors[2])  # white
            else:
                j.append(matrix_colors[0])  # red
                j.append(round(((j[0] / row_sum) * alpha), 2))
        tups.append(i)
    return tups


def create_ann_css_info(annotations, pos_dict):
    """create a dictionary of data for the css info for annotations"""
    max_key = max(pos_dict.items(), key=operator.itemgetter(1))[0]
    alpha = int(100 / pos_dict[max_key]) * 0.01
    # print(alpha)
    tups = []
    for k, val in (
        annotations[0].coordinates["word_locs"].items()
    ):  # w is the word, k positition in the tweet
        if k in pos_dict.keys():
            opacity = alpha * pos_dict[k]
            # print(pos_dict[k])
            the_tup = (val, k, 100, 60, opacity, pos_dict[k])
            tups.append(the_tup)
        else:
            tups.append((val, k, 0, "", 0))
    return tups


def matrix_metrics(cat_names, matrix_classes):
    """create a dictionary of data for the css info for matrices"""
    metrics = {i: {"category": i, "recall": 0, "precision": 0} for i in cat_names}
    for i in cat_names:
        selected_cat = i
        tp_key = str("Pred_" + selected_cat + "_Real_" + selected_cat)
        recall_keys = [str("Pred_" + selected_cat + "_Real_" + i) for i in cat_names]
        if (  # pylint: disable=consider-using-generator
            sum([matrix_classes[x] for x in recall_keys]) > 0
        ):
            metrics[i]["recall"] = round(
                matrix_classes[tp_key] / sum([matrix_classes[x] for x in recall_keys]),
                2,  # pylint: disable=consider-using-generator
            )

        precision_keys = [str("Pred_" + i + "_Real_" + selected_cat) for i in cat_names]
        if (
            sum([matrix_classes[x] for x in precision_keys]) > 0  # pylint: disable=consider-using-generator
        ):
            metrics[i]["precision"] = round(
                matrix_classes[tp_key] / sum([matrix_classes[x] for x in precision_keys]
                                             ),  # pylint: disable=consider-using-generator
                2,
            )
    return metrics
