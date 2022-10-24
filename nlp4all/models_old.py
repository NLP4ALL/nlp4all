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
from datetime import datetime, timezone, timedelta
import jwt
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

    def get_reset_token(self, expires_sec: int = 1800) -> str:
        """Get a reset token.
        Parameters:
            expires_sec (int): Number of seconds the token remains valid
        returns:
            reset_token (str): The token needed to reset the password"""
        reset_token = jwt.encode(
            {
                "user_id": self.id,
                "exp": datetime.now(tz=timezone.utc)
                        + timedelta(seconds=expires_sec)
            },
            app.config['SECRET_KEY'],
            algorithm="HS256"
        )
        return reset_token

    @staticmethod
    def verify_reset_token(token: str) -> 'User':
        """decodes the token

        Returns:
            None (None): if the token is invalid
            or
            User.query.get(user_id) ('User') : if the token is valid"""

        try:
            data = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                leeway=timedelta(seconds=10),
                algorithms=["HS256"]
                )

            user_id = data['user_id']

        except jwt.ExpiredSignatureError:
            return "Expired"
        except jwt.InvalidTokenError:
            return "Invalid"
        return User.query.get(user_id)

    def __repr__(self):
        """represents the user object
        without it print(User.query.get(user_id)) returns <user.id>"""
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
