"""models.py, sqlalchemy model definitions

This file contains the model definitions for the database tables used by the
application. The models are defined using the SQLAlchemy ORM. The models are
then used by the application to create the database tables and to interact with
the database.
"""
import collections
import functools
import operator
from random import sample
from datetime import datetime
import jwt
from nlp4all import db, login_manager, app, utils
from flask_login import UserMixin
from sqlalchemy.types import JSON
from sqlalchemy.orm import load_only
from nlp4all import db, login_manager, app
from nlp4all.datasets import create_n_split_tnt_sets

@login_manager.user_loader
def load_user(user_id):
    """Loads a user from the database.

    Args:
        user_id (int): The id of the user to load.

    Returns:
       User: User object.
    """
    return User.query.get(int(user_id))


class BayesianRobot(db.Model):
    """BayesianRobot model."""

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(25))
    parent = db.Column(db.Integer, db.ForeignKey("bayesian_robot.id"), default=None)
    child = db.Column(db.Integer, db.ForeignKey("bayesian_robot.id"), default=None)
    analysis = db.Column(db.Integer, db.ForeignKey("bayesian_analysis.id"))
    features = db.Column(JSON, default={})
    accuracy = db.Column(JSON, default={})
    retired = db.Column(db.Boolean, default=False)
    time_retired = db.Column(db.DateTime)

    def clone(self):
        """Clones a BayesianRobot object.

        Returns:
            BayesianRobot: A new BayesianRobot object.
        """
        new_robot = BayesianRobot()
        new_robot.name = self.name
        new_robot.analysis = self.analysis
        new_robot.features = self.features
        new_robot.parent = self.id
        new_robot.user = self.user
        return new_robot

    def get_analysis(self):
        """Gets the BayesianAnalysis object associated with the robot.

        Returns:
            BayesianAnalysis: The BayesianAnalysis object associated with the robot.
        """
        return BayesianAnalysis.query.get(self.analysis)

    def word_in_features(self, word):
        """Checks if a word is in the features of the robot.

        Args:
            word (str): The word to check.

        Returns:
            bool: True if the word is in the features of the robot, False otherwise.
        """
        for feature in self.features.keys():
            feature_string = feature.lower()
            if feature_string.startswith("*") and feature_string.endswith("*"):
                if feature_string[1:-1] in word:
                    return True
            elif feature_string.startswith("*"):
                if word.endswith(feature_string[1:]):
                    return True
            elif feature_string.endswith("*"):
                if word.startswith(feature_string[:1]):
                    return True
            else:
                if word == feature_string:
                    return True
        return False

    def calculate_accuracy(self): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Calculates the accuracy of the robot.

        Returns:
            dict: A dictionary containing the accuracy of the robot.
        """
        # @TODO: This function is too long and needs to be refactored.
        analysis_obj = BayesianAnalysis.query.get(self.analysis)
        proj_obj = Project.query.get(analysis_obj.project)
        tf_idf = proj_obj.tf_idf
        feature_words = {}
        for feature in self.features:
            feature_words[feature] = [
                word for word in tf_idf.get("words") if BayesianRobot.matches(word, feature)
            ]
        # relevant_words = [w for words in feature_words.values() for w in words]
        # first calculate the predictions, based on the training sets.
        predictions_by_feature = {}
        # initialize test_set_tweets so we dont need to calculate it twice
        test_set_tweets = set()
        cats = [c.id for c in proj_obj.categories]

        # make one for individual words too so we can more easily access them
        # later, and make a  list of category names for viewing
        word_category_predictions = {}
        cat_names = {cat.id: cat.name for cat in Project.query.get(analysis_obj.project).categories}

        for feature in feature_words.keys(): # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            predictions_by_feature[feature] = {}
            for word in feature_words[feature]:
                for dataset in proj_obj.training_and_test_sets[:1]:
                    train_set = dataset[0]
                    tweets = tf_idf.get("words").get(word)
                    train_set_tweets = []
                    for tweet in tweets:
                        if str(tweet[0]) in train_set.keys():
                            train_set_tweets.append(tweet)
                        else:
                            test_set_tweets.add(tweet[0])
                    categories_in_dataset = [
                        dataset[0].get(str(tweet[0])) for tweet in train_set_tweets
                    ]
                    cat_counts = {c: categories_in_dataset.count(c) for c in cats}
                    total_cats = sum(cat_counts.values())
                    predictions = 0
                    # if there are no words in the training set to learn from,
                    # we simply ignore the word and do not append anything here
                    if total_cats > 0:
                        predictions = {c: cat_counts[c] / sum(cat_counts.values()) for c in cats}
                        category_dict = {
                            "category_prediction": cat_names[
                                max(predictions.items(), key=operator.itemgetter(1))[0]
                            ]
                        }
                        word_category_predictions[word] = category_dict
                        predictions_by_feature[feature][word] = predictions
        # now for each word, figure out which tweets contain them, and build -
        # for each tweet - a classification, that we can then compare to the
        # real value

        test_set = proj_obj.training_and_test_sets[0][1]
        tweet_predictions = {}

        for word_prediction in predictions_by_feature.values():
            for word, predictions in word_prediction.items():
                word_tweets = tf_idf.get("words").get(word)
                test_set_tweets = [
                    tweet for tweet in word_tweets if str(tweet[0]) in test_set.keys()
                ]
                for tweet in test_set_tweets:
                    preds = tweet_predictions.get(
                        tweet[0], {"predictions": [], "words": [], "category": tweet[1]}
                    )
                    preds["predictions"].append(predictions)
                    preds["words"].append(word)
                    tweet_predictions[tweet[0]] = preds
        # now finally evaluate how well we did, in general and by word
        word_accuracy = {}
        for tweet_key in tweet_predictions.keys():  # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            prediction_dict = tweet_predictions[tweet_key].copy()

            summed_prediction = dict(
                functools.reduce(
                    operator.add, map(collections.Counter, prediction_dict["predictions"])
                )
            )
            # the old code that makes summed_prediction also includes the newly
            # added "category_prediction". Since we don't want to
            # sum that, we remove it first
            # it can happen that we evaluate a word that we have no information
            # on. In that
            cat_prediction = max(summed_prediction.items(), key=operator.itemgetter(1))[0]
            tweet_predictions[tweet_key]["correct"] = test_set[str(tweet_key)] == cat_prediction
            # save a per-word accuracy
            for word in prediction_dict["words"]:
                acc = word_accuracy.get(word, [])
                acc.append(tweet_predictions[tweet_key]["correct"])
                word_accuracy[word] = acc
        # and then build a nice dict full of info
        feature_info = {}
        for feature in feature_words.keys(): # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            feature_info[feature] = {}
            feature_info[feature]["words"] = {}
            for word in feature_words[feature]:
                word_dict = feature_info[feature].get(word, {})
                if (
                    word in word_accuracy
                ):  # the word is only in the word_accuracy dict if it was in the test set
                    word_dict["tweets_targeted"] = len(word_accuracy[word])
                    word_dict["accuracy"] = round(
                        len([x for x in word_accuracy[word] if x]) / len(word_accuracy[word]), 2
                    )
                    feature_info[feature]["words"][word] = word_dict
                # else:
                #     # if it's not in the test set, we just take it out.
                #     word_dict['tweets_targeted'] = 0
                #     word_dict['accuracy'] = 0
                # feature_info[feature]['words'][word] = word_dict

            accuracy_values = [d["accuracy"] for d in feature_info[feature]["words"].values()]
            targeted_values = [
                d["tweets_targeted"] for d in feature_info[feature]["words"].values()
            ]
            if len(accuracy_values) > 0:
                feature_info[feature]["accuracy"] = sum(accuracy_values) / len(accuracy_values)
                feature_info[feature]["tweets_targeted"] = sum(targeted_values)
            else:
                feature_info[feature]["accuracy"] = 0
                feature_info[feature]["tweets_targeted"] = 0
        tweets_targeted = 0
        table_data = []
        for feature in feature_info.keys(): # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
            tweets_targeted = tweets_targeted + feature_info[feature]["tweets_targeted"]
            feat_dict = {}
            feat_dict["word"] = feature
            feat_dict["category_prediction"] = "N/A"
            feat_dict["accuracy"] = feature_info[feature]["accuracy"]
            feat_dict["tweets_targeted"] = feature_info[feature]["tweets_targeted"]
            score = feat_dict["accuracy"] * feat_dict["tweets_targeted"] - (
                (1 - feat_dict["accuracy"]) * feat_dict["tweets_targeted"]
            )
            print(score)
            feat_dict["score"] = round(score, 2)
            # calculate the most often predicted category. This isn't trivial -
            # should it be by total tweets in test set, or just the most common
            # category across its words? Well, it's obvious. Boo. It needs to be
            # weighted by how many tweets there are.
            # NO  NO NO! I thought about that wrong. We just want the average
            # of each of the category prediction for each word.
            print(feat_dict)
            table_data.append(feat_dict)
            for word in feature_info[feature]["words"]:
                feat_dict = {}
                feat_dict["word"] = word
                feat_dict["category_prediction"] = word_category_predictions[word][
                    "category_prediction"
                ]
                feat_dict["accuracy"] = feature_info[feature]["words"][word]["accuracy"]
                feat_dict["tweets_targeted"] = feature_info[feature]["words"][word]["tweets_targeted"] # pylint: disable=line-too-long
                score = feat_dict["accuracy"] * feat_dict["tweets_targeted"] - (
                    (1 - feat_dict["accuracy"]) * feat_dict["tweets_targeted"]
                )
                print(score)
                feat_dict["score"] = round(score, 2)
                table_data.append(feat_dict)
        if len(tweet_predictions) == 0:
            accuracy = 0
        else:
            accuracy = len([d for d in tweet_predictions.values() if d["correct"]]) / len(
                tweet_predictions
            )
        accuracy_info = {"accuracy": round(accuracy, 2), "tweets_targeted": tweets_targeted}
        accuracy_info["features"] = feature_info
        accuracy_info["table_data"] = table_data
        return accuracy_info

    @staticmethod
    def matches(aword, afeature):
        """Check if a word matches a feature."""
        feature_string = afeature.lower()
        if feature_string.startswith("*") and feature_string.endswith("*"):
            if feature_string[1:-1] in aword:
                return True
        elif feature_string.startswith("*"):
            if aword.endswith(feature_string[1:]):
                return True
        elif feature_string.endswith("*"):
            # if aword.startswith(feature_string[:1]): ## this was a bug. Leave
            # it in if people want to see it.
            if aword.startswith(feature_string[:-1]):
                return True
        else:
            if aword == feature_string:
                return True
        return False

    def feature_words(self, a_feature, tf_idf):
        """Return a list of words that match a feature."""
        return_list = []
        words = tf_idf.get("words")
        feature_string = a_feature.lower()
        for word in words:
            if feature_string.startswith("*") and feature_string.endswith("*"):
                if feature_string[1:-1] in word:
                    return_list.append(word)
            elif feature_string.startswith("*"):
                if word.endswith(feature_string[1:]):
                    return_list.append(word)
            elif feature_string.endswith("*"):
                if word.startswith(feature_string[:1]):
                    return_list.append(word)
            else:
                if word == feature_string:
                    return_list.append(word)
        return return_list


class User(db.Model, UserMixin):
    """User model."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    organizations = db.relationship("Organization", secondary="user_orgs")
    admin = db.Column(db.Boolean, default=False)
    roles = db.relationship("Role", secondary="user_roles")
    analyses = db.relationship("BayesianAnalysis")

    def get_reset_token(self, expires_sec=1800):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_sec},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


# Define the Role data-model


class Role(db.Model): # pylint: disable=too-few-public-methods
    """Role model."""
    __tablename__ = "role"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


# Define the ProjectCategories association table
class ProjectCategories(db.Model): # pylint: disable=too-few-public-methods
    """ProjectCategories model."""
    __tablename__ = "project_categories"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("project.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer(), db.ForeignKey("tweet_tag_category.id", ondelete="CASCADE"))


# Define the UserOrgs association table


class UserOrgs(db.Model): # pylint: disable=too-few-public-methods
    """UserOrgs model."""
    __tablename__ = "user_orgs"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer(), db.ForeignKey("organization.id", ondelete="CASCADE"))


# Define the Tweet-Project association table
class TweetProject(db.Model): # pylint: disable=too-few-public-methods
    """TweetProject model."""
    __tablename__ = "tweet_project"
    id = db.Column(db.Integer(), primary_key=True)
    tweet = db.Column(db.Integer(), db.ForeignKey("tweet.id", ondelete="CASCADE"))
    project = db.Column(db.Integer(), db.ForeignKey("project.id", ondelete="CASCADE"))


# Define the UserRoles association table


class UserRoles(db.Model): # pylint: disable=too-few-public-methods
    """UserRoles model."""
    __tablename__ = "user_roles"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer(), db.ForeignKey("role.id", ondelete="CASCADE"))


# Define the Matrix-Categories association table


class MatrixCategories(db.Model): # pylint: disable=too-few-public-methods
    """MatrixCategories model."""
    __tablename__ = "confusionmatrix_categories"
    id = db.Column(db.Integer(), primary_key=True)
    matrix_id = db.Column(db.Integer(), db.ForeignKey("confusion_matrix.id", ondelete="CASCADE"))
    category_id = db.Column(
        db.Integer(), db.ForeignKey("tweet_tag_category.id", ondelete="CASCADE")
    )


# Define the Tweet-Matrix association table
class TweetMatrix(db.Model): # pylint: disable=too-few-public-methods
    """TweetMatrix model."""
    __tablename__ = "tweet_confusionmatrix"
    id = db.Column(db.Integer(), primary_key=True)
    tweet = db.Column(db.Integer(), db.ForeignKey("tweet.id", ondelete="CASCADE"))
    matrix = db.Column(db.Integer(), db.ForeignKey("confusion_matrix.id", ondelete="CASCADE"))

class Organization(db.Model): # pylint: disable=too-few-public-methods
    """Organization model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    users = db.relationship("User", secondary="user_orgs")
    projects = db.relationship("Project")


class Project(db.Model):
    """Project model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String)
    organization = db.Column(db.Integer, db.ForeignKey("organization.id"))
    analyses = db.relationship("BayesianAnalysis")
    categories = db.relationship("TweetTagCategory", secondary="project_categories")
    tf_idf = db.Column(JSON)
    tweets = db.relationship("Tweet", secondary="tweet_project", lazy="dynamic")
    training_and_test_sets = db.Column(JSON)

    def get_tweets(self):
        """Get tweets."""
        return [t for cat in self.categories for t in cat.tweets] # pylint: disable=not-an-iterable

    def get_random_tweet(self):
        """Get a random tweet."""
        tweet_ids = self.tweets.options(load_only("id")).all() # pylint: disable=no-member
        the_tweet_id = sample(tweet_ids, 1)[0]
        return Tweet.query.get(the_tweet_id.id)


class TweetTagCategory(db.Model): # pylint: disable=too-few-public-methods
    """TweetTagCategory model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(100))
    tweets = db.relationship("Tweet")
    tags = db.relationship("TweetTag")
    projects = db.relationship("Project", secondary="project_categories")
    # matrices = db.relationship('ConfusionMatrix', secondary='matrix_categories')


class Tweet(db.Model): # pylint: disable=too-few-public-methods
    """Tweet model."""
    id = db.Column(db.Integer, primary_key=True)
    time_posted = db.Column(db.DateTime)
    category = db.Column(db.Integer, db.ForeignKey("tweet_tag_category.id"))
    projects = db.Column(db.Integer, db.ForeignKey("project.id"))
    handle = db.Column(db.String(15))
    full_text = db.Column(db.String(280))
    words = db.Column(JSON)
    hashtags = db.Column(JSON)
    tags = db.relationship("TweetTag")
    links = db.Column(JSON)
    mentions = db.Column(JSON)
    url = db.Column(db.String(200), unique=True)
    text = db.Column(db.String(300))
    annotations = db.relationship("TweetAnnotation")


class TweetTag(db.Model): # pylint: disable=too-few-public-methods
    """TweetTag model."""
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    category = db.Column(db.Integer, db.ForeignKey("tweet_tag_category.id"))
    analysis = db.Column(db.Integer, db.ForeignKey("bayesian_analysis.id", ondelete="CASCADE"))
    tweet = db.Column(db.Integer, db.ForeignKey("tweet.id", ondelete="CASCADE"))
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class BayesianAnalysis(db.Model):
    """BayesianAnalysis model."""
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(50))
    tags = db.relationship("TweetTag")  # this also tells us which tweets
    data = db.Column(JSON)
    project = db.Column(db.Integer, db.ForeignKey("project.id"))
    robots = db.relationship("BayesianRobot")
    shared = db.Column(db.Boolean, default=False)
    shared_model = db.Column(db.Boolean, default=False)
    tweets = db.Column(JSON, default=[])
    annotate = db.Column(db.Boolean, default=False)
    annotations = db.relationship("TweetAnnotation")
    annotation_tags = db.Column(JSON)
    annotate = db.Column(db.Integer, default=1)

    def get_project(self):
        """Get project."""
        return Project.query.get(self.project)

    # pylint: disable=unsupported-assignment-operation, unsubscriptable-object
    def updated_data(self, tweet, category):
        """Update data."""
        self.data["counts"] = self.data["counts"] + 1
        if category.name not in self.data.keys(): # pylint: disable=no-member
            self.data[category.name] = {"counts": 0, "words": {}}
        self.data[category.name]["counts"] = (self.data[category.name].get("counts", 0)) + 1
        for word in set(tweet.words):
            val = self.data[category.name]["words"].get(word, 0)
            self.data[category.name]["words"][word] = val + 1
        return self.data
    # pylint: enable=unsupported-assignment-operation, unsubscriptable-object

    # pylint: disable=unsupported-assignment-operation, unsubscriptable-object
    def updated_a_tags(self, atag, tweet):
        """Update annotation tags."""
        if atag not in self.annotation_tags.keys(): # pylint: disable=no-member
            self.annotation_tags[atag] = {"counts": 0, "category": tweet.handle, "tweets": []}
        self.annotation_tags[atag]["counts"] = self.annotation_tags[atag]["counts"] + 1
        if tweet.id not in self.annotation_tags[atag]["tweets"]:
            self.annotation_tags[atag]["tweets"].append(tweet.id)
        return self.annotation_tags
    # pylint: enable=unsupported-assignment-operation, unsubscriptable-object

    # pylint: disable=unsupported-assignment-operation, unsubscriptable-object
    def get_predictions_and_words(self, words):
        """Get predictions and words."""
        # take each word  and  calculate a probabilty for each category
        categories = Project.query.get(self.project).categories
        category_names = [c.name for c in categories if c.name in self.data.keys()] # pylint: disable=no-member
        preds = {}
        predictions = {}
        if self.data["counts"] == 0:
            predictions = {c: {w: 0} for w in words for c in category_names}
            # predictions = {word : {category : 0 for category in category_names} for word in words}
        else:
            for word in words:  # only categorize each word once
                preds[word] = {c: 0 for c in category_names}
                for cat in category_names:
                    predictions[cat] = predictions.get(cat, {})
                    prob_ba = self.data[cat]["words"].get(word, 0) / self.data[cat]["counts"]
                    prob_a = self.data[cat]["counts"] / self.data["counts"]
                    prob_b = (
                        sum([self.data[c]["words"].get(word, 0) for c in category_names]) # pylint: disable=consider-using-generator
                        / self.data["counts"]
                    )
                    if prob_b == 0:
                        preds[word][cat] = 0
                        predictions[cat][word] = 0
                    else:
                        preds[word][cat] = round(prob_ba * prob_a / prob_b, 2)
                        predictions[cat][word] = round(prob_ba * prob_a / prob_b, 2)

        return (
            preds,
            {k: round(sum(v.values()) / len(set(words)), 2) for k, v in predictions.items()},
        )
    # pylint: enable=unsupported-assignment-operation, unsubscriptable-object

class ConfusionMatrix(db.Model): # pylint: disable=too-many-instance-attributes
    """Confusion matrix."""
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    categories = db.relationship("TweetTagCategory", secondary="confusionmatrix_categories")
    tweets = db.relationship("Tweet", secondary="tweet_confusionmatrix")
    matrix_data = db.Column(JSON)  # here to save the TP/TN/FP/FN
    train_data = db.Column(JSON)  # word counts from the training set
    tf_idf = db.Column(JSON)
    training_and_test_sets = db.Column(JSON)
    threshold = db.Column(db.Float())
    ratio = db.Column(db.Float())
    data = db.Column(JSON)  # accuracy etc resuts from the matrix
    parent = db.Column(
        db.Integer, db.ForeignKey("confusion_matrix.id"), default=None
    )  # for cloning purposes
    child = db.Column(db.Integer, db.ForeignKey("confusion_matrix.id"), default=None)

    def clone(self):
        """Clone confusion matrix."""
        new_matrix = ConfusionMatrix()
        new_matrix.parent = self.id
        new_matrix.categories = self.categories
        new_matrix.tweets = self.tweets
        new_matrix.tf_idf = self.tf_idf
        new_matrix.training_and_test_sets = self.training_and_test_sets
        new_matrix.ratio = self.ratio
        new_matrix.train_data = {"counts": 0, "words": {}}
        return new_matrix

    def updated_data(self, tweet, category):
        """Update data."""
        # update the train_data when you change tnt set, this is mostly copied
        # from a Bayesian analysis function above
        self.train_data["counts"] = self.train_data["counts"] + 1
        if category.name not in self.train_data:
            self.train_data[category.name] = {"counts": 0, "words": {}}
        self.train_data[category.name]["counts"] = (
            self.train_data[category.name].get("counts", 0)
        ) + 1
        for word in set(tweet.words):
            val = self.train_data[category.name]["words"].get(word, 0)
            self.train_data[category.name]["words"][word] = val + 1
        return self.train_data

    def update_tnt_set(self):
        """Update the training and test sets."""
        tweet_id_and_cat = {t.id: t.category for t in self.tweets}
        self.training_and_test_sets = create_n_split_tnt_sets(
            30, self.ratio, tweet_id_and_cat
        )
        return self.training_and_test_sets

    def get_predictions_and_words(self, words):
        """Get predictions and words."""
        # works the same way as for bayesian analysis
        categories = self.categories
        category_names = [c.name for c in categories]
        preds = {}
        predictions = {}
        if self.train_data["counts"] == 0:
            predictions = {c: {w: 0} for w in words for c in category_names}
            # predictions = {word : {category : 0 for category in category_names} for word in words}
        else:
            for word in words:  # only categorize each word once
                preds[word] = {c: 0 for c in category_names}
                for cat in category_names:
                    predictions[cat] = predictions.get(cat, {})
                    prob_ba = (
                        self.train_data[cat]["words"].get(word, 0) / self.train_data[cat]["counts"]
                    )
                    prob_a = self.train_data[cat]["counts"] / self.train_data["counts"]
                    prob_b = (
                        sum([self.train_data[c]["words"].get(word, 0) for c in category_names]) # pylint: disable=consider-using-generator
                        / self.train_data["counts"]
                    )
                    if prob_b == 0:
                        preds[word][cat] = 0
                        predictions[cat][word] = 0
                    else:
                        preds[word][cat] = round(prob_ba * prob_a / prob_b, 2)
                        predictions[cat][word] = round(prob_ba * prob_a / prob_b, 2)

        return (
            preds,
            {k: round(sum(v.values()) / len(set(words)), 2) for k, v in predictions.items()},
        )

    def train_model(self, train_tweet_ids):
        """Train model."""
        # reinitialize the training data
        self.train_data = {"counts": 0, "words": {}}
        # trains the model with the training data tweets
        for tweet_id in train_tweet_ids:
            tweet = Tweet.query.get(tweet_id)
            category_id = tweet.category
            category = TweetTagCategory.query.get(category_id)
            train_data = self.updated_data(tweet, category)
        return train_data

    def make_matrix_data(self, test_tweets, cat_names): # pylint: disable=unused-argument
        """Make matrix data."""
        # classifies the tweets according to the calculated prediction
        # probabilities
        matrix_data = {
            t.id: {"predictions": 0, "pred_cat": "", "probability": 0, "relative probability": 0}
            for t in test_tweets
        }
        words = {t.id: "" for t in test_tweets}

        for a_tweet in test_tweets:
            (
                words[a_tweet.id],
                matrix_data[a_tweet.id]["predictions"],
            ) = self.get_predictions_and_words(set(a_tweet.words))
            # if no data
            if bool(matrix_data[a_tweet.id]["predictions"]) is False:
                matrix_data[a_tweet.id]["pred_cat"] = "none"
            # if all prob == 0
            elif sum(matrix_data.get(a_tweet.id)["predictions"].values()) == 0:
                matrix_data[a_tweet.id]["pred_cat"] = "none"
            # else select the biggest prob
            else:
                matrix_data[a_tweet.id]["pred_cat"] = max(
                    matrix_data[a_tweet.id]["predictions"].items(), key=operator.itemgetter(1)
                )[0]
                # bayesian p
                matrix_data[a_tweet.id]["probability"] = max(
                    matrix_data[a_tweet.id]["predictions"].items(), key=operator.itemgetter(1)
                )[1]
                # relative p compared to other cats
                max_prob = max(
                    matrix_data[a_tweet.id]["predictions"].items(), key=operator.itemgetter(1)
                )[1]
                matrix_data[a_tweet.id]["relative probability"] = round(
                    max_prob / sum(matrix_data[a_tweet.id]["predictions"].values()), 3
                )
            # add the real category
            matrix_data[a_tweet.id]["real_cat"] = a_tweet.handle

        matrix_data = sorted(
            list(matrix_data.items()), key=lambda x: x[1]["probability"], reverse=True
        )  # add matrix classes/quadrants
        for tweet in matrix_data:  # this is just for indexing tweets
            for cat in self.categories:
                # if correct prediction
                if tweet[1]["pred_cat"] == tweet[1]["real_cat"] and tweet[1]["pred_cat"] == cat.name: # pylint: disable=line-too-long
                    tweet[1]["class"] = "Pred_" + str(cat.name) + "_Real_" + tweet[1]["real_cat"]
                # if uncorrect prediction
                elif tweet[1]["pred_cat"] != tweet[1]["real_cat"] and tweet[1]["pred_cat"] == cat.name: # pylint: disable=line-too-long
                    # predicted 'no', although was 'yes'
                    tweet[1]["class"] = "Pred_" + str(cat.name) + "_Real_" + tweet[1]["real_cat"]
                # if no prediction
                elif tweet[1]["pred_cat"] == "none":
                    tweet[1]["class"] = "undefined"
        return matrix_data

    def make_table_data(self, cat_names):
        """Make table data."""
        # this function is a manual way to create confusion matrix data rows
        current_data_class = [self.matrix_data[i].get("real_cat") for i in self.matrix_data.keys()] # pylint: disable=unsubscriptable-object, no-member
        predicted_class = [self.matrix_data[i].get("pred_cat") for i in self.matrix_data.keys()] # pylint: disable=unsubscriptable-object, no-member
        number_list = list(range(len(cat_names)))
        # change cat names to numbers 1,2,...
        for i in number_list:
            for j in range(len(current_data_class)): # pylint: disable=consider-using-enumerate
                if current_data_class[j] == cat_names[i]:
                    current_data_class[j] = i + 1
        for i in number_list:
            for j in range(len(predicted_class)): # pylint: disable=consider-using-enumerate
                if predicted_class[j] == cat_names[i]:
                    predicted_class[j] = i + 1
        # find number of classes
        classes = int(max(current_data_class) - min(current_data_class)) + 1
        counts = [
            [
                sum( # pylint: disable=consider-using-generator
                    [
                        (current_data_class[i] == true_class) and (predicted_class[i] == pred_class)
                        for i in range(len(current_data_class))
                    ]
                )
                for pred_class in range(1, classes + 1)
            ]
            for true_class in range(1, classes + 1)
        ]

        return counts


class TweetAnnotation(db.Model): # pylint: disable=too-few-public-methods
    """Tweet annotation."""
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    # category = db.Column(db.Integer, db.ForeignKey('tweet_tag_category.id'))
    # dropdown: project categories, other
    annotation_tag = db.Column(db.String(50))
    analysis = db.Column(db.Integer, db.ForeignKey("bayesian_analysis.id", ondelete="CASCADE"))
    tweet = db.Column(db.Integer, db.ForeignKey("tweet.id", ondelete="CASCADE"))
    words = db.Column(JSON)
    text = db.Column(db.String(50))
    coordinates = db.Column(JSON)
    time_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
