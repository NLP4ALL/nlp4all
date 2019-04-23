from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from nlp4all import db, login_manager, app
from flask_login import UserMixin
from sqlalchemy.types import JSON


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    # posts = db.relationship('Post', backref='author', lazy=True)
    organizations = db.relationship('Organization', secondary='user_orgs')
    roles = db.relationship('Role', secondary='user_roles')

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
    organization = db.Column(db.Integer, db.ForeignKey('organization.id'))

class TweetTagCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    tweets = db.relationship('Tweet')

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.Integer, db.ForeignKey('tweet_tag_category.id'))
    handle = db.Column(db.String(15))
    text = db.Column(db.String(280))
    words = db.Column(JSON)
    hashtags = db.Column(JSON)
    
# class BayesianAnalysis(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50))
#     tweets = db.relationship('Tweet')
