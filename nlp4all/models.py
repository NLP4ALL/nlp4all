from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from nlp4all import db, login_manager, app
from flask_login import UserMixin
from sqlalchemy.types import JSON
import collections

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class BayesianRobot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    parent = db.Column(db.Integer, db.ForeignKey('bayesian_robot.id'))
    analysis = db.Column(db.Integer, db.ForeignKey('bayesian_analysis.id'))
    features = db.Column(JSON)
    accuracy = db.Column(db.Float)
    retired = db.Column(db.Boolean, default=False)

    def clone(self):
        new_robot = BayesianRobot()
        new_robot.filters = self.filters
        new_robot.features = self.features
        new_robot.parent = self
        return(new_robot)
    

    # def run_analysis(self):
    def get_analysis():
        return BayesianAnalysis.query.get(self.analysis)


    def word_in_features(self, word):
        for f in self.features.keys():
            feature_string = f.lower()
            if feature_string.startswith('*') and feature_string.endswith('*'):
                if feature_string[1:-1] in word:
                    return(True)
            elif feature_string.startswith('*'):
                if word.endswith(feature_string[1:]):
                    return(True)
            elif feature_string.endswith('*'):
                if word.startswith(feature_string[:1]):
                    return(True)
            else:
                if word == feature_string :
                    return(True)
        return(False)

    def accuracy_for_tnt_set(words, tweets_with_word, words_by_tweet, tnt_sets):
        accuracy_dict = {}
        accuracy = 0
        # find de relevante tweets
        total_predictions_by_word = {}
        for tnt_set in tnt_sets:
            word_predictions = {}
            for word in words:
                categories_with_word_in_training = [n[1] for n in tnt_set[0].items() if n[0] in str(tweets_with_word[word])]
                predictions = {n : categories_with_word_in_training.count(n) / len(categories_with_word_in_training) for n in set(categories_with_word_in_training) }
                word_predictions[word] = predictions
            train_set = tnt_set[1]
            for t in train_set:
                if int(t) in words_by_tweet.keys():
                    category_predictions = collections.Counter({})
                    for word in words_by_tweet[int(t)]:
                        category_predictions = category_predictions + collections.Counter(word_predictions[word])
                    # predicted_category = max(category_predictions, key = lambda  k: category_predictions[k])
                    real_cat = Tweet.query.get(int(t)).category
                else:
                    accuracy_dict['uncategorized'] = []
            
    def calculate_accuracy(self):
        ana_obj = BayesianAnalysis.query.get(self.analysis)
        proj_obj = Project.query.get(ana_obj.project)
        tf_idf = proj_obj.tf_idf
        relevant_words = [word for  word in tf_idf.get('words') if BayesianRobot.word_in_features(self, word)]
        features_and_words = [{feature : BayesianRobot.feature_words(self, feature, tf_idf) for feature in self.features}]
        tweets_with_word = {word : [l[0] for l in tf_idf['words'].get(word)] for word in relevant_words}
        words_by_tweet =  {}
        for word, tweets in tweets_with_word.items():
            for t in tweets:
                the_list = words_by_tweet.get(t, [])
                the_list.append(word)
                words_by_tweet[t] = the_list
        x = BayesianRobot.accuracy_for_tnt_set(relevant_words, tweets_with_word, words_by_tweet, proj_obj.training_and_test_sets)

        # # okay, now we know which tweets contain any feature
        # # now we need to run through each of the training sets and compare to the test set
        # # this needs to be done for each category in the project.

    def feature_words(self, a_feature, tf_idf):
        return_list = []
        words = tf_idf.get('words')
        feature_string = a_feature.lower()
        for word in words:
            if feature_string.startswith('*') and feature_string.endswith('*'):
                if feature_string[1:-1] in word:
                    return_list.append(word)
            elif feature_string.startswith('*'):
                if word.endswith(feature_string[1:]):
                    return_list.append(word)
            elif feature_string.endswith('*'):
                if word.startswith(feature_string[:1]):
                    return_list.append(word)
            else:
                if word == feature_string :
                    return_list.append(word)
        return(return_list)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    organizations = db.relationship('Organization', secondary='user_orgs')
    admin = db.Column(db.Boolean, default=False)
    roles = db.relationship('Role', secondary='user_roles')
    analyses = db.relationship('BayesianAnalysis')

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


# Define the ProjectCategories association table
class ProjectCategories(db.Model):
    __tablename__ = 'project_categories'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('project.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('tweet_tag_category.id', ondelete='CASCADE'))

# Define the UserOrgs association table
class UserOrgs(db.Model):
    __tablename__ = 'user_orgs'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('organization.id', ondelete='CASCADE'))


# Define the Tweet-Project association table
class TweetProject(db.Model):
    __tablename__ = 'tweet_project'
    id = db.Column(db.Integer(), primary_key=True)
    tweet = db.Column(db.Integer(), db.ForeignKey('tweet.id', ondelete='CASCADE'))
    project = db.Column(db.Integer(), db.ForeignKey('project.id', ondelete='CASCADE'))

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))


# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     content = db.Column(db.Text, nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#     def __repr__(self):
#         return f"Post('{self.title}', '{self.date_posted}')"

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    users = db.relationship('User', secondary='user_orgs')
    projects = db.relationship('Project')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String)
    organization = db.Column(db.Integer, db.ForeignKey('organization.id'))
    analyses = db.relationship('BayesianAnalysis')
    categories = db.relationship('TweetTagCategory', secondary='project_categories')
    tf_idf = db.Column(JSON)
    tweets = db.relationship('Tweet', secondary='tweet_project')
    training_and_test_sets = db.Column(JSON)

    def get_tweets(self):
        return [t for cat in categories for t in cat.tweets]


class TweetTagCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(100))
    tweets = db.relationship('Tweet')
    tags = db.relationship('TweetTag')
    projects = db.relationship('Project', secondary='project_categories')

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_posted = db.Column(db.DateTime)
    category = db.Column(db.Integer, db.ForeignKey('tweet_tag_category.id'))
    projects = db.Column(db.Integer, db.ForeignKey('project.id'))
    handle = db.Column(db.String(15))
    full_text = db.Column(db.String(280))
    words = db.Column(JSON)
    hashtags = db.Column(JSON)
    tags = db.relationship('TweetTag')
    links = db.Column(JSON)
    mentions = db.Column(JSON)
    url = db.Column(db.String(200), unique=True)
    text = db.Column(db.String(300)) 
    
class TweetTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.Integer, db.ForeignKey('tweet_tag_category.id'))
    analysis = db.Column(db.Integer, db.ForeignKey('bayesian_analysis.id', ondelete="CASCADE"))
    tweet = db.Column(db.Integer, db.ForeignKey('tweet.id', ondelete="CASCADE"))

class BayesianAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(50))
    tags = db.relationship('TweetTag') # this also tells us which tweets
    data = db.Column(JSON)
    project = db.Column(db.Integer, db.ForeignKey('project.id'))
    robots = db.relationship('BayesianRobot')
    shared = db.Column(db.Boolean, default=False)
    tweets = db.Column(JSON, default=[])

    def get_project(self):
        return Project.query.get(self.project)

    def updated_data(self, tweet, category):
        self.data['counts'] = self.data['counts'] + 1
        if category.name not in self.data.keys():
            self.data[category.name] = {'counts' : 0, 'words' : {}}
        self.data[category.name]['counts'] = (self.data[category.name].get('counts', 0)) + 1
        for w in set(tweet.words):
            val = self.data[category.name]['words'].get(w, 0)
            self.data[category.name]['words'][w] = val + 1
        return self.data
    
    def get_predictions_and_words(self, words):
        # take each word  and  calculate a probabilty for each category
        categories = Project.query.get(self.project).categories
        category_names = [c.name for c in categories if c.name in self.data.keys()]
        preds = {}
        predictions = {}
        if self.data['counts'] == 0:
            predictions = {c : {w : 0} for w in words for c in category_names}
            # predictions = {word : {category : 0 for category in category_names} for word in words}
        else:
            for w in words: # only categorize each word once
                preds[w] = {c : 0 for c in category_names}
                for cat in category_names:
                    predictions[cat] = predictions.get(cat, {})
                    prob_ba = self.data[cat]['words'].get(w, 0) / self.data[cat]['counts']
                    prob_a = self.data[cat]['counts'] / self.data['counts'] 
                    prob_b = sum([self.data[c]['words'].get(w, 0) for c in category_names]) / self.data['counts']
                    if  prob_b == 0:
                        preds[w][cat] = 0
                        predictions[cat][w] = 0
                    else:
                        preds[w][cat] = round(prob_ba * prob_a / prob_b, 2)
                        predictions[cat][w] = round(prob_ba * prob_a / prob_b, 2)

        # print (preds, {k : round(sum(v.values()) / len(set(words)),2) for k, v in predictions.items()})
        return (preds, {k : round(sum(v.values()) / len(set(words)),2) for k, v in predictions.items()})